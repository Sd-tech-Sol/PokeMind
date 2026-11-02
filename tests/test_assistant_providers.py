"""Real pipes and loopback HTTP to invented peers, no cloud/auth on CI."""
import json
import socket
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from pokemind.assistant import codex_app_server as codex, provider

FAKE = r'''
import json,sys
def send(v):print(json.dumps(v),flush=True)
turn=0
for line in sys.stdin:
 r=json.loads(line);m=r.get('method');p=r.get('params',{})
 if m=='initialize' or m=='turn/interrupt':
  send({'id':r['id'],'result':{}})
  if m=='turn/interrupt':send({'method':'turn/completed','params':{'threadId':'invented-thread','turn':{'id':'invented-turn','status':'interrupted'}}})
 elif m=='account/read':send({'id':r['id'],'result':{'account':{'type':'chatgpt','email':'invented@example.invalid'}}})
 elif m in ('thread/start','thread/resume'):send({'id':r['id'],'result':{'thread':{'id':'invented-thread'}}})
 elif m=='turn/start':
  turn+=1
  send({'id':r['id'],'result':{'turn':{'id':'invented-turn'}}})
  send({'id':100+turn,'method':'item/tool/call','params':{'threadId':'invented-thread','tool':'pokemind_read','arguments':{'query':'invented'}}})
 elif 'result' in r and r.get('id',0)>100:
  send({'method':'item/agentMessage/delta','params':{'threadId':'invented-thread','delta':'Réponse inventée.'}})
  if turn<3:send({'method':'turn/completed','params':{'threadId':'invented-thread','turn':{'id':'invented-turn','status':'completed'}}})
'''


@pytest.fixture
def fake_codex(local_tmp, monkeypatch):
    script = local_tmp / 'invented-peer.py'
    script.write_text(FAKE, encoding='utf-8')
    captured = []
    def spawn(argv, cwd):
        captured.append(argv)
        return provider.spawn([sys.executable, '-u', str(script)], cwd)
    monkeypatch.setattr(codex, 'spawn', spawn)
    monkeypatch.setattr(codex, 'executable', lambda name: 'invented-codex')
    monkeypatch.setattr(codex.shutil, 'which', lambda name: 'invented-codex')
    return codex.CodexAppServer(local_tmp), captured


def test_real_jsonrpc_pipes_handshake_tool_stream_multiturn_resume_cancel(fake_codex):
    client, commands = fake_codex
    reads, output = [], []
    try:
        assert client.health()['available']
        client.start()
        thread = client.session
        def tool(args):
            reads.append(args)
            return {'as_of': '2026-10-25', 'source': 'invented fixture', 'n': 6}
        client.ask_stream('invented', [], output.append, tool)
        client.resume(thread)
        client.ask_stream('invented second', [], output.append, tool)
        assert client.session == thread and len(output) == len(reads) == 2
        ready = threading.Event()
        errors = []
        def run():
            try:
                client.ask_stream('invented third', [], lambda s: ready.set(), tool)
            except Exception as e:
                errors.append(type(e).__name__)
        worker = threading.Thread(target=run)
        worker.start()
        assert ready.wait(5)
        client.cancel()
        worker.join(5)
        assert not worker.is_alive() and not errors
        assert client.stopped.is_set()
        argv = commands[0]
        assert '--yolo' not in argv and '--dangerously-bypass-approvals-and-sandbox' not in argv
        assert 'features.shell_tool=false' in argv and 'mcp_servers={}' in argv
        # Codex 0.163 runs dynamic tools through this host; code_mode itself stays off.
        assert 'features.code_mode_host=true' in argv and 'features.code_mode=false' in argv
        assert 'include_environment_context=false' in argv and 'project_doc_max_bytes=0' in argv
    finally:
        client.close()


def test_codex_unknown_rpc_error_is_neutral(fake_codex, monkeypatch):
    client, _ = fake_codex
    try:
        client._connect()
        with pytest.raises(provider.ProviderError, match='CODEX_TIMEOUT'):
            client._rpc('invented/unknown', {}, timeout=.05)
    finally:
        client.close()


