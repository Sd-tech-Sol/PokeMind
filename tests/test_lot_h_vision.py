import hashlib
import json
import shutil
import os
from pathlib import Path

import pytest

from pokemind.ocr_benchmark import VARIANTS, benchmark_ocr, raster_text, synthetic_corpus
from pokemind.visual_coach import _png_rgb_pixels, start_session, observe_training, session_memory, advise_turn, save_observation
from pokemind.vision_evidence import review_observation, revoke_visual_review
from pokemind.cli import main
from test_visual_coach import _install_attack


def test_corpus_is_real_raster_text_reproducible_and_varied():
    a = raster_text("DRAGON SYNTHÉTIQUE")
    width, height, pixels = _png_rgb_pixels(a)
    assert width > 100 and height > 20
    assert pixels.count((0, 0, 0)) > 200
    assert a == raster_text("DRAGON SYNTHÉTIQUE")
    assert a != raster_text("DRAGON SYNTHETIQUE")
    assert len({hashlib.sha256(raster_text("SYN 007", v)).hexdigest() for v in VARIANTS[:7]}) == 7
    assert len(list(synthetic_corpus())) == 22


def test_absent_engine_is_never_reported_as_a_benchmark_pass(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    result = benchmark_ocr()
    assert result["status"] == "OCR_ENGINE_NOT_INSTALLED"
    assert not result["mock_used"] and not result["real_ocr_executed"]
    assert result["identity_false_positives"] is None and result["abstention_rate"] is None
    assert all(m["attempted"] == 0 for m in result["fields"].values())
    assert result["images_persisted"] == 0


@pytest.mark.skipif(os.environ.get("POKEMIND_TEST_EXECUTE_REVIEWED_OCR") != "1" or not os.environ.get("POKEMIND_TEST_OCR_TRUST"), reason="OCR_ENGINE_NOT_INSTALLED_OR_UNATTESTED; explicit reviewed opt-in required")
def test_installed_ocr_runs_actual_rasters():
    result = benchmark_ocr(policy_path=Path(os.environ["POKEMIND_TEST_OCR_TRUST"]), execute=True)
    assert result["real_ocr_executed"] and not result["mock_used"]
    assert result["ocr_latency_median_seconds"] is not None
    assert not result["visual_certain_allowed"]


def test_review_binds_digest_survives_memory_and_is_revocable(local_tmp):
    db = local_tmp / "vision.sqlite3"
    session = start_session(db, format="standard", platform="live", as_of="2026-10-14", apply=True, confirm_owner=True)["session_id"]
    ids = []
    for turn in (1, 2, 3):
        saved = observe_training(db, local_tmp, turn=turn, annotation={"turn": turn}, session_id=session, apply=True, confirm_owner=True)
        oid = saved["observation_id"]
        preview = review_observation(db, session, oid, verdict="confirmed", scope="synthetic", calibration_sha256="a" * 64)
        assert preview["status"] == "PREVIEW"
        assert session_memory(db, session)["visual_review"]["record_count"] == len(ids)
        r = review_observation(db, session, oid, verdict="confirmed", scope="synthetic", calibration_sha256="a" * 64, apply=True, confirm_owner=True)
        ids.append(r["review_id"])
    memory = session_memory(db, session)
    assert memory["visual_review"]["confirmed_count"] == 3
    assert memory["visual_review"]["owner_reviewed_visual_turns"] == 0
    advice = advise_turn(db, session, turn=3, format="standard", platform="live", as_of="2026-10-14")
    assert advice["visual_review"]["confirmed_count"] == 3
    assert advice["verified_possible_count"] == 0
    revoke_visual_review(db, ids[-1], apply=True, confirm_owner=True)
    assert session_memory(db, session)["visual_review"]["confirmed_count"] == 2
    assert session_memory(db, session)["visual_review"]["record_count"] == 4
    save_observation(db, session, turn=1, state={"turn": 1, "unknown_fields": ["corrected"]}, revision_of_id=memory["observations"][0]["observation_id"], apply=True, confirm_owner=True)
    assert session_memory(db, session)["visual_review"]["active_reviews"] == 1


def test_review_needs_owner_and_exact_observation(local_tmp):
    with pytest.raises(ValueError, match="OWNER_CONFIRMATION_REQUIRED"):
        review_observation(local_tmp / "absent.sqlite3", "x", 1, verdict="confirmed", scope="owner_training", calibration_sha256="a"*64, apply=True)
    assert not (local_tmp / "absent.sqlite3").exists()


def test_benchmark_cli_leaves_database_absent(local_tmp, monkeypatch, capsys):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    db = local_tmp / "absent.sqlite3"
    assert main(["match", "benchmark-ocr", "--db", str(db), "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "OCR_ENGINE_NOT_INSTALLED" and not db.exists()


def test_legacy_visual_certain_without_real_calibration_cannot_authorize_attack(local_tmp):
    db = local_tmp / "legacy.sqlite3"
    _install_attack(db, cost=["Colorless"])
    session = start_session(db, format="standard", platform="live", as_of="2026-10-14", apply=True, confirm_owner=True)["session_id"]
    state = {"turn": 1, "phase": "attack", "turn_owner": "self", "sides": {"self": {"active": {
        "visibility": "visible", "provenance": "visual_certain",
        "card": {"name": "Synthetic Active", "tcgdex_id": "syn-1", "provenance": "visual_certain"},
        "energies": [{"type": "Colorless", "count": 1, "provenance": "visual_certain"}]}}}}
    save_observation(db, session, turn=1, state=state, apply=True, confirm_owner=True, _trusted_visual=True)
    advice = advise_turn(db, session, turn=1, format="standard", platform="live", as_of="2026-10-14")
    assert advice["recommended_sequence"] == [] and advice["verified_possible_count"] == 0
