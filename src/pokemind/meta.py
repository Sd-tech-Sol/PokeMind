"""Instantanés descriptifs de la Limitless Tournament Platform."""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
import secrets
import socket
import time
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pokemind.security import neutral_exception_code

from pokemind.database import SCHEMA_VERSION, connect_readonly, connect_writable, initialize_schema, utc_now


API_ORIGIN = "https://play.limitlesstcg.com"
API_PREFIX = "/api"
USER_AGENT = "PokeMind/0.5 (+local bounded Limitless client)"
MAX_JSON_BYTES = 8 * 1024 * 1024
DEFAULT_TIMEOUT = 20.0
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_FORMATS = {"standard": "STANDARD", "expanded": "EXPANDED"}


class MetaError(ValueError):
    """Erreur contrôlée de la couche métagame."""


class RequestBudgetExhausted(MetaError):
    """Le budget explicite de requêtes est épuisé."""


class MetaNetworkFailure(MetaError):
    """La source n'a pas produit de réponse exploitable."""


class ProviderRateLimitExhausted(MetaNetworkFailure):
    """Le fournisseur a explicitement annoncé qu'aucun GET ne restait."""


def _validate_public_api_url(url: str) -> str:
    """Valide l'URL complète contre la petite allowlist publique utilisée."""
    parsed = urlparse(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise MetaError("Port Limitless invalide.") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname != "play.limitlesstcg.com"
        or port is not None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise MetaError("Seul l'hôte HTTPS public exact de Limitless est autorisé, sans identifiants ni fragment.")
    path = parsed.path
    listing = path == "/api/tournaments"
    allowed = path == "/api/games" or listing or re.fullmatch(
        r"/api/tournaments/[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}/(details|standings|pairings)", path
    )
    if not allowed:
        raise MetaError("Endpoint public Limitless non autorisé.")
    if parsed.query:
        if not listing:
            raise MetaError("Paramètres inattendus sur un endpoint Limitless de tournoi.")
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        allowed_keys = {"game", "format", "limit", "page"}
        keys = [key for key, _ in pairs]
        if not pairs or any(key not in allowed_keys for key in keys) or len(keys) != len(set(keys)):
            raise MetaError("Paramètres de liste Limitless non autorisés.")
        if any(not value or len(value) > 128 for _, value in pairs):
            raise MetaError("Valeur de paramètre Limitless invalide.")
    return url


class _SafeRedirectHandler(HTTPRedirectHandler):
    def __init__(self, before_redirect: Callable[[Any], None] | None = None) -> None:
        super().__init__()
        self._before_redirect = before_redirect

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        if req.get_method() != "GET":
            raise MetaNetworkFailure("Redirection Limitless refusée pour une méthode autre que GET.")
        try:
            _validate_public_api_url(newurl)
        except MetaError as exc:
            raise MetaNetworkFailure(f"Redirection Limitless refusée: {exc}") from exc
        if self._before_redirect is not None:
            self._before_redirect(headers)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _safe_api_url(path: str, params: dict[str, Any] | None = None) -> str:
    if not path.startswith("/") or "?" in path or "#" in path or ".." in path:
        raise MetaError("Chemin d'API Limitless invalide.")
    url = f"{API_ORIGIN}{API_PREFIX}{path}"
    if params:
        url += "?" + urlencode(params)
    try:
        return _validate_public_api_url(url)
    except MetaError as exc:
        if re.fullmatch(r"/games/[^/]+/decks/?", path, re.IGNORECASE):
            raise MetaError("L'endpoint protégé /games/{id}/decks est interdit dans PokeMind.") from exc
        raise


def _rate_limit_remaining(headers: Any) -> int | None:
    """Retourne seulement un reste explicite et parsable, sans inventer de politique."""
    values: list[int] = []
    for key, raw in headers.items():
        lowered = str(key).lower()
        value = str(raw).strip()
        if lowered in {"x-ratelimit-remaining", "ratelimit-remaining"}:
            if re.fullmatch(r"\d+", value):
                values.append(int(value))
        elif lowered == "ratelimit":
            match = re.search(r"(?:^|[;,])\s*r\s*=\s*\"?(\d+)\"?(?:\s*[;,]|$)", value, re.IGNORECASE)
            if match:
                values.append(int(match.group(1)))
    return min(values) if values else None


def _retry_delay(value: str | None, attempt: int) -> float:
    if value:
        try:
            return min(30.0, max(0.0, float(value)))
        except ValueError:
            try:
                parsed = parsedate_to_datetime(value)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return min(30.0, max(0.0, (parsed - datetime.now(timezone.utc)).total_seconds()))
            except (TypeError, ValueError, OverflowError):
                pass
    return min(4.0, 0.5 * (2 ** (attempt - 1)))


class LimitlessApiClient:
    """GET JSON sans clé, bornés; arrêt au premier refus optionnel en campagne."""

    def __init__(
        self,
        max_requests: int,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        interval: float = 0.25,
        opener: Any | None = None,
        sleep: Callable[[float], None] = time.sleep,
        stop_on_access_denial: bool = False,
        max_response_bytes: int = MAX_JSON_BYTES,
        cancelled: Callable[[], bool] | None = None,
    ) -> None:
        if not 1 <= max_requests <= 100:
            raise MetaError("--max-requests doit être compris entre 1 et 100.")
        self.max_requests = max_requests
        if not 1 <= max_response_bytes <= MAX_JSON_BYTES:
            raise MetaError('Limite de réponse Limitless invalide.')
        self.max_response_bytes = max_response_bytes
        self.cancelled = cancelled
        self.bytes_received = 0
        self.timeout = timeout
        self.interval = max(0.0, interval)
        self.requests_made = 0
        self.stop_on_access_denial = stop_on_access_denial
        self.blocked_reason: str | None = None
        self.last_rate_limit: dict[str, str] = {}
        self.provider_remaining: int | None = None
        self._sleep = sleep
        self._opener = opener or build_opener(_SafeRedirectHandler(self._before_redirect))

    @property
    def remaining(self) -> int:
        return self.max_requests - self.requests_made

    def _reserve_get(self) -> None:
        """Débite un GET avant transmission, y compris un suivi de redirection."""
        if self.cancelled and self.cancelled():
            self.blocked_reason = 'PUBLIC_RESEARCH_CANCELLED'
        if self.blocked_reason:
            raise MetaNetworkFailure(self.blocked_reason)
        if self.remaining <= 0:
            raise RequestBudgetExhausted("Budget de requêtes Limitless épuisé.")
        if self.provider_remaining == 0:
            raise ProviderRateLimitExhausted(
                "Limitless annonce un quota restant de 0; aucun GET additionnel n'a été envoyé."
            )
        if self.requests_made:
            self._sleep(self.interval)
        self.requests_made += 1

    def _before_redirect(self, headers: Any) -> None:
        announced_remaining = _rate_limit_remaining(headers or {})
        if announced_remaining is not None:
            self.provider_remaining = announced_remaining
        self._reserve_get()

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> tuple[Any, str]:
        url = _safe_api_url(path, params)
        attempt = 0
        while True:
            self._reserve_get()
            attempt += 1
            request = Request(url, method="GET", headers={"Accept": "application/json", "User-Agent": USER_AGENT})
            try:
                response = self._opener.open(request, timeout=self.timeout)
                try:
                    final_url = response.geturl()
                    try:
                        _validate_public_api_url(final_url)
                    except MetaError as exc:
                        raise MetaNetworkFailure(f"URL finale Limitless refusée: {exc}") from exc
                    self.last_rate_limit = {
                        key: value for key, value in response.headers.items()
                        if key.lower().startswith(("x-ratelimit", "ratelimit"))
                    }
                    announced_remaining = _rate_limit_remaining(response.headers)
                    if announced_remaining is not None:
                        self.provider_remaining = announced_remaining
                    length = response.headers.get("Content-Length")
                    if length:
                        try:
                            declared_length = int(length)
                        except ValueError as exc:
                            raise MetaError("Content-Length Limitless invalide.") from exc
                        if declared_length > self.max_response_bytes:
                            raise MetaError("Réponse Limitless trop volumineuse.")
                    if "json" not in (response.headers.get("Content-Type") or "").lower():
                        if self.stop_on_access_denial:
                            self.blocked_reason = "PUBLIC_SOURCE_NON_JSON_BLOCKED"
                        raise MetaError("Limitless n'a pas retourné du JSON.")
                    raw = response.read(self.max_response_bytes)
                    self.bytes_received += len(raw)
                finally:
                    response.close()
                if len(raw) >= self.max_response_bytes:
                    raise MetaError("Réponse Limitless trop volumineuse.")
                try:
                    return json.loads(raw.decode("utf-8")), final_url
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise MetaError("Réponse Limitless JSON tronquée ou malformée.") from exc
            except HTTPError as exc:
                if self.stop_on_access_denial and exc.code in {401, 403, 429}:
                    self.blocked_reason = f"PUBLIC_SOURCE_HTTP_{exc.code}_BLOCKED"
                    exc.close()
                    raise MetaNetworkFailure(self.blocked_reason) from exc
                announced_remaining = _rate_limit_remaining(exc.headers or {})
                if announced_remaining is not None:
                    self.provider_remaining = announced_remaining
                retryable = exc.code == 429 or 500 <= exc.code <= 599
                if retryable and attempt < 3 and self.remaining > 0 and self.provider_remaining != 0:
                    self._sleep(_retry_delay(exc.headers.get("Retry-After"), attempt))
                    continue
                if exc.code == 429 or self.provider_remaining == 0:
                    raise ProviderRateLimitExhausted(
                        "Limitless a refusé la requête selon son quota; le cache sain est conservé."
                    ) from exc
                raise MetaNetworkFailure(f"Limitless HTTP {exc.code}.") from exc
            except (URLError, TimeoutError, socket.timeout, OSError) as exc:
                if attempt < 3 and self.remaining > 0:
                    self._sleep(_retry_delay(None, attempt))
                    continue
                raise MetaNetworkFailure(f"Limitless inaccessible: {exc}.") from exc


def _text(value: Any, field: str, *, required: bool = False, maximum: int = 500) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or (required and not value.strip()):
        raise MetaError(f"Champ Limitless invalide: {field} doit être du texte.")
    cleaned = value.strip()
    if len(cleaned) > maximum:
        raise MetaError(f"Champ Limitless trop long: {field}.")
    return cleaned


def _identifier(value: Any, field: str) -> str:
    result = _text(value, field, required=True, maximum=128)
    assert result is not None
    if not _SAFE_ID.fullmatch(result):
        raise MetaError(f"Identifiant Limitless non sécuritaire: {field}.")
    return result


def _integer(value: Any, field: str, *, minimum: int = 0, maximum: int = 1_000_000, optional: bool = False) -> int | None:
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise MetaError(f"Champ Limitless invalide: {field} doit être un entier borné.")
    return value


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise MetaError(f"Champ Limitless invalide: {field} doit être booléen.")
    return value


def _datetime_utc(value: Any, field: str) -> str:
    raw = _text(value, field, required=True, maximum=64)
    assert raw is not None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise MetaError(f"Champ Limitless invalide: {field} n'est pas une date ISO.") from exc
    if parsed.tzinfo is None:
        raise MetaError(f"Champ Limitless invalide: {field} doit inclure un fuseau horaire.")
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _format_code(value: str) -> str:
    lowered = value.strip().lower()
    if lowered in _FORMATS:
        return _FORMATS[lowered]
    if not _SAFE_ID.fullmatch(value.strip().upper()):
        raise MetaError("Format Limitless invalide.")
    return value.strip().upper()


def _since(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise MetaError("--since doit être une date YYYY-MM-DD.") from exc


def _validated_games(payload: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if not isinstance(payload, list) or len(payload) > 100:
        raise MetaError("Réponse /games invalide ou non bornée.")
    validated: list[dict[str, Any]] = []
    ptcg: dict[str, Any] | None = None
    for item in payload:
        if not isinstance(item, dict):
            raise MetaError("Entrée /games invalide.")
        game_id = _identifier(item.get("id"), "game.id")
        formats = item.get("formats")
        platforms = item.get("platforms")
        if not isinstance(formats, dict) or not isinstance(platforms, dict):
            raise MetaError("Formats ou plateformes Limitless invalides.")
        row = {
            "id": game_id,
            "name": _text(item.get("name"), "game.name", required=True),
            "metagame": _boolean(item.get("metagame"), "game.metagame"),
            "formats": {str(k): str(v) for k, v in formats.items()},
            "platforms": {str(k): str(v) for k, v in platforms.items()},
        }
        validated.append(row)
        if game_id == "PTCG":
            ptcg = row
    if ptcg is None:
        raise MetaError("Le jeu PTCG est absent de /games.")
    return ptcg, validated


def _validated_tournament_briefs(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or len(payload) > 100:
        raise MetaError("Réponse /tournaments invalide ou non bornée.")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            raise MetaError("Tournoi Limitless invalide.")
        tournament_id = _identifier(item.get("id"), "tournament.id")
        if tournament_id in seen:
            continue
        seen.add(tournament_id)
        rows.append({
            "id": tournament_id,
            "game": _identifier(item.get("game"), "tournament.game"),
            "format": _identifier(item.get("format"), "tournament.format").upper(),
            "name": _text(item.get("name"), "tournament.name", required=True),
            "date": _datetime_utc(item.get("date"), "tournament.date"),
            "players": _integer(item.get("players"), "tournament.players"),
        })
    return rows


def _validated_details(payload: Any, expected_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or _identifier(payload.get("id"), "details.id") != expected_id:
        raise MetaError("Détails de tournoi incohérents.")
    phases = payload.get("phases")
    if not isinstance(phases, list) or len(phases) > 100:
        raise MetaError("Phases Limitless invalides.")
    validated_phases: list[dict[str, Any]] = []
    phase_ids: set[int] = set()
    for raw in phases:
        if not isinstance(raw, dict):
            raise MetaError("Phase Limitless invalide.")
        phase = _integer(raw.get("phase"), "phase.phase", maximum=10_000)
        assert phase is not None
        if phase in phase_ids:
            raise MetaError("Numéro de phase Limitless dupliqué.")
        phase_ids.add(phase)
        mode = str(raw.get("mode") or "UNKNOWN").upper()
        if mode not in {"BO1", "BO3", "BO5"}:
            mode = "UNKNOWN"
        validated_phases.append({
            "phase": phase,
            "type": _text(raw.get("type"), "phase.type", required=True, maximum=64),
            "rounds": _integer(raw.get("rounds"), "phase.rounds", maximum=10_000),
            "mode": mode,
        })
    special = payload.get("specialRules") or []
    banned = payload.get("bannedCards") or []
    if not isinstance(special, list) or not isinstance(banned, list) or len(special) > 1_000 or len(banned) > 10_000:
        raise MetaError("Règles personnalisées Limitless invalides.")
    provider_status = payload.get("status")
    return {
        "id": expected_id,
        "game": _identifier(payload.get("game"), "details.game"),
        "format": _identifier(payload.get("format"), "details.format").upper(),
        "name": _text(payload.get("name"), "details.name", required=True),
        "date": _datetime_utc(payload.get("date"), "details.date"),
        "players": _integer(payload.get("players"), "details.players"),
        "platform": _text(payload.get("platform"), "details.platform", maximum=128),
        "decklists": _boolean(payload.get("decklists"), "details.decklists"),
        "is_public": _boolean(payload.get("isPublic"), "details.isPublic"),
        "is_online": _boolean(payload.get("isOnline"), "details.isOnline"),
        "phases": validated_phases,
        "special_rules": [str(value)[:200] for value in special],
        "banned_count": len(banned),
        "provider_status": _text(provider_status, "details.status", maximum=64) if provider_status is not None else None,
    }


def _validated_standings(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or len(payload) > 100_000:
        raise MetaError("Classement Limitless invalide ou non borné.")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in payload:
        if not isinstance(raw, dict):
            raise MetaError("Entrée de classement Limitless invalide.")
        player = _identifier(raw.get("player"), "standing.player")
        if player in seen:
            raise MetaError("Participant dupliqué dans le classement Limitless.")
        seen.add(player)
        record = raw.get("record") or {}
        if not isinstance(record, dict):
            raise MetaError("Fiche de score Limitless invalide.")
        deck = raw.get("deck")
        archetype_id = archetype_name = None
        if deck is not None:
            if not isinstance(deck, dict):
                raise MetaError("Archétype Limitless invalide.")
            if deck.get("id") is not None:
                archetype_id = _identifier(deck.get("id"), "standing.deck.id")
                archetype_name = _text(deck.get("name"), "standing.deck.name", maximum=200)
        rows.append({
            "player": player,
            "placing": _integer(raw.get("placing"), "standing.placing", minimum=1, optional=True),
            "wins": _integer(record.get("wins"), "standing.record.wins", optional=True),
            "losses": _integer(record.get("losses"), "standing.record.losses", optional=True),
            "ties": _integer(record.get("ties"), "standing.record.ties", optional=True),
            "drop": _integer(raw.get("drop"), "standing.drop", optional=True),
            "archetype_id": archetype_id,
            "archetype_name": archetype_name,
        })
    return rows


def _validated_pairings(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list) or len(payload) > 500_000:
        raise MetaError("Appariements Limitless invalides ou non bornés.")
    rows: list[dict[str, Any]] = []
    for raw in payload:
        if not isinstance(raw, dict):
            raise MetaError("Appariement Limitless invalide.")
        player1 = _identifier(raw.get("player1"), "pairing.player1")
        player2 = raw.get("player2")
        if player2 in (None, ""):
            player2 = None
        else:
            player2 = _identifier(player2, "pairing.player2")
        winner = raw.get("winner")
        if isinstance(winner, str) and winner not in {"0", "-1"}:
            winner = _identifier(winner, "pairing.winner")
        elif winner not in (0, -1, "0", "-1", None):
            raise MetaError("Résultat d'appariement Limitless invalide.")
        rows.append({
            "phase": _integer(raw.get("phase"), "pairing.phase", maximum=10_000),
            "round": _integer(raw.get("round"), "pairing.round", maximum=100_000),
            "table": _integer(raw.get("table"), "pairing.table", maximum=1_000_000, optional=True),
            "match": _text(raw.get("match"), "pairing.match", maximum=128),
            "player1": player1,
            "player2": player2,
            "winner": winner,
        })
    return rows


def _privacy_key(connection: Any) -> bytes:
    row = connection.execute("SELECT value FROM metadata WHERE key='meta_privacy_key'").fetchone()
    if row is None:
        value = secrets.token_hex(32)
        connection.execute("INSERT INTO metadata(key, value) VALUES('meta_privacy_key', ?)", (value,))
    else:
        value = str(row[0])
    return bytes.fromhex(value)


def _participant_ref(key: bytes, tournament_id: str, player: str) -> str:
    return hmac.new(key, f"{tournament_id}\0{player}".encode("utf-8"), hashlib.sha256).hexdigest()


def _store_games(connection: Any, games: list[dict[str, Any]], source_url: str, fetched_at: str, payload: Any) -> None:
    payload_hash = _canonical_sha256(payload)
    with connection:
        for game in games:
            connection.execute(
                """INSERT INTO meta_games
                   (game_id, name, metagame, formats_json, platforms_json, source_url, fetched_at, payload_sha256)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(game_id) DO UPDATE SET name=excluded.name, metagame=excluded.metagame,
                     formats_json=excluded.formats_json, platforms_json=excluded.platforms_json,
                     source_url=excluded.source_url, fetched_at=excluded.fetched_at,
                     payload_sha256=excluded.payload_sha256""",
                (game["id"], game["name"], int(game["metagame"]),
                 json.dumps(game["formats"], sort_keys=True), json.dumps(game["platforms"], sort_keys=True),
                 source_url, fetched_at, payload_hash),
            )


def _save_tournament(
    connection: Any,
    details: dict[str, Any],
    standings: list[dict[str, Any]],
    pairings: list[dict[str, Any]],
    *,
    source_url: str,
    fetched_at: str,
    snapshot_hash: str,
) -> dict[str, int]:
    tournament_id = details["id"]
    connection.execute("BEGIN IMMEDIATE")
    try:
        key = _privacy_key(connection)
        connection.execute(
            """INSERT INTO meta_tournaments
               (tournament_id, name, date_utc, game, format, platform, is_online, is_public,
                provider_status, participant_count, decklists_enabled, special_rules_json,
                banned_cards_count, source_url, fetched_at, payload_sha256, snapshot_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'complete')
               ON CONFLICT(tournament_id) DO UPDATE SET
                 name=excluded.name, date_utc=excluded.date_utc, game=excluded.game,
                 format=excluded.format, platform=excluded.platform, is_online=excluded.is_online,
                 is_public=excluded.is_public, provider_status=excluded.provider_status,
                 participant_count=excluded.participant_count, decklists_enabled=excluded.decklists_enabled,
                 special_rules_json=excluded.special_rules_json, banned_cards_count=excluded.banned_cards_count,
                 source_url=excluded.source_url, fetched_at=excluded.fetched_at,
                 payload_sha256=excluded.payload_sha256, snapshot_status='complete'""",
            (tournament_id, details["name"], details["date"], details["game"], details["format"],
             details["platform"], int(details["is_online"]), int(details["is_public"]),
             details["provider_status"], details["players"], int(details["decklists"]),
             json.dumps(details["special_rules"], ensure_ascii=False, sort_keys=True), details["banned_count"],
             source_url, fetched_at, snapshot_hash),
        )
        connection.execute("DELETE FROM meta_matches WHERE tournament_id=?", (tournament_id,))
        connection.execute("DELETE FROM meta_placements WHERE tournament_id=?", (tournament_id,))
        connection.execute("DELETE FROM meta_phases WHERE tournament_id=?", (tournament_id,))
        phases = {phase["phase"]: phase for phase in details["phases"]}
        for pairing in pairings:
            phases.setdefault(pairing["phase"], {
                "phase": pairing["phase"], "type": "UNKNOWN", "rounds": pairing["round"], "mode": "UNKNOWN",
            })
        for phase in phases.values():
            connection.execute(
                "INSERT INTO meta_phases(tournament_id, phase, phase_type, rounds, mode) VALUES (?, ?, ?, ?, ?)",
                (tournament_id, phase["phase"], phase["type"], phase["rounds"], phase["mode"]),
            )
        refs: dict[str, str] = {}
        for row in standings:
            ref = _participant_ref(key, tournament_id, row["player"])
            refs[row["player"]] = ref
            connection.execute(
                """INSERT INTO meta_placements
                   (tournament_id, participant_ref, placing, wins, losses, ties, dropped_round,
                    archetype_id, archetype_name, archetype_published)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (tournament_id, ref, row["placing"], row["wins"], row["losses"], row["ties"], row["drop"],
                 row["archetype_id"], row["archetype_name"], int(row["archetype_id"] is not None)),
            )
        inserted = eligible = 0
        for row in pairings:
            p1 = refs.get(row["player1"])
            p2 = refs.get(row["player2"]) if row["player2"] else None
            reason = None
            outcome = "unknown"
            winner = row["winner"]
            if p2 is None:
                reason = "bye_or_automatic_loss"
            elif p1 is None or p2 is None:
                reason = "participant_missing_from_standings"
            elif winner in (0, "0"):
                outcome = "tie"
            elif winner in (-1, "-1"):
                outcome, reason = "double_loss", "double_loss"
            elif winner == row["player1"]:
                outcome = "p1"
            elif winner == row["player2"]:
                outcome = "p2"
            else:
                reason = "winner_not_in_pairing"
            is_eligible = reason is None
            location = row["match"] or (f"table:{row['table']}" if row["table"] is not None else "no-location")
            participants = sorted(value for value in (p1, p2) if value)
            match_key = hashlib.sha256(
                f"{tournament_id}|{row['phase']}|{row['round']}|{location}|{'|'.join(participants)}".encode("utf-8")
            ).hexdigest()
            connection.execute(
                """INSERT INTO meta_matches
                   (tournament_id, match_key, phase, round, table_number, match_label,
                    participant1_ref, participant2_ref, outcome, eligible, exclusion_reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(tournament_id, match_key) DO UPDATE SET
                     table_number=excluded.table_number, match_label=excluded.match_label,
                     participant1_ref=excluded.participant1_ref, participant2_ref=excluded.participant2_ref,
                     outcome=excluded.outcome, eligible=excluded.eligible,
                     exclusion_reason=excluded.exclusion_reason""",
                (tournament_id, match_key, row["phase"], row["round"], row["table"], row["match"],
                 p1, p2, outcome, int(is_eligible), reason),
            )
            inserted += 1
            eligible += int(is_eligible)
        connection.commit()
        return {"placements": len(standings), "matches": inserted, "eligible_matches": eligible}
    except Exception:
        connection.rollback()
        raise


def _sync_state(connection: Any, scope: str, source_url: str, state: str, *, payload: Any = None, error: str | None = None, requests_total: int = 0) -> None:
    now = utc_now()
    payload_hash = _canonical_sha256(payload) if payload is not None else None
    with connection:
        connection.execute(
            """INSERT INTO meta_sync_state
               (scope, source_url, state, fetched_at, payload_sha256, requests_total, last_error, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(scope) DO UPDATE SET source_url=excluded.source_url, state=excluded.state,
                 fetched_at=excluded.fetched_at, payload_sha256=excluded.payload_sha256,
                 requests_total=meta_sync_state.requests_total + excluded.requests_total,
                 last_error=excluded.last_error, updated_at=excluded.updated_at""",
            (scope, source_url, state, now if state == "success" else None, payload_hash,
             requests_total, error, now),
        )


def _ineligible_reason(
    details: dict[str, Any], *, format_code: str, platform_code: str, online: bool
) -> str | None:
    if details["game"] != "PTCG":
        return "game_not_ptcg"
    if details["format"] != format_code:
        return "format_mismatch_or_custom"
    if details["platform"] != platform_code:
        return "platform_mismatch"
    if details["is_online"] is not online:
        return "online_mismatch"
    if not details["is_public"]:
        return "private_or_unlisted"
    if (details["provider_status"] or "").upper() in {"CANCELLED", "CANCELED"}:
        return "cancelled"
    return None


def _mark_tournament_unavailable(connection: Any, tournament_id: str, *, public: bool) -> None:
    """Écarte un ancien snapshot des agrégats sans supprimer son historique."""
    with connection:
        connection.execute(
            """UPDATE meta_tournaments
               SET snapshot_status='partial', is_public=?, fetched_at=? WHERE tournament_id=?""",
            (int(public), utc_now(), tournament_id),
        )


def _discovery_scope(format_code: str, platform_code: str, online: bool) -> str:
    return f"discovery:PTCG:{format_code}:{platform_code}:{int(online)}"


def _discovery_tournament_scope(discovery_scope: str, tournament_id: str) -> str:
    return f"{discovery_scope}:tournament:{tournament_id}"


def _checkpoint_key(discovery_scope: str) -> str:
    return f"meta_checkpoint:{discovery_scope}"


def _load_discovery_checkpoint(connection: Any, discovery_scope: str) -> dict[str, Any]:
    row = connection.execute(
        "SELECT value FROM metadata WHERE key=?", (_checkpoint_key(discovery_scope),)
    ).fetchone()
    if row is None:
        return {"next_page": 1, "horizon_page": 0, "pending_page": None}
    try:
        payload = json.loads(str(row[0]))
        next_page = payload["next_page"]
        horizon_page = payload.get("horizon_page", 0)
        pending_page = payload.get("pending_page")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise MetaError("Checkpoint de découverte Limitless invalide; reprise refusée sans réinitialisation.") from exc
    if (
        isinstance(next_page, bool) or not isinstance(next_page, int)
        or not 1 <= next_page <= 1_000_000
        or isinstance(horizon_page, bool) or not isinstance(horizon_page, int)
        or not 0 <= horizon_page <= 1_000_000
        or (
            pending_page is not None
            and (
                isinstance(pending_page, bool) or not isinstance(pending_page, int)
                or not 1 <= pending_page <= 1_000_000
            )
        )
    ):
        raise MetaError("Checkpoint de découverte Limitless hors limites; reprise refusée.")
    return {"next_page": next_page, "horizon_page": horizon_page, "pending_page": pending_page}


def _save_discovery_checkpoint(
    connection: Any,
    discovery_scope: str,
    *,
    next_page: int,
    horizon_page: int,
    pending_page: int | None = None,
) -> None:
    payload = json.dumps(
        {
            "next_page": next_page,
            "horizon_page": horizon_page,
            "pending_page": pending_page,
            "updated_at": utc_now(),
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    with connection:
        connection.execute(
            """INSERT INTO metadata(key, value) VALUES(?, ?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
            (_checkpoint_key(discovery_scope), payload),
        )


def _known_discovery_ids(connection: Any, discovery_scope: str) -> set[str]:
    # Un snapshot complet est globalement fiable par ID. Un ancien snapshot partiel
    # peut toutefois être reconsidéré dans un autre contexte après correction source.
    imported = {
        str(row[0]) for row in connection.execute(
            "SELECT tournament_id FROM meta_tournaments WHERE snapshot_status='complete'"
        )
    }
    prefix = f"{discovery_scope}:tournament:"
    terminal_skips = {
        str(row[0])[len(prefix):]
        for row in connection.execute(
            """SELECT scope FROM meta_sync_state
               WHERE substr(scope, 1, ?) = ? AND state='skipped'""",
            (len(prefix), prefix),
        )
    }
    # Les anciennes lignes tournament:ID ne comportent aucun contexte et ne sont
    # volontairement pas interprétées comme des exclusions universelles.
    return imported | terminal_skips


def _refresh_candidates(
    connection: Any,
    *,
    format_code: str,
    platform_code: str,
    online: bool,
    discovery_scope: str,
    limit: int,
) -> list[str]:
    candidates: list[tuple[str, str]] = [
        (str(row[0]), str(row[1]))
        for row in connection.execute(
            """SELECT tournament_id, fetched_at FROM meta_tournaments
               WHERE game='PTCG' AND format=? AND platform=? AND is_online=?
               ORDER BY fetched_at, tournament_id LIMIT ?""",
            (format_code, platform_code, int(online), limit),
        )
    ]
    prefix = f"{discovery_scope}:tournament:"
    candidates.extend(
        (str(row[0])[len(prefix):], str(row[1]))
        for row in connection.execute(
            """SELECT scope, updated_at FROM meta_sync_state
               WHERE substr(scope, 1, ?) = ? AND state='skipped'
               ORDER BY updated_at, scope LIMIT ?""",
            (len(prefix), prefix, limit),
        )
    )
    ordered: list[str] = []
    seen: set[str] = set()
    for tournament_id, _ in sorted(candidates, key=lambda item: (item[1], item[0])):
        if tournament_id not in seen:
            seen.add(tournament_id)
            ordered.append(tournament_id)
    return ordered[:limit]


def sync_meta(
    db_path: Path,
    *,
    max_requests: int = 8,
    max_tournaments: int = 2,
    format: str = "standard",
    platform: str = "PTCGL",
    online: bool = True,
    mode: str = "discover",
    dry_run: bool = False,
    client: Any | None = None,
) -> dict[str, Any]:
    format_code = _format_code(format)
    platform_code = _identifier(platform.upper(), "platform")
    discovery_scope = _discovery_scope(format_code, platform_code, online)
    if not 1 <= max_tournaments <= 20:
        raise MetaError("--max-tournaments doit être compris entre 1 et 20.")
    if not 1 <= max_requests <= 100:
        raise MetaError("--max-requests doit être compris entre 1 et 100.")
    if mode not in {"discover", "refresh"}:
        raise MetaError("--mode doit être discover ou refresh.")
    if dry_run:
        schema_version = 0
        if db_path.is_file():
            connection = connect_readonly(db_path)
            try:
                schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            finally:
                connection.close()
        return {
            "database": str(db_path), "dry_run": True, "network_used": False, "writes": 0,
            "would_migrate": schema_version < SCHEMA_VERSION, "max_requests": max_requests,
            "max_tournaments": max_tournaments, "filters": {"game": "PTCG", "format": format_code,
            "platform": platform_code, "online": online},
            "mode": mode,
            "discovery_scope": discovery_scope,
            "planned_endpoints": ["/games", "/tournaments", "/tournaments/{id}/details",
                                  "/tournaments/{id}/standings", "/tournaments/{id}/pairings"],
            "forbidden_endpoint": "/games/{id}/decks",
        }
    connection = connect_writable(db_path)
    actual = client or LimitlessApiClient(max_requests)
    if actual.max_requests != max_requests:
        connection.close()
        raise MetaError("Le client injecté doit utiliser le même budget de requêtes.")
    imported: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    error: str | None = None
    stopped_reason = "nothing_pending"
    discovery = {
        "scope": discovery_scope,
        "start_page": 1,
        "next_page": 1,
        "horizon_page": 0,
        "pending_page": None,
        "head_page_replayed": False,
        "pages_requested": [],
    }
    try:
        initialize_schema(connection)
        checkpoint = _load_discovery_checkpoint(connection, discovery_scope)
        discovery.update({
            "start_page": checkpoint["next_page"],
            "next_page": checkpoint["next_page"],
            "horizon_page": checkpoint["horizon_page"],
            "pending_page": checkpoint["pending_page"],
        })
        endpoint_before = actual.requests_made
        games_payload, games_url = actual.get_json("/games")
        ptcg, games = _validated_games(games_payload)
        if format_code not in ptcg["formats"] or platform_code not in ptcg["platforms"]:
            raise MetaError("Format ou plateforme demandé absent des options PTCG publiées par /games.")
        fetched_at = utc_now()
        _store_games(connection, games, games_url, fetched_at, games_payload)
        _sync_state(
            connection, "games", games_url, "success", payload=games_payload,
            requests_total=actual.requests_made - endpoint_before,
        )

        def process_tournament(tournament_id: str, *, refreshing: bool) -> str:
            nonlocal error
            requests_before = actual.requests_made
            scoped_tournament = _discovery_tournament_scope(discovery_scope, tournament_id)
            try:
                endpoint_before = actual.requests_made
                details_payload, details_url = actual.get_json(f"/tournaments/{tournament_id}/details")
                details_requests = actual.requests_made - endpoint_before
                details = _validated_details(details_payload, tournament_id)
                reason = _ineligible_reason(
                    details, format_code=format_code, platform_code=platform_code, online=online
                )
                if reason:
                    if refreshing:
                        _mark_tournament_unavailable(
                            connection, tournament_id, public=bool(details["is_public"])
                        )
                    skipped.append({"tournament_id": tournament_id, "reason": reason})
                    _sync_state(
                        connection, scoped_tournament, details_url, "skipped",
                        payload=details_payload, error=reason,
                        requests_total=actual.requests_made - requests_before,
                    )
                    return "skipped"
                if actual.remaining < 2:
                    return "budget_exhausted"
                endpoint_before = actual.requests_made
                standings_payload, standings_url = actual.get_json(f"/tournaments/{tournament_id}/standings")
                standings_requests = actual.requests_made - endpoint_before
                standings = _validated_standings(standings_payload)
                if not standings:
                    if refreshing:
                        _mark_tournament_unavailable(connection, tournament_id, public=True)
                    skipped.append({"tournament_id": tournament_id, "reason": "incomplete_no_standings"})
                    _sync_state(
                        connection, scoped_tournament, details_url, "error",
                        payload=details_payload, error="incomplete_no_standings",
                        requests_total=actual.requests_made - requests_before,
                    )
                    return "skipped"
                if actual.remaining < 1:
                    return "budget_exhausted"
                endpoint_before = actual.requests_made
                pairings_payload, pairings_url = actual.get_json(f"/tournaments/{tournament_id}/pairings")
                pairings_requests = actual.requests_made - endpoint_before
                pairings = _validated_pairings(pairings_payload)
                snapshot_payload = {"details": details_payload, "standings": standings_payload, "pairings": pairings_payload}
                counts = _save_tournament(
                    connection, details, standings, pairings, source_url=details_url,
                    fetched_at=utc_now(), snapshot_hash=_canonical_sha256(snapshot_payload),
                )
                _sync_state(connection, f"tournament:{tournament_id}:details", details_url, "success",
                            payload=details_payload, requests_total=details_requests)
                _sync_state(connection, f"tournament:{tournament_id}:standings", standings_url, "success",
                            payload=standings_payload, requests_total=standings_requests)
                _sync_state(connection, f"tournament:{tournament_id}:pairings", pairings_url, "success",
                            payload=pairings_payload, requests_total=pairings_requests)
                _sync_state(connection, scoped_tournament, details_url, "success",
                            payload=snapshot_payload, requests_total=0)
                imported.append({"tournament_id": tournament_id, "details_url": details_url,
                                 "standings_url": standings_url, "pairings_url": pairings_url,
                                 "refreshed": refreshing, **counts})
                return "imported"
            except RequestBudgetExhausted:
                return "budget_exhausted"
            except ProviderRateLimitExhausted as exc:
                error = neutral_exception_code(exc, "LIMITLESS")
                _sync_state(connection, scoped_tournament,
                            f"{API_ORIGIN}{API_PREFIX}/tournaments/{tournament_id}", "error",
                            error=error, requests_total=actual.requests_made - requests_before)
                return "rate_limited"
            except (MetaError, MetaNetworkFailure) as exc:
                error = neutral_exception_code(exc, "LIMITLESS")
                _sync_state(connection, scoped_tournament,
                            f"{API_ORIGIN}{API_PREFIX}/tournaments/{tournament_id}", "error",
                            error=error, requests_total=actual.requests_made - requests_before)
                return "source_error"

        if mode == "refresh":
            candidates = _refresh_candidates(
                connection,
                format_code=format_code,
                platform_code=platform_code,
                online=online,
                discovery_scope=discovery_scope,
                limit=max_requests,
            )
            for tournament_id in candidates:
                if len(imported) >= max_tournaments:
                    stopped_reason = "max_tournaments"
                    break
                if actual.remaining < 1:
                    stopped_reason = "budget_exhausted"
                    break
                outcome = process_tournament(tournament_id, refreshing=True)
                if outcome in {"source_error", "rate_limited", "budget_exhausted"}:
                    stopped_reason = outcome
                    break
            else:
                stopped_reason = "refresh_batch_complete" if candidates else "nothing_pending"
        else:
            known_tournaments = _known_discovery_ids(connection, discovery_scope)
            seen_this_run: set[str] = set()
            limit = min(50, max(6, max_tournaments * 3))
            cursor_page = checkpoint["next_page"]
            progress_page = cursor_page
            queued_pages: list[int] = []
            pending_page = checkpoint["pending_page"]
            direct_page = pending_page
            if pending_page is None:
                if cursor_page > 1:
                    queued_pages.append(1)
                    overlap_page = max(2, cursor_page - 1)
                    if overlap_page != 1:
                        queued_pages.append(overlap_page)
                else:
                    progress_page = 1

            while True:
                if len(imported) >= max_tournaments:
                    stopped_reason = "max_tournaments"
                    break
                if actual.remaining < 1:
                    stopped_reason = "budget_exhausted"
                    break
                direct_scan = False
                if direct_page is not None:
                    page = direct_page
                    direct_page = None
                    direct_scan = True
                    advances_cursor = page >= cursor_page
                elif queued_pages:
                    page = queued_pages.pop(0)
                    advances_cursor = False
                    if page == 1:
                        discovery["head_page_replayed"] = True
                else:
                    page = progress_page
                    progress_page += 1
                    advances_cursor = True

                endpoint_before = actual.requests_made
                listing_payload, listing_url = actual.get_json(
                    "/tournaments", {"game": "PTCG", "format": format_code, "limit": limit, "page": page}
                )
                discovery["pages_requested"].append(page)
                discovery["horizon_page"] = max(int(discovery["horizon_page"]), page)
                page_briefs = _validated_tournament_briefs(listing_payload)
                _sync_state(
                    connection, f"{discovery_scope}:page:{page}", listing_url, "success",
                    payload=listing_payload, requests_total=actual.requests_made - endpoint_before,
                )
                page_complete = True
                for brief in page_briefs:
                    tournament_id = brief["id"]
                    if tournament_id in seen_this_run:
                        continue
                    seen_this_run.add(tournament_id)
                    if tournament_id in known_tournaments:
                        continue
                    if actual.remaining < 1:
                        stopped_reason = "budget_exhausted"
                        page_complete = False
                        break
                    outcome = process_tournament(tournament_id, refreshing=False)
                    if outcome in {"imported", "skipped"}:
                        known_tournaments.add(tournament_id)
                    if outcome == "imported" and len(imported) >= max_tournaments:
                        stopped_reason = "max_tournaments"
                        page_complete = False
                        break
                    if outcome in {"source_error", "rate_limited", "budget_exhausted"}:
                        stopped_reason = outcome
                        page_complete = False
                        break

                if page_complete and (advances_cursor or direct_scan):
                    next_page = int(discovery["next_page"])
                    if advances_cursor:
                        next_page = page if len(listing_payload) < limit else page + 1
                        discovery["next_page"] = next_page
                    discovery["pending_page"] = None
                    _save_discovery_checkpoint(
                        connection,
                        discovery_scope,
                        next_page=next_page,
                        horizon_page=int(discovery["horizon_page"]),
                    )
                if not page_complete:
                    if stopped_reason == "budget_exhausted":
                        discovery["pending_page"] = page
                        _save_discovery_checkpoint(
                            connection,
                            discovery_scope,
                            next_page=int(discovery["next_page"]),
                            horizon_page=int(discovery["horizon_page"]),
                            pending_page=page,
                        )
                    elif direct_scan:
                        discovery["pending_page"] = None
                        _save_discovery_checkpoint(
                            connection,
                            discovery_scope,
                            next_page=int(discovery["next_page"]),
                            horizon_page=int(discovery["horizon_page"]),
                        )
                    break
                if len(listing_payload) < limit:
                    if advances_cursor:
                        stopped_reason = "listing_exhausted"
                        break
                    # Une tête courte ne permet pas de conclure sur la frontière
                    # profonde déjà atteinte; la reprise scoped continue.
                if actual.remaining < 2:
                    stopped_reason = "budget_exhausted"
                    break
        if imported:
            with connection:
                connection.execute(
                    """INSERT INTO metadata(key, value) VALUES('meta_last_success_at', ?)
                       ON CONFLICT(key) DO UPDATE SET value=excluded.value""", (utc_now(),)
                )
        if error is None and stopped_reason == "nothing_pending":
            stopped_reason = "listing_exhausted"
        return {
            "database": str(db_path), "dry_run": False, "network_used": actual.requests_made > 0,
            "mode": mode,
            "filters": {"game": "PTCG", "format": format_code, "platform": platform_code, "online": online},
            "requests_made": actual.requests_made, "max_requests": max_requests,
            "rate_limit_headers": getattr(actual, "last_rate_limit", {}),
            "provider_remaining": getattr(actual, "provider_remaining", None),
            "discovery": discovery,
            "imported": imported, "skipped": skipped, "stopped_reason": stopped_reason, "error": error,
            "offline_available": bool(imported) or connection.execute("SELECT EXISTS(SELECT 1 FROM meta_tournaments)").fetchone()[0] == 1,
            "limitations": [
                "Échantillon de la Tournament Platform, pas tous les tournois mondiaux.",
                "Pagination mouvante non atomique; tête, chevauchement et horizon observé ne garantissent pas l'exhaustivité.",
                "Résultats descriptifs; aucune autorité normative de légalité.",
                "Pseudos, noms, pays et decklists ne sont pas conservés.",
            ],
        }
    except RequestBudgetExhausted:
        return {
            "database": str(db_path), "dry_run": False, "network_used": actual.requests_made > 0,
            "mode": mode,
            "filters": {"game": "PTCG", "format": format_code, "platform": platform_code, "online": online},
            "requests_made": actual.requests_made, "max_requests": max_requests,
            "rate_limit_headers": getattr(actual, "last_rate_limit", {}),
            "provider_remaining": getattr(actual, "provider_remaining", None),
            "discovery": discovery,
            "imported": imported, "skipped": skipped, "stopped_reason": "budget_exhausted", "error": None,
            "offline_available": connection.execute("SELECT EXISTS(SELECT 1 FROM meta_tournaments)").fetchone()[0] == 1,
            "limitations": ["Le budget explicite de GET est respecté; le dernier état sain demeure hors ligne."],
        }
    except ProviderRateLimitExhausted as exc:
        error = neutral_exception_code(exc, "LIMITLESS")
        _sync_state(
            connection, "sync:last", f"{API_ORIGIN}{API_PREFIX}", "error",
            error=error, requests_total=actual.requests_made,
        )
        return {
            "database": str(db_path), "dry_run": False, "network_used": actual.requests_made > 0,
            "mode": mode,
            "filters": {"game": "PTCG", "format": format_code, "platform": platform_code, "online": online},
            "requests_made": actual.requests_made, "max_requests": max_requests,
            "rate_limit_headers": getattr(actual, "last_rate_limit", {}),
            "provider_remaining": getattr(actual, "provider_remaining", None),
            "discovery": discovery,
            "imported": imported, "skipped": skipped, "stopped_reason": "rate_limited", "error": error,
            "offline_available": connection.execute("SELECT EXISTS(SELECT 1 FROM meta_tournaments)").fetchone()[0] == 1,
            "limitations": ["Le quota fournisseur annoncé est respecté; le dernier état sain demeure hors ligne."],
        }
    except (MetaError, MetaNetworkFailure) as exc:
        error = neutral_exception_code(exc, "LIMITLESS")
        _sync_state(
            connection, "sync:last", f"{API_ORIGIN}{API_PREFIX}", "error",
            error=error, requests_total=actual.requests_made,
        )
        return {
            "database": str(db_path), "dry_run": False, "network_used": actual.requests_made > 0,
            "mode": mode,
            "filters": {"game": "PTCG", "format": format_code, "platform": platform_code, "online": online},
            "requests_made": actual.requests_made, "max_requests": max_requests,
            "rate_limit_headers": getattr(actual, "last_rate_limit", {}),
            "provider_remaining": getattr(actual, "provider_remaining", None), "imported": imported,
            "discovery": discovery,
            "skipped": skipped, "stopped_reason": "source_error", "error": error,
            "offline_available": connection.execute("SELECT EXISTS(SELECT 1 FROM meta_tournaments)").fetchone()[0] == 1,
            "limitations": ["Le dernier état sain demeure consultable hors ligne."],
        }
    finally:
        connection.close()


def _filtered_tournaments(
    connection: Any, *, format: str, platform: str, online: bool, since: str | None,
    until: str | None = None, as_of: str | None = None
) -> tuple[list[Any], dict[str, Any]]:
    format_code = _format_code(format)
    platform_code = _identifier(platform.upper(), "platform")
    since_date = _since(since)
    where = ["game='PTCG'", "format=?", "platform=?", "is_online=?", "is_public=1", "snapshot_status='complete'"]
    params: list[Any] = [format_code, platform_code, int(online)]
    if since_date:
        where.append("date(date_utc) >= date(?)")
        params.append(since_date)
    for field, cutoff in (("date_utc",until),("date_utc",as_of),("fetched_at",as_of)):
        if cutoff is not None:
            where.append(f"date({field}) <= date(?)")
            params.append(_since(cutoff))
    rows = connection.execute(
        "SELECT * FROM meta_tournaments WHERE " + " AND ".join(where) + " ORDER BY date_utc DESC, tournament_id",
        params,
    ).fetchall()
    return rows, {"game": "PTCG", "format": format_code, "platform": platform_code,
                  "online": online, "since": since_date, "public_only": True,
                  "snapshot_status": "complete"}


def meta_window_comparison(db_path: Path, *, since: str, split: str, until: str, as_of: str,
                           format: str = 'standard', platform: str = 'PTCGL',
                           online: bool = True) -> dict[str, Any]:
    """Descriptive placement shares from two disjoint PUBLIC time windows.

    Reuses complete-snapshot/context filters and published archetype identities.
    Thresholds are disclosure policy, not statistical significance or causality.
    No new store, network, winrate, unique-player or personal-deck inference.
    """
    from datetime import timedelta
    dates = [_since(d) for d in (since,split,until,as_of)]
    if any(d is None for d in dates) or not since < split <= until <= as_of:
        raise MetaError('META_COMPARISON_WINDOW_INVALID')
    bounds = [(since,(date.fromisoformat(split)-timedelta(days=1)).isoformat()),(split,until)]
    windows = []
    connection = connect_readonly(db_path)
    try:
        for start,end in bounds:
            tournaments, filters = _filtered_tournaments(connection,format=format,platform=platform,
                online=online,since=start,until=end,as_of=as_of)
            # Complete snapshots of nonstandard/custom rules are not comparable.
            tournaments = [t for t in tournaments if t['special_rules_json']=='[]' and not t['banned_cards_count']]
            qualified = []
            for t in tournaments:
                try:
                    _validate_public_api_url(t['source_url'])
                    if (t['source_url']!=f'{API_ORIGIN}/api/tournaments/{t["tournament_id"]}/details'
                            or not re.fullmatch('[0-9a-f]{64}', t['payload_sha256'])):
                        continue
                    qualified.append(t)
                except (ValueError,TypeError):
                    continue
            ids = [t['tournament_id'] for t in qualified]
            counts, total, eligible, classifiable = {},0,0,0
            if ids:
                placeholders = ','.join('?' for _ in ids)
                for row in connection.execute(f'SELECT archetype_id, archetype_published, COUNT(*) n '
                        f'FROM meta_placements WHERE tournament_id IN ({placeholders}) '
                        'GROUP BY archetype_id, archetype_published',ids):
                    total += row['n']
                    if row['archetype_id'] is not None and row['archetype_published']:
                        counts[row['archetype_id']] = counts.get(row['archetype_id'],0)+row['n']
                eligible = connection.execute(f'SELECT COUNT(*) FROM meta_matches '
                    f'WHERE tournament_id IN ({placeholders}) AND eligible=1',ids).fetchone()[0]
                classifiable = connection.execute(f'''SELECT COUNT(*) FROM meta_matches m
                    JOIN meta_placements p1 ON p1.tournament_id=m.tournament_id AND p1.participant_ref=m.participant1_ref
                    JOIN meta_placements p2 ON p2.tournament_id=m.tournament_id AND p2.participant_ref=m.participant2_ref
                    WHERE m.tournament_id IN ({placeholders}) AND m.eligible=1
                    AND p1.archetype_id IS NOT NULL AND p2.archetype_id IS NOT NULL
                    AND p1.archetype_published=1 AND p2.archetype_published=1''',ids).fetchone()[0]
            classified = sum(counts.values())
            sources = [{'url':t['source_url'],'tournament_date':t['date_utc'],
                        'retrieved_at':t['fetched_at'],'version':t['payload_sha256']} for t in qualified]
            missing = []
            if len(ids)<2: missing.append('MIN_2_TOURNAMENTS_PER_WINDOW')
            if classified<10: missing.append('MIN_10_CLASSIFIED_PLACEMENTS_PER_WINDOW')
            if not total or classified/total<0.8: missing.append('MIN_80_PERCENT_CLASSIFICATION')
            if classifiable<5: missing.append('MIN_5_CLASSIFIABLE_MATCHES_PER_WINDOW')
            windows.append({'since':start,'until':end,'n_tournaments':len(ids),
                'n_placements':total,'n_classified':classified,'eligible_matches':eligible,
                'classifiable_matches':classifiable,'counts':counts,'sources':sources,'missing_data':missing})
        enough = all(not w['missing_data'] for w in windows)
        changes = []
        if enough:
            for archetype in sorted(set(windows[0]['counts']) | set(windows[1]['counts'])):
                a,b = (w['counts'].get(archetype,0)/w['n_classified'] for w in windows)
                changes.append({'archetype_id':archetype,'before_fraction':a,'after_fraction':b,
                                'change_percentage_points':(b-a)*100})
        return {'kind':'meta_window_comparison','as_of':as_of,'format':_format_code(format),
            'platform':platform.upper(),'online':online,'windows':windows,'supported':enough,'changes':changes,
            'missing_data':sorted({m for w in windows for m in w['missing_data']}),
            'classification':'provider_published_archetype_id_not_independently_verified',
            'observation_unit':'published_placement_not_unique_player','causal_improvement':'unknown',
            'limitations':['Selected published tournaments; incomplete/global representativeness unknown.',
                'Provider archetype definitions may drift; no causal or significance claim.',
                'Match counts refer to published matches, not individual games; no winrate computed.']}
    finally:
        connection.close()


def meta_tournaments(db_path: Path, *, format: str = "standard", platform: str = "PTCGL",
                     online: bool = True, since: str | None = None) -> dict[str, Any]:
    connection = connect_readonly(db_path)
    try:
        rows, filters = _filtered_tournaments(connection, format=format, platform=platform, online=online, since=since)
        return {
            "offline": True, "filters": filters, "count": len(rows),
            "tournaments": [
                {"tournament_id": row["tournament_id"], "name": row["name"], "date_utc": row["date_utc"],
                 "participants": row["participant_count"], "format": row["format"], "platform": row["platform"],
                 "online": bool(row["is_online"]), "provider_status": row["provider_status"],
                 "source_url": row["source_url"], "fetched_at": row["fetched_at"]}
                for row in rows
            ],
            "warning": "La plateforme Limitless n'est pas un recensement exhaustif des événements physiques.",
        }
    finally:
        connection.close()


def meta_archetypes(db_path: Path, *, format: str = "standard", platform: str = "PTCGL",
                    online: bool = True, since: str | None = None) -> dict[str, Any]:
    connection = connect_readonly(db_path)
    try:
        tournaments, filters = _filtered_tournaments(connection, format=format, platform=platform, online=online, since=since)
        ids = [row["tournament_id"] for row in tournaments]
        if not ids:
            return {"offline": True, "filters": filters, "n_tournaments": 0, "n_placements": 0,
                    "n_classified": 0, "classified_fraction": None, "archetypes": [],
                    "warning": "Aucun instantané admissible; aucun pourcentage calculé."}
        placeholders = ",".join("?" for _ in ids)
        total = int(connection.execute(
            f"SELECT COUNT(*) FROM meta_placements WHERE tournament_id IN ({placeholders})", ids
        ).fetchone()[0])
        rows = connection.execute(
            f"""SELECT archetype_id, MAX(archetype_name) AS archetype_name,
                       COUNT(*) AS n_placements, COUNT(DISTINCT tournament_id) AS n_tournaments,
                       AVG(placing) AS average_placing
                FROM meta_placements
                WHERE tournament_id IN ({placeholders}) AND archetype_id IS NOT NULL
                GROUP BY archetype_id ORDER BY n_placements DESC, archetype_id""", ids
        ).fetchall()
        classified = sum(int(row["n_placements"]) for row in rows)
        return {
            "offline": True, "filters": filters, "n_tournaments": len(ids), "n_placements": total,
            "n_classified": classified, "classified_fraction": classified / total if total else None,
            "archetypes": [dict(row) for row in rows],
            "sources": [{"tournament_id": row["tournament_id"], "url": row["source_url"],
                         "fetched_at": row["fetched_at"]} for row in tournaments],
            "warning": "Archétypes publiés seulement; top cut, absences et sélection des tournois peuvent biaiser l'échantillon.",
        }
    finally:
        connection.close()


def _wilson(wins: int, n: int) -> list[float] | None:
    if n <= 0:
        return None
    z = 1.959963984540054
    p = wins / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denominator
    return [max(0.0, center - margin), min(1.0, center + margin)]


def meta_matchups(db_path: Path, archetype: str, *, min_sample: int = 5,
                  format: str = "standard", platform: str = "PTCGL",
                  online: bool = True, since: str | None = None) -> dict[str, Any]:
    archetype_id = _identifier(archetype, "archetype")
    if not 1 <= min_sample <= 100_000:
        raise MetaError("--min-sample doit être compris entre 1 et 100000.")
    connection = connect_readonly(db_path)
    try:
        tournaments, filters = _filtered_tournaments(connection, format=format, platform=platform, online=online, since=since)
        ids = [row["tournament_id"] for row in tournaments]
        if not ids:
            return {"offline": True, "archetype": archetype_id, "filters": filters,
                    "min_sample": min_sample, "n_tournaments": 0, "matchups": [],
                    "excluded": {},
                    "excluded_scope": "tous les matchs des tournois filtrés, pas seulement l'archétype demandé",
                    "warning": "Aucun match admissible; aucun pourcentage calculé."}
        placeholders = ",".join("?" for _ in ids)
        rows = connection.execute(
            f"""SELECT m.tournament_id, m.outcome, p1.archetype_id AS a1,
                       p2.archetype_id AS a2, ph.phase_type, ph.mode
                FROM meta_matches m
                JOIN meta_placements p1 ON p1.tournament_id=m.tournament_id
                     AND p1.participant_ref=m.participant1_ref
                JOIN meta_placements p2 ON p2.tournament_id=m.tournament_id
                     AND p2.participant_ref=m.participant2_ref
                JOIN meta_phases ph ON ph.tournament_id=m.tournament_id AND ph.phase=m.phase
                WHERE m.tournament_id IN ({placeholders}) AND m.eligible=1
                  AND p1.archetype_id IS NOT NULL AND p2.archetype_id IS NOT NULL
                  AND (p1.archetype_id=? OR p2.archetype_id=?)""",
            [*ids, archetype_id, archetype_id],
        ).fetchall()
        groups: dict[tuple[str, str, str], dict[str, Any]] = {}
        for row in rows:
            self_is_p1 = row["a1"] == archetype_id
            opponent = row["a2"] if self_is_p1 else row["a1"]
            key = (str(opponent), str(row["phase_type"]), str(row["mode"]))
            group = groups.setdefault(key, {"opponent_archetype": opponent,
                                            "phase_type": row["phase_type"], "mode": row["mode"],
                                            "wins": 0, "losses": 0, "ties": 0,
                                            "tournaments": set()})
            if row["outcome"] == "tie":
                group["ties"] += 1
            elif (row["outcome"] == "p1") is self_is_p1:
                group["wins"] += 1
            else:
                group["losses"] += 1
            group["tournaments"].add(row["tournament_id"])
        results: list[dict[str, Any]] = []
        for group in groups.values():
            n = group["wins"] + group["losses"] + group["ties"]
            enough = n >= min_sample
            results.append({
                "opponent_archetype": group["opponent_archetype"], "phase_type": group["phase_type"],
                "mode": group["mode"], "wins": group["wins"], "losses": group["losses"],
                "ties": group["ties"], "n": n, "n_tournaments": len(group["tournaments"]),
                "observed_win_fraction": group["wins"] / n if enough and n else None,
                "wilson_95": _wilson(group["wins"], n) if enough else None,
                "warning": None if enough else f"Échantillon sous le minimum n={min_sample}; aucune proportion affichée.",
            })
        results.sort(key=lambda item: (-item["n"], str(item["opponent_archetype"]), str(item["mode"])))
        excluded_rows = connection.execute(
            f"""SELECT COALESCE(exclusion_reason, 'unclassified_archetype') AS reason, COUNT(*) AS n
                FROM meta_matches m
                LEFT JOIN meta_placements p1 ON p1.tournament_id=m.tournament_id AND p1.participant_ref=m.participant1_ref
                LEFT JOIN meta_placements p2 ON p2.tournament_id=m.tournament_id AND p2.participant_ref=m.participant2_ref
                WHERE m.tournament_id IN ({placeholders})
                  AND (m.eligible=0 OR p1.archetype_id IS NULL OR p2.archetype_id IS NULL)
                GROUP BY reason""", ids
        ).fetchall()
        return {
            "offline": True, "archetype": archetype_id, "filters": filters,
            "min_sample": min_sample, "n_tournaments": len(ids), "matchups": results,
            "excluded": {row["reason"]: row["n"] for row in excluded_rows},
            "excluded_scope": "tous les matchs des tournois filtrés, pas seulement l'archétype demandé",
            "observation_unit": "un match publié, pas une partie individuelle",
            "warning": "Estimation descriptive de la plateforme; elle ne prédit pas le rendement du joueur.",
        }
    finally:
        connection.close()


def meta_coverage(
    db_path: Path,
    *,
    format: str = "standard",
    platform: str = "PTCGL",
    online: bool = True,
    since: str | None = None,
    as_of: str | None = None,
) -> dict[str, Any]:
    """Mesure la couverture exploitable d'un contexte, sans calculer de winrate."""
    format_code = _format_code(format)
    platform_code = _identifier(platform.upper(), "platform")
    since_date = _since(since)
    cutoff = _since(as_of or datetime.now(timezone.utc).date().isoformat())
    connection = connect_readonly(db_path)
    try:
        version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if version < 7:
            raise MetaError("Cache Limitless non initialisé; exécuter 'meta sync'.")
        where = [
            "game='PTCG'", "format=?", "platform=?", "is_online=?", "is_public=1",
            "date(date_utc)<=date(?)", "date(fetched_at)<=date(?)"
        ]
        params: list[Any] = [format_code, platform_code, int(online), cutoff, cutoff]
        if since_date:
            where.append("date(date_utc) >= date(?)")
            params.append(since_date)
        tournaments = connection.execute(
            "SELECT * FROM meta_tournaments WHERE " + " AND ".join(where)
            + " ORDER BY date_utc, tournament_id",
            params,
        ).fetchall()
        complete = [row for row in tournaments if row["snapshot_status"] == "complete"]
        complete_ids = [str(row["tournament_id"]) for row in complete]
        snapshot_statuses: dict[str, int] = {}
        provider_statuses: dict[str, int] = {}
        for row in tournaments:
            snapshot = str(row["snapshot_status"])
            provider = str(row["provider_status"] or "unknown")
            snapshot_statuses[snapshot] = snapshot_statuses.get(snapshot, 0) + 1
            provider_statuses[provider] = provider_statuses.get(provider, 0) + 1
        placements_total = classified = matches_total = eligible = classifiable = 0
        modes: list[dict[str, Any]] = []
        excluded: dict[str, int] = {}
        if complete_ids:
            placeholders = ",".join("?" for _ in complete_ids)
            placements_total = int(connection.execute(
                f"SELECT COUNT(*) FROM meta_placements WHERE tournament_id IN ({placeholders})",
                complete_ids,
            ).fetchone()[0])
            classified = int(connection.execute(
                f"""SELECT COUNT(*) FROM meta_placements
                    WHERE tournament_id IN ({placeholders}) AND archetype_id IS NOT NULL""",
                complete_ids,
            ).fetchone()[0])
            matches_total = int(connection.execute(
                f"SELECT COUNT(*) FROM meta_matches WHERE tournament_id IN ({placeholders})",
                complete_ids,
            ).fetchone()[0])
            eligible = int(connection.execute(
                f"""SELECT COUNT(*) FROM meta_matches
                    WHERE tournament_id IN ({placeholders}) AND eligible=1""",
                complete_ids,
            ).fetchone()[0])
            classifiable = int(connection.execute(
                f"""SELECT COUNT(*)
                    FROM meta_matches m
                    JOIN meta_placements p1 ON p1.tournament_id=m.tournament_id
                         AND p1.participant_ref=m.participant1_ref
                    JOIN meta_placements p2 ON p2.tournament_id=m.tournament_id
                         AND p2.participant_ref=m.participant2_ref
                    WHERE m.tournament_id IN ({placeholders}) AND m.eligible=1
                      AND p1.archetype_id IS NOT NULL AND p2.archetype_id IS NOT NULL""",
                complete_ids,
            ).fetchone()[0])
            mode_rows = connection.execute(
                f"""SELECT ph.phase_type, ph.mode, COUNT(m.match_key) AS n_matches,
                           COUNT(DISTINCT ph.tournament_id) AS n_tournaments
                    FROM meta_phases ph
                    LEFT JOIN meta_matches m
                      ON m.tournament_id=ph.tournament_id AND m.phase=ph.phase
                    WHERE ph.tournament_id IN ({placeholders})
                    GROUP BY ph.phase_type, ph.mode
                    ORDER BY ph.phase_type, ph.mode""",
                complete_ids,
            ).fetchall()
            modes = [dict(row) for row in mode_rows]
            excluded_rows = connection.execute(
                f"""SELECT COALESCE(
                           CASE WHEN m.eligible=0 THEN m.exclusion_reason END,
                           CASE WHEN p1.archetype_id IS NULL OR p2.archetype_id IS NULL
                                THEN 'unclassified_archetype' END,
                           'unknown') AS reason,
                           COUNT(*) AS n
                    FROM meta_matches m
                    LEFT JOIN meta_placements p1
                      ON p1.tournament_id=m.tournament_id
                     AND p1.participant_ref=m.participant1_ref
                    LEFT JOIN meta_placements p2
                      ON p2.tournament_id=m.tournament_id
                     AND p2.participant_ref=m.participant2_ref
                    WHERE m.tournament_id IN ({placeholders})
                      AND (m.eligible=0 OR p1.archetype_id IS NULL OR p2.archetype_id IS NULL)
                    GROUP BY reason""",
                complete_ids,
            ).fetchall()
            excluded = {str(row["reason"]): int(row["n"]) for row in excluded_rows}
        date_values = [str(row["date_utc"]) for row in complete]
        fetched_values = [str(row["fetched_at"]) for row in tournaments]
        return {
            "offline": True,
            "context": {
                "game": "PTCG", "format": format_code, "platform": platform_code,
                "online": online, "since": since_date, "public_only": True,
                "as_of": cutoff, "future_events_and_future_observations_excluded": True,
            },
            "period": {
                "first_tournament_at": min(date_values) if date_values else None,
                "last_tournament_at": max(date_values) if date_values else None,
                "last_fetched_at": max(fetched_values) if fetched_values else None,
            },
            "tournaments": {
                "public_in_context": len(tournaments),
                "complete_snapshots": len(complete),
                "snapshot_statuses": snapshot_statuses,
                "provider_statuses": provider_statuses,
                "provider_finalization_interpretation": "unknown",
            },
            "placements": {
                "classified": classified,
                "denominator": placements_total,
                "ratio": round(classified / placements_total, 6) if placements_total else None,
            },
            "matches": {
                "eligible": eligible,
                "classifiable": classifiable,
                "denominator": matches_total,
                "eligible_ratio": round(eligible / matches_total, 6) if matches_total else None,
                "classifiable_ratio": (
                    round(classifiable / matches_total, 6) if matches_total else None
                ),
                "by_phase_and_mode": modes,
                "excluded": excluded,
            },
            "sources": [
                {
                    "tournament_id": row["tournament_id"],
                    "url": row["source_url"],
                    "fetched_at": row["fetched_at"],
                    "snapshot_status": row["snapshot_status"],
                }
                for row in tournaments
            ],
            "biases": [
                "Limitless Tournament Platform seulement; pas le métagame mondial.",
                "Les archétypes absents restent unknown et réduisent le ratio classifiable.",
                "Les top cuts, abandons, tournois sélectionnés et pairings publiés biaisent l'échantillon.",
                "Le statut fournisseur est exposé sans être interprété comme finalisation normative.",
            ],
            "trainer_hill": {
                "status": "BLOCKED_WITH_REASON",
                "reason": "Aucune API publique et condition d'automatisation autorisée vérifiées le 2026-10-13.",
            },
        }
    finally:
        connection.close()


def meta_status(db_path: Path) -> dict[str, Any]:
    if not db_path.is_file():
        return {"database": str(db_path), "offline": True, "schema_version": 0,
                "tournaments": 0, "placements": 0, "matches": 0, "last_success_at": None,
                "last_error": None, "ready": False}
    connection = connect_readonly(db_path)
    try:
        version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if version < 7:
            return {"database": str(db_path), "offline": True, "schema_version": version,
                    "tournaments": 0, "placements": 0, "matches": 0,
                    "last_success_at": None, "last_error": None, "ready": False}
        metadata = dict(connection.execute("SELECT key, value FROM metadata").fetchall())
        error = connection.execute(
            "SELECT last_error, updated_at FROM meta_sync_state WHERE state='error' ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        return {
            "database": str(db_path), "offline": True, "schema_version": version,
            "integrity": connection.execute("PRAGMA integrity_check").fetchone()[0],
            "tournaments": connection.execute("SELECT COUNT(*) FROM meta_tournaments").fetchone()[0],
            "placements": connection.execute("SELECT COUNT(*) FROM meta_placements").fetchone()[0],
            "matches": connection.execute("SELECT COUNT(*) FROM meta_matches").fetchone()[0],
            "eligible_matches": connection.execute("SELECT COUNT(*) FROM meta_matches WHERE eligible=1").fetchone()[0],
            "last_success_at": metadata.get("meta_last_success_at"),
            "last_error": ({"message": error[0], "at": error[1]} if error else None),
            "ready": True,
            "coverage": "Limitless Tournament Platform seulement; non exhaustive.",
        }
    finally:
        connection.close()