def test_codex_health_and_first_message_share_one_managed_process(fake_codex):
    client, commands = fake_codex
    errors = []
    def start():
        try:
            client.start()
        except Exception as error:
            errors.append(type(error).__name__)
    worker = threading.Thread(target=start)
    try:
        worker.start()
        assert client.health()['available']
        worker.join(5)
        assert not worker.is_alive() and not errors and len(commands) == 1
    finally:
        client.close()


@pytest.mark.parametrize('endpoint', ['https://remote.invalid:11434', 'http://192.0.2.1:11434',
    'http://127.0.0.1:11434/private', 'http://user:secret@127.0.0.1:11434', 'http://localhost:11434?x=1'])
def test_ollama_refuses_remote_urls(endpoint, local_tmp):
    with pytest.raises(provider.ProviderError, match='OLLAMA_REMOTE_HOST_REFUSED'):
        provider.LocalOllama(local_tmp, endpoint=endpoint)


def test_real_loopback_ollama_protocol_lists_models_streams_and_keeps_history(local_tmp):
    requests = []
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass
        def do_GET(self):
            self.send_response(200);self.end_headers()
            self.wfile.write(json.dumps({'models':[{'name':'invented:small'}]}).encode())
        def do_POST(self):
            requests.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
            self.send_response(200);self.end_headers()
            for row in ({'message':{'content':'Salut '}},{'message':{'content':'inventé'},'done':True}):
                self.wfile.write((json.dumps(row)+'\n').encode());self.wfile.flush()
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    client = provider.LocalOllama(local_tmp, model='invented:small', endpoint='http://127.0.0.1:'+str(server.server_port))
    try:
        assert client.health()['models'] == ['invented:small']
        result=[]
        client.ask_stream('invented question',[{'role':'user','content':'invented past'}],result.append)
        assert ''.join(result)=='Salut inventé'
        assert requests[0]['messages'][1]['content']=='invented past'
        assert not client.cloud
    finally:
        client.close();server.shutdown();server.server_close();thread.join(3)


def test_claude_streaming_command_uses_no_tools_and_resumes(local_tmp, monkeypatch):
    script = local_tmp/'invented-claude.py'
    script.write_text('import sys,json\nsys.stdin.readline()\nfor r in [{"type":"system","session_id":"11111111-1111-4111-8111-111111111111"},{"type":"stream_event","event":{"delta":{"type":"text_delta","text":"Salut"}}},{"type":"result","is_error":False}]:print(json.dumps(r),flush=True)\n',encoding='utf-8')
    original, captured = provider.spawn, []
    def spawn(argv, cwd):
        captured.append(argv)
        return original([sys.executable,'-u',str(script)],cwd)
    monkeypatch.setattr(provider,'spawn',spawn)
    monkeypatch.setattr(provider,'executable',lambda name:'invented-claude')
    client=provider.ClaudeCode(local_tmp)
    try:
        out=[];client.start();client.ask_stream('invented',[],out.append)
        assert out==['Salut'] and client.session=='11111111-1111-4111-8111-111111111111'
        client.ask_stream('invented followup',[],out.append)
        assert '--resume' in captured[1] and '--tools' in captured[0]
        assert '--dangerously-skip-permissions' not in captured[0]
    finally:
        client.close()


