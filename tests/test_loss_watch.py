"""Loss-first follow-up (PM-COACH-LOSS-PRIORITY-001). Every game, family and card here is invented."""
import json

from pokemind import battle_coach, loss_watch
from pokemind.desktop import ingestion
from pokemind.desktop.services import MY_DECKS, SAVE_REQUEST, Services
from test_desktop_ingestion import text

EXPORT = 'Pokémon: 20\n20 Invented Alpha INV 1\nTrainer: 20\n20 Invented Beta INV 2\nEnergy: 20\n20 Basic Invented Energy INV 3'
WIN, LOSS = text('InventedSelf'), text()


def game(ref, outcome, family, cards=(), day=None):
    return {'match': ref, 'outcome': outcome, 'opponent': {'label': family},
            'opponent_cards': [{'name': c} for c in cards], **({'added_on': day} if day else {})}


def report(matches):
    from pokemind.battle_batch import group_matches
    records = [dict(m, evidence=[], max_observed_turn=8, explicit_prize_totals={'self': None, 'opponent': None},
                    opponent=dict(m['opponent'], basis='inferred')) for m in matches]
    return {'as_of': '2026-11-06', 'matches': records, 'groups': group_matches(records),
            'outcomes': {k: sum(m['outcome'] == k for m in records) for k in ('wins', 'losses', 'unknown')}}


def family(view, name):
    return next((f for f in view['families'] if f['family'] == name), None)


def test_a_win_or_an_unknown_result_never_opens_a_follow_up():
    view = loss_watch.problem_matchups(report([game('m1', 'wins', 'Invented Alpha'), game('m2', 'unknown', 'Invented Gamma')]))
    assert view['families'] == [] and view['families_tracked'] == 0 and view['total_losses'] == 0
    assert loss_watch.followup(report([game('m1', 'wins', 'Invented Alpha')]), game('m1', 'wins', 'Invented Alpha')) | {
        'policy': None} == {'outcome': 'win', 'family': 'Invented Alpha', 'tracked': False, 'family_record': None,
                            'note': 'Victoire comptée; famille non suivie; reconstruction conditionnelle distincte.',
                            'automatic_deck_save': 'conditional_local_public_only', 'policy': None}
    unknown = loss_watch.followup(report([game('m2', 'unknown', 'Invented Gamma')]), game('m2', 'unknown', 'Invented Gamma'))
    assert unknown['outcome'] == 'unknown' and not unknown['tracked'] and unknown['family_record'] is None


def test_one_loss_on_a_small_sample_is_a_topic_to_watch_not_a_conclusion():
    value = report([game('m1', 'losses', 'Invented Alpha', ['Card One', 'Card Two'], '2026-11-02')])
    entry = family(loss_watch.problem_matchups(value), 'Invented Alpha')
    assert entry['status'] == 'watch' and (entry['wins'], entry['losses'], entry['n']) == (0, 1, 1)
    assert entry['uncertainty'].startswith('Première défaite') and 'aucune conclusion statistique' in entry['uncertainty']
    assert entry['first_loss_day'] == entry['last_loss_day'] == '2026-11-02'
    assert [c['name'] for c in entry['cards_seen_in_losses']] == ['Card One', 'Card Two']
    follow = loss_watch.followup(value, value['matches'][0])
    assert follow['outcome'] == 'loss' and follow['tracked'] and 'à surveiller' in follow['note']
    assert follow['automatic_deck_save'] == 'conditional_local_public_only'


def test_two_losses_of_one_family_make_one_recurring_entry_and_wins_keep_counting():
    value = report([game('m1', 'wins', 'Invented Alpha', ['Seen In Win']),          # WIN → LOSS → WIN → LOSS
                    game('m2', 'losses', 'Invented Alpha', ['Card One'], '2026-11-01'),
                    game('m3', 'wins', 'Invented Alpha'),
                    game('m4', 'losses', 'Invented Alpha', ['Card One', 'Card Two'], '2026-11-04'),
                    game('m5', 'losses', 'Invented Beta', ['Card Three'], '2026-11-03'),
                    game('m6', 'wins', 'Invented Omega')])
    view = loss_watch.problem_matchups(value)
    assert [f['family'] for f in view['families']] == ['Invented Alpha', 'Invented Beta']  # worst first, no win-only family
    alpha = family(view, 'Invented Alpha')
    assert (alpha['wins'], alpha['losses'], alpha['n'], alpha['games'], alpha['loss_share']) == (2, 2, 4, 4, 0.5)
    assert alpha['status'] == 'recurring_loss' and view['recurring_families'] == 1 and view['total_losses'] == 3
    assert (alpha['first_loss_day'], alpha['last_loss_day']) == ('2026-11-01', '2026-11-04')
    # Only cards seen in the losses; never a 60-card list.
    assert alpha['cards_seen_in_losses'] == [{'name': 'Card One', 'loss_games_seen': 2}, {'name': 'Card Two', 'loss_games_seen': 1}]
    assert not any(key in json.dumps(view) for key in ('"export"', 'total_cards', 'is_exact_opponent_deck'))
    # A win after the follow-up exists updates it, without erasing it.
    follow = loss_watch.followup(value, value['matches'][2])
    assert follow['outcome'] == 'win' and follow['tracked'] and follow['family_record']['wins'] == 2
    assert 'suivi existant' in follow['note']


