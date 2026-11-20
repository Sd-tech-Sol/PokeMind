"""Read-only presentation projections from an already loaded battle report."""
from __future__ import annotations
from pokemind.desktop.locale_text import T, J, Text

import hashlib
import html
from collections import Counter
from datetime import date

OUTCOMES = ('wins', 'losses', 'unknown')
OUTCOME_LABELS = {'wins': T('Victoire'), 'losses': T('Défaite'), 'unknown': T('Issue inconnue')}
EVENT_LABELS = {'use': T('Cartes jouées'), 'knockout': 'K.O.', 'prize': T('Prises de Récompenses'),
                'damage': T('Dégâts consignés'), 'evolve': T('Évolutions'), 'attach': T('Attachements')}


MONTHS = (('janvier', 'January'), ('février', 'February'), ('mars', 'March'), ('avril', 'April'), ('mai', 'May'),
          ('juin', 'June'), ('juillet', 'July'), ('août', 'August'), ('septembre', 'September'),
          ('octobre', 'October'), ('novembre', 'November'), ('décembre', 'December'))
# Said once behind an « ⓘ » button, in the player's words, instead of on every line (owner, 2026-11-16).
OPPONENT_CAVEAT = T('Le deck adverse est déduit des cartes vues pendant la partie; sa liste exacte n’est pas connue.')
RECORD_CAVEAT = T('Basé seulement sur tes parties enregistrées.')
CAUSE_CAVEAT = T('Ce que PokeMind observe dans tes parties ne prouve pas pourquoi tu as gagné ou perdu.')
TIMELINE_CAVEAT = T('La frise montre seulement ce que le journal contient : les cartes cachées et la cause du résultat '
                    'ne sont pas reconstruites.')


def count(value):
    return value if type(value) is int and value >= 0 else 0


def long_date(value):
    """« 16 novembre 2026 » / « November 16, 2026 » from an ISO date; anything else is shown as it is."""
    try:
        day = date.fromisoformat(str(value)[:10])
    except ValueError:
        return str(value)
    french, english = MONTHS[day.month - 1]
    return Text(('1er' if day.day == 1 else str(day.day)) + ' ' + french + ' ' + str(day.year),
                english + ' ' + str(day.day) + ', ' + str(day.year))


def period_text(since, until):
    """« 18 octobre 2026 → 14 novembre 2026 »: the one way a period is written (owner, 2026-11-18)."""
    return long_date(since if since else '—') + ' → ' + long_date(until if until else '—')


def games_text(number):
    return Text(str(number) + (' parties' if number > 1 else ' partie'), str(number) + (' game' if number == 1 else ' games'))


def losses_text(losses, games):
    """« 4 défaites sur 6 parties »: a record in words, without « n= »."""
    return (Text(str(losses) + (' défaites sur ' if losses > 1 else ' défaite sur '),
                 str(losses) + (' loss in ' if losses == 1 else ' losses in ')) + games_text(games))


PROBABLE = 'probable:'  # opponent_archetype.PREFIX: a label guessed from the cards seen, never a recorded one
CONFIDENCE_WORDS = {'high': T('élevée', en='high'), 'medium': T('moyenne', en='medium'), 'low': T('faible', en='low')}


def opponent_name(label):
    """The opponent as shown: the internal « unknown » label never reaches the screen, and a guessed archetype
    always reads « Probablement : … »."""
    if isinstance(label, Text):
        return label
    if label is not None and str(label).startswith(PROBABLE):
        return T('Probablement : ', en='Probably: ') + str(label)[len(PROBABLE):]
    return T('Adversaire non identifié') if label is None or str(label) in ('', 'unknown') else str(label)


def opponent_words(label):
    """The opponent inside a sentence (« contre Dragapult ex (probable) »); None when unidentified."""
    if label is None or str(label) in ('', 'unknown'):
        return None
    if str(label).startswith(PROBABLE):
        name = str(label)[len(PROBABLE):]
        return T(name + ' (probable)', en=name + ' (probable)')
    return str(label)


