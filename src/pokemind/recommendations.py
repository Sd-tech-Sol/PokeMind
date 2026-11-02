"""Recommandations personnelles conditionnelles composées de preuves locales."""

from __future__ import annotations

import json
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any

from pokemind.analysis import analyze_deck
from pokemind.cards import resolve_deck_cards
from pokemind.collection import collection_missing, collection_status, credits_status
from pokemind.database import connect_readonly
from pokemind.lessons import battle_lessons


def public_test_plan(*, target, selector, support):
    """Pure PUBLIC planning primitive; never consult owner analysis/collection."""
    return {
        "kind": "test_plan", "target_archetype_hypothesis": target,
        "published_selector": selector, "support": support,
        "protocol": [
            "Garder la liste publiée comme référence; noter séparément toute adaptation.",
            "En entraînement volontaire, attester version, date et adversaire observé.",
            "Noter installation, recherches, coûts d'attaque et relais effectivement visibles.",
            "Séparer versions et adversaires; conserver W/L/unknown et les doublons potentiels.",
            "Réévaluer après plusieurs parties; une différence descriptive ne prouve pas une cause.",
        ],
        "minimum_decided_for_descriptive_ratio": 5,
        "minimum_is_not_statistical_sufficiency": True,
        "causal_effect": "unknown", "predicted_winrate": None,
    }


def _normalized(value: Any) -> str:
    return " ".join(unicodedata.normalize("NFC", str(value or "")).casefold().split())


def _explicit_text_references(db_path: Path, deck_id: str) -> list[dict[str, Any]]:
    """Retourne des citations textuelles exactes; ne les qualifie pas automatiquement de synergie."""
    try:
        resolved = resolve_deck_cards(db_path, deck_id)
    except (FileNotFoundError, ValueError, sqlite3.DatabaseError):
        return []
    identities = {
        entry["tcgdex_ids"][0]: entry
        for entry in resolved["entries"]
        if entry["status"] == "resolved" and len(entry["tcgdex_ids"]) == 1
    }
    if len(identities) < 2:
        return []
    connection = connect_readonly(db_path)
    try:
        details: dict[str, list[sqlite3.Row]] = {}
        for printing_id in identities:
            details[printing_id] = connection.execute(
                """SELECT language, name, description, effect, abilities_json, attacks_json,
                          source_url, retrieved_at
                   FROM catalog_translations
                   WHERE printing_id = ? AND status = 'present'""",
                (printing_id,),
            ).fetchall()
        references: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str]] = set()
        for source_id, rows in details.items():
            for row in rows:
                body = " ".join(
                    str(row[field] or "")
                    for field in ("description", "effect", "abilities_json", "attacks_json")
                )
                normalized_body = _normalized(body)
                if not normalized_body:
                    continue
                for target_id, target_entry in identities.items():
                    if target_id == source_id:
                        continue
                    target_name = _normalized(target_entry["card_name"])
                    if len(target_name) < 5 or target_name not in normalized_body:
                        continue
                    key = (source_id, target_id, str(row["language"]))
                    if key in seen:
                        continue
                    seen.add(key)
                    references.append({
                        "kind": "explicit_card_text_reference",
                        "source_printing": source_id,
                        "target_printing": target_id,
                        "target_name": target_entry["card_name"],
                        "language": row["language"],
                        "source_url": row["source_url"],
                        "retrieved_at": row["retrieved_at"],
                        "status": "verified_text_reference_not_strategy_proof",
                    })
        return references
    finally:
        connection.close()


def _copy_limit_candidates(analysis: dict[str, Any], db_path: Path, deck_id: str) -> list[dict[str, Any]]:
    rules = analysis["facts"].get("rules", {})
    structure = rules.get("structure_validation", {})
    if structure.get("status") != "not_legal" or "DECK_COPY_LIMIT_EXCEEDED" not in structure.get("reason_codes", []):
        return []
    over = structure.get("checks", {}).get("over_copy_limit", [])
    if not over:
        return []
    connection = connect_readonly(db_path)
    try:
        version = connection.execute(
            "SELECT id FROM deck_versions WHERE deck_id = ? ORDER BY version_number DESC LIMIT 1", (deck_id,)
        ).fetchone()
        if version is None:
            return []
        rows = connection.execute(
            """SELECT card_name, set_code, collector_number, quantity
               FROM deck_version_cards WHERE deck_version_id = ? ORDER BY ordinal""",
            (version["id"],),
        ).fetchall()
        candidates: list[dict[str, Any]] = []
        for violation in over:
            excess = int(violation["quantity"]) - int(violation["limit"])
            matching = next((row for row in rows if _normalized(row["card_name"]) == _normalized(violation["card_name"])), None)
            if matching is None or excess <= 0:
                continue
            candidates.append({
                "remove": {
                    "name": matching["card_name"], "set_code": matching["set_code"],
                    "collector_number": matching["collector_number"], "quantity": excess,
                    "status": "verified_structural_violation",
                },
                "add": {"identity": None, "quantity": excess, "status": "unknown_replacement"},
                "reason": "La limite de copies est dépassée selon une règle officielle active et complète.",
                "source": structure.get("sources", []),
                "tradeoff": "Le remplacement stratégique n'est pas choisi sans texte, méta et contexte suffisants.",
                "status": "verified_remove_only",
            })
        return candidates
    finally:
        connection.close()


