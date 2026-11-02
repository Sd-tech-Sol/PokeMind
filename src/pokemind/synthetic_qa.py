"""Explicit synthetic QA process: checked paths and Python audit instrumentation.

This is not an OS sandbox. Normal product launches do not activate it. Only new
test roots are allocated; an explicit GUI resume may reopen its marked fixture.
"""
from __future__ import annotations

import json
import os
import re
import stat
import sys
import uuid
from pathlib import Path
from urllib.parse import unquote, urlsplit

PROJECT = Path(__file__).absolute().parents[2]
TASK = 'PM-V1-QA-RECOVERY-TO-MANUAL-OFFLINE-RECEPTION-001'
ROOT_ENV = 'POKEMIND_SYNTHETIC_QA_ROOT'
TOKEN_ENV = 'POKEMIND_SYNTHETIC_QA_TOKEN'
MARKER = 'SYNTHETIC_QA_PROCESS.json'
_ACTIVE = None


class SecurityIncident(BaseException):
    """An actual instrumented forbidden operation stops this process's work."""


def lexical(path):
    return Path(os.path.abspath(os.fsdecode(path)))


def no_alias(path, boundary, *, unlink_leaf=False):
    path, boundary = lexical(path), lexical(boundary)
    if not path.is_relative_to(boundary):
        raise ValueError('QA_PATH_OUTSIDE_BOUNDARY')
    for part in [boundary, *(boundary / p for p in reversed(path.relative_to(boundary).parents)), path]:
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('QA_REPARSE_REFUSED')
        if stat.S_ISREG(info.st_mode) and info.st_nlink != 1 and not (unlink_leaf and part == path):
            raise ValueError('QA_FILE_ALIAS_REFUSED')
    return path


def validate_root(path, *, project=PROJECT, fresh=False, purpose=None):
    project, root = lexical(project), lexical(path)
    if root.parent != project / 'build' or not re.fullmatch('qr-[0-9a-f]{8}', root.name):
        raise ValueError('QA_MARKED_ROOT_REQUIRED')
    no_alias(root, Path(project.anchor))
    marker = no_alias(root / MARKER, root)
    if not marker.is_file() or marker.stat().st_size > 512:
        raise ValueError('QA_MARKER_REQUIRED')
    value = json.loads(marker.read_text(encoding='utf-8'))
    if (not isinstance(value, dict) or set(value) != {'kind', 'root', 'token', 'purpose'}
            or value['kind'] != TASK or value['root'] != root.name
            or value['purpose'] not in {'tests', 'gui'}
            or not isinstance(value['token'], str) or not re.fullmatch('[0-9a-f]{32}', value['token'])
            or purpose is not None and purpose != value['purpose']):
        raise ValueError('QA_MARKER_REQUIRED')
    if root.resolve(strict=True) != root:
        raise ValueError('QA_NONCANONICAL_ROOT')
    if fresh and {p.name for p in root.iterdir()} != {MARKER}:
        raise ValueError('QA_ROOT_ALREADY_USED')
    return root, value


def new_root(*, project=PROJECT, purpose='tests', identifier=None):
    project = lexical(project)
    if purpose not in {'tests', 'gui'}:
        raise ValueError('QA_PURPOSE_REFUSED')
    no_alias(project / 'build', Path(project.anchor))
    (project / 'build').mkdir(exist_ok=True)
    name = 'qr-' + (identifier or uuid.uuid4().hex[:8])
    if not re.fullmatch('qr-[0-9a-f]{8}', name):
        raise ValueError('QA_ROOT_ID_INVALID')
    root = project / 'build' / name
    root.mkdir(exist_ok=False)
    marker = {'kind': TASK, 'root': name, 'purpose': purpose, 'token': uuid.uuid4().hex}
    with (root / MARKER).open('x', encoding='utf-8') as stream:
        json.dump(marker, stream)
    validate_root(root, project=project, fresh=True, purpose=purpose)
    return root, marker