def probable_tip(matches):
    """The ⓘ text of a guessed opponent: the confidence and the cards it rests on, and that it is not a fact."""
    results = [m['opponent']['probable'] for m in matches or []
               if isinstance((m.get('opponent') or {}).get('probable'), dict)]
    if not results:
        return None
    levels = Counter(r['confidence'] for r in results)
    seen = Counter()
    for result in results:
        seen.update(e['name'] for e in result.get('evidence', []))
    parts = [CONFIDENCE_WORDS[level] + (T(' (', en=' (') + games_text(levels[level]) + ')' if len(results) > 1 else '')
             for level in ('high', 'medium', 'low') if levels[level]]
    cards_seen = J(', ', (html.unescape(name) for name, _ in sorted(seen.items(), key=lambda i: (-i[1], i[0].casefold()))[:6]))
    return (T('Archétype probable, déduit des cartes adverses vues dans le journal; ce n’est pas une certitude.',
              en='Probable archetype, inferred from the opponent cards seen in the log; it is not a certainty.')
            + '\n' + T('Confiance : ', en='Confidence: ') + J(', ', parts)
            + '\n' + T('Cartes à l’appui : ', en='Supporting cards: ') + cards_seen
            + '\n' + T('Comparé hors ligne aux archétypes publics datés déjà sur ce PC (', en='Compared offline with the dated public archetypes already on this PC (')
            + results[0].get('version', '') + ').')


def short_kind(kind):
    """« Mon deck » from « Mon deck · référence personnelle… »: the pill keeps the name, its tooltip the rest."""
    def head(text):
        return text.split(' · ')[0].split(';')[0].strip()
    return Text(head(kind.fr), head(kind.en)) if isinstance(kind, Text) else head(str(kind))


def legality_label(value):
    """Nothing for an empty value; « Légalité à vérifier » while PokeMind does not know it."""
    french = str(getattr(value, 'fr', value) or '').casefold()
    if not french:
        return ''
    return T('Légalité à vérifier') if 'inconnu' in french or 'unknown' in french else value


def project_statistics(report, outcome='all'):
    """Keep aggregate coverage separate from available per-game details."""
    report = report or {}
    outcome = outcome if outcome in OUTCOMES else 'all'
    totals = {key: count(report.get('outcomes', {}).get(key)) for key in OUTCOMES}
    groups = []
    for group in report.get('groups', []):
        values = [count(group.get(key)) if outcome in ('all', key) else 0 for key in OUTCOMES]
        if sum(values):
            groups.append({'label': str(group.get('archetype') or 'unknown'), 'values': values})
    groups.sort(key=lambda g: (-sum(g['values']), g['label']))
    details = [m for m in report.get('matches', []) if isinstance(m, dict)
               and (outcome == 'all' or m.get('outcome', 'unknown') == outcome)]
    turns = [0, 0, 0, 0, 0]
    events = Counter()
    for match in details:
        turn = match.get('max_observed_turn')
        slot = (0 if turn <= 4 else 1 if turn <= 8 else 2 if turn <= 12 else 3) if type(turn) is int and turn > 0 else 4
        turns[slot] += 1
        for event in match.get('evidence', []):
            if isinstance(event, dict) and event.get('type') in EVENT_LABELS:
                events[event['type']] += 1
    return {'total': count(report.get('coverage', {}).get('valid')),
            'scope_n': sum(totals.values()) if outcome == 'all' else totals[outcome],
            'details_n': len(details), 'groups': groups, 'outcomes': totals,
            'turns': [{'label': label, 'values': [value]} for label, value in zip(
                (T('Tours 1–4'), T('Tours 5–8'), T('Tours 9–12'), T('Tour 13 et +'), T('Tour inconnu')), turns)],
            'events': [{'label': EVENT_LABELS[key], 'values': [events[key]]}
                       for key in EVENT_LABELS if events[key]],
            'event_count': sum(events.values())}


def favorite_key(row):
    return hashlib.sha256(row.get('export', '').encode('utf-8')).hexdigest()


def personal_deck(row):
    """One of the owner's own decks: from « Mes decks » and not an opponent rebuild, or a registered deck version.
    Never an opponent rebuild, a public reference, a public variant or a coach candidate not played."""
    if 'opponent_rebuild' in row:
        return not row['opponent_rebuild']
    return row.get('version') is not None


