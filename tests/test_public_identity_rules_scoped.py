"""Invented lists and SQLite files only; explicit test selection, no real caches."""
from __future__ import annotations

import io
import json
import os
import sqlite3
import socket
import urllib.request
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace

import pytest

from pokemind import public_deck_preflight as preflight, set_code_aliases


AS_OF = "2026-10-23"
TEXT = ("Pokémon: 1\n1 Invented Scout TST 1\n\nTrainer: 1\n"
        "1 Invented Tool 30C 2\n\nEnergy: 1\n58 Fire Energy MEE 10\n\nTotal Cards: 60\n")


def fixture_pair(root):
    paths = [root / p for p in preflight.SCOPED_PUBLIC_CACHES]
    for path in paths:
        path.parent.mkdir(parents=True)
    with closing(sqlite3.connect(paths[0])) as c, c:
        c.execute("CREATE TABLE meta_competitive_lists(event_id,placement,list_url,fetched_at,deck_text)")
        for rank in (1, 2):
            c.execute("INSERT INTO meta_competitive_lists VALUES (?,?,?,?,?)",
                      ("invented", rank, "https://example.invalid/invented-list", AS_OF, TEXT))
    with closing(sqlite3.connect(paths[1])) as c, c:
        c.executescript("""
            CREATE TABLE catalog_sets(tcgdex_id,tcg_online_code);
            CREATE TABLE catalog_printings(tcgdex_id,set_id,local_id,category,stage,regulation_mark,variants_json);
            CREATE TABLE catalog_translations(printing_id,status,language,name,energy_type,source_url,retrieved_at);
            CREATE TABLE official_rule_sources(source_id,title,url,published_date,consulted_at,validation_status,effective_from,effective_to);
            CREATE TABLE official_rule_assertions(assertion_id,source_id,assertion_kind,subject_id,payload_json,format,platform,effective_from,effective_to,validation_status);
            CREATE TABLE official_deck_structure_rules(rule_id,source_id,payload_json,format,platform,effective_from,effective_to,validation_status);
            INSERT INTO catalog_sets VALUES ('test','TST'),('mee',NULL),('old30','30C'),('new30',NULL);
            INSERT INTO catalog_printings VALUES ('test-1','test','1','pokemon','Basic','H','[]'),
                ('mee-010','mee','010','energy',NULL,NULL,'[{"type":"holo","stamp":["invented"]}]'),
                ('new30-002','new30','002','trainer',NULL,'J','[]');
            INSERT INTO catalog_translations VALUES
                ('test-1','present','en','Invented Scout',NULL,'https://example.invalid/scout','2026-10-22'),
                ('mee-010','present','en','Basic Fire Energy','Normal','https://example.invalid/energy','2026-10-22'),
                ('new30-002','present','en','Invented Tool',NULL,'https://example.invalid/tool','2026-10-22');
            INSERT INTO official_rule_sources VALUES
                ('invented','Invented source','https://example.invalid/rule','2026-01-01','2026-10-22','verified',NULL,'2026-10-22');
            INSERT INTO official_rule_assertions VALUES
                ('invented-rotation','invented','rotation',NULL,'{}','standard',NULL,NULL,'2026-10-22','verified');
        """)
    return paths


def bridge():
    return {"version": "invented-test-view", "aliases": {
        code: [{"set_id": set_id, "code": code, "language": "en",
                "source_url": "https://example.invalid/invented-set", "retrieved_at": "2026-10-22",
                "members": [{"id": pid, "number": number, "name": name}]}]
        for code, set_id, pid, number, name in [
            ("MEE", "mee", "mee-010", "010", "Basic Fire Energy"),
            ("30C", "new30", "new30-002", "002", "Invented Tool")]}}


def forbid(*a, **kw):
    raise AssertionError("FORBIDDEN_DISCOVERY_OR_SOURCE")


