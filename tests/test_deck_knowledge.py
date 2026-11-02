"""Invented PUBLIC knowledge only; real decks and source bodies never enter CI."""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing

import pytest

from pokemind import cli, competitive as c, deck_knowledge as k, public_deck_preflight as p
from pokemind.cards import _canonical_sha256
from pokemind.catalog_batch_store import initialize_batch_tables
from pokemind.database import connect_readonly
from pokemind.set_code_aliases import build_aliases, collector_key
from test_competitive_advisor import AS_OF, sample, tree_bytes
from test_public_deck_preflight import reference, forbid_all


EVIDENCE = {
    "scope": "SYNTHETIC_PUBLIC_DECK_KNOWLEDGE_ONLY", "guides": 4, "cards_per_export": 60,
    "sourced_alias_bridge": True, "ambiguous_alias_unknown": True, "no_name_guessing": True,
    "facts_and_hypotheses_separate": True, "unknown_live_and_matchups": True,
    "read_only_cache_unchanged": True, "network_forbidden": True,
    "owner_database_opened": False, "real_public_cache_verified": False,
}


def enriched(root):
    db = sample(root)
    ref = reference(root, db)
    with closing(sqlite3.connect(ref)) as con, con:
        con.row_factory = sqlite3.Row
        initialize_batch_tables(con)
        con.execute("INSERT INTO catalog_batch_queries VALUES ('synthetic',?,?)", (json.dumps({
            "operation": "query", "source_url": "https://api.tcgdex.net/v2/graphql", "query_sha256": 'a' * 64}), AS_OF))
        for row in con.execute("SELECT * FROM catalog_sets").fetchall():
            sid = row["tcgdex_id"]
            members = [dict(r) for r in con.execute(
                "SELECT p.tcgdex_id AS id,p.local_id AS localId,t.name FROM catalog_printings p "
                "JOIN catalog_translations t ON p.tcgdex_id=t.printing_id AND t.language='en' WHERE p.set_id=?", (sid,))]
            payload = {"id": sid, "name": "Invented set", "abbreviation": {"official": row["tcg_online_code"]},
                       "releaseDate": "2026-01-01", "cards": members}
            digest = _canonical_sha256(payload)
            con.execute("INSERT INTO catalog_detail_payloads VALUES ('sets',?,'en',?,?, 'synthetic')",
                        (sid, json.dumps(payload), digest))
            con.execute("UPDATE catalog_sets SET tcg_online_code=NULL,abbreviation_official=?,content_sha256_en=?,"
                        "source_url_en='https://api.tcgdex.net/v2/en/sets/synthetic',retrieved_at_en=? WHERE tcgdex_id=?",
                        (payload['abbreviation']['official'], digest, AS_OF, sid))
        rows = con.execute("SELECT p.*,t.name FROM catalog_printings p JOIN catalog_translations t "
                           "ON t.printing_id=p.tcgdex_id AND t.language='en'").fetchall()
        for row in rows:
            payload = {"id": row["tcgdex_id"], "name": row["name"], "category": row["category"],
                       "stage": row["stage"], "energyType": "Basic" if row["category"] == "energy" else None,
                       "abilities": [{"name": "Synthetic ability", "effect": "Once during your turn, draw a card."}],
                       "attacks": [{"name": "Synthetic strike", "cost": ["Colorless"], "damage": 10}],
                       "effect": "Search your deck for a card, then shuffle your deck."}
            digest = _canonical_sha256(payload)
            con.execute("INSERT INTO catalog_detail_payloads VALUES ('cards',?,'en',?,?,'synthetic')",
                        (row["tcgdex_id"], json.dumps(payload), digest))
            con.execute("UPDATE catalog_translations SET payload_sha256=?,effect=?,abilities_json=?,attacks_json=? "
                        "WHERE printing_id=? AND language='en'", (digest, payload['effect'], json.dumps(payload['abilities']),
                                                               json.dumps(payload['attacks']), row['tcgdex_id']))
    return db, ref


def show(root, db, ref, selector="123:1", **kwargs):
    return k.knowledge_show(root, db, ref, selector=selector, as_of=kwargs.pop("as_of", AS_OF),
                            use_set_aliases=kwargs.pop("aliases", True), **kwargs)


def preflight(root, db, ref, **kw):
    return p.competitive_preflight(root, db, ref, as_of=AS_OF, format="standard", platform=kw.pop("platform", "in_person"),
                                   use_set_aliases=kw.pop("aliases", True), **kw)


