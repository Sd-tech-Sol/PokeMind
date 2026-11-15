"""013: invented public lists and games only; real parser/publisher/Services, no model or HTTP."""
from copy import deepcopy
from datetime import date
from concurrent.futures import ThreadPoolExecutor
import json
import os
import threading

import pytest

from pokemind import battle_batch, competitive, opponent_observer as observer, rules
from pokemind.desktop import ingestion
from pokemind.desktop.services import MY_DECKS, Services
from test_desktop_ingestion import legacy  # noqa: F401 (synthetic schema7 pytest fixture)

DAY = date.today().isoformat()
POKEMON = ['Alphamon ex', 'Alphalet', 'Betadrake ex', 'Betalet']
TRAINERS = ['Invented Tool ' + chr(65 + i) for i in range(11)]
ENERGY = ['Basic Invented Fire Energy', 'Basic Invented Water Energy']
NAMES = POKEMON + TRAINERS + ENERGY
EXPORT = ('Pokémon: 10\n' + '\n'.join(f'{n} {name} INV {i+1}' for i, (n, name) in
    enumerate(zip([3, 3, 2, 2], POKEMON))) + '\nTrainer: 42\n' +
    '\n'.join(f'{4 if i < 10 else 2} {name} INV {i+10}' for i, name in enumerate(TRAINERS)) +
    '\nEnergy: 8\n4 Basic Invented Fire Energy INV 30\n4 Basic Invented Water Energy INV 31\n')


def public_index(export=EXPORT):
    cards = list(competitive._card_map(export).values())
    ref = {'archetype': 'Alphamon Betadrake', 'selector': 'invented:1', 'export': export,
           'total_cards': 60, 'names': [rules._normalized_name(n) for n in POKEMON],
           'cards': cards, 'composition': {'date_range': [DAY, DAY],
           'source_urls': ['https://www.limitlesstcg.com/decks/list/999999'],
           'composition_id': competitive._composition_id(competitive._card_map(export))}}
    return {'references': [ref], 'primary_names_by_family': {'Alphamon Betadrake': ['alphamon ex']},
            'pokemon_names': {rules._normalized_name(n): rules._normalized_name(n) for n in POKEMON},
            'as_of': DAY}


def match(names=NAMES[:6], outcome='losses', prizes=None):
    return {'match': 'synthetic-old-selected', 'outcome': outcome, 'max_observed_turn': 8,
            'explicit_prize_totals': prizes or {'self': None, 'opponent': None},
            'opponent_cards': [{'name': n, 'normalized_name': rules._normalized_name(n), 'occurrences': 2,
                                'minimum_quantity': 1} for n in names]}


@pytest.fixture
def cached(monkeypatch):
    index = public_index()
    monkeypatch.setattr(battle_batch, 'public_context', lambda *args: (deepcopy(index), [], {'status': 'AVAILABLE_SOURCE_CHECKED'}))
    return index


def files(root):
    return list((root / MY_DECKS).glob('deck-*.json'))


def test_013_explicit_selected_opponent_is_not_a_counter_deck_request():
    for question in ('Crée le deck adverse', 'Ajoute le deck de cette partie', 'Reconstruis le deck de l’adversaire',
                     'Save the opponent deck', 'Reconstruct the opponent deck'):
        assert Services.opponent_save_request(question)
    for question in ('Crée un deck pour battre cet adversaire', 'Construis un deck pour ce matchup',
                     'Propose un deck contre lui', 'Pourquoi ai-je perdu?', 'Ne reconstruis pas le deck adverse',
                     'Do not save the opponent deck', 'Pourquoi créer le deck adverse?', 'Comment reconstruire le deck adverse?'):
        assert not Services.opponent_save_request(question)


def test_013_local_threshold_17_names_and_printing_caveat():
    game = match()
    game['opponent_cards'][0].update(set_code='OTHER', collector_number='99')
    result = observer.conditional_public_deck(game, public_index(), as_of=DAY)
    assert result['status'] == 'ELIGIBLE'
    assert result['candidate']['unknowns'] == [{'name': 'Alphamon ex', 'reason': 'printing_equivalence_unproven'}]
    result = observer.conditional_public_deck(match(NAMES), public_index(), as_of=DAY)
    assert result['evidence']['distinct_observed'] == 17 and result['candidate']['total_cards'] == 60
    assert result['candidate']['probability'] is None and not result['candidate']['is_exact_opponent_deck']


