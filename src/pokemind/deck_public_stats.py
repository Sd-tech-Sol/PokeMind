"""Public archetype statistics for Deck Lab (PM-DECKLAB-PUBLIC-STATS-001, target 0.9.5).

Everything here reuses the existing PUBLIC engines; there is no second collector, store or backend:
- collection: ``batch_public_research.research_matchups`` (bounded Limitless Tournament Platform campaign,
  /tournaments + details + standings + pairings, no key, never /games/{id}/decks, daily pointer);
- aggregation: ``meta.meta_tournaments`` / ``meta_archetypes`` / ``meta_matchups`` on each marked PUBLIC
  campaign database (game/format/platform/online filters, byes and double losses excluded, Wilson interval).

What this module adds is only the honest assembly for one selected deck:
- the deck -> archetype association, computed locally from the deck's own Pokémon (the owner's deck name is
  never used, and no list or name ever leaves the PC: the network call takes no deck input at all);
- deduplication across daily snapshots (one tournament counted once, newest snapshot wins);
- per-mode figures (BO1 and BO3 are never merged), mirrors kept apart, thresholds under which no percentage
  is shown;
- the refresh guard: one automatic attempt per day shared by every deck, and a bounded manual button.

Public statistics describe an ARCHETYPE in a sample of public online tournaments, never the owner's exact
60 cards, and never a « world » win rate.
"""
from __future__ import annotations

import re
import sqlite3
import threading
import time
import unicodedata
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from pokemind import battle_batch, battle_coach, batch_public_research, meta, public_campaign
from pokemind.database import connect_readonly
from pokemind.security import neutral_exception_code

SOURCE_NAME = 'Limitless TCG · Tournament Platform (API publique)'
SOURCE_URL = 'https://play.limitlesstcg.com/api/tournaments'
DOCS_URL = 'https://docs.limitlesstcg.com/developer/tournaments'
POPULATION = {'game': 'PTCG', 'format': 'STANDARD', 'platform': 'PTCGL', 'online': True,
              'label': 'Pokémon TCG Live en ligne · Standard · tournois publics Limitless'}
FOLDER = 'data/local/public-campaigns'
CONTROL = FOLDER + '/deck-public-stats.json'
CAMPAIGN = re.compile(r'lot-i-(chat-[0-9a-f]{16})')
WINDOW_DAYS = 28            # recent tournaments only; older ones are another metagame
MAX_SNAPSHOTS = 40          # campaign databases looked at (newest first), a hard I/O bound
MIN_PLACEMENTS_SHARE = 20   # classified placements before a representation percentage is shown
MIN_MATCHES_WINRATE = 20    # admissible matches before an archetype win rate is shown
MIN_MATCHES_MATCHUP = 10    # matches against one opponent archetype before its bar shows a percentage
MATCHUPS_SHOWN = 8
MANUAL_DAILY_CAP = 2        # « Actualiser » attempts per day, on top of the single automatic one
MANUAL_MIN_SECONDS = 600    # between two attempts of any kind, to protect the provider
NAME_SUFFIXES = {'ex', 'v', 'vstar', 'vmax', 'gx', 'star'}
LEAD_MIN_COPIES = 2         # the archetype's first named Pokémon must be a real line, not a one-copy tech

_LOCK = threading.Lock()  # one refresh at a time for the whole process (two decks selected quickly)


def _tokens(text):
    """Lower-case words without accents or punctuation; trailing ex/V/VSTAR… suffixes are not names."""
    text = unicodedata.normalize('NFKD', str(text or ''))
    text = ''.join(ch for ch in text if not unicodedata.combining(ch)).casefold()
    words = re.findall(r"[a-z0-9]+", text.replace("'", ''))
    return [w for w in words if w not in NAME_SUFFIXES]


def deck_words(pokemon):
    """{word: copies} over the deck's Pokémon names (printed name and, when resolved, its English name)."""
    words = {}
    for card in pokemon:
        quantity = int(card.get('quantity') or 0)
        names = {w for name in (card.get('name'), card.get('english')) if name for w in _tokens(name)}
        for word in names:
            words[word] = words.get(word, 0) + quantity
    return words