def _saved_on(row):
    """« mon deck · 2026-11-16 » → '2026-11-16'; '' when the row says no date (a registered deck)."""
    selector = str(row.get('selector') or '')
    return selector.rsplit(' · ', 1)[-1] if selector.startswith('mon deck · ') else ''


def active_deck_row(rows, main_key=''):
    """The Active deck of the sidebar: the owner's main deck when it exists (never an opponent rebuild), else
    their most recently saved own deck, else nothing. Independent of the deck open in Deck Lab."""
    rows = list(rows or [])
    if main_key:
        main = next((row for row in rows if favorite_key(row) == main_key), None)
        if main is not None and not main.get('opponent_rebuild'):
            return main
    newest = None
    for row in rows:  # the first of the newest wins a tie
        if personal_deck(row) and (newest is None or _saved_on(row) > _saved_on(newest)):
            newest = row
    return newest


def deck_record(report, row):
    """Outcomes of the games known to be played with this exact deck, or None when no game names it. A game names
    a deck only through `personal_deck_version`: the sha256 of its list (`export_sha256`), or its registered
    deck and version. Nothing is guessed from the cards seen in a game."""
    if not row:
        return None
    key, counts, known = favorite_key(row), dict.fromkeys(OUTCOMES, 0), 0
    for match in (report or {}).get('matches', []):
        played = match.get('personal_deck_version') if isinstance(match, dict) else None
        if not isinstance(played, dict):
            continue
        same = played.get('export_sha256') == key or (
            row.get('version') is not None and played.get('deck_id') == row.get('selector')
            and played.get('version') == row.get('version'))
        if same:
            outcome = match.get('outcome') if match.get('outcome') in OUTCOMES else 'unknown'
            counts[outcome] += 1
            known += 1
    return counts if known else None


def recent_matches(report, limit=3):
    matches = list((report or {}).get('matches', []))
    def dated(match):
        try:
            return date.fromisoformat(match.get('battle_date', ''))
        except (ValueError, TypeError):
            return None
    dates = [dated(m) for m in matches]
    if matches and all(dates):
        matches.sort(key=lambda m: dated(m), reverse=True)
        return matches[:limit], T('Combats datés · plus récents en premier')
    return list(reversed(matches))[:limit], T('Ordre du rapport · chronologie non attestée')


def timeline_html(match, theme):
    def esc(value):
        value = value if value is not None else T('Inconnu')
        return Text(html.escape(value.fr), html.escape(value.en)) if isinstance(value, Text) else html.escape(str(value))
    outcome = OUTCOME_LABELS.get(match.get('outcome'), T('Issue inconnue'))
    title = esc(match.get('match', T('Partie'))) + ' · ' + esc(outcome)
    maximum = match.get('max_observed_turn')
    text = '<h2>' + title + '</h2><p><b>' + esc(opponent_name(match.get('opponent', {}).get('label'))) + '</b>'
    if type(maximum) is int and maximum > 0:
        text += ' · ' + T('Dernier tour observé : ') + esc(maximum)
    text += '</p>' + T('<h3>Frise des événements connus</h3>')
    labels = {'use': T('Carte jouée'), 'knockout': T('K.O. observé'), 'prize': T('Récompense prise'), 'damage': T('Dégâts consignés')}
    selected = [e for e in match.get('evidence', []) if e.get('type') in labels]
    for event in selected:
        color = theme['red'] if event['type'] == 'knockout' else theme['yellow'] if event['type'] == 'prize' else theme['blue']
        turn = event.get('turn')
        stamp = 'T' + str(turn) if type(turn) is int and turn > 0 else ''  # an unknown turn is not printed
        role = {'self':T('Toi'), 'opponent':T('Adversaire')}.get(event.get('role'))  # nothing shown when it is not known
        text += ('<table width="100%" cellspacing="0" cellpadding="9"><tr>'
                 '<td width="55" bgcolor="' + theme['alternate'] + '"><b>' + (esc(stamp) or '&nbsp;') + '</b></td>'
                 '<td width="3" bgcolor="' + color + '"></td><td bgcolor="' + theme['surface'] + '">'
                 '<b>' + esc(labels[event['type']]) + '</b>' + (' · ' + esc(role) if role else '') + '<br>'
                 + esc(event.get('text') or event.get('card') or T('Détail non disponible')) + '</td></tr></table><p></p>')
    if not selected:
        text += T('<p>Aucun événement détaillé disponible dans ce rapport.</p>')
    return text


