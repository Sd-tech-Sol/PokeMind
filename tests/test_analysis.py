from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

import pokemind.analysis as analysis_module
from pokemind.analysis import _battle_fact, analyze_deck
from pokemind.cli import _human_analysis, _print_json
from pokemind.decks import import_deck
from pokemind.rules import check_deck, default_registry_path, load_official_registry


ROOT = Path(__file__).resolve().parents[1]
DECK_FIXTURE = ROOT / "tests" / "fixtures" / "decks" / "valid_en.txt"


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["POKEMIND_ROOT"] = str(ROOT)
    return environment


def _ready_deck(path: Path, deck_id: str = "synthetic") -> Path:
    load_official_registry(path, default_registry_path(ROOT))
    import_deck(
        path,
        DECK_FIXTURE.read_text(encoding="utf-8"),
        deck_id=deck_id,
        source_kind="stdin",
    )
    connection = sqlite3.connect(path)
    connection.execute(
        """UPDATE deck_versions
           SET imported_at='2026-05-01T00:00:00Z',
               approved_at='2026-05-01T00:00:00Z',
               effective_from='2026-05-01T00:00:00Z'
           WHERE deck_id=?""",
        (deck_id,),
    )
    connection.commit()
    connection.close()
    return path


def _insert_battles(path: Path, deck_id: str, outcomes: list[str]) -> list[int]:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA ignore_check_constraints = ON")
    connection.execute(
        "INSERT OR IGNORE INTO observed_decks VALUES (?, 'observé partiellement', ?, ?)",
        (deck_id, "2026-05-01T00:00:00Z", "2026-05-05T00:00:00Z"),
    )
    ids: list[int] = []
    for index, outcome in enumerate(outcomes, start=1):
        cursor = connection.execute(
            """INSERT INTO battle_logs
               (source_sha256, imported_at, parser_version, source_kind, source_name,
                reference_player, opponent_name, outcome, winner, valid, deck_id,
                max_turn, recognized_events, warnings_json)
               VALUES (?, ?, 'synthetic', 'stdin', NULL, NULL, NULL, ?, NULL, 1, ?, 1, 1, '[]')""",
            (f"synthetic-sha-{index}", f"2026-05-{index:02d}T12:00:00Z", outcome, deck_id),
        )
        ids.append(int(cursor.lastrowid))
    connection.commit()
    connection.close()
    return ids


def _insert_catalog_ambiguity(path: Path) -> None:
    connection = sqlite3.connect(path)
    now = "2026-05-01T00:00:00Z"
    connection.execute(
        """INSERT INTO catalog_sets
           (tcgdex_id, name_en, tcg_online_code, discovered_at, updated_at)
           VALUES ('synthetic-set', 'Synthetic', 'SYN', ?, ?)""",
        (now, now),
    )
    for printing_id in ("synthetic-a", "synthetic-b"):
        connection.execute(
            """INSERT INTO catalog_printings
               (tcgdex_id, set_id, local_id, regulation_mark, discovered_at, updated_at,
                brief_source_url, brief_retrieved_at)
               VALUES (?, 'synthetic-set', '001', 'H', ?, ?,
                       'https://api.tcgdex.net/test', ?)""",
            (printing_id, now, now, now),
        )
        connection.execute(
            """INSERT INTO catalog_translations
               (printing_id, language, status, name, source_url, retrieved_at)
               VALUES (?, 'en', 'present', 'Creature Alpha',
                       'https://api.tcgdex.net/test', ?)""",
            (printing_id, now),
        )
    connection.commit()
    connection.close()


