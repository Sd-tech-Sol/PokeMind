from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from pokemind.collection import (
    collection_coverage,
    collection_missing,
    collection_status,
    credits_status,
    import_collection,
    rollback_collection,
    rollback_credits,
    set_credits,
)
from pokemind.database import SCHEMA_VERSION, connect_writable, initialize_schema
from pokemind.decks import import_deck


DECK = """Pokémon: 1
4 Alpha SYN 1

Trainer: 1
52 Support SYN 2

Energy: 1
4 Basic Energy SYN 3

Total Cards: 60
"""


def _catalog(db_path: Path) -> None:
    connection = connect_writable(db_path)
    try:
        initialize_schema(connection)
        now = "2026-10-13T00:00:00Z"
        connection.execute(
            """INSERT INTO catalog_sets
               (tcgdex_id, name_en, name_fr, tcg_online_code, discovered_at, updated_at)
               VALUES ('synthetic', 'Synthetic', 'Synthétique', 'SYN', ?, ?)""",
            (now, now),
        )
        for tcgdex_id, local_id, name_en, name_fr in (
            ("synthetic-1", "1", "Alpha", "Alpha FR"),
            ("synthetic-2", "2", "Support", "Soutien"),
            ("synthetic-3", "3", "Basic Energy", "Énergie de base"),
        ):
            connection.execute(
                """INSERT INTO catalog_printings
                   (tcgdex_id, set_id, local_id, discovered_at, updated_at,
                    brief_source_url, brief_retrieved_at)
                   VALUES (?, 'synthetic', ?, ?, ?, 'https://api.tcgdex.net/v2/en/cards', ?)""",
                (tcgdex_id, local_id, now, now, now),
            )
            for language, name in (("en", name_en), ("fr", name_fr)):
                connection.execute(
                    """INSERT INTO catalog_translations
                       (printing_id, language, status, name, source_url, retrieved_at)
                       VALUES (?, ?, 'present', ?, ?, ?)""",
                    (tcgdex_id, language, name, f"https://api.tcgdex.net/v2/{language}/cards/{tcgdex_id}", now),
                )
        connection.commit()
    finally:
        connection.close()


def _write_collection(path: Path, entries: list[dict[str, object]], *, as_of: str = "2026-10-13") -> Path:
    path.write_text(
        json.dumps({
            "schema_version": 1,
            "as_of": as_of,
            "source": {"kind": "owner_provided"},
            "entries": entries,
        }, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def _entry(
    name: str = "Alpha", quantity: int = 4, *, number: str = "1",
    ownership: str = "confirmed_owned", tcgdex_id: str | None = None,
) -> dict[str, object]:
    row: dict[str, object] = {
        "name": name,
        "set_code": "SYN",
        "collector_number": number,
        "variant": "normal",
        "quantity": quantity,
        "ownership_status": ownership,
    }
    if tcgdex_id is not None:
        row["tcgdex_id"] = tcgdex_id
    return row


def test_collection_dry_run_is_read_only_and_keeps_unknown_without_catalog(local_tmp: Path) -> None:
    db_path = local_tmp / "absent.sqlite3"
    source = _write_collection(local_tmp / "collection.json", [_entry()])
    before = source.read_bytes()
    result = import_collection(db_path, source)
    assert result["mode"] == "dry_run" and result["read_only"] is True
    assert result["resolution"] == {"resolved": 0, "ambiguous": 0, "unknown": 1, "denominator": 1}
    assert result["schema_migration_required_on_apply"] is True
    assert not db_path.exists() and source.read_bytes() == before


def test_collection_apply_resolves_fr_alias_versions_history_and_rollback(local_tmp: Path) -> None:
    db_path = local_tmp / "collection.sqlite3"
    _catalog(db_path)
    first_file = _write_collection(local_tmp / "first.json", [_entry(name="Alpha FR")])
    with pytest.raises(ValueError, match="--confirm-owner"):
        import_collection(db_path, first_file, apply=True)
    first = import_collection(db_path, first_file, apply=True, confirm_owner=True)
    assert first["resolution"]["resolved"] == 1 and first["duplicate"] is False
    duplicate = import_collection(db_path, first_file, apply=True, confirm_owner=True)
    assert duplicate["duplicate"] is True and duplicate["snapshot_id"] == first["snapshot_id"]

    second_file = _write_collection(local_tmp / "second.json", [_entry(quantity=2)])
    second = import_collection(db_path, second_file, apply=True, confirm_owner=True)
    status = collection_status(db_path)
    assert status["active"]["id"] == second["snapshot_id"]
    assert len(status["history"]) == 2 and status["history"][1]["status"] == "superseded"
    assert collection_coverage(db_path)["coverage"]["ratio"] == 1.0

    preview = rollback_collection(db_path, first["snapshot_id"])
    assert preview["read_only"] is True and preview["entries"] == 1
    restored = rollback_collection(db_path, first["snapshot_id"], apply=True, confirm_owner=True)
    assert restored["snapshot_id"] not in {first["snapshot_id"], second["snapshot_id"]}
    assert collection_status(db_path)["active"]["rollback_of_id"] == first["snapshot_id"]


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda row: row.update(quantity=-1), "quantity"),
        (lambda row: row.update(set_code="BAD CODE"), "set_code"),
        (lambda row: row.update(ownership_status="confirmed_owned", quantity=0), "quantity >= 1"),
    ],
)
def test_collection_rejects_invalid_entries(local_tmp: Path, mutator, message: str) -> None:
    row = _entry()
    mutator(row)
    source = _write_collection(local_tmp / "invalid.json", [row])
    with pytest.raises(ValueError, match=message):
        import_collection(local_tmp / "invalid.sqlite3", source)


