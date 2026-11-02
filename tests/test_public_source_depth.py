"""Invented PUBLIC evidence only. No actual Pokémon rule or network transport."""
import copy
import hashlib
import json
from contextlib import closing

import pytest

from pokemind import batch_public_research as research, meta
from pokemind.assistant.receipts import public_research_message
from test_batch_public_research import Response
from test_meta import FakeMetaClient, _routes_for_ids


DAY = '2031-06-01'
URL = 'https://www.pokemon.com/us/pokemon-news/2026-pokemon-tcg-standard-format-rotation-announcement'
POLICY = {'mode':'derived_fields_only', 'license':'synthetic_author_owned',
          'reference':'invented-test-license-v1'}
SENTENCE = 'In the Standard format for TCG Live, regulation marks Q, R are allowed starting 2031-05-01.'


@pytest.fixture(autouse=True)
def no_transport_delay(monkeypatch):
    monkeypatch.setattr(research.time, 'sleep', lambda _: None)


def page(sentence=SENTENCE, published='2031-04-01'):
    return (f'<html><head><meta property="article:published_time" content="{published}"></head>'
            f'<body><article><p>{sentence}</p></article></body></html>').encode()


class InventedPages:
    def __init__(self, body=None):
        self.body = page() if body is None else body
        self.calls = []

    def open(self, request, timeout):
        self.calls.append(request.full_url)
        return Response(request.full_url, b'User-agent: *\nAllow: /\n'
                        if request.full_url.endswith('/robots.txt') else self.body)


def collect(root, body=None, policy=POLICY, campaign=None):
    return research.refresh_public(root, as_of=DAY, opener=InventedPages(body), endpoints=[URL],
                                   official_policy={URL:policy}, campaign=campaign)


def test_contained_rule_becomes_bounded_fields_and_substantive_cited_answer(local_tmp):
    collect(local_tmp)
    value = research.research(local_tmp, as_of=DAY, topic='rules', offline=True)
    field = value['facts'][0]['rule_evidence']
    assert field['status'] == 'extracted_unverified'
    assert field['assertions'][0]['allowed_regulation_marks'] == ['Q', 'R']
    text = public_research_message(value, 'Explique les règles et implications')
    assert 'Q, R' in text and '2031-05-01' in text and '2031-04-01' in text
    assert 'TCG Live' in text and 'extracted_unverified' in text and URL in text
    assert 'application courante : unknown' in text  # stale collection != current authority
    assert 'réimpression : unknown' in text and 'disponibilité dans Live : unknown' in text
    assert 'Enregistrement local' not in text  # offline read never claims a write
    manifests = list(local_tmp.glob('data/local/public-campaigns/*/research.json'))
    assert SENTENCE not in manifests[0].read_text(encoding='utf-8')
    assert not list(local_tmp.glob('data/local/public-campaigns/*/pages/*.body'))


@pytest.mark.parametrize('body,reason', [
    (b'<html><title>Rotation: Q, R allowed starting 2031-05-01</title></html>', 'TEXT_ABSENT_OR_UNSUPPORTED'),
    (page('In the Standard format for TCG Live, regulation marks Q, R are allowed.'), 'EFFECTIVE_DATE_MISSING'),
    (page(published=''), 'PUBLICATION_DATE_MISSING_OR_INVALID'),
    (page(published='2031-12-01'), 'FUTURE_PUBLICATION'),
    (page(SENTENCE.replace('2031-05-01', '2031-07-01')), 'NOT_YET_EFFECTIVE'),
    (page(SENTENCE + '</p><p>' + SENTENCE.replace('Q, R','S, T')), 'CONFLICTING_ASSERTIONS'),
    (page('<script>' + SENTENCE + '</script>'), 'TEXT_ABSENT_OR_UNSUPPORTED'),
    (page(SENTENCE.replace('2031-05-01','2031-02-30')), 'EFFECTIVE_DATE_MISSING_OR_INVALID'),
])
def test_unknown_future_conflict_and_metadata_cannot_become_current_rule(local_tmp, body, reason):
    collect(local_tmp, body)
    value = research.research(local_tmp, as_of=DAY, topic='rules', offline=True)
    text = public_research_message(value, 'règles')
    assert reason in text and 'application courante : unknown' in text
    assert '100% légale' not in text


@pytest.mark.parametrize('policy', [None, {}, {'mode':'full_page','license':'synthetic_author_owned','reference':'x'},
    POLICY | {'license':'unknown'}, POLICY | {'reference':''}])
def test_unestablished_license_or_retention_never_retains_rule_fields(local_tmp, policy):
    collect(local_tmp, policy=policy)
    fact = research.knowledge_view(local_tmp, as_of=DAY)['facts'][0]
    assert fact['rule_evidence']['assertions'] == []
    assert fact['rule_evidence']['status'] == 'RETENTION_NOT_AUTHORIZED'
    assert 'Q, R' not in json.dumps(fact)


