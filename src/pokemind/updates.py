"""Actualisation locale, bornée et sans LLM des connaissances publiques."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import socket
import time
from dataclasses import dataclass
from datetime import date, datetime, time as clock_time, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pokemind.cards import CatalogApiClient, sync_cards
from pokemind.database import SCHEMA_VERSION, connect_readonly, connect_writable, initialize_schema
from pokemind.meta import LimitlessApiClient, sync_meta
from pokemind.toronto_tz import toronto_zone


TORONTO_ZONE = "America/Toronto"
OFFICIAL_MAX_BYTES = 512 * 1024
OFFICIAL_USER_AGENT = "PokeMind/0.8 (+bounded public knowledge updater)"
SOURCE_NAMES = ("tcgdex", "pokemon_official", "limitless")
UPDATE_MODES = ("daily", "deep", "auto")
DEFAULT_BUDGETS = {
    "daily": {"tcgdex": 4, "pokemon_official": 2, "limitless": 4},
    "deep": {"tcgdex": 20, "pokemon_official": 4, "limitless": 10},
}
_SAFE_SOURCE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")


class UpdateError(ValueError):
    """Erreur contrôlée de l'orchestrateur public."""


class UpdateLocked(UpdateError):
    """Une autre exécution possède le verrou local."""


class OfficialNetworkFailure(UpdateError):
    """Une source Pokémon officielle n'a pas pu être sondée."""


class OfficialBudgetExhausted(OfficialNetworkFailure):
    """Budget GET officiel épuisé."""


