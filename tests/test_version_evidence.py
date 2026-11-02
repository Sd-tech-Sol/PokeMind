from __future__ import annotations

import hashlib
import json
import os
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

import pokemind.version_evidence as version_module
from pokemind.cli import _human_deck_compare, _human_version_evidence
from pokemind.decks import import_deck
from pokemind.version_evidence import compare_deck_versions, version_evidence


ROOT = Path(__file__).resolve().parents[1]
DECK = (ROOT / "tests" / "fixtures" / "decks" / "valid_en.txt").read_text(
    encoding="utf-8"
)


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["POKEMIND_ROOT"] = str(ROOT)
    return environment


def _set_version_dates(path: Path, deck_id: str = "synthetic") -> None:
    connection = sqlite3.connect(path)
    connection.execute(
        """UPDATE deck_versions SET
               imported_at='2026-05-01T00:00:00Z',
               approved_at='2026-05-01T00:00:00Z',
               effective_from='2026-05-01T00:00:00Z'
           WHERE deck_id=?""",
        (deck_id,),
    )
    connection.commit()
    connection.close()


def _one_version(path: Path, deck_id: str = "synthetic") -> Path:
    import_deck(path, DECK, deck_id=deck_id, source_kind="stdin")
    _set_version_dates(path, deck_id)
    return path


def _two_versions(path: Path, deck_id: str = "synthetic") -> Path:
    _one_version(path, deck_id)
    changed = DECK.replace("4 Creature Alpha SYN 001", "3 Creature Alpha SYN 001").replace(
        "3 Creature Gamma SYN 003", "4 Creature Gamma SYN 003"
    )
    import_deck(path, changed, deck_id=deck_id, source_kind="stdin")
    _set_version_dates(path, deck_id)
    return path


def _insert_battles(path: Path, deck_id: str, outcomes: list[str]) -> list[int]:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(
        "INSERT OR IGNORE INTO observed_decks VALUES (?, 'observé partiellement', ?, ?)",
        (deck_id, "2026-05-01T00:00:00Z", "2026-05-20T00:00:00Z"),
    )
    ids: list[int] = []
    for index, outcome in enumerate(outcomes, start=1):
        cursor = connection.execute(
            """INSERT INTO battle_logs
               (source_sha256, imported_at, parser_version, source_kind, source_name,
                reference_player, opponent_name, outcome, winner, valid, deck_id,
                max_turn, recognized_events, warnings_json)
               VALUES (?, ?, 'synthetic', 'stdin', NULL, NULL, NULL, ?, NULL, 1, ?, 1, 1, '[]')""",
            (f"private-synthetic-digest-{index}", f"2026-05-{index + 1:02d}T12:00:00Z", outcome, deck_id),
        )
        battle_id = int(cursor.lastrowid)
        ids.append(battle_id)
        connection.execute(
            """INSERT INTO battle_events
               (battle_id, sequence, turn_number, actor, actor_role, event_type,
                card_name, evidence, confidence)
               VALUES (?, 1, 1, NULL, 'unknown', 'draw', NULL, 'synthetic', 'low')""",
            (battle_id,),
        )
    connection.commit()
    connection.close()
    return ids


def _link(path: Path, battle_id: int, deck_id: str, version: int) -> None:
    connection = sqlite3.connect(path)
    row = connection.execute(
        """SELECT id, effective_from, approved_at FROM deck_versions
           WHERE deck_id=? AND version_number=?""",
        (deck_id, version),
    ).fetchone()
    assert row is not None
    connection.execute(
        "INSERT INTO battle_deck_versions VALUES (?, ?, ?, ?)",
        (battle_id, row[0], row[1], row[2]),
    )
    connection.commit()
    connection.close()


def test_single_version_refuses_to_invent_comparison(local_tmp: Path) -> None:
    db_path = _one_version(local_tmp / "one.sqlite3")
    before = db_path.read_bytes()

    result = compare_deck_versions(
        db_path, "synthetic", from_version=1, to_version=2
    )

    assert result["comparison_status"] == "INSUFFICIENT_DECK_VERSIONS"
    assert result["facts"]["available_versions"] == 1
    assert result["read_only"] is True and result["network_used"] is False
    assert db_path.read_bytes() == before


def test_two_versions_compare_aggregates_without_private_cards(local_tmp: Path) -> None:
    db_path = _two_versions(local_tmp / "compare.sqlite3")

    result = compare_deck_versions(
        db_path,
        "synthetic",
        from_version=1,
        to_version=2,
        as_of="2026-05-31",
    )

    changes = result["facts"]["changes"]
    serialized = json.dumps(result, ensure_ascii=False)
    assert result["comparison_status"] == "COMPARISON_AVAILABLE"
    assert changes == {
        "impressions_added": 0,
        "impressions_removed": 0,
        "impressions_with_quantity_changed": 2,
        "quantity_increased": 1,
        "quantity_decreased": 1,
        "delta_total": 0,
        "changed_impressions": 2,
        "identity_uncertain_changes": 0,
        "details_included": False,
    }
    assert "Creature Alpha" not in serialized and "Creature Gamma" not in serialized
    assert result["facts"]["from"]["cards"]["total"] == 60
    assert result["facts"]["to"]["sections"] == {"present": 3, "denominator": 3}


