"""Deck Lab › Statistiques (PM-DECKLAB-PUBLIC-STATS-001): public archetype figures, invented public data only.

The real collector runs (research_matchups -> run_campaign -> sync_meta -> LimitlessApiClient); only the HTTP
opener is replaced by an invented Limitless server. Every expected number is recomputed here from the raw
pairings by a separate oracle, never read back from the code under test.
"""
from __future__ import annotations

import io
import json
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

import pytest

from pokemind import deck_public_stats as stats
from pokemind import meta, public_campaign

AS_OF = '2026-11-07'
A = ('alphamon-betadrake', 'Alphamon Betadrake')
X = ('alphamon', 'Alphamon')
G = ('gammaroo', 'Gammaroo')
D = ('deltaflare-box', 'Deltaflare Box')
CATALOG = dict([A, X, G, D])
PRIVATE_NAME = 'Gammaroo secret du propriétaire'
PRIVATE_DECK = ('Pokémon: 12\n3 Alphamon ex INV 1\n2 Alphalet INV 2\n3 Betadrake INV 3\n2 Betalet INV 4\n'
                '1 Gammaroo INV 5\n1 Lonelytech INV 6\nTrainer: 36\n36 Invented Trainer INV 7\n'
                'Energy: 12\n12 Basic Invented Energy INV 8\nTotal Cards: 60\n')


def roster():
    """24 invented players: 8 A, 8 G, 4 D, 2 X and 2 without a published archetype."""
    kinds = [A] * 8 + [G] * 8 + [D] * 4 + [X] * 2 + [None] * 2
    return [(f'p{i:02d}', kind) for i, kind in enumerate(kinds)]


