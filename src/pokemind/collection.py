"""Collection et crédits déclarés volontairement, versionnés localement."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from calendar import monthcalendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from pokemind.database import SCHEMA_VERSION, connect_readonly, connect_writable, initialize_schema, utc_now


COLLECTION_SCHEMA_VERSION = 1
MAX_COLLECTION_BYTES = 2_000_000
_SAFE_TEXT = re.compile(r"^[^\x00-\x1f\x7f]{1,200}$")
_SAFE_CODE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$")
_SAFE_NUMBER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9/._-]{0,31}$")
_OWNERSHIP = {"confirmed_owned", "reported_missing", "unknown"}


@dataclass(frozen=True, slots=True)
class CollectionEntry:
    ordinal: int
    name: str
    set_code: str
    collector_number: str
    variant: str
    quantity: int
    ownership_status: str
    supplied_tcgdex_id: str | None


def _normalized(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def _strict_date(value: Any, field: str, *, allow_future: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} doit être une date YYYY-MM-DD.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} doit être une date YYYY-MM-DD valide.") from exc
    if not allow_future and parsed > date.today():
        raise ValueError(f"{field} ne peut pas être dans le futur.")
    return parsed.isoformat()


def _text(value: Any, field: str, pattern: re.Pattern[str] = _SAFE_TEXT) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} doit être du texte.")
    cleaned = unicodedata.normalize("NFC", value).strip()
    if not pattern.fullmatch(cleaned):
        raise ValueError(f"{field} est invalide.")
    return cleaned


def _tables(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")
    }


def _read_collection(path: Path) -> tuple[str, str, tuple[CollectionEntry, ...]]:
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"Fichier de collection absent: {resolved}")
    raw = resolved.read_bytes()
    if len(raw) > MAX_COLLECTION_BYTES:
        raise ValueError(f"Collection trop volumineuse (maximum {MAX_COLLECTION_BYTES} octets).")
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("La collection doit être un JSON UTF-8 valide.") from exc
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "as_of", "source", "entries"}:
        raise ValueError("Collection JSON: champs requis exacts schema_version, as_of, source, entries.")
    if payload["schema_version"] != COLLECTION_SCHEMA_VERSION:
        raise ValueError(f"schema_version doit valoir {COLLECTION_SCHEMA_VERSION}.")
    as_of = _strict_date(payload["as_of"], "as_of")
    source = payload["source"]
    if not isinstance(source, dict) or set(source) != {"kind"} or source["kind"] != "owner_provided":
        raise ValueError("source.kind doit valoir owner_provided, sans autre champ.")
    rows = payload["entries"]
    if not isinstance(rows, list) or len(rows) > 100_000:
        raise ValueError("entries doit être une liste bornée.")
    entries: list[CollectionEntry] = []
    identities: set[tuple[str, str, str, str]] = set()
    allowed = {
        "name", "set_code", "collector_number", "variant", "quantity",
        "ownership_status", "tcgdex_id",
    }
    required = allowed - {"tcgdex_id"}
    for ordinal, row in enumerate(rows, start=1):
        if not isinstance(row, dict) or not required.issubset(row) or set(row) - allowed:
            raise ValueError(f"Entrée {ordinal}: champs manquants ou inconnus.")
        name = _text(row["name"], f"Entrée {ordinal}: name")
        set_code = _text(row["set_code"], f"Entrée {ordinal}: set_code", _SAFE_CODE)
        number = _text(row["collector_number"], f"Entrée {ordinal}: collector_number", _SAFE_NUMBER)
        variant = _text(row["variant"], f"Entrée {ordinal}: variant")
        quantity = row["quantity"]
        if isinstance(quantity, bool) or not isinstance(quantity, int) or not 0 <= quantity <= 9999:
            raise ValueError(f"Entrée {ordinal}: quantity doit être un entier entre 0 et 9999.")
        ownership = row["ownership_status"]
        if ownership not in _OWNERSHIP:
            raise ValueError(f"Entrée {ordinal}: ownership_status invalide.")
        if ownership == "confirmed_owned" and quantity < 1:
            raise ValueError(f"Entrée {ordinal}: confirmed_owned exige quantity >= 1.")
        if ownership == "reported_missing" and quantity != 0:
            raise ValueError(f"Entrée {ordinal}: reported_missing exige quantity = 0.")
        supplied = row.get("tcgdex_id")
        supplied_id = _text(supplied, f"Entrée {ordinal}: tcgdex_id") if supplied is not None else None
        identity = (_normalized(name), set_code.casefold(), number.casefold(), variant.casefold())
        if identity in identities:
            raise ValueError(f"Entrée {ordinal}: impression/variant en double.")
        identities.add(identity)
        entries.append(CollectionEntry(ordinal, name, set_code, number, variant, quantity, ownership, supplied_id))
    canonical = {
        "schema_version": COLLECTION_SCHEMA_VERSION,
        "as_of": as_of,
        "source": {"kind": "owner_provided"},
        "entries": [
            {
                "name": item.name,
                "set_code": item.set_code,
                "collector_number": item.collector_number,
                "variant": item.variant,
                "quantity": item.quantity,
                "ownership_status": item.ownership_status,
                "tcgdex_id": item.supplied_tcgdex_id,
            }
            for item in entries
        ],
    }
    digest = hashlib.sha256(
        json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return as_of, digest, tuple(entries)


def _resolve_entry(connection: sqlite3.Connection, entry: CollectionEntry) -> dict[str, Any]:
    tables = _tables(connection)
    if not {"catalog_printings", "catalog_sets", "catalog_translations"}.issubset(tables):
        return {"status": "unknown", "tcgdex_id": None, "reason": "CATALOG_UNAVAILABLE"}
    parameters: list[Any] = []
    where = ""
    if entry.supplied_tcgdex_id:
        where = "p.tcgdex_id = ?"
        parameters.append(entry.supplied_tcgdex_id)
    else:
        where = "(s.tcg_online_code = ? COLLATE NOCASE OR s.tcgdex_id = ? COLLATE NOCASE) AND p.local_id = ? COLLATE NOCASE"
        parameters.extend((entry.set_code, entry.set_code, entry.collector_number))
    rows = connection.execute(
        f"""SELECT p.tcgdex_id, p.local_id, s.tcgdex_id AS set_id, s.tcg_online_code,
                    t.name, t.status
             FROM catalog_printings p
             LEFT JOIN catalog_sets s ON s.tcgdex_id = p.set_id
             LEFT JOIN catalog_translations t ON t.printing_id = p.tcgdex_id
             WHERE {where}""",
        tuple(parameters),
    ).fetchall()
    if not rows:
        return {"status": "unknown", "tcgdex_id": None, "reason": "PRINTING_NOT_IN_LOCAL_CATALOG"}
    expected_name = _normalized(entry.name)
    by_id: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        by_id.setdefault(str(row["tcgdex_id"]), []).append(row)
    matched: list[str] = []
    conflicts: list[str] = []
    for printing_id, candidates in by_id.items():
        first = candidates[0]
        code_matches = (
            str(first["set_id"] or "").casefold() == entry.set_code.casefold()
            or str(first["tcg_online_code"] or "").casefold() == entry.set_code.casefold()
        )
        number_matches = str(first["local_id"] or "").casefold() == entry.collector_number.casefold()
        names = {_normalized(str(row["name"])) for row in candidates if row["name"] and row["status"] == "present"}
        if code_matches and number_matches and expected_name in names:
            matched.append(printing_id)
        elif entry.supplied_tcgdex_id:
            conflicts.append(printing_id)
    if len(matched) == 1:
        return {"status": "resolved", "tcgdex_id": matched[0], "reason": "EXACT_LOCAL_IDENTITY"}
    if len(matched) > 1:
        return {"status": "ambiguous", "tcgdex_id": None, "reason": "MULTIPLE_LOCAL_IDENTITIES"}
    if conflicts:
        return {"status": "ambiguous", "tcgdex_id": None, "reason": "SUPPLIED_ID_CONFLICTS_WITH_FIELDS"}
    return {"status": "unknown", "tcgdex_id": None, "reason": "NAME_OR_TRANSLATION_NOT_VERIFIED"}


def _preview(connection: sqlite3.Connection | None, entries: tuple[CollectionEntry, ...]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for entry in entries:
        resolution = (
            _resolve_entry(connection, entry)
            if connection is not None
            else {"status": "unknown", "tcgdex_id": None, "reason": "CATALOG_UNAVAILABLE"}
        )
        results.append({
            "ordinal": entry.ordinal,
            "name": entry.name,
            "set_code": entry.set_code,
            "collector_number": entry.collector_number,
            "variant": entry.variant,
            "quantity": entry.quantity,
            "ownership_status": entry.ownership_status,
            "supplied_tcgdex_id": entry.supplied_tcgdex_id,
            "resolution_status": resolution["status"],
            "resolved_tcgdex_id": resolution["tcgdex_id"],
            "resolution_reason": resolution["reason"],
        })
    return results


def import_collection(
    db_path: Path,
    path: Path,
    *,
    apply: bool = False,
    confirm_owner: bool = False,
) -> dict[str, Any]:
    as_of, digest, entries = _read_collection(path)
    if apply and not confirm_owner:
        raise ValueError("--apply exige --confirm-owner pour une collection déclarée.")
    if not apply:
        connection = connect_readonly(db_path) if db_path.is_file() else None
        try:
            resolved = _preview(connection, entries)
            schema = int(connection.execute("PRAGMA user_version").fetchone()[0]) if connection else 0
        finally:
            if connection is not None:
                connection.close()
        return _collection_result(db_path, path, as_of, digest, resolved, applied=False, snapshot_id=None, schema=schema)

    connection = connect_writable(db_path)
    try:
        initialize_schema(connection)
        connection.execute("BEGIN IMMEDIATE")
        resolved = _preview(connection, entries)
        active = connection.execute(
            "SELECT id, content_sha256, as_of FROM collection_snapshots WHERE status = 'active'"
        ).fetchone()
        if active and active["content_sha256"] == digest and active["as_of"] == as_of:
            connection.rollback()
            result = _collection_result(
                db_path, path, as_of, digest, resolved, applied=True,
                snapshot_id=int(active["id"]), schema=SCHEMA_VERSION,
            )
            result["duplicate"] = True
            return result
        if active:
            connection.execute("UPDATE collection_snapshots SET status = 'superseded' WHERE id = ?", (active["id"],))
        counts = {key: sum(item["resolution_status"] == key for item in resolved) for key in ("resolved", "ambiguous", "unknown")}
        cursor = connection.execute(
            """INSERT INTO collection_snapshots
               (recorded_at, as_of, source_kind, source_name, content_sha256, status,
                supersedes_id, rollback_of_id, entry_count, total_quantity,
                resolved_count, ambiguous_count, unknown_count)
               VALUES (?, ?, 'owner_provided', ?, ?, 'active', ?, NULL, ?, ?, ?, ?, ?)""",
            (
                utc_now(), as_of, path.name, digest, int(active["id"]) if active else None,
                len(resolved), sum(item["quantity"] for item in resolved),
                counts["resolved"], counts["ambiguous"], counts["unknown"],
            ),
        )
        snapshot_id = int(cursor.lastrowid)
        connection.executemany(
            """INSERT INTO collection_items
               (snapshot_id, ordinal, supplied_tcgdex_id, resolved_tcgdex_id, card_name,
                set_code, collector_number, variant, quantity, ownership_status,
                resolution_status, resolution_reason)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (
                    snapshot_id, item["ordinal"], item["supplied_tcgdex_id"], item["resolved_tcgdex_id"],
                    item["name"], item["set_code"], item["collector_number"], item["variant"],
                    item["quantity"], item["ownership_status"], item["resolution_status"],
                    item["resolution_reason"],
                )
                for item in resolved
            ],
        )
        connection.commit()
        result = _collection_result(db_path, path, as_of, digest, resolved, applied=True, snapshot_id=snapshot_id, schema=SCHEMA_VERSION)
        result["duplicate"] = False
        return result
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _collection_result(
    db_path: Path, path: Path, as_of: str, digest: str, rows: list[dict[str, Any]],
    *, applied: bool, snapshot_id: int | None, schema: int,
) -> dict[str, Any]:
    counts = {key: sum(row["resolution_status"] == key for row in rows) for key in ("resolved", "ambiguous", "unknown")}
    return {
        "database": str(db_path),
        "mode": "applied" if applied else "dry_run",
        "read_only": not applied,
        "network_used": False,
        "source": {"kind": "owner_provided", "name": path.name, "as_of": as_of},
        "content_sha256": digest,
        "schema_version": schema,
        "schema_migration_required_on_apply": schema < SCHEMA_VERSION,
        "snapshot_id": snapshot_id,
        "entries": len(rows),
        "total_quantity": sum(row["quantity"] for row in rows),
        "resolution": {**counts, "denominator": len(rows)},
        "items": rows,
        "limits": [
            "Déclaration du propriétaire seulement; aucun accès au compte Pokémon.",
            "Une impression non résolue reste unknown et n'est jamais substituée par son seul nom.",
            "Les coûts de fabrication et crédits requis restent unknown faute de tarif sourcé.",
        ],
    }