LEARNING_BAR_WIDTH = 220  # px: the bar column of « Tes bilans par adversaire »


def bar_url(values, theme):
    """The name of a results bar picture for a page's rich text: « pokemind-bar:dark/1-4-1/220 ». `theme` is the
    palette dict of the page; light when its background is light (no Qt here)."""
    ground = str(theme.get('background', '#000000')).lstrip('#')
    light = len(ground) == 6 and sum(int(ground[i:i + 2], 16) for i in (0, 2, 4)) > 384
    return ('pokemind-bar:' + ('light' if light else 'dark') + '/' + '-'.join(str(max(0, int(v))) for v in values)
            + '/' + str(LEARNING_BAR_WIDTH))


def learning_view(learning, theme):
    """Summary tiles and readable cards for the Learning Loop journal (read-only, no inference)."""
    def esc(value):
        value = value if value is not None else T('Inconnu')
        return Text(html.escape(value.fr), html.escape(value.en)) if isinstance(value, Text) else html.escape(str(value))
    muted = '<p style="color:' + theme['muted'] + ';">'
    tiles = {'games': '—', 'opponents': '—', 'plans': '—', 'updated': '—'}
    if not learning:
        return tiles, T('<p>Journal Learning Loop absent ou indisponible; rapport conservé consultable.</p>')
    current = learning.get('current', [])
    dates = sorted(str(item.get('recorded_at')) for item in current if item.get('recorded_at'))
    if dates:
        tiles['updated'] = long_date(dates[-1])
    stats, plans, unknown_seen = '', '', False
    for item in current:
        payload = item.get('payload', {})
        kind = item.get('kind')
        if kind == 'observed_game_event':
            tiles['games'] = str(len(payload.get('matches', [])))
        elif kind == 'derived_statistic':
            groups = payload.get('groups', [])
            tiles['opponents'] = str(len(groups))
            for group in groups[:10]:
                wins, losses, n = count(group.get('wins')), count(group.get('losses')), count(group.get('n'))
                unknown = max(0, n - wins - losses)
                unknown_seen = unknown_seen or bool(unknown)
                # The application's one bar (widgets.paint_bar, rounded like the Combats table): the page's browser
                # draws « pokemind-bar: » pictures from the values named here.
                bar = ('<img src="' + bar_url((wins, losses, unknown), theme) + '" width="' + str(LEARNING_BAR_WIDTH)
                       + '" height="10">' if n else '')
                stats += ('<tr><td width="38%" style="padding:6px 8px;"><b>' + esc(opponent_name(group.get('archetype')))
                          + '</b></td>'
                          '<td width="42%" valign="middle" style="padding:6px 8px;">'
                          + bar + '</td><td style="padding:6px 8px;" align="right">'
                          + str(wins) + ' ' + T('V', en='W') + ' · ' + str(losses) + ' ' + T('D', en='L') + ' · '
                          + games_text(n) + '</td></tr>')
        elif kind == 'test_plan':
            recommendations = payload.get('recommendations', [])
            tiles['plans'] = str(len(recommendations))
            for recommendation in recommendations[:5]:
                refs = ' '.join('<span style="background:' + theme['alternate'] + ';">&nbsp;' + esc(ref) + '&nbsp;</span>'
                                for ref in recommendation.get('loss_match_refs', [])[:6])
                plans += ('<table width="100%" cellspacing="0" cellpadding="10"><tr>'
                          '<td width="4" bgcolor="' + theme['red'] + '"></td><td bgcolor="' + theme['surface'] + '">'
                          + T('<b>Contre ') + esc(opponent_name(recommendation.get('archetype'))) + '</b><br>'
                          + T('Défaites : ') + refs)
                for option in recommendation.get('plan', {}).get('alternatives', [])[:2]:
                    plans += (T('<br>➜ Base à tester : <b>') + esc(J(' / ', option.get('archetypes', []))) + '</b> · '
                              + T('<a href="pokemind://page/2">ouvrir dans Deck Lab</a>'))
                plans += '</td></tr></table><p></p>'
    text = ''
    if stats:
        text += (T('<h3>Tes bilans par adversaire</h3>') + '<table width="100%" cellspacing="0" cellpadding="0">'
                 + stats + '</table>' + muted + T('Bleu : victoires · Rouge : défaites')
                 + (T(' · Jaune : sans résultat', en=' · Yellow: no result') if unknown_seen else '') + '</p>')
    if plans:
        text += T('<h3>À tester ensuite</h3>') + plans
    revisions = [item for item in learning.get('history', []) if item.get('revises')]
    if revisions:
        text += T('<h3>Historique des révisions</h3>')
        for item in revisions[:10]:
            revised = {'observed_game_event': T('Observations'), 'derived_statistic': T('Bilans par adversaire'),
                       'test_plan': T('Plans à tester')}.get(item.get('revises'), item.get('revises'))
            text += (muted + esc(long_date(item.get('recorded_at'))) + ' · ' + esc(revised)
                     + T(' · version précédente conservée') + '</p>')
    return tiles, text or T('<p>Aucune observation enregistrée pour l’instant.</p>')


