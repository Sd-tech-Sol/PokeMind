"""Summaries in a player's words (pipeline 023, phase 7), on invented games only."""
from __future__ import annotations

import re

from pokemind.desktop.stories import learning_html, learning_story, matchup_story, overview_story

JARGON = re.compile(r'n\s*=|corpus|causal|représentativ|representativ|%|taux de victoire|win rate', re.I)


def game(number, outcome, label='Famille inventée A', turn=8, day='2026-11-01', cards=()):
    return {'match': 'M%04d' % number, 'outcome': outcome, 'max_observed_turn': turn, 'added_on': day,
            'opponent': {'label': label}, 'opponent_cards': [{'name': c} for c in cards]}


def season():
    return {'matches': [
        game(1, 'losses', turn=5, day='2026-11-01', cards=('Créature inventée', 'Objet inventé')),
        game(2, 'wins', 'Famille inventée B', turn=9, day='2026-11-02'),
        game(3, 'losses', turn=6, day='2026-11-03', cards=('Créature inventée', 'Objet inventé', 'Stade inventé')),
        game(4, 'wins', 'probable:Famille devinée', turn=10, day='2026-11-04'),
        game(5, 'losses', 'unknown', turn=None, day='2026-11-05'),
        game(6, 'wins', 'Famille inventée B', turn=7, day='2026-11-06'),
        game(7, 'wins', 'Famille inventée A', turn=8, day='2026-11-07', cards=('Créature inventée',)),
    ]}


def test_overview_story_tells_streak_last_five_length_and_opponents_from_real_games():
    story = overview_story(season())
    # One sentence per line; one loss has no known length, so the average says what it rests on.
    assert story.fr == ('Tu es sur une série de 2 victoires; tes 5 dernières parties : D, V, D, V, V.\n'
                        'Tes victoires durent en moyenne 9 tours, tes défaites 6 '
                        '(calculé sur 4 victoires et 2 défaites dont la durée est connue).\n'
                        'Tes adversaires les plus fréquents : Famille inventée A, 1 victoire et 2 défaites en 3 parties; '
                        'Famille inventée B, 2 victoires et 0 défaite en 2 parties.')
    assert story.en.split('\n')[1] == ('Your wins last 9 turns on average, your losses 6 '
                                       '(computed over 4 wins and 2 losses whose length is known).')
    assert story.en.startswith('You are on a 2-win streak; your last 5 games: L, W, L, W, W.\nYour wins last 9 turns')
    assert story.en.endswith('Your most frequent opponents: Famille inventée A, 1 win and 2 losses in 3 games; '
                             'Famille inventée B, 2 wins and 0 losses in 2 games.')
    assert not JARGON.search(story.fr) and not JARGON.search(story.en)


def test_every_length_known_keeps_the_short_wording_and_a_game_without_result_is_n():
    report = season()
    report['matches'][4] = game(5, 'draw', 'unknown', turn=None, day='2026-11-05')
    story = overview_story(report)
    assert story.fr.split('\n')[0] == 'Tu es sur une série de 2 victoires; tes 5 dernières parties : D, V, N, V, V.'
    assert story.en.split('\n')[0].endswith('your last 5 games: L, W, N, W, W.')
    assert '?' not in story.fr and '?' not in story.en
    assert 'tes défaites 6 (sur 4 victoires et 2 défaites).' in story.fr
    assert 'dont la durée est connue' not in story.fr
    from pokemind.desktop.stories import OVERVIEW_CAVEAT
    assert 'N = nul ou sans résultat' in OVERVIEW_CAVEAT.fr and 'N = draw or no result' in OVERVIEW_CAVEAT.en


def test_a_sentence_appears_only_when_its_data_exists():
    assert overview_story({'matches': []}) is None and overview_story(None) is None
    # No day the logs were added: no streak and no « last five »; one game per opponent: no « you meet ».
    undated = {'matches': [dict(game(1, 'wins', turn=None), added_on=None), dict(game(2, 'losses', 'B'), added_on=None)]}
    assert overview_story(undated) is None
    losing = {'matches': [game(i, 'losses', turn=4, day='2026-11-0%d' % i) for i in range(1, 4)]}
    assert overview_story(losing).fr.startswith('Tu restes sur 3 défaites de suite.')
    assert 'Tes victoires' not in overview_story(losing).fr
    # Logs added the same day keep the order of the analysis: no streak and no « last five » is told then.
    same_day = {'matches': [game(i, 'wins', 'Famille %d' % i, day='2026-11-01') for i in range(1, 7)]}
    assert overview_story(same_day) is None
    two_days = {'matches': same_day['matches'] + [game(7, 'wins', 'Famille 7', day='2026-11-02')]}
    assert overview_story(two_days) is None  # the streak would include games of the same day


def test_matchup_story_gives_record_length_and_cards_seen_most():
    report = season()
    chosen = [m for m in report['matches'] if m['opponent']['label'] == 'Famille inventée A']
    story = matchup_story('Famille inventée A', chosen)
    assert story.fr == ('Contre Famille inventée A : 1 victoire, 2 défaites en 3 parties. Ces parties durent en moyenne '
                        '6 tours. Cartes adverses vues le plus souvent : Créature inventée (3 parties) et Objet inventé (2 parties).')
    assert story.en.startswith('Against Famille inventée A: 1 win, 2 losses in 3 games.')
    partly = chosen + [game(8, 'losses', turn=None, day='2026-11-08')]
    assert 'Ces parties durent en moyenne 6 tours (calculé sur 3 parties dont la durée est connue).' in matchup_story(
        'Famille inventée A', partly).fr
    assert 'These games last 6 turns on average (computed over 3 games whose length is known).' in matchup_story(
        'Famille inventée A', partly).en
    guessed = matchup_story('probable:Famille devinée', [m for m in report['matches'] if m['match'] == 'M0004'])
    assert guessed.fr == 'Contre Famille devinée (probable) : 1 victoire, 0 défaite en 1 partie.'
    assert guessed.en == 'Against Famille devinée (probable): 1 win, 0 losses in 1 game.'
    assert matchup_story('unknown', [report['matches'][4]]).fr.startswith('Contre les adversaires non identifiés : ')
    assert matchup_story('x', []) is None


def test_learning_story_speaks_like_a_player_and_counts_its_games():
    observations, plans = learning_story(season())
    assert [o.fr for o in observations] == ['Tu perds souvent contre Famille inventée A : 2 défaites en 3 parties.',
                                            'Tu gagnes souvent contre Famille inventée B : 2 victoires en 2 parties.',
                                            '2 de tes 2 défaites dont la durée est connue se terminent au plus tard '
                                            'au 6e tour.']
    known = season()
    known['matches'][4]['max_observed_turn'] = 11
    assert learning_story(known)[0][-1].fr == '2 de tes 3 défaites se terminent au plus tard au 6e tour.'
    assert plans[0].fr.startswith('Contre Famille inventée A : relis tes 2 défaites dans Combats')
    assert plans[1].en.startswith('Over your next 5 games')
    for text in observations + plans:
        assert not JARGON.search(text.fr) and not JARGON.search(text.en)
    html = learning_html(season())
    assert '<h3>Ce que tes parties montrent</h3>' in html.fr and '<h3>Plans to try</h3>' in html.en
    assert learning_html({'matches': [game(1, 'wins')]}) == ''
