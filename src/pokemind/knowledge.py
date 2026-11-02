"""Diagnostic intégré, hors ligne et en lecture seule des connaissances PokeMind."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from pokemind.cards import cards_coverage
from pokemind.database import SCHEMA_VERSION, connect_readonly, database_status, fts_checks
from pokemind.meta import meta_coverage
from pokemind.rules import rules_status
from pokemind.updates import official_validation_queue


def _ratio(numerator: int, denominator: int) -> dict[str, Any]:
    return {
        "numerator": numerator,
        "denominator": denominator,
        "ratio": round(numerator / denominator, 6) if denominator else None,
    }


def _legacy_cards(connection: Any) -> dict[str, Any]:
    printings = int(connection.execute("SELECT COUNT(*) FROM catalog_printings").fetchone()[0])
    translations = int(connection.execute("SELECT COUNT(*) FROM catalog_translations").fetchone()[0])
    present = int(connection.execute(
        "SELECT COUNT(*) FROM catalog_translations WHERE status='present'"
    ).fetchone()[0])
    return {
        "state": "requires_schema_migration",
        "sets_discovered": int(connection.execute("SELECT COUNT(*) FROM catalog_sets").fetchone()[0]),
        "unique_printings": printings,
        "translations": _ratio(present, printings * 2),
        "translation_rows": translations,
        "global_provider_total": None,
        "global_provider_total_status": "unknown",
        "known_completion_work": None,
        "reason_code": "SCHEMA_MIGRATION_REQUIRED_FOR_DETAILED_COVERAGE",
    }


def _legacy_rules(connection: Any) -> dict[str, Any]:
    source_counts = dict(connection.execute(
        "SELECT validation_status, COUNT(*) FROM official_rule_sources GROUP BY validation_status"
    ).fetchall())
    assertion_counts = dict(connection.execute(
        "SELECT validation_status, COUNT(*) FROM official_rule_assertions GROUP BY validation_status"
    ).fetchall())
    return {
        "state": "requires_schema_migration",
        "source_counts": source_counts,
        "assertion_counts": assertion_counts,
        "deck_structure_rule_counts": {},
        "reason_code": "DECK_STRUCTURE_REGISTRY_NOT_MIGRATED",
    }


def knowledge_status(db_path: Path) -> dict[str, Any]:
    """Agrège les métriques disponibles sans migration ni accès réseau."""
    base = database_status(db_path)
    result: dict[str, Any] = {
        "database": str(db_path),
        "offline": True,
        "read_only": True,
        "network_used": False,
        "as_of": date.today().isoformat(),
        "schema_version": base["schema_version"],
        "schema_current": base["schema_version"] == SCHEMA_VERSION,
        "integrity": base["integrity"],
        "cards": {"state": "absent"},
        "reprints": {"verified_assertions": 0, "status": "not_available"},
        "rules": {"state": "absent"},
        "metagame": {"state": "absent"},
        "official_validation": official_validation_queue(db_path),
        "actions": [],
        "limits": [
            "Les totaux globaux fournisseur restent unknown sans dénominateur publié ou scan terminé.",
            "Catalogue, légalité, disponibilité Live, possession et métagame sont des dimensions distinctes.",
        ],
    }
    if not db_path.is_file():
        result["actions"].append({
            "priority": 1, "code": "INITIALIZE_LOCAL_DATABASE",
            "estimated_network_gets": 0, "estimate_status": "exact",
        })
        return result
    connection = connect_readonly(db_path)
    try:
        tables = {
            str(row[0]) for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
            ).fetchall()
        }
        if {"catalog_sets", "catalog_printings", "catalog_translations"}.issubset(tables):
            if base["schema_version"] >= SCHEMA_VERSION:
                coverage = cards_coverage(db_path)
                result["cards"] = {"state": "available", **coverage}
            else:
                result["cards"] = _legacy_cards(connection)
        if {"official_rule_sources", "official_rule_assertions"}.issubset(tables):
            verified_reprints = int(connection.execute(
                """SELECT COUNT(*) FROM official_rule_assertions a
                   JOIN official_rule_sources s USING(source_id)
                   WHERE a.assertion_kind='reprint_equivalence'
                     AND a.validation_status='verified'
                     AND s.validation_status='verified'"""
            ).fetchone()[0])
            result["reprints"] = {
                "verified_assertions": verified_reprints,
                "status": "partial" if verified_reprints else "none_verified",
                "completeness": "unknown",
            }
            if (
                base["schema_version"] >= SCHEMA_VERSION
                and "official_deck_structure_rules" in tables
            ):
                result["rules"] = {"state": "available", **rules_status(db_path)}
            else:
                result["rules"] = _legacy_rules(connection)
        if "meta_tournaments" in tables and base["schema_version"] >= 7:
            result["metagame"] = {
                "state": "available",
                **meta_coverage(
                    db_path, format="standard", platform="PTCGL", online=True, since=None
                ),
            }
    finally:
        connection.close()

    actions: list[dict[str, Any]] = []
    if not result["schema_current"]:
        actions.append({
            "priority": 1, "code": "MIGRATE_WITH_BACKUP",
            "estimated_network_gets": 0, "estimate_status": "exact",
            "reason": f"schéma {result['schema_version']} < {SCHEMA_VERSION}",
        })
    cards = result["cards"]
    if cards.get("state") == "available":
        work = cards["known_completion_work"]
        remaining = int(work["detail_gets_remaining_on_discovered"])
        if remaining:
            actions.append({
                "priority": 2, "code": "FETCH_DISCOVERED_CARD_DETAILS",
                "estimated_network_gets": remaining, "estimate_status": "exact_on_discovered",
            })
        if not cards["discovery"]["complete"]:
            actions.append({
                "priority": 3, "code": "CONTINUE_CARD_INDEX_DISCOVERY",
                "estimated_network_gets": None,
                "estimate_status": "unknown_without_provider_total",
            })
    elif cards.get("state") == "requires_schema_migration":
        actions.append({
            "priority": 2, "code": "REMEASURE_CARD_COVERAGE_AFTER_MIGRATION",
            "estimated_network_gets": 0, "estimate_status": "exact",
        })
    rules = result["rules"]
    structure_verified = int(rules.get("deck_structure_rule_counts", {}).get("verified", 0))
    if not structure_verified:
        actions.append({
            "priority": 4, "code": "LOAD_VERSIONED_OFFICIAL_RULE_REGISTRY",
            "estimated_network_gets": 0, "estimate_status": "exact_local_load",
        })
    meta = result["metagame"]
    complete_meta = int(meta.get("tournaments", {}).get("complete_snapshots", 0))
    if complete_meta == 0:
        actions.append({
            "priority": 5, "code": "SYNC_PUBLIC_LIMITLESS_SAMPLE",
            "estimated_network_gets": None,
            "estimate_status": "user_budget_required",
        })
    result["actions"] = sorted(actions, key=lambda item: (item["priority"], item["code"]))
    return result


def knowledge_audit(db_path: Path) -> dict[str, Any]:
    """Ajoute des invariants de cohérence et une matrice factuelle A1–A5."""
    status = knowledge_status(db_path)
    checks: dict[str, Any] = {
        "database_integrity": status["integrity"],
        "schema_current": status["schema_current"],
        "foreign_key_violations": None,
        "sections_fts": {"status": "not_available"},
        "catalog_fts": {"status": "not_available"},
    }
    if db_path.is_file():
        connection = connect_readonly(db_path)
        try:
            tables = {
                str(row[0]) for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type IN ('table','view')"
                ).fetchall()
            }
            checks["foreign_key_violations"] = len(
                connection.execute("PRAGMA foreign_key_check").fetchall()
            )
            if {"sections", "sections_fts"}.issubset(tables):
                source = int(connection.execute("SELECT COUNT(*) FROM sections").fetchone()[0])
                indexed = int(connection.execute("SELECT COUNT(*) FROM sections_fts").fetchone()[0])
                checks["sections_fts"] = {
                    "status": "ok" if source == indexed else "mismatch",
                    "source_rows": source, "indexed_rows": indexed,
                }
            if {"catalog_translations", "catalog_fts"}.issubset(tables):
                source = int(connection.execute(
                    "SELECT COUNT(*) FROM catalog_translations"
                ).fetchone()[0])
                indexed = int(connection.execute("SELECT COUNT(*) FROM catalog_fts").fetchone()[0])
                checks["catalog_fts"] = {
                    "status": "ok" if source == indexed else "mismatch",
                    "source_rows": source, "indexed_rows": indexed,
                }
            index_evidence = fts_checks(connection)
            checks["sections_fts"] = index_evidence.get("sections_fts", {"status": "not_available"})
            checks["catalog_fts"] = index_evidence.get("catalog_fts", {"status": "not_available"})
        finally:
            connection.close()

    cards = status["cards"]
    rules = status["rules"]
    meta = status["metagame"]
    cards_complete = bool(cards.get("complete", False))
    reprints_verified = int(status["reprints"]["verified_assertions"])
    matrix = {
        "A1_catalog_discovery": {
            "status": "DONE" if cards_complete else "PARTIAL_WITH_EVIDENCE",
            "evidence": {
                "unique_printings": cards.get("unique_printings", 0),
                "discovery_complete": cards.get("discovery", {}).get("complete", False),
            },
        },
        "A2_identity_reprints": {
            "status": "PARTIAL_WITH_EVIDENCE",
            "evidence": {
                "verified_reprint_assertions": reprints_verified,
                "completeness": "unknown",
                "note": "Le mécanisme est livré; aucune attestation ne prouve un registre exhaustif.",
            },
        },
        "A3_official_rules_structure": {
            "status": "PARTIAL_WITH_EVIDENCE",
            "evidence": {
                "verified_structure_rules": int(
                    rules.get("deck_structure_rule_counts", {}).get("verified", 0)
                ),
                "coverage": rules.get("coverage", {}),
            },
        },
        "A4_limitless_metagame": {
            "status": "PARTIAL_WITH_EVIDENCE",
            "evidence": {
                "complete_snapshots": int(
                    meta.get("tournaments", {}).get("complete_snapshots", 0)
                ),
                "classifiable_matches": int(meta.get("matches", {}).get("classifiable", 0)),
                "trainer_hill": meta.get("trainer_hill", {
                    "status": "BLOCKED_WITH_REASON",
                    "reason": "Aucune donnée chargée.",
                }),
            },
        },
        "A5_integrated_audit": {
            "status": "DONE",
            "evidence": {"offline": True, "read_only": True, "checks": checks},
        },
    }
    healthy = (
        checks["database_integrity"] == "ok"
        and checks["foreign_key_violations"] in {None, 0}
        and all(
            value["status"] in {"ok", "not_available"}
            for key, value in checks.items() if key.endswith("_fts")
        )
    )
    return {
        **status,
        "audit": {
            "status": "healthy_with_partial_coverage" if healthy else "attention_required",
            "checks": checks,
            "acceptance": matrix,
        },
    }
