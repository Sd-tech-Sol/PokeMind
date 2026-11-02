from __future__ import annotations

import hashlib
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path

import pytest

import pokemind.attestations as attestation_module
import pokemind.cli as cli_module
import pokemind.database as database_module
from pokemind.analysis import analyze_deck
from pokemind.attestations import (
    confirm_battle_version,
    list_link_candidates,
    revoke_battle_version,
)
from pokemind.database import connect_writable, initialize_schema
from pokemind.decks import import_deck
from pokemind.version_evidence import version_evidence


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


def _add_battle(
    path: Path,
    *,
    deck_id: str = "synthetic",
    valid: int = 1,
    suffix: str = "1",
) -> int:
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute(
        "INSERT OR IGNORE INTO observed_decks VALUES (?, 'observé partiellement', ?, ?)",
        (deck_id, "2026-05-01T00:00:00Z", "2026-05-02T00:00:00Z"),
    )
    cursor = connection.execute(
        """INSERT INTO battle_logs
           (source_sha256, imported_at, parser_version, source_kind, source_name,
            reference_player, opponent_name, outcome, winner, valid, deck_id,
            max_turn, recognized_events, warnings_json)
           VALUES (?, '2026-05-02T12:00:00Z', 'synthetic', 'stdin', NULL,
                   NULL, NULL, 'W', NULL, ?, ?, 1, 0, '[]')""",
        (f"synthetic-digest-{deck_id}-{suffix}", valid, deck_id),
    )
    battle_id = int(cursor.lastrowid)
    connection.commit()
    connection.close()
    return battle_id


def _database(path: Path, *, two_versions: bool = False) -> tuple[Path, int]:
    import_deck(path, DECK, deck_id="synthetic", source_kind="stdin")
    if two_versions:
        changed = DECK.replace(
            "4 Creature Alpha SYN 001", "3 Creature Alpha SYN 001"
        ).replace("3 Creature Gamma SYN 003", "4 Creature Gamma SYN 003")
        import_deck(path, changed, deck_id="synthetic", source_kind="stdin")
    connection = sqlite3.connect(path)
    connection.execute(
        """UPDATE deck_versions
              SET imported_at='2026-05-01T00:00:00Z',
                  approved_at='2026-05-01T00:00:00Z',
                  effective_from='2026-05-01T00:00:00Z'
            WHERE deck_id='synthetic'"""
    )
    connection.commit()
    connection.close()
    battle_id = _add_battle(path)
    return path, battle_id


def _downgrade_fixture_to_schema7(path: Path) -> None:
    connection = sqlite3.connect(path)
    connection.execute("DROP TABLE battle_version_attestations")
    connection.execute("PRAGMA user_version=7")
    connection.commit()
    connection.close()


def test_schema7_preview_is_byte_exact_and_missing_confirmation_never_migrates(
    local_tmp: Path,
) -> None:
    db_path, battle_id = _database(local_tmp / "preview.sqlite3")
    _downgrade_fixture_to_schema7(db_path)
    before = hashlib.sha256(db_path.read_bytes()).hexdigest()

    preview = confirm_battle_version(db_path, "synthetic", battle_id, 1)

    assert preview["status"] == "READY_FOR_OWNER_CONFIRMATION"
    assert preview["dry_run"] is True and preview["schema_version"] == 7
    assert hashlib.sha256(db_path.read_bytes()).hexdigest() == before
    with pytest.raises(ValueError, match="--confirm-owner"):
        confirm_battle_version(
            db_path, "synthetic", battle_id, 1, apply=True, confirm_owner=False
        )
    assert hashlib.sha256(db_path.read_bytes()).hexdigest() == before
    connection = sqlite3.connect(db_path)
    assert connection.execute("PRAGMA user_version").fetchone()[0] == 7
    assert connection.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE name='battle_version_attestations'"
    ).fetchone()[0] == 0
    connection.close()


