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


def count(value):
    return value if type(value) is int and value >= 0 else 0


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
    text = '<h2>' + title + '</h2><p><b>' + esc(match.get('opponent', {}).get('label', 'unknown'))
    text += T('</b> · famille hypothétique, deck exact adverse inconnu.<br>')
    text += T('Dernier tour observé : ') + (esc(maximum) if type(maximum) is int and maximum > 0 else T('inconnu'))
    text += T('. Cause de la défaite inconnue.</p><h3>Frise des événements connus</h3>')
    labels = {'use': T('Carte jouée'), 'knockout': T('K.O. observé'), 'prize': T('Récompense prise'), 'damage': T('Dégâts consignés')}
    selected = [e for e in match.get('evidence', []) if e.get('type') in labels]
    for event in selected:
        color = theme['red'] if event['type'] == 'knockout' else theme['yellow'] if event['type'] == 'prize' else theme['blue']
        turn = event.get('turn')
        stamp = 'T' + str(turn) if type(turn) is int and turn > 0 else T('Tour ?')
        role = {'self':T('Toi'), 'opponent':T('Adversaire')}.get(event.get('role'), T('Rôle inconnu'))
        text += ('<table width="100%" cellspacing="0" cellpadding="9"><tr>'
                 '<td width="55" bgcolor="' + theme['alternate'] + '"><b>' + esc(stamp) + '</b></td>'
                 '<td width="3" bgcolor="' + color + '"></td><td bgcolor="' + theme['surface'] + '">'
                 '<b>' + esc(labels[event['type']]) + '</b> · ' + esc(role) + '<br>'
                 + esc(event.get('text') or event.get('card') or T('Détail non disponible')) + '</td></tr></table><p></p>')
    if not selected:
        text += T('<p>Aucun événement détaillé disponible dans ce rapport.</p>')
    return text + T('<p>Traces disponibles seulement. Les intervalles et les informations cachées ne sont pas reconstruits.</p>')


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
        tiles['updated'] = dates[-1][:10]
    stats, plans, other = '', '', ''
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
                cells = ''.join('<td width="' + str(max(1, round(100 * value / n))) + '%" bgcolor="' + color
                                + '" style="font-size:7px;">&nbsp;</td>'
                                for value, color in ((wins, theme['blue']), (losses, theme['red']), (unknown, theme['yellow']))
                                if n and value)
                stats += ('<tr><td width="38%" style="padding:6px 8px;"><b>' + esc(group.get('archetype')) + '</b></td>'
                          '<td width="42%" style="padding:6px 8px;"><table width="100%" cellspacing="0" cellpadding="0"><tr>'
                          + cells + '</tr></table></td><td style="padding:6px 8px;" align="right">'
                          + str(wins) + T('V', en='W') + ' · ' + str(losses) + T('D', en='L') + ' · n=' + str(n) + '</td></tr>')
        elif kind == 'test_plan':
            recommendations = payload.get('recommendations', [])
            tiles['plans'] = str(len(recommendations))
            for recommendation in recommendations[:5]:
                refs = ' '.join('<span style="background:' + theme['alternate'] + ';">&nbsp;' + esc(ref) + '&nbsp;</span>'
                                for ref in recommendation.get('loss_match_refs', [])[:6])
                plans += ('<table width="100%" cellspacing="0" cellpadding="10"><tr>'
                          '<td width="4" bgcolor="' + theme['red'] + '"></td><td bgcolor="' + theme['surface'] + '">'
                          + T('<b>Contre ') + esc(recommendation.get('archetype')) + '</b><br><small>'
                          + T('Défaites : ') + refs + '</small>')
                for option in recommendation.get('plan', {}).get('alternatives', [])[:2]:
                    plans += (T('<br>➜ Base à tester : <b>') + esc(J(' / ', option.get('archetypes', []))) + '</b> · '
                              + T('<a href="pokemind://page/2">ouvrir dans Deck Lab</a>'))
                plans += '</td></tr></table><p></p>'
        else:
            other += T('<p>Plan de test ou classification révisable. Version jouée et effet causal inconnus.</p>')
    text = ''
    if stats:
        text += (T('<h3>Tes bilans par adversaire</h3>') + '<table width="100%" cellspacing="0" cellpadding="0">'
                 + stats + '</table>' + muted
                 + T('Bleu : victoires · rouge : défaites · jaune : issues inconnues. Bilan descriptif; aucune causalité.')
                 + '</p>')
    if plans:
        text += (T('<h3>À tester ensuite</h3>') + plans + muted
                 + T('Un changement à la fois; aucune amélioration causale démontrée.') + '</p>')
    text += other
    revisions = [item for item in learning.get('history', []) if item.get('revises')]
    if revisions:
        text += T('<h3>Historique des révisions</h3>')
        for item in revisions[:10]:
            revised = {'observed_game_event': T('Observations'), 'derived_statistic': T('Bilans par adversaire'),
                       'test_plan': T('Plans à tester')}.get(item.get('revises'), item.get('revises'))
            text += (muted + esc(str(item.get('recorded_at'))[:10]) + ' · ' + esc(revised)
                     + T(' · version précédente conservée') + '</p>')
    return tiles, text or T('<p>Aucune observation enregistrée pour l’instant.</p>')


def _percent(value):
    number = round(value * 100)
    return Text(str(number) + ' %', str(number) + '%')


def _when(value):
    """An ISO timestamp as « 2026-11-07 14:05 UTC »; anything else unchanged."""
    text = str(value)
    if len(text) >= 16 and text[10] == 'T':
        return text[:10] + ' ' + text[11:16] + ' UTC'
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
              + str(window.get('since', '?')) + ' → ' + str(window.get('until', '?')) + '.']
    if period:
        source.append(T('Tournois analysés : ', en='Tournaments analysed: ') + str(len(tournaments)) + ' (' + period[0] + ' → '
                      + period[1] + ')' + T('. Méta publique : population ', en='. Public meta: population ')
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
