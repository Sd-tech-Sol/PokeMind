"""Synthèses cumulatives prudentes des parties importées."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from pokemind.database import connect_readonly
from pokemind.battle_sample import conservative_sample


MIN_REVIEW_GAMES = 5


def _scope(deck_id: str | None) -> tuple[str, tuple[object, ...]]:
    return (" AND deck_id = ?", (deck_id,)) if deck_id else ("", ())


def _summary(connection, deck_id: str | None) -> dict[str, Any]:
    suffix, parameters = _scope(deck_id)
    rows = connection.execute(
        "SELECT id,outcome FROM battle_logs WHERE valid=1" + suffix + " ORDER BY id", parameters,
    ).fetchall()
    stored_counts = Counter(row["outcome"] for row in rows)
    cohort = conservative_sample(connection, (row["id"] for row in rows))
    selected = set(cohort["battle_ids"])
    rows = [row for row in rows if row["id"] in selected]
    counts = Counter(row["outcome"] for row in rows)
    invalid = connection.execute(
        "SELECT COUNT(*) FROM battle_logs WHERE valid = 0" + suffix, parameters
    ).fetchone()[0]
    total = len(rows)
    wins, losses, unknown = counts["W"], counts["L"], counts["inconnue"]
    decided = wins + losses
    observations: Counter[str] = Counter()
    games_seen: Counter[str] = Counter()
    # Bounded parameter batches also work with SQLite's older 999 limit.
    ordered_ids = cohort["battle_ids"]
    for offset in range(0, len(ordered_ids), 900):
        batch = ordered_ids[offset:offset + 900]
        placeholders = ",".join("?" for _ in batch)
        for row in connection.execute(
            "SELECT card_name,COUNT(*) AS observations,COUNT(DISTINCT battle_id) AS games_seen "
            f"FROM card_observations WHERE owner_role='self' AND battle_id IN ({placeholders}) "
            "GROUP BY card_name", batch,
        ):
            observations[row["card_name"]] += int(row["observations"])
            games_seen[row["card_name"]] += int(row["games_seen"])
    cards = [{"card": name, "games_seen": games_seen[name], "observations": observations[name]}
             for name in sorted(observations, key=lambda name: (-games_seen[name], -observations[name], name))[:100]]
    repeated = [
        f"{item['card']} a été observée dans {item['games_seen']} parties."
        for item in cards if item["games_seen"] >= 2
    ]
    limits = [
        "Les cartes observées ne constituent ni une liste confirmée de 60 cartes ni une preuve de collection.",
        "Les journaux décrivent seulement les événements exportés; les informations cachées restent inconnues.",
        "Une corrélation répétée ne démontre pas la cause d'une victoire ou d'une défaite.",
    ]
    limits.extend(cohort["limits"])
    possible_weaknesses: list[str] = []
    if cohort["probable_duplicates_excluded"]:
        possible_weaknesses.append("Doublons probables entre versions du parseur : bilan conservateur, confirmation propriétaire non acquise.")
    if losses >= 2:
        possible_weaknesses.append(
            f"Les {losses} défaites méritent une revue ciblée, mais leur cause n'est pas démontrée par ce seul échantillon."
        )
    if unknown:
        possible_weaknesses.append(f"{unknown} partie(s) valide(s) ont une issue inconnue, ce qui limite le ratio.")
    if invalid:
        possible_weaknesses.append(f"{int(invalid)} import(s) non valide(s) ne sont pas comptés dans l'échantillon.")
    return {
        "scope": {"deck_id": deck_id, "all_decks": deck_id is None},
        "sample": {"valid_games": total, "minimum_for_first_review": MIN_REVIEW_GAMES,
                   "invalid_imports": int(invalid), "stored_valid_games": cohort["stored_valid_games"],
                   "probable_duplicates_excluded": cohort["probable_duplicates_excluded"]},
        "sample_review": {key: value for key, value in cohort.items() if key != "battle_ids"},
        "stored_outcomes": {"wins": stored_counts["W"], "losses": stored_counts["L"],
                            "unknown": stored_counts["inconnue"]},
        "outcome_basis": "PROVISIONAL_DUPLICATE_REVIEW" if cohort["probable_duplicates_excluded"] else "STORED_SOURCE_HASHES",
        "outcomes": {
            "wins": wins, "losses": losses, "unknown": unknown,
            "win_ratio": round(wins / decided, 4) if decided and not cohort["probable_duplicates_excluded"] else None,
            "ratio_denominator": decided,
        },
        "assessment_ready": total >= MIN_REVIEW_GAMES,
        "assessment": (
            "Premier bilan prudent disponible; 10 parties ou plus sont recommandées."
            if total >= MIN_REVIEW_GAMES
            else f"Données insuffisantes: {total}/{MIN_REVIEW_GAMES} parties valides."
        ),
        "observed_cards": cards,
        "repeated_findings": repeated,
        "possible_weaknesses": possible_weaknesses,
        "limits": limits,
    }


def profile_summary(db_path: Path, deck_id: str | None = None) -> dict[str, Any]:
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente; exécuter d'abord 'import-seed'.")
    connection = connect_readonly(db_path)
    try:
        connection.execute("BEGIN")
        return _summary(connection, deck_id)
    finally:
        connection.close()


def profile_review(db_path: Path, deck_id: str | None = None) -> dict[str, Any]:
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente; exécuter d'abord 'import-seed'.")
    suffix, parameters = _scope(deck_id)
    connection = connect_readonly(db_path)
    try:
        connection.execute("BEGIN")
        summary = _summary(connection, deck_id)
        games = connection.execute(
            """SELECT id, source_sha256, outcome, max_turn, recognized_events,
                      reference_player, opponent_name, warnings_json
               FROM battle_logs WHERE valid = 1""" + suffix + " ORDER BY id",
            parameters,
        ).fetchall()
        excluded = {value for group in summary["sample_review"]["probable_duplicate_groups"]
                    for value in group["battle_ids"] if value != group["representative_id"]}
        facts: list[dict[str, Any]] = []
        for game in games:
            if game["id"] in excluded:
                continue
            anchors = connection.execute(
                """SELECT turn_number, event_type, card_name, confidence
                   FROM battle_events WHERE battle_id = ? AND actor_role = 'self'
                   ORDER BY sequence LIMIT 12""",
                (game["id"],),
            ).fetchall()
            facts.append(
                {
                    "battle_id": int(game["id"]),
                    "sha256_prefix": game["source_sha256"][:12],
                    "outcome": game["outcome"],
                    "max_turn": game["max_turn"],
                    "recognized_events": int(game["recognized_events"]),
                    "reference_player": game["reference_player"],
                    "opponent": game["opponent_name"],
                    "turn_evidence": [
                        {
                            "turn": row["turn_number"], "event": row["event_type"],
                            "card": row["card_name"], "confidence": row["confidence"],
                        }
                        for row in anchors
                    ],
                    "warnings": json.loads(game["warnings_json"]),
                }
            )
        hypotheses: list[str] = []
        if summary["assessment_ready"]:
            hypotheses.append(
                "Si une carte revient dans plusieurs défaites, examiner sa séquence et le contexte avant tout changement de deck."
            )
        else:
            hypotheses.append("Attendre au moins 5 parties valides avant de transformer une tendance en piste d'entraînement.")
        questions = [
            "Le deck associé est-il le même export de 60 cartes pour toutes ces parties?",
            "Quels choix précis semblaient difficiles aux tours indiqués?",
            "Les journaux avec issue inconnue peuvent-ils être exportés de nouveau en entier?",
        ]
        return {
            "summary": summary,
            "facts": facts,
            "hypotheses": hypotheses,
            "targeted_questions": questions,
            "format_validation": "fixtures synthétiques et exemple public seulement; test terrain utilisateur requis",
        }
    finally:
        connection.close()
