"""Unattended update preparation must never select or commission an owner DB."""
import hashlib
import json
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from pokemind.cli import main
from pokemind.database import connect_writable, initialize_schema
from pokemind.public_campaign import require_public_database
from pokemind.scheduler import scheduler_preview


def _workspace(root):
    path = root / "data/local/public-campaigns/lot-i-synthetic"
    path.mkdir(parents=True)
    (path / "PUBLIC_ONLY.json").write_text(json.dumps({
        "kind": "pokemind_public_only_lot_i", "campaign": "synthetic", "schema_version": 1,
    }), encoding="utf-8")
    return path / "public.sqlite3"


@pytest.mark.parametrize("explicit", [False, True])
def test_public_update_rejects_owner_selection_before_database_metadata(
    local_tmp, monkeypatch, capsys, explicit,
):
    monkeypatch.setattr("pokemind.cli.find_project_root", lambda: local_tmp)
    def forbidden(*args, **kwargs):
        raise AssertionError("No default/owner database metadata may be selected")
    monkeypatch.setattr("pokemind.cli._db_for", forbidden)
    command = ["knowledge", "update", "--public-only", "--dry-run", "--json"]
    if explicit: command += ["--db", str(local_tmp / "owner.sqlite3")]
    assert main(command) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["error_code"] == ("PUBLIC_UPDATE_WORKSPACE_REQUIRED" if explicit
                                    else "PUBLIC_UPDATE_EXPLICIT_DATABASE_REQUIRED")
    assert not list(local_tmp.iterdir())


def test_marker_does_not_authorize_owner_rows_or_any_update(local_tmp, monkeypatch, capsys):
    db = _workspace(local_tmp)
    with closing(connect_writable(db)) as connection:
        initialize_schema(connection)
        connection.execute("INSERT INTO observed_decks VALUES ('synthetic', 'observé partiellement', 'fixture', 'fixture')")
        connection.commit()
    before = hashlib.sha256(db.read_bytes()).digest()
    monkeypatch.setattr("pokemind.cli.find_project_root", lambda: local_tmp)
    def forbidden(*args, **kwargs): raise AssertionError("Updater must not start")
    monkeypatch.setattr("pokemind.cli.run_public_update", forbidden)
    assert main(["knowledge", "update", "--public-only", "--apply", "--confirm-owner",
                 "--db", str(db), "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["error_code"] == "PUBLIC_CAMPAIGN_OWNER_OR_UNKNOWN_DATA_BLOCKED"
    assert hashlib.sha256(db.read_bytes()).digest() == before


def test_empty_attested_workspace_preview_creates_no_database(local_tmp, monkeypatch, capsys):
    db = _workspace(local_tmp)
    monkeypatch.setattr("pokemind.cli.find_project_root", lambda: local_tmp)
    assert main(["knowledge", "update", "--public-only", "--dry-run", "--db", str(db), "--json"]) == 0
    assert not json.loads(capsys.readouterr().out)["network_used"]
    assert not db.exists()


def test_unattested_workspace_is_rejected_without_sqlite(local_tmp, monkeypatch):
    db = _workspace(local_tmp)
    (db.parent / "PUBLIC_ONLY.json").write_text("{}", encoding="utf-8")
    def forbidden(*args, **kwargs): raise AssertionError("SQLite must not open")
    monkeypatch.setattr(sqlite3, "connect", forbidden)
    with pytest.raises(ValueError, match="WORKSPACE_UNATTESTED"):
        require_public_database(local_tmp, db)


def test_aliased_database_is_rejected_without_opening_it(local_tmp, monkeypatch):
    db = _workspace(local_tmp)
    source = local_tmp / "synthetic-source.bin"
    source.write_bytes(b"synthetic, never opened as SQLite")
    os.link(source, db)
    def forbidden(*args, **kwargs): raise AssertionError("SQLite must not open")
    monkeypatch.setattr(sqlite3, "connect", forbidden)
    with pytest.raises(ValueError, match="DATABASE_ALIAS_BLOCKED"):
        require_public_database(local_tmp, db)


def test_scheduler_and_cadence_previews_never_select_default_db(local_tmp, monkeypatch, capsys):
    monkeypatch.setattr("pokemind.cli.find_project_root", lambda: local_tmp)
    def forbidden(*args, **kwargs): raise AssertionError("No DB or process allowed")
    monkeypatch.setattr("pokemind.cli._db_for", forbidden)
    monkeypatch.setattr("subprocess.run", forbidden)
    assert main(["knowledge", "scheduler", "--action", "install", "--daily-time", "08:15",
                 "--deep-time", "19:30", "--windows-timezone", "Eastern Standard Time",
                 "--dry-run", "--json"]) == 0
    preview = json.loads(capsys.readouterr().out)
    assert all('-Database "<OWNER_PUBLIC_DATABASE_REQUIRED>"' in item["arguments"] for item in preview["manifests"])
    assert preview["configuration"]["database_selection"] == "OWNER_SELECTION_REQUIRED"
    assert not preview["scheduler_contacted"]
    assert main(["knowledge", "cadence", "--start-utc", "2026-10-22T00:00:00Z",
                 "--daily-time", "08:15", "--deep-time", "19:30", "--json"]) == 0
    assert not json.loads(capsys.readouterr().out)["scheduler_contacted"]


def test_declared_public_database_and_deep_time_are_in_both_manifests(local_tmp):
    db = local_tmp / "data/local/public-campaigns/lot-i-synthetic/public.sqlite3"
    result = scheduler_preview(local_tmp, daily_time="08:15", deep_time="19:30",
                               windows_timezone="Eastern Standard Time", public_database=db)
    assert all(f'-Database "{db}"' in item["arguments"] for item in result["manifests"])
    assert "-DeepTime 19:30" in result["manifests"][1]["arguments"]
    assert result["configuration"]["database_selection"] == "DECLARED_NOT_ATTESTED"
    assert not list(local_tmp.iterdir())


def test_powershell_launcher_requires_explicit_public_only_database():
    script = (Path(__file__).parents[1] / "scripts/pokemind_update.ps1").read_text(encoding="utf-8-sig")
    assert "[Parameter(Mandatory = $true)]\n    [ValidateNotNullOrEmpty()]\n    [string]$Database" in script
    assert "'--public-only', '--json', '--db', $Database" in script
