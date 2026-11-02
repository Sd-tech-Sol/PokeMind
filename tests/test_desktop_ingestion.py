"""Invented logs through the real parser, file publisher, coach and Learning Loop."""
import json
import os
import sqlite3
import threading
from contextlib import closing
from pathlib import Path

import pytest

from pokemind import battle_batch, battle_coach, database, battle_logs
from pokemind.desktop import ingestion
from pokemind.desktop.services import Services


def text(winner='InventedRival'):
    return ("Reference player: InventedSelf\nTurn # 1 - InventedSelf's Turn\n"
        "InventedSelf played Creature Alpha.\nTurn # 2 - InventedRival's Turn\n"
        "InventedRival played Creature Beta.\n" + winner + " wins.\n")


@pytest.fixture
def legacy(local_tmp):
    db=local_tmp/'data/local/pokemind.sqlite3'
    db.parent.mkdir(parents=True)
    with closing(sqlite3.connect(db)) as con:
        con.executescript((Path(__file__).parent/'fixtures/legacy_schema7.sql').read_text(encoding='utf-8'))
    return db,db.read_bytes()


@pytest.mark.parametrize('question', ['Quels sont mes chiffres?', 'How many battles did I lose?',
    'Explique le talent de cette carte.', 'Pourquoi jouer ce stade?'])
def test_normal_questions_are_not_raw_logs(question):
    assert ingestion.classify(question)=='question'


@pytest.mark.parametrize('fragment',['Préparation\nInventedSelf a choisi pile.','InventedSelf drew a card.'])
def test_short_incomplete_log_fragments_stay_local(local_tmp,fragment):
    assert ingestion.classify(fragment)=='ambiguous'
    assert ingestion.ingest(local_tmp,fragment)['status']=='REFUSED'
    assert not (local_tmp/battle_coach.LOG_DIR).exists()


def test_real_ingress_publishes_once_refreshes_real_counts_and_keeps_legacy(local_tmp,legacy):
    db,before=legacy
    stages=[]
    result=ingestion.ingest(local_tmp,text(),notify=stages.append)
    assert result['status']=='SAVED' and result['new_unique']==1 and result['stats_updated']
    assert result['outcome']=='L' and result['opponent']=='InventedRival'
    assert result['result']['report']['outcomes']=={'wins':0,'losses':1,'unknown':0}
    assert result['result']['learning']['current']
    files=list((local_tmp/battle_coach.LOG_DIR).glob('*.log'))
    assert len(files)==1 and files[0].stat().st_nlink==1 and files[0].read_text()==text()
    assert db.read_bytes()==before
    assert any('Enregistrement' in s for s in stages) and any('Actualisation' in s for s in stages)


def test_semantic_duplicate_already_saved_under_other_name_is_not_republished(local_tmp):
    folder=local_tmp/battle_coach.LOG_DIR;folder.mkdir(parents=True)
    original=folder/'invented-original.txt';original.write_text(text(),encoding='utf-8')
    result=ingestion.ingest(local_tmp,'\n\n'.join('  '+line+'  ' for line in text().splitlines()))
    assert result['status']=='DUPLICATE' and result['new_unique']==0 and result['match']
    assert list(folder.glob('*.txt'))==[original] and not list(folder.glob('*.log'))
    assert result['result']['report']['coverage']['valid']==1


def test_repeated_ingestion_and_new_win_revise_existing_learning_without_fake_statistics(local_tmp):
    first=ingestion.ingest(local_tmp,text())
    duplicate=ingestion.ingest(local_tmp,text(),report=first['result']['report'])
    win=ingestion.ingest(local_tmp,text('InventedSelf'))
    assert duplicate['status']=='DUPLICATE' and duplicate['result']['report']['coverage']['valid']==1
    assert win['new_unique']==1 and win['result']['report']['coverage']['valid']==2
    assert win['result']['report']['outcomes']=={'wins':1,'losses':1,'unknown':0}
    assert first['result']['report']['outcomes']['wins']==0


@pytest.mark.parametrize('value', [text().replace('InventedRival wins.',''),
    text().replace("Turn # 1 - InventedSelf's Turn\n",'').replace("Turn # 2 - InventedRival's Turn\n",''),
    text()+'InventedSelf wins.\n',text()+text(), 'InventedSelf played Something.\nInventedRival drew a card.'])