def _insert_meta(
    path: Path,
    *,
    publish_archetype: bool = True,
    live_before_fetched_at: str = "2026-05-02T00:00:00Z",
) -> None:
    connection = sqlite3.connect(path)
    for tournament_id, when, platform, online, fetched_at in (
        ("live-before", "2026-05-01T18:00:00Z", "PTCGL", 1, live_before_fetched_at),
        ("live-future", "2026-06-01T18:00:00Z", "PTCGL", 1, "2026-05-02T00:00:00Z"),
        ("tabletop-before", "2026-05-01T18:00:00Z", "TABLETOP", 0, "2026-05-02T00:00:00Z"),
    ):
        connection.execute(
            """INSERT INTO meta_tournaments
               (tournament_id, name, date_utc, game, format, platform, is_online,
                is_public, provider_status, participant_count, decklists_enabled,
                special_rules_json, banned_cards_count, source_url, fetched_at,
                payload_sha256, snapshot_status)
               VALUES (?, 'Synthetic event', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                tournament_id,
                when,
                "PTCG",
                "STANDARD",
                platform,
                online,
                1,
                "COMPLETED",
                2,
                1,
                "[]",
                0,
                "https://play.limitlesstcg.com/api/tournaments/synthetic/details",
                fetched_at,
                "public-hash",
                "complete",
            ),
        )
        first_archetype = "deck-a" if publish_archetype else None
        for participant, archetype in (("opaque-a", first_archetype), ("opaque-b", None)):
            connection.execute(
                """INSERT INTO meta_placements
                   (tournament_id, participant_ref, placing, wins, losses, ties,
                    dropped_round, archetype_id, archetype_name, archetype_published)
                   VALUES (?, ?, 1, 1, 0, 0, NULL, ?, NULL, ?)""",
                (tournament_id, participant, archetype, int(archetype is not None)),
            )
    connection.commit()
    connection.close()


def _insert_restricted_printing(path: Path) -> None:
    connection = sqlite3.connect(path)
    captured = "2026-01-01T00:00:00Z"
    connection.execute(
        """INSERT INTO catalog_sets
           (tcgdex_id, name_en, tcg_online_code, discovered_at, updated_at)
           VALUES ('synthetic-set', 'Synthetic', 'SYN', ?, ?)""",
        (captured, captured),
    )
    connection.execute(
        """INSERT INTO catalog_printings
           (tcgdex_id, set_id, local_id, regulation_mark, discovered_at, updated_at,
            brief_source_url, brief_retrieved_at)
           VALUES ('synthetic-banned', 'synthetic-set', '001', 'H', ?, ?,
                   'https://api.tcgdex.net/test', ?)""",
        (captured, captured, captured),
    )
    connection.execute(
        """INSERT INTO catalog_translations
           (printing_id, language, status, name, source_url, retrieved_at)
           VALUES ('synthetic-banned', 'en', 'present', 'Creature Alpha',
                   'https://api.tcgdex.net/test', ?)""",
        (captured,),
    )
    connection.execute(
        """INSERT INTO official_rule_sources
           (source_id, source_type, url, title, language, published_date,
            consulted_at, captured_at, content_sha256, validation_status,
            effective_from, effective_to, rights_note, notes)
           VALUES ('synthetic-restriction-source', 'web',
                   'https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources',
                   'Synthetic restriction', 'en', '2026-01-01', ?, ?,
                   'synthetic-public-hash', 'verified', '2026-01-01', NULL,
                   'Synthetic test fixture', NULL)""",
        (captured, captured),
    )
    connection.execute(
        """INSERT INTO official_rule_assertions
           (assertion_id, source_id, assertion_kind, format, platform,
            effective_from, effective_to, subject_id, payload_json,
            validation_status, confidence, captured_at)
           VALUES ('synthetic-restriction', 'synthetic-restriction-source',
                   'restriction', 'standard', 'live', '2026-01-01', NULL,
                   'synthetic-banned', '{}', 'verified', 'high', ?)""",
        (captured,),
    )
    connection.commit()
    connection.close()


def test_missing_database_is_controlled_and_not_created(local_tmp: Path) -> None:
    db_path = local_tmp / "missing.sqlite3"
    result = analyze_deck(db_path, "synthetic", as_of="2026-05-01")
    assert result["read_only"] is True and result["network_used"] is False
    assert result["assessment"] == "données insuffisantes"
    assert {item["code"] for item in result["unknowns"]} == {"DATABASE_MISSING"}
    assert not db_path.exists()


def test_absent_deck_returns_useful_unknowns_without_migration(local_tmp: Path) -> None:
    db_path = _ready_deck(local_tmp / "absent.sqlite3", "another-deck")
    before = db_path.read_bytes()
    result = analyze_deck(db_path, "missing-deck", as_of="2026-05-01")
    assert result["facts"]["deck"] == {"found": False}
    assert "DECK_NOT_FOUND" in {item["code"] for item in result["unknowns"]}
    assert db_path.read_bytes() == before


def test_latest_unconfirmed_version_is_not_replaced_by_previous_exact(local_tmp: Path) -> None:
    db_path = _ready_deck(local_tmp / "latest.sqlite3")
    changed = DECK_FIXTURE.read_text(encoding="utf-8").replace(
        "4 Creature Alpha SYN 001", "3 Creature Alpha SYN 001"
    ).replace("3 Creature Gamma SYN 003", "4 Creature Gamma SYN 003")
    import_deck(db_path, changed, deck_id="synthetic", source_kind="stdin")
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA ignore_check_constraints = ON")
    connection.execute(
        "UPDATE deck_versions SET exact_confirmed=0 WHERE deck_id='synthetic' AND version_number=2"
    )
    connection.commit()
    connection.close()

    result = analyze_deck(db_path, "synthetic", as_of="2026-12-31")

    assert result["facts"]["deck"]["version"] == 2
    assert result["facts"]["deck"]["exact_confirmed"] is False
    assert "DECK_VERSION_UNCONFIRMED" in {item["code"] for item in result["unknowns"]}


def test_invalid_quantities_and_ambiguous_printing_stay_unknown(local_tmp: Path) -> None:
    db_path = _ready_deck(local_tmp / "invalid.sqlite3")
    _insert_catalog_ambiguity(db_path)
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA ignore_check_constraints = ON")
    version_id = connection.execute(
        "SELECT id FROM deck_versions WHERE deck_id='synthetic'"
    ).fetchone()[0]
    connection.execute("UPDATE deck_versions SET total_cards=59 WHERE id=?", (version_id,))
    connection.commit()
    connection.close()

    result = analyze_deck(db_path, "synthetic", as_of="2026-05-01")

    assert result["facts"]["deck"]["recorded_total"] == 59
    assert result["facts"]["deck"]["quantity_sum"] == 60
    assert result["facts"]["catalog"]["entry_resolution"]["ambiguous"] == 1
    assert result["facts"]["rules"]["status"] == "unknown"
    assert "DECK_STRUCTURE_NOT_VERIFIED" in result["facts"]["rules"]["reason_codes"]
    codes = {item["code"] for item in result["unknowns"]}
    assert {"DECK_QUANTITY_INVALID", "PRINTINGS_AMBIGUOUS", "PRINTINGS_UNRESOLVED"} <= codes


def test_five_battles_are_not_attributed_without_explicit_version_link(local_tmp: Path) -> None:
    db_path = _ready_deck(local_tmp / "battles.sqlite3")
    battle_ids = _insert_battles(db_path, "synthetic", ["W", "W", "W", "W", "L"])
    connection = sqlite3.connect(db_path)
    version_id = connection.execute(
        "SELECT id FROM deck_versions WHERE deck_id='synthetic'"
    ).fetchone()[0]
    connection.execute(
        "INSERT INTO battle_deck_versions VALUES (?, ?, '2026-05-01', '2026-05-01')",
        (battle_ids[0], version_id),
    )
    connection.commit()
    connection.close()

    result = analyze_deck(db_path, "synthetic", as_of="2026-05-31")
    battles = result["facts"]["battles"]

    assert battles["valid_unique"] == 5
    assert battles["outcomes"] == {"wins": 4, "losses": 1, "draws": 0, "ambiguous": 0}
    assert battles["with_selected_version_proven"] == 1
    assert battles["with_deck_identity_recorded"] == 5
    assert battles["rate_or_matchup_claim"] is None
    assert all("sha" not in json.dumps(item).casefold() for item in battles["observations"])
    assert any("taux de victoire" in warning for warning in result["warnings"])


def test_duplicate_draw_ambiguous_and_other_version_are_separated() -> None:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE battle_logs(id INTEGER, source_sha256 TEXT, imported_at TEXT,
            outcome TEXT, valid INTEGER, deck_id TEXT);
        CREATE TABLE deck_versions(id INTEGER, version_number INTEGER);
        CREATE TABLE battle_deck_versions(battle_id INTEGER, deck_version_id INTEGER);
        INSERT INTO deck_versions VALUES(10, 1), (20, 2);
        INSERT INTO battle_logs VALUES
            (1, 'same', '2026-05-01T00:00:00Z', 'W', 1, 'synthetic'),
            (2, 'same', '2026-05-01T00:00:00Z', 'L', 1, 'synthetic'),
            (3, 'draw', '2026-05-02T00:00:00Z', 'draw', 1, 'synthetic'),
            (4, 'ambiguous', '2026-05-03T00:00:00Z', 'inconnue', 1, 'synthetic');
        INSERT INTO battle_deck_versions VALUES(1, 10), (3, 20);
        """
    )
    result = _battle_fact(connection, "synthetic", 10, "2026-05-31")
    connection.close()
    assert result["valid_unique"] == 3 and result["duplicates_excluded"] == 1
    assert result["outcomes"] == {"wins": 1, "losses": 0, "draws": 1, "ambiguous": 1}
    assert result["with_selected_version_proven"] == 1
    assert result["with_any_version_proven"] == 2


