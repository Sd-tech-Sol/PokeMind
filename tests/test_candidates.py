from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from pokemind.candidates import _validate_candidate, create_candidate, export_candidate, show_candidate
from pokemind.database import connect_writable, initialize_schema
from pokemind.decks import import_deck, parse_deck_export


BASE_DECK = """Pokémon: 1
4 Alpha SYN 1

Trainer: 1
52 Support SYN 2

Energy: 1
4 Basic Energy SYN 3

Total Cards: 60
"""


def _ready_db(db_path: Path, *, complete_rule: bool = False) -> None:
    import_deck(db_path, BASE_DECK, deck_id="synthetic", source_kind="stdin")
    connection = connect_writable(db_path)
    try:
        initialize_schema(connection)
        now = "2026-10-13T00:00:00Z"
        connection.execute(
            "INSERT INTO catalog_sets(tcgdex_id,name_en,tcg_online_code,discovered_at,updated_at) VALUES('syn','Syn','SYN',?,?)",
            (now, now),
        )
        for printing, number, name, category, stage, energy_type in (
            ("syn-1", "1", "Alpha", "pokemon", "Basic", None),
            ("syn-2", "2", "Support", "trainer", None, None),
            ("syn-3", "3", "Basic Energy", "energy", None, "Basic"),
            ("syn-4", "4", "Beta", "pokemon", "Basic", None),
            ("syn-5", "5", "Alpha", "pokemon", "Basic", None),
        ):
            connection.execute(
                """INSERT INTO catalog_printings
                   (tcgdex_id,set_id,local_id,category,stage,discovered_at,updated_at,
                    brief_source_url,brief_retrieved_at)
                   VALUES(?,'syn',?,?,?,?,?,'https://api.tcgdex.net/v2/en/cards',?)""",
                (printing, number, category, stage, now, now, now),
            )
            connection.execute(
                """INSERT INTO catalog_translations
                   (printing_id,language,status,name,category,energy_type,source_url,retrieved_at)
                   VALUES(?,'en','present',?,?,?,?,?)""",
                (printing, name, category, energy_type,
                 f"https://api.tcgdex.net/v2/en/cards/{printing}", now),
            )
        if complete_rule:
            connection.execute(
                """INSERT INTO official_rule_sources
                   (source_id,source_type,url,title,language,published_date,consulted_at,captured_at,
                    content_sha256,validation_status,effective_from,effective_to,rights_note,notes)
                   VALUES('structure','rulebook','https://www.pokemon.com/rules','Rules','en','2026-01-01',?,?,
                          'synthetic','verified','2026-01-01',NULL,'test',NULL)""",
                (now, now),
            )
            connection.execute(
                """INSERT INTO official_deck_structure_rules
                   (rule_id,source_id,format,platform,effective_from,effective_to,payload_json,
                    validation_status,confidence,captured_at)
                   VALUES('structure-1','structure','standard','live','2026-01-01',NULL,?,
                          'verified','high',?)""",
                (json.dumps({
                    "exact_deck_size": 60,
                    "same_name_limit": 4,
                    "basic_energy_unlimited": True,
                    "requires_basic_pokemon": True,
                    "copy_limit_exceptions_complete": True,
                    "special_rule_limits_complete": True,
                }), now),
            )
        connection.commit()
    finally:
        connection.close()


def _changes(path: Path, changes: list[dict[str, object]], *, name: str = "Candidate") -> Path:
    path.write_text(json.dumps({
        "schema_version": 1,
        "name": name,
        "base_deck": {"deck_id": "synthetic", "version": 1},
        "context": {"format": "standard", "platform": "live", "as_of": "2026-10-13"},
        "source": {"kind": "owner_controlled_changes"},
        "changes": changes,
    }, ensure_ascii=False), encoding="utf-8")
    return path


def _remove(name: str, number: str, quantity: int) -> dict[str, object]:
    return {"action": "remove", "name": name, "set_code": "SYN", "collector_number": number, "quantity": quantity}


def _add(card_type: str, name: str, number: str, quantity: int) -> dict[str, object]:
    return {"action": "add", "type": card_type, "name": name, "set_code": "SYN", "collector_number": number, "quantity": quantity}


