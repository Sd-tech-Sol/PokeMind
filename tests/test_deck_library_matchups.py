"""Invented events/lists/decks/games only; never open owner data in this lot."""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from pokemind import attestations, battle_logs as logs, cli, competitive as c, deck_knowledge as k
from pokemind import deck_library as library, matchup_analytics as a, opponent_observer as o
from pokemind.database import connect_readonly
from pokemind.decks import import_deck
from test_competitive_advisor import AS_OF, sample, tree_bytes
from test_deck_knowledge import enriched
from test_public_deck_preflight import forbid_all


DECK = (Path(__file__).parent / 'fixtures/decks/valid_en.txt').read_text(encoding='utf-8')
EVIDENCE = {
    'scope': 'SYNTHETIC_DECK_LIBRARY_MATCHUP_ONLY', 'public_compositions': 4, 'public_placements': 6,
    'exports60': 4, 'valid_games': 5, 'v1_hypothesized_losses': 2, 'v1_decided_n': 2,
    'v1_unknown_outcomes': 1, 'v2_hypothesized_wins': 1, 'unattested_games': 1,
    'hidden_draw_excluded': True, 'proxy_is_not_exact_deck': True,
    'duplicates_and_versions_checked': True, 'no_invented_mee_equivalence': True,
    'read_only_unchanged': True, 'network_forbidden': True,
    'real_personal_records_opened': False, 'real_public_cache_verified': False,
}


def fictional_log(number=1, *, language='en', outcome='L', card='Synthetic Delta', turns=6):
    if language == 'fr':
        text = 'Joueur de référence : InventedSelf\n'
        for turn in range(1, turns + 1):
            actor = 'InventedSelf' if turn % 2 else 'InventedRival'
            text += f'Tour {turn} - Tour de {actor}\n'
            text += f'{actor} a pioché une carte.\n{actor} a joué {card if actor == "InventedRival" else "Creature Beta"}.\n'
        if outcome in {'W', 'L'}:
            text += ('InventedSelf' if outcome == 'W' else 'InventedRival') + ' a gagné.\n'
    else:
        text = 'Reference player: InventedSelf\n'
        for turn in range(1, turns + 1):
            actor = 'InventedSelf' if turn % 2 else 'InventedRival'
            text += f"Turn # {turn} - {actor}'s Turn\n"
            text += f'{actor} drew a card.\n{actor} played {card if actor == "InventedRival" else "Creature Beta"}.\n'
        if outcome in {'W', 'L'}:
            text += ('InventedSelf' if outcome == 'W' else 'InventedRival') + ' wins.\n'
    return text + f'Invented game marker {number}\n'


def scenario(root, monkeypatch):
    public, ref = enriched(root)
    db = root / 'data/local/invented-matchups.sqlite3'
    import_deck(db, DECK, deck_id='invented', source_kind='stdin')
    changed = DECK.replace('4 Creature Alpha SYN 001', '3 Creature Alpha SYN 001').replace('3 Creature Gamma SYN 003', '4 Creature Gamma SYN 003')
    import_deck(db, changed, deck_id='invented', source_kind='stdin')
    with closing(sqlite3.connect(db)) as con, con:
        con.execute("UPDATE deck_versions SET imported_at='2026-01-01',approved_at='2026-01-01',effective_from='2026-01-01'")
    monkeypatch.setattr(attestations, 'utc_now', lambda: '2026-10-21T12:00:00Z')
    ids = []
    for number, language, outcome, card, version in (
        (1, 'fr', 'L', 'Synthetic Delta', 1), (2, 'en', 'L', 'Synthetic Delta', 1),
        (3, 'en', 'unknown', 'Synthetic Delta', 1), (4, 'en', 'W', 'Synthetic Delta', 2),
        (5, 'en', 'L', 'Creature Alpha', None),
    ):
        battle = logs.import_battle_log(db, fictional_log(number, language=language, outcome=outcome, card=card),
                                        source_kind='stdin', deck_id='invented')
        ids.append(battle['battle_id'])
        with closing(sqlite3.connect(db)) as con, con:
            con.execute("UPDATE battle_logs SET imported_at='2026-10-20T12:00:00Z' WHERE id=?", (ids[-1],))
        if version:
            attestations.confirm_battle_version(db, 'invented', ids[-1], version=version,
                battle_date='2026-10-10', apply=True, confirm_owner=True)
    return db, public, ref, ids