def _recorded_local_date(value: Any) -> date | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    utc = parsed.astimezone(timezone.utc)
    # Règles nord-américaines modernes utilisées à Toronto depuis 2007.
    march_sundays = [week[6] for week in monthcalendar(utc.year, 3) if week[6]]
    november_sundays = [week[6] for week in monthcalendar(utc.year, 11) if week[6]]
    dst_start = datetime(utc.year, 3, march_sundays[1], 7, tzinfo=timezone.utc)
    dst_end = datetime(utc.year, 11, november_sundays[0], 6, tzinfo=timezone.utc)
    offset = timedelta(hours=-4 if dst_start <= utc < dst_end else -5)
    return (utc + offset).date()


def _snapshot_at_date(rows: list[dict[str, Any]], as_of: str | None) -> dict[str, Any] | None:
    if as_of is None:
        return next((row for row in rows if row["status"] == "active"), None)
    cutoff = date.fromisoformat(_strict_date(as_of, "as_of"))
    eligible = []
    for row in rows:
        try:
            observed = date.fromisoformat(str(row["as_of"]))
        except (TypeError, ValueError):
            continue
        recorded = _recorded_local_date(row.get("recorded_at"))
        if recorded is not None and observed <= cutoff and recorded <= cutoff:
            eligible.append(row)
    return max(eligible, key=lambda row: (str(row["recorded_at"]), int(row["id"])), default=None)


