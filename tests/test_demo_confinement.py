"""Real CLI export routing against fake projects, profiles and active data roots only."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import uuid

import pytest

from pokemind import data_location, demo
from test_user_journey_e2e import _block_parent_network

ROOT = Path(__file__).resolve().parents[1]


def tree(path):
    return {p.relative_to(path).as_posix(): p.read_bytes() if p.is_file() else None
            for p in path.rglob('*')}


@pytest.fixture
def fake_project(tmp_path, monkeypatch):
    project = tmp_path / 'project'
    # Copy only public source/seed inputs; never copy a data directory or profile.
    shutil.copytree(ROOT / 'src', project / 'src', ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy2(ROOT / 'pyproject.toml', project / 'pyproject.toml')
    shutil.copytree(ROOT / 'source_material/markdown', project / 'source_material/markdown')
    fixture = project / 'tests/fixtures/cards/catalog_api.json'
    fixture.parent.mkdir(parents=True)
    shutil.copy2(ROOT / 'tests/fixtures/cards/catalog_api.json', fixture)
    (project / '.orchestrator').mkdir()
    for name in ('AGENTS.md', '.orchestrator/PROJECT_SPEC.md', '.orchestrator/HANDOFF.md'):
        (project / name).write_text('# Invented confinement QA only\n', encoding='utf-8')
    profile = tmp_path / 'profile'
    profile.mkdir()
    for name in ('LOCALAPPDATA', 'APPDATA', 'USERPROFILE', 'HOME'):
        monkeypatch.setenv(name, str(profile))
    for name in ('POKEMIND_DATA_ROOT', 'POKEMIND_DESKTOP_SMOKE'):
        monkeypatch.delenv(name, raising=False)
    _block_parent_network(monkeypatch)
    return project, profile


def observe_children(monkeypatch, allowed, *, collision=False):
    """Record writes and block networking/process launches inside every fresh CLI."""
    real_run, temporary = demo.subprocess.run, demo.tempfile.TemporaryDirectory
    observed = {'commands': [], 'writes': [], 'exports': [], 'files': {}}

    @contextmanager
    def workspace(**kwargs):
        with temporary(**kwargs) as directory:
            target = Path(directory)
            observed['workspace'] = target
            if collision:
                folder = target / 'data/local/decks/import_ready'
                folder.mkdir(parents=True)
                for suffix in ('txt', 'json'):
                    (folder / ('synthetic_v2.' + suffix)).write_bytes(b'existing invented export')
            try:
                yield directory
            finally:
                observed['files'] = tree(target)  # inspect BEFORE TemporaryDirectory removes it

    def run(command, **kwargs):
        assert command[1:3] == ['-m', 'pokemind']
        target = observed['workspace']
        if '--db' in command:
            assert Path(command[command.index('--db') + 1]).is_relative_to(target)
        log = target / ('writes-' + uuid.uuid4().hex + '.jsonl')
        bootstrap = f'''
import os, sys, json
from pathlib import Path
from urllib.parse import unquote, urlsplit
allowed = Path({str(allowed)!r}).resolve()
stream = open({str(log)!r}, 'a', encoding='utf-8')
def record(name):
    if not isinstance(name, (str, bytes, os.PathLike)):
        return
    path = Path(os.fsdecode(name)).resolve()
    if not path.is_relative_to(allowed):
        raise AssertionError('WRITE_OUTSIDE_SYNTHETIC_TEST')
    stream.write(json.dumps(str(path)) + '\\n'); stream.flush()
def audit(event, args):
    if event.startswith('socket.') or event in ('subprocess.Popen', 'os.system', 'os.startfile'):
        raise AssertionError('DEMO_NETWORK_OR_EXTERNAL_PROCESS_FORBIDDEN')
    if event == 'open' and ((isinstance(args[1], str) and any(c in args[1] for c in 'wax+'))
                          or (args[2] & (os.O_WRONLY | os.O_RDWR))):
        record(args[0])
    elif event == 'os.mkdir':
        record(args[0])
    elif event in ('os.link', 'os.rename'):
        record(args[1])
    elif event == 'sqlite3.connect' and str(args[0]) != ':memory:':
        name = str(args[0])
        if name.startswith('file:'):
            name = unquote(urlsplit(name).path)
            if os.name == 'nt' and name.startswith('/') and name[2:3] == ':': name = name[1:]
        record(name)
sys.addaudithook(audit)
from pokemind.paths import find_project_root
assert find_project_root() == Path({str(kwargs['cwd'])!r}), 'FAKE_PROJECT_ROOT_NOT_SELECTED'
from pokemind.cli import main
raise SystemExit(main())
'''
        observed['commands'].append(tuple(command[3:5]))
        env = dict(kwargs['env'], TEMP=str(target), TMP=str(target))
        completed = real_run([command[0], '-c', bootstrap, *command[3:]], **(kwargs | {'env': env}))
        assert 'DEMO_NETWORK_OR_EXTERNAL_PROCESS_FORBIDDEN' not in completed.stderr
        assert 'WRITE_OUTSIDE_SYNTHETIC_TEST' not in completed.stderr
        observed['writes'].extend(Path(json.loads(line)) for line in log.read_text().splitlines())
        if completed.returncode == 0:
            result = json.loads(completed.stdout)
            observed['exports'].extend(Path(result[key]) for key in ('text_path', 'report_path') if key in result)
        return completed

    monkeypatch.setattr(demo.tempfile, 'TemporaryDirectory', workspace)
    monkeypatch.setattr(demo.subprocess, 'run', run)
    return observed


@pytest.mark.parametrize('active', ['pointer', 'override'])
def test_demo_ignores_external_fake_pointer_and_inherited_override(tmp_path, fake_project, monkeypatch, active):
    project, profile = fake_project
    pointer_root, override_root = tmp_path / 'pointer-data', tmp_path / 'override-data'
    for folder in (pointer_root, override_root):
        (folder / 'data/local').mkdir(parents=True)
        (folder / 'data/local/sentinel.txt').write_bytes(b'untouched invented data')
    pointer = profile / 'PokeMind/location.json'
    pointer.parent.mkdir()
    pointer.write_text(json.dumps({'schema_version': 1, 'projects': {
        data_location._key(project): {'status': 'outside', 'data_root': str(pointer_root)}}}), encoding='utf-8')
    if active == 'override':
        monkeypatch.setenv('POKEMIND_DATA_ROOT', str(override_root))
    before = tree(pointer_root), tree(override_root), pointer.read_bytes()
    observed = observe_children(monkeypatch, tmp_path)
    error = None
    try:
        report = demo.run_demo(project)
    except ValueError as exc:
        error = str(exc)
    # This is intentionally first: the vulnerable code creates two fake files
    # in the selected outside root before raising DEMO_EXPORT_OUTSIDE_WORKSPACE.
    assert (tree(pointer_root), tree(override_root), pointer.read_bytes()) == before, 'EXTERNAL_SYNTHETIC_ROOT_CONTAMINATED'
    assert error is None, error
    assert report['status'] == 'SYNTHETIC_REHEARSAL_PASSED'
    assert len(observed['commands']) == report['cli_processes'] == 79
    assert observed['exports'] and all(p.is_relative_to(observed['workspace']) for p in observed['exports'])
    assert observed['writes'] and all(p.is_relative_to(observed['workspace']) for p in observed['writes'])
    assert ('deck', 'export') in observed['commands'] and ('deck', 'candidate-export') in observed['commands']
    assert any(p.endswith('synthetic_v2.txt') for p in observed['files'])
    assert any('candidate-' in p and p.endswith('.txt') for p in observed['files'])
    assert not report['network_used'] and not observed['workspace'].exists()


@pytest.mark.parametrize('redirected', ['import_ready', 'drafts'])
def test_demo_checks_export_directories_before_starting_any_child(fake_project, monkeypatch, redirected):
    project, _ = fake_project
    real = demo._redirected
    monkeypatch.setattr(demo, '_redirected', lambda p: p.name == redirected or real(p))
    def forbidden(*args, **kwargs):
        pytest.fail('child started before the export directory safety check')
    monkeypatch.setattr(demo.subprocess, 'run', forbidden)
    with pytest.raises(ValueError, match='DEMO_DIRECTORY_UNSAFE'):
        demo.run_demo(project)


def test_demo_does_not_overwrite_existing_synthetic_export(tmp_path, fake_project, monkeypatch):
    project, _ = fake_project
    observed = observe_children(monkeypatch, tmp_path, collision=True)
    with pytest.raises(ValueError, match='DEMO_CLI_STEP_FAILED:deck'):
        demo.run_demo(project)
    assert observed['commands'][-1] == ('deck', 'export')
    for suffix in ('txt', 'json'):
        assert observed['files']['data/local/decks/import_ready/synthetic_v2.' + suffix] == b'existing invented export'
    assert all(p.is_relative_to(observed['workspace']) for p in observed['writes'])
    assert not observed['workspace'].exists()
