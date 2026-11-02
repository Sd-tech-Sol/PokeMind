from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from pokemind.battle_logs import import_battle_log
from pokemind.database import SCHEMA_VERSION, database_status
from pokemind.decks import decode_deck_bytes, import_deck, parse_deck_export, show_deck


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "decks"
BATTLE_FIXTURES = ROOT / "tests" / "fixtures" / "battle_logs"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["POKEMIND_ROOT"] = str(ROOT)
    return environment


@pytest.mark.parametrize("name", ["valid_en.txt", "valid_fr.txt", "valid_old.txt"])
def test_parser_accepts_confirmed_en_fr_and_legacy_shapes(name: str) -> None:
    parsed = parse_deck_export(_fixture(name))
    assert parsed.total_cards == 60
    assert sum(parsed.section_counts.values()) == 60
    assert parsed.coverage["entries_with_printing"] == len(parsed.cards)


@pytest.mark.parametrize(
    "text, message",
    [
        (
            _fixture("valid_en.txt").replace("Energy: 12", "Energy: 11").replace(
                "7 Basic Lightning", "6 Basic Lightning"
            ),
            "Total final incohérent",
        ),
        (
            _fixture("valid_en.txt").replace("Energy: 12", "Energy: 13").replace(
                "7 Basic Lightning", "8 Basic Lightning"
            ),
            "Total final incohérent",
        ),
        (_fixture("valid_en.txt").replace("4 Research Notes SYN 101", "Research Notes"), "malformée"),
        (_fixture("valid_en.txt").replace("Trainer: 36", "Section inconnue: 36"), "section non reconnue"),
    ],
)
def test_parser_rejects_59_61_and_malformed_exports(text: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        parse_deck_export(text)


def test_unicode_and_windows_encodings_are_supported() -> None:
    text = _fixture("valid_fr.txt")
    decoded, encoding = decode_deck_bytes(text.encode("cp1252"))
    assert decoded == text
    assert encoding == "cp1252"
    assert "Créature Éclair" in {card.name for card in parse_deck_export(decoded).cards}


def test_import_is_idempotent_and_new_list_creates_immutable_version(local_tmp: Path) -> None:
    db_path = local_tmp / "decks.sqlite3"
    first = import_deck(db_path, _fixture("valid_en.txt"), deck_id="principal", source_kind="stdin")
    same_cards_new_order = _fixture("valid_en.txt").replace(
        "4 Creature Alpha SYN 001\n3 Creature Beta SYN 002",
        "3 Creature Beta SYN 002\n4 Creature Alpha SYN 001",
    )
    duplicate = import_deck(db_path, same_cards_new_order, deck_id="principal", source_kind="clipboard")
    changed = _fixture("valid_en.txt").replace("4 Creature Alpha SYN 001", "3 Creature Alpha SYN 001").replace(
        "3 Creature Gamma SYN 003", "4 Creature Gamma SYN 003"
    )
    second = import_deck(db_path, changed, deck_id="principal", source_kind="file", source_name="private.txt")

    assert (first["version"], first["duplicate"]) == (1, False)
    assert (duplicate["version"], duplicate["duplicate"]) == (1, True)
    assert (second["version"], second["duplicate"]) == (2, False)
    shown = show_deck(db_path, "principal")
    assert shown["version"] == 2
    assert shown["total_cards"] == 60
    assert shown["raw_stored"] is False
    assert shown["source"]["name"] == "private.txt"

    connection = sqlite3.connect(db_path)
    versions = connection.execute(
        "SELECT version_number, total_cards, raw_stored FROM deck_versions ORDER BY version_number"
    ).fetchall()
    cards = connection.execute(
        "SELECT card_name, set_code, collector_number FROM deck_version_cards "
        "WHERE card_name = 'Creature Beta' ORDER BY set_code"
    ).fetchall()
    connection.close()
    assert versions == [(1, 60, 0), (2, 60, 0)]
    assert {tuple(card) for card in cards} == {
        ("Creature Beta", "OLD", "099"),
        ("Creature Beta", "SYN", "002"),
    }


def test_migration_preserves_two_battles_and_does_not_backfill_version(local_tmp: Path) -> None:
    db_path = local_tmp / "migration.sqlite3"
    victory = (BATTLE_FIXTURES / "victory_en.txt").read_text(encoding="utf-8")
    defeat = (BATTLE_FIXTURES / "defeat_fr.txt").read_text(encoding="utf-8")
    first = import_battle_log(db_path, victory, source_kind="file", deck_id="principal")
    second = import_battle_log(db_path, defeat, source_kind="file", deck_id="principal")
    before = [(first["battle_id"], first["outcome"]), (second["battle_id"], second["outcome"])]

    imported = import_deck(db_path, _fixture("valid_fr.txt"), deck_id="principal", source_kind="stdin")

    connection = sqlite3.connect(db_path)
    after = connection.execute("SELECT id, outcome FROM battle_logs ORDER BY id").fetchall()
    links = connection.execute("SELECT COUNT(*) FROM battle_deck_versions").fetchone()[0]
    observed = connection.execute(
        "SELECT status FROM observed_decks WHERE deck_id = 'principal'"
    ).fetchone()[0]
    connection.close()
    assert after == before
    assert links == 0
    assert observed == "observé partiellement"
    assert imported["historical_battles_linked"] is False
    assert database_status(db_path)["schema_version"] == SCHEMA_VERSION


def test_observed_only_deck_stays_distinct_from_exact_deck(local_tmp: Path) -> None:
    db_path = local_tmp / "observed.sqlite3"
    victory = (BATTLE_FIXTURES / "victory_en.txt").read_text(encoding="utf-8")
    import_battle_log(db_path, victory, source_kind="stdin", deck_id="principal")
    shown = show_deck(db_path, "principal")
    assert shown["status"] == "observé partiellement"
    assert shown["exact_confirmed"] is False
    assert shown["total_cards"] is None


def test_cli_file_stdin_and_show_json(local_tmp: Path) -> None:
    db_path = local_tmp / "cli.sqlite3"
    fixture = FIXTURES / "valid_en.txt"
    file_import = subprocess.run(
        [
            sys.executable,
            "-m",
            "pokemind",
            "deck",
            "import",
            str(fixture),
            "--deck",
            "principal",
            "--db",
            str(db_path),
            "--json",
        ],
        cwd=ROOT,
        env=_environment(),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    assert file_import.returncode == 0, file_import.stderr
    assert json.loads(file_import.stdout)["total_cards"] == 60

    stdin_import = subprocess.run(
        [
            sys.executable,
            "-m",
            "pokemind",
            "deck",
            "import",
            "-",
            "--deck",
            "principal",
            "--db",
            str(db_path),
            "--json",
        ],
        cwd=ROOT,
        env=_environment(),
        input=_fixture("valid_en.txt"),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    assert stdin_import.returncode == 0, stdin_import.stderr
    assert json.loads(stdin_import.stdout)["duplicate"] is True

    shown = subprocess.run(
        [
            sys.executable,
            "-m",
            "pokemind",
            "deck",
            "show",
            "principal",
            "--db",
            str(db_path),
            "--json",
        ],
        cwd=ROOT,
        env=_environment(),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    assert shown.returncode == 0, shown.stderr
    payload = json.loads(shown.stdout)
    assert payload["exact_confirmed"] is True
    assert sum(card["quantity"] for card in payload["cards"]) == 60