@pytest.mark.parametrize('change,reason', [
    ({'opponent_cards': match(NAMES[:3])['opponent_cards']}, 'INSUFFICIENT_EVIDENCE'),
    ({'max_observed_turn': 2}, 'INSUFFICIENT_EVIDENCE'),
    ({'opponent_cards': match(TRAINERS)['opponent_cards']}, 'INSUFFICIENT_EVIDENCE'),
    ({'outcome': 'unknown'}, 'OUTCOME_NOT_ELIGIBLE'),
    ({'outcome': 'tie'}, 'OUTCOME_NOT_ELIGIBLE'),
    ({'outcome': 'wins'}, 'OUTCOME_NOT_ELIGIBLE'),
    ({'outcome': 'wins', 'explicit_prize_totals': {'self': 6, 'opponent': 2}}, 'OUTCOME_NOT_ELIGIBLE'),
    ({'outcome': 'wins', 'explicit_prize_totals': {'self': None, 'opponent': 5}}, 'OUTCOME_NOT_ELIGIBLE'),
    ({'outcome': 'wins', 'explicit_prize_totals': {'self': 1, 'opponent': 0}}, 'OUTCOME_NOT_ELIGIBLE'),
])
def test_013_fail_closed_early_generic_unknown_or_non_close(change, reason):
    assert observer.conditional_public_deck(match() | change, public_index(), as_of=DAY)['reason'] == reason


def test_013_missing_stale_invalid_ambiguous_reference():
    for index in (None, {'references': []}):
        assert observer.conditional_public_deck(match(), index, as_of=DAY)['reason'] == 'PUBLIC_REFERENCE_UNAVAILABLE'
    for changes in ({'date_range': ['2000-01-01']}, {'date_range': ['2999-01-01']},
                    {'source_urls': ['https://private.invalid/list']}, {'source_urls': []}):
        index = public_index()
        index['references'][0]['composition'].update(changes)
        assert observer.conditional_public_deck(match(), index, as_of=DAY)['reason'] == 'PUBLIC_REFERENCE_UNAVAILABLE'
    index = public_index()
    variant = deepcopy(index['references'][0])
    variant['export'] = EXPORT.replace(TRAINERS[-1], 'Unseen Alternative Tool')
    variant['cards'] = list(competitive._card_map(variant['export']).values())
    index['references'].append(variant)
    assert observer.conditional_public_deck(match(), index, as_of=DAY)['reason'] == 'AMBIGUOUS_PUBLIC_REFERENCE'
    # Two observed names separate these variants; deterministic, no percentage of certainty.
    variant['export'] = EXPORT.replace(TRAINERS[0], 'Other Tool One').replace(TRAINERS[1], 'Other Tool Two')
    variant['cards'] = list(competitive._card_map(variant['export']).values())
    assert observer.conditional_public_deck(match(), index, as_of=DAY)['status'] == 'ELIGIBLE'


def test_013_saved_once_metadata_no_player_or_raw_log_and_prepare_is_readonly(local_tmp, cached):
    services = Services(local_tmp)
    receipt = services.save_public_opponent(match())
    assert receipt['status'] == 'SAVED_DECK' and len(files(local_tmp)) == 1
    assert services.saved_deck is None  # cannot appear as an LLM save in a later unrelated turn
    record = json.loads(files(local_tmp)[0].read_text(encoding='utf-8'))
    assert record['source'] == 'opponent_auto' and record['reconstruction']['hypothesis']
    assert record['reconstruction']['evidence']['distinct_observed'] == 6
    assert 'raw' not in json.dumps(record) and 'synthetic-old-selected' not in json.dumps(record)
    assert services.save_public_opponent(match())['status'] == 'ALREADY_SAVED'
    cached['references'][0]['export'] = EXPORT.replace(TRAINERS[-1], 'Unseen Variant Tool')
    cached['references'][0]['cards'] = list(competitive._card_map(cached['references'][0]['export']).values())
    assert Services(local_tmp).save_public_opponent(match())['status'] == 'ALREADY_SAVED'
    assert len(files(local_tmp)) == 1
    services.prepare_question('Explique ce deck', 'public', log_followup=True)
    assert len(files(local_tmp)) == 1
    assert services.tool_call({'operation': 'save_deck', 'query': 'LLM arbitrary', 'export_text': EXPORT},
                             'aggregates')['error'] == 'DECK_SAVE_REQUIRES_OWNER_REQUEST'
    assert 'reconstruction' not in json.dumps(services.context('decks', 'public'))