def _utc_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _tables(connection: Any) -> set[str]:
    return {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _parse_local_time(value: str | None) -> clock_time | None:
    if value is None:
        return None
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
        raise UpdateError("L'heure locale doit être HH:MM sur 24 heures.")
    hour, minute = (int(part) for part in value.split(":"))
    return clock_time(hour, minute)


def deep_schedule_due(
    now_utc: datetime,
    *,
    local_time: str | None,
    completed_local_dates: Iterable[str] = (),
    lookback_days: int = 14,
) -> dict[str, Any]:
    """Calcule un cycle mardi/vendredi sans supposer une machine toujours allumée."""
    if now_utc.tzinfo is None:
        raise UpdateError("UPDATE_CLOCK_TIMEZONE_REQUIRED")
    scheduled_time = _parse_local_time(local_time)
    local_now = now_utc.astimezone(toronto_zone())
    base = {
        "timezone": TORONTO_ZONE,
        "local_now": local_now.replace(microsecond=0).isoformat(),
        "configured": scheduled_time is not None,
        "scheduled_local_time": local_time,
        "holiday_policy": "run_normally; no holiday calendar assumption",
        "due": False,
        "scheduled_local_date": None,
        "reason": "SCHEDULE_TIME_NOT_CONFIGURED" if scheduled_time is None else "NOT_DUE",
    }
    if scheduled_time is None:
        return base
    if not 1 <= lookback_days <= 60:
        raise UpdateError("La fenêtre de rattrapage doit être comprise entre 1 et 60 jours.")
    completed = {date.fromisoformat(item).isoformat() for item in completed_local_dates}
    scheduled_dates: list[date] = []
    for offset in range(lookback_days - 1, -1, -1):
        candidate = local_now.date() - timedelta(days=offset)
        if candidate.weekday() not in {1, 4}:  # mardi / vendredi
            continue
        scheduled = datetime.combine(candidate, scheduled_time, tzinfo=toronto_zone())
        if scheduled <= local_now:
            scheduled_dates.append(candidate)
    if not scheduled_dates:
        return base
    # Une seule réconciliation de rattrapage suffit : seule la plus récente
    # échéance est pertinente. Une échéance plus récente complétée couvre donc les
    # anciennes fenêtres manquées au lieu de provoquer une rafale rétroactive.
    selected = scheduled_dates[-1]
    if selected.isoformat() in completed:
        return base
    return {
        **base,
        "due": True,
        "scheduled_local_date": selected.isoformat(),
        "reason": "SCHEDULED_TODAY" if selected == local_now.date() else "CATCH_UP_AFTER_DOWNTIME",
    }


def _completed_deep_dates(db_path: Path) -> list[str]:
    if not db_path.is_file():
        return []
    connection = connect_readonly(db_path)
    try:
        if "knowledge_update_cycles" not in _tables(connection):
            return []
        return [
            str(row[0]) for row in connection.execute(
                """SELECT DISTINCT scheduled_local_date FROM knowledge_update_cycles
                   WHERE mode='deep' AND status='completed' AND scheduled_local_date IS NOT NULL"""
            ).fetchall()
        ]
    finally:
        connection.close()


def plan_public_update(
    db_path: Path,
    *,
    mode: str = "daily",
    now_utc: datetime | None = None,
    deep_local_time: str | None = None,
    budgets: dict[str, int] | None = None,
) -> dict[str, Any]:
    if mode not in UPDATE_MODES:
        raise UpdateError("--mode doit être daily, deep ou auto.")
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise UpdateError("L'horloge doit inclure un fuseau horaire.")
    schedule = deep_schedule_due(
        now,
        local_time=deep_local_time,
        completed_local_dates=_completed_deep_dates(db_path),
    )
    resolved_mode = "deep" if mode == "auto" and schedule["due"] else ("daily" if mode == "auto" else mode)
    selected = dict(DEFAULT_BUDGETS[resolved_mode])
    if budgets:
        for source, value in budgets.items():
            if source not in SOURCE_NAMES or isinstance(value, bool) or not 1 <= int(value) <= 1000:
                raise UpdateError("Budget de source invalide.")
            selected[source] = int(value)
    total = sum(selected.values())
    local_now = now.astimezone(toronto_zone())
    discovery_complete = False
    if db_path.is_file():
        connection = connect_readonly(db_path)
        try:
            if "catalog_sync_state" in _tables(connection):
                completed = {row[0] for row in connection.execute("SELECT scope FROM catalog_sync_state WHERE completed=1")}
                discovery_complete = {f"{kind}:{lang}" for kind in ("sets", "cards") for lang in ("en", "fr")}.issubset(completed)
        finally:
            connection.close()
    return {
        "requested_mode": mode,
        "mode": resolved_mode,
        "timezone": TORONTO_ZONE,
        "local_time": local_now.replace(microsecond=0).isoformat(),
        "scheduled_local_date": schedule["scheduled_local_date"] if resolved_mode == "deep" else None,
        "schedule": schedule,
        "budgets": selected,
        "global_request_budget": total,
        "sources": {
            "tcgdex": {
                "phase": "index" if resolved_mode == "daily" else "balanced",
                "refresh_index": resolved_mode == "daily" or discovery_complete,
                "initial_discovery_complete": discovery_complete,
                "languages": ["en", "fr"],
            },
            "pokemon_official": {
                "probe_count": selected["pokemon_official"],
                "normative_promotion": False,
                "changed_content_status": "conflict",
            },
            "limitless": {
                "mode": "discover" if resolved_mode == "daily" else "refresh",
                "format": "standard",
                "platform": "PTCGL",
                "online": True,
            },
        },
        "dry_run_contract": {"network_used": False, "writes": 0, "would_migrate": _schema_version(db_path) < SCHEMA_VERSION},
    }


def _schema_version(db_path: Path) -> int:
    if not db_path.is_file():
        return 0
    connection = connect_readonly(db_path)
    try:
        return int(connection.execute("PRAGMA user_version").fetchone()[0])
    finally:
        connection.close()


def _validate_official_url(url: str) -> str:
    parsed = urlparse(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise UpdateError("Port de source officielle invalide.") from exc
    hostname = (parsed.hostname or "").casefold()
    allowed = hostname == "pokemon.com" or hostname.endswith(".pokemon.com")
    if (
        parsed.scheme != "https" or not allowed or port is not None
        or parsed.username is not None or parsed.password is not None or parsed.fragment
    ):
        raise UpdateError("Seules les URL HTTPS officielles pokemon.com sans identifiants sont autorisées.")
    if not parsed.path.startswith("/"):
        raise UpdateError("Chemin officiel invalide.")
    return url


class _OfficialRedirectHandler(HTTPRedirectHandler):
    def __init__(self, reserve: Callable[[], None], validate: Callable[[str], str]) -> None:
        super().__init__()
        self._reserve = reserve
        self._validate = validate

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        if req.get_method() != "GET":
            raise OfficialNetworkFailure("Redirection officielle non-GET refusée.")
        self._validate(newurl)
        self._reserve()
        return super().redirect_request(req, fp, code, msg, headers, newurl)


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


class OfficialSourceClient:
    """GET bornés, arrêt sur refus optionnel; aucune validation normative implicite."""

    def __init__(
        self,
        max_requests: int,
        *,
        timeout: float = 15.0,
        interval: float = 0.25,
        opener: Any | None = None,
        sleep: Callable[[float], None] = time.sleep,
        allowed_urls: Iterable[str] | None = None,
        stop_on_access_denial: bool = False,
    ) -> None:
        if not 1 <= max_requests <= 20:
            raise UpdateError("Budget Pokémon officiel invalide (1-20).")
        self.max_requests = max_requests
        self.requests_made = 0
        self.stop_on_access_denial = stop_on_access_denial
        self.blocked_reason: str | None = None
        self.timeout = timeout
        self.interval = max(0.0, interval)
        self._sleep = sleep
        self._allowed_urls = (
            frozenset(_validate_official_url(url) for url in allowed_urls)
            if allowed_urls is not None else None
        )
        self._opener = opener or build_opener(_OfficialRedirectHandler(self._reserve, self._validate_target))

    @property
    def remaining(self) -> int:
        return self.max_requests - self.requests_made

    def _reserve(self) -> None:
        if self.blocked_reason:
            raise OfficialNetworkFailure(self.blocked_reason)
        if self.remaining <= 0:
            raise OfficialBudgetExhausted("Budget Pokémon officiel épuisé.")
        if self.requests_made:
            self._sleep(self.interval)
        self.requests_made += 1

    def _validate_target(self, url: str) -> str:
        validated = _validate_official_url(url)
        if self._allowed_urls is not None and validated not in self._allowed_urls:
            raise UpdateError("Endpoint Pokémon officiel absent du registre allowlisté.")
        return validated

    def probe(self, url: str, *, etag: str | None = None, last_modified: str | None = None) -> dict[str, Any]:
        self._validate_target(url)
        attempt = 0
        while True:
            self._reserve()
            attempt += 1
            headers = {"Accept": "text/html,application/pdf;q=0.9,*/*;q=0.1", "User-Agent": OFFICIAL_USER_AGENT}
            if etag:
                headers["If-None-Match"] = etag
            if last_modified:
                headers["If-Modified-Since"] = last_modified
            request = Request(url, headers=headers, method="GET")
            try:
                response = self._opener.open(request, timeout=self.timeout)
                try:
                    final_url = self._validate_target(response.geturl())
                    raw = response.read(OFFICIAL_MAX_BYTES + 1)
                    truncated = len(raw) > OFFICIAL_MAX_BYTES
                    body = raw[:OFFICIAL_MAX_BYTES]
                    if self.stop_on_access_denial and (
                        response.headers.get("cf-mitigated") == "challenge"
                        or any(token in body.lower() for token in (
                            b"/cdn-cgi/challenge-platform/", b"verify you are human", b"<title>access denied",
                            b"pardon our interruption", b"made us think you were a bot",
                        ))
                    ):
                        self.blocked_reason = "PUBLIC_SOURCE_CHALLENGE_BLOCKED"
                        raise OfficialNetworkFailure(self.blocked_reason)
                    return {
                        "source_url": final_url,
                        "http_status": int(getattr(response, "status", 200)),
                        "content_type": (response.headers.get("Content-Type") or "")[:200],
                        "content_length": int(response.headers.get("Content-Length")) if (response.headers.get("Content-Length") or "").isdigit() else None,
                        "etag": (response.headers.get("ETag") or "")[:500] or None,
                        "last_modified": (response.headers.get("Last-Modified") or "")[:200] or None,
                        "content_sha256": hashlib.sha256(body).hexdigest() if body else None,
                        "truncated": truncated,
                        "not_modified": False,
                    }
                finally:
                    response.close()
            except HTTPError as exc:
                if self.stop_on_access_denial and exc.code in {401, 403, 429}:
                    self.blocked_reason = f"PUBLIC_SOURCE_HTTP_{exc.code}_BLOCKED"
                    exc.close()
                    raise OfficialNetworkFailure(self.blocked_reason) from exc
                if exc.code == 304:
                    return {
                        "source_url": url, "http_status": 304, "content_type": None,
                        "content_length": None, "etag": etag, "last_modified": last_modified,
                        "content_sha256": None, "truncated": False, "not_modified": True,
                    }
                if exc.code == 404:
                    return {
                        "source_url": url, "http_status": 404, "content_type": None,
                        "content_length": None, "etag": None, "last_modified": None,
                        "content_sha256": None, "truncated": False, "not_modified": False,
                    }
                retryable = exc.code == 429 or 500 <= exc.code <= 599
                if retryable and attempt < 3 and self.remaining > 0:
                    self._sleep(_retry_delay(exc.headers.get("Retry-After"), attempt))
                    continue
                raise OfficialNetworkFailure(f"SOURCE_HTTP_{exc.code}") from exc
            except (URLError, TimeoutError, socket.timeout, OSError) as exc:
                if attempt < 3 and self.remaining > 0:
                    self._sleep(_retry_delay(None, attempt))
                    continue
                raise OfficialNetworkFailure("SOURCE_NETWORK_UNAVAILABLE") from exc


@dataclass(slots=True)
class _UpdateLock:
    path: Path
    now: datetime
    stale_after: timedelta = timedelta(hours=6)
    acquired: bool = False

    def __enter__(self) -> "_UpdateLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"created_at": _utc_text(self.now), "kind": "pokemind-public-update-lock"}
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                existing = json.loads(self.path.read_text(encoding="utf-8"))
                created = datetime.fromisoformat(str(existing["created_at"]).replace("Z", "+00:00"))
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                raise UpdateLocked("UPDATE_LOCKED_UNREADABLE") from None
            if self.now.astimezone(timezone.utc) - created.astimezone(timezone.utc) <= self.stale_after:
                raise UpdateLocked("UPDATE_ALREADY_RUNNING")
            stale = self.path.with_name(f"{self.path.name}.stale-{self.now.strftime('%Y%m%dT%H%M%SZ')}")
            try:
                os.replace(self.path, stale)
                descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except OSError as exc:
                raise UpdateLocked("UPDATE_STALE_LOCK_RECOVERY_FAILED") from exc
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(_canonical_json(payload))
        self.acquired = True
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if self.acquired:
            try:
                self.path.unlink(missing_ok=True)
            finally:
                self.acquired = False


def _read_registry_sources(registry_path: Path) -> list[dict[str, str]]:
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    raw_sources = payload.get("sources") if isinstance(payload, dict) else None
    if not isinstance(raw_sources, list):
        raise UpdateError("Registre officiel invalide.")
    sources: list[dict[str, str]] = []
    for source in raw_sources:
        if not isinstance(source, dict):
            raise UpdateError("Source officielle invalide.")
        source_id = source.get("source_id")
        url = source.get("url")
        if not isinstance(source_id, str) or not _SAFE_SOURCE_ID.fullmatch(source_id):
            raise UpdateError("Identifiant de source officielle invalide.")
        if not isinstance(url, str):
            raise UpdateError("URL officielle invalide.")
        sources.append({"source_id": source_id, "url": _validate_official_url(url)})
    return sources


def _last_observations(db_path: Path) -> dict[str, dict[str, Any]]:
    if not db_path.is_file():
        return {}
    connection = connect_readonly(db_path)
    try:
        if "public_source_observations" not in _tables(connection):
            return {}
        rows = connection.execute(
            """SELECT p.* FROM public_source_observations p
               JOIN (SELECT source_id, MAX(id) AS id FROM public_source_observations GROUP BY source_id) x
               ON x.id=p.id"""
        ).fetchall()
        return {str(row["source_id"]): dict(row) for row in rows}
    finally:
        connection.close()


def _select_registry_sources(db_path: Path, registry_path: Path, limit: int) -> list[dict[str, str]]:
    sources = _read_registry_sources(registry_path)
    previous = _last_observations(db_path)
    return sorted(
        sources,
        key=lambda item: (str(previous.get(item["source_id"], {}).get("observed_at") or ""), item["source_id"]),
    )[:limit]


def _begin_cycle(db_path: Path, cycle: dict[str, Any], plan: dict[str, Any], now: datetime) -> None:
    connection = connect_writable(db_path)
    try:
        initialize_schema(connection)
        with connection:
            connection.execute(
                """INSERT INTO knowledge_update_cycles
                   (cycle_id,mode,scope_json,scheduled_local_date,started_at_utc,started_at_local,
                    completed_at_utc,status,timezone,request_budget,requests_attempted,report_json,error_code,config_sha256)
                   VALUES(?,?,?,?,?,?,NULL,'attempted',?,?,0,'{}',NULL,?)""",
                (
                    cycle["cycle_id"], plan["mode"], _canonical_json(plan["sources"]),
                    plan["scheduled_local_date"], _utc_text(now), plan["local_time"],
                    TORONTO_ZONE, plan["global_request_budget"], cycle["config_sha256"],
                ),
            )
            for source in SOURCE_NAMES:
                connection.execute(
                    """INSERT INTO knowledge_update_source_runs
                       (cycle_id,source,state,request_budget,validation_status,detail_json)
                       VALUES(?,?,'planned',?,'not_applicable','{}')""",
                    (cycle["cycle_id"], source, plan["budgets"][source]),
                )
    finally:
        connection.close()


def _finish_source(db_path: Path, cycle_id: str, source: str, result: dict[str, Any], now: datetime) -> None:
    connection = connect_writable(db_path)
    try:
        with connection:
            connection.execute(
                """UPDATE knowledge_update_source_runs SET
                   state=?,started_at_utc=COALESCE(started_at_utc,?),completed_at_utc=?,
                   requests_attempted=?,new_count=?,changed_count=?,missing_count=?,unknown_count=?,
                   source_url=?,captured_at=?,validation_status=?,reason_code=?,detail_json=?
                   WHERE cycle_id=? AND source=?""",
                (
                    result["state"], _utc_text(now), _utc_text(now), result["requests_attempted"],
                    result["new"], result["changed"], result["missing"], result["unknown"],
                    result.get("source_url"), result.get("captured_at"), result["validation_status"],
                    result.get("reason_code"), _canonical_json(result.get("detail", {})), cycle_id, source,
                ),
            )
    finally:
        connection.close()


def _cards_result(raw: dict[str, Any]) -> dict[str, Any]:
    pages = raw.get("pages", [])
    details = raw.get("details", {})
    error = raw.get("error")
    stopped = raw.get("stopped_reason")
    completed_scopes = {
        str(page.get("scope")) for page in pages if page.get("completed")
    }
    bounded_index_complete = raw.get("phase") == "index" and completed_scopes == {
        "sets:en", "sets:fr", "cards:en", "cards:fr"
    }
    state = (
        "partial"
        if error or stopped == "source_error" or (stopped == "budget_exhausted" and not bounded_index_complete)
        else "completed"
    )
    return {
        "state": state,
        "requests_attempted": int(raw.get("requests_made", 0)),
        "new": sum(int(page.get("new_items", 0)) for page in pages),
        "changed": sum(int(page.get("changed_items", 0)) for page in pages),
        "missing": int(details.get("sets_absent", 0)) + int(details.get("cards_absent", 0)),
        "unknown": int(bool(error)),
        "validation_status": "not_applicable",
        "reason_code": "TCGDEX_SOURCE_ERROR" if error else ("BUDGET_CHECKPOINTED" if stopped == "budget_exhausted" else None),
        "source_url": "https://api.tcgdex.net/v2",
        "captured_at": None,
        "detail": {"stopped_reason": stopped, "pages": len(pages), "phase": raw.get("phase")},
    }


def _meta_result(raw: dict[str, Any]) -> dict[str, Any]:
    stopped = raw.get("stopped_reason")
    error = raw.get("error")
    state = "partial" if error or stopped in {"source_error", "rate_limited", "budget_exhausted"} else "completed"
    return {
        "state": state,
        "requests_attempted": int(raw.get("requests_made", 0)),
        "new": len(raw.get("imported", [])) if raw.get("mode") == "discover" else 0,
        "changed": len(raw.get("imported", [])) if raw.get("mode") == "refresh" else 0,
        "missing": len(raw.get("skipped", [])),
        "unknown": int(bool(error)),
        "validation_status": "not_applicable",
        "reason_code": "LIMITLESS_SOURCE_ERROR" if error else ("BUDGET_CHECKPOINTED" if stopped == "budget_exhausted" else None),
        "source_url": "https://play.limitlesstcg.com/api",
        "captured_at": None,
        "detail": {"stopped_reason": stopped, "mode": raw.get("mode"), "imported": len(raw.get("imported", []))},
    }


def _probe_official_sources(
    db_path: Path,
    registry_path: Path,
    *,
    client: Any | None,
    budget: int,
    observed_at: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, str]]]:
    selected = _select_registry_sources(db_path, registry_path, budget)
    actual_client = client or OfficialSourceClient(
        budget, allowed_urls=[source["url"] for source in selected]
    )
    previous = _last_observations(db_path)
    observations: list[dict[str, Any]] = []
    alerts: list[dict[str, str]] = []
    errors = 0
    for source in selected:
        old = previous.get(source["source_id"])
        try:
            probe = actual_client.probe(
                source["url"],
                etag=old.get("etag") if old else None,
                last_modified=old.get("last_modified") if old else None,
            )
            if probe.get("not_modified"):
                state = "unchanged"
                digest = old.get("content_sha256") if old else None
            elif int(probe.get("http_status", 0)) == 404:
                state, digest = "missing", None
            else:
                digest = probe.get("content_sha256")
                old_signature = (old.get("etag"), old.get("last_modified"), old.get("content_sha256")) if old else None
                new_signature = (probe.get("etag"), probe.get("last_modified"), digest)
                state = "new" if old is None else ("changed" if old_signature != new_signature else "unchanged")
            validation = "conflict" if state == "changed" else "non_verified"
            observation = {
                "source_id": source["source_id"], "source_url": probe.get("source_url", source["url"]),
                "observed_at": observed_at, "http_status": probe.get("http_status"),
                "content_type": probe.get("content_type"), "content_length": probe.get("content_length"),
                "etag": probe.get("etag"), "last_modified": probe.get("last_modified"),
                "content_sha256": digest, "truncated": bool(probe.get("truncated")),
                "observation_state": state, "validation_status": validation,
            }
            observations.append(observation)
            if state == "changed":
                alerts.append({
                    "source": "pokemon_official", "severity": "warning",
                    "code": "OFFICIAL_SOURCE_CHANGED_REQUIRES_VALIDATION",
                    "message": "Une source officielle publique a changé; l'ancien contenu normatif reste en vigueur jusqu'à validation datée.",
                })
        except (UpdateError, OSError):
            errors += 1
    requests = int(getattr(actual_client, "requests_made", 0))
    changed = sum(item["observation_state"] == "changed" for item in observations)
    missing = sum(item["observation_state"] == "missing" for item in observations)
    new = sum(item["observation_state"] == "new" for item in observations)
    state = "completed" if errors == 0 and len(observations) == len(selected) else "partial"
    result = {
        "state": state, "requests_attempted": requests, "new": new, "changed": changed,
        "missing": missing, "unknown": errors,
        "validation_status": "conflict" if changed else "non_verified",
        "reason_code": "OFFICIAL_SOURCE_PROBE_PARTIAL" if errors else None,
        "source_url": "https://www.pokemon.com/",
        "captured_at": observed_at,
        "detail": {"selected": len(selected), "observed": len(observations), "normative_promotion": False},
    }
    return result, observations, alerts


