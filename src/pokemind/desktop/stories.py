"""Short summaries in a player's words, from the games really recorded (pipeline 023, phase 7).

Every sentence appears only when its data exists, says how many games it rests on, and never states a cause, a
general win rate or a percentage. The cautions are in the ⓘ (STORY_CAVEAT), not in the sentences.

What a game gives here: its result, the last turn header seen in its log, its opponent (recorded or probable), the
opponent cards seen, and the day its log was added (the log itself has no date: `battle_date` is « unknown »).
"""
from __future__ import annotations

import html
from collections import Counter

from pokemind.desktop.insights import opponent_words
from pokemind.desktop.locale_text import T, Text

MIN_AVERAGE = 2      # games behind an average
SHORT_GAME = 6       # « ends by turn 6 », as the engine's short-game signal
LETTERS = {'wins': ('V', 'W'), 'losses': ('D', 'L')}
OTHER_LETTER = ('N', 'N')  # a draw or a game without a result (owner, 2026-11-18: no « ? »)

STORY_CAVEAT = T(
    'Ces phrases décrivent tes parties enregistrées, pas un taux de victoire général, et ne disent pas pourquoi une '
    'partie a été gagnée ou perdue. Ordre des parties : le jour où chaque journal a été ajouté, puis l’ordre de '
    'l’analyse. Les tours sont les en-têtes de tour du journal (les deux joueurs). Un adversaire « probable » est '
    'déduit des cartes vues.',
    en='These sentences describe your recorded games, not a general win rate, and do not say why a game was won or '
       'lost. Order of the games: the day each log was added, then the order of the analysis. Turns are the turn '
       'headers of the log (both players). A « probable » opponent is inferred from the cards seen.')
LAST_FIVE_LEGEND = T('5 dernières parties : V = victoire, D = défaite, N = nul ou sans résultat.',
                     en='Last 5 games: W = win, L = loss, N = draw or no result.')
OVERVIEW_CAVEAT = LAST_FIVE_LEGEND + Text('\n\n', '\n\n') + STORY_CAVEAT


def _known_length(counts, complete):
    """« (sur 8 victoires et 8 défaites) », or, when some games have no known length, the owner's wording
    (2026-11-18): « (calculé sur 8 victoires et 8 défaites dont la durée est connue) »."""
    if complete:
        return Text(' (sur ', ' (over ') + counts + Text(')', ')')
    return Text(' (calculé sur ', ' (computed over ') + counts + Text(' dont la durée est connue)',
                                                                      ' whose length is known)')


def _count(number, fr, frs, en, ens):
    return Text(str(number) + ' ' + (frs if number > 1 else fr), str(number) + ' ' + (en if number == 1 else ens))


def wins_text(number):
    return _count(number, 'victoire', 'victoires', 'win', 'wins')


def losses_words(number):
    return _count(number, 'défaite', 'défaites', 'loss', 'losses')


def games_words(number):
    return _count(number, 'partie', 'parties', 'game', 'games')


def _text(value):
    return value if isinstance(value, Text) else Text(str(value), str(value))


def _join(parts, fr=' et ', en=' and '):
    parts = [_text(p) for p in parts]
    if len(parts) <= 1:
        return parts[0] if parts else Text('', '')
    return Text(', '.join(p.fr for p in parts[:-1]) + fr + parts[-1].fr,
                ', '.join(p.en for p in parts[:-1]) + en + parts[-1].en)


def _turn(match):
    value = match.get('max_observed_turn')
    return value if type(value) is int and value > 0 else None


def _average(values):
    return int(sum(values) / len(values) + 0.5) if len(values) >= MIN_AVERAGE else None  # 8.5 → 9, as people round


def ordered(matches):
    """Games oldest first by the day their log was added; None when no game has that day."""
    days = [m.get('added_on') if isinstance(m.get('added_on'), str) else None for m in matches]
    if not any(days):
        return None
    return [m for _, _, m in sorted(((d or '', i, m) for i, (d, m) in enumerate(zip(days, matches))),
                                    key=lambda item: (item[0], item[1]))]


def _distinct_days(games):
    days = [m.get('added_on') for m in games]
    return all(days) and len(set(days)) == len(days)


def _record(matches):
    wins = sum(m.get('outcome') == 'wins' for m in matches)
    losses = sum(m.get('outcome') == 'losses' for m in matches)
    return wins, losses


def _record_text(matches):
    """« 2 victoires, 3 défaites en 5 parties »."""
    wins, losses = _record(matches)
    return wins_text(wins) + Text(', ', ', ') + losses_words(losses) + Text(' en ', ' in ') + games_words(len(matches))


