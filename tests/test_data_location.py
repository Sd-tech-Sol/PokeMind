"""Owner data copied out of the project (audit P0-1). Every file and folder here is invented."""
import hashlib
import json
from pathlib import Path

import pytest

from pokemind import data_location


@pytest.fixture
def app_folder(tmp_path, monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path / 'appdata'))
    monkeypatch.delenv('POKEMIND_DATA_ROOT', raising=False)
    monkeypatch.delenv('POKEMIND_DESKTOP_SMOKE', raising=False)
    return tmp_path / 'appdata' / 'PokeMind'


def project(tmp_path):
    root = tmp_path / 'projet'
    local = root / 'data/local'
    (local / 'battle_logs').mkdir(parents=True)
    (local / 'battle_logs/partie-inventee.txt').write_text('Tour 1 inventé\n', encoding='utf-8')
    (local / 'chat').mkdir()
    (local / 'chat/preferences.json').write_text('{"language": "fr"}', encoding='utf-8')
    (local / 'pokemind.sqlite3').write_bytes(bytes(range(256)) * 50)
    (local / 'vide').mkdir()
    (local / 'test-runs/abc').mkdir(parents=True)
    (local / 'test-runs/abc/synthetique.bin').write_bytes(b'x' * 1000)
    (local / '.gitkeep').write_text('')
    return root


def tree(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob('*')) if p.is_file()}


def test_copy_out_verifies_every_file_keeps_the_original_and_points_the_project_at_the_copy(tmp_path, app_folder):
    root = project(tmp_path)
    before = tree(root / 'data/local')
    assert data_location.resolve(root) == (root.absolute(), 'offer')
    steps = []
    receipt = data_location.copy_out(root, progress=lambda done, total: steps.append((done, total)))
    copied = app_folder / 'data/local'
    assert tree(root / 'data/local') == before  # original untouched
    expected = {k: v for k, v in before.items() if not k.startswith('test-runs/')}
    assert tree(copied) == expected and (copied / 'vide').is_dir() and not (copied / 'test-runs').exists()
    assert receipt['files'] == len(expected) and receipt['excluded'] == ['test-runs']
    assert steps[0][0] == 0 and steps[-1][0] == steps[-1][1] == sum((root / 'data/local' / k).stat().st_size for k in expected)
    assert data_location.resolve(root) == (app_folder, 'outside')
    assert not list((app_folder / 'data').glob('local.partial-*'))
    pointer = json.loads((app_folder / 'location.json').read_text(encoding='utf-8'))
    assert list(pointer['projects'].values())[0]['status'] == 'outside'


def test_pointer_belongs_to_one_project_and_release_qa_or_override_never_follow_it(tmp_path, app_folder, monkeypatch):
    root = project(tmp_path)
    data_location.copy_out(root)
    other = tmp_path / 'autre-projet'
    (other / 'data/local').mkdir(parents=True)
    assert data_location.resolve(other) == (other.absolute(), 'project')
    monkeypatch.setenv('POKEMIND_DESKTOP_SMOKE', '1')
    assert data_location.resolve(root) == (root.absolute(), 'project')
    monkeypatch.delenv('POKEMIND_DESKTOP_SMOKE')
    monkeypatch.setenv('POKEMIND_DATA_ROOT', str(tmp_path / 'force'))
    assert data_location.resolve(root) == ((tmp_path / 'force').absolute(), 'override')


def test_revert_decline_and_a_second_copy_never_write_over_an_earlier_one(tmp_path, app_folder):
    root = project(tmp_path)
    data_location.use_project(root, 'declined')
    assert data_location.resolve(root)[1] == 'project'
    data_location.request_copy(root)
    assert data_location.resolve(root)[1] == 'offer'
    first = data_location.copy_out(root)
    data_location.use_project(root, 'reverted')
    assert data_location.resolve(root) == (root.absolute(), 'project')
    assert data_location.entry(root)['previous_data_root'] == first['data_root']
    second = data_location.copy_out(root)
    assert second['data_root'] != first['data_root'] and Path(second['data_root']).parent == app_folder
    assert (Path(first['data_root']) / 'data/local/pokemind.sqlite3').is_file()
    with pytest.raises(ValueError, match='DATA_TARGET_NOT_EMPTY'):
        data_location.copy_out(root, first['data_root'])


