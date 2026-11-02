from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import pytest

import pokemind.battle_logs as battle_logs
from pokemind.battle_logs import MAX_LOG_BYTES, decode_log_bytes, import_battle_log, parse_battle_log
from pokemind.database import SCHEMA_VERSION, database_status, initialize_schema


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "battle_logs"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _synthetic(number: int, outcome: str = "JoueurA") -> str:
    return (
        "Setup\nReference player: JoueurA\n"
        f"JoueurA played Ralts {number} to the Active Spot.\n"
        "Turn # 1 - JoueurA's Turn\n"
        "JoueurA drew Iono.\nJoueurA played Iono.\n"
        f"All Prize cards taken. {outcome} wins.\n"
    )


def test_parser_is_prudent_for_win_loss_unknown_and_malformed() -> None:
    victory = parse_battle_log(_fixture("victory_en.txt"))
    defeat = parse_battle_log(_fixture("defeat_fr.txt"))
    unknown = parse_battle_log(_fixture("unknown.txt"))
    malformed = parse_battle_log(_fixture("malformed.txt"))

    assert (victory.valid, victory.outcome, victory.reference_player) == (True, "W", "JoueurA")
    assert (defeat.valid, defeat.outcome) == (True, "L")
    assert (unknown.valid, unknown.outcome) == (True, "inconnue")
    assert malformed.valid is False
    assert malformed.outcome == "inconnue"


def test_winner_must_match_two_corroborated_participants_with_unicode_case() -> None:
    base = (
        "Reference player: Élodie\n"
        "Turn # 1 - Élodie's Turn\n"
        "Élodie played Ralts.\n"
        "Turn # 1 - AdversaireB's Turn\n"
        "AdversaireB played Pikachu.\n"
    )
    assert parse_battle_log(base + "E\u0301LODIE wins.\n").outcome == "W"
    assert parse_battle_log(base + "adversaireb wins.\n").outcome == "L"

    third = parse_battle_log(base + "Intrus wins.\n")
    assert third.outcome == "inconnue"
    assert any("non corroboré" in warning for warning in third.warnings)


def test_win_without_corroborated_opponent_stays_unknown() -> None:
    parsed = parse_battle_log(
        "Reference player: JoueurA\nTurn # 1 - JoueurA's Turn\n"
        "JoueurA played Iono.\nJoueurA wins.\n"
    )
    assert parsed.outcome == "inconnue"
    assert any("sans adversaire corroboré" in warning for warning in parsed.warnings)


def test_conflicting_identity_or_winner_is_ambiguous() -> None:
    conflicting_reference = parse_battle_log(
        "Reference player: JoueurA\nReference player: AdversaireB\n"
        "Turn # 1 - JoueurA's Turn\nJoueurA played Iono.\n"
        "Turn # 1 - AdversaireB's Turn\nAdversaireB played Pikachu.\n"
        "JoueurA wins.\n"
    )
    assert conflicting_reference.reference_player is None
    assert conflicting_reference.outcome == "inconnue"
    assert conflicting_reference.valid is False

    conflicting_winner = parse_battle_log(
        "Reference player: JoueurA\n"
        "Turn # 1 - JoueurA's Turn\nJoueurA played Iono.\n"
        "Turn # 1 - AdversaireB's Turn\nAdversaireB played Pikachu.\n"
        "JoueurA wins.\nAdversaireB wins.\n"
    )
    assert conflicting_winner.winner is None
    assert conflicting_winner.outcome == "inconnue"
    assert any("Plusieurs gagnants" in warning for warning in conflicting_winner.warnings)


@pytest.mark.parametrize(
    "text",
    [
        (
            "Turn # 1 - JoueurA's Turn\nJoueurA drew Iono.\n"
            "Turn # 1 - AdversaireB's Turn\nAdversaireB drew Pikachu.\n"
            "AdversaireB drew Nest Ball.\nAdversaireB wins.\n"
        ),
        (
            "Tour no 1 - Tour de JoueurA\nJoueurA a pioché Iono.\n"
            "Tour no 1 - Tour de AdversaireB\nAdversaireB a pioché Pikachu.\n"
            "AdversaireB a pioché Hyper Ball.\nAdversaireB remporte la partie.\n"
        ),
    ],
)
def test_named_draw_frequency_never_assigns_player_identity(text: str) -> None:
    parsed = parse_battle_log(text)
    assert parsed.reference_player is None
    assert parsed.outcome == "inconnue"
    assert parsed.valid is False


