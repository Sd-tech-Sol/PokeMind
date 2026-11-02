from __future__ import annotations

import json
import sqlite3
import struct
import zlib
from pathlib import Path

import pytest

from pokemind.database import SCHEMA_VERSION, connect_writable, initialize_schema
from pokemind.visual_coach import (
    advise_turn,
    close_session,
    correct_observation,
    inspect_training_image,
    observe_training,
    revoke_correction,
    session_memory,
    start_session,
    vision_backend_status,
)


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def _png(path: Path, width: int = 4, height: int = 3) -> Path:
    rows = b"".join(b"\x00" + b"\x80\x80\x80" * width for _ in range(height))
    data = (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(rows))
        + _chunk(b"IEND", b"")
    )
    path.write_bytes(data)
    return path


def _rgb_png(path: Path, rows: list[list[tuple[int, int, int]]]) -> Path:
    height = len(rows)
    width = len(rows[0])
    raw = b"".join(b"\x00" + b"".join(bytes(pixel) for pixel in row) for row in rows)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw))
        + _chunk(b"IEND", b"")
    )
    return path


def _calibration(path: Path) -> Path:
    profile = {
        "schema_version": 1,
        "adapter": "pokemind_marker_v1",
        "markers": [
            {"field": "phase", "x": 0, "y": 0, "width": 1, "height": 1, "values": {"255,0,0": "attack", "192,0,0": "main"}},
            {"field": "turn_owner", "x": 1, "y": 0, "width": 1, "height": 1, "values": {"0,255,0": "self", "0,192,0": "opponent"}},
            {"field": "self_active_name", "x": 2, "y": 0, "width": 1, "height": 1, "values": {"0,0,255": "Synthetic Active"}},
            {"field": "self_active_id", "x": 3, "y": 0, "width": 1, "height": 1, "values": {"255,255,0": "syn-1"}},
            {"field": "self_active_energy_type", "x": 0, "y": 1, "width": 1, "height": 1, "values": {"255,0,255": "Colorless"}},
            {"field": "self_active_energy_count", "x": 1, "y": 1, "width": 1, "height": 1, "values": {"0,255,255": 1}},
        ],
    }
    path.write_text(json.dumps(profile), encoding="utf-8")
    return path


def _jpeg(path: Path, width: int = 8, height: int = 6, orientation: int = 6) -> Path:
    tiff = b"II\x2a\x00\x08\x00\x00\x00\x01\x00" + struct.pack("<HHI", 0x0112, 3, 1)
    tiff += struct.pack("<H", orientation) + b"\x00\x00\x00\x00\x00\x00"
    exif = b"Exif\x00\x00" + tiff
    sof = b"\x08" + struct.pack(">HH", height, width) + b"\x01\x01\x11\x00"
    path.write_bytes(
        b"\xff\xd8\xff\xe1" + struct.pack(">H", len(exif) + 2) + exif
        + b"\xff\xc0" + struct.pack(">H", len(sof) + 2) + sof + b"\xff\xd9"
    )
    return path


def _webp(path: Path, width: int = 7, height: int = 5) -> Path:
    payload = b"VP8X" + struct.pack("<I", 10) + b"\x00\x00\x00\x00" + (width - 1).to_bytes(3, "little") + (height - 1).to_bytes(3, "little")
    path.write_bytes(b"RIFF" + struct.pack("<I", len(payload) + 4) + b"WEBP" + payload)
    return path


def _annotation(*, turn: int = 1, name: str = "Synthetic Active", tcgdex_id: str | None = None) -> dict[str, object]:
    card = {"name": name, "provenance": "owner_annotated", "confidence": "certain"}
    if tcgdex_id:
        card["tcgdex_id"] = tcgdex_id
    return {
        "turn": turn,
        "phase": "attack",
        "turn_owner": "self",
        "sides": {
            "self": {
                "active": {
                    "visibility": "visible",
                    "card": card,
                    "damage": 20,
                    "energies": [{"type": "Colorless", "count": 1, "provenance": "owner_annotated"}],
                    "provenance": "owner_annotated",
                },
                "hand": {"visibility": "partial", "count": 3, "cards": [], "provenance": "owner_annotated"},
                "prizes": {"apparent_count": 4, "contents": ["must not survive"], "provenance": "owner_annotated"},
            },
            "opponent": {
                "active": {"visibility": "ambiguous", "provenance": "ocr_uncertain"},
                "hand": {"visibility": "hidden", "count": 5, "cards": [{"name": "Hidden"}]},
                "prizes": {"apparent_count": 5, "contents": ["hidden"]},
            },
        },
        "unknown_fields": ["Banc adverse partiellement masqué"],
        "recognition_errors": [],
    }


