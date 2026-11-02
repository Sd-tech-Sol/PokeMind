from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pytest

import pokemind.recovery as recovery
from pokemind.cli import main
from test_recovery import _created, _database


@pytest.mark.parametrize("exception", [sqlite3.OperationalError, sqlite3.DatabaseError, PermissionError, OSError, recovery.RecoveryError, RuntimeError])
@pytest.mark.parametrize("existing", [False, True])
def test_every_postpublication_exception_rolls_back_bytes(local_tmp, monkeypatch, exception, existing):
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    manifest = recovery._manifest_for(backup)
    before = (backup.read_bytes(), manifest.read_bytes())
    target = local_tmp / "target.sqlite3"
    original = b"synthetic original byte identity"
    if existing:
        target.write_bytes(original)
    candidate = _database(local_tmp / "candidate.sqlite3")
    checks = recovery._sqlite_checks(candidate)
    real_checks = recovery._sqlite_checks

    def fail_after_publish(path):
        if path == target:
            assert target.read_bytes().startswith(b"SQLite format 3")
            raise exception("C:\\Synthetic\\Private token=fixture-secret")
        return real_checks(path)

    monkeypatch.setattr(recovery, "_sqlite_checks", fail_after_publish)
    with pytest.raises(recovery.RecoveryError) as error:
        recovery._publish_isolated_restore(candidate, target, checks, _allow_existing_fixture=existing)
    assert "fixture-secret" not in str(error.value)
    assert target.read_bytes() == original if existing else not target.exists()
    assert (backup.read_bytes(), manifest.read_bytes()) == before
    assert not list(local_tmp.glob("*.quarantine-*"))


def test_rollback_failure_preserves_original_quarantine(local_tmp, monkeypatch):
    target = local_tmp / "original.sqlite3"
    target.write_bytes(b"original preserved in quarantine")
    candidate = _database(local_tmp / "candidate.sqlite3")
    checks = recovery._sqlite_checks(candidate)
    real_replace = os.replace
    real_checks = recovery._sqlite_checks

    def fail_check(path):
        if path == target:
            raise sqlite3.OperationalError("synthetic postpublication")
        return real_checks(path)

    def fail_rollback(src, dst):
        if ".quarantine-" in Path(src).name:
            raise PermissionError("synthetic rollback denial")
        return real_replace(src, dst)

    monkeypatch.setattr(recovery, "_sqlite_checks", fail_check)
    monkeypatch.setattr(recovery.os, "replace", fail_rollback)
    with pytest.raises(recovery.RecoveryError, match="RESTORE_ROLLBACK_INCOMPLETE"):
        recovery._publish_isolated_restore(candidate, target, checks, _allow_existing_fixture=True)
    quarantines = list(local_tmp.glob("*.quarantine-*"))
    assert len(quarantines) == 1
    assert quarantines[0].read_bytes() == b"original preserved in quarantine"


@pytest.mark.parametrize("writer_mode", ["idle", "transaction", "wal_closed"])
def test_public_existing_target_is_always_blocked(local_tmp, writer_mode):
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    target = _database(local_tmp / "target.sqlite3")
    connection = sqlite3.connect(target)
    if writer_mode == "transaction":
        connection.execute("BEGIN IMMEDIATE")
    if writer_mode == "wal_closed":
        connection.execute("PRAGMA journal_mode=WAL")
        connection.close()
    before = target.read_bytes()
    try:
        with pytest.raises(recovery.RecoveryError, match="RESTORE_EXISTING_TARGET_BLOCKED|TARGET_IN_USE_OR_WAL_ACTIVE"):
            recovery.restore_backup(backup, target, apply=True, confirm_owner=True, min_free_bytes=0)
        assert target.read_bytes() == before
    finally:
        if writer_mode != "wal_closed":
            connection.rollback()
            connection.close()


def test_writer_after_initial_screen_is_preserved(local_tmp, monkeypatch):
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    target = local_tmp / "target.sqlite3"
    real_copy = recovery._copy_database
    writer = None

    def open_writer_after_copy(src, dst, **kwargs):
        nonlocal writer
        real_copy(src, dst, **kwargs)
        writer = sqlite3.connect(target)
        writer.execute("CREATE TABLE concurrent_writer(sentinel TEXT)")
        writer.execute("INSERT INTO concurrent_writer VALUES('must survive')")
        writer.commit()

    monkeypatch.setattr(recovery, "_copy_database", open_writer_after_copy)
    try:
        with pytest.raises(recovery.RecoveryError, match="RESTORE_TARGET_APPEARED"):
            recovery.restore_backup(backup, target, apply=True, confirm_owner=True, min_free_bytes=0)
        assert writer.execute("SELECT sentinel FROM concurrent_writer").fetchone()[0] == "must survive"
    finally:
        if writer:
            writer.close()


def test_target_created_at_publication_is_never_overwritten(local_tmp, monkeypatch):
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    target = local_tmp / "target.sqlite3"
    real_link = os.link

    def collision(src, dst):
        target.write_bytes(b"concurrent external target")
        return real_link(src, dst)

    monkeypatch.setattr(recovery.os, "link", collision)
    with pytest.raises(recovery.RecoveryError, match="RESTORE_APPLY_FAILED"):
        recovery.restore_backup(backup, target, apply=True, confirm_owner=True, min_free_bytes=0)
    assert target.read_bytes() == b"concurrent external target"