def no_discovery(monkeypatch):
    for name in ("glob", "rglob", "iterdir"):
        monkeypatch.setattr(Path, name, forbid)
    for name in ("listdir", "scandir", "walk"):
        monkeypatch.setattr(os, name, forbid)
    monkeypatch.setattr(preflight.competitive, "_advisor_snapshot", forbid)
    monkeypatch.setattr(preflight, "require_public_database", forbid)
    monkeypatch.setattr(preflight.competitive, "BoundedPages", forbid)
    monkeypatch.setattr(socket, "create_connection", forbid)
    monkeypatch.setattr(urllib.request, "urlopen", forbid)


@pytest.mark.parametrize("scope,code", [("two_sqlite_only", "BLOCKED_SOURCE_SCOPE"),
                                        ("invented_invalid", "PUBLIC_PREFLIGHT_SOURCE_SCOPE_INVALID")])
def test_full_preflight_refuses_before_any_source_or_stat(monkeypatch, scope, code):
    no_discovery(monkeypatch)
    monkeypatch.setattr(Path, "is_file", forbid)
    monkeypatch.setattr(Path, "stat", forbid)
    with pytest.raises(ValueError, match=code):
        preflight.competitive_preflight(Path("unused"), Path("unused-db"), Path("unused-ref"),
            as_of=AS_OF, format="standard", platform="live", source_scope=scope)


def test_exact_pair_no_other_open_and_idempotent_resume(local_tmp, monkeypatch):
    paths = fixture_pair(local_tmp)
    monkeypatch.setattr(set_code_aliases, "build_aliases", lambda *a, **k: bridge())
    original_open, original_connect = io.open, sqlite3.connect
    opened, connected = [], []
    def exact_open(path, mode="r", *a, **kw):
        assert Path(path) in paths and mode == "rb"
        opened.append(Path(path))
        return original_open(path, mode, *a, **kw)
    def readonly(database, *a, **kw):
        assert database in {p.as_uri() + "?mode=ro&immutable=1" for p in paths}
        connected.append(database)
        c = original_connect(database, *a, **kw)
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            c.execute("CREATE TABLE forbidden_write(x)")
        return c
    with monkeypatch.context() as m:
        no_discovery(m)
        m.setattr(io, "open", exact_open)
        m.setattr(sqlite3, "connect", readonly)
        first = preflight.scoped_identity_rules_observations(local_tmp, as_of=AS_OF)
        second = preflight.scoped_identity_rules_observations(local_tmp, as_of=AS_OF)
    assert first == second
    assert set(opened) == set(paths) and len(connected) == 4
    assert first["exact_sqlite_files_unchanged"] == 2
    assert first["placements"] == 2 and len(first["compositions"]) == 1
    assert (first["row_denominator"], first["copy_denominator"]) == (3, 60)
    assert (first["resolved_rows"], first["resolved_copies"]) == (1, 1)
    by_code = {r["code"]: r for r in first["identity_matrix"]}
    assert by_code["MEE"]["reason"] == "CATALOG_NAME_OR_PRESENT_TRANSLATION_MISSING"
    assert by_code["MEE"]["catalog_candidates"][0]["tcgdex_id"] == "mee-010"
    assert by_code["MEE"]["identity"] == "unknown"
    assert by_code["30C"]["reason"] == "SET_CODE_ALIAS_AMBIGUOUS"
    assert by_code["30C"]["set_context"] == {"native_sets": ["old30"], "alias_sets": ["new30"]}
    assert all("members" not in e for r in first["identity_matrix"] for e in r["alias_sources"])
    assert first["source_validation"] == "BLOCKED_SOURCE_SCOPE"
    assert not first["full_legality_preflight_executed"]
    assert not first["owner_database_opened"] and first["provider_gets"] == 0
    for platform in ("in_person", "live"):
        assert first["normative"][platform]["active_verified_assertions"] == []
        assert first["compositions"][0][platform] == "unknown"
        assert "NO_UNIQUE_ACTIVE_ROTATION" in first["compositions"][0]["blockers"][platform]