def test_focus_keeps_a_named_family_and_the_limit_reports_the_rest():
    value = report([game('m%d' % i, 'losses', 'Invented %02d' % i) for i in range(12)])
    view = loss_watch.problem_matchups(value, focus={'invented 11'}, limit=3)
    assert view['families'][0]['family'] == 'Invented 11' and len(view['families']) == 3 and view['more'] == 9


def prepared(services, question, *, log=None):
    """log: the ingest result of the pasted game, selected as the app does (ingest_done); report order is not paste order."""
    services.load()
    services.selected_match = log['match']['match'] if log else None
    return services.prepare_question(question, 'aggregates', log_followup=bool(log))


def no_opponent_deck_written(root):
    return not (root / MY_DECKS).exists() and not list((root / battle_coach.REPORT_DIR).glob('candidate-*.txt'))


def test_a_pasted_loss_is_followed_and_the_coach_cannot_save_the_opponent_deck(local_tmp):
    pasted = ingestion.ingest(local_tmp, LOSS)
    assert pasted['outcome'] == 'L'
    services = Services(local_tmp)
    context = prepared(services, 'J’ai perdu cette partie. Situe-la dans mon suivi des défaites.', log=pasted)
    follow = context['log_followup']
    assert follow['outcome'] == 'loss' and follow['tracked'] and follow['family_record']['losses'] == 1
    assert 'opponent_reconstruction' in context and context['loss_watch']['total_losses'] == 1
    assert 'InventedRival' not in json.dumps(context) and 'InventedSelf' not in json.dumps(context)
    refused = services.tool_call({'operation': 'save_deck', 'query': 'Deck adverse inventé', 'export_text': EXPORT}, 'aggregates')
    assert refused['error'] == 'DECK_SAVE_REQUIRES_OWNER_REQUEST' and services.saved_deck is None
    candidate = services.tool_call({'operation': 'save_candidate', 'export_text': EXPORT}, 'aggregates')
    assert candidate['error'] == 'CANDIDATE_REQUIRES_OWNER_REQUEST'
    assert no_opponent_deck_written(local_tmp)


def test_a_pasted_win_counts_without_reconstruction_follow_up_or_deck(local_tmp):
    pasted = ingestion.ingest(local_tmp, WIN)
    services = Services(local_tmp)
    context = prepared(services, 'J’ai gagné cette partie. Fais un bref bilan de ce qui a fonctionné.', log=pasted)
    assert context['log_followup']['outcome'] == 'win' and not context['log_followup']['tracked']
    assert 'opponent_reconstruction' not in context and context['loss_watch']['families'] == []
    assert context['outcomes'] == {'wins': 1, 'losses': 0, 'unknown': 0}
    assert services.tool_call({'operation': 'save_deck', 'query': 'Gagné', 'export_text': EXPORT},
                              'aggregates')['error'] == 'DECK_SAVE_REQUIRES_OWNER_REQUEST'
    assert no_opponent_deck_written(local_tmp)


def test_win_loss_win_sequence_and_repeated_paste_keep_exact_counts_without_duplicates(local_tmp):
    first = ingestion.ingest(local_tmp, WIN)
    ingestion.ingest(local_tmp, LOSS)
    again = ingestion.ingest(local_tmp, LOSS, report=first['result']['report'])   # the same loss pasted twice
    assert again['status'] == 'DUPLICATE'
    last = ingestion.ingest(local_tmp, WIN.replace('Creature Alpha', 'Creature Delta'))  # a second, distinct win
    assert last['result']['report']['outcomes'] == {'wins': 2, 'losses': 1, 'unknown': 0}
    services = Services(local_tmp)
    context = prepared(services, 'J’ai gagné cette partie.', log=last)
    record = context['log_followup']['family_record']
    assert context['log_followup']['outcome'] == 'win' and context['log_followup']['tracked']
    assert (record['wins'], record['losses'], record['n']) == (2, 1, 3) and record['status'] == 'watch'
    assert context['loss_watch']['families_tracked'] == 1 and len(context['loss_watch']['families']) == 1
    assert no_opponent_deck_written(local_tmp)