def test_used_action_does_not_turn_attack_name_into_observed_card(local_tmp: Path) -> None:
    text = (
        "Joueur de référence : JoueurA\n"
        "Tour no 1 - Tour de JoueurA\n"
        "JoueurA a joué Tarsal.\nJoueurA a utilisé Memory Skip.\n"
        "Tour no 1 - Tour de AdversaireB\nAdversaireB a joué Pikachu.\n"
        "JoueurA remporte la partie.\n"
    )
    parsed = parse_battle_log(text)
    used = [event for event in parsed.events if event.event_type == "use"]
    assert len(used) == 1
    assert used[0].card_name is None

    db_path = local_tmp / "attacks.sqlite3"
    import_battle_log(db_path, text, source_kind="file", deck_id="principal")
    connection = sqlite3.connect(db_path)
    cards = {row[0] for row in connection.execute("SELECT card_name FROM card_observations")}
    connection.close()
    assert "Memory Skip" not in cards


def test_public_log_shapes_do_not_invent_actor_or_opening_hand_card() -> None:
    parsed = parse_battle_log(
        "Setup\nReference player: JoueurA\n"
        "JoueurA drew 7 cards for the opening hand.\n"
        "Turn # 1 - JoueurA's Turn\n"
        "JoueurA drew Ralts and played it to the Bench.\n"
        "AdversaireB drew 2 cards and played them to the Bench.\n"
        "All Prize cards taken. JoueurA wins.\n"
    )
    assert parsed.opponent_name == "AdversaireB"
    assert {event.actor for event in parsed.events} == {"JoueurA"}
    assert [event.card_name for event in parsed.events] == ["Ralts"]


def test_import_migrates_schema_one_without_losing_seed_tables(local_tmp: Path) -> None:
    db_path = local_tmp / "migration.sqlite3"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY, title TEXT)")
    connection.execute("INSERT INTO documents(title) VALUES ('conserver')")
    connection.execute("PRAGMA user_version = 1")
    connection.commit()
    initialize_schema(connection)
    assert connection.execute("SELECT title FROM documents").fetchone()[0] == "conserver"
    assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    connection.close()


def test_duplicate_import_is_idempotent_and_raw_is_not_stored(local_tmp: Path) -> None:
    db_path = local_tmp / "logs.sqlite3"
    text = _fixture("victory_en.txt")
    first = import_battle_log(db_path, text, source_kind="file", source_name="private.txt", deck_id="principal")
    second = import_battle_log(db_path, text, source_kind="file", source_name="private.txt", deck_id="principal")
    assert first["duplicate"] is False
    assert second["duplicate"] is True
    assert first["battle_id"] == second["battle_id"]
    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT COUNT(*) FROM battle_logs").fetchone()[0] == 1
    columns = {row[1] for row in connection.execute("PRAGMA table_info(battle_logs)")}
    assert "raw_text" not in columns
    connection.close()


def test_reparse_replaces_old_analysis_transactionally_without_duplication(local_tmp: Path) -> None:
    db_path = local_tmp / "reparse.sqlite3"
    text = (
        "Reference player: JoueurA\n"
        "Turn # 1 - JoueurA's Turn\nJoueurA played Ralts.\n"
        "Turn # 1 - AdversaireB's Turn\nAdversaireB played Pikachu.\n"
        "Intrus wins.\n"
    )
    first = import_battle_log(
        db_path, text, source_kind="file", source_name="ancien.txt",
        deck_id="principal", parser_version="pm0002-1",
    )
    connection = sqlite3.connect(db_path)
    connection.execute(
        "UPDATE battle_logs SET outcome = 'L', parser_version = 'pm0002-1' WHERE id = ?",
        (first["battle_id"],),
    )
    connection.commit()
    connection.close()

    repaired = import_battle_log(
        db_path, text, source_kind="file", source_name="ancien.txt",
        deck_id="principal", reparse=True,
    )
    assert repaired["reparsed"] is True
    assert repaired["battle_id"] == first["battle_id"]
    assert repaired["outcome"] == "inconnue"

    connection = sqlite3.connect(db_path)
    row = connection.execute(
        "SELECT COUNT(*), outcome, parser_version, deck_id FROM battle_logs"
    ).fetchone()
    event_count = connection.execute("SELECT COUNT(*) FROM battle_events").fetchone()[0]
    connection.close()
    assert row == (1, "inconnue", battle_logs.PARSER_VERSION, "principal")
    assert event_count == repaired["events"]


