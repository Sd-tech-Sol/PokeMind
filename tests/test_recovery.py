from __future__ import annotations

import json
import os
import shutil
import sqlite3
import socket
from collections import namedtuple
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pokemind.cli import main
from pokemind.database import SCHEMA_VERSION, connect_writable, initialize_schema
import pokemind.recovery as recovery_module
from pokemind.recovery import (
    RecoveryError,
    apply_retention,
    backup_plan,
    backup_status,
    create_backup,
    restore_backup,
    restore_plan,
    restore_verify,
    retention_plan,
    verify_backup,
)


def _database(path: Path, *, schema_version: int = SCHEMA_VERSION) -> Path:
    connection = connect_writable(path)
    initialize_schema(connection)
    connection.execute(
        "INSERT INTO metadata(key,value) VALUES('recovery_sentinel','preserved') "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value"
    )
    connection.execute(f"PRAGMA user_version={schema_version}")
    connection.commit()
    connection.close()
    return path


def _created(db_path: Path, destination: Path, *, now: datetime | None = None) -> tuple[dict, Path]:
    result = create_backup(
        db_path, destination, apply=True, confirm_owner=True,
        min_free_bytes=0, now=now,
    )
    return result, destination / result["backup_file"]


def test_backup_plan_create_status_and_verify_are_coherent(local_tmp: Path) -> None:
    source = _database(local_tmp / "source.sqlite3")
    destination = local_tmp / "backups"
    plan = backup_plan(source, destination, min_free_bytes=0)
    assert plan["mode"] == "dry_run" and plan["method"] == "sqlite3.backup"
    assert not destination.exists()

    created, backup = _created(source, destination)
    assert created["state"] == "verified" and backup.is_file()
    manifest = json.loads((destination / created["manifest_file"]).read_text(encoding="utf-8"))
    assert manifest["state"] == "verified" and manifest["verified_at"]
    assert "source.sqlite3" not in json.dumps(manifest)
    assert manifest["cloud_uploaded"] is False

    verified = verify_backup(backup)
    assert verified["checks"]["integrity"] == "ok"
    assert verified["checks"]["foreign_key_violations"] == 0
    status = backup_status(destination)
    assert status["counts"] == {"verified": 1}


def test_backup_requires_owner_confirmation_and_rejects_insufficient_disk(local_tmp: Path, monkeypatch) -> None:
    source = _database(local_tmp / "source.sqlite3")
    with pytest.raises(RecoveryError, match="OWNER_CONFIRMATION_REQUIRED"):
        create_backup(source, local_tmp / "backups", apply=True)
    usage = namedtuple("usage", "total used free")
    monkeypatch.setattr(shutil, "disk_usage", lambda _: usage(100, 99, 1))
    plan = backup_plan(source, local_tmp / "backups", min_free_bytes=100)
    assert plan["would_write"] is False and plan["reason_code"] == "INSUFFICIENT_DISK_SPACE"
    with pytest.raises(RecoveryError, match="INSUFFICIENT_DISK_SPACE"):
        create_backup(
            source, local_tmp / "backups", apply=True, confirm_owner=True,
            min_free_bytes=100,
        )


