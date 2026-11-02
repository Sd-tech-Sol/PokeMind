"""Optional local OCR contract: explicit PNG/ROI, bounded process, no download.

The adapter is NOT calibrated on owner training. Even an exact multifield catalog
match remains an OCR candidate; it cannot authorize a game action on its own.
"""

from __future__ import annotations

import csv
import io
import json
import math
import os
import re
import shutil
import struct
import subprocess
import unicodedata
import zlib
from pathlib import Path
from typing import Any, Callable

from pokemind.database import connect_readonly


ADAPTER = "pokemind_tesseract_roi_v1"
MAX_FIELDS = 12
MAX_TSV_BYTES = 256_000
FIELDS = {"name", "set_code", "collector_number", "hp", "damage", "energy_type", "energy_count", "phase", "turn_owner"}


def _normalized(value: Any) -> str:
    return " ".join(unicodedata.normalize("NFC", str(value or "")).casefold().split())


def _png_region(width: int, pixels: list[tuple[int, int, int]], roi: tuple[int, int, int, int]) -> bytes:
    x, y, w, h = roi
    raw = b"".join(b"\x00" + b"".join(bytes(pixels[row * width + col]) for col in range(x, x + w)) for row in range(y, y + h))

    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def _run_tesseract(png: bytes, language: str, *, policy_path=None, expected_policy_sha256=None) -> str:
    from pokemind.ocr_trust import run_reviewed
    if policy_path is None:
        raise ValueError("OCR_TRUST_POLICY_REQUIRED")
    if language not in {"eng", "fra", "eng+fra"}:
        raise ValueError("OCR_LANGUAGE_REJECTED")
    try:
        output = run_reviewed(policy_path, ["stdin", "stdout", "-l", language, "--psm", "7", "tsv"],
                              input_bytes=png, limit=MAX_TSV_BYTES, timeout=10,
                              expected_policy_sha256=expected_policy_sha256)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError("LOCAL_OCR_PROCESS_FAILED") from exc
    return output.decode("utf-8", errors="strict")


def _tsv_line(tsv: str, threshold: float) -> tuple[str | None, float, str]:
    if not isinstance(tsv, str) or len(tsv.encode("utf-8")) > MAX_TSV_BYTES:
        return None, 0.0, "OCR_OUTPUT_INVALID"
    try:
        rows = list(csv.DictReader(io.StringIO(tsv), delimiter="\t"))
        if len(rows) > 1000:
            return None, 0.0, "OCR_OUTPUT_INVALID"
        words = [row for row in rows if row.get("level") == "5" and str(row.get("text") or "").strip()]
        if not words:
            return None, 0.0, "OCR_TEXT_UNREADABLE"
        lines = {(row.get("page_num"), row.get("block_num"), row.get("par_num"), row.get("line_num")) for row in words}
        if len(lines) != 1:
            return None, 0.0, "OCR_MULTIPLE_LINES_AMBIGUOUS"
        scores = [float(row["conf"]) / 100 for row in words]
        if any(not math.isfinite(score) or not 0 <= score <= 1 for score in scores):
            return None, 0.0, "OCR_SCORE_INVALID"
        score = min(scores)
        text = unicodedata.normalize("NFC", " ".join(str(row["text"]).strip() for row in words))
        if score < threshold or len(text) > 200 or any(ord(char) < 32 for char in text):
            return None, score, "OCR_BELOW_THRESHOLD"
        return text, score, "OCR_UNCALIBRATED_CANDIDATE"
    except (KeyError, TypeError, ValueError, csv.Error):
        return None, 0.0, "OCR_OUTPUT_INVALID"