def test_text_after_tool_calls_starts_a_new_paragraph_for_claude_and_codex(local_tmp, monkeypatch):
    # « …je relance validate_deck.J'ai monté une liste » was glued in the owner's chat.
    start = lambda kind: {'type':'stream_event','event':{'type':'content_block_start','content_block':{'type':kind}}}
    text = lambda value: {'type':'stream_event','event':{'type':'content_block_delta','delta':{'type':'text_delta','text':value}}}
    rows = [start('text'), text('Je vérifie.'), start('tool_use'), start('text'), text('Liste inventée'), {'type':'result','is_error':False}]
    script = local_tmp/'invented-claude-blocks.py'
    script.write_text('import sys,json\nsys.stdin.readline()\nfor r in ' + repr(rows) + ':print(json.dumps(r),flush=True)\n', encoding='utf-8')
    original = provider.spawn
    monkeypatch.setattr(provider,'spawn',lambda argv,cwd: original([sys.executable,'-u',str(script)],cwd))
    monkeypatch.setattr(provider,'executable',lambda name:'invented-claude')
    client = provider.ClaudeCode(local_tmp)
    try:
        out = [];client.ask_stream('invented',[],out.append)
        assert ''.join(out) == 'Je vérifie.\n\nListe inventée'
    finally:
        client.close()
    peer = local_tmp/'invented-codex-blocks.py'
    peer.write_text(r'''
import json,sys
def send(v):print(json.dumps(v),flush=True)
t={'threadId':'invented-thread'}
for line in sys.stdin:
 r=json.loads(line);m=r.get('method')
 if m=='initialize':send({'id':r['id'],'result':{}})
 elif m=='thread/start':send({'id':r['id'],'result':{'thread':{'id':'invented-thread'}}})
 elif m=='turn/start':
  send({'id':r['id'],'result':{'turn':{'id':'invented-turn'}}})
  send({'method':'item/started','params':dict(t,item={'type':'agentMessage'})})
  send({'method':'item/agentMessage/delta','params':dict(t,delta='Je vérifie.')})
  send({'method':'item/started','params':dict(t,item={'type':'dynamicToolCall'})})
  send({'method':'item/started','params':dict(t,item={'type':'agentMessage'})})
  send({'method':'item/agentMessage/delta','params':dict(t,delta='Liste inventée')})
  send({'method':'turn/completed','params':dict(t,turn={'id':'invented-turn','status':'completed'})})
''', encoding='utf-8')
    monkeypatch.setattr(codex,'spawn',lambda argv,cwd: original([sys.executable,'-u',str(peer)],cwd))
    monkeypatch.setattr(codex,'executable',lambda name:'invented-codex')
    client = codex.CodexAppServer(local_tmp)
    try:
        out = [];client.ask_stream('invented',[],out.append)
        assert ''.join(out) == 'Je vérifie.\n\nListe inventée'
    finally:
        client.close()


def test_hostile_claude_session_never_reaches_windows_command_arguments(local_tmp,monkeypatch):
    monkeypatch.setattr(provider,'spawn',lambda *a,**k:pytest.fail('no process for hostile session'))
    with pytest.raises(provider.ProviderError,match='CLAUDE_SESSION_INVALID'):
        provider.ClaudeCode(local_tmp).resume('bad&session')



@pytest.mark.parametrize('coach_tools', [True, False])
def test_codex_in_the_project_folder_loads_agents_md_and_adds_coach_tools(local_tmp, monkeypatch, coach_tools):
    client = codex.CodexAppServer(local_tmp / 'sandbox')
    calls = []
    monkeypatch.setattr(client, '_connect', lambda: None)
    monkeypatch.setattr(client, '_rpc', lambda method, params, **k: calls.append((method, params)) or {'thread': {'id': 'invented-thread'}})
    client.configure(development=True, permission_mode='full', cwd=local_tmp, privacy_acknowledged=True,
                     coach_tools=coach_tools)
    client.start()
    method, params = calls[0]
    assert method == 'thread/start' and params['cwd'] == str(local_tmp)
    assert params['sandbox'] == 'danger-full-access' and params['approvalPolicy'] == 'never'
    assert 'baseInstructions' not in params and 'project_doc_max_bytes' not in params['config']  # AGENTS.md is read
    names = [tool['name'] for tool in params['dynamicTools']]
    if coach_tools:
        assert names == ['pokemind_project', 'pokemind_read', 'pokemind_tool']
        assert params['developerInstructions'] == provider.PROJECT_SYSTEM
    else:
        assert names == ['pokemind_project'] and params['developerInstructions'] == provider.AGENT_SYSTEM
