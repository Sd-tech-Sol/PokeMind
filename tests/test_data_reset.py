import json
import os
import subprocess
import sys
import time

from pokemind import data_location, data_reset


def owner_data(root):
    local = root / 'data/local'
    (local / 'chat').mkdir(parents=True)
    (local / 'chat/preferences.json').write_text('{"language": "fr"}', encoding='utf-8')
    (local / 'battle_logs').mkdir()
    (local / 'battle_logs/partie-inventee.txt').write_text('Tour 1 inventé', encoding='utf-8')
    (local / 'web_memory.sqlite3').write_bytes(b'invented')
    (local / '.gitkeep').write_text('', encoding='utf-8')
    return local


def names(folder):
    return sorted(child.name for child in folder.iterdir())


def test_reset_keeps_a_dated_copy_by_default_and_runs_once(local_tmp):
    local = owner_data(local_tmp)
    assert data_reset.pending(local_tmp) is None and data_reset.apply(local_tmp) is None
    data_reset.request(local_tmp, True)
    result = data_reset.apply(local_tmp)
    copy = local / result['kept_copy'].replace('\\', '/').rsplit('/', 1)[-1]
    assert result['status'] == 'RESET' and result['items'] == 3 and not result['erased']
    assert copy.name.startswith(data_reset.COPY_PREFIX) and names(copy) == ['battle_logs', 'chat', 'web_memory.sqlite3']
    assert (copy / 'battle_logs/partie-inventee.txt').read_text(encoding='utf-8') == 'Tour 1 inventé'
    assert names(local) == ['.gitkeep', copy.name]  # nothing left that a first launch would read
    assert data_reset.apply(local_tmp) is None


def test_reset_without_copy_erases_but_never_touches_an_earlier_copy(local_tmp):
    local = owner_data(local_tmp)
    earlier = local / (data_reset.COPY_PREFIX + '20261101-120000')
    earlier.mkdir()
    (earlier / 'ancienne.txt').write_text('copie inventée', encoding='utf-8')
    leftover = local / (data_reset.TRASH_PREFIX + 'inventee')
    (leftover / 'reste').mkdir(parents=True)
    locked = local / 'chat/lecture-seule.json'
    locked.write_text('{}', encoding='utf-8')
    os.chmod(locked, 0o444)  # read-only, as Git or an engine leave some files: erased too
    data_reset.request(local_tmp, False)
    result = data_reset.apply(local_tmp)
    assert result['status'] == 'RESET' and result['erased'] and result['kept_copy'] is None and not result['leftover']
    assert names(local) == ['.gitkeep', earlier.name]
    assert (earlier / 'ancienne.txt').read_text(encoding='utf-8') == 'copie inventée'


def test_a_locked_file_puts_everything_back_and_erases_nothing(local_tmp, monkeypatch):
    local = owner_data(local_tmp)
    before = names(local)
    real = data_reset._move
    def move(source, target, attempts, wait):
        if source.name == 'chat':
            raise PermissionError('invented lock')
        real(source, target, attempts, wait)
    monkeypatch.setattr(data_reset, '_move', move)
    data_reset.request(local_tmp, False)
    result = data_reset.apply(local_tmp)
    assert result == {'status': 'FAILED', 'error': 'PermissionError', 'erased': False, 'kept_copy': None,
                      'full': True, 'categories': list(data_reset.CATEGORIES), 'blocked': 'chat'}
    assert names(local) == sorted(set(before))  # battle_logs came back, the request is gone: no retry loop
    assert (local / 'battle_logs/partie-inventee.txt').exists() and (local / 'chat/preferences.json').exists()


def test_an_invalid_request_is_ignored(local_tmp):
    local = owner_data(local_tmp)
    for content in ('pas du json', json.dumps({'schema_version': 1, 'keep_copy': 'oui'}), json.dumps([1])):
        (local / data_reset.REQUEST).write_text(content, encoding='utf-8')
        assert data_reset.pending(local_tmp) is None and data_reset.apply(local_tmp) is None
    assert (local / 'chat/preferences.json').exists()


def test_reset_waits_for_the_closing_window(local_tmp):
    owner_data(local_tmp)
    closing = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(1.2)'])
    try:
        data_reset.request(local_tmp, True, pid=closing.pid)
        started = time.monotonic()
        assert data_reset.apply(local_tmp)['status'] == 'RESET'
        assert time.monotonic() - started >= 0.8 and closing.poll() is not None
    finally:
        closing.wait(10)