def test_show_changes_is_explicit_and_distinguishes_same_name_printings(
    local_tmp: Path,
) -> None:
    db_path = _one_version(local_tmp / "printings.sqlite3")
    changed = DECK.replace("3 Creature Beta SYN 002", "2 Creature Beta SYN 002").replace(
        "2 Creature Beta OLD 099", "3 Creature Beta OLD 099"
    )
    import_deck(db_path, changed, deck_id="synthetic", source_kind="stdin")
    _set_version_dates(db_path)

    result = compare_deck_versions(
        db_path,
        "synthetic",
        from_version=1,
        to_version=2,
        show_changes=True,
    )

    details = result["facts"]["changes"]["details"]
    assert len(details) == 2
    assert {(item["set_code"], item["collector_number"]) for item in details} == {
        ("SYN", "002"),
        ("OLD", "099"),
    }
    assert all(item["card_name"] == "Creature Beta" for item in details)
    assert any("PRIVÉ" in warning for warning in result["warnings"])


def test_missing_printing_identifiers_stay_uncertain(local_tmp: Path) -> None:
    db_path = _one_version(local_tmp / "uncertain.sqlite3")
    changed = DECK.replace("4 Creature Alpha SYN 001", "3 Creature Alpha").replace(
        "3 Creature Gamma SYN 003", "4 Creature Gamma SYN 003"
    )
    import_deck(db_path, changed, deck_id="synthetic", source_kind="stdin")
    _set_version_dates(db_path)

    result = compare_deck_versions(
        db_path, "synthetic", from_version=1, to_version=2, show_changes=True
    )

    assert result["identity_limits"]["missing_set_or_number"] == 1
    assert result["facts"]["changes"]["identity_uncertain_changes"] == 1
    assert "IDENTITY_UNCERTAIN" in {item["code"] for item in result["unknowns"]}


