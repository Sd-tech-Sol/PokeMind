"""Focused readiness child regression under the unchanged E2E audit barriers."""
import json
import os
import subprocess
import sys

import pytest

from test_readiness import _database
from test_user_journey_e2e import (
    ROOT, _block_parent_network, _child_failure_summary, _guarded_command,
)


def _readiness_child(workspace, db, *, injected_probe=""):
    command = _guarded_command([
        sys.executable, "-m", "pokemind", "v1", "readiness", "--db", str(db), "--json",
    ], workspace)
    if injected_probe:
        command[2] = command[2].replace("from pokemind.cli import main", injected_probe + "\nfrom pokemind.cli import main")
    return subprocess.run(command, cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src"), "POKEMIND_ROOT": str(ROOT),
             "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, encoding="utf-8", timeout=45)


@pytest.mark.parametrize("filename", ["synthetic.sqlite3", "synthetic # 50%.sqlite3"])
def test_fresh_guarded_readiness_child_is_read_only_without_os_process(local_tmp, monkeypatch, filename):
    _block_parent_network(monkeypatch)
    db = _database(local_tmp / filename)
    before = db.read_bytes()
    completed = _readiness_child(local_tmp, db)
    assert completed.returncode == 0, _child_failure_summary(completed)
    report = json.loads(completed.stdout)
    assert report["status"] == "NOT_RELEASE_READY" and report["read_only"]
    assert not report["network_used"] and not report["private_values_disclosed"]
    assert report["runtime"]["os"] == ("Windows" if os.name == "nt" else "Linux")
    assert db.read_bytes() == before
    assert list(local_tmp.iterdir()) == [db]


@pytest.mark.parametrize("operation,fault", [
    ("file", "E2E_FILE_OUTSIDE_FIXTURE"),
    ("process", "E2E_NETWORK_OR_EXTERNAL_PROCESS_PROHIBITED"),
])
def test_readiness_still_rejects_outside_fixture_or_process(local_tmp, monkeypatch, operation, fault):
    _block_parent_network(monkeypatch)
    workspace = local_tmp / "contained"
    workspace.mkdir()
    db = _database(workspace / "synthetic.sqlite3")
    before = db.read_bytes()
    outside = local_tmp / "synthetic-must-not-be-created.txt"
    action = (f"open({str(outside)!r}, 'w')" if operation == "file"
              else "__import__('subprocess').run(['synthetic-not-an-executable'])")
    probe = ("import pokemind.readiness as target\n"
             "def prohibited_database_status(*args):\n    " + action + "\n"
             "target.database_status = prohibited_database_status")
    completed = _readiness_child(workspace, db, injected_probe=probe)
    assert completed.returncode != 0
    assert _child_failure_summary(completed)["fault"] == fault
    assert not outside.exists() and db.read_bytes() == before


def test_child_diagnostic_omits_raw_output_and_synthetic_secret():
    completed = subprocess.CompletedProcess([], 1, "SYNTHETIC_SECRET_STDOUT",
        "AssertionError: E2E_NETWORK_OR_EXTERNAL_PROCESS_PROHIBITED:subprocess.Popen\n"
        "SYNTHETIC_SECRET_STDERR C:/synthetic-private/example.txt")
    assert _child_failure_summary(completed) == {
        "returncode": 1, "fault": "E2E_NETWORK_OR_EXTERNAL_PROCESS_PROHIBITED",
        "audit_event": "subprocess.Popen",
    }


def test_encoded_uri_outside_fixture_is_still_denied(local_tmp, monkeypatch):
    _block_parent_network(monkeypatch)
    workspace = local_tmp / "contained"
    workspace.mkdir()
    db = _database(workspace / "synthetic.sqlite3")
    outside = local_tmp / "synthetic # outside.sqlite3"
    probe = f"import sqlite3\nsqlite3.connect({outside.as_uri() + '?mode=ro'!r}, uri=True)"
    completed = _readiness_child(workspace, db, injected_probe=probe)
    assert completed.returncode != 0
    assert _child_failure_summary(completed)["fault"] == "E2E_DATABASE_OUTSIDE_FIXTURE"
    assert not outside.exists()
