"""Statut hors ligne des capacités du LOT B, sans divulguer les valeurs privées."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from pokemind.database import SCHEMA_VERSION, connect_readonly


def _tables(connection: sqlite3.Connection) -> set[str]:
    return {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _count(connection: sqlite3.Connection, sql: str, parameters: tuple[Any, ...] = ()) -> int:
    return int(connection.execute(sql, parameters).fetchone()[0])


def capability_status(db_path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "database_exists": db_path.is_file(),
        "read_only": True,
        "network_used": False,
        "schema_version": 0,
        "schema_current": False,
        "objects": {
            "collection": {"exists": False, "source": "unknown", "as_of": None},
            "credits": {"exists": False, "source": "unknown", "as_of": None, "amount_disclosed": False},
            "exact_deck_versions": 0,
            "deck_candidates": 0,
            "valid_battles": 0,
            "owner_attested_battles": 0,
            "validated_battle_notes": 0,
            "verified_rule_sources": 0,
            "verified_structure_rules": 0,
            "complete_meta_snapshots": 0,
            "classified_meta_placements": 0,
        },
        "capabilities": {},
        "gaps": [],
    }
    if not db_path.is_file():
        result["gaps"].append("DATABASE_MISSING")
        return result
    connection = connect_readonly(db_path)
    try:
        schema = int(connection.execute("PRAGMA user_version").fetchone()[0])
        tables = _tables(connection)
        result["schema_version"] = schema
        result["schema_current"] = schema == SCHEMA_VERSION
        objects = result["objects"]
        if "collection_snapshots" in tables:
            active = connection.execute(
                "SELECT as_of, source_kind FROM collection_snapshots WHERE status='active'"
            ).fetchone()
            if active:
                objects["collection"] = {"exists": True, "source": active["source_kind"], "as_of": active["as_of"]}
        if "credit_snapshots" in tables:
            active = connection.execute(
                "SELECT as_of, source_kind FROM credit_snapshots WHERE status='active'"
            ).fetchone()
            if active:
                objects["credits"] = {
                    "exists": True, "source": active["source_kind"], "as_of": active["as_of"],
                    "amount_disclosed": False,
                }
        if "deck_versions" in tables:
            objects["exact_deck_versions"] = _count(connection, "SELECT COUNT(*) FROM deck_versions WHERE exact_confirmed=1")
        if "deck_candidates" in tables:
            objects["deck_candidates"] = _count(connection, "SELECT COUNT(*) FROM deck_candidates")
        if "battle_logs" in tables:
            objects["valid_battles"] = _count(connection, "SELECT COUNT(*) FROM battle_logs WHERE valid=1")
        if "battle_version_attestations" in tables:
            objects["owner_attested_battles"] = _count(
                connection, "SELECT COUNT(DISTINCT battle_id) FROM battle_version_attestations WHERE status='active'"
            )
        if "battle_lessons" in tables:
            objects["validated_battle_notes"] = _count(connection, "SELECT COUNT(*) FROM battle_lessons WHERE status='active'")
        if "official_rule_sources" in tables:
            objects["verified_rule_sources"] = _count(
                connection, "SELECT COUNT(*) FROM official_rule_sources WHERE validation_status='verified'"
            )
        if "official_deck_structure_rules" in tables:
            objects["verified_structure_rules"] = _count(
                connection, "SELECT COUNT(*) FROM official_deck_structure_rules WHERE validation_status='verified'"
            )
        if "meta_tournaments" in tables:
            objects["complete_meta_snapshots"] = _count(
                connection, "SELECT COUNT(*) FROM meta_tournaments WHERE snapshot_status='complete'"
            )
        if "meta_placements" in tables:
            objects["classified_meta_placements"] = _count(
                connection, "SELECT COUNT(*) FROM meta_placements WHERE archetype_published=1 AND archetype_id IS NOT NULL"
            )
        result["capabilities"] = {
            "collection_missing": "available" if objects["collection"]["exists"] else "unknown_without_owner_import",
            "credit_aware_advice": (
                "partial_craft_cost_unknown" if objects["credits"]["exists"] else "unknown_without_owner_declaration"
            ),
            "deck_recommendation": (
                "available_with_evidence_limits" if objects["exact_deck_versions"] else "blocked_without_exact_deck"
            ),
            "version_attributed_lessons": (
                "available" if objects["owner_attested_battles"] else "partial_without_owner_attestations"
            ),
            "candidate_export": "available" if objects["exact_deck_versions"] else "blocked_without_exact_deck",
            "legality": (
                "tri_state_available" if objects["verified_rule_sources"] and objects["verified_structure_rules"]
                else "unknown_incomplete_official_evidence"
            ),
            "matchups": (
                "descriptive_sample_available" if objects["classified_meta_placements"] else "unknown_unclassified_meta"
            ),
        }
        if not result["schema_current"]:
            result["gaps"].append("MIGRATION_REQUIRED_ON_EXPLICIT_WRITE")
        if not objects["collection"]["exists"]:
            result["gaps"].append("COLLECTION_NOT_OWNER_PROVIDED")
        if not objects["credits"]["exists"]:
            result["gaps"].append("CREDITS_NOT_OWNER_PROVIDED")
        if not objects["owner_attested_battles"]:
            result["gaps"].append("NO_OWNER_ATTESTED_BATTLE_VERSION")
        if not objects["verified_structure_rules"]:
            result["gaps"].append("STRUCTURE_RULES_INCOMPLETE_OR_NOT_MIGRATED")
        if not objects["classified_meta_placements"]:
            result["gaps"].append("META_ARCHETYPES_UNCLASSIFIED")
        result["gaps"] = list(dict.fromkeys(result["gaps"]))
        return result
    finally:
        connection.close()
