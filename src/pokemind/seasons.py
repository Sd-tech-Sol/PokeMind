"""TCG Live seasons for the owner's statistics (owner, 2026-11-05).

A season starts with a Ranked Ladder and lasts until the next one. Official starts are listed below with
their source; the owner can also start one from the app when PokeMind does not know the date yet
(seasons.json beside the analysis, removed with the games by a reset). A battle log carries no date, so a
game belongs to the season of the day its log was added to PokeMind (local date of the file in
battle_logs; copies, the data folder move and restore keep it).

Nothing is moved or deleted: a past season stays readable, and « Cumul » counts every game. A season view
is the same report with its matches limited to that season, grouped again by the analysis engine's own
group_matches, so every count is computed the same way as before. What needs the whole corpus
(recommendations, Learning Loop) stays computed on every game, and says so.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from pokemind import battle_batch

OFFICIAL = (
    {'start': '2026-11-05', 'name': 'Delta Reign',
     'detail': 'Ladder classé de novembre 2026 · extension Méga-Évolution — Delta Reign',
     'source': 'https://community.pokemon.com/en-us/discussion/26744/letter-to-the-community-october-30-2026'},
)
FILE = 'data/local/battle-intelligence/seasons.json'
LOGS = 'data/local/battle_logs'
CURRENT, ALL, BEFORE = 'current', 'all', 'before'
WHOLE_CORPUS = 'Recommandations et apprentissage : calculés sur toutes les parties, toutes saisons.'


def _day(value):
    try:
        return date.fromisoformat(value).isoformat() if isinstance(value, str) and len(value) == 10 else None
    except ValueError:
        return None


def owner_starts(root):
    path = Path(root) / FILE
    try:
        if not path.is_file() or path.stat().st_size > 65536:
            return []
        value = json.loads(battle_batch.safe_path(root, path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return []
    rows = value.get('starts', []) if isinstance(value, dict) and value.get('schema_version') == 1 else []
    return [{'start': _day(r['start']), 'name': r['name'].strip()[:60]} for r in rows[:200]
            if isinstance(r, dict) and _day(r.get('start')) and isinstance(r.get('name'), str) and r['name'].strip()]


def add_start(root, name, day=None):
    """The owner starts a season (today by default); same day = renamed. Earlier games keep their season."""
    day = _day(day or date.today().isoformat())
    name = re.sub(r'\s+', ' ', str(name or '')).strip()[:60] or 'Saison du ' + day
    if not day:
        raise ValueError('SEASON_DATE_INVALID')
    rows = [r for r in owner_starts(root) if r['start'] != day] + [{'start': day, 'name': name}]
    path = battle_batch.safe_path(root, Path(root) / FILE, exists=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.seasons-' + uuid.uuid4().hex + '.tmp')
    temporary.write_text(json.dumps({'schema_version': 1, 'starts': sorted(rows, key=lambda r: r['start'])[-200:]},
                                    ensure_ascii=False, indent=1), encoding='utf-8')
    os.replace(temporary, path)
    return {'start': day, 'name': name}


def periods(root, today=None):
    """Seasons begun by today, oldest first; the last one is the current season."""
    today = _day(today) or date.today().isoformat()
    starts = {r['start']: dict(r) for r in OFFICIAL}
    for row in owner_starts(root):
        starts[row['start']] = starts.get(row['start'], {}) | row | {'owner': True}
    begun = [starts[d] for d in sorted(starts) if d <= today]
    if not begun:
        return [{'key': BEFORE, 'name': 'Toutes les parties', 'start': None, 'end': None}]
    rows = [{'key': BEFORE, 'name': 'Avant le ' + begun[0]['start'], 'start': None, 'end': begun[0]['start']}]
    for index, row in enumerate(begun):
        rows.append(row | {'key': row['start'], 'end': begun[index + 1]['start'] if index + 1 < len(begun) else None})
    return rows


def resolve(key, rows):
    """The period for a picker key; 'all' gives None (no limit); an unknown key gives the current season."""
    if key == ALL:
        return None
    return next((r for r in rows if r['key'] == key), rows[-1]) if key != CURRENT else rows[-1]


def added_dates(root, matches):
    """{log file name: local date it was added}; None when the file is no longer there."""
    folder = Path(root) / LOGS
    dates = {}
    for name in {m.get('source_relative') for m in matches if isinstance(m.get('source_relative'), str)}:
        path = folder / name
        try:
            battle_batch.safe_path(root, path)
            dates[name] = datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
        except (OSError, ValueError):
            dates[name] = None
    return dates


def _within(day, period):
    return day is not None and (period['start'] is None or day >= period['start']) and (
        period['end'] is None or day < period['end'])


def counts(matches):
    outcome = Counter(m.get('outcome') for m in matches)
    return {'wins': outcome['wins'], 'losses': outcome['losses'], 'unknown': outcome['unknown']}


def scoped(report, period, dates):
    """The report limited to one season (None = every game), with the same groups the engine makes."""
    if not report:
        return report
    matches = report.get('matches', [])
    if period is None:
        return dict(report, season={'key': ALL, 'name': 'Cumul · toutes les saisons', 'games': len(matches),
                                    'undated': sum(dates.get(m.get('source_relative')) is None for m in matches)})
    if period['start'] is None and period['end'] is None:
        return report  # no season begun yet: every game, the report itself
    keep = [m for m in matches if _within(dates.get(m.get('source_relative')), period)]
    view = dict(report, matches=keep, groups=battle_batch.group_matches(keep), outcomes=counts(keep),
                coverage=dict(report.get('coverage', {}), valid=len(keep)),
                own_decks=dict(Counter(m.get('own_deck_hypothesis', {}).get('label') or 'unknown' for m in keep)))
    view['season'] = {k: period[k] for k in ('key', 'name', 'start', 'end') if k in period} | {
        'games': len(keep), 'all_games': len(matches), 'whole_corpus': WHOLE_CORPUS}
    return view


def summary(report, dates, rows):
    """Per-season counts and the total, small enough for the coach."""
    matches = (report or {}).get('matches', [])
    result = [{'name': r['name'], 'start': r['start'], 'end': r['end'], 'games': len(kept), **counts(kept)}
              for r in rows for kept in [[m for m in matches if _within(dates.get(m.get('source_relative')), r)]]]
    return {'seasons': [r for r in result if r['games'] or r['end'] is None],
            'all_seasons': {'games': len(matches), **counts(matches)},
            'rule': 'Une partie compte dans la saison du jour où son journal a été ajouté à PokeMind.'}
