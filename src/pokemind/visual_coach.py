"""Coach visuel local et prudent pour entraînements explicitement autorisés."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import secrets
import shutil
import sqlite3
import struct
import zlib
from datetime import date
from pathlib import Path
from typing import Any

from pokemind.database import connect_readonly, connect_writable, initialize_schema, utc_now


BOARD_SCHEMA_VERSION = 1
MAX_IMAGE_BYTES = 25 * 1024 * 1024
MAX_IMAGE_PIXELS = 50_000_000
MAX_ADAPTER_PIXELS = 1_000_000
MAX_DIMENSION = 20_000
MAX_ANNOTATION_BYTES = 1_000_000
MAX_CALIBRATION_BYTES = 256_000
_PROVENANCE = {"visual_certain", "ocr_uncertain", "owner_annotated", "inferred", "unknown"}
# No independently calibrated real-image producer exists yet. In particular,
# legacy synthetic observations carrying visual_certain cannot authorize advice.
_FACT_PROVENANCE = {"owner_annotated"}
_BASIC_ENERGY_TYPES = {
    "grass": "Grass", "fire": "Fire", "water": "Water", "lightning": "Lightning",
    "psychic": "Psychic", "fighting": "Fighting", "darkness": "Darkness",
    "metal": "Metal", "fairy": "Fairy", "dragon": "Dragon", "colorless": "Colorless",
}
_SYNTHETIC_MARKER_VALUES: dict[str, dict[str, Any]] = {
    "phase": {"255,0,0": "attack", "192,0,0": "main"},
    "turn_owner": {"0,255,0": "self", "0,192,0": "opponent"},
    "self_active_name": {"0,0,255": "Synthetic Active"},
    "self_active_id": {"255,255,0": "syn-1"},
    "self_active_damage": {"128,0,0": 20},
    "self_active_energy_type": {"255,0,255": "Colorless"},
    "self_active_energy_count": {"0,255,255": 1},
}


def vision_backend_status() -> dict[str, Any]:
    """Décrit les composants locaux sans les importer, installer ou exécuter."""
    components = {
        "pillow": importlib.util.find_spec("PIL") is not None,
        "opencv": importlib.util.find_spec("cv2") is not None,
        "pytesseract": importlib.util.find_spec("pytesseract") is not None,
        "tesseract_executable": shutil.which("tesseract") is not None,
        "easyocr": importlib.util.find_spec("easyocr") is not None,
        "onnxruntime": importlib.util.find_spec("onnxruntime") is not None,
    }
    available = [name for name, present in components.items() if present]
    return {
        "status": "VISION_BACKEND_UNAVAILABLE",
        "operational": False,
        "local_only": True,
        "network_used": False,
        "cloud_allowed": False,
        "automatic_install": False,
        "components": components,
        "components_detected": available,
        "adapter": {
            "configured": False,
            "model_or_ruleset": None,
            "calibration_id": None,
            "minimum_required_evidence": [
                "backend local explicitement configuré",
                "calibration sur images synthétiques distinctes",
                "score et seuils par champ observable",
                "identité ambiguë retournée unknown",
                "essai réel d'entraînement autorisé par le propriétaire",
            ],
        },
        "synthetic_pixel_adapter": {
            "installed": True,
            "available": True,
            "calibrated": False,
            "verified_on_synthetic": True,
            "verified_on_user_training": False,
            "formats": ["PNG RGB/RGBA 8-bit non-interlaced"],
            "scope": "explicit calibration markers; not general card recognition",
        },
        "text_adapter": {
            "installed_code": True,
            "available": False,
            "path_candidate_detected": components["tesseract_executable"],
            "execution_requires": "explicit reviewed policy and execution opt-in",
            "calibrated": False,
            "verified_on_synthetic": False,
            "verified_on_user_training": False,
            "scope": "optional local Tesseract single-line ROI; uncalibrated candidates",
            "test_evidence": "contract tests plus H raster corpus; actual benchmark requires installed engine",
        },
        "reason_code": "NO_CALIBRATED_LOCAL_VISION_ADAPTER",
        "owner_action_required": "installation facultative, calibration et essai réel avec consentements distincts",
    }


def _png_rgb_pixels(payload: bytes) -> tuple[int, int, list[tuple[int, int, int]]]:
    """Decode bounded PNG pixels with the standard library (no metadata inference)."""
    width, height, _ = _png_metadata(payload)
    if width * height > MAX_ADAPTER_PIXELS:
        raise ValueError("VISION_IMAGE_TOO_LARGE_FOR_LOCAL_ADAPTER")
    offset = 8
    color_type = bit_depth = interlace = None
    compressed = bytearray()
    while offset + 12 <= len(payload):
        length = int.from_bytes(payload[offset:offset + 4], "big")
        kind = payload[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(payload):
            raise ValueError("Bloc PNG tronqué.")
        chunk = payload[offset + 8:offset + 8 + length]
        expected_crc = int.from_bytes(payload[offset + 8 + length:end], "big")
        if zlib.crc32(kind + chunk) & 0xFFFFFFFF != expected_crc:
            raise ValueError("CRC PNG invalide.")
        if kind == b"IHDR":
            bit_depth, color_type, _, _, interlace = chunk[8:13]
        elif kind == b"IDAT":
            compressed.extend(chunk)
        elif kind == b"IEND":
            break
        offset = end
    if bit_depth != 8 or color_type not in {2, 6} or interlace != 0:
        raise ValueError("VISION_PNG_VARIANT_UNSUPPORTED")
    channels = 3 if color_type == 2 else 4
    stride = width * channels
    expected_size = (stride + 1) * height
    try:
        decompressor = zlib.decompressobj()
        raw = decompressor.decompress(bytes(compressed), expected_size + 1)
        if len(raw) > expected_size or decompressor.unconsumed_tail:
            raise ValueError("Données PNG décompressées hors limites.")
        if len(raw) < expected_size:
            raw += decompressor.flush(expected_size - len(raw) + 1)
    except (zlib.error, TypeError) as exc:
        raise ValueError("Données PNG invalides.") from exc
    if len(raw) != expected_size or not decompressor.eof:
        raise ValueError("Dimensions PNG incohérentes.")
    previous = bytearray(stride)
    pixels: list[tuple[int, int, int]] = []
    position = 0
    for _ in range(height):
        filter_type = raw[position]
        position += 1
        row = bytearray(raw[position:position + stride])
        position += stride
        if filter_type not in {0, 1, 2, 3, 4}:
            raise ValueError("Filtre PNG non pris en charge.")
        for index in range(stride):
            left = row[index - channels] if index >= channels else 0
            up = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 1:
                row[index] = (row[index] + left) & 0xFF
            elif filter_type == 2:
                row[index] = (row[index] + up) & 0xFF
            elif filter_type == 3:
                row[index] = (row[index] + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                estimate = left + up - upper_left
                distances = (abs(estimate - left), abs(estimate - up), abs(estimate - upper_left))
                predictor = (left, up, upper_left)[distances.index(min(distances))]
                row[index] = (row[index] + predictor) & 0xFF
        for x in range(width):
            start = x * channels
            if channels == 4 and row[start + 3] != 255:
                raise ValueError("VISION_TRANSPARENCY_UNSUPPORTED")
            pixels.append((row[start], row[start + 1], row[start + 2]))
        previous = row
    return width, height, pixels


def _calibrated_marker_state(
    image_path: Path, calibration_path: Path, private_root: Path, *, turn: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    image = _private_file(image_path, private_root)
    calibration = _private_file(calibration_path, private_root)
    if image.suffix.casefold() != ".png":
        raise ValueError("VISION_ADAPTER_REQUIRES_PNG")
    calibration_payload = _read_bounded(calibration, MAX_CALIBRATION_BYTES)
    try:
        profile = json.loads(calibration_payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("VISION_CALIBRATION_INVALID") from exc
    if not isinstance(profile, dict) or profile.get("schema_version") != 1 or profile.get("adapter") != "pokemind_marker_v1":
        raise ValueError("VISION_CALIBRATION_INVALID")
    raw = _read_bounded(image, MAX_IMAGE_BYTES)
    width, height, pixels = _png_rgb_pixels(raw)
    markers = profile.get("markers")
    if not isinstance(markers, list) or not 1 <= len(markers) <= 32:
        raise ValueError("VISION_CALIBRATION_INVALID")
    allowed = set(_SYNTHETIC_MARKER_VALUES)
    recognized: dict[str, Any] = {}
    evidence: list[dict[str, Any]] = []
    unknown: list[str] = []
    for marker in markers:
        if not isinstance(marker, dict) or marker.get("field") not in allowed:
            raise ValueError("VISION_CALIBRATION_INVALID")
        field = str(marker["field"])
        try:
            x, y, region_width, region_height = (int(marker[key]) for key in ("x", "y", "width", "height"))
            threshold = float(marker.get("min_match", 0.95))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("VISION_CALIBRATION_INVALID") from exc
        if x < 0 or y < 0 or region_width < 1 or region_height < 1 or x + region_width > width or y + region_height > height or not 0.5 <= threshold <= 1.0:
            raise ValueError("VISION_CALIBRATION_OUT_OF_FRAME")
        values = marker.get("values")
        # Coordinates and thresholds are configurable, but semantic mappings are
        # an immutable adapter ruleset. A private JSON cannot mint a card identity.
        if values != _SYNTHETIC_MARKER_VALUES[field]:
            raise ValueError("VISION_CALIBRATION_INVALID")
        region = [pixels[row * width + column] for row in range(y, y + region_height) for column in range(x, x + region_width)]
        scores: list[tuple[float, Any]] = []
        for color, value in values.items():
            try:
                expected = tuple(int(part) for part in str(color).split(","))
            except ValueError as exc:
                raise ValueError("VISION_CALIBRATION_INVALID") from exc
            if len(expected) != 3 or any(part < 0 or part > 255 for part in expected):
                raise ValueError("VISION_CALIBRATION_INVALID")
            scores.append((sum(pixel == expected for pixel in region) / len(region), value))
        scores.sort(key=lambda item: item[0], reverse=True)
        best_score, best_value = scores[0]
        ambiguous = len(scores) > 1 and scores[1][0] == best_score
        accepted = best_score >= threshold and not ambiguous
        evidence.append({"field": field, "score": round(best_score, 6), "threshold": threshold, "accepted": accepted})
        if accepted:
            recognized[field] = best_value
        else:
            unknown.append(field)
    slot: dict[str, Any] = {"visibility": "unknown", "provenance": "unknown"}
    if "self_active_name" in recognized or "self_active_id" in recognized:
        slot = {
            "visibility": "ambiguous", "provenance": "ocr_uncertain",
            "card": {
                "name": recognized.get("self_active_name"),
                "tcgdex_id": recognized.get("self_active_id"),
                "provenance": "ocr_uncertain", "confidence": "uncertain",
            },
        }
    if "self_active_damage" in recognized:
        slot["damage"] = recognized["self_active_damage"]
    if "self_active_energy_type" in recognized and "self_active_energy_count" in recognized:
        slot["energies"] = [{
            "type": recognized["self_active_energy_type"],
            "count": recognized["self_active_energy_count"],
            "provenance": "ocr_uncertain",
        }]
    state = _normalize_board_state({
        "turn": turn,
        "phase": recognized.get("phase", "unknown"),
        "turn_owner": recognized.get("turn_owner", "unknown"),
        "sides": {"self": {"active": slot}},
        "unknown_fields": unknown + ["SYNTHETIC_MARKERS_NOT_REAL_CARD_CALIBRATION"],
        "recognition_errors": [],
    }, turn=turn, trusted_visual=True)
    return state, {
        "name": "stdlib_png_calibrated_markers",
        "status": "VISION_SYNTHETIC_ADAPTER_ACTIVE",
        "operational": True,
        "scope": "calibrated_markers_only",
        "calibrated": False,
        "synthetic_marker_coordinates_calibrated": True,
        "verified_on_synthetic": True,
        "verified_on_user_training": False,
        "calibration_sha256": hashlib.sha256(calibration_payload).hexdigest(),
        "field_evidence": evidence,
        "network_used": False,
    }


def _tables(connection: sqlite3.Connection) -> set[str]:
    return {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _strict_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError) as exc:
        raise ValueError("as_of doit être une date YYYY-MM-DD.") from exc


def _bounded_text(value: Any, field: str, *, maximum: int = 300) -> str:
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise ValueError(f"{field} doit être un texte de 1 à {maximum} caractères.")
    text = value.strip()
    if any(ord(character) < 32 and character not in "\t\n\r" for character in text):
        raise ValueError(f"{field} contient des caractères de contrôle.")
    return text


def _private_file(path: Path, private_root: Path) -> Path:
    root = private_root.resolve(strict=True)
    raw = path if path.is_absolute() else Path.cwd() / path
    resolved = raw.resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError("Le fichier doit rester sous data/local et être un fichier ordinaire.")
    try:
        relative = raw.absolute().relative_to(root)
    except ValueError as exc:
        raise ValueError("Traversée de chemin refusée pour un fichier privé.") from exc
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ValueError("Les liens symboliques sont refusés pour les entrées privées.")
    return resolved


def _read_bounded(path: Path, maximum: int) -> bytes:
    with path.open("rb") as handle:
        payload = handle.read(maximum + 1)
    if not payload or len(payload) > maximum:
        raise ValueError(f"Fichier vide ou supérieur à {maximum} octets.")
    return payload


def _png_metadata(payload: bytes) -> tuple[int, int, int]:
    if len(payload) < 24 or payload[:8] != b"\x89PNG\r\n\x1a\n" or payload[12:16] != b"IHDR":
        raise ValueError("Signature PNG ou bloc IHDR invalide.")
    width, height = struct.unpack(">II", payload[16:24])
    return width, height, 1


def _jpeg_orientation(segment: bytes) -> int | None:
    if not segment.startswith(b"Exif\x00\x00") or len(segment) < 14:
        return None
    data = segment[6:]
    endian = data[:2]
    if endian not in {b"II", b"MM"}:
        return None
    order = "<" if endian == b"II" else ">"
    try:
        offset = struct.unpack(order + "I", data[4:8])[0]
        count = struct.unpack(order + "H", data[offset:offset + 2])[0]
        for index in range(count):
            entry = data[offset + 2 + index * 12:offset + 14 + index * 12]
            if len(entry) == 12 and struct.unpack(order + "H", entry[:2])[0] == 0x0112:
                value = struct.unpack(order + "H", entry[8:10])[0]
                return value if 1 <= value <= 8 else None
    except (IndexError, struct.error):
        return None
    return None


def _jpeg_metadata(payload: bytes) -> tuple[int, int, int | None]:
    if len(payload) < 4 or payload[:2] != b"\xff\xd8":
        raise ValueError("Signature JPEG invalide.")
    offset = 2
    width = height = None
    orientation = None
    sof = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while offset + 4 <= len(payload):
        if payload[offset] != 0xFF:
            offset += 1
            continue
        while offset < len(payload) and payload[offset] == 0xFF:
            offset += 1
        if offset >= len(payload):
            break
        marker = payload[offset]
        offset += 1
        if marker in {0xD8, 0xD9}:
            continue
        if marker == 0xDA:
            break
        if offset + 2 > len(payload):
            break
        length = struct.unpack(">H", payload[offset:offset + 2])[0]
        if length < 2 or offset + length > len(payload):
            raise ValueError("Segment JPEG tronqué.")
        segment = payload[offset + 2:offset + length]
        if marker == 0xE1:
            orientation = _jpeg_orientation(segment) or orientation
        if marker in sof and len(segment) >= 5:
            height, width = struct.unpack(">HH", segment[1:5])
        offset += length
    if width is None or height is None:
        raise ValueError("Dimensions JPEG introuvables.")
    return width, height, orientation


def _webp_metadata(payload: bytes) -> tuple[int, int, int]:
    if len(payload) < 30 or payload[:4] != b"RIFF" or payload[8:12] != b"WEBP":
        raise ValueError("Signature WebP invalide.")
    chunk = payload[12:16]
    if chunk == b"VP8X":
        width = 1 + int.from_bytes(payload[24:27], "little")
        height = 1 + int.from_bytes(payload[27:30], "little")
    elif chunk == b"VP8L" and len(payload) >= 25 and payload[20] == 0x2F:
        bits = int.from_bytes(payload[21:25], "little")
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
    elif chunk == b"VP8 " and len(payload) >= 30 and payload[23:26] == b"\x9d\x01\x2a":
        width = int.from_bytes(payload[26:28], "little") & 0x3FFF
        height = int.from_bytes(payload[28:30], "little") & 0x3FFF
    else:
        raise ValueError("Dimensions WebP introuvables ou codec non pris en charge.")
    return width, height, 1


def inspect_training_image(image_path: Path, private_root: Path) -> dict[str, Any]:
    path = _private_file(image_path, private_root)
    extension = path.suffix.casefold()
    if extension not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError("Format refusé; utiliser PNG, JPEG ou WebP.")
    payload = _read_bounded(path, MAX_IMAGE_BYTES)
    try:
        if payload.startswith(b"\x89PNG"):
            image_format, mime = "PNG", "image/png"
            width, height, orientation = _png_metadata(payload)
            expected = {".png"}
        elif payload.startswith(b"\xff\xd8"):
            image_format, mime = "JPEG", "image/jpeg"
            width, height, orientation = _jpeg_metadata(payload)
            expected = {".jpg", ".jpeg"}
        elif payload.startswith(b"RIFF"):
            image_format, mime = "WEBP", "image/webp"
            width, height, orientation = _webp_metadata(payload)
            expected = {".webp"}
        else:
            raise ValueError("Signature d'image inconnue.")
        if extension not in expected:
            raise ValueError("L'extension ne correspond pas à la signature de l'image.")
        pixels = width * height
        if width < 1 or height < 1 or width > MAX_DIMENSION or height > MAX_DIMENSION or pixels > MAX_IMAGE_PIXELS:
            raise ValueError("Dimensions ou nombre de pixels hors limites.")
        return {
            "format": image_format, "mime": mime, "byte_size": len(payload),
            "width": width, "height": height, "pixel_count": pixels,
            "orientation": orientation if orientation is not None else "unknown",
            "stored": False, "path_exposed": False, "content_hash_exposed": False,
        }
    finally:
        del payload


def _provenance(value: Any, default: str = "owner_annotated", *, trusted_visual: bool = False) -> str:
    """Normalise une provenance venant d'une annotation non fiable.

    Aucun backend local n'atteste actuellement ``visual_certain`` ou
    ``ocr_uncertain``. Une annotation propriétaire ne peut donc pas s'autoattribuer
    ces provenances. Un futur adaptateur devra écrire sa propre attestation par une
    voie interne distincte avant qu'elles puissent redevenir factuelles.
    """
    if value == "visual_certain" and not trusted_visual:
        return "owner_annotated"
    if value == "ocr_uncertain" and not trusted_visual:
        return "unknown"
    return value if value in _PROVENANCE else default


def _card(value: Any, *, trusted_visual: bool = False) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("Une carte annotée doit être un objet JSON.")
    name = value.get("name")
    return {
        "name": _bounded_text(name, "card.name") if name else None,
        "tcgdex_id": _bounded_text(value["tcgdex_id"], "card.tcgdex_id", maximum=100) if value.get("tcgdex_id") else None,
        "set_code": _bounded_text(value["set_code"], "card.set_code", maximum=32) if value.get("set_code") else None,
        "collector_number": _bounded_text(value["collector_number"], "card.collector_number", maximum=32) if value.get("collector_number") else None,
        "provenance": _provenance(value.get("provenance"), trusted_visual=trusted_visual),
        "confidence": value.get("confidence") if value.get("confidence") in {"certain", "uncertain", "unknown"} else "unknown",
    }


def _slot(value: Any, *, trusted_visual: bool = False) -> dict[str, Any]:
    if value is None:
        return {"visibility": "unknown", "card": None, "damage": None, "energies": [], "provenance": "unknown"}
    if not isinstance(value, dict):
        raise ValueError("Un emplacement Pokémon doit être un objet JSON.")
    visibility = value.get("visibility", "unknown")
    if visibility not in {"visible", "ambiguous", "unknown", "empty"}:
        raise ValueError("slot.visibility invalide.")
    damage = value.get("damage")
    if damage is not None and (isinstance(damage, bool) or not isinstance(damage, int) or damage < 0 or damage > 9999):
        raise ValueError("slot.damage invalide.")
    energies = []
    for item in value.get("energies", []):
        if not isinstance(item, dict):
            raise ValueError("Une énergie visible doit être un objet JSON.")
        count = item.get("count", 1)
        if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 99:
            raise ValueError("energy.count invalide.")
        energies.append({
            "type": _bounded_text(item.get("type", "unknown"), "energy.type", maximum=50),
            "count": count, "provenance": _provenance(item.get("provenance"), trusted_visual=trusted_visual),
        })
    return {
        "visibility": visibility, "card": _card(value.get("card"), trusted_visual=trusted_visual), "damage": damage,
        "energies": energies, "provenance": _provenance(value.get("provenance"), trusted_visual=trusted_visual),
    }


def _side(value: Any, *, opponent: bool, trusted_visual: bool = False) -> dict[str, Any]:
    value = value if isinstance(value, dict) else {}
    bench = value.get("bench", [])
    if not isinstance(bench, list) or len(bench) > 8:
        raise ValueError("side.bench doit être une liste bornée.")
    hand = value.get("hand") if isinstance(value.get("hand"), dict) else {}
    hand_visibility = hand.get("visibility", "hidden" if opponent else "unknown")
    if hand_visibility not in {"visible", "partial", "hidden", "unknown"}:
        raise ValueError("hand.visibility invalide.")
    count = hand.get("count")
    if count is not None and (isinstance(count, bool) or not isinstance(count, int) or not 0 <= count <= 99):
        raise ValueError("hand.count invalide.")
    hand_cards = hand.get("cards", [])
    if not isinstance(hand_cards, list) or len(hand_cards) > 60:
        raise ValueError("hand.cards doit être une liste bornée.")
    cards = [_card(item, trusted_visual=trusted_visual) for item in hand_cards]
    if hand_visibility in {"hidden", "unknown"}:
        cards = []
    discard = value.get("discard") if isinstance(value.get("discard"), dict) else {}
    discard_visibility = discard.get("visibility", "unknown")
    if discard_visibility not in {"visible", "partial", "hidden", "unknown"}:
        raise ValueError("discard.visibility invalide.")
    discard_cards = discard.get("cards", [])
    if not isinstance(discard_cards, list) or len(discard_cards) > 100:
        raise ValueError("discard.cards doit être une liste bornée.")
    prizes = value.get("prizes") if isinstance(value.get("prizes"), dict) else {}
    prize_count = prizes.get("apparent_count")
    if prize_count is not None and (isinstance(prize_count, bool) or not isinstance(prize_count, int) or not 0 <= prize_count <= 6):
        raise ValueError("prizes.apparent_count invalide.")
    normalized_discard_cards = [_card(item, trusted_visual=trusted_visual) for item in discard_cards]
    if discard_visibility in {"hidden", "unknown"}:
        normalized_discard_cards = []
    return {
        "active": _slot(value.get("active"), trusted_visual=trusted_visual),
        "bench": [_slot(item, trusted_visual=trusted_visual) for item in bench],
        "hand": {"visibility": hand_visibility, "count": count, "cards": cards,
                 "provenance": _provenance(hand.get("provenance"), trusted_visual=trusted_visual)},
        "discard": {"visibility": discard_visibility,
                    "cards": normalized_discard_cards,
                    "provenance": _provenance(discard.get("provenance"), trusted_visual=trusted_visual)},
        "prizes": {"apparent_count": prize_count, "contents": "UNKNOWN",
                   "provenance": _provenance(prizes.get("provenance"), trusted_visual=trusted_visual)},
    }


def _normalize_board_state(
    annotation: dict[str, Any], *, turn: int, trusted_visual: bool,
) -> dict[str, Any]:
    if not isinstance(annotation, dict):
        raise ValueError("L'annotation doit être un objet JSON.")
    declared_turn = annotation.get("turn", turn)
    if isinstance(declared_turn, bool) or not isinstance(declared_turn, int) or declared_turn < 1:
        raise ValueError("turn doit être un entier positif.")
    if declared_turn != turn:
        raise ValueError("Le tour de l'annotation contredit --turn.")
    phase = annotation.get("phase", "unknown")
    if phase not in {"setup", "main", "attack", "checkup", "unknown"}:
        raise ValueError("phase invalide.")
    owner = annotation.get("turn_owner", "unknown")
    if owner not in {"self", "opponent", "unknown"}:
        raise ValueError("turn_owner invalide.")
    sides = annotation.get("sides", {})
    if not isinstance(sides, dict):
        raise ValueError("sides doit être un objet JSON.")
    raw_actions = annotation.get("available_actions", [])
    if not isinstance(raw_actions, list) or len(raw_actions) > 50:
        raise ValueError("available_actions doit être une liste bornée.")
    actions = []
    for item in raw_actions:
        if not isinstance(item, dict):
            raise ValueError("available_actions doit contenir des objets.")
        actions.append({
            "kind": _bounded_text(item.get("kind", "other"), "action.kind", maximum=50),
            "description": _bounded_text(item.get("description", "Action annotée"), "action.description"),
            "attack_name": _bounded_text(item["attack_name"], "action.attack_name") if item.get("attack_name") else None,
            "provenance": _provenance(item.get("provenance"), trusted_visual=trusted_visual),
            "contradicted": bool(item.get("contradicted", False)),
        })
    raw_unknowns = annotation.get("unknown_fields", [])
    raw_errors = annotation.get("recognition_errors", [])
    if not isinstance(raw_unknowns, list) or not isinstance(raw_errors, list):
        raise ValueError("unknown_fields et recognition_errors doivent être des listes.")
    unknowns = [_bounded_text(item, "unknown_fields[]") for item in raw_unknowns[:100]]
    errors = [_bounded_text(item, "recognition_errors[]") for item in raw_errors[:100]]
    return {
        "schema_version": BOARD_SCHEMA_VERSION, "turn": turn, "phase": phase, "turn_owner": owner,
        "sides": {
            "self": _side(sides.get("self"), opponent=False, trusted_visual=trusted_visual),
            "opponent": _side(sides.get("opponent"), opponent=True, trusted_visual=trusted_visual),
        },
        "available_actions": actions, "unknown_fields": unknowns,
        "recognition_errors": errors,
        "hidden_information_policy": {"opponent_hand": "UNKNOWN", "prize_contents": "UNKNOWN", "deck_order": "UNKNOWN"},
    }


def normalize_board_state(annotation: dict[str, Any], *, turn: int) -> dict[str, Any]:
    """Normalize owner-supplied content; it can never mint visual provenance."""
    return _normalize_board_state(annotation, turn=turn, trusted_visual=False)


def load_annotation(path: Path, private_root: Path, *, turn: int) -> dict[str, Any]:
    source = _private_file(path, private_root)
    payload = _read_bounded(source, MAX_ANNOTATION_BYTES)
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Annotation JSON UTF-8 invalide.") from exc
    finally:
        del payload
    return normalize_board_state(data, turn=turn)


def start_session(
    db_path: Path, *, format: str, platform: str, as_of: str,
    apply: bool = False, confirm_owner: bool = False,
) -> dict[str, Any]:
    if format not in {"standard", "expanded"} or platform != "live":
        raise ValueError("Le coach accepte standard/expanded sur la plateforme live seulement.")
    as_of = _strict_date(as_of)
    result = {
        "mode": "applied" if apply else "dry_run", "read_only": not apply, "network_used": False,
        "session_id": None, "status": "PREVIEW", "context": {"format": format, "platform": platform, "as_of": as_of},
        "assistance_scope": "authorized_training_only", "images_stored": 0,
    }
    if not apply:
        return result
    if not confirm_owner:
        raise ValueError("--apply exige --confirm-owner pour ouvrir une mémoire de séance.")
    session_id = "train-" + secrets.token_hex(12)
    connection = connect_writable(db_path)
    try:
        initialize_schema(connection)
        connection.execute(
            """INSERT INTO training_sessions
               (session_id,created_at,closed_at,status,mode,format,platform,context_date,image_storage,assistance_scope)
               VALUES(?,?,NULL,'active','training',?, ?,?,'none','authorized_training_only')""",
            (session_id, utc_now(), format, platform, as_of),
        )
        connection.commit()
    finally:
        connection.close()
    return {**result, "session_id": session_id, "status": "ACTIVE"}


def _state_digest(state: dict[str, Any]) -> tuple[str, str]:
    serialized = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return serialized, hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def save_observation(
    db_path: Path, session_id: str, *, turn: int, state: dict[str, Any],
    apply: bool = False, confirm_owner: bool = False, revision_of_id: int | None = None,
    _trusted_visual: bool = False,
) -> dict[str, Any]:
    normalized = _normalize_board_state(state, turn=turn, trusted_visual=_trusted_visual)
    serialized, digest = _state_digest(normalized)
    confidence = "unknown" if normalized["unknown_fields"] else (
        "uncertain" if normalized["recognition_errors"] else "certain"
    )
    result = {
        "mode": "applied" if apply else "dry_run", "read_only": not apply, "network_used": False,
        "session_id": session_id, "turn": turn, "observation_id": None,
        "status": "PREVIEW", "state": normalized, "images_stored": 0,
    }
    if not apply:
        return result
    if not confirm_owner:
        raise ValueError("--apply exige --confirm-owner pour mémoriser du texte de séance.")
    connection = connect_writable(db_path)
    try:
        initialize_schema(connection)
        connection.execute("BEGIN IMMEDIATE")
        session = connection.execute("SELECT status FROM training_sessions WHERE session_id=?", (session_id,)).fetchone()
        if session is None or session["status"] != "active":
            raise ValueError("Séance active introuvable.")
        current = connection.execute(
            "SELECT id FROM training_observations WHERE session_id=? AND turn_number=? AND status='active'",
            (session_id, turn),
        ).fetchone()
        if revision_of_id is not None and (current is None or int(current["id"]) != revision_of_id):
            raise ValueError("La correction doit viser l'observation active de ce tour.")
        duplicate = connection.execute(
            """SELECT id FROM training_observations
               WHERE session_id=? AND turn_number=? AND state_sha256=? AND status='active'""",
            (session_id, turn, digest),
        ).fetchone()
        if duplicate:
            connection.rollback()
            return {**result, "observation_id": int(duplicate["id"]), "status": "DUPLICATE", "duplicate": True}
        latest_turn = int(connection.execute(
            "SELECT COALESCE(MAX(turn_number),0) FROM training_observations WHERE session_id=?",
            (session_id,),
        ).fetchone()[0])
        if revision_of_id is None and latest_turn and turn != latest_turn + 1:
            raise ValueError("TURN_SEQUENCE_INVALID: le prochain tour doit suivre la dernière observation.")
        if revision_of_id is None and current is not None:
            raise ValueError("Ce tour a déjà une observation active; utiliser match correct.")
        if current is not None:
            connection.execute("UPDATE training_observations SET status='superseded' WHERE id=?", (current["id"],))
        cursor = connection.execute(
            """INSERT INTO training_observations
               (session_id,turn_number,recorded_at,source_kind,confidence,state_json,state_sha256,status,revision_of_id)
               VALUES(?,?,?,?,?,?,?,'active',?)""",
            (session_id, turn, utc_now(), "owner_correction" if revision_of_id else ("local_vision" if _trusted_visual else "owner_annotation"),
             confidence, serialized, digest, revision_of_id),
        )
        connection.commit()
        return {**result, "observation_id": int(cursor.lastrowid), "status": "SAVED", "duplicate": False}
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def observe_training(
    db_path: Path, private_root: Path, *, turn: int, image_path: Path | None = None,
    annotation_path: Path | None = None, annotation: dict[str, Any] | None = None,
    session_id: str | None = None, mode: str = "training",
    frame_scope: str = "unknown",
    calibration_path: Path | None = None,
    ocr_policy: Path | None = None, execute_reviewed_ocr: bool = False,
    apply: bool = False, confirm_owner: bool = False,
) -> dict[str, Any]:
    if mode != "training":
        raise ValueError("Seul --mode training est permis.")
    if frame_scope not in {"full_board", "crop", "unknown"}:
        raise ValueError("frame_scope invalide.")
    if image_path is None and annotation_path is None and annotation is None:
        raise ValueError("Fournir explicitement --image ou --annotation.")
    image = inspect_training_image(image_path, private_root) if image_path else None
    if annotation_path is not None and annotation is not None:
        raise ValueError("Choisir un fichier d'annotation ou un objet, pas les deux.")
    state = load_annotation(annotation_path, private_root, turn=turn) if annotation_path else (
        normalize_board_state(annotation, turn=turn) if annotation is not None else None
    )
    vision_generated = False
    if calibration_path is not None:
        if image_path is None or state is not None:
            raise ValueError("--calibration exige une image sans annotation concurrente.")
        profile = json.loads(_read_bounded(_private_file(calibration_path, private_root), MAX_CALIBRATION_BYTES).decode("utf-8"))
        if isinstance(profile, dict) and profile.get("adapter") == "pokemind_tesseract_roi_v1":
            from pokemind.local_ocr import recognize_local_text

            context_date = session_memory(db_path, session_id).get("context", {}).get("as_of") if session_id else None
            state, backend = recognize_local_text(
                db_path, image_path, calibration_path, private_root, turn=turn, as_of=context_date,
                ocr_policy=ocr_policy, execute_reviewed_ocr=execute_reviewed_ocr,
            )
        else:
            state, backend = _calibrated_marker_state(
                image_path, calibration_path, private_root, turn=turn,
            )
        vision_generated = state is not None
    else:
        backend = {
            "name": "none",
            **vision_backend_status(),
            "reason": "Aucun adaptateur local calibré n'est configuré; aucune extraction n'est simulée.",
        }
    base = {
        "mode": "applied" if apply else "dry_run", "training_only": True, "network_used": False,
        "image": image, "image_lifecycle": {
            "consumed_for_request_only": image is not None, "copied": False, "stored_in_sqlite": False,
            "deleted_by_pokemind": False,
            "owner_cleanup": "Le fichier source reste au propriétaire; le retirer manuellement lorsqu'il n'est plus requis.",
        },
        "vision_backend": backend, "frame_scope": frame_scope, "state": state,
        "status": ("VISION_OBSERVATION_ACCEPTED" if vision_generated else "MANUAL_ANNOTATION_ACCEPTED") if state is not None else "NEEDS_MANUAL_ANNOTATION",
    }
    if state is None:
        if apply:
            raise ValueError("Aucune observation ne peut être mémorisée sans annotation manuelle validée.")
        return base
    if not apply:
        return base
    if not session_id:
        raise ValueError("--session est requis pour mémoriser une observation.")
    saved = save_observation(
        db_path, session_id, turn=turn, state=state, apply=True, confirm_owner=confirm_owner,
        _trusted_visual=vision_generated,
    )
    return {**base, "status": saved["status"], "session_id": session_id,
            "observation_id": saved["observation_id"], "duplicate": saved.get("duplicate", False)}


def session_memory(db_path: Path, session_id: str) -> dict[str, Any]:
    base = {"session_id": session_id, "read_only": True, "network_used": False, "images_stored": 0}
    if not db_path.is_file():
        return {**base, "status": "NOT_FOUND", "observations": []}
    connection = connect_readonly(db_path)
    try:
        if "training_sessions" not in _tables(connection):
            return {**base, "status": "SCHEMA_MIGRATION_REQUIRED", "observations": []}
        session = connection.execute("SELECT * FROM training_sessions WHERE session_id=?", (session_id,)).fetchone()
        if session is None:
            return {**base, "status": "NOT_FOUND", "observations": []}
        rows = connection.execute(
            """SELECT id,turn_number,recorded_at,source_kind,confidence,state_json,status,revision_of_id
               FROM training_observations WHERE session_id=? ORDER BY turn_number,id""",
            (session_id,),
        ).fetchall()
        observations = [
            {"observation_id": int(row["id"]), "turn": int(row["turn_number"]),
             "recorded_at": row["recorded_at"], "source_kind": row["source_kind"],
             "confidence": row["confidence"], "status": row["status"],
             "revision_of_id": row["revision_of_id"], "state": json.loads(row["state_json"])}
            for row in rows
        ]
        from pokemind.vision_evidence import visual_review_summary
        review = visual_review_summary(connection, session_id)
        return {**base, "status": str(session["status"]).upper(),
                "context": {"format": session["format"], "platform": session["platform"], "as_of": session["context_date"]},
                "created_at": session["created_at"], "closed_at": session["closed_at"],
                "observations": observations, "visual_review": review}
    finally:
        connection.close()


def correct_observation(
    db_path: Path, private_root: Path, session_id: str, observation_id: int, annotation_path: Path,
    *, apply: bool = False, confirm_owner: bool = False,
) -> dict[str, Any]:
    memory = session_memory(db_path, session_id)
    target = next((row for row in memory["observations"] if row["observation_id"] == observation_id), None)
    if target is None or target["status"] != "active":
        raise ValueError("Observation active introuvable pour cette séance.")
    state = load_annotation(annotation_path, private_root, turn=target["turn"])
    return save_observation(
        db_path, session_id, turn=target["turn"], state=state, apply=apply,
        confirm_owner=confirm_owner, revision_of_id=observation_id,
    )


def revoke_correction(
    db_path: Path, session_id: str, observation_id: int, *,
    apply: bool = False, confirm_owner: bool = False,
) -> dict[str, Any]:
    result = {"mode": "applied" if apply else "dry_run", "read_only": not apply,
              "session_id": session_id, "observation_id": observation_id, "network_used": False}
    if not apply:
        return {**result, "status": "PREVIEW"}
    if not confirm_owner:
        raise ValueError("--apply exige --confirm-owner pour révoquer une correction.")
    connection = connect_writable(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT * FROM training_observations WHERE id=? AND session_id=?",
            (observation_id, session_id),
        ).fetchone()
        if row is None or row["revision_of_id"] is None or row["status"] != "active":
            raise ValueError("Correction active et révisable introuvable.")
        session = connection.execute("SELECT status FROM training_sessions WHERE session_id=?", (session_id,)).fetchone()
        if session is None or session["status"] != "active":
            raise ValueError("La séance doit être active pour révoquer une correction.")
        connection.execute("UPDATE training_observations SET status='revoked' WHERE id=?", (observation_id,))
        connection.execute("UPDATE training_observations SET status='active' WHERE id=?", (row["revision_of_id"],))
        connection.commit()
        return {**result, "status": "REVOKED", "restored_observation_id": int(row["revision_of_id"])}
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def close_session(
    db_path: Path, session_id: str, *, apply: bool = False, confirm_owner: bool = False,
) -> dict[str, Any]:
    result = {"mode": "applied" if apply else "dry_run", "read_only": not apply,
              "session_id": session_id, "network_used": False, "ephemeral_images_removed": 0,
              "images_stored": 0}
    if not apply:
        return {**result, "status": "PREVIEW"}
    if not confirm_owner:
        raise ValueError("--apply exige --confirm-owner pour clore une séance.")
    connection = connect_writable(db_path)
    try:
        cursor = connection.execute(
            "UPDATE training_sessions SET status='closed',closed_at=? WHERE session_id=? AND status='active'",
            (utc_now(), session_id),
        )
        if cursor.rowcount != 1:
            raise ValueError("Séance active introuvable.")
        connection.commit()
        return {**result, "status": "CLOSED"}
    finally:
        connection.close()


def _catalog_attacks(connection: sqlite3.Connection, tcgdex_id: str) -> list[dict[str, Any]]:
    if "catalog_translations" not in _tables(connection):
        return []
    row = connection.execute(
        """SELECT attacks_json,source_url,retrieved_at FROM catalog_translations
           WHERE printing_id=? AND status='present' AND attacks_json IS NOT NULL
           ORDER BY CASE language WHEN 'fr' THEN 0 ELSE 1 END LIMIT 1""",
        (tcgdex_id,),
    ).fetchone()
    if row is None:
        return []
    try:
        attacks = json.loads(row["attacks_json"])
    except (TypeError, json.JSONDecodeError):
        return []
    return [dict(item, source_url=row["source_url"], retrieved_at=row["retrieved_at"])
            for item in attacks if isinstance(item, dict)]


def _energy_compatibility(cost: list[Any], energies: list[dict[str, Any]]) -> tuple[str, str, dict[str, int]]:
    required: dict[str, int] = {}
    for raw in cost:
        if not isinstance(raw, str) or raw.casefold() not in _BASIC_ENERGY_TYPES:
            return "unknown", "ATTACK_COST_TYPE_UNKNOWN", required
        energy_type = _BASIC_ENERGY_TYPES[raw.casefold()]
        required[energy_type] = required.get(energy_type, 0) + 1
    available: dict[str, int] = {}
    unknown_resources = 0
    for item in energies:
        raw = item.get("type")
        if not isinstance(raw, str) or raw.casefold() not in _BASIC_ENERGY_TYPES:
            unknown_resources += int(item.get("count", 0))
            continue
        energy_type = _BASIC_ENERGY_TYPES[raw.casefold()]
        available[energy_type] = available.get(energy_type, 0) + int(item.get("count", 0))
    remaining = dict(available)
    for energy_type, count in required.items():
        if energy_type == "Colorless":
            continue
        if remaining.get(energy_type, 0) < count:
            return (
                ("unknown", "SPECIAL_ENERGY_OR_MODIFIER_UNVERIFIED")
                if unknown_resources
                else ("not_met", "ENERGY_TYPE_NOT_VERIFIED")
            ) + (required,)
        remaining[energy_type] -= count
    colorless = required.get("Colorless", 0)
    known_remaining = sum(remaining.values())
    if known_remaining >= colorless:
        return "met", "VISIBLE_TYPED_ENERGY_MATCH", required
    if known_remaining + unknown_resources >= colorless:
        return "unknown", "SPECIAL_ENERGY_OR_MODIFIER_UNVERIFIED", required
    return "not_met", "VISIBLE_ENERGY_INSUFFICIENT", required


def advise_turn(
    db_path: Path, session_id: str, *, turn: int, format: str, platform: str, as_of: str,
) -> dict[str, Any]:
    as_of = _strict_date(as_of)
    memory = session_memory(db_path, session_id)
    if memory["status"] not in {"ACTIVE", "CLOSED"}:
        raise ValueError("Séance introuvable.")
    candidates = [row for row in memory["observations"] if row["turn"] == turn and row["status"] == "active"]
    if len(candidates) != 1:
        raise ValueError("Une observation active exacte est requise pour ce tour.")
    requested_context = {"format": format, "platform": platform, "as_of": as_of}
    session_context = memory.get("context", {})
    conflicts = [
        field for field in ("format", "platform", "as_of")
        if requested_context[field] != session_context.get(field)
    ]
    if conflicts:
        return {
            "session_id": session_id, "turn": turn,
            "context": {**requested_context, "mode": "training"},
            "session_context": session_context,
            "context_conflicts": conflicts,
            "read_only": True, "network_used": False, "automated_game_action": False,
            "status": "CONTEXT_CONFLICT", "recommended_sequence": [],
            "fallback": None, "options": [], "verified_possible_count": 0,
            "conditional_count": 0, "not_supported_count": 0,
            "hidden_information": candidates[0]["state"]["hidden_information_policy"],
            "next_annotation_or_capture": ["Utiliser le format, la plateforme et la date de la séance ou ouvrir une nouvelle séance cohérente."],
            "capture_timing": "Aucune capture supplémentaire ne résout un conflit de contexte.",
            "limits": ["Aucune citation de carte ou règle n'est fournie sous un contexte temporel contradictoire."],
        }
    state = candidates[0]["state"]
    options: list[dict[str, Any]] = []
    active = state["sides"]["self"]["active"]
    card = active.get("card") or {}
    card_is_fact = (
        active.get("visibility") == "visible"
        and card.get("provenance") in _FACT_PROVENANCE
        and active.get("provenance") in _FACT_PROVENANCE
    )
    energy_is_fact = all(item.get("provenance") in _FACT_PROVENANCE for item in active.get("energies", []))
    visible_energy = sum(int(item["count"]) for item in active.get("energies", [])) if energy_is_fact else None
    attacks: list[dict[str, Any]] = []
    if card_is_fact and card.get("tcgdex_id") and db_path.is_file():
        connection = connect_readonly(db_path)
        try:
            attacks = _catalog_attacks(connection, card["tcgdex_id"])
        finally:
            connection.close()
    for attack in attacks:
        cost = attack.get("cost") if isinstance(attack.get("cost"), list) else []
        source_complete = bool(attack.get("source_url") and attack.get("retrieved_at"))
        source_date = str(attack.get("retrieved_at") or "")[:10]
        source_available = source_complete and source_date <= as_of
        compatibility = (
            _energy_compatibility(cost, active.get("energies", []))
            if energy_is_fact else ("unknown", "ENERGY_PROVENANCE_NOT_ATTESTED", {})
        )
        context_allows = state["turn_owner"] == "self" and state["phase"] in {"main", "attack"}
        option_status = "conditional" if compatibility[0] == "met" and context_allows and source_available else "not_supported"
        if not source_complete:
            reason_code = "PUBLIC_SOURCE_INCOMPLETE"
        elif not source_available:
            reason_code = "PUBLIC_SOURCE_NOT_AVAILABLE_AS_OF"
        elif not context_allows:
            reason_code = "TURN_OR_PHASE_NOT_SUPPORTED"
        elif compatibility[0] == "met":
            reason_code = "VISIBLE_TYPED_PREREQUISITES_MET_RULES_INCOMPLETE"
        else:
            reason_code = compatibility[1]
        options.append({
            "status": option_status,
            "action": f"Attaquer avec {attack.get('name', 'attaque identifiée')}",
            "order": len(options) + 1,
            "conditions": [
                f"Coût public typé: {compatibility[2] or 'unknown'}; énergie(s) visible(s): {visible_energy if visible_energy is not None else 'unknown'}.",
                "Confirmer les restrictions de tour, effets actifs et coûts modifiés; la légalité complète n'est pas prouvée.",
            ],
            "advantage": "Option tirée du texte public de l'impression exacte.",
            "disadvantage": "Les effets temporaires et informations cachées peuvent changer la décision.",
            "evidence": {"tcgdex_id": card["tcgdex_id"], "source_url": attack.get("source_url"),
                         "retrieved_at": attack.get("retrieved_at"), "as_of": as_of},
            "reason_code": reason_code,
        })
    for annotated in state["available_actions"]:
        options.append({
            "status": "not_supported" if annotated["contradicted"] else "conditional",
            "action": annotated["description"], "order": len(options) + 1,
            "conditions": ["Action annotée par le propriétaire; légalité officielle complète non démontrée."],
            "advantage": "Reflète une possibilité signalée dans l'état courant.",
            "disadvantage": "Une annotation n'est pas une preuve normative.",
            "evidence": {"provenance": annotated["provenance"], "as_of": as_of},
            "reason_code": "ANNOTATION_CONTRADICTED" if annotated["contradicted"] else "OWNER_ANNOTATED_CONDITION",
        })
    if not options:
        options.append({
            "status": "not_supported", "action": "Choisir une action de jeu précise", "order": 1,
            "conditions": ["Identifier l'Actif, ses énergies visibles, la phase et les options pertinentes."],
            "advantage": "Évite d'inventer une carte, un coût ou un effet.",
            "disadvantage": "Aucun coup précis ne peut être recommandé maintenant.",
            "evidence": {"observation_id": candidates[0]["observation_id"], "as_of": as_of},
            "reason_code": "INSUFFICIENT_VISIBLE_EVIDENCE",
        })
    usable = [option for option in options if option["status"] == "conditional"]
    next_needed = []
    if not card_is_fact:
        next_needed.append("Annoter l'identité exacte de votre Pokémon Actif ou fournir un crop lisible.")
    if visible_energy is None:
        next_needed.append("Confirmer les énergies visibles attachées à l'Actif.")
    next_needed.extend(state["unknown_fields"][:3])
    return {
        "session_id": session_id, "turn": turn,
        "context": {"format": format, "platform": platform, "as_of": as_of, "mode": "training"},
        "read_only": True, "network_used": False, "automated_game_action": False,
        "status": "CONDITIONAL_ADVICE" if usable else "INSUFFICIENT_EVIDENCE",
        "recommended_sequence": usable[:3],
        "fallback": next((option for option in options if option["status"] == "not_supported"), None),
        "options": options,
        "verified_possible_count": sum(option["status"] == "verified_possible" for option in options),
        "conditional_count": sum(option["status"] == "conditional" for option in options),
        "not_supported_count": sum(option["status"] == "not_supported" for option in options),
        "hidden_information": state["hidden_information_policy"],
        "visual_review": memory.get("visual_review", {}),
        "next_annotation_or_capture": list(dict.fromkeys(next_needed))[:4],
        "capture_timing": "Seulement après pioche/recherche/effet déterminant ou changement majeur.",
        "limits": [
            "Conseil d'entraînement seulement; ne pas utiliser si l'assistance est interdite.",
            "Aucun meilleur coup absolu ni taux de victoire n'est calculé.",
            "Aucune action n'est envoyée au client Pokémon TCG Live.",
        ],
    }
