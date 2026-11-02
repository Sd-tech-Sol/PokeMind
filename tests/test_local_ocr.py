from __future__ import annotations

import json
import os
import struct
import zlib
from pathlib import Path

import pytest

import pokemind.local_ocr as ocr
from pokemind.database import connect_writable, initialize_schema
from pokemind.visual_coach import advise_turn, observe_training, session_memory, start_session


def _tsv(text, score=98):
    return "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tconf\ttext\r\n" + f"5\t1\t1\t1\t1\t1\t{score}\t{text}\r\n"


def _fixture(root: Path, *, scale=1, field="name"):
    # Visible monochrome typographic glyphs and card frame, no color-to-ID code.
    # Rendering is fixture construction; mocked OCR does NOT prove recognition.
    glyphs = {"H": ["101", "101", "111", "101", "101"], "P": ["110", "101", "110", "100", "100"],
              "1": ["010", "110", "010", "010", "111"], "2": ["110", "001", "010", "100", "111"], "0": ["111", "101", "101", "101", "111"]}
    width, height = 80 * scale, 40 * scale
    pixels = [[(250, 250, 250) for _ in range(width)] for _ in range(height)]
    for i, char in enumerate("HP120"):
        for y, line in enumerate(glyphs[char]):
            for x, bit in enumerate(line):
                if bit == "1":
                    for dy in range(scale):
                        for dx in range(scale):
                            pixels[(5 + y) * scale + dy][(5 + i * 4 + x) * scale + dx] = (20, 20, 20)
    for x in range(width):
        pixels[0][x] = pixels[-1][x] = (80, 80, 80)
    for y in range(height):
        pixels[y][0] = pixels[y][-1] = (80, 80, 80)
    raw = b"".join(b"\x00" + b"".join(bytes(p) for p in row) for row in pixels)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    image = root / "representative.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    profile = {"schema_version": 1, "adapter": ocr.ADAPTER, "language": "eng+fra", "reference_size": [80, 40], "fields": [{"field": field, "roi": [1, 1, 78, 38], "min_confidence": 0.95}]}
    calibration = root / "ocr.json"
    calibration.write_text(json.dumps(profile), encoding="utf-8")
    return image, calibration, profile


def _catalog(db):
    connection = connect_writable(db)
    initialize_schema(connection)
    connection.execute("INSERT INTO catalog_sets(tcgdex_id,tcg_online_code,discovered_at,updated_at) VALUES('syn','SYN','2026-10-14','2026-10-14')")
    connection.execute("INSERT INTO catalog_printings(tcgdex_id,set_id,local_id,category,hp,discovered_at,updated_at,brief_source_url,brief_retrieved_at) VALUES('syn-1','syn','1','pokemon',120,'2026-10-14','2026-10-14','https://api.tcgdex.net/v2/en/cards','2026-10-14')")
    connection.execute("INSERT INTO catalog_translations(printing_id,language,status,name,source_url,retrieved_at) VALUES('syn-1','fr','present','Éclat Synthétique','https://api.tcgdex.net/v2/fr/cards/syn-1','2026-10-14')")
    connection.commit()
    connection.close()


def test_missing_backend_abstains_without_database_mutation(local_tmp, monkeypatch):
    image, calibration, _ = _fixture(local_tmp)
    monkeypatch.setattr(ocr.shutil, "which", lambda _: None)
    report = observe_training(local_tmp / "absent.sqlite3", local_tmp, turn=1, image_path=image, calibration_path=calibration)
    assert report["status"] == "NEEDS_MANUAL_ANNOTATION"
    assert report["vision_backend"]["status"] == "VISION_BACKEND_UNAVAILABLE"
    assert not report["vision_backend"]["verified_on_synthetic"]
    assert not (local_tmp / "absent.sqlite3").exists()


@pytest.mark.parametrize("text,score,reason", [("120", 30, "OCR_BELOW_THRESHOLD"), ("120", "nan", "OCR_SCORE_INVALID"), ("???", 98, "OCR_COUNTER_INVALID"), ("", 98, "OCR_TEXT_UNREADABLE")])
def test_occlusion_bad_scores_and_unreadable_counters_abstain(local_tmp, text, score, reason):
    image, calibration, _ = _fixture(local_tmp, field="hp")
    state, backend = ocr.recognize_local_text(local_tmp / "absent.sqlite3", image, calibration, local_tmp, turn=1, _runner=lambda *_: _tsv(text, score))
    assert backend["field_evidence"][0]["reason_code"] == reason
    assert backend["field_evidence"][0]["accepted_candidate"] is False
    assert state["sides"]["self"]["active"]["card"] is None


