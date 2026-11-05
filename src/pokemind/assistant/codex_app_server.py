"""Codex CLI App Server stdio JSON-RPC, pinned to the installed wire schema."""
from __future__ import annotations

import json
import queue
import shutil
import threading
import time
import os
import sys
from pathlib import Path
import uuid

from pokemind import __version__
from pokemind.assistant.provider import (ProviderAdapter, ProviderError, COACH_WEB_SYSTEM, COACH_TIMEOUT, AGENT_SYSTEM,
    PROJECT_SYSTEM, executable, spawn)
from pokemind.assistant.tools import READ_TOOL as TOOL, TOOL as ACTION_TOOL, run_tool
DISABLED = ('shell_tool', 'unified_exec', 'code_mode', 'apps', 'plugins', 'hooks',
    'browser_use', 'browser_use_external', 'computer_use', 'view_image', 'image_generation',
    'skill_search', 'sleep_tool', 'workspace_dependencies')
# Codex 0.163 runs every tool call, dynamic PokeMind tools included, through this
# host; disabling it made each coach tool call fail with "code-mode host is disabled".
# code_mode itself (the model writing code) stays disabled above.
REQUIRED = ('code_mode_host',)
PROJECT_TOOL = {'type':'function', 'name':'pokemind_project',
    'description':'Actions de développement réellement exécutées dans le projet choisi. Utiliser cet outil pour lire/écrire un fichier et lancer commandes, tests et Git. Exec utilise command/exec officiel de Codex avec les permissions réelles sélectionnées. Aucun node_repl nécessaire.',
    'inputSchema':{'type':'object','properties':{
        'operation':{'type':'string','enum':['read','write','exec']},
        'path':{'type':'string','maxLength':240},
        'content':{'type':'string','maxLength':200000},
        'offset':{'type':'integer','minimum':0},
        'command':{'type':'array','minItems':1,'maxItems':80,'items':{'type':'string','maxLength':12000}}},
        'required':['operation'],'additionalProperties':False}}