def test_knowledge_reproduction(local_tmp, monkeypatch, record_testsuite_property):
    db, ref = enriched(local_tmp)
    before = tree_bytes(db.parent), tree_bytes(ref.parent)
    forbid_all(monkeypatch)
    baseline = preflight(local_tmp, db, ref, aliases=False)
    mapped = preflight(local_tmp, db, ref)
    assert all(o['counts']['identity']['resolved'] == 0 for o in baseline['options'])
    assert all(o['counts']['identity']['unresolved'] == 0 for o in mapped['options'])
    assert preflight(local_tmp, db, ref, platform="live")['deck_status_counts']['unknown'] == 4
    reports = [show(local_tmp, db, ref, o['selector']) for o in mapped['options']]
    assert len(reports) == 4
    for report in reports:
        assert c.parse_deck_export(report['export']['text']).total_cards == 60
        assert report['export']['clipboard_used'] is False
        assert report['uncertainty']['live_availability'] == report['uncertainty']['matchups'] == 'unknown'
        assert report['uncertainty']['strength_ranking'] is None
        assert report['strategic_claim'] and report['card_role']
        assert all(x['kind'] in {'fact', 'inference', 'hypothesis_to_test', 'unknown'} for x in report['strategic_claim'])
        assert all(x['support'] and x['dated_provenance'] and x['conditions'] for x in report['strategic_claim'])
        assert all(x['observed_card_text']['kind'] == 'fact' for x in report['card_role'])
        assert report['version_sha256'] == show(local_tmp, db, ref, report['variant']['selector'])['version_sha256']
        assert 'DO_NOT_STORE' not in json.dumps(report)
    assert (tree_bytes(db.parent), tree_bytes(ref.parent)) == before
    # Only after the RO invariant, inject a conflicting synthetic native code.
    with closing(sqlite3.connect(ref)) as con, con:
        con.execute("UPDATE catalog_sets SET tcg_online_code='SYN' WHERE tcgdex_id='alt'")
    ambiguous = preflight(local_tmp, db, ref, selectors=['123:1'])['options'][0]
    assert ambiguous['counts']['identity']['ambiguous'] > 0 and ambiguous['status'] == 'unknown'
    assert show(local_tmp, db, ref)['uncertainty']['missing_card_text']
    record_testsuite_property("public_deck_knowledge_reproduction", json.dumps(EVIDENCE))


@pytest.mark.parametrize('fault', ['missing_payload', 'hash', 'code', 'membership', 'name', 'future_release',
                                  'future_source', 'stale', 'untrusted_url', 'wrong_id'])
def test_alias_requires_cross_checked_source(local_tmp, fault):
    db, ref = enriched(local_tmp)
    with closing(sqlite3.connect(ref)) as con, con:
        if fault == 'missing_payload':
            con.execute("DELETE FROM catalog_detail_payloads WHERE kind='sets' AND entity_id='syn'")
        elif fault in {'hash', 'code', 'future_source', 'stale', 'untrusted_url'}:
            field, value = {'hash': ('content_sha256_en', '0' * 64), 'code': ('abbreviation_official', 'FALSE'),
                            'future_source': ('retrieved_at_en', '2027-01-01'), 'stale': ('detail_stale_en', 1),
                            'untrusted_url': ('source_url_en', 'https://untrusted.invalid/source')}[fault]
            con.execute(f"UPDATE catalog_sets SET {field}=? WHERE tcgdex_id='syn'", (value,))
        else:
            payload = json.loads(con.execute("SELECT payload_json FROM catalog_detail_payloads WHERE kind='sets' AND entity_id='syn'").fetchone()[0])
            if fault == 'membership':
                payload['cards'] = []
            elif fault == 'name':
                for item in payload['cards']:
                    item['name'] = 'Wrong name'
            elif fault == 'future_release':
                payload['releaseDate'] = '2027-01-01'
            else:
                payload['id'] = 'false-set'
            digest = _canonical_sha256(payload)
            con.execute("UPDATE catalog_detail_payloads SET payload_json=?,payload_sha256=? WHERE kind='sets' AND entity_id='syn'",
                        (json.dumps(payload), digest))
            con.execute("UPDATE catalog_sets SET content_sha256_en=? WHERE tcgdex_id='syn'", (digest,))
    option = preflight(local_tmp, db, ref, selectors=['123:1'])['options'][0]
    assert option['counts']['identity']['unresolved'] > 0
    assert option['status'] == 'unknown'


