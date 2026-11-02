"""Deterministic raster text, not markers or mocked OCR. No optional dependencies.

Original 5x7 glyphs below are project code. The deliberately simple typography is
only a synthetic test corpus, never a calibration for real Pokémon screenshots.
"""
from __future__ import annotations

import hashlib
import statistics
import time
import tracemalloc
import unicodedata
from typing import Any

from pokemind.local_ocr import _png_region, _run_tesseract, _tsv_line, _normalized


_GLYPHS = {
    "A":"01110/10001/10001/11111/10001/10001/10001", "B":"11110/10001/10001/11110/10001/10001/11110",
    "C":"01111/10000/10000/10000/10000/10000/01111", "D":"11110/10001/10001/10001/10001/10001/11110",
    "E":"11111/10000/10000/11110/10000/10000/11111", "F":"11111/10000/10000/11110/10000/10000/10000",
    "G":"01111/10000/10000/10111/10001/10001/01111", "H":"10001/10001/10001/11111/10001/10001/10001",
    "I":"11111/00100/00100/00100/00100/00100/11111", "J":"00111/00010/00010/00010/10010/10010/01100",
    "K":"10001/10010/10100/11000/10100/10010/10001", "L":"10000/10000/10000/10000/10000/10000/11111",
    "M":"10001/11011/10101/10101/10001/10001/10001", "N":"10001/11001/11001/10101/10011/10011/10001",
    "O":"01110/10001/10001/10001/10001/10001/01110", "P":"11110/10001/10001/11110/10000/10000/10000",
    "Q":"01110/10001/10001/10001/10101/10010/01101", "R":"11110/10001/10001/11110/10100/10010/10001",
    "S":"01111/10000/10000/01110/00001/00001/11110", "T":"11111/00100/00100/00100/00100/00100/00100",
    "U":"10001/10001/10001/10001/10001/10001/01110", "V":"10001/10001/10001/10001/10001/01010/00100",
    "W":"10001/10001/10001/10101/10101/10101/01010", "X":"10001/10001/01010/00100/01010/10001/10001",
    "Y":"10001/10001/01010/00100/00100/00100/00100", "Z":"11111/00001/00010/00100/01000/10000/11111",
    "0":"01110/10001/10011/10101/11001/10001/01110", "1":"00100/01100/00100/00100/00100/00100/01110",
    "2":"01110/10001/00001/00010/00100/01000/11111", "3":"11110/00001/00001/01110/00001/00001/11110",
    "4":"00010/00110/01010/10010/11111/00010/00010", "5":"11111/10000/10000/11110/00001/00001/11110",
    "6":"01110/10000/10000/11110/10001/10001/01110", "7":"11111/00001/00010/00100/01000/01000/01000",
    "8":"01110/10001/10001/01110/10001/10001/01110", "9":"01110/10001/10001/01111/00001/00001/01110",
    " ":"00000/00000/00000/00000/00000/00000/00000", "-":"00000/00000/00000/11111/00000/00000/00000",
}
VARIANTS = ("clean", "small", "zoom", "crop", "rotate", "noise", "occluded", "wrong_printing", "unknown", "wrong_number", "wrong_hp")


