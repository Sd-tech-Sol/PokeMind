"""Reset PokeMind, entirely or by kind of data, on the owner's explicit request (owner, 2026-11-03).

The window only writes a request, closes, and starts PokeMind again. The next launch applies the request
before anything opens a file in data/local (diagnostic log, databases, chat), once the closing window's
process has ended. The chosen items are moved into a dated « avant-reinitialisation-… » folder inside
data/local, keeping their place in the tree. When the owner chose not to keep a copy, that folder is then
renamed to a hidden « .reinitialisation-… » folder and deleted; until every move succeeded, the data always
sits under the visible copy name. If one item cannot be moved, every item already moved goes back and
nothing is erased. Earlier copies are never moved again. The data folder itself stays, so a data location
chosen outside the project remains valid. Removing the preferences brings the welcome assistant back.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

from pokemind import battle_batch

LOCAL = 'data/local'
REQUEST = 'reset-request.json'
COPY_PREFIX = 'avant-reinitialisation-'
TRASH_PREFIX = '.reinitialisation-'
KEPT = ('.gitkeep',)
# Kinds of data the owner can pick; all of them together is the full reset (anything unknown goes too).
CATEGORIES = ('games', 'decks', 'chats', 'knowledge', 'public', 'preferences', 'technical')
MY_DECKS = 'battle-intelligence/my-decks'
PUBLIC = 'public-campaigns'
RESEARCH = re.compile(r'lot-i-battle-intelligence-.*|battle-intelligence-index\.jsonl|research-control\.json'
                      r'|chat-matchups\.json')
CONVERSATION = re.compile(r'conversation-[0-9a-f]{32}\.json|\.chat-.*\.tmp')
TECHNICAL = ('logs', 'update-logs', 'desktop-dev', 'demo-runs', 'test-runs', 'knowledge-update.lock')


def _writable(function, path, *_):
    try:
        os.chmod(path, stat.S_IWRITE)
        function(path)
    except OSError:
        pass


def remove_tree(path):
    """Delete a folder, read-only files too (left by Git or an engine); what stays locked stays."""
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_writable)
    else:
        shutil.rmtree(path, onerror=_writable)


def kept_aside(name):
    """Earlier reset copies and leftovers: never moved by a later reset nor counted as owner data at launch."""
    return name.startswith((COPY_PREFIX, TRASH_PREFIX))


def _local(root, *, exists=True):
    return battle_batch.safe_path(root, Path(root) / LOCAL, expected=LOCAL, exists=exists)


def _categories(value):
    if not isinstance(value, (list, tuple)) or not value or any(c not in CATEGORIES for c in value):
        raise ValueError('RESET_CATEGORIES_INVALID')
    return sorted(set(value), key=CATEGORIES.index)


def request(root, keep_copy, *, categories=CATEGORIES, pid=None):
    local = _local(root, exists=False)
    local.mkdir(parents=True, exist_ok=True)
    value = {'schema_version': 1, 'keep_copy': bool(keep_copy), 'categories': _categories(categories),
             'requested_at': datetime.now().isoformat(timespec='seconds')}
    if pid:
        value['pid'] = int(pid)
    temporary = local / (REQUEST + '.' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(value), encoding='utf-8')
    os.replace(temporary, local / REQUEST)
    return value


def pending(root):
    path = Path(root) / LOCAL / REQUEST
    try:
        if path.is_file() and not path.is_symlink() and path.stat().st_size <= 4096:
            value = json.loads(path.read_text(encoding='utf-8'))
            if isinstance(value, dict) and value.get('schema_version') == 1 and type(value.get('keep_copy')) is bool:
                value['categories'] = _categories(value.get('categories', list(CATEGORIES)))
                return value
    except (OSError, ValueError):
        pass
    return None


def _children(local, folder, wanted):
    path = local / folder
    if not path.is_dir() or path.is_symlink():
        return []
    return [Path(folder) / child.name for child in sorted(path.iterdir()) if wanted(child.name)]


def _database(local, name):
    """The database and its SQLite companions (-wal, -shm, -journal)."""
    return [Path(c.name) for c in sorted(local.iterdir()) if c.name == name or c.name.startswith(name + '-')]


def selection(local, categories):
    """Paths under data/local to move, relative to it. Every kind together = everything (full reset)."""
    chosen = set(categories)
    if chosen == set(CATEGORIES):
        return [Path(c.name) for c in sorted(local.iterdir()) if c.name not in KEPT + (REQUEST,) and not kept_aside(c.name)]
    paths = []
    if 'games' in chosen:
        paths += [Path('battle_logs')] + _children(local, 'battle-intelligence', lambda name: name != 'my-decks')
    if 'decks' in chosen:
        paths += [Path(MY_DECKS), Path('decks'), Path('deck-export.txt')]
    if 'chats' in chosen:
        paths += _children(local, 'chat', lambda name: name == 'sandbox' or bool(CONVERSATION.fullmatch(name)))
    if 'preferences' in chosen:
        paths.append(Path('chat/preferences.json'))
    if 'knowledge' in chosen:
        paths += _database(local, 'web_memory.sqlite3') + _database(local, 'pokemind.sqlite3')
        paths += _children(local, PUBLIC, lambda name: bool(RESEARCH.fullmatch(name)))
    if 'public' in chosen:
        paths += [Path('card-images')] + _children(local, PUBLIC, lambda name: not RESEARCH.fullmatch(name))
    if 'technical' in chosen:
        paths += [Path(name) for name in TECHNICAL]
    return [p for p in paths if (local / p).exists() or (local / p).is_symlink()]


def _wait_for_exit(pid, seconds):
    """Wait until the window that asked for the reset has ended (it may still be closing its files)."""
    if type(pid) is not int or not 0 < pid < 2 ** 32 or pid == os.getpid():
        return
    if sys.platform == 'win32':
        import ctypes
        kernel = ctypes.windll.kernel32
        handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE only
        if handle:
            try:
                kernel.WaitForSingleObject(handle, int(seconds * 1000))
            finally:
                kernel.CloseHandle(handle)
        return
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)  # POSIX only: signal 0 just checks existence
        except OSError:
            return
        time.sleep(0.2)


def _move(source, target, attempts, wait):
    for attempt in range(attempts):
        try:
            os.replace(source, target)
            return
        except PermissionError:  # a file may still be held for a moment
            if attempt == attempts - 1:
                raise
            time.sleep(wait)


def _copy_folder(local):
    stamp = COPY_PREFIX + datetime.now().strftime('%Y%m%d-%H%M%S')
    for suffix in [''] + ['-%d' % n for n in range(2, 100)]:
        target = local / (stamp + suffix)
        try:
            target.mkdir()
            return target
        except FileExistsError:
            continue
    raise FileExistsError(stamp)


def _forget_conversations(local, target):
    """Discussions removed, preferences kept: the saved list of discussions is emptied (original copied)."""
    path = local / 'chat/preferences.json'
    if not path.is_file() or path.is_symlink():
        return
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        return
    (target / 'chat').mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target / 'chat/preferences.json')
    value.update(conversations=[], current=None)
    temporary = path.with_name('.chat-' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def apply(root, *, attempts=40, wait=0.5, exit_wait=90):
    """Apply a pending request; returns None when there is none, else the outcome."""
    value = pending(root)
    if value is None:
        return None
    local = _local(root)
    (local / REQUEST).unlink()  # one attempt per request: a failure never repeats on every launch
    _wait_for_exit(value.get('pid'), exit_wait)
    categories = value['categories']
    full = set(categories) == set(CATEGORIES)
    target = _copy_folder(local)
    items = [p for p in selection(local, categories) if local / p != target]
    moved = []
    try:
        for item in items:
            (target / item).parent.mkdir(parents=True, exist_ok=True)
            _move(local / item, target / item, attempts, wait)
            moved.append(item)
        if 'chats' in categories and 'preferences' not in categories:
            _forget_conversations(local, target)
    except (OSError, ValueError) as error:
        stuck = []
        for item in reversed(moved):
            try:
                os.replace(target / item, local / item)
            except OSError:
                stuck.append(str(item))
        if not stuck:
            shutil.rmtree(target, ignore_errors=True)  # only the empty folders made for the copy remain
        blocked = items[len(moved)].as_posix() if len(moved) < len(items) else None
        return {'status': 'FAILED', 'error': type(error).__name__, 'erased': False, 'full': full,
                'categories': categories, 'kept_copy': str(target) if stuck else None, 'blocked': blocked}
    outcome = {'status': 'RESET', 'items': len(items), 'full': full, 'categories': categories}
    if value['keep_copy']:
        return outcome | {'erased': False, 'kept_copy': str(target)}
    trash = local / (TRASH_PREFIX + uuid.uuid4().hex)
    try:
        os.replace(target, trash)
    except OSError:
        trash = target
    remove_tree(trash)
    for leftover in local.iterdir():  # a hidden folder an earlier erase could not finish deleting
        if leftover.name.startswith(TRASH_PREFIX):
            remove_tree(leftover)
    return outcome | {'erased': True, 'kept_copy': None,
                      'leftover': any(c.name.startswith(TRASH_PREFIX) or c == target for c in local.iterdir())}
