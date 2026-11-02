import json
import hashlib

from pokemind.commissioning import commissioning_preflight, STEPS
from pokemind.database import connect_readonly, SCHEMA_VERSION
from pokemind.recovery import create_backup, restore_backup, verify_backup
from pokemind.visual_coach import start_session, observe_training, session_memory, advise_turn
from pokemind.vision_evidence import review_observation, revoke_visual_review
from pokemind.readiness import v1_readiness
from pokemind.cli import main
from test_lot_g_e2e import _historical_v7, _history
from test_lot_f_e2e import _vision_fixture


def test_h3_full_synthetic_historical_rehearsal_preserves_histories_and_owner_guards(local_tmp):
    original = local_tmp / "history7.sqlite3"
    _historical_v7(original)
    before, history = original.read_bytes(), _history(original)
    pre = commissioning_preflight(original, step="migration")
    assert pre["status"] == "BLOCKED_WITH_REASON" and pre["database"]["schema_version"] == 7
    backup = create_backup(original, local_tmp / "backups", apply=True, confirm_owner=True, min_free_bytes=0)
    backup_path = local_tmp / "backups" / backup["backup_file"]
    assert verify_backup(backup_path)["state"] == "verified"
    target = local_tmp / "clone13.sqlite3"
    pre = commissioning_preflight(original, step="clone", backup_path=backup_path, clone_path=target)
    assert pre["technical_preflight_passed"] and not pre["owner_authorization_inferred"]
    assert original.read_bytes() == before and not target.exists()
    restored = restore_backup(backup_path, target, apply=True, confirm_owner=True, migrate_clone=True, min_free_bytes=0)
    assert restored["schema_version"] == SCHEMA_VERSION == 13
    assert _history(target) == history and original.read_bytes() == before
    assert commissioning_preflight(original, step="clone", backup_path=backup_path, clone_path=target)["status"] == "BLOCKED_WITH_REASON"
    session = start_session(target, format="standard", platform="live", as_of="2026-10-14", apply=True, confirm_owner=True)["session_id"]
    image, calibration = _vision_fixture(local_tmp)
    digest = hashlib.sha256(calibration.read_bytes()).hexdigest()
    reviews = []
    for turn in (1, 2, 3):
        # Actual synthetic PNG decoding (marker adapter), explicitly not OCR.
        saved = observe_training(target, local_tmp, turn=turn, image_path=image, calibration_path=calibration,
                                 session_id=session, apply=True, confirm_owner=True)
        r = review_observation(target, session, saved["observation_id"], verdict="confirmed", scope="synthetic",
                               calibration_sha256=digest, apply=True, confirm_owner=True)
        reviews.append(r["review_id"])
        advice = advise_turn(target, session, turn=turn, format="standard", platform="live", as_of="2026-10-14")
        assert not advice["automated_game_action"]
    assert session_memory(target, session)["visual_review"]["confirmed_count"] == 3
    revoke_visual_review(target, reviews[0], apply=True, confirm_owner=True)
    snapshot = create_backup(target, local_tmp / "after", apply=True, confirm_owner=True, min_free_bytes=0)
    final = local_tmp / "final.sqlite3"
    restore_backup(local_tmp / "after" / snapshot["backup_file"], final, apply=True, confirm_owner=True, min_free_bytes=0)
    assert session_memory(final, session)["visual_review"]["confirmed_count"] == 2
    report = v1_readiness(final, backup_directory=local_tmp / "after")
    assert report["status"] == "NOT_RELEASE_READY"
    assert not report["gates"]["vision_owner_trial"]["passed"]
    assert str(local_tmp) not in json.dumps(report)
    connection = connect_readonly(final)
    assert connection.execute("SELECT COUNT(*) FROM sections_fts WHERE sections_fts MATCH 'SYNTHETIC_SENTINEL'").fetchone()[0] == 1
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
    connection.close()
    assert original.read_bytes() == before


def test_preflight_all_steps_are_readonly_no_private_paths_in_report(local_tmp, capsys):
    original = local_tmp / "history7.sqlite3"
    _historical_v7(original)
    before = original.read_bytes()
    for step in STEPS:
        result = commissioning_preflight(original, step=step)
        assert result["writes"] == 0 and result["read_only"]
        assert not result["owner_authorization_inferred"]
        assert str(local_tmp) not in json.dumps(result)
    assert original.read_bytes() == before
    assert main(["owner-plan", "--step", "migration", "--db", str(original), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "BLOCKED_WITH_REASON"
