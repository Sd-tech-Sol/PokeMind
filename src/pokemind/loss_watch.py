"""Loss-first matchup follow-up (PM-COACH-LOSS-PRIORITY-001).

Every game, won, lost or unknown, stays in the history and the matchup statistics. Only the opponent
families that beat the owner become work topics. The follow-up is derived from the canonical local
report each time it is read: nothing is stored a second time, nothing is deleted and no deck is written.
A family the owner later beats keeps its follow-up, with the win added to its record.
"""
from __future__ import annotations

from collections import Counter

from pokemind import seasons

OUTCOMES = {'W': 'win', 'wins': 'win', 'L': 'loss', 'losses': 'loss'}
SMALL_SAMPLE = 5  # below this many decided games a family is a topic to watch, not a statistical finding
CARDS_SHOWN = 12
FAMILY_CHARS = 120
POLICY = ('Toutes les parties comptent dans les statistiques. Seules les familles qui ont battu le propriétaire '
          'sont suivies. L’automate local peut ajouter une hypothèse PUBLIC après défaite ou victoire 6–5 attestée, '
          'avec preuves suffisantes et sans doublon. Aucune liste adverse de 60 cartes n’est connue : '
          'seules les cartes vues dans les journaux sont des faits.')


def outcome_of(match):
    """'win', 'loss' or 'unknown', from the owner's side as the parser recorded it; never inferred."""
    return OUTCOMES.get((match or {}).get('outcome'), 'unknown')


def family_of(match):
    return ((match or {}).get('opponent') or {}).get('label') or 'unknown'


def _uncertainty(losses, n):
    if n < SMALL_SAMPLE:
        first = 'Première défaite : ' if losses == 1 else ''
        return (first + 'échantillon faible (n=' + str(n) + ' < ' + str(SMALL_SAMPLE)
                + ') : sujet à surveiller, aucune conclusion statistique.')
    return 'n=' + str(n) + ' : tendance descriptive du corpus choisi; taux de victoire global inconnu.'


def _entry(group, matches, dates):
    refs = set(group.get('matches', []))
    losses = [m for m in matches if m.get('match') in refs and m.get('outcome') == 'losses']
    days = sorted(day for day in (seasons.day_of(m, dates) for m in losses) if day)
    seen = Counter(name for m in losses for name in {c['name'] for c in m.get('opponent_cards', []) if c.get('name')})
    wins, lost = group.get('wins', 0), group.get('losses', 0)
    n = wins + lost
    family = str(group.get('archetype') or 'unknown')[:FAMILY_CHARS]
    return {'family': family, 'family_resolved': family != 'unknown',
            'family_basis': 'estimée d’après les cartes visibles; liste exacte inconnue',
            'wins': wins, 'losses': lost, 'unknown': group.get('unknown', 0), 'n': n,
            'games': len(refs) or n + group.get('unknown', 0),
            'loss_share': round(lost / n, 2) if n else None,
            'status': 'recurring_loss' if lost >= 2 else 'watch',
            'first_loss_day': days[0] if days else 'unknown', 'last_loss_day': days[-1] if days else 'unknown',
            'cards_seen_in_losses': [{'name': name, 'loss_games_seen': count} for name, count in sorted(
                seen.items(), key=lambda item: (-item[1], item[0].casefold(), item[0]))][:CARDS_SHOWN],
            'cards_basis': 'observées dans les journaux de défaite; ni liste de 60 ni preuve de version',
            'signals': [{k: s[k] for k in ('explanation', 'loss_games', 'win_games')} for s in group.get('signals', [])[:3]],
            'uncertainty': _uncertainty(lost, n), 'causal_effect': 'unknown'}


def problem_matchups(report, *, dates=None, focus=(), limit=8):
    """The families that beat the owner, the most losses first, with their whole record (wins included)."""
    if not report:
        return {'status': 'NO_LOCAL_REPORT', 'families': []}
    matches = report.get('matches', [])
    groups = [g for g in report.get('groups', []) if g.get('losses', 0) >= 1]
    entries = sorted((_entry(g, matches, dates or {}) for g in groups),
                     key=lambda e: (-e['losses'], -(e['loss_share'] or 0), e['family'].casefold(), e['family']))
    wanted = [e for e in entries if any(word in e['family'].casefold() for word in focus)]
    shown = wanted + [e for e in entries if e not in wanted][:max(0, limit - len(wanted))]
    return {'source': 'PokeMind · suivi local des défaites, dérivé du rapport canonique ' + str(report.get('as_of', 'unknown')),
            'scope': 'toutes les parties enregistrées, toutes saisons', 'policy': POLICY,
            'families_tracked': len(entries), 'total_losses': sum(e['losses'] for e in entries),
            'recurring_families': sum(e['status'] == 'recurring_loss' for e in entries),
            'families': shown, 'more': max(0, len(entries) - len(shown))}


def followup(report, match, *, dates=None):
    """What a pasted game means for the follow-up: a loss opens or updates its family, a win or an
    unknown result only updates a follow-up that already exists. No deck is ever written here."""
    outcome, family = outcome_of(match), family_of(match)
    group = next((g for g in (report or {}).get('groups', []) if (g.get('archetype') or 'unknown') == family), None)
    tracked = bool(group and group.get('losses', 0) >= 1)
    record = _entry(group, (report or {}).get('matches', []), dates or {}) if tracked else None
    note = {'loss': 'Défaite : famille suivie comme matchup difficile' + (' (défaite récurrente).' if record and
                    record['status'] == 'recurring_loss' else ' (première défaite : à surveiller).'),
            'win': 'Victoire comptée' + (' dans le suivi existant de cette famille.' if tracked
                                         else '; famille non suivie; reconstruction conditionnelle distincte.'),
            'unknown': 'Résultat inconnu : compté comme inconnu, aucun suivi créé ni deck enregistré.'}[outcome]
    return {'outcome': outcome, 'family': family, 'tracked': tracked, 'family_record': record, 'note': note,
            'automatic_deck_save': 'conditional_local_public_only', 'policy': POLICY}
