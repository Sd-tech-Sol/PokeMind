"""Real CLI parser/formatters on the owned synthetic pair, without a child."""
import builtins
import io
import os
import socket
import sqlite3
import subprocess
import sys
from contextlib import ExitStack, redirect_stdout, redirect_stderr
from unittest.mock import patch

from pokemind import cli, public_deck_preflight as public, synthetic_qa as qa


def denied(*args, **kwargs):
    raise AssertionError('QA_CLI_FORBIDDEN_IO')


def call(root, args):
    context = qa.current()
    root = qa.lexical(root)
    if root.parent != context.root or root.name not in context.allocations:
        raise ValueError('QA_CLI_OWN_ALLOCATION_REQUIRED')
    qa.no_alias(root, context.root)
    if args[:2] != ['meta', 'public-identity-explain']:
        raise ValueError('QA_CLI_OPERATION_REFUSED')
    tail = iter(args[2:])
    for flag in tail:
        if flag in {'--as-of', '--selector'}:
            value = next(tail, None)
            if not isinstance(value, str) or len(value) > 128:
                raise ValueError('QA_CLI_ARGUMENT_REFUSED')
        elif flag not in {'--json', '--html'}:
            raise ValueError('QA_CLI_ARGUMENT_REFUSED')
    allowed = {os.path.normcase(str(root / p)) for p in public.SCOPED_PUBLIC_CACHES}
    uris = {(root / p).as_uri() + '?mode=ro&immutable=1' for p in public.SCOPED_PUBLIC_CACHES}
    readers, original_connect = (builtins.open, io.open, os.open), sqlite3.connect

    def opened(opener, name, *a, **kw):
        if isinstance(name, int) or os.path.normcase(os.path.abspath(name)) not in allowed:
            denied()
        mode = a[0] if a else kw.get('mode', 'r')
        write = (mode & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
                 if isinstance(mode, int) else any(flag in mode for flag in 'wax+'))
        if write:
            denied()
        return opener(name, *a, **kw)

    def connected(database, *a, **kw):
        if database not in uris or not kw.get('uri'):
            denied()
        return original_connect(database, *a, **kw)

    out, err = io.StringIO(), io.StringIO()
    with ExitStack() as stack:
        stack.enter_context(patch.object(os, 'getcwd', lambda: str(root)))
        for module, original in zip((builtins, io, os), readers):
            stack.enter_context(patch.object(module, 'open', lambda n, *a, _op=original, **k: opened(_op, n, *a, **k)))
        stack.enter_context(patch.object(sqlite3, 'connect', connected))
        for target, names in ((cli, ('find_project_root', 'default_db_path', '_db_for')),
                              (public, ('require_public_database',)),
                              (public.competitive, ('_advisor_snapshot',)),
                              (os, ('listdir', 'scandir', 'walk')),
                              (qa.Path, ('glob', 'rglob', 'iterdir')),
                              (socket, ('socket', 'create_connection', 'getaddrinfo'))):
            for name in names:
                stack.enter_context(patch.object(target, name, denied))
        stack.enter_context(patch.object(sys, 'stdin', io.StringIO('')))
        stack.enter_context(redirect_stdout(out)); stack.enter_context(redirect_stderr(err))
        try:
            code = cli.main(args)
        except SystemExit as exc:
            code = exc.code
    return subprocess.CompletedProcess(args, code, out.getvalue().encode('utf-8'), err.getvalue().encode('utf-8'))
