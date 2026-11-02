import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from pokemind import recovery
from pokemind.cards import sync_cards, cards_coverage, PAGE_SIZE
from pokemind.catalog_snapshots import record_page, record_failure, snapshot_coverage
from pokemind.database import connect_writable, initialize_schema
from pokemind.local_ocr import _catalog_candidate
from pokemind.ocr_preflight import ocr_preflight
from test_cards import FakeCatalogClient
from test_local_ocr import _catalog
from test_recovery import _database


def test_duplicate_in_one_page_and_failed_refresh_do_not_certify_denominator(local_tmp):
    con = connect_writable(local_tmp / "snap.sqlite3")
    initialize_schema(con)
    now = datetime(2026, 10, 15, tzinfo=timezone.utc)
    stamp = "2026-10-15T00:00:00Z"
    record_page(con, "cards:en", "discovery", 1, ["syn-1", "syn-1"], completed=True, timestamp=stamp)
    result = snapshot_coverage(con, "cards:en", now=now)
    assert result["duplicate_members"] == 1 and result["denominator"] is None
    record_page(con, "cards:en", "refresh", 1, [], completed=True, timestamp=stamp)
    result = snapshot_coverage(con, "cards:en", now=now)
    assert result["denominator"] == 0 and result["detail_ratio"] is None
    record_failure(con, "cards:en", "refresh", stamp)
    result = snapshot_coverage(con, "cards:en", now=now)
    assert result["last_error"] and result["denominator"] is None
    con.close()


def test_resumed_changed_head_discards_old_tail_and_restarts_scan(local_tmp):
    db = local_tmp / "drift.sqlite3"
    members = [{"id": f"syn-{i:03d}", "localId": str(i), "name": f"Synthetic {i}"} for i in range(PAGE_SIZE)]
    def routes(head):
        return {"/en/sets": lambda *_: [],
                "/en/cards": lambda _, params: head if params["pagination:page"] == 1 else []}
    sync_cards(db, languages="en", phase="index", refresh_index=True, max_requests=2,
               client=FakeCatalogClient(2, routes(members)))
    changed = [{"id": "syn-new", "localId": "999", "name": "Synthetic New"}, *members[:-1]]
    report = sync_cards(db, languages="en", phase="index", refresh_index=True, max_requests=2,
                        client=FakeCatalogClient(2, routes(changed)))
    assert any(p["pagination_drift_restarted"] for p in report["pages"])
    snapshot = cards_coverage(db)["languages"]["en"]["index"]["snapshot"]
    assert not snapshot["complete"] and snapshot["denominator"] is None
    con = connect_writable(db)
    saved = json.loads(con.execute("SELECT value FROM metadata WHERE key='catalog_snapshot:cards:en:refresh'").fetchone()[0])
    assert saved["pages"]["1"] == [r["id"] for r in changed]
    con.close()


def test_long_running_scan_cannot_give_current_ratio(local_tmp):
    con = connect_writable(local_tmp / "long.sqlite3")
    initialize_schema(con)
    record_page(con, "sets:fr", "discovery", 1, ["syn"], completed=False, timestamp="2026-10-01T00:00:00Z")
    record_page(con, "sets:fr", "discovery", 2, [], completed=True, timestamp="2026-10-15T00:00:00Z")
    result = snapshot_coverage(con, "sets:fr", now=datetime(2026, 10, 15, tzinfo=timezone.utc))
    assert result["scan_duration_exceeded"] and result["denominator"] is None
    con.close()


def test_refresh_failure_before_first_page_invalidates_previous_discovery(local_tmp):
    con = connect_writable(local_tmp / "failure.sqlite3")
    initialize_schema(con)
    record_page(con, "sets:en", "discovery", 1, [], completed=True, timestamp="2026-10-15T00:00:00Z")
    record_failure(con, "sets:en", "refresh", "2026-10-15T01:00:00Z")
    result = snapshot_coverage(con, "sets:en", now=datetime(2026, 10, 15, 2, tzinfo=timezone.utc))
    assert not result["complete"] and result["detail_ratio"] is None and result["last_error"]
    con.close()