def test_reparse_preserves_deck_and_old_data_when_request_is_invalid(
    local_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = local_tmp / "reparse-safety.sqlite3"
    text = _fixture("victory_en.txt")
    first = import_battle_log(db_path, text, source_kind="file", deck_id="principal")

    duplicate = import_battle_log(db_path, text, source_kind="file", deck_id="autre")
    assert duplicate["duplicate"] is True
    assert duplicate["deck_id"] == "principal"

    with pytest.raises(ValueError, match="refuse de changer le deck"):
        import_battle_log(
            db_path, text, source_kind="file", deck_id="autre", reparse=True,
        )
    with pytest.raises(ValueError, match="vide"):
        import_battle_log(db_path, "", source_kind="file", deck_id="principal", reparse=True)

    connection = sqlite3.connect(db_path)
    event_count_before = connection.execute("SELECT COUNT(*) FROM battle_events").fetchone()[0]
    connection.execute("UPDATE battle_logs SET outcome = 'L' WHERE id = ?", (first["battle_id"],))
    connection.commit()
    connection.close()

    def fail_during_replacement(*args, **kwargs):
        raise RuntimeError("échec simulé après suppression")

    monkeypatch.setattr(battle_logs, "_insert_events", fail_during_replacement)
    with pytest.raises(RuntimeError, match="échec simulé"):
        import_battle_log(db_path, text, source_kind="file", reparse=True)

    connection = sqlite3.connect(db_path)
    row = connection.execute(
        "SELECT id, deck_id, outcome FROM battle_logs WHERE id = ?", (first["battle_id"],)
    ).fetchone()
    count = connection.execute("SELECT COUNT(*) FROM battle_logs").fetchone()[0]
    event_count_after = connection.execute("SELECT COUNT(*) FROM battle_events").fetchone()[0]
    connection.close()
    assert row == (first["battle_id"], "principal", "L")
    assert count == 1
    assert event_count_after == event_count_before


def test_unassigned_logs_get_distinct_observed_decks(local_tmp: Path) -> None:
    db_path = local_tmp / "decks.sqlite3"
    first = import_battle_log(db_path, _synthetic(1), source_kind="stdin")
    second = import_battle_log(db_path, _synthetic(2), source_kind="stdin")
    assert first["deck_id"].startswith("observed-")
    assert first["deck_id"] != second["deck_id"]


def test_parser_versions_are_recorded_without_breaking_profiles(local_tmp: Path) -> None:
    db_path = local_tmp / "versions.sqlite3"
    import_battle_log(db_path, _synthetic(1), source_kind="stdin", deck_id="principal", parser_version="pm0002-1")
    import_battle_log(db_path, _synthetic(2), source_kind="stdin", deck_id="principal", parser_version="pm0002-2")
    connection = sqlite3.connect(db_path)
    versions = {row[0] for row in connection.execute("SELECT parser_version FROM battle_logs")}
    connection.close()
    assert versions == {"pm0002-1", "pm0002-2"}


def test_malicious_lines_are_data_and_never_executed(local_tmp: Path) -> None:
    marker = ROOT / "data" / "local" / "should-not-exist.txt"
    assert not marker.exists()
    result = import_battle_log(local_tmp / "safe.sqlite3", _fixture("malicious.txt"), source_kind="file")
    assert result["valid"] is True
    assert not marker.exists()


def test_windows_encodings_and_oversized_input() -> None:
    text = "JoueurA a joué Énergie."
    decoded, encoding = decode_log_bytes(text.encode("cp1252"))
    assert decoded == text
    assert encoding == "cp1252"
    with pytest.raises(ValueError, match="volumineux"):
        parse_battle_log("x" * (MAX_LOG_BYTES + 1))


def test_clipboard_is_explicit_fixed_command_and_content_remains_data(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[list[str]] = []

    def fake_run(command, **kwargs):
        captured.append(command)
        return subprocess.CompletedProcess(command, 0, "$(Write-Output danger)\n", "")

    monkeypatch.setattr(battle_logs.sys, "platform", "win32")
    monkeypatch.setattr(battle_logs.subprocess, "run", fake_run)
    assert battle_logs.read_clipboard() == "$(Write-Output danger)\n"
    assert len(captured) == 1
    assert captured[0][:4] == ["powershell", "-NoProfile", "-NonInteractive", "-Command"]
    assert captured[0][4].endswith("Get-Clipboard -Raw")
    assert "UTF8Encoding" in captured[0][4]


def test_database_status_reports_migrated_schema(local_tmp: Path) -> None:
    db_path = local_tmp / "status.sqlite3"
    import_battle_log(db_path, _fixture("unknown.txt"), source_kind="file")
    assert database_status(db_path)["schema_version"] == SCHEMA_VERSION


def test_current_french_export_shape_uses_unnumbered_turns_and_combined_result() -> None:
    text = (
        "JoueurAlpha a pioché 7 cartes pour sa main de départ.\n"
        "• Ralts, Énergie Psy, Iono\n"
        "Tour de AdversaireBeta\n"
        "- AdversaireBeta a pioché Pikachu.\n"
        "Tour de JoueurAlpha\n"
        "- JoueurAlpha a joué Ralts.\n"
        "- Ralts de JoueurAlpha a utilisé Rugissement.\n"
        "JoueurAlpha a récupéré toutes ses cartes Récompense. JoueurAlpha gagne.\n"
    )

    parsed = parse_battle_log(text)

    assert parsed.reference_player == "JoueurAlpha"
    assert parsed.opponent_name == "AdversaireBeta"
    assert parsed.winner == "JoueurAlpha"
    assert parsed.outcome == "W"
    assert parsed.valid is True
    assert parsed.max_turn == 2
    assert "Rugissement" not in {event.card_name for event in parsed.events}


@pytest.mark.parametrize(
    ("text", "expected_card", "opponent_card"),
    [
        (
            "Joueur de référence : JoueurA\n"
            "Tour de AdversaireB\nAdversaireB a pioché la carte Carte Beta et l’a jouée sur le Banc.\n"
            "Tour de JoueurA\nJoueurA a pioché la carte Carte Alpha et l’a jouée sur le Banc.\n"
            "JoueurA gagne.\n",
            "Carte Alpha",
            "Carte Beta",
        ),
        (
            "Reference player: PlayerA\n"
            "Turn # 1 - PlayerA's Turn\nPlayerA drew the card Card Alpha and played it to the Bench.\n"
            "Turn # 1 - PlayerB's Turn\nPlayerB drew the card Card Beta and played it to the Bench.\n"
            "PlayerB wins.\n",
            "Card Alpha",
            "Card Beta",
        ),
    ],
)
def test_compound_draw_play_keeps_only_the_real_card_name(
    local_tmp: Path, text: str, expected_card: str, opponent_card: str
) -> None:
    parsed = parse_battle_log(text)
    assert parsed.valid is True
    assert parsed.outcome in {"W", "L"}
    assert {event.card_name for event in parsed.events} >= {expected_card}
    assert not any(
        event.card_name and ("played" in event.card_name or "joué" in event.card_name)
        for event in parsed.events
    )

    db_path = local_tmp / "compound.sqlite3"
    imported = import_battle_log(db_path, text, source_kind="file", deck_id="principal")
    connection = sqlite3.connect(db_path)
    rows = connection.execute(
        "SELECT owner_role, card_name FROM card_observations ORDER BY owner_role"
    ).fetchall()
    connection.close()
    assert imported["outcome"] == parsed.outcome
    assert set(rows) == {("self", expected_card), ("opponent", opponent_card)}


@pytest.mark.parametrize(
    "generic_draw",
    [
        "JoueurA a pioché une carte supplémentaire car JoueurB a déclaré au moins une misère.",
        "PlayerA drew an additional card because PlayerB declared at least one mulligan.",
    ],
)
def test_generic_mulligan_draw_is_an_event_not_a_card_observation(
    local_tmp: Path, generic_draw: str
) -> None:
    text = (
        "Reference player: PlayerA\n"
        "Turn # 1 - PlayerA's Turn\n"
        f"{generic_draw}\nPlayerA played Card Alpha.\n"
        "Turn # 1 - PlayerB's Turn\nPlayerB played Card Beta.\n"
    )
    parsed = parse_battle_log(text)
    generic_events = [
        event
        for event in parsed.events
        if "additional" in event.evidence or "supplémentaire" in event.evidence
    ]
    assert len(generic_events) == 1
    assert generic_events[0].event_type == "draw"
    assert generic_events[0].card_name is None
    assert generic_events[0].confidence == "low"

    db_path = local_tmp / "generic.sqlite3"
    import_battle_log(db_path, text, source_kind="stdin", deck_id="principal")
    connection = sqlite3.connect(db_path)
    event = connection.execute(
        "SELECT card_name, confidence FROM battle_events WHERE evidence LIKE '%mulligan%' OR evidence LIKE '%misère%'"
    ).fetchone()
    observations = connection.execute("SELECT COUNT(*) FROM card_observations").fetchone()[0]
    connection.close()
    assert event == (None, "low")
    assert observations == 2


def test_precision_reparse_preserves_battle_deck_and_private_boundaries(local_tmp: Path) -> None:
    db_path = local_tmp / "precision.sqlite3"
    deck_text = (ROOT / "tests" / "fixtures" / "decks" / "valid_fr.txt").read_text(encoding="utf-8")
    from pokemind.decks import import_deck

    deck = import_deck(db_path, deck_text, deck_id="principal", source_kind="stdin")
    text = (
        "Joueur de référence : JoueurA\n"
        "Tour de JoueurA\n"
        "JoueurA a pioché la carte Carte Alpha et l’a jouée sur le Banc.\n"
        "JoueurA a pioché une carte supplémentaire car JoueurB a déclaré au moins une misère.\n"
        "Tour de JoueurB\nJoueurB a joué Carte Beta.\nJoueurA gagne.\n"
    )
    first = import_battle_log(
        db_path, text, source_kind="file", source_name="private-user-log.txt",
        deck_id="principal", parser_version="ancien",
    )
    connection = sqlite3.connect(db_path)
    connection.execute(
        "UPDATE battle_logs SET imported_at = '2020-01-01T00:00:00Z' WHERE id = ?",
        (first["battle_id"],),
    )
    connection.execute(
        "UPDATE observed_decks SET last_seen_at = '2020-01-02T00:00:00Z' WHERE deck_id = 'principal'"
    )
    connection.commit()
    connection.close()
    reparsed = import_battle_log(
        db_path, text, source_kind="file", source_name="private-user-log.txt",
        deck_id="principal", reparse=True,
    )
    duplicate = import_battle_log(
        db_path, text, source_kind="file", source_name="private-user-log.txt",
        deck_id="principal",
    )

    connection = sqlite3.connect(db_path)
    battle = connection.execute(
        "SELECT id, outcome, deck_id, parser_version, imported_at FROM battle_logs"
    ).fetchone()
    observed_last_seen = connection.execute(
        "SELECT last_seen_at FROM observed_decks WHERE deck_id = 'principal'"
    ).fetchone()[0]
    deck_after = connection.execute(
        "SELECT id, version_number, total_cards, list_sha256 FROM deck_versions"
    ).fetchone()
    links = connection.execute("SELECT COUNT(*) FROM battle_deck_versions").fetchone()[0]
    false_fragments = connection.execute(
        "SELECT COUNT(*) FROM card_observations WHERE card_name LIKE '%joué%' OR card_name LIKE '%misère%'"
    ).fetchone()[0]
    columns = {row[1] for row in connection.execute("PRAGMA table_info(battle_logs)")}
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    connection.close()

    assert reparsed["battle_id"] == first["battle_id"] == duplicate["battle_id"]
    assert duplicate["duplicate"] is True
    assert battle == (
        first["battle_id"], "W", "principal", battle_logs.PARSER_VERSION,
        "2020-01-01T00:00:00Z",
    )
    assert observed_last_seen == "2020-01-02T00:00:00Z"
    assert deck_after == (deck["deck_version_id"], 1, 60, deck["list_sha256"])
    assert links == 0
    assert false_fragments == 0
    assert "raw_text" not in columns
    assert integrity == "ok"