@pytest.mark.parametrize('source', ['owner', 'coach'])
def test_013_existing_owner_or_legacy_family_never_overwritten(local_tmp, cached, source):
    services = Services(local_tmp)
    variant = EXPORT.replace(TRAINERS[-1], 'Previously Entered Tool')
    assert services.save_deck('Unchanged previous name', variant, source)['status'] == 'SAVED_DECK'
    before = {f.name: f.read_bytes() for f in files(local_tmp)}
    assert services.save_public_opponent(match())['status'] == 'ALREADY_SAVED'
    assert before == {f.name: f.read_bytes() for f in files(local_tmp)}


def test_013_normalized_composition_ignores_order_and_whitespace():
    reordered = EXPORT.replace('Alphamon ex', 'ALPHAMON   ex').replace('3 ALPHAMON   ex INV 1\n3 Alphalet INV 2',
        '3 Alphalet INV 2\n3 ALPHAMON   ex INV 1')
    assert observer.composition_key(EXPORT) == observer.composition_key(reordered)
    assert observer.composition_key(EXPORT) != observer.composition_key(EXPORT.replace('INV 1\n', 'INV 99\n'))


def test_013_legacy_registered_deck_is_checked_readonly_before_auto_add(local_tmp, legacy, cached, monkeypatch):
    db, before = legacy
    read = []
    def registered(root, path, preflight, as_of, **kwargs):
        read.append((path == db, preflight['integrity'], kwargs['all_versions']))
        return [{'export': EXPORT.replace(TRAINERS[-1], 'Legacy Variant Tool')}]
    monkeypatch.setattr(battle_batch, 'registered_decks', registered)
    assert Services(local_tmp).save_public_opponent(match())['status'] == 'ALREADY_SAVED'
    assert read == [(True, 'ok', True)] and db.read_bytes() == before and not files(local_tmp)


def test_013_close_win_and_no_model_or_network(local_tmp, cached, monkeypatch):
    from pokemind import deck_public_stats, batch_public_research
    def forbidden(*args, **kwargs):
        pytest.fail('No collector/cloud may be called by the local engine')
    monkeypatch.setattr(deck_public_stats, 'refresh', forbidden)
    monkeypatch.setattr(batch_public_research, 'research', forbidden)
    monkeypatch.setattr(batch_public_research, 'research_matchups', forbidden)
    services = Services(local_tmp)
    assert services.save_public_opponent(match(outcome='wins'))['status'] == 'SKIPPED'
    assert not files(local_tmp)
    assert services.save_public_opponent(match(outcome='wins', prizes={'self': 6, 'opponent': 5}))['status'] == 'SAVED_DECK'


def test_013_concurrent_calls_publish_one_complete_deck(local_tmp, cached):
    barrier = threading.Barrier(2)
    def run(_):
        barrier.wait(timeout=5)
        return Services(local_tmp).save_public_opponent(match())['status']
    with ThreadPoolExecutor(2) as pool:
        assert sorted(pool.map(run, range(2))) == ['ALREADY_SAVED', 'SAVED_DECK']
    assert len(files(local_tmp)) == 1 and json.loads(files(local_tmp)[0].read_text(encoding='utf-8'))['export'] == EXPORT


def test_013_cancel_before_commit_or_partial_publication_has_no_saved_file(local_tmp, cached, monkeypatch):
    cancelled = threading.Event()
    real = os.fsync
    def cancel(fd):
        real(fd)
        cancelled.set()
    monkeypatch.setattr(os, 'fsync', cancel)
    assert Services(local_tmp).save_public_opponent(match(), cancelled=cancelled.is_set)['reason'] == 'CANCELLED'
    assert not files(local_tmp)