def _label(match):
    return (match.get('opponent') or {}).get('label') or 'unknown'


def overview_story(report):
    """Two or three sentences for the Overview: streak and last five, game length, the opponents met most."""
    matches = [m for m in (report or {}).get('matches', []) if isinstance(m, dict)]
    if not matches:
        return None
    sentences = []
    chronology = ordered(matches)
    if chronology:
        last = chronology[-1].get('outcome')
        streak = 0
        for match in reversed(chronology):
            if match.get('outcome') != last:
                break
            streak += 1
        first = []
        # An order is told only when the games involved were added on different days: logs added together keep
        # the order of the analysis, which may not be the order they were played in.
        if not _distinct_days(chronology[-(streak + 1):]):
            streak = 0
        if last == 'wins' and streak >= 2:
            first.append(Text('Tu es sur une série de ' + str(streak) + ' victoires', 'You are on a ' + str(streak) + '-win streak'))
        elif last == 'losses' and streak >= 2:
            first.append(Text('Tu restes sur ' + str(streak) + ' défaites de suite', 'You have lost your last ' + str(streak) + ' games'))
        if len(chronology) >= 5 and _distinct_days(chronology[-5:]):
            five = chronology[-5:]
            letters = [LETTERS.get(m.get('outcome'), OTHER_LETTER) for m in five]
            first.append(Text('tes 5 dernières parties : ' + ', '.join(f for f, _ in letters),
                              'your last 5 games: ' + ', '.join(e for _, e in letters)))
        if first:
            sentence = first[0] if len(first) == 1 else Text(first[0].fr + '; ' + first[1].fr, first[0].en + '; ' + first[1].en)
            sentences.append(Text(sentence.fr[:1].upper() + sentence.fr[1:] + '.', sentence.en[:1].upper() + sentence.en[1:] + '.'))
    won = [_turn(m) for m in matches if m.get('outcome') == 'wins' and _turn(m)]
    lost = [_turn(m) for m in matches if m.get('outcome') == 'losses' and _turn(m)]
    if _average(won) and _average(lost):
        wins, losses = _record(matches)
        sentences.append(Text('Tes victoires durent en moyenne ' + str(_average(won)) + ' tours, tes défaites '
                              + str(_average(lost)),
                              'Your wins last ' + str(_average(won)) + ' turns on average, your losses '
                              + str(_average(lost)))
                         + _known_length(wins_text(len(won)) + Text(' et ', ' and ') + losses_words(len(lost)),
                                         len(won) == wins and len(lost) == losses)
                         + Text('.', '.'))
    groups = Counter(_label(m) for m in matches if _label(m) != 'unknown')
    common = [label for label, games in sorted(groups.items(), key=lambda i: (-i[1], i[0])) if games >= 2][:2]
    if common:
        parts = []
        for label in common:
            games = [m for m in matches if _label(m) == label]
            wins, losses = _record(games)
            parts.append(_text(opponent_words(label)) + Text(', ', ', ') + wins_text(wins) + Text(' et ', ' and ')
                         + losses_words(losses) + Text(' en ', ' in ') + games_words(len(games)))
        sentences.append((Text('Ton adversaire le plus fréquent : ', 'Your most frequent opponent: ') if len(parts) == 1 else
                          Text('Tes adversaires les plus fréquents : ', 'Your most frequent opponents: '))
                         + Text('; '.join(p.fr for p in parts) + '.', '; '.join(p.en for p in parts) + '.'))
    # One sentence per line (owner, 2026-11-18): the Overview shows them in a box under its title.
    return Text('\n'.join(s.fr for s in sentences), '\n'.join(s.en for s in sentences)) if sentences else None


def matchup_story(label, matches):
    """For the opponent chosen in Combats: its record, how long the games last, the opponent cards seen most."""
    matches = [m for m in matches or [] if isinstance(m, dict)]
    if not matches:
        return None
    who = opponent_words(label)
    lead = Text('Contre ', 'Against ') + _text(who) if who else Text('Contre les adversaires non identifiés',
                                                                     'Against unidentified opponents')
    sentences = [lead + Text(' : ', ': ') + _record_text(matches) + Text('.', '.')]
    turns = [_turn(m) for m in matches if _turn(m)]
    if _average(turns):
        length = Text('Ces parties durent en moyenne ' + str(_average(turns)) + ' tours',
                      'These games last ' + str(_average(turns)) + ' turns on average')
        if len(turns) < len(matches):
            length += _known_length(games_words(len(turns)), False)
        sentences.append(length + Text('.', '.'))
    seen = Counter()
    for match in matches:
        seen.update({html.unescape(str(c.get('name'))) for c in match.get('opponent_cards', []) if c.get('name')})
    frequent = [(name, games) for name, games in sorted(seen.items(), key=lambda i: (-i[1], i[0].casefold())) if games >= 2][:3]
    if frequent and len(matches) >= 2:
        sentences.append(Text('Cartes adverses vues le plus souvent : ', 'Opponent cards seen most: ')
                         + _join([Text(name + ' (', name + ' (') + games_words(games) + Text(')', ')') for name, games in frequent])
                         + Text('.', '.'))
    return Text(' '.join(s.fr for s in sentences), ' '.join(s.en for s in sentences))


