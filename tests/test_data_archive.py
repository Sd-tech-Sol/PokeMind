"""Invented account folders only: archive, reset and restore of the whole PokeMind folder."""
import json
import os
import zipfile

import pytest

from pokemind import data_archive, data_location


@pytest.fixture(autouse=True)
def closed(monkeypatch):
    monkeypatch.setattr(data_archive, 'running', lambda: False)  # the owner's real window never matters here


def account(base):
    root = base / 'PokeMind'
    local = root / 'data/local'
    (local / 'chat').mkdir(parents=True)
    (local / 'chat/preferences.json').write_text('{"language": "fr"}', encoding='utf-8')
    (local / 'battle_logs').mkdir()
    log = local / 'battle_logs/pokemind-inventee.log'
    log.write_text('Tour 1 inventé', encoding='utf-8')
    os.utime(log, (1_793_000_000, 1_793_000_000))  # a game of an earlier season keeps its date
    (local / 'card-images').mkdir()
    (local / 'card-images/carte.png').write_bytes(b'\x89PNG invented')
    (local / 'avant-reinitialisation-20261101-120000').mkdir()
    (root / 'workspace/notes').mkdir(parents=True)
    (root / 'workspace/notes/idee.txt').write_text('idée inventée', encoding='utf-8')
    other = root / 'donnees-20261020-101010/data/local'
    other.mkdir(parents=True)
    (other / 'web_memory.sqlite3').write_bytes(b'invented')
    pointer = {'schema_version': 1, 'projects': {
        'c:\\projet-invente': {'status': 'outside', 'data_root': str(root / 'donnees-20261020-101010')},
        'c:\\autre': {'status': 'outside', 'data_root': str(base / 'ailleurs')}, 'x': 'pas un dict'}}
    (root / data_location.POINTER).write_text(json.dumps(pointer), encoding='utf-8')
    return root


def tree(root):
    return sorted(str(p.relative_to(root)).replace('\\', '/') for p in root.rglob('*'))


def zip_in(base, result):
    return base / data_archive.ARCHIVES / result['zip'].replace('\\', '/').rsplit('/', 1)[-1]


def test_archive_is_one_verified_zip_beside_the_folder(local_tmp):
    root = account(local_tmp)
    before = tree(root)
    result = data_archive.archive(root)
    path = zip_in(local_tmp, result)
    assert result['status'] == 'ARCHIVED' and path.is_file() and result['files'] == 6
    assert tree(root) == before  # archiving changes nothing
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        assert 'data/local/battle_logs/pokemind-inventee.log' in names and 'location.json' in names
        assert 'data/local/avant-reinitialisation-20261101-120000/' in names  # empty folders come back too
        assert archive.getinfo('data/local/card-images/carte.png').compress_type == zipfile.ZIP_STORED
    assert not [p for p in path.parent.iterdir() if '.partial-' in p.name]
    second = data_archive.archive(root)
    assert second['zip'] != result['zip']  # an earlier archive is never written over
    with pytest.raises(ValueError, match='ARCHIVE_INSIDE_SOURCE'):
        data_archive.archive(root, root / 'data')


def test_a_failed_check_leaves_no_partial_zip(local_tmp, monkeypatch):
    root = account(local_tmp)
    def refuse(*args):
        raise ValueError('ARCHIVE_CONTENT_MISMATCH')
    monkeypatch.setattr(data_archive, 'verify', refuse)
    with pytest.raises(ValueError, match='ARCHIVE_CONTENT_MISMATCH'):
        data_archive.archive(root)
    assert list((local_tmp / data_archive.ARCHIVES).iterdir()) == []


def test_reset_archives_first_then_leaves_only_what_a_first_launch_needs(local_tmp):
    root = account(local_tmp)
    before = tree(root)
    result = data_archive.reset(root)
    assert result['status'] == 'RESET' and not result['leftover'] and zip_in(local_tmp, result).is_file()
    assert tree(root) == ['data', 'data/local', 'donnees-20261020-101010', 'donnees-20261020-101010/data',
                          'donnees-20261020-101010/data/local', 'location.json', 'workspace']
    assert not (local_tmp / 'ailleurs').exists()  # a data folder outside this one is never created
    with zipfile.ZipFile(zip_in(local_tmp, result)) as archive:
        assert sorted(n.rstrip('/') for n in archive.namelist()) == before


