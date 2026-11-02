"""Diagnostic personnel hors ligne, conservateur et strictement en lecture seule."""

from __future__ import annotations

from pokemind.battle_sample import conservative_sample

import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from pokemind.battle_logs import DECK_ID_RE
from pokemind.cards import cards_coverage, resolve_deck_cards
from pokemind.database import connect_readonly
from pokemind.rules import check_deck, rules_status


FORMATS = {"standard", "expanded"}
PLATFORMS = {"live", "in_person"}


def _strict_date(value: str) -> str:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("--as-of doit être une date ISO stricte YYYY-MM-DD.") from exc
    if parsed.isoformat() != value:
        raise ValueError("--as-of doit être une date ISO stricte YYYY-MM-DD.")
    return value


def _unknown(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _empty_report(deck_id: str, *, as_of: str, format: str, platform: str) -> dict[str, Any]:
    return {
        "read_only": True,
        "network_used": False,
        "context": {
            "deck_id": deck_id,
            "as_of": as_of,
            "format": format,
            "platform": platform,
        },
        "assessment": "données insuffisantes",
        "confidence": {
            "level": "faible",
            "basis": ["Aucune preuve locale exploitable n'a encore été établie."],
        },
        "facts": {
            "deck": {"found": False},
            "battles": {
                "valid_unique": 0,
                "duplicates_excluded": 0,
                "outcomes": {"wins": 0, "losses": 0, "draws": 0, "ambiguous": 0},
                "with_any_version_proven": 0,
                "with_selected_version_proven": 0,
                "with_selected_version_owner_attested": 0,
                "with_selected_version_legacy_unattested": 0,
                "owner_attested_revoked": 0,
                "attestations_after_as_of": 0,
                "with_deck_identity_recorded": 0,
                "period": {"from": None, "to": None},
                "observations": [],
            },
            "catalog": {"available": False},
            "rules": {"available": False, "status": "unknown"},
            "metagame": {"available": False},
        },
        "evidence": [],
        "unknowns": [],
        "next_evidence": [],
        "warnings": [],
    }


def _table_names(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }


def _deck_fact(connection: sqlite3.Connection, deck_id: str, as_of: str) -> dict[str, Any]:
    row = connection.execute(
        """SELECT id, version_number, imported_at, approved_at, effective_from,
                  exact_confirmed, total_cards, entry_count
           FROM deck_versions WHERE deck_id=? ORDER BY version_number DESC LIMIT 1""",
        (deck_id,),
    ).fetchone()
    if row is None:
        return {"found": False}
    quantity_sum = int(
        connection.execute(
            "SELECT COALESCE(SUM(quantity), 0) FROM deck_version_cards WHERE deck_version_id=?",
            (row["id"],),
        ).fetchone()[0]
    )
    effective = str(row["effective_from"] or row["imported_at"] or "")
    effective_date = effective[:10] if len(effective) >= 10 else None
    try:
        parsed_effective = date.fromisoformat(effective_date or "")
    except ValueError:
        historical_applicability = "unknown"
    else:
        historical_applicability = (
            "applicable" if parsed_effective.isoformat() <= as_of else "not_applicable"
        )
    in_scope = historical_applicability == "applicable"
    exact = bool(row["exact_confirmed"])
    total = int(row["total_cards"])
    constraints = {
        "latest_version_selected": True,
        "exact_confirmed": exact,
        "recorded_total_is_60": total == 60,
        "quantity_sum_is_60": quantity_sum == 60,
        "recorded_total_matches_quantity_sum": total == quantity_sum,
        "effective_on_or_before_as_of": in_scope,
    }
    return {
        "found": True,
        "version": int(row["version_number"]),
        "version_ref": f"deck-version:{deck_id}:v{int(row['version_number'])}",
        "imported_at": row["imported_at"],
        "approved_at": row["approved_at"],
        "effective_from": row["effective_from"],
        "exact_confirmed": exact,
        "recorded_total": total,
        "quantity_sum": quantity_sum,
        "entry_count": int(row["entry_count"]),
        "historical_applicability": historical_applicability,
        "constraints": constraints,
        "selected_version_id": int(row["id"]),
    }


def _outcome_bucket(value: Any) -> str:
    normalized = str(value or "").strip().casefold()
    if normalized in {"w", "win", "victoire"}:
        return "wins"
    if normalized in {"l", "loss", "défaite", "defaite"}:
        return "losses"
    if normalized in {"d", "draw", "tie", "nul", "nulle"}:
        return "draws"
    return "ambiguous"


def _date_part(value: Any) -> str | None:
    candidate = str(value or "")[:10]
    try:
        return date.fromisoformat(candidate).isoformat()
    except ValueError:
        return None


def _attestation_at_date(
    history: list[sqlite3.Row], as_of: str
) -> tuple[str | None, sqlite3.Row | None]:
    available = [
        row for row in history
        if _date_part(row["confirmed_at"]) is not None
        and str(_date_part(row["confirmed_at"])) <= as_of
    ]
    if not available:
        return ("after_as_of", None) if history else (None, None)
    latest = max(available, key=lambda row: (str(row["confirmed_at"]), int(row["id"])))
    revoked = _date_part(latest["revoked_at"])
    if latest["revoked_at"] is not None and revoked is None:
        return "conflict", latest
    if revoked is not None and revoked <= as_of:
        return "revoked", latest
    return "active", latest


def _battle_fact(
    connection: sqlite3.Connection,
    deck_id: str,
    selected_version_id: int | None,
    as_of: str,
    *,
    selected_version_applicable: bool = True,
    selected_version_effective_date: str | None = None,
) -> dict[str, Any]:
    rows = connection.execute(
        """SELECT b.id, b.source_sha256, b.imported_at, b.outcome,
                  link.deck_version_id, linked.version_number AS linked_version
           FROM battle_logs b
           LEFT JOIN battle_deck_versions link ON link.battle_id=b.id
           LEFT JOIN deck_versions linked ON linked.id=link.deck_version_id
           WHERE b.deck_id=? AND b.valid=1
           ORDER BY b.imported_at, b.id""",
        (deck_id,),
    ).fetchall()
    tables = _table_names(connection)
    attestation_history: dict[int, list[sqlite3.Row]] = {}
    if "battle_version_attestations" in tables:
        for attestation in connection.execute(
            """SELECT a.id, a.battle_id, a.deck_version_id, a.confirmed_at,
                      a.status, a.revoked_at, a.provenance,
                      v.deck_id AS attested_deck_id,
                      v.version_number AS attested_version,
                      v.exact_confirmed AS attested_exact_confirmed,
                      v.total_cards AS attested_total_cards,
                      (SELECT COALESCE(SUM(c.quantity), 0)
                         FROM deck_version_cards c
                        WHERE c.deck_version_id=v.id) AS attested_quantity_sum
                 FROM battle_version_attestations a
                 LEFT JOIN deck_versions v ON v.id=a.deck_version_id
                WHERE a.battle_id IN (
                    SELECT id FROM battle_logs WHERE deck_id=? AND valid=1
                )
                ORDER BY a.confirmed_at, a.id""",
            (deck_id,),
        ).fetchall():
            attestation_history.setdefault(int(attestation["battle_id"]), []).append(
                attestation
            )
    seen: set[str] = set()
    kept: list[Any] = []
    duplicates = 0
    excluded_after_as_of = 0
    excluded_invalid_date = 0
    for row in rows:
        imported = str(row["imported_at"] or "")
        observed_date = imported[:10] if len(imported) >= 10 else ""
        try:
            parsed_date = date.fromisoformat(observed_date)
        except ValueError:
            excluded_invalid_date += 1
            continue
        if parsed_date.isoformat() > as_of:
            excluded_after_as_of += 1
            continue
        identity = str(row["source_sha256"] or f"battle-id:{row['id']}")
        if identity in seen:
            duplicates += 1
            continue
        seen.add(identity)
        kept.append(row)
    cohort = conservative_sample(connection, (row["id"] for row in kept))
    selected_ids = set(cohort["battle_ids"])
    kept = [row for row in kept if row["id"] in selected_ids]
    duplicates += cohort["probable_duplicates_excluded"]
    outcomes = {"wins": 0, "losses": 0, "draws": 0, "ambiguous": 0}
    observations: list[dict[str, Any]] = []
    any_version = 0
    selected_version = 0
    selected_owner_attested = 0
    selected_legacy = 0
    owner_revoked = 0
    attestations_after_as_of = 0
    dates: list[str] = []
    for ordinal, row in enumerate(kept, start=1):
        bucket = _outcome_bucket(row["outcome"])
        outcomes[bucket] += 1
        observed_date = str(row["imported_at"])[:10]
        linked_id = row["deck_version_id"]
        attestation_state, attestation = _attestation_at_date(
            attestation_history.get(int(row["id"]), []), as_of
        )
        confirmed_at = None
        provenance = None
        if attestation_state == "after_as_of":
            attestations_after_as_of += 1
            version_evidence = "owner_attestation_not_available_as_of"
        elif attestation_state == "revoked":
            owner_revoked += 1
            version_evidence = "owner_attested_revoked"
            confirmed_at = attestation["confirmed_at"] if attestation is not None else None
            provenance = "owner_asserted"
        elif attestation_state == "conflict":
            version_evidence = "owner_attestation_conflict"
        elif attestation_state == "active":
            assert attestation is not None
            confirmed_at = attestation["confirmed_at"]
            provenance = "owner_asserted"
            attested_id = int(attestation["deck_version_id"])
            valid_attestation = (
                str(attestation["attested_deck_id"] or "") == deck_id
                and bool(attestation["attested_exact_confirmed"])
                and int(attestation["attested_total_cards"] or 0) == 60
                and int(attestation["attested_quantity_sum"] or 0) == 60
                and (
                    str(attestation["status"]) != "active"
                    or (linked_id is not None and int(linked_id) == attested_id)
                )
            )
            if not valid_attestation:
                version_evidence = "owner_attestation_conflict"
            else:
                any_version += 1
                if selected_version_id is not None and attested_id == selected_version_id:
                    # La déclaration propriétaire porte sur la version réellement
                    # jouée; une exportation locale postérieure au combat ne la
                    # contredit pas. Seule sa disponibilité au contexte as_of compte.
                    link_is_temporally_applicable = selected_version_applicable
                    if link_is_temporally_applicable:
                        selected_version += 1
                        selected_owner_attested += 1
                        version_evidence = "owner_attested_selected_version"
                    else:
                        version_evidence = "owner_attested_selected_version_not_applicable"
                else:
                    version_evidence = "owner_attested_other_version"
        elif linked_id is None:
            version_evidence = "unproven"
        else:
            any_version += 1
            provenance = "legacy_link_unattested"
            if selected_version_id is not None and int(linked_id) == selected_version_id:
                link_is_temporally_applicable = (
                    selected_version_applicable
                    and (
                        selected_version_effective_date is None
                        or observed_date >= selected_version_effective_date
                    )
                )
                if link_is_temporally_applicable:
                    selected_version += 1
                    selected_legacy += 1
                    version_evidence = "legacy_selected_version_unattested"
                else:
                    version_evidence = "legacy_selected_version_not_applicable"
            else:
                version_evidence = "legacy_other_version_unattested"
        dates.append(observed_date)
        observations.append(
            {
                "reference": f"local-observation-{ordinal:03d}",
                "observed_date": observed_date,
                "outcome": bucket,
                "version_evidence": version_evidence,
                "linked_version": (
                    int(attestation["attested_version"])
                    if attestation is not None and attestation["attested_version"] is not None
                    else (int(row["linked_version"]) if row["linked_version"] is not None else None)
                ),
                "provenance": provenance,
                "confirmed_at": confirmed_at,
            }
        )
    return {
        "valid_unique": len(kept),
        "duplicates_excluded": duplicates,
        "sample_quality": {key: value for key, value in cohort.items()
                           if key not in {"battle_ids", "probable_duplicate_groups"}},
        "excluded_after_as_of": excluded_after_as_of,
        "excluded_invalid_date": excluded_invalid_date,
        "outcomes": outcomes,
        "with_any_version_proven": any_version,
        "with_selected_version_proven": selected_version,
        "with_selected_version_owner_attested": selected_owner_attested,
        "with_selected_version_legacy_unattested": selected_legacy,
        "owner_attested_revoked": owner_revoked,
        "attestations_after_as_of": attestations_after_as_of,
        "with_deck_identity_recorded": len(kept),
        "period": {"from": min(dates) if dates else None, "to": max(dates) if dates else None},
        "observations": observations,
        "rate_or_matchup_claim": None,
    }


def _catalog_fact(db_path: Path, deck_id: str) -> tuple[dict[str, Any], list[dict[str, str]]]:
    coverage = cards_coverage(db_path)
    resolution = resolve_deck_cards(db_path, deck_id)
    entry_counts = dict(resolution["counts"])
    quantity_counts = {"resolved": 0, "ambiguous": 0, "unresolved": 0}
    for entry in resolution["entries"]:
        quantity_counts[entry["status"]] += int(entry["quantity"])
    denominator_entries = sum(entry_counts.values())
    denominator_cards = sum(quantity_counts.values())
    fact = {
        "available": True,
        "deck_version": resolution["deck_version"],
        "entry_resolution": {**entry_counts, "denominator": denominator_entries},
        "quantity_resolution": {**quantity_counts, "denominator": denominator_cards},
        "local_coverage": {
            "sets_discovered": coverage["sets_discovered"],
            "unique_printings": coverage["unique_printings"],
            "details_retrieved_any_language": coverage["details_retrieved_any_language"],
            "complete": coverage["complete"],
            "last_success_at": coverage["last_success_at"],
        },
        "live_support": "unknown",
    }
    unknowns: list[dict[str, str]] = []
    if entry_counts["unresolved"]:
        unknowns.append(_unknown("PRINTINGS_UNRESOLVED", "Au moins une ligne n'a pas d'identité TCGdex unique vérifiée."))
    if entry_counts["ambiguous"]:
        unknowns.append(_unknown("PRINTINGS_AMBIGUOUS", "Au moins une ligne concorde avec plusieurs impressions TCGdex."))
    if not coverage["complete"]:
        unknowns.append(_unknown("CATALOG_PARTIAL", "Le catalogue local TCGdex est partiel."))
    return fact, unknowns


def _rules_fact(db_path: Path, deck_id: str, *, format: str, platform: str, as_of: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    status = rules_status(db_path)
    verdict = check_deck(db_path, deck_id, format=format, platform=platform, as_of=as_of)
    card_statuses = {"legal": 0, "not_legal": 0, "unknown": 0}
    evidence: dict[str, dict[str, Any]] = {}
    for card in verdict["cards"]:
        card_status = str(card["verdict"].get("status", "unknown"))
        card_statuses[card_status if card_status in card_statuses else "unknown"] += 1
        for source in card["verdict"].get("sources", []):
            source_id = str(source["source_id"])
            evidence[source_id] = {
                "source": "Pokémon officiel",
                "type": "règle officielle locale",
                "date": source.get("published_date") or source.get("consulted_at"),
                "identifier": source_id,
            }
    fact = {
        "available": True,
        "offline": True,
        "as_of": as_of,
        "format": format,
        "platform": platform,
        "registry_version": status["registry_version"],
        "latest_consulted_at": status["latest_consulted_at"],
        "coverage": status["coverage"],
        "status": verdict["status"],
        "reason_codes": verdict["reason_codes"],
        "structure_validation": verdict["structure_validation"],
        "card_statuses": card_statuses,
        "sources_used": sorted(evidence),
        "live_support": "unknown",
        "ownership": "unknown",
        "craftability": "unknown",
    }
    registry_id = str(status["registry_version"] or "unversioned")
    evidence.setdefault(
        f"registry:{registry_id}",
        {
            "source": "Pokémon officiel (registre local)",
            "type": "couverture réglementaire datée",
            "date": status["latest_consulted_at"],
            "identifier": f"official-rules:{registry_id}",
        },
    )
    return fact, list(evidence.values())


def _meta_fact(connection: sqlite3.Connection, *, format: str, platform: str, as_of: str) -> dict[str, Any]:
    meta_platform = "PTCGL" if platform == "live" else "TABLETOP"
    online = platform == "live"
    context_parameters = (format.upper(), meta_platform, int(online))
    tournament_rows = connection.execute(
        """SELECT tournament_id, fetched_at FROM meta_tournaments
           WHERE game='PTCG' AND format=? AND platform=? AND is_online=?
             AND is_public=1 AND snapshot_status='complete'
             AND date(date_utc) <= date(?) AND date(fetched_at) <= date(?)
           ORDER BY date_utc, tournament_id""",
        (*context_parameters, as_of, as_of),
    ).fetchall()
    exclusions = connection.execute(
        """SELECT
               SUM(CASE WHEN date(date_utc) > date(?) THEN 1 ELSE 0 END) AS future_events,
               SUM(CASE WHEN date(date_utc) <= date(?) AND date(fetched_at) > date(?)
                        THEN 1 ELSE 0 END) AS later_snapshots,
               SUM(CASE WHEN date(date_utc) IS NULL OR date(fetched_at) IS NULL
                        THEN 1 ELSE 0 END) AS invalid_dates
           FROM meta_tournaments
           WHERE game='PTCG' AND format=? AND platform=? AND is_online=?
             AND is_public=1 AND snapshot_status='complete'""",
        (as_of, as_of, as_of, *context_parameters),
    ).fetchone()
    excluded = {
        "event_after_as_of": int(exclusions["future_events"] or 0),
        "snapshot_captured_after_as_of": int(exclusions["later_snapshots"] or 0),
        "invalid_event_or_capture_date": int(exclusions["invalid_dates"] or 0),
    }
    ids = [str(row["tournament_id"]) for row in tournament_rows]
    if ids and excluded["snapshot_captured_after_as_of"]:
        availability = "partial_as_of"
    elif ids:
        availability = "available_as_of"
    elif excluded["snapshot_captured_after_as_of"]:
        availability = "not_available_as_of"
    else:
        availability = "no_matching_snapshot"
    result = {
        "available": True,
        "filters": {
            "game": "PTCG",
            "format": format.upper(),
            "platform": meta_platform,
            "online": online,
            "through": as_of,
            "event_through": as_of,
            "evidence_captured_through": as_of,
            "public_only": True,
            "complete_snapshots_only": True,
        },
        "snapshot_availability": availability,
        "capture_date_semantics": "local_cache_capture_not_provider_publication",
        "excluded": excluded,
        "n_tournaments": len(ids),
        "n_placements": 0,
        "n_classified_placements": 0,
        "n_published_archetypes": 0,
        "n_published_matches": 0,
        "n_exploitable_matches": 0,
        "deck_archetype_mapping": "unproven",
        "matchup_statistics": None,
        "last_fetched_at": max((str(row["fetched_at"]) for row in tournament_rows), default=None),
    }
    if not ids:
        return result
    placeholders = ",".join("?" for _ in ids)
    placements = connection.execute(
        f"""SELECT COUNT(*) AS total,
                   SUM(CASE WHEN archetype_id IS NOT NULL THEN 1 ELSE 0 END) AS classified,
                   COUNT(DISTINCT archetype_id) AS archetypes
            FROM meta_placements WHERE tournament_id IN ({placeholders})""",
        ids,
    ).fetchone()
    result["n_placements"] = int(placements["total"] or 0)
    result["n_classified_placements"] = int(placements["classified"] or 0)
    result["n_published_archetypes"] = int(placements["archetypes"] or 0)
    result["n_published_matches"] = int(
        connection.execute(
            f"SELECT COUNT(*) FROM meta_matches WHERE tournament_id IN ({placeholders})", ids
        ).fetchone()[0]
    )
    result["n_exploitable_matches"] = int(
        connection.execute(
            f"""SELECT COUNT(*) FROM meta_matches m
                JOIN meta_placements p1 ON p1.tournament_id=m.tournament_id
                    AND p1.participant_ref=m.participant1_ref
                JOIN meta_placements p2 ON p2.tournament_id=m.tournament_id
                    AND p2.participant_ref=m.participant2_ref
                WHERE m.tournament_id IN ({placeholders}) AND m.eligible=1
                  AND p1.archetype_id IS NOT NULL AND p2.archetype_id IS NOT NULL""",
            ids,
        ).fetchone()[0]
    )
    return result


def analyze_deck(
    db_path: Path, deck_id: str, *, as_of: str, format: str = "standard", platform: str = "live"
) -> dict[str, Any]:
    """Compose les moteurs locaux sans créer, migrer ni modifier la base."""
    if not DECK_ID_RE.fullmatch(deck_id):
        raise ValueError("Identifiant de deck invalide (1-64 caractères: lettres, chiffres, . _ -).")
    if format not in FORMATS or platform not in PLATFORMS:
        raise ValueError("Format ou plateforme invalide.")
    as_of = _strict_date(as_of)
    report = _empty_report(deck_id, as_of=as_of, format=format, platform=platform)
    if not db_path.is_file():
        report["unknowns"].append(_unknown("DATABASE_MISSING", "La base locale est absente."))
        report["next_evidence"].append("Importer volontairement un deck local et les preuves publiques requises.")
        report["warnings"].append("Aucun fichier n'a été créé et aucune migration n'a été tentée.")
        return report

    connection = connect_readonly(db_path)
    try:
        schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
        tables = _table_names(connection)
        report["facts"]["database"] = {"schema_version": schema_version, "integrity": integrity}
        report["evidence"].append(
            {"source": "SQLite locale", "type": "contrôle d'intégrité", "date": as_of, "identifier": f"schema:{schema_version}"}
        )
        required = {"deck_versions", "deck_version_cards", "battle_logs", "battle_deck_versions"}
        if not required.issubset(tables):
            report["unknowns"].append(_unknown("SCHEMA_UNSUPPORTED", "Le schéma local ne contient pas les tables minimales du diagnostic."))
            report["next_evidence"].append("Mettre la base locale à niveau avec une commande d'écriture explicitement autorisée.")
            return report

        deck = _deck_fact(connection, deck_id, as_of)
        selected_id = deck.pop("selected_version_id", None)
        report["facts"]["deck"] = deck
        historical_applicability = deck.get("historical_applicability")
        report["facts"]["battles"] = _battle_fact(
            connection,
            deck_id,
            selected_id,
            as_of,
            selected_version_applicable=historical_applicability == "applicable",
            selected_version_effective_date=(str(deck.get("effective_from") or "")[:10] or None),
        )
        if not deck["found"]:
            report["unknowns"].append(_unknown("DECK_NOT_FOUND", "Aucune version locale du deck demandé n'est disponible."))
            report["next_evidence"].append("Importer volontairement la version choisie du deck, idéalement l'export exact de 60 cartes.")
        else:
            report["evidence"].append(
                {"source": "deck local", "type": "version explicitement enregistrée", "date": deck["imported_at"], "identifier": deck["version_ref"]}
            )
            if not deck["constraints"]["effective_on_or_before_as_of"]:
                report["unknowns"].append(_unknown("LATEST_VERSION_OUTSIDE_AS_OF", "La dernière version reste sélectionnée, mais sa date n'est pas exploitable au contexte demandé; aucune ancienne version ne lui a été substituée."))
            if not deck["exact_confirmed"]:
                report["unknowns"].append(_unknown("DECK_VERSION_UNCONFIRMED", "La dernière version est non confirmée; une ancienne version exacte n'a pas été substituée."))
            if not deck["constraints"]["quantity_sum_is_60"] or not deck["constraints"]["recorded_total_matches_quantity_sum"]:
                report["unknowns"].append(_unknown("DECK_QUANTITY_INVALID", "Les quantités de la dernière version ne prouvent pas un deck exact de 60 cartes."))

        battles = report["facts"]["battles"]
        for observation in battles["observations"]:
            report["evidence"].append(
                {"source": "journal importé localement", "type": "observation de combat", "date": observation["observed_date"], "identifier": observation["reference"]}
            )
            if observation.get("confirmed_at"):
                report["evidence"].append(
                    {
                        "source": "déclaration explicite du propriétaire",
                        "type": observation["version_evidence"],
                        "date": observation["confirmed_at"],
                        "identifier": f"{observation['reference']}:owner-attestation",
                        "provenance": "owner_asserted",
                        "externally_verified": False,
                    }
                )
        if battles["valid_unique"] < 5:
            report["unknowns"].append(_unknown("BATTLE_SAMPLE_SMALL", f"Seulement {battles['valid_unique']} combat(s) valide(s) et unique(s) sont disponibles."))
        if battles["with_selected_version_proven"] < battles["valid_unique"]:
            report["unknowns"].append(_unknown("BATTLE_VERSION_LINK_INCOMPLETE", "Les résultats non liés explicitement ne sont pas attribués à la version sélectionnée."))
        if battles["with_selected_version_legacy_unattested"]:
            report["unknowns"].append(_unknown("LEGACY_LINK_UNATTESTED", "Des liens historiques restent des preuves limitées sans attestation propriétaire datée."))
        if battles["owner_attested_revoked"]:
            report["unknowns"].append(_unknown("OWNER_ATTESTATION_REVOKED", "Une attestation révoquée n'attribue plus le résultat à la version."))
        if battles["attestations_after_as_of"]:
            report["unknowns"].append(_unknown("OWNER_ATTESTATION_NOT_AVAILABLE_AS_OF", "Une confirmation postérieure n'est pas attribuée rétroactivement à ce contexte historique."))
        if battles["valid_unique"] <= 5:
            report["warnings"].append("Ce petit échantillon ne justifie ni taux de victoire généralisé, ni avantage de matchup, ni changement de carte.")

        if deck["found"] and schema_version >= 5 and {"catalog_printings", "catalog_translations", "catalog_sets"}.issubset(tables):
            try:
                report["facts"]["catalog"], catalog_unknowns = _catalog_fact(db_path, deck_id)
                report["facts"]["catalog"]["historical_applicability"] = historical_applicability
                report["unknowns"].extend(catalog_unknowns)
                coverage_date = report["facts"]["catalog"]["local_coverage"]["last_success_at"]
                report["evidence"].append(
                    {"source": "TCGdex (cache local)", "type": "couverture de catalogue", "date": coverage_date, "identifier": "catalog-cache"}
                )
            except (ValueError, sqlite3.DatabaseError):
                report["facts"]["catalog"] = {"available": False, "error": "catalog_unavailable"}
                report["unknowns"].append(_unknown("CATALOG_UNAVAILABLE", "Le moteur catalogue local est indisponible pour ce diagnostic; la cause technique est caviardée."))
        else:
            report["unknowns"].append(_unknown("CATALOG_UNAVAILABLE", "Le catalogue local n'est pas disponible pour ce deck."))

        if deck["found"] and schema_version >= 6 and {"official_rule_sources", "official_rule_assertions"}.issubset(tables):
            if historical_applicability != "applicable":
                report["facts"]["rules"] = {
                    "available": True,
                    "offline": True,
                    "as_of": as_of,
                    "format": format,
                    "platform": platform,
                    "status": "unknown",
                    "historical_applicability": historical_applicability,
                    "reason_codes": ["LATEST_VERSION_OUTSIDE_AS_OF"],
                    "structure_validation": {
                        "status": "unknown",
                        "reason_codes": ["LATEST_VERSION_OUTSIDE_AS_OF"],
                    },
                    "card_statuses": {"legal": 0, "not_legal": 0, "unknown": 0},
                    "sources_used": [],
                    "live_support": "unknown",
                    "ownership": "unknown",
                    "craftability": "unknown",
                }
                report["unknowns"].append(_unknown("LEGALITY_UNKNOWN", "La décision réglementaire n'est pas applicable historiquement à cette version datée après le contexte demandé."))
            else:
                try:
                    report["facts"]["rules"], rule_evidence = _rules_fact(
                        db_path, deck_id, format=format, platform=platform, as_of=as_of
                    )
                    report["facts"]["rules"]["historical_applicability"] = "applicable"
                    report["evidence"].extend(rule_evidence)
                    if report["facts"]["rules"]["status"] == "unknown":
                        report["unknowns"].append(_unknown("LEGALITY_UNKNOWN", "La légalité globale reste inconnue selon les règles officielles locales et leurs lacunes."))
                except (ValueError, sqlite3.DatabaseError):
                    report["facts"]["rules"] = {"available": False, "status": "unknown", "error": "rules_unavailable"}
                    report["unknowns"].append(_unknown("RULES_UNAVAILABLE", "Le moteur de règles local est indisponible pour ce diagnostic; la cause technique est caviardée."))
        else:
            report["unknowns"].append(_unknown("RULES_UNAVAILABLE", "Les sources officielles locales ne sont pas disponibles pour ce deck."))

        if schema_version >= 7 and {"meta_tournaments", "meta_placements", "meta_matches"}.issubset(tables):
            report["facts"]["metagame"] = _meta_fact(
                connection, format=format, platform=platform, as_of=as_of
            )
            meta = report["facts"]["metagame"]
            if meta["n_tournaments"]:
                report["evidence"].append(
                    {"source": "Limitless (cache local)", "type": "échantillon descriptif filtré", "date": meta["last_fetched_at"], "identifier": "meta-cache:context"}
                )
            if meta["excluded"]["snapshot_captured_after_as_of"]:
                report["unknowns"].append(_unknown("SNAPSHOT_NOT_AVAILABLE_AS_OF", "Au moins un événement antérieur n'avait pas encore de snapshot dans le cache local à la date demandée; sa date de capture n'est pas une date officielle de publication."))
            if meta["n_published_archetypes"] == 0:
                report["unknowns"].append(_unknown("META_ARCHETYPE_ABSENT", "Aucun archétype publié n'est disponible dans le même contexte; aucun matchup chiffré n'est produit."))
            else:
                report["unknowns"].append(_unknown("DECK_ARCHETYPE_MAPPING_UNPROVEN", "Aucune preuve fiable ne relie le deck local à un archétype Limitless publié."))
        else:
            report["unknowns"].append(_unknown("META_UNAVAILABLE", "Le cache métagame local n'est pas disponible."))
    finally:
        connection.close()

    next_evidence = report["next_evidence"]
    if report["facts"]["battles"]["valid_unique"] < 10:
        next_evidence.append("Importer volontairement plusieurs journaux complets supplémentaires, sans doublons, avec le deck utilisé identifié.")
    catalog = report["facts"]["catalog"]
    if not catalog.get("available") or catalog.get("entry_resolution", {}).get("resolved", 0) < catalog.get("entry_resolution", {}).get("denominator", 1):
        next_evidence.append("Résoudre localement les impressions ambiguës ou absentes avant toute comparaison de cartes.")
    rules = report["facts"]["rules"]
    if rules.get("status") != "legal":
        next_evidence.append("Compléter la validation officielle datée de la structure, des quotas, du Pokémon de base et des réimpressions.")
    meta = report["facts"]["metagame"]
    if not meta.get("available") or meta.get("n_published_archetypes", 0) == 0:
        next_evidence.append("Collecter un échantillon public Limitless compatible qui publie réellement les archétypes.")
    next_evidence.append("Fournir volontairement un inventaire et des coûts vérifiés avant toute estimation de cartes manquantes ou de crédits.")
    report["next_evidence"] = list(dict.fromkeys(next_evidence))[:5]
    report["unknowns"] = list({item["code"]: item for item in report["unknowns"]}.values())
    report["warnings"].extend(
        [
            "Une carte observée ne prouve ni la liste de 60 cartes ni la collection.",
            "TCGdex ne prouve pas la disponibilité dans TCG Live; Limitless ne prouve pas le rendement du deck personnel.",
            "Aucun meilleur deck, achat, coût en crédits ou export automatique n'est justifié par ces preuves.",
        ]
    )
    deck_ok = (
        report["facts"]["deck"].get("exact_confirmed") is True
        and report["facts"]["deck"].get("historical_applicability") == "applicable"
    )
    resolved = report["facts"]["catalog"].get("entry_resolution", {})
    all_resolved = resolved.get("denominator", 0) > 0 and resolved.get("resolved") == resolved.get("denominator")
    version_links = report["facts"]["battles"]["with_selected_version_proven"]
    report["confidence"] = {
        "level": "modérée" if deck_ok and all_resolved and version_links >= 5 and report["facts"]["rules"].get("status") != "unknown" else "faible",
        "basis": [
            f"deck exact confirmé: {'oui' if deck_ok else 'non'}",
            f"applicabilité historique: {report['facts']['deck'].get('historical_applicability', 'unknown')}",
            f"impressions résolues: {resolved.get('resolved', 0)}/{resolved.get('denominator', 0)}",
            f"combats liés à la version sélectionnée: {version_links}",
            f"légalité globale: {report['facts']['rules'].get('status', 'unknown')}",
            f"archétypes Limitless publiés dans le contexte: {report['facts']['metagame'].get('n_published_archetypes', 0)}",
        ],
    }
    return report