def raster_text(text: str, variant: str = "clean") -> bytes:
    if variant not in VARIANTS or not 1 <= len(text) <= 80:
        raise ValueError("BENCHMARK_INPUT_INVALID")
    scale = 2 if variant == "small" else (6 if variant == "zoom" else 4)
    width, height = (len(text) * 6 + 8) * scale, 15 * scale
    pixels = [(255, 255, 255)] * (width * height)
    for i, char in enumerate(text.upper()):
        decomposed = unicodedata.normalize("NFD", char)
        glyph = _GLYPHS.get(decomposed[0])
        if glyph is None:
            raise ValueError("BENCHMARK_GLYPH_UNSUPPORTED")
        cells = [(x, y + 3) for y, row in enumerate(glyph.split("/")) for x, bit in enumerate(row) if bit == "1"]
        if len(decomposed) > 1:  # visible accent, not removed from the raster
            cells += [(2, 1), (3, 0)]
        for x, y in cells:
            for dy in range(scale):
                for dx in range(scale):
                    px, py = (4 + i * 6 + x) * scale + dx, y * scale + dy
                    if variant == "rotate":  # bounded shear approximates a tilted text line
                        py += (px - width // 2) // 24
                    if 0 <= py < height:
                        pixels[py * width + px] = (0, 0, 0)
    if variant == "noise":
        for i in range(0, len(pixels), 97):
            pixels[i] = (128, 128, 128)
    if variant == "occluded":
        for y in range(height):
            for x in range(width // 3, 2 * width // 3):
                pixels[y * width + x] = (255, 255, 255)
    roi = (width // 4, 0, width // 2, height) if variant == "crop" else (0, 0, width, height)
    return _png_region(width, pixels, roi)


def synthetic_corpus():
    for language, name in (("eng", "SYNTHETIC DRAGON"), ("fra", "DRAGON SYNTHÉTIQUE")):
        for variant in VARIANTS:
            fields = {"name": "UNKNOWN CREATURE" if variant == "unknown" else name,
                      "set_code": "BAD" if variant == "wrong_printing" else "SYN",
                      "collector_number": "008" if variant == "wrong_number" else "007",
                      "hp": "220" if variant == "wrong_hp" else "120"}
            yield {"language": language, "variant": variant, "fields": fields,
                   "identity_expected": variant not in {"unknown", "wrong_printing", "wrong_number", "wrong_hp", "crop", "occluded"}}


def benchmark_ocr(*, policy_path=None, execute=False) -> dict[str, Any]:
    from pokemind.ocr_preflight import ocr_preflight
    diagnostic = ocr_preflight(policy_path=policy_path, execute=execute)
    available = diagnostic["status"] == "OCR_INSTALLED_UNCALIBRATED"
    started = time.perf_counter()
    tracemalloc.start()
    cases, field_metrics, latencies, fingerprint = [], {}, [], hashlib.sha256()
    for case in synthetic_corpus():
        accepted, all_exact = {}, True
        errors = []
        for field, expected in case["fields"].items():
            png = raster_text(expected, case["variant"])
            fingerprint.update(png)
            metrics = field_metrics.setdefault(field, {"samples": 0, "attempted": 0, "wrong_accepted": 0, "exact": 0, "abstained": 0})
            metrics["samples"] += 1
            if not available:
                continue
            tick = time.perf_counter()
            try:
                candidate, _, reason = _tsv_line(_run_tesseract(png, case["language"], policy_path=policy_path, expected_policy_sha256=diagnostic["policy_sha256"]), .95)
            except ValueError:
                candidate, reason = None, "OCR_ENGINE_OR_LANGUAGE_UNAVAILABLE"
                errors.append(reason)
            latencies.append(time.perf_counter() - tick)
            metrics["attempted"] += 1
            metrics["abstained"] += int(candidate is None)
            exact = candidate is not None and _normalized(candidate) == _normalized(expected)
            metrics["exact"] += int(exact)
            metrics["wrong_accepted"] += int(candidate is not None and not exact)
            all_exact &= exact
            if candidate is not None:
                accepted[field] = candidate
        # Local synthetic reference only: bad printing/unknown must never resolve.
        reference_name = "SYNTHETIC DRAGON" if case["language"] == "eng" else "DRAGON SYNTHÉTIQUE"
        identity = all(_normalized(accepted.get(f)) == _normalized(v) for f, v in {
            "name": reference_name, "set_code": "SYN", "collector_number": "007", "hp": "120"}.items()) if available else None
        cases.append({"language": case["language"], "variant": case["variant"],
                      "identity_candidate": identity, "identity_expected": case["identity_expected"],
                      "all_fields_exact": all_exact if available else None, "errors": errors})
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    attempted = sum(m["attempted"] for m in field_metrics.values())
    return {"schema_version": 1, "corpus_version": "synthetic_text_v1", "corpus_sha256": fingerprint.hexdigest(),
            "status": "BENCHMARK_EXECUTED" if available else diagnostic["status"],
            "release_status": "BLOCKED_WITH_REASON", "real_ocr_executed": bool(attempted),
            "mock_used": False, "network_used": False, "images_persisted": 0,
            "case_count": len(cases), "fields": field_metrics, "cases": cases,
            "identity_false_positives": sum(c["identity_candidate"] is True and not c["identity_expected"] for c in cases) if attempted else None,
            "abstention_rate": sum(m["abstained"] for m in field_metrics.values()) / attempted if attempted else None,
            "wall_seconds": round(time.perf_counter() - started, 4),
            "ocr_latency_median_seconds": round(statistics.median(latencies), 4) if latencies else None,
            "python_peak_bytes": peak, "engine_cpu_seconds": None, "engine_peak_bytes": None,
            "calibrated_on_owner": False, "visual_certain_allowed": False,
            "limits": ["Original 5x7 font; rotation is shear; not real-card calibration.",
                       "Engine CPU/RSS unmeasured; Python allocation peak excludes child process."]}
