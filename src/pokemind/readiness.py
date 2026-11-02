"""Rapport V1 agrégé, hors ligne, sans détails personnels."""

from __future__ import annotations

import os
import platform
import sqlite3
import sys
from pathlib import Path
from typing import Any

from pokemind.capabilities import capability_status
from pokemind.battle_sample import conservative_sample
from pokemind.database import SCHEMA_VERSION, connect_readonly, database_status
from pokemind.knowledge import knowledge_status, knowledge_audit
from pokemind.recovery import RecoveryError, backup_status, verify_backup
from pokemind.updates import update_status
from pokemind.visual_coach import vision_backend_status
from pokemind.rules import normative_coverage


def _tables(connection: Any) -> set[str]:
    return {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _completion_evidence(db_path: Path, *, read_existing: bool = True) -> dict[str, Any]:
    result: dict[str, Any] = {
        "confirmed_deck_versions": 0,
        "confirmed_60_card_versions": 0,
        "owner_attributed_battles": 0,
        "conservative_valid_battles": 0,
        "probable_duplicate_battles": 0,
        "collection_declared": False,
        "credits_declared": False,
        "catalog": {"state": "absent", "complete": False},
        "metagame": {"complete_snapshots": 0, "classifiable_matches": 0, "zero_safe": True},
        "normative": {"complete": False, "dimensions": {}},
        "official_review_pending": 0,
        "visual_reviews": {"records": 0, "active_confirmed": 0, "independent_trial_verified": False},
    }
    if not read_existing or not db_path.is_file():
        return result
    connection = connect_readonly(db_path)
    try:
        tables = _tables(connection)
        if {"battle_logs", "battle_events"}.issubset(tables):
            cohort = conservative_sample(connection, (
                row[0] for row in connection.execute("SELECT id FROM battle_logs WHERE valid=1")
            ))
            result["conservative_valid_battles"] = len(cohort["battle_ids"])
            result["probable_duplicate_battles"] = cohort["probable_duplicates_excluded"]
        if {"deck_versions", "deck_version_cards"}.issubset(tables):
            result["confirmed_deck_versions"] = int(connection.execute(
                "SELECT COUNT(*) FROM deck_versions WHERE exact_confirmed=1"
            ).fetchone()[0])
            result["confirmed_60_card_versions"] = int(connection.execute(
                """SELECT COUNT(*) FROM (
                       SELECT v.id FROM deck_versions v
                       JOIN deck_version_cards c ON c.deck_version_id=v.id
                       WHERE v.exact_confirmed=1 GROUP BY v.id HAVING SUM(c.quantity)=60
                   )"""
            ).fetchone()[0])
        if "battle_version_attestations" in tables:
            attested_ids = [row[0] for row in connection.execute(
                """SELECT DISTINCT a.battle_id FROM battle_version_attestations a
                   JOIN battle_logs b ON b.id=a.battle_id
                   JOIN deck_versions v ON v.id=a.deck_version_id
                   WHERE a.status='active' AND b.valid=1 AND b.deck_id=v.deck_id
                     AND v.exact_confirmed=1 AND a.provenance='owner_asserted'
                     AND a.actor='owner_explicit_confirmation'
                     AND (SELECT SUM(c.quantity) FROM deck_version_cards c WHERE c.deck_version_id=v.id)=60"""
            )]
            result["owner_attributed_battles"] = len(conservative_sample(connection, attested_ids)["battle_ids"])
        if "collection_snapshots" in tables:
            result["collection_declared"] = bool(connection.execute(
                "SELECT 1 FROM collection_snapshots WHERE status='active' LIMIT 1"
            ).fetchone())
        if "credit_snapshots" in tables:
            result["credits_declared"] = bool(connection.execute(
                "SELECT 1 FROM credit_snapshots WHERE status='active' LIMIT 1"
            ).fetchone())
        if "training_sessions" in tables:
            from pokemind.vision_evidence import visual_review_summary
            for session in connection.execute("SELECT session_id FROM training_sessions"):
                review = visual_review_summary(connection, session[0])
                result["visual_reviews"]["records"] += review["record_count"]
                result["visual_reviews"]["active_confirmed"] += review["confirmed_count"]
    finally:
        connection.close()
    knowledge = knowledge_status(db_path)
    result["normative"] = normative_coverage(db_path)
    result["official_review_pending"] = int(knowledge.get("official_validation", {}).get("count", 0))
    cards = knowledge.get("cards", {})
    result["catalog"] = {
        "state": cards.get("state", "absent"),
        "unique_printings": int(cards.get("unique_printings", 0)),
        "discovery_complete": bool(cards.get("discovery", {}).get("complete", False)),
        "details_complete_on_discovered": bool(cards.get("details_complete_on_discovered", False)),
        "complete": bool(cards.get("complete", False)),
        "provider_total_proven": all(
            cards.get("languages", {}).get(lang, {}).get("index", {}).get("provider_visible_total") is not None
            for lang in ("en", "fr")
        ),
    }
    meta = knowledge.get("metagame", {})
    result["metagame"] = {
        "complete_snapshots": int(meta.get("tournaments", {}).get("complete_snapshots", 0)),
        "classifiable_matches": int(meta.get("matches", {}).get("classifiable", 0)),
        "zero_safe": True,
        "trainer_hill_status": meta.get("trainer_hill", {}).get("status", "BLOCKED_WITH_REASON"),
        "last_fetched_at": meta.get("period", {}).get("last_fetched_at"),
    }
    return result


def _backup_readiness(destination: Path | None) -> dict[str, Any]:
    if destination is None:
        return {
            "configured": False, "verified_count": 0, "rejected_count": 0,
            "status": "OWNER_CONFIGURATION_REQUIRED",
        }
    if not destination.exists():
        return {
            "configured": True, "verified_count": 0, "rejected_count": 0,
            "status": "NO_BACKUPS",
        }
    try:
        inventory = backup_status(destination)
    except (OSError, RecoveryError):
        return {
            "configured": True, "verified_count": 0, "rejected_count": 0,
            "status": "BACKUP_DIRECTORY_UNREADABLE",
        }
    verified = rejected = 0
    for item in inventory.get("backups", []):
        name = item.get("backup_file")
        if not name:
            rejected += 1
            continue
        try:
            verify_backup(destination / str(name))
            verified += 1
        except (OSError, RecoveryError):
            rejected += 1
    return {
        "configured": True,
        "verified_count": verified,
        "rejected_count": rejected,
        "interrupted_count": int(inventory.get("counts", {}).get("in_progress", 0)),
        "failed_count": int(inventory.get("counts", {}).get("failed", 0)),
        "status": "VERIFIED_BACKUP_AVAILABLE" if verified else "NO_VERIFIED_BACKUP",
        "inventory_complete": inventory.get("inventory_complete", True),
    }


def v1_readiness(db_path: Path, *, backup_directory: Path | None = None) -> dict[str, Any]:
    """Compose one non-mutating availability report without paths or private values."""
    database = database_status(db_path)
    vision = vision_backend_status()
    backups = _backup_readiness(backup_directory)
    owner, updates, checks = {}, {}, {}
    completion = _completion_evidence(db_path, read_existing=False)
    read_error = None
    if database.get("database_exists") and database.get("integrity") == "ok":
        try:
            owner = capability_status(db_path)
            updates = update_status(db_path)
            completion = _completion_evidence(db_path)
            checks = knowledge_audit(db_path).get("audit", {}).get("checks", {})
        except (OSError, ValueError, sqlite3.Error):
            read_error = "READINESS_EVIDENCE_UNREADABLE"
    # CPython 3.11's Windows platform.system()/machine() populate uname via
    # win32_ver(), which can launch the shell command "ver". A read-only
    # readiness report must not spawn a process just to identify the runtime.
    if sys.platform == "win32":
        system_name = "Windows"
        machine = (os.environ.get("PROCESSOR_ARCHITEW6432")
                   or os.environ.get("PROCESSOR_ARCHITECTURE") or "unknown")
    else:
        system_name, machine = platform.system(), platform.machine()
    runtime = {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "implementation": platform.python_implementation(),
        "os": system_name,
        "architecture": machine,
        "supported": sys.version_info >= (3, 11) and system_name in {"Windows", "Linux"},
    }
    update_summary = {
        "status": updates.get("status"),
        "schema_current": updates.get("schema_current", False),
        "last_cycle_status": (updates.get("last_cycle") or {}).get("status"),
        "open_alert_count": len(updates.get("open_alerts", [])),
        "scheduler_installed_by_report": False,
        "scheduler_activation_gate": "SCHEDULER_ACTIVATION_DISABLED_IN_LOT_D",
        "os_activation_status": "OWNER_ACTION_REQUIRED",
        "active_service_proven": False,
    }
    owner_summary = {
        "collection_declared": completion["collection_declared"],
        "credits_declared": completion["credits_declared"],
        "confirmed_deck_versions": completion["confirmed_deck_versions"],
        "confirmed_60_card_versions": completion["confirmed_60_card_versions"],
        "owner_attributed_battles": completion["owner_attributed_battles"],
        "gaps": owner.get("gaps", []),
        "private_values_disclosed": False,
    }
    gates: dict[str, dict[str, Any]] = {}

    def gate(name: str, passed: bool, reason: str, source: str, *, category: str = "PRODUCT_CAPABILITY_PARTIAL", required: bool = True) -> None:
        gates[name] = {"status": "DONE" if passed else ("OWNER_ACTION_REQUIRED" if category == "OWNER_ACTION_REQUIRED" else "PARTIAL_WITH_EVIDENCE"),
                       "passed": bool(passed), "required": required, "category": category,
                       "reason_code": None if passed else reason, "evidence_source": source}

    gate("runtime", runtime["supported"], "UNSUPPORTED_RUNTIME", "runtime Python/OS")
    gate("database_schema", database.get("database_exists") and database.get("schema_version") == SCHEMA_VERSION, "DATABASE_MISSING_OR_MIGRATION_REQUIRED", "PRAGMA user_version", category="OWNER_ACTION_REQUIRED")
    healthy = database.get("integrity") == "ok" and checks.get("foreign_key_violations") == 0 and all(checks.get(key, {}).get("status") == "ok" for key in ("sections_fts", "catalog_fts"))
    gate("database_integrity_fk_fts", healthy and read_error is None, "DATABASE_INTEGRITY_OR_INDEX_EVIDENCE_INCOMPLETE", "read-only SQLite integrity/FK/FTS audit")
    gate("library", database.get("documents", 0) >= 4 and database.get("sections", 0) > 0, "LIBRARY_COVERAGE_INCOMPLETE", "documents/sections counts; citation tests remain separate")
    gate("catalog_fr_en", completion["catalog"].get("complete", False), "PUBLIC_CATALOG_COVERAGE_PARTIAL", "cards coverage discovery/details/stale FR/EN")
    gate("historical_catalog_denominator", completion["catalog"].get("provider_total_proven", False), "CATALOG_PROVIDER_TOTAL_UNPROVEN", "provider snapshot membership; local rows are insufficient")
    normative = completion.get("normative", {}).get("dimensions", {})
    for name in ("standard_rotation_live", "standard_rotation_in_person", "restrictions", "deck_structure", "reprints", "errata", "promos", "expanded_eligibility", "live_support"):
        gate(name, normative.get(name, {}).get("complete", False), "NORMATIVE_" + name.upper() + "_INCOMPLETE", "dated official sources/assertions: normative_coverage")
    gate("official_changes_reviewed", completion.get("official_review_pending", 0) == 0 and bool(normative), "OFFICIAL_CONTENT_REVIEW_PENDING", "public_source_observations review queue; HTTP/hash is not validation")
    meta = completion["metagame"]
    gate("metagame_sample", meta.get("complete_snapshots", 0) >= 2 and meta.get("classifiable_matches", 0) >= 5, "METAGAME_SAMPLE_INSUFFICIENT", "Limitless standard/PTCGL/online; 2 snapshots and n>=5 are only a minimum sample, not a global estimate")
    gate("trainer_hill", False, "TRAINER_HILL_AUTHORIZED_ACCESS_NOT_PROVEN", "no permitted public API established")
    gate("exact_deck_60", completion["confirmed_60_card_versions"] > 0, "OWNER_EXACT_DECK_REQUIRED", "exact_confirmed and SUM(quantity)=60", category="OWNER_ACTION_REQUIRED")
    gate("battle_profile", completion["conservative_valid_battles"] >= 5, "OWNER_VALID_BATTLE_SAMPLE_REQUIRED", "conservative battle sample n>=5; probable cross-parser duplicates excluded in memory", category="OWNER_ACTION_REQUIRED")
    gate("version_attribution", completion["owner_attributed_battles"] >= 5, "OWNER_BATTLE_VERSION_ATTESTATIONS_REQUIRED", "active explicit owner attestations; never inferred", category="OWNER_ACTION_REQUIRED")
    # Only a future calibrated adapter with a separately audited owner-trial
    # evidence store may satisfy this. Neither marker flags nor mock TSV count.
    gate("vision_owner_trial", False, "VISION_NOT_VERIFIED_ON_OWNER_TRAINING", "H owner review store is reversible and digest-bound; independent calibration and permitted real trial remain unproven", category="OWNER_ACTION_REQUIRED")
    gate("raster_ocr_calibration", False, "OCR_REAL_CALIBRATION_UNPROVEN", "H raster benchmark is not real-card/owner calibration; absent engine is not a pass")
    gate("updater_cycles", all(updates.get("sources", {}).get(name, {}).get("last_successful") for name in ("tcgdex", "pokemon_official", "limitless")), "PUBLIC_UPDATER_CYCLES_UNPROVEN", "completed source runs; normative review is a separate gate")
    gate("scheduler_cadence", False, "SCHEDULER_OWNER_OPT_IN_AND_CADENCE_REQUIRED", "activation disabled; daily and Tue/Fri Toronto dry-run is not activation", category="OWNER_ACTION_REQUIRED")
    gate("verified_backup", backups["verified_count"] > 0 and backups.get("inventory_complete", True), "NO_OWNER_VERIFIED_BACKUP", "verify_backup SHA/SQLite and complete bounded inventory", category="OWNER_ACTION_REQUIRED")
    gate("existing_target_restore", False, "RESTORE_EXISTING_TARGET_BLOCKED", "G0 fail-closed: no durable external exclusion proven")
    gate("retention_safety", False, "RETENTION_EXTERNAL_EXCLUSION_UNPROVEN", "H0 public apply blocked; no safe multifile purge or durable keep_last proof")
    gate("independent_release_audit", False, "INDEPENDENT_RELEASE_AUDIT_REQUIRED", "ChatGPT audit required; Codex does not self-verify")
    gate("optional_collection", completion["collection_declared"], "OPTIONAL_COLLECTION_NOT_PROVIDED", "owner-provided snapshot only", category="OWNER_ACTION_REQUIRED", required=False)
    gate("optional_credits", completion["credits_declared"], "OPTIONAL_CREDITS_NOT_PROVIDED", "owner-provided snapshot only; crafting tariff remains unknown", category="OWNER_ACTION_REQUIRED", required=False)
    blockers = [value["reason_code"] for value in gates.values() if value["required"] and not value["passed"]]
    if read_error:
        blockers.append(read_error)
    return {
        "status": "RELEASE_READY" if not blockers else "NOT_RELEASE_READY",
        "offline": True,
        "read_only": True,
        "network_used": False,
        "private_values_disclosed": False,
        "runtime": runtime,
        "first_use_rehearsal": {"status": "NOT_EXECUTED_BY_READINESS", "command": "python -m pokemind demo --json",
                                "scope": "disposable synthetic Windows/Codex workflow", "release_evidence": False},
        "database": {
            "exists": bool(database.get("database_exists")),
            "integrity": database.get("integrity"),
            "schema_version": database.get("schema_version", 0),
            "expected_schema_version": SCHEMA_VERSION,
            "schema_current": database.get("schema_version") == SCHEMA_VERSION,
        },
        "vision": vision,
        "updates": update_summary,
        "backups": backups,
        "owner": owner_summary,
        "completion": completion,
        "gates": gates,
        "technical_tests": {"status": "UNKNOWN_NO_RUNTIME_TEST_ATTESTATION", "evidence_source": "GitHub Actions at exact delivered SHA; see versioned LOT I report", "inferred_from_capability_flags": False},
        "owner_action_status": "OWNER_ACTION_REQUIRED" if any(not item["passed"] and item["category"] == "OWNER_ACTION_REQUIRED" for item in gates.values()) else "AVAILABLE",
        "product_capability_status": "PRODUCT_CAPABILITY_PARTIAL" if blockers else "RELEASE_READY",
        "blockers": blockers,
        "next_work": [
            "Essai visuel réel autorisé et calibration propriétaire distincte.",
            "Campagnes publiques bornées jusqu'aux dénominateurs et détails mesurés.",
            "Sauvegarde propriétaire vérifiée puis exercice de restauration sur clone.",
            "Collection/crédits seulement si le propriétaire choisit de les déclarer.",
        ],
    }
