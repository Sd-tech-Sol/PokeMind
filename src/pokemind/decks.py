"""Import strict et versionne des exports de deck Pokemon TCG Live."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pokemind.battle_logs import DECK_ID_RE
from pokemind.database import connect_readonly, connect_writable, initialize_schema, utc_now


DECK_PARSER_VERSION = "pm0003-1"
MAX_DECK_BYTES = 500_000

_SECTION_ALIASES = {
    "pokemon": "pokemon",
    "pokémon": "pokemon",
    "trainer": "trainer",
    "trainers": "trainer",
    "trainer card": "trainer",
    "trainer cards": "trainer",
    "dresseur": "trainer",
    "dresseurs": "trainer",
    "carte dresseur": "trainer",
    "cartes dresseur": "trainer",
    "energy": "energy",
    "energies": "energy",
    "énergie": "energy",
    "énergies": "energy",
}
_SECTION_RE = re.compile(r"^(?:##\s*)?(.+?)\s*(?::|-)\s*(\d+)\s*$", re.IGNORECASE)
_TOTAL_RE = re.compile(
    r"^(?:total\s+(?:cards?|de\s+cartes|cartes))\s*(?::|-)\s*(\d+)\s*$",
    re.IGNORECASE,
)
_COLLECTOR_RE = re.compile(r"^(?=.*\d)[A-Za-z0-9]+(?:[/.-][A-Za-z0-9]+)*$")
_SET_CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,19}$")


@dataclass(frozen=True, slots=True)
class DeckCard:
    ordinal: int
    source_line: int
    card_type: str
    quantity: int
    name: str
    set_code: str | None
    collector_number: str | None
    normalized_line: str


@dataclass(frozen=True, slots=True)
class ParsedDeck:
    cards: tuple[DeckCard, ...]
    section_counts: dict[str, int]
    total_cards: int
    export_sha256: str
    list_sha256: str
    coverage: dict[str, Any]


def _normalized_text(text: str) -> str:
    return unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n").strip()


def decode_deck_bytes(raw: bytes) -> tuple[str, str]:
    if len(raw) > MAX_DECK_BYTES:
        raise ValueError(f"Export de deck trop volumineux (maximum {MAX_DECK_BYTES} octets).")
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("Encodage du deck non reconnu (UTF-8, UTF-16 ou Windows-1252 attendu).")


def _section_key(label: str) -> str | None:
    key = unicodedata.normalize("NFKC", label).strip().casefold()
    key = re.sub(r"\s+", " ", key)
    return _SECTION_ALIASES.get(key)


def _parse_card_line(line: str, line_number: int, card_type: str, ordinal: int) -> DeckCard:
    cleaned = re.sub(r"^\*\s*", "", line.strip())
    match = re.fullmatch(r"([1-9]\d?)\s+(.+?)\s*", cleaned)
    if not match:
        raise ValueError(f"Ligne {line_number}: carte malformée.")
    quantity = int(match.group(1))
    if quantity > 60:
        raise ValueError(f"Ligne {line_number}: quantité hors limites.")
    remainder = re.sub(r"\s+", " ", match.group(2).strip())
    tokens = remainder.split(" ")
    set_code: str | None = None
    collector_number: str | None = None
    if len(tokens) >= 3 and _SET_CODE_RE.fullmatch(tokens[-2]) and _COLLECTOR_RE.fullmatch(tokens[-1]):
        set_code = tokens[-2]
        collector_number = tokens[-1]
        tokens = tokens[:-2]
    name = " ".join(tokens).strip()
    if not name or len(name) > 200:
        raise ValueError(f"Ligne {line_number}: nom de carte invalide.")
    normalized_line = f"{quantity} {name}"
    if set_code and collector_number:
        normalized_line += f" {set_code} {collector_number}"
    return DeckCard(
        ordinal=ordinal,
        source_line=line_number,
        card_type=card_type,
        quantity=quantity,
        name=name,
        set_code=set_code,
        collector_number=collector_number,
        normalized_line=normalized_line,
    )


def parse_deck_export(text: str) -> ParsedDeck:
    normalized = _normalized_text(text)
    if not normalized:
        raise ValueError("L'export de deck est vide.")
    if len(normalized.encode("utf-8")) > MAX_DECK_BYTES:
        raise ValueError(f"Export de deck trop volumineux (maximum {MAX_DECK_BYTES} octets).")

    declared: dict[str, int] = {}
    cards: list[DeckCard] = []
    current_section: str | None = None
    footer_total: int | None = None
    for line_number, raw_line in enumerate(normalized.split("\n"), start=1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("******") and line.endswith("******"):
            continue
        if total_match := _TOTAL_RE.fullmatch(line):
            if footer_total is not None:
                raise ValueError(f"Ligne {line_number}: total final en double.")
            footer_total = int(total_match.group(1))
            current_section = None
            continue
        if section_match := _SECTION_RE.fullmatch(line):
            section = _section_key(section_match.group(1))
            if section is not None:
                if section in declared:
                    raise ValueError(f"Ligne {line_number}: section {section} en double.")
                declared[section] = int(section_match.group(2))
                current_section = section
                continue
            raise ValueError(f"Ligne {line_number}: section non reconnue.")
        if current_section is None:
            raise ValueError(f"Ligne {line_number}: contenu hors d'une section reconnue.")
        cards.append(_parse_card_line(line, line_number, current_section, len(cards) + 1))

    required = {"pokemon", "trainer", "energy"}
    if set(declared) != required:
        missing = ", ".join(sorted(required - set(declared))) or "aucune"
        raise ValueError(f"Sections Pokémon/Trainer/Énergie incomplètes (manquantes: {missing}).")
    actual = {
        section: sum(card.quantity for card in cards if card.card_type == section)
        for section in ("pokemon", "trainer", "energy")
    }
    entry_counts = {
        section: sum(1 for card in cards if card.card_type == section)
        for section in ("pokemon", "trainer", "energy")
    }
    quantity_headers = all(declared[section] == actual[section] for section in required)
    entry_headers = all(declared[section] == entry_counts[section] for section in required)
    if not quantity_headers and not entry_headers:
        details = ", ".join(
            f"{section}: annoncé {declared[section]}, quantités {actual[section]}, entrées {entry_counts[section]}"
            for section in ("pokemon", "trainer", "energy")
        )
        raise ValueError(f"Totaux de sections incohérents ({details}).")
    if quantity_headers and entry_headers:
        header_count_mode = "ambiguous"
    elif entry_headers:
        header_count_mode = "entries"
    else:
        header_count_mode = "quantities"
    total = sum(actual.values())
    if footer_total is not None and footer_total != total:
        raise ValueError(f"Total final incohérent: annoncé {footer_total}, lu {total}.")
    if total != 60:
        raise ValueError(f"Un deck exact doit contenir 60 cartes; total lu: {total}.")

    canonical_counts: dict[tuple[str, str, str | None, str | None], int] = {}
    for card in cards:
        identity = (card.card_type, card.name, card.set_code, card.collector_number)
        canonical_counts[identity] = canonical_counts.get(identity, 0) + card.quantity
    canonical = [
        [card_type, name, set_code, collector_number, quantity]
        for (card_type, name, set_code, collector_number), quantity in sorted(
            canonical_counts.items(), key=lambda item: tuple(part or "" for part in item[0])
        )
    ]
    list_payload = json.dumps(canonical, ensure_ascii=False, separators=(",", ":"))
    with_printing = sum(1 for card in cards if card.set_code and card.collector_number)
    coverage = {
        "entries_total": len(cards),
        "entries_with_printing": with_printing,
        "printing_coverage": round(with_printing / len(cards), 4) if cards else 0.0,
        "footer_present": footer_total is not None,
        "section_header_count_mode": header_count_mode,
        "languages_accepted": ["fr", "en"],
    }
    return ParsedDeck(
        cards=tuple(cards),
        section_counts=actual,
        total_cards=total,
        export_sha256=hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        list_sha256=hashlib.sha256(list_payload.encode("utf-8")).hexdigest(),
        coverage=coverage,
    )


def import_deck(
    db_path: Path,
    text: str,
    *,
    deck_id: str,
    source_kind: str,
    source_name: str | None = None,
    source_encoding: str | None = None,
) -> dict[str, Any]:
    if not DECK_ID_RE.fullmatch(deck_id):
        raise ValueError("Identifiant de deck invalide (1-64 caractères: lettres, chiffres, . _ -).")
    if source_kind not in {"clipboard", "file", "stdin"}:
        raise ValueError("Provenance de deck invalide.")
    parsed = parse_deck_export(text)
    imported_at = utc_now()
    connection = connect_writable(db_path)
    try:
        initialize_schema(connection)
        existing = connection.execute(
            "SELECT id, version_number, imported_at FROM deck_versions WHERE deck_id = ? AND list_sha256 = ?",
            (deck_id, parsed.list_sha256),
        ).fetchone()
        if existing:
            return {
                "database": str(db_path),
                "deck_id": deck_id,
                "deck_version_id": int(existing["id"]),
                "version": int(existing["version_number"]),
                "duplicate": True,
                "exact_confirmed": True,
                "total_cards": 60,
                "list_sha256": parsed.list_sha256,
                "first_imported_at": existing["imported_at"],
                "raw_stored": False,
                "historical_battles_linked": False,
            }
        row = connection.execute(
            "SELECT COALESCE(MAX(version_number), 0) + 1 FROM deck_versions WHERE deck_id = ?",
            (deck_id,),
        ).fetchone()
        version_number = int(row[0])
        with connection:
            cursor = connection.execute(
                """INSERT INTO deck_versions
                   (deck_id, version_number, imported_at, approved_at, effective_from,
                    parser_version, source_kind, source_name, source_encoding, export_sha256,
                    list_sha256, total_cards, entry_count, exact_confirmed, sections_json,
                    coverage_json, raw_stored)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 60, ?, 1, ?, ?, 0)""",
                (
                    deck_id,
                    version_number,
                    imported_at,
                    imported_at,
                    imported_at,
                    DECK_PARSER_VERSION,
                    source_kind,
                    Path(source_name).name if source_name else None,
                    source_encoding,
                    parsed.export_sha256,
                    parsed.list_sha256,
                    len(parsed.cards),
                    json.dumps(parsed.section_counts, ensure_ascii=False, sort_keys=True),
                    json.dumps(parsed.coverage, ensure_ascii=False, sort_keys=True),
                ),
            )
            version_id = int(cursor.lastrowid)
            connection.executemany(
                """INSERT INTO deck_version_cards
                   (deck_version_id, ordinal, source_line, card_type, quantity, card_name,
                    set_code, collector_number, normalized_line)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (
                        version_id,
                        card.ordinal,
                        card.source_line,
                        card.card_type,
                        card.quantity,
                        card.name,
                        card.set_code,
                        card.collector_number,
                        card.normalized_line,
                    )
                    for card in parsed.cards
                ],
            )
        return {
            "database": str(db_path),
            "deck_id": deck_id,
            "deck_version_id": version_id,
            "version": version_number,
            "duplicate": False,
            "exact_confirmed": True,
            "total_cards": 60,
            "entries": len(parsed.cards),
            "sections": parsed.section_counts,
            "coverage": parsed.coverage,
            "export_sha256": parsed.export_sha256,
            "list_sha256": parsed.list_sha256,
            "approved_at": imported_at,
            "effective_from": imported_at,
            "raw_stored": False,
            "historical_battles_linked": False,
        }
    finally:
        connection.close()