def _install_attack(db_path: Path, *, cost: list[str], source_url: str | None = "https://api.tcgdex.net/v2/en/cards/syn-1", retrieved_at: str | None = "2026-10-13T00:00:00Z") -> None:
    connection = connect_writable(db_path)
    try:
        initialize_schema(connection)
        now = "2026-10-13T00:00:00Z"
        connection.execute("INSERT INTO catalog_sets(tcgdex_id,name_en,discovered_at,updated_at) VALUES('syn','Synthetic',?,?)", (now, now))
        connection.execute(
            """INSERT INTO catalog_printings
               (tcgdex_id,set_id,local_id,category,stage,discovered_at,updated_at,brief_source_url,brief_retrieved_at)
               VALUES('syn-1','syn','1','pokemon','Basic',?,?, 'https://api.tcgdex.net/v2/en/cards',?)""",
            (now, now, now),
        )
        connection.execute(
            """INSERT INTO catalog_translations
               (printing_id,language,status,name,category,attacks_json,source_url,retrieved_at)
               VALUES('syn-1','en','present','Synthetic Active','pokemon',?,?,?)""",
            (json.dumps([{"name": "Measured Hit", "cost": cost, "damage": "30"}]), source_url or "", retrieved_at),
        )
        connection.commit()
    finally:
        connection.close()


def _annotation_file(path: Path, payload: dict[str, object]) -> Path:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def test_image_validation_accepts_synthetic_formats_without_exposing_path_or_hash(local_tmp: Path) -> None:
    for image, expected, orientation in (
        (_png(local_tmp / "board.png"), "PNG", 1),
        (_jpeg(local_tmp / "board.jpg"), "JPEG", 6),
        (_webp(local_tmp / "board.webp"), "WEBP", 1),
    ):
        metadata = inspect_training_image(image, local_tmp)
        assert metadata["format"] == expected and metadata["orientation"] == orientation
        assert metadata["width"] > 0 and metadata["height"] > 0 and metadata["pixel_count"] > 0
        assert metadata["stored"] is False and "path" not in metadata and "sha" not in json.dumps(metadata).casefold()


def test_image_validation_rejects_invalid_mismatch_external_and_symlink(local_tmp: Path, tmp_path: Path) -> None:
    invalid = local_tmp / "bad.jpg"
    invalid.write_bytes(b"not an image")
    with pytest.raises(ValueError, match="Signature"):
        inspect_training_image(invalid, local_tmp)
    mismatch = _png(local_tmp / "wrong.jpg")
    with pytest.raises(ValueError, match="extension"):
        inspect_training_image(mismatch, local_tmp)
    outside = _png(tmp_path / "outside.png")
    with pytest.raises(ValueError, match="data/local"):
        inspect_training_image(outside, local_tmp)
    link = local_tmp / "linked.png"
    try:
        link.symlink_to(local_tmp / "wrong.jpg")
    except OSError:
        return
    with pytest.raises(ValueError, match="symboliques"):
        inspect_training_image(link, local_tmp)


def test_image_only_abstains_and_never_creates_or_mutates_database(local_tmp: Path) -> None:
    db_path = local_tmp / "absent.sqlite3"
    image = _png(local_tmp / "board.png")
    result = observe_training(db_path, local_tmp, turn=1, image_path=image, frame_scope="crop")
    assert result["status"] == "NEEDS_MANUAL_ANNOTATION"
    assert result["vision_backend"]["status"] == "VISION_BACKEND_UNAVAILABLE"
    assert result["frame_scope"] == "crop"
    assert result["image_lifecycle"]["stored_in_sqlite"] is False
    assert image.is_file() and not db_path.exists()


