"""Synthetic folder trees only. No owner identities, logs or local caches."""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

import pytest

from pokemind import battle_batch as batch, battle_logs as logs, cli, learning_loop

AS_OF = "2026-10-24"
PLAYER = "InventedSelf"


def text(outcome="L", *, language="fr", headers=True):
    start = "Joueur de référence : InventedSelf\n" if language == "fr" else "Reference player: InventedSelf\n"
    if language == "fr":
        return (start + ("Tour de InventedSelf\n" if headers else "") +
            "InventedSelf a placé Creature Alpha en position Active.\n"
            "InventedSelf a joué Invented Tool.\n" + ("Tour de InventedRival\n" if headers else "") +
            "InventedRival a placé Creature Delta sur le Banc.\n"
            "InventedRival a fait évoluer Creature Delta en Creature Omega.\n"
            "InventedRival a pioché Hidden Creature.\n" +
            (("InventedSelf" if outcome == "W" else "InventedRival") + " a gagné.\n" if outcome != "unknown" else ""))
    return (start + ("Turn # 1 - InventedSelf's Turn\n" if headers else "") +
        "InventedSelf played Creature Alpha.\n" + ("Turn # 2 - InventedRival's Turn\n" if headers else "") +
        "InventedRival played Creature Delta.\nInventedRival drew Hidden Creature.\n" +
        (("InventedSelf" if outcome == "W" else "InventedRival") + " wins.\n" if outcome != "unknown" else ""))


@pytest.fixture
def folder(local_tmp, monkeypatch):
    target = local_tmp / "data/local/battle_logs"
    target.mkdir(parents=True)
    db = local_tmp / "data/local/pokemind.sqlite3"
    with closing(sqlite3.connect(db)) as con:
        con.execute("PRAGMA user_version=7")
    monkeypatch.setattr(batch, "public_context", lambda *a: (None, [], {"status": "BLOCKED_PUBLIC_REFERENCE", "references": 0}))
    return local_tmp, target, db


def run(data, **kw):
    root, target, db = data
    return batch.batch_analyze(root, folder=target, player=PLAYER, db=db, as_of=AS_OF, **kw)


@pytest.mark.parametrize("language", ["fr", "en"])
@pytest.mark.parametrize("outcome", ["W", "L", "unknown"])
@pytest.mark.parametrize("headers", [True, False])
def test_explicit_player_outcomes_without_guessed_deck(language, outcome, headers):
    parsed = batch.parse_selected(text(outcome, language=language, headers=headers), PLAYER)
    assert parsed.valid and parsed.outcome == (outcome if outcome != "unknown" else "inconnue")
    record = batch.analyze_record(parsed, None, as_of=AS_OF, match_id="M0001")
    assert record["personal_deck_version"] == "unknown" and not record["exact_opponent_60"]
    assert "Hidden Creature" not in str(record["opponent_cards"])
    assert PLAYER not in str(record["evidence"])


def test_contradictory_damage_actor_is_not_pokemon_owner():
    value = text("W").replace("InventedSelf a gagné.",
        "InventedRival a placé 6 marqueurs de dégâts sur Creature Alpha de InventedSelf.\nInventedSelf a gagné.")
    parsed = batch.parse_selected(value, PLAYER)
    assert parsed.outcome == "W"
    record = batch.analyze_record(parsed, None, as_of=AS_OF, match_id="M0001")
    assert "Creature Alpha" not in [c["name"] for c in record["opponent_cards"]]
    assert any(e["type"] == "damage" and e["confidence"] == "ambiguous_owner" for e in record["evidence"])


def test_authoritative_player_overrides_export_reference_without_flipping_winner():
    value = text("W").replace("Joueur de référence : InventedSelf", "Joueur de référence : InventedRival")
    parsed = batch.parse_selected(value, PLAYER)
    assert parsed.outcome == "W" and parsed.opponent_name == "InventedRival"
    assert any("differs" in warning for warning in parsed.warnings)
    with pytest.raises(ValueError):
        batch.parse_selected(value, "AbsentPlayer")


