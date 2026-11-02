"""Local diagnostic journal: rotating, redacted, never sent anywhere.

Exceptions used to become a bare code (LOCAL_SERVICE_UNAVAILABLE) with no trace.
This journal keeps the exception type, message and stack frames in
data/local/logs so an error can be triaged, after masking absolute paths,
the Windows user name and e-mail addresses. Battle-log text, prompts and model
answers are never logged by PokeMind code.
"""
from __future__ import annotations

import getpass
import logging
import logging.handlers
import platform
import re
import sys
import threading
from pathlib import Path

LOGGER = 'pokemind'
LOG_DIR = 'data/local/logs'
LOG_NAME = 'pokemind.log'
MAX_BYTES = 1024 * 1024
BACKUPS = 4
MAX_MESSAGE = 2000

_PATH = re.compile(r'(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/]|\\\\)[^\s"\'<>|]+')
_POSIX_HOME = re.compile(r'/(?:home|Users)/[^/\s"\']+')
_EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
_lock = threading.Lock()
_installed = None
_hooks = None


def redact(text, root=None):
    """Mask what identifies the owner's machine; keep file names for triage."""
    text = str(text)
    if root:
        text = text.replace(str(Path(root).absolute()), '<projet>')
    text = _PATH.sub(lambda m: '<chemin>/' + re.split(r'[\\/]', m[0].rstrip('\\/'))[-1], text)
    text = _POSIX_HOME.sub('<home>', text)
    text = _EMAIL.sub('<courriel>', text)
    try:
        user = getpass.getuser()
    except (OSError, KeyError, ImportError):
        user = ''
    if len(user) >= 3:
        text = re.sub(re.escape(user), '<utilisateur>', text, flags=re.I)
    return text[:MAX_MESSAGE * 4]


class RedactingFormatter(logging.Formatter):
    def __init__(self, root):
        super().__init__('%(asctime)s %(levelname)s %(name)s %(threadName)s · %(message)s')
        self.root = root

    def format(self, record):
        record = logging.makeLogRecord(record.__dict__)
        record.msg = str(record.getMessage())[:MAX_MESSAGE]
        record.args = None
        return redact(super().format(record), self.root)


def log_path(root):
    return Path(root).absolute() / LOG_DIR / LOG_NAME


def setup(root):
    """Install the journal once per process; failure to log never blocks the app."""
    global _installed, _hooks
    with _lock:
        if _installed is not None:
            return _installed
        logger = logging.getLogger(LOGGER)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        path = log_path(root)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.handlers.RotatingFileHandler(path, maxBytes=MAX_BYTES, backupCount=BACKUPS,
                                                           encoding='utf-8', delay=True)
        except OSError:
            handler = logging.NullHandler()
        handler.setFormatter(RedactingFormatter(root))
        logger.addHandler(handler)
        previous_hook, previous_thread_hook = _hooks = sys.excepthook, threading.excepthook

        def hook(kind, value, traceback):
            logger.critical('Exception non interceptée', exc_info=(kind, value, traceback))
            previous_hook(kind, value, traceback)

        def thread_hook(arguments):
            logger.error('Exception non interceptée dans un fil', exc_info=(
                arguments.exc_type, arguments.exc_value, arguments.exc_traceback))
            previous_thread_hook(arguments)

        sys.excepthook, threading.excepthook = hook, thread_hook
        from pokemind import __version__
        logger.info('Démarrage PokeMind %s · Python %s · %s', __version__, platform.python_version(),
                    platform.platform(terse=True))
        _installed = path
        return path


def get(name=''):
    return logging.getLogger(LOGGER + ('.' + name if name else ''))


def report(root, lines=200):
    """Text the owner can copy into a bug report: versions and the journal tail."""
    from pokemind import __version__
    header = [f'PokeMind {__version__}', f'Python {platform.python_version()} · {platform.platform(terse=True)}',
              f'Exécutable figé : {bool(getattr(sys, "frozen", False))}']
    try:
        import PySide6
        header.append(f'PySide6 {PySide6.__version__}')
    except ImportError:
        pass
    path = log_path(root)
    tail = []
    if path.is_file():
        with path.open(encoding='utf-8', errors='replace') as stream:
            tail = stream.readlines()[-lines:]
    body = ''.join(tail) if tail else 'Journal vide.\n'
    return redact('\n'.join(header) + '\n\n' + body, root)


def reset_for_tests():
    """Detach handlers so a test can install the journal in its own root."""
    global _installed, _hooks
    with _lock:
        logger = logging.getLogger(LOGGER)
        for handler in list(logger.handlers):
            logger.removeHandler(handler)
            handler.close()
        if _hooks:
            sys.excepthook, threading.excepthook = _hooks
        _installed = _hooks = None