def test_collection_rejects_duplicates_future_dates_and_conflicting_identity(local_tmp: Path) -> None:
    duplicate = _write_collection(local_tmp / "duplicate.json", [_entry(), _entry()])
    with pytest.raises(ValueError, match="en double"):
        import_collection(local_tmp / "duplicate.sqlite3", duplicate)
    future = _write_collection(local_tmp / "future.json", [_entry()], as_of="2999-01-01")
    with pytest.raises(ValueError, match="futur"):
        import_collection(local_tmp / "future.sqlite3", future)

    db_path = local_tmp / "conflict.sqlite3"
    _catalog(db_path)
    conflict = _write_collection(
        local_tmp / "conflict.json", [_entry(tcgdex_id="synthetic-2")]
    )
    result = import_collection(db_path, conflict)
    assert result["resolution"]["ambiguous"] == 1
    assert result["items"][0]["resolution_reason"] == "SUPPLIED_ID_CONFLICTS_WITH_FIELDS"


def test_missing_distinguishes_known_missing_unknown_and_never_infers_from_deck(local_tmp: Path) -> None:
    db_path = local_tmp / "missing.sqlite3"
    _catalog(db_path)
    import_deck(db_path, DECK, deck_id="synthetic", source_kind="stdin")
    unknown = collection_missing(db_path, "synthetic")
    assert unknown["collection_status"] == "unknown"
    assert all(line["missing_quantity"] is None for line in unknown["lines"])

    source = _write_collection(
        local_tmp / "partial.json",
        [
            _entry(quantity=4),
            _entry(name="Support", number="2", quantity=0, ownership="reported_missing"),
        ],
    )
    import_collection(db_path, source, apply=True, confirm_owner=True)
    result = collection_missing(db_path, "synthetic")
    by_name = {line["name"]: line for line in result["lines"]}
    assert by_name["Alpha"]["missing_quantity"] == 0
    assert by_name["Support"]["missing_quantity"] == 52
    assert by_name["Basic Energy"]["missing_quantity"] is None
    assert all(line["craft_cost"] == "unknown" for line in result["lines"])


def test_credits_are_previewed_versioned_and_rollback_never_spends(local_tmp: Path) -> None:
    db_path = local_tmp / "credits.sqlite3"
    preview = set_credits(db_path, 1200, as_of="2026-10-13")
    assert preview["read_only"] is True and preview["credits_spent"] == 0
    assert not db_path.exists()
    with pytest.raises(ValueError, match="--confirm-owner"):
        set_credits(db_path, 1200, as_of="2026-10-13", apply=True)
    first = set_credits(db_path, 1200, as_of="2026-10-13", apply=True, confirm_owner=True)
    second = set_credits(db_path, 900, as_of="2026-10-13", apply=True, confirm_owner=True)
    assert credits_status(db_path)["active"]["id"] == second["snapshot_id"]
    assert rollback_credits(db_path, first["snapshot_id"])["read_only"] is True
    restored = rollback_credits(db_path, first["snapshot_id"], apply=True, confirm_owner=True)
    active = credits_status(db_path)["active"]
    assert active["id"] == restored["snapshot_id"] and active["amount"] == 1200
    assert active["source_kind"] == "owner_rollback" and restored["credits_spent"] == 0