def test_candidate_cycle_preview_apply_show_export_and_roundtrip(local_tmp: Path) -> None:
    db_path = local_tmp / "candidate.sqlite3"
    _ready_db(db_path)
    changes = _changes(local_tmp / "changes.json", [_remove("Support", "2", 1), _add("pokemon", "Beta", "4", 1)])
    before = hashlib.sha256(db_path.read_bytes()).hexdigest()
    preview = create_candidate(db_path, changes)
    assert preview["status"] == "UNKNOWN_LEGALITY"
    assert preview["read_only"] is True and preview["deck_version_created"] is False
    assert sum(card["quantity"] for card in preview["cards"]) == 60
    assert hashlib.sha256(db_path.read_bytes()).hexdigest() == before
    with pytest.raises(ValueError, match="--confirm-owner"):
        create_candidate(db_path, changes, apply=True)

    created = create_candidate(db_path, changes, apply=True, confirm_owner=True)
    shown = show_candidate(db_path, created["candidate_id"])
    assert shown["status"] == "UNKNOWN_LEGALITY" and shown["distinct_from_played_version"] is True
    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT COUNT(*) FROM deck_versions").fetchone()[0] == 1
    connection.close()

    root = local_tmp / "decks"
    export_preview = export_candidate(db_path, created["candidate_id"], root)
    assert export_preview["read_only"] is True and not Path(export_preview["text_path"]).exists()
    with pytest.raises(ValueError, match="--confirm-owner"):
        export_candidate(db_path, created["candidate_id"], root, apply=True)
    exported = export_candidate(db_path, created["candidate_id"], root, apply=True, confirm_owner=True)
    assert Path(exported["text_path"]).is_file() and Path(exported["report_path"]).is_file()
    assert Path(exported["text_path"]).resolve().is_relative_to(root.resolve())
    assert parse_deck_export(Path(exported["text_path"]).read_text(encoding="utf-8")).total_cards == 60
    assert exported["transmitted_to_game"] is False and exported["credits_spent"] == 0
    duplicate = export_candidate(db_path, created["candidate_id"], root, apply=True, confirm_owner=True)
    assert duplicate["duplicate"] is True
    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT COUNT(*) FROM deck_versions").fetchone()[0] == 1
    connection.close()


@pytest.mark.parametrize(
    ("changes", "total"),
    [
        ([_remove("Support", "2", 1)], 59),
        ([_add("pokemon", "Beta", "4", 1)], 61),
    ],
)
def test_candidate_rejects_59_and_61(local_tmp: Path, changes: list[dict[str, object]], total: int) -> None:
    db_path = local_tmp / f"invalid-{total}.sqlite3"
    _ready_db(db_path)
    result = create_candidate(db_path, _changes(local_tmp / f"invalid-{total}.json", changes))
    assert result["status"] == "REJECTED_INVALID_60"
    assert result["validation"]["checks"]["total_cards"] == total


def test_candidate_rejects_absent_basic_and_proven_five_copy_violation(local_tmp: Path) -> None:
    db_path = local_tmp / "structure.sqlite3"
    _ready_db(db_path, complete_rule=True)
    no_basic = create_candidate(
        db_path,
        _changes(local_tmp / "no-basic.json", [_remove("Alpha", "1", 4), _add("trainer", "Support", "2", 4)]),
    )
    assert no_basic["status"] == "REJECTED_STRUCTURE"
    assert "CANDIDATE_NO_BASIC_POKEMON" in no_basic["validation"]["reason_codes"]

    five = create_candidate(
        db_path,
        _changes(local_tmp / "five.json", [_remove("Support", "2", 1), _add("pokemon", "Alpha", "1", 1)]),
    )
    assert five["status"] == "REJECTED_STRUCTURE"
    assert "CANDIDATE_COPY_LIMIT_EXCEEDED" in five["validation"]["reason_codes"]


def test_candidate_keeps_exact_reprint_identity_and_unknown_cards_are_not_substituted(local_tmp: Path) -> None:
    db_path = local_tmp / "identity.sqlite3"
    _ready_db(db_path)
    exact_reprint = create_candidate(
        db_path,
        _changes(local_tmp / "reprint.json", [_remove("Support", "2", 1), _add("pokemon", "Alpha", "5", 1)]),
    )
    added = next(card for card in exact_reprint["cards"] if card["collector_number"] == "5")
    assert added["tcgdex_id"] == "syn-5" and added["status"] == "resolved"
    assert any(card["tcgdex_id"] == "syn-1" for card in exact_reprint["cards"])

    unknown = create_candidate(
        db_path,
        _changes(local_tmp / "unknown.json", [_remove("Support", "2", 1), _add("pokemon", "Mystery", "999", 1)]),
    )
    mysterious = next(card for card in unknown["cards"] if card["collector_number"] == "999")
    assert unknown["status"] == "UNKNOWN_LEGALITY"
    assert mysterious["tcgdex_id"] is None and mysterious["status"] == "unknown"


