"""Invented DBs and saved reports only; no owner data or migrations."""
from __future__ import annotations

import copy
import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest

from pokemind import battle_batch, battle_logs, cli, database, legacy_bridge as bridge

AS_OF = '2026-10-25'
FIXTURE = Path(__file__).parent / 'fixtures/legacy_schema7.sql'


def make_db(root, version=7, sql=None):
    path = root / 'data/local/pokemind.sqlite3'
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as con:
        if version == 13:
            database.initialize_schema(con)  # New empty fixture, never an upgrade.
        else:
            con.executescript(sql if sql is not None else FIXTURE.read_text(encoding='utf-8'))
        con.commit()
    return path


def snapshot(version='battle-batch-v4', outcome='losses'):
    match = {'match':'M0001','outcome':outcome,'opponent':{'label':'Invented Engine'},
        'opponent_hypothesis':{'label':'Invented Engine'},'own_deck_hypothesis':{'label':'Invented Own'},
        'opponent_cards':[{'name':'Invented Omega'}],'own_cards':[],
        'max_observed_turn':3,'personal_deck_version':'unknown','battle_date':'unknown',
        'explicit_prize_totals':{'self':None,'opponent':None},'exact_opponent_60':False,
        'warnings':[],'evidence':[{'sequence':1,'turn':3,'role':'opponent','type':'use',
            'card':'Invented Omega','text':'[adversaire] utilise une attaque inventée sur [joueur].',
            'confidence':'low','target':None}],
        'causal_loss_reason':'unknown','source_relative':'invented-private-name.log',
        'semantic_identity':'invented-private-digest','encoding':'utf-8','source_segment':1}
    result = {'model_version':version,'as_of':AS_OF,'scope':'OWNER_SELECTED_FOLDER_LOCAL_ONLY',
        'coverage':{'files_seen':1,'valid':1,'duplicate':0,'refused_or_malformed':0,
                    'unknown_archetype':0,'signature_only_archetype':1},
        'outcomes':{k:int(k==outcome) for k in ('wins','losses','unknown')},
        'own_decks':{'Invented Own':1},'matches':[match],'groups':battle_batch.group_matches([match]),
        'recommendations':[],'published_same_family_variants':[],
        'public_reference':{'status':'unknown'},'public_refresh':None,'fresh_public_decks':[],
        'registered_deck_references':[{'deck_id':'invented-private-deck','version':1,
            'scope':'registered_reference_not_attested_played_version','export':'invented-private-export'}],
        'persistence':{'status':'BLOCKED_SCHEMA_NO_MIGRATION','schema_version':7,
                       'expected_schema':13,'can_import':False},
        'release_status':'NOT_RELEASE_READY','limits':['No causal proof; legality unknown.']}
    return result


def saved(root, value=None):
    value = value or snapshot()
    result = battle_batch.save_memory(root, value, as_of=AS_OF)
    return root / result['report'], root / result['learning']


def named(root, raw, name='invented.json'):
    target=root/'data/local/battle-intelligence'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(raw if isinstance(raw,str) else json.dumps(raw),encoding='utf-8')
    return target


def test_schema7_is_historical_full_schema_not_version_only(local_tmp,monkeypatch):
    path=make_db(local_tmp);before=path.read_bytes()
    monkeypatch.setattr(database,'initialize_schema',lambda *a:pytest.fail('no migration'))
    monkeypatch.setattr(database,'_backup_before_migration',lambda *a:pytest.fail('no backup'))
    result=bridge.legacy_plan(local_tmp,db=path)
    assert result['status']=='LEGACY_UPGRADE_REQUIRED'
    assert result['db_import_status']=='DB_IMPORT_BLOCKED_SCHEMA_7'
    assert result['integrity_ok'] and result['foreign_keys_ok']
    assert result['missing_tables']==result['column_contract_mismatches']==[]
    assert len(result['post7_missing_tables'])==14 and len(result['future_steps'])==6
    assert not result['migration_executed'] and not result['backup_created'] and not result['import_performed']
    assert path.read_bytes()==before


