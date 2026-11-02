"""Invented public pages and matches only; no real corpus copied into Git."""
from __future__ import annotations

import copy
import json
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path

import pytest

from pokemind import cli, competitive, counter_deck as counter, learning_loop as loop
from pokemind.learning_simulation import simulate, human_simulation
from pokemind.decks import parse_deck_export
from test_competitive_advisor import AS_OF, tree_bytes
from test_deck_knowledge import enriched
from test_public_deck_preflight import forbid_all


EVIDENCE = {"scope": "SYNTHETIC_COUNTER_DECK_LEARNING_ONLY", "published_options": 4, "cards_per_export": 60,
    "retained_games": 6, "duplicate_excluded": 1, "fictional_versions": 2,
    "before_v1_losses": 2, "before_v1_unknown": 1, "after_v2_wins": 1, "after_v2_losses": 1,
    "ambiguous_unattested_games": 1, "append_only_idempotent_reversible": True,
    "proxy_not_exact": True, "no_causal_improvement": True, "cache_unchanged": True,
    "network_forbidden": True, "real_personal_records_opened": False, "real_public_cache_verified": False}


def plan(root, db, ref, **kw):
    return counter.counter_plan(root, db, ref, as_of=kw.pop("as_of", AS_OF),
        target=kw.pop("target", "Hydrapple"), use_set_aliases=True, **kw)


def test_complete_invented_cycle_and_evidence(local_tmp, monkeypatch, record_testsuite_property, capsys):
    db, ref = enriched(local_tmp)
    before = tree_bytes(db.parent), tree_bytes(ref.parent)
    forbid_all(monkeypatch)
    original_connect = sqlite3.connect
    allowed_ro = {p.resolve().as_uri() + "?mode=ro" for p in (db, ref)}
    def selected_only(database, *args, **kwargs):
        if str(database) not in allowed_ro:
            if kwargs.get("uri"):
                assert "synthetic-learning-" in str(database) and str(database).endswith("?mode=ro")
            else:
                path = Path(database).absolute()
                assert path.parent.name.startswith("synthetic-learning-")
                assert path.is_relative_to(local_tmp.absolute() / "data/local")
        return original_connect(database, *args, **kwargs)
    monkeypatch.setattr(sqlite3, "connect", selected_only)
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: pytest.fail("no client/OS subprocess"))
    result = simulate(local_tmp, db, ref, as_of=AS_OF, target="Hydrapple", use_set_aliases=True)
    assert result["status"] == "SYNTHETIC_LEARNING_CYCLE_PASSED"
    assert result["temporary_workspace_removed"] and result["exact_duplicate_idempotent"]
    assert not list((local_tmp / "data/local").glob("synthetic-learning-*"))
    assert result["fictional_deck_versions"] == 2
    assert result["before"]["outcomes"] == {"wins": 0, "losses": 2, "unknown": 1}
    assert result["after"]["outcomes"] == {"wins": 1, "losses": 4, "unknown": 1}
    assert result["after"]["sample_review"]["probable_duplicates_excluded"] == 1
    v2 = next(r for r in result["after"]["groups"] if r["version"] == 2)
    assert v2["wins"] == v2["losses"] == 1 and v2["n"] == 2
    assert next(r for r in result["after"]["groups"] if r["version"] is None)["games"] == 1
    assert all(r["observed_win_ratio"] is None for r in result["after"]["groups"])
    assert not result["delta"]["improvement_demonstrated"]
    journal = result["journal"]
    assert loop.validate(journal)
    assert {r["kind"] for r in journal} == loop.KINDS
    assert next(r for r in journal if r["id"] == "loss-event")["payload"]["observer"]["exact_confirmed_60"] is None
    event = next(r for r in journal if r["id"] == "loss-event")["payload"]["observer"]
    assert event["classification"]["label"] == "Hydrapple"
    assert event["classification"]["basis"] == "hypothesized"
    assert event["public_reference_proxy"][0]["is_exact_opponent_deck"] is False
    assert all(c["minimum_quantity"] == 1 for c in event["observed_partial"]["cards"])
    assert loop.append_record(journal, record_id="rejection", kind="rejected", recorded_at=AS_OF,
        payload=journal[-1]["payload"], refs=journal[-1]["refs"], revises="causal-claim") == journal
    ids = {r["id"] for r in result["current_view"]["current"]}
    assert "reopened" in ids and "question" not in ids and "rejection" in ids
    for option in result["plan"]["alternatives"]:
        assert parse_deck_export(option["export"]["text"]).total_cards == 60
        assert all(v == 0 for v in option["construction_changes"]["omitted_identities"].values())
        assert option["test_plan"]["causal_effect"] == "unknown"
        assert option["uncertainty"]["live_availability"] == "unknown"
    assert len(result["plan"]["alternatives"]) == 4 and result["plan"]["adaptation"]["export"] is None
    assert (tree_bytes(db.parent), tree_bytes(ref.parent)) == before
    assert not result["future_import"]["real_import_authorized_by_this_feature"]
    human_simulation(result)
    output = capsys.readouterr().out
    assert "SIMULATION" in output and "60/60" in output and "n=2" in output and "Aucun progrès" in output
    record_testsuite_property("public_counter_learning_reproduction", json.dumps(EVIDENCE))


