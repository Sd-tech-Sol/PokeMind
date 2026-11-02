import json
import os

import pytest

from pokemind.commissioning import commissioning_preflight
from pokemind import recovery
from test_lot_g_e2e import _historical_v7
from test_recovery import _database


def _preview_snapshot(root):
    # Only this disposable fixture; atime may change during read-only checks.
    fields = ("st_dev", "st_ino", "st_nlink", "st_size", "st_mtime_ns", "st_ctime_ns", "st_file_attributes")
    snapshot = {}
    for path in (root, *root.rglob("*")):
        info = path.stat()
        snapshot[path.relative_to(root)] = (
            tuple(getattr(info, field, None) for field in fields),
            path.read_bytes() if path.is_file() else None,
        )
    return snapshot


@pytest.mark.parametrize("migrate_clone", [False, True])
def test_schema7_cli_restore_plan_preserves_bytes_metadata_and_absent_target(local_tmp, capsys, monkeypatch, migrate_clone):
    from pokemind.cli import main

    source = local_tmp / "history7.sqlite3"
    _historical_v7(source)
    created = recovery.create_backup(source, local_tmp / "backups", apply=True, confirm_owner=True, min_free_bytes=0)
    saved = local_tmp / "backups" / created["backup_file"]
    target = local_tmp / "new-clone.sqlite3"
    before = _preview_snapshot(local_tmp)

    def no_copy_or_migration(*args, **kwargs):
        pytest.fail("A restore plan must neither copy nor migrate a database")

    monkeypatch.setattr(recovery, "_copy_database", no_copy_or_migration)
    monkeypatch.setattr(recovery, "initialize_schema", no_copy_or_migration)
    args = ["restore", "plan", "--backup", str(saved), "--db", str(target), "--json"]
    if migrate_clone:
        args.append("--migrate-clone")
    assert main(args) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["ok"] and plan["mode"] == "dry_run" and plan["read_only"]
    assert not plan["network_used"] and not plan["target"]["exists"]
    assert plan["backup"]["state"] == plan["backup"]["manifest_state"] == "verified"
    checks = plan["backup"]["checks"]
    assert checks["schema_version"] == 7 and checks["integrity"] == "ok"
    assert checks["foreign_key_violations"] == 0 and len(checks["fts"]) == 2
    assert all(item["status"] == "ok" for item in checks["fts"].values())
    assert plan["migrate_clone"] is migrate_clone
    assert plan["target_schema_version"] == (13 if migrate_clone else 7)
    assert plan["capacity"]["enough"] and plan["would_write"] and plan["reason_code"] is None
    assert not target.exists() and _preview_snapshot(local_tmp) == before


@pytest.mark.parametrize("target_exists,free_bytes,reason", [
    (False, 0, "INSUFFICIENT_DISK_SPACE"),
    (True, 0, "RESTORE_EXISTING_TARGET_BLOCKED"),
    (True, 1 << 40, "RESTORE_EXISTING_TARGET_BLOCKED"),
])
def test_restore_plan_explains_capacity_or_collision_without_writes(local_tmp, monkeypatch, target_exists, free_bytes, reason):
    from collections import namedtuple

    source = local_tmp / "history7.sqlite3"
    _historical_v7(source)
    created = recovery.create_backup(source, local_tmp / "backups", apply=True, confirm_owner=True, min_free_bytes=0)
    saved = local_tmp / "backups" / created["backup_file"]
    target = local_tmp / "clone.sqlite3"
    if target_exists:
        target.write_bytes(b"synthetic existing target must be preserved")
    before = _preview_snapshot(local_tmp)
    usage = namedtuple("usage", "total used free")
    monkeypatch.setattr(recovery.shutil, "disk_usage", lambda _: usage(1 << 41, 0, free_bytes))

    plan = recovery.restore_plan(saved, target)

    assert plan["mode"] == "dry_run" and plan["read_only"] and not plan["network_used"]
    assert plan["target"]["exists"] is target_exists and not plan["would_write"]
    assert plan["capacity"]["enough"] is (free_bytes > 0)
    assert _preview_snapshot(local_tmp) == before
    assert plan["reason_code"] == reason


