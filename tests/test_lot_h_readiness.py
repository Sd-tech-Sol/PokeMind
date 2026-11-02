import json

from pokemind.database import connect_writable, initialize_schema
from pokemind.readiness import v1_readiness
from pokemind.rules import normative_coverage
from pokemind.meta import meta_coverage
from test_meta import _seed_complete_tournaments


def test_h_readiness_preserves_every_unsafe_release_gate(local_tmp):
    db = local_tmp / "readiness.sqlite3"
    connection = connect_writable(db)
    initialize_schema(connection)
    connection.close()
    before = db.read_bytes()
    report = v1_readiness(db)
    assert report["status"] == "NOT_RELEASE_READY"
    for name in ("raster_ocr_calibration", "retention_safety", "vision_owner_trial", "scheduler_cadence", "existing_target_restore", "independent_release_audit"):
        assert report["gates"][name]["required"] and not report["gates"][name]["passed"]
    assert report["updates"]["os_activation_status"] == "OWNER_ACTION_REQUIRED"
    assert not report["updates"]["active_service_proven"]
    assert not report["completion"]["visual_reviews"]["independent_trial_verified"]
    assert str(local_tmp) not in json.dumps(report) and db.read_bytes() == before


def test_meta_cutoff_excludes_future_event_and_future_cache(local_tmp):
    db = local_tmp / "meta.sqlite3"
    _seed_complete_tournaments(db, ["current", "future_event", "future_observation"])
    connection = connect_writable(db)
    connection.execute("UPDATE meta_tournaments SET date_utc='2030-01-01T00:00:00Z' WHERE tournament_id='future_event'")
    connection.execute("UPDATE meta_tournaments SET fetched_at='2030-01-01T00:00:00Z' WHERE tournament_id='future_observation'")
    connection.commit()
    connection.close()
    current = meta_coverage(db, as_of="2026-10-14")
    assert current["tournaments"]["complete_snapshots"] == 1
    assert current["matches"]["classifiable_ratio"] is None
    assert meta_coverage(db, as_of="2026-09-01")["tournaments"]["complete_snapshots"] == 0


def test_future_assertion_capture_cannot_complete_rotation(local_tmp):
    db = local_tmp / "norms.sqlite3"
    connection = connect_writable(db)
    initialize_schema(connection)
    connection.execute("INSERT INTO official_rule_sources(source_id,source_type,url,title,language,consulted_at,captured_at,content_sha256,validation_status,rights_note) VALUES('syn','official_test','https://www.pokemon.com/us/test','Synthetic','en','2026-10-14','2026-10-14','synthetic','verified','fixture')")
    connection.execute("INSERT INTO official_rule_assertions(assertion_id,source_id,assertion_kind,format,platform,payload_json,validation_status,confidence,captured_at) VALUES('syn:rotation','syn','rotation','standard','live',?,'verified','high','2030-01-01')", (json.dumps({"allowed_regulation_marks": ["Z"]}),))
    connection.commit()
    connection.close()
    report = normative_coverage(db, as_of="2026-10-14")
    assert not report["dimensions"]["standard_rotation_live"]["complete"]