def test_confirmation_is_dated_idempotent_and_not_retroactive(
    local_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path, battle_id = _database(local_tmp / "confirm.sqlite3")
    _downgrade_fixture_to_schema7(db_path)
    monkeypatch.setattr(attestation_module, "utc_now", lambda: "2026-06-01T12:34:56Z")

    applied = confirm_battle_version(
        db_path,
        "synthetic",
        battle_id,
        1,
        apply=True,
        confirm_owner=True,
        battle_date="2026-04-30",
    )
    duplicate = confirm_battle_version(
        db_path, "synthetic", battle_id, 1, apply=True, confirm_owner=True
    )

    assert applied["status"] == "OWNER_ATTESTATION_ACTIVE"
    assert applied["confirmed_at"] == "2026-06-01T12:34:56Z"
    assert duplicate["idempotent"] is True and duplicate["applied"] is False
    connection = sqlite3.connect(db_path)
    row = connection.execute(
        """SELECT confirmed_at, actor, provenance, asserted_battle_date,
                  battle_date_source, status
             FROM battle_version_attestations"""
    ).fetchone()
    assert row == (
        "2026-06-01T12:34:56Z",
        "owner_explicit_confirmation",
        "owner_asserted",
        "2026-04-30",
        "owner_declared",
        "active",
    )
    assert connection.execute("PRAGMA user_version").fetchone()[0] == database_module.SCHEMA_VERSION
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    connection.close()

    historical = version_evidence(db_path, "synthetic", as_of="2026-05-31")
    current = version_evidence(db_path, "synthetic", as_of="2026-06-01")
    analysis_before = analyze_deck(db_path, "synthetic", as_of="2026-05-31")
    analysis_after = analyze_deck(db_path, "synthetic", as_of="2026-06-01")
    assert historical["facts"]["battles"]["proven_same_deck_links"] == 0
    assert historical["facts"]["battles"]["temporal_unknown"] == 1
    assert current["facts"]["battles"]["owner_attested_active"] == 1
    assert current["facts"]["versions"][0]["owner_attested_battles"] == 1
    assert analysis_before["facts"]["battles"]["with_selected_version_proven"] == 0
    assert analysis_after["facts"]["battles"]["with_selected_version_owner_attested"] == 1
    assert any(
        item.get("provenance") == "owner_asserted"
        and item.get("externally_verified") is False
        for item in analysis_after["evidence"]
    )


def test_change_requires_revocation_and_revocation_preserves_audit(
    local_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path, battle_id = _database(local_tmp / "revoke.sqlite3", two_versions=True)
    timestamps = iter(
        ("2026-06-01T00:00:00Z", "2026-06-02T00:00:00Z", "2026-06-03T00:00:00Z")
    )
    monkeypatch.setattr(attestation_module, "utc_now", lambda: next(timestamps))
    confirm_battle_version(
        db_path, "synthetic", battle_id, 1, apply=True, confirm_owner=True
    )

    conflict = confirm_battle_version(db_path, "synthetic", battle_id, 2)
    assert conflict["status"] == "ACTIVE_ATTESTATION_CONFLICT"
    with pytest.raises(ValueError, match="ACTIVE_ATTESTATION_CONFLICT"):
        confirm_battle_version(
            db_path, "synthetic", battle_id, 2, apply=True, confirm_owner=True
        )

    revoked = revoke_battle_version(
        db_path, "synthetic", battle_id, apply=True, confirm_owner=True
    )
    again = revoke_battle_version(
        db_path, "synthetic", battle_id, apply=True, confirm_owner=True
    )
    assert revoked["status"] == "OWNER_ATTESTATION_REVOKED"
    assert again["status"] == "OWNER_ATTESTATION_ALREADY_REVOKED"
    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT COUNT(*) FROM battle_deck_versions").fetchone()[0] == 0
    assert connection.execute(
        "SELECT status, revoked_at, revocation_reason FROM battle_version_attestations"
    ).fetchone() == (
        "revoked",
        "2026-06-02T00:00:00Z",
        "owner_explicit_revocation",
    )
    connection.close()
    report = version_evidence(db_path, "synthetic", as_of="2026-06-02")
    assert report["facts"]["battles"]["owner_attested_revoked"] == 1
    assert report["facts"]["battles"]["proven_same_deck_links"] == 0
    assert list_link_candidates(db_path, "synthetic")["candidates"][0]["state"] == (
        "owner_attested_revoked"
    )

    replacement = confirm_battle_version(
        db_path, "synthetic", battle_id, 2, apply=True, confirm_owner=True
    )
    assert replacement["status"] == "OWNER_ATTESTATION_ACTIVE"
    connection = sqlite3.connect(db_path)
    assert connection.execute(
        "SELECT COUNT(*) FROM battle_version_attestations"
    ).fetchone()[0] == 2
    assert connection.execute(
        "SELECT COUNT(*) FROM battle_version_attestations WHERE status='active'"
    ).fetchone()[0] == 1
    connection.close()


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("UPDATE battle_logs SET valid=0", "BATTLE_INVALID"),
        ("UPDATE battle_logs SET deck_id='other'", "BATTLE_DECK_MISMATCH"),
        ("UPDATE deck_versions SET exact_confirmed=0", "VERSION_NOT_EXACT_60"),
        ("UPDATE deck_version_cards SET quantity=59 WHERE ordinal=1", "VERSION_NOT_EXACT_60"),
    ],
)
def test_invalid_pair_shapes_are_refused(
    local_tmp: Path, mutation: str, expected: str
) -> None:
    db_path, battle_id = _database(local_tmp / f"invalid-{expected}.sqlite3")
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA ignore_check_constraints=ON")
    connection.execute(mutation)
    connection.commit()
    connection.close()
    result = confirm_battle_version(db_path, "synthetic", battle_id, 1)
    assert result["status"] == expected