def test_corrupted_backup_is_rejected_without_damaging_verified_source(local_tmp: Path) -> None:
    source = _database(local_tmp / "source.sqlite3")
    created, backup = _created(source, local_tmp / "backups")
    corrupt = backup.with_name("corrupt.sqlite3")
    shutil.copy2(backup, corrupt)
    manifest = json.loads((local_tmp / "backups" / created["manifest_file"]).read_text(encoding="utf-8"))
    manifest["backup_file"] = corrupt.name
    (corrupt.with_name(f"{corrupt.name}.manifest.json")).write_text(json.dumps(manifest), encoding="utf-8")
    with corrupt.open("r+b") as handle:
        handle.seek(max(0, corrupt.stat().st_size // 2))
        handle.write(b"PARTIAL-CORRUPTION")
    with pytest.raises(RecoveryError, match="CHECKSUM_MISMATCH"):
        verify_backup(corrupt)
    assert verify_backup(backup)["state"] == "verified"


def test_restore_plan_verify_old_schema_and_atomic_apply_with_quarantine(local_tmp: Path) -> None:
    source = _database(local_tmp / "old.sqlite3", schema_version=7)
    _, backup = _created(source, local_tmp / "backups")
    target = local_tmp / "restored.sqlite3"
    target.write_bytes(b"synthetic-corruption")

    plan = restore_plan(backup, target, migrate_clone=True, min_free_bytes=0)
    assert plan["target"]["would_quarantine_existing"] is False
    checked = restore_verify(backup, migrate_clone=True, work_directory=local_tmp)
    assert checked["source_schema_version"] == 7
    assert checked["clone_schema_version"] == SCHEMA_VERSION
    assert checked["backup_unchanged"] is True and checked["temporary_clone_removed"] is True

    with pytest.raises(RecoveryError, match="RESTORE_EXISTING_TARGET_BLOCKED"):
        restore_backup(backup, target, apply=True, confirm_owner=True, min_free_bytes=0)
    assert target.read_bytes() == b"synthetic-corruption"
    target = local_tmp / "new-clone.sqlite3"
    restored = restore_backup(
        backup, target, apply=True, confirm_owner=True,
        migrate_clone=True, min_free_bytes=0,
    )
    assert restored["state"] == "verified" and restored["schema_version"] == SCHEMA_VERSION
    assert restored["quarantine_file"] is None
    assert restored["publication"] == "new_clone_no_overwrite"
    connection = sqlite3.connect(target)
    assert connection.execute("SELECT value FROM metadata WHERE key='recovery_sentinel'").fetchone()[0] == "preserved"
    connection.close()
    assert verify_backup(backup)["state"] == "verified"


def test_restore_refuses_same_target_and_symlinks_when_supported(local_tmp: Path) -> None:
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    with pytest.raises(RecoveryError, match="EQUALS_BACKUP"):
        restore_plan(backup, backup, min_free_bytes=0)
    link = local_tmp / "linked.sqlite3"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("Création de lien symbolique non permise sur cette machine Windows.")
    with pytest.raises(RecoveryError, match="TARGET_NOT_SAFE"):
        restore_plan(backup, link, min_free_bytes=0)


def test_live_process_stale_lock_is_never_stolen(local_tmp: Path) -> None:
    source = _database(local_tmp / "source.sqlite3")
    destination = local_tmp / "backups"
    destination.mkdir()
    (destination / ".pokemind-backup.lock").write_text(json.dumps({
        "kind": "pokemind-recovery-lock",
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        "created_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
    }), encoding="utf-8")
    with pytest.raises(RecoveryError, match="ALREADY_RUNNING"):
        create_backup(
            source, destination, apply=True, confirm_owner=True,
            min_free_bytes=0,
        )
    assert not list(destination.glob("*.sqlite3"))


def test_retention_is_preview_first_and_applies_only_matching_fixture_plan(local_tmp: Path) -> None:
    source = _database(local_tmp / "source.sqlite3")
    destination = local_tmp / "backups"
    old = datetime(2026, 1, 1, tzinfo=timezone.utc)
    recent = datetime(2026, 10, 12, tzinfo=timezone.utc)
    first, first_path = _created(source, destination, now=old)
    second, second_path = _created(source, destination, now=recent)
    assert first_path.exists() and second_path.exists()

    plan = retention_plan(
        destination, local_root=local_tmp, keep_last=1, max_age_days=30,
        max_total_bytes=10**12, now=datetime(2026, 10, 13, tzinfo=timezone.utc),
    )
    assert plan["mode"] == "dry_run" and plan["candidate_count"] == 1
    assert first_path.exists()
    with pytest.raises(RecoveryError, match="PLAN_CHANGED"):
        apply_retention(
            destination, local_root=local_tmp, plan_sha256="wrong",
            apply=True, confirm_owner=True, keep_last=1, max_age_days=30,
            max_total_bytes=10**12, now=datetime(2026, 10, 13, tzinfo=timezone.utc),
        )
    with pytest.raises(RecoveryError, match="RETENTION_EXTERNAL_EXCLUSION_UNPROVEN"):
        apply_retention(
            destination, local_root=local_tmp, plan_sha256=plan["plan_sha256"],
            apply=True, confirm_owner=True, keep_last=1, max_age_days=30,
            max_total_bytes=10**12, now=datetime(2026, 10, 13, tzinfo=timezone.utc),
        )
    assert first_path.exists() and second_path.exists()
    assert (destination / first["manifest_file"]).exists()


def test_backup_status_marks_interrupted_work_unknown(local_tmp: Path) -> None:
    destination = local_tmp / "backups"
    destination.mkdir()
    (destination / ".synthetic.sqlite3.inprogress").write_bytes(b"partial")
    status = backup_status(destination)
    assert status["counts"]["in_progress"] == 1


def test_backup_crash_keeps_failed_work_state_without_false_success(local_tmp: Path, monkeypatch) -> None:
    source = _database(local_tmp / "source.sqlite3")
    destination = local_tmp / "backups"

    def crash(_source: Path, target: Path, *, max_duration_seconds: float) -> None:
        del max_duration_seconds
        target.write_bytes(b"partial synthetic backup")
        raise RecoveryError("SYNTHETIC_CRASH")

    monkeypatch.setattr(recovery_module, "_copy_database", crash)
    with pytest.raises(RecoveryError, match="SYNTHETIC_CRASH"):
        create_backup(
            source, destination, apply=True, confirm_owner=True,
            min_free_bytes=0,
        )
    assert not list(destination.glob("*.manifest.json"))
    assert not list(destination.glob("pokemind-*.sqlite3"))
    assert backup_status(destination)["counts"]["in_progress"] == 1
    assert next(destination.glob("*.inprogress")).read_bytes() == b"partial synthetic backup"
    assert (destination / ".pokemind-backup.lock").is_file()


def test_restore_publish_failure_rolls_quarantine_back_and_preserves_backup(local_tmp: Path, monkeypatch) -> None:
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    target = local_tmp / "target.sqlite3"
    original = b"existing-target-before-restore"
    target.write_bytes(original)
    temporary = _database(local_tmp / "candidate.restore-inprogress")
    checks = recovery_module._sqlite_checks(temporary)
    real_link = os.link

    def fail_publish(src, dst):
        if str(src).endswith(".restore-inprogress") and Path(dst) == target:
            raise OSError("C:\\Synthetic\\private-name token=hidden")
        return real_link(src, dst)

    monkeypatch.setattr(recovery_module.os, "link", fail_publish)
    with pytest.raises(RecoveryError, match="RESTORE_APPLY_FAILED"):
        recovery_module._publish_isolated_restore(
            temporary, target, checks, _allow_existing_fixture=True,
        )
    assert target.read_bytes() == original
    assert verify_backup(backup)["state"] == "verified"


def test_restore_source_race_before_publication_preserves_target_byte_for_byte(
    local_tmp: Path, monkeypatch
) -> None:
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    target = local_tmp / "target.sqlite3"
    manifest = backup.with_name(f"{backup.name}.manifest.json")
    real_checks = recovery_module._sqlite_checks
    mutated = False

    def mutate_manifest_after_clone(path: Path) -> dict:
        nonlocal mutated
        result = real_checks(path)
        if str(path).endswith(".restore-inprogress") and not mutated:
            manifest.write_bytes(manifest.read_bytes() + b" ")
            mutated = True
        return result

    monkeypatch.setattr(recovery_module, "_sqlite_checks", mutate_manifest_after_clone)
    with pytest.raises(RecoveryError, match="BACKUP_SOURCE_CHANGED_DURING_RESTORE"):
        restore_backup(
            backup, target, apply=True, confirm_owner=True, min_free_bytes=0,
        )
    assert not target.exists()


def test_restore_backup_content_race_during_copy_never_publishes_target(
    local_tmp: Path, monkeypatch
) -> None:
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    target = local_tmp / "target.sqlite3"
    real_copy = recovery_module._copy_database

    def mutate_after_copy(source_path: Path, target_path: Path, *, max_duration_seconds: float) -> None:
        real_copy(source_path, target_path, max_duration_seconds=max_duration_seconds)
        with source_path.open("ab") as handle:
            handle.write(b"synthetic-race")

    monkeypatch.setattr(recovery_module, "_copy_database", mutate_after_copy)
    with pytest.raises(RecoveryError, match="BACKUP_SOURCE_CHANGED_DURING_RESTORE"):
        restore_backup(
            backup, target, apply=True, confirm_owner=True, min_free_bytes=0,
        )
    assert not target.exists()
    assert backup.exists()


def test_restore_refuses_wal_sidecars_and_active_writer_without_touching_target(
    local_tmp: Path,
) -> None:
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    target = _database(local_tmp / "target.sqlite3")
    writer = sqlite3.connect(target)
    try:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("CREATE TABLE live_writer(value TEXT)")
        writer.commit()
        assert Path(f"{target}-wal").exists()
        before = target.read_bytes()
        with pytest.raises(RecoveryError, match="TARGET_IN_USE_OR_WAL_ACTIVE"):
            restore_backup(
                backup, target, apply=True, confirm_owner=True, min_free_bytes=0,
            )
        assert target.read_bytes() == before
    finally:
        writer.close()


def test_restore_refuses_active_delete_journal_writer(local_tmp: Path) -> None:
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    target = _database(local_tmp / "target.sqlite3")
    writer = sqlite3.connect(target, timeout=0)
    try:
        writer.execute("PRAGMA journal_mode=DELETE")
        writer.execute("BEGIN IMMEDIATE")
        with pytest.raises(RecoveryError, match="RESTORE_EXISTING_TARGET_BLOCKED"):
            restore_backup(
                backup, target, apply=True, confirm_owner=True, min_free_bytes=0,
            )
    finally:
        writer.rollback()
        writer.close()


def test_retention_rejects_content_change_and_manifest_permission_failure(
    local_tmp: Path, monkeypatch
) -> None:
    source = _database(local_tmp / "source.sqlite3")
    destination = local_tmp / "backups"
    old = datetime(2026, 1, 1, tzinfo=timezone.utc)
    first, first_path = _created(source, destination, now=old)
    _created(source, destination, now=datetime(2026, 10, 12, tzinfo=timezone.utc))
    policy = {
        "keep_last": 1, "max_age_days": 30, "max_total_bytes": 10**12,
        "now": datetime(2026, 10, 13, tzinfo=timezone.utc),
    }
    plan = retention_plan(destination, local_root=local_tmp, **policy)
    connection = sqlite3.connect(first_path)
    connection.execute("INSERT INTO metadata(key,value) VALUES('changed_after_plan','yes')")
    connection.commit()
    connection.close()
    manifest_path = destination / first["manifest_file"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sha256"] = recovery_module._sha256_file(first_path)
    manifest["size_bytes"] = first_path.stat().st_size
    manifest_path.write_bytes(recovery_module._canonical(manifest))
    with pytest.raises(RecoveryError, match="RETENTION_PLAN_CHANGED"):
        apply_retention(
            destination, local_root=local_tmp, plan_sha256=plan["plan_sha256"],
            apply=True, confirm_owner=True, **policy,
        )
    assert first_path.exists() and manifest_path.exists()

    original_read_text = Path.read_text

    def denied(path: Path, *args, **kwargs):
        if path == manifest_path:
            raise PermissionError("synthetic denial")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", denied)
    denied_plan = retention_plan(destination, local_root=local_tmp, **policy)
    assert denied_plan["rejected_backup_count"] >= 1
    assert all(item["name"] != first_path.name for item in denied_plan["candidates"])


def test_retention_pair_staging_rolls_back_on_partial_move(local_tmp: Path, monkeypatch) -> None:
    source = _database(local_tmp / "source.sqlite3")
    destination = local_tmp / "backups"
    first, first_path = _created(source, destination, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    _created(source, destination, now=datetime(2026, 10, 12, tzinfo=timezone.utc))
    policy = {
        "keep_last": 1, "max_age_days": 30, "max_total_bytes": 10**12,
        "now": datetime(2026, 10, 13, tzinfo=timezone.utc),
    }
    plan = retention_plan(destination, local_root=local_tmp, **policy)
    manifest_path = destination / first["manifest_file"]
    real_replace = os.replace

    def fail_manifest_stage(src, dst):
        if Path(src) == manifest_path and ".retention-" in str(dst):
            raise OSError("synthetic pair failure")
        return real_replace(src, dst)

    monkeypatch.setattr(recovery_module.os, "replace", fail_manifest_stage)
    with pytest.raises(RecoveryError, match="RETENTION_EXTERNAL_EXCLUSION_UNPROVEN"):
        apply_retention(
            destination, local_root=local_tmp, plan_sha256=plan["plan_sha256"],
            apply=True, confirm_owner=True, **policy,
        )
    assert first_path.exists() and manifest_path.exists()


def test_retention_corrupt_backup_never_satisfies_keep_last(local_tmp: Path) -> None:
    source = _database(local_tmp / "source.sqlite3")
    destination = local_tmp / "backups"
    _, healthy = _created(source, destination, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    _, corrupt = _created(source, destination, now=datetime(2026, 10, 12, tzinfo=timezone.utc))
    with corrupt.open("r+b") as handle:
        handle.seek(100)
        handle.write(b"CORRUPT")
    plan = retention_plan(
        destination, keep_last=1, max_age_days=30, max_total_bytes=10**12,
        now=datetime(2026, 10, 13, tzinfo=timezone.utc),
    )
    assert plan["verified_backup_count"] == 1
    assert plan["rejected_backup_count"] == 1
    assert plan["candidate_count"] == 0
    assert healthy.exists() and corrupt.exists()


def test_cli_backup_and_restore_e2e_on_synthetic_database(local_tmp: Path, capsys) -> None:
    source = _database(local_tmp / "cli-source.sqlite3")
    destination = local_tmp / "cli-backups"
    assert main([
        "backup", "plan", "--db", str(source), "--destination", str(destination),
        "--min-free-bytes", "0", "--json",
    ]) == 0
    planned = json.loads(capsys.readouterr().out)
    assert planned["ok"] is True and planned["mode"] == "dry_run" and not destination.exists()
    assert main([
        "backup", "create", "--db", str(source), "--destination", str(destination),
        "--min-free-bytes", "0", "--apply", "--confirm-owner", "--json",
    ]) == 0
    created = json.loads(capsys.readouterr().out)
    backup = destination / created["backup_file"]
    target = local_tmp / "cli-restored.sqlite3"
    assert main([
        "restore", "verify", "--backup", str(backup), "--db", str(target),
        "--migrate-clone", "--min-free-bytes", "0", "--json",
    ]) == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified["state"] == "verified" and not target.exists()
    assert main([
        "restore", "apply", "--backup", str(backup), "--db", str(target),
        "--migrate-clone", "--min-free-bytes", "0", "--apply", "--confirm-owner", "--json",
    ]) == 0
    restored = json.loads(capsys.readouterr().out)
    assert restored["state"] == "verified" and target.is_file()
