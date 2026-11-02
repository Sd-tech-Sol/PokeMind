"""Invented catalog and loopback peers: every coach engine gets the same tools.

No real card data, no cloud call. Covers the four defects behind "les outils
PokeMind sont indisponibles": rotation windows closing, text-ranked old/Pocket
printings, a validate_deck call that always failed, and engines without tools.
"""
import json
import logging
import sqlite3
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from pokemind import coach_cards, rules
from pokemind.assistant import codex_app_server as codex, mcp_bridge, provider, tools
from pokemind.database import connect_writable, initialize_schema
from pokemind.desktop.services import Services
from pokemind.public_deck_preflight import SCOPED_PUBLIC_CACHES

NOW = '2026-10-22T00:00:00Z'
LATER = '2026-10-29'
SETS = [('inv1', 'Invented Old', 'Invention Ancienne', 'sv', '2023-03-31', 'IVO'),
        ('inv2', 'Invented New', 'Invention Nouvelle', 'me', '2025-11-14', 'IVN'),
        ('pocket1', 'Invented Pocket', 'Poche Inventée', 'tcgp', '2025-01-01', None)]
PRINTINGS = [
    ('inv1-001', 'inv1', '001', 'pokemon', 'G', 'Invented Blaze ex', 'Flambo-ex inventé', None),
    ('inv2-013', 'inv2', '013', 'pokemon', 'I', 'Mega Invented Blaze X ex', 'Méga-Flambo X-ex inventé', None),
    ('inv2-022', 'inv2', '022', 'pokemon', 'J', 'Mega Invented Blaze Y ex', 'Méga-Flambo Y-ex inventé', None),
    ('inv2-099', 'inv2', '099', 'pokemon', 'K', 'Invented Blaze Future', 'Flambo futur inventé', None),
    ('inv2-150', 'inv2', '150', 'trainer', 'I', 'Invented Ball', 'Ball inventée', None),
    ('inv2-200', 'inv2', '200', 'energy', None, 'Basic Invented Fire Energy', 'Énergie Feu inventée de base', 'Normal'),
    ('pocket1-1', 'pocket1', '1', 'pokemon', None, 'Invented Blaze Pocket', 'Flambo poche inventé', None)]