def test_013_exclusive_atomic_publish_does_not_overwrite(local_tmp, cached, monkeypatch):
    def collision(source, destination):
        destination.write_bytes(b'preserved concurrent file')
        raise FileExistsError('invented collision')
    monkeypatch.setattr(os, 'link', collision)
    receipt = Services(local_tmp).save_public_opponent(match())
    assert receipt['status'] == 'SKIPPED' and receipt.get('status') != 'SAVED_DECK'
    assert files(local_tmp)[0].read_bytes() == b'preserved concurrent file'


@pytest.mark.parametrize('outcome', ['permission', 'collision', 'cancelled', 'success'])
def test_014_only_owned_staging_is_removed_on_failure_cancel_or_success(local_tmp, cached, monkeypatch, outcome):
    pending = local_tmp / MY_DECKS / '.pending'
    pending.mkdir(parents=True)
    historical = pending / 'historical.tmp'
    historical.write_bytes(b'preserve historical staging')
    unrelated = pending / 'other-attempt.tmp'
    unrelated.write_bytes(b'preserve another attempt')
    if outcome in {'permission', 'collision'}:
        def fail(source, target):
            if outcome == 'collision':
                target.write_bytes(b'preserve existing destination')
                raise FileExistsError('synthetic concurrent destination')
            raise PermissionError(13, 'synthetic access denied')
        monkeypatch.setattr(os, 'link', fail)
    stopped = threading.Event()
    if outcome == 'cancelled':
        fsync = os.fsync
        def cancel(fd):
            fsync(fd)
            stopped.set()
        monkeypatch.setattr(os, 'fsync', cancel)
    receipt = Services(local_tmp).save_public_opponent(match(), cancelled=stopped.is_set)
    assert receipt['status'] == ('SAVED_DECK' if outcome == 'success' else 'SKIPPED')
    assert sorted(p.name for p in pending.iterdir()) == ['historical.tmp', 'other-attempt.tmp']
    assert historical.read_bytes() == b'preserve historical staging'
    assert unrelated.read_bytes() == b'preserve another attempt'
    if outcome == 'collision':
        assert files(local_tmp)[0].read_bytes() == b'preserve existing destination'
    elif outcome != 'success':
        assert not files(local_tmp)


def test_014_staging_name_collision_preserves_the_file_this_attempt_did_not_create(local_tmp, cached, monkeypatch):
    from types import SimpleNamespace
    from pokemind.desktop import services
    pending = local_tmp / MY_DECKS / '.pending'
    pending.mkdir(parents=True)
    name = 'a' * 32
    previous = pending / (name + '.tmp')
    previous.write_bytes(b'existing unrelated staging')
    monkeypatch.setattr(services.uuid, 'uuid4', lambda: SimpleNamespace(hex=name))
    assert Services(local_tmp).save_public_opponent(match())['status'] == 'SKIPPED'
    assert previous.read_bytes() == b'existing unrelated staging'
    assert list(pending.iterdir()) == [previous] and not files(local_tmp)


def full_log():
    return ("Reference player: InventedSelf\nTurn # 1 - InventedSelf's Turn\nInventedSelf played Invented Own Pokemon.\n"
            "Turn # 2 - InventedRival's Turn\n" + ''.join(f'InventedRival played {n}.\n' for n in NAMES[:6]) +
            "Turn # 3 - InventedSelf's Turn\nInventedSelf played Invented Own Tool.\n"
            "Turn # 4 - InventedRival's Turn\nInventedRival played Alphamon ex.\nInventedRival played Alphalet.\nInventedRival wins.\n")


