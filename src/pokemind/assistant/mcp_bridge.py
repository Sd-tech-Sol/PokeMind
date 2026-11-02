"""Loopback MCP endpoint that gives Claude Code the same coach tools as Codex.

Codex receives pokemind_read/pokemind_tool as App Server dynamic tools. Claude
Code only takes custom tools from an MCP server, so the desktop process serves
those two tools itself: Streamable HTTP with plain JSON replies, bound to
127.0.0.1, behind a random per-process bearer token. Calls run through
tools.run_tool, the same path as Codex and the local model.
"""
from __future__ import annotations

import hmac
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from pokemind import __version__
from pokemind.assistant.tools import COACH_TOOLS, run_tool

SERVER_NAME = 'pokemind'
PROTOCOLS = ('2025-11-25', '2025-06-18', '2025-03-26', '2024-11-05')
MAX_BODY = 1024 * 1024


class CoachToolBridge:
    def __init__(self):
        self.token = secrets.token_urlsafe(32)
        self.handler = None  # set per question: the same callable Codex receives
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), _Handler)
        self.server.daemon_threads = True
        self.server.bridge = self
        self.thread = threading.Thread(target=self.server.serve_forever, name='pokemind-mcp', daemon=True)
        self.thread.start()

    @property
    def url(self):
        return f'http://127.0.0.1:{self.server.server_port}/mcp'

    def config(self):
        return json.dumps({'mcpServers': {SERVER_NAME: {'type': 'http', 'url': self.url,
                           'headers': {'Authorization': 'Bearer ' + self.token}}}})

    @staticmethod
    def allowed_tools():
        return ','.join(f'mcp__{SERVER_NAME}__{tool["name"]}' for tool in COACH_TOOLS)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(3)

    def dispatch(self, message):
        """One JSON-RPC message; None for a notification."""
        if not isinstance(message, dict) or message.get('jsonrpc') != '2.0':
            return {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32600, 'message': 'Invalid Request'}}
        method, params, ident = message.get('method'), message.get('params') or {}, message.get('id')
        if ident is None:
            return None
        if method == 'initialize':
            wanted = params.get('protocolVersion')
            result = {'protocolVersion': wanted if wanted in PROTOCOLS else PROTOCOLS[0],
                      'capabilities': {'tools': {'listChanged': False}},
                      'serverInfo': {'name': SERVER_NAME, 'version': __version__}}
        elif method == 'ping':
            result = {}
        elif method == 'tools/list':
            result = {'tools': [{'name': t['name'], 'description': t['description'],
                                 'inputSchema': t['inputSchema']} for t in COACH_TOOLS]}
        elif method == 'tools/call':
            value, success = run_tool(params.get('name'), params.get('arguments') or {}, self.handler)
            result = {'content': [{'type': 'text', 'text': json.dumps(value, ensure_ascii=False)}],
                      'isError': not success}
        else:
            return {'jsonrpc': '2.0', 'id': ident, 'error': {'code': -32601, 'message': 'Method not found'}}
        return {'jsonrpc': '2.0', 'id': ident, 'result': result}


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _refuse(self, code):
        self.send_response(code)
        self.send_header('Content-Length', '0')
        self.end_headers()

    def _allowed(self):
        bridge = self.server.bridge
        host = self.headers.get('Host', '')
        authorization = self.headers.get('Authorization', '')
        # Loopback only, no browser origin, and the per-process token (DNS rebinding, other local pages).
        return (self.path.split('?')[0] == '/mcp' and host in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}
                and not self.headers.get('Origin')
                and hmac.compare_digest(authorization.encode(), ('Bearer ' + bridge.token).encode()))

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self._refuse(400)
        if not 0 < length <= MAX_BODY:
            return self._refuse(413)
        # Read before any refusal: a reply sent over an unread body resets the socket on
        # Windows, and the client then sees a connection error instead of the status.
        raw = self.rfile.read(length)
        if not self._allowed():
            return self._refuse(403)
        try:
            message = json.loads(raw)
        except ValueError:
            return self._refuse(400)
        bridge = self.server.bridge
        replies = ([r for r in map(bridge.dispatch, message) if r] if isinstance(message, list)
                   else [r for r in [bridge.dispatch(message)] if r])
        if not replies:
            return self._refuse(202)
        body = json.dumps(replies if isinstance(message, list) else replies[0], ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        # No server-initiated stream: every reply travels in its POST response.
        self._refuse(405 if self._allowed() else 403)

    def do_DELETE(self):
        self._refuse(200 if self._allowed() else 403)