def _catalog_candidate(db_path: Path, values: dict[str, str], *, as_of: str | None, language: str = "eng+fra") -> tuple[str | None, str]:
    if not all(values.get(field) for field in ("name", "set_code", "collector_number", "hp")):
        return None, "IDENTITY_FIELDS_INCOMPLETE"
    if not db_path.is_file():
        return None, "CATALOG_UNAVAILABLE"
    connection = connect_readonly(db_path)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"catalog_sets", "catalog_printings", "catalog_translations"}.issubset(tables):
            return None, "CATALOG_UNAVAILABLE"
        rows = connection.execute(
            """SELECT p.tcgdex_id,p.local_id,p.hp,s.tcg_online_code,t.name,t.source_url,t.retrieved_at,
                      t.language,p.detail_stale_en,p.detail_stale_fr
               FROM catalog_printings p JOIN catalog_sets s ON s.tcgdex_id=p.set_id
               JOIN catalog_translations t ON t.printing_id=p.tcgdex_id
               WHERE t.status='present' AND p.category='pokemon'
                 AND lower(s.tcg_online_code)=lower(?) AND p.local_id=?""",
            (values["set_code"].strip(), values["collector_number"].strip()),
        )
        matches = set()
        for row in rows:
            allowed = {"eng": {"en"}, "fra": {"fr"}, "eng+fra": {"en", "fr"}}[language]
            if row["language"] not in allowed or row["detail_stale_" + row["language"]]:
                continue
            if not row["source_url"] or not row["retrieved_at"] or (as_of and str(row["retrieved_at"])[:10] > as_of):
                continue
            if all(_normalized(row[column]) == _normalized(values[field]) for column, field in (
                ("name", "name"), ("tcg_online_code", "set_code"), ("local_id", "collector_number"),
            )):
                if "hp" in values and str(row["hp"]) != values["hp"]:
                    return None, "IDENTITY_HP_CONFLICT"
                matches.add(str(row["tcgdex_id"]))
        if len(matches) == 1:
            return next(iter(matches)), "EXACT_MULTIFIELD_OCR_CANDIDATE"
        return None, "IDENTITY_AMBIGUOUS" if matches else "IDENTITY_NOT_VERIFIED"
    finally:
        connection.close()