def _store_official_observations(db_path: Path, observations: list[dict[str, Any]]) -> None:
    if not observations:
        return
    connection = connect_writable(db_path)
    try:
        with connection:
            connection.executemany(
                """INSERT INTO public_source_observations
                   (source_id,source_url,observed_at,http_status,content_type,content_length,
                    etag,last_modified,content_sha256,truncated,observation_state,validation_status)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                [
                    (
                        item["source_id"], item["source_url"], item["observed_at"], item["http_status"],
                        item["content_type"], item["content_length"], item["etag"], item["last_modified"],
                        item["content_sha256"], int(item["truncated"]), item["observation_state"],
                        item["validation_status"],
                    )
                    for item in observations
                ],
            )
    finally:
        connection.close()


def _finish_cycle(
    db_path: Path,
    cycle_id: str,
    results: dict[str, dict[str, Any]],
    alerts: list[dict[str, str]],
    now: datetime,
) -> dict[str, Any]:
    states = [results[source]["state"] for source in SOURCE_NAMES]
    status = "completed" if all(state == "completed" for state in states) else (
        "blocked" if all(state == "blocked" for state in states) else "partial"
    )
    requests = sum(results[source]["requests_attempted"] for source in SOURCE_NAMES)
    check = connect_readonly(db_path)
    try:
        for source in SOURCE_NAMES:
            incomplete = 0
            for row in check.execute(
                "SELECT state FROM knowledge_update_source_runs WHERE source=? ORDER BY id DESC LIMIT 20",
                (source,),
            ).fetchall():
                if row[0] == "completed":
                    break
                incomplete += 1
            if incomplete >= 3:
                alerts.append({
                    "source": source, "severity": "warning", "code": "SOURCE_FAILURE_PROLONGED",
                    "message": "Trois cycles consécutifs ou plus sont incomplets; le dernier état public valide reste conservé.",
                })
    finally:
        check.close()
    report = {
        "cycle_id": cycle_id,
        "status": status,
        "requests_attempted": requests,
        "sources": {
            source: {
                "state": results[source]["state"],
                "new": results[source]["new"],
                "changed": results[source]["changed"],
                "missing": results[source]["missing"],
                "unknown": results[source]["unknown"],
                "reason_code": results[source].get("reason_code"),
                "validation_status": results[source]["validation_status"],
            }
            for source in SOURCE_NAMES
        },
        "alerts": [{"source": item["source"], "severity": item["severity"], "code": item["code"]} for item in alerts],
    }
    connection = connect_writable(db_path)
    try:
        with connection:
            for alert in alerts:
                connection.execute(
                    """INSERT OR IGNORE INTO knowledge_update_alerts
                       (cycle_id,created_at,source,severity,code,message,status)
                       VALUES(?,?,?,?,?,?,'open')""",
                    (cycle_id, _utc_text(now), alert["source"], alert["severity"], alert["code"], alert["message"]),
                )
            connection.execute(
                """UPDATE knowledge_update_cycles SET completed_at_utc=?,status=?,requests_attempted=?,
                   report_json=?,error_code=? WHERE cycle_id=?""",
                (
                    _utc_text(now), status, requests, _canonical_json(report),
                    None if status == "completed" else "ONE_OR_MORE_SOURCES_INCOMPLETE", cycle_id,
                ),
            )
    finally:
        connection.close()
    return report


def _append_local_log(db_path: Path, report: dict[str, Any], now: datetime) -> str | None:
    log_dir = db_path.parent / "update-logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"knowledge-{now.astimezone(toronto_zone()).date().isoformat()}.jsonl"
        with log_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(_canonical_json(report) + "\n")
        return None
    except OSError:
        return "LOCAL_LOG_WRITE_FAILED"


def run_public_update(
    db_path: Path,
    registry_path: Path,
    *,
    mode: str = "daily",
    dry_run: bool = True,
    apply: bool = False,
    confirm_owner: bool = False,
    probe_public_network: bool = False,
    deep_local_time: str | None = None,
    now_utc: datetime | None = None,
    budgets: dict[str, int] | None = None,
    cards_client: Any | None = None,
    official_client: Any | None = None,
    meta_client: Any | None = None,
) -> dict[str, Any]:
    if dry_run and apply:
        raise UpdateError("Choisir --dry-run ou --apply, pas les deux.")
    if apply and not confirm_owner:
        raise UpdateError("--apply exige --confirm-owner pour actualiser les données publiques locales.")
    if probe_public_network and apply:
        raise UpdateError("--probe-public-network est réservé à un dry-run sans écriture.")
    now = now_utc or datetime.now(timezone.utc)
    plan = plan_public_update(db_path, mode=mode, now_utc=now, deep_local_time=deep_local_time, budgets=budgets)
    if not apply:
        result = {
            "mode": "dry_run", "status": "PLANNED", "read_only": True,
            "network_used": False, "writes": 0, "plan": plan,
        }
        if not probe_public_network:
            return result
        selected = _select_registry_sources(db_path, registry_path, 1)
        if not selected:
            return {**result, "status": "PROBE_BLOCKED", "probe": {"reason_code": "NO_OFFICIAL_SOURCE"}}
        client = official_client or OfficialSourceClient(1, allowed_urls=[selected[0]["url"]])
        try:
            probe = client.probe(selected[0]["url"])
            return {
                **result, "status": "PROBE_COMPLETED", "network_used": True,
                "probe": {"source_id": selected[0]["source_id"], "http_status": probe.get("http_status"),
                          "requests_attempted": int(getattr(client, "requests_made", 0)), "writes": 0,
                          "validation_status": "non_verified"},
            }
        except UpdateError:
            return {
                **result, "status": "PROBE_PARTIAL", "network_used": bool(getattr(client, "requests_made", 0)),
                "probe": {"source_id": selected[0]["source_id"], "reason_code": "PUBLIC_PROBE_FAILED",
                          "requests_attempted": int(getattr(client, "requests_made", 0)), "writes": 0},
            }
    cycle_id = f"update-{plan['mode']}-{now.astimezone(toronto_zone()).strftime('%Y%m%d')}-{secrets.token_hex(6)}"
    cycle = {"cycle_id": cycle_id, "config_sha256": _sha256(plan)}
    lock_path = db_path.parent / "knowledge-update.lock"
    with _UpdateLock(lock_path, now):
        _begin_cycle(db_path, cycle, plan, now)
        results: dict[str, dict[str, Any]] = {}
        alerts: list[dict[str, str]] = []
        card_budget = plan["budgets"]["tcgdex"]
        effective_cards_client = cards_client
        try:
            if effective_cards_client is None:
                effective_cards_client = CatalogApiClient(card_budget)
            raw_cards = sync_cards(
                db_path, languages="en,fr", max_requests=card_budget, dry_run=False,
                phase=plan["sources"]["tcgdex"]["phase"],
                refresh_index=plan["sources"]["tcgdex"]["refresh_index"],
                client=effective_cards_client,
            )
            results["tcgdex"] = _cards_result(raw_cards)
        except Exception:
            results["tcgdex"] = {
                "state": "partial",
                "requests_attempted": int(getattr(effective_cards_client, "requests_made", 0)),
                "new": 0, "changed": 0, "missing": 0, "unknown": 1,
                "validation_status": "not_applicable", "reason_code": "TCGDEX_COLLECTOR_FAILED",
                "source_url": "https://api.tcgdex.net/v2", "captured_at": None, "detail": {},
            }
        _finish_source(db_path, cycle_id, "tcgdex", results["tcgdex"], now)

        official_budget = plan["budgets"]["pokemon_official"]
        try:
            official_result, observations, official_alerts = _probe_official_sources(
                db_path, registry_path, client=official_client, budget=official_budget, observed_at=_utc_text(now),
            )
            _store_official_observations(db_path, observations)
            results["pokemon_official"] = official_result
            alerts.extend(official_alerts)
        except Exception:
            results["pokemon_official"] = {
                "state": "partial", "requests_attempted": int(getattr(official_client, "requests_made", 0)),
                "new": 0, "changed": 0, "missing": 0, "unknown": 1,
                "validation_status": "non_verified", "reason_code": "OFFICIAL_COLLECTOR_FAILED",
                "source_url": "https://www.pokemon.com/", "captured_at": _utc_text(now), "detail": {},
            }
        _finish_source(db_path, cycle_id, "pokemon_official", results["pokemon_official"], now)

        meta_budget = plan["budgets"]["limitless"]
        effective_meta_client = meta_client
        try:
            if effective_meta_client is None:
                effective_meta_client = LimitlessApiClient(meta_budget)
            raw_meta = sync_meta(
                db_path, max_requests=meta_budget, max_tournaments=1 if plan["mode"] == "daily" else 2,
                format="standard", platform="PTCGL", online=True,
                mode=plan["sources"]["limitless"]["mode"], dry_run=False,
                client=effective_meta_client,
            )
            results["limitless"] = _meta_result(raw_meta)
        except Exception:
            results["limitless"] = {
                "state": "partial",
                "requests_attempted": int(getattr(effective_meta_client, "requests_made", 0)),
                "new": 0, "changed": 0, "missing": 0, "unknown": 1,
                "validation_status": "not_applicable", "reason_code": "LIMITLESS_COLLECTOR_FAILED",
                "source_url": "https://play.limitlesstcg.com/api", "captured_at": None, "detail": {},
            }
        _finish_source(db_path, cycle_id, "limitless", results["limitless"], now)
        report = _finish_cycle(db_path, cycle_id, results, alerts, now)
        log_warning = _append_local_log(db_path, report, now)
        return {
            "mode": "applied", "read_only": False, "network_used": report["requests_attempted"] > 0,
            "public_data_only": True, "cycle_id": cycle_id, "status": report["status"].upper(),
            "plan": plan, "report": report, "log_warning": log_warning,
        }


def update_status(
    db_path: Path,
    *,
    now_utc: datetime | None = None,
    deep_local_time: str | None = None,
) -> dict[str, Any]:
    now = now_utc or datetime.now(timezone.utc)
    base = {
        "offline": True, "read_only": True, "network_used": False,
        "schema_version": _schema_version(db_path), "schema_current": _schema_version(db_path) == SCHEMA_VERSION,
        "schedule": deep_schedule_due(
            now, local_time=deep_local_time, completed_local_dates=_completed_deep_dates(db_path)
        ),
        "last_cycle": None, "sources": {}, "open_alerts": [],
    }
    if not db_path.is_file():
        return {**base, "status": "NOT_CONFIGURED"}
    connection = connect_readonly(db_path)
    try:
        if "knowledge_update_cycles" not in _tables(connection):
            return {**base, "status": "SCHEMA_MIGRATION_REQUIRED"}
        cycle = connection.execute(
            """SELECT cycle_id,mode,scheduled_local_date,started_at_utc,started_at_local,
                      completed_at_utc,status,request_budget,requests_attempted,error_code
               FROM knowledge_update_cycles ORDER BY started_at_utc DESC,cycle_id DESC LIMIT 1"""
        ).fetchone()
        source_status: dict[str, Any] = {}
        for source in SOURCE_NAMES:
            last = connection.execute(
                """SELECT state,completed_at_utc,requests_attempted,new_count,changed_count,
                          missing_count,unknown_count,reason_code,validation_status
                   FROM knowledge_update_source_runs WHERE source=?
                   ORDER BY id DESC LIMIT 1""",
                (source,),
            ).fetchone()
            success = connection.execute(
                """SELECT completed_at_utc FROM knowledge_update_source_runs
                   WHERE source=? AND state='completed' ORDER BY id DESC LIMIT 1""",
                (source,),
            ).fetchone()
            failures = 0
            for row in connection.execute(
                "SELECT state FROM knowledge_update_source_runs WHERE source=? ORDER BY id DESC LIMIT 20",
                (source,),
            ).fetchall():
                if row[0] == "completed":
                    break
                failures += 1
            source_status[source] = {
                "last_attempt": dict(last) if last else None,
                "last_successful": str(success[0]) if success else None,
                "consecutive_incomplete": failures,
            }
        alerts = [
            dict(row) for row in connection.execute(
                """SELECT created_at,source,severity,code,message,status
                   FROM knowledge_update_alerts WHERE status='open' ORDER BY id DESC LIMIT 100"""
            ).fetchall()
        ]
        return {
            **base,
            "status": "AVAILABLE" if cycle else "NO_CYCLES",
            "last_cycle": dict(cycle) if cycle else None,
            "sources": source_status,
            "open_alerts": alerts,
        }
    finally:
        connection.close()


def official_validation_queue(db_path: Path) -> dict[str, Any]:
    """Expose pending public-source reviews without promoting a hash to a rule."""
    base = {"read_only": True, "network_used": False, "normative_promotion": False,
            "count": 0, "entries": [], "counts": {"truncated": 0, "changed": 0, "missing": 0, "unreviewed": 0}}
    if not db_path.is_file():
        return base
    connection = connect_readonly(db_path)
    try:
        if "public_source_observations" not in _tables(connection):
            return base
        rows = connection.execute(
            """SELECT p.* FROM public_source_observations p
               JOIN (SELECT source_id,MAX(id) AS id FROM public_source_observations GROUP BY source_id) latest
               ON latest.id=p.id ORDER BY p.source_id"""
        ).fetchall()
        entries = []
        for row in rows:
            from pokemind.official_reviews import official_review
            review = official_review(connection, row)
            reasons = ["CONTENT_REVIEW_REQUIRED"]
            if review.get("current") and review["status"] == "verified":
                reasons = ["ASSERTION_RECONCILIATION_REQUIRED"]
            if row["truncated"]:
                reasons.append("BOUNDED_HASH_NOT_FULL_CONTENT")
            if row["observation_state"] in {"changed", "missing", "unknown"}:
                reasons.append("SOURCE_STATE_REQUIRES_RECONCILIATION")
            entries.append({"source_id": row["source_id"], "source_url": row["source_url"],
                            "observed_at": row["observed_at"], "http_status": row["http_status"],
                            "state": row["observation_state"], "validation_status": row["validation_status"],
                            "hash_scope": "bounded_prefix" if row["truncated"] else "response_body",
                            "document_review": review,
                            "reason_codes": reasons, "next_action": "Review full authorized source, date and relevant assertions; add a versioned normative decision."})
        return {**base, "count": len(entries), "entries": entries,
                "counts": {"truncated": sum(bool(row["truncated"]) for row in rows),
                           "changed": sum(row["observation_state"] == "changed" for row in rows),
                           "missing": sum(row["observation_state"] == "missing" for row in rows),
                           "unreviewed": len(entries)}}
    finally:
        connection.close()
