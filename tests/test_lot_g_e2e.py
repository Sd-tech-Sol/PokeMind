from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import pytest

import pokemind.recovery as recovery
import pokemind.local_ocr as ocr
from pokemind.database import SCHEMA_VERSION, connect_writable, initialize_schema
from pokemind.decks import import_deck
from pokemind.readiness import v1_readiness
from pokemind.visual_coach import _png_rgb_pixels, observe_training, session_memory, start_session
from test_local_ocr import _catalog, _fixture, _tsv
from test_recovery import _created, _database


def _historical_v7(path):
    _catalog(path)
    import_deck(path, "Pokémon: 1\n4 Synthetic Basic SYN 1\nTrainer: 1\n4 Synthetic Trainer SYN 2\nEnergy: 1\n52 Synthetic Energy SYN 3\n", deck_id="synthetic", source_kind="file", source_name="synthetic.txt")
    connection = connect_writable(path)
    connection.execute("INSERT INTO documents(document_key,title,path,source_date,content_sha256,imported_at) VALUES('synthetic.md','Synthetic','synthetic.md','2026-10-14','fixture','2026-10-14')")
    connection.execute("INSERT INTO sections(document_id,ordinal,heading,heading_path,heading_level,start_line,end_line,char_start,char_end,content,content_sha256) VALUES(1,1,'SYNTHETIC_SENTINEL','SYNTHETIC_SENTINEL',1,1,2,0,30,'historical fixture preserved','fixture')")
    connection.execute("INSERT INTO observed_decks VALUES('synthetic','observé partiellement','2026-10-14','2026-10-14')")
    connection.execute("INSERT INTO battle_logs(source_sha256,imported_at,parser_version,source_kind,outcome,valid,deck_id,recognized_events,warnings_json) VALUES('fixture','2026-10-14','fixture','file','inconnue',1,'synthetic',0,'[]')")
    connection.commit()
    # Remove every table introduced after v7, rather than only changing user_version
    # on a current schema. Older histories and FTS indexes remain actual fixtures.
    for table in ("knowledge_update_alerts", "public_source_observations", "knowledge_update_source_runs", "knowledge_update_cycles", "training_observations", "training_sessions", "deck_candidate_cards", "deck_candidates", "battle_lessons", "collection_items", "collection_snapshots", "credit_snapshots", "official_deck_structure_rules", "battle_version_attestations"):
        connection.execute(f"DROP TABLE {table}")
    connection.execute("PRAGMA user_version=7")
    connection.commit()
    connection.close()


def _history(path):
    connection = sqlite3.connect(path)
    try:
        return {table: connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall() for table in ("documents", "sections", "battle_logs", "battle_events", "card_observations", "deck_versions", "deck_version_cards", "battle_deck_versions", "catalog_sets", "catalog_printings", "catalog_translations")}
    finally:
        connection.close()


def test_schema7_history_clone_migration_ocr_memory_backup_readiness(local_tmp, monkeypatch):
    old = local_tmp / "history-v7.sqlite3"
    _historical_v7(old)
    history = _history(old)
    original_bytes = old.read_bytes()
    created, backup = _created(old, local_tmp / "backups")
    backup_bytes = backup.read_bytes()
    verified = recovery.restore_verify(backup, migrate_clone=True, work_directory=local_tmp)
    assert verified["source_schema_version"] == 7 and verified["clone_schema_version"] == SCHEMA_VERSION
    clone = local_tmp / "new-v13.sqlite3"
    result = recovery.restore_backup(backup, clone, apply=True, confirm_owner=True, migrate_clone=True, min_free_bytes=0)
    assert result["checks"]["foreign_key_violations"] == 0 and result["checks"]["integrity"] == "ok"
    assert all(item["status"] == "ok" for item in result["checks"]["fts"].values())
    assert _history(clone) == history
    assert old.read_bytes() == original_bytes and backup.read_bytes() == backup_bytes
    connection = sqlite3.connect(clone)
    assert connection.execute("SELECT COUNT(*) FROM sections_fts WHERE sections_fts MATCH 'SYNTHETIC_SENTINEL'").fetchone()[0] == 1
    assert connection.execute("SELECT COUNT(*) FROM catalog_fts WHERE catalog_fts MATCH 'Synthétique'").fetchone()[0] == 1
    connection.close()
    session = start_session(clone, format="standard", platform="live", as_of="2026-10-14", apply=True, confirm_owner=True)
    image, calibration, _ = _fixture(local_tmp)
    real_ocr = ocr.recognize_local_text
    monkeypatch.setattr(ocr, "recognize_local_text", lambda *args, **kwargs: real_ocr(*args, **kwargs, _runner=lambda *_: _tsv("Éclat Synthétique")))
    for turn in (1, 2, 3):
        observe_training(clone, local_tmp, turn=turn, image_path=image, calibration_path=calibration, session_id=session["session_id"], apply=True, confirm_owner=True)
    second_backup = recovery.create_backup(clone, local_tmp / "final-backups", apply=True, confirm_owner=True, min_free_bytes=0)
    final_clone = local_tmp / "final-clone.sqlite3"
    recovery.restore_backup(local_tmp / "final-backups" / second_backup["backup_file"], final_clone, apply=True, confirm_owner=True, min_free_bytes=0)
    memory = session_memory(final_clone, session["session_id"])
    assert len(memory["observations"]) == 3 and memory["images_stored"] == 0
    report = v1_readiness(final_clone, backup_directory=local_tmp / "final-backups")
    assert report["status"] == "NOT_RELEASE_READY"
    assert report["gates"]["database_integrity_fk_fts"]["passed"]
    assert report["gates"]["exact_deck_60"]["passed"]
    assert "RESTORE_EXISTING_TARGET_BLOCKED" in report["blockers"]
    assert str(local_tmp) not in json.dumps(report)