def test_sessions_isolate_text_memory_deduplicate_and_never_store_pixels(local_tmp: Path) -> None:
    db_path = local_tmp / "sessions.sqlite3"
    preview = start_session(db_path, format="standard", platform="live", as_of="2026-10-13")
    assert preview["read_only"] is True and not db_path.exists()
    first = start_session(db_path, format="standard", platform="live", as_of="2026-10-13", apply=True, confirm_owner=True)
    second = start_session(db_path, format="standard", platform="live", as_of="2026-10-13", apply=True, confirm_owner=True)
    assert first["session_id"] != second["session_id"]
    image = _png(local_tmp / "turn.png")
    annotation = _annotation_file(local_tmp / "turn.json", _annotation())
    saved = observe_training(
        db_path, local_tmp, turn=1, image_path=image, annotation_path=annotation,
        session_id=first["session_id"], apply=True, confirm_owner=True,
    )
    duplicate = observe_training(
        db_path, local_tmp, turn=1, image_path=image, annotation_path=annotation,
        session_id=first["session_id"], apply=True, confirm_owner=True,
    )
    assert saved["status"] == "SAVED" and duplicate["status"] == "DUPLICATE"
    memory = session_memory(db_path, first["session_id"])
    assert len(memory["observations"]) == 1 and memory["images_stored"] == 0
    state = memory["observations"][0]["state"]
    assert state["sides"]["self"]["prizes"]["contents"] == "UNKNOWN"
    assert state["sides"]["opponent"]["hand"]["cards"] == []
    assert session_memory(db_path, second["session_id"])["observations"] == []
    connection = sqlite3.connect(db_path)
    columns = [row[1] for row in connection.execute("PRAGMA table_info(training_observations)")]
    stored = connection.execute("SELECT state_json FROM training_observations").fetchone()[0]
    connection.close()
    assert not any("image" in column or "path" in column or "blob" in column for column in columns)
    assert "PNG" not in stored and str(image.resolve()) not in stored


def test_correction_is_revisioned_and_revocable(local_tmp: Path) -> None:
    db_path = local_tmp / "correction.sqlite3"
    session = start_session(db_path, format="standard", platform="live", as_of="2026-10-13", apply=True, confirm_owner=True)
    original = observe_training(
        db_path, local_tmp, turn=1, annotation=_annotation(), session_id=session["session_id"],
        apply=True, confirm_owner=True,
    )
    corrected_payload = _annotation(name="Corrected Active")
    correction_file = _annotation_file(local_tmp / "correction.json", corrected_payload)
    corrected = correct_observation(
        db_path, local_tmp, session["session_id"], original["observation_id"], correction_file,
        apply=True, confirm_owner=True,
    )
    memory = session_memory(db_path, session["session_id"])
    assert [row["status"] for row in memory["observations"]] == ["superseded", "active"]
    revoked = revoke_correction(
        db_path, session["session_id"], corrected["observation_id"], apply=True, confirm_owner=True,
    )
    assert revoked["restored_observation_id"] == original["observation_id"]
    replay = session_memory(db_path, session["session_id"])
    assert [row["status"] for row in replay["observations"]] == ["active", "revoked"]


def test_correction_can_restore_historical_identical_state_and_revoke_it(local_tmp: Path) -> None:
    db_path = local_tmp / "a-b-a.sqlite3"
    session = start_session(db_path, format="standard", platform="live", as_of="2026-10-13", apply=True, confirm_owner=True)
    first = observe_training(db_path, local_tmp, turn=1, annotation=_annotation(name="A"), session_id=session["session_id"], apply=True, confirm_owner=True)
    b_file = _annotation_file(local_tmp / "b.json", _annotation(name="B"))
    second = correct_observation(db_path, local_tmp, session["session_id"], first["observation_id"], b_file, apply=True, confirm_owner=True)
    a_file = _annotation_file(local_tmp / "a.json", _annotation(name="A"))
    third = correct_observation(db_path, local_tmp, session["session_id"], second["observation_id"], a_file, apply=True, confirm_owner=True)
    assert third["status"] == "SAVED" and third["observation_id"] not in {first["observation_id"], second["observation_id"]}
    memory = session_memory(db_path, session["session_id"])
    assert [row["status"] for row in memory["observations"]] == ["superseded", "superseded", "active"]
    revoked = revoke_correction(db_path, session["session_id"], third["observation_id"], apply=True, confirm_owner=True)
    assert revoked["restored_observation_id"] == second["observation_id"]
    assert [row["status"] for row in session_memory(db_path, session["session_id"])["observations"]] == ["superseded", "active", "revoked"]


