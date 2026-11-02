"""Observed index members, separate from cross-language/cache unions.

Pagination is not an atomic provider snapshot. A complete observed scan proves its
own member denominator only; it cannot establish a live worldwide/provider total.
"""
import hashlib
import json
from datetime import datetime, timezone, timedelta

PREFIX = "catalog_snapshot:"


def record_page(connection, scope, mode, page, ids, *, completed, timestamp):
    key = PREFIX + scope + ":" + mode
    previous = connection.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
    state = json.loads(previous[0]) if previous else None
    if page == 1:
        state = {"schema_version": 2, "scope": scope, "mode": mode, "started_at": timestamp,
                 "pages": {}, "completed": False, "contiguous_from_start": True}
    if state is None:
        state = {"schema_version": 1, "scope": scope, "mode": mode, "started_at": timestamp,
                 "pages": {}, "completed": False, "contiguous_from_start": False}
    # Preserve duplicates within a page; collapsing them hid moving pagination.
    state["pages"][str(page)] = list(ids)
    state.pop("last_error", None)
    state["last_attempt_at"] = timestamp
    state["completed"] = bool(completed)
    state["last_observed_at"] = timestamp
    state["completed_at"] = timestamp if completed else None
    connection.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES(?,?)", (key, json.dumps(state, sort_keys=True)))


def head_matches(connection, scope, mode, ids):
    """A resume probe is evidence of drift, never an atomic snapshot guarantee."""
    row = connection.execute("SELECT value FROM metadata WHERE key=?", (PREFIX + scope + ":" + mode,)).fetchone()
    if row is None:
        return False
    state = json.loads(row[0])
    before = state["pages"].get("1")
    return state.get("schema_version") == 2 and before == list(ids)


def record_failure(connection, scope, mode, timestamp):
    key = PREFIX + scope + ":" + mode
    row = connection.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
    if row is None:
        # A refresh can fail before its first member page exists. Invalidate the
        # previous observation instead of quietly showing a healthy old scan.
        key = PREFIX + scope + ":" + ("discovery" if mode == "refresh" else "refresh")
        row = connection.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
    if row:
        state = json.loads(row[0])
        state["last_error"] = "INDEX_OBSERVATION_FAILED"
        state["last_attempt_at"] = timestamp
        connection.execute("UPDATE metadata SET value=? WHERE key=?", (json.dumps(state, sort_keys=True), key))


def snapshot_coverage(connection, scope, *, now=None):
    if scope not in {f"{kind}:{lang}" for kind in ("cards", "sets") for lang in ("en", "fr")}:
        raise ValueError("CATALOG_SNAPSHOT_SCOPE_INVALID")
    rows = connection.execute("SELECT value FROM metadata WHERE key IN (?,?)", (PREFIX + scope + ":discovery", PREFIX + scope + ":refresh")).fetchall()
    if not rows:
        return {"status": "unknown_without_snapshot_membership", "denominator": None,
                "provider_visible_total": None, "complete": False}
    states = [json.loads(r[0]) for r in rows]
    state = max(states, key=lambda s: (s.get("last_attempt_at", s["last_observed_at"]), s["last_observed_at"], s["mode"] == "refresh"))
    pages = state["pages"]
    numbers = sorted(int(n) for n in pages)
    contiguous = bool(numbers) and state["contiguous_from_start"] and numbers == list(range(1, max(numbers) + 1))
    flat = [v for page in pages.values() for v in page]
    ids = sorted(set(flat))
    duplicates = len(flat) - len(ids)
    current = now or datetime.now(timezone.utc)
    observed = datetime.fromisoformat(state["last_observed_at"].replace("Z", "+00:00"))
    stale = current - observed > timedelta(days=7) or observed > current
    started = datetime.fromisoformat(state["started_at"].replace("Z", "+00:00"))
    scan_too_long = observed - started > timedelta(days=7) or started > observed
    observed_complete = bool(state.get("schema_version") == 2 and state["completed"] and contiguous
                             and not duplicates and not state.get("last_error") and not scan_too_long)
    complete = observed_complete and not stale
    digest = hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode()).hexdigest()
    kind, language = scope.split(":")
    if kind == "cards":
        rows = {r[0]: (r[1], r[2]) for r in connection.execute(
            f"SELECT p.tcgdex_id,t.status,p.detail_stale_{language} FROM catalog_printings p LEFT JOIN catalog_translations t ON t.printing_id=p.tcgdex_id AND t.language=?", (language,))}
    else:
        rows = {r[0]: (r[1], r[2]) for r in connection.execute(
            f"SELECT tcgdex_id,detail_status_{language},detail_stale_{language} FROM catalog_sets")}
    healthy = sum(rows.get(i) == ("present", 0) for i in ids)
    absent = sum(rows.get(i, (None,))[0] == "absent" for i in ids)
    return {"status": "observed_scan_complete" if complete else "partial_observed_scan",
            "complete": complete, "observed_scan_complete": observed_complete, "stale": stale, "mode": state["mode"],
            "membership_version_supported": state.get("schema_version") == 2,
            "started_at": state["started_at"], "completed_at": state["completed_at"],
            "last_observed_at": state["last_observed_at"], "page_count": len(pages),
            "duplicate_members": duplicates, "observed_members": len(ids),
            "last_error": state.get("last_error"), "scan_duration_exceeded": scan_too_long,
            "membership_sha256": digest, "denominator": len(ids) if complete else None,
            "details_present_fresh": healthy, "details_absent": absent,
            "details_unavailable_or_stale": len(ids) - healthy - absent,
            "detail_ratio": round(healthy / len(ids), 6) if complete and ids and not stale else None,
            "provider_visible_total": None, "provider_total_status": (
                "pinned_source_tree_only" if state.get("transport") == "pinned_git_literal_snapshot" else
                "unknown_non_atomic_pagination"),
            "transport": state.get("transport"), "source_commit": state.get("source_commit"),
            "live_compatibility_proven": False, "legality_proven": False}