def report(root, db, public, ref, **kwargs):
    return a.matchup_report(root, db, deck_id='invented', as_of=kwargs.pop('as_of', AS_OF),
        confirm_owner_read=True, public_db=public, reference_db=ref, **kwargs)


def test_end_to_end_library_observer_and_matchups(local_tmp, monkeypatch, record_testsuite_property, capsys):
    db, public, ref, ids = scenario(local_tmp, monkeypatch)
    before = tree_bytes(local_tmp)
    forbid_all(monkeypatch)
    inv = library.library_list(local_tmp, public, as_of=AS_OF)
    assert inv['matching_compositions'] == 4 and inv['matching_placements'] == 6
    for item in inv['library']:
        guide = k.knowledge_show(local_tmp, public, ref, selector=item['selector'], as_of=AS_OF, use_set_aliases=True)
        assert c.parse_deck_export(guide['export']['text']).total_cards == 60
    result = report(local_tmp, db, public, ref)
    assert result['valid_games'] == 5 and result['outcomes'] == {'wins': 1, 'losses': 3, 'unknown': 1}
    v1 = next(g for g in result['groups'] if g['version'] == 1 and g['opponent_archetype'] == 'Hydrapple')
    v2 = next(g for g in result['groups'] if g['version'] == 2)
    assert (v1['wins'], v1['losses'], v1['unknown'], v1['n'], v1['games']) == (0, 2, 1, 2, 3)
    assert v2['wins'] == v2['n'] == 1
    assert sum(g['games'] for g in result['groups'] if g['version'] is None) == 1
    assert all(g['observed_win_ratio'] is None for g in result['groups'])
    for battle in result['battles'][:4]:
        opponent = battle['opponent']
        assert opponent['classification']['label'] == 'Hydrapple'
        assert opponent['classification']['basis'] == 'hypothesized'
        assert opponent['exact_confirmed_60'] is None
        assert opponent['public_reference_proxy'][0]['is_exact_opponent_deck'] is False
        assert opponent['public_reference_proxy'][0]['total_cards'] == 60
        assert [r['name'] for r in opponent['observed_partial']['cards']] == ['Synthetic Delta']
        assert opponent['observed_partial']['cards'][0]['minimum_quantity'] == 1
    assert result['battles'][-1]['opponent']['classification']['basis'] == 'ambiguous'
    assert not result['public_tournament_results_mixed_with_battle_rates']
    from pokemind import rules
    from pokemind.set_code_aliases import build_aliases
    energy = next(card for card in c.parse_deck_export(DECK).cards if card.card_type == 'energy')
    assert energy.name.startswith('Basic ')
    with closing(connect_readonly(ref)) as con:
        identity = rules._resolve_structure_identity(con, {'card_name':energy.name.removeprefix('Basic '),
            'set_code':energy.set_code,'collector_number':energy.collector_number},
            set_aliases=build_aliases(con,as_of=AS_OF))
    assert identity['ids'] == []  # Never generalize a Basic Energy name equivalence.
    assert tree_bytes(local_tmp) == before
    # Existing probable duplicate method, on a separate synthetic record pair.
    from test_battle_sample import _pair
    duplicate_db = local_tmp / 'data/local/invented-duplicates.sqlite3'
    first, second = _pair(duplicate_db)
    duplicate = a.matchup_report(local_tmp, duplicate_db, deck_id='synthetic', as_of='2099-01-01', confirm_owner_read=True)
    assert duplicate['sample_review']['probable_duplicates_excluded'] == 1 and duplicate['valid_games'] == 1
    assert duplicate['battles'][0]['player_version']['version'] is None
    record_testsuite_property('public_deck_library_matchup_reproduction', json.dumps(EVIDENCE))
    print('DÉMO SYNTHÉTIQUE : v1 / hypothèse Hydrapple → 2 défaites confirmées, n=2, 1 issue inconnue; '
          'v2 → 1 victoire; 1 partie sans version attestée. Proxy PUBLIC60 distinct du deck adverse exact.')


