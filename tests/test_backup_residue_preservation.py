"""Targeted Stage 1B repair: exclusively synthetic files under local_tmp."""
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pokemind import recovery
from test_recovery import _created, _database


NOW = datetime(2026, 10, 15, tzinfo=timezone.utc)


def _snapshot(path):
    stat = path.stat()
    return (path.read_bytes(), stat.st_size, stat.st_mtime_ns, stat.st_dev, stat.st_ino)


def _setup(local_tmp):
    source = _database(local_tmp / "synthetic.sqlite3", schema_version=7)
    directory = local_tmp / "backups"
    _, old_backup = _created(source, directory)
    old_manifest = recovery._manifest_for(old_backup)
    failed = directory / ".old.sqlite3.failed"
    failed.write_bytes(b"previous synthetic diagnostic")
    protected = {p: _snapshot(p) for p in (source, old_backup, old_manifest, failed)}
    return source, directory, old_backup, protected


def _unchanged(protected):
    assert {p: _snapshot(p) for p in protected} == protected


@pytest.mark.parametrize("stage", [
    "copy_and_replace", "backup_link", "backup_fsync", "backup_directory_sync",
    "manifest_link", "manifest_fsync", "manifest_directory_sync", "verification",
    "lock_cleanup", "backup_alias_cleanup", "manifest_alias_cleanup",
])
def test_failure_preserves_residues_source_and_old_backups(local_tmp, monkeypatch, stage):
    source, directory, old_backup, protected = _setup(local_tmp)
    before_names = {p.name for p in directory.iterdir()}
    link, fsync, unlink = os.link, os.fsync, Path.unlink
    copy_database = recovery._copy_database
    copied = []
    sync_calls = 0
    deleted = []
    faults = []

    def copy(src, target, **kwargs):
        copied.append(target)
        if stage == "copy_and_replace":
            faults.append(stage)
            target.write_bytes(b"partial synthetic bytes")
            raise recovery.RecoveryError("SYNTHETIC_COPY_FAILED")
        return copy_database(src, target, **kwargs)

    def replace_denied(*args, **kwargs):
        # The historical second fault: diagnostic rename would fail too.
        raise PermissionError("synthetic diagnostic rename denied")

    def link_fault(src, dst):
        is_manifest = str(dst).endswith(".manifest.json")
        if stage == ("manifest_link" if is_manifest else "backup_link"):
            faults.append(stage)
            raise PermissionError("synthetic publication denied")
        return link(src, dst)

    fsync_calls = 0

    def fsync_fault(fd):
        nonlocal fsync_calls
        fsync_calls += 1  # lock, backup, manifest (directory sync mocked below)
        if fsync_calls == {"backup_fsync": 2, "manifest_fsync": 3}.get(stage):
            faults.append(stage)
            raise OSError("synthetic disk full")
        return fsync(fd)

    def sync_fault(path):
        nonlocal sync_calls
        sync_calls += 1
        if sync_calls == {"backup_directory_sync": 1, "manifest_directory_sync": 2}.get(stage):
            faults.append(stage)
            raise OSError("synthetic namespace flush denied")
        # Exercise the existing platform result, without POSIX-only fsync calls
        # affecting the deterministic fault count.
        return False

    def unlink_fault(path, *args, **kwargs):
        if path.parent == directory:
            if ((stage == "lock_cleanup" and path.name.endswith(".lock"))
                    or (stage == "backup_alias_cleanup" and path.name.endswith(".inprogress"))
                    or (stage == "manifest_alias_cleanup" and path.name.endswith(".tmp"))):
                faults.append(stage)
                raise PermissionError("synthetic cleanup denied")
            deleted.append(path.name)
        return unlink(path, *args, **kwargs)

    def verification_fault(*args, **kwargs):
        faults.append(stage)
        raise recovery.RecoveryError("SYNTHETIC_VERIFICATION_FAILED")

    with monkeypatch.context() as patch:
        patch.setattr(recovery, "_copy_database", copy)
        patch.setattr(recovery.os, "replace", replace_denied)
        patch.setattr(recovery.os, "link", link_fault)
        patch.setattr(recovery.os, "fsync", fsync_fault)
        patch.setattr(recovery, "_sync_directory", sync_fault)
        patch.setattr(Path, "unlink", unlink_fault)
        if stage == "verification":
            patch.setattr(recovery, "_verify_backup", verification_fault)
        with pytest.raises(recovery.RecoveryError) as error:
            _created(source, directory)
        assert str(local_tmp) not in str(error.value)
        assert faults == [stage]

    _unchanged(protected)
    new_files = [p for p in directory.iterdir() if p.name not in before_names]
    assert new_files
    work = copied[0]
    if stage != "manifest_alias_cleanup":
        assert work.is_file()
        if stage == "copy_and_replace":
            assert work.read_bytes() == b"partial synthetic bytes"
        else:
            assert recovery._sqlite_checks(work)["schema_version"] == 7
    if stage.startswith("manifest_") or stage in {"verification", "lock_cleanup", "backup_alias_cleanup"}:
        assert list(directory.glob(".*.manifest.json.*.tmp"))
    if "cleanup" not in stage:
        assert deleted == []  # No error path deletes ANY diagnostic file.
        assert (directory / ".pokemind-backup.lock").is_file()
    for path in new_files:
        if path.name.endswith((".sqlite3", ".inprogress", ".failed", ".tmp")):
            with pytest.raises((recovery.RecoveryError, FileNotFoundError)):
                recovery.verify_backup(path)
    status = recovery.backup_status(directory)
    assert status["counts"].get("verified", 0) == 1  # Only the old backup.
    assert recovery.verify_backup(old_backup)["state"] == "verified"


