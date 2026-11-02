"""Catalogue local TCGdex FR/EN, acquisition bornée et consultation hors ligne."""

from __future__ import annotations

import hashlib
import json
import re
import socket
import time
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pokemind.security import neutral_exception_code

from pokemind.database import (
    SCHEMA_VERSION,
    connect_readonly,
    connect_writable,
    initialize_schema,
    utc_now,
)
from pokemind.search import query_tokens


API_ORIGIN = "https://api.tcgdex.net"
API_VERSION = "v2"
LANGUAGES = ("en", "fr")
PAGE_SIZE = 100
MAX_JSON_BYTES = 8 * 1024 * 1024
DEFAULT_TIMEOUT = 15.0
USER_AGENT = "PokeMind/0.4 (catalogue local; https://github.com/Sd-tech-Sol/PokeMind)"
STATUS_VALUES = ("present", "absent", "not_fetched", "network_error")
SYNC_PHASES = ("index", "details", "balanced")
# TCGdex publie quelques identifiants contenant ``?`` (p. ex. exu-?). Ils
# restent sûrs une fois encodés en %3F dans un segment; slash, fragment,
# antislash et espaces demeurent interdits.
_SAFE_ID = re.compile(r"^[^/#\\\s]{1,128}$")


class CatalogError(ValueError):
    """Erreur contrôlée du catalogue."""


class RequestBudgetExhausted(CatalogError):
    """Le budget réseau explicite est épuisé."""


class BodyBudgetExhausted(RequestBudgetExhausted):
    """Le corps suivant ne peut être lu dans l'enveloppe restante."""


class ApiNotFound(CatalogError):
    """La ressource n'existe pas dans la langue demandée."""


class NetworkFailure(CatalogError):
    """Une requête a échoué sans réponse exploitable."""


def _validate_public_api_url(url: str) -> str:
    """Valide une URL TCGdex complète contre les seuls endpoints utilisés."""
    parsed = urlparse(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise CatalogError("Port TCGdex invalide.") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname != "api.tcgdex.net"
        or port is not None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise CatalogError(
            "Seul l'hôte HTTPS public exact de TCGdex est autorisé, sans identifiants ni fragment."
        )
    match = re.fullmatch(r"/v2/(en|fr)/(cards|sets)(?:/([^/]+))?", parsed.path)
    if match is None:
        raise CatalogError("Endpoint public TCGdex non autorisé.")
    identifier = match.group(3)
    if identifier is not None:
        decoded = unquote(identifier)
        if not _SAFE_ID.fullmatch(decoded):
            raise CatalogError("Identifiant d'endpoint TCGdex invalide.")
        if parsed.query:
            raise CatalogError("Paramètres inattendus sur un détail TCGdex.")
    elif parsed.query:
        pairs = parse_qsl(parsed.query, keep_blank_values=True)
        allowed = {
            "pagination:page",
            "pagination:itemsPerPage",
            "sort:field",
            "sort:order",
        }
        keys = [key for key, _ in pairs]
        if not pairs or any(key not in allowed for key in keys) or len(keys) != len(set(keys)):
            raise CatalogError("Paramètres de liste TCGdex non autorisés.")
        values = dict(pairs)
        for key in ("pagination:page", "pagination:itemsPerPage"):
            if key in values and not re.fullmatch(r"[1-9]\d{0,5}", values[key]):
                raise CatalogError("Pagination TCGdex invalide.")
        if "sort:field" in values and values["sort:field"] != "id":
            raise CatalogError("Champ de tri TCGdex non autorisé.")
        if "sort:order" in values and values["sort:order"] not in {"ASC", "DESC"}:
            raise CatalogError("Ordre de tri TCGdex invalide.")
    return url


class _SafeRedirectHandler(HTTPRedirectHandler):
    def __init__(self, before_redirect: Callable[[], None] | None = None) -> None:
        super().__init__()
        self._before_redirect = before_redirect

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        if req.get_method() != "GET":
            raise NetworkFailure("Redirection TCGdex refusée pour une méthode autre que GET.")
        try:
            _validate_public_api_url(newurl)
        except CatalogError as exc:
            raise NetworkFailure(f"Redirection TCGdex refusée: {exc}") from exc
        if self._before_redirect is not None:
            self._before_redirect()
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _canonical_sha256(payload: Any) -> str:
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _bounded_text(value: Any, field: str, *, required: bool = False, maximum: int = 2_000) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str) or (required and not value.strip()):
        raise CatalogError(f"Champ TCGdex invalide: {field} doit être du texte.")
    cleaned = value.strip()
    if len(cleaned) > maximum:
        raise CatalogError(f"Champ TCGdex trop long: {field}.")
    return cleaned


def _identifier(value: Any, field: str = "id") -> str:
    result = _bounded_text(value, field, required=True, maximum=128)
    assert result is not None
    if not _SAFE_ID.fullmatch(result):
        raise CatalogError(f"Identifiant TCGdex non sécuritaire: {field}.")
    return result


def _optional_int(value: Any, field: str, *, maximum: int = 100_000) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise CatalogError(f"Champ TCGdex invalide: {field} doit être un entier borné.")
    return value


def _json_list(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, list) or len(value) > 100:
        raise CatalogError(f"Champ TCGdex invalide: {field} doit être une liste bornée.")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _json_object_or_list(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, (dict, list)):
        raise CatalogError(f"Champ TCGdex invalide: {field}.")
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(encoded.encode("utf-8")) > 200_000:
        raise CatalogError(f"Champ TCGdex trop volumineux: {field}.")
    return encoded


def parse_languages(value: str | Iterable[str]) -> tuple[str, ...]:
    raw = value.split(",") if isinstance(value, str) else list(value)
    result: list[str] = []
    for item in raw:
        language = str(item).strip().lower()
        if language not in LANGUAGES:
            raise CatalogError("Langues permises: en, fr.")
        if language not in result:
            result.append(language)
    if not result:
        raise CatalogError("Choisir au moins une langue (en ou fr).")
    return tuple(result)


def _normalized_identity_name(value: Any) -> str:
    """Compare les noms sans dépendre de leur forme Unicode ou de la casse."""
    if not isinstance(value, str):
        return ""
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def _safe_api_url(path: str, params: dict[str, Any] | None = None) -> str:
    if not path.startswith("/") or "?" in path or "#" in path:
        raise CatalogError("Chemin d'API TCGdex invalide.")
    url = f"{API_ORIGIN}/{API_VERSION}{path}"
    if params:
        url += "?" + urlencode(params)
    return _validate_public_api_url(url)


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


class CatalogApiClient:
    """GET JSON bornés; les campagnes optent pour l'arrêt au premier refus."""

    def __init__(
        self,
        max_requests: int,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        interval: float = 0.2,
        opener: Any | None = None,
        sleep: Callable[[float], None] = time.sleep,
        stop_on_access_denial: bool = False,
        maximum_body_bytes: int | None = None,
        maximum_attempts: int = 3,
    ) -> None:
        if not 1 <= max_requests <= 1_000:
            raise CatalogError("--max-requests doit être compris entre 1 et 1000.")
        self.max_requests = max_requests
        self.timeout = timeout
        self.interval = max(0.0, interval)
        self.requests_made = 0
        self.stop_on_access_denial = stop_on_access_denial
        self.blocked_reason: str | None = None
        self.last_http_status: int | None = None
        if maximum_body_bytes is not None and (type(maximum_body_bytes) is not int or maximum_body_bytes < 1):
            raise CatalogError("TCGDEX_BODY_BUDGET_INVALID")
        if type(maximum_attempts) is not int or not 1 <= maximum_attempts <= 3:
            raise CatalogError("TCGDEX_ATTEMPT_LIMIT_INVALID")
        self.maximum_body_bytes = maximum_body_bytes
        self.body_bytes_read = 0
        self.maximum_attempts = maximum_attempts
        self._sleep = sleep
        self._opener = opener or build_opener(_SafeRedirectHandler(self._reserve_get))

    @property
    def remaining(self) -> int:
        return self.max_requests - self.requests_made

    def _reserve_get(self) -> None:
        """Débite un GET avant transmission, y compris un suivi de redirection."""
        if self.blocked_reason:
            raise NetworkFailure(self.blocked_reason)
        if self.remaining <= 0:
            raise RequestBudgetExhausted("Budget de requêtes TCGdex épuisé.")
        if self.maximum_body_bytes is not None and self.body_bytes_read >= self.maximum_body_bytes:
            raise BodyBudgetExhausted("TCGDEX_BODY_BUDGET_EXHAUSTED")
        if self.requests_made:
            self._sleep(self.interval)
        self.requests_made += 1

    def get_json(self, path: str, params: dict[str, Any] | None = None) -> tuple[Any, str]:
        url = _safe_api_url(path, params)
        attempt = 0
        while True:
            self._reserve_get()
            attempt += 1
            request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
            self.last_http_status = None
            try:
                response = self._opener.open(request, timeout=self.timeout)
                try:
                    status = getattr(response, "status", None)
                    if type(status) is int and 100 <= status <= 599:
                        self.last_http_status = status
                    final_url = response.geturl()
                    try:
                        _validate_public_api_url(final_url)
                    except CatalogError as exc:
                        raise NetworkFailure("TCGDEX_FINAL_URL_REJECTED: URL finale TCGdex refusée.") from exc
                    content_length = response.headers.get("Content-Length")
                    if content_length is not None:
                        try:
                            length = int(content_length)
                        except (TypeError, ValueError, OverflowError) as exc:
                            raise CatalogError("TCGDEX_RESPONSE_LENGTH_INVALID: Content-Length invalide.") from exc
                        if length < 0:
                            raise CatalogError("TCGDEX_RESPONSE_LENGTH_INVALID: Content-Length invalide.")
                        if length > MAX_JSON_BYTES:
                            raise CatalogError("TCGDEX_RESPONSE_TOO_LARGE: Réponse TCGdex trop volumineuse.")
                        if self.maximum_body_bytes is not None and length > self.maximum_body_bytes - self.body_bytes_read:
                            raise BodyBudgetExhausted("TCGDEX_BODY_BUDGET_EXHAUSTED")
                    media_type = (response.headers.get("Content-Type") or "").lower()
                    if "json" not in media_type:
                        if self.stop_on_access_denial:
                            self.blocked_reason = "PUBLIC_SOURCE_NON_JSON_BLOCKED"
                        raise CatalogError("TCGDEX_RESPONSE_NOT_JSON: TCGdex n'a pas retourné du JSON.")
                    if self.maximum_body_bytes is None:
                        raw = response.read(MAX_JSON_BYTES + 1)
                        self.body_bytes_read += len(raw)
                    else:
                        chunks, size = [], 0
                        while True:
                            available = self.maximum_body_bytes - self.body_bytes_read
                            # Known exact length can finish at the cap without a sentinel read.
                            if content_length is not None and size == length:
                                break
                            if available <= 0:
                                raise BodyBudgetExhausted("TCGDEX_BODY_BUDGET_EXHAUSTED")
                            chunk = response.read(min(65_536, available, MAX_JSON_BYTES + 1 - size))
                            self.body_bytes_read += len(chunk)
                            size += len(chunk)
                            chunks.append(chunk)
                            if not chunk or size > MAX_JSON_BYTES:
                                break
                        raw = b"".join(chunks)
                finally:
                    response.close()
                if len(raw) > MAX_JSON_BYTES:
                    raise CatalogError("TCGDEX_RESPONSE_TOO_LARGE: Réponse TCGdex trop volumineuse.")
                try:
                    return json.loads(raw.decode("utf-8")), final_url
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise CatalogError("TCGDEX_RESPONSE_JSON_INVALID: Réponse TCGdex JSON malformée.") from exc
            except HTTPError as exc:
                self.last_http_status = exc.code if type(exc.code) is int and 100 <= exc.code <= 599 else None
                try:
                    if self.stop_on_access_denial and exc.code in {401, 403, 429}:
                        self.blocked_reason = f"PUBLIC_SOURCE_HTTP_{exc.code}_BLOCKED"
                        raise NetworkFailure(self.blocked_reason) from exc
                    if exc.code == 404:
                        raise ApiNotFound("TCGDEX_HTTP_404: Ressource TCGdex absente.") from exc
                    retryable = exc.code == 429 or 500 <= exc.code <= 599
                    if retryable and attempt < self.maximum_attempts and self.requests_made < self.max_requests:
                        self._sleep(_retry_delay(exc.headers.get("Retry-After"), attempt))
                        continue
                    raise NetworkFailure(f"TCGDEX_HTTP_{self.last_http_status or 'UNKNOWN'}") from exc
                finally:
                    exc.close()
            except (URLError, TimeoutError, socket.timeout, OSError) as exc:
                if attempt < self.maximum_attempts and self.requests_made < self.max_requests:
                    self._sleep(_retry_delay(None, attempt))
                    continue
                raise NetworkFailure("TCGDEX_NETWORK_UNAVAILABLE: TCGdex inaccessible.") from exc


