from __future__ import annotations

import json
import sqlite3

import pytest

import pokemind.readiness as readiness
from pokemind.database import connect_writable, initialize_schema
from pokemind.recovery import create_backup


def _db(path):
    connection = connect_writable(path)
    initialize_schema(connection)
    connection.commit()
    connection.close()
    return path


def test_superficially_green_flags_never_bypass_full_product_gates(local_tmp, monkeypatch):
    db = _db(local_tmp / "superficial.sqlite3")
    original = readiness._completion_evidence

    def superficial(path, **kwargs):
        result = original(path, **kwargs)
        result.update({"confirmed_60_card_versions": 1, "owner_attributed_battles": 5,
                       "collection_declared": True, "credits_declared": True,
                       "catalog": {"complete": True, "provider_total_proven": True},
                       "metagame": {"complete_snapshots": 5, "classifiable_matches": 100}})
        return result

    monkeypatch.setattr(readiness, "_completion_evidence", superficial)
    monkeypatch.setattr(readiness, "_backup_readiness", lambda _: {"verified_count": 1, "inventory_complete": True})
    real_vision = readiness.vision_backend_status

    def fake_marker_flags():
        report = real_vision()
        report["synthetic_pixel_adapter"]["verified_on_user_training"] = True
        report["synthetic_pixel_adapter"]["verified_on_synthetic"] = True
        return report

    monkeypatch.setattr(readiness, "vision_backend_status", fake_marker_flags)
    report = readiness.v1_readiness(db)
    assert report["status"] == "NOT_RELEASE_READY"
    for required in ("reprints", "errata", "promos", "live_support", "restrictions", "expanded_eligibility", "vision_owner_trial", "scheduler_cadence", "existing_target_restore", "independent_release_audit"):
        assert report["gates"][required]["required"]
        assert not report["gates"][required]["passed"]
    assert "VISION_NOT_VERIFIED_ON_OWNER_TRAINING" in report["blockers"]
    assert report["technical_tests"]["inferred_from_capability_flags"] is False


def test_optional_owner_collection_and_credits_are_not_release_blockers(local_tmp):
    report = readiness.v1_readiness(_db(local_tmp / "optional.sqlite3"))
    assert not report["gates"]["optional_collection"]["required"]
    assert not report["gates"]["optional_credits"]["required"]
    assert "OPTIONAL_COLLECTION_NOT_PROVIDED" not in report["blockers"]
    assert "OPTIONAL_CREDITS_NOT_PROVIDED" not in report["blockers"]
    assert report["owner"]["collection_declared"] is False


def test_single_meta_result_is_not_a_sufficient_product_sample(local_tmp, monkeypatch):
    db = _db(local_tmp / "meta.sqlite3")
    original = readiness._completion_evidence

    def one_result(path, **kwargs):
        result = original(path, **kwargs)
        result["metagame"] = {"complete_snapshots": 1, "classifiable_matches": 1}
        return result

    monkeypatch.setattr(readiness, "_completion_evidence", one_result)
    report = readiness.v1_readiness(db)
    assert "METAGAME_SAMPLE_INSUFFICIENT" in report["blockers"]
    assert not report["gates"]["trainer_hill"]["passed"]


def test_corrupt_database_has_neutral_closed_report(local_tmp):
    db = local_tmp / "private-database.sqlite3"
    db.write_bytes(b"synthetic not sqlite")
    report = readiness.v1_readiness(db)
    assert report["status"] == "NOT_RELEASE_READY"
    assert not report["gates"]["database_integrity_fk_fts"]["passed"]
    assert str(local_tmp) not in json.dumps(report)


def test_readiness_does_not_leak_private_values_or_backup_names(local_tmp):
    db = _db(local_tmp / "synthetic-private.sqlite3")
    connection = connect_writable(db)
    connection.execute("INSERT INTO credit_snapshots(recorded_at,as_of,amount,source_kind,status) VALUES('2026-10-14','2026-10-14',87654321,'owner_provided','active')")
    connection.execute("INSERT INTO metadata(key,value) VALUES('private_fixture','SYNTHETIC_PRIVATE_SENTINEL')")
    connection.commit()
    connection.close()
    directory = local_tmp / "backups"
    created = create_backup(db, directory, apply=True, confirm_owner=True, min_free_bytes=0)
    before = db.read_bytes()
    report = readiness.v1_readiness(db, backup_directory=directory)
    serialized = json.dumps(report)
    for forbidden in ("87654321", "SYNTHETIC_PRIVATE_SENTINEL", created["backup_file"], str(local_tmp)):
        assert forbidden not in serialized
    assert db.read_bytes() == before
    assert report["owner_action_status"] == "OWNER_ACTION_REQUIRED"
    assert report["product_capability_status"] == "PRODUCT_CAPABILITY_PARTIAL"