# The three cautions the Learning page used to print, behind its « ⓘ » (owner, 2026-11-16).
LEARNING_CAVEAT = J('\n', (
    T('PokeMind garde ce qu’il observe dans tes parties et révise ses idées quand de nouvelles parties arrivent; '
      'aucun modèle d’IA n’est réentraîné.'),
    CAUSE_CAVEAT,
    T('Teste un seul changement à la fois : rien ne prouve encore qu’un plan améliore tes résultats.')))


def _percent(value):
    number = round(value * 100)
    return Text(str(number) + ' %', str(number) + '%')


def _when(value):
    """An ISO timestamp as « 7 novembre 2026 · 14:05 UTC »; anything else unchanged."""
    text = str(value)
    if len(text) >= 16 and text[10] == 'T':
        return long_date(text) + ' · ' + text[11:16] + ' UTC'
    return text


def _interval(bounds):
    low, high = (round(v * 100) for v in bounds)
    return Text('IC 95 % ' + str(low) + '–' + str(high) + ' %', '95% CI ' + str(low) + '–' + str(high) + '%')


PUBLIC_EVIDENCE = {
    'public_label_corroborated': T('étiquette publique de cette liste, corroborée par ses Pokémon',
                                   en='public label of this list, corroborated by its Pokémon'),
    'pokemon_in_list': T('correspondance par les Pokémon de ta liste (indice, pas une certification)',
                         en='match on the Pokémon in your list (a hint, not a certification)')}
PUBLIC_REFRESH = {
    'CACHE_TODAY': T('Instantané du jour déjà présent : aucune requête.', en='Today’s snapshot already present: no request.'),
    'SOURCE_SNAPSHOT_SAVED': T('Nouvel instantané public enregistré.', en='New public snapshot saved.'),
    'INSUFFICIENT_OR_BLOCKED_PUBLIC_DATA': T('Source indisponible, limitée ou sans match exploitable : dernier instantané valide conservé.',
                                             en='Source unavailable, rate-limited or without usable matches: last valid snapshot kept.'),
    'REFRESH_DAILY_LIMIT': T('Limite d’actualisations manuelles du jour atteinte : dernier instantané conservé.',
                             en='Today’s manual refresh limit reached: last snapshot kept.'),
    'REFRESH_TOO_SOON': T('Actualisation trop rapprochée de la précédente : réessaie plus tard.',
                          en='Too soon after the previous refresh: try again later.'),
    'INTERRUPTED': T('Actualisation interrompue : dernier instantané valide conservé.',
                     en='Refresh interrupted: last valid snapshot kept.'),
    'ERROR': T('Actualisation en échec : dernier instantané valide conservé.', en='Refresh failed: last valid snapshot kept.'),
    'IN_PROGRESS': T('Dernière tentative non terminée.', en='Last attempt did not finish.')}