def test_as_of_and_live_vs_in_person_meta_context_are_strict(local_tmp: Path) -> None:
    db_path = _ready_deck(local_tmp / "meta.sqlite3")
    _insert_meta(db_path)
    live = analyze_deck(
        db_path, "synthetic", as_of="2026-05-15", format="standard", platform="live"
    )
    tabletop = analyze_deck(
        db_path, "synthetic", as_of="2026-05-15", format="standard", platform="in_person"
    )
    assert live["facts"]["metagame"]["n_tournaments"] == 1
    assert live["facts"]["metagame"]["filters"]["platform"] == "PTCGL"
    assert tabletop["facts"]["metagame"]["n_tournaments"] == 1
    assert tabletop["facts"]["metagame"]["filters"]["platform"] == "TABLETOP"
    with pytest.raises(ValueError, match="ISO stricte"):
        analyze_deck(db_path, "synthetic", as_of="2026-5-1")


def test_as_of_excludes_snapshot_captured_after_requested_date(local_tmp: Path) -> None:
    db_path = _ready_deck(local_tmp / "late-snapshot.sqlite3")
    _insert_meta(db_path, live_before_fetched_at="2026-06-01T00:00:00Z")

    historical = analyze_deck(db_path, "synthetic", as_of="2026-05-15")
    later = analyze_deck(db_path, "synthetic", as_of="2026-06-02")

    meta = historical["facts"]["metagame"]
    assert meta["n_tournaments"] == 0
    assert meta["snapshot_availability"] == "not_available_as_of"
    assert meta["excluded"] == {
        "event_after_as_of": 1,
        "snapshot_captured_after_as_of": 1,
        "invalid_event_or_capture_date": 0,
    }
    assert meta["filters"]["event_through"] == "2026-05-15"
    assert meta["filters"]["evidence_captured_through"] == "2026-05-15"
    assert "SNAPSHOT_NOT_AVAILABLE_AS_OF" in {
        item["code"] for item in historical["unknowns"]
    }
    assert not any(
        item["source"] == "Limitless (cache local)" for item in historical["evidence"]
    )
    assert later["facts"]["metagame"]["n_tournaments"] == 2
    assert later["facts"]["metagame"]["last_fetched_at"] == "2026-06-01T00:00:00Z"


