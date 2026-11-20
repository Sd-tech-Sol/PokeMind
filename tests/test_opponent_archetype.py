"""Probable opponent archetype (pipeline 023, phase 6) on invented TCG Live-format logs, archetypes and names."""
from __future__ import annotations

import copy

from pokemind import battle_batch, battle_logs, opponent_archetype as oa, opponent_observer
from pokemind.desktop.insights import opponent_name, opponent_words, probable_tip
from pokemind.desktop.locale_text import display

KNOWN = oa.signatures(['Synthwing Rex', 'Voltcrest', 'Mirefang', 'Voltcrest Mirefang', 'Synthwing Mirefang ex',
                       'Synthwing Rex'])
ALIASES = {  # the catalogue: printed names (any language) of invented Pokémon to their English name
    'synthwing rex': {'Synthwing Rex'}, 'rexaile': {'Synthwing Rex'}, 'rexling': {'Rexling'},
    'voltcrest': {'Voltcrest'}, 'mirefang': {'Mirefang'}, 'mirefang ex': {'Mirefang ex'},
}


def log(plays, *, language='en'):
    """A TCG Live-format log; `plays` are the opponent's cards in order, the owner plays an invented Trainer."""
    text = 'Reference player: InventedSelf\n' if language == 'en' else 'Joueur de référence : InventedSelf\n'
    for turn, card in enumerate(plays, 1):
        for actor, played in (('InventedSelf', 'Invented Ball'), ('InventedRival', card)):
            if language == 'en':
                text += f"Turn # {turn} - {actor}'s Turn\n{actor} drew a card.\n{actor} played {played}.\n"
            else:
                text += f"Tour {turn} - Tour de {actor}\n{actor} a pioché une carte.\n{actor} a joué {played}.\n"
    return text + 'InventedRival wins.\n'


def observed(plays, **kwargs):
    parsed = battle_logs.parse_battle_log(log(plays, **kwargs), reference_player='InventedSelf')
    return opponent_observer.observe(parsed, as_of='2026-11-18')['observed_partial']['cards']


def test_clear_identification_names_its_cards_and_confidence():
    cards = observed(['Synthwing Rex', 'Rexling', 'Synthwing Rex', 'Invented Rod', 'Synthwing Rex', 'Synthwing Rex'])
    result = oa.identify(cards, KNOWN, ALIASES)
    assert result['label'] == 'Synthwing Rex' and result['confidence'] == 'high'
    assert result['evidence'] == [{'name': 'Synthwing Rex', 'occurrences': 4}]
    assert result['version'] == oa.VERSION
    # Seen twice only: the same archetype, with less confidence.
    fewer = oa.identify(observed(['Synthwing Rex', 'Rexling', 'Invented Rod', 'Synthwing Rex']), KNOWN, ALIASES)
    assert (fewer['label'], fewer['confidence']) == ('Synthwing Rex', 'medium')


def test_a_french_log_goes_through_the_catalogue_names():
    result = oa.identify(observed(['Rexaile', 'Rexling', 'Super Bonbon Inventé', 'Rexaile'], language='fr'),
                         KNOWN, ALIASES)
    assert (result['label'], result['confidence']) == ('Synthwing Rex', 'medium')
    assert result['evidence'][0]['name'] == 'Rexaile'


def test_two_equally_specific_archetypes_stay_unidentified():
    known = oa.signatures(['Voltcrest', 'Mirefang'])
    result = oa.identify(observed(['Mirefang', 'Voltcrest', 'Invented Rod', 'Voltcrest', 'Mirefang']), known, ALIASES)
    assert result['label'] is None and result['confidence'] is None
    assert result['candidates'] == ['Mirefang', 'Voltcrest']
    # A two-word name fully seen is more specific than a one-word one: not a tie.
    rex = oa.identify(observed(['Synthwing Rex', 'Voltcrest', 'Invented Rod', 'Synthwing Rex']), KNOWN, ALIASES)
    assert rex['label'] == 'Synthwing Rex'


def test_too_few_cards_is_never_enough():
    result = oa.identify(observed(['Synthwing Rex', 'Synthwing Rex', 'Synthwing Rex', 'Rexling']), KNOWN, ALIASES)
    assert result['label'] is None and result['reason'] == 'TOO_FEW_CARDS'
    assert oa.identify([], KNOWN, ALIASES)['reason'] == 'TOO_FEW_CARDS'


