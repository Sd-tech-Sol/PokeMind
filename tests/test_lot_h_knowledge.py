import json
from datetime import datetime, timezone

import pytest

from pokemind.catalog_snapshots import record_page, snapshot_coverage
from pokemind.cards import sync_cards, cards_coverage
from pokemind.database import connect_writable, initialize_schema
from pokemind.official_reviews import record_official_review
from pokemind.updates import official_validation_queue
from test_cards import FakeCatalogClient, _routes
from test_updates import FakeOfficialClient, _registry, _run

NOW = datetime(2026, 10, 14, tzinfo=timezone.utc)


def test_snapshot_members_are_not_translation_union_and_resume_is_atomic(local_tmp):
    db = local_tmp / "catalog.sqlite3"
    routes = _routes()
    for kind in ("cards", "sets"):
        for lang in ("en", "fr"):
            path = f"/{lang}/{kind}"
            items = routes[path]
            routes[path] = lambda _p, params, items=items: items if params["pagination:page"] == 1 else []
    sync_cards(db, max_requests=4, phase="index", client=FakeCatalogClient(4, routes))
    before = cards_coverage(db)
    assert before["languages"]["en"]["index"]["snapshot"]["denominator"] is None
    sync_cards(db, max_requests=8, phase="index", client=FakeCatalogClient(8, routes))
    after = cards_coverage(db)
    for lang in ("en", "fr"):
        snapshot = after["languages"][lang]["index"]["snapshot"]
        assert snapshot["complete"] and snapshot["denominator"] == len(_routes()[f"/{lang}/cards"])
        assert snapshot["provider_visible_total"] is None
        assert snapshot["detail_ratio"] == 0


def test_snapshot_duplicate_gap_stale_and_future_cannot_be_current_complete(local_tmp):
    connection = connect_writable(local_tmp / "snapshots.sqlite3")
    initialize_schema(connection)
    for page, ids in ((1, ["syn-1"]), (2, ["syn-1"]), (3, [])):
        record_page(connection, "cards:en", "discovery", page, ids, completed=page == 3, timestamp="2026-10-14T00:00:00Z")
    assert not snapshot_coverage(connection, "cards:en", now=NOW)["complete"]
    record_page(connection, "cards:en", "refresh", 2, ["syn-2"], completed=True, timestamp="2026-10-14T01:00:00Z")
    assert snapshot_coverage(connection, "cards:en", now=NOW)["denominator"] is None
    record_page(connection, "cards:fr", "discovery", 1, [], completed=True, timestamp="2026-10-01T00:00:00Z")
    stale = snapshot_coverage(connection, "cards:fr", now=NOW)
    assert stale["stale"] and stale["detail_ratio"] is None
    record_page(connection, "cards:fr", "discovery", 1, [], completed=True, timestamp="2026-12-01T00:00:00Z")
    assert snapshot_coverage(connection, "cards:fr", now=NOW)["stale"]
    connection.close()


def test_full_document_review_never_promotes_hash_or_rule(local_tmp):
    db = local_tmp / "rules.sqlite3"
    registry = _registry(local_tmp / "registry.json")
    _run(db, registry, FakeOfficialClient("v1"), now=datetime(2026, 10, 13, tzinfo=timezone.utc))
    connection = connect_writable(db)
    row = connection.execute("SELECT * FROM public_source_observations ORDER BY id DESC LIMIT 1").fetchone()
    source, digest = row["source_id"], row["content_sha256"]
    connection.close()
    kwargs = dict(content_sha256=digest, document_version="synthetic-v1", decision="verified", full_document_reviewed=True)
    before = db.read_bytes()
    assert record_official_review(db, source, **kwargs)["status"] == "PREVIEW"
    assert db.read_bytes() == before
    record_official_review(db, source, **kwargs, apply=True, confirm_owner=True)
    q = official_validation_queue(db)
    assert q["entries"][0]["document_review"]["current"]
    assert q["entries"][0]["reason_codes"] == ["ASSERTION_RECONCILIATION_REQUIRED"]
    assert q["count"] == 1 and not q["normative_promotion"]
    _run(db, registry, FakeOfficialClient("v2"), now=NOW)
    assert official_validation_queue(db)["entries"][0]["document_review"]["status"] == "stale_review"
    with pytest.raises(ValueError, match="FULL_RESPONSE_HASH_REQUIRED"):
        record_official_review(db, source, **kwargs, apply=True, confirm_owner=True)
    connection = connect_writable(db)
    assert connection.execute("SELECT COUNT(*) FROM official_rule_assertions").fetchone()[0] == 0
    connection.execute("UPDATE public_source_observations SET truncated=1")
    connection.commit()
    connection.close()
    with pytest.raises(ValueError, match="FULL_RESPONSE_HASH_REQUIRED"):
        record_official_review(db, source, **kwargs)