def test_incomplete_ambiguous_or_contradictory_never_creates_log_or_counts(local_tmp,value):
    result=ingestion.ingest(local_tmp,value)
    assert result['status']=='REFUSED' and result['reasons'] and result['new_unique']==0
    assert not (local_tmp/battle_coach.LOG_DIR).exists()


def test_configured_owner_must_be_one_of_two_participants(local_tmp):
    target=local_tmp/battle_coach.REPORT_DIR;target.mkdir(parents=True)
    (target/'coach-settings.json').write_text(json.dumps({'schema_version':1,'player':'UnrelatedInvented'}))
    assert ingestion.ingest(local_tmp,text())['status']=='REFUSED'
    assert not (local_tmp/battle_coach.LOG_DIR).exists()
    (target/'coach-settings.json').write_text('{invalid')
    with pytest.raises(ValueError,match='INGEST_PLAYER_SETTINGS_INVALID'):
        ingestion.ingest(local_tmp,text())
    assert not (local_tmp/battle_coach.LOG_DIR).exists()


def test_large_local_log_is_accepted_but_oversize_never_published(local_tmp):
    large=text().replace('InventedRival wins.','Observation neutre inventée.\n'*6000+'InventedRival wins.')
    assert len(large)>12000 and ingestion.classify(large)=='log'
    assert ingestion.ingest(local_tmp,large)['new_unique']==1
    files=list((local_tmp/battle_coach.LOG_DIR).glob('*.log'))
    assert ingestion.ingest(local_tmp,large*20)['status']=='REFUSED'
    assert list((local_tmp/battle_coach.LOG_DIR).glob('*.log'))==files


def test_atomic_publish_failure_never_exposes_partial_log_or_changes_existing(local_tmp,monkeypatch):
    folder=local_tmp/battle_coach.LOG_DIR;folder.mkdir(parents=True)
    existing=folder/'keep.txt';existing.write_text('invented existing file')
    monkeypatch.setattr(ingestion.os,'link',lambda *a:(_ for _ in ()).throw(OSError('invented interruption')))
    with pytest.raises(OSError):
        ingestion.ingest(local_tmp,text())
    assert not list(folder.glob('*.log')) and existing.read_text()=='invented existing file'
    assert not (folder/'.pokemind-ingest.lock').exists()


def test_two_concurrent_pastes_publish_one_unique_part(local_tmp):
    results=[]
    workers=[threading.Thread(target=lambda:results.append(ingestion.ingest(local_tmp,text()))) for _ in range(2)]
    for t in workers:t.start()
    for t in workers:t.join(10)
    assert all(not t.is_alive() for t in workers)
    assert sorted(r['status'] for r in results)==['DUPLICATE','SAVED']
    assert len(list((local_tmp/battle_coach.LOG_DIR).glob('*.log')))==1


def test_old_database_exact_duplicate_is_detected_without_new_raw_file(local_tmp):
    db=local_tmp/battle_coach.DB;db.parent.mkdir(parents=True)
    battle_logs.import_battle_log(db,text(),source_kind='file',reference_player='InventedSelf')
    before=db.read_bytes()
    result=ingestion.ingest(local_tmp,text())
    assert result['status']=='DUPLICATE' and result['new_unique']==0 and not result['stats_updated']
    assert not list((local_tmp/battle_coach.LOG_DIR).glob('*.log')) and db.read_bytes()==before


def test_public_only_personal_answer_uses_real_local_report_without_cloud(local_tmp):
    result=ingestion.ingest(local_tmp,text())
    services=Services(local_tmp);services.load()
    answer=services.local_answer('Mes statistiques')
    assert '1 parties uniques' in answer and '1 défaites' in answer and 'global inconnu' in answer
    context=services.context('Quels sont mes chiffres?','aggregates')
    assert context['valid_games']==1 and context['outcomes']['losses']==1
    assert context['personal_source']['internal_url']=='pokemind://page/1'
    assert 'InventedSelf' not in json.dumps(context) and 'InventedRival' not in json.dumps(context)


