import json
from datetime import datetime, timezone

import pytest

from pokemind.cards import cards_coverage, sync_cards
from pokemind.catalog_snapshots import record_page, snapshot_coverage
from pokemind.database import connect_writable, initialize_schema
from pokemind.rules import check_card, normative_coverage
from test_rules import _ready_db, _coverage, _assertion
from pokemind.demo import DemoCatalogClient
from pathlib import Path

NOW = datetime(2026, 10, 15, tzinfo=timezone.utc)


@pytest.mark.parametrize("scope", ["sets:en", "sets:fr", "cards:en", "cards:fr"])
def test_legacy_membership_and_stale_scans_cannot_certify_current_coverage(local_tmp, scope):
    con = connect_writable(local_tmp / "catalog.sqlite3")
    initialize_schema(con)
    record_page(con, scope, "discovery", 1, [], completed=True, timestamp="2026-10-01T00:00:00Z")
    result = snapshot_coverage(con, scope, now=NOW)
    assert result["observed_scan_complete"] and not result["complete"] and result["denominator"] is None
    key = "catalog_snapshot:" + scope + ":discovery"
    state = json.loads(con.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()[0])
    state["schema_version"] = 1
    state["last_observed_at"] = state["started_at"] = "2026-10-15T00:00:00Z"
    con.execute("UPDATE metadata SET value=? WHERE key=?", (json.dumps(state), key))
    result = snapshot_coverage(con, scope, now=NOW)
    assert not result["membership_version_supported"] and not result["complete"]
    record_page(con, scope, "discovery", 1, [], completed=True, timestamp="2026-10-15T00:00:00Z")
    assert snapshot_coverage(con, scope, now=NOW)["denominator"] == 0
    con.close()


def test_gap_reset_and_reverse_time_are_unknown(local_tmp):
    con = connect_writable(local_tmp / "gap.sqlite3")
    initialize_schema(con)
    record_page(con, "cards:fr", "discovery", 2, ["syn-1"], completed=True, timestamp="2026-10-15T00:00:00Z")
    assert snapshot_coverage(con, "cards:fr", now=NOW)["denominator"] is None
    record_page(con, "cards:fr", "discovery", 1, ["syn-2"], completed=False, timestamp="2026-10-15T00:00:00Z")
    record_page(con, "cards:fr", "discovery", 2, [], completed=True, timestamp="2026-10-14T00:00:00Z")
    assert snapshot_coverage(con, "cards:fr", now=NOW)["scan_duration_exceeded"]
    con.close()


def test_set_discovered_members_do_not_expand_index_snapshot_denominator(local_tmp):
    root = Path(__file__).resolve().parents[1]
    db = local_tmp / "sets.sqlite3"
    client = DemoCatalogClient(root)
    sync_cards(db, max_requests=24, phase="index", client=client)
    before = cards_coverage(db)
    client = DemoCatalogClient(root)
    sync_cards(db, max_requests=24, phase="details", client=client)
    after = cards_coverage(db)
    for lang in ("en", "fr"):
        snapshot = after["languages"][lang]["index"]["snapshot"]
        assert snapshot["denominator"] == before["languages"][lang]["index"]["snapshot"]["denominator"] == 3
        assert snapshot["provider_visible_total"] is None and not snapshot["legality_proven"]
    assert after["languages"]["fr"]["statuses"]["absent"] >= 1


def test_contradictory_reprint_identity_is_unknown_even_when_both_sources_verified(local_tmp):
    db = _ready_db(local_tmp / "reprints.sqlite3")
    _coverage(db)
    _assertion(db, "reprint-positive", "reprint_equivalence", subject="synthetic-g", payload={"current_printing_id": "synthetic-h"})
    _assertion(db, "reprint-negative", "reprint_equivalence", subject="synthetic-g", payload={"no_current_equivalent": True})
    result = check_card(db, "synthetic-g", format="standard", platform="live", as_of="2026-05-01")
    assert result["status"] == "unknown" and result["reason_codes"] == ["CONFLICTING_OFFICIAL_ASSERTIONS"]


def test_future_publication_cannot_establish_past_rule(local_tmp):
    db = _ready_db(local_tmp / "dates.sqlite3")
    _coverage(db)
    con = connect_writable(db)
    con.execute("UPDATE official_rule_sources SET published_date='2099-01-01' WHERE source_id='pokemon-rotation-2026-en'")
    con.commit()
    con.close()
    result = check_card(db, "synthetic-h", format="standard", platform="live", as_of="2026-05-01")
    assert result["status"] == "unknown" and result["reason_codes"] == ["OFFICIAL_EVIDENCE_NOT_AVAILABLE_AS_OF"]
    assert not normative_coverage(db, as_of="2026-05-01")["complete"]


def test_global_catalog_coverage_does_not_trust_old_completed_cursor(local_tmp):
    root = Path(__file__).resolve().parents[1]
    db = local_tmp / "old.sqlite3"
    sync_cards(db, max_requests=24, phase="index", client=DemoCatalogClient(root))
    sync_cards(db, max_requests=24, phase="details", client=DemoCatalogClient(root))
    assert cards_coverage(db)["current_indexes_complete"]
    con = connect_writable(db)
    rows = con.execute("SELECT key,value FROM metadata WHERE key LIKE 'catalog_snapshot:%'").fetchall()
    for key, value in rows:
        state = json.loads(value)
        state["schema_version"] = 1
        con.execute("UPDATE metadata SET value=? WHERE key=?", (json.dumps(state), key))
    con.commit()
    con.close()
    result = cards_coverage(db)
    assert result["discovery"]["complete"]  # historical cursor only
    assert not result["current_indexes_complete"] and not result["complete"]
    assert result["known_completion_work"]["index_gets_remaining"] is None