def test_current_schema_contract_matches_actual_database_module(local_tmp):
    path=make_db(local_tmp,13);before=path.read_bytes()
    result=bridge.legacy_plan(local_tmp,db=path)
    assert result['status']=='CURRENT_BATTLE_SCHEMA_COMPATIBLE'
    assert result['post7_missing_tables']==[] and result['owner_attestation_index_present']
    assert result['training_contract_current'] and result['registered_exact60_count']==0
    assert result['played_version'].startswith('unknown') and path.read_bytes()==before


def test_future_application_schema_requires_new_contract(local_tmp,monkeypatch):
    monkeypatch.setattr(bridge,'SCHEMA_VERSION',14)
    monkeypatch.setattr(bridge.sqlite3,'connect',lambda *a,**k:pytest.fail('future contract must stop first'))
    with pytest.raises(bridge.BridgeError,match='CONTRACT_UPDATE_REQUIRED'):
        bridge.legacy_plan(local_tmp,db=local_tmp/'data/local/pokemind.sqlite3')


def test_exact60_reference_never_becomes_played_attestation(local_tmp):
    path=make_db(local_tmp)
    with closing(sqlite3.connect(path)) as con,con:
        con.execute("INSERT INTO deck_versions(deck_id,version_number,imported_at,approved_at,effective_from,parser_version,source_kind,export_sha256,list_sha256,total_cards,entry_count,exact_confirmed,sections_json,coverage_json) VALUES ('invented',1,?,?,?,'invented','file','invented','invented',60,1,1,'{}','{}')",(AS_OF,AS_OF,AS_OF))
        con.execute("INSERT INTO deck_version_cards(deck_version_id,ordinal,source_line,card_type,quantity,card_name,normalized_line) VALUES(1,1,1,'energy',60,'Invented Energy','60 Invented Energy')")
    result=bridge.legacy_plan(local_tmp,db=path)
    assert result['registered_exact60_count']==1 and not result['owner_attestation_index_present']
    assert result['played_version'].startswith('unknown')


@pytest.mark.parametrize('version',[0,7,13,99])
def test_user_version_alone_is_not_compatibility(local_tmp,version):
    path=local_tmp/'data/local/pokemind.sqlite3';path.parent.mkdir(parents=True)
    with closing(sqlite3.connect(path)) as con:con.execute('PRAGMA user_version='+str(version))
    result=bridge.legacy_plan(local_tmp,db=path)
    assert result['status']=='BLOCKED_SCHEMA_OR_INTEGRITY' and result['missing_tables']


def test_foreign_key_shape_drift_is_blocked(local_tmp):
    sql=FIXTURE.read_text(encoding='utf-8').replace('REFERENCES deck_versions(id) ON DELETE RESTRICT',
                                                   'REFERENCES deck_versions(id) ON DELETE CASCADE')
    result=bridge.legacy_plan(local_tmp,db=make_db(local_tmp,sql=sql))
    assert result['status']=='BLOCKED_SCHEMA_OR_INTEGRITY'
    assert 'battle_deck_versions' in result['foreign_key_contract_mismatches']


def test_foreign_key_violation_does_not_echo_rows(local_tmp):
    path=make_db(local_tmp)
    with closing(sqlite3.connect(path)) as con,con:
        con.execute("INSERT INTO battle_events(battle_id,sequence,actor_role,event_type,evidence,confidence) VALUES(9999,1,'unknown','use','invented secret','low')")
    result=bridge.legacy_plan(local_tmp,db=path)
    assert not result['foreign_keys_ok'] and result['status']=='BLOCKED_SCHEMA_OR_INTEGRITY'
    assert 'invented secret' not in str(result) and '9999' not in str(result)


