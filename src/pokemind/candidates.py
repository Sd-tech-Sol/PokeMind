"""Candidats de deck distincts des versions jouées et export volontaire."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

from pokemind.database import connect_readonly, connect_writable, initialize_schema, utc_now
from pokemind.deck_exports import _atomic_write_new, serialize_deck
from pokemind.decks import DeckCard
from pokemind.rules import check_card


CANDIDATE_SCHEMA_VERSION = 1
MAX_CHANGES_BYTES = 500_000
_SAFE_TEXT = re.compile(r"^[^\x00-\x1f\x7f]{1,200}$")
_SAFE_CODE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")
_SAFE_NUMBER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9/._-]{0,31}$")


def _normalized(value: Any) -> str:
    return " ".join(unicodedata.normalize("NFC", str(value or "")).casefold().split())


def _text(value: Any, field: str, pattern: re.Pattern[str] = _SAFE_TEXT) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} doit être du texte.")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not pattern.fullmatch(cleaned):
        raise ValueError(f"{field} est invalide.")
    return cleaned


def _strict_date(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("context.as_of doit être une date YYYY-MM-DD.")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ValueError("context.as_of doit être une date YYYY-MM-DD valide.") from exc


def _tables(connection: sqlite3.Connection) -> set[str]:
    return {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _read_changes(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Fichier de changements absent: {resolved}")
    raw = resolved.read_bytes()
    if len(raw) > MAX_CHANGES_BYTES:
        raise ValueError(f"Fichier de changements trop volumineux (maximum {MAX_CHANGES_BYTES} octets).")
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Le fichier de changements doit être un JSON UTF-8 valide.") from exc
    required = {"schema_version", "name", "base_deck", "context", "source", "changes"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise ValueError("Changements JSON: structure exacte invalide.")
    if payload["schema_version"] != CANDIDATE_SCHEMA_VERSION:
        raise ValueError(f"schema_version doit valoir {CANDIDATE_SCHEMA_VERSION}.")
    name = _text(payload["name"], "name")
    base = payload["base_deck"]
    if not isinstance(base, dict) or set(base) != {"deck_id", "version"}:
        raise ValueError("base_deck doit contenir exactement deck_id et version.")
    deck_id = _text(base["deck_id"], "base_deck.deck_id")
    version = base["version"]
    if isinstance(version, bool) or not isinstance(version, int) or version < 1:
        raise ValueError("base_deck.version doit être un entier positif.")
    context = payload["context"]
    if not isinstance(context, dict) or set(context) != {"format", "platform", "as_of"}:
        raise ValueError("context doit contenir exactement format, platform et as_of.")
    if context["format"] not in {"standard", "expanded"} or context["platform"] not in {"live", "in_person"}:
        raise ValueError("Format ou plateforme du candidat invalide.")
    as_of = _strict_date(context["as_of"])
    source = payload["source"]
    if not isinstance(source, dict) or set(source) != {"kind"} or source["kind"] != "owner_controlled_changes":
        raise ValueError("source.kind doit valoir owner_controlled_changes.")
    changes = payload["changes"]
    if not isinstance(changes, list) or not changes or len(changes) > 500:
        raise ValueError("changes doit être une liste non vide et bornée.")
    normalized_changes: list[dict[str, Any]] = []
    for index, raw_change in enumerate(changes, start=1):
        if not isinstance(raw_change, dict):
            raise ValueError(f"Changement {index}: objet JSON attendu.")
        action = raw_change.get("action")
        required_change = {"action", "name", "set_code", "collector_number", "quantity"}
        allowed_change = required_change | {"type"}
        if action not in {"add", "remove"} or not required_change.issubset(raw_change) or set(raw_change) - allowed_change:
            raise ValueError(f"Changement {index}: champs ou action invalides.")
        card_type = raw_change.get("type")
        if action == "add" and card_type not in {"pokemon", "trainer", "energy"}:
            raise ValueError(f"Changement {index}: type requis pour un ajout.")
        if action == "remove" and card_type is not None:
            raise ValueError(f"Changement {index}: type interdit pour un retrait.")
        quantity = raw_change["quantity"]
        if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= 60:
            raise ValueError(f"Changement {index}: quantity doit être entre 1 et 60.")
        normalized_changes.append({
            "action": action,
            "type": card_type,
            "name": _text(raw_change["name"], f"Changement {index}: name"),
            "set_code": _text(raw_change["set_code"], f"Changement {index}: set_code", _SAFE_CODE),
            "collector_number": _text(raw_change["collector_number"], f"Changement {index}: collector_number", _SAFE_NUMBER),
            "quantity": quantity,
        })
    canonical = {
        "name": name, "base_deck": {"deck_id": deck_id, "version": version},
        "context": {"format": context["format"], "platform": context["platform"], "as_of": as_of},
        "changes": normalized_changes,
    }
    digest = hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {**canonical, "change_sha256": digest, "source_name": path.name}


def _load_base(connection: sqlite3.Connection, deck_id: str, version: int) -> tuple[int, list[dict[str, Any]]]:
    row = connection.execute(
        """SELECT id, exact_confirmed, total_cards FROM deck_versions
           WHERE deck_id = ? AND version_number = ?""",
        (deck_id, version),
    ).fetchone()
    if row is None or not bool(row["exact_confirmed"]) or int(row["total_cards"]) != 60:
        raise ValueError("La version de base doit être une version exacte confirmée de 60 cartes.")
    cards = [dict(item) for item in connection.execute(
        """SELECT card_type, quantity, card_name, set_code, collector_number
           FROM deck_version_cards WHERE deck_version_id = ? ORDER BY ordinal""",
        (row["id"],),
    ).fetchall()]
    return int(row["id"]), cards


def _identity(card: dict[str, Any]) -> tuple[str, str, str]:
    return (_normalized(card["card_name"]), str(card["set_code"] or "").casefold(), str(card["collector_number"] or "").casefold())


def _apply_changes(cards: list[dict[str, Any]], changes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for original in cards:
        card = dict(original)
        key = _identity(card)
        if key in grouped:
            if grouped[key]["card_type"] != card["card_type"]:
                raise ValueError("La version de base contient une identité sous deux types incompatibles.")
            grouped[key]["quantity"] = int(grouped[key]["quantity"]) + int(card["quantity"])
        else:
            grouped[key] = card
    working = list(grouped.values())
    for change in changes:
        key = (_normalized(change["name"]), change["set_code"].casefold(), change["collector_number"].casefold())
        matches = [card for card in working if _identity(card) == key]
        if change["action"] == "remove":
            if len(matches) != 1 or int(matches[0]["quantity"]) < change["quantity"]:
                raise ValueError(f"Retrait impossible ou ambigu pour {change['name']} {change['set_code']} {change['collector_number']}.")
            matches[0]["quantity"] = int(matches[0]["quantity"]) - change["quantity"]
            if matches[0]["quantity"] == 0:
                working.remove(matches[0])
        else:
            if len(matches) > 1:
                raise ValueError(f"Ajout ambigu pour {change['name']} {change['set_code']} {change['collector_number']}.")
            if matches:
                if matches[0]["card_type"] != change["type"]:
                    raise ValueError("Le type de l'ajout contredit l'entrée existante.")
                matches[0]["quantity"] = int(matches[0]["quantity"]) + change["quantity"]
            else:
                working.append({
                    "card_type": change["type"], "quantity": change["quantity"],
                    "card_name": change["name"], "set_code": change["set_code"],
                    "collector_number": change["collector_number"],
                })
    return working


def _resolve_card(connection: sqlite3.Connection, card: dict[str, Any]) -> dict[str, Any]:
    rows = connection.execute(
        """SELECT DISTINCT p.tcgdex_id, p.category, p.stage, t.name,
                          t.category AS translation_category, t.energy_type,
                          t.source_url, t.retrieved_at
           FROM catalog_printings p
           JOIN catalog_sets s ON s.tcgdex_id = p.set_id
           LEFT JOIN catalog_translations t ON t.printing_id = p.tcgdex_id AND t.status = 'present'
           WHERE (s.tcg_online_code = ? COLLATE NOCASE OR s.tcgdex_id = ? COLLATE NOCASE)
             AND p.local_id = ? COLLATE NOCASE""",
        (card["set_code"], card["set_code"], card["collector_number"]),
    ).fetchall()
    ids = sorted({str(row["tcgdex_id"]) for row in rows if _normalized(row["name"]) == _normalized(card["card_name"])})
    if len(ids) != 1:
        return {"status": "ambiguous" if len(ids) > 1 else "unknown", "tcgdex_id": None, "details": None}
    matching = [row for row in rows if str(row["tcgdex_id"]) == ids[0]]
    detail = dict(matching[0])
    categories = {
        _normalized(value)
        for row in matching
        for value in (row["category"], row["translation_category"])
        if _normalized(value) in {"pokemon", "trainer", "energy"}
    }
    if len(categories) > 1:
        category_status = "conflict"
        public_category = None
    elif categories:
        public_category = next(iter(categories))
        category_status = "verified" if public_category == card["card_type"] else "mismatch"
    else:
        category_status = "unknown"
        public_category = None
    return {
        "status": "resolved", "tcgdex_id": ids[0], "details": detail,
        "category_status": category_status, "public_category": public_category,
    }


def _structure_rule(connection: sqlite3.Connection, *, format: str, platform: str, as_of: str) -> dict[str, Any] | None:
    if "official_deck_structure_rules" not in _tables(connection):
        return None
    rows = connection.execute(
        """SELECT r.payload_json, r.rule_id, r.source_id, s.url, s.published_date
           FROM official_deck_structure_rules r
           JOIN official_rule_sources s ON s.source_id = r.source_id
           WHERE r.validation_status = 'verified' AND s.validation_status = 'verified'
             AND (r.format IS NULL OR r.format = ?) AND (r.platform IS NULL OR r.platform = ?)
             AND (r.effective_from IS NULL OR r.effective_from <= ?)
             AND (r.effective_to IS NULL OR r.effective_to >= ?)
             AND (s.effective_from IS NULL OR s.effective_from <= ?)
             AND (s.effective_to IS NULL OR s.effective_to >= ?)""",
        (format, platform, as_of, as_of, as_of, as_of),
    ).fetchall()
    if len(rows) != 1:
        return None
    try:
        payload = json.loads(rows[0]["payload_json"])
    except json.JSONDecodeError:
        return None
    return {"payload": payload, "rule_id": rows[0]["rule_id"], "source_id": rows[0]["source_id"],
            "url": rows[0]["url"], "published_date": rows[0]["published_date"]}


def _validate_candidate(
    connection: sqlite3.Connection, cards: list[dict[str, Any]], *, format: str, platform: str, as_of: str,
) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    total = sum(int(card["quantity"]) for card in cards)
    sections = {kind: sum(int(card["quantity"]) for card in cards if card["card_type"] == kind) for kind in ("pokemon", "trainer", "energy")}
    resolved_cards: list[dict[str, Any]] = []
    for card in cards:
        resolution = _resolve_card(connection, card)
        resolved_cards.append({**card, **resolution})
    identity_counts = {
        state: sum(card["status"] == state for card in resolved_cards)
        for state in ("resolved", "ambiguous", "unknown")
    }
    checks: dict[str, Any] = {
        "total_cards": total,
        "sections": sections,
        "identities": {**identity_counts, "denominator": len(cards)},
        "basic_pokemon_count": None,
        "over_copy_limit": [],
        "card_legality": {"legal": 0, "not_legal": 0, "unknown": 0},
        "category_checks": [
            {
                "card_name": card["card_name"], "tcgdex_id": card.get("tcgdex_id"),
                "declared": card["card_type"], "public": card.get("public_category"),
                "status": card.get("category_status", "unknown"),
                "source_url": (card.get("details") or {}).get("source_url"),
                "retrieved_at": (card.get("details") or {}).get("retrieved_at"),
            }
            for card in resolved_cards
        ],
    }
    reasons: list[str] = []
    if total != 60:
        return "REJECTED_INVALID_60", {"checks": checks, "reason_codes": ["CANDIDATE_TOTAL_NOT_60"]}, resolved_cards
    unresolved = any(card["status"] != "resolved" for card in resolved_cards)
    category_mismatches = [card for card in resolved_cards if card.get("category_status") == "mismatch"]
    category_unknown = any(
        card["status"] == "resolved" and card.get("category_status") in {"unknown", "conflict"}
        for card in resolved_cards
    )
    if category_mismatches:
        reasons.append("CANDIDATE_CATEGORY_MISMATCH")
    pokemon_entries = [
        card for card in resolved_cards
        if card["card_type"] == "pokemon" and card.get("category_status") == "verified"
    ]
    all_categories_verified = bool(resolved_cards) and all(
        card["status"] == "resolved" and card.get("category_status") == "verified"
        for card in resolved_cards
    )
    if pokemon_entries and all((card.get("details") or {}).get("stage") for card in pokemon_entries):
        checks["basic_pokemon_count"] = sum(
            int(card["quantity"]) for card in pokemon_entries
            if _normalized(card["details"].get("stage")) == "basic"
        )
    elif not pokemon_entries and all_categories_verified:
        checks["basic_pokemon_count"] = 0
    rule = _structure_rule(connection, format=format, platform=platform, as_of=as_of)
    normative_complete = False
    if rule:
        payload = rule["payload"]
        normative_complete = all(payload.get(key) is True for key in (
            "copy_limit_exceptions_complete", "special_rule_limits_complete",
        ))
        if payload.get("requires_basic_pokemon") is True:
            declared_pokemon = [card for card in resolved_cards if card["card_type"] == "pokemon"]
            pokemon_classification_complete = all_categories_verified and all(
                (card.get("details") or {}).get("stage") for card in declared_pokemon
            )
            if pokemon_classification_complete and checks["basic_pokemon_count"] == 0:
                reasons.append("CANDIDATE_NO_BASIC_POKEMON")
        limit = payload.get("same_name_limit")
        if normative_complete and isinstance(limit, int):
            totals: dict[str, int] = {}
            for card in resolved_cards:
                if card["status"] != "resolved":
                    continue
                details = card["details"] or {}
                basic_energy = card["card_type"] == "energy" and _normalized(details.get("energy_type")) == "basic"
                if payload.get("basic_energy_unlimited") and basic_energy:
                    continue
                key = _normalized(details.get("name") or card["card_name"])
                totals[key] = totals.get(key, 0) + int(card["quantity"])
            checks["over_copy_limit"] = [
                {"card_name": name, "quantity": quantity, "limit": limit}
                for name, quantity in totals.items() if quantity > limit
            ]
            if checks["over_copy_limit"]:
                reasons.append("CANDIDATE_COPY_LIMIT_EXCEEDED")
    for card in resolved_cards:
        if card["status"] != "resolved":
            checks["card_legality"]["unknown"] += 1
            continue
        try:
            verdict = check_card(db_path=Path(connection.execute("PRAGMA database_list").fetchone()[2]),
                                 tcgdex_id=card["tcgdex_id"], format=format, platform=platform, as_of=as_of)
            state = verdict.get("status", "unknown")
        except (ValueError, sqlite3.DatabaseError):
            state = "unknown"
        checks["card_legality"][state if state in checks["card_legality"] else "unknown"] += 1
        if state == "not_legal":
            reasons.append("CANDIDATE_CONTAINS_NOT_LEGAL_CARD")
    validation = {
        "checks": checks,
        "reason_codes": list(dict.fromkeys(reasons)),
        "structure_rule": (
            {key: rule[key] for key in ("rule_id", "source_id", "url", "published_date")}
            if rule else None
        ),
        "normative_structure_complete": normative_complete,
        "ownership": "unknown",
        "craft_cost": "unknown",
        "live_availability": "unknown",
    }
    if reasons:
        return "REJECTED_STRUCTURE", validation, resolved_cards
    all_legal = checks["card_legality"]["legal"] == len(cards)
    if not unresolved and not category_unknown and normative_complete and all_legal:
        return "READY_FOR_REVIEW", validation, resolved_cards
    validation["reason_codes"].append("LEGALITY_OR_COVERAGE_INCOMPLETE")
    return "UNKNOWN_LEGALITY", validation, resolved_cards


def create_candidate(db_path: Path, changes_path: Path, *, apply: bool = False, confirm_owner: bool = False) -> dict[str, Any]:
    request = _read_changes(changes_path)
    if apply and not confirm_owner:
        raise ValueError("--apply exige --confirm-owner pour enregistrer un candidat.")
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente; importer d'abord le deck de base.")
    connection = connect_writable(db_path) if apply else connect_readonly(db_path)
    try:
        if apply:
            initialize_schema(connection)
        base_version_id, base_cards = _load_base(connection, request["base_deck"]["deck_id"], request["base_deck"]["version"])
        candidate_cards = _apply_changes(base_cards, request["changes"])
        status, validation, resolved_cards = _validate_candidate(
            connection, candidate_cards, format=request["context"]["format"],
            platform=request["context"]["platform"], as_of=request["context"]["as_of"],
        )
        canonical_cards = sorted(
            [[card["card_type"], card["card_name"], card["set_code"], card["collector_number"], card["quantity"]] for card in resolved_cards],
            key=lambda row: tuple(str(value) for value in row),
        )
        list_sha = hashlib.sha256(json.dumps(canonical_cards, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
        result = {
            "mode": "applied" if apply else "dry_run", "read_only": not apply, "network_used": False,
            "candidate_id": None, "name": request["name"], "base_deck": request["base_deck"],
            "context": request["context"], "source": {"kind": "owner_controlled_changes", "name": request["source_name"]},
            "change_sha256": request["change_sha256"], "list_sha256": list_sha,
            "status": status, "validation": validation,
            "cards": [
                {key: card.get(key) for key in ("card_type", "quantity", "card_name", "set_code", "collector_number", "tcgdex_id", "status")}
                for card in resolved_cards
            ],
            "distinct_from_played_version": True,
            "deck_version_created": False,
            "credits_spent": 0,
        }
        if not apply:
            return result
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute(
            "SELECT id FROM deck_candidates WHERE base_version_id = ? AND change_sha256 = ?",
            (base_version_id, request["change_sha256"]),
        ).fetchone()
        if existing:
            connection.rollback()
            return {**result, "candidate_id": int(existing["id"]), "duplicate": True}
        cursor = connection.execute(
            """INSERT INTO deck_candidates
               (name, created_at, base_deck_id, base_version_id, format, platform, as_of,
                source_kind, change_sha256, list_sha256, validation_status, validation_json,
                lifecycle_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'owner_controlled_changes', ?, ?, ?, ?, 'active')""",
            (request["name"], utc_now(), request["base_deck"]["deck_id"], base_version_id,
             request["context"]["format"], request["context"]["platform"], request["context"]["as_of"],
             request["change_sha256"], list_sha, status,
             json.dumps(validation, ensure_ascii=False, sort_keys=True)),
        )
        candidate_id = int(cursor.lastrowid)
        connection.executemany(
            """INSERT INTO deck_candidate_cards
               (candidate_id, ordinal, card_type, quantity, card_name, set_code,
                collector_number, tcgdex_id, identity_status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(candidate_id, ordinal, card["card_type"], card["quantity"], card["card_name"],
              card["set_code"], card["collector_number"], card["tcgdex_id"], card["status"])
             for ordinal, card in enumerate(resolved_cards, start=1)],
        )
        connection.commit()
        return {**result, "candidate_id": candidate_id, "duplicate": False}
    except Exception:
        if apply:
            connection.rollback()
        raise
    finally:
        connection.close()