def test_batch_all_descendants_dedup_refusals_and_readonly_old_db(folder):
    root, target, db = folder
    (target / "a.txt").write_text(text("L"), encoding="utf-8")
    (target / "nested").mkdir()
    (target / "nested/b.LOG").write_bytes(text("L").replace("\n", "\r\n").encode())
    (target / "c.log").write_text(text("W", language="en"), encoding="utf-8")
    (target / "invalid.txt").write_text("not a match", encoding="utf-8")
    (target / "ignored.json").write_text("unselected", encoding="utf-8")
    before = db.read_bytes()
    result = run(folder, apply=True)
    assert result["coverage"]["files_seen"] == 4
    assert result["coverage"]["valid"] == 2 and result["coverage"]["duplicate"] == 1
    assert result["coverage"]["refused_or_malformed"] == 1
    assert result["outcomes"] == {"wins": 1, "losses": 1, "unknown": 0}
    assert result["persistence"]["status"] == "BLOCKED_SCHEMA_NO_MIGRATION" and db.read_bytes() == before
    again = run(folder, apply=True)
    assert again["memory"]["status"] == "ALREADY_PRESENT_IDENTICALLY"
    journal = json.loads((root / result["memory"]["learning"]).read_text(encoding="utf-8"))
    assert learning_loop.validate(journal)
    assert "own_deck_hypothesis" not in journal[0]["payload"]["matches"][0]
    assert journal[-1]["kind"] == "hypothesis_to_test"


def test_concatenated_and_reordered_games_not_blindly_imported():
    with pytest.raises(ValueError, match="CONCATENATED"):
        batch.parse_selected(text("W") + text("L"), PLAYER)


def test_concatenated_file_isolated_and_each_terminal_result_kept(folder):
    _, target, _ = folder
    (target / "combined.txt").write_text(text("W") + text("L"), encoding="utf-8")
    result = run(folder)
    assert result["coverage"]["valid"] == 2 and result["coverage"]["valid_files"] == 1
    assert result["outcomes"] == {"wins": 1, "losses": 1, "unknown": 0}


def test_numbered_turns_can_repeat_for_different_players():
    value = text(language="en").replace("Turn # 2", "Turn # 1")
    assert batch.parse_selected(value, PLAYER).outcome == "L"


def test_compatible_import_uses_observed_bucket_without_attested_version(folder):
    from pokemind.database import initialize_schema
    root, target, db = folder
    with closing(sqlite3.connect(db)) as con:
        con.execute("PRAGMA user_version=0")
        initialize_schema(con)
    (target / "a.txt").write_text(text(), encoding="utf-8")
    first, second = run(folder, apply=True), run(folder, apply=True)
    assert first["persistence"]["imports"][0]["duplicate"] is False
    assert second["persistence"]["imports"][0]["duplicate"] is True
    assert second["memory"]["status"] == "ALREADY_PRESENT_IDENTICALLY"
    with closing(sqlite3.connect(db)) as con:
        assert con.execute("SELECT count(*) FROM battle_logs").fetchone()[0] == 1
        assert con.execute("SELECT count(*) FROM deck_versions").fetchone()[0] == 0
        assert con.execute("SELECT count(*) FROM battle_version_attestations").fetchone()[0] == 0


def test_atomic_import_failure_rolls_back_and_retains_derived_report(folder, monkeypatch):
    from pokemind.database import initialize_schema
    _, target, db = folder
    with closing(sqlite3.connect(db)) as con:
        con.execute("PRAGMA user_version=0")
        initialize_schema(con)
    (target / "a.txt").write_text(text(), encoding="utf-8")
    def fail(*a): raise sqlite3.OperationalError("invented write failure")
    monkeypatch.setattr(logs, "_insert_events", fail)
    result = run(folder, apply=True)
    assert result["outcomes"]["losses"] == 1
    assert result["persistence"]["status"].startswith("PARTIAL_IMPORT_BLOCKED")
    assert result["memory"]["status"] == "SAVED_LOCAL"
    with closing(sqlite3.connect(db)) as con:
        assert con.execute("SELECT count(*) FROM battle_logs").fetchone()[0] == 0


def test_missing_db_not_created_and_derived_memory_saved(folder):
    root, target, _ = folder
    other_root = root / "new"
    other_folder = other_root / "data/local/battle_logs"
    other_folder.mkdir(parents=True)
    (other_folder / "a.txt").write_text(text(), encoding="utf-8")
    db = other_root / "data/local/pokemind.sqlite3"
    result = batch.batch_analyze(other_root, folder=other_folder, player=PLAYER, db=db, as_of=AS_OF, apply=True)
    assert not db.exists() and result["memory"]["status"] == "SAVED_LOCAL"