def test_manual_annotation_cannot_forge_visual_provenance_or_hidden_cards(local_tmp: Path) -> None:
    payload = _annotation()
    payload["sides"]["self"]["active"]["provenance"] = "visual_certain"
    payload["sides"]["self"]["active"]["card"]["provenance"] = "visual_certain"
    payload["sides"]["opponent"]["discard"] = {
        "visibility": "hidden", "cards": [{"name": "Forged Hidden", "provenance": "visual_certain"}],
        "provenance": "ocr_uncertain",
    }
    result = observe_training(local_tmp / "none.sqlite3", local_tmp, turn=1, annotation=payload)
    state = result["state"]
    assert state["sides"]["self"]["active"]["provenance"] == "owner_annotated"
    assert state["sides"]["self"]["active"]["card"]["provenance"] == "owner_annotated"
    assert state["sides"]["opponent"]["discard"]["provenance"] == "unknown"
    assert state["sides"]["opponent"]["discard"]["cards"] == []


def test_advice_uses_exact_local_card_text_but_stays_conditional(local_tmp: Path) -> None:
    db_path = local_tmp / "advice.sqlite3"
    session = start_session(db_path, format="standard", platform="live", as_of="2026-10-13", apply=True, confirm_owner=True)
    _install_attack(db_path, cost=["Colorless"])
    observe_training(
        db_path, local_tmp, turn=1, annotation=_annotation(tcgdex_id="syn-1"),
        session_id=session["session_id"], apply=True, confirm_owner=True,
    )
    report = advise_turn(
        db_path, session["session_id"], turn=1, format="standard", platform="live", as_of="2026-10-13"
    )
    assert report["status"] == "CONDITIONAL_ADVICE"
    assert report["conditional_count"] == 1 and report["verified_possible_count"] == 0
    assert report["recommended_sequence"][0]["action"] == "Attaquer avec Measured Hit"
    assert report["recommended_sequence"][0]["evidence"]["tcgdex_id"] == "syn-1"
    assert report["hidden_information"]["prize_contents"] == "UNKNOWN"
    assert report["automated_game_action"] is False and report["network_used"] is False


@pytest.mark.parametrize(
    ("cost", "energy_type", "expected"),
    [(["Fire"], "Water", "ENERGY_TYPE_NOT_VERIFIED"), (["Fire", "Colorless"], "Fire", "VISIBLE_ENERGY_INSUFFICIENT")],
)
def test_advice_requires_typed_energy(cost: list[str], energy_type: str, expected: str, local_tmp: Path) -> None:
    db_path = local_tmp / (expected + ".sqlite3")
    session = start_session(db_path, format="standard", platform="live", as_of="2026-10-13", apply=True, confirm_owner=True)
    _install_attack(db_path, cost=cost)
    payload = _annotation(tcgdex_id="syn-1")
    payload["sides"]["self"]["active"]["energies"] = [{"type": energy_type, "count": 1, "provenance": "owner_annotated"}]
    observe_training(db_path, local_tmp, turn=1, annotation=payload, session_id=session["session_id"], apply=True, confirm_owner=True)
    report = advise_turn(db_path, session["session_id"], turn=1, format="standard", platform="live", as_of="2026-10-13")
    assert report["status"] == "INSUFFICIENT_EVIDENCE"
    assert report["options"][0]["reason_code"] == expected


def test_advice_special_energy_and_context_or_source_conflicts_abstain(local_tmp: Path) -> None:
    db_path = local_tmp / "context.sqlite3"
    session = start_session(db_path, format="standard", platform="live", as_of="2026-10-13", apply=True, confirm_owner=True)
    _install_attack(db_path, cost=["Fire"])
    payload = _annotation(tcgdex_id="syn-1")
    payload["sides"]["self"]["active"]["energies"] = [{"type": "Special Energy", "count": 1, "provenance": "owner_annotated"}]
    observe_training(db_path, local_tmp, turn=1, annotation=payload, session_id=session["session_id"], apply=True, confirm_owner=True)
    special = advise_turn(db_path, session["session_id"], turn=1, format="standard", platform="live", as_of="2026-10-13")
    assert special["options"][0]["reason_code"] == "SPECIAL_ENERGY_OR_MODIFIER_UNVERIFIED"
    conflict = advise_turn(db_path, session["session_id"], turn=1, format="expanded", platform="live", as_of="2026-10-14")
    assert conflict["status"] == "CONTEXT_CONFLICT" and conflict["options"] == []