def test_reset_puts_everything_back_when_a_file_is_in_use(local_tmp, monkeypatch):
    root = account(local_tmp)
    before = tree(root)
    real = data_archive._move
    def move(source, target, attempts, wait):
        if source.name == 'workspace':
            raise PermissionError(13, 'in use', str(source))
        real(source, target, 1, 0)
    monkeypatch.setattr(data_archive, '_move', move)
    with pytest.raises(ValueError, match='RESET_FILE_IN_USE'):
        data_archive.reset(root)
    assert tree(root) == before
    assert len(list((local_tmp / data_archive.ARCHIVES).glob('*.zip'))) == 1  # the archive made is kept


def test_nothing_is_done_while_pokemind_is_open(local_tmp, monkeypatch, capsys):
    root = account(local_tmp)
    before = tree(root)
    monkeypatch.setattr(data_archive, 'running', lambda: True)
    assert data_archive.main('reset', ['--dossier', str(root)]) == 2
    assert 'Ferme-le' in capsys.readouterr().out and tree(root) == before
    assert not (local_tmp / data_archive.ARCHIVES).exists()


def test_restore_brings_back_files_and_their_dates_and_keeps_what_it_replaces(local_tmp):
    root = account(local_tmp)
    before = tree(root)
    first = data_archive.reset(root)
    (root / 'data/local/battle_logs').mkdir()
    (root / 'data/local/battle_logs/pokemind-nouvelle.log').write_text('Saison nouvelle', encoding='utf-8')
    (root / data_location.POINTER).write_text('{"schema_version": 1, "projects": {}}', encoding='utf-8')
    result = data_archive.restore(zip_in(local_tmp, first), root)
    assert result['status'] == 'RESTORED' and result['previous_archive'] and not result['leftover']
    assert tree(root) == before
    assert json.loads((root / data_location.POINTER).read_text(encoding='utf-8')) == {
        'schema_version': 1, 'projects': {}}  # the pointer in use stays
    log = root / 'data/local/battle_logs/pokemind-inventee.log'
    assert abs(log.stat().st_mtime - 1_793_000_000) <= 2 and log.read_text(encoding='utf-8') == 'Tour 1 inventé'
    with zipfile.ZipFile(zip_in(local_tmp, {'zip': result['previous_archive']})) as archive:
        assert 'data/local/battle_logs/pokemind-nouvelle.log' in archive.namelist()


def test_restore_refuses_names_outside_the_folder(local_tmp):
    root = account(local_tmp)
    before = tree(root)
    bad = local_tmp / 'mauvaise.zip'
    with zipfile.ZipFile(bad, 'w') as archive:
        archive.writestr('../dehors.txt', 'non')
    with pytest.raises(ValueError, match='RESTORE_NAME_REFUSED'):
        data_archive.restore(bad, root)
    assert tree(root) == before and not (local_tmp / 'dehors.txt').exists()


def test_scripts_print_where_the_archive_is(local_tmp, capsys):
    root = account(local_tmp)
    assert data_archive.main('archive', ['--dossier', str(root)]) == 0
    out = capsys.readouterr().out
    assert 'Archive vérifiée' in out and '6 fichiers' in out


def test_read_only_files_and_an_earlier_leftover_are_deleted_but_never_archived_again(local_tmp):
    root = account(local_tmp)
    locked = root / 'workspace/notes/lecture-seule.txt'
    locked.write_text('inventé', encoding='utf-8')
    os.chmod(locked, 0o444)  # what Git or an engine leaves in the workspace
    earlier = root / (data_archive.TRASH + 'a' * 32)
    (earlier / 'data').mkdir(parents=True)
    (earlier / 'data/ancien.txt').write_text('déjà archivé', encoding='utf-8')
    result = data_archive.reset(root)
    assert not result['leftover'] and not earlier.exists() and not (root / 'workspace/notes').exists()
    with zipfile.ZipFile(zip_in(local_tmp, result)) as archive:
        assert 'workspace/notes/lecture-seule.txt' in archive.namelist()
        assert not [n for n in archive.namelist() if n.startswith(data_archive.TRASH)]
    (earlier / 'x').mkdir(parents=True)
    assert data_archive.clear_leftovers(root) is False and not earlier.exists()


# From the app (Settings, Data): the data folder only, where the owner chooses; restore at the next launch.