def test_folder_cap_before_content(folder, monkeypatch):
    root, target, _ = folder
    for name in ("a.txt", "b.txt"):
        (target / name).write_text(text(), encoding="utf-8")
    monkeypatch.setattr(batch, "read_selected", lambda *a: pytest.fail("no content on cap violation"))
    with pytest.raises(ValueError, match="TOTAL_CAP"):
        batch.files_in_folder(root, target, max_files=1)


@pytest.mark.parametrize("fault", ["other_folder", "other_db", "traversal", "ads"])
def test_paths_are_exact_before_any_content(folder, fault):
    root, target, db = folder
    if fault == "other_folder": target = root / "other"
    if fault == "other_db": db = root / "data/local/other.sqlite3"
    if fault == "traversal": target = root / "data/local/../battle_logs"
    if fault == "ads": target = root / "data/local/battle_logs:stream"
    with pytest.raises(ValueError, match="BATCH_"):
        batch.batch_analyze(root, folder=target, player=PLAYER, db=db, as_of=AS_OF)


def test_hardlink_input_rejected(folder):
    root, target, _ = folder
    first = target / "a.txt"
    first.write_text(text(), encoding="utf-8")
    os.link(first, target / "b.txt")
    result = run(folder)
    assert result["coverage"]["valid"] == 0 and result["coverage"]["refusal_reasons"]["unsafe_file"] == 2