def recognize_local_text(
    db_path: Path, image_path: Path, calibration_path: Path, private_root: Path,
    *, turn: int, as_of: str | None = None,
    _runner: Callable[[bytes, str], str] | None = None,
    ocr_policy=None, execute_reviewed_ocr=False,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    from pokemind.visual_coach import MAX_CALIBRATION_BYTES, MAX_IMAGE_BYTES, _normalize_board_state, _png_rgb_pixels, _private_file, _read_bounded

    profile = json.loads(_read_bounded(_private_file(calibration_path, private_root), MAX_CALIBRATION_BYTES).decode("utf-8"))
    if not isinstance(profile, dict) or profile.get("adapter") != ADAPTER or profile.get("schema_version") != 1:
        raise ValueError("VISION_CALIBRATION_INVALID")
    if image_path.suffix.casefold() != ".png":
        raise ValueError("VISION_ADAPTER_REQUIRES_PNG")
    fields = profile.get("fields")
    language = profile.get("language", "eng")
    if language not in {"eng", "fra", "eng+fra"} or not isinstance(fields, list) or not 1 <= len(fields) <= MAX_FIELDS:
        raise ValueError("VISION_CALIBRATION_INVALID")
    backend = {
        "name": "local_tesseract_roi", "status": "VISION_BACKEND_UNAVAILABLE",
        "operational": False, "calibrated": False, "verified_on_synthetic": False,
        "verified_on_user_training": False, "network_used": False,
        "scope": "explicit single-line text ROI; OCR candidates only",
        "test_contract_only": _runner is not None,
    }
    if _runner is None:
        from pokemind.ocr_preflight import ocr_preflight
        diagnostic = ocr_preflight(policy_path=ocr_policy, execute=execute_reviewed_ocr)
        if diagnostic["status"] != "OCR_INSTALLED_UNCALIBRATED":
            return None, {**backend, "reason_code": diagnostic["status"]}
    raw = _read_bounded(_private_file(image_path, private_root), MAX_IMAGE_BYTES)
    width, height, pixels = _png_rgb_pixels(raw)
    reference = profile.get("reference_size")
    if not isinstance(reference, list) or len(reference) != 2 or any(type(n) is not int or n < 1 for n in reference):
        raise ValueError("VISION_CALIBRATION_INVALID")
    if abs(width / reference[0] - height / reference[1]) > 0.01:
        raise ValueError("VISION_FRAME_ASPECT_MISMATCH")
    values: dict[str, str] = {}
    evidence = []
    seen = set()
    try:
        for field in fields:
            if not isinstance(field, dict) or field.get("field") not in FIELDS or field["field"] in seen:
                raise ValueError("VISION_CALIBRATION_INVALID")
            name = field["field"]
            seen.add(name)
            roi = field.get("roi")
            threshold = field.get("min_confidence", 0.95)
            if not isinstance(roi, list) or len(roi) != 4 or any(type(n) is not int for n in roi) or type(threshold) not in {int, float} or not 0.9 <= threshold <= 1:
                raise ValueError("VISION_CALIBRATION_INVALID")
            x, y, w, h = roi
            if min(x, y) < 0 or min(w, h) < 1 or x + w > reference[0] or y + h > reference[1]:
                raise ValueError("VISION_CALIBRATION_OUT_OF_FRAME")
            mapped = (round(x * width / reference[0]), round(y * height / reference[1]), round(w * width / reference[0]), round(h * height / reference[1]))
            if min(mapped[2:]) < 1 or mapped[0] + mapped[2] > width or mapped[1] + mapped[3] > height:
                raise ValueError("VISION_CALIBRATION_OUT_OF_FRAME")
            png = _png_region(width, pixels, mapped)
            tsv = _runner(png, language) if _runner else _run_tesseract(png, language, policy_path=ocr_policy, expected_policy_sha256=diagnostic["policy_sha256"])
            text, score, reason = _tsv_line(tsv, float(threshold))
            if text is not None and name in {"hp", "damage", "energy_count"}:
                if not re.fullmatch(r"\d{1,4}", text) or (name == "energy_count" and not 1 <= int(text) <= 99):
                    text, reason = None, "OCR_COUNTER_INVALID"
            if text is not None:
                values[name] = text
            evidence.append({"field": name, "score": round(score, 6), "threshold": threshold, "accepted_candidate": text is not None, "reason_code": reason})
    finally:
        del raw, pixels
    identity, identity_reason = _catalog_candidate(db_path, values, as_of=as_of, language=language)
    active: dict[str, Any] = {"visibility": "ambiguous", "provenance": "ocr_uncertain"}
    if values.get("name"):
        active["card"] = {"name": values["name"], "tcgdex_id": identity, "set_code": values.get("set_code"), "collector_number": values.get("collector_number"), "provenance": "ocr_uncertain", "confidence": "uncertain"}
    if "damage" in values:
        active["damage"] = int(values["damage"])
    # No icon-to-energy guess: only an explicit, supported text label plus count.
    energy = next((item for item in ("Grass", "Fire", "Water", "Lightning", "Psychic", "Fighting", "Darkness", "Metal", "Colorless") if _normalized(item) == _normalized(values.get("energy_type"))), None)
    if energy and "energy_count" in values:
        active["energies"] = [{"type": energy, "count": int(values["energy_count"]), "provenance": "ocr_uncertain"}]
    state = _normalize_board_state({
        "turn": turn, "phase": "unknown", "turn_owner": "unknown", "sides": {"self": {"active": active}},
        "unknown_fields": ["OCR_NOT_CALIBRATED_OWNER_CONFIRMATION_REQUIRED", identity_reason] + [field for field in sorted(seen) if field not in values],
        "recognition_errors": [],
    }, turn=turn, trusted_visual=True)
    return state, {**backend, "status": "OCR_UNCALIBRATED_CANDIDATES", "operational": True, "field_evidence": evidence, "identity_status": identity_reason}
