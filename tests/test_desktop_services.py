"""Desktop service privacy and persistence using invented data only."""
import json
import os
from pathlib import Path

import pytest

from pokemind.assistant.sessions import Store
from pokemind.desktop.services import Services


def test_empty_services_never_initialize_or_create_owner_db(local_tmp, monkeypatch):
    from pokemind import database, battle_batch
    monkeypatch.setattr(database, 'initialize_schema', lambda *a: pytest.fail('no migration'))
    monkeypatch.setattr(battle_batch, 'batch_analyze', lambda *a, **k: pytest.fail('no automatic analysis'))
    result = Services(local_tmp).load()
    assert result['report'] is None
    assert not (local_tmp / 'data/local/pokemind.sqlite3').exists()


def test_cancel_before_analysis_never_writes_memory_or_db(local_tmp):
    from pokemind import battle_coach
    with pytest.raises(battle_coach.CoachError,match='COACH_CANCELLED'):
        battle_coach.coach(local_tmp,cancelled=lambda:True)
    assert not (local_tmp/'data/local/battle-intelligence').exists()


def test_batch_journals_each_phase_with_its_duration_and_never_content(local_tmp):
    # « 68 / 69 fichiers » stayed on screen for minutes: the journal now says which phase waits.
    import logging
    from pokemind import battle_batch
    folder=local_tmp/'data/local/battle_logs';folder.mkdir(parents=True)
    (folder/'invented.txt').write_text("Reference player: InventedSelf\nTurn # 1 - InventedSelf's Turn\n"
        "InventedSelf played Creature Alpha.\nTurn # 2 - InventedRival's Turn\nInventedRival played Creature Beta.\n"
        "InventedRival wins.\n",encoding='utf-8')
    lines,steps=[],[]
    class Keep(logging.Handler):
        def emit(self,record):
            lines.append(record.getMessage())
    logger,handler=logging.getLogger('pokemind.analysis'),Keep()
    previous=logger.level
    logger.addHandler(handler);logger.setLevel(logging.INFO)
    try:
        battle_batch.batch_analyze(local_tmp,folder=folder,player='InventedSelf',db=local_tmp/'data/local/pokemind.sqlite3',
            as_of='2026-10-25',progress=lambda done,total:steps.append((done,total)))
    finally:
        logger.removeHandler(handler);logger.setLevel(previous)
    assert [line.split(' · ')[1] for line in lines[:4]]==['contexte public','base locale','1 fichiers lus','familles et variantes publiques']
    assert all(line.startswith('Analyse · ') and line.endswith(' s') for line in lines)
    assert not any('Invented' in line or 'Creature' in line for line in lines)
    assert steps[:2]==[(0,1),(1,1)]


def test_batch_progress_cancel_keeps_original_and_does_not_publish_snapshot(local_tmp):
    import threading
    from pokemind import battle_batch
    folder=local_tmp/'data/local/battle_logs';folder.mkdir(parents=True)
    path=folder/'invented.txt'
    raw=("Reference player: Invented\nTurn # 1 - Invented's Turn\nInvented played Creature Alpha.\n"
         "Turn # 2 - Rival's Turn\nRival played Creature Beta.\nRival wins.\n").encode()
    path.write_bytes(raw)
    stopped=threading.Event();calls=[]
    def progress(done,total):
        calls.append((done,total));stopped.set()
    with pytest.raises(ValueError,match='BATCH_CANCELLED'):
        battle_batch.batch_analyze(local_tmp,folder=folder,player='Invented',db=local_tmp/'data/local/pokemind.sqlite3',
            as_of='2026-10-25',apply=True,cancelled=stopped.is_set,progress=progress)
    assert calls==[(0,1)] and path.read_bytes()==raw
    assert not (local_tmp/'data/local/battle-intelligence').exists()


def test_context_sharing_is_explicit_and_does_not_expose_private_records(local_tmp, monkeypatch):
    services = Services(local_tmp)
    services.report = {'as_of': '2026-10-25', 'coverage': {'valid': 6},
        'outcomes': {'wins': 2, 'losses': 4, 'unknown': 0}, 'groups': [
            {'archetype': 'Invented Family', 'wins': 2, 'losses': 4, 'unknown': 0, 'n': 6,
             'matches': ['invented-private-match'], 'source_name': 'invented-private.log'}],
        'matches': [{'actor': 'invented-private-name', 'evidence': 'invented-private-raw'}]}
    monkeypatch.setattr(services, 'search_cards', lambda *a: [])
    public = services.context('question', 'public')
    selected = services.context('question', 'aggregates')
    assert 'outcomes' not in public and 'valid_games' not in public
    assert selected['valid_games'] == 6 and selected['matchups'][0]['n'] == 6
    assert 'invented-private' not in json.dumps(selected)
    assert 'invented-private' not in json.dumps(public)