def test_explicit_owner_requests_still_save_and_old_opponent_saves_are_kept_apart(local_tmp):
    pasted = ingestion.ingest(local_tmp, LOSS)
    services = Services(local_tmp)
    # The owner's own words around the pasted log are an explicit request.
    prepared(services, 'Ajoute ce deck à mes decks', log=pasted)
    assert services.deck_save_allowed and services.candidate_allowed
    assert services.tool_call({'operation': 'save_deck', 'query': 'Alpha - adversaire du 2026-10-31',
                               'export_text': EXPORT}, 'aggregates')['status'] == 'SAVED_DECK'
    # A normal turn keeps save_deck for the owner's own deck, no keyword gate (owner, 2026-11-02).
    prepared(services, 'Crée-le stp')
    assert services.deck_save_allowed and not services.candidate_allowed
    mine = EXPORT.replace('20 Invented Alpha', '20 Invented Mine')
    assert services.save_deck('Mon deck inventé', mine, source='owner')['status'] == 'SAVED_DECK'
    options = [o for o in services.deck_options() if 'personnelle' in o['kind']]
    assert [o['label'] for o in options] == ['Mon deck inventé', 'Alpha - adversaire du 2026-10-31']
    assert options[1]['opponent_rebuild'] and 'Deck adverse reconstruit' in options[1]['kind']
    assert options[1]['selector'].startswith('deck adverse · ') and options[0]['selector'].startswith('mon deck · ')
    assert not options[0]['opponent_rebuild'] and len(list((local_tmp / MY_DECKS).glob('deck-*.json'))) == 2  # nothing deleted


def test_loss_questions_reach_the_coach_with_the_follow_up_and_its_limits(local_tmp):
    ingestion.ingest(local_tmp, LOSS)
    ingestion.ingest(local_tmp, LOSS.replace('Creature Beta', 'Creature Epsilon'))
    services = Services(local_tmp)
    for question in ('Contre quels decks je perds le plus?', 'Comment battre ce deck?', 'Propose-moi un deck pour le battre'):
        watch = prepared(services, question)['loss_watch']
        assert watch['total_losses'] == 2 and watch['families'] and 'aucune liste adverse de 60' in watch['policy'].casefold()
        assert all('uncertainty' in f and f['causal_effect'] == 'unknown' for f in watch['families'])
    assert services.tool_call({'operation': 'context', 'query': 'défaites'}, 'aggregates')['loss_watch']['total_losses'] == 2
    assert 'loss_watch' not in services.context('Contre quels decks je perds le plus?', 'public')  # personal: never public-only


def test_the_automatic_question_words_never_count_as_a_save_request():
    from pokemind.assistant.provider import COACH_SYSTEM
    from pokemind.assistant.tools import TOOL
    for question in ('J’ai perdu cette partie. Identifie la famille adverse d’après les cartes vues, situe-la dans mon '
                     'suivi des défaites (bilan, n, incertitude), puis dis-moi ce qui a pu jouer contre moi et comment '
                     'préparer ce matchup.',
                     'J’ai gagné cette partie. Fais un bref bilan de ce qui a fonctionné; elle compte dans mes statistiques.'):
        assert not SAVE_REQUEST.search(question)
    assert 'colle un journal' not in TOOL['description'] and 'L automate local peut enregistrer une hypothese PUBLIC' in COACH_SYSTEM


def test_the_main_deck_list_follows_the_personal_deck_gate_and_the_consent_text_says_so(local_tmp):
    """Audit point 0.9.4: « + mes statistiques anonymes » sent the whole main-deck list with every question.
    The list now goes only when the question is about a deck or a list (the rule of « Mes decks »); the name
    stays, so « mon deck » still works, and the settings and wizard say what is sent."""
    from pokemind.desktop.insights import favorite_key
    from pokemind.desktop.translations import _PAIRS
    services = Services(local_tmp)
    mine = EXPORT.replace('20 Invented Alpha', '20 Invented Mine')
    assert services.save_deck('Mon deck inventé', mine, source='owner')['status'] == 'SAVED_DECK'
    services.main_deck = favorite_key({'export': mine})
    unrelated = services.prepare_question('Explique les Récompenses en une phrase.', 'aggregates')['owner_main_deck']
    assert unrelated['name'] == 'Mon deck inventé' and 'export' not in unrelated
    assert 'deck' in unrelated['export_withheld'] and mine not in json.dumps(unrelated, ensure_ascii=False)
    for question in ('Comment battre Invented Beta avec mon deck?', 'Améliore ma liste'):
        assert services.prepare_question(question, 'aggregates')['owner_main_deck']['export'] == mine
    assert 'owner_main_deck' not in services.prepare_question('Comment battre Invented Beta avec mon deck?', 'public')
    assert 'la liste de ton deck principal quand ta question parle de deck' in _PAIRS