def identify(pokemon, catalog, public_labels=()):
    """The archetype of the provider's sample this deck belongs to, with its evidence, or why not.

    ``catalog`` is {archetype_id: archetype_name} as published in the sample. Two kinds of evidence:
    - ``public_label_corroborated``: the deck is a PUBLIC reference whose published label names exactly one
      archetype of the sample, and every Pokémon of that name is in the list;
    - ``pokemon_in_list``: every Pokémon named by exactly one most specific archetype of the sample is in the
      list, its first one with at least two copies. A heuristic, said so; never the owner's deck name.
    Ties or no match: not identified (the candidates are listed, no rate is attributed).
    """
    words = deck_words(pokemon)
    by_name = {}
    for archetype_id, name in catalog.items():
        key = tuple(_tokens(name))
        if key:
            by_name.setdefault(key, []).append(archetype_id)

    def corroborated(key):
        return all(word in words for word in key) and words.get(key[0], 0) >= LEAD_MIN_COPIES

    for label in public_labels:
        key = tuple(_tokens(label))
        if key and len(by_name.get(key, [])) == 1 and corroborated(key):
            archetype_id = by_name[key][0]
            return {'status': 'IDENTIFIED', 'archetype_id': archetype_id, 'archetype_name': catalog[archetype_id],
                    'evidence': 'public_label_corroborated', 'matched_pokemon': list(key), 'candidates': []}
    matches = [(len(key), key, ids) for key, ids in by_name.items() if corroborated(key)]
    if not matches:
        return {'status': 'UNIDENTIFIED', 'archetype_id': None, 'archetype_name': None, 'evidence': None,
                'matched_pokemon': [], 'candidates': [],
                'reason': 'NO_SAMPLE_ARCHETYPE_NAMES_ONLY_POKEMON_OF_THIS_LIST' if catalog else 'NO_PUBLIC_SAMPLE'}
    best = max(score for score, _, _ in matches)
    top = [(key, ids) for score, key, ids in matches if score == best]
    candidates = sorted(catalog[i] for _, ids in top for i in ids)
    if len(top) != 1 or len(top[0][1]) != 1:
        return {'status': 'AMBIGUOUS', 'archetype_id': None, 'archetype_name': None, 'evidence': None,
                'matched_pokemon': [], 'candidates': candidates[:6], 'reason': 'SEVERAL_ARCHETYPES_EQUALLY_SPECIFIC'}
    key, ids = top[0]
    return {'status': 'IDENTIFIED', 'archetype_id': ids[0], 'archetype_name': catalog[ids[0]],
            'evidence': 'pokemon_in_list', 'matched_pokemon': list(key), 'candidates': []}


def _snapshot_paths(root):
    """Marked PUBLIC campaign databases of the daily matchup collector, newest file first, bounded."""
    root = Path(root).absolute()
    folder = battle_batch.safe_path(root, root / FOLDER, exists=False)
    if not folder.is_dir():
        return []
    found = []
    for child in folder.iterdir():
        if not CAMPAIGN.fullmatch(child.name):
            continue
        db = child / 'public.sqlite3'
        try:
            if db.is_file():
                public_campaign.require_public_database(root, db)
                found.append((db.stat().st_mtime_ns, db))
        except (OSError, ValueError, sqlite3.Error):
            continue
    return [db for _, db in sorted(found, key=lambda item: item[0], reverse=True)[:MAX_SNAPSHOTS]]


def _snapshots(root, since, until=None):
    """One entry per included database, deduplicated by tournament: newest snapshot of a tournament wins."""
    rows = []
    for db in _snapshot_paths(root):
        try:
            listed = meta.meta_tournaments(db, since=since)['tournaments']
        except (OSError, ValueError, sqlite3.Error):
            continue
        # meta queries operate on the whole snapshot: reject it as a unit if its current
        # window contains a future event, rather than leak that event into the aggregate.
        if listed and not (until and any(t['date_utc'][:10] > until for t in listed)):
            rows.append((max(t['fetched_at'] or '' for t in listed), db, listed))
    seen, result, skipped = set(), [], 0
    for _, db, listed in sorted(rows, key=lambda item: item[0], reverse=True):
        ids = {t['tournament_id'] for t in listed}
        if ids & seen:  # an older snapshot of an already counted tournament: never counted twice
            skipped += 1
            continue
        seen |= ids
        result.append({'db': db, 'tournaments': listed})
    return result, skipped