def test_read_tool_cannot_accept_sql_path_or_command(local_tmp):
    services = Services(local_tmp)
    for args in ({'path': '../invented'}, {'command': 'invented'}, {'sql': 'SELECT 1'}, []):
        assert services.read_tool(args, 'public')['error'] == 'READ_ONLY_QUERY_REQUIRED'


def test_huge_hostile_label_cannot_overrun_cloud_context_budget(local_tmp, monkeypatch):
    services = Services(local_tmp)
    services.report = {'as_of':'2026-10-25','coverage':{'valid':6},'outcomes':{'wins':0,'losses':6,'unknown':0},
        'groups':[{'archetype':'x'*100000,'wins':0,'losses':6,'unknown':0,'n':6}]}
    monkeypatch.setattr(services,'search_cards',lambda *a:[])
    assert len(json.dumps(services.context('question','aggregates')).encode()) <= 24000


def test_registered_version_history_reuses_engine_without_migration(local_tmp):
    import sqlite3
    from contextlib import closing
    from pokemind import battle_batch
    db=local_tmp/'data/local/pokemind.sqlite3';db.parent.mkdir(parents=True)
    with closing(sqlite3.connect(db)) as con:
        con.executescript((Path(__file__).parent/'fixtures/legacy_schema7.sql').read_text(encoding='utf-8'))
        for version in (1,2):
            con.execute("INSERT INTO deck_versions(deck_id,version_number,imported_at,approved_at,effective_from,parser_version,source_kind,export_sha256,list_sha256,total_cards,entry_count,exact_confirmed,sections_json,coverage_json) VALUES ('invented',?,? ,?,?,'invented','file',?,?,60,1,1,'{}','{}')",(version,'2026-10-25','2026-10-25','2026-10-25','invented'+str(version),'invented-list'+str(version)))
            con.execute("INSERT INTO deck_version_cards(deck_version_id,ordinal,source_line,card_type,quantity,card_name,normalized_line) VALUES(?,1,1,'energy',60,'Invented Energy','60 Invented Energy')",(version,))
        con.commit()
    before=db.read_bytes()
    preflight=battle_batch.database_preflight(local_tmp,db)
    latest=battle_batch.registered_decks(local_tmp,db,preflight,'2026-10-25')
    all_versions=battle_batch.registered_decks(local_tmp,db,preflight,'2026-10-25',all_versions=True)
    assert [r['version'] for r in latest]==[2]
    assert [r['version'] for r in all_versions]==[2,1]
    assert before==db.read_bytes()


def test_chat_preferences_and_history_survive_restart_without_auth_tokens(local_tmp):
    store = Store(local_tmp)
    prefs = store.preferences()
    assert prefs['provider'] == 'codex' and not prefs['cloud_consent']
    conversation = store.new('codex')
    conversation.update(session='invented-provider-thread', messages=[{'role': 'user', 'content': 'Question inventée'},
        {'role': 'assistant', 'content': 'Réponse inventée → sourcée'}])
    store.save(conversation)
    prefs.update(current=conversation['id'], conversations=[{'id': conversation['id'], 'title': 'Invented', 'provider': 'codex'}])
    store.write('preferences.json', prefs)
    fresh = Store(local_tmp)
    assert fresh.load(fresh.preferences()['current']) == conversation
    assert not (local_tmp / 'data/local/pokemind.sqlite3').exists()


def test_owner_deletes_one_conversation_and_nothing_else(local_tmp):
    store = Store(local_tmp)
    kept, erased = store.new('codex'), store.new('claude')
    for conversation in (kept, erased):
        conversation['messages'] = [{'role': 'user', 'content': 'Question inventée'}]
        store.save(conversation)
    assert store.delete(erased['id']) is True
    assert not store.path('conversation-' + erased['id'] + '.json').exists()
    assert store.load(kept['id']) == kept and store.delete(erased['id']) is False
    for identity in ('../preferences', 'preferences', 'A' * 32, None):
        with pytest.raises(ValueError):
            store.delete(identity)
    assert sorted(p.name for p in store.folder.iterdir()) == ['conversation-' + kept['id'] + '.json', 'sandbox']


