"""Player journey and export isolation; all files and identities are synthetic."""
import json
import os
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from pokemind.cli import main
from pokemind.demo import _deck
from pokemind.decks import import_deck


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("command", ["preflight", "capabilities", "benchmark-ocr"])
def test_database_free_vision_diagnostics_never_select_default_database(local_tmp, monkeypatch, capsys, command):
    monkeypatch.setattr("pokemind.cli.find_project_root", lambda: local_tmp)

    def forbidden(*args, **kwargs):
        raise AssertionError("Database-free diagnostics must not inspect default DB metadata")

    monkeypatch.setattr("pokemind.cli._db_for", forbidden)
    assert main(["match", command, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    assert list(local_tmp.iterdir()) == []


def _guarded_command(command, workspace):
    """Apply guards inside every fresh child, not just in the pytest parent."""
    bootstrap = f"""
import os, sys, socket
from pathlib import Path
from urllib.parse import unquote, urlsplit
workspace = Path({str(workspace)!r}).resolve()
local = Path({str(ROOT / 'data/local')!r}).absolute()
socket.gethostname = lambda: 'synthetic-host'
def guard(event, args):
    if event.startswith('socket.') or event in ('subprocess.Popen', 'os.system', 'os.startfile'):
        raise AssertionError('E2E_NETWORK_OR_EXTERNAL_PROCESS_PROHIBITED:' + event)
    if event == 'sqlite3.connect':
        name = str(args[0])
        if name == ':memory:':
            return
        if name.startswith('file:'):
            uri = urlsplit(name)
            if uri.netloc:
                raise AssertionError('E2E_DATABASE_OUTSIDE_FIXTURE')
            name = unquote(uri.path)
            if os.name == 'nt' and len(name) > 3 and name[0] == '/' and name[2] == ':':
                name = name[1:]
        if not Path(name).resolve().is_relative_to(workspace):
            raise AssertionError('E2E_DATABASE_OUTSIDE_FIXTURE')
    if event in ('open', 'os.listdir', 'os.scandir') and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0])).resolve()
        if path.is_relative_to(local) and not path.is_relative_to(workspace):
            raise AssertionError('E2E_FILE_OUTSIDE_FIXTURE')
sys.addaudithook(guard)
from pokemind.cli import main
raise SystemExit(main())
"""
    assert command[1:3] == ["-m", "pokemind"]
    return [command[0], "-c", bootstrap, *command[3:]]


def _child_failure_summary(completed):
    """Expose a bounded audit category, never child stdout/stderr or paths."""
    fault = next((code for code in (
        "E2E_NETWORK_OR_EXTERNAL_PROCESS_PROHIBITED", "E2E_DATABASE_OUTSIDE_FIXTURE",
        "E2E_FILE_OUTSIDE_FIXTURE",
    ) if code in completed.stderr), "CHILD_PROCESS_FAILED")
    event = next((name for name in (
        "subprocess.Popen", "os.system", "os.startfile", "socket.__new__",
        "socket.getaddrinfo", "socket.connect", "socket.bind", "socket.sendto",
    ) if f"{fault}:{name}" in completed.stderr), "unknown")
    return {"returncode": completed.returncode, "fault": fault, "audit_event": event}


def _block_parent_network(monkeypatch):
    def block(*args, **kwargs):
        raise AssertionError("E2E_NETWORK_PROHIBITED")
    for name in ("create_connection", "getaddrinfo", "gethostbyname", "gethostbyname_ex", "gethostbyaddr"):
        monkeypatch.setattr(socket, name, block)
    for name in ("connect", "connect_ex", "bind", "sendto"):
        monkeypatch.setattr(socket.socket, name, block)


def test_complete_player_journey_blocks_network_in_every_cli_child(monkeypatch, record_testsuite_property):
    import pokemind.demo as demo
    _block_parent_network(monkeypatch)
    real_run = subprocess.run
    databases = set()
    commands = []

    def guarded_run(command, **kwargs):
        if "--db" in command:
            db = Path(command[command.index("--db") + 1])
        else:
            assert tuple(command[3:5]) in {("knowledge", "scheduler"), ("knowledge", "cadence")}
            assert len(databases) == 1
            db = next(iter(databases))
        assert db.name == "synthetic.sqlite3"
        assert db.parent.parent == ROOT / "data/local/demo-runs"
        databases.add(db)
        commands.append(tuple(command[3:5]))
        completed = real_run(_guarded_command(command, db.parent), **kwargs)
        assert completed.returncode == 0, {"step": " ".join(command[3:5]), **_child_failure_summary(completed)}
        return completed

    monkeypatch.setattr(demo.subprocess, "run", guarded_run)
    report = demo.run_demo(ROOT)
    assert report["status"] == "SYNTHETIC_REHEARSAL_PASSED"
    assert report["battles"]["n"] == report["battles"]["reimports"] == 5
    assert report["battles"]["unknown_outcomes"] == 1 and report["battles"]["decided_denominator"] == 4
    assert report["battle_links"]["active_after_revocation"] == 0
    assert report["battle_links"]["revoked"] == 1
    assert report["candidate"]["cards"] == 60 and report["candidate"]["played_version_unchanged"]
    assert report["candidate"]["legality"] == "unknown"
    assert report["legality_fixture"]["verdicts"] == ["legal", "not_legal", "unknown"]
    assert report["legality_fixture"]["expired_source"] == "unknown"
    assert report["coach"]["pixels_stored"] == 0 and report["coach"]["fresh_process_resume"]
    assert report["coach"]["correction_history_preserved"] and report["coach"]["conflicting_context_rejected"]
    assert report["release_status"] == "NOT_RELEASE_READY"
    assert report["cli_processes"] == len(commands) >= 75
    assert len(report["checkpoints"]) == len(set(report["checkpoints"])) == 13
    assert len(databases) == 1 and not next(iter(databases)).parent.exists()
    assert str(ROOT) not in json.dumps(report)
    record_testsuite_property("synthetic_cli_processes", len(commands))


@pytest.mark.parametrize("attempt", ["dns", "socket", "database", "file", "process"])
def test_child_guards_reject_prohibited_operations(local_tmp, attempt):
    # Even the forbidden paths here are nonexistent stand-ins inside this
    # freshly created fixture, never actual personal paths.
    probes = {
        "dns": "import socket; socket.getaddrinfo('example.invalid', 443)",
        "socket": "import socket; socket.socket()",
        "database": f"import sqlite3; sqlite3.connect({str(local_tmp.parent / 'forbidden.sqlite3')!r})",
        "file": f"open({str(local_tmp.parent / 'forbidden.txt')!r}, 'w')",
        "process": "import subprocess; subprocess.run(['not-an-executable'])",
    }
    command = _guarded_command([sys.executable, "-m", "pokemind"], local_tmp)
    command[2] = command[2].split("from pokemind.cli import main")[0] + probes[attempt]
    result = subprocess.run(command, capture_output=True, encoding="utf-8", timeout=15)
    assert result.returncode != 0 and "E2E_" in result.stderr


def test_schema7_backup_clone_migration_public_cli_offline(local_tmp, monkeypatch, record_testsuite_property):
    from test_lot_g_e2e import _historical_v7, _history
    _block_parent_network(monkeypatch)
    source = local_tmp / "synthetic-v7.sqlite3"
    _historical_v7(source)
    original = source.read_bytes()
    history = _history(source)
    environment = {**os.environ, "PYTHONPATH": str(ROOT / "src"), "POKEMIND_ROOT": str(ROOT)}
    calls = []

    def run(db, *args, expect=0):
        command = [sys.executable, "-m", "pokemind", *args, "--db", str(db), "--json"]
        completed = subprocess.run(_guarded_command(command, local_tmp), cwd=ROOT,
                                   env=environment, capture_output=True, encoding="utf-8", timeout=45)
        assert completed.returncode == expect, completed.stdout + completed.stderr
        calls.append(args[:2])
        return json.loads(completed.stdout)

    destination = local_tmp / "backups"
    assert run(source, "backup", "plan", "--destination", str(destination))["mode"] == "dry_run"
    assert not destination.exists() and source.read_bytes() == original
    created = run(source, "backup", "create", "--destination", str(destination), "--apply", "--confirm-owner")
    backup = destination / created["backup_file"]
    saved = backup.read_bytes()
    verified = run(source, "backup", "verify", "--backup", str(backup))
    assert verified["state"] == "verified" and verified["checks"]["schema_version"] == 7
    for migrate, version in ((False, 7), (True, 13)):
        clone = local_tmp / f"synthetic-clone{version}.sqlite3"
        migration = ("--migrate-clone",) if migrate else ()
        plan = run(clone, "restore", "plan", "--backup", str(backup), *migration)
        assert plan["mode"] == "dry_run" and plan["target_schema_version"] == version
        assert not clone.exists()
        restored = run(clone, "restore", "apply", "--backup", str(backup), *migration, "--apply", "--confirm-owner")
        checks = restored["checks"]
        assert checks["schema_version"] == version and checks["integrity"] == "ok"
        assert checks["foreign_key_violations"] == 0
        assert all(item["status"] == "ok" for item in checks["fts"].values())
        assert _history(clone) == history
        connection = sqlite3.connect(clone)
        try:
            assert connection.execute("SELECT COUNT(*) FROM sections_fts WHERE sections_fts MATCH 'SYNTHETIC_SENTINEL'").fetchone()[0] == 1
        finally:
            connection.close()
        before = clone.read_bytes()
        rejected = run(clone, "restore", "apply", "--backup", str(backup), "--apply", "--confirm-owner", expect=2)
        assert rejected["ok"] is False and clone.read_bytes() == before
    assert source.read_bytes() == original and backup.read_bytes() == saved
    record_testsuite_property("synthetic_recovery_cli_processes", len(calls))


@pytest.mark.parametrize("kind", ["played", "candidate"])
def test_demo_cli_exports_stay_with_disposable_database(local_tmp, monkeypatch, capsys, kind):
    # Fake project, including a fake personal export directory. Never inspect the
    # real personal directory to establish this regression.
    root = local_tmp / "project"
    workspace = root / "data/local/demo-runs/fresh"
    workspace.mkdir(parents=True)
    personal = root / "data/local/decks"
    personal.mkdir()
    sentinel = personal / "synthetic-sentinel.txt"
    sentinel.write_bytes(b"untouched synthetic personal stand-in")
    db = workspace / "synthetic.sqlite3"
    import_deck(db, _deck(), deck_id="synthetic", source_kind="stdin")
    monkeypatch.setattr("pokemind.cli.find_project_root", lambda: root)
    if kind == "candidate":
        changes = workspace / "changes.json"
        changes.write_text(json.dumps({
            "schema_version": 1, "name": "Synthetic candidate",
            "base_deck": {"deck_id": "synthetic", "version": 1},
            "context": {"format": "standard", "platform": "live", "as_of": "2026-01-01"},
            "source": {"kind": "owner_controlled_changes"},
            "changes": [
                {"action": "remove", "name": "Synthetic Support 1", "set_code": "SYN", "collector_number": "2", "quantity": 1},
                {"action": "add", "type": "trainer", "name": "Synthetic Alternative", "set_code": "SYN", "collector_number": "90", "quantity": 1},
            ],
        }), encoding="utf-8")
        assert main(["deck", "candidate-create", "--changes", str(changes), "--apply", "--confirm-owner", "--db", str(db), "--json"]) == 0
        candidate = json.loads(capsys.readouterr().out)["candidate_id"]
        args = ["candidate-export", "--candidate", str(candidate), "--apply", "--confirm-owner"]
    else:
        args = ["export", "synthetic"]
    assert main(["deck", *args, "--db", str(db), "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert Path(result["text_path"]).is_relative_to(workspace)
    assert list(personal.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b"untouched synthetic personal stand-in"