@pytest.mark.parametrize('filter_name,value,expected', [
    ('archetype', 'hydra', 1), ('archetype', 'missing', 0), ('event', '123', 4),
    ('event', '999', 0), ('since', '2026-10-11', 0), ('until', '2026-10-10', 4),
])
def test_library_filters(local_tmp, filter_name, value, expected):
    db = sample(local_tmp)
    r = library.library_list(local_tmp, db, as_of=AS_OF, **{filter_name: value})
    assert r['matching_compositions'] == expected


def test_library_version_and_existing_compare_export(local_tmp):
    db = sample(local_tmp)
    inv = library.library_list(local_tmp, db, as_of=AS_OF)
    version = inv['library'][0]['composition_id']
    assert library.library_list(local_tmp, db, as_of=AS_OF, version=version)['matching_compositions'] == 1
    difference = c.competitive_compare(local_tmp, db, '123:1', '123:4', as_of=AS_OF)
    assert difference['changes']['counts'] == {'shared': 59, 'removed': 1, 'added': 1}


@pytest.mark.parametrize('kwargs', [{'event':'../owner'}, {'version':'guess'}, {'as_of':'today'},
                                  {'since':'2026-10-21','until':'2026-10-10'}, {'until':'2099-01-01'}])
def test_library_invalid_context_before_io(local_tmp, monkeypatch, kwargs):
    monkeypatch.setattr(c, '_advisor_snapshot', lambda *a: pytest.fail('no file access'))
    with pytest.raises(ValueError):
        library.library_list(local_tmp, local_tmp/'unused', **{'as_of':AS_OF, **kwargs})


@pytest.mark.parametrize('language', ['en', 'fr'])
def test_visible_cards_only_no_hidden_draw_or_attack_name(language):
    text = fictional_log(language=language)
    text += ('InventedRival drew Hidden Creature.\nInventedRival played an attack.\n'
             "InventedRival's Synthetic Delta used Fictional Beam.\n" if language == 'en' else
             'InventedRival a pioché Hidden Creature.\nInventedRival a utilisé Fictional Beam.\n')
    result = o.observe(logs.parse_battle_log(text), as_of=AS_OF)
    seen = result['observed_partial']['cards']
    assert [x['name'] for x in seen] == ['Synthetic Delta']
    assert seen[0]['minimum_quantity'] == 1 and seen[0]['occurrences'] >= 3
    assert result['excluded_evidence']


def test_explicit_draw_then_play_is_visible():
    parsed = logs.parse_battle_log(fictional_log() + 'InventedRival drew Visible Creature and played it to the Bench.\n')
    result = o.observe(parsed, as_of=AS_OF)
    assert 'Visible Creature' in [c['name'] for c in result['observed_partial']['cards']]


def test_incomplete_and_conflicting_identity_never_become_exact():
    parsed = logs.parse_battle_log('InventedRival played Synthetic Delta.\n')
    assert o.observe(parsed, as_of=AS_OF)['observed_partial']['cards'] == []
    parsed = logs.parse_battle_log(fictional_log() + 'Reference player: AnotherReference\n')
    result = o.observe(parsed, as_of=AS_OF)
    assert result['observed_partial']['cards'] == [] and result['classification']['label'] is None