def test_future_deck_version_has_no_historical_rules_or_battle_attribution(
    local_tmp: Path,
) -> None:
    db_path = _ready_deck(local_tmp / "future-version.sqlite3")
    _insert_restricted_printing(db_path)
    battle_id = _insert_battles(db_path, "synthetic", ["W"])[0]
    connection = sqlite3.connect(db_path)
    version_id = int(
        connection.execute(
            "SELECT id FROM deck_versions WHERE deck_id='synthetic'"
        ).fetchone()[0]
    )
    connection.execute(
        """UPDATE deck_versions
           SET imported_at='2026-06-01T00:00:00Z',
               approved_at='2026-06-01T00:00:00Z',
               effective_from='2026-06-01T00:00:00Z'
           WHERE id=?""",
        (version_id,),
    )
    connection.execute(
        "INSERT INTO battle_deck_versions VALUES (?, ?, '2026-06-01', '2026-06-01')",
        (battle_id, version_id),
    )
    connection.commit()
    connection.close()

    assert check_deck(
        db_path,
        "synthetic",
        format="standard",
        platform="live",
        as_of="2026-05-15",
    )["status"] == "not_legal"

    historical = analyze_deck(db_path, "synthetic", as_of="2026-05-15")

    assert historical["facts"]["deck"]["historical_applicability"] == "not_applicable"
    assert historical["facts"]["rules"]["status"] == "unknown"
    assert historical["facts"]["rules"]["historical_applicability"] == "not_applicable"
    assert historical["facts"]["rules"]["reason_codes"] == [
        "LATEST_VERSION_OUTSIDE_AS_OF"
    ]
    assert historical["facts"]["rules"]["card_statuses"]["not_legal"] == 0
    assert historical["facts"]["battles"]["with_selected_version_proven"] == 0
    assert historical["facts"]["battles"]["observations"][0]["version_evidence"] == (
        "legacy_selected_version_not_applicable"
    )
    assert "LATEST_VERSION_OUTSIDE_AS_OF" in {
        item["code"] for item in historical["unknowns"]
    }