def test_other_deck_missing_ids_and_legacy_link_are_never_overwritten(
    local_tmp: Path,
) -> None:
    db_path, battle_id = _database(local_tmp / "legacy.sqlite3")
    connection = sqlite3.connect(db_path)
    version_id, effective, approved = connection.execute(
        "SELECT id, effective_from, approved_at FROM deck_versions"
    ).fetchone()
    connection.execute(
        "INSERT INTO battle_deck_versions VALUES (?, ?, ?, ?)",
        (battle_id, version_id, effective, approved),
    )
    connection.commit()
    connection.close()
    before = db_path.read_bytes()
    assert confirm_battle_version(db_path, "synthetic", battle_id, 1)["status"] == (
        "LEGACY_LINK_UNATTESTED"
    )
    assert revoke_battle_version(db_path, "synthetic", battle_id)["status"] == (
        "LEGACY_LINK_UNATTESTED"
    )
    assert confirm_battle_version(db_path, "synthetic", 9999, 1)["status"] == (
        "BATTLE_NOT_FOUND"
    )
    assert confirm_battle_version(db_path, "synthetic", battle_id, 9999)["status"] == (
        "VERSION_NOT_FOUND"
    )
    assert db_path.read_bytes() == before


def test_two_concurrent_incompatible_confirmations_leave_one_active_link(
    local_tmp: Path,
) -> None:
    db_path, battle_id = _database(local_tmp / "concurrent.sqlite3", two_versions=True)
    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    lock = threading.Lock()

    def worker(version: int) -> None:
        barrier.wait()
        try:
            result = confirm_battle_version(
                db_path,
                "synthetic",
                battle_id,
                version,
                apply=True,
                confirm_owner=True,
            )
            outcome = result["status"]
        except ValueError as exc:
            outcome = str(exc)
        with lock:
            outcomes.append(outcome)

    threads = [threading.Thread(target=worker, args=(version,)) for version in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT COUNT(*) FROM battle_deck_versions").fetchone()[0] == 1
    assert connection.execute(
        "SELECT COUNT(*) FROM battle_version_attestations WHERE status='active'"
    ).fetchone()[0] == 1
    connection.close()
    assert len(outcomes) == 2
    assert sum(item == "OWNER_ATTESTATION_ACTIVE" for item in outcomes) == 1


def test_schema7_migration_backup_preserves_all_subsystems(local_tmp: Path) -> None:
    db_path, battle_id = _database(local_tmp / "migration.sqlite3")
    for suffix in ("2", "3", "4", "5"):
        _add_battle(db_path, suffix=suffix)
    connection = sqlite3.connect(db_path)
    for index in range(1, 5):
        cursor = connection.execute(
            """INSERT INTO documents
               (document_key, title, path, source_date, content_sha256, imported_at)
               VALUES (?, ?, ?, '2026-01-01', ?, '2026-01-01T00:00:00Z')""",
            (
                f"synthetic-{index}.md",
                f"Synthétique {index}",
                f"synthetic-{index}.md",
                f"public-synthetic-{index}",
            ),
        )
        connection.execute(
            """INSERT INTO sections
               (document_id, ordinal, heading, heading_path, heading_level, start_line,
                end_line, char_start, char_end, content, content_sha256)
               VALUES (?, 1, ?, ?, 1, 1, 1, 0, 4, 'test', ?)""",
            (int(cursor.lastrowid), f"Test {index}", f"Test {index}", f"section-{index}"),
        )
    connection.execute(
        """INSERT INTO catalog_sets(tcgdex_id, discovered_at, updated_at)
           VALUES ('synthetic-set', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"""
    )
    connection.execute(
        """INSERT INTO official_rule_sources
           (source_id, source_type, url, title, language, consulted_at, captured_at,
            content_sha256, validation_status, rights_note)
           VALUES ('synthetic-rule', 'rules', 'https://www.pokemon.com/synthetic',
                   'Synthétique', 'fr', '2026-01-01T00:00:00Z',
                   '2026-01-01T00:00:00Z', 'rule-synthetic', 'verified', 'test')"""
    )
    connection.execute(
        """INSERT INTO meta_tournaments
           (tournament_id, name, date_utc, game, format, platform, is_online,
            is_public, provider_status, participant_count, decklists_enabled,
            special_rules_json, banned_cards_count, source_url, fetched_at,
            payload_sha256, snapshot_status)
           VALUES ('synthetic-tournament', 'Synthétique', '2026-01-01T00:00:00Z',
                   'PTCG', 'STANDARD', 'PTCGL', 1, 1, 'completed', 8, 1, '[]', 0,
                   'https://play.limitlesstcg.com/tournament/synthetic',
                   '2026-01-01T00:00:00Z', 'meta-synthetic', 'complete')"""
    )
    connection.execute("PRAGMA user_version=7")
    connection.execute("DROP TABLE battle_version_attestations")
    before = {
        table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        for table in (
            "documents", "sections", "deck_versions", "battle_logs",
            "catalog_sets", "official_rule_sources", "meta_tournaments",
        )
    }
    connection.commit()
    connection.close()

    confirm_battle_version(
        db_path, "synthetic", battle_id, 1, apply=True, confirm_owner=True
    )
    connection = sqlite3.connect(db_path)
    after = {
        table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        for table in before
    }
    backup_path = Path(
        connection.execute(
            "SELECT value FROM metadata WHERE key='last_schema_backup'"
        ).fetchone()[0]
    )
    assert before == after
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert connection.execute("SELECT COUNT(*) FROM sections_fts").fetchone()[0] == 4
    connection.close()
    assert backup_path.is_file()
    restored_path = local_tmp / "restored-schema7.sqlite3"
    shutil.copy2(backup_path, restored_path)
    restored = sqlite3.connect(restored_path)
    assert restored.execute("PRAGMA user_version").fetchone()[0] == 7
    assert restored.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert restored.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE name='battle_version_attestations'"
    ).fetchone()[0] == 0
    restored_counts = {
        table: int(restored.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        for table in before
    }
    assert restored_counts == before
    restored.close()


def test_attestation_migration_rolls_back_on_simulated_failure(
    local_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path, _ = _database(local_tmp / "rollback.sqlite3")
    _downgrade_fixture_to_schema7(db_path)

    def fail(connection: sqlite3.Connection) -> None:
        connection.execute("BEGIN IMMEDIATE")
        try:
            connection.execute("CREATE TABLE should_rollback(value TEXT)")
            raise sqlite3.DatabaseError("synthetic failure")
        except Exception:
            connection.rollback()
            raise

    monkeypatch.setattr(database_module, "_migrate_attestation_schema", fail)
    connection = connect_writable(db_path)
    with pytest.raises(sqlite3.DatabaseError, match="synthetic failure"):
        initialize_schema(connection)
    connection.close()
    check = sqlite3.connect(db_path)
    assert check.execute("PRAGMA user_version").fetchone()[0] == 7
    assert check.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE name='should_rollback'"
    ).fetchone()[0] == 0
    check.close()


def test_cli_json_text_listing_redaction_and_no_network(
    local_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path, battle_id = _database(
        local_tmp / "PrivateName token=synthetic-secret.sqlite3"
    )
    connection = sqlite3.connect(db_path)
    connection.execute(
        "UPDATE battle_logs SET opponent_name='PrivateOpponent' WHERE id=?",
        (battle_id,),
    )
    connection.commit()
    connection.close()
    candidates = list_link_candidates(db_path, "synthetic")
    assert candidates["candidates"][0]["battle_id"] == battle_id

    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket, "socket", forbidden)
    assert confirm_battle_version(db_path, "synthetic", battle_id, 1)["network_used"] is False

    base = [
        sys.executable, "-m", "pokemind", "deck", "link-battle",
        "--deck", "synthetic", "--battle-id", str(battle_id), "--version", "1",
        "--db", str(db_path),
    ]
    human = subprocess.run(
        base, cwd=ROOT, env=_environment(), text=True, encoding="utf-8",
        capture_output=True, check=False,
    )
    machine = subprocess.run(
        [*base, "--json"], cwd=ROOT, env=_environment(), text=True,
        encoding="utf-8", capture_output=True, check=False,
    )
    assert human.returncode == machine.returncode == 0
    payload = json.loads(machine.stdout)
    serialized = json.dumps(payload, ensure_ascii=False)
    assert payload["status"] == "READY_FOR_OWNER_CONFIRMATION"
    assert "prévisualisée sans écriture" in human.stdout
    for secret in (
        "PrivateName", "synthetic-secret", "PrivateOpponent", "Creature Alpha",
        str(db_path), "source_sha256",
    ):
        assert secret not in serialized
        assert secret not in human.stdout


def test_cli_redacts_database_error_details(
    local_tmp: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    db_path, battle_id = _database(local_tmp / "redacted.sqlite3")
    secret = r"C:\Users\PrivateName\private.sqlite3 token=secret Opponent Card"

    def fail(*args: object, **kwargs: object) -> dict[str, object]:
        raise sqlite3.DatabaseError(secret)

    monkeypatch.setattr(cli_module, "confirm_battle_version", fail)
    exit_code = cli_module.main(
        [
            "deck", "link-battle", "--deck", "synthetic",
            "--battle-id", str(battle_id), "--version", "1",
            "--db", str(db_path), "--json",
        ]
    )
    rendered = capsys.readouterr().out
    assert exit_code == 2
    assert secret not in rendered
    assert "détail technique est caviardé" in rendered