EXCLUSION_LABELS = {
    'bye_or_automatic_loss': T('byes', en='byes'), 'double_loss': T('doubles défaites', en='double losses'),
    'unclassified_archetype': T('archétype non publié', en='archetype not published'),
    'participant_missing_from_standings': T('participant absent du classement', en='player missing from standings'),
    'winner_not_in_pairing': T('résultat incohérent', en='inconsistent result')}


def _identity_text(view):
    identity = view.get('identity') or {}
    if not view or view.get('status') == 'NO_SNAPSHOT':
        return T('Aucun instantané public disponible pour l’instant. « Actualiser » lance une collecte bornée.',
                 en='No public snapshot available yet. “Refresh” starts a bounded collection.')
    if identity.get('status') == 'IDENTIFIED':
        return (T('Archétype public : ', en='Public archetype: ') + str(identity['archetype_name']) + ' — '
                + PUBLIC_EVIDENCE.get(identity.get('evidence'), '') + '. '
                + T('Statistiques de l’archétype, pas de tes 60 cartes exactes.', en='Archetype statistics, not your exact 60 cards.'))
    if identity.get('status') == 'AMBIGUOUS':
        return (T('Archétype non identifié : plusieurs archétypes publics correspondent autant (',
                  en='Archetype not identified: several public archetypes match equally (')
                + J(', ', identity.get('candidates', [])) + T('). Aucun taux attribué à ce deck.', en='). No rate attributed to this deck.'))
    return T('Archétype non identifié : aucun archétype de l’échantillon public ne correspond aux Pokémon de cette liste. '
             'Aucun taux attribué à ce deck; méta publique générale ci-dessous.',
             en='Archetype not identified: no archetype of the public sample matches the Pokémon of this list. '
             'No rate attributed to this deck; general public meta below.')