def _signature(snapshot):
    """The match modes a snapshot's tournaments were played in (BO1, BO3, BO1+BO3…): its population."""
    ids = [t['tournament_id'] for t in snapshot['tournaments']]
    connection = connect_readonly(snapshot['db'])
    try:
        modes = {str(row[0]) for row in connection.execute(
            'SELECT DISTINCT mode FROM meta_phases WHERE tournament_id IN (' + ','.join('?' for _ in ids) + ')', ids)}
    finally:
        connection.close()
    return '+'.join(sorted(modes)) or 'UNKNOWN'


def _merge_matchups(snapshots, archetype_id, since):
    """Per mode (BO1, BO3… never merged): wins/losses/ties by opponent archetype over disjoint tournaments."""
    modes, excluded = {}, {}
    for snapshot in snapshots:
        result = meta.meta_matchups(snapshot['db'], archetype_id, min_sample=1, since=since)
        for reason, n in result.get('excluded', {}).items():
            excluded[reason] = excluded.get(reason, 0) + int(n)
        for row in result['matchups']:
            mode = modes.setdefault(str(row['mode']), {})
            entry = mode.setdefault(str(row['opponent_archetype']), {'wins': 0, 'losses': 0, 'ties': 0,
                                                                      'phases': set()})
            for key in ('wins', 'losses', 'ties'):
                entry[key] += int(row[key])
            entry['phases'].add(str(row['phase_type']))
    return modes, excluded


def _rate(wins, n, minimum):
    if n < minimum or n <= 0:
        return None, None
    return wins / n, meta._wilson(wins, n)


def _mode_view(archetype_id, opponents, names):
    mirror = opponents.get(archetype_id, {'wins': 0, 'losses': 0, 'ties': 0})
    rows = []
    for opponent, entry in opponents.items():
        if opponent == archetype_id:
            continue  # a mirror is one win and one loss for the same archetype: never in its rate
        n = entry['wins'] + entry['losses'] + entry['ties']
        fraction, interval = _rate(entry['wins'], n, MIN_MATCHES_MATCHUP)
        rows.append({'opponent_id': opponent, 'opponent': names.get(opponent) or opponent,
                     'wins': entry['wins'], 'losses': entry['losses'], 'ties': entry['ties'], 'n': n,
                     'win_fraction': fraction, 'wilson_95': interval, 'phases': sorted(entry['phases'])})
    rows.sort(key=lambda r: (-r['n'], r['opponent']))
    wins = sum(r['wins'] for r in rows)
    losses = sum(r['losses'] for r in rows)
    ties = sum(r['ties'] for r in rows)
    n = wins + losses + ties
    fraction, interval = _rate(wins, n, MIN_MATCHES_WINRATE)
    return {'wins': wins, 'losses': losses, 'ties': ties, 'n': n, 'win_fraction': fraction,
            'wilson_95': interval, 'mirror_matches': mirror['wins'] + mirror['losses'] + mirror['ties'],
            'matchups': rows, 'phases': sorted({p for r in rows for p in r['phases']})}


def _control(root):
    path = battle_batch.safe_path(Path(root).absolute(), Path(root).absolute() / CONTROL, exists=False)
    value, stamp = battle_coach._control(Path(root).absolute(), path)
    return path, (value if isinstance(value, dict) else {}), stamp


def _pointer(root):
    root = Path(root).absolute()
    path = battle_batch.safe_path(root, root / FOLDER / 'chat-matchups.json', exists=False)
    value, _ = battle_coach._control(root, path)
    return value if isinstance(value, dict) else {}


def refresh_state(root, *, as_of, now=None):
    """Read-only: what the guard would allow now, and the last attempt. No network."""
    now = time.time() if now is None else now
    try:
        _, control, _ = _control(root)
        pointer = _pointer(root)
    except (OSError, ValueError):
        control, pointer = {}, {}
    today = control.get('day') == as_of
    manual = int(control.get('manual_attempts', 0)) if today else 0
    last = control.get('last_attempt_epoch')
    wait = max(0, int(MANUAL_MIN_SECONDS - (now - last))) if isinstance(last, (int, float)) else 0
    done_today = (today and bool(control.get('auto_attempted'))) or pointer.get('as_of') == as_of
    return {'day': as_of, 'automatic_due': not done_today, 'manual_attempts_today': manual,
            'manual_left_today': max(0, MANUAL_DAILY_CAP - manual), 'retry_after_seconds': wait,
            'last_attempt_at': control.get('last_attempt_at'), 'last_outcome': control.get('last_outcome'),
            'collector_day': pointer.get('as_of'), 'collector_status': pointer.get('status')}