def test_the_app_archives_its_data_where_the_owner_chose(local_tmp):
    root = account(local_tmp)
    (root / 'data/local/test-runs/synthetique').mkdir(parents=True)
    (root / 'data/local/test-runs/synthetique/x.txt').write_text('test', encoding='utf-8')
    (root / ('data/local/.reinitialisation-' + 'b' * 32)).mkdir()
    chosen = local_tmp / 'Bureau' / 'mes-donnees'  # the dialog may give a name without .zip
    result = data_archive.archive(root, target=chosen, parts=data_archive.APP_PARTS,
                                  excluded=data_archive.APP_EXCLUDED, app=True)
    assert result['zip'].endswith('mes-donnees.zip') and (local_tmp / 'Bureau/mes-donnees.zip').is_file()
    with zipfile.ZipFile(local_tmp / 'Bureau/mes-donnees.zip') as archive:
        names = archive.namelist()
    assert 'data/local/chat/preferences.json' in names and 'workspace/notes/idee.txt' in names
    assert not [n for n in names if n.startswith(('location.json', 'donnees-', 'data/local/test-runs'))]
    assert not [n for n in names if '.reinitialisation-' in n]
    with pytest.raises(ValueError, match='ARCHIVE_INSIDE_SOURCE'):
        data_archive.archive(root, target=root / 'data/local/dedans.zip', parts=('data/local',), app=True)


def test_restore_asked_from_the_app_is_applied_at_the_next_launch(local_tmp):
    root = account(local_tmp)
    saved = data_archive.archive(root, target=local_tmp / 'cle-usb/archive.zip', parts=data_archive.APP_PARTS, app=True)
    (root / 'data/local/battle_logs/pokemind-inventee.log').unlink()
    (root / 'data/local/battle_logs/pokemind-nouvelle.log').write_text('Partie nouvelle', encoding='utf-8')
    (root / 'data/local/chat/preferences.json').write_text('{"language": "en"}', encoding='utf-8')
    asked = data_archive.request_restore(root, saved['zip'], parts=data_archive.APP_PARTS,
                                         archives=local_tmp / 'cle-usb', pid=os.getpid())
    assert data_archive.pending_restore(root) == asked
    result = data_archive.apply_restore(root)
    assert result['status'] == 'RESTORED' and not result['leftover'] and data_archive.pending_restore(root) is None
    log = root / 'data/local/battle_logs/pokemind-inventee.log'
    assert abs(log.stat().st_mtime - 1_793_000_000) <= 2  # the game stays in its season
    assert not (root / 'data/local/battle_logs/pokemind-nouvelle.log').exists()
    assert json.loads((root / 'data/local/chat/preferences.json').read_text(encoding='utf-8')) == {'language': 'fr'}
    assert (root / 'donnees-20261020-101010/data/local/web_memory.sqlite3').is_file()  # outside the app's data: kept
    with zipfile.ZipFile(result['previous_archive']) as archive:  # what it replaced, beside the chosen zip
        assert 'data/local/battle_logs/pokemind-nouvelle.log' in archive.namelist()
    assert data_archive.apply_restore(root) is None


def test_the_app_refuses_an_unusable_zip_before_closing_and_a_broken_one_changes_nothing(local_tmp):
    root = account(local_tmp)
    other = local_tmp / 'autre.zip'
    with zipfile.ZipFile(other, 'w') as archive:
        archive.writestr('photos/vacances.txt', 'pas PokeMind')
    with pytest.raises(ValueError, match='RESTORE_NOT_POKEMIND'):
        data_archive.request_restore(root, other, parts=('data/local',), archives=local_tmp)
    inside = root / 'data/local/dedans.zip'
    inside.write_bytes(other.read_bytes())
    with pytest.raises(ValueError, match='ARCHIVE_INSIDE_SOURCE'):
        data_archive.request_restore(root, inside, parts=('data/local',), archives=root / 'data/local')
    inside.unlink()
    saved = data_archive.archive(root, target=local_tmp / 'bonne.zip', parts=('data/local',), app=True)
    data_archive.request_restore(root, saved['zip'], parts=('data/local',), archives=local_tmp)
    before = tree(root)
    (local_tmp / 'bonne.zip').write_bytes(b'PK abime')  # the zip changed before the next launch
    result = data_archive.apply_restore(root)
    assert result['status'] == 'FAILED' and result['error'] == 'RESTORE_NOT_POKEMIND'
    assert tree(root) == [p for p in before if p != 'data/local/' + data_archive.RESTORE_REQUEST]
    assert data_archive.pending_restore(root) is None  # one attempt per request


def test_a_script_archive_of_the_whole_folder_can_be_restored_from_the_app(local_tmp):
    root = account(local_tmp)
    whole = data_archive.archive(root)
    (root / 'workspace/notes/idee.txt').unlink()
    data_archive.request_restore(root, whole['zip'], parts=data_archive.APP_PARTS, archives=local_tmp)
    result = data_archive.apply_restore(root)
    assert result['status'] == 'RESTORED' and (root / 'workspace/notes/idee.txt').is_file()
    assert result['files'] == 4  # data/local and workspace only; the pointer and other folders stay as they are