class CodexAppServer(ProviderAdapter):
    def __init__(self, cwd):
        super().__init__(cwd)
        self.lock = threading.Lock()
        self.connection_lock = threading.RLock()
        self.pending = {}
        self.events = queue.Queue(maxsize=2048)
        self.counter = 0
        self.turn = None
        self.ready = False
        self.model = None
        self.token_usage = None
        self.last_error = None
        self.last_rpc_error = None
        self.command_process = None
        self.last_command_result = None
        self.last_command_argv = None
        self.last_project_error = None

    def project_tool(self, arguments):
        """Small frontend tool bridge; all process execution stays in Codex."""
        from pokemind.battle_batch import safe_path
        if not self.development or not isinstance(arguments, dict) or set(arguments) - {'operation','path','content','command','offset'}:
            raise ProviderError('PROJECT_ACTION_NOT_AUTHORIZED')
        op = arguments.get('operation')
        if op == 'exec':
            command = arguments.get('command')
            if not isinstance(command, list) or not 1 <= len(command) <= 80 or any(
                    not isinstance(v,str) or not v or '\x00' in v or len(v)>12000 for v in command):
                raise ProviderError('PROJECT_ARGV_INVALID')
            command = list(command)
            # CreateProcessAsUserW in the native Windows sandbox does not use
            # the interactive user's executable lookup (notably python/git).
            command[0] = shutil.which(command[0]) or command[0]
            self.command_process = 'pokemind-' + uuid.uuid4().hex
            params = {'command':command, 'cwd':str(self.cwd), 'processId':self.command_process,
                'timeoutMs':1800000, 'sandboxPolicy':{'type':'dangerFullAccess'} if self.permission_mode == 'full'
                    else {'type':'workspaceWrite', 'writableRoots':[str(self.cwd)], 'networkAccess':True}}
            try:
                result = self._rpc('command/exec', params, timeout=1810)
                if not isinstance(result, dict) or 'exitCode' not in result:
                    raise ProviderError('PROJECT_EXEC_RESULT_INVALID')
                self.last_command_result, self.last_command_argv = result, list(command)
                self.on_event({'method':'pokemind/projectResult','params':{'item':{
                    'type':'projectExecution','command':command, 'result':result, 'status':'completed'}}})
                return {k:result[k][:9000] if isinstance(result[k],str) else result[k]
                        for k in ('exitCode','stdout','stderr') if k in result} | {
                    'output_truncated':any(len(result.get(k,''))>9000 for k in ('stdout','stderr'))}
            finally:
                self.command_process = None
        if op not in {'read','write'}:
            raise ProviderError('PROJECT_OPERATION_INVALID')
        relative = arguments.get('path')
        if not isinstance(relative,str) or not relative or len(relative)>240:
            raise ProviderError('PROJECT_PATH_INVALID')
        part = Path(relative)
        if part.is_absolute() or '..' in part.parts or any(p.casefold() in {
                'data','.git','.codex','.env','auth.json','credentials.json'} for p in part.parts):
            raise ProviderError('PROJECT_PRIVATE_PATH_REFUSED')
        path = safe_path(Path(self.cwd), Path(self.cwd) / part, exists=False)
        if path.exists() and (not path.is_file() or path.stat().st_nlink != 1):
            raise ProviderError('PROJECT_FILE_ALIAS_REFUSED')
        if op == 'read':
            if path.stat().st_size > 200000:
                raise ProviderError('PROJECT_FILE_SIZE_CAP')
            from pokemind.legacy_bridge import _bytes
            raw, _ = _bytes(Path(self.cwd), path, maximum=200000)
            text = raw.decode('utf-8')
            offset = arguments.get('offset', 0)
            if type(offset) is not int or offset < 0:
                raise ProviderError('PROJECT_OFFSET_INVALID')
            part = text[offset:offset + 16000]
            more = offset + len(part) < len(text)
            # Never truncate silently: the model learns the size and the next offset.
            return {'path':relative, 'content':part, 'offset':offset, 'total_chars':len(text),
                    'truncated':more, 'next_offset':offset + len(part) if more else None}
        content = arguments.get('content')
        if not isinstance(content,str) or len(content.encode()) > 200000:
            raise ProviderError('PROJECT_CONTENT_INVALID')
        path.parent.mkdir(parents=True, exist_ok=True)
        safe_path(Path(self.cwd), path.parent)
        stamp = path.stat() if path.exists() else None
        temporary = path.with_name('.pokemind-edit-' + uuid.uuid4().hex + '.tmp')
        with temporary.open('x', encoding='utf-8', newline='') as stream:
            stream.write(content); stream.flush(); os.fsync(stream.fileno())
        current = path.stat() if path.exists() else None
        if (stamp is None) != (current is None) or stamp and (
                stamp.st_ino,stamp.st_size,stamp.st_mtime_ns) != (current.st_ino,current.st_size,current.st_mtime_ns):
            raise ProviderError('PROJECT_CONCURRENT_CHANGE_RESIDUE_PRESERVED')
        safe_path(Path(self.cwd), path, exists=False)
        os.replace(temporary, path)
        return {'path':relative,'status':'written','bytes':len(content.encode())}

    def _send(self, value):
        with self.lock:
            if not self.process or self.process.poll() is not None:
                raise ProviderError('CODEX_DISCONNECTED')
            self.process.stdin.write(json.dumps(value, ensure_ascii=False) + '\n')
            self.process.stdin.flush()

    def _reader(self):
        try:
            for line in self.process.stdout:
                if len(line) > 4*1024*1024:
                    raise ValueError
                value = json.loads(line)
                if 'id' in value and 'method' not in value:
                    waiter = self.pending.get(value['id'])
                    if waiter:
                        waiter.put(value)
                else:
                    self.events.put(value, timeout=2)
        except (OSError, ValueError, queue.Full):
            pass
        finally:
            self.ready = False
            for waiter in list(self.pending.values()):
                waiter.put({'error': {'code': 'CODEX_DISCONNECTED'}})
            try:
                self.events.put({'method': 'pokemind/disconnected'}, timeout=1)
            except queue.Full:
                pass

    def _rpc(self, method, params, timeout=30):
        with self.lock:
            self.counter += 1
            identity = self.counter
            waiter = self.pending[identity] = queue.Queue()
        try:
            self._send({'id': identity, 'method': method, 'params': params})
            try:
                value = waiter.get(timeout=timeout)
            except queue.Empty:
                raise ProviderError('CODEX_TIMEOUT') from None
            if 'error' in value:
                self.last_rpc_error = value['error']
                raise ProviderError('CODEX_RPC_FAILED')
            return value.get('result', {})
        finally:
            self.pending.pop(identity, None)

    def _connect(self):
        with self.connection_lock:
            self._connect_locked()

    def _connect_locked(self):
        if self.ready and self.process and self.process.poll() is None:
            return
        args = [executable('codex'), 'app-server', '--stdio']
        disabled = tuple(f for f in DISABLED if not self.development or f not in {'shell_tool', 'unified_exec'})
        for feature in disabled:
            args += ['-c', 'features.' + feature + '=false']
        for feature in REQUIRED:
            args += ['-c', 'features.' + feature + '=true']
        if self.development:
            args += ['-c', 'features.shell_tool=true', '-c', 'features.unified_exec=true']
        # Live web search in every channel (owner, 2026-11-03); the coach still has no shell.
        args += ['-c', 'mcp_servers={}', '-c', 'web_search="live"', '-c', 'include_apps_instructions=false',
                 '-c', 'features.skip_host_skill_discovery=true']
        if not self.development:
            # The Pokemon coach sees no repository rules or environment. Development
            # keeps the AGENTS.md, environment and permission context, as in a terminal.
            args += ['-c', 'include_environment_context=false', '-c', 'include_permissions_instructions=false',
                     '-c', 'project_doc_max_bytes=0', '-c', 'skills.include_instructions=false']
        self.process = spawn(args, self.cwd)
        self.reader_thread = threading.Thread(target=self._reader, daemon=True)
        self.reader_thread.start()
        self._rpc('initialize', {'clientInfo': {'name': 'pokemind_desktop', 'title': 'PokeMind', 'version': __version__},
            'capabilities': {'experimentalApi': True}})
        self._send({'method': 'initialized', 'params': {}})
        self.ready = True

    def status(self):
        """Official account metrics, with explicit missing fields; never model text."""
        self._connect()
        result = {'source': 'Codex App Server', 'model': self.model,
                  'session': bool(self.session), 'token_usage': self.token_usage,
                  'permissions': self.permission_mode if self.development else 'PokeMind tools only'}
        for method, key in [('account/read', 'account'), ('account/rateLimits/read', 'limits'),
                            ('account/usage/read', 'usage')]:
            try:
                value = self._rpc(method, {'refreshToken': False} if key == 'account' else {}, timeout=15)
                if key == 'account':
                    account = value.get('account') or {}
                    value = {'authenticated': bool(account), 'type': account.get('type'), 'planType': account.get('planType')}
                result[key] = value
            except ProviderError:
                result[key] = {'status': 'unavailable', 'method': method}
        return result

    def compact(self):
        if not self.session:
            raise ProviderError('CODEX_NO_ACTIVE_THREAD')
        return self._rpc('thread/compact/start', {'threadId': self.session})

    def health(self):
        try:
            executable('codex')
        except ProviderError:
            return {'available': False, 'status': 'Codex CLI non installé'}
        try:
            self._connect()
            result = self._rpc('account/read', {'refreshToken': False})
            account = result.get('account')
            return {'available': bool(account), 'status': 'Session Codex connectée' if account else 'Connexion Codex requise dans son terminal'}
        except (OSError, ProviderError):
            self.close()
            return {'available': False, 'status': 'Codex App Server indisponible ou connexion requise'}

    def start(self, session=None):
        self._connect()
        self.stopped.clear()
        system = (PROJECT_SYSTEM if self.coach_tools else AGENT_SYSTEM) if self.development else COACH_WEB_SYSTEM
        disabled = {f: False for f in DISABLED if not self.development or f not in {'shell_tool','unified_exec'}}
        disabled.update(dict.fromkeys(REQUIRED, True))
        if self.development:
            disabled.update(shell_tool=True, unified_exec=True)
        params = {'cwd': str(self.cwd), 'sandbox': 'read-only', 'approvalPolicy': 'on-request',
            'baseInstructions': system, 'developerInstructions': system,
            'config': {'mcp_servers': {}, 'web_search': 'live',
                       'include_environment_context': False, 'include_permissions_instructions': False,
                       'project_doc_max_bytes': 0,
                       'skills': {'include_instructions': False},
                       'features': {**disabled, 'skip_host_skill_discovery': True}}}
        if self.development:
            params['approvalPolicy'] = 'never'
            params['sandbox'] = 'danger-full-access' if self.permission_mode == 'full' else 'workspace-write'
            # Keep the native Codex base instructions (tools, patch format, working
            # style) and the repository AGENTS.md; PokeMind only adds its rules.
            del params['baseInstructions']
            params['config'] = {'mcp_servers': {}, 'web_search': 'live',
                                'features': {**disabled, 'skip_host_skill_discovery': True}}
        if session:
            params['threadId'] = session
            result = self._rpc('thread/resume', params)
        else:
            params.update(dynamicTools=([PROJECT_TOOL, TOOL, ACTION_TOOL] if self.coach_tools else [PROJECT_TOOL])
                          if self.development else [TOOL, ACTION_TOOL])
            if not self.development:
                params['environments'] = []
            result = self._rpc('thread/start', params)
        self.session = result['thread']['id']
        self.model = result.get('model')

    def ask_stream(self, prompt, history, emit, tool=None):
        self.stopped.clear()
        if not self.session:
            self.start()
        while True:
            try:
                self.events.get_nowait()
            except queue.Empty:
                break
        params = {'threadId': self.session,
            'input': [{'type': 'text', 'text': prompt, 'text_elements': []}],
            'sandboxPolicy': {'type': 'readOnly', 'networkAccess': False}, 'approvalPolicy': 'on-request'}
        if self.development:
            params['approvalPolicy'] = 'never'
            params['sandboxPolicy'] = {'type':'dangerFullAccess'} if self.permission_mode == 'full' else {
                'type':'workspaceWrite', 'writableRoots':[str(self.cwd)], 'networkAccess':True}
        response = self._rpc('turn/start', params)
        self.turn = response['turn']['id']
        if self.stopped.is_set():
            self.cancel()
            return
        start, received = time.monotonic(), 0
        while True:
            if time.monotonic() - start > (1800 if self.development else COACH_TIMEOUT):
                self.cancel()
                raise ProviderError('CODEX_TIMEOUT')
            if self.stopped.is_set() and self.turn is None:
                return
            try:
                item = self.events.get(timeout=.2)
            except queue.Empty:
                continue
            method, params = item.get('method'), item.get('params', {})
            if params.get('threadId', self.session) != self.session:
                continue
            if 'id' in item:
                if method == 'item/tool/call' and params.get('tool') == 'pokemind_project':
                    try:
                        arguments = params.get('arguments', {})
                        if isinstance(arguments, str):
                            arguments = json.loads(arguments)
                        value = self.project_tool(arguments)
                        success = True
                    except (ValueError, OSError, ProviderError) as error:
                        self.last_project_error = {'code':str(error), 'rpc':self.last_rpc_error}
                        value, success = {'error':'PROJECT_ACTION_FAILED_OR_REFUSED'}, False
                    self._send({'id':item['id'],'result':{'contentItems':[{'type':'inputText',
                        'text':json.dumps(value,ensure_ascii=False)}],'success':success}})
                elif method == 'item/tool/call' and params.get('tool') in {'pokemind_read', 'pokemind_tool'} and tool:
                    value, success = run_tool(params['tool'], params.get('arguments', {}), tool)
                    self._send({'id': item['id'], 'result': {'contentItems': [{'type': 'inputText',
                        'text': json.dumps(value, ensure_ascii=False)}], 'success': success}})
                elif method in {'item/commandExecution/requestApproval', 'item/fileChange/requestApproval'}:
                    decision = self.approval(method, params) if self.development and self.approval else {'decision': 'decline'}
                    self._send({'id': item['id'], 'result': decision})
                else:
                    self._send({'id': item['id'], 'error': {'code': -32601, 'message': 'Lecture seule PokeMind; action refusée.'}})
            elif method == 'item/agentMessage/delta':
                delta = params.get('delta', '')
                received += len(delta)
                if received > 100000:
                    self.cancel()
                    raise ProviderError('PROVIDER_OUTPUT_SIZE_CAP')
                emit(delta)
            elif method == 'turn/completed':
                self.turn = None
                if params.get('turn', {}).get('status') not in {'completed', 'interrupted'}:
                    self.last_error = params.get('turn', {}).get('error')
                    raise ProviderError('CODEX_TURN_FAILED')
                return
            elif method == 'thread/tokenUsage/updated':
                self.token_usage = params.get('tokenUsage')
            elif method in {'item/started', 'item/completed', 'item/commandExecution/outputDelta', 'item/fileChange/outputDelta'}:
                if method == 'item/started' and received and params.get('item', {}).get('type') == 'agentMessage':
                    emit('\n\n')  # a message written after tool calls is a new paragraph, not glued on
                self.on_event({'method': method, 'params': params})
            elif method == 'pokemind/disconnected':
                raise ProviderError('CODEX_DISCONNECTED')

    def cancel(self):
        self.stopped.set()
        if self.command_process:
            try:
                self._rpc('command/exec/terminate', {'processId':self.command_process}, timeout=5)
            except (OSError, ProviderError):
                pass
        if self.session and self.turn and self.ready:
            try:
                self._rpc('turn/interrupt', {'threadId': self.session, 'turnId': self.turn}, timeout=5)
            except (OSError, ProviderError):
                pass
        self.turn = None

    def close(self):
        with self.connection_lock:
            self.cancel()
            super().close()
            if hasattr(self, 'reader_thread') and self.reader_thread is not threading.current_thread():
                self.reader_thread.join(3)
            self.ready = False