@dataclass(frozen=True, slots=True)
class _SetRecord:
    tcgdex_id: str
    name: str
    card_count_total: int | None
    card_count_official: int | None
    series_id: str | None = None
    release_date: str | None = None
    tcg_online_code: str | None = None
    abbreviation_official: str | None = None
    abbreviation_localized: str | None = None


@dataclass(frozen=True, slots=True)
class _CardBrief:
    tcgdex_id: str
    local_id: str
    name: str


def _counts(payload: dict[str, Any]) -> tuple[int | None, int | None]:
    value = payload.get("cardCount")
    if value is None:
        return None, None
    if not isinstance(value, dict):
        raise CatalogError("Champ TCGdex invalide: cardCount.")
    return (
        _optional_int(value.get("total"), "cardCount.total"),
        _optional_int(value.get("official"), "cardCount.official"),
    )


def _set_record(payload: Any, *, expected_id: str | None = None) -> _SetRecord:
    if not isinstance(payload, dict):
        raise CatalogError("Objet d'extension TCGdex invalide.")
    tcgdex_id = _identifier(payload.get("id"))
    if expected_id is not None and tcgdex_id != expected_id:
        raise CatalogError("TCGdex a retourné une autre extension que celle demandée.")
    name = _bounded_text(payload.get("name"), "name", required=True, maximum=500)
    assert name is not None
    total, official = _counts(payload)
    serie = payload.get("serie")
    if serie is not None and not isinstance(serie, dict):
        raise CatalogError("Champ TCGdex invalide: serie.")
    abbreviation = payload.get("abbreviation")
    if abbreviation is not None and not isinstance(abbreviation, dict):
        raise CatalogError("Champ TCGdex invalide: abbreviation.")
    return _SetRecord(
        tcgdex_id=tcgdex_id,
        name=name,
        card_count_total=total,
        card_count_official=official,
        series_id=_bounded_text((serie or {}).get("id"), "serie.id", maximum=128),
        release_date=_bounded_text(payload.get("releaseDate"), "releaseDate", maximum=40),
        tcg_online_code=_bounded_text(payload.get("tcgOnline"), "tcgOnline", maximum=40),
        abbreviation_official=_bounded_text((abbreviation or {}).get("official"), "abbreviation.official", maximum=40),
        abbreviation_localized=_bounded_text((abbreviation or {}).get("localized"), "abbreviation.localized", maximum=40),
    )


def _card_brief(payload: Any) -> _CardBrief:
    if not isinstance(payload, dict):
        raise CatalogError("Objet carte TCGdex invalide.")
    tcgdex_id = _identifier(payload.get("id"))
    local_id = _bounded_text(payload.get("localId"), "localId", required=True, maximum=80)
    name = _bounded_text(payload.get("name"), "name", required=True, maximum=500)
    assert local_id is not None and name is not None
    return _CardBrief(tcgdex_id, local_id, name)


def _validated_list(
    payload: Any, parser: Callable[[Any], Any], kind: str, *, max_items: int = PAGE_SIZE
) -> list[Any]:
    if not isinstance(payload, list) or len(payload) > max_items:
        raise CatalogError(f"Page TCGdex {kind} invalide ou trop grande.")
    return [parser(item) for item in payload]


def _upsert_set_brief(
    connection: Any, record: _SetRecord, language: str, source_url: str, retrieved_at: str
) -> tuple[bool, bool]:
    name_column = "name_en" if language == "en" else "name_fr"
    source_column = "source_url_en" if language == "en" else "source_url_fr"
    retrieved_column = "retrieved_at_en" if language == "en" else "retrieved_at_fr"
    hash_column = "brief_sha256_en" if language == "en" else "brief_sha256_fr"
    stale_column = "detail_stale_en" if language == "en" else "detail_stale_fr"
    brief_hash = _canonical_sha256({
        "id": record.tcgdex_id,
        "name": record.name,
        "cardCount": {
            "total": record.card_count_total,
            "official": record.card_count_official,
        },
    })
    current = connection.execute(
        f"SELECT {name_column}, card_count_total, card_count_official, {hash_column} "
        "FROM catalog_sets WHERE tcgdex_id=?",
        (record.tcgdex_id,),
    ).fetchone()
    is_new = current is None
    old_hash = None
    if current is not None:
        old_hash = current[hash_column] or _canonical_sha256({
            "id": record.tcgdex_id,
            "name": current[name_column],
            "cardCount": {
                "total": current["card_count_total"],
                "official": current["card_count_official"],
            },
        })
    changed = current is not None and old_hash != brief_hash
    connection.execute(
        f"""INSERT INTO catalog_sets
            (tcgdex_id, {name_column}, card_count_total, card_count_official,
             discovered_at, updated_at, {source_column}, {retrieved_column}, {hash_column})
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(tcgdex_id) DO UPDATE SET
                {name_column}=excluded.{name_column},
                card_count_total=COALESCE(excluded.card_count_total, catalog_sets.card_count_total),
                card_count_official=COALESCE(excluded.card_count_official, catalog_sets.card_count_official),
                updated_at=excluded.updated_at,
                {source_column}=excluded.{source_column},
                {retrieved_column}=excluded.{retrieved_column},
                {hash_column}=excluded.{hash_column},
                {stale_column}=CASE WHEN catalog_sets.{hash_column} IS NOT NULL
                                         AND catalog_sets.{hash_column} <> excluded.{hash_column}
                                    THEN 1 ELSE catalog_sets.{stale_column} END""",
        (
            record.tcgdex_id,
            record.name,
            record.card_count_total,
            record.card_count_official,
            retrieved_at,
            retrieved_at,
            source_url,
            retrieved_at,
            brief_hash,
        ),
    )
    return is_new, changed


def _upsert_card_brief(
    connection: Any, record: _CardBrief, language: str, source_url: str, retrieved_at: str
) -> tuple[bool, bool]:
    hash_column = "brief_sha256_en" if language == "en" else "brief_sha256_fr"
    stale_column = "detail_stale_en" if language == "en" else "detail_stale_fr"
    brief_hash = _canonical_sha256({
        "id": record.tcgdex_id,
        "localId": record.local_id,
        "name": record.name,
    })
    current = connection.execute(
        f"""SELECT p.local_id, p.{hash_column}, t.name
            FROM catalog_printings p
            LEFT JOIN catalog_translations t
              ON t.printing_id=p.tcgdex_id AND t.language=?
            WHERE p.tcgdex_id=?""",
        (language, record.tcgdex_id),
    ).fetchone()
    is_new = current is None
    old_hash = None
    if current is not None:
        old_hash = current[hash_column] or _canonical_sha256({
            "id": record.tcgdex_id,
            "localId": current["local_id"],
            "name": current["name"],
        })
    changed = current is not None and old_hash != brief_hash
    connection.execute(
        """INSERT INTO catalog_printings
           (tcgdex_id, local_id, discovered_at, updated_at, brief_source_url,
            brief_retrieved_at, brief_sha256_en, brief_sha256_fr)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(tcgdex_id) DO UPDATE SET
              local_id=excluded.local_id, updated_at=excluded.updated_at,
              brief_source_url=excluded.brief_source_url,
              brief_retrieved_at=excluded.brief_retrieved_at,
              {hash_column}=excluded.{hash_column},
              {stale_column}=CASE WHEN catalog_printings.{hash_column} IS NOT NULL
                                       AND catalog_printings.{hash_column} <> excluded.{hash_column}
                                  THEN 1 ELSE catalog_printings.{stale_column} END""".format(
            hash_column=hash_column, stale_column=stale_column
        ),
        (
            record.tcgdex_id,
            record.local_id,
            retrieved_at,
            retrieved_at,
            source_url,
            retrieved_at,
            brief_hash if language == "en" else None,
            brief_hash if language == "fr" else None,
        ),
    )
    detail_url = _safe_api_url(
        f"/{language}/cards/{quote(record.tcgdex_id, safe='%!._-')}"
    )
    connection.execute(
        """INSERT INTO catalog_translations
           (printing_id, language, status, name, source_url)
           VALUES (?, ?, 'not_fetched', ?, ?)
           ON CONFLICT(printing_id, language) DO UPDATE SET
              name=excluded.name,
              source_url=excluded.source_url,
              status=CASE WHEN catalog_translations.status IN ('present', 'absent')
                          THEN catalog_translations.status ELSE 'not_fetched' END,
              last_error=CASE WHEN catalog_translations.status IN ('present', 'absent')
                              THEN catalog_translations.last_error ELSE NULL END""",
        (record.tcgdex_id, language, record.name, detail_url),
    )
    return is_new, changed