def test_cli_environment_explicit_no_root_or_default_db_discovery(folder, monkeypatch, capsys):
    root, target, db = folder
    (target / "a.txt").write_text(text(), encoding="utf-8")
    monkeypatch.chdir(root)
    monkeypatch.setenv("POKEMIND_BATTLE_LOGS_DIR", str(target))
    monkeypatch.setenv("POKEMIND_PLAYER_NAME", PLAYER)
    monkeypatch.setattr(cli, "find_project_root", lambda: pytest.fail("no discovery"))
    assert cli.main(["battle", "batch-intelligence", "--db", str(db), "--as-of", AS_OF, "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["outcomes"]["losses"] == 1 and payload["matches"][0]["personal_deck_version"] == "unknown"


def test_pokemon_signature_priority_beats_common_box_overlap():
    from pokemind.opponent_observer import classify
    refs = [{"archetype": "Dragapult", "names": ["drakloak"]},
            {"archetype": "Basic Box", "names": ["tech a", "tech b"]}]
    observed = [{"normalized_name": name} for name in ("drakloak", "tech a", "tech b")]
    index = {"references": refs, "minimum_matches_by_family": {"Dragapult": 1, "Basic Box": 2},
             "signature_weights_by_family": {"Dragapult": 100, "Basic Box": 1}}
    assert classify(observed, index)["label"] == "Dragapult"


def test_public_provider_label_aliases_do_not_split_one_family():
    known={"Dragapult","Slowking","Absol Audino"}
    assert batch.canonical_family("Dragapult ex",known)=="Dragapult"
    assert batch.canonical_family("Slowking Seek Inspiration",known)=="Slowking"
    assert batch.canonical_family("Mega Absol ex",known)=="Absol Audino"


def test_french_pokemon_owner_use_is_visible_but_attack_is_not_a_card():
    value=text().replace("InventedRival a gagné.","Creature Omega de InventedRival a utilisé Invented Beam.\nInventedRival a gagné.")
    parsed=batch.parse_selected(value,PLAYER)
    event=next(e for e in parsed.events if "Invented Beam" in e.evidence)
    assert event.actor=="InventedRival" and event.card_name=="Creature Omega"
    record=batch.analyze_record(parsed,None,as_of=AS_OF,match_id="M0001")
    assert "Invented Beam" not in [c['name'] for c in record['opponent_cards']]


def test_signature_uses_visible_attacker_before_repeated_engine_ability():
    value=text().replace("InventedRival a gagné.",
        "Creature Engine de InventedRival a utilisé Invented Draw.\n"*5+
        "Creature Omega de InventedRival a utilisé Invented Beam et a infligé 250 dégâts.\nInventedRival a gagné.")
    index={'references':[],'pokemon_names':{'creature engine':'creature engine','creature omega':'creature omega'}}
    record=batch.analyze_record(batch.parse_selected(value,PLAYER),index,as_of=AS_OF,match_id='M0001')
    assert record['opponent']['label']=='Noyau observé : creature omega'


def test_language_aliases_collapse_only_proven_printing(monkeypatch):
    original={('english','TST','1'):{'name':'Invented Scout','set':'TST','number':'1','type':'pokemon','quantity':60}}
    translated={('french','TST','1'):{'name':'Créature inventée','set':'TST','number':'1','type':'pokemon','quantity':60}}
    monkeypatch.setattr(batch.rules,'_resolve_structure_identity',lambda *a,**k:{'ids':['invented-printing']})
    left,missing=batch.printing_map(original,None,{})
    right,_=batch.printing_map(translated,None,{})
    assert not missing and batch.competitive._quantitative_diff({'cards':left},{'cards':right},60)['counts']=={'shared':60,'removed':0,'added':0}
    monkeypatch.setattr(batch.rules,'_resolve_structure_identity',lambda *a,**k:{'ids':[]})
    assert batch.printing_map(translated,None,{})[1]


def test_shared_evolution_engine_does_not_prove_usual_attacker():
    value=text().replace("InventedRival a gagné.",
        "Creature Engine de InventedRival a utilisé Invented Draw.\n"
        "Creature Omega de InventedRival a utilisé Invented Beam et a infligé 250 dégâts.\nInventedRival a gagné.")
    index={'references':[{'archetype':'Invented Family','names':['creature engine']}],
           'minimum_matches_by_family':{'Invented Family':1},
           'primary_names_by_family':{'Invented Family':['creature usual']},
           'pokemon_names':{'creature engine':'creature engine','creature omega':'creature omega'}}
    record=batch.analyze_record(batch.parse_selected(value,PLAYER),index,as_of=AS_OF,match_id='M0001')
    assert record['opponent']['label']=='Noyau observé : creature omega'
    assert record['opponent']['exact_deck_proven'] is False


def test_equal_count_card_order_stable_across_process_hash_seeds():
    program="""
import json
from pokemind.battle_batch import group_matches
cards=[{'name':'Invented '+str(i)} for i in range(12)]
r={'match':'M0001','opponent':{'label':'Invented Family'},'outcome':'losses',
   'opponent_cards':cards,'evidence':[],'max_observed_turn':None,
   'explicit_prize_totals':{'self':None,'opponent':None}}
print(json.dumps(group_matches([r]),sort_keys=True))
"""
    outputs=[]
    for seed in ('1','2'):
        result=subprocess.run([sys.executable,'-B','-c',program],capture_output=True,
            env={**os.environ,'PYTHONHASHSEED':seed,'PYTHONDONTWRITEBYTECODE':'1'},timeout=20)
        assert result.returncode==0 and not result.stderr
        outputs.append(result.stdout)
    assert outputs[0]==outputs[1]


def test_published_variants_preserve_source_and_sixty_copies(monkeypatch,local_tmp):
    def card(name,quantity):
        return {'name':name,'quantity':quantity,'type':'energy','set':'TST','number':'1'}
    groups={
        'base':{'quality':[],'occurrences':[{'archetype':'Invented Family','selector':'invented:1'}],
                'cards':{('common',):card('Invented Basic',58),('old',):card('Invented Old',2)}},
        'other':{'quality':[],'occurrences':[{'archetype':'Invented Family','selector':'invented:2'}],
                'cards':{('common',):card('Invented Basic',58),('new',):card('Invented New',2)}}}
    monkeypatch.setattr(batch.competitive,'_advisor_snapshot',lambda *a:(groups,None,None,None))
    source={'observations':[{'list_url':'https://example.invalid/invented-list'}]}
    monkeypatch.setattr(batch.deck_knowledge,'knowledge_show',lambda *a,**k:{
        'export':{'text':'invented export60','total_cards':60},'source_list':source,'preflight':{'status':'unknown'}})
    variants=batch.published_variants(local_tmp,[local_tmp/'public1',local_tmp/'public2'],'Invented Family',AS_OF)
    assert len(variants)==1
    variant=variants[0]
    assert variant['diff']['counts']=={'shared':58,'removed':2,'added':2}
    assert variant['source']==source and variant['export']['total_cards']==60
    assert variant['legality']==variant['live']=='unknown'
    assert variant['kind']=='published_same_family_variant_not_personal_swap'
    assert not batch.published_variants(local_tmp,[], 'Noyau observé : unknown',AS_OF)


def test_catalog_evolution_and_french_aliases_define_same_signature(local_tmp, monkeypatch):
    from pokemind import catalog_batch_store, set_code_aliases, batch_public_research
    pair = [local_tmp / p for p in batch.SCOPED_PUBLIC_CACHES]
    for path in pair:
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(path)) as con: con.execute("PRAGMA user_version=13")
    with closing(sqlite3.connect(pair[1])) as con, con:
        con.executescript("CREATE TABLE catalog_printings(tcgdex_id,category); CREATE TABLE catalog_translations(printing_id,language,name,status,retrieved_at,payload_sha256);")
        for pid, en, fr in (("drag", "Dragapult ex", "Lanssorien-ex"), ("drak", "Drakloak", "Dispareptil"), ("dree", "Dreepy", "Fantyrm")):
            con.execute("INSERT INTO catalog_printings VALUES (?, 'Pokemon')", (pid,))
            for lang, name in (("en", en), ("fr", fr)):
                con.execute("INSERT INTO catalog_translations VALUES (?,?,?,'present',?,'invented')", (pid,lang,name,AS_OF))
    monkeypatch.setattr(batch.deck_library, "reference_index", lambda *a, **k: {"references": [
        {"archetype": "Dragapult", "selector": "invented:1", "names": ["dragapult ex", "drakloak", "dreepy"]}]})
    monkeypatch.setattr(batch_public_research, "load_public_research", lambda *a: None)
    monkeypatch.setattr(catalog_batch_store, "verified_payload", lambda con, kind, pid, lang, sha: {"evolveFrom": {"drag":"Drakloak","drak":"Dreepy"}.get(pid)})
    monkeypatch.setattr(set_code_aliases, "payload_source", lambda *a: {"source_url":"https://example.invalid/invented"})
    index,_,_=batch.public_context(local_tmp,AS_OF)
    assert {"fantyrm","dispareptil","lanssorien-ex"} <= set(index["references"][0]["names"])


def test_prize_trace_is_explicit_not_inferred_from_missing_events():
    value = text().replace("InventedRival a gagné.",
        "InventedSelf a pris 2 cartes Récompense.\nInventedRival a pris une carte Récompense.\n"
        "Creature Alpha de InventedSelf a été mis K.O.\nInventedRival a gagné.")
    parsed=batch.parse_selected(value,PLAYER)
    record=batch.analyze_record(parsed,None,as_of=AS_OF,match_id="M0001")
    assert record["explicit_prize_totals"] == {"self":2,"opponent":1}
    assert any(e["type"]=="knockout" and e["role"]=="unknown" for e in record["evidence"])
    missing=batch.analyze_record(batch.parse_selected(text(),PLAYER),None,as_of=AS_OF,match_id="M0002")
    assert missing["explicit_prize_totals"] == {"self":None,"opponent":None}


@pytest.mark.parametrize("json_mode", [False, True])
def test_real_batch_cli_cp1252_to_utf8_and_local_persistence(folder, json_mode):
    root,target,db=folder
    log=target/'invented-unicode.txt'
    log.write_text(text(),encoding='utf-8')
    before=db.read_bytes(),log.read_bytes()
    env={**os.environ,'POKEMIND_BATTLE_LOGS_DIR':str(target),'POKEMIND_PLAYER_NAME':PLAYER,
         'PYTHONIOENCODING':'cp1252','PYTHONDONTWRITEBYTECODE':'1'}
    args=[sys.executable,'-B','-m','pokemind','battle','batch-intelligence','--db',str(db),'--as-of',AS_OF,'--apply']
    if json_mode:args.append('--json')
    result=subprocess.run(args,cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=40)
    assert result.returncode==0 and not result.stderr
    output=result.stdout.decode('utf-8',errors='strict')
    assert str(root) not in output and PLAYER not in output
    if json_mode:
        payload=json.loads(output)
        assert payload['outcomes']['losses']==1 and payload['memory']['status']=='SAVED_LOCAL'
    else:
        assert 'défaites 1' in output and 'BLOCKED_SCHEMA_NO_MIGRATION' in output and 'SAVED_LOCAL' in output
    assert before==(db.read_bytes(),log.read_bytes())
