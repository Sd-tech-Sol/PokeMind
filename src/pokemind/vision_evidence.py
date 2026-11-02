"""Reversible owner reviews bound to exact text observations, never to pixels.

Stored in existing schema-13 metadata. These are declarations, not independent
calibration or release certification. Corrections invalidate the old digest.
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Any
from pathlib import Path

from pokemind.database import SCHEMA_VERSION, connect_readonly, connect_writable, utc_now

PREFIX = "vision_review:"


def _rows(connection):
    return [json.loads(row[0]) for row in connection.execute(
        "SELECT value FROM metadata WHERE key LIKE 'vision_review:%' ORDER BY key")]


def _active(rows):
    revoked = {r["revokes"] for r in rows if r.get("revokes")}
    return [r for r in rows if not r.get("revokes") and r["id"] not in revoked]


def review_observation(db_path: Path, session_id: str, observation_id: int, *,
                       verdict: str, scope: str, calibration_sha256: str,
                       apply: bool = False, confirm_owner: bool = False) -> dict[str, Any]:
    if verdict not in {"confirmed", "rejected"} or scope not in {"synthetic", "owner_training"}:
        raise ValueError("VISION_REVIEW_INVALID")
    if not re.fullmatch(r"[0-9a-f]{64}", calibration_sha256):
        raise ValueError("VISION_CALIBRATION_DIGEST_REQUIRED")
    if apply and not confirm_owner:
        raise ValueError("OWNER_CONFIRMATION_REQUIRED")
    if not db_path.is_file():
        raise ValueError("VISION_REVIEW_DATABASE_REQUIRED")
    connection = connect_writable(db_path) if apply else connect_readonly(db_path)
    try:
        if int(connection.execute("PRAGMA user_version").fetchone()[0]) != SCHEMA_VERSION:
            raise ValueError("VISION_REVIEW_SCHEMA_MIGRATION_REQUIRED")
        if apply:
            connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            """SELECT o.state_sha256,o.turn_number,s.format,s.platform,s.context_date
               FROM training_observations o JOIN training_sessions s USING(session_id)
               WHERE o.session_id=? AND o.id=? AND o.status='active'""", (session_id, observation_id)).fetchone()
        if row is None:
            raise ValueError("VISION_REVIEW_ACTIVE_OBSERVATION_REQUIRED")
        record = {"id": uuid.uuid4().hex, "session_id": session_id, "observation_id": observation_id,
                  "state_sha256": row["state_sha256"], "turn": row["turn_number"],
                  "context": {k: row[k] for k in ("format", "platform", "context_date")},
                  "verdict": verdict, "scope": scope, "calibration_sha256": calibration_sha256,
                  "recorded_at": utc_now(), "provenance": "owner_asserted", "revokes": None}
        current = [r for r in _active(_rows(connection)) if r["observation_id"] == observation_id]
        if current:
            same = all(current[0][k] == record[k] for k in ("state_sha256", "verdict", "scope", "calibration_sha256"))
            if not same:
                raise ValueError("VISION_REVIEW_REVOKE_CONFLICT_FIRST")
            return {"status": "DUPLICATE", "review_id": current[0]["id"], "read_only": not apply}
        if apply:
            connection.execute("INSERT INTO metadata(key,value) VALUES(?,?)", (PREFIX + record["id"], json.dumps(record, sort_keys=True)))
            connection.commit()
        return {"status": "RECORDED" if apply else "PREVIEW", "review_id": record["id"],
                "read_only": not apply, "network_used": False, "visual_certain_allowed": False}
    finally:
        connection.close()


def revoke_visual_review(db_path: Path, review_id: str, *, apply=False, confirm_owner=False):
    if not re.fullmatch(r"[0-9a-f]{32}", review_id):
        raise ValueError("VISION_REVIEW_ID_INVALID")
    if apply and not confirm_owner:
        raise ValueError("OWNER_CONFIRMATION_REQUIRED")
    if not db_path.is_file():
        raise ValueError("VISION_REVIEW_DATABASE_REQUIRED")
    connection = connect_writable(db_path) if apply else connect_readonly(db_path)
    try:
        if apply:
            connection.execute("BEGIN IMMEDIATE")
        rows = _rows(connection)
        record = next((r for r in rows if r["id"] == review_id and not r.get("revokes")), None)
        if record is None:
            raise ValueError("VISION_REVIEW_NOT_FOUND")
        if any(r.get("revokes") == review_id for r in rows):
            return {"status": "ALREADY_REVOKED", "read_only": not apply}
        if apply:
            event = {**record, "id": uuid.uuid4().hex, "recorded_at": utc_now(), "revokes": review_id}
            connection.execute("INSERT INTO metadata(key,value) VALUES(?,?)", (PREFIX + event["id"], json.dumps(event, sort_keys=True)))
            connection.commit()
        return {"status": "REVOKED" if apply else "PREVIEW", "read_only": not apply,
                "network_used": False, "history_preserved": True}
    finally:
        connection.close()


def visual_review_summary(connection, session_id: str) -> dict[str, Any]:
    rows = [r for r in _rows(connection) if r["session_id"] == session_id]
    current = {r["id"]: r for r in connection.execute(
        "SELECT id,state_sha256,turn_number,source_kind FROM training_observations WHERE session_id=? AND status='active'", (session_id,))}
    live = [r for r in _active(rows) if r["observation_id"] in current
            and current[r["observation_id"]]["state_sha256"] == r["state_sha256"]]
    owner_turns = {r["turn"] for r in live if r["verdict"] == "confirmed" and r["scope"] == "owner_training"
                   and current[r["observation_id"]]["source_kind"] == "local_vision"}
    return {"record_count": len(rows), "active_reviews": len(live),
            "confirmed_count": sum(r["verdict"] == "confirmed" for r in live),
            "rejected_count": sum(r["verdict"] == "rejected" for r in live),
            "owner_reviewed_visual_turns": len(owner_turns), "independent_calibration_verified": False,
            "visual_certain_allowed": False, "images_stored": 0,
            "provenance": "owner_asserted_not_independent_test"}