def test_reordered_rows_compare_with_zero_difference(local_tmp: Path) -> None:
    db_path = _one_version(local_tmp / "reordered.sqlite3")
    connection = sqlite3.connect(db_path)
    source = connection.execute(
        "SELECT * FROM deck_versions WHERE deck_id='synthetic' AND version_number=1"
    ).fetchone()
    assert source is not None
    columns = [row[1] for row in connection.execute("PRAGMA table_info(deck_versions)")]
    values = dict(zip(columns, source))
    source_id = int(values["id"])
    values.update(
        id=None,
        version_number=2,
        export_sha256="synthetic-reordered-export",
        list_sha256="synthetic-reordered-list",
    )
    insert_columns = [column for column in columns if column != "id"]
    cursor = connection.execute(
        f"INSERT INTO deck_versions ({','.join(insert_columns)}) VALUES ({','.join('?' for _ in insert_columns)})",
        [values[column] for column in insert_columns],
    )
    second_id = int(cursor.lastrowid)
    cards = connection.execute(
        "SELECT * FROM deck_version_cards WHERE deck_version_id=? ORDER BY ordinal DESC",
        (source_id,),
    ).fetchall()
    card_columns = [row[1] for row in connection.execute("PRAGMA table_info(deck_version_cards)")]
    for ordinal, card in enumerate(cards, start=1):
        item = dict(zip(card_columns, card))
        connection.execute(
            """INSERT INTO deck_version_cards
               (deck_version_id, ordinal, source_line, card_type, quantity, card_name,
                set_code, collector_number, normalized_line)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                second_id,
                ordinal,
                ordinal,
                item["card_type"],
                item["quantity"],
                item["card_name"],
                item["set_code"],
                item["collector_number"],
                item["normalized_line"],
            ),
        )
    connection.commit()
    connection.close()

    result = compare_deck_versions(
        db_path, "synthetic", from_version=1, to_version=2
    )
    assert result["facts"]["changes"]["changed_impressions"] == 0
    assert result["facts"]["changes"]["delta_total"] == 0


@pytest.mark.parametrize(
    "mutation",
    [
        "UPDATE deck_versions SET exact_confirmed=0 WHERE version_number=2",
        "UPDATE deck_versions SET total_cards=59 WHERE version_number=2",
        "UPDATE deck_version_cards SET quantity=-1 WHERE deck_version_id=(SELECT id FROM deck_versions WHERE version_number=2) AND ordinal=1",
    ],
)
def test_invalid_or_unconfirmed_version_is_refused(local_tmp: Path, mutation: str) -> None:
    db_path = _two_versions(local_tmp / "invalid.sqlite3")
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA ignore_check_constraints = ON")
    connection.execute(mutation)
    connection.commit()
    connection.close()
    result = compare_deck_versions(
        db_path, "synthetic", from_version=1, to_version=2
    )
    assert result["comparison_status"] == "INVALID_DECK_VERSION"


def test_foreign_or_missing_version_is_not_substituted(local_tmp: Path) -> None:
    db_path = _two_versions(local_tmp / "foreign.sqlite3")
    _one_version(db_path, "other-deck")
    result = compare_deck_versions(
        db_path, "synthetic", from_version=1, to_version=3
    )
    assert result["comparison_status"] == "VERSION_NOT_FOUND"


def test_five_unlinked_battles_attribute_zero_wins_to_version(local_tmp: Path) -> None:
    db_path = _one_version(local_tmp / "unlinked.sqlite3")
    _insert_battles(db_path, "synthetic", ["W", "W", "W", "W", "L"])

    result = version_evidence(db_path, "synthetic", as_of="2026-05-31")

    battles = result["facts"]["battles"]
    assert battles["valid_unique_declared_deck"] == 5
    assert battles["unlinked"] == 5
    assert battles["proven_same_deck_links"] == 0
    assert result["facts"]["versions"][0]["outcomes"]["wins"] == 0
    assert result["facts"]["performance_comparison"]["rates"] is None
    serialized = json.dumps(result, ensure_ascii=False)
    assert "private-synthetic-digest" not in serialized


def test_one_explicit_link_attributes_only_one_battle(local_tmp: Path) -> None:
    db_path = _one_version(local_tmp / "linked.sqlite3")
    battles = _insert_battles(db_path, "synthetic", ["W", "W", "L"])
    _link(db_path, battles[0], "synthetic", 1)

    result = version_evidence(db_path, "synthetic", as_of="2026-05-31")

    counts = result["facts"]["battles"]
    assert counts["proven_same_deck_links"] == 1
    assert counts["unlinked"] == 2
    assert result["facts"]["versions"][0]["linked_battles"] == 1
    assert result["facts"]["versions"][0]["outcomes"]["wins"] == 1


def test_foreign_link_and_temporal_doubt_are_not_proven(local_tmp: Path) -> None:
    db_path = _one_version(local_tmp / "conflicts.sqlite3")
    _one_version(db_path, "other-deck")
    battles = _insert_battles(db_path, "synthetic", ["W", "L"])
    _link(db_path, battles[0], "other-deck", 1)
    connection = sqlite3.connect(db_path)
    own = connection.execute(
        "SELECT id FROM deck_versions WHERE deck_id='synthetic' AND version_number=1"
    ).fetchone()[0]
    connection.execute(
        """UPDATE deck_versions SET effective_from='2026-06-01T00:00:00Z',
               approved_at='2026-06-01T00:00:00Z' WHERE id=?""",
        (own,),
    )
    connection.execute(
        "INSERT INTO battle_deck_versions VALUES (?, ?, ?, ?)",
        (battles[1], own, "2026-06-01T00:00:00Z", "2026-06-01T00:00:00Z"),
    )
    connection.commit()
    connection.close()

    result = version_evidence(db_path, "synthetic", as_of="2026-06-30")

    counts = result["facts"]["battles"]
    assert counts["conflicting_links"] == 1
    assert counts["temporal_doubts"] == 1
    assert counts["proven_same_deck_links"] == 0
    assert {item["reason"] for item in result["confirmations"]} == {
        "LINKED_VERSION_OTHER_DECK",
        "TEMPORAL_COMPATIBILITY_UNCERTAIN",
    }


def test_link_approved_after_as_of_is_not_available_historically(local_tmp: Path) -> None:
    db_path = _one_version(local_tmp / "late-link.sqlite3")
    battle_id = _insert_battles(db_path, "synthetic", ["W"])[0]
    connection = sqlite3.connect(db_path)
    connection.execute(
        "UPDATE deck_versions SET approved_at='2026-06-01T00:00:00Z' WHERE deck_id='synthetic'"
    )
    connection.commit()
    connection.close()
    _link(db_path, battle_id, "synthetic", 1)

    historical = version_evidence(db_path, "synthetic", as_of="2026-05-31")
    later = version_evidence(db_path, "synthetic", as_of="2026-06-02")

    assert historical["facts"]["battles"]["proven_same_deck_links"] == 0
    assert historical["facts"]["battles"]["temporal_doubts"] == 1
    assert later["facts"]["battles"]["proven_same_deck_links"] == 1


def test_duplicate_and_future_battles_are_counted_conservatively(local_tmp: Path) -> None:
    db_path = local_tmp / "legacy.sqlite3"
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        PRAGMA user_version=7;
        CREATE TABLE deck_versions(id INTEGER, deck_id TEXT, version_number INTEGER,
          exact_confirmed INTEGER, total_cards INTEGER, effective_from TEXT, approved_at TEXT);
        CREATE TABLE deck_version_cards(deck_version_id INTEGER, quantity INTEGER);
        CREATE TABLE battle_logs(id INTEGER, source_sha256 TEXT, imported_at TEXT,
          outcome TEXT, valid INTEGER, deck_id TEXT, recognized_events INTEGER);
        CREATE TABLE battle_deck_versions(battle_id INTEGER, deck_version_id INTEGER,
          effective_from TEXT, approved_at TEXT);
        CREATE TABLE battle_events(id INTEGER, battle_id INTEGER);
        INSERT INTO deck_versions VALUES(1, 'synthetic', 1, 1, 60, '2026-05-01', '2026-05-01');
        INSERT INTO deck_version_cards VALUES(1, 60);
        INSERT INTO battle_logs VALUES
          (1, 'same-private-digest', '2026-05-02', 'W', 1, 'synthetic', 0),
          (2, 'same-private-digest', '2026-05-03', 'L', 1, 'synthetic', 0),
          (3, 'future-private-digest', '2026-07-01', 'W', 1, 'synthetic', 0);
        """
    )
    connection.commit()
    connection.close()

    result = version_evidence(db_path, "synthetic", as_of="2026-05-31")
    counts = result["facts"]["battles"]
    assert counts["valid_unique_declared_deck"] == 1
    assert counts["duplicates_excluded"] == 1
    assert counts["excluded_after_as_of"] == 1
    assert "private-digest" not in json.dumps(result)