def test_historical_collection_and_credits_require_observation_and_local_capture_dates(local_tmp: Path) -> None:
    db_path = local_tmp / "historical.sqlite3"
    _catalog(db_path)
    import_deck(db_path, DECK, deck_id="synthetic", source_kind="stdin")
    first = import_collection(
        db_path, _write_collection(local_tmp / "may.json", [_entry(quantity=4)], as_of="2026-05-01"),
        apply=True, confirm_owner=True,
    )
    second = import_collection(
        db_path, _write_collection(local_tmp / "june.json", [_entry(quantity=2)], as_of="2026-06-01"),
        apply=True, confirm_owner=True,
    )
    first_credits = set_credits(db_path, 111, as_of="2026-05-01", apply=True, confirm_owner=True)
    second_credits = set_credits(db_path, 222, as_of="2026-06-01", apply=True, confirm_owner=True)
    connection = sqlite3.connect(db_path)
    connection.execute("UPDATE collection_snapshots SET recorded_at='2026-05-02T02:00:00Z' WHERE id=?", (first["snapshot_id"],))
    connection.execute("UPDATE collection_snapshots SET recorded_at='2026-06-02T02:00:00Z' WHERE id=?", (second["snapshot_id"],))
    connection.execute("UPDATE credit_snapshots SET recorded_at='2026-05-02T02:00:00Z' WHERE id=?", (first_credits["snapshot_id"],))
    connection.execute("UPDATE credit_snapshots SET recorded_at='2026-06-02T02:00:00Z' WHERE id=?", (second_credits["snapshot_id"],))
    connection.commit()
    connection.close()

    assert collection_status(db_path, as_of="2026-04-30")["availability_status"] == "NOT_AVAILABLE_AS_OF"
    assert collection_status(db_path, as_of="2026-05-01")["active"]["id"] == first["snapshot_id"]
    assert collection_status(db_path, as_of="2026-06-01")["active"]["id"] == second["snapshot_id"]
    assert credits_status(db_path, as_of="2026-04-30")["active"] is None
    assert credits_status(db_path, as_of="2026-05-01")["active"]["amount"] == 111
    assert credits_status(db_path, as_of="2026-06-01")["active"]["amount"] == 222
    missing = collection_missing(db_path, "synthetic", as_of="2026-05-01")
    assert missing["availability_status"] == "AVAILABLE_AS_OF"
    assert next(row for row in missing["lines"] if row["name"] == "Alpha")["missing_quantity"] == 0

    rollback = rollback_collection(db_path, first["snapshot_id"], apply=True, confirm_owner=True)
    rollback_credit = rollback_credits(db_path, first_credits["snapshot_id"], apply=True, confirm_owner=True)
    connection = sqlite3.connect(db_path)
    connection.execute("UPDATE collection_snapshots SET recorded_at='2026-07-01T16:00:00Z' WHERE id=?", (rollback["snapshot_id"],))
    connection.execute("UPDATE credit_snapshots SET recorded_at='2026-07-01T16:00:00Z' WHERE id=?", (rollback_credit["snapshot_id"],))
    connection.commit()
    connection.close()
    assert collection_status(db_path, as_of="2026-06-15")["active"]["id"] == second["snapshot_id"]
    assert collection_status(db_path, as_of="2026-07-01")["active"]["id"] == rollback["snapshot_id"]
    assert credits_status(db_path, as_of="2026-07-01")["active"]["amount"] == 111


def test_historical_status_on_old_schema_is_unknown_without_migration(local_tmp: Path) -> None:
    db_path = local_tmp / "old.sqlite3"
    sqlite3.connect(db_path).close()
    collection = collection_status(db_path, as_of="2026-05-01")
    credits = credits_status(db_path, as_of="2026-05-01")
    assert collection["availability_status"] == "NOT_AVAILABLE_AS_OF"
    assert credits["availability_status"] == "NOT_AVAILABLE_AS_OF"
    assert collection["reason"] == credits["reason"] == "SCHEMA_MIGRATION_REQUIRED"


def test_lot_b_migration_creates_backup_and_preserves_integrity(local_tmp: Path) -> None:
    db_path = local_tmp / "legacy.sqlite3"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute("INSERT INTO metadata VALUES ('sentinel', 'preserved')")
    connection.execute("PRAGMA user_version = 9")
    connection.commit()
    connection.close()

    source = _write_collection(local_tmp / "migrate.json", [])
    import_collection(db_path, source, apply=True, confirm_owner=True)
    connection = sqlite3.connect(db_path)
    assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert connection.execute("SELECT value FROM metadata WHERE key='sentinel'").fetchone()[0] == "preserved"
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    backup = Path(connection.execute("SELECT value FROM metadata WHERE key='last_schema_backup'").fetchone()[0])
    connection.close()
    assert backup.is_file()
    restored = sqlite3.connect(backup)
    assert restored.execute("PRAGMA user_version").fetchone()[0] == 9
    assert restored.execute("SELECT value FROM metadata WHERE key='sentinel'").fetchone()[0] == "preserved"
    assert restored.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    restored.close()
