"""Préparation locale et sûre de textes de deck à copier dans TCG Live."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from pokemind.database import utc_now
from pokemind.decks import (
    MAX_DECK_BYTES,
    DeckCard,
    _COLLECTOR_RE,
    _SET_CODE_RE,
    decode_deck_bytes,
    parse_deck_export,
    show_deck,
)


PROPOSAL_SCHEMA_VERSION = 1
REPORT_SCHEMA_VERSION = 1
FORMAT_VALIDATION = "OUTPUT_FORMAT_NOT_FIELD_VALIDATED"
MAX_PROPOSAL_BYTES = 500_000
_CARD_TYPES = ("pokemon", "trainer", "energy")
_SECTION_LABELS = {"pokemon": "Pokémon", "trainer": "Trainer", "energy": "Energy"}
_SAFE_NAME_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,200}$")


@dataclass(frozen=True, slots=True)
class PreparedDeck:
    text_path: Path
    report_path: Path
    text: str
    report: dict[str, Any]


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} doit être un objet JSON.")
    return value


def _require_keys(value: dict[str, Any], *, required: set[str], allowed: set[str], label: str) -> None:
    missing = sorted(required - set(value))
    extra = sorted(set(value) - allowed)
    if missing:
        raise ValueError(f"{label}: champs requis absents: {', '.join(missing)}.")
    if extra:
        raise ValueError(f"{label}: champs inconnus: {', '.join(extra)}.")


def _string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"{label} doit être une liste de chaînes non vides.")
    return [item.strip() for item in value]


def _safe_name(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} doit être une chaîne.")
    normalized = unicodedata.normalize("NFC", value).strip()
    if not _SAFE_NAME_RE.fullmatch(normalized):
        raise ValueError(f"{label} est vide, trop long ou contient un caractère de contrôle.")
    return normalized


def _slug(value: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.casefold()).strip("-")
    if not slug:
        raise ValueError("Le nom du deck ne permet pas de créer un nom de fichier sûr.")
    return slug[:64].rstrip("-")


def _card(
    *, ordinal: int, card_type: Any, quantity: Any, name: Any,
    set_code: Any, collector_number: Any,
) -> DeckCard:
    if card_type not in _CARD_TYPES:
        raise ValueError(f"Carte {ordinal}: type invalide; pokemon, trainer ou energy attendu.")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= 60:
        raise ValueError(f"Carte {ordinal}: quantité entière entre 1 et 60 attendue.")
    safe_name = _safe_name(name, f"Carte {ordinal}: nom")
    if (set_code is None) != (collector_number is None):
        raise ValueError(f"Carte {ordinal}: set_code et collector_number doivent être fournis ensemble.")
    safe_set: str | None = None
    safe_number: str | None = None
    if set_code is not None:
        safe_set = _safe_name(set_code, f"Carte {ordinal}: set_code")
        safe_number = _safe_name(collector_number, f"Carte {ordinal}: collector_number")
        if not _SET_CODE_RE.fullmatch(safe_set):
            raise ValueError(f"Carte {ordinal}: set_code invalide.")
        if not _COLLECTOR_RE.fullmatch(safe_number):
            raise ValueError(f"Carte {ordinal}: collector_number invalide.")
    line = f"{quantity} {safe_name}"
    if safe_set and safe_number:
        line += f" {safe_set} {safe_number}"
    return DeckCard(
        ordinal=ordinal,
        source_line=ordinal,
        card_type=card_type,
        quantity=quantity,
        name=safe_name,
        set_code=safe_set,
        collector_number=safe_number,
        normalized_line=line,
    )


def _validate_cards(cards: Iterable[DeckCard]) -> tuple[DeckCard, ...]:
    validated = tuple(
        _card(
            ordinal=index,
            card_type=card.card_type,
            quantity=card.quantity,
            name=card.name,
            set_code=card.set_code,
            collector_number=card.collector_number,
        )
        for index, card in enumerate(cards, start=1)
    )
    if not validated:
        raise ValueError("Le deck ne contient aucune entrée.")
    total = sum(card.quantity for card in validated)
    if total != 60:
        raise ValueError(f"Un deck préparé doit contenir exactement 60 cartes; total reçu: {total}.")
    identities: set[tuple[str, str, str | None, str | None]] = set()
    for card in validated:
        identity = (card.card_type, card.name, card.set_code, card.collector_number)
        if identity in identities:
            raise ValueError(f"Entrée de carte en double: {card.name}; regrouper sa quantité.")
        identities.add(identity)
    return validated


def serialize_deck(cards: Iterable[DeckCard]) -> str:
    """Sérialise 60 cartes; les en-têtes comptent les entrées distinctes."""
    validated = _validate_cards(cards)
    lines: list[str] = []
    for section in _CARD_TYPES:
        section_cards = [card for card in validated if card.card_type == section]
        if not section_cards:
            raise ValueError(f"La section {section} est vide.")
        lines.append(f"{_SECTION_LABELS[section]}: {len(section_cards)}")
        lines.extend(card.normalized_line for card in section_cards)
        lines.append("")
    lines.append("Total Cards: 60")
    text = "\n".join(lines) + "\n"
    reparsed = parse_deck_export(text)
    if reparsed.total_cards != 60 or reparsed.coverage["section_header_count_mode"] not in {"entries", "ambiguous"}:
        raise ValueError("Échec du contrôle interne de sérialisation du deck.")
    return text


def load_proposal(path: Path) -> tuple[str, tuple[DeckCard, ...], dict[str, Any]]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Proposition absente: {resolved}")
    if resolved.stat().st_size > MAX_PROPOSAL_BYTES:
        raise ValueError(f"Proposition trop volumineuse (maximum {MAX_PROPOSAL_BYTES} octets).")
    try:
        payload = json.loads(resolved.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("La proposition doit être un document JSON UTF-8 valide.") from exc
    proposal = _require_object(payload, "La proposition")
    _require_keys(
        proposal,
        required={"schema_version", "name", "source", "cards"},
        allowed={"schema_version", "name", "source", "verification_tags", "cards"},
        label="Proposition",
    )
    if proposal["schema_version"] != PROPOSAL_SCHEMA_VERSION:
        raise ValueError(f"schema_version doit valoir {PROPOSAL_SCHEMA_VERSION}.")
    name = _safe_name(proposal["name"], "name")
    source = _require_object(proposal["source"], "source")
    _require_keys(source, required={"kind"}, allowed={"kind", "reference"}, label="source")
    if source["kind"] != "agent_proposal":
        raise ValueError("source.kind doit valoir agent_proposal.")
    if "reference" in source:
        source["reference"] = _safe_name(source["reference"], "source.reference")
    top_tags = _string_list(proposal.get("verification_tags", []), "verification_tags")
    rows = proposal["cards"]
    if not isinstance(rows, list):
        raise ValueError("cards doit être une liste JSON.")
    cards: list[DeckCard] = []
    card_metadata: list[dict[str, Any]] = []
    for index, raw in enumerate(rows, start=1):
        item = _require_object(raw, f"Carte {index}")
        _require_keys(
            item,
            required={"type", "quantity", "name", "provenance", "verification_tags"},
            allowed={
                "type", "quantity", "name", "set_code", "collector_number",
                "provenance", "verification_tags",
            },
            label=f"Carte {index}",
        )
        provenance = _safe_name(item["provenance"], f"Carte {index}: provenance")
        tags = _string_list(item["verification_tags"], f"Carte {index}: verification_tags")
        cards.append(
            _card(
                ordinal=index,
                card_type=item["type"],
                quantity=item["quantity"],
                name=item["name"],
                set_code=item.get("set_code"),
                collector_number=item.get("collector_number"),
            )
        )
        card_metadata.append({"provenance": provenance, "verification_tags": tags})
    validated = _validate_cards(cards)
    metadata = {
        "kind": "agent_proposal",
        "proposal_path": str(resolved),
        "source": source,
        "verification_tags": top_tags,
        "cards": card_metadata,
    }
    return name, validated, metadata


def _cards_from_database(db_path: Path, deck_id: str) -> tuple[str, tuple[DeckCard, ...], dict[str, Any]]:
    shown = show_deck(db_path, deck_id)
    if not shown["exact_confirmed"]:
        raise ValueError(f"Le deck {deck_id} n'a aucune version exacte confirmée de 60 cartes.")
    cards = tuple(
        _card(
            ordinal=index,
            card_type=row["card_type"],
            quantity=row["quantity"],
            name=row["card_name"],
            set_code=row["set_code"],
            collector_number=row["collector_number"],
        )
        for index, row in enumerate(shown["cards"], start=1)
    )
    return deck_id, _validate_cards(cards), {
        "kind": "confirmed_deck_version",
        "deck_id": deck_id,
        "version": shown["version"],
        "imported_at": shown["imported_at"],
    }


def _atomic_write_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise FileExistsError(f"Sortie déjà existante; aucun fichier écrasé: {path}") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _prepare(
    *, name: str, cards: tuple[DeckCard, ...], source: dict[str, Any],
    private_decks_root: Path, suffix: str,
) -> PreparedDeck:
    text = serialize_deck(cards)
    proposal_metadata = source.get("cards") if source.get("kind") == "agent_proposal" else None
    missing_printings = [
        index
        for index, card in enumerate(cards, start=1)
        if not card.set_code
        or (
            proposal_metadata is not None
            and "printing_verified" not in proposal_metadata[index - 1]["verification_tags"]
        )
    ]
    ready = not missing_printings
    directory = private_decks_root.resolve() / ("import_ready" if ready else "drafts")
    safe_stem = f"{_slug(name)}_{suffix}"
    text_path = directory / f"{safe_stem}.txt"
    report_path = directory / f"{safe_stem}.json"
    if text_path.exists() or report_path.exists():
        raise FileExistsError(f"Sortie déjà existante; aucun fichier écrasé: {safe_stem}")
    created_at = utc_now()
    warnings = [
        "La légalité Standard, la disponibilité dans TCG Live et la possession ne sont pas vérifiées.",
        "Le coût et la possibilité de fabrication doivent être vérifiés dans TCG Live par l'utilisateur.",
        "Le format de sortie n'a pas encore été validé par un aller-retour dans le client réel.",
    ]
    if missing_printings:
        warnings.insert(
            0,
            "Des identités set+numéro manquent ou ne sont pas étiquetées printing_verified; "
            "ce fichier demeure un brouillon hors import_ready.",
        )
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": "READY_TO_TRY_UNVERIFIED_FORMAT" if ready else "DRAFT_PRINTINGS_UNRESOLVED",
        "created_at": created_at,
        "format_validation": FORMAT_VALIDATION,
        "source": source,
        "total_cards": 60,
        "sections": {
            section: sum(card.quantity for card in cards if card.card_type == section)
            for section in _CARD_TYPES
        },
        "printing_codes": {
            "entries_total": len(cards),
            "entries_resolved": len(cards) - len(missing_printings),
            "unresolved_entry_ordinals": missing_printings,
        },
        "cards": [
            {
                "ordinal": index,
                "name": card.name,
                "set_code": card.set_code,
                "collector_number": card.collector_number,
                "possession": "unknown",
                "availability": "not_verified",
            }
            for index, card in enumerate(cards, start=1)
        ],
        "warnings": warnings,
    }
    report_bytes = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    created: list[Path] = []
    try:
        _atomic_write_new(text_path, text.encode("utf-8"))
        created.append(text_path)
        _atomic_write_new(report_path, report_bytes)
        created.append(report_path)
    except Exception:
        for created_path in created:
            created_path.unlink(missing_ok=True)
        raise
    return PreparedDeck(text_path, report_path, text, report)


def export_confirmed_deck(db_path: Path, deck_id: str, private_decks_root: Path) -> PreparedDeck:
    name, cards, source = _cards_from_database(db_path, deck_id)
    return _prepare(
        name=name,
        cards=cards,
        source=source,
        private_decks_root=private_decks_root,
        suffix=f"v{source['version']}",
    )


def prepare_proposal(path: Path, private_decks_root: Path) -> PreparedDeck:
    name, cards, source = load_proposal(path)
    timestamp = utc_now().replace("-", "").replace(":", "")
    return _prepare(
        name=name,
        cards=cards,
        source=source,
        private_decks_root=private_decks_root,
        suffix=timestamp,
    )


def copy_text_to_clipboard(text: str) -> None:
    if sys.platform != "win32":
        raise OSError("Presse-papiers disponible seulement sous Windows; ouvrir le .txt puis Ctrl+A, Ctrl+C.")
    try:
        completed = subprocess.run(
            [
                "powershell", "-NoProfile", "-NonInteractive", "-Command",
                "$text = [Console]::In.ReadToEnd(); Set-Clipboard -Value $text",
            ],
            input=text,
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        raise OSError("Écriture du presse-papiers impossible; ouvrir le .txt puis Ctrl+A, Ctrl+C.") from exc
    if completed.returncode != 0:
        raise OSError("Écriture du presse-papiers impossible; ouvrir le .txt puis Ctrl+A, Ctrl+C.")


def copy_ready_file(path: Path, private_decks_root: Path) -> dict[str, Any]:
    ready_root = (private_decks_root.resolve() / "import_ready").resolve()
    resolved = path.resolve()
    if not resolved.is_relative_to(ready_root) or resolved.suffix.casefold() != ".txt":
        raise ValueError("Seul un fichier .txt sous data/local/decks/import_ready peut être copié.")
    if not resolved.is_file():
        raise FileNotFoundError(f"Fichier prêt à importer absent: {resolved}")
    if resolved.stat().st_size > MAX_DECK_BYTES:
        raise ValueError(f"Deck trop volumineux (maximum {MAX_DECK_BYTES} octets).")
    text, _ = decode_deck_bytes(resolved.read_bytes())
    parse_deck_export(text)
    copy_text_to_clipboard(text)
    return {"path": str(resolved), "copied": True, "fallback": "ouvrir le .txt, Ctrl+A, Ctrl+C"}