@pytest.mark.parametrize('kind', ['alias_conflict', 'native_conflict'])
def test_ambiguous_set_cannot_be_disambiguated_by_a_convenient_name(local_tmp, kind):
    db, ref = enriched(local_tmp)
    with closing(sqlite3.connect(ref)) as con, con:
        if kind == 'native_conflict':
            con.execute("UPDATE catalog_sets SET tcg_online_code='SYN' WHERE tcgdex_id='alt'")
        else:
            payload = json.loads(con.execute("SELECT payload_json FROM catalog_detail_payloads WHERE kind='sets' AND entity_id='alt'").fetchone()[0])
            payload['abbreviation']['official'] = 'SYN'
            digest = _canonical_sha256(payload)
            con.execute("UPDATE catalog_detail_payloads SET payload_json=?,payload_sha256=? WHERE kind='sets' AND entity_id='alt'", (json.dumps(payload), digest))
            con.execute("UPDATE catalog_sets SET abbreviation_official='SYN',content_sha256_en=? WHERE tcgdex_id='alt'", (digest,))
    option = preflight(local_tmp, db, ref, selectors=['123:1'])['options'][0]
    assert option['counts']['identity']['ambiguous'] > 0
    assert 'SET_CODE_ALIAS_AMBIGUOUS' in option['blockers']
    assert option['status'] == 'unknown'


@pytest.mark.parametrize('fault', ['no_text', 'stale', 'future', 'wrong_name', 'hash', 'no_attacks'])
def test_no_generated_text_or_strategy_when_source_is_insufficient(local_tmp, fault):
    db, ref = enriched(local_tmp)
    with closing(sqlite3.connect(ref)) as con, con:
        if fault == 'no_text':
            con.execute("DELETE FROM catalog_detail_payloads WHERE kind='cards'")
        elif fault == 'stale':
            con.execute("UPDATE catalog_printings SET detail_stale_en=1")
        elif fault == 'future':
            con.execute("UPDATE catalog_translations SET retrieved_at='2027-01-01'")
        elif fault == 'wrong_name':
            con.execute("UPDATE catalog_translations SET name='Wrong'")
        elif fault == 'hash':
            con.execute("UPDATE catalog_translations SET payload_sha256='bad'")
        else:
            rows = con.execute("SELECT entity_id,payload_json FROM catalog_detail_payloads WHERE kind='cards'").fetchall()
            for entity, raw in rows:
                payload = json.loads(raw)
                payload.update(attacks=None, abilities=None, effect=None)
                digest = _canonical_sha256(payload)
                con.execute("UPDATE catalog_detail_payloads SET payload_json=?,payload_sha256=? WHERE kind='cards' AND entity_id=?", (json.dumps(payload), digest, entity))
                con.execute("UPDATE catalog_translations SET payload_sha256=? WHERE printing_id=?", (digest, entity))
    report = show(local_tmp, db, ref)
    assert report['status'] == 'PARTIAL_WITH_EVIDENCE'
    if fault != 'no_attacks':
        assert report['uncertainty']['missing_card_text']
    assert not report['attack_options']
    assert not any(x['section'] == 'attacks' for x in report['strategic_claim'])


def test_decimal_padding_only(local_tmp):
    assert collector_key('008') == collector_key('8')
    assert collector_key('TG08') != collector_key('8')
    db, ref = enriched(local_tmp)
    with closing(sqlite3.connect(ref)) as con, con:
        con.execute("UPDATE catalog_printings SET local_id='1' WHERE tcgdex_id='syn-001'")
    assert show(local_tmp, db, ref)['card_role'][0]['identity_status'] == 'resolved'


def test_cli_and_private_fallback_refused(local_tmp, monkeypatch, capsys):
    db, ref = enriched(local_tmp)
    monkeypatch.setattr(cli, 'find_project_root', lambda: local_tmp)
    forbid_all(monkeypatch)
    args = ['meta', 'deck-knowledge', '--selector', '123:1', '--as-of', AS_OF,
            '--reference-db', str(ref), '--set-aliases']
    assert cli.main(args + ['--json']) == 2
    assert json.loads(capsys.readouterr().out)['status'] == 'BLOCKED_WITH_REASON'
    assert cli.main(args + ['--db', str(db), '--json']) == 0
    assert json.loads(capsys.readouterr().out)['export']['total_cards'] == 60
    assert cli.main(args + ['--db', str(db)]) == 0
    assert 'Export 60/60' in capsys.readouterr().out
    assert cli.main(args + ['--db', str(local_tmp / 'data/local/pokemind.sqlite3'), '--json']) == 2
    assert json.loads(capsys.readouterr().out)['status'] == 'BLOCKED_WITH_REASON'