def test_rejected_candidate_cannot_export_and_changes_are_idempotent(local_tmp: Path) -> None:
    db_path = local_tmp / "rejected.sqlite3"
    _ready_db(db_path)
    changes = _changes(local_tmp / "rejected.json", [_remove("Support", "2", 1)])
    first = create_candidate(db_path, changes, apply=True, confirm_owner=True)
    second = create_candidate(db_path, changes, apply=True, confirm_owner=True)
    assert first["status"] == "REJECTED_INVALID_60" and second["duplicate"] is True
    with pytest.raises(ValueError, match="rejeté"):
        export_candidate(db_path, first["candidate_id"], local_tmp / "decks")


def test_zero_energy_or_trainer_is_not_an_invented_structure_violation(local_tmp: Path) -> None:
    db_path = local_tmp / "optional-sections.sqlite3"
    _ready_db(db_path, complete_rule=True)
    connection = connect_writable(db_path)
    try:
        now = "2026-10-13T00:00:00Z"
        for index in range(10, 25):
            connection.execute(
                """INSERT INTO catalog_printings
                   (tcgdex_id,set_id,local_id,category,stage,discovered_at,updated_at,
                    brief_source_url,brief_retrieved_at)
                   VALUES(?,'syn',?,'pokemon','Basic',?,?,
                          'https://api.tcgdex.net/v2/en/cards',?)""",
                (f"syn-{index}", str(index), now, now, now),
            )
            connection.execute(
                """INSERT INTO catalog_translations
                   (printing_id,language,status,name,category,source_url,retrieved_at)
                   VALUES(?,'en','present',?,'pokemon',?,?)""",
                (f"syn-{index}", f"Basic {index}", f"https://api.tcgdex.net/v2/en/cards/syn-{index}", now),
            )
        connection.commit()
        pokemon_only = [
            {"card_type": "pokemon", "quantity": 4, "card_name": f"Basic {index}",
             "set_code": "SYN", "collector_number": str(index)}
            for index in range(10, 25)
        ]
        status, validation, _ = _validate_candidate(
            connection, pokemon_only, format="standard", platform="live", as_of="2026-10-13"
        )
        assert status != "REJECTED_STRUCTURE"
        assert "CANDIDATE_SECTION_EMPTY" not in validation["reason_codes"]

        no_trainer = [
            {"card_type": "pokemon", "quantity": 4, "card_name": "Alpha", "set_code": "SYN", "collector_number": "1"},
            {"card_type": "energy", "quantity": 56, "card_name": "Basic Energy", "set_code": "SYN", "collector_number": "3"},
        ]
        status, validation, _ = _validate_candidate(
            connection, no_trainer, format="standard", platform="live", as_of="2026-10-13"
        )
        assert status != "REJECTED_STRUCTURE"
        assert "CANDIDATE_SECTION_EMPTY" not in validation["reason_codes"]
    finally:
        connection.close()


def test_candidate_rejects_proven_category_mismatch_and_abstains_when_unknown(local_tmp: Path) -> None:
    db_path = local_tmp / "category.sqlite3"
    _ready_db(db_path)
    mismatch = create_candidate(
        db_path,
        _changes(local_tmp / "mismatch.json", [_remove("Support", "2", 1), _add("trainer", "Beta", "4", 1)]),
    )
    assert mismatch["status"] == "REJECTED_STRUCTURE"
    assert "CANDIDATE_CATEGORY_MISMATCH" in mismatch["validation"]["reason_codes"]
    check = next(row for row in mismatch["validation"]["checks"]["category_checks"] if row["card_name"] == "Beta")
    assert check["declared"] == "trainer" and check["public"] == "pokemon"
    assert check["source_url"].startswith("https://api.tcgdex.net/")

    connection = sqlite3.connect(db_path)
    connection.execute("UPDATE catalog_printings SET category=NULL WHERE tcgdex_id='syn-4'")
    connection.execute("UPDATE catalog_translations SET category=NULL WHERE printing_id='syn-4'")
    connection.commit()
    connection.close()
    unknown = create_candidate(
        db_path,
        _changes(local_tmp / "unknown-category.json", [_remove("Support", "2", 1), _add("pokemon", "Beta", "4", 1)]),
    )
    assert unknown["status"] == "UNKNOWN_LEGALITY"
    assert "CANDIDATE_CATEGORY_MISMATCH" not in unknown["validation"]["reason_codes"]