def recommend_deck(
    db_path: Path,
    deck_id: str,
    *,
    as_of: str,
    format: str = "standard",
    platform: str = "live",
    use_collection: bool = False,
) -> dict[str, Any]:
    analysis = analyze_deck(db_path, deck_id, as_of=as_of, format=format, platform=platform)
    lessons = battle_lessons(db_path, deck_id, as_of=as_of)
    collection = collection_status(db_path, as_of=as_of)
    credits = credits_status(db_path, as_of=as_of)
    missing: dict[str, Any] | None = None
    if use_collection and collection.get("available"):
        missing = collection_missing(db_path, deck_id, as_of=as_of)
    strengths: list[dict[str, Any]] = []
    weaknesses: list[dict[str, Any]] = []
    deck = analysis["facts"]["deck"]
    if deck.get("exact_confirmed") and deck.get("quantity_sum") == 60:
        strengths.append({
            "claim": "Une version exacte de 60 cartes est confirmée localement.",
            "evidence": deck.get("version_ref"),
            "status": "verified_local_fact",
        })
    text_references = _explicit_text_references(db_path, deck_id)
    for reference in text_references:
        strengths.append({
            "claim": "Un texte de carte vérifié cite explicitement une autre impression du deck.",
            "evidence": reference,
            "status": "text_reference_only",
        })
    version_n = lessons["version_evidence"]["owner_attested"]
    if version_n:
        strengths.append({
            "claim": f"{version_n} combat(s) sont reliés à une version par attestation propriétaire datée.",
            "evidence": {"n": version_n, "provenance": "owner_asserted"},
            "status": "verified_owner_statement",
        })
    for unknown in analysis["unknowns"]:
        weaknesses.append({
            "finding": unknown["message"],
            "code": unknown["code"],
            "status": "unknown_or_insufficient_evidence",
        })
    if missing is not None:
        known_missing = int(missing.get("known_missing_total", 0))
        if known_missing:
            weaknesses.append({
                "finding": f"La collection déclarée manque {known_missing} copie(s) pour cette impression exacte.",
                "code": "OWNER_REPORTED_MISSING",
                "status": "owner_provided",
            })
    elif use_collection:
        weaknesses.append({
            "finding": "Aucune collection propriétaire active n'est disponible.",
            "code": "COLLECTION_UNKNOWN",
            "status": "unknown",
        })
    candidate_changes = _copy_limit_candidates(analysis, db_path, deck_id)
    meta = analysis["facts"].get("metagame", {})
    matchups = {
        "status": "unknown",
        "n": int(meta.get("n_exploitable_matches", 0) or 0),
        "reason": "Aucun mapping prouvé ne relie le deck local à un archétype Limitless publié.",
    }
    evidence_sufficient = bool(candidate_changes)
    status = "CONDITIONAL_CANDIDATES" if evidence_sufficient else "INSUFFICIENT_EVIDENCE"
    next_evidence = list(analysis["next_evidence"])
    if not text_references:
        next_evidence.append("Récupérer les textes TCGdex des impressions exactes avant toute affirmation de synergie.")
    if use_collection and not collection.get("available"):
        next_evidence.append("Importer volontairement une collection datée pour évaluer les cartes manquantes.")
    if not credits.get("available"):
        next_evidence.append("Déclarer volontairement les crédits si une future estimation sourcée devient nécessaire.")
    return {
        "deck_id": deck_id,
        "context": {"format": format, "platform": platform, "as_of": as_of},
        "read_only": True,
        "network_used": False,
        "status": status,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "verified_text_references": text_references,
        "candidate_changes": candidate_changes,
        "matchups": matchups,
        "ownership": {
            "requested": use_collection,
            "status": "owner_provided" if collection.get("available") else "unknown",
            "availability_status": collection.get("availability_status"),
            "as_of": collection.get("active", {}).get("as_of") if collection.get("active") else None,
            "missing": missing,
        },
        "credits": {
            "status": "owner_provided" if credits.get("available") else "unknown",
            "availability_status": credits.get("availability_status"),
            "as_of": credits.get("active", {}).get("as_of") if credits.get("active") else None,
            "amount": credits.get("active", {}).get("amount") if credits.get("active") else None,
            "craft_cost": "unknown",
            "availability_after_crafting": "unknown",
        },
        "battle_lessons": lessons,
        "evidence_layers": {
            "official_rules": analysis["facts"].get("rules", {}),
            "card_text": text_references,
            "limitless": matchups,
            "personal_observations": {
                "n": lessons["sample"]["valid_battles"],
                "owner_attested_version_n": version_n,
            },
            "hypotheses": lessons["plausible_hypotheses"],
        },
        "next_evidence": list(dict.fromkeys(next_evidence))[:8],
        "limits": [
            "Aucune carte n'est automatiquement ajoutée, retirée, achetée ou fabriquée.",
            "Même cinq combats demeurent exploratoires et ne prouvent pas un matchup universel.",
            "Populaire, observé ou textuellement lié ne signifie pas meilleur.",
        ],
    }