def test_official_review_of_future_content_is_stale_even_with_matching_hash(local_tmp):
    from pokemind.official_reviews import official_review
    con = connect_writable(local_tmp / "official.sqlite3")
    initialize_schema(con)
    saved = {"content_sha256": "a" * 64, "source_url": "https://www.pokemon.com/synthetic",
             "reviewed_at": "2026-10-01T00:00:00Z", "decision": "verified", "document_version": "synthetic-v1"}
    con.execute("INSERT INTO metadata(key,value) VALUES(?,?)", ("official_document_review:synthetic", json.dumps(saved)))
    row = {"source_id": "synthetic", "http_status": 200, "truncated": False,
           "content_sha256": "a" * 64, "source_url": saved["source_url"], "observed_at": "2099-10-01T00:00:00Z"}
    result = official_review(con, row)
    assert result["status"] == "stale_review" and not result["normative_promotion"]
    con.close()


def test_ocr_wrong_language_missing_hp_and_stale_detail_abstain(local_tmp):
    db = local_tmp / "ocr.sqlite3"
    _catalog(db)
    values = dict(name="Éclat Synthétique", set_code="SYN", collector_number="1", hp="120")
    assert _catalog_candidate(db, values, as_of="2026-10-15", language="fra")[0] == "syn-1"
    assert _catalog_candidate(db, values, as_of="2026-10-15", language="eng")[0] is None
    assert _catalog_candidate(db, {k: v for k, v in values.items() if k != "hp"}, as_of=None)[0] is None
    con = connect_writable(db)
    con.execute("UPDATE catalog_printings SET detail_stale_fr=1")
    con.commit()
    con.close()
    assert _catalog_candidate(db, values, as_of=None)[0] is None


def test_preflight_missing_packs_and_neutral_failed_output(local_tmp, monkeypatch):
    import pokemind.ocr_preflight as module
    binary = local_tmp / "synthetic.exe"
    binary.write_bytes(b"synthetic executable; never executed")
    monkeypatch.setattr(module.shutil, "which", lambda _: str(binary))
    def runner(args, **kwargs):
        assert kwargs["shell"] is False and kwargs["timeout"] == 5
        return SimpleNamespace(returncode=0, stdout=b"tesseract 5.5.0" if args[1] == "--version" else b"private path\neng\n")
    monkeypatch.setattr(module.subprocess, "run", runner)
    result = ocr_preflight()
    assert result["status"] == "OCR_BINARY_UNATTESTED" and result["version"] is None
    assert result["executable_sha256"] is None and not result["binary_executed"]
    assert "private path" not in json.dumps(result) and str(local_tmp) not in json.dumps(result)
    monkeypatch.setattr(module.shutil, "which", lambda _: None)
    assert ocr_preflight()["status"] == "OCR_ENGINE_NOT_INSTALLED"


def test_backup_manifest_publication_failure_keeps_unattested_backup(local_tmp, monkeypatch):
    source = _database(local_tmp / "source.sqlite3")
    directory = local_tmp / "backup"
    before = source.read_bytes()
    def fail(*args, **kwargs):
        raise OSError("synthetic interruption between files")
    monkeypatch.setattr(recovery, "_atomic_bytes", fail)
    with pytest.raises(recovery.RecoveryError, match="BACKUP_CREATE_FAILED"):
        recovery.create_backup(source, directory, apply=True, confirm_owner=True, min_free_bytes=0)
    assert source.read_bytes() == before
    assert recovery.recovery_residues(directory)["counts"]["unattested_database"] == 1
    assert recovery.backup_status(directory)["counts"].get("verified", 0) == 0
    plan = recovery.backup_plan(source, directory, min_free_bytes=0)
    assert not plan["atomic_publish"] and not plan["durability"]["multifile_atomic"]


def test_windows_reparse_point_and_residues_are_fail_closed(local_tmp, monkeypatch):
    source = _database(local_tmp / "source.sqlite3")
    real = recovery._redirected
    monkeypatch.setattr(recovery, "_redirected", lambda p: p == local_tmp or real(p))
    with pytest.raises(recovery.RecoveryError, match="NOT_REGULAR_FILE"):
        recovery.backup_plan(source, local_tmp / "backup")
    monkeypatch.setattr(recovery, "_redirected", real)
    for name in ("s.sqlite3-wal", "orphan.sqlite3.manifest.json", ".pokemind-backup.lock"):
        (local_tmp / name).write_text("synthetic", encoding="utf-8")
    report = recovery.recovery_residues(local_tmp)
    assert report["counts"]["sqlite_sidecar"] == 1 and report["counts"]["orphan_manifest"] == 1
    assert report["counts"]["lock_requires_owner_review"] == 1 and not report["automatic_repair"]