def test_database_errors_are_redacted(local_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = local_tmp / "present.sqlite3"
    db_path.write_bytes(b"synthetic")
    secret = r"C:\Users\Private\deck.sqlite3 token=private-card"

    def fail(_: Path) -> sqlite3.Connection:
        raise sqlite3.DatabaseError(secret)

    monkeypatch.setattr(version_module, "connect_readonly", fail)
    comparison = compare_deck_versions(
        db_path, "synthetic", from_version=1, to_version=2
    )
    evidence = version_evidence(db_path, "synthetic", as_of="2026-05-31")
    rendered = json.dumps([comparison, evidence], ensure_ascii=False)
    assert secret not in rendered and "private-card" not in rendered
    assert comparison["comparison_status"] == "DATABASE_UNAVAILABLE"
    assert evidence["evidence_status"] == "DATABASE_UNAVAILABLE"


def test_functions_use_no_network(local_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    db_path = _two_versions(local_tmp / "offline.sqlite3")

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket, "socket", forbidden)
    assert compare_deck_versions(
        db_path, "synthetic", from_version=1, to_version=2
    )["network_used"] is False
    assert version_evidence(db_path, "synthetic", as_of="2026-05-31")[
        "network_used"
    ] is False


def test_cli_json_human_and_database_bytes_are_coherent(local_tmp: Path) -> None:
    db_path = _two_versions(local_tmp / "cli.sqlite3")
    battles = _insert_battles(db_path, "synthetic", ["W"])
    _link(db_path, battles[0], "synthetic", 1)
    before = hashlib.sha256(db_path.read_bytes()).hexdigest()
    commands = (
        [
            "deck",
            "compare",
            "synthetic",
            "--from-version",
            "1",
            "--to-version",
            "2",
        ],
        ["deck", "version-evidence", "synthetic", "--as-of", "2026-05-31"],
    )
    for command in commands:
        base = [sys.executable, "-m", "pokemind", *command, "--db", str(db_path)]
        human = subprocess.run(
            base,
            cwd=ROOT,
            env=_environment(),
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        machine = subprocess.run(
            [*base, "--json"],
            cwd=ROOT,
            env=_environment(),
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        assert human.returncode == machine.returncode == 0, machine.stderr
        payload = json.loads(machine.stdout)
        assert payload["read_only"] is True and payload["network_used"] is False
        assert "lecture seule, hors ligne" in human.stdout
    after = hashlib.sha256(db_path.read_bytes()).hexdigest()
    assert before == after


def test_human_renderers_do_not_require_private_fields(
    local_tmp: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    db_path = _two_versions(local_tmp / "human.sqlite3")
    comparison = compare_deck_versions(
        db_path, "synthetic", from_version=1, to_version=2
    )
    evidence = version_evidence(db_path, "synthetic", as_of="2026-05-31")
    _human_deck_compare(comparison)
    _human_version_evidence(evidence)
    rendered = capsys.readouterr().out
    assert "Creature" not in rendered
    assert "COMPARISON_AVAILABLE" in rendered
    assert "EVIDENCE_AUDIT_AVAILABLE" in rendered