def test_unadmitted_source_has_no_rule_extraction_and_no_request(local_tmp):
    opener = InventedPages()
    value = research.refresh_public(local_tmp, as_of=DAY, opener=opener,
        endpoints=['https://unadmitted.invalid/rules'], official_policy={URL:POLICY})
    assert not opener.calls and not value['facts']


def test_dedup_reopen_stale_and_revision_use_existing_memory_only(local_tmp, monkeypatch):
    monkeypatch.setattr(research.time, 'sleep', lambda _: None)
    campaign = 'a'*32
    first = collect(local_tmp, campaign=campaign)
    again = collect(local_tmp, campaign=campaign)
    assert again['reused_offline'] and first['facts'] == again['facts']
    collect(local_tmp, campaign='b'*32)
    assert len(research.knowledge_view(local_tmp, as_of=DAY)['history']) == 1
    before = [(p, hashlib.sha256(p.read_bytes()).hexdigest()) for p in
              local_tmp.glob('data/local/public-campaigns/*/research.json')]
    class Forbidden:
        def open(self, *args, **kwargs): pytest.fail('offline GET forbidden')
    value = research.research(local_tmp, as_of='2031-08-01', topic='rules', offline=True, opener=Forbidden())
    assert value['gets'] == value['added'] == value['updated'] == 0
    text = public_research_message(value,'règles')
    assert 'Q, R' in text and 'application courante : unknown' in text
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==sha for p,sha in before)
    collect(local_tmp, page(SENTENCE.replace('Q, R','S, T')), campaign='c'*32)
    view = research.knowledge_view(local_tmp, as_of=DAY)
    assert len(view['history']) == 2 and view['history'][0]['revision_status'] == 'superseded'


def meta_fixture(root, *, missing=False, one=False):
    db = root / 'meta.sqlite3'
    ids = ['a','b'] if one else ['a','b','c','d']
    routes = _routes_for_ids(ids)
    for i, tid in enumerate(ids):
        day = '2031-05-05' if i < 2 else '2031-05-25'
        routes[f'/tournaments/{tid}/details']['date'] = day + 'T12:00:00Z'
        standings = routes[f'/tournaments/{tid}/standings']
        # 10 placements and 5 classified published matches per tournament.
        standings[:] = [copy.deepcopy(standings[j%2]) | {'player':f'{tid}-{j}', 'placing':j+1}
                        for j in range(10)]
        for j, row in enumerate(standings):
            row['deck'] = None if missing else {'id':'aurora' if (j < (2 if i<2 else 8)) else 'boreal',
                                               'name':'Invented family'}
        routes[f'/tournaments/{tid}/pairings'] = [
            {'phase':1,'round':1,'table':j+1,'player1':f'{tid}-{2*j}',
             'player2':f'{tid}-{2*j+1}','winner':0} for j in range(5)]
    meta.sync_meta(db,max_requests=30,max_tournaments=4,client=FakeMetaClient(30,routes))
    with closing(__import__('sqlite3').connect(db)) as con:
        con.execute("UPDATE meta_tournaments SET fetched_at='2031-05-31T12:00:00Z'")
        con.commit()
    return db


@pytest.mark.parametrize('missing,one,supported', [(False,False,True),(True,False,False),(False,True,False)])
def test_temporal_classified_sample_supports_only_descriptive_change(local_tmp, missing, one, supported):
    db = meta_fixture(local_tmp,missing=missing,one=one)
    before = hashlib.sha256(db.read_bytes()).hexdigest()
    result = meta.meta_window_comparison(db,since='2031-05-01',split='2031-05-15',until='2031-05-31',as_of=DAY)
    assert result['supported'] is supported
    assert result['causal_improvement'] == 'unknown'
    assert result['observation_unit'] == 'published_placement_not_unique_player'
    if supported:
        assert result['changes'][0]['before_fraction'] != result['changes'][0]['after_fraction']
        assert result['windows'][0]['n_tournaments'] == 2
        assert result['windows'][0]['classifiable_matches'] == 10
    else:
        assert not result['changes'] and result['missing_data']
    text = public_research_message({'as_of':DAY,'facts':[],'meta_evidence':result},'tendances méta pourquoi?')
    assert ('Variation descriptive' in text) is supported
    assert 'causalité : unknown' in text and '2031-05-01' in text and 'PTCGL' in text
    assert hashlib.sha256(db.read_bytes()).hexdigest() == before


