"""Invented PUBLIC lists/catalog/rules; no real cards or PC cache certify the fixtures."""
from __future__ import annotations

import json
import socket
import sqlite3
import urllib.request
from contextlib import closing

import pytest

from pokemind import cli, competitive as c, public_deck_preflight as p, rules
from pokemind.database import connect_readonly
from test_competitive_advisor import AS_OF, sample, tree_bytes, forbid_io


def reference(root, competitive_db):
    target = c.create_workspace(root, "preflight-reference")
    db = target / "public.sqlite3"
    source = {"source_id": "synthetic-preflight", "source_type": "synthetic_fixture",
              "url": "https://www.pokemon.com/us/synthetic-preflight", "title": "Invented rules for tests only",
              "language": "en", "published_date": "2026-01-01", "validation_status": "verified"}
    assertions = []
    for name, kind, subject, payload in (
        ("rotation", "rotation", None, {"allowed_regulation_marks": ["H", "I", "J"]}),
        ("coverage", "restriction_coverage", None, {"complete": True}),
        ("reprint", "reprint_equivalence", "old-099", {"current_printing_id": "syn-002", "functional_identity_verified": True}),
        ("errata", "errata", "syn-101", {"effective_text": "Synthetic corrected instruction."}),
    ):
        assertions.append({"assertion_id": "synthetic-" + name, "source_id": source["source_id"],
                           "assertion_kind": kind, "format": "standard", "platform": "in_person",
                           "subject_id": subject, "payload": payload, "effective_from": "2026-01-01",
                           "effective_to": AS_OF, "validation_status": "verified", "confidence": "high"})
    registry = {"consulted_at": "2026-10-22T18:00:00Z", "sources": [source], "assertions": assertions,
                "deck_structure_rules": [{"rule_id": "synthetic-structure", "source_id": source["source_id"],
                    "format": "standard", "platform": None, "validation_status": "verified", "confidence": "high",
                    "effective_from": "2026-01-01", "effective_to": AS_OF,
                    "payload": {"required_total": 60, "same_name_limit": 6, "basic_energy_unlimited": True,
                                "requires_basic_pokemon": True, "copy_limit_exceptions_complete": True,
                                "special_rule_limits_complete": True}}]}
    registry_path = target / "synthetic-registry.json"
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    rules.load_official_registry(db, registry_path)
    groups, _, _, _ = c._advisor_snapshot(root, competitive_db, AS_OF)
    cards = {(card["set"], card["number"]): card for g in groups.values() for card in g["cards"].values()}
    with closing(sqlite3.connect(db)) as con, con:
        for code in {key[0] for key in cards}:
            con.execute("INSERT INTO catalog_sets(tcgdex_id,tcg_online_code,discovered_at,updated_at) VALUES (?,?,?,?)",
                        (code.lower(), code, AS_OF, AS_OF))
        for (code, number), card in cards.items():
            printing_id = code.lower() + "-" + number
            con.execute("""INSERT INTO catalog_printings(tcgdex_id,set_id,local_id,category,stage,regulation_mark,
                           discovered_at,updated_at,brief_source_url,brief_retrieved_at) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                        (printing_id, code.lower(), number, card["type"], "Basic" if card["type"] == "pokemon" else None,
                         "G" if code == "OLD" else "H", AS_OF, AS_OF, "https://api.tcgdex.net/synthetic", AS_OF))
            con.execute("""INSERT INTO catalog_translations(printing_id,language,status,name,category,energy_type,
                           description,source_url,retrieved_at) VALUES(?,'en','present',?,?,?,?,?,?)""",
                        (printing_id, card["name"], card["type"], "Basic" if card["type"] == "energy" else None,
                         "Invented text.", "https://api.tcgdex.net/synthetic/" + printing_id, AS_OF))
    return db


def run(root, db, ref, **kw):
    return p.competitive_preflight(root, db, ref, as_of=kw.pop("as_of", AS_OF), format="standard",
                                   platform=kw.pop("platform", "in_person"), **kw)


def forbid_all(monkeypatch):
    forbid_io(monkeypatch)
    def forbidden(*args, **kwargs):
        raise AssertionError("network/default owner/writable DB forbidden")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    monkeypatch.setattr(rules, "connect_writable", forbidden)
    original = p.connect_readonly
    def readonly(path):
        con = original(path)
        assert con.execute("PRAGMA query_only").fetchone()[0] == 1
        with pytest.raises(sqlite3.OperationalError):
            con.execute("CREATE TABLE forbidden(x)")
        return con
    monkeypatch.setattr(p, "connect_readonly", readonly)


def test_full_public_preflight_reproduction(local_tmp, monkeypatch, record_testsuite_property):
    db = sample(local_tmp)
    ref = reference(local_tmp, db)
    before = tree_bytes(db.parent), tree_bytes(ref.parent)
    forbid_all(monkeypatch)
    report = run(local_tmp, db, ref)
    live = run(local_tmp, db, ref, platform="live")
    assert len(report["options"]) == 4 and report["deck_status_counts"] == {"legal": 4, "not_legal": 0, "unknown": 0}
    assert live["deck_status_counts"] == {"legal": 0, "not_legal": 0, "unknown": 4}
    assert report["status"] == live["status"] == "PARTIAL_WITH_EVIDENCE"
    for option in report["options"]:
        assert option["total_cards"] == option["quantity_sum"] == 60
        assert option["counts"]["copy_legality"] == {"legal": 60, "not_legal": 0, "unknown": 0}
        assert option["counts"]["identity"]["resolved"] == option["counts"]["identity_denominator"]
        assert option["live_availability"] == option["ownership"] == option["craftability"] == "unknown"
        assert option["readiness_status"] == "unknown"
        for card in option["cards"]:
            assert card["verdict"]["sources"] and card["catalog_evidence"]["catalog_texts"]
    old = next(card for card in report["options"][0]["cards"] if card["set_code"] == "OLD")
    assert "FUNCTIONAL_REPRINT_VERIFIED" in old["verdict"]["reason_codes"]
    trainer = next(card for card in report["options"][0]["cards"] if card["collector_number"] == "101")
    errata = next(a for a in trainer["catalog_evidence"]["official_assertions"] if a["kind"] == "errata")
    assert errata["effective_from"] == "2026-01-01" and errata["source"]["url"].startswith("https://www.pokemon.com/")
    assert (tree_bytes(db.parent), tree_bytes(ref.parent)) == before
    assert not report["network_used"] and not report["owner_database_opened"] and not report["database_mutated"]
    record_testsuite_property("public_deck_preflight_reproduction", json.dumps({
        "scope": "SYNTHETIC_PUBLIC_DECK_PREFLIGHT_ONLY", "options": 4, "cards_per_deck": 60,
        "in_person_legal_decks": 4, "live_unknown_decks": 4, "reprint_and_errata_checked": True,
        "separate_public_dbs": True, "read_only_cache_unchanged": True, "network_forbidden": True,
        "owner_database_opened": False, "real_public_cache_verified": False,
    }))


@pytest.mark.parametrize("fault", ["missing_printing", "ambiguous", "name", "category", "translation_status",
                                  "no_rotation", "no_coverage", "no_reprint", "incomplete_structure", "future_source",
                                  "missing_stage", "missing_energy", "restriction", "unmapped_set", "unknown_stage", "energy_conflict"])
def test_fail_closed_evidence_and_negative_proof(local_tmp, fault):
    db = sample(local_tmp)
    ref = reference(local_tmp, db)
    with closing(sqlite3.connect(ref)) as con, con:
        if fault == "missing_printing":
            con.execute("DELETE FROM catalog_translations WHERE printing_id='syn-001'")
        elif fault == "ambiguous":
            con.execute("""INSERT INTO catalog_printings SELECT 'syn-alias',set_id,local_id,category,hp,stage,regulation_mark,
                rarity,illustrator,types_json,variants_json,brief_sha256_en,brief_sha256_fr,detail_stale_en,detail_stale_fr,
                discovered_at,updated_at,brief_source_url,brief_retrieved_at FROM catalog_printings WHERE tcgdex_id='syn-001'""")
            con.execute("""INSERT INTO catalog_translations(printing_id,language,status,name,source_url,retrieved_at)
                SELECT 'syn-alias',language,status,name,source_url,retrieved_at FROM catalog_translations WHERE printing_id='syn-001'""")
        elif fault == "name":
            con.execute("UPDATE catalog_translations SET name='Other' WHERE printing_id='syn-001'")
        elif fault == "category":
            con.execute("UPDATE catalog_translations SET category='trainer' WHERE printing_id='syn-001'")
        elif fault == "translation_status":
            con.execute("UPDATE catalog_translations SET status='absent' WHERE printing_id='syn-001'")
        elif fault in {"no_rotation", "no_coverage", "no_reprint"}:
            con.execute("DELETE FROM official_rule_assertions WHERE assertion_id=?", ("synthetic-" + fault[3:],))
        elif fault == "incomplete_structure":
            payload = json.loads(con.execute("SELECT payload_json FROM official_deck_structure_rules").fetchone()[0])
            payload["special_rule_limits_complete"] = False
            con.execute("UPDATE official_deck_structure_rules SET payload_json=?", (json.dumps(payload),))
        elif fault == "future_source":
            con.execute("UPDATE official_rule_sources SET published_date='2026-10-23'")
        elif fault == "missing_stage":
            con.execute("UPDATE catalog_printings SET stage=NULL WHERE category='pokemon'")
        elif fault == "missing_energy":
            con.execute("UPDATE catalog_translations SET energy_type=NULL WHERE category='energy'")
        elif fault == "unmapped_set":
            con.execute("UPDATE catalog_sets SET tcg_online_code=NULL WHERE tcgdex_id='syn'")
        elif fault == "unknown_stage":
            con.execute("UPDATE catalog_printings SET stage='Unclassified' WHERE category='pokemon'")
        elif fault == "energy_conflict":
            con.execute("""INSERT INTO catalog_translations(printing_id,language,status,name,category,energy_type,source_url,retrieved_at)
                SELECT printing_id,'fr',status,name,category,'Special',source_url,retrieved_at
                FROM catalog_translations WHERE category='energy'""")
        elif fault == "restriction":
            con.execute("UPDATE official_rule_assertions SET assertion_kind='restriction',subject_id='syn-001',payload_json='{}' "
                        "WHERE assertion_id='synthetic-errata'")
    option = run(local_tmp, db, ref, selectors=["123:1"])["options"][0]
    assert option["status"] == ("not_legal" if fault == "restriction" else "unknown")
    if fault == "ambiguous":
        assert option["counts"]["identity"]["ambiguous"] == 1
    if fault == "future_source":
        assert "DECK_STRUCTURE_EVIDENCE_NOT_AVAILABLE_AS_OF" in option["blockers"]
    if fault == "unmapped_set":
        assert option["counts"]["identity_reasons"]["SET_CODE_MAPPING_MISSING"] > 0


def test_structure_violation_and_expired_rules(local_tmp):
    db = sample(local_tmp)
    ref = reference(local_tmp, db)
    with closing(sqlite3.connect(ref)) as con, con:
        payload = json.loads(con.execute("SELECT payload_json FROM official_deck_structure_rules").fetchone()[0])
        payload["same_name_limit"] = 4
        con.execute("UPDATE official_deck_structure_rules SET payload_json=?", (json.dumps(payload),))
        con.execute("UPDATE catalog_translations SET name='creature beta' WHERE printing_id='old-099'")
    option = run(local_tmp, db, ref, selectors=["123:1"])["options"][0]
    assert option["status"] == "not_legal" and "DECK_COPY_LIMIT_EXCEEDED" in option["blockers"]
    assert run(local_tmp, db, ref, as_of="2026-10-23")["deck_status_counts"]["unknown"] == 4


@pytest.mark.parametrize("selectors", [["123"], ["123:99"], ["../owner:1"], ["123:1", "123:2"], ["123:1", "123:1"]])
def test_invalid_or_duplicate_selectors(local_tmp, selectors):
    db = sample(local_tmp)
    ref = reference(local_tmp, db)
    with pytest.raises(ValueError):
        run(local_tmp, db, ref, selectors=selectors)


@pytest.mark.parametrize("fault", ["missing_ref", "missing_competitive", "private_ref", "private_competitive", "schema", "owner_rows"])
def test_explicit_public_paths_and_schema_required(local_tmp, monkeypatch, fault):
    db = sample(local_tmp)
    ref = reference(local_tmp, db)
    if fault == "missing_ref":
        ref = c.create_workspace(local_tmp, "missing-reference") / "public.sqlite3"
    elif fault == "missing_competitive":
        db = c.create_workspace(local_tmp, "missing-competitive") / "public.sqlite3"
    elif fault == "private_ref":
        ref = local_tmp / "data/local/pokemind.sqlite3"
    elif fault == "private_competitive":
        db = local_tmp / "data/local/pokemind.sqlite3"
    elif fault == "schema":
        with closing(sqlite3.connect(ref)) as con, con:
            con.execute("DROP TABLE official_rule_assertions")
    elif fault == "owner_rows":
        with closing(sqlite3.connect(ref)) as con, con:
            con.execute("CREATE TABLE owner_secret(value)")
            con.execute("INSERT INTO owner_secret VALUES ('MUST_NOT_LEAK')")
    forbid_all(monkeypatch)
    with pytest.raises(ValueError):
        run(local_tmp, db, ref)


@pytest.mark.parametrize("date", ["2026-2-01", "2026-02-30", "tomorrow"])
def test_dates_fail_before_db_access(local_tmp, monkeypatch, date):
    monkeypatch.setattr(p, "require_public_database", lambda *a: pytest.fail("no file access"))
    with pytest.raises(ValueError):
        run(local_tmp, local_tmp / "unused", local_tmp / "unused-ref", as_of=date)


def test_cli_human_json_and_no_fallback(local_tmp, monkeypatch, capsys):
    db = sample(local_tmp)
    ref = reference(local_tmp, db)
    monkeypatch.setattr(cli, "find_project_root", lambda: local_tmp)
    forbid_all(monkeypatch)
    args = ["meta", "competitive-preflight", "--db", str(db), "--reference-db", str(ref),
            "--as-of", AS_OF, "--format", "standard", "--platform", "in_person"]
    assert cli.main(args + ["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] and len(payload["options"]) == 4
    assert "DO_NOT_STORE" not in json.dumps(payload)
    assert cli.main(args) == 0
    assert "60 cartes" in capsys.readouterr().out
    assert cli.main(args[:2] + args[4:] + ["--json"]) == 2
    error = json.loads(capsys.readouterr().out)
    assert error["status"] == "BLOCKED_WITH_REASON" and error["missing_evidence"]


def test_shared_engine_total_without_import(local_tmp):
    db = sample(local_tmp)
    ref = reference(local_tmp, db)
    entries = [{"ordinal": 1, "quantity": 59, "card_name": "Creature Alpha", "set_code": "SYN", "collector_number": "001"}]
    report = rules.check_deck_entries(ref, entries, total_cards=59, exact_confirmed=True,
                                      format="standard", platform="in_person", as_of=AS_OF)
    assert report["status"] == "not_legal" and "DECK_TOTAL_NOT_REQUIRED_COUNT" in report["reason_codes"]
    con = connect_readonly(ref)
    try:
        assert con.execute("SELECT COUNT(*) FROM deck_versions").fetchone()[0] == 0
    finally:
        con.close()