def test_exact_name_positive_still_cannot_certify_deck_or_live(local_tmp, monkeypatch):
    paths = fixture_pair(local_tmp)
    with closing(sqlite3.connect(paths[0])) as c, c:
        c.execute("UPDATE meta_competitive_lists SET deck_text=?", (TEXT.replace("58 Fire", "58 Basic Fire"),))
    monkeypatch.setattr(set_code_aliases, "build_aliases", lambda *a, **k: bridge())
    result = preflight.scoped_identity_rules_observations(local_tmp, as_of=AS_OF)
    assert result["resolved_rows"] == 2 and result["resolved_copies"] == 59
    assert [r["code"] for r in result["identity_matrix"]] == ["30C"]
    assert result["compositions"][0]["live"] == "unknown"
    assert result["compositions"][0]["in_person"] == "unknown"


def test_member_name_conflict_is_not_equivalence(local_tmp, monkeypatch):
    fixture_pair(local_tmp)
    view = bridge()
    view["aliases"]["MEE"][0]["members"][0]["name"] = "Invented conflicting member"
    monkeypatch.setattr(set_code_aliases, "build_aliases", lambda *a, **k: view)
    result = preflight.scoped_identity_rules_observations(local_tmp, as_of=AS_OF)
    row = next(r for r in result["identity_matrix"] if r["code"] == "MEE")
    assert row["identity"] == "unknown" and row["reason"] == "COLLECTOR_NUMBER_NOT_FOUND"


def test_two_sourced_sets_for_30c_remain_ambiguous_without_native_code(local_tmp, monkeypatch):
    paths = fixture_pair(local_tmp)
    with closing(sqlite3.connect(paths[1])) as c, c:
        c.execute("UPDATE catalog_sets SET tcg_online_code=NULL WHERE tcgdex_id='old30'")
    view = bridge()
    view["aliases"]["30C"].append({**view["aliases"]["30C"][0], "set_id": "old30"})
    monkeypatch.setattr(set_code_aliases, "build_aliases", lambda *a, **k: view)
    result = preflight.scoped_identity_rules_observations(local_tmp, as_of=AS_OF)
    row = next(r for r in result["identity_matrix"] if r["code"] == "30C")
    assert row["reason"] == "SET_CODE_ALIAS_AMBIGUOUS"
    assert row["set_context"] == {"native_sets": [], "alias_sets": ["new30", "old30"]}
    assert row["identity"] == "unknown"


def test_active_synthetic_rotation_does_not_certify_source_or_live(local_tmp, monkeypatch):
    fixture_pair(local_tmp)
    monkeypatch.setattr(set_code_aliases, "build_aliases", lambda *a, **k: bridge())
    result = preflight.scoped_identity_rules_observations(local_tmp, as_of="2026-10-22")
    for platform in ("in_person", "live"):
        assert result["normative"][platform]["rotation_proven"]
        assert result["compositions"][0][platform] == "unknown"
        assert "BLOCKED_SOURCE_SCOPE" in result["compositions"][0]["blockers"][platform]


@pytest.mark.parametrize("argument", ["bad_date", "traversal"])
def test_bad_input_refused_before_paths(monkeypatch, argument):
    monkeypatch.setattr(Path, "lstat", forbid)
    with pytest.raises(ValueError):
        preflight.scoped_identity_rules_observations(
            Path("unused/../outside") if argument == "traversal" else Path("unused"),
            as_of="20261023" if argument == "bad_date" else AS_OF)


def test_incomplete_cached_list_not_accepted(local_tmp, monkeypatch):
    paths = fixture_pair(local_tmp)
    with closing(sqlite3.connect(paths[0])) as c, c:
        c.execute("UPDATE meta_competitive_lists SET deck_text=?", (TEXT.replace("58 Fire", "57 Fire"),))
    monkeypatch.setattr(set_code_aliases, "build_aliases", lambda *a, **k: bridge())
    with pytest.raises(ValueError):
        preflight.scoped_identity_rules_observations(local_tmp, as_of=AS_OF)