def precheck(environ, modules):
    if environ.get(ROOT_ENV) or environ.get(TOKEN_ENV):
        raise ValueError('QA_BOOTSTRAP_ENV_COLLISION')
    if any(name == 'pytest' or name.startswith('_pytest') for name in modules):
        raise ValueError('QA_PYTEST_ALREADY_IMPORTED')


class Policy:
    def __init__(self, root):
        self.root = lexical(root)
        self.libraries = {lexical(sys.base_prefix), lexical(sys.prefix)}

    def event(self, event):
        if event.startswith('socket.') or event in {'urllib.Request', 'http.client.connect', 'http.client.send'}:
            raise PermissionError('QA_NETWORK_REFUSED')
        if event in {'subprocess.Popen', 'os.system', 'os.startfile', 'os.posix_spawn', 'os.exec', 'os.spawn'}:
            raise PermissionError('QA_PROCESS_REFUSED')

    def path(self, name, *, write=False, database=False, unlink_leaf=False):
        if isinstance(name, int) or os.fsdecode(name).lower() == os.devnull.lower():
            return None
        path = lexical(name)
        if (path.is_relative_to(PROJECT / 'data/local') or path.is_relative_to(PROJECT / 'dist')
                or path.is_relative_to(PROJECT.parent) and not path.is_relative_to(PROJECT)
                or path.name.startswith('.env')):
            raise PermissionError('QA_PRIVATE_NAMESPACE_REFUSED')
        if (write or database) and not path.is_relative_to(self.root):
            raise PermissionError('QA_WRITE_OR_DATABASE_OUTSIDE_ROOT')
        if not write and not database and not path.is_relative_to(PROJECT) and not any(path.is_relative_to(p) for p in self.libraries):
            raise PermissionError('QA_EXTERNAL_READ_REFUSED')
        if path.is_relative_to(self.root):
            no_alias(path, self.root, unlink_leaf=unlink_leaf)
        elif path.is_relative_to(PROJECT):
            no_alias(path, Path(PROJECT.anchor))
        return path


