from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from pokemind.database import SCHEMA_VERSION, connect_writable, initialize_schema
from pokemind.rules import (
    RulesError,
    check_card,
    check_deck,
    check_deck_entries,
    default_registry_path,
    load_official_registry,
    rules_sources,
    rules_status,
)


ROOT = Path(__file__).resolve().parents[1]


def _ready_db(path: Path) -> Path:
    load_official_registry(path, default_registry_path(ROOT))
    connection = sqlite3.connect(path)
    now = "2026-01-01T00:00:00Z"
    connection.execute(
        """INSERT INTO catalog_sets
           (tcgdex_id, name_en, tcg_online_code, discovered_at, updated_at)
           VALUES ('synthetic-set', 'Synthetic', 'SYN', ?, ?)""", (now, now)
    )
    for card_id, local_id, mark, name, category, stage, energy_type in (
        ("synthetic-h", "1", "H", "Shared Name", "pokemon", "Basic", None),
        ("synthetic-g", "2", "G", "Shared Name", "pokemon", "Basic", None),
        ("synthetic-i", "3", "I", "Waiting Card", "pokemon", "Basic", None),
        ("synthetic-promo", "4", "H", "Promo Card", "pokemon", "Basic", None),
        ("synthetic-trainer", "5", "H", "Trainer Unit", "trainer", None, None),
        ("synthetic-basic-energy", "6", "H", "Basic Energy", "energy", None, "Basic"),
    ):
        connection.execute(
            """INSERT INTO catalog_printings
               (tcgdex_id, set_id, local_id, regulation_mark, category, stage,
                discovered_at, updated_at,
                brief_source_url, brief_retrieved_at)
               VALUES (?, 'synthetic-set', ?, ?, ?, ?, ?, ?,
                       'https://api.tcgdex.net/test', ?)""",
            (card_id, local_id, mark, category, stage, now, now, now),
        )
        connection.execute(
            """INSERT INTO catalog_translations
               (printing_id, language, status, name, energy_type, source_url, retrieved_at)
               VALUES (?, 'en', 'present', ?, ?, 'https://api.tcgdex.net/test', ?)""",
            (card_id, name, energy_type, now),
        )
    connection.commit()
    connection.close()
    return path


def _assertion(
    path: Path,
    assertion_id: str,
    kind: str,
    *,
    subject: str | None = None,
    payload: dict | None = None,
    status: str = "verified",
    format: str = "standard",
    platform: str = "live",
    start: str = "2026-03-26",
    end: str = "2026-10-11",
    source_id: str = "pokemon-rotation-2026-en",
) -> None:
    connection = sqlite3.connect(path)
    connection.execute(
        """INSERT INTO official_rule_assertions
           (assertion_id, source_id, assertion_kind, format, platform, effective_from,
            effective_to, subject_id, payload_json, validation_status, confidence, captured_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'high',
                   '2026-10-11T16:00:00Z')""",
        (assertion_id, source_id, kind, format, platform, start, end, subject,
         json.dumps(payload or {}, sort_keys=True), status),
    )
    connection.commit()
    connection.close()


def _coverage(path: Path, platform: str = "live") -> None:
    _assertion(path, f"coverage-{platform}", "restriction_coverage",
               payload={"complete": True}, platform=platform)


def _replace_structure_rule(
    path: Path,
    *,
    copy_exceptions_complete: bool = True,
    special_limits_complete: bool = True,
    status: str = "verified",
    end: str | None = None,
) -> None:
    connection = sqlite3.connect(path)
    connection.execute("DELETE FROM official_deck_structure_rules")
    connection.execute(
        """INSERT INTO official_deck_structure_rules
           (rule_id, source_id, format, platform, effective_from, effective_to,
            payload_json, validation_status, confidence, captured_at)
           VALUES ('synthetic-structure', 'pokemon-rulebook-par-en', NULL, NULL,
                   '2026-01-01', ?, ?, ?, 'high', '2026-10-13T00:00:00Z')""",
        (
            end,
            json.dumps({
                "required_total": 60,
                "same_name_limit": 4,
                "basic_energy_unlimited": True,
                "requires_basic_pokemon": True,
                "copy_limit_exceptions_complete": copy_exceptions_complete,
                "special_rule_limits_complete": special_limits_complete,
            }, sort_keys=True),
            status,
        ),
    )
    connection.commit()
    connection.close()