def test_013_real_ingestion_unique_duplicate_refused_and_pending(local_tmp, cached, monkeypatch):
    # This fixture supplies a checked in-memory reference, no catalog databases for counter-deck plans.
    # Keep the real parser/analysis/persistence and disable only those unrelated recommendation plans.
    analyze = battle_batch.batch_analyze
    monkeypatch.setattr(battle_batch, 'batch_analyze', lambda *a, **k: analyze(*a, **k, recommendations=False))
    first = ingestion.ingest(local_tmp, full_log())
    assert first['new_unique'] == 1 and first['opponent_deck']['status'] == 'SAVED_DECK'
    again = ingestion.ingest(local_tmp, full_log())
    assert again['status'] == 'DUPLICATE' and again['opponent_deck'] is None
    assert ingestion.ingest(local_tmp, full_log().replace('InventedRival wins.', ''))['status'] == 'REFUSED'
    other = ingestion.ingest(local_tmp, full_log().replace('Invented Own Tool', 'Different Invented Own Tool'))
    assert other['opponent_deck']['status'] == 'ALREADY_SAVED' and len(files(local_tmp)) == 1
    monkeypatch.setattr(ingestion, 'refresh', lambda *a, **k: (_ for _ in ()).throw(ValueError('synthetic partial')))
    pending = ingestion.ingest(local_tmp, full_log().replace('Invented Own Tool', 'Third Invented Own Tool'))
    assert pending['status'] == 'SAVED_REFRESH_PENDING' and len(files(local_tmp)) == 1


def test_013_rechecked_public_cache_not_an_unverified_export(local_tmp):
    import hashlib
    from pokemind import deck_library
    from test_competitive_advisor import deck_page, EVENT_URL, AS_OF
    target = competitive.create_workspace(local_tmp, 'auto-opponent-invented')
    db = target / 'public.sqlite3'
    url = 'https://www.limitlesstcg.com/decks/list/999999'
    body = ('<div class="infobox-heading">Synthetic Regional</div>'
            '<div class="infobox-line">10th October 2026 • 20 Players</div>'
            '<a href="/decks/?time=all&amp;format=SYN">Synthetic range</a><table>'
            '<tr data-rank="1" data-deck="Alphamon Betadrake" data-name="PRIVATE-NOT-STORED">'
            '<td><a href="/decks/list/999999">List</a></td></tr></table>').encode()
    listing = (b'<tr><td>10 Oct 26</td><td>XX</td><td><a href="/tournaments/123">Synthetic Regional</a></td>'
               b'<td><img alt="standard"></td><td>20</td><td>PRIVATE-NOT-STORED</td></tr>')
    event = competitive.qualify_standard(competitive.parse_event(body, EVENT_URL, as_of=AS_OF), listing)
    payloads = {competitive.INDEX_URL: listing, EVENT_URL: body,
                url: deck_page(competitive.parse_deck_export(EXPORT).cards)}
    ledger = []
    for address, payload in payloads.items():
        sha = hashlib.sha256(payload).hexdigest()
        (target / 'pages' / (sha + '.body')).write_bytes(payload)
        ledger.append({'url': address, 'sha256': sha, 'state': 'complete', 'http_status': 200,
                       'fetched_at': AS_OF + 'T18:00:00Z', 'bytes': len(payload)})
    (target / 'requests.json').write_text(json.dumps({'requests': ledger, 'gets': 3,
        'bytes': sum(r['bytes'] for r in ledger), 'stopped': 'COMPLETED_BATCH_NO_RESTART'}), encoding='utf-8')
    row = event['placements'][0] | {'page_sha256': ledger[-1]['sha256'],
        'fetched_at': ledger[-1]['fetched_at'], 'deck_text': competitive.parse_list(payloads[url])}
    competitive.store_event(local_tmp, db, event, [row])
    index = deck_library.reference_index(local_tmp, db, as_of=AS_OF)
    assert len(index['references']) == 1
    # This fixture's public Pokémon names/categories are explicit; production adds verified catalog aliases.
    index.update(primary_names_by_family={'Alphamon Betadrake': ['alphamon ex']},
                 pokemon_names=public_index()['pokemon_names'])
    assert observer.conditional_public_deck(match(), index, as_of=AS_OF)['status'] == 'ELIGIBLE'
    (target / 'pages' / (ledger[-1]['sha256'] + '.body')).write_bytes(b'invented tampered list')
    damaged = deck_library.reference_index(local_tmp, db, as_of=AS_OF)
    assert not damaged['references']  # original engine rejects a mismatched archived source body
    assert observer.conditional_public_deck(match(), damaged, as_of=AS_OF)['reason'] == 'PUBLIC_REFERENCE_UNAVAILABLE'