@pytest.mark.parametrize('suffix',['-wal','-shm','-journal'])
def test_sidecars_refused_without_sqlite_open(local_tmp,monkeypatch,suffix):
    path=make_db(local_tmp);sidecar=path.with_name(path.name+suffix);sidecar.write_bytes(b'invented')
    monkeypatch.setattr(bridge.sqlite3,'connect',lambda *a,**k:pytest.fail('sidecar must stop before SQLite'))
    with pytest.raises(bridge.BridgeError,match='SIDECAR'):bridge.legacy_plan(local_tmp,db=path)


def test_locked_and_corrupt_sqlite_errors_neutral(local_tmp):
    path=make_db(local_tmp);before=path.read_bytes()
    with closing(sqlite3.connect(path)) as con:
        con.execute('BEGIN EXCLUSIVE')
        with pytest.raises(bridge.BridgeError,match='DATABASE_UNAVAILABLE'):bridge.legacy_plan(local_tmp,db=path)
        con.rollback()
    assert path.read_bytes()==before
    path.write_bytes(b'invented corrupted SQLite')
    with pytest.raises(bridge.BridgeError,match='HEADER'):bridge.legacy_plan(local_tmp,db=path)


def test_wal_header_missing_db_and_outside_db_never_opened(local_tmp,monkeypatch):
    path=local_tmp/'data/local/pokemind.sqlite3'
    with pytest.raises(bridge.BridgeError):bridge.legacy_plan(local_tmp,db=path)
    assert not path.exists()
    with pytest.raises(bridge.BridgeError,match='DB_PATH_REFUSED'):
        bridge.legacy_plan(local_tmp,db=local_tmp/'invented-other.sqlite3')
    path=make_db(local_tmp);raw=bytearray(path.read_bytes());raw[18:20]=b'\x02\x02';path.write_bytes(raw)
    monkeypatch.setattr(bridge.sqlite3,'connect',lambda *a,**k:pytest.fail('WAL refusal before SQLite'))
    with pytest.raises(bridge.BridgeError,match='JOURNAL_MODE'):bridge.legacy_plan(local_tmp,db=path)


@pytest.mark.parametrize('schema',[7,13])
def test_ambiguity_storage_uses_existing_low_confidence_contract(local_tmp,schema):
    path=make_db(local_tmp,schema)
    parsed=battle_logs.parse_battle_log('Reference player: InventedSelf\nTurn # 1 - InventedSelf\n'
        'InventedSelf played Invented Energy.\nInventedOther a placé 6 marqueurs de dégâts sur Invented Alpha de InventedSelf.\n'
        'Invented Alpha de InventedSelf a été mis K.O.\nInventedOther wins.\n',reference_player='InventedSelf')
    assert {e.confidence for e in parsed.events}>={'ambiguous_owner','owner_unknown'}
    with closing(sqlite3.connect(path)) as con,con:
        con.execute("INSERT INTO battle_logs(source_sha256,imported_at,parser_version,source_kind,outcome,valid,recognized_events,warnings_json) VALUES('invented',?,'invented','file','L',1,3,'[]')",(AS_OF,))
        battle_logs._insert_events(con,1,parsed)
        rows=con.execute("SELECT confidence,card_name FROM battle_events WHERE event_type IN ('damage','knockout')").fetchall()
        assert rows==[('low',None),('low',None)]
        assert con.execute('PRAGMA user_version').fetchone()[0]==schema


