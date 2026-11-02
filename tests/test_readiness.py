from __future__ import annotations

import json
from pathlib import Path

from pokemind.cli import main
from pokemind.database import SCHEMA_VERSION, connect_writable, initialize_schema
from pokemind.readiness import v1_readiness
from pokemind.recovery import create_backup


def _database(path: Path) -> Path:
    connection = connect_writable(path)
    initialize_schema(connection)
    connection.commit()
    connection.close()
    return path


def test_v1_readiness_missing_database_is_offline_private_safe(local_tmp: Path) -> None:
    report = v1_readiness(local_tmp / "missing.sqlite3")
    assert report["status"] == "NOT_RELEASE_READY"
    assert report["offline"] is report["read_only"] is True
    assert report["network_used"] is False
    assert report["private_values_disclosed"] is False
    assert report["database"]["exists"] is False
    assert "DATABASE_MISSING_OR_MIGRATION_REQUIRED" in report["blockers"]
    assert report["completion"]["metagame"]["zero_safe"] is True


def test_v1_readiness_reports_verified_backup_without_names_or_paths(local_tmp: Path) -> None:
    db_path = _database(local_tmp / "brain.sqlite3")
    destination = local_tmp / "backups"
    created = create_backup(
        db_path, destination, apply=True, confirm_owner=True, min_free_bytes=0,
    )
    report = v1_readiness(db_path, backup_directory=destination)
    serialized = json.dumps(report)
    assert report["database"]["schema_version"] == SCHEMA_VERSION
    assert report["backups"]["verified_count"] == 1
    assert report["backups"]["status"] == "VERIFIED_BACKUP_AVAILABLE"
    assert created["backup_file"] not in serialized
    assert str(local_tmp) not in serialized
    assert report["owner"]["private_values_disclosed"] is False
    assert report["completion"]["confirmed_60_card_versions"] == 0


def test_v1_readiness_cli_is_single_json_report(local_tmp: Path, capsys) -> None:
    db_path = _database(local_tmp / "cli.sqlite3")
    assert main(["v1", "readiness", "--db", str(db_path), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["ok"] is True and report["status"] == "NOT_RELEASE_READY"
    assert report["runtime"]["supported"] is True
    assert report["vision"]["synthetic_pixel_adapter"]["verified_on_synthetic"] is True
    assert report["vision"]["synthetic_pixel_adapter"]["verified_on_user_training"] is False
    assert report["updates"]["scheduler_installed_by_report"] is False