def refresh(root, *, as_of, manual=False, now=None, cancelled=None):
    """At most one automatic attempt per day (shared by every deck and by the coach's collector), plus a
    bounded manual one. The attempt is recorded BEFORE any GET, so a crash cannot turn into a retry loop.
    The collector receives no deck, no name and no private data."""
    root = Path(root).absolute()
    with _LOCK:
        now = time.time() if now is None else now
        state = refresh_state(root, as_of=as_of, now=now)
        if not manual and not state['automatic_due']:
            return {'status': 'CACHE_TODAY', 'network_used': False, 'gets': 0}
        if manual and state['manual_left_today'] <= 0:
            return {'status': 'REFRESH_DAILY_LIMIT', 'network_used': False, 'gets': 0}
        if state['retry_after_seconds'] > 0:
            return {'status': 'REFRESH_TOO_SOON', 'network_used': False, 'gets': 0,
                    'retry_after_seconds': state['retry_after_seconds']}
        path, control, stamp = _control(root)
        # Any attempt, manual included, is the day's attempt: no automatic one follows a manual refresh.
        record = {'schema_version': 1, 'day': as_of, 'auto_attempted': True,
                  'manual_attempts': state['manual_attempts_today'] + (1 if manual else 0),
                  'last_attempt_epoch': now,
                  'last_attempt_at': datetime.fromtimestamp(now, timezone.utc).isoformat(timespec='seconds'),
                  'last_outcome': {'status': 'IN_PROGRESS'}}
        battle_batch.safe_path(root, path.parent, exists=False).mkdir(parents=True, exist_ok=True)
        battle_coach._atomic_control(root, path, record, stamp)
        try:
            receipt = batch_public_research.research_matchups(root, as_of=as_of, cancelled=cancelled, force=manual)
            outcome = {'status': str(receipt.get('status', 'UNKNOWN')), 'gets': int(receipt.get('gets') or 0),
                       'eligible_matches': receipt.get('eligible_matches'), 'error': receipt.get('error'),
                       'cache_hit': bool(receipt.get('cache_hit'))}
        except (ValueError, OSError, sqlite3.Error) as exc:
            outcome = {'status': 'ERROR', 'gets': None, 'error': neutral_exception_code(exc, 'PUBLIC_STATS')}
        if cancelled and cancelled():
            outcome['status'] = 'INTERRUPTED'
        _, _, stamp = _control(root)
        battle_coach._atomic_control(root, path, record | {'last_outcome': outcome}, stamp)
        return outcome | {'network_used': outcome.get('gets') != 0 and not outcome.get('cache_hit')}