def collection_status(db_path: Path, *, as_of: str | None = None) -> dict[str, Any]:
    if as_of is not None:
        as_of = _strict_date(as_of, "as_of")
    base = {
        "database": str(db_path), "read_only": True, "network_used": False,
        "available": False, "active": None, "history": [], "requested_as_of": as_of,
        "availability_status": "NOT_AVAILABLE_AS_OF" if as_of else "NOT_AVAILABLE",
    }
    if not db_path.is_file():
        return base
    connection = connect_readonly(db_path)
    try:
        schema = int(connection.execute("PRAGMA user_version").fetchone()[0])
        base["schema_version"] = schema
        if "collection_snapshots" not in _tables(connection):
            base["reason"] = "SCHEMA_MIGRATION_REQUIRED"
            return base
        rows = connection.execute(
            """SELECT id, recorded_at, as_of, source_kind, source_name, status,
                      entry_count, total_quantity, resolved_count, ambiguous_count, unknown_count,
                      supersedes_id, rollback_of_id
               FROM collection_snapshots ORDER BY id DESC"""
        ).fetchall()
        history = [dict(row) for row in rows]
        base["history"] = history
        base["active"] = _snapshot_at_date(history, as_of)
        base["available"] = base["active"] is not None
        base["availability_status"] = "AVAILABLE_AS_OF" if as_of and base["available"] else (
            "AVAILABLE" if base["available"] else base["availability_status"]
        )
        base["ownership_provenance"] = "owner_provided" if base["available"] else "unknown"
        return base
    finally:
        connection.close()