def _sync_state(connection: Any, scope: str) -> dict[str, Any]:
    row = connection.execute(
        """SELECT next_page, completed, end_candidate_page, started_at, completed_at
           FROM catalog_sync_state WHERE scope = ?""",
        (scope,),
    ).fetchone()
    if row is None:
        return {
            "next_page": 1,
            "completed": False,
            "end_candidate_page": None,
            "started_at": None,
            "completed_at": None,
        }
    return {
        "next_page": int(row["next_page"]),
        "completed": bool(row["completed"]),
        "end_candidate_page": row["end_candidate_page"],
        "started_at": row["started_at"],
        "completed_at": row["completed_at"],
    }


def _page_transition(page: int, item_count: int, end_candidate_page: int | None) -> tuple[int, bool, int | None]:
    """Confirme la fin par une page vide suivant une page abrégée."""
    if item_count == PAGE_SIZE:
        return page + 1, False, None
    if end_candidate_page is not None and page > end_candidate_page and item_count == 0:
        return page + 1, True, end_candidate_page
    return page + 1, False, page


def _save_sync_state(
    connection: Any,
    scope: str,
    *,
    next_page: int,
    completed: bool,
    end_candidate_page: int | None,
    timestamp: str,
    request_attempts: int,
) -> None:
    connection.execute(
        """INSERT INTO catalog_sync_state
           (scope, next_page, completed, requests_total, end_candidate_page,
            started_at, completed_at, last_success_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(scope) DO UPDATE SET
              next_page=excluded.next_page, completed=excluded.completed,
               requests_total=catalog_sync_state.requests_total + excluded.requests_total,
               end_candidate_page=excluded.end_candidate_page,
               started_at=COALESCE(catalog_sync_state.started_at, excluded.started_at),
               completed_at=excluded.completed_at,
              last_success_at=excluded.last_success_at, last_error=NULL,
              updated_at=excluded.updated_at""",
        (
            scope,
            next_page,
            int(completed),
            request_attempts,
            end_candidate_page,
            timestamp,
            timestamp if completed else None,
            timestamp,
            timestamp,
        ),
    )


def _refresh_state(connection: Any, scope: str, timestamp: str) -> dict[str, Any]:
    row = connection.execute(
        """SELECT next_page, in_progress, end_candidate_page, head_probe_done,
                  cycle_started_at, last_completed_at
           FROM catalog_refresh_state WHERE scope=?""",
        (scope,),
    ).fetchone()
    if row is None or not bool(row["in_progress"]):
        connection.execute(
            """INSERT INTO catalog_refresh_state
               (scope, next_page, in_progress, end_candidate_page, head_probe_done,
                cycle_started_at, requests_total, pages_scanned_current,
                items_seen_current, new_items_current, changed_items_current, updated_at)
               VALUES (?, 1, 1, NULL, 0, ?, 0, 0, 0, 0, 0, ?)
               ON CONFLICT(scope) DO UPDATE SET
                  next_page=1, in_progress=1, end_candidate_page=NULL,
                  head_probe_done=0, cycle_started_at=excluded.cycle_started_at,
                  pages_scanned_current=0, items_seen_current=0,
                  new_items_current=0, changed_items_current=0,
                  last_error=NULL, updated_at=excluded.updated_at""",
            (scope, timestamp, timestamp),
        )
        return {
            "next_page": 1,
            "in_progress": True,
            "end_candidate_page": None,
            "head_probe_done": False,
            "cycle_started_at": timestamp,
            "last_completed_at": row["last_completed_at"] if row is not None else None,
        }
    return {
        "next_page": int(row["next_page"]),
        "in_progress": True,
        "end_candidate_page": row["end_candidate_page"],
        "head_probe_done": bool(row["head_probe_done"]),
        "cycle_started_at": row["cycle_started_at"],
        "last_completed_at": row["last_completed_at"],
    }


def _save_refresh_state(
    connection: Any,
    scope: str,
    *,
    next_page: int,
    completed: bool,
    end_candidate_page: int | None,
    head_probe_done: bool,
    timestamp: str,
    item_count: int,
    new_items: int,
    changed_items: int,
    request_attempts: int,
) -> None:
    connection.execute(
        """UPDATE catalog_refresh_state SET
              next_page=?, in_progress=?, end_candidate_page=?, head_probe_done=?,
              last_completed_at=CASE WHEN ? THEN ? ELSE last_completed_at END,
              requests_total=requests_total + ?,
              pages_scanned_current=pages_scanned_current + 1,
              items_seen_current=items_seen_current + ?,
              new_items_current=new_items_current + ?,
              changed_items_current=changed_items_current + ?,
              last_success_at=?, last_error=NULL, updated_at=?
           WHERE scope=?""",
        (
            next_page,
            int(not completed),
            end_candidate_page,
            int(head_probe_done),
            int(completed),
            timestamp,
            request_attempts,
            item_count,
            new_items,
            changed_items,
            timestamp,
            timestamp,
            scope,
        ),
    )


def _sync_index_page(
    connection: Any,
    client: CatalogApiClient,
    kind: str,
    language: str,
    *,
    refresh: bool = False,
    allow_head_probe: bool = False,
) -> dict[str, Any] | None:
    scope = f"{kind}:{language}"
    timestamp = utc_now()
    probe = False
    if refresh:
        state = _refresh_state(connection, scope, timestamp)
        page = int(state["next_page"])
        if allow_head_probe and page > 1 and not state["head_probe_done"]:
            page = 1
            probe = True
    else:
        state = _sync_state(connection, scope)
        if state["completed"]:
            return None
        page = int(state["next_page"])
    params: dict[str, Any] = {
        "pagination:page": page,
        "pagination:itemsPerPage": PAGE_SIZE,
    }
    if refresh:
        params.update({"sort:field": "id", "sort:order": "ASC"})
    requests_before = client.requests_made
    payload, source_url = client.get_json(
        f"/{language}/{kind}",
        params,
    )
    request_attempts = client.requests_made - requests_before
    was_probe = probe
    parser = _set_record if kind == "sets" else _card_brief
    records = _validated_list(payload, parser, kind)
    retrieved_at = utc_now()
    new_items = 0
    changed_items = 0
    with connection:
        for record in records:
            if kind == "sets":
                is_new, changed = _upsert_set_brief(
                    connection, record, language, source_url, retrieved_at
                )
            else:
                is_new, changed = _upsert_card_brief(
                    connection, record, language, source_url, retrieved_at
                )
            new_items += int(is_new)
            changed_items += int(changed)
        drift = False
        if refresh and probe:
            from pokemind.catalog_snapshots import head_matches
            drift = not head_matches(connection, scope, "refresh", [r.tcgdex_id for r in records])
            if drift:
                # Resume from this newly observed head. Never join a changed
                # first page to an older tail and report a complete denominator.
                state["next_page"] = 2
                state["end_candidate_page"] = 1 if len(records) < PAGE_SIZE else None
                probe = False
        if refresh and probe:
            next_page = int(state["next_page"])
            is_complete = False
            end_candidate = state["end_candidate_page"]
            head_probe_done = True
        else:
            next_page, is_complete, end_candidate = _page_transition(
                page, len(records), None if drift else state["end_candidate_page"]
            )
            head_probe_done = drift or bool(state.get("head_probe_done", False))
        if refresh:
            _save_refresh_state(
                connection,
                scope,
                next_page=next_page,
                completed=is_complete,
                end_candidate_page=end_candidate,
                head_probe_done=head_probe_done,
                timestamp=retrieved_at,
                item_count=len(records),
                new_items=new_items,
                changed_items=changed_items,
                request_attempts=request_attempts,
            )
        else:
            _save_sync_state(
                connection,
                scope,
                next_page=next_page,
                completed=is_complete,
                end_candidate_page=end_candidate,
                timestamp=retrieved_at,
                request_attempts=request_attempts,
            )
        if not probe:
            from pokemind.catalog_snapshots import record_page
            record_page(connection, scope, "refresh" if refresh else "discovery", page,
                        [r.tcgdex_id for r in records], completed=is_complete, timestamp=retrieved_at)
    return {
        "scope": scope,
        "mode": "refresh" if refresh else "discovery",
        "page": page,
        "probe": was_probe,
        "pagination_drift_restarted": drift,
        "items": len(records),
        "new_items": new_items,
        "changed_items": changed_items,
        "completed": is_complete,
        "end_confirmation_pending": not is_complete and end_candidate is not None,
    }


def _pending_set(
    connection: Any,
    language: str,
    *,
    recheck_absent: bool = False,
    exclude_ids: set[str] | None = None,
) -> str | None:
    column = "detail_status_en" if language == "en" else "detail_status_fr"
    stale_column = "detail_stale_en" if language == "en" else "detail_stale_fr"
    statuses = "'not_fetched', 'network_error'" + (", 'absent'" if recheck_absent else "")
    excluded = sorted(exclude_ids or set())
    exclude_clause = ""
    if excluded:
        exclude_clause = " AND tcgdex_id NOT IN (" + ",".join("?" for _ in excluded) + ")"
    absent_guard = "" if recheck_absent else f" AND {column} <> 'absent'"
    row = connection.execute(
        f"""SELECT tcgdex_id FROM catalog_sets
            WHERE ({column} IN ({statuses}) OR {stale_column}=1)
              {absent_guard}{exclude_clause}
            ORDER BY CASE {column}
                       WHEN 'not_fetched' THEN 0 WHEN 'network_error' THEN 1
                       WHEN 'absent' THEN 2 ELSE 3 END,
                     tcgdex_id LIMIT 1""",
        excluded,
    ).fetchone()
    return str(row[0]) if row else None


