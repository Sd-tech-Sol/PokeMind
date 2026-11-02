from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path

from pokemind.readiness import v1_readiness
from pokemind.recovery import create_backup, restore_backup
from pokemind.visual_coach import observe_training, session_memory, start_session


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(
        ">I", zlib.crc32(kind + payload) & 0xFFFFFFFF
    )


def _vision_fixture(root: Path) -> tuple[Path, Path]:
    pixels = [[(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]]
    raw = b"\x00" + b"".join(bytes(pixel) for pixel in pixels[0])
    image = root / "lot-f-board.png"
    image.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", 4, 1, 8, 2, 0, 0, 0))
        + _chunk(b"IDAT", zlib.compress(raw))
        + _chunk(b"IEND", b"")
    )
    calibration = root / "lot-f-calibration.json"
    calibration.write_text(json.dumps({
        "schema_version": 1,
        "adapter": "pokemind_marker_v1",
        "markers": [
            {"field": "phase", "x": 0, "y": 0, "width": 1, "height": 1, "values": {"255,0,0": "attack", "192,0,0": "main"}},
            {"field": "turn_owner", "x": 1, "y": 0, "width": 1, "height": 1, "values": {"0,255,0": "self", "0,192,0": "opponent"}},
            {"field": "self_active_name", "x": 2, "y": 0, "width": 1, "height": 1, "values": {"0,0,255": "Synthetic Active"}},
            {"field": "self_active_id", "x": 3, "y": 0, "width": 1, "height": 1, "values": {"255,255,0": "syn-1"}},
        ],
    }), encoding="utf-8")
    return image, calibration


def test_lot_f_synthetic_end_to_end_recovery_vision_memory_and_readiness(local_tmp: Path) -> None:
    db_path = local_tmp / "lot-f.sqlite3"
    session = start_session(
        db_path, format="standard", platform="live", as_of="2026-10-13",
        apply=True, confirm_owner=True,
    )
    image, calibration = _vision_fixture(local_tmp)
    observed = observe_training(
        db_path, local_tmp, turn=1, image_path=image, calibration_path=calibration,
        session_id=session["session_id"], apply=True, confirm_owner=True,
    )
    assert observed["status"] == "SAVED"
    assert session_memory(db_path, session["session_id"])["observations"][0]["source_kind"] == "local_vision"

    destination = local_tmp / "backups"
    created = create_backup(
        db_path, destination, apply=True, confirm_owner=True, min_free_bytes=0,
    )
    restored = local_tmp / "restored.sqlite3"
    recovery = restore_backup(
        destination / created["backup_file"], restored,
        apply=True, confirm_owner=True, min_free_bytes=0,
    )
    assert recovery["state"] == "verified"
    memory = session_memory(restored, session["session_id"])
    assert memory["observations"][0]["state"]["sides"]["self"]["active"]["card"]["name"] == "Synthetic Active"

    report = v1_readiness(restored, backup_directory=destination)
    assert report["status"] == "NOT_RELEASE_READY"
    assert report["backups"]["verified_count"] == 1
    assert report["vision"]["synthetic_pixel_adapter"]["verified_on_synthetic"] is True
    assert "VISION_NOT_VERIFIED_ON_OWNER_TRAINING" in report["blockers"]