def show_candidate(db_path: Path, candidate_id: int) -> dict[str, Any]:
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente.")
    connection = connect_readonly(db_path)
    try:
        if "deck_candidates" not in _tables(connection):
            raise ValueError("Candidats indisponibles; migration requise par une écriture explicite.")
        candidate = connection.execute("SELECT * FROM deck_candidates WHERE id = ?", (candidate_id,)).fetchone()
        if candidate is None:
            raise ValueError("Candidat introuvable.")
        cards = [dict(row) for row in connection.execute(
            "SELECT * FROM deck_candidate_cards WHERE candidate_id = ? ORDER BY ordinal", (candidate_id,)
        ).fetchall()]
        return {
            "candidate_id": candidate_id, "name": candidate["name"], "created_at": candidate["created_at"],
            "base_deck_id": candidate["base_deck_id"], "format": candidate["format"],
            "platform": candidate["platform"], "as_of": candidate["as_of"],
            "status": candidate["validation_status"], "lifecycle_status": candidate["lifecycle_status"],
            "validation": json.loads(candidate["validation_json"]), "cards": cards,
            "export_text_path": candidate["export_text_path"], "export_report_path": candidate["export_report_path"],
            "read_only": True, "network_used": False, "distinct_from_played_version": True,
        }
    finally:
        connection.close()