def test_size_cap_never_discards_personal_totals(local_tmp,monkeypatch):
    services=Services(local_tmp)
    services.report={'as_of':'2026-10-26','model_version':'battle-batch-v4','coverage':{'valid':7},
        'outcomes':{'wins':2,'losses':5,'unknown':0},'groups':[{'archetype':'x'*60000,'wins':2,'losses':5,'unknown':0,'n':7}]}
    monkeypatch.setattr(services,'search_cards',lambda *a:[])
    context=services.context('Mes combats','aggregates')
    assert context['valid_games']==7 and context['outcomes']['losses']==5
    assert len(json.dumps(context).encode())<=24000


def test_complete_only_batch_rejects_incomplete_and_deduplicates_indentation(local_tmp):
    folder=local_tmp/battle_coach.LOG_DIR;folder.mkdir(parents=True)
    for name,value in [('one.txt',text()),('two.txt','\n'.join('  '+l for l in text().splitlines())),
                       ('unfinished.txt',text().replace('InventedRival wins.',''))]:
        (folder/name).write_text(value,encoding='utf-8')
    result=battle_coach.coach(local_tmp,player='InventedSelf',update=True,complete_only=True)
    assert result['report']['coverage']['valid']==1 and result['report']['coverage']['duplicate']==1
    assert result['report']['outcomes']['unknown']==0


def test_attachment_scope_extensions_hardlinks_and_utf16(local_tmp):
    selected=local_tmp/'selected.log';selected.write_bytes(text().encode('utf-16'))
    assert ingestion.read_attachment(local_tmp,selected)==text()
    # A selected source can live outside the app project; this entire fixture
    # remains under the test workspace and no sibling is discovered.
    assert ingestion.read_attachment(local_tmp/'app',selected)==text()
    with pytest.raises(ValueError):ingestion.read_attachment(local_tmp,local_tmp/'../outside.log')
    other=local_tmp/'alias.log'
    try:os.link(selected,other)
    except OSError:pytest.skip('Hardlink unavailable')
    with pytest.raises(ValueError):ingestion.read_attachment(local_tmp,other)


def test_specific_matchup_is_prioritized_even_after_large_number_of_other_groups(local_tmp,monkeypatch):
    services=Services(local_tmp)
    groups=[{'archetype':'Invented Family '+str(i),'wins':1,'losses':1,'unknown':0,'n':2} for i in range(70)]
    groups.append({'archetype':'InventedSpecialRival','wins':0,'losses':1,'unknown':0,'n':1})
    services.report={'as_of':'2026-10-26','model_version':'battle-batch-v4','coverage':{'valid':141},
        'outcomes':{'wins':70,'losses':71,'unknown':0},'groups':groups,'own_decks':{'InventedOwnFamily':141}}
    monkeypatch.setattr(services,'search_cards',lambda *a:[])
    value=services.context('Mes défaites contre InventedSpecialRival','aggregates')
    assert value['matchups'][0]['archetype']=='InventedSpecialRival'
    # The named family, then the 15 that beat the owner most; the context tool gives the others (audit A-7).
    assert len(value['matchups'])==16 and value['matchups_not_shown']==55 and 'operation=context' in value['matchups_more']
    assert value['matchup_groups_total']==71 and value['observed_own_decks']['InventedOwnFamily']==141
    assert 'public_decks' not in value


def test_unchanged_duplicate_and_startup_do_not_reanalyze_but_new_content_does(local_tmp,monkeypatch):
    original=battle_batch.batch_analyze;calls=[]
    def analyze(*a,**k):
        calls.append(True);return original(*a,**k)
    monkeypatch.setattr(battle_batch,'batch_analyze',analyze)
    first=ingestion.ingest(local_tmp,text())
    again=ingestion.ingest(local_tmp,text())
    services=Services(local_tmp);services.load(update=True)
    assert len(calls)==1 and again['status']=='DUPLICATE'
    assert services.report['coverage']['valid']==1
    path=next((local_tmp/battle_coach.LOG_DIR).glob('*.log'))
    path.write_text(text('InventedSelf'))
    services.load(update=True)
    assert len(calls)==2 and services.report['outcomes']['wins']==1
    assert first['result']['report']['outcomes']['losses']==1