def test_a_card_shared_by_archetypes_needs_a_card_of_its_own():
    known = oa.signatures(['Voltcrest Mirefang', 'Synthwing Mirefang'])
    shared = oa.identify(observed(['Mirefang', 'Invented Rod', 'Mirefang', 'Invented Ball']), known, ALIASES)
    assert shared['label'] is None and shared['reason'] == 'NO_KNOWN_ARCHETYPE'
    both = oa.identify(observed(['Mirefang', 'Voltcrest', 'Invented Rod', 'Mirefang', 'Voltcrest']), known, ALIASES)
    assert (both['label'], both['confidence']) == ('Voltcrest Mirefang', 'high')
    assert {e['name'] for e in both['evidence']} == {'Mirefang', 'Voltcrest'}
    # The most specific name wins over « Voltcrest » alone; another archetype fully seen lowers the confidence.
    known = oa.signatures(['Voltcrest', 'Voltcrest Mirefang', 'Rexling'])
    mixed = oa.identify(observed(['Mirefang', 'Voltcrest', 'Rexling', 'Invented Rod']), known, ALIASES)
    assert (mixed['label'], mixed['confidence'], mixed['candidates']) == ('Voltcrest Mirefang', 'low', ['Rexling'])


def test_trainers_and_energy_never_count():
    result = oa.identify(observed(['Voltcrest Energy', 'Invented Rod', 'Invented Ball']), KNOWN, ALIASES)
    assert result['label'] is None


def match(reference, plays, label=None, outcome='losses'):
    return {'match': reference, 'outcome': outcome, 'max_observed_turn': 6, 'evidence': [],
            'explicit_prize_totals': {'self': None, 'opponent': None},
            'opponent': {'label': label, 'basis': 'unknown', 'exact_deck_proven': False},
            'opponent_cards': observed(plays)}


def test_the_report_copy_carries_probable_opponents_and_the_original_is_untouched():
    report = {'matches': [match('Partie 1', ['Synthwing Rex', 'Rexling', 'Invented Rod', 'Synthwing Rex']),
                          match('Partie 2', ['Invented Rod', 'Invented Ball', 'Rexling'], outcome='wins'),
                          match('Partie 3', ['Voltcrest'], label='Recorded Family')]}
    original = copy.deepcopy(report)
    classify = oa.Classifier(KNOWN, ALIASES)
    shown = oa.with_probable_opponents(report, classify)
    assert report == original
    labels = [m['opponent']['label'] for m in shown['matches']]
    assert labels == ['probable:Synthwing Rex', None, 'Recorded Family']
    assert {g['archetype'] for g in shown['groups']} == {'probable:Synthwing Rex', 'unknown', 'Recorded Family'}
    assert shown['probable_opponents'] == {'version': oa.VERSION, 'games': 1}
    assert classify(report['matches'][0]['opponent_cards']) is classify(report['matches'][0]['opponent_cards'])
    assert oa.with_probable_opponents(report, None) is report
    # Display: never a fact, the cards in the ⓘ, the Coach's {adversaire} in a sentence.
    assert display(opponent_name('probable:Synthwing Rex')) in ('Probablement : Synthwing Rex', 'Probably: Synthwing Rex')
    assert opponent_name('probable:Synthwing Rex').en == 'Probably: Synthwing Rex'
    assert opponent_words('probable:Synthwing Rex').fr == 'Synthwing Rex (probable)'
    assert opponent_words('unknown') is None and display(opponent_name('unknown')) in ('Adversaire non identifié', 'Unidentified opponent')
    tip = probable_tip(shown['matches'])
    assert 'Synthwing Rex' in tip.fr and 'moyenne' in tip.fr and 'pas une certitude' in tip.fr
    assert 'medium' in tip.en and oa.VERSION in tip.fr
    assert probable_tip(original['matches']) is None


def test_no_local_archetypes_means_no_classifier(local_tmp):
    assert oa.local_classifier(local_tmp) is None


def test_services_read_a_report_with_probable_opponents_without_writing(local_tmp, monkeypatch):
    from pokemind.desktop.services import Services
    report = {'as_of': '2026-11-18', 'model_version': 'battle-batch-v4', 'coverage': {'valid': 1},
              'outcomes': {'wins': 0, 'losses': 1, 'unknown': 0}, 'own_decks': {},
              'matches': [match('Partie 1', ['Synthwing Rex', 'Rexling', 'Invented Rod', 'Synthwing Rex'])]}
    report['groups'] = battle_batch.group_matches(report['matches'])
    original = copy.deepcopy(report)
    before = sorted(p.name for p in local_tmp.rglob('*'))
    monkeypatch.setattr(oa, 'local_classifier', lambda root: oa.Classifier(KNOWN, ALIASES))
    services = Services(local_tmp)
    services.set_full_report(report)
    assert report == original and sorted(p.name for p in local_tmp.rglob('*')) == before
    assert [g['archetype'] for g in services.full_report['groups']] == ['probable:Synthwing Rex']
    assert services.report['matches'][0]['opponent']['probable']['confidence'] == 'medium'
    assert 'Probablement : Synthwing Rex' in str(services.local_answer('bilan'))