def test_one_tournament_without_published_archetype_has_no_matchup(local_tmp: Path) -> None:
    db_path = _ready_deck(local_tmp / "zero-archetype.sqlite3")
    _insert_meta(db_path, publish_archetype=False)
    result = analyze_deck(db_path, "synthetic", as_of="2026-05-15")
    meta = result["facts"]["metagame"]
    assert meta["n_tournaments"] == 1
    assert meta["n_published_archetypes"] == 0
    assert meta["n_exploitable_matches"] == 0
    assert meta["matchup_statistics"] is None
    assert "META_ARCHETYPE_ABSENT" in {item["code"] for item in result["unknowns"]}


@pytest.mark.parametrize(
    ("target", "expected_code"),
    (("_catalog_fact", "CATALOG_UNAVAILABLE"), ("_rules_fact", "RULES_UNAVAILABLE")),
)
def test_technical_errors_are_redacted_in_json_and_human_output(
    local_tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    target: str,
    expected_code: str,
) -> None:
    db_path = _ready_deck(local_tmp / f"redaction-{target}.sqlite3")
    secret = r"C:\Users\PrivateName\private.sqlite3 secret-token=synthetic-secret Creature Private"

    def fail_with_private_text(*args: object, **kwargs: object) -> None:
        raise sqlite3.DatabaseError(secret)

    monkeypatch.setattr(analysis_module, target, fail_with_private_text)
    result = analyze_deck(db_path, "synthetic", as_of="2026-05-15")

    _print_json(result)
    _human_analysis(result)
    rendered = capsys.readouterr().out
    serialized = json.dumps(result, ensure_ascii=False)
    for private_fragment in (
        secret,
        "PrivateName",
        "secret-token",
        "synthetic-secret",
        "Creature Private",
    ):
        assert private_fragment not in serialized
        assert private_fragment not in rendered
    assert expected_code in {item["code"] for item in result["unknowns"]}


def test_command_is_byte_for_byte_read_only_offline_and_redacted(local_tmp: Path) -> None:
    db_path = _ready_deck(local_tmp / "readonly.sqlite3")
    _insert_battles(db_path, "synthetic", ["W"])
    before = hashlib.sha256(db_path.read_bytes()).hexdigest()
    completed = subprocess.run(
        [
            sys.executable, "-m", "pokemind", "analyze", "deck", "synthetic",
            "--as-of", "2026-05-31", "--format", "expanded", "--platform", "live",
            "--db", str(db_path), "--json",
        ],
        cwd=ROOT,
        env=_environment(),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    after = hashlib.sha256(db_path.read_bytes()).hexdigest()
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    serialized = json.dumps(payload, ensure_ascii=False)
    assert before == after
    assert payload["read_only"] is True and payload["network_used"] is False
    assert str(local_tmp) not in serialized and str(db_path) not in serialized
    assert "synthetic-sha" not in serialized
    assert '"card_name":' not in serialized and '"source_sha256":' not in serialized
    assert payload["context"]["format"] == "expanded"


def test_human_and_json_outputs_are_coherent(local_tmp: Path) -> None:
    db_path = _ready_deck(local_tmp / "cli.sqlite3")
    base = [
        sys.executable, "-m", "pokemind", "analyze", "deck", "synthetic",
        "--as-of", "2026-05-01", "--db", str(db_path),
    ]
    human = subprocess.run(base, cwd=ROOT, env=_environment(), text=True, encoding="utf-8", capture_output=True)
    machine = subprocess.run([*base, "--json"], cwd=ROOT, env=_environment(), text=True, encoding="utf-8", capture_output=True)
    assert human.returncode == machine.returncode == 0
    payload = json.loads(machine.stdout)
    assert "données insuffisantes" in human.stdout
    assert f"version {payload['facts']['deck']['version']}" in human.stdout
    assert "Règles: unknown" in human.stdout