def test_exact_export_only_when_explicit_valid_and_consistent(local_tmp):
    public = sample(local_tmp)
    index = library.reference_index(local_tmp, public, as_of=AS_OF)
    parsed = logs.parse_battle_log(fictional_log())
    export = c.competitive_export(local_tmp, public, '123', 5)
    assert o.observe(parsed, index=index, as_of=AS_OF)['exact_confirmed_60'] is None
    exact = o.observe(parsed, index=index, as_of=AS_OF, exact_export=export)
    assert exact['exact_confirmed_60']['total_cards'] == 60
    assert not exact['public_reference_proxy'][0]['is_exact_opponent_deck']
    assert o.observe(parsed, index=index, as_of=AS_OF, exact_export=DECK)['exact_confirmed_60'] is None
    with pytest.raises(ValueError):
        o.observe(parsed, as_of=AS_OF, exact_export=export.replace('4 Synthetic Delta ALT 301','24 Synthetic Delta ALT 301'))


def test_review_history_is_dated_reversible_and_keeps_model_hypothesis(local_tmp):
    public = sample(local_tmp)
    index = library.reference_index(local_tmp, public, as_of=AS_OF)
    parsed = logs.parse_battle_log(fictional_log())
    reviews = [{'review_id':'r1','recorded_at':'2026-10-21','status':'active','label':'Reviewed Label','source':'invented owner review'},
               {'review_id':'r2','recorded_at':'2026-10-22','status':'withdrawn','source':'invented withdrawal'}]
    prior = o.observe(parsed, index=index, as_of='2026-10-21', reviews=reviews)
    later = o.observe(parsed, index=index, as_of=AS_OF, reviews=reviews)
    assert prior['classification']['basis'] == 'owner_observed_label'
    assert prior['archetype_hypothesis']['label'] == later['classification']['label'] == 'Hydrapple'
    assert len(later['classification_history']) == 2 and prior['version_sha256'] != later['version_sha256']


@pytest.mark.parametrize('fault', ['future_confirmation','revoked','legacy','conflicting_link','deck_mismatch','version80','future_version','invalid_events','outcome_conflict'])
def test_versions_and_outcomes_never_guessed(local_tmp, monkeypatch, fault):
    db, public, ref, ids = scenario(local_tmp, monkeypatch)
    with closing(sqlite3.connect(db)) as con, con:
        if fault == 'future_confirmation':
            con.execute("UPDATE battle_version_attestations SET confirmed_at='2027-01-01'")
        elif fault == 'revoked':
            con.execute("UPDATE battle_version_attestations SET status='revoked',revoked_at='2026-10-21',revocation_reason='owner_explicit_revocation'")
        elif fault == 'legacy':
            con.execute('DELETE FROM battle_version_attestations')
        elif fault == 'conflicting_link':
            con.execute('DELETE FROM battle_deck_versions')
        elif fault == 'deck_mismatch':
            con.execute("UPDATE deck_versions SET deck_id='other'")
        elif fault == 'version80':
            con.execute('UPDATE deck_version_cards SET quantity=quantity+20 WHERE ordinal=1')
        elif fault == 'future_version':
            con.execute("UPDATE deck_versions SET effective_from='2027-01-01'")
        elif fault == 'invalid_events':
            con.execute('UPDATE battle_logs SET recognized_events=0')
        else:
            con.execute("UPDATE battle_logs SET winner='ThirdUncorroboratedPlayer'")
    result = report(local_tmp, db, public, ref)
    if fault == 'outcome_conflict':
        assert result['outcomes'] == {'wins':0,'losses':0,'unknown':5}
    else:
        assert all(g['version'] is None for g in result['groups'])
    assert all(g['observed_win_ratio'] is None for g in result['groups'])


def test_period_uses_attested_date_not_import_date(local_tmp, monkeypatch):
    db, public, ref, ids = scenario(local_tmp, monkeypatch)
    result = report(local_tmp, db, public, ref, since='2026-10-09', until='2026-10-11')
    assert result['valid_games'] == 4 and result['excluded']['unknown_battle_date'] == 1
    assert report(local_tmp, db, public, ref, since='2026-10-15')['valid_games'] == 0


def test_exact_import_duplicate_keeps_sample_size(local_tmp, monkeypatch):
    db, public, ref, ids = scenario(local_tmp, monkeypatch)
    duplicate = logs.import_battle_log(db, fictional_log(1,language='fr'), source_kind='stdin',deck_id='invented')
    assert duplicate['duplicate'] and report(local_tmp,db,public,ref)['valid_games'] == 5


