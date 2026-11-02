"""H0 public safety tests; every file is synthetic, subprocesses never see owner DB."""
import json
import os
import sqlite3
import subprocess
import sys

import pytest

from pokemind import recovery
from test_recovery import _database, _created


@pytest.mark.parametrize("mode", ["idle", "writer", "wal"])
def test_external_process_existing_target_is_never_replaced(local_tmp, mode):
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    target = _database(local_tmp / "target.sqlite3")
    script = """import sqlite3,sys
c=sqlite3.connect(sys.argv[1])
if sys.argv[2]=='wal': c.execute('PRAGMA journal_mode=WAL')
if sys.argv[2]=='writer': c.execute('BEGIN IMMEDIATE')
print('READY',flush=True)
sys.stdin.readline()
c.rollback(); c.close()
"""
    child = subprocess.Popen([sys.executable, "-c", script, str(target), mode],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline().strip() == "READY"
        before = target.read_bytes()
        with pytest.raises(recovery.RecoveryError, match="RESTORE_EXISTING_TARGET_BLOCKED|TARGET_IN_USE_OR_WAL_ACTIVE"):
            recovery.restore_backup(backup, target, apply=True, confirm_owner=True)
        assert target.read_bytes() == before
    finally:
        child.communicate("stop\n", timeout=10)
    assert child.returncode == 0


def test_external_target_creation_during_publication_is_preserved(local_tmp, monkeypatch):
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    target = local_tmp / "new.sqlite3"
    link = os.link

    def collision(src, dst):
        if dst == target:
            subprocess.run([sys.executable, "-c", "from pathlib import Path; import sys; Path(sys.argv[1]).write_bytes(b'external synthetic')", str(target)], check=True, timeout=10)
        return link(src, dst)

    monkeypatch.setattr(recovery.os, "link", collision)
    with pytest.raises(recovery.RecoveryError, match="RESTORE_APPLY_FAILED"):
        recovery.restore_backup(backup, target, apply=True, confirm_owner=True)
    assert target.read_bytes() == b"external synthetic"


def test_backup_alias_is_not_an_offline_attestation(local_tmp):
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    alias = local_tmp / "alias.sqlite3"
    os.link(backup, alias)
    with pytest.raises(recovery.RecoveryError, match="HARDLINK_ALIAS_BLOCKED"):
        recovery.verify_backup(backup)


def test_readonly_inventory_does_not_require_write_permission(local_tmp, monkeypatch):
    local_tmp.joinpath(".retention-old").mkdir()
    local_tmp.joinpath("unattested.sqlite3").write_bytes(b"synthetic residue")
    monkeypatch.setattr(recovery.os, "access", lambda *args: False)
    report = recovery.backup_status(local_tmp)
    assert report["residues"]["counts"] == {"legacy_retention_staging": 1, "unattested_database": 1}
    assert not report["residues"]["automatic_repair"]


def test_manifest_collision_preserves_external_bytes_and_orphan_is_visible(local_tmp, monkeypatch):
    source = _database(local_tmp / "source.sqlite3")
    destination = local_tmp / "backups"
    link = os.link

    def collision(src, dst):
        if str(dst).endswith(".manifest.json"):
            dst.write_bytes(b"external manifest")
        return link(src, dst)

    monkeypatch.setattr(recovery.os, "link", collision)
    with pytest.raises(recovery.RecoveryError, match="BACKUP_CREATE_FAILED"):
        _created(source, destination)
    assert next(destination.glob("*.manifest.json")).read_bytes() == b"external manifest"
    assert recovery.backup_status(destination)["counts"] == {"unknown": 1, "in_progress": 1}


def test_purge_has_no_mutating_bypass_even_with_valid_token(local_tmp):
    plan = recovery.retention_plan(local_tmp)
    before = sorted(p.name for p in local_tmp.iterdir())
    assert not plan["apply_allowed"]
    with pytest.raises(recovery.RecoveryError, match="EXTERNAL_EXCLUSION_UNPROVEN"):
        recovery.apply_retention(local_tmp, plan_sha256=plan["plan_sha256"], apply=True, confirm_owner=True)
    assert sorted(p.name for p in local_tmp.iterdir()) == before


def test_disk_flush_failure_never_returns_verified_success(local_tmp, monkeypatch):
    source = _database(local_tmp / "source.sqlite3")
    def denied(_):
        raise OSError("synthetic disk full")
    monkeypatch.setattr(recovery.os, "fsync", denied)
    with pytest.raises((OSError, recovery.RecoveryError)):
        _created(source, local_tmp / "backups")
    assert not list((local_tmp / "backups").glob("*.manifest.json"))


def test_replaced_cooperative_lock_is_not_deleted(local_tmp):
    path = local_tmp / "lock"
    with pytest.raises(recovery.RecoveryError, match="LOCK_CLEANUP_REQUIRED"):
        with recovery._ProcessLock(path):
            path.write_text(json.dumps({"token": "external replacement"}), encoding="utf-8")
    assert json.loads(path.read_text(encoding="utf-8"))["token"] == "external replacement"