@pytest.mark.parametrize("part", [0, 1])
def test_reparse_metadata_refused_before_open(local_tmp, monkeypatch, part):
    paths = fixture_pair(local_tmp)
    original = Path.lstat
    def redirected(path, *a, **kw):
        if path == paths[part]:
            return SimpleNamespace(st_mode=0, st_file_attributes=1024)
        return original(path, *a, **kw)
    monkeypatch.setattr(Path, "lstat", redirected)
    monkeypatch.setattr(sqlite3, "connect", forbid)
    with pytest.raises(ValueError, match="SCOPED_REDIRECTION_BLOCKED"):
        preflight.scoped_identity_rules_observations(local_tmp, as_of=AS_OF)


def test_wal_main_file_refused_without_sidecar_access(local_tmp, monkeypatch):
    paths = fixture_pair(local_tmp)
    with paths[0].open("r+b") as f:
        f.seek(18)
        f.write(b"\x02\x02")
    monkeypatch.setattr(sqlite3, "connect", forbid)
    with pytest.raises(ValueError, match="SCOPED_SQLITE_NOT_STANDALONE"):
        preflight.scoped_identity_rules_observations(local_tmp, as_of=AS_OF)


def test_missing_cache_never_searches_alternatives(local_tmp, monkeypatch):
    no_discovery(monkeypatch)
    monkeypatch.setattr(sqlite3, "connect", forbid)
    with pytest.raises(FileNotFoundError):
        preflight.scoped_identity_rules_observations(local_tmp, as_of=AS_OF)


def test_observed_source_change_discards_report(local_tmp, monkeypatch):
    paths = fixture_pair(local_tmp)
    monkeypatch.setattr(set_code_aliases, "build_aliases", lambda *a, **k: bridge())
    original = preflight._scoped_observations
    def change(*a, **kw):
        report = original(*a, **kw)
        st = paths[0].stat()
        os.utime(paths[0], ns=(st.st_atime_ns, st.st_mtime_ns + 1000000000))
        return report
    monkeypatch.setattr(preflight, "_scoped_observations", change)
    with pytest.raises(ValueError, match="SCOPED_SOURCE_CHANGED"):
        preflight.scoped_identity_rules_observations(local_tmp, as_of=AS_OF)


@pytest.mark.parametrize("bad", [None, "commit", "blob", "url", "language"])
def test_literal_provenance_requires_all_pins(bad):
    commit = "a" * 40  # invented object, no network request
    url = f"https://github.com/tcgdex/cards-database/blob/{commit}/data/Invented.ts"
    proof = {"operation": "literal_snapshot", "language": "en", "source_commit": commit,
        "source_url": f"https://github.com/tcgdex/cards-database/tree/{commit}/data",
        "source_objects": {"invented": {"source_url": url, "git_blob": "b" * 40}}}
    if bad == "commit": proof["source_commit"] = "main"
    if bad == "blob": proof["source_objects"]["invented"]["git_blob"] = "missing"
    if bad == "url": proof["source_objects"]["invented"]["source_url"] += "?other=true"
    if bad == "language": proof["language"] = "fr"
    with closing(sqlite3.connect(":memory:")) as c, c:
        c.execute("CREATE TABLE catalog_batch_queries(query_sha256,evidence_json)")
        c.execute("CREATE TABLE catalog_detail_payloads(kind,entity_id,language,query_sha256)")
        c.execute("INSERT INTO catalog_batch_queries VALUES ('invented',?)", (json.dumps(proof),))
        c.execute("INSERT INTO catalog_detail_payloads VALUES ('sets','invented','en','invented')")
        result = set_code_aliases.payload_source(c, "sets", "invented", "en")
    assert (result is not None) == (bad is None)