def test_read_canonical_snapshot_and_learning_without_reanalysis(local_tmp,monkeypatch):
    path,journal=saved(local_tmp);before=path.read_bytes(),journal.read_bytes()
    monkeypatch.setattr(battle_batch,'batch_analyze',lambda *a,**k:pytest.fail('no analysis'))
    monkeypatch.setattr(bridge.sqlite3,'connect',lambda *a,**k:pytest.fail('no DB'))
    result=bridge.saved_report(local_tmp,report=path,learning=journal)
    assert result['snapshot_selection']=='EXPLICIT_CANONICAL'
    assert result['db_import_status']=='DB_IMPORT_BLOCKED_SCHEMA_7'
    assert result['report']['outcomes']['losses']==1 and result['learning']['facts_preserved']
    assert all(not result[k] for k in ('reanalysis_performed','database_opened','network_used','writes_performed'))
    assert before==(path.read_bytes(),journal.read_bytes())
    assert 'invented-private' not in json.dumps(result)


def test_old_and_corrected_paths_are_independent_idempotent_snapshots(local_tmp,monkeypatch):
    old,_=saved(local_tmp,snapshot('battle-batch-v3'))
    corrected,_=saved(local_tmp,snapshot('battle-batch-v4','wins'))
    monkeypatch.setattr(os,'scandir',lambda *a:pytest.fail('no scans'))
    old_read=bridge.saved_report(local_tmp,report=old)
    new_read=bridge.saved_report(local_tmp,report=corrected)
    assert old_read['report']['outcomes']['losses']==1 and new_read['report']['outcomes']['wins']==1
    assert new_read==bridge.saved_report(local_tmp,report=corrected)
    assert old_read==bridge.saved_report(local_tmp,report=old)


def test_named_alias_warns_it_is_not_latest_and_v2_defaults(local_tmp):
    value=snapshot('battle-batch-v2');del value['published_same_family_variants']
    path=named(local_tmp,value)
    result=bridge.saved_report(local_tmp,report=path)
    assert result['snapshot_selection']=='EXPLICIT_NAMED_SNAPSHOT_NOT_LATEST'
    assert result['report']['published_same_family_variants']==[]


def test_stored_public_export_is_checked_without_catalog_or_network(local_tmp):
    value=snapshot()
    export='Pokémon: 0\n\nTrainer: 0\n\nEnergy: 60\n60 Basic Psychic Energy SVE 5\n\nTotal Cards: 60\n'
    value['fresh_public_decks']=[{'export':export,'archetype':'Invented Public','source_url':'https://example.invalid/invented',
                                'retrieved_at':AS_OF,'total_cards':60}]
    assert 'Total Cards: 60' in bridge.saved_report(local_tmp,report=named(local_tmp,value))['text']
    value['fresh_public_decks'][0]['export']=export.replace('60 Basic','59 Basic')
    with pytest.raises(bridge.BridgeError,match='SNAPSHOT_SCHEMA'):
        bridge.saved_report(local_tmp,report=named(local_tmp,value,name='invented-bad.json'))


@pytest.mark.parametrize('kind',['missing','future','scope','counts','bool','groups','date'])
def test_invalid_snapshot_schema_neutral(local_tmp,kind):
    value=snapshot()
    if kind=='missing':del value['matches']
    if kind=='future':value['model_version']='battle-batch-v99'
    if kind=='scope':value['scope']='other'
    if kind=='counts':value['outcomes']['wins']=7
    if kind=='bool':value['outcomes']['losses']=True
    if kind=='groups':value['groups'][0]['matches']=[]
    if kind=='date':value['as_of']='2026-02-30'
    with pytest.raises(bridge.BridgeError,match='SNAPSHOT_SCHEMA'):bridge.saved_report(local_tmp,report=named(local_tmp,value))


@pytest.mark.parametrize('raw',['{"a":1,"a":2}','{"a":NaN}','{"a":1e999}','[1,2','['*80+'1'+']'*80])
def test_json_failures_neutral_and_bounded(local_tmp,raw):
    with pytest.raises(bridge.BridgeError):bridge.saved_report(local_tmp,report=named(local_tmp,raw))


def test_size_cap_before_open(local_tmp,monkeypatch):
    path=named(local_tmp,snapshot());monkeypatch.setattr(bridge,'MAX_REPORT_BYTES',10)
    monkeypatch.setattr(Path,'open',lambda *a,**k:pytest.fail('cap before content'))
    with pytest.raises(bridge.BridgeError,match='SIZE_CAP'):bridge.saved_report(local_tmp,report=path)