def test_cli_human_json_and_opt_in_before_default_inspection(local_tmp, monkeypatch, capsys):
    db, public, ref, ids = scenario(local_tmp, monkeypatch)
    monkeypatch.setattr(cli, 'find_project_root', lambda: local_tmp)
    forbid_all(monkeypatch)
    monkeypatch.setattr(cli, '_db_for', lambda *a: pytest.fail('no implicit DB inspection'))
    assert cli.main(['meta','deck-library','--as-of',AS_OF,'--db',str(public),'--json']) == 0
    assert json.loads(capsys.readouterr().out)['matching_compositions'] == 4
    for command,selection in [('opponent',['--battle-id',str(ids[0])]),('matchups',['--deck','invented'])]:
        args=['battle',command,*selection,'--as-of',AS_OF,'--public-db',str(public),'--reference-db',str(ref)]
        assert cli.main(args+['--json']) == 2
        assert json.loads(capsys.readouterr().out)['ok'] is False
        assert cli.main(args+['--db',str(db),'--json']) == 2
        capsys.readouterr()
        args += ['--db',str(db),'--confirm-owner-read']
        assert cli.main(args+['--json']) == 0
        assert json.loads(capsys.readouterr().out)['ok'] is True
        assert cli.main(args) == 0
        assert 'unknown' in capsys.readouterr().out


@pytest.mark.parametrize('fault', ['outside','missing','redirected','schema','public_as_private','bad_date'])
def test_read_scope_and_schema_guards(local_tmp, monkeypatch, fault):
    db, public, ref, ids = scenario(local_tmp, monkeypatch)
    kwargs = {'confirm_owner_read':True,'as_of':AS_OF,'deck_id':'invented'}
    if fault == 'outside':
        db = local_tmp.parent/'forbidden.sqlite3'
    elif fault == 'missing':
        db = local_tmp/'data/local/missing.sqlite3'
    elif fault == 'redirected':
        monkeypatch.setattr(a,'_redirected',lambda p: p==db)
    elif fault == 'schema':
        with closing(sqlite3.connect(db)) as con,con:
            con.execute('DROP TABLE battle_events')
    elif fault == 'public_as_private':
        db = public
        # PUBLIC schema has empty battle tables, so absence of personal matches is valid.
        assert a.matchup_report(local_tmp,db,**kwargs)['valid_games'] == 0
        return
    else:
        kwargs['as_of']='today'
    with pytest.raises(ValueError):
        a.matchup_report(local_tmp,db,**kwargs)


def test_win_ratio_requires_decided_n_and_confirmed_version(local_tmp, monkeypatch):
    db, public, ref, ids = scenario(local_tmp, monkeypatch)
    for number in range(10, 13):
        battle = logs.import_battle_log(db,fictional_log(number,outcome='W'),source_kind='stdin',deck_id='invented')
        with closing(sqlite3.connect(db)) as con,con:
            con.execute("UPDATE battle_logs SET imported_at='2026-10-20' WHERE id=?",(battle['battle_id'],))
        attestations.confirm_battle_version(db,'invented',battle['battle_id'],version=1,battle_date='2026-10-10',apply=True,confirm_owner=True)
    result=report(local_tmp,db,public,ref)
    group=next(g for g in result['groups'] if g['version']==1 and g['opponent_archetype']=='Hydrapple')
    assert (group['wins'],group['losses'],group['unknown'],group['n'],group['games'])==(3,2,1,5,6)
    assert group['observed_win_ratio']==0.6 and group['interpretation']=='descriptive_not_predictive'
    assert group['classification_basis']=='hypothesized' and group['causal_loss_reason']=='unknown'


