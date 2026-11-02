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