@pytest.mark.parametrize("command", ["counter-plan", "learning-simulate"])
def test_positive_cli_json_and_human_no_default_selection(local_tmp, monkeypatch, capsys, command):
    db, ref = enriched(local_tmp)
    forbid_all(monkeypatch)
    monkeypatch.setattr(cli, "find_project_root", lambda: local_tmp)
    argv = ["meta", command, "--db", str(db), "--reference-db", str(ref), "--target", "Hydrapple",
            "--as-of", AS_OF, "--set-aliases"]
    assert cli.main(argv + ["--json"]) == 0
    value = json.loads(capsys.readouterr().out)
    assert value["ok"] and not value["network_used"] and not value["owner_database_opened"]
    assert cli.main(argv) == 0
    text = capsys.readouterr().out
    assert "60/60" in text and "Sources" in text and "unknown" in text


@pytest.mark.parametrize("options", [1, 2, 3, 4])
def test_exact_options_copy_diffs_and_sourced_target(local_tmp, monkeypatch, options):
    db, ref = enriched(local_tmp)
    before = tree_bytes(local_tmp)
    forbid_all(monkeypatch)
    result = plan(local_tmp, db, ref, options=options)
    assert len(result["alternatives"]) == options
    assert result["target"]["mechanics"] and not result["target"]["is_exact_opponent_deck"]
    for alt in result["alternatives"]:
        diff = alt["construction_changes"]
        assert diff["counts"]["added"] == sum(r["quantity"] for r in diff["added"])
        assert diff["counts"]["shared"] + diff["counts"]["removed"] == 60
        assert diff["counts"]["removed"] == diff["counts"]["added"]
        assert sum(alt["structure"]["published_copies"].values()) == 60
        assert all(q["support"] for q in alt["conditional_questions"])
        assert all(m["text"]["dated_provenance"]["as_of"] == AS_OF for m in alt["mechanics"])
        assert alt["ko_lines"]["status"] == "unknown"
    basic = next((o for o in result["alternatives"] if "Basic Box" in o["archetypes"]), None)
    if basic:
        assert basic["construction_changes"]["counts"] == {"shared": 59, "removed": 1, "added": 1}
    assert tree_bytes(local_tmp) == before


@pytest.mark.parametrize("fault", ["missing_text", "stale", "future", "wrong_name", "hash"])
def test_missing_target_or_native_proof_does_not_invent_mechanics(local_tmp, monkeypatch, fault):
    db, ref = enriched(local_tmp)
    with closing(sqlite3.connect(ref)) as con, con:
        if fault == "missing_text": con.execute("DELETE FROM catalog_detail_payloads WHERE kind='cards'")
        if fault == "stale": con.execute("UPDATE catalog_printings SET detail_stale_en=1,detail_stale_fr=1")
        if fault == "future": con.execute("UPDATE catalog_translations SET retrieved_at='2099-01-01'")
        if fault == "wrong_name": con.execute("UPDATE catalog_translations SET name='Invented wrong name'")
        if fault == "hash": con.execute("UPDATE catalog_translations SET payload_sha256=?", ("0" * 64,))
    forbid_all(monkeypatch)
    result = plan(local_tmp, db, ref)
    assert not result["target"]["mechanics"] and result["target"]["missing_evidence"]
    assert all(not r["mechanics"] and not r["conditional_questions"] for r in result["alternatives"])
    assert "plan_hypothesis" not in json.dumps(result)  # No inherited name-based strategy guess.
    assert result["matchup_advantage"] == "unknown" and result["predicted_winrate"] is None


def test_unknown_archetype_is_an_explicit_question_not_a_counter(local_tmp):
    db, ref = enriched(local_tmp)
    result = plan(local_tmp, db, ref, target="Unknown Public Family")
    assert result["target"]["public_reference_proxy"] is None
    assert result["target"]["missing_evidence"] == ["DATED_TARGET_TEXT_MISSING"]


def test_one_option_can_keep_the_only_available_published_baseline(local_tmp):
    db, ref = enriched(local_tmp)
    with closing(sqlite3.connect(db)) as con, con:
        con.execute("DELETE FROM meta_competitive_lists WHERE placement > 3")
    result = plan(local_tmp, db, ref, options=1)
    assert len(result["alternatives"]) == 1
    assert result["alternatives"][0]["decision"] == "keep_published_base_and_test_play"
    assert result["alternatives"][0]["construction_changes"]["counts"]["shared"] == 60


def test_future_import_contract_uses_existing_parser_without_reading_any_log():
    args = cli.build_parser().parse_args(["log", "import", "one-explicit-log.txt", "--deck", "invented", "--db", "selected.sqlite3"])
    assert args.path == "one-explicit-log.txt" and args.deck == "invented"
    assert "log import <one-selected-file>" in loop.future_import_contract()["existing_entrypoints"][0]