def _pending_card(
    connection: Any,
    language: str,
    *,
    recheck_absent: bool = False,
    priority_ids: set[str] | None = None,
    standard_priority_ids: set[str] | None = None,
    exclude_ids: set[str] | None = None,
) -> str | None:
    statuses = ["not_fetched", "network_error"]
    if recheck_absent:
        statuses.append("absent")
    stale_column = "detail_stale_en" if language == "en" else "detail_stale_fr"
    placeholders = ",".join("?" for _ in statuses)
    priority_ids = priority_ids or set()
    standard_priority_ids = standard_priority_ids or set()
    priority_clause = "2"
    priority_parameters: list[str] = []
    if priority_ids:
        priority_placeholders = ",".join("?" for _ in priority_ids)
        priority_clause = f"CASE WHEN p.tcgdex_id IN ({priority_placeholders}) THEN 0 ELSE 2 END"
        priority_parameters = sorted(priority_ids)
    standard_clause = "2"
    standard_parameters: list[str] = []
    if standard_priority_ids:
        standard_placeholders = ",".join("?" for _ in standard_priority_ids)
        standard_clause = (
            f"CASE WHEN p.tcgdex_id IN ({standard_placeholders}) THEN 1 ELSE 2 END"
        )
        standard_parameters = sorted(standard_priority_ids)
    excluded = sorted(exclude_ids or set())
    exclude_clause = ""
    if excluded:
        exclude_clause = " AND p.tcgdex_id NOT IN (" + ",".join("?" for _ in excluded) + ")"
    parameters: list[Any] = [
        language, *statuses, *excluded, *priority_parameters, *standard_parameters
    ]
    absent_guard = "" if recheck_absent else " AND (t.status IS NULL OR t.status <> 'absent')"
    row = connection.execute(
        f"""SELECT p.tcgdex_id AS printing_id
            FROM catalog_printings p
            LEFT JOIN catalog_translations t
              ON t.printing_id=p.tcgdex_id AND t.language=?
            WHERE (t.id IS NULL OR t.status IN ({placeholders}) OR p.{stale_column}=1)
              {absent_guard}{exclude_clause}
            ORDER BY MIN({priority_clause}, {standard_clause}),
                     CASE COALESCE(t.status, 'not_fetched')
                       WHEN 'not_fetched' THEN 0 WHEN 'network_error' THEN 1
                       WHEN 'absent' THEN 2 ELSE 3 END,
                     p.tcgdex_id LIMIT 1""",
        parameters,
    ).fetchone()
    return str(row[0]) if row else None


def _ensure_translation_row(connection: Any, printing_id: str, language: str) -> None:
    source_url = _safe_api_url(f"/{language}/cards/{quote(printing_id, safe='%!._-')}")
    with connection:
        connection.execute(
            """INSERT INTO catalog_translations
               (printing_id, language, status, source_url)
               VALUES (?, ?, 'not_fetched', ?)
               ON CONFLICT(printing_id, language) DO NOTHING""",
            (printing_id, language, source_url),
        )


def _deck_priority_ids(connection: Any, deck_id: str | None) -> set[str]:
    """Résout localement seulement les identités exactes d'un deck confirmé."""
    if not deck_id:
        return set()
    version = connection.execute(
        """SELECT id FROM deck_versions
           WHERE deck_id=? AND exact_confirmed=1
           ORDER BY version_number DESC LIMIT 1""",
        (deck_id,),
    ).fetchone()
    if version is None:
        raise CatalogError(f"Aucune version exacte confirmée pour le deck {deck_id}.")
    rows = connection.execute(
        """SELECT DISTINCT p.tcgdex_id, t.name, d.card_name
           FROM deck_version_cards d
           JOIN catalog_sets s
             ON lower(s.tcg_online_code)=lower(d.set_code)
           JOIN catalog_printings p
             ON p.set_id=s.tcgdex_id AND p.local_id=d.collector_number
           JOIN catalog_translations t ON t.printing_id=p.tcgdex_id
           WHERE d.deck_version_id=? AND d.set_code IS NOT NULL
             AND d.collector_number IS NOT NULL
             AND t.name IS NOT NULL""",
        (version["id"],),
    ).fetchall()
    return {
        str(row[0]) for row in rows
        if _normalized_identity_name(row[1]) == _normalized_identity_name(row[2])
    }