def _source(
    path: Path,
    source_id: str,
    status: str,
    *,
    start: str | None = "2026-03-26",
    end: str | None = "2026-10-11",
) -> None:
    connection = sqlite3.connect(path)
    connection.execute(
        """INSERT INTO official_rule_sources
           (source_id, source_type, url, title, language, published_date, consulted_at,
            captured_at, content_sha256, validation_status, effective_from, effective_to,
            rights_note, notes)
           VALUES (?, 'synthetic', ?, 'Synthetic source', 'en', '2026-01-01',
                   '2026-10-11T16:00:00Z', '2026-10-11T16:00:00Z', ?, ?, ?, ?,
                   'Synthetic test data', NULL)""",
        (source_id, f"https://www.pokemon.com/us/{source_id}", f"hash-{source_id}",
         status, start, end),
    )
    connection.commit()
    connection.close()


def _insert_deck_version(
    path: Path,
    deck_id: str,
    version: int,
    *,
    exact_confirmed: int,
    total_cards: int,
    cards: list[tuple[str, int, str, str | None, str | None]],
) -> None:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA ignore_check_constraints = ON")
    cursor = connection.execute(
        """INSERT INTO deck_versions
           (deck_id, version_number, imported_at, approved_at, effective_from, parser_version,
            source_kind, export_sha256, list_sha256, total_cards, entry_count, exact_confirmed,
            sections_json, coverage_json, raw_stored)
           VALUES (?, ?, 'x', 'x', 'x', 'test', 'stdin', ?, ?, ?, ?, ?, '{}', '{}', 0)""",
        (deck_id, version, f"export-{deck_id}-{version}", f"list-{deck_id}-{version}",
         total_cards, len(cards), exact_confirmed),
    )
    version_id = int(cursor.lastrowid)
    connection.executemany(
        """INSERT INTO deck_version_cards
           (deck_version_id, ordinal, source_line, card_type, quantity, card_name,
            set_code, collector_number, normalized_line)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (version_id, ordinal, ordinal, card_type, quantity, name, set_code, number,
             f"{quantity} {name} {set_code or ''} {number or ''}".strip())
            for ordinal, (card_type, quantity, name, set_code, number) in enumerate(cards, start=1)
        ],
    )
    connection.commit()
    connection.close()


def test_registry_load_is_offline_idempotent_and_versioned(local_tmp: Path) -> None:
    db_path = local_tmp / "rules.sqlite3"
    first = load_official_registry(db_path, default_registry_path(ROOT))
    second = load_official_registry(db_path, default_registry_path(ROOT))
    assert first["network_used"] is second["network_used"] is False
    assert (first["sources_loaded"], first["assertions_loaded"]) == (14, 6)
    assert first["deck_structure_rules_loaded"] == 1
    assert rules_sources(db_path)["count"] == 14
    status = rules_status(db_path)
    assert status["schema_version"] == SCHEMA_VERSION
    assert status["coverage"]["restriction_registry"] == "partial"
    assert status["deck_structure_rule_counts"] == {"verified": 1}


@pytest.mark.parametrize("source_status", ["navigation_only", "non_verified", "conflict"])
@pytest.mark.parametrize(
    "kind,subject,payload",
    [
        ("rotation", None, {"allowed_regulation_marks": ["H", "I", "J"]}),
        ("restriction", "synthetic-h", {"status": "banned"}),
        ("restriction_coverage", None, {"complete": True}),
        ("reprint_equivalence", "synthetic-g", {"current_printing_id": "synthetic-h"}),
    ],
)
def test_registry_rejects_verified_assertion_from_unverified_source_atomically(
    local_tmp: Path,
    source_status: str,
    kind: str,
    subject: str | None,
    payload: dict,
) -> None:
    db_path = local_tmp / f"atomic-{source_status}-{kind}.sqlite3"
    load_official_registry(db_path, default_registry_path(ROOT))
    connection = sqlite3.connect(db_path)
    before = (
        connection.execute("SELECT COUNT(*) FROM official_rule_sources").fetchone()[0],
        connection.execute("SELECT COUNT(*) FROM official_rule_assertions").fetchone()[0],
        connection.execute(
            "SELECT value FROM metadata WHERE key='official_rules_registry_version'"
        ).fetchone()[0],
    )
    connection.close()
    registry = {
        "registry_version": "must-not-be-written",
        "consulted_at": "2026-10-11T16:00:00Z",
        "sources": [
            {
                "source_id": "synthetic-source",
                "source_type": "synthetic",
                "url": "https://www.pokemon.com/us/synthetic-source",
                "title": "Synthetic source",
                "language": "en",
                "validation_status": source_status,
                "rights_note": "Synthetic test data",
            }
        ],
        "assertions": [
            {
                "assertion_id": f"synthetic-{kind}",
                "source_id": "synthetic-source",
                "assertion_kind": kind,
                "format": "standard",
                "platform": "live",
                "effective_from": "2026-03-26",
                "effective_to": "2026-10-11",
                "subject_id": subject,
                "payload": payload,
                "validation_status": "verified",
                "confidence": "high",
            }
        ],
    }
    registry_path = local_tmp / f"invalid-{source_status}-{kind}.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    with pytest.raises(RulesError, match="Assertion verified sans source verified"):
        load_official_registry(db_path, registry_path)

    connection = sqlite3.connect(db_path)
    after = (
        connection.execute("SELECT COUNT(*) FROM official_rule_sources").fetchone()[0],
        connection.execute("SELECT COUNT(*) FROM official_rule_assertions").fetchone()[0],
        connection.execute(
            "SELECT value FROM metadata WHERE key='official_rules_registry_version'"
        ).fetchone()[0],
    )
    connection.close()
    assert after == before


def test_migration_to_six_preserves_private_tables_and_creates_backup(local_tmp: Path) -> None:
    db_path = local_tmp / "migration.sqlite3"
    connection = connect_writable(db_path)
    initialize_schema(connection)
    connection.execute("PRAGMA user_version = 5")
    connection.execute("INSERT INTO observed_decks VALUES ('private', 'observé partiellement', 'x', 'x')")
    connection.commit()
    connection.close()
    load_official_registry(db_path, default_registry_path(ROOT))
    connection = sqlite3.connect(db_path)
    assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert connection.execute("SELECT deck_id FROM observed_decks").fetchone()[0] == "private"
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    backup = Path(connection.execute("SELECT value FROM metadata WHERE key='last_schema_backup'").fetchone()[0])
    connection.close()
    restored = sqlite3.connect(backup)
    assert restored.execute("PRAGMA user_version").fetchone()[0] == 5
    assert restored.execute("SELECT deck_id FROM observed_decks").fetchone()[0] == "private"
    restored.close()


def test_platform_activation_dates_and_future_are_unknown(local_tmp: Path) -> None:
    db_path = _ready_db(local_tmp / "dates.sqlite3")
    _coverage(db_path, "live")
    _coverage(db_path, "in_person")
    assert check_card(db_path, "synthetic-h", format="standard", platform="live", as_of="2026-03-25")["status"] == "unknown"
    assert check_card(db_path, "synthetic-h", format="standard", platform="live", as_of="2026-03-26")["status"] == "legal"
    assert check_card(db_path, "synthetic-h", format="standard", platform="in_person", as_of="2026-04-09")["status"] == "unknown"
    assert check_card(db_path, "synthetic-h", format="standard", platform="in_person", as_of="2026-04-10")["status"] == "legal"
    future = check_card(db_path, "synthetic-h", format="standard", platform="live", as_of="2026-10-12")
    assert future["status"] == "unknown"
    assert "NO_UNIQUE_ACTIVE_ROTATION" in future["reason_codes"]


@pytest.mark.parametrize("source_status", ["navigation_only", "non_verified", "conflict"])
@pytest.mark.parametrize("kind", ["rotation", "restriction", "restriction_coverage", "reprint_equivalence"])
def test_incoherent_historical_rows_never_create_normative_certainty(
    local_tmp: Path, source_status: str, kind: str
) -> None:
    db_path = _ready_db(local_tmp / f"historical-{source_status}-{kind}.sqlite3")
    source_id = f"unsafe-{source_status}-{kind}"
    _source(db_path, source_id, source_status)
    subject = "synthetic-h" if kind == "restriction" else (
        "synthetic-g" if kind == "reprint_equivalence" else None
    )
    payload = {
        "rotation": {"allowed_regulation_marks": ["H", "I", "J"]},
        "restriction": {"status": "banned"},
        "restriction_coverage": {"complete": True},
        "reprint_equivalence": {
            "current_printing_id": "synthetic-h",
            "functional_identity_verified": True,
        },
    }[kind]
    _assertion(
        db_path, f"unsafe-assertion-{source_status}-{kind}", kind,
        subject=subject, payload=payload, source_id=source_id,
    )
    if kind in {"restriction", "reprint_equivalence"}:
        _coverage(db_path)
    card_id = "synthetic-g" if kind == "reprint_equivalence" else "synthetic-h"

    result = check_card(db_path, card_id, format="standard", platform="live", as_of="2026-05-01")

    assert result["status"] == "unknown"
    expected = "CONFLICTING_OFFICIAL_SOURCES" if source_status == "conflict" else "UNVERIFIED_NORMATIVE_SOURCE"
    assert expected in result["reason_codes"]


def test_non_verified_assertion_stays_non_normative_in_historical_database(local_tmp: Path) -> None:
    db_path = _ready_db(local_tmp / "assertion-status.sqlite3")
    _coverage(db_path)
    _assertion(
        db_path, "unverified-ban", "restriction", subject="synthetic-h",
        payload={"status": "banned"}, status="non_verified",
    )

    result = check_card(db_path, "synthetic-h", format="standard", platform="live", as_of="2026-05-01")

    assert result["status"] == "unknown"
    assert "UNVERIFIED_OFFICIAL_ASSERTION" in result["reason_codes"]


def test_unverified_source_for_another_printing_does_not_mask_valid_evidence(local_tmp: Path) -> None:
    db_path = _ready_db(local_tmp / "irrelevant-source.sqlite3")
    _coverage(db_path)
    _source(db_path, "unverified-other-card", "non_verified")
    _assertion(
        db_path, "unverified-other-ban", "restriction", subject="synthetic-i",
        payload={"status": "banned"}, source_id="unverified-other-card",
    )

    result = check_card(db_path, "synthetic-h", format="standard", platform="live", as_of="2026-05-01")

    assert result["status"] == "legal"
    assert "UNVERIFIED_NORMATIVE_SOURCE" not in result["reason_codes"]


def test_source_effective_window_bounds_verified_assertion(local_tmp: Path) -> None:
    db_path = _ready_db(local_tmp / "source-window.sqlite3")
    _source(db_path, "expiring-coverage", "verified", end="2026-04-30")
    _assertion(
        db_path, "coverage-beyond-source", "restriction_coverage",
        payload={"complete": True}, source_id="expiring-coverage",
    )

    active = check_card(db_path, "synthetic-h", format="standard", platform="live", as_of="2026-04-15")
    expired = check_card(db_path, "synthetic-h", format="standard", platform="live", as_of="2026-05-01")

    assert active["status"] == "legal"
    assert expired["status"] == "unknown"
    assert "RESTRICTIONS_NOT_FULLY_VERIFIED" in expired["reason_codes"]


def test_old_mark_requires_explicit_reprint_identity(local_tmp: Path) -> None:
    db_path = _ready_db(local_tmp / "reprints.sqlite3")
    _coverage(db_path)
    unproved = check_card(db_path, "synthetic-g", format="standard", platform="live", as_of="2026-05-01")
    assert unproved["status"] == "unknown"
    assert "REPRINT_EQUIVALENCE_UNVERIFIED" in unproved["reason_codes"]
    _assertion(db_path, "proved-reprint", "reprint_equivalence", subject="synthetic-g",
               payload={"current_printing_id": "synthetic-h", "functional_identity_verified": True})
    proved = check_card(db_path, "synthetic-g", format="standard", platform="live", as_of="2026-05-01")
    assert proved["status"] == "legal"
    assert "FUNCTIONAL_REPRINT_VERIFIED" in proved["reason_codes"]


def test_explicit_no_reprint_ban_waiting_conflict_and_promo(local_tmp: Path) -> None:
    db_path = _ready_db(local_tmp / "decisions.sqlite3")
    _coverage(db_path)
    _assertion(db_path, "no-reprint", "reprint_equivalence", subject="synthetic-g",
               payload={"no_current_equivalent": True})
    assert check_card(db_path, "synthetic-g", format="standard", platform="live", as_of="2026-05-01")["status"] == "not_legal"
    _assertion(db_path, "ban-h", "restriction", subject="synthetic-h", payload={"status": "banned"})
    assert check_card(db_path, "synthetic-h", format="standard", platform="live", as_of="2026-05-01")["status"] == "not_legal"
    _assertion(db_path, "waiting-i", "release_window", subject="synthetic-i",
               payload={"legal_from": "2026-05-15"})
    waiting = check_card(db_path, "synthetic-i", format="standard", platform="live", as_of="2026-05-01")
    assert waiting["status"] == "not_legal" and "WAITING_PERIOD_ACTIVE" in waiting["reason_codes"]
    promo = check_card(db_path, "synthetic-promo", format="expanded", platform="in_person", as_of="2026-05-01")
    assert promo["status"] == "unknown"
    _assertion(db_path, "conflict-i", "errata", subject="synthetic-i", payload={}, status="conflict")
    conflict = check_card(db_path, "synthetic-i", format="standard", platform="live", as_of="2026-05-20")
    assert conflict["status"] == "unknown"
    assert "CONFLICTING_OFFICIAL_ASSERTIONS" in conflict["reason_codes"]


def test_deck_legality_fails_closed_for_every_unverified_structure(local_tmp: Path) -> None:
    db_path = _ready_db(local_tmp / "deck-guards.sqlite3")
    _coverage(db_path)
    legal_pokemon = [("pokemon", 60, "Shared Name", "SYN", "1")]
    legal_trainers = [("trainer", 60, "Trainer Unit", "SYN", "5")]
    _insert_deck_version(
        db_path, "unconfirmed", 1, exact_confirmed=0, total_cards=60, cards=legal_pokemon,
    )
    _insert_deck_version(
        db_path, "latest-unconfirmed", 1, exact_confirmed=1, total_cards=60, cards=legal_pokemon,
    )
    _insert_deck_version(
        db_path, "latest-unconfirmed", 2, exact_confirmed=0, total_cards=60, cards=legal_pokemon,
    )
    _insert_deck_version(
        db_path, "fifty-nine", 1, exact_confirmed=1, total_cards=59,
        cards=[("pokemon", 59, "Shared Name", "SYN", "1")],
    )
    _insert_deck_version(
        db_path, "mismatched-total", 1, exact_confirmed=1, total_cards=60,
        cards=[("pokemon", 59, "Shared Name", "SYN", "1")],
    )
    _insert_deck_version(
        db_path, "sixty-copies", 1, exact_confirmed=1, total_cards=60, cards=legal_pokemon,
    )
    _insert_deck_version(
        db_path, "zero-basic", 1, exact_confirmed=1, total_cards=60, cards=legal_trainers,
    )
    _insert_deck_version(
        db_path, "unknown-entry", 1, exact_confirmed=1, total_cards=60,
        cards=[
            ("pokemon", 59, "Shared Name", "SYN", "1"),
            ("trainer", 1, "Missing Card", "NONE", "999"),
        ],
    )
    connection = sqlite3.connect(db_path)
    before = (
        connection.execute("SELECT COUNT(*) FROM deck_versions").fetchone()[0],
        connection.execute("SELECT COUNT(*) FROM deck_version_cards").fetchone()[0],
        connection.execute("SELECT GROUP_CONCAT(list_sha256, '|') FROM deck_versions ORDER BY id").fetchone()[0],
    )
    connection.close()

    results = {
        deck_id: check_deck(
            db_path, deck_id, format="standard", platform="live", as_of="2026-05-01"
        )
        for deck_id in (
            "unconfirmed", "latest-unconfirmed", "fifty-nine", "mismatched-total",
            "sixty-copies", "zero-basic", "unknown-entry",
        )
    }

    assert results["fifty-nine"]["status"] == "not_legal"
    assert results["zero-basic"]["status"] == "not_legal"
    assert all(
        results[deck_id]["status"] == "unknown"
        for deck_id in (
            "unconfirmed", "latest-unconfirmed", "mismatched-total",
            "sixty-copies", "unknown-entry",
        )
    )
    assert results["unconfirmed"]["exact_confirmed"] is False
    assert "DECK_VERSION_UNCONFIRMED" in results["unconfirmed"]["reason_codes"]
    assert results["latest-unconfirmed"]["deck_version"] == 2
    assert results["latest-unconfirmed"]["exact_confirmed"] is False
    assert "DECK_TOTAL_NOT_REQUIRED_COUNT" in results["fifty-nine"]["reason_codes"]
    assert results["mismatched-total"]["total_cards"] == 60
    assert results["mismatched-total"]["quantity_sum"] == 59
    assert "DECK_TOTAL_QUANTITY_MISMATCH" in results["mismatched-total"]["reason_codes"]
    assert results["sixty-copies"]["cards"][0]["verdict"]["status"] == "legal"
    assert results["zero-basic"]["cards"][0]["verdict"]["status"] == "legal"
    assert "DECK_HAS_NO_BASIC_POKEMON" in results["zero-basic"]["reason_codes"]
    assert "DECK_CARD_LEGALITY_UNKNOWN" in results["unknown-entry"]["reason_codes"]
    connection = sqlite3.connect(db_path)
    after = (
        connection.execute("SELECT COUNT(*) FROM deck_versions").fetchone()[0],
        connection.execute("SELECT COUNT(*) FROM deck_version_cards").fetchone()[0],
        connection.execute("SELECT GROUP_CONCAT(list_sha256, '|') FROM deck_versions ORDER BY id").fetchone()[0],
    )
    connection.close()
    assert after == before


def test_not_legal_card_is_decisive_without_hiding_unknown_structure(local_tmp: Path) -> None:
    db_path = _ready_db(local_tmp / "deck-not-legal.sqlite3")
    _coverage(db_path)
    _assertion(
        db_path, "ban-synthetic-h", "restriction", subject="synthetic-h",
        payload={"status": "banned"},
    )
    _insert_deck_version(
        db_path, "banned-card", 1, exact_confirmed=1, total_cards=60,
        cards=[("pokemon", 60, "Shared Name", "SYN", "1")],
    )

    result = check_deck(
        db_path, "banned-card", format="standard", platform="live", as_of="2026-05-01"
    )

    assert result["status"] == "not_legal"
    assert "DECK_CONTAINS_NOT_LEGAL_CARD" in result["reason_codes"]
    assert "DECK_STRUCTURE_NOT_VERIFIED" in result["reason_codes"]
    assert result["structure_validation"]["status"] == "unknown"


def test_partial_real_registry_never_false_legal_and_deck_is_read_only(local_tmp: Path) -> None:
    db_path = _ready_db(local_tmp / "deck.sqlite3")
    connection = sqlite3.connect(db_path)
    connection.execute(
        """INSERT INTO deck_versions
           (deck_id, version_number, imported_at, approved_at, effective_from, parser_version,
            source_kind, export_sha256, list_sha256, total_cards, entry_count, exact_confirmed,
            sections_json, coverage_json, raw_stored)
           VALUES ('synthetic', 1, 'x', 'x', 'x', 'test', 'stdin', 'a', 'b', 60, 1, 1, '{}', '{}', 0)"""
    )
    version_id = connection.execute("SELECT id FROM deck_versions").fetchone()[0]
    connection.execute(
        """INSERT INTO deck_version_cards
           (deck_version_id, ordinal, source_line, card_type, quantity, card_name,
            set_code, collector_number, normalized_line)
           VALUES (?, 1, 1, 'pokemon', 60, 'Shared Name', 'SYN', '1', '60 Shared Name SYN 1')""",
        (version_id,),
    )
    before = connection.execute("SELECT COUNT(*) FROM deck_version_cards").fetchone()[0]
    connection.commit()
    connection.close()
    card = check_card(db_path, "synthetic-h", format="standard", platform="live", as_of="2026-05-01")
    assert card["status"] == "unknown"
    assert "RESTRICTIONS_NOT_FULLY_VERIFIED" in card["reason_codes"]
    deck = check_deck(db_path, "synthetic", format="standard", platform="live", as_of="2026-05-01")
    assert deck["status"] == "unknown" and deck["read_only"] is True
    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT COUNT(*) FROM deck_version_cards").fetchone()[0] == before
    connection.close()


def test_fully_sourced_structure_can_be_legal_or_demonstrably_not_legal(
    local_tmp: Path,
) -> None:
    db_path = _ready_db(local_tmp / "complete-structure.sqlite3")
    _coverage(db_path)
    _replace_structure_rule(db_path)
    _insert_deck_version(
        db_path, "valid", 1, exact_confirmed=1, total_cards=60,
        cards=[
            ("pokemon", 4, "Shared Name", "SYN", "1"),
            ("energy", 56, "Basic Energy", "SYN", "6"),
        ],
    )
    _insert_deck_version(
        db_path, "five-copies", 1, exact_confirmed=1, total_cards=60,
        cards=[
            ("pokemon", 5, "Shared Name", "SYN", "1"),
            ("energy", 55, "Basic Energy", "SYN", "6"),
        ],
    )
    _insert_deck_version(
        db_path, "no-basic", 1, exact_confirmed=1, total_cards=60,
        cards=[
            ("trainer", 4, "Trainer Unit", "SYN", "5"),
            ("energy", 56, "Basic Energy", "SYN", "6"),
        ],
    )
    _insert_deck_version(
        db_path, "sixty-one", 1, exact_confirmed=1, total_cards=61,
        cards=[
            ("pokemon", 4, "Shared Name", "SYN", "1"),
            ("energy", 57, "Basic Energy", "SYN", "6"),
        ],
    )

    valid = check_deck(
        db_path, "valid", format="standard", platform="live", as_of="2026-05-01"
    )
    copies = check_deck(
        db_path, "five-copies", format="standard", platform="live", as_of="2026-05-01"
    )
    no_basic = check_deck(
        db_path, "no-basic", format="standard", platform="live", as_of="2026-05-01"
    )
    sixty_one = check_deck(
        db_path, "sixty-one", format="standard", platform="live", as_of="2026-05-01"
    )

    assert valid["status"] == "legal"
    assert valid["structure_validation"]["status"] == "legal"
    assert valid["structure_validation"]["checks"]["basic_pokemon_count"] == 4
    assert copies["structure_validation"]["status"] == "not_legal"
    assert "DECK_COPY_LIMIT_EXCEEDED" in copies["reason_codes"]
    assert no_basic["structure_validation"]["status"] == "not_legal"
    assert "DECK_HAS_NO_BASIC_POKEMON" in no_basic["reason_codes"]
    assert sixty_one["structure_validation"]["status"] == "not_legal"
    assert "DECK_TOTAL_NOT_REQUIRED_COUNT" in sixty_one["reason_codes"]


def test_one_ace_spec_and_one_radiant_per_deck(local_tmp: Path) -> None:
    db_path = _ready_db(local_tmp / "special-limits.sqlite3")
    connection = sqlite3.connect(db_path)
    now = "2026-01-01T00:00:00Z"
    for card_id, local_id, name, category, stage, rarity in (
        ("synthetic-ace-1", "7", "Invented Stamp", "trainer", None, "ACE SPEC Rare"),
        ("synthetic-ace-2", "8", "Invented Catcher", "trainer", None, "ACE SPEC Rare"),
        ("synthetic-radiant-1", "9", "Radiant Inventmon", "pokemon", "Basic", "Radiant Rare"),
        ("synthetic-radiant-2", "10", "Radiant Fakemon", "pokemon", "Basic", "Radiant Rare"),
    ):
        connection.execute(
            """INSERT INTO catalog_printings (tcgdex_id, set_id, local_id, regulation_mark, category, stage, rarity,
               discovered_at, updated_at, brief_source_url, brief_retrieved_at)
               VALUES (?, 'synthetic-set', ?, 'H', ?, ?, ?, ?, ?, 'https://api.tcgdex.net/test', ?)""",
            (card_id, local_id, category, stage, rarity, now, now, now))
        connection.execute(
            """INSERT INTO catalog_translations (printing_id, language, status, name, energy_type, source_url, retrieved_at)
               VALUES (?, 'en', 'present', ?, NULL, 'https://api.tcgdex.net/test', ?)""", (card_id, name, now))
    connection.commit()
    connection.close()
    _coverage(db_path)
    _replace_structure_rule(db_path)

    def deck(*extra):
        lines = [(4, "Shared Name", "1"), *extra]
        lines.append((60 - sum(q for q, _, _ in lines), "Basic Energy", "6"))
        entries = [{"ordinal": i, "card_name": name, "set_code": "SYN", "collector_number": number, "quantity": q}
                   for i, (q, name, number) in enumerate(lines, 1)]
        return check_deck_entries(db_path, entries, total_cards=60, exact_confirmed=True, format="standard",
                                  platform="live", as_of="2026-05-01")

    one = deck((1, "Invented Stamp", "7"), (1, "Radiant Inventmon", "9"))
    assert one["structure_validation"]["status"] == "legal"
    assert one["structure_validation"]["checks"]["ace_spec_count"] == 1
    two_aces = deck((1, "Invented Stamp", "7"), (1, "Invented Catcher", "8"))
    assert two_aces["structure_validation"]["status"] == "not_legal"
    assert "DECK_ACE_SPEC_LIMIT_EXCEEDED" in two_aces["reason_codes"]
    same_ace_twice = deck((2, "Invented Stamp", "7"))
    assert "DECK_ACE_SPEC_LIMIT_EXCEEDED" in same_ace_twice["reason_codes"]
    two_radiants = deck((1, "Radiant Inventmon", "9"), (1, "Radiant Fakemon", "10"))
    assert "DECK_RADIANT_LIMIT_EXCEEDED" in two_radiants["reason_codes"]
    assert "DECK_ACE_SPEC_LIMIT_EXCEEDED" not in two_radiants["reason_codes"]


def test_incomplete_exceptions_conflicts_and_expired_windows_stay_unknown(
    local_tmp: Path,
) -> None:
    db_path = _ready_db(local_tmp / "structure-unknown.sqlite3")
    _coverage(db_path)
    _replace_structure_rule(db_path, copy_exceptions_complete=False)
    _insert_deck_version(
        db_path, "candidate", 1, exact_confirmed=1, total_cards=60,
        cards=[
            ("pokemon", 5, "Shared Name", "SYN", "1"),
            ("energy", 55, "Basic Energy", "SYN", "6"),
        ],
    )
    incomplete = check_deck(
        db_path, "candidate", format="standard", platform="live", as_of="2026-05-01"
    )
    assert incomplete["status"] == "unknown"
    assert "COPY_LIMIT_EXCEPTION_REGISTRY_INCOMPLETE" in incomplete["reason_codes"]

    connection = sqlite3.connect(db_path)
    connection.execute(
        "UPDATE official_rule_sources SET validation_status='conflict' "
        "WHERE source_id='pokemon-rulebook-par-en'"
    )
    connection.commit()
    connection.close()
    conflict = check_deck(
        db_path, "candidate", format="standard", platform="live", as_of="2026-05-01"
    )
    assert conflict["structure_validation"]["status"] == "unknown"
    assert "CONFLICTING_DECK_STRUCTURE_RULES" in conflict["reason_codes"]

    connection = sqlite3.connect(db_path)
    connection.execute(
        "UPDATE official_rule_sources SET validation_status='verified' "
        "WHERE source_id='pokemon-rulebook-par-en'"
    )
    connection.execute(
        "UPDATE official_deck_structure_rules SET effective_to='2026-04-30'"
    )
    connection.commit()
    connection.close()
    expired = check_deck(
        db_path, "candidate", format="standard", platform="live", as_of="2026-05-01"
    )
    assert expired["structure_validation"]["status"] == "unknown"
    assert "DECK_STRUCTURE_RULE_NOT_FOUND" in expired["reason_codes"]


def test_registry_rejects_verified_structure_rule_from_unverified_source(
    local_tmp: Path,
) -> None:
    registry = {
        "registry_version": "invalid-structure",
        "consulted_at": "2026-10-13T00:00:00Z",
        "sources": [{
            "source_id": "unverified-rulebook",
            "source_type": "official_pdf",
            "url": "https://assets.pokemon.com/test.pdf",
            "title": "Unverified",
            "language": "en",
            "validation_status": "non_verified",
            "rights_note": "Synthetic fixture",
        }],
        "assertions": [],
        "deck_structure_rules": [{
            "rule_id": "bad-structure",
            "source_id": "unverified-rulebook",
            "format": None,
            "platform": None,
            "payload": {
                "required_total": 60,
                "same_name_limit": 4,
                "basic_energy_unlimited": True,
                "requires_basic_pokemon": True,
                "copy_limit_exceptions_complete": True,
                "special_rule_limits_complete": True,
            },
            "validation_status": "verified",
            "confidence": "high",
        }],
    }
    registry_path = local_tmp / "invalid-structure.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    with pytest.raises(RulesError, match="verified sans source verified"):
        load_official_registry(local_tmp / "never-created.sqlite3", registry_path)
    assert not (local_tmp / "never-created.sqlite3").exists()


def test_schema_eight_to_nine_backup_and_lot_a_rollback(local_tmp: Path) -> None:
    db_path = local_tmp / "schema-eight.sqlite3"
    connection = connect_writable(db_path)
    initialize_schema(connection)
    connection.execute("DROP TABLE official_deck_structure_rules")
    connection.execute("PRAGMA user_version = 8")
    connection.execute(
        "INSERT INTO observed_decks VALUES ('private', 'observé partiellement', 'x', 'x')"
    )
    connection.commit()
    initialize_schema(connection)
    backup = Path(connection.execute(
        "SELECT value FROM metadata WHERE key='last_schema_backup'"
    ).fetchone()[0])
    assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert connection.execute("SELECT deck_id FROM observed_decks").fetchone()[0] == "private"
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    connection.close()
    restored = sqlite3.connect(backup)
    assert restored.execute("PRAGMA user_version").fetchone()[0] == 8
    assert restored.execute("SELECT deck_id FROM observed_decks").fetchone()[0] == "private"
    restored.close()

    rollback_path = local_tmp / "schema-eight-rollback.sqlite3"
    connection = connect_writable(rollback_path)
    initialize_schema(connection)
    connection.execute("DROP TABLE official_deck_structure_rules")
    connection.execute("PRAGMA user_version = 8")
    connection.commit()

    def deny_lot_a_table(
        action: int, arg1: str | None, arg2: str | None,
        database: str | None, source: str | None,
    ) -> int:
        if action == sqlite3.SQLITE_CREATE_TABLE and arg1 == "official_deck_structure_rules":
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK

    connection.set_authorizer(deny_lot_a_table)
    with pytest.raises(sqlite3.DatabaseError):
        initialize_schema(connection)
    connection.set_authorizer(None)
    assert connection.execute("PRAGMA user_version").fetchone()[0] == 8
    assert connection.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE name='official_deck_structure_rules'"
    ).fetchone()[0] == 0
    connection.close()
