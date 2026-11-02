"""Entirely invented pages/lists; never import the real tournament cache."""
from __future__ import annotations

import hashlib
import json
import socket
from dataclasses import replace
from html import escape
from pathlib import Path

import pytest

from pokemind import cli, competitive as c


AS_OF = "2026-10-22"
EVENT_URL = "https://www.limitlesstcg.com/tournaments/123"


def deck_page(cards):
    result = '<div data-text-decklist>'
    for kind, label in (("pokemon", "Pokémon"), ("trainer", "Trainer"), ("energy", "Energy")):
        section = [card for card in cards if card.card_type == kind]
        result += f'<div class="decklist-column"><div class="decklist-column-heading">{label} ({sum(x.quantity for x in section)})</div>'
        for card in section:
            result += (f'<div class="decklist-card" data-set="{card.set_code}" data-number="{card.collector_number}" data-lang="en">'
                       f'<span class="card-count">{card.quantity}</span><span class="card-name">{escape(card.name)}</span></div>')
        result += '</div>'
    return (result + '</div>').encode('utf-8')


def sample(root, campaign="advisor-synthetic", *, duplicates=0, dragapult_variants=False, printing_conflict=False, ambiguous_label=False):
    target = c.create_workspace(root, campaign)
    db = target / "public.sqlite3"
    cards = c.parse_deck_export((Path(__file__).parent / "fixtures/decks/valid_en.txt").read_text(encoding="utf-8")).cards
    changed = list(cards)
    changed[4] = replace(changed[4], quantity=changed[4].quantity + 1,
                         normalized_line="5 Research Notes SYN 101")
    changed[-1] = replace(changed[-1], quantity=changed[-1].quantity - 1,
                          normalized_line="4 Basic Psychic Energy SYN 202")
    alternate = list(cards)
    alternate[0] = replace(alternate[0], name="Synthetic Delta", set_code="ALT", collector_number="301",
                            normalized_line="4 Synthetic Delta ALT 301")
    if printing_conflict:
        alternate[0] = replace(alternate[0], set_code="SYN", collector_number="001",
                                normalized_line="4 Synthetic Delta SYN 001")
    other = list(cards)
    other[-1] = replace(other[-1], name="Synthetic Energy", set_code="ALT", collector_number="401",
                        normalized_line="5 Synthetic Energy ALT 401")
    definitions = [("Dragapult", 1001, cards), ("Dragapult", 1001, cards),
                   ("Dragapult", 1003, cards), ("Basic Box", 1004, changed),
                   ("Hydrapple", 1005, alternate), ("Dhelmise", 1006, other)]
    if ambiguous_label:
        definitions[2] = ('Basic Box', 1003, cards)
    if dragapult_variants:
        definitions[3] = ('Dragapult', 1004, changed)
        definitions[4] = ('Dragapult', 1005, alternate)
    definitions += [("Dragapult", 1004, changed) if dragapult_variants else ("Dragapult", 1001, cards)] * duplicates
    body = '<div class="infobox-heading">Synthetic Regional</div><div class="infobox-line">10th October 2026 • 20 Players</div>'
    body += '<a href="/decks/?time=all&amp;format=SYN">Synthetic range</a><table>'
    for rank, (label, list_id, _) in enumerate(definitions, 1):
        body += f'<tr data-rank="{rank}" data-deck="{label}" data-name="DO_NOT_STORE"><td><a href="/decks/list/{list_id}">List</a></td></tr>'
    event_body = (body + '</table>').encode('utf-8')
    index_body = (b'<tr><td>10 Oct 26</td><td>XX</td><td><a href="/tournaments/123">Synthetic Regional</a></td>'
                  b'<td><img alt="standard"></td><td>20</td><td>DO_NOT_STORE</td></tr>')
    event = c.qualify_standard(c.parse_event(event_body, EVENT_URL, as_of=AS_OF), index_body)
    payloads = {c.INDEX_URL: index_body, EVENT_URL: event_body}
    for _, list_id, source_cards in definitions:
        payloads[f"https://www.limitlesstcg.com/decks/list/{list_id}"] = deck_page(source_cards)
    payloads['https://www.limitlesstcg.com/cards/SYN/001'] = (
        b'<span class="card-text-name">Creature Alpha</span>'
        b'<p class="card-text-type">Pokemon - Stage 2 - Evolves from Synthetic</p>')
    records = []
    for url, payload in payloads.items():
        digest = hashlib.sha256(payload).hexdigest()
        (target / "pages" / (digest + ".body")).write_bytes(payload)
        records.append({"url": url, "sha256": digest, "state": "complete", "http_status": 200,
                        "fetched_at": "2026-10-22T18:00:00Z", "bytes": len(payload)})
    ledger = {"requests": records, "gets": len(records), "bytes": sum(r["bytes"] for r in records), "stopped": "COMPLETED_BATCH_NO_RESTART"}
    (target / "requests.json").write_text(json.dumps(ledger), encoding="utf-8")
    rows = []
    for placement in event["placements"]:
        record = next(r for r in records if r["url"] == placement["list_url"])
        rows.append({**placement, "page_sha256": record["sha256"], "fetched_at": record["fetched_at"],
                     "deck_text": c.parse_list(payloads[placement["list_url"]])})
    c.store_event(root, db, event, rows)
    return db


