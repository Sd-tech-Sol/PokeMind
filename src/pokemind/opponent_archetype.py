"""Probable opponent archetype from the opponent's cards seen in a log (pipeline 023, phase 6).

Offline and deterministic. Computed when a report is read, kept in memory only: no migration, nothing written,
the saved report and the logs are never changed. A result is a probability in words (« Probablement : … »),
never a fact, and every result names the cards it rests on.

How it decides:
- the archetypes known locally are the dated public archetype names already collected for Deck Lab (Limitless
  tournament snapshots), each reduced to the Pokémon words of its name (« Charizard Pidgeot » → charizard, pidgeot);
- the opponent's observed cards are turned into English Pokémon names through the local card catalogue (a French
  log names « Dracolosse », the catalogue says Dragonite); Trainer and Energy cards never count;
- an archetype is a candidate when every word of its name was seen; the most specific candidate wins
  (« Charizard Pidgeot » over « Charizard ex »), a tie between equally specific archetypes is « Non identifié »;
- confidence counts how often the supporting cards were seen: 4 or more mentions high, 2–3 medium, 1 low;
  another archetype fully seen beside it lowers it one level (low then becomes « Non identifié »);
- fewer than MIN_CARDS distinct observed cards is never enough.
"""
from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import closing
from pathlib import Path

VERSION = 'opponent-archetype-v1'
PREFIX = 'probable:'          # an opponent label made by this module, never a recorded one
MIN_CARDS = 3                 # distinct opponent cards seen before any guess
LEVELS = ('low', 'medium', 'high')

_LOCK = threading.Lock()
_CLASSIFIERS = {}


def _tokens(text):
    from pokemind.deck_public_stats import _tokens as words
    return words(text)


def signatures(labels):
    """[{label, words}] for archetype names; names with the same Pokémon words are one archetype (first name kept)."""
    result = {}
    for label in sorted({str(x).strip() for x in labels if str(x or '').strip()}, key=lambda x: (len(x), x)):
        words = tuple(dict.fromkeys(_tokens(label)))
        if words and words not in result:
            result[words] = label
    return tuple({'label': label, 'words': words} for words, label in sorted(result.items(), key=lambda i: (i[1], i[0])))


def _unidentified(reason, candidates=()):
    return {'version': VERSION, 'label': None, 'confidence': None, 'evidence': [], 'candidates': sorted(candidates),
            'reason': reason}


def identify(cards, known, aliases):
    """`cards`: observed opponent cards ({name, normalized_name, occurrences}); `known`: signatures();
    `aliases`: {normalized card name: {English Pokémon names}} (Pokémon only)."""
    cards = [c for c in cards or [] if isinstance(c, dict) and c.get('normalized_name')]
    if len({c['normalized_name'] for c in cards}) < MIN_CARDS:
        return _unidentified('TOO_FEW_CARDS')
    pokemon = []
    for card in cards:
        words = {w for name in sorted(aliases.get(card['normalized_name'], ())) for w in _tokens(name)}
        if words:
            pokemon.append((card, words))
    seen = set().union(*(words for _, words in pokemon)) if pokemon else set()
    matches = [s for s in known if set(s['words']) <= seen]
    if not matches:
        return _unidentified('NO_KNOWN_ARCHETYPE')
    best = max(len(s['words']) for s in matches)
    top = [s for s in matches if len(s['words']) == best]
    if len(top) != 1:
        return _unidentified('SEVERAL_ARCHETYPES_EQUALLY_LIKELY', [s['label'] for s in top])
    chosen = top[0]
    words = set(chosen['words'])
    support = [card for card, card_words in pokemon if card_words & words]
    mentions = sum(max(1, int(card.get('occurrences') or 1)) for card in support)
    level = 2 if mentions >= 4 else 1 if mentions >= 2 else 0
    rivals = [s['label'] for s in matches if not set(s['words']) <= words]
    if rivals:
        level -= 1
    if level < 0:
        return _unidentified('ANOTHER_ARCHETYPE_SEEN_TOO', [chosen['label'], *rivals])
    evidence = sorted(({'name': c.get('name') or c['normalized_name'], 'occurrences': max(1, int(c.get('occurrences') or 1))}
                       for c in support), key=lambda e: (-e['occurrences'], e['name'].casefold()))
    return {'version': VERSION, 'label': chosen['label'], 'confidence': LEVELS[level], 'evidence': evidence,
            'candidates': sorted(rivals), 'reason': 'ALL_NAME_POKEMON_SEEN'}