def test_changed_source_is_refused_without_writing(local_tmp,monkeypatch):
    path,_=saved(local_tmp);before=path.read_bytes();original=bridge._stamp;calls=0
    def stamp(selected):
        nonlocal calls
        calls+=1;value=original(selected)
        return (*value[:3],value[3]+1) if calls>1 else value
    monkeypatch.setattr(bridge,'_stamp',stamp)
    with pytest.raises(bridge.BridgeError,match='SOURCE_CHANGED'):bridge.saved_report(local_tmp,report=path)
    assert path.read_bytes()==before


def test_none_is_not_a_default_database_or_report(local_tmp):
    with pytest.raises(bridge.BridgeError,match='EXPLICIT_PATH_REQUIRED'):bridge.legacy_plan(local_tmp,db=None)
    with pytest.raises(bridge.BridgeError,match='EXPLICIT_PATH_REQUIRED'):bridge.saved_report(local_tmp,report=None)


def test_digest_mismatch_and_learning_pair_conflict(local_tmp):
    path,journal=saved(local_tmp)
    value=json.loads(path.read_text(encoding='utf-8'));value['own_decks']={'Changed':1};path.write_text(json.dumps(value),encoding='utf-8')
    with pytest.raises(bridge.BridgeError,match='DIGEST_MISMATCH'):bridge.saved_report(local_tmp,report=path)
    other=named(local_tmp,[],name='other.learning.json')
    with pytest.raises(bridge.BridgeError,match='PATH_REFUSED'):bridge.saved_report(local_tmp,report=other)


def test_learning_pair_and_immutable_chain_validated(local_tmp):
    path,journal=saved(local_tmp)
    other=named(local_tmp,[],name='other.learning.json')
    with pytest.raises(bridge.BridgeError,match='PAIR_MISMATCH'):
        bridge.saved_report(local_tmp,report=path,learning=other)
    data=json.loads(journal.read_text(encoding='utf-8'));data[-1]['digest']='invented-tamper'
    journal.write_text(json.dumps(data),encoding='utf-8')
    with pytest.raises(bridge.BridgeError):bridge.saved_report(local_tmp,report=path,learning=journal)


def test_readonly_repeat_schema_and_reports_preserves_all_bytes(local_tmp):
    db=make_db(local_tmp);path,journal=saved(local_tmp)
    before={p:p.read_bytes() for p in (db,path,journal)}
    first=bridge.legacy_plan(local_tmp,db=db)
    assert first==bridge.legacy_plan(local_tmp,db=db)
    saved_result=bridge.saved_report(local_tmp,report=path,learning=journal)
    assert saved_result==bridge.saved_report(local_tmp,report=path,learning=journal)
    assert before=={p:p.read_bytes() for p in before}


def test_untrusted_display_escapes_html_controls_paths_and_private_metadata(local_tmp):
    value=snapshot();value['own_decks']={'<script>invented</script>\x1b[31m':1}
    value['matches'][0]['evidence'][0]['text']='\x1b]52;c;invented\x07 <img src=x> \u202e C:\\private\\invented.txt'
    result=bridge.saved_report(local_tmp,report=named(local_tmp,value))
    output=json.dumps(result,ensure_ascii=False)
    assert '<script>' not in result['text'] and '&lt;script&gt;' in result['text']
    assert '\x1b' not in result['text'] and '\u202e' not in result['text'] and '\x07' not in result['text']
    assert 'C:\\private' not in result['text'] and 'invented-private' not in output