def tree_bytes(target):
    return {str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in target.rglob('*') if p.is_file()}


def forbid_io(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("network/client/write/default owner resolver forbidden")
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(c.BoundedPages, "__init__", forbidden)
    monkeypatch.setattr(c, "connect_writable", forbidden)
    monkeypatch.setattr(cli, "_db_for", forbidden)
    monkeypatch.setattr(cli, "default_db_path", forbidden)


def test_complete_offline_advisor_read_only_and_source_aware(local_tmp, monkeypatch, record_testsuite_property):
    db = sample(local_tmp)
    before = tree_bytes(db.parent)
    forbid_io(monkeypatch)
    report = c.competitive_inventory(local_tmp, db, as_of=AS_OF)
    assert report['status'] == 'OK'
    assert report['sampled_placements'] == report['valid_placements'] == 6
    assert report['distinct_compositions'] == 4
    duplicate = next(g for g in report['compositions'] if g['reference'] == '123:1')
    assert duplicate['placements'] == 3 and len(duplicate['source_urls']) == 2
    assert duplicate['placement_range'] == [1, 3]
    comparison = c.competitive_compare(local_tmp, db, '123:1', '123:4', as_of=AS_OF, limit=60)
    assert comparison['changes']['counts'] == {'shared': 59, 'removed': 1, 'added': 1}
    assert comparison['changes']['added'][0]['name'] == 'Research Notes'
    assert comparison['changes']['removed'][0]['name'] == 'Basic Psychic Energy'
    assert comparison['left']['build_facts']['stages_from_cached_text'][0]['stage'] == 'Stage 2'
    assert 'unknown' in comparison['left']['build_facts']['unverified_stages']
    same = c.competitive_compare(local_tmp, db, '123:2', '123:3', as_of=AS_OF)
    assert same['same_composition'] and same['changes']['counts'] == {'shared': 60, 'removed': 0, 'added': 0}
    assert same['requested_selectors'] == {'left':'123:2','right':'123:3'}
    shortlist = c.competitive_shortlist(local_tmp, db, as_of=AS_OF)
    assert len(shortlist['options']) == len({o['composition_id'] for o in shortlist['options']}) == 4
    assert [o['archetypes'][0] for o in shortlist['options']] == ['Dragapult', 'Basic Box', 'Hydrapple', 'Dhelmise']
    for option in shortlist['options']:
        assert option['plan_hypothesis'].startswith('Hypothèse') and option['occurrences']
        event_id, rank = option['export_selector'].split(':')
        assert c.parse_deck_export(c.competitive_export(local_tmp, db, event_id, int(rank))).total_cards == 60
    for value in (report, comparison, shortlist):
        assert value['strength_ranking'] is None and not value['network_used']
        assert not value['owner_database_opened'] and not value['database_mutated']
        assert {'winrate','BO1/BO3','collection','credits'} <= set(value['unknowns'])
        assert 'DO_NOT_STORE' not in json.dumps(value)
    assert tree_bytes(db.parent) == before
    record_testsuite_property('public_competitive_advisor_reproduction', json.dumps({
        'scope': 'SYNTHETIC_OFFLINE_PUBLIC_ADVISOR_ONLY', 'placements': 6, 'distinct_compositions': 4,
        'shortlist_options': 4, 'comparison_shared': 59, 'comparison_removed': 1, 'comparison_added': 1,
        'read_only_cache_unchanged': True, 'network_forbidden': True, 'unknowns_preserved': True,
        'real_public_cache_verified': False, 'owner_database_opened': False,
    },sort_keys=True))


def test_normalized_identity_order_case_and_reprints_are_separate():
    original = (Path(__file__).parent / "fixtures/decks/valid_en.txt").read_text(encoding='utf-8')
    a = c._card_map(original)
    b = c._card_map(original.replace('Creature Alpha SYN 001','creature alpha syn 001'))
    assert c._composition_id(a) == c._composition_id(b)
    assert c._composition_id(a) == c._composition_id(dict(reversed(list(a.items()))))
    d = c._card_map(original.replace('Creature Alpha SYN 001','Creature Alpha ALT 001'))
    assert c._quantitative_diff({'cards':a},{'cards':d},60)['counts'] == {'shared':56,'removed':4,'added':4}
    assert c._composition_id(a) != c._composition_id(d)


@pytest.mark.parametrize('bad', ['123','owner:1','123:0','0:1','../123:1'])
def test_invalid_selector_never_opens_owner_data(local_tmp,bad):
    db=sample(local_tmp)
    with pytest.raises(ValueError,match='SELECTOR'):
        c.competitive_compare(local_tmp,db,bad,'123:1',as_of=AS_OF)


def test_reused_placements_do_not_reweight_shortlist(local_tmp):
    first=sample(local_tmp,'advisor-first',dragapult_variants=True)
    other=sample(local_tmp,'advisor-other',duplicates=6,dragapult_variants=True)
    a=c.competitive_shortlist(local_tmp,first,as_of=AS_OF)
    b=c.competitive_shortlist(local_tmp,other,as_of=AS_OF)
    assert [o['composition_id'] for o in a['options']] == [o['composition_id'] for o in b['options']]
    assert a['options'][0]['reference'] == b['options'][0]['reference'] == '123:1'


@pytest.mark.parametrize('fault',['printing_conflict','ambiguous_label'])
def test_sourced_ambiguity_reported_and_not_used_for_shortlist(local_tmp,fault):
    db=sample(local_tmp,**{fault:True})
    report=c.competitive_inventory(local_tmp,db,as_of=AS_OF)
    assert report['status']=='PARTIAL_WITH_EVIDENCE'
    code='AMBIGUOUS_PRINTING_NAME_OR_TYPE' if fault=='printing_conflict' else 'ARCHETYPE_FAMILY_DISAGREEMENT'
    assert any(issue['code']==code for issue in report['issues'])
    with pytest.raises(ValueError,match='DRAGAPULT_BASE_MISSING'):
        c.competitive_shortlist(local_tmp,db,as_of=AS_OF)


@pytest.mark.parametrize('selector',['123:4','123:99'])
def test_explicit_base_must_be_valid_dragapult(local_tmp,selector):
    db=sample(local_tmp)
    with pytest.raises(ValueError,match='VALID_DRAGAPULT_BASE_REQUIRED|MISSING_INVALID_OR_AMBIGUOUS'):
        c.competitive_shortlist(local_tmp,db,as_of=AS_OF,base=selector)


def test_future_sources_and_truncated_diff_are_explicit(local_tmp):
    db=sample(local_tmp)
    result=c.competitive_inventory(local_tmp,db,as_of='2026-10-09')
    assert result['status']=='PARTIAL_WITH_EVIDENCE' and result['distinct_compositions']==0
    assert result['issues']
    result=c.competitive_compare(local_tmp,db,'123:1','123:5',as_of=AS_OF,limit=1)
    assert result['changes']['omitted_identities']['shared']>0
    assert result['changes']['counts']=={'shared':56,'removed':4,'added':4}


@pytest.mark.parametrize('fault',['invalid_60','printing_missing','source_hash','event_date','missing_page','duplicate_ledger'])
def test_missing_or_ambiguous_sources_never_become_valid(local_tmp,fault):
    db=sample(local_tmp)
    connection=c.connect_writable(db)
    if fault=='invalid_60':
        connection.execute("UPDATE meta_competitive_lists SET deck_text=replace(deck_text,'Total Cards: 60','Total Cards: 59') WHERE placement=4")
    elif fault=='printing_missing':
        connection.execute("UPDATE meta_competitive_lists SET deck_text=replace(deck_text,' SYN 101','') WHERE placement=4")
    elif fault=='source_hash':
        connection.execute("UPDATE meta_competitive_lists SET page_sha256=? WHERE placement=4",('0'*64,))
    elif fault=='event_date':
        metadata=json.loads(connection.execute('SELECT metadata_json FROM meta_competitive_events').fetchone()[0]);metadata['date']='2026-10-11'
        connection.execute('UPDATE meta_competitive_events SET metadata_json=?',(json.dumps(metadata),))
    connection.commit();connection.close()
    ledger_path=db.parent/'requests.json'
    ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
    record=next(r for r in ledger['requests'] if r['url'].endswith('/1004'))
    if fault=='missing_page':
        (db.parent/'pages'/(record['sha256']+'.body')).write_bytes(b'changed synthetic page')
    elif fault=='duplicate_ledger':
        ledger['requests'].append(record);ledger_path.write_text(json.dumps(ledger),encoding='utf-8')
    before=tree_bytes(db.parent)
    result=c.competitive_inventory(local_tmp,db,as_of=AS_OF)
    assert result['status']=='PARTIAL_WITH_EVIDENCE' and result['issues']
    with pytest.raises(ValueError,match='MISSING_INVALID_OR_AMBIGUOUS'):
        c.competitive_compare(local_tmp,db,'123:1','123:4',as_of=AS_OF)
    assert tree_bytes(db.parent)==before


def test_cli_json_human_blocked_and_no_fallback(local_tmp,monkeypatch,capsys):
    db=sample(local_tmp)
    monkeypatch.setattr(cli,'find_project_root',lambda:local_tmp)
    forbid_io(monkeypatch)
    common=['--db',str(db),'--as-of',AS_OF]
    commands=[['competitive-inventory'],['competitive-compare','--left','123:1','--right','123:4','--limit','1'],['competitive-shortlist','--options','2']]
    for command in commands:
        assert cli.main(['meta',*command,*common,'--json'])==0
        value=json.loads(capsys.readouterr().out);assert value['ok'] and not value['network_used']
        assert cli.main(['meta',*command,*common])==0
        text=capsys.readouterr().out;assert 'PUBLIC hors ligne' in text and 'Inconnus' in text
    for command in commands:
        assert cli.main(['meta',*command,'--as-of',AS_OF,'--json'])==2
        value=json.loads(capsys.readouterr().out);assert value['status']=='BLOCKED_WITH_REASON'
    missing=db.parent.parent/'lot-i-missing'/'public.sqlite3'
    assert cli.main(['meta','competitive-inventory','--db',str(missing),'--as-of',AS_OF,'--json'])==2
    assert json.loads(capsys.readouterr().out)['status']=='BLOCKED_WITH_REASON'
    assert cli.main(['meta','competitive-inventory','--db',str(local_tmp/'owner.sqlite3'),'--as-of',AS_OF,'--json'])==2
    assert json.loads(capsys.readouterr().out)['status']=='BLOCKED_WITH_REASON'


def test_source_cache_required_no_download_or_creation(local_tmp):
    target=c.create_workspace(local_tmp,'advisor-empty');db=target/'public.sqlite3'
    with pytest.raises(ValueError,match='PUBLIC_CACHE_MISSING'):
        c.competitive_inventory(local_tmp,db,as_of=AS_OF)
    assert not db.exists()


def test_incomplete_schema_is_blocked_without_migration(local_tmp):
    db=sample(local_tmp)
    connection=c.connect_writable(db)
    connection.execute('ALTER TABLE meta_competitive_lists RENAME COLUMN deck_text TO missing_text')
    connection.commit();connection.close()
    before=tree_bytes(db.parent)
    with pytest.raises(ValueError,match='SCHEMA_INCOMPLETE_NO_MIGRATION'):
        c.competitive_inventory(local_tmp,db,as_of=AS_OF)
    assert tree_bytes(db.parent)==before


@pytest.mark.parametrize('options',[0,1,5,True])
def test_shortlist_option_bounds(local_tmp,options):
    with pytest.raises(ValueError,match='OPTIONS_2_TO_4'):
        c.competitive_shortlist(local_tmp,local_tmp/'owner.sqlite3',as_of=AS_OF,options=options)
