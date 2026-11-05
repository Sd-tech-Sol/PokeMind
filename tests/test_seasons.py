"""Invented games only: statistics of the current season, of past seasons, and of every season together."""
import json
import os
from datetime import datetime

import pytest

from pokemind import battle_batch, seasons
from pokemind.desktop.services import Services

LADDERS = seasons.OFFICIAL  # read before conftest empties it for the other tests


@pytest.fixture(autouse=True)
def real_ladders(every_game_in_one_season):
    seasons.OFFICIAL = LADDERS  # conftest puts back the real value after the test
    yield


def stamp(day):
    return datetime.fromisoformat(day + 'T12:00:00').timestamp()


def game(number, outcome, family, log):
    return {'match': f'M{number:04d}', 'outcome': outcome, 'opponent': {'label': family},
            'opponent_cards': [{'name': 'Carte inventée ' + family}], 'evidence': [], 'max_observed_turn': 8,
            'explicit_prize_totals': {'self': None, 'opponent': None}, 'own_deck_hypothesis': {'label': 'Mon deck'},
            'source_relative': log}


def corpus(root):
    """Two games before the November 2026 ladder, three after; one log no longer on disk."""
    folder = root / seasons.LOGS
    folder.mkdir(parents=True)
    days = {'pokemind-a.log': '2026-10-20', 'pokemind-b.log': '2026-11-04', 'pokemind-c.log': '2026-11-05',
            'pokemind-d.log': '2026-11-20'}
    for name, day in days.items():
        (folder / name).write_text('journal inventé', encoding='utf-8')
        os.utime(folder / name, (stamp(day), stamp(day)))
    matches = [game(1, 'losses', 'Famille A', 'pokemind-a.log'), game(2, 'wins', 'Famille B', 'pokemind-b.log'),
               game(3, 'losses', 'Famille A', 'pokemind-c.log'), game(4, 'wins', 'Famille A', 'pokemind-d.log'),
               game(5, 'unknown', 'Famille B', 'pokemind-d.log'), game(6, 'wins', 'Famille C', 'pokemind-gone.log')]
    report = {'as_of': '2026-11-20', 'model_version': 'battle-batch-v4', 'matches': matches,
              'groups': battle_batch.group_matches(matches), 'outcomes': seasons.counts(matches),
              'coverage': {'valid': len(matches), 'files_seen': 5}, 'own_decks': {'Mon deck': 6},
              'recommendations': [{'invented': True}]}
    return report


def test_a_season_lasts_from_its_ladder_to_the_next_and_the_owner_can_start_one(local_tmp):
    rows = seasons.periods(local_tmp, today='2026-11-20')
    assert [(r['key'], r['start'], r['end']) for r in rows] == [
        ('before', None, '2026-11-05'), ('2026-11-05', '2026-11-05', None)]
    assert rows[-1]['name'] == 'Delta Reign' and rows[-1]['source'].startswith('https://community.pokemon.com/')
    assert seasons.periods(local_tmp, today='2026-11-04') == [
        {'key': 'before', 'name': 'Toutes les parties', 'start': None, 'end': None}]  # not begun yet
    seasons.add_start(local_tmp, '  Saison   inventée ', '2027-02-04')
    assert seasons.add_start(local_tmp, 'Renommée', '2027-02-04') == {'start': '2027-02-04', 'name': 'Renommée'}
    rows = seasons.periods(local_tmp, today='2027-03-01')
    assert [(r['key'], r['end']) for r in rows] == [('before', '2026-11-05'), ('2026-11-05', '2027-02-04'),
                                                    ('2027-02-04', None)]
    assert rows[-1]['name'] == 'Renommée' and rows[-1]['owner']
    assert seasons.resolve('current', rows) is rows[-1] and seasons.resolve('all', rows) is None
    assert seasons.resolve('2026-11-05', rows) is rows[1] and seasons.resolve('2020-01-01', rows) is rows[-1]
    single = seasons.periods(local_tmp, today='2026-11-04')[0]
    report = {'matches': [], 'groups': []}
    assert seasons.scoped(report, single, {}) is report  # no season begun: the report itself
    (local_tmp / seasons.FILE).write_text('{"schema_version": 1, "starts": [{"start": "pas une date"}]}', encoding='utf-8')
    assert seasons.owner_starts(local_tmp) == []  # a broken file never breaks the statistics


def test_season_view_counts_only_its_games_with_the_engine_grouping(local_tmp):
    report = corpus(local_tmp)
    dates = seasons.added_dates(local_tmp, report['matches'])
    assert dates == {'pokemind-a.log': '2026-10-20', 'pokemind-b.log': '2026-11-04', 'pokemind-c.log': '2026-11-05',
                     'pokemind-d.log': '2026-11-20', 'pokemind-gone.log': None}
    rows = seasons.periods(local_tmp, today='2026-11-20')
    current = seasons.scoped(report, seasons.resolve('current', rows), dates)
    assert [m['match'] for m in current['matches']] == ['M0003', 'M0004', 'M0005']
    assert current['outcomes'] == {'wins': 1, 'losses': 1, 'unknown': 1} and current['coverage']['valid'] == 3
    assert current['groups'] == battle_batch.group_matches(current['matches'])  # same numbers as the engine
    assert [(g['archetype'], g['wins'], g['losses'], g['n']) for g in current['groups']] == [
        ('Famille A', 1, 1, 2), ('Famille B', 0, 0, 0)]
    assert current['season']['name'] == 'Delta Reign' and current['season']['all_games'] == 6
    assert current['recommendations'] == report['recommendations'] and current['own_decks'] == {'Mon deck': 3}
    before = seasons.scoped(report, seasons.resolve('before', rows), dates)
    assert [m['match'] for m in before['matches']] == ['M0001', 'M0002']
    every = seasons.scoped(report, None, dates)
    assert every['matches'] == report['matches'] and every['groups'] == report['groups']
    assert every['season'] == {'key': 'all', 'name': 'Cumul · toutes les saisons', 'games': 6, 'undated': 1}
    assert report['coverage']['valid'] == 6 and len(report['matches']) == 6  # the full report is never changed
    summary = seasons.summary(report, dates, rows)
    assert [(s['start'], s['games'], s['wins'], s['losses']) for s in summary['seasons']] == [
        (None, 2, 1, 1), ('2026-11-05', 3, 1, 1)]
    assert summary['all_seasons'] == {'games': 6, 'wins': 3, 'losses': 2, 'unknown': 1}


def test_services_show_the_chosen_season_and_tell_the_coach_both(local_tmp, monkeypatch):
    report = corpus(local_tmp)
    report['recommendations'] = []
    monkeypatch.setattr(seasons, 'periods', lambda root, today=None: [
        {'key': 'before', 'name': 'Avant le 2026-11-05', 'start': None, 'end': '2026-11-05'},
        {'key': '2026-11-05', 'name': 'Delta Reign', 'start': '2026-11-05', 'end': None}])
    services = Services(local_tmp)
    services.set_full_report(report)
    assert services.report['coverage']['valid'] == 3 and services.full_report is report
    services.set_season('all')
    assert services.report['coverage']['valid'] == 6
    services.set_season('current')
    context = services.context('mes statistiques', 'aggregates')
    assert context['valid_games'] == 3 and context['season_shown']['name'] == 'Delta Reign'
    assert context['seasons']['all_seasons']['games'] == 6 and 'key' not in context['season_shown']
    assert 'Saison : Delta Reign' in services.local_answer('mes statistiques')
    json.dumps(context, ensure_ascii=False)
