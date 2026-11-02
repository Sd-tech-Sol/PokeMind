"""Conservative, in-memory review of equivalent historical parser records.

This never merges stored matches or transfers version attestations. Equivalence
is only a probable duplicate: short logs and same-parser repeats remain separate.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from typing import Any


def conservative_sample(
    connection: sqlite3.Connection, battle_ids: Iterable[int],
) -> dict[str, Any]:
    ids = sorted(set(int(value) for value in battle_ids))
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    columns = {row[1] for row in connection.execute("PRAGMA table_info(battle_logs)")}
    available = {"battle_logs", "battle_events"}.issubset(tables) and {
        "deck_id", "reference_player", "opponent_name", "outcome", "max_turn",
        "parser_version", "recognized_events", "imported_at", "valid",
    }.issubset(columns)
    buckets: dict[bytes, list[tuple[int, str, int, str]]] = defaultdict(list)
    for battle_id in ids if available else ():
        row = connection.execute(
            """SELECT deck_id,reference_player,opponent_name,outcome,max_turn,parser_version,
                      recognized_events,imported_at
               FROM battle_logs WHERE id=? AND valid=1""", (battle_id,),
        ).fetchone()
        if row is None or not row["reference_player"] or not row["opponent_name"] or (row["max_turn"] or 0) < 3:
            continue
        digest = hashlib.sha256()
        digest.update(json.dumps(tuple(row)[:5], ensure_ascii=True).encode("ascii"))
        opponent = " ".join(unicodedata.normalize("NFC", row["opponent_name"]).split())
        generic_draws = {f"{opponent} a pioché une carte.", f"{opponent} drew a card."}
        anchors = 0
        for event in connection.execute(
            "SELECT evidence FROM battle_events WHERE battle_id=? ORDER BY sequence", (battle_id,),
        ):
            evidence = " ".join(unicodedata.normalize("NFC", event["evidence"]).split())
            # Early parsers omitted these hidden-identity draws. No named card,
            # self draw, action order or turn evidence is discarded.
            if evidence in generic_draws:
                continue
            digest.update(b"\n" + json.dumps(evidence, ensure_ascii=True).encode("ascii"))
            anchors += 1
        if anchors >= 12:
            buckets[digest.digest()].append((battle_id, row["parser_version"],
                                             row["recognized_events"], row["imported_at"]))
    groups = []
    excluded: set[int] = set()
    for members in buckets.values():
        if len(members) < 2 or len({member[1] for member in members}) < 2:
            continue
        member_ids = sorted(member[0] for member in members)
        representative = max(members, key=lambda member: (member[2], member[3], -member[0]))[0]
        excluded.update(value for value in member_ids if value != representative)
        groups.append({"representative_id": representative, "battle_ids": member_ids,
                       "status": "PROBABLE_DUPLICATE_NOT_OWNER_CONFIRMED"})
    return {
        "battle_ids": [value for value in ids if value not in excluded],
        "stored_valid_games": len(ids),
        "probable_duplicates_excluded": len(excluded),
        "probable_duplicate_groups": sorted(groups, key=lambda group: group["representative_id"]),
        "method": "cross_parser_event_equivalence_conservative_in_memory",
        "comparison_available": available,
        "limits": ["Equivalence des événements ≠ identité de partie confirmée; les enregistrements restent intacts.",
                   "Journaux courts, incomplets ou issus du même parseur non dédupliqués sémantiquement."],
    }