def test_sqlite_original_is_byte_identical_after_postpublication_failure(local_tmp, monkeypatch):
    old = _database(local_tmp / "old.sqlite3")
    candidate = _database(local_tmp / "candidate.sqlite3")
    connection = sqlite3.connect(old)
    connection.execute("UPDATE metadata SET value='old state' WHERE key='recovery_sentinel'")
    connection.commit()
    connection.close()
    before = old.read_bytes()
    checks = recovery._sqlite_checks(candidate)
    real_checks = recovery._sqlite_checks

    def fail_published(path):
        if path == old:
            raise PermissionError("synthetic postpublication")
        return real_checks(path)

    monkeypatch.setattr(recovery, "_sqlite_checks", fail_published)
    with pytest.raises(recovery.RecoveryError, match="RESTORE_APPLY_FAILED"):
        recovery._publish_isolated_restore(candidate, old, checks, _allow_existing_fixture=True)
    assert old.read_bytes() == before
    assert real_checks(old)["status"] == "ok"


def test_external_postpublication_mutation_is_preserved_as_incomplete(local_tmp, monkeypatch):
    source = _database(local_tmp / "source.sqlite3")
    _, backup = _created(source, local_tmp / "backups")
    target = local_tmp / "new.sqlite3"
    real_checks = recovery._sqlite_checks

    def mutate_published(path):
        checks = real_checks(path)
        if path == target:
            with target.open("ab") as handle:
                handle.write(b"external write must not be discarded")
            raise OSError("synthetic write race")
        return checks

    monkeypatch.setattr(recovery, "_sqlite_checks", mutate_published)
    with pytest.raises(recovery.RecoveryError, match="RESTORE_ROLLBACK_INCOMPLETE"):
        recovery.restore_backup(backup, target, apply=True, confirm_owner=True, min_free_bytes=0)
    assert target.read_bytes().endswith(b"external write must not be discarded")
    assert recovery.verify_backup(backup)["state"] == "verified"


def test_retained_backup_corruption_during_staging_restores_candidates(local_tmp, monkeypatch):
    from datetime import datetime, timezone
    source = _database(local_tmp / "source.sqlite3")
    directory = local_tmp / "backups"
    _, older = _created(source, directory, now=datetime(2026, 1, 1, tzinfo=timezone.utc))
    _, retained = _created(source, directory, now=datetime(2026, 10, 12, tzinfo=timezone.utc))
    policy = {"keep_last": 1, "max_age_days": 30, "now": datetime(2026, 10, 14, tzinfo=timezone.utc)}
    plan = recovery.retention_plan(directory, **policy)
    original = older.read_bytes()
    real_replace = os.replace

    def mutate_retained(src, dst):
        result = real_replace(src, dst)
        if Path(src) == recovery._manifest_for(older):
            with retained.open("r+b") as handle:
                handle.seek(100)
                handle.write(b"MUTATED")
        return result

    monkeypatch.setattr(recovery.os, "replace", mutate_retained)
    with pytest.raises(recovery.RecoveryError, match="RETENTION_EXTERNAL_EXCLUSION_UNPROVEN"):
        recovery.apply_retention(directory, plan_sha256=plan["plan_sha256"], apply=True, confirm_owner=True, **policy)
    assert older.read_bytes() == original and recovery.verify_backup(older)["state"] == "verified"


def test_transparent_hidden_rgb_cannot_be_read_as_visible_glyph():
    import struct, zlib
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    payload = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00\x00")) + chunk(b"IEND", b"")
    with pytest.raises(ValueError, match="VISION_TRANSPARENCY_UNSUPPORTED"):
        _png_rgb_pixels(payload)


def test_equal_fts_counts_with_wrong_text_are_not_a_healthy_backup(local_tmp):
    db = local_tmp / "fts.sqlite3"
    _historical_v7(db)
    connection = sqlite3.connect(db)
    before = connection.execute("SELECT COUNT(*) FROM sections_fts").fetchone()[0]
    connection.execute("UPDATE sections_fts SET content='wrong indexed text' WHERE rowid=1")
    connection.commit()
    assert connection.execute("SELECT COUNT(*) FROM sections_fts").fetchone()[0] == before
    connection.close()
    checks = recovery._sqlite_checks(db)
    assert checks["status"] == "failed" and checks["fts"]["sections_fts"]["content_mismatch_rows"] == 1
    with pytest.raises(recovery.RecoveryError, match="SOURCE_DATABASE_NOT_HEALTHY"):
        recovery.create_backup(db, local_tmp / "backups", apply=True, confirm_owner=True, min_free_bytes=0)