@pytest.mark.parametrize("scale", [1, 2])
def test_unicode_crlf_scaled_roi_and_exact_multifield_candidate(local_tmp, scale):
    db = local_tmp / "ocr.sqlite3"
    _catalog(db)
    image, calibration, profile = _fixture(local_tmp, scale=scale)
    names = ["name", "set_code", "collector_number", "hp", "damage"]
    profile["fields"] = [{"field": name, "roi": [1, 1, 78, 38]} for name in names]
    calibration.write_text(json.dumps(profile), encoding="utf-8")
    outputs = iter(["E\u0301clat Synthe\u0301tique", "SYN", "1", "120", "20"])

    def runner(png, language):
        assert png.startswith(b"\x89PNG") and language == "eng+fra"
        return _tsv(next(outputs))

    state, backend = ocr.recognize_local_text(db, image, calibration, local_tmp, turn=1, as_of="2026-10-14", _runner=runner)
    card = state["sides"]["self"]["active"]["card"]
    assert card["tcgdex_id"] == "syn-1" and card["provenance"] == "ocr_uncertain"
    assert backend["identity_status"] == "EXACT_MULTIFIELD_OCR_CANDIDATE"
    assert backend["test_contract_only"] and not backend["verified_on_synthetic"]
    assert state["hidden_information_policy"]["opponent_hand"] == "UNKNOWN"


@pytest.mark.parametrize("fields", [["Éclat Synthétique", "BAD", "1", "120"], ["Wrong Name", "SYN", "1", "120"], ["Éclat Synthétique", "SYN", "1", "130"]])
def test_wrong_card_or_hp_never_gets_identity(local_tmp, fields):
    db = local_tmp / "ocr.sqlite3"
    _catalog(db)
    image, calibration, profile = _fixture(local_tmp)
    profile["fields"] = [{"field": name, "roi": [1, 1, 78, 38]} for name in ["name", "set_code", "collector_number", "hp"]]
    calibration.write_text(json.dumps(profile), encoding="utf-8")
    outputs = iter(fields)
    state, _ = ocr.recognize_local_text(db, image, calibration, local_tmp, turn=1, _runner=lambda *_: _tsv(next(outputs)))
    assert state["sides"]["self"]["active"]["card"]["tcgdex_id"] is None


def test_mock_contract_flows_through_three_turns_without_promoting_action(local_tmp, monkeypatch):
    db = local_tmp / "sessions.sqlite3"
    _catalog(db)
    image, calibration, _ = _fixture(local_tmp)
    original = ocr.recognize_local_text

    def mock_contract(*args, **kwargs):
        return original(*args, **kwargs, _runner=lambda *_: _tsv("Éclat Synthétique"))

    monkeypatch.setattr(ocr, "recognize_local_text", mock_contract)
    session = start_session(db, format="standard", platform="live", as_of="2026-10-14", apply=True, confirm_owner=True)
    for turn in [1, 2, 3]:
        observed = observe_training(db, local_tmp, turn=turn, image_path=image, calibration_path=calibration, session_id=session["session_id"], apply=True, confirm_owner=True)
        assert observed["vision_backend"]["test_contract_only"]
        advice = advise_turn(db, session["session_id"], turn=turn, format="standard", platform="live", as_of="2026-10-14")
        assert advice["status"] == "INSUFFICIENT_EVIDENCE" and advice["verified_possible_count"] == 0
    memory = session_memory(db, session["session_id"])
    assert len(memory["observations"]) == 3 and memory["images_stored"] == 0
    assert all(row["source_kind"] == "local_vision" for row in memory["observations"])
    assert str(image) not in json.dumps(memory)


def test_frame_geometry_and_multi_line_ambiguity_fail_closed(local_tmp):
    image, calibration, profile = _fixture(local_tmp)
    profile["reference_size"] = [80, 80]
    calibration.write_text(json.dumps(profile), encoding="utf-8")
    with pytest.raises(ValueError, match="VISION_FRAME_ASPECT_MISMATCH"):
        ocr.recognize_local_text(local_tmp / "absent.sqlite3", image, calibration, local_tmp, turn=1, _runner=lambda *_: _tsv("120"))
    tsv = _tsv("one") + "5\t1\t1\t1\t2\t1\t98\ttwo\r\n"
    assert ocr._tsv_line(tsv, 0.95)[2] == "OCR_MULTIPLE_LINES_AMBIGUOUS"


def test_real_backend_optional_is_explicitly_skipped_when_absent(local_tmp):
    if os.environ.get("POKEMIND_TEST_EXECUTE_REVIEWED_OCR") != "1" or not os.environ.get("POKEMIND_TEST_OCR_TRUST"):
        pytest.skip("OCR absent ou non attesté : opt-in et politique revus requis, aucune reconnaissance réelle attestée.")
    image, _, _ = _fixture(local_tmp)
    assert isinstance(ocr._run_tesseract(image.read_bytes(), "eng", policy_path=Path(os.environ["POKEMIND_TEST_OCR_TRUST"])), str)
