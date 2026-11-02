"""Import local et parsing prudent des journaux Pokémon TCG Live."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pokemind.database import connect_writable, initialize_schema, utc_now


PARSER_VERSION = "pm0003f-1"
MAX_LOG_BYTES = 2_000_000
MAX_EVIDENCE_CHARS = 300
DECK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
TURN_PATTERNS = (
    re.compile(r"^Turn\s*#\s*(\d+)\s*-\s*(.+?)(?:['’]s)\s+Turn\s*$", re.IGNORECASE),
    re.compile(r"^Tour\s*(?:#|n[°ºo]?)?\s*(\d+)\s*-\s*Tour\s+d['’e]?\s*(.+?)\s*$", re.IGNORECASE),
)
UNNUMBERED_TURN_PATTERNS = (
    re.compile(r"^Tour\s+de\s+(.+?)\s*$", re.IGNORECASE),
    re.compile(r"^(.+?)(?:['’]s)\s+Turn\s*$", re.IGNORECASE),
)
REFERENCE_PATTERNS = (
    re.compile(r"^(?:Exporting player|Reference player)\s*:\s*(.+?)\s*$", re.IGNORECASE),
    re.compile(r"^Joueur de référence\s*:\s*(.+?)\s*$", re.IGNORECASE),
)
WIN_PATTERNS = (
    re.compile(
        r"(?:.*\.\s+|^)(.+?)\s+(?:wins?|won the game|a gagné|gagne|remporte la partie)\.\s*$",
        re.IGNORECASE,
    ),
    re.compile(r"(?:All Prize cards taken\.\s*)?(.+?)\s+wins?\.\s*$", re.IGNORECASE),
    re.compile(r"(.+?)\s+(?:won the game|a gagné|gagne|remporte la partie)\.\s*$", re.IGNORECASE),
)
GENERIC_CARDS = {
    "a card", "cards", "une carte", "des cartes", "the card", "la carte",
}
GENERIC_CARD_PATTERNS = (
    re.compile(r"^(?:an?|one|the)\s+(?:additional\s+|extra\s+)?cards?(?:\s+because\b.*)?$", re.IGNORECASE),
    re.compile(r"^(?:une?|la)\s+carte(?:\s+supplémentaire)?(?:\s+car\b.*)?$", re.IGNORECASE),
)


@dataclass(frozen=True, slots=True)
class ParsedEvent:
    sequence: int
    turn_number: int | None
    actor: str | None
    event_type: str
    card_name: str | None
    evidence: str
    confidence: str = "high"
    target: str | None = None
    card_owner: str | None = None


@dataclass(frozen=True, slots=True)
class ParsedBattle:
    reference_player: str | None
    opponent_name: str | None
    winner: str | None
    outcome: str
    valid: bool
    max_turn: int | None
    events: tuple[ParsedEvent, ...]
    warnings: tuple[str, ...]


def _clean_name(value: str) -> str:
    return value.strip().strip(". \t\r\n")


def _name_key(value: str) -> str:
    return unicodedata.normalize("NFKC", _clean_name(value)).casefold()


def _same_name(left: str, right: str) -> bool:
    return _name_key(left) == _name_key(right)


def _clean_card(value: str) -> str | None:
    card = value.strip().strip(". \t\r\n")
    card = re.sub(
        r"\s+(?:to|onto|in|on|au|aux|à|dans|sur)\s+(?:the |le |la |les |l['’])?.*$",
        "",
        card,
        flags=re.IGNORECASE,
    ).strip()
    if (
        not card
        or card.casefold() in GENERIC_CARDS
        or any(pattern.fullmatch(card) for pattern in GENERIC_CARD_PATTERNS)
        or "opening hand" in card.casefold()
        or "main de départ" in card.casefold()
        or re.match(r"^\d+\s+(?:cards?|cartes?)\b", card, re.IGNORECASE)
    ):
        return None
    card = re.sub(r"^(?:the card|la carte)\s+", "", card, flags=re.IGNORECASE).strip()
    if not card:
        return None
    return card[:200]


def _is_generic_draw(value: str) -> bool:
    candidate = value.strip().strip(". \t\r\n")
    return candidate.casefold() in GENERIC_CARDS or any(
        pattern.fullmatch(candidate) for pattern in GENERIC_CARD_PATTERNS
    )


def _match_turn(line: str) -> tuple[int, str] | None:
    for pattern in TURN_PATTERNS:
        if match := pattern.match(line):
            return int(match.group(1)), _clean_name(match.group(2))
    return None


def _match_unnumbered_turn(line: str) -> str | None:
    for pattern in UNNUMBERED_TURN_PATTERNS:
        if match := pattern.match(line):
            return _clean_name(match.group(1))
    return None


def _reference_from_opening_hand(lines: list[str]) -> str | None:
    opening = re.compile(
        r"^(.+?)\s+(?:drew\s+\d+\s+cards?\s+for\s+the\s+opening\s+hand|"
        r"a pioché\s+\d+\s+cartes?\s+pour\s+(?:sa|la)\s+main\s+de\s+départ)\.\s*$",
        re.IGNORECASE,
    )
    candidates: list[str] = []
    for index, line in enumerate(lines):
        match = opening.match(line)
        if not match:
            continue
        following = lines[index + 1 : index + 4]
        if any("•" in item and re.search(r"[A-Za-zÀ-ÿ]", item) for item in following):
            candidates.append(_clean_name(match.group(1)))
    unique = list(dict.fromkeys(candidates))
    return unique[0] if len(unique) == 1 else None


def _event_from_line(line: str, sequence: int, turn: int | None) -> ParsedEvent | None:
    stripped = re.sub(r"^-\s*", "", line.strip())
    # A damage counter placed *on* another player's Pokemon is not a play
    # of that Pokemon by the actor. Keep the event, never manufacture ownership.
    effect = re.match(r"^(.+?)\s+(?:a placé|placed)\s+(.+?(?:marqueurs?|counters?).+?)\s+(?:sur|on)\s+(.+?)\.\s*$", stripped, re.I)
    if effect:
        return ParsedEvent(sequence, turn, _clean_name(effect[1]), "damage", None,
                           stripped[:MAX_EVIDENCE_CHARS], "ambiguous_owner", target=effect[3])
    prize = re.match(r"^(.+?)\s+(?:a pris|took)\s+(\d+|une?|an?)\s+(?:cartes? Récompense|Prize cards?)\b", stripped, re.I)
    if prize:
        count = prize[2] if prize[2].isdigit() else "1"
        return ParsedEvent(sequence, turn, _clean_name(prize[1]), "prize", None,
                           stripped[:MAX_EVIDENCE_CHARS], target=count)
    knocked = re.match(r"^(.+?)\s+(?:a été mis K\.O\.|est K\.O\.|was Knocked Out|is Knocked Out)", stripped, re.I)
    if knocked:
        return ParsedEvent(sequence, turn, None, "knockout", None,
                           stripped[:MAX_EVIDENCE_CHARS], "owner_unknown", target=knocked[1])
    owned_use = re.match(r"^(.+)\s+de\s+(.+?)\s+a utilisé\s+(.+?)\.\s*$", stripped, re.I)
    if owned_use:
        actor = _clean_name(owned_use[2])
        return ParsedEvent(sequence, turn, actor, "use", _clean_card(owned_use[1]),
                           stripped[:MAX_EVIDENCE_CHARS], card_owner=actor)
    placed = re.match(r"^(.+?)\s+(?:a placé|put)\s+(.+?)\s+(?:en position Active|sur (?:son |le )?Banc|in the Active Spot|on (?:their |the )?Bench)\.\s*$", stripped, re.I)
    if placed:
        return ParsedEvent(sequence, turn, _clean_name(placed[1]), "place", _clean_card(placed[2]),
                           stripped[:MAX_EVIDENCE_CHARS], card_owner=_clean_name(placed[1]))
    evolved = re.match(r"^(.+?)\s+(?:a fait évoluer|evolved)\s+(.+?)\s+(?:en|into)\s+(.+?)\.\s*$", stripped, re.I)
    if evolved and not re.search(r"\bde\s|['’]s", evolved[3], re.I):
        return ParsedEvent(sequence, turn, _clean_name(evolved[1]), "evolve", _clean_card(evolved[3]),
                           stripped[:MAX_EVIDENCE_CHARS], card_owner=_clean_name(evolved[1]))
    compound_draw_patterns = (
        re.compile(
            r"^(.+?)\s+drew\s+(.+?)\s+and played\s+(?:it|them)(?:\s+.*)?\.\s*$",
            re.IGNORECASE,
        ),
        re.compile(
            r"^(.+?)\s+a pioché\s+(.+?)\s+et\s+(?:l['’]a\s+jouée?|les\s+a\s+jouées?|"
            r"a\s+joué\s+(?:la|les))(?:\s+.*)?\.\s*$",
            re.IGNORECASE,
        ),
    )
    for compound_pattern in compound_draw_patterns:
        if compound_draw := compound_pattern.match(stripped):
            card = _clean_card(compound_draw.group(2))
            if card is None:
                return None
            return ParsedEvent(
                sequence, turn, _clean_name(compound_draw.group(1)), "draw", card,
                stripped[:MAX_EVIDENCE_CHARS],
            )
    patterns: tuple[tuple[str, re.Pattern[str]], ...] = (
        ("play", re.compile(r"^(.+?)\s+(?:played|a joué)\s+(.+?)\.\s*$", re.IGNORECASE)),
        ("attach", re.compile(r"^(.+?)\s+(?:attached|a attaché)\s+(.+?)\.\s*$", re.IGNORECASE)),
        ("reveal", re.compile(r"^(.+?)\s+(?:revealed|a révélé)\s+(.+?)\.\s*$", re.IGNORECASE)),
        ("draw", re.compile(r"^(.+?)\s+(?:drew|a pioché)\s+(.+?)\.\s*$", re.IGNORECASE)),
    )
    for event_type, pattern in patterns:
        if match := pattern.match(stripped):
            actor = _clean_name(match.group(1))
            if re.search(r"\b(?:drew|played|attached|a pioché|a joué|a attaché)\b", actor, re.IGNORECASE):
                continue
            card = _clean_card(match.group(2))
            if card is None:
                if event_type == "draw" and _is_generic_draw(match.group(2)):
                    return ParsedEvent(
                        sequence, turn, actor, event_type, None,
                        stripped[:MAX_EVIDENCE_CHARS], "low",
                    )
                return None
            return ParsedEvent(
                sequence, turn, actor, event_type, card,
                stripped[:MAX_EVIDENCE_CHARS],
            )

    used_en = re.match(r"^(.+?)['’]s\s+(.+?)\s+used\s+(.+?)(?:\s+on\s+.+)?\.\s*$", stripped, re.IGNORECASE)
    if used_en:
        return ParsedEvent(
            sequence, turn, _clean_name(used_en.group(1)), "use", _clean_card(used_en.group(2)),
            stripped[:MAX_EVIDENCE_CHARS],
        )
    used_fr = re.match(r"^(.+?)\s+a utilisé\s+(.+?)\.\s*$", stripped, re.IGNORECASE)
    if used_fr:
        return ParsedEvent(
            sequence, turn, _clean_name(used_fr.group(1)), "use", None,
            stripped[:MAX_EVIDENCE_CHARS],
        )
    return None


def parse_battle_log(text: str, *, reference_player: str | None = None) -> ParsedBattle:
    if not text.strip():
        raise ValueError("Le journal est vide.")
    if len(text.encode("utf-8")) > MAX_LOG_BYTES:
        raise ValueError(f"Journal trop volumineux (maximum {MAX_LOG_BYTES} octets).")
    lines = [line.strip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    participants: list[str] = []
    turn_participants: list[str] = []
    explicit_references: dict[str, str] = {}
    winners: dict[str, str] = {}
    current_turn: int | None = None
    sequential_turn = 0
    max_turn: int | None = None
    events: list[ParsedEvent] = []

    for line in lines:
        if not line:
            continue
        for pattern in REFERENCE_PATTERNS:
            if match := pattern.match(line):
                name = _clean_name(match.group(1))
                explicit_references.setdefault(_name_key(name), name)
                break
        if turn_match := _match_turn(line):
            current_turn, player = turn_match
            max_turn = max(max_turn or 0, current_turn)
            if player not in participants:
                participants.append(player)
            if not any(_same_name(player, known) for known in turn_participants):
                turn_participants.append(player)
            continue
        if player := _match_unnumbered_turn(line):
            sequential_turn += 1
            current_turn = sequential_turn
            max_turn = current_turn
            if player not in participants:
                participants.append(player)
            if not any(_same_name(player, known) for known in turn_participants):
                turn_participants.append(player)
            continue
        for pattern in WIN_PATTERNS:
            if match := pattern.search(line):
                name = _clean_name(match.group(1))
                winners.setdefault(_name_key(name), name)
                break
        actor_match = re.match(
            r"^-?\s*(.+?)\s+(?:drew|played|attached|revealed|a pioché|a joué|a attaché|a révélé)\b",
            line,
            re.IGNORECASE,
        )
        if actor_match:
            actor = _clean_name(actor_match.group(1))
            if actor and actor not in participants:
                participants.append(actor)
        event = _event_from_line(line, len(events) + 1, current_turn)
        if event:
            events.append(event)
            if event.actor and event.actor not in participants:
                participants.append(event.actor)

    if len(explicit_references) == 1:
        reference = next(iter(explicit_references.values()))
    elif explicit_references:
        reference = None
    else:
        reference = _reference_from_opening_hand(lines)
    winner = next(iter(winners.values())) if len(winners) == 1 else None
    opponent = None
    if reference:
        participant_source = (
            turn_participants
            if any(not _same_name(name, reference) for name in turn_participants)
            else participants
        )
        distinct_others: dict[str, str] = {}
        for name in participant_source:
            if not _same_name(name, reference):
                distinct_others.setdefault(_name_key(name), name)
        if len(distinct_others) == 1:
            opponent = next(iter(distinct_others.values()))

    warnings: list[str] = []
    if reference_player is not None:
        if not isinstance(reference_player, str) or not reference_player.strip() or len(reference_player) > 100:
            raise ValueError("BATTLE_EXPLICIT_PLAYER_INVALID")
        confirmed = _clean_name(reference_player)
        if reference and not _same_name(reference, confirmed):
            warnings.append("Export reference differs from explicitly selected player; selected player used.")
        reference = confirmed if any(_same_name(confirmed, p) for p in participants) else None
        others = {_name_key(p): p for p in (turn_participants or participants)
                  if reference and not _same_name(p, reference)}
        opponent = next(iter(others.values())) if len(others) == 1 else None
    if len(explicit_references) > 1:
        warnings.append("Plusieurs joueurs de référence contradictoires; identité laissée inconnue.")
    if len(winners) > 1:
        warnings.append("Plusieurs gagnants contradictoires; issue laissée inconnue.")
    outcome = "inconnue"
    if winner and reference and opponent:
        if _same_name(winner, reference):
            outcome = "W"
        elif _same_name(winner, opponent):
            outcome = "L"
        else:
            warnings.append("Gagnant non corroboré par les deux participants reconnus; issue laissée inconnue.")
    elif winner:
        warnings.append("Gagnant présent sans adversaire corroboré; issue laissée inconnue.")
    if max_turn is None:
        warnings.append("Aucun en-tête de tour reconnu.")
    if reference is None:
        warnings.append("Joueur de référence non déterminé.")
    if winner is None:
        warnings.append("Issue non déterminée; aucune victoire ou défaite n'est inventée.")
    if not events:
        warnings.append("Aucun événement pris en charge n'a été reconnu.")
    valid = reference is not None and bool(events) and (max_turn is not None or reference_player is not None)
    return ParsedBattle(reference, opponent, winner, outcome, valid, max_turn, tuple(events), tuple(warnings))


def decode_log_bytes(raw: bytes) -> tuple[str, str]:
    if len(raw) > MAX_LOG_BYTES:
        raise ValueError(f"Journal trop volumineux (maximum {MAX_LOG_BYTES} octets).")
    for encoding in ("utf-8-sig", "utf-16", "cp1252"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError("Encodage du journal non reconnu (UTF-8, UTF-16 ou Windows-1252 attendu).")


def read_clipboard() -> str:
    if sys.platform != "win32":
        raise OSError("Presse-papiers disponible seulement sous Windows; utiliser un fichier ou '-' pour stdin.")
    try:
        completed = subprocess.run(
            [
                "powershell", "-NoProfile", "-NonInteractive", "-Command",
                "$utf8 = [System.Text.UTF8Encoding]::new($false); "
                "[Console]::OutputEncoding = $utf8; $OutputEncoding = $utf8; Get-Clipboard -Raw",
            ],
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        raise OSError("Lecture du presse-papiers impossible; utiliser un fichier ou '-' pour stdin.") from exc
    if completed.returncode != 0:
        raise OSError("Lecture du presse-papiers impossible; utiliser un fichier ou '-' pour stdin.")
    if not completed.stdout.strip():
        raise ValueError("Le presse-papiers ne contient aucun texte.")
    return completed.stdout


def _actor_role(actor: str | None, parsed: ParsedBattle) -> str:
    if not actor or not parsed.reference_player:
        return "unknown"
    if _same_name(actor, parsed.reference_player):
        return "self"
    if parsed.opponent_name and _same_name(actor, parsed.opponent_name):
        return "opponent"
    return "unknown"


def _insert_events(connection: Any, battle_id: int, parsed: ParsedBattle) -> None:
    for event in parsed.events:
        role = _actor_role(event.actor, parsed)
        # Ownership qualifiers stay in the parsed event/evidence. Both schema7
        # and schema13 constrain stored confidence to high/medium/low.
        confidence = "low" if event.confidence in {"ambiguous_owner", "owner_unknown"} else event.confidence
        if confidence not in {"high", "medium", "low"}:
            raise ValueError("BATTLE_UNSUPPORTED_CONFIDENCE")
        event_cursor = connection.execute(
            """INSERT INTO battle_events
               (battle_id, sequence, turn_number, actor, actor_role, event_type,
                card_name, evidence, confidence)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                battle_id, event.sequence, event.turn_number, event.actor, role,
                event.event_type, event.card_name, event.evidence, confidence,
            ),
        )
        if event.card_name:
            connection.execute(
                """INSERT INTO card_observations
                   (battle_id, event_id, owner_role, card_name, observation_type,
                    turn_number, confidence) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    battle_id, int(event_cursor.lastrowid), role, event.card_name,
                    event.event_type, event.turn_number, confidence,
                ),
            )


def import_battle_log(
    db_path: Path,
    text: str,
    *,
    source_kind: str,
    source_name: str | None = None,
    deck_id: str | None = None,
    parser_version: str = PARSER_VERSION,
    reparse: bool = False,
    reference_player: str | None = None,
) -> dict[str, Any]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    raw_size = len(normalized.encode("utf-8"))
    if raw_size > MAX_LOG_BYTES:
        raise ValueError(f"Journal trop volumineux (maximum {MAX_LOG_BYTES} octets).")
    if deck_id and not DECK_ID_RE.fullmatch(deck_id):
        raise ValueError("Identifiant de deck invalide (1-64 caractères: lettres, chiffres, . _ -).")
    if not parser_version or len(parser_version) > 64:
        raise ValueError("Version du parseur invalide.")
    parsed = parse_battle_log(normalized, reference_player=reference_player)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    effective_deck = deck_id or f"observed-{digest[:12]}"
    imported_at = utc_now()
    connection = connect_writable(db_path)
    try:
        initialize_schema(connection)
        existing = connection.execute(
            "SELECT id, deck_id, valid, outcome, imported_at FROM battle_logs WHERE source_sha256 = ?",
            (digest,),
        ).fetchone()
        if existing and not reparse:
            return {
                "database": str(db_path), "battle_id": int(existing["id"]), "sha256": digest,
                "duplicate": True, "valid": bool(existing["valid"]), "outcome": existing["outcome"],
                "deck_id": existing["deck_id"], "reparsed": False, "raw_stored": False,
            }

        if existing and deck_id and deck_id != existing["deck_id"]:
            raise ValueError(
                "--reparse refuse de changer le deck déjà lié; réutiliser le deck existant ou omettre --deck."
            )

        with connection:
            if existing:
                battle_id = int(existing["id"])
                effective_deck = str(existing["deck_id"])
                connection.execute("DELETE FROM battle_events WHERE battle_id = ?", (battle_id,))
                connection.execute(
                    """UPDATE battle_logs SET
                       parser_version = ?, source_kind = ?, source_name = ?,
                       reference_player = ?, opponent_name = ?, outcome = ?, winner = ?, valid = ?,
                       max_turn = ?, recognized_events = ?, warnings_json = ?
                       WHERE id = ?""",
                    (
                        parser_version, source_kind, Path(source_name).name if source_name else None,
                        parsed.reference_player, parsed.opponent_name, parsed.outcome, parsed.winner,
                        int(parsed.valid), parsed.max_turn, len(parsed.events),
                        json.dumps(parsed.warnings, ensure_ascii=False), battle_id,
                    ),
                )
                _insert_events(connection, battle_id, parsed)
                return {
                    "database": str(db_path), "battle_id": battle_id, "sha256": digest,
                    "duplicate": False, "reparsed": True, "valid": parsed.valid,
                    "outcome": parsed.outcome, "deck_id": effective_deck,
                    "deck_status": "observé partiellement",
                    "reference_player": parsed.reference_player, "opponent": parsed.opponent_name,
                    "events": len(parsed.events), "max_turn": parsed.max_turn,
                    "warnings": list(parsed.warnings), "raw_stored": False,
                }

            connection.execute(
                """INSERT INTO observed_decks(deck_id, status, created_at, last_seen_at)
                   VALUES (?, 'observé partiellement', ?, ?)
                   ON CONFLICT(deck_id) DO UPDATE SET last_seen_at = excluded.last_seen_at""",
                (effective_deck, imported_at, imported_at),
            )
            cursor = connection.execute(
                """INSERT INTO battle_logs
                   (source_sha256, imported_at, parser_version, source_kind, source_name,
                    reference_player, opponent_name, outcome, winner, valid, deck_id,
                    max_turn, recognized_events, warnings_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    digest, imported_at, parser_version, source_kind,
                    Path(source_name).name if source_name else None,
                    parsed.reference_player, parsed.opponent_name, parsed.outcome, parsed.winner,
                    int(parsed.valid), effective_deck, parsed.max_turn, len(parsed.events),
                    json.dumps(parsed.warnings, ensure_ascii=False),
                ),
            )
            battle_id = int(cursor.lastrowid)
            _insert_events(connection, battle_id, parsed)
        return {
            "database": str(db_path), "battle_id": battle_id, "sha256": digest,
            "duplicate": False, "reparsed": False, "valid": parsed.valid, "outcome": parsed.outcome,
            "deck_id": effective_deck, "deck_status": "observé partiellement",
            "reference_player": parsed.reference_player, "opponent": parsed.opponent_name,
            "events": len(parsed.events), "max_turn": parsed.max_turn,
            "warnings": list(parsed.warnings), "raw_stored": False,
        }
    finally:
        connection.close()