@pytest.mark.parametrize("kwargs", [{"options":0}, {"options":5}, {"options":True},
    {"target":""}, {"as_of":"today"}, {"db":None}, {"reference_db":None}])
def test_context_and_explicit_database_required_before_io(local_tmp, monkeypatch, kwargs):
    monkeypatch.setattr(competitive, "_advisor_snapshot", lambda *a: pytest.fail("no IO"))
    args = dict(db=local_tmp/"unused", reference_db=local_tmp/"ref", as_of=AS_OF, target="Hydrapple")
    args.update(kwargs)
    with pytest.raises(ValueError): counter.counter_plan(local_tmp, **args)


@pytest.mark.parametrize("command", ["counter-plan", "learning-simulate"])
def test_cli_missing_or_private_db_fails_without_fallback(local_tmp, monkeypatch, capsys, command):
    forbid_all(monkeypatch)
    monkeypatch.setattr(cli, "find_project_root", lambda: local_tmp)
    argv = ["meta", command, "--as-of", AS_OF, "--target", "Hydrapple", "--reference-db", str(local_tmp/"owner.sqlite3"), "--json"]
    for suffix in ([], ["--db", str(local_tmp/"data/local/owner.sqlite3")]):
        assert cli.main(argv + suffix) == 2
        result = json.loads(capsys.readouterr().out)
        assert result["status"] == "BLOCKED_WITH_REASON"
    assert not (local_tmp/"data/local/owner.sqlite3").exists()


def journal():
    j = loop.append_record([], record_id="f", kind="source_fact", recorded_at="2026-10-20",
        payload={"provenance":"invented source", "fact":"invented"}, refs=["source:invented"])
    return loop.append_record(j, record_id="h", kind="hypothesis_to_test", recorded_at="2026-10-20",
        payload={"text":"test setup"}, refs=["f"])


def test_append_only_revocation_reopening_date_and_alias_independence():
    j = journal()
    old = copy.deepcopy(j)
    j = loop.append_record(j, record_id="withdraw", kind="withdrawn", recorded_at="2026-10-21",
        payload={"reason":"insufficient evidence"}, refs=["h"], revises="h")
    j = loop.append_record(j, record_id="reopen", kind="hypothesis_to_test", recorded_at="2026-10-22",
        payload={"reason":"new protocol"}, refs=["withdraw"], revises="withdraw")
    assert j[:2] == old and loop.validate(j)
    assert [r["id"] for r in loop.view(j, as_of="2026-10-20")["current"]] == ["f", "h"]
    assert [r["id"] for r in loop.view(j, as_of="2026-10-21")["current"]] == ["f", "withdraw"]
    view = loop.view(j, as_of="2026-10-22")
    view["history"][0]["payload"]["fact"] = "tampered return value"
    assert j[0]["payload"]["fact"] == "invented"


@pytest.mark.parametrize("fault", ["tamper", "id_conflict", "future_parent", "rewrite_fact", "branch", "backdate", "no_reason"])
def test_inconsistent_history_rejected_without_mutation(fault):
    j = journal()
    before = copy.deepcopy(j)
    with pytest.raises(ValueError):
        if fault == "tamper":
            altered = copy.deepcopy(j); altered[0]["payload"]["fact"] = "overwritten"; loop.validate(altered)
        elif fault == "id_conflict":
            loop.append_record(j, record_id="h", kind="hypothesis_to_test", recorded_at="2026-10-20", payload={"text":"other"}, refs=["f"])
        else:
            kw = dict(record_id="r", kind="withdrawn", recorded_at="2026-10-21", payload={"reason":"review"}, refs=["h"], revises="h")
            if fault == "future_parent": kw.update(refs=["missing"], revises="missing")
            if fault == "rewrite_fact": kw.update(refs=["f"], revises="f")
            if fault == "backdate": kw.update(recorded_at="2026-10-19")
            if fault == "no_reason": kw.update(payload={"text":"not justified"})
            if fault == "branch":
                branch = loop.append_record(j, **kw)
                loop.append_record(branch, **{**kw, "record_id":"branch"})
            else: loop.append_record(j, **kw)
    assert j == before


def test_snapshot_differences_do_not_pool_versions_or_infer_causation():
    group = {"version":1,"opponent_archetype":"Invented","classification_basis":"hypothesized",
             "wins":0,"losses":2,"unknown":1,"n":2,"games":3}
    a = {"as_of":"2026-10-20","deck_id":"invented","period":{},"groups":[group],"battle_refs":[1,2,3]}
    b = {**a,"as_of":"2026-10-22","groups":[{**group,"version":2,"wins":1,"losses":0,"unknown":0,"n":1,"games":1}],"battle_refs":[4]}
    delta = loop.compare_snapshots(a,b)
    assert len(delta["changes"]) == 2 and delta["removed_or_reclassified_refs"] == [1,2,3]
    assert not delta["improvement_demonstrated"] and delta["causal_effect"] == "unknown"
    for altered in ({**b,"deck_id":"other"},{**b,"as_of":"2026-10-19"},{**b,"period":{"since":"2026-10-01"}}):
        with pytest.raises(ValueError): loop.compare_snapshots(a,altered)