def project_public_stats(view, mode=None):
    """Texts and chart rows for Deck Lab › Statistiques; never a number without its n and its source."""
    view = view or {}
    archetype = view.get('archetype')
    meta_block = view.get('meta') or {}
    modes = list((archetype or {}).get('modes', {}).items())
    chosen = next((m for m in modes if m[0] == mode), modes[0] if modes else None)
    result = {'modes': [(key, value['n']) for key, value in modes], 'mode': chosen[0] if chosen else None,
              'identity': _identity_text(view), 'matchup_rows': [], 'meta_rows': [],
              'history': T('Évolution datée : historique insuffisant (moins de deux tournois).',
                           en='Dated trend: not enough history (fewer than two tournaments).')}
    classified = meta_block.get('n_classified', 0)
    for row in meta_block.get('archetypes', []):
        share = (' · ' + _percent(row['share'])) if row.get('share') is not None else ''
        result['meta_rows'].append({'label': str(row['name']), 'values': [row['n']],
            'description': str(row['name']) + ' : ' + str(row['n']) + T(' placements sur ', en=' placements of ')
            + str(classified) + T(' classifiés', en=' classified') + share})
    lines = []
    if archetype:
        representation = archetype.get('representation') or {}
        picked = representation.get(chosen[0]) if chosen else None
        picked = picked or next(iter(representation.values()), None)
        if picked:
            lines.append(T('Représentation (tournois ', en='Representation (') + str(picked['population'])
                         + T(') : ', en=' events): ')
                         + (_percent(picked['share']) if picked['share'] is not None else T('échantillon insuffisant', en='sample too small'))
                         + ' (' + str(picked['n']) + ' / ' + str(picked['classified'])
                         + T(' placements classifiés, ', en=' classified placements, ') + str(picked['tournaments'])
                         + T(' tournoi(s))', en=' event(s))'))
            others = [str(r['population']) + ' ' + str(r['n']) + '/' + str(r['classified'])
                      for key, r in representation.items() if r is not picked]
            if others:
                lines.append(T('Autres populations de tournois, jamais additionnées : ',
                               en='Other event populations, never added together: ') + J(', ', others))
        if chosen:
            data = chosen[1]
            rate = (_percent(data['win_fraction']) + ' (' + _interval(data['wilson_95']) + ')'
                    if data['win_fraction'] is not None else T('données insuffisantes', en='insufficient data'))
            lines.append(T('Taux de victoire ', en='Win rate ') + chosen[0] + ' : ' + rate + ' · ' + str(data['wins'])
                         + T(' V / ', en=' W / ') + str(data['losses']) + T(' D / ', en=' L / ') + str(data['ties'])
                         + T(' N · n=', en=' T · n=') + str(data['n'])
                         + T(' matchs admissibles (miroirs exclus : ', en=' admissible matches (mirrors excluded: ')
                         + str(data['mirror_matches']) + ')')
            for row in data['matchups'][:8]:
                rate = (_percent(row['win_fraction']) + ', ' + _interval(row['wilson_95'])
                        if row['win_fraction'] is not None else T('n trop petit, aucun pourcentage', en='n too small, no percentage'))
                result['matchup_rows'].append({'label': str(row['opponent']), 'values': [row['wins'], row['losses'], row['ties']],
                    'description': T('contre ', en='vs ') + str(row['opponent']) + ' : ' + str(row['wins']) + T(' V, ', en=' W, ')
                    + str(row['losses']) + T(' D, ', en=' L, ') + str(row['ties']) + T(' N; n=', en=' T; n=') + str(row['n'])
                    + ' · ' + rate})
            others = [key + ' n=' + str(n) for key, n in result['modes'] if key != chosen[0]]
            if others:
                lines.append(T('Autre population, jamais fusionnée : ', en='Other population, never merged: ') + J(', ', others))
        else:
            lines.append(T('Taux de victoire : aucun match admissible.', en='Win rate: no admissible match.'))
        history = archetype.get('history') or []
        if history:
            result['history'] = T('Évolution datée (part par tournoi) : ', en='Dated trend (share per tournament): ') + J(' · ', (
                row['date'] + ' ' + str(row.get('population', '')) + ' ' + (_percent(row['share']) if row['share'] is not None else T('n petit', en='small n'))
                + ' (' + str(row['n']) + '/' + str(row['classified']) + ')' for row in history))
        excluded = archetype.get('excluded_all_archetypes') or {}
        if excluded:
            lines.append(T('Exclus de l’échantillon (tous archétypes) : ', en='Excluded from the sample (all archetypes): ')
                         + J(', ', (EXCLUSION_LABELS.get(k, k) + ' ' + str(n) for k, n in sorted(excluded.items()))))
    result['summary'] = J('\n', lines)
    tournaments = view.get('tournaments') or []
    window = view.get('window') or {}
    period = view.get('date_range')
    source = [T('Source : ', en='Source: ') + str(view.get('source', 'Limitless TCG')) + ' · ' + str(view.get('docs_url', '')),
              T('Population : Pokémon TCG Live en ligne · Standard · tournois publics de la plateforme Limitless '
                '(pas tous les tournois, aucun tournoi physique). Fenêtre ',
                en='Population: Pokémon TCG Live online · Standard · public tournaments of the Limitless platform '
                '(not every tournament, no in-person event). Window ')
              + period_text(window.get('since'), window.get('until')) + '.']
    if period:
        source.append(T('Tournois analysés : ', en='Tournaments analysed: ') + str(len(tournaments)) + ' (' + period_text(period[0], period[1]) + ')' + T('. Méta publique : population ', en='. Public meta: population ')
                      + str(meta_block.get('population')) + T(' (la plus large), n placements = ', en=' (the largest), n placements = ')
                      + str(meta_block.get('n_placements', 0)) + T(', dont classifiés ', en=', classified ') + str(classified) + '.')
    source.append(T('Dernière synchronisation réussie : ', en='Last successful sync: ')
                  + (_when(view['last_success_at']) if view.get('last_success_at') else T('aucune', en='none'))
                  + T(' (date de récupération, pas date des matchs).', en=' (retrieval date, not match date).'))
    refresh = view.get('refresh') or {}
    outcome = refresh.get('last_outcome') or {}
    if refresh.get('last_attempt_at'):
        source.append(T('Dernière tentative : ', en='Last attempt: ') + _when(refresh['last_attempt_at']) + ' · '
                      + PUBLIC_REFRESH.get(outcome.get('status'), str(outcome.get('status', ''))))
    result['source'] = J('\n', source)
    current = (view.get('refresh_outcome') or {}).get('status')
    result['refresh'] = PUBLIC_REFRESH.get(current, '') if current else ''
    return result