def test_duplicate_representative_never_inherits_other_version(local_tmp,monkeypatch):
    from test_battle_sample import _pair
    db=local_tmp/'data/local/duplicate-case.sqlite3'
    first,second=_pair(db)
    import_deck(db,DECK,deck_id='synthetic',source_kind='stdin')
    with closing(sqlite3.connect(db)) as con,con:
        con.execute("UPDATE deck_versions SET imported_at='2026-01-01',approved_at='2026-01-01',effective_from='2026-01-01'")
    attestations.confirm_battle_version(db,'synthetic',first,version=1,apply=True,confirm_owner=True)
    r=a.matchup_report(local_tmp,db,deck_id='synthetic',as_of='2099-01-01',confirm_owner_read=True)
    assert r['valid_games']==1 and r['battles'][0]['battle_id']==second
    assert r['battles'][0]['player_version']['version'] is None
    assert r['groups'][0]['observed_win_ratio'] is None


@pytest.mark.parametrize('fault',['none','future','stale','wrong_hash'])
def test_verified_french_card_name_alias_only(local_tmp,fault):
    from pokemind.cards import _canonical_sha256
    public,ref=enriched(local_tmp)
    with closing(sqlite3.connect(ref)) as con,con:
        payload={'id':'alt-301','name':'Créature Delta','category':'pokemon'}
        digest=_canonical_sha256(payload)
        con.execute("INSERT INTO catalog_translations(printing_id,language,status,name,source_url,retrieved_at,payload_sha256) VALUES('alt-301','fr','present','Créature Delta','https://api.tcgdex.net/v2/fr/cards/alt-301',?,?)",('2027-01-01' if fault=='future' else AS_OF,'bad' if fault=='wrong_hash' else digest))
        con.execute("INSERT INTO catalog_detail_payloads VALUES('cards','alt-301','fr',?,?,'synthetic')",(json.dumps(payload),digest))
        if fault=='stale':
            con.execute("UPDATE catalog_printings SET detail_stale_fr=1 WHERE tcgdex_id='alt-301'")
    index=library.reference_index(local_tmp,public,as_of=AS_OF,reference_db=ref)
    parsed=logs.parse_battle_log(fictional_log(language='fr',card='Créature Delta'))
    r=o.observe(parsed,index=index,as_of=AS_OF)
    assert r['classification']['label']==('Hydrapple' if fault=='none' else None)


def test_opt_in_checked_before_metadata_or_connections(local_tmp,monkeypatch):
    monkeypatch.setattr(a,'_redirected',lambda *args:pytest.fail('no metadata before consent'))
    monkeypatch.setattr(a,'connect_readonly',lambda *args:pytest.fail('no DB before consent'))
    with pytest.raises(ValueError,match='OPT_IN'):
        a.matchup_report(local_tmp,local_tmp/'data/local/selected.sqlite3',deck_id='invented',as_of=AS_OF)


@pytest.mark.parametrize('suffix',['-wal','-shm','-journal'])
def test_sidecars_refused_before_sqlite(local_tmp,monkeypatch,suffix):
    db,public,ref,ids=scenario(local_tmp,monkeypatch)
    db.with_name(db.name+suffix).write_bytes(b'synthetic sidecar')
    monkeypatch.setattr(a,'connect_readonly',lambda *args:pytest.fail('must not open SQLite'))
    with pytest.raises(ValueError,match='SIDECAR'):
        a.matchup_report(local_tmp,db,deck_id='invented',as_of=AS_OF,confirm_owner_read=True)


@pytest.mark.parametrize('generic',['their hand','a Supporter','a Pokémon','Energy','Active Pokémon'])
def test_generic_reveals_do_not_become_card_names(generic):
    parsed=logs.parse_battle_log(fictional_log()+f'InventedRival revealed {generic}.\n')
    r=o.observe(parsed,as_of=AS_OF)
    assert [c['name'] for c in r['observed_partial']['cards']]==['Synthetic Delta']


def test_exact_export_cannot_fix_missing_participant_identity():
    parsed=logs.parse_battle_log('InventedRival played Creature Alpha.\n')
    r=o.observe(parsed,as_of=AS_OF,exact_export=DECK)
    assert r['exact_confirmed_60'] is None
