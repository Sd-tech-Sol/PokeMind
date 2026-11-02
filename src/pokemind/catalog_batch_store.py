"""Atomic PUBLIC batch pages on the existing catalog schema; no owner migration."""
from __future__ import annotations

import json
import re

from pokemind.cards import (
    CatalogError, _card_brief, _canonical_sha256, _ensure_translation_row,
    _page_transition, _save_sync_state, _set_record,
    _sync_state, _upsert_card_brief, _upsert_card_detail, _upsert_set_brief,
    _upsert_set_detail, _validated_card_detail, _validated_list,
)
from pokemind.catalog_snapshots import PREFIX, record_page
from pokemind.database import utc_now
from pokemind.tcgdex_batch import ENDPOINT


class _PageTransaction:
    """Nested legacy helper contexts cannot commit an incomplete batch page."""
    def __init__(self, connection):
        self.connection = connection

    def execute(self, *args, **kwargs):
        return self.connection.execute(*args, **kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def initialize_batch_tables(connection):
    # Additive extension ONLY in the explicitly created PUBLIC DB. No change to
    # global SCHEMA_VERSION, implicit consultation or private database migration.
    with connection:
        connection.execute("""CREATE TABLE IF NOT EXISTS catalog_batch_queries (
            query_sha256 TEXT PRIMARY KEY, evidence_json TEXT NOT NULL,
            retrieved_at TEXT NOT NULL)""")
        connection.execute("""CREATE TABLE IF NOT EXISTS catalog_detail_payloads (
            kind TEXT NOT NULL CHECK(kind IN ('sets','cards')),
            entity_id TEXT NOT NULL, language TEXT NOT NULL CHECK(language IN ('en','fr')),
            payload_json TEXT NOT NULL, payload_sha256 TEXT NOT NULL,
            query_sha256 TEXT NOT NULL REFERENCES catalog_batch_queries(query_sha256),
            PRIMARY KEY(kind,entity_id,language))""")


def _validate(kind, rows):
    if not isinstance(rows, list) or len(rows) > 100:
        raise CatalogError("TCGDEX_BATCH_PAGE_INVALID")
    records = []
    for row in rows:
        if kind == "cards":
            record = _card_brief(row)
            _validated_card_detail(row, record.tcgdex_id)
        elif kind == "sets":
            record = _set_record(row)
            _validated_list(row.get("cards"), _card_brief, "set cards", max_items=2000)
        else:
            raise CatalogError("TCGDEX_BATCH_SCOPE_INVALID")
        records.append(record)
    ids = [record.tcgdex_id for record in records]
    if len(ids) != len(set(ids)):
        raise CatalogError("TCGDEX_BATCH_DUPLICATE_MEMBERS")
    return records


def _query_record(connection, evidence, timestamp):
    graphql = evidence.get("source_url") == ENDPOINT and evidence.get("operation") == "query"
    literal = evidence.get("operation") == "literal_snapshot"
    if literal:
        commit = evidence.get("source_commit", "")
        prefix = f"https://github.com/tcgdex/cards-database/blob/{commit}/data/"
        literal = bool(re.fullmatch(r"[0-9a-f]{40}", commit) and evidence.get("source_url") ==
            f"https://github.com/tcgdex/cards-database/tree/{commit}/data" and
            isinstance(evidence.get("source_objects"), dict))
        for obj in evidence.get("source_objects", {}).values():
            url = obj.get("source_url", "")
            literal = literal and (url.startswith(prefix) and url.endswith(".ts") and
                not any(part in url[len(prefix):] for part in ("..", "?", "#", "\\")) and
                bool(re.fullmatch(r"[0-9a-f]{40}", obj.get("git_blob", ""))))
    if not (graphql or literal) or not re.fullmatch(r"[0-9a-f]{64}", evidence.get("query_sha256", "")):
        raise CatalogError("TCGDEX_BATCH_PROVENANCE_INVALID")
    connection.execute("INSERT OR REPLACE INTO catalog_batch_queries VALUES (?,?,?)",
                       (evidence["query_sha256"], json.dumps(evidence, sort_keys=True), timestamp))


def _payload_record(connection, kind, entity_id, language, payload, evidence):
    connection.execute("INSERT OR REPLACE INTO catalog_detail_payloads VALUES (?,?,?,?,?,?)",
        (kind, entity_id, language, json.dumps(payload, ensure_ascii=False, sort_keys=True),
         _canonical_sha256(payload), evidence["query_sha256"]))


def _descriptive_hash(value):
    # REST repairs can include volatile prices/image URLs. Head stability concerns
    # descriptive card data, not price-provider refreshes unrelated to this task.
    excluded = {"pricing", "thirdParty", "image", "logo", "symbol", "updated", "legal",
                "artwork_front", "artwork_back"}
    def clean(item):
        if isinstance(item, dict):
            return {key: clean(value) for key, value in item.items() if key not in excluded}
        if isinstance(item, list):
            return [clean(value) for value in item]
        return item
    return _canonical_sha256(clean(value))


def _store_present(connection, kind, language, row, evidence, timestamp):
    entity_id = row["id"]
    source_url = _source_url(evidence, entity_id)
    if evidence.get("operation") != "literal_snapshot":
        source_url = next((repair["source_url"] for repair in evidence.get("rest_repairs", [])
                       if repair["kind"] == kind and repair["language"] == language and repair["id"] == entity_id), ENDPOINT)
    if kind == "cards":
        _upsert_card_brief(connection, _card_brief(row), language, source_url, timestamp)
        _upsert_card_detail(connection, row, entity_id, language, source_url)
    else:
        _upsert_set_brief(connection, _set_record(row), language, source_url, timestamp)
        _upsert_set_detail(connection, row, entity_id, language, source_url)
    _payload_record(connection, kind, entity_id, language, row, evidence)


def _source_url(evidence, entity_id):
    if evidence.get("operation") == "literal_snapshot":
        obj = evidence.get("source_objects", {}).get(entity_id)
        if not obj:
            raise CatalogError("SNAPSHOT_OBJECT_PROVENANCE_MISSING")
        return obj["source_url"]
    return ENDPOINT


def store_page(connection, kind, language, page, rows, evidence, *, request_attempts):
    if language not in {"en", "fr"}:
        raise CatalogError("TCGDEX_BATCH_SCOPE_INVALID")
    records = _validate(kind, rows)  # whole page before any writes
    scope = kind + ":" + language
    state = _sync_state(connection, scope)
    if state["completed"] or page != state["next_page"]:
        raise CatalogError("TCGDEX_BATCH_PAGE_SEQUENCE_INVALID")
    old = connection.execute("SELECT value FROM metadata WHERE key=?", (PREFIX + scope + ":discovery",)).fetchone()
    old_pages = json.loads(old[0])["pages"] if old else {}
    seen = {value for values in old_pages.values() for value in values}
    if seen.intersection(record.tcgdex_id for record in records):
        raise CatalogError("TCGDEX_BATCH_DUPLICATE_MEMBERS")
    timestamp = utc_now()
    next_page, complete, end_candidate = _page_transition(page, len(records), state["end_candidate_page"])
    with connection:
        view = _PageTransaction(connection)
        _query_record(view, evidence, timestamp)
        for row in rows:
            _store_present(view, kind, language, row, evidence, timestamp)
        _save_sync_state(view, scope, next_page=next_page, completed=complete,
                         end_candidate_page=end_candidate, timestamp=timestamp,
                         request_attempts=request_attempts)
        record_page(view, scope, "discovery", page, [record.tcgdex_id for record in records],
                    completed=complete, timestamp=timestamp)
        key = PREFIX + scope + ":discovery"
        snapshot = json.loads(view.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()[0])
        snapshot.update(transport=("pinned_git_literal_snapshot" if evidence.get("operation") ==
            "literal_snapshot" else "graphql_fixed_query"), endpoint=evidence["source_url"], page_size=100)
        if evidence.get("operation") == "literal_snapshot":
            snapshot["source_commit"] = evidence["source_commit"]
        if page == 1:
            snapshot["first_page_payload_sha256"] = _descriptive_hash(rows)
        elif old:
            snapshot["first_page_payload_sha256"] = json.loads(old[0])["first_page_payload_sha256"]
        view.execute("UPDATE metadata SET value=? WHERE key=?", (json.dumps(snapshot, sort_keys=True), key))
    return complete


def pending_language_ids(connection, kind, language):
    if language not in {"en", "fr"} or kind not in {"cards", "sets"}:
        raise CatalogError("TCGDEX_BATCH_SCOPE_INVALID")
    if kind == "cards":
        return [r[0] for r in connection.execute("""SELECT p.tcgdex_id FROM catalog_printings p
            LEFT JOIN catalog_translations t ON t.printing_id=p.tcgdex_id AND t.language=?
            WHERE t.status IS NULL OR t.status NOT IN ('present','absent') ORDER BY p.tcgdex_id""", (language,))]
    return [r[0] for r in connection.execute(
        f"SELECT tcgdex_id FROM catalog_sets WHERE detail_status_{language} NOT IN ('present','absent') ORDER BY tcgdex_id")]


def store_selection(connection, kind, language, selected, evidence):
    if kind not in {"cards", "sets"} or language not in {"en", "fr"} or not 1 <= len(selected) <= 30:
        raise CatalogError("TCGDEX_BATCH_SELECTION_INVALID")
    for entity_id, row in selected.items():
        if row is not None:
            _validate(kind, [row])
            if row["id"] != entity_id:
                raise CatalogError("TCGDEX_BATCH_SELECTION_ID_MISMATCH")
    timestamp = utc_now()
    with connection:
        view = _PageTransaction(connection)
        _query_record(view, evidence, timestamp)
        for entity_id, row in selected.items():
            if row is not None:
                _store_present(view, kind, language, row, evidence, timestamp)
                continue
            source_url = _source_url(evidence, entity_id)
            if kind == "cards":
                _ensure_translation_row(view, entity_id, language)
                view.execute("""UPDATE catalog_translations SET status='absent',source_url=?,
                    retrieved_at=?,payload_sha256=?,last_error=NULL WHERE printing_id=? AND language=?""",
                    (source_url, timestamp, _canonical_sha256(None), entity_id, language))
            else:
                view.execute(f"""UPDATE catalog_sets SET detail_status_{language}='absent',
                    source_url_{language}=?,retrieved_at_{language}=?,content_sha256_{language}=?,
                    detail_stale_{language}=0,last_error_{language}=NULL WHERE tcgdex_id=?""",
                    (source_url, timestamp, _canonical_sha256(None), entity_id))
            _payload_record(view, kind, entity_id, language, None, evidence)


def verify_head(connection, kind, language, rows):
    row = connection.execute("SELECT value FROM metadata WHERE key=?", (PREFIX + kind + ":" + language + ":discovery",)).fetchone()
    state = json.loads(row[0])
    if state.get("first_page_payload_sha256") != _descriptive_hash(rows):
        with connection:
            state["last_error"] = "BATCH_HEAD_CHANGED"
            connection.execute("UPDATE metadata SET value=? WHERE key=?",
                (json.dumps(state, sort_keys=True), PREFIX + kind + ":" + language + ":discovery"))
        raise CatalogError("TCGDEX_BATCH_HEAD_CHANGED")


def verified_payload(connection, kind, entity_id, language, expected_sha):
    """RO language-specific fields; never use a stale auxiliary copy after REST."""
    if not expected_sha or not connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='catalog_detail_payloads'"
    ).fetchone():
        return None
    row = connection.execute("""SELECT payload_json,payload_sha256 FROM catalog_detail_payloads
        WHERE kind=? AND entity_id=? AND language=?""", (kind, entity_id, language)).fetchone()
    if row is None or row[1] != expected_sha:
        return None
    payload = json.loads(row[0])
    return payload if isinstance(payload, dict) and _canonical_sha256(payload) == expected_sha else None