class Classifier:
    """One set of known archetypes and catalogue names, with an in-memory cache of the results."""

    def __init__(self, known, aliases):
        self.known, self.aliases, self._cache = tuple(known), aliases, {}

    def __call__(self, cards):
        key = tuple(sorted((str(c.get('normalized_name')), int(c.get('occurrences') or 1), str(c.get('name')))
                           for c in cards or [] if isinstance(c, dict)))
        if key not in self._cache:
            if len(self._cache) > 4096:
                self._cache.clear()
            self._cache[key] = identify(cards, self.known, self.aliases)
        return self._cache[key]


def _stamp(path):
    try:
        info = os.stat(path)
        return info.st_mtime_ns, info.st_size
    except OSError:
        return None


def catalog_aliases(path):
    """{normalized printed name (any language): {English name}} for Pokémon printings, read-only."""
    from pokemind import rules
    by_id = {}
    with closing(sqlite3.connect(Path(path).as_uri() + '?mode=ro&immutable=1', uri=True)) as con:
        rows = con.execute("SELECT t.printing_id,t.language,t.name,p.category FROM catalog_translations t "
                           "JOIN catalog_printings p ON p.tcgdex_id=t.printing_id WHERE t.status='present'").fetchall()
    for pid, language, name, category in rows:
        if name and rules._normalized_name(category or '') in {'pokemon', 'pokémon'}:
            by_id.setdefault(pid, {})[language] = name
    aliases = {}
    for names in by_id.values():
        if 'en' in names:
            for name in names.values():
                aliases.setdefault(rules._normalized_name(name), set()).add(names['en'])
    return aliases


def local_classifier(root):
    """The classifier for this data folder, rebuilt only when a snapshot or the catalogue changed; None if either
    the archetypes or the catalogue is missing (every game then stays « Adversaire non identifié »)."""
    from pokemind import deck_public_stats, meta
    from pokemind.public_deck_preflight import SCOPED_PUBLIC_CACHES
    root = Path(root).absolute()
    snapshots = deck_public_stats._snapshot_paths(root)
    catalog = root / SCOPED_PUBLIC_CACHES[1]
    key = (os.path.normcase(str(root)), tuple((str(p), _stamp(p)) for p in snapshots), _stamp(catalog))
    with _LOCK:
        if key in _CLASSIFIERS:
            return _CLASSIFIERS[key]
    labels = set()
    for db in snapshots:
        try:
            labels.update(row['archetype_name'] for row in meta.meta_archetypes(db, since=None)['archetypes']
                          if row['archetype_name'])
        except (OSError, ValueError, sqlite3.Error):
            continue
    classifier = None
    if labels and catalog.is_file():
        try:
            classifier = Classifier(signatures(labels), catalog_aliases(catalog))
        except (OSError, sqlite3.Error):
            classifier = None
    with _LOCK:
        _CLASSIFIERS.clear()
        _CLASSIFIERS[key] = classifier
    return classifier


def with_probable_opponents(report, classify):
    """A copy of a report in which each game without an identified opponent carries its probable archetype as the
    label PREFIX + name, and `opponent.probable` holds the result; the groups are rebuilt from those labels.
    The report given is left as it is."""
    if not report or classify is None:
        return report
    from pokemind import battle_batch
    matches, changed = [], False
    for match in report.get('matches', []):
        opponent = match.get('opponent') or {}
        if str(opponent.get('label') or 'unknown') == 'unknown':
            result = classify(match.get('opponent_cards', []))
            if result['label']:
                match = dict(match, opponent=dict(opponent, label=PREFIX + result['label'], probable=result,
                                                  recorded_label=opponent.get('label')))
                changed = True
        matches.append(match)
    if not changed:
        return report
    return dict(report, matches=matches, groups=battle_batch.group_matches(matches),
                probable_opponents={'version': VERSION, 'games': sum(1 for m in matches
                                                                     if (m.get('opponent') or {}).get('probable'))})