def _slug(value: str) -> str:
    text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").casefold()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")[:48] or "candidate"


def export_candidate(
    db_path: Path, candidate_id: int, private_decks_root: Path, *,
    apply: bool = False, confirm_owner: bool = False,
) -> dict[str, Any]:
    candidate = show_candidate(db_path, candidate_id)
    if candidate["status"] in {"REJECTED_INVALID_60", "REJECTED_STRUCTURE"}:
        raise ValueError("Un candidat rejeté ne peut pas être exporté.")
    cards = tuple(
        DeckCard(index, index, row["card_type"], int(row["quantity"]), row["card_name"],
                 row["set_code"], row["collector_number"], "")
        for index, row in enumerate(candidate["cards"], start=1)
    )
    cards = tuple(
        DeckCard(card.ordinal, card.source_line, card.card_type, card.quantity, card.name,
                 card.set_code, card.collector_number,
                 f"{card.quantity} {card.name} {card.set_code} {card.collector_number}")
        for card in cards
    )
    text = serialize_deck(cards)
    ready = candidate["status"] == "READY_FOR_REVIEW"
    directory = private_decks_root.resolve() / ("import_ready" if ready else "drafts")
    stem = f"candidate-{candidate_id}-{_slug(candidate['name'])}"
    text_path = directory / f"{stem}.txt"
    report_path = directory / f"{stem}.json"
    report = {
        "candidate_id": candidate_id, "status": candidate["status"],
        "format": candidate["format"], "platform": candidate["platform"], "as_of": candidate["as_of"],
        "total_cards": 60, "distinct_from_played_version": True, "deck_version_created": False,
        "transmitted_to_game": False, "credits_spent": 0,
        "warnings": [
            "Export local volontaire seulement; aucune transmission à Pokémon TCG Live.",
            "Possession, crédits, fabrication et support Live restent indépendants.",
        ],
    }
    result = {
        **report, "mode": "applied" if apply else "dry_run", "read_only": not apply,
        "network_used": False, "text_path": str(text_path), "report_path": str(report_path),
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }
    if not apply:
        return result
    if not confirm_owner:
        raise ValueError("--apply exige --confirm-owner pour exporter un candidat.")
    if candidate["lifecycle_status"] == "exported":
        return {**result, "duplicate": True, "text_path": candidate["export_text_path"], "report_path": candidate["export_report_path"]}
    created: list[Path] = []
    try:
        _atomic_write_new(text_path, text.encode("utf-8"))
        created.append(text_path)
        _atomic_write_new(report_path, (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        created.append(report_path)
        connection = connect_writable(db_path)
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """UPDATE deck_candidates SET lifecycle_status='exported', exported_at=?,
                          export_text_path=?, export_report_path=?
                   WHERE id=? AND lifecycle_status='active'""",
                (utc_now(), str(text_path), str(report_path), candidate_id),
            )
            connection.commit()
        finally:
            connection.close()
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return {**result, "duplicate": False}