def catalog(root):
    path = root / SCOPED_PUBLIC_CACHES[1]
    path.parent.mkdir(parents=True)
    connection = connect_writable(path)
    initialize_schema(connection)
    with connection:
        for sid, en, fr, series, released, code in SETS:
            connection.execute(
                "INSERT INTO catalog_sets(tcgdex_id,name_en,name_fr,series_id,release_date,tcg_online_code,"
                "abbreviation_official,discovered_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (sid, en, fr, series, released, code, code, NOW, NOW))
        for pid, sid, local, category, mark, en, fr, energy in PRINTINGS:
            connection.execute(
                "INSERT INTO catalog_printings(tcgdex_id,set_id,local_id,category,regulation_mark,discovered_at,"
                "updated_at,brief_source_url,brief_retrieved_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (pid, sid, local, category, mark, NOW, NOW, 'https://invalid.example/' + pid, NOW))
            for language, name in (('en', en), ('fr', fr)):
                connection.execute(
                    "INSERT INTO catalog_translations(printing_id,language,status,name,category,energy_type,source_url)"
                    " VALUES (?,?,?,?,?,?,?)", (pid, language, 'present', name, category, energy,
                                                'https://invalid.example/' + pid))
        # Observed on one day only, as the real review recorded it.
        connection.execute(
            "INSERT INTO official_rule_sources VALUES ('inv-rotation','official_page',"
            "'https://www.pokemon.com/invented-rotation','Invented rotation','en','2026-01-09',?,?,?,"
            "'verified','2026-10-22','2026-10-22','invented',NULL)", (NOW, NOW, 'a' * 64))
        connection.execute(
            "INSERT INTO official_rule_assertions VALUES ('inv-rot-live','inv-rotation','rotation','standard','live',"
            "'2026-10-22','2026-10-22',NULL,?,'verified','high',?)",
            (json.dumps({'allowed_regulation_marks': ['H', 'I', 'J'], 'rotation_effective_date': '2026-03-26'}), NOW))
    connection.close()
    return path


def test_presumption_survives_closed_observation_window(local_tmp):
    path = catalog(local_tmp)
    strict = rules.check_card(path, 'inv2-013', format='standard', platform='live', as_of=LATER)
    assert strict['status'] == 'unknown' and strict['reason_codes'] == ['NO_UNIQUE_ACTIVE_ROTATION']
    rotation = rules.latest_verified_rotation(path, format='standard', platform='live', as_of=LATER)
    assert rotation['allowed_regulation_marks'] == ['H', 'I', 'J']
    assert (rotation['in_force_since'], rotation['last_verified_on']) == ('2026-03-26', '2026-10-22')
    assert rules.presume_mark('I', rotation)['status'] == 'presumed_legal'
    assert rules.presume_mark('G', rotation)['reason'] == 'MARK_ROTATED_OUT'
    assert rules.presume_mark('K', rotation)['reason'] == 'MARK_NEWER_THAN_VERIFIED_ROTATION'
    assert rules.presume_mark(None, rotation)['status'] == 'unknown'
    assert '2026-10-22' in rules.presume_mark('I', rotation)['basis']
    assert rules.latest_verified_rotation(path, format='standard', platform='live', as_of='2026-01-01') is None


def test_coach_search_ranks_playable_printings_and_drops_pocket(local_tmp):
    path = catalog(local_tmp)
    found = coach_cards.find_cards(path, 'crée-moi un deck puissant avec Flambo', as_of=LATER)
    ids = [card['tcgdex_id'] for card in found['cards']]
    assert 'pocket1-1' not in ids
    assert ids[:2] == ['inv2-013', 'inv2-022'] and found['cards'][0]['export'] == 'Mega Invented Blaze X ex IVN 013'
    statuses = {card['tcgdex_id']: card['standard'] for card in found['cards']}
    assert statuses['inv1-001'] == 'presumed_not_legal' and statuses['inv2-099'] == 'unknown'
    assert coach_cards.find_cards(path, 'Méga-Flambo Y-ex', as_of=LATER)['cards'][0]['tcgdex_id'] == 'inv2-022'
    energy = coach_cards.find_cards(path, 'Énergie Feu inventée de base', as_of=LATER)['cards'][0]
    assert energy['standard'] == 'presumed_legal'
    assert coach_cards.find_cards(path, 'deck puissant', as_of=LATER)['cards'] == []


def export(pokemon):
    return f"Pokémon: 8\n4 Mega Invented Blaze X ex IVN 013\n4 {pokemon}\n\nTrainer: 4\n4 Invented Ball IVN 150\n\n" \
           "Energy: 48\n48 Basic Invented Fire Energy IVN 200\n"


def test_validate_deck_reports_fixable_problems(local_tmp):
    catalog(local_tmp)
    services = Services(local_tmp)
    rotated = services.tool_call({'operation': 'validate_deck', 'export_text': export('Invented Blaze ex IVO 001')})
    live = rotated['legality']['live']
    assert rotated['total_cards'] == 60 and live['presumed_status'] == 'presumed_not_legal'
    assert [(p['line'], p['reason']) for p in live['problems']] == [('4 Invented Blaze ex IVO 001', 'MARK_ROTATED_OUT')]
    fixed = services.tool_call({'operation': 'validate_deck', 'export_text': export('Mega Invented Blaze Y ex IVN 022')})
    assert fixed['legality']['live']['presumed_status'] == 'presumed_legal'
    assert fixed['legality']['live']['problems'] == [] and '2026-10-22' in fixed['presumption_basis']
    short = services.tool_call({'operation': 'validate_deck', 'export_text': 'Pokémon: 4\n4 Invented Ball IVN 150\n'})
    assert short['status'] == 'INVALID_EXPORT' and short['error']
    assert services.tool_call({'operation': 'legality'})['error'] == 'IDENTITY_REQUIRED'
    card = services.tool_call({'operation': 'legality', 'identity': 'inv2-013'})
    assert card['standard_presume']['live']['status'] == 'presumed_legal'
    batch = services.tool_call({'operation': 'cards', 'query': 'Méga-Flambo X; Ball inventée; Zorblax'})
    assert [r['cards'][0]['tcgdex_id'] if r['cards'] else None for r in batch['results']] == ['inv2-013', 'inv2-150', None]


def test_tool_runner_journals_outcome_not_content():
    records = []
    handler = logging.Handler()
    handler.emit = records.append
    logger = logging.getLogger('pokemind.coach')
    logger.addHandler(handler)
    previous = logger.level
    logger.setLevel(logging.INFO)
    try:
        def broken(arguments):
            raise sqlite3.OperationalError('invented failure')
        value, ok = tools.run_tool('pokemind_tool', {'operation': 'cards', 'query': 'secret-question'}, broken)
        assert not ok and value == {'error': 'READ_SERVICE_UNAVAILABLE', 'error_kind': 'OperationalError'}
        value, ok = tools.run_tool('pokemind_tool', '{"operation":"cards"}', lambda a: {'cards': ['x' * 30000]})
        assert not ok and value['error'] == 'CONTEXT_SIZE_CAP'
        assert tools.run_tool('shell', {}, lambda a: {})[0] == {'error': 'UNKNOWN_TOOL'}
        assert tools.run_tool('pokemind_read', {'query': 'q'}, lambda a: {'ok': True}) == ({'ok': True}, True)
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous)
    lines = [record.getMessage() for record in records]
    assert any('pokemind_tool/cards' in line and 'READ_SERVICE_UNAVAILABLE' in line for line in lines)
    assert not any('secret-question' in line for line in lines)


def post(bridge, message, token=None, origin=None):
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + (token or bridge.token)}
    if origin:
        headers['Origin'] = origin
    request = urllib.request.Request(bridge.url, data=json.dumps(message).encode(), headers=headers)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=5) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        return error.code, None