def collection_coverage(db_path: Path, *, as_of: str | None = None) -> dict[str, Any]:
    status = collection_status(db_path, as_of=as_of)
    active = status.get("active")
    if not active:
        return {**status, "coverage": {"resolved": 0, "ambiguous": 0, "unknown": 0, "denominator": 0, "ratio": None}}
    denominator = int(active["entry_count"])
    return {
        **status,
        "coverage": {
            "resolved": int(active["resolved_count"]),
            "ambiguous": int(active["ambiguous_count"]),
            "unknown": int(active["unknown_count"]),
            "denominator": denominator,
            "ratio": round(int(active["resolved_count"]) / denominator, 6) if denominator else None,
        },
    }


def rollback_collection(db_path: Path, snapshot_id: int, *, apply: bool = False, confirm_owner: bool = False) -> dict[str, Any]:
    if snapshot_id < 1:
        raise ValueError("snapshot doit être un entier positif.")
    if apply and not confirm_owner:
        raise ValueError("--apply exige --confirm-owner pour restaurer une collection.")
    connection = connect_writable(db_path) if apply else connect_readonly(db_path)
    try:
        if apply:
            initialize_schema(connection)
        if "collection_snapshots" not in _tables(connection):
            raise ValueError("Historique de collection indisponible; migration requise à l'application.")
        target = connection.execute("SELECT * FROM collection_snapshots WHERE id = ?", (snapshot_id,)).fetchone()
        if target is None:
            raise ValueError("Instantané de collection introuvable.")
        items = connection.execute("SELECT * FROM collection_items WHERE snapshot_id = ? ORDER BY ordinal", (snapshot_id,)).fetchall()
        preview = {
            "mode": "applied" if apply else "dry_run", "read_only": not apply, "network_used": False,
            "target_snapshot_id": snapshot_id, "target_as_of": target["as_of"], "entries": len(items),
        }
        if not apply:
            return preview
        connection.execute("BEGIN IMMEDIATE")
        active = connection.execute("SELECT id FROM collection_snapshots WHERE status = 'active'").fetchone()
        if active and int(active["id"]) == snapshot_id:
            connection.rollback()
            return {**preview, "snapshot_id": snapshot_id, "duplicate": True}
        if active:
            connection.execute("UPDATE collection_snapshots SET status = 'superseded' WHERE id = ?", (active["id"],))
        cursor = connection.execute(
            """INSERT INTO collection_snapshots
               (recorded_at, as_of, source_kind, source_name, content_sha256, status,
                supersedes_id, rollback_of_id, entry_count, total_quantity,
                resolved_count, ambiguous_count, unknown_count)
               VALUES (?, ?, 'owner_rollback', NULL, ?, 'active', ?, ?, ?, ?, ?, ?, ?)""",
            (utc_now(), target["as_of"], target["content_sha256"], int(active["id"]) if active else None,
             snapshot_id, target["entry_count"], target["total_quantity"], target["resolved_count"],
             target["ambiguous_count"], target["unknown_count"]),
        )
        new_id = int(cursor.lastrowid)
        connection.executemany(
            """INSERT INTO collection_items
               (snapshot_id, ordinal, supplied_tcgdex_id, resolved_tcgdex_id, card_name,
                set_code, collector_number, variant, quantity, ownership_status,
                resolution_status, resolution_reason)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(new_id, row["ordinal"], row["supplied_tcgdex_id"], row["resolved_tcgdex_id"], row["card_name"],
              row["set_code"], row["collector_number"], row["variant"], row["quantity"],
              row["ownership_status"], row["resolution_status"], row["resolution_reason"]) for row in items],
        )
        connection.commit()
        return {**preview, "snapshot_id": new_id, "duplicate": False}
    except Exception:
        if apply:
            connection.rollback()
        raise
    finally:
        connection.close()


def collection_missing(db_path: Path, deck_id: str, *, as_of: str | None = None) -> dict[str, Any]:
    if as_of is not None:
        as_of = _strict_date(as_of, "as_of")
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente.")
    connection = connect_readonly(db_path)
    try:
        tables = _tables(connection)
        version = connection.execute(
            "SELECT id, version_number FROM deck_versions WHERE deck_id = ? ORDER BY version_number DESC LIMIT 1",
            (deck_id,),
        ).fetchone() if "deck_versions" in tables else None
        if version is None:
            raise ValueError(f"Deck exact inconnu: {deck_id}.")
        cards = connection.execute(
            """SELECT card_type, quantity, card_name, set_code, collector_number
               FROM deck_version_cards WHERE deck_version_id = ? ORDER BY ordinal""",
            (version["id"],),
        ).fetchall()
        active = collection_status(db_path, as_of=as_of).get("active")
        if active is None:
            return {
                "deck_id": deck_id, "deck_version": int(version["version_number"]),
                "collection_status": "unknown", "as_of": None,
                "availability_status": "NOT_AVAILABLE_AS_OF" if as_of else "NOT_AVAILABLE",
                "lines": [
                    {"name": row["card_name"], "set_code": row["set_code"],
                     "collector_number": row["collector_number"], "required": int(row["quantity"]),
                     "ownership_status": "unknown", "missing_quantity": None, "craft_cost": "unknown"}
                    for row in cards
                ],
                "network_used": False, "read_only": True,
            }
        owned_rows = connection.execute(
            "SELECT * FROM collection_items WHERE snapshot_id = ?", (active["id"],)
        ).fetchall()
        exact: dict[tuple[str, str, str], list[sqlite3.Row]] = {}
        for item in owned_rows:
            key = (_normalized(str(item["card_name"])), str(item["set_code"]).casefold(), str(item["collector_number"]).casefold())
            exact.setdefault(key, []).append(item)
        lines: list[dict[str, Any]] = []
        for row in cards:
            key = (_normalized(str(row["card_name"])), str(row["set_code"] or "").casefold(), str(row["collector_number"] or "").casefold())
            matches = exact.get(key, [])
            confirmed = sum(int(item["quantity"]) for item in matches if item["ownership_status"] == "confirmed_owned")
            known_missing = any(item["ownership_status"] == "reported_missing" for item in matches)
            known = bool(matches) and all(item["ownership_status"] != "unknown" for item in matches)
            required = int(row["quantity"])
            ownership = "confirmed_owned" if confirmed >= required else ("reported_missing" if known_missing or known else "unknown")
            lines.append({
                "name": row["card_name"], "set_code": row["set_code"], "collector_number": row["collector_number"],
                "required": required, "confirmed_owned": confirmed if known else None,
                "ownership_status": ownership, "missing_quantity": max(0, required - confirmed) if known else None,
                "craft_cost": "unknown",
            })
        return {
            "deck_id": deck_id, "deck_version": int(version["version_number"]),
            "collection_status": "owner_provided", "as_of": active["as_of"], "lines": lines,
            "recorded_at": active["recorded_at"],
            "availability_status": "AVAILABLE_AS_OF" if as_of else "AVAILABLE",
            "known_missing_total": sum(item["missing_quantity"] or 0 for item in lines if item["missing_quantity"] is not None),
            "unknown_lines": sum(item["missing_quantity"] is None for item in lines),
            "network_used": False, "read_only": True,
            "limits": ["craft_cost=unknown faute de tarif officiel daté et sourcé."],
        }
    finally:
        connection.close()


def set_credits(
    db_path: Path, amount: int, *, as_of: str, apply: bool = False, confirm_owner: bool = False,
) -> dict[str, Any]:
    if isinstance(amount, bool) or not isinstance(amount, int) or not 0 <= amount <= 100_000_000:
        raise ValueError("amount doit être un entier entre 0 et 100000000.")
    as_of = _strict_date(as_of, "as_of")
    if apply and not confirm_owner:
        raise ValueError("--apply exige --confirm-owner pour enregistrer des crédits.")
    result = {
        "mode": "applied" if apply else "dry_run", "read_only": not apply,
        "network_used": False, "amount": amount, "as_of": as_of,
        "source": "owner_provided", "credits_spent": 0,
    }
    if not apply:
        return result
    connection = connect_writable(db_path)
    try:
        initialize_schema(connection)
        connection.execute("BEGIN IMMEDIATE")
        active = connection.execute("SELECT id, amount, as_of FROM credit_snapshots WHERE status = 'active'").fetchone()
        if active and int(active["amount"]) == amount and active["as_of"] == as_of:
            connection.rollback()
            return {**result, "snapshot_id": int(active["id"]), "duplicate": True}
        if active:
            connection.execute("UPDATE credit_snapshots SET status = 'superseded' WHERE id = ?", (active["id"],))
        cursor = connection.execute(
            """INSERT INTO credit_snapshots
               (recorded_at, as_of, amount, source_kind, status, supersedes_id, rollback_of_id)
               VALUES (?, ?, ?, 'owner_provided', 'active', ?, NULL)""",
            (utc_now(), as_of, amount, int(active["id"]) if active else None),
        )
        connection.commit()
        return {**result, "snapshot_id": int(cursor.lastrowid), "duplicate": False}
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def credits_status(db_path: Path, *, as_of: str | None = None) -> dict[str, Any]:
    if as_of is not None:
        as_of = _strict_date(as_of, "as_of")
    base = {"database": str(db_path), "read_only": True, "network_used": False,
            "available": False, "active": None, "history": [], "requested_as_of": as_of,
            "availability_status": "NOT_AVAILABLE_AS_OF" if as_of else "NOT_AVAILABLE"}
    if not db_path.is_file():
        return base
    connection = connect_readonly(db_path)
    try:
        if "credit_snapshots" not in _tables(connection):
            base["reason"] = "SCHEMA_MIGRATION_REQUIRED"
            return base
        rows = [dict(row) for row in connection.execute("SELECT * FROM credit_snapshots ORDER BY id DESC").fetchall()]
        base["history"] = rows
        base["active"] = _snapshot_at_date(rows, as_of)
        base["available"] = base["active"] is not None
        base["availability_status"] = "AVAILABLE_AS_OF" if as_of and base["available"] else (
            "AVAILABLE" if base["available"] else base["availability_status"]
        )
        base["source"] = "owner_provided" if base["available"] else "unknown"
        return base
    finally:
        connection.close()


def rollback_credits(db_path: Path, snapshot_id: int, *, apply: bool = False, confirm_owner: bool = False) -> dict[str, Any]:
    if snapshot_id < 1:
        raise ValueError("snapshot doit être un entier positif.")
    if apply and not confirm_owner:
        raise ValueError("--apply exige --confirm-owner pour restaurer les crédits.")
    connection = connect_writable(db_path) if apply else connect_readonly(db_path)
    try:
        if apply:
            initialize_schema(connection)
        if "credit_snapshots" not in _tables(connection):
            raise ValueError("Historique de crédits indisponible.")
        target = connection.execute("SELECT * FROM credit_snapshots WHERE id = ?", (snapshot_id,)).fetchone()
        if target is None:
            raise ValueError("Instantané de crédits introuvable.")
        result = {"mode": "applied" if apply else "dry_run", "read_only": not apply, "network_used": False,
                  "target_snapshot_id": snapshot_id, "amount": int(target["amount"]), "as_of": target["as_of"], "credits_spent": 0}
        if not apply:
            return result
        connection.execute("BEGIN IMMEDIATE")
        active = connection.execute("SELECT id FROM credit_snapshots WHERE status = 'active'").fetchone()
        if active and int(active["id"]) == snapshot_id:
            connection.rollback()
            return {**result, "snapshot_id": snapshot_id, "duplicate": True}
        if active:
            connection.execute("UPDATE credit_snapshots SET status = 'superseded' WHERE id = ?", (active["id"],))
        cursor = connection.execute(
            """INSERT INTO credit_snapshots
               (recorded_at, as_of, amount, source_kind, status, supersedes_id, rollback_of_id)
               VALUES (?, ?, ?, 'owner_rollback', 'active', ?, ?)""",
            (utc_now(), target["as_of"], target["amount"], int(active["id"]) if active else None, snapshot_id),
        )
        connection.commit()
        return {**result, "snapshot_id": int(cursor.lastrowid), "duplicate": False}
    except Exception:
        if apply:
            connection.rollback()
        raise
    finally:
        connection.close()
