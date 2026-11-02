"""The CI publisher must reject missing evidence instead of upgrading test totals."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest
from pokemind.cards import _canonical_sha256


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("write_ci_evidence", ROOT / "scripts/write_ci_evidence.py")
publisher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publisher)


def _report():
    fields = ("tcgdex_id", "format", "platform", "as_of", "status")
    return {
        "scope": "VERSIONED_REGISTRIES_WITH_SYNTHETIC_PRINTINGS",
        "review_sources": 4, "review_assertions": 16,
        "sqlite_totals": {"sources": 15, "assertions": 22, "structure_rules": 1},
        "sql_assertions_match_registries": True, "normative_reload_rows_identical": True,
        "integrity": "ok", "foreign_key_errors": 0, "read_only_verdicts": True,
        "without_catalog": "unknown", "synthetic_printings": 6,
        "local_database_verified": False, "source_documents_revalidated": False,
        "competitive_data_acquired": False,
        "registry_sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
            "knowledge/curated/official_rules_2026.json", "knowledge/curated/official_rules_20261022.json",
        )},
        "registry_canonical_sha256": {name: _canonical_sha256(json.loads((ROOT / name).read_bytes().decode("utf-8"))) for name in (
            "knowledge/curated/official_rules_2026.json", "knowledge/curated/official_rules_20261022.json",
        )},
        "verdicts": [dict(zip(fields, values)) for values in (
            ("sm1-129", "standard", "in_person", "2026-10-22", "legal"),
            ("swsh2-154", "standard", "in_person", "2026-10-22", "legal"),
            ("me01-125", "standard", "in_person", "2026-10-22", "legal"),
            ("me01-114", "standard", "in_person", "2026-10-22", "legal"),
            ("sm5-114", "expanded", "in_person", "2026-10-22", "not_legal"),
            ("sv07-086", "standard", "in_person", "2026-10-22", "unknown"),
            ("me01-125", "standard", "live", "2026-10-22", "unknown"),
            ("me01-125", "standard", "in_person", "2026-10-23", "unknown"),
        )],
    }


def _context(local_tmp, monkeypatch, report, *, copies=1, failures=0):
    junit = local_tmp / "synthetic-junit.xml"
    summary = local_tmp / "synthetic-summary.md"
    root = ET.Element("testsuites")
    suite = ET.SubElement(root, "testsuite", tests="1", skipped="0", errors="0", failures=str(failures))
    properties = ET.SubElement(suite, "properties")
    for _ in range(copies):
        ET.SubElement(properties, "property", name="public_rules_reproduction", value=json.dumps(report))
    ET.SubElement(properties, "property", name="public_competitive_reproduction", value=json.dumps({
        "scope": "SYNTHETIC_COMPETITIVE_PAGES_ONLY", "events": 1, "lists": 1,
        "total_cards": 60, "idempotent": True, "read_only_offline_export": True,
        "integrity": "ok", "foreign_key_errors": 0, "owner_database_opened": False,
        "real_public_cache_verified": False,
    }))
    ET.SubElement(properties, "property", name="public_competitive_advisor_reproduction", value=json.dumps({
        'scope': 'SYNTHETIC_OFFLINE_PUBLIC_ADVISOR_ONLY', 'placements': 6, 'distinct_compositions': 4,
        'shortlist_options': 4, 'comparison_shared': 59, 'comparison_removed': 1, 'comparison_added': 1,
        'read_only_cache_unchanged': True, 'network_forbidden': True, 'unknowns_preserved': True,
        'real_public_cache_verified': False, 'owner_database_opened': False,
    }))
    ET.SubElement(properties, "property", name="public_deck_preflight_reproduction", value=json.dumps({
        "scope": "SYNTHETIC_PUBLIC_DECK_PREFLIGHT_ONLY", "options": 4, "cards_per_deck": 60,
        "in_person_legal_decks": 4, "live_unknown_decks": 4, "reprint_and_errata_checked": True,
        "separate_public_dbs": True, "read_only_cache_unchanged": True, "network_forbidden": True,
        "owner_database_opened": False, "real_public_cache_verified": False,
    }))
    ET.SubElement(properties, "property", name="public_deck_knowledge_reproduction", value=json.dumps({
        "scope": "SYNTHETIC_PUBLIC_DECK_KNOWLEDGE_ONLY", "guides": 4, "cards_per_export": 60,
        "sourced_alias_bridge": True, "ambiguous_alias_unknown": True, "no_name_guessing": True,
        "facts_and_hypotheses_separate": True, "unknown_live_and_matchups": True,
        "read_only_cache_unchanged": True, "network_forbidden": True,
        "owner_database_opened": False, "real_public_cache_verified": False,
    }))
    ET.SubElement(properties, "property", name="public_deck_library_matchup_reproduction", value=json.dumps({
        'scope': 'SYNTHETIC_DECK_LIBRARY_MATCHUP_ONLY', 'public_compositions': 4, 'public_placements': 6,
        'exports60': 4, 'valid_games': 5, 'v1_hypothesized_losses': 2, 'v1_decided_n': 2,
        'v1_unknown_outcomes': 1, 'v2_hypothesized_wins': 1, 'unattested_games': 1,
        'hidden_draw_excluded': True, 'proxy_is_not_exact_deck': True,
        'duplicates_and_versions_checked': True, 'no_invented_mee_equivalence': True,
        'read_only_unchanged': True, 'network_forbidden': True,
        'real_personal_records_opened': False, 'real_public_cache_verified': False,
    }))
    from test_counter_deck_learning import EVIDENCE
    ET.SubElement(properties, "property", name="public_counter_learning_reproduction", value=json.dumps(EVIDENCE))
    from test_owner_selected_match_review import EVIDENCE as SELECTED
    ET.SubElement(properties, "property", name="owner_selected_match_review_reproduction", value=json.dumps(SELECTED))
    ET.ElementTree(root).write(junit, encoding="utf-8")
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    monkeypatch.setenv("GITHUB_RUN_ID", "123")
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setattr(sys, "argv", ["write_ci_evidence.py", str(junit)])
    return summary


def test_ci_publishes_scoped_evidence_and_filters_unexpected_text(local_tmp, monkeypatch, capsys):
    report = _report()
    report["untrusted_extra"] = "MUST_NOT_BE_PUBLISHED"
    report["verdicts"][0]["untrusted_extra"] = "MUST_NOT_BE_PUBLISHED"
    summary = _context(local_tmp, monkeypatch, report)
    assert publisher.main() == 0
    output = capsys.readouterr().out
    emitted = json.loads(output.split("rules_registry_evidence=", 1)[1])
    assert emitted["sha"] == "a" * 40
    assert emitted["review_assertions"] == 16 and not emitted["local_database_verified"]
    assert "MUST_NOT_BE_PUBLISHED" not in output + summary.read_text(encoding="utf-8")
    assert "synthétiques" in summary.read_text(encoding="utf-8")


def test_ci_combines_independent_core_and_qt_reports(local_tmp, monkeypatch, capsys):
    summary = _context(local_tmp, monkeypatch, _report())
    qt = local_tmp / 'invented-qt.xml'
    ET.ElementTree(ET.Element('testsuite', tests='2', failures='0', errors='0', skipped='0')).write(qt)
    monkeypatch.setattr(sys, 'argv', [*sys.argv, str(qt)])
    assert publisher.main() == 0
    assert 'passed=3 skipped=0' in capsys.readouterr().out
    assert '3 passed' in summary.read_text(encoding='utf-8')


@pytest.mark.parametrize('fault', ['failures', 'errors'])
def test_ci_cannot_hide_a_failed_independent_qt_report(local_tmp, monkeypatch, capsys, fault):
    summary = _context(local_tmp, monkeypatch, _report())
    qt = local_tmp / 'invented-qt.xml'
    counts = dict(tests='1', failures='0', errors='0', skipped='0')
    counts[fault] = '1'
    ET.ElementTree(ET.Element('testsuite', **counts)).write(qt)
    monkeypatch.setattr(sys, 'argv', [*sys.argv, str(qt)])
    assert publisher.main() == 2
    assert 'TECHNICAL_TESTS_GREEN' not in capsys.readouterr().out
    assert not summary.exists()


@pytest.mark.parametrize("fault", ["missing", "duplicate", "scope", "local", "hash", "canonical", "verdict", "counts", "failed_suite"])
def test_ci_cannot_claim_reproduction_without_the_required_checks(local_tmp, monkeypatch, capsys, fault):
    report = _report()
    if fault == "scope":
        report["scope"] = "LOCAL_PC_VERIFIED"
    elif fault == "local":
        report["local_database_verified"] = True
    elif fault == "hash":
        report["registry_sha256"] = {}
    elif fault == "canonical":
        report["registry_canonical_sha256"] = {}
    elif fault == "verdict":
        report["verdicts"][-1]["status"] = "legal"
    elif fault == "counts":
        report["sqlite_totals"]["assertions"] = 21
    summary = _context(local_tmp, monkeypatch, report,
                       copies=0 if fault == "missing" else 2 if fault == "duplicate" else 1,
                       failures=int(fault == "failed_suite"))
    assert publisher.main() == 2
    assert "TECHNICAL_TESTS_GREEN" not in capsys.readouterr().out
    assert not summary.exists()


@pytest.mark.parametrize("fault", ["missing", "duplicate", "real_cache", "cards"])
def test_competitive_evidence_cannot_upgrade_real_pc_cache(local_tmp, monkeypatch, capsys, fault):
    summary = _context(local_tmp, monkeypatch, _report())
    path = Path(sys.argv[1])
    doc = ET.parse(path)
    properties = doc.find("testsuite/properties")
    node = next(p for p in properties if p.get("name") == "public_competitive_reproduction")
    report = json.loads(node.get("value"))
    if fault == "missing":
        properties.remove(node)
    elif fault == "duplicate":
        ET.SubElement(properties, "property", **node.attrib)
    elif fault == "real_cache":
        report["real_public_cache_verified"] = True
        node.set("value", json.dumps(report))
    elif fault == "cards":
        report["total_cards"] = 59
        node.set("value", json.dumps(report))
    doc.write(path, encoding="utf-8")
    assert publisher.main() == 2
    assert "TECHNICAL_TESTS_GREEN" not in capsys.readouterr().out
    assert not summary.exists()


@pytest.mark.parametrize('fault',['missing','duplicate','real_cache','changed','network','counts'])
def test_advisor_evidence_is_required_and_synthetic(local_tmp,monkeypatch,capsys,fault):
    summary=_context(local_tmp,monkeypatch,_report())
    path=Path(sys.argv[1]);doc=ET.parse(path);properties=doc.find('testsuite/properties')
    node=next(p for p in properties if p.get('name')=='public_competitive_advisor_reproduction')
    report=json.loads(node.get('value'))
    if fault=='missing':
        properties.remove(node)
    elif fault=='duplicate':
        ET.SubElement(properties,'property',**node.attrib)
    else:
        key={'real_cache':'real_public_cache_verified','changed':'read_only_cache_unchanged','network':'network_forbidden','counts':'distinct_compositions'}[fault]
        report[key]=True if fault=='real_cache' else False if fault in {'changed','network'} else 6
        node.set('value',json.dumps(report))
    doc.write(path,encoding='utf-8')
    assert publisher.main()==2
    assert 'TECHNICAL_TESTS_GREEN' not in capsys.readouterr().out
    assert not summary.exists()


@pytest.mark.parametrize('fault', ['missing', 'duplicate', 'real_cache', 'changed', 'network', 'counts', 'scope'])
def test_preflight_evidence_is_required_and_synthetic(local_tmp, monkeypatch, capsys, fault):
    summary = _context(local_tmp, monkeypatch, _report())
    path = Path(sys.argv[1])
    doc = ET.parse(path)
    properties = doc.find('testsuite/properties')
    node = next(p for p in properties if p.get('name') == 'public_deck_preflight_reproduction')
    report = json.loads(node.get('value'))
    if fault == 'missing':
        properties.remove(node)
    elif fault == 'duplicate':
        ET.SubElement(properties, 'property', **node.attrib)
    else:
        key = {'real_cache': 'real_public_cache_verified', 'changed': 'read_only_cache_unchanged',
               'network': 'network_forbidden', 'counts': 'live_unknown_decks', 'scope': 'scope'}[fault]
        report[key] = True if fault == 'real_cache' else 'REAL_PC_VERIFIED' if fault == 'scope' else False if fault in {'changed', 'network'} else 0
        node.set('value', json.dumps(report))
    doc.write(path, encoding='utf-8')
    assert publisher.main() == 2
    assert 'TECHNICAL_TESTS_GREEN' not in capsys.readouterr().out
    assert not summary.exists()


@pytest.mark.parametrize('fault', ['missing', 'duplicate', 'scope', 'real_cache', 'network', 'cards', 'unexpected'])
def test_knowledge_ci_evidence_is_scoped(local_tmp, monkeypatch, capsys, fault):
    summary = _context(local_tmp, monkeypatch, _report())
    path = Path(sys.argv[1])
    doc = ET.parse(path)
    properties = doc.find('testsuite/properties')
    node = next(p for p in properties if p.get('name') == 'public_deck_knowledge_reproduction')
    report = json.loads(node.get('value'))
    if fault == 'missing':
        properties.remove(node)
    elif fault == 'duplicate':
        ET.SubElement(properties, 'property', **node.attrib)
    else:
        key = {'scope': 'scope', 'real_cache': 'real_public_cache_verified', 'network': 'network_forbidden',
               'cards': 'cards_per_export', 'unexpected': 'untrusted_extra'}[fault]
        report[key] = {'scope': 'REAL_PC', 'real_cache': True, 'network': False, 'cards': 59,
                       'unexpected': 'MUST_NOT_PUBLISH'}[fault]
        node.set('value', json.dumps(report))
    doc.write(path, encoding='utf-8')
    assert publisher.main() == (0 if fault == 'unexpected' else 2)
    output = capsys.readouterr().out
    assert 'MUST_NOT_PUBLISH' not in output
    if fault != 'unexpected':
        assert 'TECHNICAL_TESTS_GREEN' not in output and not summary.exists()


@pytest.mark.parametrize('fault',['missing','duplicate','scope','personal','real_cache','network','games','losses','n','versions','hidden','proxy','mee','unexpected'])
def test_library_matchup_evidence_is_synthetic_only(local_tmp,monkeypatch,capsys,fault):
    summary=_context(local_tmp,monkeypatch,_report())
    path=Path(sys.argv[1]);doc=ET.parse(path);props=doc.find('testsuite/properties')
    node=next(p for p in props if p.get('name')=='public_deck_library_matchup_reproduction')
    report=json.loads(node.get('value'))
    if fault=='missing':
        props.remove(node)
    elif fault=='duplicate':
        ET.SubElement(props,'property',**node.attrib)
    else:
        key,value={'scope':('scope','REAL_PC_CERTIFIED'),'personal':('real_personal_records_opened',True),
            'real_cache':('real_public_cache_verified',True),'network':('network_forbidden',False),
            'games':('valid_games',9),'losses':('v1_hypothesized_losses',3),'n':('v1_decided_n',5),
            'versions':('duplicates_and_versions_checked',False),'hidden':('hidden_draw_excluded',False),
            'proxy':('proxy_is_not_exact_deck',False),'mee':('no_invented_mee_equivalence',False),
            'unexpected':('untrusted','MUST_NOT_PUBLISH')}[fault]
        report[key]=value;node.set('value',json.dumps(report))
    doc.write(path,encoding='utf-8')
    assert publisher.main()==(0 if fault=='unexpected' else 2)
    output=capsys.readouterr().out
    assert 'MUST_NOT_PUBLISH' not in output
    if fault!='unexpected':
        assert 'TECHNICAL_TESTS_GREEN' not in output and not summary.exists()


@pytest.mark.parametrize('fault', ['missing', 'duplicate', 'scope', 'personal', 'causality', 'count', 'type', 'extra'])
def test_counter_learning_evidence_is_required_and_cannot_certify_pc(local_tmp, monkeypatch, capsys, fault):
    _context(local_tmp, monkeypatch, _report())
    path = Path(sys.argv[1])
    tree = ET.parse(path)
    props = tree.getroot().find('testsuite/properties')
    node = next(p for p in props if p.get('name') == 'public_counter_learning_reproduction')
    value = json.loads(node.get('value'))
    if fault == 'missing': props.remove(node)
    elif fault == 'duplicate': ET.SubElement(props, 'property', name=node.get('name'), value=node.get('value'))
    else:
        if fault == 'scope': value['scope'] = 'REAL_PLAYER_MATCHES'
        if fault == 'personal': value['real_personal_records_opened'] = True
        if fault == 'causality': value['no_causal_improvement'] = False
        if fault == 'count': value['cards_per_export'] = 59
        if fault == 'type': value['duplicate_excluded'] = True
        if fault == 'extra': value['untrusted'] = 'MUST_NOT_PUBLISH'
        node.set('value', json.dumps(value))
    tree.write(path, encoding='utf-8')
    assert publisher.main() == (0 if fault == 'extra' else 2)
    output = capsys.readouterr().out
    assert 'MUST_NOT_PUBLISH' not in output
    if fault == 'extra': assert 'counter_learning_evidence=' in output


@pytest.mark.parametrize("fault", ["missing", "duplicate", "scope", "personal", "consents", "network", "type", "extra"])
def test_selected_review_evidence_cannot_certify_real_records(local_tmp, monkeypatch, capsys, fault):
    summary = _context(local_tmp, monkeypatch, _report())
    path = Path(sys.argv[1])
    tree = ET.parse(path)
    props = tree.find("testsuite/properties")
    node = next(p for p in props if p.get("name") == "owner_selected_match_review_reproduction")
    report = json.loads(node.get("value"))
    if fault == "missing": props.remove(node)
    elif fault == "duplicate": ET.SubElement(props, "property", **node.attrib)
    else:
        key, value = {"scope": ("scope", "REAL_DATA_VERIFIED"), "personal": ("real_personal_records_opened", True),
            "consents": ("distinct_consents", 1), "network": ("network_forbidden", False),
            "type": ("import_does_not_attest", 1), "extra": ("untrusted", "MUST_NOT_PUBLISH")}[fault]
        report[key] = value
        node.set("value", json.dumps(report))
    tree.write(path, encoding="utf-8")
    assert publisher.main() == (0 if fault == "extra" else 2)
    output = capsys.readouterr().out
    assert "MUST_NOT_PUBLISH" not in output
    if fault != "extra": assert not summary.exists() and "TECHNICAL_TESTS_GREEN" not in output
    else: assert "selected_match_review_evidence=" in output
