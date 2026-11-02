"""Small REST detail batches for guarded PUBLIC workspaces; no bulk code loader.

The campaign owns path validation and the database. Reuse the catalogue's schema,
validators, provenance and FTS; never infer language from a neighbouring record.
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

from pokemind.cards import (
    ApiNotFound, CatalogError, NetworkFailure, RequestBudgetExhausted,
    _card_brief, _safe_api_url, _upsert_card_brief, _upsert_card_detail,
    _validated_card_detail, cards_coverage, parse_languages,
    _record_sync_metadata,
)
from pokemind.database import SCHEMA_VERSION, connect_readonly, connect_writable, initialize_schema, utc_now
from pokemind.security import neutral_exception_code

MAX_SELECTION = 100
MAX_CACHE_AGE = timedelta(days=30)
BLOCK_KEY = 'catalog_public_selection_access_blocked'


def selection_plan(card_ids, languages='en,fr'):
    if isinstance(card_ids, str):
        if len(card_ids) > MAX_SELECTION * 129:
            raise CatalogError('PUBLIC_SELECTION_TOO_LARGE')
        card_ids = card_ids.split(',')
    if not isinstance(card_ids, (list, tuple)) or not 1 <= len(card_ids) <= MAX_SELECTION:
        raise CatalogError('PUBLIC_SELECTION_INVALID')
    ids = []
    for value in card_ids:
        # No encoded URLs, separators or dot segments. Values are IDs, never paths.
        if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9!?._-]{0,127}', value):
            raise CatalogError('PUBLIC_SELECTION_ID_INVALID')
        if value in ids:
            raise CatalogError('PUBLIC_SELECTION_DUPLICATE_ID')
        ids.append(value)
    selected_languages = list(parse_languages(languages))
    return {'card_ids': ids, 'languages': selected_languages,
            'maximum_detail_pairs': len(ids) * len(selected_languages),
            'cache_max_age_days': MAX_CACHE_AGE.days,
            'index_scan_performed': False, 'provider_total': 'unknown',
            'bulk_import': 'BLOCKED_UNSUPPORTED_UPSTREAM_TYPESCRIPT'}


def _url(card_id, language):
    return _safe_api_url(f'/{language}/cards/{quote(card_id, safe="!._-")}')


def _resolved(connection, card_id, language, recheck_absent):
    row = connection.execute(
        f'''SELECT t.status,t.retrieved_at,t.source_url,t.payload_sha256,
                   p.detail_stale_{language} AS stale
            FROM catalog_translations t JOIN catalog_printings p ON p.tcgdex_id=t.printing_id
            WHERE t.printing_id=? AND t.language=?''', (card_id, language),
    ).fetchone()
    if row is None:
        return False
    if row['status'] == 'absent':
        return not recheck_absent
    if row['status'] != 'present' or row['stale'] or not row['payload_sha256'] or row['source_url'] != _url(card_id, language):
        return False
    try:
        retrieved = datetime.fromisoformat(row['retrieved_at'])
        return retrieved.tzinfo is not None and timedelta(0) <= datetime.now(timezone.utc) - retrieved <= MAX_CACHE_AGE
    except (TypeError, ValueError):
        return False


def _store_absent(connection, card_id, language):
    timestamp, url = utc_now(), _url(card_id, language)
    with connection:
        connection.execute(
            '''INSERT INTO catalog_printings
               (tcgdex_id,discovered_at,updated_at,brief_source_url,brief_retrieved_at)
               VALUES (?,?,?,?,?) ON CONFLICT(tcgdex_id) DO NOTHING''',
            (card_id, timestamp, timestamp, url, timestamp),
        )
        connection.execute(
            '''INSERT INTO catalog_translations(printing_id,language,status,source_url,retrieved_at)
               VALUES (?,?,'absent',?,?) ON CONFLICT(printing_id,language) DO UPDATE SET
               status='absent',source_url=excluded.source_url,retrieved_at=excluded.retrieved_at,last_error=NULL''',
            (card_id, language, url, timestamp),
        )


def _fetch_detail(connection, client, card_id, language):
    try:
        payload, url = client.get_json(f'/{language}/cards/{quote(card_id, safe="!._-")}')
    except ApiNotFound:
        _store_absent(connection, card_id, language)
        return 'absent'
    if url != _url(card_id, language):
        raise CatalogError('PUBLIC_SELECTION_SOURCE_MISMATCH')
    _validated_card_detail(payload, card_id)
    with connection:
        _upsert_card_brief(connection, _card_brief(payload), language, url, utc_now())
        # The existing transaction commits brief/detail together or rolls both
        # back if validation, SQL or FTS fails. No writes follow its commit.
        _upsert_card_detail(connection, payload, card_id, language, url)
    return 'present'


def sync_public_selection(db, plan, client, *, recheck_absent=False):
    """Called only after the campaign's PUBLIC guard; each detail commits atomically.

    Completed pairs survive interruption. An invalid response does not commit a
    brief, partial detail, index membership or fabricated translation. Re-running
    skips fresh/absent pairs, including when the previous budget ended mid-card.
    """
    plan = selection_plan(plan['card_ids'], plan['languages'])
    if db.exists():
        existing = connect_readonly(db)
        try:
            if existing.execute('PRAGMA user_version').fetchone()[0] != SCHEMA_VERSION:
                raise CatalogError('PUBLIC_SELECTION_SCHEMA_VERSION_UNSUPPORTED')
        finally:
            existing.close()
    connection = connect_writable(db)
    details = {'sets_present': 0, 'sets_absent': 0, 'cards_present': 0, 'cards_absent': 0}
    result = {'selection': plan, 'details': details, 'stopped_reason': 'selection_resolved',
              'error': None, 'cache_hits': 0, 'requests_made': 0, 'processed': [],
              'index_scan_performed': False, 'complete': False}
    try:
        initialize_schema(connection)
        pairs = [(i, lang) for i in plan['card_ids'] for lang in plan['languages']]
        pending = [(i, lang) for i, lang in pairs if not _resolved(connection, i, lang, recheck_absent)]
        result['cache_hits'] = len(pairs) - len(pending)
        result['pending_pairs_before'] = len(pending)
        block = connection.execute('SELECT value FROM metadata WHERE key=?', (BLOCK_KEY,)).fetchone()
        if block:
            result.update(error='PUBLIC_SELECTION_PREVIOUS_ACCESS_DENIAL', stopped_reason='provider_blocked',
                          blocked_reason='PUBLIC_SELECTION_PREVIOUS_ACCESS_DENIAL')
        else:
            for card_id, language in pending:
                if client.remaining <= 0:
                    result['stopped_reason'] = 'budget_exhausted'
                    break
                try:
                    status = _fetch_detail(connection, client, card_id, language)
                    details['cards_' + status] += 1
                    result['processed'].append({'id': card_id, 'language': language, 'status': status})
                except RequestBudgetExhausted:
                    result['stopped_reason'] = 'budget_exhausted'
                    break
                except (CatalogError, NetworkFailure, sqlite3.Error) as exc:
                    connection.rollback()
                    result.update(error=neutral_exception_code(exc, 'TCGDEX'), stopped_reason='source_error')
                    if getattr(client, 'blocked_reason', None):
                        with connection:
                            connection.execute('INSERT OR REPLACE INTO metadata(key,value) VALUES (?,?)',
                                               (BLOCK_KEY, 'PUBLIC_SOURCE_ACCESS_DENIED'))
                        result['stopped_reason'] = 'provider_blocked'
                    break
        result['requests_made'] = client.requests_made
        _record_sync_metadata(connection, client.requests_made,
                              success=bool(result['processed']), error=result['error'])
        result['pending_pairs_after'] = len(pending) - len(result['processed'])
        result['selection_resolved'] = result['pending_pairs_after'] == 0 and not result['error']
        result['coverage'] = cards_coverage(db, _connection=connection)
        result['limits'] = ['Selected details only; no provider index/total, legality, Live support or ownership proof.',
                            'Missing fields stay unknown; absent translation is not an English fallback.',
                            'Fresh details use a 30-day cache; this is not a provider change detector.']
        return result
    finally:
        connection.close()
