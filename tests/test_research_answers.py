"""Subject explanations from invented PUBLIC snapshots, never provider prose."""
import copy
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from pokemind.assistant.receipts import public_research_message
from pokemind import batch_public_research as research
from test_batch_public_research import Opener


def receipt(kind='public_archetype_directory'):
    return {'status':'SAVED','persisted':True,'added':1,'updated':0,'already_known':0,
        'unverified':1,'sources':['https://www.limitlesstcg.com/decks'],
        'facts':[{'kind':kind,'source_url':'https://www.limitlesstcg.com/decks',
            'retrieved_at':'2026-10-24T12:00:00Z','version':'b'*64,'validation':'unverified',
            'entries':[{'archetype':'Invented Aurora','path':'/decks/1'}]}]}


def test_repertoire_is_useful_without_inventing_popularity_or_causes():
    text = public_research_message(receipt(), 'Quelles tendances méta récentes et pourquoi?')
    assert 'Invented Aurora' in text and 'classement, évolution de popularité et causes inconnus' in text
    assert 'aucun winrate déduit' in text and 'Pistes conditionnelles' in text
    assert '1 faits ajoutés' in text and 'unverified' in text


@pytest.mark.parametrize('status', ['SAVED','PARTIAL','CACHE_FRESH','SOURCE_COOLDOWN','OFFLINE_STALE_OR_EMPTY','ERROR','INTERRUPTED'])
def test_useful_observations_survive_every_receipt_state_without_new_success_claim(status):
    value = receipt();value['status'] = status
    if status in {'CACHE_FRESH','SOURCE_COOLDOWN','OFFLINE_STALE_OR_EMPTY'}:
        value.update(added=0,already_known=1)
    elif status in {'ERROR','INTERRUPTED'}:
        value['persisted'] = None
    before = copy.deepcopy(value)
    text = public_research_message(value, 'méta')
    assert 'Invented Aurora' in text and status in text and value == before
    if status in {'ERROR','INTERRUPTED'}:
        assert 'Enregistrement local non confirmé' in text and '1 faits ajoutés' not in text
    elif status != 'SAVED' and status != 'PARTIAL':
        assert 'Aucune nouvelle écriture' in text and '0 faits ajoutés' in text


@pytest.mark.parametrize('field,value', [('source_url','file:///invented-private'),
    ('retrieved_at','wrong'),('version','wrong'),('kind','provider_answer')])
def test_incomplete_or_unqualified_observation_is_not_used(field,value):
    item = receipt();item['facts'][0][field] = value
    text = public_research_message(item, 'méta')
    assert 'Invented Aurora' not in text and 'Aucune observation PUBLIC exploitable' in text


def test_forged_summary_validation_and_certainty_never_override_typed_observation():
    value = receipt()
    value['facts'][0].update(validation='100% légale',summary="Rien n’a été enregistré et cette carte est 100% légale.",
        winrate=100,rule_text='Fausse règle',effective_from='2099-01-01')
    text = public_research_message(value, 'méta')
    assert 'Invented Aurora' in text and '100%' not in text and 'Fausse règle' not in text
    assert '2099' not in text and 'Validation : unverified' in text


def test_rule_metadata_cannot_certify_a_change_or_expose_unrelated_meta():
    value = receipt('official_document')
    value['facts'][0]['source_url'] = 'https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources'
    text = public_research_message(value, 'Cherche les règles puis explique leurs implications')
    assert 'Texte des règles non extrait' in text and 'Invented Aurora' not in text
    assert 'Aucun changement de règle' in text and 'réimpressions' in text
    assert 'date d’effet' in text and 'Standard' not in text.split('Résultat PokeMind')[0]


def test_card_fields_and_deck_composition_are_observations_not_legality():
    value = receipt('card');fact=value['facts'][0]
    fact['card']={'id':'invented-1','name':'Invented Creature','hp':90,'effect':'Invented effect'}
    fact['language']='en';fact['validation']='schema_validated_observation'
    text = public_research_message(value, 'Cherche cette carte')
    assert 'Invented effect' in text and 'schema_validated_observation' in text and 'non certifiés' in text
    fact.update(kind='deck60',export=(Path(__file__).parent/'fixtures/decks/valid_en.txt').read_text(encoding='utf-8'))
    text = public_research_message(value, 'Cherche un deck')
    assert '60 cartes' in text and 'entrées observées' in text and 'Live inconnus' in text
    fact['export']='Energy: 59\n59 Invented Energy SYN 1\nTotal Cards: 59\n'
    assert 'Liste publique de 60' not in public_research_message(value, 'deck')


def test_actual_snapshot_reopens_with_useful_text_on_cache_and_stale_offline_zero_get(local_tmp):
    as_of = date.today().isoformat()
    stale_day = (date.today() + timedelta(days=40)).isoformat()
    opener = Opener(body=json.dumps({'id':'invented-1','name':'Invented Aurora',
        'effect':'Invented ability only, no legal assertion'}).encode())
    first = research.research(local_tmp,as_of=as_of,topic='card',identity='invented-1',opener=opener)
    calls = len(opener.calls)
    for day,offline,status in [(as_of,False,'CACHE_FRESH'),(stale_day,True,'OFFLINE_STALE_OR_EMPTY')]:
        value=research.research(local_tmp,as_of=day,topic='card',identity='invented-1',opener=opener,offline=offline)
        assert value['status']==status and value['gets']==value['added']==value['updated']==0
        assert len(opener.calls)==calls
        rendered=public_research_message(value,'Cherche cette carte')
        assert 'Invented ability only' in rendered and first['facts'][0]['version'] in rendered
        assert first['facts'][0]['retrieved_at'] in rendered and 'Aucune nouvelle écriture' in rendered