def test_mcp_bridge_serves_codex_tools_over_authenticated_loopback():
    assert codex.TOOL is tools.READ_TOOL and codex.ACTION_TOOL is tools.TOOL
    assert 'code_mode_host' in codex.REQUIRED and 'code_mode' in codex.DISABLED
    bridge = mcp_bridge.CoachToolBridge()
    calls = []
    bridge.handler = lambda arguments: calls.append(arguments) or {'cards': [{'nom': 'Carte inventée'}]}
    try:
        assert bridge.url.startswith('http://127.0.0.1:')
        assert post(bridge, {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}, token='wrong')[0] == 403
        assert post(bridge, {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}, origin='https://invalid.example')[0] == 403
        status, reply = post(bridge, {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                                      'params': {'protocolVersion': '2025-06-18', 'capabilities': {}}})
        assert status == 200 and reply['result']['protocolVersion'] == '2025-06-18'
        assert post(bridge, {'jsonrpc': '2.0', 'method': 'notifications/initialized'})[0] == 202
        listed = post(bridge, {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'})[1]['result']['tools']
        assert [t['name'] for t in listed] == [t['name'] for t in tools.COACH_TOOLS] == ['pokemind_read', 'pokemind_tool']
        assert listed[1]['inputSchema'] == codex.ACTION_TOOL['inputSchema']
        called = post(bridge, {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {
            'name': 'pokemind_tool', 'arguments': {'operation': 'cards', 'query': 'Flambo'}}})[1]['result']
        assert calls == [{'operation': 'cards', 'query': 'Flambo'}] and called['isError'] is False
        assert json.loads(called['content'][0]['text']) == {'cards': [{'nom': 'Carte inventée'}]}
        assert post(bridge, {'jsonrpc': '2.0', 'id': 4, 'method': 'resources/list'})[1]['error']['code'] == -32601
        assert 'mcp__pokemind__pokemind_tool' in bridge.allowed_tools()
    finally:
        bridge.close()


def test_mcp_bridge_refusals_arrive_as_403_not_as_connection_resets():
    # Refusing before reading the body reset 1 socket in 7 on Windows (WinError 10053).
    bridge = mcp_bridge.CoachToolBridge()
    try:
        message = {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/list'}
        codes = [post(bridge, message, token='wrong')[0] for _ in range(150)]
        codes += [post(bridge, message, origin='https://invalid.example')[0] for _ in range(150)]
        assert codes == [403] * 300
    finally:
        bridge.close()


# The invented Claude peer reads its own --mcp-config and calls the bridge, as Claude Code does.
FAKE_CLAUDE = r'''
import json, sys, urllib.request
argv = json.loads(sys.argv[1]); sys.stdin.readline()
config = json.loads(argv[argv.index('--mcp-config') + 1])['mcpServers']['pokemind']
body = json.dumps({'jsonrpc': '2.0', 'id': 7, 'method': 'tools/call',
                   'params': {'name': 'pokemind_tool', 'arguments': {'operation': 'cards', 'query': 'Flambo'}}}).encode()
request = urllib.request.Request(config['url'], data=body, headers=dict(config['headers'], **{'Content-Type': 'application/json'}))
reply = json.loads(urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request, timeout=5).read())
text = json.loads(reply['result']['content'][0]['text'])['cards'][0]['nom']
for event in ({'type': 'system', 'session_id': '22222222-2222-4222-8222-222222222222'},
              {'type': 'stream_event', 'event': {'delta': {'type': 'text_delta', 'text': text}}},
              {'type': 'result', 'is_error': False}):
    print(json.dumps(event), flush=True)
'''


def test_claude_coach_gets_same_tools_without_safe_mode_or_memory(local_tmp, monkeypatch):
    script = local_tmp / 'invented-claude.py'
    script.write_text(FAKE_CLAUDE, encoding='utf-8')
    original, captured = provider.spawn, []

    def spawn(argv, cwd):
        captured.append(argv)
        return original([sys.executable, '-u', str(script), json.dumps(argv)], cwd)
    monkeypatch.setattr(provider, 'spawn', spawn)
    monkeypatch.setattr(provider, 'executable', lambda name: 'invented-claude')
    client = provider.ClaudeCode(local_tmp)
    calls, out = [], []
    try:
        client.ask_stream('Flambo?', [], out.append, tool=lambda a: calls.append(a) or {'cards': [{'nom': 'Flambo inventé'}]})
        assert out == ['Flambo inventé'] and calls == [{'operation': 'cards', 'query': 'Flambo'}]
        argv = captured[0]
        assert '--safe-mode' not in argv and argv[argv.index('--tools') + 1] == ''
        assert argv[argv.index('--system-prompt') + 1] == provider.COACH_SYSTEM
        assert argv[argv.index('--allowedTools') + 1] == 'mcp__pokemind__pokemind_read,mcp__pokemind__pokemind_tool'
        assert json.loads(argv[argv.index('--settings') + 1]) == {'autoMemoryEnabled': False, 'disableAllHooks': True}
        assert '--strict-mcp-config' in argv and argv[argv.index('--setting-sources') + 1] == ''
    finally:
        client.close()
    assert client.bridge is None



def test_claude_in_the_project_folder_keeps_folder_rules_native_tools_and_coach_tools(local_tmp, monkeypatch):
    script = local_tmp / 'invented-claude.py'
    script.write_text(FAKE_CLAUDE, encoding='utf-8')
    original, captured = provider.spawn, []

    def spawn(argv, cwd):
        captured.append((argv, cwd))
        return original([sys.executable, '-u', str(script), json.dumps(argv)], cwd)
    monkeypatch.setattr(provider, 'spawn', spawn)
    monkeypatch.setattr(provider, 'executable', lambda name: 'invented-claude')
    client = provider.ClaudeCode(local_tmp / 'sandbox')
    client.configure(development=True, permission_mode='workspace', cwd=local_tmp, privacy_acknowledged=True,
                     coach_tools=True)
    calls, out = [], []
    try:
        client.ask_stream('Flambo?', [], out.append, tool=lambda a: calls.append(a) or {'cards': [{'nom': 'Flambo inventé'}]})
        assert out == ['Flambo inventé'] and calls == [{'operation': 'cards', 'query': 'Flambo'}]
        argv, cwd = captured[0]
        assert cwd == local_tmp and argv[argv.index('--setting-sources') + 1] == 'project,local'
        assert '--system-prompt' not in argv and argv[argv.index('--append-system-prompt') + 1] == provider.PROJECT_SYSTEM
        assert argv[argv.index('--allowedTools') + 1] == (
            'Read,Edit,Write,Bash,Glob,Grep,mcp__pokemind__pokemind_read,mcp__pokemind__pokemind_tool')
        assert '--dangerously-skip-permissions' not in argv
        assert json.loads(argv[argv.index('--settings') + 1])['permissions']['deny'][0] == 'Read(./data/**)'
    finally:
        client.close()
    client.configure(development=True, permission_mode='workspace', cwd=local_tmp, privacy_acknowledged=True)
    assert client.coach_tools is False  # explicit development without the default chat: no coach tools


class OllamaPeer(BaseHTTPRequestHandler):
    requests = []
    supports_tools = True

    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        type(self).requests.append(body)
        if 'tools' in body and not self.supports_tools:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b'{"error":"registry.invalid/invented does not support tools"}')
            return
        self.send_response(200)
        self.end_headers()
        if 'tools' in body and not any(m['role'] == 'tool' for m in body['messages']):
            rows = [{'message': {'content': '', 'tool_calls': [{'function': {
                'name': 'pokemind_tool', 'arguments': {'operation': 'cards', 'query': 'Flambo'}}}]}, 'done': True}]
        else:
            rows = [{'message': {'content': 'Liste '}}, {'message': {'content': 'inventée'}, 'done': True}]
        for row in rows:
            self.wfile.write((json.dumps(row) + '\n').encode())


@pytest.mark.parametrize('supports_tools', [True, False])
def test_local_model_runs_the_same_tool_loop(local_tmp, supports_tools):
    OllamaPeer.requests, OllamaPeer.supports_tools = [], supports_tools
    server = ThreadingHTTPServer(('127.0.0.1', 0), OllamaPeer)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = provider.LocalOllama(local_tmp, model='invented:small', endpoint='http://127.0.0.1:' + str(server.server_port))
    calls, out = [], []
    try:
        client.ask_stream('Flambo?', [], out.append, tool=lambda a: calls.append(a) or {'cards': []})
    finally:
        client.close()
        server.shutdown()
        server.server_close()
        thread.join(3)
    first = OllamaPeer.requests[0]
    assert [t['function']['name'] for t in first['tools']] == [t['name'] for t in tools.COACH_TOOLS]
    assert first['messages'][0]['content'] == provider.COACH_SYSTEM and ''.join(out) == 'Liste inventée'
    if supports_tools:
        assert calls == [{'operation': 'cards', 'query': 'Flambo'}]
        assert OllamaPeer.requests[1]['messages'][-1] == {'role': 'tool', 'tool_name': 'pokemind_tool', 'content': '{"cards": []}'}
    else:
        assert calls == [] and 'tools' not in OllamaPeer.requests[1]
        assert OllamaPeer.requests[1]['messages'][0]['content'] == provider.SYSTEM
