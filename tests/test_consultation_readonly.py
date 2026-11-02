"""Consultations on synthetic historical databases must not commission them."""
from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from pokemind.battle_logs import import_battle_log
from pokemind.database import connect_readonly
from pokemind.decks import import_deck, show_deck
from pokemind.profiles import profile_review, profile_summary


FIXTURES = Path(__file__).parent / "fixtures"


def _fixture_database(path: Path) -> None:
    import_deck(path, (FIXTURES / "decks/valid_en.txt").read_text(encoding="utf-8"),
                deck_id="synthetic", source_kind="stdin")
    import_battle_log(path, (FIXTURES / "battle_logs/victory_en.txt").read_text(encoding="utf-8"),
                      deck_id="synthetic", source_kind="stdin")
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("PRAGMA user_version=7")


@pytest.mark.parametrize("operation", [show_deck, profile_summary, profile_review])
def test_historical_consultation_never_opens_writable_or_migrates(
    local_tmp: Path, monkeypatch: pytest.MonkeyPatch, operation,
) -> None:
    path = local_tmp / "history.sqlite3"
    _fixture_database(path)
    before = (hashlib.sha256(path.read_bytes()).digest(), path.stat().st_mtime_ns,
              sorted(item.name for item in local_tmp.iterdir()))
    original_connect = sqlite3.connect
    calls = []

    def read_only_connect(database, *args, **kwargs):
        calls.append(str(database))
        assert kwargs.get("uri") is True and "mode=ro" in str(database)
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", read_only_connect)
    result = operation(path, "synthetic")
    assert result and calls
    assert before == (hashlib.sha256(path.read_bytes()).digest(), path.stat().st_mtime_ns,
                      sorted(item.name for item in local_tmp.iterdir()))
    with closing(original_connect(path)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 7


def test_readonly_uri_preserves_literal_hash_and_percent(local_tmp: Path) -> None:
    path = local_tmp / "catalog # 50%.sqlite3"
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("CREATE TABLE sample (value TEXT)")
        connection.execute("INSERT INTO sample VALUES ('synthetic')")
    before = sorted(item.name for item in local_tmp.iterdir())
    connection = connect_readonly(path)
    try:
        assert connection.execute("SELECT value FROM sample").fetchone()[0] == "synthetic"
    finally:
        connection.close()
    assert sorted(item.name for item in local_tmp.iterdir()) == before


def test_readonly_connection_also_disallows_temp_writes(local_tmp: Path) -> None:
    path = local_tmp / "sample.sqlite3"
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("CREATE TABLE sample (value TEXT)")
    connection = connect_readonly(path)
    try:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            connection.execute("CREATE TEMP TABLE unexpected (value TEXT)")
    finally:
        connection.close()