def test_advice_rejects_opponent_phase_and_incomplete_source(local_tmp: Path) -> None:
    db_path = local_tmp / "source.sqlite3"
    session = start_session(db_path, format="standard", platform="live", as_of="2026-10-13", apply=True, confirm_owner=True)
    _install_attack(db_path, cost=["Colorless"], source_url=None)
    payload = _annotation(tcgdex_id="syn-1")
    payload["turn_owner"] = "opponent"
    payload["phase"] = "checkup"
    observe_training(db_path, local_tmp, turn=1, annotation=payload, session_id=session["session_id"], apply=True, confirm_owner=True)
    report = advise_turn(db_path, session["session_id"], turn=1, format="standard", platform="live", as_of="2026-10-13")
    assert report["status"] == "INSUFFICIENT_EVIDENCE"
    assert report["options"][0]["reason_code"] == "PUBLIC_SOURCE_INCOMPLETE"


def test_turn_conflict_contradictory_action_and_close_are_conservative(local_tmp: Path) -> None:
    db_path = local_tmp / "conflict.sqlite3"
    session = start_session(db_path, format="standard", platform="live", as_of="2026-10-13", apply=True, confirm_owner=True)
    bad = _annotation(turn=2)
    with pytest.raises(ValueError, match="contredit"):
        observe_training(db_path, local_tmp, turn=1, annotation=bad)
    annotated = _annotation()
    annotated["available_actions"] = [{
        "kind": "attack", "description": "Attaque contradictoire",
        "provenance": "owner_annotated", "contradicted": True,
    }]
    observe_training(
        db_path, local_tmp, turn=1, annotation=annotated,
        session_id=session["session_id"], apply=True, confirm_owner=True,
    )
    with pytest.raises(ValueError, match="TURN_SEQUENCE_INVALID"):
        observe_training(
            db_path, local_tmp, turn=3, annotation=_annotation(turn=3),
            session_id=session["session_id"], apply=True, confirm_owner=True,
        )
    report = advise_turn(db_path, session["session_id"], turn=1, format="standard", platform="live", as_of="2026-10-13")
    assert any(option["reason_code"] == "ANNOTATION_CONTRADICTED" and option["status"] == "not_supported" for option in report["options"])
    assert close_session(db_path, session["session_id"])["status"] == "PREVIEW"
    closed = close_session(db_path, session["session_id"], apply=True, confirm_owner=True)
    assert closed["status"] == "CLOSED" and closed["images_stored"] == 0
    with pytest.raises(ValueError, match="active"):
        observe_training(
            db_path, local_tmp, turn=2, annotation=_annotation(turn=2),
            session_id=session["session_id"], apply=True, confirm_owner=True,
        )


def test_lot_c_migration_backs_up_schema_10_and_preserves_existing_data(local_tmp: Path) -> None:
    db_path = local_tmp / "legacy.sqlite3"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute("INSERT INTO metadata VALUES('sentinel','preserved')")
    connection.execute("PRAGMA user_version=10")
    connection.commit()
    connection.close()
    start_session(
        db_path, format="standard", platform="live", as_of="2026-10-13",
        apply=True, confirm_owner=True,
    )
    connection = sqlite3.connect(db_path)
    assert connection.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert connection.execute("SELECT value FROM metadata WHERE key='sentinel'").fetchone()[0] == "preserved"
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    backup = Path(connection.execute("SELECT value FROM metadata WHERE key='last_schema_backup'").fetchone()[0])
    connection.close()
    restored = sqlite3.connect(backup)
    assert restored.execute("PRAGMA user_version").fetchone()[0] == 10
    assert restored.execute("SELECT value FROM metadata WHERE key='sentinel'").fetchone()[0] == "preserved"
    restored.close()


def test_portable_skill_mirrors_are_identical_and_have_valid_minimal_frontmatter() -> None:
    root = Path(__file__).resolve().parents[1]
    codex = (root / ".agents" / "skills" / "visual-training-coach" / "SKILL.md").read_text(encoding="utf-8")
    claude = (root / ".claude" / "skills" / "visual-training-coach" / "SKILL.md").read_text(encoding="utf-8")
    assert codex == claude
    assert codex.startswith("---\nname: visual-training-coach\ndescription:")
    assert "NEEDS_MANUAL_ANNOTATION" in codex and "match advise" in codex