def _standard_context_priority_ids(connection: Any) -> set[str]:
    """Retourne seulement des IDs publics déjà reliés à une rotation vérifiée."""
    tables = {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if not {"official_rule_assertions", "official_rule_sources"}.issubset(tables):
        return set()
    today = date.today().isoformat()
    rows = connection.execute(
        """SELECT a.payload_json
           FROM official_rule_assertions a
           JOIN official_rule_sources s USING(source_id)
           WHERE a.assertion_kind='rotation' AND a.format='standard'
             AND a.platform='live' AND a.validation_status='verified'
             AND s.validation_status='verified'
             AND (a.effective_from IS NULL OR a.effective_from<=?)
             AND (a.effective_to IS NULL OR a.effective_to>=?)
             AND (s.effective_from IS NULL OR s.effective_from<=?)
             AND (s.effective_to IS NULL OR s.effective_to>=?)""",
        (today, today, today, today),
    ).fetchall()
    marks: set[str] = set()
    for row in rows:
        try:
            payload = json.loads(row[0])
        except (TypeError, json.JSONDecodeError):
            continue
        values = payload.get("allowed_regulation_marks", [])
        if isinstance(values, list):
            marks.update(str(value) for value in values if isinstance(value, str))
    if not marks:
        return set()
    placeholders = ",".join("?" for _ in marks)
    return {
        str(row[0])
        for row in connection.execute(
            f"SELECT tcgdex_id FROM catalog_printings WHERE regulation_mark IN ({placeholders})",
            sorted(marks),
        ).fetchall()
    }


def _upsert_set_detail(
    connection: Any, payload: Any, expected_id: str, language: str, source_url: str
) -> None:
    record = _set_record(payload, expected_id=expected_id)
    retrieved_at = utc_now()
    name_column = "name_en" if language == "en" else "name_fr"
    source_column = "source_url_en" if language == "en" else "source_url_fr"
    retrieved_column = "retrieved_at_en" if language == "en" else "retrieved_at_fr"
    status_column = "detail_status_en" if language == "en" else "detail_status_fr"
    hash_column = "content_sha256_en" if language == "en" else "content_sha256_fr"
    stale_column = "detail_stale_en" if language == "en" else "detail_stale_fr"
    error_column = "last_error_en" if language == "en" else "last_error_fr"
    cards = payload.get("cards")
    if cards is not None:
        card_records = _validated_list(
            cards, _card_brief, "cartes d'extension", max_items=2_000
        )
    else:
        card_records = []
    content_hash = _canonical_sha256(payload)
    with connection:
        connection.execute(
            f"""UPDATE catalog_sets SET
                {name_column}=?, series_id=COALESCE(?, series_id),
                release_date=COALESCE(?, release_date),
                card_count_total=COALESCE(?, card_count_total),
                card_count_official=COALESCE(?, card_count_official),
                tcg_online_code=COALESCE(?, tcg_online_code),
                abbreviation_official=COALESCE(?, abbreviation_official),
                abbreviation_localized=COALESCE(?, abbreviation_localized),
                updated_at=?, {source_column}=?, {retrieved_column}=?,
                {status_column}='present', {hash_column}=?, {stale_column}=0,
                {error_column}=NULL
                WHERE tcgdex_id=?""",
            (
                record.name,
                record.series_id,
                record.release_date,
                record.card_count_total,
                record.card_count_official,
                record.tcg_online_code,
                record.abbreviation_official,
                record.abbreviation_localized,
                retrieved_at,
                source_url,
                retrieved_at,
                content_hash,
                expected_id,
            ),
        )
        for card in card_records:
            _upsert_card_brief(connection, card, language, source_url, retrieved_at)


def _normalize_category(value: str | None) -> str | None:
    if value is None:
        return None
    folded = value.casefold().replace("é", "e")
    if folded in {"pokemon", "pokémon"}:
        return "pokemon"
    if folded in {"trainer", "dresseur"}:
        return "trainer"
    if folded in {"energy", "energie"}:
        return "energy"
    return value.casefold()


def _validated_card_detail(payload: Any, expected_id: str) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise CatalogError("Détail de carte TCGdex invalide.")
    tcgdex_id = _identifier(payload.get("id"))
    if tcgdex_id != expected_id:
        raise CatalogError("TCGdex a retourné une autre carte que celle demandée.")
    local_id = _bounded_text(payload.get("localId"), "localId", required=True, maximum=80)
    name = _bounded_text(payload.get("name"), "name", required=True, maximum=500)
    category = _bounded_text(payload.get("category"), "category", maximum=80)
    set_payload = payload.get("set")
    if not isinstance(set_payload, dict):
        raise CatalogError("Détail de carte sans extension TCGdex valide.")
    set_record = _set_record(set_payload)
    hp = payload.get("hp")
    if isinstance(hp, str) and hp.isdigit():
        hp = int(hp)
    hp = _optional_int(hp, "hp", maximum=100_000)
    retreat = _optional_int(payload.get("retreat"), "retreat", maximum=100)
    return {
        "id": tcgdex_id,
        "local_id": local_id,
        "name": name,
        "category": category,
        "normalized_category": _normalize_category(category),
        "set": set_record,
        "hp": hp,
        "stage": _bounded_text(payload.get("stage"), "stage", maximum=100),
        "regulation_mark": _bounded_text(payload.get("regulationMark"), "regulationMark", maximum=20),
        "rarity": _bounded_text(payload.get("rarity"), "rarity", maximum=100),
        "illustrator": _bounded_text(payload.get("illustrator"), "illustrator", maximum=300),
        "types_json": _json_list(payload.get("types"), "types"),
        "variants_json": _json_object_or_list(payload.get("variants"), "variants"),
        "description": _bounded_text(payload.get("description"), "description", maximum=20_000),
        "effect": _bounded_text(payload.get("effect"), "effect", maximum=20_000),
        "trainer_type": _bounded_text(payload.get("trainerType"), "trainerType", maximum=200),
        "energy_type": _bounded_text(payload.get("energyType"), "energyType", maximum=200),
        "abilities_json": _json_list(payload.get("abilities"), "abilities"),
        "attacks_json": _json_list(payload.get("attacks"), "attacks"),
        "weaknesses_json": _json_list(payload.get("weaknesses"), "weaknesses"),
        "resistances_json": _json_list(payload.get("resistances"), "resistances"),
        "retreat": retreat,
        "payload_sha256": _canonical_sha256(payload),
    }


def _upsert_card_detail(
    connection: Any, payload: Any, expected_id: str, language: str, source_url: str
) -> None:
    record = _validated_card_detail(payload, expected_id)
    retrieved_at = utc_now()
    with connection:
        _upsert_set_brief(connection, record["set"], language, source_url, retrieved_at)
        connection.execute(
            """UPDATE catalog_printings SET
               set_id=?, local_id=?, category=COALESCE(?, category), hp=COALESCE(?, hp),
               stage=COALESCE(?, stage), regulation_mark=COALESCE(?, regulation_mark),
               rarity=COALESCE(?, rarity), illustrator=COALESCE(?, illustrator),
               types_json=COALESCE(?, types_json), variants_json=COALESCE(?, variants_json),
               detail_stale_en=CASE WHEN ?='en' THEN 0 ELSE detail_stale_en END,
               detail_stale_fr=CASE WHEN ?='fr' THEN 0 ELSE detail_stale_fr END,
               updated_at=? WHERE tcgdex_id=?""",
            (
                record["set"].tcgdex_id,
                record["local_id"],
                record["normalized_category"],
                record["hp"],
                record["stage"],
                record["regulation_mark"],
                record["rarity"],
                record["illustrator"],
                record["types_json"],
                record["variants_json"],
                language,
                language,
                retrieved_at,
                expected_id,
            ),
        )
        connection.execute(
            """UPDATE catalog_translations SET
               status='present', name=?, category=?, description=?, effect=?,
               trainer_type=?, energy_type=?, abilities_json=?, attacks_json=?,
               weaknesses_json=?, resistances_json=?, retreat=?, source_url=?,
               retrieved_at=?, payload_sha256=?, last_error=NULL
               WHERE printing_id=? AND language=?""",
            (
                record["name"],
                record["category"],
                record["description"],
                record["effect"],
                record["trainer_type"],
                record["energy_type"],
                record["abilities_json"],
                record["attacks_json"],
                record["weaknesses_json"],
                record["resistances_json"],
                record["retreat"],
                source_url,
                retrieved_at,
                record["payload_sha256"],
                expected_id,
                language,
            ),
        )


def _mark_missing_or_error(
    connection: Any, kind: str, entity_id: str, language: str, status: str, error: str | None
) -> None:
    timestamp = utc_now()
    with connection:
        if kind == "sets":
            status_column = "detail_status_en" if language == "en" else "detail_status_fr"
            error_column = "last_error_en" if language == "en" else "last_error_fr"
            connection.execute(
                f"UPDATE catalog_sets SET {status_column}=?, {error_column}=?, updated_at=? WHERE tcgdex_id=?",
                (status, error, timestamp, entity_id),
            )
        else:
            connection.execute(
                """UPDATE catalog_translations SET status=?, last_error=?, retrieved_at=?
                   WHERE printing_id=? AND language=?""",
                (status, error, timestamp, entity_id, language),
            )


def _record_sync_metadata(
    connection: Any, requests_made: int, *, success: bool, error: str | None = None
) -> None:
    timestamp = utc_now()
    with connection:
        connection.execute(
            """INSERT INTO metadata(key, value) VALUES('catalog_total_requests', ?)
               ON CONFLICT(key) DO UPDATE SET
               value=CAST(CAST(metadata.value AS INTEGER) + CAST(excluded.value AS INTEGER) AS TEXT)""",
            (str(requests_made),),
        )
        if success:
            connection.execute(
                """INSERT INTO metadata(key, value) VALUES('catalog_last_success_at', ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                (timestamp,),
            )
        if error:
            connection.execute(
                """INSERT INTO metadata(key, value) VALUES('catalog_last_failure_at', ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                (timestamp,),
            )
            connection.execute(
                """INSERT INTO metadata(key, value) VALUES('catalog_last_error', ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                (error[:500],),
            )


def _record_index_failure(
    connection: Any,
    scope: str,
    *,
    refresh: bool,
    request_attempts: int,
    error: str,
) -> None:
    timestamp = utc_now()
    with connection:
        from pokemind.catalog_snapshots import record_failure
        record_failure(connection, scope, "refresh" if refresh else "discovery", timestamp)
        if refresh:
            connection.execute(
                """UPDATE catalog_refresh_state SET
                      requests_total=requests_total + ?, last_failure_at=?,
                      last_error=?, updated_at=? WHERE scope=?""",
                (request_attempts, timestamp, error[:500], timestamp, scope),
            )
        else:
            connection.execute(
                """INSERT INTO catalog_sync_state
                   (scope, next_page, completed, requests_total, started_at,
                    last_failure_at, last_error, updated_at)
                   VALUES (?, 1, 0, ?, ?, ?, ?, ?)
                   ON CONFLICT(scope) DO UPDATE SET
                      requests_total=catalog_sync_state.requests_total + excluded.requests_total,
                      last_failure_at=excluded.last_failure_at,
                      last_error=excluded.last_error, updated_at=excluded.updated_at""",
                (
                    scope,
                    request_attempts,
                    timestamp,
                    timestamp,
                    error[:500],
                    timestamp,
                ),
            )


def sync_cards(
    db_path: Path,
    *,
    languages: str | Iterable[str] = LANGUAGES,
    max_requests: int = 10,
    dry_run: bool = False,
    phase: str = "balanced",
    refresh_index: bool = False,
    recheck_absent: bool = False,
    prioritize_deck: str | None = None,
    client: CatalogApiClient | None = None,
) -> dict[str, Any]:
    selected = parse_languages(languages)
    if not 1 <= max_requests <= 1_000:
        raise CatalogError("--max-requests doit être compris entre 1 et 1000.")
    if phase not in SYNC_PHASES:
        raise CatalogError("--phase doit être index, details ou balanced.")
    if refresh_index and phase == "details":
        raise CatalogError("--refresh-index exige --phase index ou balanced.")
    if dry_run:
        schema_version = 0
        if db_path.is_file():
            connection = connect_readonly(db_path)
            try:
                schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            finally:
                connection.close()
        return {
            "database": str(db_path),
            "dry_run": True,
            "network_used": False,
            "writes": 0,
            "languages": list(selected),
            "max_requests": max_requests,
            "phase": phase,
            "refresh_index": refresh_index,
            "recheck_absent": recheck_absent,
            "local_priority_requested": prioritize_deck is not None,
            "would_migrate": schema_version < SCHEMA_VERSION,
            "plan": (
                (["manual index refresh"] if refresh_index else ["initial index discovery"])
                if phase == "index"
                else ["set details", "card details"]
                if phase == "details"
                else [
                    "manual index refresh" if refresh_index else "initial index discovery",
                    "set details",
                    "card details",
                ]
            ),
        }
    connection = connect_writable(db_path)
    actual_client = client or CatalogApiClient(max_requests)
    if actual_client.max_requests != max_requests:
        raise CatalogError("Le client injecté doit utiliser le même budget de requêtes.")
    pages: list[dict[str, Any]] = []
    details = {"sets_present": 0, "sets_absent": 0, "cards_present": 0, "cards_absent": 0}
    stopped_reason = "budget_exhausted"
    error: str | None = None
    successes = 0
    priority_ids: set[str] = set()
    standard_priority_ids: set[str] = set()
    try:
        initialize_schema(connection)
        priority_ids = _deck_priority_ids(connection, prioritize_deck)
        standard_priority_ids = _standard_context_priority_ids(connection)
        if phase in {"index", "balanced"}:
            scopes = [(kind, language) for kind in ("sets", "cards") for language in selected]
            resumed_refresh_scopes = {
                str(row[0])
                for row in connection.execute(
                    "SELECT scope FROM catalog_refresh_state WHERE in_progress=1"
                ).fetchall()
            } if refresh_index else set()
            finished_scopes: set[str] = set()
            keep_indexing = True
            while actual_client.remaining > 0 and keep_indexing:
                keep_indexing = False
                for kind, language in scopes:
                    scope = f"{kind}:{language}"
                    if actual_client.remaining <= 0 or scope in finished_scopes:
                        continue
                    requests_before = actual_client.requests_made
                    try:
                        result = _sync_index_page(
                            connection,
                            actual_client,
                            kind,
                            language,
                            refresh=refresh_index,
                            allow_head_probe=scope in resumed_refresh_scopes,
                        )
                    except (NetworkFailure, CatalogError) as exc:
                        _record_index_failure(
                            connection,
                            scope,
                            refresh=refresh_index,
                            request_attempts=actual_client.requests_made - requests_before,
                            error=neutral_exception_code(exc, "TCGDEX"),
                        )
                        raise
                    if result is None:
                        finished_scopes.add(scope)
                        continue
                    pages.append(result)
                    successes += 1
                    keep_indexing = True
                    if result["completed"]:
                        finished_scopes.add(scope)
                    if phase == "balanced" and len(pages) >= len(scopes):
                        keep_indexing = False
                        break
                if phase == "balanced":
                    break
        attempted_details: dict[tuple[str, str], set[str]] = {}
        while phase in {"details", "balanced"} and actual_client.remaining > 0:
            made_progress = False
            for kind in ("sets", "cards"):
                for language in selected:
                    if actual_client.remaining <= 0:
                        break
                    excluded = attempted_details.setdefault((kind, language), set())
                    entity_id = (
                        _pending_set(
                            connection,
                            language,
                            recheck_absent=recheck_absent,
                            exclude_ids=excluded,
                        )
                        if kind == "sets"
                        else _pending_card(
                            connection,
                            language,
                            recheck_absent=recheck_absent,
                            priority_ids=priority_ids,
                            standard_priority_ids=standard_priority_ids,
                            exclude_ids=excluded,
                        )
                    )
                    if not entity_id:
                        continue
                    made_progress = True
                    excluded.add(entity_id)
                    if kind == "cards":
                        _ensure_translation_row(connection, entity_id, language)
                    path = f"/{language}/{kind}/{quote(entity_id, safe='%!._-')}"
                    try:
                        payload, source_url = actual_client.get_json(path)
                        if kind == "sets":
                            _upsert_set_detail(connection, payload, entity_id, language, source_url)
                            details["sets_present"] += 1
                        else:
                            _upsert_card_detail(connection, payload, entity_id, language, source_url)
                            details["cards_present"] += 1
                        successes += 1
                    except ApiNotFound:
                        _mark_missing_or_error(connection, kind, entity_id, language, "absent", None)
                        details[f"{kind}_absent"] += 1
                        successes += 1
                    except BodyBudgetExhausted:
                        stopped_reason = "body_budget_exhausted"
                        error = "TCGDEX_BODY_BUDGET_EXHAUSTED"
                        break
                    except RequestBudgetExhausted:
                        stopped_reason = "budget_exhausted"
                        break
                    except NetworkFailure as exc:
                        error = neutral_exception_code(exc, "TCGDEX")
                        _mark_missing_or_error(
                            connection, kind, entity_id, language, "network_error", error
                        )
                        stopped_reason = "source_error"
                        break
                    except CatalogError as exc:
                        error = neutral_exception_code(exc, "TCGDEX")
                        stopped_reason = "source_error"
                        break
                if error or actual_client.remaining <= 0:
                    break
            if error:
                break
            if not made_progress:
                stopped_reason = "nothing_pending"
                break
        _record_sync_metadata(
            connection, actual_client.requests_made, success=successes > 0, error=error
        )
        coverage = cards_coverage(db_path, _connection=connection)
        return {
            "database": str(db_path),
            "dry_run": False,
            "network_used": actual_client.requests_made > 0,
            "languages": list(selected),
            "max_requests": max_requests,
            "phase": phase,
            "refresh_index": refresh_index,
            "recheck_absent": recheck_absent,
            "local_priority_requested": prioritize_deck is not None,
            "local_priority_candidates": len(priority_ids),
            "standard_priority_candidates": len(standard_priority_ids),
            "requests_made": actual_client.requests_made,
            "pages": pages,
            "details": details,
            "stopped_reason": stopped_reason,
            "error": error,
            "coverage": coverage,
        }
    except (NetworkFailure, CatalogError) as exc:
        error = neutral_exception_code(exc, "TCGDEX")
        _record_sync_metadata(connection, actual_client.requests_made, success=successes > 0, error=error)
        return {
            "database": str(db_path),
            "dry_run": False,
            "network_used": actual_client.requests_made > 0,
            "languages": list(selected),
            "max_requests": max_requests,
            "phase": phase,
            "refresh_index": refresh_index,
            "recheck_absent": recheck_absent,
            "local_priority_requested": prioritize_deck is not None,
            "local_priority_candidates": len(priority_ids),
            "standard_priority_candidates": len(standard_priority_ids),
            "requests_made": actual_client.requests_made,
            "pages": pages,
            "details": details,
            "stopped_reason": "source_error",
            "error": error,
            "coverage": cards_coverage(db_path, _connection=connection),
        }
    finally:
        connection.close()


def _require_catalog(connection: Any) -> None:
    version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    if version < SCHEMA_VERSION:
        raise CatalogError("Catalogue non initialisé; exécuter 'cards sync' d'abord.")


def _loads_or_none(value: str | None) -> Any:
    return json.loads(value) if value else None


def show_card(db_path: Path, tcgdex_id: str, language: str = "fr") -> dict[str, Any]:
    language = parse_languages((language,))[0]
    tcgdex_id = _identifier(tcgdex_id)
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente; synchroniser d'abord le catalogue.")
    connection = connect_readonly(db_path)
    try:
        _require_catalog(connection)
        row = connection.execute(
            """SELECT p.*, t.language, t.status, t.name, t.category AS localized_category,
                      t.description, t.effect, t.trainer_type, t.energy_type,
                      t.abilities_json, t.attacks_json, t.weaknesses_json,
                      t.resistances_json, t.retreat, t.source_url,
                      t.retrieved_at, t.payload_sha256, t.last_error,
                      s.name_en AS set_name_en, s.name_fr AS set_name_fr,
                      s.release_date AS set_release_date,
                      s.tcg_online_code AS set_tcg_online_code
               FROM catalog_printings p
               LEFT JOIN catalog_translations t
                 ON t.printing_id=p.tcgdex_id AND t.language=?
               LEFT JOIN catalog_sets s ON s.tcgdex_id=p.set_id
               WHERE p.tcgdex_id=?""",
            (language, tcgdex_id),
        ).fetchone()
        if row is None:
            raise CatalogError(f"Impression TCGdex inconnue localement: {tcgdex_id}.")
        stale_column = "detail_stale_en" if language == "en" else "detail_stale_fr"
        translation_rows = connection.execute(
            """SELECT language, status, name, source_url, retrieved_at,
                      payload_sha256, last_error
               FROM catalog_translations WHERE printing_id=? ORDER BY language""",
            (tcgdex_id,),
        ).fetchall()
        translations = {
            str(item["language"]): {
                "status": item["status"],
                "name": item["name"],
                "provenance": {
                    "url": item["source_url"],
                    "retrieved_at": item["retrieved_at"],
                    "sha256": item["payload_sha256"],
                    "last_error": item["last_error"],
                },
            }
            for item in translation_rows
        }
        missing_fields = [
            field
            for field, value in (
                ("set_id", row["set_id"]),
                ("set_release_date", row["set_release_date"]),
                ("category", row["category"]),
                ("rarity", row["rarity"]),
                ("regulation_mark", row["regulation_mark"]),
                ("localized_name", row["name"]),
                ("localized_text", row["description"] or row["effect"] or row["attacks_json"]),
            )
            if value is None
        ]
        result = {
            "tcgdex_id": row["tcgdex_id"],
            "printing_identity": {
                "kind": "tcgdex_printing",
                "stable_public_id": row["tcgdex_id"],
                "functional_identity": "unknown",
                "reason": "Une impression n'est pas une équivalence fonctionnelle prouvée.",
            },
            "language": language,
            "status": row["status"] or "not_fetched",
            "name": row["name"],
            "aliases_by_language": {
                key: value["name"] for key, value in translations.items()
                if value["name"] is not None
            },
            "translations": translations,
            "set": {
                "id": row["set_id"],
                "name_en": row["set_name_en"],
                "name_fr": row["set_name_fr"],
                "release_date": row["set_release_date"],
                "tcg_online_code": row["set_tcg_online_code"],
            },
            "local_id": row["local_id"],
            "category": row["category"],
            "localized_category": row["localized_category"],
            "hp": row["hp"],
            "stage": row["stage"],
            "regulation_mark": row["regulation_mark"],
            "rarity": row["rarity"],
            "illustrator": row["illustrator"],
            "types": _loads_or_none(row["types_json"]),
            "variants": _loads_or_none(row["variants_json"]),
            "description": row["description"],
            "effect": row["effect"],
            "trainer_type": row["trainer_type"],
            "energy_type": row["energy_type"],
            "abilities": _loads_or_none(row["abilities_json"]),
            "attacks": _loads_or_none(row["attacks_json"]),
            "weaknesses": _loads_or_none(row["weaknesses_json"]),
            "resistances": _loads_or_none(row["resistances_json"]),
            "retreat": row["retreat"],
            "possibly_stale": bool(row[stale_column]),
            "missing_fields": missing_fields,
            "provenance": {
                "url": row["source_url"],
                "retrieved_at": row["retrieved_at"],
                "sha256": row["payload_sha256"],
                "last_error": row["last_error"],
            },
            "limits": [
                "TCGdex ne prouve ni disponibilité dans TCG Live, ni légalité, possession ou coût."
            ],
        }
        # A bilingual batch preserves labels per language instead of exposing
        # whichever translation last updated the legacy shared printing row.
        from pokemind.catalog_batch_store import verified_payload
        payload = verified_payload(connection, "cards", tcgdex_id, language, row["payload_sha256"])
        if payload is not None:
            for output, source in (("types", "types"), ("stage", "stage"), ("rarity", "rarity"),
                                   ("hp", "hp"), ("variants", "variants"), ("illustrator", "illustrator")):
                result[output] = payload.get(source)
            set_hash_column = "content_sha256_en" if language == "en" else "content_sha256_fr"
            set_hash = connection.execute(f"SELECT {set_hash_column} FROM catalog_sets WHERE tcgdex_id=?",
                                          (row["set_id"],)).fetchone()
            set_payload = verified_payload(connection, "sets", row["set_id"], language, set_hash[0]) if set_hash else None
            if set_payload is not None:
                result["set"]["release_date"] = set_payload.get("releaseDate")
                result["set"]["tcg_online_code"] = set_payload.get("tcgOnline")
            for field, value in (("rarity", result["rarity"]), ("set_release_date", result["set"]["release_date"])):
                if field in result["missing_fields"]:
                    result["missing_fields"].remove(field)
                if value is None:
                    result["missing_fields"].append(field)
            result["additional_descriptive_fields"] = {key: payload.get(key) for key in
                ("evolveFrom", "suffix", "dexId", "cameoDexIds", "level", "weight", "item", "variants_detailed")}
            result["provenance"]["transport"] = ("graphql_fixed_query" if row["source_url"] ==
                "https://api.tcgdex.net/v2/graphql" else "pinned_git_literal_snapshot" if
                row["source_url"].startswith("https://github.com/tcgdex/cards-database/blob/") else
                "rest_detail_preserved_in_batch")
        from pokemind.french_text_store import apply_to_card
        return apply_to_card(connection, result)
    finally:
        connection.close()


def card_reprints(
    db_path: Path, tcgdex_id: str, *, as_of: str | None = None
) -> dict[str, Any]:
    """Expose seulement les équivalences soutenues par une assertion officielle."""
    tcgdex_id = _identifier(tcgdex_id)
    if as_of is not None:
        try:
            as_of = date.fromisoformat(as_of).isoformat()
        except (TypeError, ValueError) as exc:
            raise CatalogError("--as-of doit être une date YYYY-MM-DD.") from exc
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente.")
    connection = connect_readonly(db_path)
    try:
        _require_catalog(connection)
        printing = connection.execute(
            "SELECT 1 FROM catalog_printings WHERE tcgdex_id=?", (tcgdex_id,)
        ).fetchone()
        if printing is None:
            raise CatalogError(f"Impression TCGdex inconnue localement: {tcgdex_id}.")
        tables = {
            str(row[0]) for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        rows = []
        if {"official_rule_assertions", "official_rule_sources"}.issubset(tables):
            rows = connection.execute(
                """SELECT a.assertion_id, a.subject_id, a.payload_json,
                          a.format, a.platform,
                          a.effective_from, a.effective_to,
                          a.validation_status AS assertion_status,
                          s.source_id, s.title, s.url, s.consulted_at,
                          s.validation_status AS source_status,
                          s.effective_from AS source_effective_from,
                          s.effective_to AS source_effective_to
                   FROM official_rule_assertions a
                   JOIN official_rule_sources s USING(source_id)
                   WHERE a.assertion_kind='reprint_equivalence'
                   ORDER BY a.assertion_id"""
            ).fetchall()
        verified: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            target = payload.get("current_printing_id")
            if row["subject_id"] != tcgdex_id and target != tcgdex_id:
                continue
            active = as_of is None or (
                (row["effective_from"] is None or row["effective_from"] <= as_of)
                and (row["effective_to"] is None or row["effective_to"] >= as_of)
                and (
                    row["source_effective_from"] is None
                    or row["source_effective_from"] <= as_of
                )
                and (
                    row["source_effective_to"] is None
                    or row["source_effective_to"] >= as_of
                )
            )
            item = {
                "assertion_id": row["assertion_id"],
                "from_printing_id": row["subject_id"],
                "to_printing_id": target,
                "format": row["format"],
                "platform": row["platform"],
                "effective_from": row["effective_from"],
                "effective_to": row["effective_to"],
                "active_for_query": active,
                "source": {
                    "source_id": row["source_id"],
                    "title": row["title"],
                    "url": row["url"],
                    "consulted_at": row["consulted_at"],
                },
            }
            if (
                active
                and row["assertion_status"] == "verified"
                and row["source_status"] == "verified"
                and isinstance(target, str)
            ):
                verified.append(item)
            else:
                item["reason"] = "Assertion, source, cible ou fenêtre non vérifiée."
                rejected.append(item)
        return {
            "tcgdex_id": tcgdex_id,
            "as_of": as_of,
            "status": "verified" if verified else "unknown",
            "verified_reprints": verified,
            "non_authoritative_candidates": rejected,
            "reason_codes": [] if verified else ["NO_VERIFIED_REPRINT_EQUIVALENCE"],
            "limits": [
                "Un nom FR/EN identique n'est jamais utilisé seul comme preuve de réimpression.",
                "TCGdex décrit les impressions; Pokémon officiel demeure normatif.",
            ],
        }
    finally:
        connection.close()


def search_cards(
    db_path: Path, query: str, *, language: str = "fr", limit: int = 20
) -> list[dict[str, Any]]:
    selected_languages = LANGUAGES if language == "all" else (parse_languages((language,))[0],)
    if not 1 <= limit <= 100:
        raise CatalogError("La limite doit être comprise entre 1 et 100.")
    tokens = query_tokens(query)
    if not tokens:
        raise CatalogError("La recherche doit contenir au moins un mot significatif.")
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente; synchroniser d'abord le catalogue.")
    connection = connect_readonly(db_path)
    try:
        _require_catalog(connection)
        backend_row = connection.execute(
            "SELECT value FROM metadata WHERE key='catalog_search_backend'"
        ).fetchone()
        backend = str(backend_row[0]) if backend_row else "like"
        if backend == "fts5":
            expression = " OR ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens)
            language_placeholders = ",".join("?" for _ in selected_languages)
            rows = connection.execute(
                f"""SELECT t.printing_id, t.language, t.status, t.name,
                          p.set_id, p.local_id, p.category,
                          snippet(catalog_fts, 3, '[', ']', ' … ', 20) AS excerpt,
                          bm25(catalog_fts, 5.0, 1.0) AS score
                   FROM catalog_fts
                   JOIN catalog_translations t ON t.id=catalog_fts.rowid
                   JOIN catalog_printings p ON p.tcgdex_id=t.printing_id
                   WHERE catalog_fts MATCH ? AND t.language IN ({language_placeholders})
                   ORDER BY score, t.printing_id LIMIT ?""",
                (expression, *selected_languages, limit),
            ).fetchall()
        else:
            patterns = [f"%{token}%" for token in tokens]
            clauses = " OR ".join(
                "lower(COALESCE(t.name,'') || ' ' || COALESCE(t.description,'') || ' ' || "
                "COALESCE(t.effect,'') || ' ' || COALESCE(t.attacks_json,'')) LIKE ?"
                for _ in patterns
            )
            language_placeholders = ",".join("?" for _ in selected_languages)
            rows = connection.execute(
                f"""SELECT t.printing_id, t.language, t.status, t.name,
                            p.set_id, p.local_id, p.category, '' AS excerpt, 0 AS score
                     FROM catalog_translations t
                     JOIN catalog_printings p ON p.tcgdex_id=t.printing_id
                     WHERE t.language IN ({language_placeholders}) AND ({clauses})
                     ORDER BY t.name, t.printing_id LIMIT ?""",
                (*selected_languages, *patterns, limit),
            ).fetchall()
        result = [
            {
                "tcgdex_id": row["printing_id"],
                "language": row["language"],
                "status": row["status"],
                "name": row["name"],
                "set_id": row["set_id"],
                "local_id": row["local_id"],
                "category": row["category"],
                "snippet": row["excerpt"] or "",
                "score": round(float(row["score"]), 6),
            }
            for row in rows
        ]
        if "fr" in selected_languages:
            from pokemind.french_text_store import search_fields
            expression = " OR ".join(f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens)
            known = {(r["tcgdex_id"], r["language"]): r for r in result}
            for item in search_fields(connection, expression, limit):
                key = item["tcgdex_id"], item["language"]
                if key in known:
                    known[key]["french_supplement_available"] = True
                    if not known[key]["name"]:
                        known[key]["name"] = item["name"]
                else:
                    result.append(item)
                    known[key] = item
        return result[:limit]
    finally:
        connection.close()


def browse_cards(
    db_path: Path, *, language: str = "fr", offset: int = 0, limit: int = 18
) -> dict[str, Any]:
    """Page through named printings, newest set first, for the card binder (read-only)."""
    language = parse_languages((language,))[0]
    if not 1 <= limit <= 100 or offset < 0:
        raise CatalogError("Pagination invalide.")
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente; synchroniser d'abord le catalogue.")
    connection = connect_readonly(db_path)
    try:
        _require_catalog(connection)
        where = "t.language=? AND t.status='present' AND t.name IS NOT NULL AND t.name<>''"
        total = connection.execute(
            f"SELECT count(*) FROM catalog_translations t WHERE {where}", (language,)
        ).fetchone()[0]
        rows = connection.execute(
            f"""SELECT t.printing_id, t.language, t.name, p.set_id, p.local_id, p.category
                FROM catalog_translations t
                JOIN catalog_printings p ON p.tcgdex_id=t.printing_id
                LEFT JOIN catalog_sets s ON s.tcgdex_id=p.set_id
                WHERE {where}
                ORDER BY COALESCE(s.release_date, '') DESC, p.set_id,
                         CAST(p.local_id AS INTEGER), p.local_id, t.printing_id
                LIMIT ? OFFSET ?""",
            (language, limit, offset),
        ).fetchall()
        return {
            "language": language, "offset": offset, "total": int(total),
            "cards": [{"tcgdex_id": row["printing_id"], "language": row["language"], "name": row["name"],
                       "set_id": row["set_id"], "local_id": row["local_id"], "category": row["category"]}
                      for row in rows],
        }
    finally:
        connection.close()


def cards_coverage(db_path: Path, *, _connection: Any | None = None) -> dict[str, Any]:
    if _connection is None and not db_path.is_file():
        raise FileNotFoundError("Base locale absente; synchroniser d'abord le catalogue.")
    connection = _connection or connect_readonly(db_path)
    close = _connection is None
    try:
        _require_catalog(connection)
        metadata = dict(connection.execute("SELECT key, value FROM metadata").fetchall())
        printings = int(connection.execute("SELECT COUNT(*) FROM catalog_printings").fetchone()[0])
        sets = int(connection.execute("SELECT COUNT(*) FROM catalog_sets").fetchone()[0])
        statuses: dict[str, dict[str, int]] = {}
        set_statuses: dict[str, dict[str, int]] = {}
        for language in LANGUAGES:
            explicit = {
                status: int(connection.execute(
                    "SELECT COUNT(*) FROM catalog_translations WHERE language=? AND status=?",
                    (language, status),
                ).fetchone()[0])
                for status in STATUS_VALUES
            }
            explicit["not_fetched"] = max(
                0,
                printings
                - explicit["present"]
                - explicit["absent"]
                - explicit["network_error"],
            )
            statuses[language] = explicit
            set_column = "detail_status_en" if language == "en" else "detail_status_fr"
            set_statuses[language] = {
                status: int(connection.execute(
                    f"SELECT COUNT(*) FROM catalog_sets WHERE {set_column}=?", (status,)
                ).fetchone()[0])
                for status in STATUS_VALUES
            }
        languages: dict[str, Any] = {}
        for language in LANGUAGES:
            stale_column = "detail_stale_en" if language == "en" else "detail_stale_fr"
            languages[language] = {
                "discovered_printings_denominator": printings,
                "names": int(connection.execute(
                    "SELECT COUNT(*) FROM catalog_translations WHERE language=? AND name IS NOT NULL",
                    (language,),
                ).fetchone()[0]),
                "details_present": statuses[language]["present"],
                "descriptions": int(connection.execute(
                    "SELECT COUNT(*) FROM catalog_translations WHERE language=? AND description IS NOT NULL",
                    (language,),
                ).fetchone()[0]),
                "attacks": int(connection.execute(
                    "SELECT COUNT(*) FROM catalog_translations WHERE language=? AND attacks_json IS NOT NULL",
                    (language,),
                ).fetchone()[0]),
                "statuses": statuses[language],
                "possibly_stale_details": int(connection.execute(
                    f"SELECT COUNT(*) FROM catalog_printings WHERE {stale_column}=1"
                ).fetchone()[0]),
                "sets": {
                    "discovered_denominator": sets,
                    "statuses": set_statuses[language],
                    "possibly_stale_details": int(connection.execute(
                        f"SELECT COUNT(*) FROM catalog_sets WHERE {stale_column}=1"
                    ).fetchone()[0]),
                },
            }
        scopes = [dict(row) for row in connection.execute(
            """SELECT scope, next_page, completed, end_candidate_page, started_at,
                      completed_at, requests_total, last_success_at,
                      last_failure_at, last_error
               FROM catalog_sync_state ORDER BY scope"""
        ).fetchall()]
        refresh_scopes = [dict(row) for row in connection.execute(
            """SELECT scope, next_page, in_progress, end_candidate_page,
                      head_probe_done, cycle_started_at, last_completed_at,
                      requests_total, pages_scanned_current, items_seen_current,
                      new_items_current, changed_items_current, last_success_at,
                      last_failure_at, last_error
               FROM catalog_refresh_state ORDER BY scope"""
        ).fetchall()]
        incomplete = int(connection.execute(
            """SELECT COUNT(*) FROM catalog_printings p
               WHERE NOT EXISTS (
                   SELECT 1 FROM catalog_translations t
                   WHERE t.printing_id=p.tcgdex_id AND t.language='en' AND t.status='present'
               ) OR NOT EXISTS (
                   SELECT 1 FROM catalog_translations t
                   WHERE t.printing_id=p.tcgdex_id AND t.language='fr' AND t.status='present'
               )"""
        ).fetchone()[0])
        expected_scopes = {f"{kind}:{language}" for kind in ("sets", "cards") for language in LANGUAGES}
        scope_by_name = {str(row["scope"]): row for row in scopes}
        discovery_complete = all(
            name in scope_by_name and bool(scope_by_name[name]["completed"])
            for name in expected_scopes
        )
        details_complete = all(
            statuses[language]["not_fetched"] == 0
            and statuses[language]["network_error"] == 0
            and set_statuses[language]["not_fetched"] == 0
            and set_statuses[language]["network_error"] == 0
            and languages[language]["possibly_stale_details"] == 0
            and languages[language]["sets"]["possibly_stale_details"] == 0
            for language in LANGUAGES
        )
        refresh_by_name = {str(row["scope"]): row for row in refresh_scopes}
        refresh_in_progress = any(bool(row["in_progress"]) for row in refresh_scopes)
        refresh_finished = all(
            name in refresh_by_name
            and not bool(refresh_by_name[name]["in_progress"])
            and refresh_by_name[name]["last_completed_at"] is not None
            for name in expected_scopes
        )
        for language in LANGUAGES:
            card_scope = scope_by_name.get(f"cards:{language}")
            set_scope = scope_by_name.get(f"sets:{language}")
            discovered_language = int(connection.execute(
                "SELECT COUNT(*) FROM catalog_translations WHERE language=?", (language,)
            ).fetchone()[0])
            details_present = statuses[language]["present"]
            languages[language]["index"] = {
                "scan_complete": bool(card_scope and card_scope["completed"]),
                "discovered": discovered_language,
                # Translation rows may also come from another language's details
                # or set contents. They are NOT membership in a provider snapshot.
                "provider_visible_total": None,
                "provider_total_status": "unknown_without_snapshot_membership",
                "last_success_at": card_scope["last_success_at"] if card_scope else None,
            }
            languages[language]["detail_coverage"] = {
                "numerator": details_present,
                "denominator": printings,
                "ratio": round(details_present / printings, 6) if printings else None,
            }
            languages[language]["sets"]["index_scan_complete"] = bool(
                set_scope and set_scope["completed"]
            )
            from pokemind.catalog_snapshots import snapshot_coverage
            languages[language]["index"]["snapshot"] = snapshot_coverage(connection, f"cards:{language}")
            languages[language]["sets"]["snapshot"] = snapshot_coverage(connection, f"sets:{language}")
            languages[language]["index"]["legacy_cursor_completed"] = languages[language]["index"]["scan_complete"]
            languages[language]["index"]["scan_complete"] = languages[language]["index"]["snapshot"]["complete"]
            languages[language]["sets"]["legacy_cursor_completed"] = languages[language]["sets"]["index_scan_complete"]
            languages[language]["sets"]["index_scan_complete"] = languages[language]["sets"]["snapshot"]["complete"]
        current_indexes_complete = all(
            languages[language][section]["snapshot"]["complete"]
            for language in LANGUAGES for section in ("index", "sets"))
        known_detail_requests = sum(
            statuses[language]["not_fetched"] + statuses[language]["network_error"]
            + set_statuses[language]["not_fetched"] + set_statuses[language]["network_error"]
            for language in LANGUAGES
        )
        stale_requests = sum(
            int(connection.execute(
                f"""SELECT COUNT(*) FROM catalog_printings p JOIN catalog_translations t
                    ON t.printing_id=p.tcgdex_id AND t.language=?
                    WHERE p.detail_stale_{language}=1 AND t.status='present'""", (language,),
            ).fetchone()[0])
            + int(connection.execute(
                f"SELECT COUNT(*) FROM catalog_sets WHERE detail_stale_{language}=1 AND detail_status_{language}='present'"
            ).fetchone()[0])
            for language in LANGUAGES
        )
        from pokemind.french_text_store import coverage_fields
        return {
            "sets_discovered": sets,
            "french_text_supplements": coverage_fields(connection),
            "pinned_source": json.loads(metadata["catalog_pinned_source"]) if "catalog_pinned_source" in metadata else None,
            "unique_printings": printings,
            "details_retrieved_any_language": int(connection.execute(
                "SELECT COUNT(DISTINCT printing_id) FROM catalog_translations WHERE status='present'"
            ).fetchone()[0]),
            "incomplete_printings": incomplete,
            "languages": languages,
            "last_success_at": metadata.get("catalog_last_success_at"),
            "last_failure_at": metadata.get("catalog_last_failure_at"),
            "last_error": metadata.get("catalog_last_error"),
            "requests_total": int(metadata.get("catalog_total_requests", "0")),
            "known_completion_work": {
                "detail_gets_remaining_on_discovered": known_detail_requests + stale_requests,
                "stale_detail_gets_required": stale_requests,
                "index_gets_remaining": None if not current_indexes_complete else 0,
                "index_estimate_status": (
                    "observed_scans_complete" if current_indexes_complete else "unknown_without_current_membership"
                ),
                "recheck_absent_gets_optional": sum(
                    statuses[language]["absent"] + set_statuses[language]["absent"]
                    for language in LANGUAGES
                ),
            },
            "discovery": {
                "complete": discovery_complete,
                "scopes": scopes,
            },
            "details_complete_on_discovered": details_complete,
            "refresh": {
                "in_progress": refresh_in_progress,
                "finished": refresh_finished,
                "scopes": refresh_scopes,
            },
            "scopes": scopes,
            "current_indexes_complete": current_indexes_complete,
            "complete": bool(printings) and current_indexes_complete and details_complete,
            "limits": [
                "La couverture mesure le cache local, pas TCG Live ni la légalité d'un format.",
                "Absent de la source, non récupéré et erreur réseau sont comptés séparément.",
                "Une fin de scan exige une page vide de confirmation après une page abrégée.",
                "Un refresh paginé peut manquer une mutation concurrente malgré le tri stable et la sonde de tête.",
            ],
        }
    finally:
        if close:
            connection.close()


def resolve_deck_cards(db_path: Path, deck_id: str) -> dict[str, Any]:
    """Diagnostic en lecture seule: code TCG Live + numéro + nom doivent tous concorder."""
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente.")
    connection = connect_readonly(db_path)
    try:
        _require_catalog(connection)
        version = connection.execute(
            "SELECT id, version_number FROM deck_versions WHERE deck_id=? ORDER BY version_number DESC LIMIT 1",
            (deck_id,),
        ).fetchone()
        if version is None:
            raise CatalogError(f"Aucune version exacte pour le deck {deck_id}.")
        entries = connection.execute(
            """SELECT ordinal, card_name, set_code, collector_number, quantity
               FROM deck_version_cards WHERE deck_version_id=? ORDER BY ordinal""",
            (version["id"],),
        ).fetchall()
        results: list[dict[str, Any]] = []
        counts = {"resolved": 0, "ambiguous": 0, "unresolved": 0}
        for entry in entries:
            if not entry["set_code"] or not entry["collector_number"]:
                state, candidates, reason = "unresolved", [], "code d'extension ou numéro absent"
            else:
                rows = connection.execute(
                    """SELECT DISTINCT p.tcgdex_id, t.name
                       FROM catalog_printings p
                       JOIN catalog_sets s ON s.tcgdex_id=p.set_id
                       LEFT JOIN catalog_translations t ON t.printing_id=p.tcgdex_id
                       WHERE lower(s.tcg_online_code)=lower(?) AND p.local_id=?""",
                    (entry["set_code"], entry["collector_number"]),
                ).fetchall()
                exact_name = [
                    row for row in rows
                    if _normalized_identity_name(row["name"])
                    == _normalized_identity_name(entry["card_name"])
                ]
                ids = sorted({str(row["tcgdex_id"]) for row in exact_name})
                if len(ids) == 1:
                    state, candidates, reason = "resolved", ids, "code TCG Online, numéro et nom concordent"
                elif len(ids) > 1:
                    state, candidates, reason = "ambiguous", ids, "plusieurs impressions concordent"
                else:
                    state, candidates, reason = "unresolved", [], "aucune correspondance vérifiée"
            counts[state] += 1
            results.append({
                "ordinal": int(entry["ordinal"]),
                "quantity": int(entry["quantity"]),
                "card_name": entry["card_name"],
                "set_code": entry["set_code"],
                "collector_number": entry["collector_number"],
                "status": state,
                "tcgdex_ids": candidates,
                "reason": reason,
            })
        return {
            "deck_id": deck_id,
            "deck_version": int(version["version_number"]),
            "read_only": True,
            "counts": counts,
            "entries": results,
            "limits": [
                "Un code TCG Live n'est jamais supposé égal à un ID de set TCGdex.",
                "Ce diagnostic ne modifie ni le deck, ni les combats, ni les crédits.",
            ],
        }
    finally:
        connection.close()