def test_failed_or_cancelled_copy_leaves_no_partial_copy_and_no_pointer_change(tmp_path, app_folder, monkeypatch):
    root = project(tmp_path)
    with pytest.raises(ValueError, match='DATA_COPY_CANCELLED'):
        data_location.copy_out(root, cancelled=lambda: True)
    assert not list((app_folder / 'data').glob('local.partial-*')) and not (app_folder / 'data/local').exists()
    assert data_location.resolve(root)[1] == 'offer'

    def busy(source, destination, step):
        raise PermissionError('verrou inventé')
    original = data_location._copy_one
    monkeypatch.setattr(data_location, '_copy_one', busy)
    with pytest.raises(ValueError, match='DATA_SOURCE_BUSY'):
        data_location.copy_out(root)
    assert data_location.resolve(root)[1] == 'offer'
    monkeypatch.setattr(data_location, '_copy_one', original)
    monkeypatch.setattr(data_location.shutil, 'disk_usage', lambda path: type('U', (), {'free': 10})())
    with pytest.raises(ValueError, match='DATA_TARGET_SPACE'):
        data_location.copy_out(root)
    with pytest.raises(ValueError, match='DATA_TARGET_INSIDE_PROJECT'):
        data_location.copy_out(root, root / 'dedans')


def test_copy_one_refuses_a_source_that_changes_while_it_is_read(tmp_path):
    source, destination = tmp_path / 'source.bin', tmp_path / 'copie.bin'
    source.write_bytes(b'a' * (3 << 20))
    real_open = Path.open

    def open_and_touch(self, mode='r', *args, **kwargs):
        stream = real_open(self, mode, *args, **kwargs)
        if self == source and 'r' in mode:
            with real_open(source, 'ab') as writer:
                writer.write(b'b')
        return stream
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Path, 'open', open_and_touch)
        with pytest.raises(ValueError, match='DATA_SOURCE_CHANGED_DURING_COPY'):
            data_location._copy_one(source, destination)


def test_project_without_owner_data_is_not_offered_a_copy(tmp_path, app_folder):
    root = tmp_path / 'neuf'
    (root / 'data/local/test-runs').mkdir(parents=True)
    (root / 'data/local/.gitkeep').write_text('')
    assert data_location.resolve(root) == (root.absolute(), 'project')


def cli_project(tmp_path):
    root = project(tmp_path)
    (root / 'pyproject.toml').write_text('[project]\nname = "inventé"\n', encoding='utf-8')
    (root / '.orchestrator').mkdir()
    (root / '.orchestrator/PROJECT_SPEC.md').write_text('inventé\n', encoding='utf-8')
    (root / 'source_material/markdown').mkdir(parents=True)
    return root


def test_command_line_follows_only_an_accepted_copy_or_the_override(tmp_path, app_folder, monkeypatch, capsys):
    from pokemind import cli
    root = cli_project(tmp_path)
    monkeypatch.setenv('POKEMIND_ROOT', str(root))
    assert data_location.cli_root(root) == root.absolute()  # data still in the project: no offer, no copy
    assert not app_folder.exists()

    def status():
        assert cli.main(['status', '--json']) == 0
        return Path(json.loads(capsys.readouterr().out)['database'])
    assert status().is_relative_to(root.resolve())
    receipt = data_location.copy_out(root)
    assert status() == Path(receipt['data_root']) / 'data' / 'local' / 'pokemind.sqlite3'
    data_location.use_project(root, 'reverted')
    assert status().is_relative_to(root.resolve())
    monkeypatch.setenv('POKEMIND_DATA_ROOT', str(tmp_path / 'force'))
    assert status() == (tmp_path / 'force').absolute() / 'data' / 'local' / 'pokemind.sqlite3'


def test_private_paths_stay_under_data_local_in_both_the_project_and_the_data_folder(tmp_path):
    from pokemind.cli import _private_path
    code, data = tmp_path / 'projet', tmp_path / 'donnees'
    assert _private_path(data / 'data/local/backups/a.sqlite3', data, code, label='La sauvegarde').is_relative_to(data.resolve())
    assert _private_path(code / 'data/local/backups/a.sqlite3', data, code, label='La sauvegarde').is_relative_to(code.resolve())
    assert _private_path(tmp_path / 'ailleurs/a.sqlite3', data, code, label='La sauvegarde').name == 'a.sqlite3'
    for outside_data_local in (data / 'a.sqlite3', code / 'src/a.sqlite3'):
        with pytest.raises(ValueError, match='doit rester sous data/local'):
            _private_path(outside_data_local, data, code, label='La sauvegarde')
