"""Invented public pages only: the battle analysis reuses verified public work instead of redoing it."""
import json
import os
import shutil

from pokemind import battle_batch, competitive, counter_deck, deck_knowledge
from pokemind.public_deck_preflight import SCOPED_PUBLIC_CACHES
from test_competitive_advisor import AS_OF
from test_deck_knowledge import enriched


def test_public_sample_is_read_once_until_one_of_its_files_changes(local_tmp, monkeypatch):
    db, ref = enriched(local_tmp)
    competitive._SNAPSHOTS.clear()
    calls = []
    real = competitive._advisor_snapshot_uncached
    monkeypatch.setattr(competitive, '_advisor_snapshot_uncached', lambda *a: calls.append(1) or real(*a))
    first = competitive._advisor_snapshot(local_tmp, db, AS_OF)
    key = next(iter(first[0]))
    first[0][key]['quality'].append('INVENTED_MUTATION')  # a caller changing its copy changes nothing else
    second = competitive._advisor_snapshot(local_tmp, db, AS_OF)
    assert len(calls) == 1 and 'INVENTED_MUTATION' not in second[0][key]['quality']
    assert second[1:] == first[1:] and sorted(second[0]) == sorted(first[0])
    page = sorted((db.parent / 'pages').iterdir())[0]
    info = page.stat()
    os.utime(page, ns=(info.st_atime_ns, info.st_mtime_ns + 2_000_000_000))
    third = competitive._advisor_snapshot(local_tmp, db, AS_OF)
    assert len(calls) == 2 and third[1:] == second[1:]  # a touched page is verified again
    competitive._advisor_snapshot(local_tmp, db, AS_OF)
    assert len(calls) == 2


def test_a_changed_page_is_still_caught_after_a_cached_read(local_tmp):
    db, ref = enriched(local_tmp)
    competitive._SNAPSHOTS.clear()
    groups, _, issues, _ = competitive._advisor_snapshot(local_tmp, db, AS_OF)
    assert not [i for i in issues if i.get('code') == 'LIST_60_PRINTING_OR_SOURCE_INVALID']
    ledger = json.loads((db.parent / 'requests.json').read_text(encoding='utf-8'))
    listed = {r['sha256'] for r in ledger['requests'] if '/decks/' in r['url'] or 'list' in r['url']}
    page = next(p for p in sorted((db.parent / 'pages').iterdir()) if p.stem in listed)
    page.write_bytes(page.read_bytes() + b'<!-- invented change -->')
    _, _, issues, _ = competitive._advisor_snapshot(local_tmp, db, AS_OF)
    assert [i for i in issues if i.get('code') == 'LIST_60_PRINTING_OR_SOURCE_INVALID']


def test_counter_plans_of_one_analysis_share_the_public_work_with_identical_results(local_tmp, monkeypatch):
    db, ref = enriched(local_tmp)
    alone = counter_deck.counter_plan(local_tmp, db, ref, as_of=AS_OF, target='Hydrapple', use_set_aliases=True)
    built = []
    real = deck_knowledge.knowledge_show
    monkeypatch.setattr(deck_knowledge, 'knowledge_show', lambda *a, **k: built.append(k['selector']) or real(*a, **k))
    shared = {}
    plans = [counter_deck.counter_plan(local_tmp, db, ref, as_of=AS_OF, target='Hydrapple', use_set_aliases=True,
                                       shared=shared) for _ in range(3)]
    assert built and len(built) == len(set(built))  # each public guide is built once for all the plans
    same = lambda plan: json.dumps(plan, sort_keys=True, default=str)
    assert same(plans[0]) == same(alone) == same(plans[2])
    plans[0]['alternatives'][0]['mechanics'].append({'invented': True})
    assert same(plans[1]) == same(alone)  # plans do not share mutable parts
    other = counter_deck.counter_plan(local_tmp, db, ref, as_of=AS_OF, target='Hydrapple', use_set_aliases=True,
                                      options=2, shared=shared)
    assert len(other['alternatives']) == 2 and shared['key'][4] == 2  # other inputs start a fresh share


def test_counter_plans_are_kept_between_analyses_until_a_public_file_changes(local_tmp, monkeypatch):
    db, ref = enriched(local_tmp)
    built = []
    real = deck_knowledge.knowledge_show
    monkeypatch.setattr(deck_knowledge, 'knowledge_show', lambda *a, **k: built.append(k['selector']) or real(*a, **k))
    plan = lambda: counter_deck.counter_plan(local_tmp, db, ref, as_of=AS_OF, target='Hydrapple', use_set_aliases=True,
                                             shared=counter_deck.public_memo(db, ref, AS_OF))
    same = lambda value: json.dumps(value, sort_keys=True, default=str)
    first = plan()
    count, expected = len(built), same(first)
    first['alternatives'].clear()  # the next analysis gets its own copy
    second = plan()
    assert count and len(built) == count and same(second) == expected  # nothing rebuilt for the next game
    info = ref.stat()
    os.utime(ref, ns=(info.st_atime_ns, info.st_mtime_ns + 2_000_000_000))
    third = plan()
    assert len(built) == 2 * count and same(third) == expected  # a touched catalogue is read again
    kept = len(counter_deck._MEMOS)
    assert counter_deck.public_memo(local_tmp / 'absent.sqlite3', ref, AS_OF) == {}  # no stamp, no reuse
    assert len(counter_deck._MEMOS) == kept <= 2


def test_public_context_is_reused_until_one_of_its_files_changes(local_tmp, monkeypatch):
    db, ref = enriched(local_tmp)
    scoped = [local_tmp / p for p in SCOPED_PUBLIC_CACHES]
    shutil.copytree(db.parent, scoped[0].parent)
    scoped[1].parent.mkdir(parents=True)
    shutil.copyfile(ref, scoped[1])
    built = []
    def uncached(root, as_of):
        built.append(as_of)
        return {'references': [{'archetype': 'Invented'}]}, scoped, {'status': 'AVAILABLE_SOURCE_CHECKED', 'references': 1}
    monkeypatch.setattr(battle_batch, '_public_context_uncached', uncached)
    first, paths, status = battle_batch.public_context(local_tmp, AS_OF)
    first['references'].append({'archetype': 'INVENTED_MUTATION'})
    second, _, again = battle_batch.public_context(local_tmp, AS_OF)
    assert len(built) == 1 and second == {'references': [{'archetype': 'Invented'}]} and again == status
    index = local_tmp / battle_batch.RESEARCH_INDEX
    index.write_text('', encoding='utf-8')  # new public research: read again
    battle_batch.public_context(local_tmp, AS_OF)
    battle_batch.public_context(local_tmp, AS_OF)
    assert len(built) == 2
    info = scoped[1].stat()
    os.utime(scoped[1], ns=(info.st_atime_ns, info.st_mtime_ns + 2_000_000_000))
    battle_batch.public_context(local_tmp, AS_OF)
    battle_batch.public_context(local_tmp, '2026-10-25')  # another day is another context
    assert built == [AS_OF, AS_OF, AS_OF, '2026-10-25']