def test_vision_capabilities_never_promote_components_to_operational(monkeypatch) -> None:
    class Present:
        pass

    monkeypatch.setattr("pokemind.visual_coach.importlib.util.find_spec", lambda name: Present())
    monkeypatch.setattr("pokemind.visual_coach.shutil.which", lambda name: "synthetic-tesseract")
    status = vision_backend_status()
    assert status["components_detected"]
    assert status["operational"] is False
    assert status["adapter"]["configured"] is False
    assert status["reason_code"] == "NO_CALIBRATED_LOCAL_VISION_ADAPTER"
    assert status["synthetic_pixel_adapter"] == {
        "installed": True,
        "available": True,
        "calibrated": False,
        "verified_on_synthetic": True,
        "verified_on_user_training": False,
        "formats": ["PNG RGB/RGBA 8-bit non-interlaced"],
        "scope": "explicit calibration markers; not general card recognition",
    }


def test_calibrated_adapter_reads_real_synthetic_pixels_and_feeds_memory_and_advice(
    local_tmp: Path,
) -> None:
    image = _rgb_png(local_tmp / "markers.png", [[
        (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
    ], [
        (255, 0, 255), (0, 255, 255), (128, 128, 128), (128, 128, 128),
    ]])
    calibration = _calibration(local_tmp / "calibration.json")
    db_path = local_tmp / "vision.sqlite3"
    _install_attack(db_path, cost=["Colorless"])
    session = start_session(
        db_path, format="standard", platform="live", as_of="2026-10-13",
        apply=True, confirm_owner=True,
    )
    observed = observe_training(
        db_path, local_tmp, turn=1, image_path=image, calibration_path=calibration,
        session_id=session["session_id"], frame_scope="full_board",
        apply=True, confirm_owner=True,
    )
    assert observed["status"] == "SAVED"
    assert observed["vision_backend"]["calibrated"] is False
    assert observed["vision_backend"]["synthetic_marker_coordinates_calibrated"] is True
    assert observed["vision_backend"]["verified_on_synthetic"] is True
    assert observed["vision_backend"]["verified_on_user_training"] is False
    active = observed["state"]["sides"]["self"]["active"]
    assert active["card"]["name"] == "Synthetic Active"
    assert active["provenance"] == active["card"]["provenance"] == "ocr_uncertain"
    memory = session_memory(db_path, session["session_id"])
    assert memory["observations"][0]["source_kind"] == "local_vision"
    advice = advise_turn(
        db_path, session["session_id"], turn=1, format="standard",
        platform="live", as_of="2026-10-13",
    )
    assert advice["recommended_sequence"] == []
    assert advice["status"] == "INSUFFICIENT_EVIDENCE"


def test_calibrated_adapter_fails_closed_on_occluded_or_shifted_markers(local_tmp: Path) -> None:
    image = _rgb_png(local_tmp / "occluded.png", [[
        (99, 99, 99), (0, 255, 0), (0, 0, 255), (255, 255, 0),
    ], [
        (255, 0, 255), (0, 255, 255), (128, 128, 128), (128, 128, 128),
    ]])
    calibration = _calibration(local_tmp / "calibration.json")
    result = observe_training(
        local_tmp / "absent.sqlite3", local_tmp, turn=1,
        image_path=image, calibration_path=calibration,
    )
    assert result["state"]["phase"] == "unknown"
    assert "phase" in result["state"]["unknown_fields"]
    profile = json.loads(calibration.read_text(encoding="utf-8"))
    profile["markers"][0]["x"] = 99
    calibration.write_text(json.dumps(profile), encoding="utf-8")
    with pytest.raises(ValueError, match="VISION_CALIBRATION_OUT_OF_FRAME"):
        observe_training(
            local_tmp / "absent.sqlite3", local_tmp, turn=1,
            image_path=image, calibration_path=calibration,
        )


def test_calibration_cannot_replace_internal_semantic_mapping(local_tmp: Path) -> None:
    image = _rgb_png(local_tmp / "markers.png", [[
        (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
    ], [
        (255, 0, 255), (0, 255, 255), (128, 128, 128), (128, 128, 128),
    ]])
    calibration = _calibration(local_tmp / "calibration.json")
    profile = json.loads(calibration.read_text(encoding="utf-8"))
    profile["markers"][2]["values"] = {"0,0,255": "Forged Card"}
    calibration.write_text(json.dumps(profile), encoding="utf-8")
    with pytest.raises(ValueError, match="VISION_CALIBRATION_INVALID"):
        observe_training(
            local_tmp / "absent.sqlite3", local_tmp, turn=1,
            image_path=image, calibration_path=calibration,
        )