@pytest.mark.parametrize('name', ['../private.json', 'conversation-no.json', '/outside.json', 'preferences.json:stream'])
def test_chat_control_paths_are_fixed(local_tmp, name):
    with pytest.raises(ValueError):
        Store(local_tmp).read(name)


def test_chat_hardlink_and_corrupt_history_refused(local_tmp):
    store = Store(local_tmp)
    conversation = store.new('codex')
    store.save(conversation)
    path = store.path('conversation-' + conversation['id'] + '.json')
    os.link(path, local_tmp / 'unselected.json')
    with pytest.raises(ValueError):
        store.load(conversation['id'])
    with pytest.raises(ValueError):
        store.write(path.name, conversation)


def test_chat_failure_does_not_replace_existing_history(local_tmp, monkeypatch):
    store = Store(local_tmp)
    conversation = store.new('ollama')
    store.save(conversation)
    before = store.path('conversation-' + conversation['id'] + '.json').read_bytes()
    def fail(*args):
        raise OSError('invented failure')
    monkeypatch.setattr(os, 'replace', fail)
    conversation['title'] = 'Changed'
    with pytest.raises(OSError):
        store.save(conversation)
    assert store.path('conversation-' + conversation['id'] + '.json').read_bytes() == before


def test_chat_invalid_settings_do_not_become_enabled_cloud(local_tmp):
    store = Store(local_tmp)
    store.write('preferences.json', {'cloud_consent': 'yes'})
    with pytest.raises(ValueError):
        store.preferences()


def test_unsupported_history_provider_cannot_be_resumed(local_tmp):
    store = Store(local_tmp)
    conversation = store.new('codex')
    conversation['provider'] = 'invented-arbitrary-shell'
    store.save(conversation)
    with pytest.raises(ValueError):
        store.load(conversation['id'])


def test_unchanged_snapshot_is_parsed_once_across_reloads(local_tmp, monkeypatch):
    from pokemind import battle_coach, legacy_bridge
    from test_desktop_ingestion import text
    folder = local_tmp/'data/local/battle_logs'; folder.mkdir(parents=True)
    (folder/'invented.txt').write_text(text(), encoding='utf-8')
    assert battle_coach.coach(local_tmp, player='InventedSelf', update=True, complete_only=True)['report']
    battle_coach._RANKS.clear()
    calls = []
    original = legacy_bridge.saved_report
    monkeypatch.setattr(legacy_bridge, 'saved_report', lambda *a, **k: calls.append(1) or original(*a, **k))
    services = Services(local_tmp)
    for _ in range(5):
        result = services.load()
    # One rank discovery parse and one selected projection, then cache hits.
    assert len(calls) == 2 and result['report']['coverage']['valid'] == 1
    assert services.report is result['report'] and services.match_index



def test_first_run_language_follows_the_system_and_a_saved_choice_wins(local_tmp, monkeypatch):
    from pokemind.assistant import sessions
    monkeypatch.setitem(sessions.DEFAULTS, 'language', None)
    monkeypatch.setattr(sessions, 'system_language', lambda: 'en')
    store = sessions.Store(local_tmp)
    assert store.preferences()['language'] == 'en'
    monkeypatch.setattr(sessions, 'system_language', lambda: 'fr')
    assert store.preferences()['language'] == 'fr'
    store.write('preferences.json', {'language': 'en'})
    assert store.preferences()['language'] == 'en'


def test_system_language_is_french_or_english():
    from pokemind.assistant.sessions import system_language
    assert system_language() in {'fr', 'en'}


def test_context_delta_pastes_only_what_changed_within_one_engine_session():
    from pokemind.desktop.services import context_delta
    first = {'source': 'invented', 'matchups': [{'archetype': 'Invented Family', 'n': 6}], 'public_cards': ['a']}
    payload, digests = context_delta(first)
    assert payload is first and set(digests) == set(first) and all(len(v) == 64 for v in digests.values())
    second = dict(first, public_cards=['b'])
    payload, again = context_delta(second, digests)
    assert payload['public_cards'] == ['b'] and 'source' not in payload and 'matchups' not in payload
    assert payload['unchanged_since_previous_message'] == ['matchups', 'source']
    assert 'operation=context' in payload['unchanged_note']
    assert set(context_delta(second, again)[0]) == {'unchanged_since_previous_message', 'unchanged_note'}
