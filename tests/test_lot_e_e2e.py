from __future__ import annotations

import hashlib
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pokemind.capabilities import capability_status
from pokemind.database import SCHEMA_VERSION, import_seed
from pokemind.knowledge import knowledge_audit
from pokemind.recovery import create_backup, restore_verify, verify_backup
from pokemind.scheduler import scheduler_preview
from pokemind.updates import run_public_update, update_status
from pokemind.visual_coach import vision_backend_status


ROOT = Path(__file__).resolve().parents[1]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_lot_e_offline_recovery_and_readiness_path_is_end_to_end(local_tmp: Path) -> None:
    db_path = local_tmp / "PokeMind-épreuve.sqlite3"
    seeded = import_seed(ROOT, db_path)
    assert seeded["documents_total"] == 4
    before = _sha(db_path)

    audit = knowledge_audit(db_path)
    capabilities = capability_status(db_path)
    updater = run_public_update(
        db_path, ROOT / "knowledge" / "curated" / "official_rules_2026.json",
        mode="auto", deep_local_time="19:30", dry_run=True,
        now_utc=datetime(2026, 10, 13, 23, 30, tzinfo=timezone.utc),
    )
    updater_status = update_status(
        db_path, deep_local_time="19:30",
        now_utc=datetime(2026, 10, 13, 23, 30, tzinfo=timezone.utc),
    )
    assert _sha(db_path) == before
    assert audit["offline"] is True and audit["network_used"] is False
    assert capabilities["network_used"] is False
    assert updater["network_used"] is False and updater["writes"] == 0
    assert updater_status["offline"] is True and updater_status["read_only"] is True

    destination = local_tmp / "sauvegardes-épreuve"
    created = create_backup(
        db_path, destination, apply=True, confirm_owner=True, min_free_bytes=0,
    )
    backup = destination / created["backup_file"]
    assert verify_backup(backup)["state"] == "verified"
    restored = restore_verify(backup, migrate_clone=True, work_directory=local_tmp)
    assert restored["clone_schema_version"] == SCHEMA_VERSION
    assert restored["backup_unchanged"] is True

    scheduler = scheduler_preview(
        ROOT, action="install", daily_time="08:15", deep_time="19:30",
        dry_run=True, windows_timezone="Eastern Standard Time",
    )
    vision = vision_backend_status()
    assert scheduler["system_changed"] is False and scheduler["scheduler_contacted"] is False
    assert scheduler["activation_gate"] == "SCHEDULER_ACTIVATION_DISABLED_IN_LOT_D"
    assert vision["operational"] is False and vision["network_used"] is False


def test_sqlite_runtime_has_integrity_foreign_keys_and_fts5(local_tmp: Path) -> None:
    connection = sqlite3.connect(local_tmp / "runtime.sqlite3")
    try:
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("CREATE VIRTUAL TABLE smoke_fts USING fts5(content)")
        connection.execute("INSERT INTO smoke_fts(content) VALUES('énergie synthétique')")
        assert connection.execute("SELECT COUNT(*) FROM smoke_fts WHERE smoke_fts MATCH 'energie'").fetchone()[0] == 1
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    finally:
        connection.close()


def test_powershell_launcher_parses_without_execution_when_available() -> None:
    executable = shutil.which("pwsh") or shutil.which("powershell")
    if executable is None:
        pytest.skip("PowerShell absent; smoke couvert par la matrice Windows CI.")
    script = ROOT / "scripts" / "pokemind_update.ps1"
    command = (
        "$tokens=$null; $errors=$null; "
        f"[System.Management.Automation.Language.Parser]::ParseFile('{script}',[ref]$tokens,[ref]$errors) | Out-Null; "
        "if ($errors.Count -gt 0) { $errors | ForEach-Object { $_.Message }; exit 1 }"
    )
    completed = subprocess.run(
        [executable, "-NoProfile", "-NonInteractive", "-Command", command],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
