"""Human full-document review, bound to full response hash and current source.

HTTP observation, full-document review and normative assertion validation remain
three distinct pieces of evidence. This module never edits rule assertions.
"""
import json
import re
import uuid
from datetime import datetime, timezone

from pokemind.database import SCHEMA_VERSION, connect_readonly, connect_writable, utc_now


def official_review(connection, row):
    saved = connection.execute("SELECT value FROM metadata WHERE key=?", ("official_document_review:" + row["source_id"],)).fetchone()
    if not saved:
        return {"status": "not_reviewed", "normative_promotion": False}
    review = json.loads(saved[0])
    observed = datetime.fromisoformat(row["observed_at"].replace("Z", "+00:00"))
    reviewed = datetime.fromisoformat(review["reviewed_at"].replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    current = (row["http_status"] == 200 and not row["truncated"]
               and observed.tzinfo is not None and reviewed.tzinfo is not None
               and observed <= now and reviewed <= now
               and review["content_sha256"] == row["content_sha256"]
               and review["source_url"] == row["source_url"])
    return {"status": review["decision"] if current else "stale_review", "current": current,
            "reviewed_at": review["reviewed_at"], "document_version": review["document_version"],
            "normative_promotion": False, "assertion_validation": "SEPARATE_VERSIONED_REGISTRY_REQUIRED"}


def record_official_review(db_path, source_id, *, content_sha256, document_version,
                          decision, full_document_reviewed=False, apply=False, confirm_owner=False):
    if (not re.fullmatch(r"[0-9a-f]{64}", content_sha256) or decision not in {"verified", "non_verified", "conflict"}
        or not re.fullmatch(r"[A-Za-z0-9._:-]{1,80}", document_version)):
        raise ValueError("OFFICIAL_REVIEW_INVALID")
    if not full_document_reviewed:
        raise ValueError("FULL_DOCUMENT_REVIEW_REQUIRED")
    if apply and not confirm_owner:
        raise ValueError("OWNER_CONFIRMATION_REQUIRED")
    if not db_path.is_file():
        raise ValueError("OFFICIAL_REVIEW_DATABASE_REQUIRED")
    connection = connect_writable(db_path) if apply else connect_readonly(db_path)
    try:
        if connection.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
            raise ValueError("OFFICIAL_REVIEW_SCHEMA_MIGRATION_REQUIRED")
        if apply:
            connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT * FROM public_source_observations WHERE source_id=? ORDER BY id DESC LIMIT 1", (source_id,)).fetchone()
        if row is None or row["http_status"] != 200 or row["truncated"] or row["content_sha256"] != content_sha256:
            raise ValueError("OFFICIAL_FULL_RESPONSE_HASH_REQUIRED")
        observed = datetime.fromisoformat(row["observed_at"].replace("Z", "+00:00"))
        if observed.tzinfo is None or observed > datetime.now(timezone.utc):
            raise ValueError("OFFICIAL_REVIEW_FUTURE_OBSERVATION")
        record = {"source_id": source_id, "source_url": row["source_url"], "observation_id": row["id"],
                  "content_sha256": content_sha256, "document_version": document_version,
                  "decision": decision, "reviewed_at": utc_now(), "provenance": "explicit_document_reviewer"}
        if apply:
            # Keep an immutable audit entry and an indexed latest pointer.
            key = f"official_document_review_history:{row['id']}:{uuid.uuid4().hex}"
            connection.execute("INSERT INTO metadata(key,value) VALUES(?,?)", (key, json.dumps(record, sort_keys=True)))
            connection.execute("INSERT OR REPLACE INTO metadata(key,value) VALUES(?,?)", ("official_document_review:" + source_id, json.dumps(record, sort_keys=True)))
            connection.commit()
        return {"status": "RECORDED" if apply else "PREVIEW", "read_only": not apply,
                "network_used": False, "document_review": decision, "normative_promotion": False,
                "next_action": "VERSIONED_ASSERTION_RECONCILIATION_REQUIRED"}
    finally:
        connection.close()