@pytest.mark.parametrize('which',['outside','traversal','ads','learning','missing'])
def test_report_paths_refused(local_tmp,which):
    parent=local_tmp/'data/local/battle-intelligence'
    path={'outside':local_tmp/'other.json','traversal':parent/'..'/'other.json','ads':parent/'a.json:stream',
          'learning':parent/'x.learning.json','missing':parent/'absent.json'}[which]
    with pytest.raises(bridge.BridgeError):bridge.saved_report(local_tmp,report=path)


def test_hardlinks_and_symlinks_refused(local_tmp):
    path,_=saved(local_tmp);linked=path.with_name('invented-link.json');os.link(path,linked)
    with pytest.raises(bridge.BridgeError,match='UNSAFE'):bridge.saved_report(local_tmp,report=path)
    link=path.with_name('invented-symlink.json')
    try:os.symlink(path,link)
    except OSError:return
    with pytest.raises(bridge.BridgeError,match='UNSAFE'):bridge.saved_report(local_tmp,report=link)


@pytest.mark.parametrize('command',['batch-report','legacy-plan'])
@pytest.mark.parametrize('json_mode',[False,True])
def test_cli_utf8_readonly_audit_guard(local_tmp,command,json_mode):
    path,journal=saved(local_tmp);db=make_db(local_tmp)
    before={p:p.read_bytes() for p in (path,journal,db)}
    args=['battle',command,'--report' if command=='batch-report' else '--db',str(path if command=='batch-report' else db)]
    if json_mode:args.append('--json')
    program='''
import sys,os
from pathlib import Path
from pokemind import cli,legacy_bridge,battle_batch,battle_logs,database
selected=Path(sys.argv[4]).absolute()
project=Path(cli.__file__).parents[2]
def forbidden(*a,**k):raise AssertionError('UNEXPECTED_OPERATION')
cli.find_project_root=forbidden
database.initialize_schema=database.connect_writable=database._backup_before_migration=forbidden
battle_batch.batch_analyze=battle_batch.files_in_folder=battle_logs.import_battle_log=forbidden
def guard(event,args):
 if event.startswith('socket.') or event in {'os.listdir','os.scandir','os.remove','os.rename','os.rmdir'}:forbidden()
 if event=='open' and not isinstance(args[0],int):
  if args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):forbidden()
  opened=Path(args[0]).absolute()
  if opened.is_relative_to(project/'data/local') and opened!=selected:forbidden()
 if event=='sqlite3.connect':
  if sys.argv[2]=='batch-report' or str(args[0])!=selected.as_uri()+'?mode=ro':forbidden()
sys.addaudithook(guard)
raise SystemExit(cli.main(sys.argv[1:]))
'''
    env={**os.environ,'PYTHONIOENCODING':'cp1252','PYTHONDONTWRITEBYTECODE':'1','POKEMIND_ROOT':'invented-do-not-use',
         'POKEMIND_BATTLE_LOGS_DIR':'invented-do-not-use','POKEMIND_PLAYER_NAME':'invented-do-not-use'}
    completed=subprocess.run([sys.executable,'-B','-c',program,*args],cwd=local_tmp,env=env,capture_output=True,timeout=30)
    assert completed.returncode==0 and not completed.stderr
    output=completed.stdout.decode('utf-8',errors='strict')
    assert str(local_tmp) not in output and 'DB_IMPORT_BLOCKED_SCHEMA_7' in output
    if json_mode:assert json.loads(output)['ok']
    assert before=={p:p.read_bytes() for p in before}


def test_cli_neutral_error_and_explicit_arguments_only(local_tmp,monkeypatch,capsys):
    monkeypatch.chdir(local_tmp)
    assert cli.main(['battle','batch-report','--report','invented-sensitive.json','--json'])==2
    payload=json.loads(capsys.readouterr().out)
    assert not payload['ok'] and 'invented-sensitive' not in json.dumps(payload)
    with pytest.raises(SystemExit):cli.main(['battle','legacy-plan'])
    with pytest.raises(SystemExit):cli.main(['battle','batch-report','--report','anything','--apply'])
