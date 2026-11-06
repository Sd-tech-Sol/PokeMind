"""Newer TCGdex cards from the app, in one click (owner, 2026-11-05: new sets such as Delta Reign).

check(): one tiny GitHub request gives the newest TCGdex commit. When it differs from the catalogue in use,
one request to the public TCGdex API lists the sets, compared with the local catalogue: new sets, and sets
that now have more cards. Nothing personal is sent.

update(): the newest commit is built in a staging folder inside data/local, with the same verified download
and offline importer as the first catalogue; it must be complete and hold at least about as many printings
as the catalogue in use. It is then put in place, and the catalogue it replaces is kept once
(data/local/catalog-previous) to go back. While a file of the catalogue in use is still open, the new one
waits, ready, and is put in place at the next launch (apply_pending, before the window opens).
"""
from __future__ import annotations

import json
import os
import shutil
import time
import uuid
from datetime import datetime
from pathlib import Path
from urllib.request import Request, build_opener

from pokemind import catalog_download
from pokemind.cards import CatalogError
from pokemind.database import connect_readonly
from pokemind.security import neutral_exception_code

SETS_URL = 'https://api.tcgdex.net/v2/en/sets'
STAGING = 'catalog-staging-'
READY = 'ready.json'
PREVIOUS = 'catalog-previous'
MAX_SETS = 8 << 20
SMALLER = 0.95  # a newer catalogue never loses more than a few printings
RECENT = 20  # the API lists sets by release; older special sets are counted differently (promos, jumbo)


def _open_api(url):
    if url != SETS_URL:
        raise CatalogError('CATALOG_UPDATE_URL_REFUSED')
    request = Request(url, headers={'User-Agent': 'PokeMind-desktop', 'Accept': 'application/json'})
    return build_opener(catalog_download._NoRedirect).open(request, timeout=20)


def _read(response, maximum):
    body = catalog_download._Bounded(response, maximum, lambda n: None, lambda: False)
    return b''.join(iter(lambda: body.read(), b''))


def local_counts(db):
    """{set id: printings} of a catalogue database, read-only."""
    connection = connect_readonly(db)
    try:
        counts = {str(row[0]): int(row[1]) for row in connection.execute(
            'SELECT set_id, COUNT(*) FROM catalog_printings GROUP BY set_id')}
        for row in connection.execute('SELECT tcgdex_id FROM catalog_sets'):
            counts.setdefault(str(row[0]), 0)
        return counts
    finally:
        connection.close()


def compare(sets, counts):
    """New sets, and recent sets with more cards than the local catalogue, from the TCGdex API set list."""
    new, grown = [], []
    sets = sets if isinstance(sets, list) else []
    recent = {item.get('id') for item in sets[-RECENT:] if isinstance(item, dict)}
    for item in sets:
        if not isinstance(item, dict) or not isinstance(item.get('id'), str):
            continue
        name = str(item.get('name') or item['id'])[:80]
        total = (item.get('cardCount') or {}).get('total')
        total = total if type(total) is int and 0 <= total < 10_000 else 0
        if item['id'] not in counts:
            new.append({'id': item['id'], 'name': name, 'cards': total})
        elif total > counts[item['id']] and item['id'] in recent:
            grown.append({'id': item['id'], 'name': name, 'added': total - counts[item['id']]})
    return new[:50], grown[:50]


def check(root, *, fetch=catalog_download._open, fetch_api=_open_api):
    """{'status': 'CURRENT' | 'AVAILABLE' | 'MISSING', ...}; network errors raise."""
    current = catalog_download.installed(root)
    if current is None:
        return {'status': 'MISSING'}  # the first download is offered by the catalogue row
    newest = catalog_download.latest_commit(fetch)
    if newest == current['commit']:
        return {'status': 'CURRENT', 'commit': newest, 'installed': current}
    result = {'status': 'AVAILABLE', 'commit': newest, 'installed': current, 'new_sets': [], 'grown_sets': []}
    try:
        with fetch_api(SETS_URL) as response:
            sets = json.loads(_read(response, MAX_SETS))
        db = catalog_download.campaign_folder(root) / 'public.sqlite3'
        result['new_sets'], result['grown_sets'] = compare(sets, local_counts(db))
    except (CatalogError, OSError, ValueError) as error:
        result['detail_error'] = neutral_exception_code(error, 'CATALOG_UPDATE')  # still updatable
    result['notable'] = bool(result['new_sets'] or result['grown_sets'])
    return result