def round_robin_pairings(players, rounds=5):
    """Circle method: each round a perfect matching; invented, deterministic results with some ties."""
    names = [p for p, _ in players]
    fixed, rest = names[0], names[1:]
    result = []
    for r in range(1, rounds + 1):
        order = [fixed] + rest
        for k in range(len(order) // 2):
            p1, p2 = order[k], order[-1 - k]
            winner = 0 if (k * r) % 7 == 3 else (p1 if (k + r) % 3 else p2)
            result.append({'phase': 1, 'round': r, 'table': k + 1, 'player1': p1, 'player2': p2, 'winner': winner})
        rest = rest[-1:] + rest[:-1]
    # A bye, a double loss and the same match listed twice (inverted): excluded or counted once.
    result.append({'phase': 1, 'round': rounds + 1, 'table': 1, 'player1': names[3], 'player2': '', 'winner': names[3]})
    result.append({'phase': 1, 'round': rounds + 1, 'table': 2, 'player1': names[1], 'player2': names[9], 'winner': -1})
    # A mirror (two A players): one win and one loss for the same archetype, kept out of its rate.
    result.append({'phase': 1, 'round': rounds + 1, 'table': 3, 'player1': names[2], 'player2': names[5], 'winner': names[2]})
    first = result[0]
    result.append({**first, 'player1': first['player2'], 'player2': first['player1']})
    return result


def tournament(tid, date, mode, players, pairings):
    return {
        'brief': {'id': tid, 'game': 'PTCG', 'format': 'STANDARD', 'name': f'Invented {tid}', 'date': date, 'players': len(players)},
        'details': {'id': tid, 'game': 'PTCG', 'format': 'STANDARD', 'name': f'Invented {tid}', 'date': date,
                    'players': len(players), 'platform': 'PTCGL', 'decklists': True, 'isPublic': True, 'isOnline': True,
                    'phases': [{'phase': 1, 'type': 'SWISS', 'rounds': 6, 'mode': mode}], 'bannedCards': [], 'specialRules': []},
        'standings': [{'player': p, 'name': 'PRIVATE-' + p, 'country': 'CA', 'placing': i + 1,
                       'record': {'wins': 0, 'losses': 0, 'ties': 0},
                       'deck': ({'id': kind[0], 'name': kind[1]} if kind else None)} for i, (p, kind) in enumerate(players)],
        'pairings': pairings}


PLAYERS = roster()
BO1 = tournament('t-bo1', '2026-11-01T18:00:00.000Z', 'BO1', PLAYERS, round_robin_pairings(PLAYERS))
SMALL = [('q1', A), ('q2', G), ('q3', A), ('q4', D)]
BO3 = tournament('t-bo3', '2026-11-03T18:00:00.000Z', 'BO3', SMALL, [
    {'phase': 1, 'round': 1, 'match': 'm1', 'player1': 'q1', 'player2': 'q2', 'winner': 'q2'},
    {'phase': 1, 'round': 1, 'match': 'm2', 'player1': 'q3', 'player2': 'q4', 'winner': 'q3'}])
OLD = tournament('t-old', '2026-08-01T18:00:00.000Z', 'BO1', SMALL, [
    {'phase': 1, 'round': 1, 'match': 'o1', 'player1': 'q1', 'player2': 'q2', 'winner': 'q1'}])


def oracle(event, archetype_id):
    """Wins/losses/ties of one archetype by opponent, from the raw invented pairings."""
    kind = {s['player']: (s['deck']['id'] if s['deck'] else None) for s in event['standings']}
    seen, totals, mirror = {}, {}, 0
    for row in event['pairings']:
        if not row['player2'] or row['winner'] in (-1, '-1'):
            continue
        key = (row['round'], row.get('table'), row.get('match'), tuple(sorted((row['player1'], row['player2']))))
        seen[key] = row  # the later listing of one match replaces the earlier one
    for row in seen.values():
        a1, a2 = kind[row['player1']], kind[row['player2']]
        if a1 is None or a2 is None or archetype_id not in (a1, a2):
            continue
        if a1 == a2:
            mirror += 1
            continue
        mine, opponent = (row['player1'], a2) if a1 == archetype_id else (row['player2'], a1)
        entry = totals.setdefault(opponent, [0, 0, 0])
        entry[0 if row['winner'] == mine else 2 if row['winner'] in (0, '0') else 1] += 1
    return totals, mirror


class _Response:
    def __init__(self, url, payload):
        self.url, self.body = url, io.BytesIO(json.dumps(payload).encode())
        self.headers = {'Content-Type': 'application/json', 'X-RateLimit-Remaining': '50'}

    def geturl(self):
        return self.url

    def read(self, size):
        return self.body.read(size)

    def close(self):
        pass


class Server:
    """Invented Limitless Tournament Platform. Records every URL that would have left the PC."""

    def __init__(self, listing, failure=None):
        self.listing, self.failure, self.urls = listing, failure, []
        self.events = {e['brief']['id']: e for e in (BO1, BO3, OLD)}

    def open(self, request, timeout):
        url = request.full_url
        self.urls.append(url)
        if self.failure == 'offline':
            raise URLError('invented offline network')
        if self.failure == '429':
            raise HTTPError(url, 429, 'Too Many Requests', {'Retry-After': '0'}, None)
        path = urlsplit(url).path.removeprefix('/api')
        if self.failure == 'json':
            response = _Response(url, {})
            response.body = io.BytesIO(b'{"broken"')
            return response
        if path == '/games':
            payload = [{'id': 'PTCG', 'name': 'Pokémon TCG', 'formats': {'STANDARD': 'Standard'},
                        'platforms': {'PTCGL': 'Pokémon TCG Live'}, 'metagame': True}]
        elif path == '/tournaments':
            assert parse_qs(urlsplit(url).query)['format'] == ['STANDARD']
            payload = [self.events[t]['brief'] for t in self.listing]
        else:
            _, _, tid, endpoint = path.split('/')
            payload = self.events[tid][endpoint]
        return _Response(url, payload)


@pytest.fixture
def server(monkeypatch):
    """The real LimitlessApiClient, with the invented server as its opener and no waiting between GETs."""
    holder = {}

    class Client(meta.LimitlessApiClient):
        def __init__(self, max_requests, **options):
            options.update(opener=holder['server'], interval=0, sleep=lambda seconds: None)
            super().__init__(max_requests, **options)
    monkeypatch.setattr(public_campaign, 'LimitlessApiClient', Client)

    def install(listing, failure=None):
        holder['server'] = Server(listing, failure)
        return holder['server']
    return install


def pokemon(*cards):
    return [{'name': name, 'quantity': quantity, 'english': english} for name, quantity, english in cards]


def selector_row(name, label=None):
    return {'label': label or name, 'kind': 'Référence personnelle', 'selector': name,
            'export': f'Pokémon: 4\n4 {name} INV 1\nTrainer: 48\n48 Invented Tool INV 2\nEnergy: 8\n8 Basic Invented Energy INV 3'}


def test_013_selector_public_bo1_order_oracle_shared_sample_and_unknowns(local_tmp, server, monkeypatch):
    from pokemind.desktop.services import Services
    web = server(['t-bo1', 't-bo3'])
    stats.refresh(local_tmp, as_of=AS_OF)
    requests = list(web.urls)
    rows = [selector_row('Lonelytech', 'Unknown'), selector_row('Gammaroo'), selector_row('Alphamon'),
            {'label': 'Owner secret name', 'selector': 'private', 'kind': 'Référence personnelle', 'export': PRIVATE_DECK}]
    calls, merged = [], []
    snapshots, merge = stats._snapshots, stats._merge_matchups
    monkeypatch.setattr(stats, '_snapshots', lambda *a: (calls.append(1), snapshots(*a))[1])
    monkeypatch.setattr(stats, '_merge_matchups', lambda *a: (merged.append(a[1]), merge(*a))[1])
    result = Services(local_tmp).rank_decks(rows, as_of=AS_OF)
    expected = {}
    for archetype in (A, G, X):
        values, _ = oracle(BO1, archetype[0])
        n = sum(sum(v) for v in values.values())
        expected[archetype[0]] = (sum(v[0] for v in values.values()) / n, n) if n >= 20 else (None, 0)
    for row in result:
        ranking = row['public_ranking']
        assert ranking['mode'] == 'BO1' and ranking['source_url'] == stats.SOURCE_URL
        assert ranking['window'] == {'since': '2026-10-11', 'until': AS_OF}
        if ranking['identity']['status'] == 'IDENTIFIED':
            fraction, n = expected[ranking['identity']['archetype_id']]
            assert ranking['fraction'] == pytest.approx(fraction) if fraction is not None else ranking['fraction'] is None
            assert ranking['n'] == n
    rates = [r['public_ranking']['fraction'] for r in result if r['public_ranking']['fraction'] is not None]
    assert rates == sorted(rates, reverse=True)
    assert result[-1]['label'] == 'Unknown' or result[-1]['public_ranking']['fraction'] is None
    assert calls == [1] and len(merged) == len(set(merged)) and web.urls == requests
    # The name of a private deck never helps attribution or goes to a provider.
    assert not any('secret' in url or 'Owner' in url for url in web.urls)


def test_013_selector_bo3_only_even_with_twenty_matches_never_compared_to_bo1(local_tmp, server):
    from copy import deepcopy
    from pokemind.desktop.services import Services
    web = server(['t-bo3'])
    event = deepcopy(BO3)
    event['pairings'] = [{'phase': 1, 'round': i + 1, 'match': f'b{i}', 'player1': 'q1',
                         'player2': 'q2', 'winner': 'q1'} for i in range(20)]
    web.events['t-bo3'] = event
    stats.refresh(local_tmp, as_of=AS_OF)
    view = stats.public_view(local_tmp, as_of=AS_OF, pokemon=DECK_A)
    assert view['archetype']['modes']['BO3']['n'] == 20
    assert view['archetype']['modes']['BO3']['win_fraction'] == 1
    assert Services(local_tmp).rank_decks([{'export': PRIVATE_DECK, 'label': 'Invented', 'kind': 'Référence personnelle'}],
        as_of=AS_OF)[0]['public_ranking']['fraction'] is None


@pytest.mark.parametrize('n_decks', [5, 50, 500])
def test_013_selector_cost_one_sample_and_one_resolution_per_pokemon_list(local_tmp, server, monkeypatch, n_decks):
    from pokemind.desktop.services import Services
    server(['t-bo1'])
    stats.refresh(local_tmp, as_of=AS_OF)
    services = Services(local_tmp)
    resolves, reads = [], []
    original, snapshots = services.deck_pokemon, stats._snapshots
    monkeypatch.setattr(services, 'deck_pokemon', lambda text: (resolves.append(1), original(text))[1])
    monkeypatch.setattr(stats, '_snapshots', lambda *a: (reads.append(1), snapshots(*a))[1])
    result = services.rank_decks([selector_row('Gammaroo', f'Invented {i}') for i in range(n_decks)], as_of=AS_OF)
    assert len(result) == n_decks and resolves == [1] and reads == [1]
    assert [r['label'] for r in result] == [f'Invented {i}' for i in range(n_decks)]  # stable ties


def test_013_selector_empty_stale_and_invalid_cache_no_rate(local_tmp, server):
    from pokemind.desktop.services import Services
    row = selector_row('Gammaroo')
    services = Services(local_tmp)
    assert services.rank_decks([row], as_of=AS_OF)[0]['public_ranking']['fraction'] is None
    server(['t-old'])
    stats.refresh(local_tmp, as_of=AS_OF)
    assert services.rank_decks([row], as_of=AS_OF)[0]['public_ranking']['fraction'] is None
    for path in stats._snapshot_paths(local_tmp):
        path.write_bytes(b'invented invalid sqlite')
    assert services.rank_decks([row], as_of=AS_OF)[0]['public_ranking']['fraction'] is None


def test_013_future_tournament_snapshot_never_claims_a_current_rate(local_tmp, server):
    from copy import deepcopy
    from pokemind.desktop.services import Services
    web = server(['t-bo1'])
    future = deepcopy(BO1)
    future['details']['date'] = '2099-01-01T18:00:00.000Z'
    future['brief']['date'] = future['details']['date']
    web.events['t-bo1'] = future
    stats.refresh(local_tmp, as_of=AS_OF)
    assert Services(local_tmp).rank_decks([selector_row('Gammaroo')], as_of=AS_OF)[0]['public_ranking']['fraction'] is None


DECK_A = pokemon(('Alphamon ex', 3, None), ('Alphalet', 2, None), ('Betadrake', 3, None), ('Gammaroo', 1, None))


def test_identification_uses_the_list_never_the_deck_name_and_refuses_ties():
    assert stats.identify(DECK_A, CATALOG)['archetype_id'] == A[0]          # most specific archetype of the sample
    assert stats.identify(DECK_A, CATALOG)['evidence'] == 'pokemon_in_list'
    # A one-copy tech is not an archetype; a missing partner is not invented.
    assert stats.identify(pokemon(('Gammaroo', 1, None), ('Deltaflare', 4, None)), CATALOG)['status'] == 'UNIDENTIFIED'
    assert stats.identify(pokemon(('Alphamon', 4, None)), CATALOG)['archetype_id'] == X[0]
    ambiguous = stats.identify(pokemon(('Alphamon', 3, None), ('Betadrake', 3, None), ('Gammaroo', 3, None)),
                               CATALOG | {'betadrake-gammaroo': 'Betadrake Gammaroo'})
    assert ambiguous['status'] == 'AMBIGUOUS' and ambiguous['archetype_id'] is None
    assert set(ambiguous['candidates']) == {'Alphamon Betadrake', 'Betadrake Gammaroo'}
    # A French printing matches through the English name of its exact printing (resolved locally).
    assert stats.identify(pokemon(('Alphamonne-ex', 3, 'Alphamon ex'), ('Bétadrac', 2, 'Betadrake')), CATALOG)['archetype_id'] == A[0]
    # A public reference's label is evidence only when its Pokémon are in the list.
    labelled = stats.identify(DECK_A, CATALOG, public_labels=['Alphamon'])
    assert labelled['archetype_id'] == X[0] and labelled['evidence'] == 'public_label_corroborated'
    assert stats.identify(DECK_A, CATALOG, public_labels=['Gammaroo'])['archetype_id'] == A[0]   # 1 copy: not corroborated
    assert stats.identify(DECK_A, {})['reason'] == 'NO_PUBLIC_SAMPLE'


def test_rates_denominators_byes_duplicates_and_mirrors_match_an_independent_oracle(local_tmp, server):
    web = server(['t-bo1'])
    outcome = stats.refresh(local_tmp, as_of=AS_OF)
    assert outcome['status'] == 'SOURCE_SNAPSHOT_SAVED' and outcome['network_used'] and outcome['gets'] == 5
    view = stats.public_view(local_tmp, as_of=AS_OF, pokemon=DECK_A)
    expected, mirror = oracle(BO1, A[0])
    bo1 = view['archetype']['modes']['BO1']
    assert {r['opponent_id']: [r['wins'], r['losses'], r['ties']] for r in bo1['matchups']} == expected
    wins, n = sum(v[0] for v in expected.values()), sum(sum(v) for v in expected.values())
    assert (bo1['wins'], bo1['n'], bo1['mirror_matches']) == (wins, n, mirror) and mirror > 0
    assert bo1['win_fraction'] == pytest.approx(wins / n) and n >= stats.MIN_MATCHES_WINRATE
    low, high = bo1['wilson_95']
    assert low < wins / n < high
    for row in bo1['matchups']:
        assert (row['win_fraction'] is None) == (row['n'] < stats.MIN_MATCHES_MATCHUP)
    # Representation: placements of A over classified placements (22 of 24 players carry a published archetype).
    assert view['meta']['n_placements'] == 24 and view['meta']['n_classified'] == 22
    assert view['archetype']['representation'] == {'BO1': {'population': 'BO1', 'n': 8, 'classified': 22,
                                                           'tournaments': 1, 'share': pytest.approx(8 / 22)}}
    assert view['archetype']['excluded_all_archetypes']['bye_or_automatic_loss'] == 1
    assert view['archetype']['excluded_all_archetypes']['double_loss'] == 1
    assert view['status'] == 'OK' and view['date_range'] == ['2026-11-01', '2026-11-01']
    assert view['population']['platform'] == 'PTCGL' and view['population']['online'] is True
    assert view['last_success_at'] and view['tournaments'][0]['date'] == '2026-11-01'  # retrieval time kept apart
    # Only the documented keyless endpoints left the PC; never the protected /games/{id}/decks.
    paths = [urlsplit(u).path for u in web.urls]
    assert paths == ['/api/games', '/api/tournaments', '/api/tournaments/t-bo1/details',
                     '/api/tournaments/t-bo1/standings', '/api/tournaments/t-bo1/pairings']


def test_one_automatic_attempt_a_day_shared_by_decks_and_a_bounded_manual_refresh(local_tmp, server):
    web = server(['t-bo1'])
    assert stats.refresh_state(local_tmp, as_of=AS_OF)['automatic_due'] is True
    stats.refresh(local_tmp, as_of=AS_OF, now=1000.0)
    sent = len(web.urls)
    for _ in range(3):  # other decks selected the same day: zero network
        assert stats.refresh(local_tmp, as_of=AS_OF, now=1100.0) == {'status': 'CACHE_TODAY', 'network_used': False, 'gets': 0}
        stats.public_view(local_tmp, as_of=AS_OF, pokemon=DECK_A)
    assert len(web.urls) == sent and stats.refresh_state(local_tmp, as_of=AS_OF)['automatic_due'] is False
    too_soon = stats.refresh(local_tmp, as_of=AS_OF, manual=True, now=1100.0)
    assert too_soon['status'] == 'REFRESH_TOO_SOON' and too_soon['retry_after_seconds'] == 500 and len(web.urls) == sent
    web.listing = ['t-bo3', 't-bo1']
    assert stats.refresh(local_tmp, as_of=AS_OF, manual=True, now=2000.0)['status'] == 'SOURCE_SNAPSHOT_SAVED'
    assert stats.refresh(local_tmp, as_of=AS_OF, manual=True, now=3000.0)['status'] == 'SOURCE_SNAPSHOT_SAVED'
    sent = len(web.urls)
    assert stats.refresh(local_tmp, as_of=AS_OF, manual=True, now=9000.0)['status'] == 'REFRESH_DAILY_LIMIT'
    assert len(web.urls) == sent
    # Three snapshots, two of the same tournament t-bo3: counted once; BO1 and BO3 never merged.
    view = stats.public_view(local_tmp, as_of=AS_OF, pokemon=DECK_A)
    assert view['snapshots_used'] == 2 and view['duplicate_snapshots_skipped'] == 1
    assert sorted(view['archetype']['modes']) == ['BO1', 'BO3']
    bo3 = view['archetype']['modes']['BO3']
    assert (bo3['wins'], bo3['losses'], bo3['n'], bo3['win_fraction']) == (1, 1, 2, None)   # n too small: no percentage
    # Representation is never pooled across BO1 and BO3 events either.
    assert sorted(view['populations']) == ['BO1', 'BO3'] and view['meta']['population'] == 'BO1'
    assert (view['meta']['n_placements'], view['populations']['BO3']['n_placements']) == (24, 4)
    assert view['archetype']['representation']['BO3'] == {'population': 'BO3', 'n': 2, 'classified': 4,
                                                          'tournaments': 1, 'share': None}
    assert [t['tournament_id'] for t in view['tournaments']] == ['t-bo1', 't-bo3']
    assert [(h['date'], h['population']) for h in view['archetype']['history']] == [('2026-11-01', 'BO1'), ('2026-11-03', 'BO3')]
    assert view['archetype']['history'][1]['share'] is None          # 4 placements: below the share threshold
    # The next day: one new automatic attempt again.
    assert stats.refresh_state(local_tmp, as_of='2026-11-08', now=9000.0)['automatic_due'] is True


@pytest.mark.parametrize('failure', ['offline', '429', 'json'])
def test_network_failures_keep_the_last_valid_snapshot_and_say_so(local_tmp, server, failure):
    server(['t-bo1'])
    stats.refresh(local_tmp, as_of='2026-11-06', now=1000.0)
    before = stats.public_view(local_tmp, as_of=AS_OF, pokemon=DECK_A)
    web = server(['t-bo1'], failure=failure)
    outcome = stats.refresh(local_tmp, as_of=AS_OF, now=5000.0)
    assert outcome['status'] == 'INSUFFICIENT_OR_BLOCKED_PUBLIC_DATA' and len(web.urls) >= 1
    if failure == '429':
        assert outcome['error'] == 'PUBLIC_SOURCE_HTTP_429_BLOCKED' and len(web.urls) == 1   # stops at the first refusal
    after = stats.public_view(local_tmp, as_of=AS_OF, pokemon=DECK_A)
    assert after['archetype'] == before['archetype'] and after['last_success_at'] == before['last_success_at']
    assert after['refresh']['last_outcome']['status'] == 'INSUFFICIENT_OR_BLOCKED_PUBLIC_DATA'
    assert after['refresh']['automatic_due'] is False                    # no retry loop the same day
    sent = len(web.urls)
    stats.refresh(local_tmp, as_of=AS_OF, now=5100.0)
    assert len(web.urls) == sent


def test_no_snapshot_no_match_old_tournaments_and_unidentified_decks_show_no_rate(local_tmp, server):
    empty = stats.public_view(local_tmp, as_of=AS_OF, pokemon=DECK_A)
    assert empty['status'] == 'NO_SNAPSHOT' and empty['archetype'] is None and empty['meta']['archetypes'] == []
    server(['t-old'])
    assert stats.refresh(local_tmp, as_of=AS_OF)['status'] == 'SOURCE_SNAPSHOT_SAVED'
    old = stats.public_view(local_tmp, as_of=AS_OF, pokemon=DECK_A)
    assert old['status'] == 'NO_SNAPSHOT' and old['tournaments'] == []              # outside the 28-day window
    unknown = stats.public_view(local_tmp, as_of='2026-08-02', pokemon=pokemon(('Zetaunknown', 4, None)))
    assert unknown['status'] == 'ARCHETYPE_UNIDENTIFIED' and unknown['archetype'] is None
    assert unknown['meta']['n_classified'] == 4 and unknown['meta']['archetypes'][0]['share'] is None  # n < 20


def test_the_collector_receives_no_deck_and_cancellation_is_honoured(local_tmp, server):
    web = server(['t-bo1'])
    outcome = stats.refresh(local_tmp, as_of=AS_OF, cancelled=lambda: True)
    assert outcome['status'] == 'INTERRUPTED' and web.urls == []
    view = stats.public_view(local_tmp, as_of=AS_OF, pokemon=DECK_A)
    assert view['status'] == 'NO_SNAPSHOT' and view['refresh']['automatic_due'] is False
    assert stats.refresh(local_tmp, as_of=AS_OF)['status'] == 'CACHE_TODAY'
    stored = ''.join(p.read_text(encoding='utf-8', errors='ignore') for p in local_tmp.rglob('*.json'))
    assert 'Alphamon' not in stored and 'PRIVATE-' not in stored


def test_services_attribute_public_figures_by_list_never_by_the_owner_deck_name(local_tmp, server):
    from pokemind.desktop.services import Services
    web = server(['t-bo1'])
    services = Services(local_tmp)
    mine = {'label': PRIVATE_NAME, 'selector': 'mon deck', 'export': PRIVATE_DECK, 'source': {},
            'kind': 'Mon deck · référence personnelle entrée par moi', 'legality': 'inconnue', 'total': 60}
    first = services.deck_public_stats(mine, refresh='auto', as_of=AS_OF)
    assert first['identity']['archetype_id'] == A[0] and first['refresh_outcome']['status'] == 'SOURCE_SNAPSHOT_SAVED'
    for url in web.urls:  # neither the deck name nor a card of the private list left the PC
        assert not any(word in url for word in ('Gammaroo', 'Alphamon', 'Betadrake', 'secret', 'INV'))
    other = {**mine, 'label': 'Alphamon', 'export': PRIVATE_DECK.replace('3 Betadrake INV 3', '3 Alphamon ex INV 9')}
    second = services.deck_public_stats(other, refresh='auto', as_of=AS_OF)
    assert second['refresh_outcome']['status'] == 'CACHE_TODAY' and second['identity']['archetype_id'] == X[0]
    assert first['deck_key'] != second['deck_key']
    public = {'label': 'Alphamon', 'selector': '1:1', 'export': PRIVATE_DECK, 'source': {'urls': []},
              'kind': 'Bibliothèque PUBLIC · 1 placements observés', 'legality': 'inconnue', 'total': 60}
    labelled = services.deck_public_stats(public, as_of=AS_OF)
    assert labelled['identity']['evidence'] == 'public_label_corroborated' and labelled['identity']['archetype_id'] == X[0]


def test_projection_keeps_n_source_dates_and_both_languages(local_tmp, server):
    from pokemind.desktop.insights import project_public_stats
    from pokemind.desktop.locale_text import set_current_language, display
    server(['t-bo1'])
    stats.refresh(local_tmp, as_of=AS_OF)
    view = stats.public_view(local_tmp, as_of=AS_OF, pokemon=DECK_A)
    try:
        model = project_public_stats(view)
        text = display(model['summary']) + display(model['source']) + display(model['identity'])
        assert 'Alphamon Betadrake' in text and 'pas de tes 60 cartes exactes' in text
        assert 'n=' + str(view['archetype']['modes']['BO1']['n']) in text and 'IC 95 %' in text
        assert 'Représentation (tournois BO1) : 36 % (8 / 22 placements classifiés, 1 tournoi(s))' in text
        assert '1er novembre 2026 → 1er novembre 2026' in text and 'pas date des matchs' in text  # one date format (D-317) and 'docs.limitlesstcg.com' in text
        assert len(model['matchup_rows']) == len(view['archetype']['modes']['BO1']['matchups'])
        set_current_language('en')
        english = display(project_public_stats(view)['summary']) + display(project_public_stats(view)['identity'])
        assert 'Win rate BO1' in english and 'not your exact 60 cards' in english and '95% CI' in english
        unknown = project_public_stats(stats.public_view(local_tmp, as_of=AS_OF, pokemon=pokemon(('Zeta', 4, None))))
        assert unknown['matchup_rows'] == [] and 'No rate attributed' in display(unknown['identity'])
    finally:
        set_current_language('fr')