def learning_story(report):
    """(observations, plans): sentences in a player's words, each saying how many games it rests on."""
    matches = [m for m in (report or {}).get('matches', []) if isinstance(m, dict)]
    observations, plans = [], []
    by_label = {}
    for match in matches:
        if _label(match) != 'unknown':
            by_label.setdefault(_label(match), []).append(match)
    hard = sorted(((label, games) for label, games in by_label.items()
                   if _record(games)[1] >= 2 and _record(games)[1] > _record(games)[0]),
                  key=lambda item: (-_record(item[1])[1], item[0]))[:2]
    for label, games in hard:
        observations.append(Text('Tu perds souvent contre ', 'You often lose against ') + _text(opponent_words(label))
                            + Text(' : ', ': ') + losses_words(_record(games)[1]) + Text(' en ', ' in ')
                            + games_words(len(games)) + Text('.', '.'))
    easy = sorted(((label, games) for label, games in by_label.items()
                   if _record(games)[0] >= 2 and _record(games)[0] > _record(games)[1]),
                  key=lambda item: (-_record(item[1])[0], item[0]))[:1]
    for label, games in easy:
        observations.append(Text('Tu gagnes souvent contre ', 'You often win against ') + _text(opponent_words(label))
                            + Text(' : ', ': ') + wins_text(_record(games)[0]) + Text(' en ', ' in ')
                            + games_words(len(games)) + Text('.', '.'))
    losses = [m for m in matches if m.get('outcome') == 'losses' and _turn(m)]
    short = [m for m in losses if _turn(m) <= SHORT_GAME]
    if len(short) >= 2:
        # Same rule as the averages: say it when some losses have no known length.
        known = _record(matches)[1] == len(losses)
        observations.append(Text(str(len(short)) + ' de tes ' + str(len(losses)) + ' défaites'
                                 + ('' if known else ' dont la durée est connue') + ' se terminent au plus tard au '
                                 + str(SHORT_GAME) + 'e tour.',
                                 str(len(short)) + ' of your ' + str(len(losses)) + ' losses'
                                 + ('' if known else ' whose length is known') + ' end by turn ' + str(SHORT_GAME) + '.'))
    if hard:
        label, games = hard[0]
        plans.append(Text('Contre ', 'Against ') + _text(opponent_words(label)) + Text(
            ' : relis tes ' + str(_record(games)[1]) + ' défaites dans Combats, choisis une seule chose à changer et '
            'essaie-la sur tes 3 prochaines parties contre ce deck.',
            ': go over your ' + str(_record(games)[1]) + ' losses in Combats, pick one single thing to change and try it '
            'in your next 3 games against this deck.'))
    if len(short) >= 2:
        plans.append(Text('Sur tes 5 prochaines parties, note combien de Pokémon tu as en jeu à la fin de ton 2e tour; '
                          'on comparera avec tes ' + str(len(short)) + ' défaites rapides.',
                          'Over your next 5 games, write down how many Pokémon you have in play at the end of your 2nd '
                          'turn; we will compare with your ' + str(len(short)) + ' quick losses.'))
    return observations, plans


def learning_html(report):
    """The two lists of learning_story as HTML, or '' when there is nothing to say."""
    observations, plans = learning_story(report)
    text = Text('', '')
    for title, items in ((T('Ce que tes parties montrent', en='What your games show'), observations),
                         (T('Plans à essayer', en='Plans to try'), plans)):
        if items:
            text += Text('<h3>', '<h3>') + title + Text('</h3><ul>', '</h3><ul>')
            for item in items:
                text += Text('<li>' + html.escape(item.fr, quote=False) + '</li>', '<li>' + html.escape(item.en, quote=False) + '</li>')
            text += Text('</ul>', '</ul>')
    return text if text.fr else ''
