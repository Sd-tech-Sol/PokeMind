"""First card catalogue on a new PC: the pinned public TCGdex snapshot, fetched once and imported offline.

Two HTTPS GETs (the Git tree listing and the source archive at one pinned commit) replace thousands of
API pages. Every kept file is checked against its Git blob hash from the tree, then the existing offline
importer (public_catalog_snapshot) builds the PUBLIC catalogue where the app already reads it. Nothing
of the owner's is read or sent; upstream code is never executed. The temporary download is removed.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import tarfile
from datetime import datetime
from pathlib import Path, PurePosixPath
from urllib.request import HTTPRedirectHandler, Request, build_opener

from pokemind.cards import CatalogError
from pokemind.security import neutral_exception_code

REPOSITORY = 'tcgdex/cards-database'
COMMIT = 'cbddf7e54033b1b58e44af1049c88832e55b94d0'
CAMPAIGN = 'catalog-snapshot-20261022'  # the same pinned snapshot as the owner's catalogue, at the same path
TREE_URL = 'https://api.github.com/repos/' + REPOSITORY + '/git/trees/' + COMMIT + '?recursive=1'
ARCHIVE_URL = 'https://codeload.github.com/' + REPOSITORY + '/tar.gz/' + COMMIT
ARCHIVE_SIZE = 14_718_039  # measured on 2026-10-22; only a progress estimate, never a check
MAX_TREE, MAX_ARCHIVE, MAX_UNPACKED, MAX_FILE = 16 << 20, 32 << 20, 192 << 20, 131_072
LEFTOVER = re.compile(r'catalog-discovery-app-\d{8}-\d{6}')
STOPPED = ('IN_PROGRESS', 'OFFLINE_IMPORT_STOP', 'VALIDATION_INCOMPLETE_STOP')


def campaign_folder(root):
    return Path(root).absolute() / 'data/local/public-campaigns' / ('lot-i-' + CAMPAIGN)


def state(root):
    """'present' (the database the app reads exists), 'stopped' (an import cut short) or 'missing'."""
    folder = campaign_folder(root)
    if not folder.exists():
        return 'missing'
    try:
        status = json.loads((folder / 'snapshot-report.json').read_text(encoding='utf-8')).get('status')
    except (OSError, ValueError, AttributeError):
        status = None
    if status in STOPPED or not (folder / 'public.sqlite3').is_file():
        return 'stopped'
    return 'present'


def ready(root):
    return state(root) == 'present'


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise CatalogError('CATALOG_DOWNLOAD_REDIRECT_REFUSED')


def _open(url):
    if not url.startswith(('https://api.github.com/', 'https://codeload.github.com/')):
        raise CatalogError('CATALOG_DOWNLOAD_URL_REFUSED')
    request = Request(url, headers={'User-Agent': 'PokeMind-desktop', 'Accept': 'application/vnd.github+json'
                                    if 'api.github.com' in url else 'application/octet-stream'})
    return build_opener(_NoRedirect).open(request, timeout=30)


class _Bounded:
    """A response stream that stops at a byte ceiling, reports progress and honours cancellation."""

    def __init__(self, stream, maximum, step, cancelled):
        self.stream, self.maximum, self.step, self.cancelled, self.count = stream, maximum, step, cancelled, 0

    def read(self, size=-1):
        if self.cancelled():
            raise CatalogError('CATALOG_DOWNLOAD_CANCELLED')
        chunk = self.stream.read(65536 if size is None or size < 0 else min(size, 65536))
        self.count += len(chunk)
        if self.count > self.maximum:
            raise CatalogError('CATALOG_DOWNLOAD_TOO_LARGE')
        self.step(self.count)
        return chunk


def _git_blob(body):
    return hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest()


def _selected(tree):
    """The same files the offline importer expects: data/**/*.ts, the French labels and the licence."""
    if tree.get('truncated') is not False or not isinstance(tree.get('tree'), list):
        raise CatalogError('CATALOG_DOWNLOAD_TREE_INCOMPLETE')
    expected = {}
    for item in tree['tree']:
        path = item.get('path', '')
        if item.get('type') == 'blob' and (path.startswith('data/') and path.endswith('.ts')
                                           or path in {'LICENSE', 'meta/translations/fr.json'}):
            parts = PurePosixPath(path).parts
            if (item.get('mode') != '100644' or not 0 < item.get('size', 0) <= MAX_FILE
                    or any(p in {'.', '..'} or '\\' in p or ':' in p for p in parts)
                    or not re.fullmatch(r'[0-9a-f]{40}', str(item.get('sha', '')))):
                raise CatalogError('CATALOG_DOWNLOAD_TREE_ENTRY_REJECTED')
            expected[path] = item
    if not expected or len(expected) > 50_000:
        raise CatalogError('CATALOG_DOWNLOAD_TREE_VOLUME_REJECTED')
    return expected


def _unpack(stream, expected, output):
    """Keep only the expected regular files, each matching its Git blob hash, as JSON lines."""
    prefix = 'cards-database-' + COMMIT + '/'
    declared, seen = 0, set()
    with tarfile.open(fileobj=stream, mode='r|gz') as archive, output.open('w', encoding='utf-8', newline='\n') as lines:
        for member in archive:
            declared += max(member.size, 0)
            if declared > MAX_UNPACKED:
                raise CatalogError('CATALOG_DOWNLOAD_UNPACKED_TOO_LARGE')
            if member.name == prefix[:-1] and member.isdir():
                continue
            if not member.name.startswith(prefix):
                raise CatalogError('CATALOG_DOWNLOAD_ARCHIVE_ROOT_REJECTED')
            path = member.name[len(prefix):]
            item = expected.get(path)
            if item is None:
                continue
            if not member.isreg() or member.size != item['size'] or path in seen:
                raise CatalogError('CATALOG_DOWNLOAD_ARCHIVE_ENTRY_REJECTED')
            body = archive.extractfile(member).read(MAX_FILE + 1)
            if _git_blob(body) != item['sha']:
                raise CatalogError('CATALOG_DOWNLOAD_BLOB_MISMATCH')
            lines.write(json.dumps({'path': path, 'text': body.decode('utf-8')}, ensure_ascii=False) + '\n')
            seen.add(path)
    if seen != set(expected):
        raise CatalogError('CATALOG_DOWNLOAD_ARCHIVE_INCOMPLETE')
    return len(seen)


def download(root, *, progress=lambda phase, done, total: None, cancelled=lambda: False, fetch=_open):
    """Fetch and import the pinned public catalogue into root/data/local; returns a short receipt.

    `progress(phase, done, total)` runs on the calling thread: phases 'download' then 'import'.
    """
    root = Path(root).absolute()
    current = state(root)
    if current == 'present':
        return {'status': 'PRESENT', 'network_used': False}
    from pokemind.public_catalog_snapshot import import_snapshot
    local = root / 'data/local'
    local.mkdir(parents=True, exist_ok=True)
    for leftover in local.iterdir():  # downloads cut short by a closed app, never anything else
        if LEFTOVER.fullmatch(leftover.name) and leftover.is_dir() and not leftover.is_symlink():
            shutil.rmtree(leftover, ignore_errors=True)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    if current == 'stopped':  # an import cut short: set aside, never deleted or reused
        stopped = campaign_folder(root)
        stopped.rename(stopped.with_name('stopped-catalog-' + stamp))
    source = local / ('catalog-discovery-app-' + stamp)
    source.mkdir()
    received = 0
    try:
        with fetch(TREE_URL) as response:
            tree_body = _Bounded(response, MAX_TREE, lambda n: None, cancelled)
            tree_bytes = b''.join(iter(lambda: tree_body.read(), b''))
        expected = _selected(json.loads(tree_bytes))
        received += len(tree_bytes)
        with fetch(ARCHIVE_URL) as response:
            stream = _Bounded(response, MAX_ARCHIVE,
                              lambda n: progress('download', n, max(ARCHIVE_SIZE, n)), cancelled)
            files = _unpack(stream, expected, source / 'literal-source.jsonl')
            received += stream.count
        (source / 'tree.json').write_bytes(tree_bytes)
        (source / 'PUBLIC_SOURCE_ONLY.json').write_text(json.dumps({
            'schema_version': 1, 'kind': 'tcgdex_pinned_public_dataset', 'repository': REPOSITORY,
            'commit': COMMIT, 'tree_sha256': hashlib.sha256(tree_bytes).hexdigest()}), encoding='utf-8')
        if cancelled():
            raise CatalogError('CATALOG_DOWNLOAD_CANCELLED')
        progress('import', 0, files)
        report = import_snapshot(root, source, CAMPAIGN, execute=True, create=True)
    except (CatalogError, OSError, ValueError, tarfile.TarError) as error:
        return {'status': 'STOPPED', 'error': neutral_exception_code(error, 'CATALOG_DOWNLOAD'),
                'network_used': True, 'bytes': received}
    finally:
        shutil.rmtree(source, ignore_errors=True)
    complete = report.get('status') == 'PINNED_CATALOG_COMPLETE'
    return {'status': 'COMPLETE' if complete else 'STOPPED', 'error': None if complete else report.get('error') or report.get('status'),
            'network_used': True, 'bytes': received, 'printings': report.get('unique_printings'),
            'sets': report.get('sets'), 'commit': COMMIT}