def public_sample(root, *, as_of, now=None):
    """One bounded offline sample shared by a selector batch; no deck/name goes to a provider."""
    since = (date.fromisoformat(as_of) - timedelta(days=WINDOW_DAYS - 1)).isoformat()
    snapshots, skipped = _snapshots(root, since, as_of)
    view = {'kind': 'deck_public_stats', 'as_of': as_of, 'source': SOURCE_NAME, 'source_url': SOURCE_URL,
            'docs_url': DOCS_URL, 'population': dict(POPULATION), 'window': {'since': since, 'until': as_of},
            'refresh': refresh_state(root, as_of=as_of, now=now), 'snapshots_used': len(snapshots),
            'duplicate_snapshots_skipped': skipped, 'unit': 'match publié (BO1 ou BO3), pas une partie',
            'scope': 'archétype dans un échantillon public; pas tes 60 cartes exactes'}
    tournaments = sorted((t for s in snapshots for t in s['tournaments']), key=lambda t: t['date_utc'])
    view['tournaments'] = [{'tournament_id': t['tournament_id'], 'name': t['name'], 'date': t['date_utc'][:10],
                            'participants': t['participants'], 'fetched_at': t['fetched_at'],
                            'source_url': t['source_url']} for t in tournaments]
    view['date_range'] = [tournaments[0]['date_utc'][:10], tournaments[-1]['date_utc'][:10]] if tournaments else None
    view['last_success_at'] = max((t['fetched_at'] for t in tournaments if t['fetched_at']), default=None)
    names, per_snapshot, populations = {}, [], {}
    for snapshot in snapshots:
        result = meta.meta_archetypes(snapshot['db'], since=since)
        local = {}
        for row in result['archetypes']:
            key = str(row['archetype_id'])
            local[key] = int(row['n_placements'])
            names.setdefault(key, row['archetype_name'] or key)
        signature = _signature(snapshot)
        per_snapshot.append({'date': min(t['date_utc'] for t in snapshot['tournaments'])[:10], 'population': signature,
                             'placements': int(result['n_placements']), 'classified': int(result['n_classified']),
                             'counts': local})
        group = populations.setdefault(signature, {'n_placements': 0, 'n_classified': 0, 'counts': {}, 'tournaments': 0})
        group['n_placements'] += int(result['n_placements'])
        group['n_classified'] += int(result['n_classified'])
        group['tournaments'] += len(snapshot['tournaments'])
        for key, n in local.items():
            group['counts'][key] = group['counts'].get(key, 0) + n

    def share(n, denominator):
        return n / denominator if denominator >= MIN_PLACEMENTS_SHARE else None

    # Representation is computed per tournament population (BO1 events, BO3 events, mixed…), never pooled.
    view['populations'] = {}
    for signature, group in sorted(populations.items(), key=lambda item: (-item[1]['n_placements'], item[0])):
        view['populations'][signature] = {
            'population': signature, 'tournaments': group['tournaments'], 'n_placements': group['n_placements'],
            'n_classified': group['n_classified'],
            'classified_fraction': group['n_classified'] / group['n_placements'] if group['n_placements'] else None,
            'archetypes': [{'archetype_id': key, 'name': names[key], 'n': n, 'share': share(n, group['n_classified'])}
                           for key, n in sorted(group['counts'].items(), key=lambda item: (-item[1], item[0]))][:MATCHUPS_SHOWN]}
    empty = {'population': None, 'tournaments': 0, 'n_placements': 0, 'n_classified': 0, 'classified_fraction': None,
             'archetypes': []}
    view['meta'] = next(iter(view['populations'].values()), empty)  # the largest population; the others are listed
    return {'view': view, 'names': names, 'snapshots': snapshots, 'since': since,
            'populations': populations, 'per_snapshot': per_snapshot, 'modes': {}}


def public_view(root, *, as_of, pokemon, public_labels=(), now=None, sample=None):
    """Offline read model for one deck. A batch may share its checked sample and per-archetype SQL."""
    import copy
    sample = sample if sample is not None else public_sample(root, as_of=as_of, now=now)
    view = copy.deepcopy(sample['view'])
    names, snapshots, since = sample['names'], sample['snapshots'], sample['since']
    populations, per_snapshot = sample['populations'], sample['per_snapshot']
    def share(n, denominator):
        return n / denominator if denominator >= MIN_PLACEMENTS_SHARE else None
    identity = identify(pokemon, names, public_labels)
    view['identity'] = identity
    view['archetype'] = None
    if not snapshots:
        view['status'] = 'NO_SNAPSHOT'
        return view
    if identity['status'] != 'IDENTIFIED':
        view['status'] = 'ARCHETYPE_' + identity['status']
        return view
    archetype_id = identity['archetype_id']
    if archetype_id not in sample['modes']:
        sample['modes'][archetype_id] = _merge_matchups(snapshots, archetype_id, since)
    modes, excluded = sample['modes'][archetype_id]
    by_mode = {mode: _mode_view(archetype_id, opponents, names) for mode, opponents in modes.items()}
    history = [{'date': s['date'], 'population': s['population'], 'n': s['counts'].get(archetype_id, 0),
                'classified': s['classified'], 'share': share(s['counts'].get(archetype_id, 0), s['classified'])}
               for s in sorted(per_snapshot, key=lambda s: s['date'])]
    representation = {signature: {'population': signature, 'n': group['counts'].get(archetype_id, 0),
                                  'classified': group['n_classified'], 'tournaments': group['tournaments'],
                                  'share': share(group['counts'].get(archetype_id, 0), group['n_classified'])}
                      for signature, group in populations.items()}
    view['archetype'] = {'archetype_id': archetype_id, 'name': identity['archetype_name'],
                         'representation': dict(sorted(representation.items(), key=lambda item: -item[1]['classified'])),
                         'modes': dict(sorted(by_mode.items(), key=lambda item: -item[1]['n'])),
                         'history': history if len(history) >= 2 else [],
                         'excluded_all_archetypes': excluded}
    enough = any(m['win_fraction'] is not None for m in by_mode.values())
    view['status'] = 'OK' if enough else 'INSUFFICIENT_MATCHES'
    return view