def test_future_events_observations_incomplete_or_other_context_excluded(local_tmp):
    db = meta_fixture(local_tmp)
    with closing(__import__('sqlite3').connect(db)) as con:
        con.execute("UPDATE meta_tournaments SET date_utc='2031-06-02T00:00:00Z' WHERE tournament_id='a'")
        con.execute("UPDATE meta_tournaments SET fetched_at='2031-06-02T00:00:00Z' WHERE tournament_id='b'")
        con.execute("UPDATE meta_tournaments SET snapshot_status='partial' WHERE tournament_id='c'")
        con.execute("UPDATE meta_tournaments SET platform='TABLETOP' WHERE tournament_id='d'")
        con.commit()
    result = meta.meta_window_comparison(db,since='2031-05-01',split='2031-05-15',until='2031-05-31',as_of=DAY)
    assert not result['supported'] and all(w['n_tournaments']==0 for w in result['windows'])


def test_cross_source_conflict_and_forged_provider_prose_fail_closed(local_tmp):
    collect(local_tmp)
    value = research.research(local_tmp,as_of=DAY,topic='rules',offline=True)
    other = copy.deepcopy(value['facts'][0])
    other['source_url'] = 'https://www.pokemon.com/us/play-pokemon/about/tournaments-rules-and-resources'
    other['rule_evidence']['assertions'][0]['allowed_regulation_marks'] = ['S','T']
    value['facts'].append(other)
    value['provider_answer'] = '100% légale, rien mémorisé'
    text = public_research_message(value,'règles et réimpression')
    assert 'CONFLICTING_ASSERTIONS' in text and '100% légale' not in text
    assert 'réimpression : unknown' in text


@pytest.mark.parametrize('body', [b'<html>captcha</html>', b'x'*(2*1024*1024)], ids=['challenge','size-cap'])
def test_official_transport_protections_precede_extraction_and_no_page_retention(local_tmp,body):
    result=collect(local_tmp,body)
    assert not result['facts'] and result['closed_hosts']
    assert not list(local_tmp.glob('data/local/public-campaigns/*/pages/*.body'))


def test_official_redirect_and_robots_denial_stop_without_extraction(local_tmp):
    class Redirect(InventedPages):
        def open(self,request,timeout):
            response=super().open(request,timeout)
            if not request.full_url.endswith('/robots.txt'):
                response.url='https://unadmitted.invalid/redirect'
            return response
    result=research.refresh_public(local_tmp,as_of=DAY,opener=Redirect(),endpoints=[URL],official_policy={URL:POLICY})
    assert not result['facts'] and result['closed_hosts']
    opener=InventedPages()
    opener.open=lambda request,timeout: Response(request.full_url,b'User-agent: *\nDisallow: /\n')
    result=research.refresh_public(local_tmp,as_of=DAY,opener=opener,endpoints=[URL],official_policy={URL:POLICY},campaign='d'*32)
    assert not result['facts'] and result['gets']==1


def test_rule_fields_from_a_directory_or_untyped_summary_are_never_used(local_tmp):
    collect(local_tmp)
    value=research.research(local_tmp,as_of=DAY,topic='rules',offline=True)
    value['facts'][0]['source_url']='https://www.limitlesstcg.com/decks'
    text=public_research_message(value,'règles')
    assert 'Q, R' not in text
    value['facts'][0]['rule_evidence']='100% légale'
    assert '100%' not in public_research_message(value,'règles')


def test_meta_insufficient_counts_cannot_be_overridden_by_summary_or_supported_flag(local_tmp):
    db=meta_fixture(local_tmp,one=True)
    result=meta.meta_window_comparison(db,since='2031-05-01',split='2031-05-15',until='2031-05-31',as_of=DAY)
    result.update(supported=True,summary='Guaranteed causal improvement',changes=[{'winrate':100}])
    text=public_research_message({'facts':[],'meta_evidence':result},'méta')
    assert 'aucune tendance calculée' in text and 'Guaranteed' not in text
    result['windows'][0]['sources'][0]['version']='invalid'
    assert 'Données descriptives' not in public_research_message({'facts':[],'meta_evidence':result},'méta')


def test_marked_existing_pairing_cache_is_reused_offline_without_writes_or_get(local_tmp,monkeypatch):
    db=meta_fixture(local_tmp)
    monkeypatch.setattr(research,'matchup_database',lambda root:db)
    class Forbidden:
        def open(self,*a,**k):pytest.fail('offline must not collect')
    before=hashlib.sha256(db.read_bytes()).hexdigest()
    receipt=research.research(local_tmp,as_of=DAY,topic='meta',offline=True,opener=Forbidden())
    assert receipt['gets']==receipt['added']==receipt['updated']==0
    assert receipt['meta_evidence']['windows'] and not receipt['facts']
    assert 'Variation descriptive' in public_research_message(receipt,'tendances méta')
    assert hashlib.sha256(db.read_bytes()).hexdigest()==before