def show_deck(db_path: Path, deck_id: str) -> dict[str, Any]:
    if not DECK_ID_RE.fullmatch(deck_id):
        raise ValueError("Identifiant de deck invalide (1-64 caractères: lettres, chiffres, . _ -).")
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente; importer d'abord le deck ou les volumes.")
    connection = connect_readonly(db_path)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        version = connection.execute(
            "SELECT * FROM deck_versions WHERE deck_id = ? ORDER BY version_number DESC LIMIT 1",
            (deck_id,),
        ).fetchone() if "deck_versions" in tables else None
        observed = connection.execute(
            "SELECT status, created_at, last_seen_at FROM observed_decks WHERE deck_id = ?",
            (deck_id,),
        ).fetchone() if "observed_decks" in tables else None
        battle_count = int(
            connection.execute("SELECT COUNT(*) FROM battle_logs WHERE deck_id = ?", (deck_id,)).fetchone()[0]
        ) if "battle_logs" in tables else 0
        if version is None:
            if observed is None:
                raise ValueError(f"Deck inconnu: {deck_id}.")
            return {
                "database": str(db_path),
                "deck_id": deck_id,
                "status": observed["status"],
                "exact_confirmed": False,
                "version": None,
                "total_cards": None,
                "cards": [],
                "historical_battles": battle_count,
                "battles_linked_to_version": 0,
                "limits": ["Les cartes observées dans les journaux ne forment pas une liste exacte de 60 cartes."],
            }
        cards = connection.execute(
            """SELECT ordinal, source_line, card_type, quantity, card_name, set_code,
                      collector_number, normalized_line
               FROM deck_version_cards WHERE deck_version_id = ? ORDER BY ordinal""",
            (version["id"],),
        ).fetchall()
        linked = int(
            connection.execute(
                "SELECT COUNT(*) FROM battle_deck_versions WHERE deck_version_id = ?", (version["id"],)
            ).fetchone()[0]
        )
        return {
            "database": str(db_path),
            "deck_id": deck_id,
            "status": "export 60 cartes vérifié",
            "exact_confirmed": True,
            "deck_version_id": int(version["id"]),
            "version": int(version["version_number"]),
            "imported_at": version["imported_at"],
            "approved_at": version["approved_at"],
            "effective_from": version["effective_from"],
            "parser_version": version["parser_version"],
            "source": {
                "kind": version["source_kind"],
                "name": version["source_name"],
                "encoding": version["source_encoding"],
                "export_sha256": version["export_sha256"],
                "list_sha256": version["list_sha256"],
            },
            "total_cards": int(version["total_cards"]),
            "entry_count": int(version["entry_count"]),
            "sections": json.loads(version["sections_json"]),
            "coverage": json.loads(version["coverage_json"]),
            "cards": [dict(card) for card in cards],
            "raw_stored": bool(version["raw_stored"]),
            "historical_battles": battle_count,
            "battles_linked_to_version": linked,
            "limits": [
                "Cette version n'est pas une preuve de collection complète ni de légalité Standard/Live.",
                "Aucune partie historique n'est associée automatiquement à cette version.",
            ],
        }
    finally:
        connection.close()
