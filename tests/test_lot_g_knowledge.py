from __future__ import annotations

import json
from datetime import datetime, timezone

from pokemind.cards import cards_coverage
from pokemind.database import connect_writable, initialize_schema
from pokemind.knowledge import knowledge_status
from pokemind.rules import normative_coverage
from pokemind.updates import official_validation_queue, plan_public_update
from test_updates import FakeOfficialClient, _registry, _run


def _db(path):
    connection = connect_writable(path)
    initialize_schema(connection)
    return connection


def test_stale_details_prevent_complete_and_have_exact_reconciliation_work(local_tmp):
    path = local_tmp / "coverage.sqlite3"
    connection = _db(path)
    connection.execute("INSERT INTO catalog_sets(tcgdex_id,discovered_at,updated_at,detail_status_en,detail_status_fr) VALUES('syn','2026-10-14','2026-10-14','present','present')")
    connection.execute("INSERT INTO catalog_printings(tcgdex_id,set_id,discovered_at,updated_at,brief_source_url,brief_retrieved_at,detail_stale_fr) VALUES('syn-1','syn','2026-10-14','2026-10-14','https://api.tcgdex.net/v2/en/cards','2026-10-14',1)")
    for lang in ("en", "fr"):
        connection.execute("INSERT INTO catalog_translations(printing_id,language,status,name,source_url,retrieved_at) VALUES('syn-1',?,'present','Synthetic','https://api.tcgdex.net/v2/en/cards/syn-1','2026-10-14')", (lang,))
        for kind in ("sets", "cards"):
            connection.execute("INSERT INTO catalog_sync_state(scope,completed,updated_at) VALUES(?,1,'2026-10-14')", (f"{kind}:{lang}",))
    connection.commit()
    connection.close()
    before = path.read_bytes()
    coverage = cards_coverage(path)
    assert not coverage["complete"] and not coverage["details_complete_on_discovered"]
    assert coverage["known_completion_work"]["stale_detail_gets_required"] == 1
    assert coverage["known_completion_work"]["detail_gets_remaining_on_discovered"] == 1
    assert coverage["languages"]["en"]["index"]["provider_visible_total"] is None
    assert path.read_bytes() == before


def test_deep_update_advances_initial_discovery_then_refreshes(local_tmp):
    path = local_tmp / "updates.sqlite3"
    connection = _db(path)
    connection.close()
    assert not plan_public_update(path, mode="deep")["sources"]["tcgdex"]["refresh_index"]
    connection = connect_writable(path)
    for kind in ("sets", "cards"):
        for lang in ("en", "fr"):
            connection.execute("INSERT INTO catalog_sync_state(scope,completed,updated_at) VALUES(?,1,'2026-10-14')", (f"{kind}:{lang}",))
    connection.commit()
    connection.close()
    deep = plan_public_update(path, mode="deep")
    assert deep["sources"]["tcgdex"]["initial_discovery_complete"]
    assert deep["sources"]["tcgdex"]["refresh_index"]
    assert plan_public_update(path, mode="daily")["sources"]["tcgdex"]["refresh_index"]


def test_normative_status_is_dated_and_source_backed_not_hardcoded(local_tmp):
    path = local_tmp / "rules.sqlite3"
    connection = _db(path)
    assert not normative_coverage(path, as_of="2026-10-14")["dimensions"]["standard_rotation_live"]["complete"]
    connection.execute("INSERT INTO official_rule_sources(source_id,source_type,url,title,language,consulted_at,captured_at,content_sha256,validation_status,rights_note) VALUES('syn','official_test','https://www.pokemon.com/us/test','Synthetic','en','2026-10-14','2026-10-14','synthetic','verified','fixture')")
    connection.execute("INSERT INTO official_rule_assertions(assertion_id,source_id,assertion_kind,format,platform,payload_json,validation_status,confidence,captured_at) VALUES('syn:rotation','syn','rotation','standard','live',?,'verified','high','2026-10-14')", (json.dumps({"allowed_regulation_marks": ["Z"]}),))
    connection.commit()
    assert normative_coverage(path, as_of="2026-10-14")["dimensions"]["standard_rotation_live"]["complete"]
    assert not normative_coverage(path, as_of="2026-10-13")["dimensions"]["standard_rotation_live"]["complete"]
    connection.execute("UPDATE official_rule_sources SET validation_status='non_verified'")
    connection.commit()
    connection.close()
    evidence = normative_coverage(path, as_of="2026-10-14")
    assert evidence["dimensions"]["standard_rotation_live"]["pending_items"] == 1
    assert not evidence["complete"]
    assert all(not evidence["dimensions"][name]["complete"] for name in ("reprints", "errata", "promos", "expanded_eligibility", "live_support"))


def test_official_changes_enter_review_queue_without_promoting_assertions(local_tmp):
    path = local_tmp / "public.sqlite3"
    registry = _registry(local_tmp / "registry.json")
    _run(path, registry, FakeOfficialClient("first"), now=datetime(2026, 10, 13, tzinfo=timezone.utc))
    _run(path, registry, FakeOfficialClient("second"), now=datetime(2026, 10, 14, tzinfo=timezone.utc))
    connection = connect_writable(path)
    connection.execute("UPDATE public_source_observations SET truncated=1 WHERE id=(SELECT MAX(id) FROM public_source_observations)")
    connection.commit()
    assert connection.execute("SELECT COUNT(*) FROM official_rule_assertions").fetchone()[0] == 0
    connection.close()
    before = path.read_bytes()
    queue = official_validation_queue(path)
    assert queue["count"] == queue["counts"]["changed"] == queue["counts"]["truncated"] == 1
    assert queue["entries"][0]["hash_scope"] == "bounded_prefix"
    assert queue["entries"][0]["validation_status"] == "conflict"
    assert not queue["normative_promotion"]
    assert knowledge_status(path)["official_validation"] == queue
    assert path.read_bytes() == before