def test_five_previews_preserve_source_backup_and_clone(local_tmp):
    source = _database(local_tmp / "source.sqlite3")
    source_bytes = source.read_bytes()
    backup = recovery.create_backup(source, local_tmp / "backups", apply=True, confirm_owner=True, min_free_bytes=0)
    # Result contains a private backup filename only inside this disposable test.
    files = list((local_tmp / "backups").glob("*.sqlite3"))
    assert len(files) == 1
    saved = files[0]
    saved_bytes = saved.read_bytes()
    clone = local_tmp / "clone.sqlite3"
    assert recovery.backup_plan(source, local_tmp / "backups", min_free_bytes=0)["mode"] == "dry_run"
    assert commissioning_preflight(source, step="verify", backup_path=saved)["technical_preflight_passed"]
    assert commissioning_preflight(source, step="clone", backup_path=saved, clone_path=clone)["technical_preflight_passed"]
    assert commissioning_preflight(source, step="migration", backup_path=saved)["technical_preflight_passed"]
    assert not clone.exists()
    recovery.restore_backup(saved, clone, apply=True, confirm_owner=True, min_free_bytes=0)
    preview = commissioning_preflight(clone, step="activate", backup_path=saved)
    assert preview["status"] == "OWNER_ACTION_REQUIRED" and not preview["owner_authorization_inferred"]
    assert str(local_tmp) not in json.dumps(preview)
    assert source.read_bytes() == source_bytes and saved.read_bytes() == saved_bytes
    before = clone.read_bytes()
    with pytest.raises(recovery.RecoveryError, match="RESTORE_EXISTING_TARGET_BLOCKED"):
        recovery.restore_backup(saved, clone, apply=True, confirm_owner=True, min_free_bytes=0)
    assert clone.read_bytes() == before


def test_clone_owner_preview_rejects_windows_reparse_before_creation(local_tmp, monkeypatch):
    source = _database(local_tmp / "source.sqlite3")
    recovery.create_backup(source, local_tmp / "backups", apply=True, confirm_owner=True, min_free_bytes=0)
    saved = next((local_tmp / "backups").glob("*.sqlite3"))
    clone = local_tmp / "redirected" / "clone.sqlite3"
    import pokemind.commissioning as module
    monkeypatch.setattr(module, "_redirected", lambda path: path.name == "redirected")
    report = commissioning_preflight(source, step="clone", backup_path=saved, clone_path=clone)
    assert "RESTORE_EXISTING_OR_UNSAFE_TARGET_BLOCKED" in report["blockers"]
    assert not clone.parent.exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction end-to-end test")
def test_cli_rejects_actual_windows_junction_before_resolving_paths(local_tmp, capsys):
    import _winapi
    from pokemind.cli import main
    destination = local_tmp / "real"
    destination.mkdir()
    junction = local_tmp / "junction"
    _winapi.CreateJunction(str(destination), str(junction))
    try:
        assert recovery._redirected(junction)
        # Both DB selection and clone/backup arguments must retain the alias
        # until safety validation, before touching any source or destination.
        for args in (
            ["backup", "plan", "--db", str(junction / "source.sqlite3")],
            ["restore", "plan", "--backup", str(junction / "backup.sqlite3"), "--db", str(local_tmp / "clone.sqlite3")],
            ["owner-plan", "--step", "clone", "--clone", str(junction / "clone.sqlite3"), "--db", str(local_tmp / "source.sqlite3")],
        ):
            assert main([*args, "--json"]) == 2
            result = json.loads(capsys.readouterr().out)
            assert "RECOVERY_PATH_REDIRECTED" in json.dumps(result)
            assert str(local_tmp) not in json.dumps(result)
        assert list(destination.iterdir()) == []
    finally:
        # Remove only this generated junction; never recurse into its target.
        assert junction.absolute().is_relative_to(local_tmp.absolute())
        junction.rmdir()