def every_kind(root):
    local = owner_data(root)
    (local / 'battle-intelligence/my-decks').mkdir(parents=True)
    (local / 'battle-intelligence/my-decks/deck-inventé.json').write_text('{}', encoding='utf-8')
    (local / 'battle-intelligence/report-2026-11-03.json').write_text('{}', encoding='utf-8')
    (local / ('chat/conversation-' + 'a' * 32 + '.json')).write_text('{}', encoding='utf-8')
    (local / 'chat/preferences.json').write_text(json.dumps(
        {'language': 'fr', 'conversations': [{'id': 'a' * 32}], 'current': 'a' * 32}), encoding='utf-8')
    (local / 'chat/sandbox').mkdir()
    (local / 'pokemind.sqlite3').write_bytes(b'invented')
    (local / 'pokemind.sqlite3-wal').write_bytes(b'invented')
    (local / 'public-campaigns/lot-i-catalog-snapshot-20261022').mkdir(parents=True)
    (local / 'public-campaigns/lot-i-battle-intelligence-20261103').mkdir(parents=True)
    (local / 'public-campaigns/battle-intelligence-index.jsonl').write_text('', encoding='utf-8')
    (local / 'card-images').mkdir()
    (local / 'logs').mkdir()
    (local / 'futur-inconnu.bin').write_bytes(b'invented')
    return local


def test_only_the_ticked_kinds_move_and_the_rest_stays(local_tmp):
    local = every_kind(local_tmp)
    data_reset.request(local_tmp, True, categories=['games'])
    result = data_reset.apply(local_tmp)
    copy = local / result['kept_copy'].replace('\\', '/').rsplit('/', 1)[-1]
    assert result['status'] == 'RESET' and not result['full'] and result['categories'] == ['games']
    assert names(copy) == ['battle-intelligence', 'battle_logs']
    assert names(copy / 'battle-intelligence') == ['report-2026-11-03.json']
    assert names(local / 'battle-intelligence') == ['my-decks']  # saved decks are another kind
    assert (local / 'chat/preferences.json').exists() and (local / 'pokemind.sqlite3').exists()


def test_discussions_without_preferences_empty_the_saved_list_only(local_tmp):
    local = every_kind(local_tmp)
    data_reset.request(local_tmp, False, categories=['chats', 'decks'])
    result = data_reset.apply(local_tmp)
    assert result['status'] == 'RESET' and result['erased'] and result['categories'] == ['decks', 'chats']
    assert names(local / 'chat') == ['preferences.json']
    preferences = json.loads((local / 'chat/preferences.json').read_text(encoding='utf-8'))
    assert preferences == {'language': 'fr', 'conversations': [], 'current': None}
    assert not (local / 'battle-intelligence/my-decks').exists() and (local / 'battle_logs').exists()
    assert not [c for c in local.iterdir() if data_reset.kept_aside(c.name)]


def test_knowledge_and_public_data_split_the_public_folder(local_tmp):
    local = every_kind(local_tmp)
    data_reset.request(local_tmp, True, categories=['knowledge'])
    copy = local / data_reset.apply(local_tmp)['kept_copy'].replace('\\', '/').rsplit('/', 1)[-1]
    assert names(copy) == ['pokemind.sqlite3', 'pokemind.sqlite3-wal', 'public-campaigns', 'web_memory.sqlite3']
    assert names(copy / 'public-campaigns') == ['battle-intelligence-index.jsonl', 'lot-i-battle-intelligence-20261103']
    assert names(local / 'public-campaigns') == ['lot-i-catalog-snapshot-20261022']
    data_reset.request(local_tmp, True, categories=['public', 'technical', 'preferences'])
    copy = local / data_reset.apply(local_tmp)['kept_copy'].replace('\\', '/').rsplit('/', 1)[-1]
    assert names(copy) == ['card-images', 'chat', 'logs', 'public-campaigns'] and names(copy / 'chat') == ['preferences.json']
    assert (local / 'futur-inconnu.bin').exists()  # only « Tout » takes what PokeMind does not know


def test_every_kind_ticked_is_the_full_reset(local_tmp):
    local = every_kind(local_tmp)
    data_reset.request(local_tmp, False, categories=list(reversed(data_reset.CATEGORIES)))
    result = data_reset.apply(local_tmp)
    assert result['full'] and result['erased'] and names(local) == ['.gitkeep']


def test_unknown_kinds_are_refused(local_tmp):
    local = owner_data(local_tmp)
    for categories in ([], ['everything'], 'games'):
        try:
            data_reset.request(local_tmp, True, categories=categories)
        except ValueError as error:
            assert str(error) == 'RESET_CATEGORIES_INVALID'
        else:
            raise AssertionError(categories)
    (local / data_reset.REQUEST).write_text(json.dumps({'schema_version': 1, 'keep_copy': True,
                                                         'categories': ['games', 'invented']}), encoding='utf-8')
    assert data_reset.pending(local_tmp) is None and data_reset.apply(local_tmp) is None


def test_a_reset_copy_is_not_owner_data_to_offer_at_launch(local_tmp):
    local = local_tmp / 'data/local'
    (local / (data_reset.COPY_PREFIX + '20261103-090000')).mkdir(parents=True)
    (local / data_reset.REQUEST).write_text('{}', encoding='utf-8')
    assert not data_location.legacy_data(local_tmp)
    (local / 'chat').mkdir()
    assert data_location.legacy_data(local_tmp)
