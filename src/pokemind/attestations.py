"""Attestations locales, explicites et révocables combat-version."""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from pokemind.battle_logs import DECK_ID_RE
from pokemind.database import (
    SCHEMA_VERSION,
    connect_readonly,
    connect_writable,
    initialize_schema,
    utc_now,
)


ATTESTATION_TABLE = "battle_version_attestations"


def _positive_integer(value: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{label} doit être un entier local positif.")
    return value


def _validate_deck_id(deck_id: str) -> None:
    if not DECK_ID_RE.fullmatch(deck_id):
        raise ValueError(
            "Identifiant de deck invalide (1-64 caractères: lettres, chiffres, . _ -)."
        )


def _strict_date(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("--battle-date doit être une date ISO stricte YYYY-MM-DD.") from exc
    if parsed.isoformat() != value:
        raise ValueError("--battle-date doit être une date ISO stricte YYYY-MM-DD.")
    return value


def _tables(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }


def _base_result(
    deck_id: str,
    battle_id: int,
    version: int | None,
    *,
    operation: str,
) -> dict[str, Any]:
    return {
        "operation": operation,
        "local_only": True,
        "network_used": False,
        "deck_id": deck_id,
        "battle_id": battle_id,
        "version": version,
        "eligible": False,
        "status": "DATA_UNAVAILABLE",
        "applied": False,
        "idempotent": False,
        "source": "owner_asserted",
        "externally_verified": False,
        "confirmed_at": None,
        "revoked_at": None,
        "warnings": [
            "Identifiant de combat local seulement; ne pas le publier comme identifiant global.",
            "Une attestation propriétaire ne prouve ni légalité, ni possession, ni rendement prédictif.",
        ],
    }


def _active_attestation(
    connection: sqlite3.Connection, battle_id: int, tables: set[str]
) -> sqlite3.Row | None:
    if ATTESTATION_TABLE not in tables:
        return None
    return connection.execute(
        f"""SELECT id, battle_id, deck_version_id, confirmed_at, asserted_battle_date,
                   status, revoked_at
              FROM {ATTESTATION_TABLE}
             WHERE battle_id=? AND status='active'
             ORDER BY id DESC LIMIT 1""",
        (battle_id,),
    ).fetchone()


def _latest_attestation(
    connection: sqlite3.Connection, battle_id: int, tables: set[str]
) -> sqlite3.Row | None:
    if ATTESTATION_TABLE not in tables:
        return None
    return connection.execute(
        f"""SELECT id, battle_id, deck_version_id, confirmed_at, asserted_battle_date,
                   status, revoked_at
              FROM {ATTESTATION_TABLE}
             WHERE battle_id=? ORDER BY id DESC LIMIT 1""",
        (battle_id,),
    ).fetchone()


def _inspect_confirmation(
    connection: sqlite3.Connection,
    deck_id: str,
    battle_id: int,
    version: int,
    *,
    battle_date: str | None,
) -> dict[str, Any]:
    result = _base_result(
        deck_id, battle_id, version, operation="confirm_battle_version"
    )
    tables = _tables(connection)
    required = {"battle_logs", "deck_versions", "deck_version_cards", "battle_deck_versions"}
    if not required.issubset(tables):
        result["status"] = "SCHEMA_UNSUPPORTED"
        return result

    battle = connection.execute(
        "SELECT id, imported_at, valid, deck_id FROM battle_logs WHERE id=?",
        (battle_id,),
    ).fetchone()
    if battle is None:
        result["status"] = "BATTLE_NOT_FOUND"
        return result
    result["battle"] = {
        "local_id": battle_id,
        "imported_date": str(battle["imported_at"] or "")[:10] or None,
        "valid": bool(battle["valid"]),
        "declared_deck_matches": str(battle["deck_id"] or "") == deck_id,
        "asserted_battle_date": battle_date,
    }
    if not bool(battle["valid"]):
        result["status"] = "BATTLE_INVALID"
        return result
    if str(battle["deck_id"] or "") != deck_id:
        result["status"] = "BATTLE_DECK_MISMATCH"
        return result

    deck_version = connection.execute(
        """SELECT id, exact_confirmed, total_cards, entry_count, effective_from,
                  approved_at
             FROM deck_versions WHERE deck_id=? AND version_number=?""",
        (deck_id, version),
    ).fetchone()
    if deck_version is None:
        result["status"] = "VERSION_NOT_FOUND"
        return result
    quantity = connection.execute(
        """SELECT COALESCE(SUM(quantity), 0), COUNT(*)
             FROM deck_version_cards WHERE deck_version_id=?""",
        (deck_version["id"],),
    ).fetchone()
    quantity_sum = int(quantity[0])
    row_count = int(quantity[1])
    version_valid = (
        bool(deck_version["exact_confirmed"])
        and int(deck_version["total_cards"]) == 60
        and quantity_sum == 60
        and int(deck_version["entry_count"]) == row_count
        and row_count > 0
    )
    result["deck_version"] = {
        "number": version,
        "exact_confirmed": bool(deck_version["exact_confirmed"]),
        "recorded_total": int(deck_version["total_cards"]),
        "quantity_sum": quantity_sum,
        "entry_count_consistent": int(deck_version["entry_count"]) == row_count,
    }
    if not version_valid:
        result["status"] = "VERSION_NOT_EXACT_60"
        return result

    current_link = connection.execute(
        "SELECT deck_version_id FROM battle_deck_versions WHERE battle_id=?",
        (battle_id,),
    ).fetchone()
    active = _active_attestation(connection, battle_id, tables)
    target_id = int(deck_version["id"])
    if active is not None:
        if int(active["deck_version_id"]) == target_id and current_link is not None and int(
            current_link["deck_version_id"]
        ) == target_id:
            result.update(
                status="OWNER_ATTESTATION_ALREADY_ACTIVE",
                eligible=True,
                idempotent=True,
                confirmed_at=active["confirmed_at"],
            )
            return result
        result["status"] = "ACTIVE_ATTESTATION_CONFLICT"
        return result
    if current_link is not None:
        result["status"] = (
            "LEGACY_LINK_UNATTESTED"
            if int(current_link["deck_version_id"]) == target_id
            else "EXISTING_LINK_CONFLICT"
        )
        return result

    result.update(
        status="READY_FOR_OWNER_CONFIRMATION",
        eligible=True,
        consequences={
            "single_pair_only": True,
            "create_active_link": True,
            "append_audit_attestation": True,
            "confirmed_at": "current_utc_when_applied",
            "historical_results_before_confirmation": "not_attributed",
            "battle_date": battle_date or "unknown",
        },
    )
    return result


def list_link_candidates(db_path: Path, deck_id: str) -> dict[str, Any]:
    """Liste des combats locaux non liés sans révéler journal, adversaire ou cartes."""
    _validate_deck_id(deck_id)
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente; aucun fichier n'a été créé.")
    connection = connect_readonly(db_path)
    try:
        connection.execute("PRAGMA query_only = ON")
        tables = _tables(connection)
        if not {"battle_logs", "battle_deck_versions"}.issubset(tables):
            raise ValueError("Le schéma local ne contient pas les combats requis.")
        has_attestations = ATTESTATION_TABLE in tables
        attestation_join = (
            "LEFT JOIN battle_version_attestations a "
            "ON a.battle_id=b.id AND a.status='active'"
            if has_attestations
            else ""
        )
        active_column = "a.id AS active_attestation_id" if has_attestations else "NULL AS active_attestation_id"
        latest_status_column = (
            "(SELECT h.status FROM battle_version_attestations h "
            "WHERE h.battle_id=b.id ORDER BY h.id DESC LIMIT 1) AS latest_attestation_status"
            if has_attestations
            else "NULL AS latest_attestation_status"
        )
        rows = connection.execute(
            f"""SELECT b.id, b.imported_at, b.outcome, link.deck_version_id,
                       {active_column}, {latest_status_column}
                  FROM battle_logs b
                  LEFT JOIN battle_deck_versions link ON link.battle_id=b.id
                  {attestation_join}
                 WHERE b.deck_id=? AND b.valid=1
                 ORDER BY b.imported_at, b.id""",
            (deck_id,),
        ).fetchall()
        candidates = [
            {
                "battle_id": int(row["id"]),
                "imported_date": str(row["imported_at"] or "")[:10] or None,
                "outcome": str(row["outcome"] or "inconnue"),
                "state": (
                    "owner_attested_revoked"
                    if row["latest_attestation_status"] == "revoked"
                    else "unlinked"
                ),
                "battle_date": "unknown",
            }
            for row in rows
            if row["deck_version_id"] is None and row["active_attestation_id"] is None
        ]
        return {
            "local_only": True,
            "read_only": True,
            "network_used": False,
            "deck_id": deck_id,
            "count": len(candidates),
            "candidates": candidates,
            "warning": "Les battle_id sont des clés SQLite locales, jamais des identifiants publics.",
        }
    finally:
        connection.close()


def confirm_battle_version(
    db_path: Path,
    deck_id: str,
    battle_id: int,
    version: int,
    *,
    apply: bool = False,
    confirm_owner: bool = False,
    battle_date: str | None = None,
) -> dict[str, Any]:
    """Prévisualise ou applique une confirmation propriétaire à une seule paire."""
    _validate_deck_id(deck_id)
    _positive_integer(battle_id, "--battle-id")
    _positive_integer(version, "--version")
    battle_date = _strict_date(battle_date)
    if apply and not confirm_owner:
        raise ValueError("--apply exige --confirm-owner pour cette paire unique.")
    if confirm_owner and not apply:
        raise ValueError("--confirm-owner n'est accepté qu'avec --apply.")
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente; aucun fichier n'a été créé.")

    preview_connection = connect_readonly(db_path)
    try:
        preview_connection.execute("PRAGMA query_only = ON")
        preview = _inspect_confirmation(
            preview_connection, deck_id, battle_id, version, battle_date=battle_date
        )
        preview["dry_run"] = not apply
        preview["schema_version"] = int(
            preview_connection.execute("PRAGMA user_version").fetchone()[0]
        )
    finally:
        preview_connection.close()
    if not apply:
        return preview
    if not preview["eligible"]:
        raise ValueError(f"Confirmation refusée: {preview['status']}.")
    if preview["idempotent"]:
        preview["dry_run"] = False
        return preview

    connection = connect_writable(db_path)
    try:
        initialize_schema(connection)
        connection.execute("BEGIN IMMEDIATE")
        try:
            checked = _inspect_confirmation(
                connection, deck_id, battle_id, version, battle_date=battle_date
            )
            if checked["idempotent"]:
                connection.rollback()
                checked.update(dry_run=False, schema_version=SCHEMA_VERSION)
                return checked
            if not checked["eligible"]:
                raise ValueError(f"Confirmation refusée: {checked['status']}.")
            deck_version = connection.execute(
                """SELECT id, effective_from, approved_at FROM deck_versions
                   WHERE deck_id=? AND version_number=?""",
                (deck_id, version),
            ).fetchone()
            assert deck_version is not None
            confirmed_at = utc_now()
            connection.execute(
                """INSERT INTO battle_deck_versions
                   (battle_id, deck_version_id, effective_from, approved_at)
                   VALUES (?, ?, ?, ?)""",
                (
                    battle_id,
                    int(deck_version["id"]),
                    deck_version["effective_from"],
                    deck_version["approved_at"],
                ),
            )
            connection.execute(
                """INSERT INTO battle_version_attestations
                   (battle_id, deck_version_id, confirmed_at, actor, provenance,
                    asserted_battle_date, battle_date_source, battle_date_reliability,
                    status, revoked_at, reason, revocation_reason)
                   VALUES (?, ?, ?, 'owner_explicit_confirmation', 'owner_asserted',
                           ?, ?, ?, 'active', NULL,
                           'manual_single_pair_confirmation', NULL)""",
                (
                    battle_id,
                    int(deck_version["id"]),
                    confirmed_at,
                    battle_date,
                    "owner_declared" if battle_date else "unknown",
                    "owner_asserted" if battle_date else "unknown",
                ),
            )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        checked.update(
            status="OWNER_ATTESTATION_ACTIVE",
            applied=True,
            idempotent=False,
            dry_run=False,
            confirmed_at=confirmed_at,
            schema_version=SCHEMA_VERSION,
        )
        return checked
    except sqlite3.IntegrityError as exc:
        raise ValueError("Confirmation refusée: conflit transactionnel.") from exc
    finally:
        connection.close()


def _inspect_revocation(
    connection: sqlite3.Connection, deck_id: str, battle_id: int
) -> dict[str, Any]:
    result = _base_result(deck_id, battle_id, None, operation="revoke_battle_version")
    tables = _tables(connection)
    if not {"battle_logs", "battle_deck_versions"}.issubset(tables):
        result["status"] = "SCHEMA_UNSUPPORTED"
        return result
    battle = connection.execute(
        "SELECT valid, deck_id FROM battle_logs WHERE id=?", (battle_id,)
    ).fetchone()
    if battle is None:
        result["status"] = "BATTLE_NOT_FOUND"
        return result
    if str(battle["deck_id"] or "") != deck_id:
        result["status"] = "BATTLE_DECK_MISMATCH"
        return result
    active = _active_attestation(connection, battle_id, tables)
    current_link = connection.execute(
        "SELECT deck_version_id FROM battle_deck_versions WHERE battle_id=?",
        (battle_id,),
    ).fetchone()
    if active is None:
        latest = _latest_attestation(connection, battle_id, tables)
        if latest is not None and str(latest["status"]) == "revoked" and current_link is None:
            result.update(
                status="OWNER_ATTESTATION_ALREADY_REVOKED",
                eligible=True,
                idempotent=True,
                confirmed_at=latest["confirmed_at"],
                revoked_at=latest["revoked_at"],
            )
        elif current_link is not None:
            result["status"] = "LEGACY_LINK_UNATTESTED"
        else:
            result["status"] = "NO_ACTIVE_OWNER_ATTESTATION"
        return result
    if current_link is None or int(current_link["deck_version_id"]) != int(
        active["deck_version_id"]
    ):
        result["status"] = "ACTIVE_ATTESTATION_LINK_CONFLICT"
        return result
    result.update(
        status="READY_FOR_OWNER_REVOCATION",
        eligible=True,
        version=None,
        confirmed_at=active["confirmed_at"],
        consequences={
            "single_pair_only": True,
            "remove_active_link": True,
            "preserve_revoked_audit_row": True,
            "revoked_at": "current_utc_when_applied",
        },
    )
    result["attestation_id"] = int(active["id"])
    return result


def revoke_battle_version(
    db_path: Path,
    deck_id: str,
    battle_id: int,
    *,
    apply: bool = False,
    confirm_owner: bool = False,
) -> dict[str, Any]:
    """Prévisualise ou applique la révocation d'une attestation créée ici."""
    _validate_deck_id(deck_id)
    _positive_integer(battle_id, "--battle-id")
    if apply and not confirm_owner:
        raise ValueError("--apply exige --confirm-owner pour cette paire unique.")
    if confirm_owner and not apply:
        raise ValueError("--confirm-owner n'est accepté qu'avec --apply.")
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente; aucun fichier n'a été créé.")
    preview_connection = connect_readonly(db_path)
    try:
        preview_connection.execute("PRAGMA query_only = ON")
        preview = _inspect_revocation(preview_connection, deck_id, battle_id)
        preview["dry_run"] = not apply
        preview["schema_version"] = int(
            preview_connection.execute("PRAGMA user_version").fetchone()[0]
        )
    finally:
        preview_connection.close()
    if not apply:
        preview.pop("attestation_id", None)
        return preview
    if not preview["eligible"]:
        raise ValueError(f"Révocation refusée: {preview['status']}.")
    if preview["idempotent"]:
        preview["dry_run"] = False
        return preview

    connection = connect_writable(db_path)
    try:
        connection.execute("BEGIN IMMEDIATE")
        try:
            checked = _inspect_revocation(connection, deck_id, battle_id)
            if checked["idempotent"]:
                connection.rollback()
                checked.pop("attestation_id", None)
                checked.update(dry_run=False, schema_version=SCHEMA_VERSION)
                return checked
            if not checked["eligible"]:
                raise ValueError(f"Révocation refusée: {checked['status']}.")
            revoked_at = utc_now()
            attestation_id = int(checked.pop("attestation_id"))
            updated = connection.execute(
                """UPDATE battle_version_attestations
                      SET status='revoked', revoked_at=?,
                          revocation_reason='owner_explicit_revocation'
                    WHERE id=? AND status='active'""",
                (revoked_at, attestation_id),
            ).rowcount
            deleted = connection.execute(
                """DELETE FROM battle_deck_versions
                    WHERE battle_id=? AND deck_version_id=(
                        SELECT deck_version_id FROM battle_version_attestations WHERE id=?
                    )""",
                (battle_id, attestation_id),
            ).rowcount
            if updated != 1 or deleted != 1:
                raise ValueError("Révocation refusée: conflit transactionnel.")
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        checked.update(
            status="OWNER_ATTESTATION_REVOKED",
            applied=True,
            idempotent=False,
            dry_run=False,
            revoked_at=revoked_at,
            schema_version=SCHEMA_VERSION,
        )
        return checked
    except sqlite3.IntegrityError as exc:
        raise ValueError("Révocation refusée: conflit transactionnel.") from exc
    finally:
        connection.close()
