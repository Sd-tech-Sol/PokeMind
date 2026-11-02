"""Explicitly selected QA policy/namespace/CLI tests; no ordinary autostart."""
import json
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
import pytest
from pokemind import synthetic_qa as qa


def test_owned_fixture_and_early_temp(local_tmp):
    c = qa.current()
    assert local_tmp.parent == c.root and Path(tempfile.gettempdir()) == c.temp
    assert c.validate_live() == c.root and c.before_conftest >= 2


@pytest.mark.parametrize('relative', ['data/local', 'data/local/backups', 'source_material', 'build/ordinary', 'build/qr-wrong'])
def test_namespace_refused_before_inspection(local_tmp, relative, monkeypatch):
    project = local_tmp / 'project'
    monkeypatch.setattr(Path, 'lstat', lambda *a, **k: pytest.fail('no inspection of inadmissible namespace'))
    with pytest.raises(ValueError, match='QA_MARKED_ROOT_REQUIRED'):
        qa.validate_root(project / relative, project=project)


def test_root_collision_and_occupation(local_tmp):
    project = local_tmp / 'project'; project.mkdir()
    root, _ = qa.new_root(project=project, identifier='aaaaaaaa')
    with pytest.raises(FileExistsError):
        qa.new_root(project=project, identifier='aaaaaaaa')
    (root / 'occupied').write_text('invented', encoding='utf-8')
    with pytest.raises(ValueError, match='QA_ROOT_ALREADY_USED'):
        qa.validate_root(root, project=project, fresh=True)


@pytest.mark.parametrize('fault', ['missing', 'wrong', 'hardlink', 'reparse'])
def test_marker_and_alias_rejections(local_tmp, monkeypatch, fault):
    project = local_tmp / 'project'; project.mkdir()
    root, _ = qa.new_root(project=project); marker = root / qa.MARKER
    if fault == 'missing': marker.unlink()
    elif fault == 'wrong': marker.write_text('{}', encoding='utf-8')
    elif fault == 'hardlink': os.link(marker, root / 'alias')
    else:
        original = Path.lstat
        def lstat(path, *a, **k):
            value = original(path, *a, **k)
            return SimpleNamespace(st_mode=value.st_mode, st_nlink=value.st_nlink, st_file_attributes=0x400) if path == root else value
        monkeypatch.setattr(Path, 'lstat', lstat)
    with pytest.raises(ValueError, match='QA_'):
        qa.validate_root(root, project=project)


@pytest.mark.parametrize('event', ['socket.connect', 'socket.getaddrinfo', 'socket.gethostname', 'urllib.Request', 'http.client.send', 'subprocess.Popen', 'os.system', 'os.startfile'])
def test_process_and_network_policy_is_closed(event):
    with pytest.raises(PermissionError, match='QA_(NETWORK|PROCESS)_REFUSED'):
        qa.current().policy.event(event)


@pytest.mark.parametrize('environment,modules', [({qa.ROOT_ENV: 'untrusted'}, {}), ({qa.TOKEN_ENV: 'untrusted'}, {}), ({}, {'pytest': object()}), ({}, {'_pytest.capture': object()})])
def test_bootstrap_collision_and_order(environment, modules):
    with pytest.raises(ValueError, match='QA_'): qa.precheck(environment, modules)


def test_changed_runtime_token_rejects_allocation(monkeypatch):
    monkeypatch.setenv(qa.TOKEN_ENV, 'untrusted')
    with pytest.raises(ValueError, match='QA_BOOTSTRAP_SESSION_MISMATCH'): qa.current().allocate()


@pytest.mark.parametrize('write,database', [(False, False), (True, False), (False, True)])
def test_private_namespace_policy_without_io(write, database):
    with pytest.raises(PermissionError, match='QA_PRIVATE_NAMESPACE_REFUSED'):
        qa.current().policy.path(qa.PROJECT / 'data/local/DO_NOT_OPEN', write=write, database=database)


@pytest.mark.parametrize('args', [['status'], ['knowledge', 'update'], ['meta', 'public-identity-explain', '--db', 'private'], ['meta', 'public-identity-explain', '--as-of']])
def test_cli_cannot_select_other_operations_or_paths(local_tmp, args):
    from qa_synthetic_cli import call
    with pytest.raises(ValueError, match='QA_CLI_'): call(local_tmp, args)


def test_three_real_formatters_and_unchanged_pair(local_tmp, monkeypatch):
    from test_public_evidence_explain_cli import two_compositions, call
    import subprocess
    pair = two_compositions(local_tmp); before = [p.read_bytes() for p in pair]
    monkeypatch.setattr(subprocess, 'Popen', lambda *a, **k: pytest.fail('no child expected'))
    args = ['meta', 'public-identity-explain', '--as-of', '2026-10-23']
    human, data, html = [call(local_tmp, args + mode, guarded=True) for mode in ([], ['--json'], ['--html'])]
    assert human.returncode == data.returncode == html.returncode == 0
    assert b'Composition' in human.stdout and html.stdout.startswith(b'<!doctype html>')
    assert json.loads(data.stdout)['exact_sqlite_files_unchanged'] == 2
    assert not human.stderr and not data.stderr and not html.stderr
    assert before == [p.read_bytes() for p in pair]


def test_legacy_setting_unchanged_without_opt_in(monkeypatch):
    monkeypatch.delenv(qa.ROOT_ENV); monkeypatch.delenv(qa.TOKEN_ENV)
    assert qa.opt_in_root() is None


def test_atomic_publication_unlinks_own_temporary_name_only(local_tmp):
    from pokemind.recovery import _atomic_bytes
    target = local_tmp / 'invented-marker.json'
    _atomic_bytes(target, b'{"invented":true}', overwrite=False)
    assert target.read_bytes() == b'{"invented":true}' and target.stat().st_nlink == 1
    assert not qa.current().denials


def test_runner_counts_calls_and_setup_errors_without_junit():
    from run_synthetic_qa import Outcomes
    reports = Outcomes()
    for phase in ('setup', 'call', 'teardown'):
        reports.pytest_runtest_logreport(SimpleNamespace(nodeid='invented-pass', when=phase, outcome='passed'))
    reports.pytest_runtest_logreport(SimpleNamespace(nodeid='invented-setup-error', when='setup', outcome='failed'))
    assert reports.counts() == {'tests': 2, 'tests_called': 1, 'passed': 1, 'failures': 0, 'errors': 1, 'skipped': 0}


@pytest.mark.parametrize('fault', ['hardlink', 'reparse'])
def test_source_read_alias_refused_by_policy_before_open(monkeypatch, fault):
    import stat
    target = qa.PROJECT / 'src' / 'INVENTED_DO_NOT_OPEN'
    original = Path.lstat
    def lstat(path, *a, **k):
        if path == target:
            return SimpleNamespace(st_mode=stat.S_IFREG, st_nlink=2 if fault == 'hardlink' else 1,
                                   st_file_attributes=0x400 if fault == 'reparse' else 0)
        return original(path, *a, **k)
    monkeypatch.setattr(Path, 'lstat', lstat)
    with pytest.raises(ValueError, match='QA_(FILE_ALIAS|REPARSE)_REFUSED'):
        qa.current().policy.path(target)