def _move(source, target, attempts, wait):
    for attempt in range(attempts):
        try:
            os.replace(source, target)
            return True
        except PermissionError:  # the app may be reading the catalogue for a moment
            if attempt == attempts - 1:
                return False
            time.sleep(wait)
    return False


def _remove(path):
    from pokemind.data_reset import remove_tree
    if path.is_dir() and not path.is_symlink():
        remove_tree(path)


def _built(staging):
    return staging / 'data/local/public-campaigns' / ('lot-i-' + catalog_download.CAMPAIGN)


def activate(root, staging, *, attempts=20, wait=0.5):
    """Put a ready staging catalogue in place; the replaced one is kept once. False if still in use."""
    root = Path(root).absolute()
    new, target = _built(staging), catalog_download.campaign_folder(root)
    keep = root / 'data/local' / PREVIOUS
    old = None
    if target.exists():
        if keep.exists():  # only the last replaced catalogue is kept
            old = keep.with_name(PREVIOUS + '.old-' + uuid.uuid4().hex[:8])
            if not _move(keep, old, attempts, wait):
                return False
        keep.mkdir()
        if not _move(target, keep / target.name, attempts, wait):
            keep.rmdir()
            if old is not None:
                os.replace(old, keep)
            return False
    target.parent.mkdir(parents=True, exist_ok=True)
    if not _move(new, target, attempts, wait):
        if (keep / target.name).exists():
            os.replace(keep / target.name, target)
            keep.rmdir()
            if old is not None:
                os.replace(old, keep)
        return False
    for path in (staging, old):
        if path is not None:
            _remove(path)
    return True


def _clear_staging(root):
    local = Path(root) / 'data/local'
    for child in local.iterdir() if local.is_dir() else ():
        if child.name.startswith(STAGING) and child.is_dir() and not child.is_symlink():
            _remove(child)


def update(root, *, progress=lambda phase, done, total: None, cancelled=lambda: False, fetch=catalog_download._open,
           attempts=20, wait=0.5):
    """Build the newest TCGdex catalogue beside the one in use, then put it in place."""
    root = Path(root).absolute()
    current = catalog_download.installed(root)
    if current is None:
        return {'status': 'MISSING'}
    try:
        newest = catalog_download.latest_commit(fetch)
    except (CatalogError, OSError, ValueError) as error:
        return {'status': 'STOPPED', 'error': neutral_exception_code(error, 'CATALOG_UPDATE')}
    if newest == current['commit']:
        return {'status': 'CURRENT', 'commit': newest}
    _clear_staging(root)
    staging = root / 'data/local' / (STAGING + datetime.now().strftime('%Y%m%d-%H%M%S'))
    receipt = catalog_download.build(staging, newest, progress=progress, cancelled=cancelled, fetch=fetch)
    if receipt['status'] == 'COMPLETE' and (current.get('printings') or 0) * SMALLER > (receipt.get('printings') or 0):
        receipt = dict(receipt, status='STOPPED', error='CATALOG_UPDATE_SMALLER')
    if receipt['status'] != 'COMPLETE' or cancelled():
        _remove(staging)
        return dict(receipt, status='STOPPED', error=receipt.get('error') or 'CATALOG_DOWNLOAD_CANCELLED')
    (staging / READY).write_text(json.dumps({'schema_version': 1, 'commit': newest,
                                             'printings': receipt.get('printings'), 'sets': receipt.get('sets')}),
                                 encoding='utf-8')
    placed = activate(root, staging, attempts=attempts, wait=wait)
    return dict(receipt, status='UPDATED' if placed else 'READY_NEXT_LAUNCH', previous=current)


def apply_pending(root):
    """At launch, before anything opens the catalogue: put a ready update in place, drop unfinished ones."""
    local = Path(root) / 'data/local'
    if not local.is_dir():
        return None
    result = None
    for staging in sorted((c for c in local.iterdir() if c.name.startswith(STAGING) and c.is_dir()
                           and not c.is_symlink()), reverse=True):
        try:
            ready = json.loads((staging / READY).read_text(encoding='utf-8'))
        except (OSError, ValueError):
            ready = None
        if result is None and isinstance(ready, dict) and _built(staging).is_dir():
            result = {'status': 'UPDATED' if activate(root, staging) else 'READY_NEXT_LAUNCH',
                      'commit': ready.get('commit'), 'printings': ready.get('printings')}
            continue
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)  # a download cut short: public data, rebuilt on demand
    return result
