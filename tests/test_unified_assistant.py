"""Unified journeys on invented data and bounded fake public endpoints."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pokemind import batch_public_research as research, opponent_observer as observer, competitive
from pokemind.assistant.sessions import Store
from pokemind.assistant import tools
from pokemind.assistant.tools import slash
from pokemind.assistant.codex_app_server import CodexAppServer
from pokemind.assistant.provider import ProviderAdapter, ProviderError
from pokemind.desktop.ingestion import split_message, validate
from pokemind.desktop.services import Services
from test_batch_public_research import Opener

TODAY = datetime.now(timezone.utc).astimezone().date().isoformat()
DECK = (Path(__file__).parent / 'fixtures/decks/valid_en.txt').read_text(encoding='utf-8')


@pytest.fixture(autouse=True)
def stable_research_clock(monkeypatch):
    # A full suite may cross Toronto midnight after module collection.
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromisoformat(TODAY + 'T12:00:00+00:00')
    monkeypatch.setattr(research, 'datetime', FixedDateTime)


@pytest.mark.parametrize('fixture', ['defeat_fr.txt', 'victory_en.txt'])
def test_log_plus_question_is_locally_separated_without_losing_the_log(fixture):
    raw = (Path(__file__).parent / 'fixtures/battle_logs' / fixture).read_text(encoding='utf-8').strip()
    question = 'Pourquoi cette défaite?\nReconstruis son deck et compare les variantes.'
    log, pending = split_message(raw + '\n\n' + question)
    assert pending == question
    assert validate(log)[0] is not None
    assert question not in log


def test_slash_commands_are_recognised_and_no_mode_is_guessed_from_words():
    assert not hasattr(tools, 'development_request') and not hasattr(tools, 'research_request')
    assert slash('Affiche mon statut Codex.') == 'status'
    assert slash('/status') == 'status'
    assert slash('Pourquoi je perds?') is None


def test_provider_refuses_development_without_explicit_privacy_acceptance(local_tmp):
    client = ProviderAdapter(local_tmp)
    client.session = 'invented-coach'
    with pytest.raises(ProviderError, match='PRIVACY_ACKNOWLEDGEMENT_REQUIRED'):
        client.configure(development=True)
    assert not client.development and client.session == 'invented-coach'
    client.configure(development=True, privacy_acknowledged=True)
    assert client.development
    with pytest.raises(ProviderError, match='PRIVACY_ACKNOWLEDGEMENT_REQUIRED'):
        client.configure(development=True, permission_mode='full')
    client.configure(development=False)
    assert not client.development


def test_existing_cloud_and_full_permissions_do_not_accept_shell_privacy(local_tmp):
    store = Store(local_tmp)
    store.write('preferences.json', {'cloud_consent':True, 'permission_mode':'full'})
    assert store.preferences()['development_privacy_acknowledgements'] == []
    store.write('preferences.json', {'development_privacy_acknowledgements':True})
    with pytest.raises(ValueError, match='CHAT_PREFERENCES_INVALID'):
        store.preferences()


def test_same_ui_conversation_retains_distinct_provider_and_permission_threads(local_tmp):
    store = Store(local_tmp)
    c = store.new('codex')
    identity = c['id']
    c.update(session='codex-coach', messages=[{'role':'user','content':'Invented question'}])
    store.switch(c, 'claude')
    c['session'] = 'claude-coach'
    store.switch(c, 'codex', 'development:workspace')
    assert c['session'] is None
    c['session'] = 'codex-development'
    store.switch(c, 'codex')
    assert c['id'] == identity and c['session'] == 'codex-coach' and len(c['messages']) == 1
    store.save(c)
    loaded = Store(local_tmp).load(identity)
    store.switch(loaded, 'claude')
    assert loaded['session'] == 'claude-coach'


def test_official_status_keeps_null_metrics_and_excludes_account_identity(local_tmp, monkeypatch):
    client = CodexAppServer(local_tmp)
    monkeypatch.setattr(client, '_connect', lambda: None)
    methods = []
    def rpc(method, params, **kwargs):
        methods.append(method)
        if method == 'account/read':
            return {'account': {'type':'chatgpt','planType':'invented','email':'invented@example.invalid'}}
        if method == 'account/rateLimits/read':
            return {'rateLimits': {'primary': {'usedPercent': 17, 'resetsAt': 123}, 'secondary': None}}
        return {'summary': {'lifetimeTokens': None}, 'dailyUsageBuckets': None}
    monkeypatch.setattr(client, '_rpc', rpc)
    result = client.status()
    assert len(methods) == 3 and result['limits']['rateLimits']['primary']['usedPercent'] == 17
    assert result['usage']['summary']['lifetimeTokens'] is None
    assert 'email' not in json.dumps(result) and result['model'] is None


def test_real_project_tool_uses_official_rpc_resolved_executable_and_selected_permission(local_tmp, monkeypatch):
    from pokemind.assistant import codex_app_server as wire
    client = CodexAppServer(local_tmp)
    client.development = True
    calls = []
    monkeypatch.setattr(wire.shutil, 'which', lambda _: 'C:/InventedRuntime/python.exe')
    def rpc(method, params, **kwargs):
        calls.append((method,params))
        return {'exitCode':0,'stdout':'invented test passed','stderr':''}
    monkeypatch.setattr(client, '_rpc', rpc)
    result = client.project_tool({'operation':'exec','command':['python','-c','assert True']})
    assert result['exitCode'] == 0 and calls[0][0] == 'command/exec'
    assert calls[0][1]['command'][0] == 'C:/InventedRuntime/python.exe'
    assert calls[0][1]['sandboxPolicy']['type'] == 'workspaceWrite'
    client.permission_mode = 'full'
    client.project_tool({'operation':'exec','command':['python','-c','assert True']})
    assert calls[-1][1]['sandboxPolicy']['type'] == 'dangerFullAccess'


@pytest.mark.parametrize('path',['../outside.txt','data/local/private.txt','.git/config','.env'])
def test_project_file_tools_refuse_private_or_outside_paths(local_tmp,path):
    client = CodexAppServer(local_tmp)
    client.development = True
    with pytest.raises(ValueError):
        client.project_tool({'operation':'write','path':path,'content':'invented'})


def test_refused_source_has_daily_cooldown_and_does_not_retry_on_next_question(local_tmp, monkeypatch):
    monkeypatch.setattr(research.time, 'sleep', lambda _: None)
    opener = Opener(status=429)
    first = research.research(local_tmp, as_of=TODAY, topic='card', identity='invented-1', opener=opener)
    second = research.research(local_tmp, as_of=TODAY, topic='card', identity='invented-1', opener=opener)
    assert first['status'] == 'PARTIAL' and second['status'] == 'SOURCE_COOLDOWN'
    assert len(opener.calls) == 1 and second['gets'] == 0


def test_research_memory_reopens_in_another_process_offline_without_duplicates(local_tmp, monkeypatch):
    monkeypatch.setattr(research.time, 'sleep', lambda _: None)
    opener = Opener()
    first = research.research(local_tmp, as_of=TODAY, topic='card', identity='invented-1', opener=opener)
    assert first['persisted'] and first['added'] == 2 and len(opener.calls) == 2
    again = research.research(local_tmp, as_of=TODAY, topic='card', identity='invented-1', opener=opener)
    assert again['gets'] == 0 and len(opener.calls) == 2
    script = ('import json,sys; from pokemind.batch_public_research import research; '
              'r=research(sys.argv[1],as_of=sys.argv[2],topic="card",identity="invented-1",offline=True); '
              'print(json.dumps({"gets":r["gets"],"facts":len(r["facts"])}))')
    result = subprocess.run([sys.executable, '-c', script, str(local_tmp), TODAY], capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == {'gets':0,'facts':2}
    assert len(research.knowledge_view(local_tmp, as_of=TODAY)['history']) == 2


def test_revised_source_retains_old_version_and_unverified_rules_are_not_promoted(local_tmp, monkeypatch):
    monkeypatch.setattr(research.time, 'sleep', lambda _: None)
    url = 'https://api.tcgdex.net/v2/en/cards/invented-1'
    for name in ('Invented first', 'Invented corrected'):
        research.refresh_public(local_tmp, as_of=TODAY, campaign=('1' if name.endswith('first') else '2') * 32,
            endpoints=[url], opener=Opener(body=json.dumps({'id':'invented-1','name':name}).encode()))
    view = research.knowledge_view(local_tmp, as_of=TODAY)
    assert len(view['history']) == 2 and len(view['facts']) == 1
    assert view['history'][0]['revision_status'] == 'superseded'
    assert view['facts'][0]['card']['name'] == 'Invented corrected'


def test_persistence_failure_cannot_return_a_success_receipt(local_tmp, monkeypatch):
    from pokemind import battle_batch
    original = battle_batch._new_file
    def fail(path, raw):
        if path.name == 'research.json':
            raise OSError('invented storage failure')
        return original(path, raw)
    monkeypatch.setattr(battle_batch, '_new_file', fail)
    monkeypatch.setattr(research.time, 'sleep', lambda _: None)
    with pytest.raises(OSError):
        research.research(local_tmp, as_of=TODAY, topic='card', identity='invented-1', opener=Opener())
    assert research.knowledge_view(local_tmp, as_of=TODAY)['facts'] == []


def reference(text=DECK):
    cards = list(competitive._card_map(text).values())
    return {'archetype':'Invented family', 'selector':'1:1','cards':cards,'export':text,
        'composition':{'source_urls':['https://example.invalid/invented'], 'date_range':['2026-01-01','2026-01-01']}}


def test_reconstruction_60_has_observations_and_unseen_cards_not_probabilities():
    ref = reference()
    card = ref['cards'][0]
    observed = [{'name':card['name'], 'minimum_quantity':1}]
    result = observer.reconstruct(observed, {'references':[ref]}, as_of=TODAY)
    candidate = result['variants'][0]
    assert candidate['total_cards'] == 60 and not candidate['is_exact_opponent_deck']
    assert candidate['probability'] is None and candidate['legality'] == 'unknown'
    assert any(c['status'] == 'probable_unconfirmed' for c in candidate['cards'])
    assert competitive.parse_deck_export(candidate['export']).total_cards == 60


def test_incompatible_observations_and_quantities_do_not_produce_fake_compatible_60():
    ref = reference()
    for seen in ([{'name':'Invented absent card','minimum_quantity':1}],
                 [{'name':ref['cards'][0]['name'],'minimum_quantity':99}]):
        result = observer.reconstruct(seen, {'references':[ref]}, as_of=TODAY)
        assert result['status'] == 'NO_COMPATIBLE_REFERENCE' and not result['variants']
        assert result['incompatible_references'][0]['contradictions']


def test_private_tools_and_unrequested_writes_are_refused(local_tmp):
    services = Services(local_tmp)
    for op in ('match','reconstruct','learning','collection'):
        assert services.tool_call({'operation':op}, 'public')['status'] == 'PRIVATE_CONTEXT_WITHHELD_BY_PREFERENCE'
    assert 'error' in services.tool_call({'operation':'research','topic':'meta'})
    assert 'error' in services.tool_call({'operation':'context','path':'../private'})


def test_candidate_is_validated_persisted_and_visible_without_changing_played_decks(local_tmp):
    services = Services(local_tmp)
    arguments = {'operation':'save_candidate', 'export_text':DECK}
    assert 'error' in services.tool_call(arguments, 'aggregates')
    services.candidate_allowed = True
    first = services.tool_call(arguments, 'aggregates')
    second = services.tool_call(arguments, 'aggregates')
    assert first == second and first['played_deck_changed'] is False
    options = Services(local_tmp).deck_options()
    assert len(options) == 1 and options[0]['export'] == DECK and options[0]['total'] == 60
    assert Services(local_tmp).tool_call({'operation':'decks'}, 'public')['decks'] == []


def test_annotation_correction_and_withdrawal_extend_the_existing_learning_loop(local_tmp):
    services = Services(local_tmp)
    services.report = {'matches':[{'match':'invented-match'}]}
    services.annotation_allowed = True
    assert services.annotate('Hypothèse inventée')['status'] == 'SAVED_OWNER_HYPOTHESIS'
    assert services.annotate('Hypothèse inventée')['status'] == 'ALREADY_KNOWN'
    assert services.annotate('Correction inventée')['history_preserved']
    reopened = Services(local_tmp)
    assert reopened.annotations('invented-match')[-1]['payload']['note'] == 'Correction inventée'
    assert reopened.tool_call({'operation':'learning'}, 'aggregates')['owner_annotations']
    assert services.annotate('Retrait inventé', withdraw=True)['status'] == 'WITHDRAWN'
    assert reopened.annotations('invented-match')[-1]['kind'] == 'withdrawn'
    assert services.report['matches'][0] == {'match':'invented-match'}


def test_public_network_errors_retain_last_good_snapshot(local_tmp, monkeypatch):
    monkeypatch.setattr(research.time, 'sleep', lambda _: None)
    url = 'https://api.tcgdex.net/v2/en/cards/invented-1'
    research.refresh_public(local_tmp, as_of=TODAY, campaign='1'*32, endpoints=[url], opener=Opener())
    research.refresh_public(local_tmp, as_of=TODAY, campaign='2'*32, endpoints=[url], opener=Opener(status=429))
    assert research.knowledge_view(local_tmp, as_of=TODAY)['facts'][0]['card']['name'] == 'Invented card'


def test_prepared_research_tool_reuses_the_write_receipt_without_second_search(local_tmp, monkeypatch):
    services = Services(local_tmp)
    receipt = {'status':'SAVED','persisted':True,'added':2,'updated':0,
        'already_known':0,'unverified':2,'facts':[]}
    calls = []
    def collect(*args, **kwargs):
        calls.append(kwargs)
        return receipt
    monkeypatch.setattr(research,'research',collect)
    context = services.prepare_question('Recherche les règles et mémorise les sources.', 'public', research=True)
    assert context['public_research']['added'] == 2
    assert services.tool_call({'operation':'research','topic':'meta'}) is receipt
    assert services.tool_call({'operation':'research','topic':'rules'}) is receipt
    assert len(calls) == 1 and services.last_research_receipt['added'] == 2
    services.prepare_question('Cherche sur le web les règles actuelles', 'public')  # words alone never collect
    assert services.last_research_receipt is None and len(calls) == 1
    assert services.tool_call({'operation':'research','topic':'rules'})['error'] == 'PUBLIC_RESEARCH_REQUIRES_OWNER_REQUEST'


def test_cancelled_collection_keeps_uncertain_write_outcome_without_a_success_claim(local_tmp, monkeypatch):
    services = Services(local_tmp)
    monkeypatch.setattr(research,'research',lambda *a, **k:(_ for _ in ()).throw(ValueError('BATCH_CANCELLED')))
    with pytest.raises(ValueError,match='BATCH_CANCELLED'):
        services.prepare_question('Recherche les règles.', 'public',cancelled=lambda:True,research=True)
    assert services.last_research_receipt == {'status':'INTERRUPTED','persisted':None}


def test_development_codex_keeps_native_instructions_and_repository_rules(local_tmp, monkeypatch):
    from pokemind.assistant import codex_app_server as wire
    captured, calls = [], []
    monkeypatch.setattr(wire, 'executable', lambda name: 'invented-codex')
    monkeypatch.setattr(wire, 'spawn', lambda argv, cwd: captured.append(argv) or pytest.skip('argv captured'))
    coach = CodexAppServer(local_tmp)
    with pytest.raises(pytest.skip.Exception):
        coach._connect_locked()
    assert 'project_doc_max_bytes=0' in captured[-1]
    client = CodexAppServer(local_tmp)
    client.development = True
    with pytest.raises(pytest.skip.Exception):
        client._connect_locked()
    assert 'project_doc_max_bytes=0' not in captured[-1] and 'include_environment_context=false' not in captured[-1]
    monkeypatch.setattr(client, '_connect', lambda: None)
    monkeypatch.setattr(client, '_rpc', lambda method, params, **k: calls.append(params) or {'thread': {'id': 'invented'}})
    client.start()
    assert 'baseInstructions' not in calls[0] and 'pokemind_project' in calls[0]['developerInstructions']
    assert 'project_doc_max_bytes' not in calls[0]['config'] and calls[0]['sandbox'] == 'workspace-write'
    coach.development = False
    monkeypatch.setattr(coach, '_connect', lambda: None)
    monkeypatch.setattr(coach, '_rpc', lambda method, params, **k: calls.append(params) or {'thread': {'id': 'invented'}})
    coach.start()
    assert calls[-1]['baseInstructions'] and calls[-1]['config']['project_doc_max_bytes'] == 0


def test_development_claude_appends_rules_and_loads_project_memory(local_tmp, monkeypatch):
    from pokemind.assistant import provider
    captured = []
    monkeypatch.setattr(provider, 'executable', lambda name: 'invented-claude')
    def spawn(argv, cwd):
        captured.append(argv)
        raise ProviderError('INVENTED_STOP')
    monkeypatch.setattr(provider, 'spawn', spawn)
    client = provider.ClaudeCode(local_tmp)
    for development in (False, True):
        client.development = development
        with pytest.raises(ProviderError):
            client.ask_stream('invented', [], lambda _: None)
    coach, agent = captured
    assert '--system-prompt' in coach and coach[coach.index('--setting-sources') + 1] == ''
    assert '--system-prompt' not in agent and '--append-system-prompt' in agent
    assert agent[agent.index('--setting-sources') + 1] == 'project,local'
    assert 'Read(./data/**)' in agent[agent.index('--settings') + 1]


def test_project_read_is_paginated_never_silently_truncated(local_tmp):
    client = CodexAppServer(local_tmp)
    client.development = True
    (local_tmp / 'big.py').write_text('x' * 40000, encoding='utf-8')
    first = client.project_tool({'operation': 'read', 'path': 'big.py'})
    assert first['truncated'] and first['total_chars'] == 40000 and len(first['content']) == 16000
    last = client.project_tool({'operation': 'read', 'path': 'big.py', 'offset': 32000})
    assert not last['truncated'] and last['next_offset'] is None and len(last['content']) == 8000
    with pytest.raises(ProviderError, match='PROJECT_OFFSET_INVALID'):
        client.project_tool({'operation': 'read', 'path': 'big.py', 'offset': -1})


def test_tool_activity_shows_commands_output_and_changed_files_once():
    pytest.importorskip('PySide6')
    from pokemind.desktop.window import tool_activity
    command = {'type': 'commandExecution', 'command': 'python -m pytest -q', 'exitCode': 1,
               'aggregatedOutput': 'invented failure\n'}
    assert tool_activity('item/started', command) is None
    shown = tool_activity('item/completed', command)
    assert 'python -m pytest -q' in shown and '1' in shown and 'invented failure' in shown
    change = {'type': 'fileChange', 'changes': [{'path': 'src/invented.py', 'kind': 'update'}]}
    assert 'src/invented.py' in tool_activity('item/completed', change)
    claude = {'type': 'tool_use', 'status': 'tool_use', 'name': 'Bash', 'summary': 'git status'}
    assert 'Bash' in tool_activity('item/completed', claude) and 'git status' in tool_activity('item/completed', claude)
    assert tool_activity('item/completed', dict(claude, status='tool_result')) is None