class Context:
    def __init__(self, root, marker):
        self.root, self.marker = root, marker
        self.pid = os.getpid()
        self.runtime_token = uuid.uuid4().hex
        self.temp = root / ('tmp-' + uuid.uuid4().hex[:8])
        self.log_file = root / ('pytest-' + uuid.uuid4().hex[:8] + '.log')
        self.policy = Policy(root)
        self.steps = ['marked_canonical_root_validated']
        self.denials = []
        self.security_incident = False
        self.tempfiles = []
        self.before_conftest = None
        self.allocations = []

    def audit(self, event, args):
        try:
            self.policy.event(event)
            if event == 'open':
                write = bool((args[2] or 0) & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
                self.policy.path(args[0], write=write)
            elif event == 'sqlite3.connect' and args[0] != ':memory:':
                value = os.fsdecode(args[0])
                if value.startswith('file:'):
                    value = unquote(urlsplit(value).path)
                    if os.name == 'nt' and re.match('^/[A-Za-z]:', value):
                        value = value[1:]
                self.policy.path(value, database=True)
            elif event == 'os.remove':
                # unlink removes this owned directory entry, never edits the
                # linked inode. Atomic publication legitimately leaves nlink=2.
                self.policy.path(args[0], write=True, unlink_leaf=True)
            elif event in {'os.mkdir', 'os.rmdir', 'os.chmod', 'os.utime', 'shutil.rmtree'}:
                self.policy.path(args[0], write=True)
            elif event in {'os.rename', 'os.link', 'os.symlink'}:
                self.policy.path(args[0], write=True); self.policy.path(args[1], write=True)
            elif event in {'os.listdir', 'os.scandir'} and args[0] is not None:
                self.policy.path(args[0])
            elif event == 'tempfile.mkstemp':
                path = self.policy.path(args[0], write=True)
                self.tempfiles.append(path.relative_to(self.root).as_posix())
        except (ValueError, PermissionError) as exc:
            # Full rejected targets remain local. Published receipts use categories.
            name = args[0] if args else ''
            raw = os.fsdecode(name) if isinstance(name, (str, bytes, os.PathLike)) else ''
            synthetic = bool(raw) and lexical(raw).is_relative_to(self.root)
            null_device = os.name == 'nt' and bool(raw) and lexical(raw) == lexical(os.devnull)
            # gethostname is local report metadata, not a connection. It is
            # still refused; the runner supplies a fictional JUnit identity.
            technical = ((synthetic and str(exc) not in {'QA_REPARSE_REFUSED', 'QA_FILE_ALIAS_REFUSED'})
                         or null_device or event == 'socket.gethostname')
            self.denials.append({'event': event, 'category': str(exc), 'target': raw, 'technical': technical})
            if not technical:
                self.security_incident = True
                raise SecurityIncident('QA_SECURITY_BOUNDARY') from None
            raise

    def validate_live(self):
        if os.environ.get(ROOT_ENV) != str(self.root) or os.environ.get(TOKEN_ENV) != self.runtime_token or self.pid != os.getpid():
            raise ValueError('QA_BOOTSTRAP_SESSION_MISMATCH')
        root, marker = validate_root(self.root, purpose=self.marker['purpose'])
        if marker != self.marker:
            raise ValueError('QA_MARKER_CHANGED')
        return root

    def allocate(self):
        self.validate_live()
        path = no_alias(self.root / uuid.uuid4().hex, self.root)
        path.mkdir(exist_ok=False)
        if path.resolve(strict=True).parent != self.root:
            raise ValueError('QA_ALLOCATION_NONCANONICAL')
        self.allocations.append(path.name)
        return path

    def summary(self):
        return {'workspace': self.root.relative_to(PROJECT).as_posix(), 'purpose': self.marker['purpose'],
                'steps': self.steps, 'capture_tempfiles_before_conftest': self.before_conftest,
                'tempfiles_in_workspace': len(self.tempfiles), 'fixture_allocations_in_workspace': len(self.allocations),
                'denials': [{'event': d['event'], 'category': d['category'], 'technical': d['technical']} for d in self.denials],
                'security_incident': self.security_incident, 'os_isolation_claimed': False,
                'real_source_gets': 0, 'real_provider_calls': 0}


def bootstrap(*, purpose='tests', resume=None):
    global _ACTIVE
    precheck(os.environ, sys.modules)
    if _ACTIVE is not None or Path.cwd().absolute() != PROJECT:
        raise ValueError('QA_FRESH_PROJECT_PROCESS_REQUIRED')
    if resume is not None:
        if purpose != 'gui':
            raise ValueError('QA_TEST_ROOT_REUSE_REFUSED')
        root, marker = validate_root(PROJECT / resume, purpose='gui')
    else:
        root, marker = new_root(purpose=purpose)
    context = Context(root, marker)
    context.temp.mkdir()
    for key in ('TEMP', 'TMP', 'TMPDIR'):
        os.environ[key] = str(context.temp)
    os.environ[ROOT_ENV], os.environ[TOKEN_ENV] = str(root), context.runtime_token
    os.environ['POKEMIND_TEST_OFFLINE'] = '1'
    os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
    os.environ['PYTEST_ADDOPTS'] = ''
    sys.dont_write_bytecode = True
    context.steps.append('child_environment_configured')
    import tempfile
    tempfile.tempdir = str(context.temp)
    if lexical(tempfile.gettempdir()) != context.temp:
        raise ValueError('QA_TEMP_BOOTSTRAP_MISMATCH')
    context.steps.append('tempfile_configured_before_pytest')
    _ACTIVE = context
    sys.addaudithook(context.audit)
    context.steps.append('python_instrumentation_installed')
    return context


def current():
    if _ACTIVE is None:
        raise ValueError('QA_EARLY_BOOTSTRAP_REQUIRED')
    return _ACTIVE


def optional():
    if not os.environ.get(ROOT_ENV):
        if os.environ.get(TOKEN_ENV):
            raise ValueError('QA_AMBIGUOUS_OPT_IN')
        return None
    return current()


def opt_in_root():
    context = optional()
    if context is None:
        return None
    root = context.validate_live()
    if context.before_conftest is None:
        context.before_conftest = len(context.tempfiles)
        context.steps.append('conftest_loaded_after_capture')
    return root