@pytest.mark.parametrize("which", ["backup_alias", "manifest_alias", "final", "extra_link"])
def test_changed_work_ownership_prevents_cleanup_and_public_attestation(local_tmp, monkeypatch, which):
    source, directory, _, protected = _setup(local_tmp)
    verify = recovery._verify_backup
    replaced = []

    def change_after_verification(path, **kwargs):
        evidence = verify(path, **kwargs)
        aliases = kwargs.get("work_aliases")
        if aliases:
            target = {"backup_alias": aliases[0], "manifest_alias": aliases[1], "final": path}.get(which)
            if which == "extra_link":
                target = directory / "external-synthetic-alias"
                os.link(aliases[0], target)
            else:
                external = local_tmp / "external.synthetic"
                external.write_bytes(b"external replacement must survive")
                os.replace(external, target)
            replaced.append((target, _snapshot(target)))
        return evidence

    monkeypatch.setattr(recovery, "_verify_backup", change_after_verification)
    with pytest.raises(recovery.RecoveryError, match="BACKUP_WORK_OWNERSHIP_CHANGED"):
        _created(source, directory)
    assert replaced and _snapshot(replaced[0][0]) == replaced[0][1]
    _unchanged(protected)
    assert recovery.backup_status(directory)["counts"].get("verified", 0) == 1


@pytest.mark.parametrize("occupied", ["backup", "work", "manifest", "manifest_temp"])
def test_occupied_name_is_never_overwritten_or_deleted(local_tmp, monkeypatch, occupied):
    source, directory, _, protected = _setup(local_tmp)
    monkeypatch.setattr(recovery.time, "monotonic_ns", lambda: 0)
    stamp = NOW.strftime("%Y%m%dT%H%M%SZ")
    nonce = hashlib.sha256(f"{stamp}:{os.getpid()}:0".encode()).hexdigest()[:10]
    name = f"pokemind-v7-{stamp}-{nonce}.sqlite3"
    manifest = f"{name}.manifest.json"
    names = {"backup": name, "work": f".{name}.inprogress", "manifest": manifest,
             "manifest_temp": f".{manifest}.{os.getpid()}.tmp"}
    collision = directory / names[occupied]
    collision.write_bytes(b"occupied synthetic bytes")
    failed = directory / f".{name}.failed"
    failed.write_bytes(b"occupied synthetic failure")
    protected.update({p: _snapshot(p) for p in (collision, failed)})
    with pytest.raises(recovery.RecoveryError, match="BACKUP_CREATE_FAILED"):
        _created(source, directory, now=NOW)
    _unchanged(protected)
    assert (directory / ".pokemind-backup.lock").is_file()
    assert recovery.backup_status(directory)["counts"].get("verified", 0) == 1


def test_backup_lock_write_failure_keeps_diagnostic_without_touching_existing_files(local_tmp, monkeypatch):
    source, directory, _, protected = _setup(local_tmp)
    def fail(_):
        raise OSError("synthetic fsync denied")
    monkeypatch.setattr(recovery.os, "fsync", fail)
    with pytest.raises(OSError):
        _created(source, directory)
    assert (directory / ".pokemind-backup.lock").read_bytes()
    _unchanged(protected)


def test_success_checks_before_owned_alias_cleanup_and_public_verify(local_tmp, monkeypatch):
    source, directory, _, protected = _setup(local_tmp)
    verify = recovery._verify_backup
    checked = []
    unlink = Path.unlink

    def inspect_verification(path, **kwargs):
        aliases = kwargs.get("work_aliases")
        if aliases:
            assert all(p.is_file() for p in aliases)
            assert (directory / ".pokemind-backup.lock").is_file()
            # No public API accepts work aliases as verified evidence.
            with pytest.raises(recovery.RecoveryError, match="HARDLINK_ALIAS_BLOCKED"):
                recovery.verify_backup(path)
            checked.append(verify(path, **kwargs))
            return checked[-1]
        return verify(path, **kwargs)

    def inspect_cleanup(path, *args, **kwargs):
        if path.parent == directory:
            assert checked
        return unlink(path, *args, **kwargs)

    monkeypatch.setattr(recovery, "_verify_backup", inspect_verification)
    monkeypatch.setattr(Path, "unlink", inspect_cleanup)
    result, backup = _created(source, directory)
    assert result["state"] == "verified" and result["source_unchanged_during_backup"]
    evidence = recovery.verify_backup(backup)
    assert evidence["checks"]["integrity"] == "ok"
    assert evidence["checks"]["foreign_key_violations"] == 0
    assert evidence["checks"]["schema_version"] == 7
    assert all(item["status"] == "ok" for item in evidence["checks"]["fts"].values())
    assert evidence["sha256"] == result["sha256"]
    assert not list(directory.glob("*.inprogress"))
    assert not list(directory.glob("*.tmp"))
    assert not (directory / ".pokemind-backup.lock").exists()
    _unchanged(protected)
