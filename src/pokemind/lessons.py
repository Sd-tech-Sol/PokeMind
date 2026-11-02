"""Leçons prudentes fondées sur les seuls événements de combat reconnus."""

from __future__ import annotations

import hashlib
import sqlite3
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pokemind.database import connect_readonly, connect_writable, initialize_schema, utc_now
from pokemind.battle_sample import conservative_sample


def _strict_date(value: str) -> str:
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError) as exc:
        raise ValueError("--as-of doit être une date YYYY-MM-DD valide.") from exc


def _tables(connection: sqlite3.Connection) -> set[str]:
    return {str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def battle_lessons(db_path: Path, deck_id: str, *, as_of: str) -> dict[str, Any]:
    as_of = _strict_date(as_of)
    base: dict[str, Any] = {
        "deck_id": deck_id,
        "as_of": as_of,
        "read_only": True,
        "network_used": False,
        "sample": {"valid_battles": 0, "decided": 0, "wins": 0, "losses": 0},
        "version_evidence": {"owner_attested": 0, "legacy_unattested": 0, "unlinked": 0},
        "observed_facts": [],
        "demonstrated_errors": [],
        "plausible_hypotheses": [],
        "review_questions": [],
        "validated_notes": [],
        "unknowns": [
            "Main adverse, prochaine pioche et Récompenses face cachée.",
            "Actions absentes ou tronquées du journal.",
            "Causalité entre une carte, une décision et l'issue.",
        ],
        "limits": [
            "Une observation n'est ni une preuve de collection ni une liste de 60 cartes.",
            "Les récurrences sont descriptives et affichent leur nombre de combats.",
        ],
    }
    if not db_path.is_file():
        base["status"] = "INSUFFICIENT_EVIDENCE"
        base["review_questions"].append("Importer volontairement des journaux complets pour ce deck.")
        return base
    connection = connect_readonly(db_path)
    try:
        tables = _tables(connection)
        required = {"battle_logs", "battle_events"}
        if not required.issubset(tables):
            base["status"] = "INSUFFICIENT_EVIDENCE"
            base["review_questions"].append("Mettre le schéma local à niveau par une commande d'écriture explicite.")
            return base
        battles = connection.execute(
            """SELECT id, outcome, imported_at, recognized_events, max_turn
               FROM battle_logs
               WHERE deck_id = ? AND valid = 1 AND substr(imported_at, 1, 10) <= ?
               ORDER BY imported_at, id""",
            (deck_id, as_of),
        ).fetchall()
        cohort = conservative_sample(connection, (row["id"] for row in battles))
        selected_ids = set(cohort["battle_ids"])
        battles = [row for row in battles if row["id"] in selected_ids]
        base["sample_review"] = {key: value for key, value in cohort.items() if key != "battle_ids"}
        base["limits"].extend(cohort["limits"])
        wins = sum(row["outcome"] == "W" for row in battles)
        losses = sum(row["outcome"] == "L" for row in battles)
        base["sample"] = {
            "valid_battles": len(battles),
            "decided": wins + losses,
            "wins": wins,
            "losses": losses,
            "unknown_outcome": len(battles) - wins - losses,
            "interpretation": "exploratory" if len(battles) <= 5 else "descriptive_not_predictive",
        }
        battle_ids = [int(row["id"]) for row in battles]
        if battle_ids:
            placeholders = ",".join("?" for _ in battle_ids)
            recurrences = connection.execute(
                f"""SELECT event_type, card_name, COUNT(*) AS observations,
                            COUNT(DISTINCT battle_id) AS n_battles,
                            MIN(confidence) AS confidence
                     FROM battle_events
                     WHERE battle_id IN ({placeholders}) AND actor_role = 'self'
                     GROUP BY event_type, card_name
                     ORDER BY n_battles DESC, observations DESC, event_type, card_name""",
                battle_ids,
            ).fetchall()
            base["observed_facts"] = [
                {
                    "fact": "recognized_event",
                    "event_type": row["event_type"],
                    "card_name": row["card_name"],
                    "observations": int(row["observations"]),
                    "n_battles": int(row["n_battles"]),
                    "confidence": row["confidence"],
                    "provenance": "battle_events",
                }
                for row in recurrences
            ]
            base["plausible_hypotheses"] = [
                {
                    "hypothesis": (
                        f"Revoir le contexte de {row['event_type']}"
                        + (f" pour {row['card_name']}" if row["card_name"] else "")
                        + "; la répétition ne démontre ni erreur ni causalité."
                    ),
                    "n_battles": int(row["n_battles"]),
                    "status": "plausible_not_proven",
                }
                for row in recurrences if int(row["n_battles"]) >= 2
            ][:10]
        if "battle_version_attestations" in tables:
            for battle_id in battle_ids:
                attestation = connection.execute(
                    """SELECT status, confirmed_at, revoked_at
                       FROM battle_version_attestations
                       WHERE battle_id = ? AND substr(confirmed_at, 1, 10) <= ?
                       ORDER BY confirmed_at DESC, id DESC LIMIT 1""",
                    (battle_id, as_of),
                ).fetchone()
                if attestation and (
                    attestation["status"] == "active"
                    or (attestation["revoked_at"] and str(attestation["revoked_at"])[:10] > as_of)
                ):
                    base["version_evidence"]["owner_attested"] += 1
                elif "battle_deck_versions" in tables and connection.execute(
                    "SELECT 1 FROM battle_deck_versions WHERE battle_id = ?", (battle_id,)
                ).fetchone():
                    base["version_evidence"]["legacy_unattested"] += 1
                else:
                    base["version_evidence"]["unlinked"] += 1
        else:
            linked = 0
            if "battle_deck_versions" in tables and battle_ids:
                placeholders = ",".join("?" for _ in battle_ids)
                linked = int(connection.execute(
                    f"SELECT COUNT(*) FROM battle_deck_versions WHERE battle_id IN ({placeholders})", battle_ids
                ).fetchone()[0])
            base["version_evidence"]["legacy_unattested"] = linked
            base["version_evidence"]["unlinked"] = len(battle_ids) - linked
        if "battle_lessons" in tables:
            base["validated_notes"] = [
                {
                    "battle_ref": row["evidence_ref"],
                    "kind": row["lesson_kind"],
                    "note": row["note_text"],
                    "confidence": row["confidence"],
                    "created_at": row["created_at"],
                    "provenance": row["provenance"],
                    "public_source_url": row["public_source_url"],
                    "public_source_date": row["public_source_date"],
                }
                for row in connection.execute(
                    """SELECT * FROM battle_lessons
                       WHERE deck_id = ? AND status = 'active' AND substr(created_at, 1, 10) <= ?
                       ORDER BY created_at, id""",
                    (deck_id, as_of),
                ).fetchall()
            ]
        if len(battles) < 5:
            base["review_questions"].append(f"Importer d'autres combats complets : n={len(battles)}/5 pour un premier constat prudent.")
        if base["version_evidence"]["owner_attested"] < len(battles):
            base["review_questions"].append(
                "Quelles parties peuvent être reliées volontairement à une version exacte par attestation propriétaire?"
            )
        if losses:
            base["review_questions"].append(
                f"Pour les {losses} défaite(s), quel choix précis et visible du journal souhaites-tu revoir?"
            )
        base["review_questions"].append(
            "Une séquence reconnue manque-t-elle de contexte que seul le propriétaire peut confirmer?"
        )
        base["status"] = "DESCRIPTIVE_ONLY" if battles else "INSUFFICIENT_EVIDENCE"
        return base
    finally:
        connection.close()


def save_battle_note(
    db_path: Path,
    *,
    deck_id: str,
    battle_id: int,
    text: str,
    confidence: str,
    kind: str = "owner_note",
    public_source_url: str | None = None,
    public_source_date: str | None = None,
    apply: bool = False,
    confirm_owner: bool = False,
) -> dict[str, Any]:
    normalized = unicodedata.normalize("NFC", text).strip()
    if not normalized or len(normalized) > 1000 or any(ord(char) < 32 and char not in "\n\t" for char in normalized):
        raise ValueError("La note doit contenir 1 à 1000 caractères de texte sûr.")
    if confidence not in {"high", "medium", "low", "unknown"}:
        raise ValueError("confidence doit être high, medium, low ou unknown.")
    if kind not in {"owner_note", "validated_fact"}:
        raise ValueError("kind doit être owner_note ou validated_fact.")
    if public_source_url is not None:
        parsed = urlparse(public_source_url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
            raise ValueError("La source publique doit être une URL HTTPS sans identifiants ni fragment.")
    if public_source_date is not None:
        public_source_date = _strict_date(public_source_date)
    if apply and not confirm_owner:
        raise ValueError("--apply exige --confirm-owner pour écrire une note de combat.")
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente.")
    connection = connect_writable(db_path) if apply else connect_readonly(db_path)
    try:
        if apply:
            initialize_schema(connection)
        battle = connection.execute(
            "SELECT id, deck_id, valid FROM battle_logs WHERE id = ?", (battle_id,)
        ).fetchone()
        if battle is None or not bool(battle["valid"]) or battle["deck_id"] != deck_id:
            raise ValueError("Le combat doit être valide et appartenir au deck demandé.")
        evidence_ref = f"local-battle-{battle_id:03d}"
        dedup_key = hashlib.sha256(
            f"{battle_id}\0{deck_id}\0{kind}\0{normalized.casefold()}\0{confidence}\0{public_source_url or ''}\0{public_source_date or ''}".encode("utf-8")
        ).hexdigest()
        result = {
            "mode": "applied" if apply else "dry_run",
            "read_only": not apply,
            "network_used": False,
            "battle_ref": evidence_ref,
            "deck_id": deck_id,
            "kind": kind,
            "confidence": confidence,
            "note": normalized,
            "provenance": "owner_validated",
            "public_source_url": public_source_url,
            "public_source_date": public_source_date,
        }
        if not apply:
            return result
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute("SELECT id FROM battle_lessons WHERE dedup_key = ?", (dedup_key,)).fetchone()
        if existing:
            connection.rollback()
            return {**result, "lesson_id": int(existing["id"]), "duplicate": True}
        cursor = connection.execute(
            """INSERT INTO battle_lessons
               (battle_id, deck_id, created_at, lesson_kind, note_text, confidence,
                provenance, evidence_ref, public_source_url, public_source_date, dedup_key, status)
               VALUES (?, ?, ?, ?, ?, ?, 'owner_validated', ?, ?, ?, ?, 'active')""",
            (battle_id, deck_id, utc_now(), kind, normalized, confidence, evidence_ref,
             public_source_url, public_source_date, dedup_key),
        )
        connection.commit()
        return {**result, "lesson_id": int(cursor.lastrowid), "duplicate": False}
    except Exception:
        if apply:
            connection.rollback()
        raise
    finally:
        connection.close()