@pytest.mark.parametrize('value', ['tomorrow', '2026-2-01', '2026-02-30'])
def test_invalid_dates_before_io(local_tmp, monkeypatch, value):
    monkeypatch.setattr(p, 'require_public_database', lambda *a: pytest.fail('no file access'))
    with pytest.raises(ValueError):
        show(local_tmp, local_tmp / 'unused', local_tmp / 'unused-ref', as_of=value)


def test_source_disagreement_is_blocked(local_tmp):
    db, ref = enriched(local_tmp)
    with closing(sqlite3.connect(db)) as con, con:
        con.execute("UPDATE meta_competitive_lists SET page_sha256=?", ('0' * 64,))
    with pytest.raises(ValueError):
        show(local_tmp, db, ref)


def test_roles_require_text_not_card_name():
    assert k._roles(None) == []
    observation = {'fields': {'name': 'Draw Search Energy Master', 'effect': None, 'abilities': None, 'attacks': None},
                   'dated_provenance': {'provider': 'synthetic'}}
    assert k._roles(observation) == []
    observation['fields']['effect'] = "You cannot draw 2 cards or search your deck."
    assert not any(r['role'] in {'draw', 'search'} for r in k._roles(observation))


def test_source_content_change_versions_the_guide(local_tmp):
    db, ref = enriched(local_tmp)
    first = show(local_tmp, db, ref)
    with closing(sqlite3.connect(ref)) as con, con:
        payload = json.loads(con.execute("SELECT payload_json FROM catalog_detail_payloads WHERE kind='cards' AND entity_id='syn-001'").fetchone()[0])
        payload['effect'] = 'Synthetic revision: draw 2 cards.'
        digest = _canonical_sha256(payload)
        con.execute("UPDATE catalog_detail_payloads SET payload_json=?,payload_sha256=? WHERE kind='cards' AND entity_id='syn-001'", (json.dumps(payload), digest))
        con.execute("UPDATE catalog_translations SET payload_sha256=? WHERE printing_id='syn-001' AND language='en'", (digest,))
    second = show(local_tmp, db, ref)
    assert first['version_sha256'] != second['version_sha256']
    assert first['variant'] == second['variant']


@pytest.mark.parametrize('fault', ['none', 'commit', 'object_url', 'blob', 'language', 'operation', 'missing_object'])
def test_pinned_importer_provenance_is_checked(local_tmp, fault):
    db, ref = enriched(local_tmp)
    with closing(sqlite3.connect(ref)) as con, con:
        objects = {row[0]: {'source_url': 'https://github.com/tcgdex/cards-database/blob/' + 'c' * 40 + '/data/synthetic/' + row[0] + '.ts',
                            'git_blob': 'b' * 40} for row in con.execute('SELECT entity_id FROM catalog_detail_payloads')}
        proof = {'operation': 'literal_snapshot', 'source_commit': 'c' * 40, 'source_objects': objects,
                 'source_url': 'https://github.com/tcgdex/cards-database/tree/' + 'c' * 40 + '/data'}
        if fault == 'commit':
            proof['source_commit'] = 'bad'
        elif fault == 'object_url':
            for item in objects.values():
                item['source_url'] = 'https://github.com/another/repo/blob/main/data/fake.ts'
        elif fault == 'blob':
            for item in objects.values():
                item['git_blob'] = 'bad'
        elif fault == 'language':
            proof['language'] = 'fr'
        elif fault == 'operation':
            proof['operation'] = 'unknown'
        elif fault == 'missing_object':
            proof['source_objects'] = {}
        con.execute("UPDATE catalog_batch_queries SET evidence_json=?", (json.dumps(proof),))
    report = show(local_tmp, db, ref)
    if fault == 'none':
        assert all(r['observed_card_text'] for r in report['card_role'])
        assert all(r['observed_card_text']['dated_provenance']['source_commit'] == 'c' * 40 for r in report['card_role'])
    else:
        assert report['preflight']['counts']['identity']['resolved'] == 0
        assert len(report['uncertainty']['missing_card_text']) == len(report['card_role'])
        assert not report['strategic_claim']