@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
def test_sidecar_created_during_prepare_blocks_publication(local_tmp, monkeypatch, suffix):
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    target = local_tmp / "target.sqlite3"
    real_copy = recovery._copy_database

    def create_sidecar(src, dst, **kwargs):
        real_copy(src, dst, **kwargs)
        Path(str(target) + suffix).write_bytes(b"external sidecar")

    monkeypatch.setattr(recovery, "_copy_database", create_sidecar)
    with pytest.raises(recovery.RecoveryError, match="TARGET_IN_USE_OR_WAL_ACTIVE"):
        recovery.restore_backup(backup, target, apply=True, confirm_owner=True, min_free_bytes=0)
    assert not target.exists()
    assert Path(str(target) + suffix).read_bytes() == b"external sidecar"


@pytest.mark.parametrize("hostile", ["../outside.sqlite3", "C:\\Synthetic\\outside.sqlite3", "/outside.sqlite3", [], None])
def test_backup_status_never_follows_manifest_paths(local_tmp, hostile):
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    manifest = recovery._manifest_for(backup)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["backup_file"] = hostile
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    report = recovery.backup_status(backup.parent)
    assert report["counts"] == {"corrupt": 1}
    assert report["total_bytes"] == 0
    assert report["backups"][0]["backup_file"] is None


def test_inventory_limit_blocks_retention_instead_of_hiding_entries(local_tmp):
    directory = local_tmp / "backups"
    directory.mkdir()
    for index in range(1001):
        (directory / f"empty-{index:04}.sqlite3.manifest.json").write_text("{}", encoding="utf-8")
    status = recovery.backup_status(directory)
    assert len(status["backups"]) == 1000 and not status["inventory_complete"]
    plan = recovery.retention_plan(directory)
    with pytest.raises(recovery.RecoveryError, match="RETENTION_INVENTORY_LIMIT_EXCEEDED"):
        recovery.apply_retention(directory, plan_sha256=plan["plan_sha256"], apply=True, confirm_owner=True)


def test_partial_unlink_reports_staged_residue_not_false_removal(local_tmp, monkeypatch):
    source = _database(local_tmp / "source.sqlite3")
    destination = local_tmp / "backups"
    _, older = _created(source, destination, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    _, recent = _created(source, destination, now=datetime(2026, 10, 12, tzinfo=timezone.utc))
    policy = {"keep_last": 1, "max_age_days": 30, "now": datetime(2026, 10, 14, tzinfo=timezone.utc)}
    plan = recovery.retention_plan(destination, **policy)
    real_unlink = Path.unlink

    def fail_manifest_unlink(path, *args, **kwargs):
        if path.parent.name.startswith(".retention-") and path.name.endswith(".manifest.json"):
            raise PermissionError("synthetic deletion denial")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_manifest_unlink)
    with pytest.raises(recovery.RecoveryError, match="RETENTION_EXTERNAL_EXCLUSION_UNPROVEN"):
        recovery.apply_retention(destination, plan_sha256=plan["plan_sha256"], apply=True, confirm_owner=True, **policy)
    assert recent.exists() and recovery.verify_backup(recent)["state"] == "verified"
    assert older.exists() and not list(destination.glob(".retention-*"))
    monkeypatch.setattr(Path, "unlink", real_unlink)


def test_cli_existing_target_is_blocked_and_error_is_redacted(local_tmp, capsys):
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    target = _database(local_tmp / "target.sqlite3")
    before = target.read_bytes()
    assert main(["restore", "apply", "--backup", str(backup), "--db", str(target), "--apply", "--confirm-owner", "--json"]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["error_code"] == "RESTORE_EXISTING_TARGET_BLOCKED"
    assert str(target) not in json.dumps(report)
    assert target.read_bytes() == before


def test_unhashed_backup_wal_is_not_verified_even_when_main_sha_matches(local_tmp):
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    writer = sqlite3.connect(backup)
    try:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        manifest = recovery._manifest_for(backup)
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        payload["sha256"] = recovery._sha256_file(backup)
        manifest.write_bytes(recovery._canonical(payload))
        before = recovery._sha256_file(backup)
        writer.execute("INSERT INTO metadata(key,value) VALUES('unhashed_wal','synthetic')")
        writer.commit()
        assert recovery._sha256_file(backup) == before
        with pytest.raises(recovery.RecoveryError, match="BACKUP_IN_USE_OR_WAL_ACTIVE"):
            recovery.verify_backup(backup)
        assert recovery.backup_status(backup.parent)["counts"] == {"unknown": 1}
    finally:
        writer.close()


def test_backup_from_live_wal_source_is_a_self_contained_delete_snapshot(local_tmp):
    source = _database(local_tmp / "source.sqlite3")
    writer = sqlite3.connect(source)
    try:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("INSERT INTO metadata(key,value) VALUES('live_wal_sentinel','preserved')")
        writer.commit()
        _, backup = _created(source, local_tmp / "backups")
        assert recovery.verify_backup(backup)["state"] == "verified"
        connection = sqlite3.connect(backup)
        try:
            assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
            assert connection.execute("SELECT value FROM metadata WHERE key='live_wal_sentinel'").fetchone()[0] == "preserved"
        finally:
            connection.close()
        assert not Path(str(backup) + "-wal").exists()
    finally:
        writer.close()


@pytest.mark.parametrize("mutate", ["backup", "manifest"])
def test_verification_rechecks_content_and_manifest_after_sqlite_checks(local_tmp, monkeypatch, mutate):
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    manifest = recovery._manifest_for(backup)
    real_checks = recovery._sqlite_checks

    def mutate_during_checks(path):
        result = real_checks(path)
        changed = backup if mutate == "backup" else manifest
        with changed.open("ab") as handle:
            handle.write(b" ")
        return result

    monkeypatch.setattr(recovery, "_sqlite_checks", mutate_during_checks)
    with pytest.raises(recovery.RecoveryError, match="BACKUP_CONTENT_CHANGED_DURING_VERIFICATION"):
        recovery.verify_backup(backup)
