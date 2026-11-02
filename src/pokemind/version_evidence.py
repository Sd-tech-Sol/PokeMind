"""Comparaison de versions et provenance combat-version, hors ligne et en lecture seule."""

from __future__ import annotations

import sqlite3
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from pokemind.battle_logs import DECK_ID_RE
from pokemind.database import connect_readonly


CARD_TYPES = ("pokemon", "trainer", "energy")
REQUIRED_TABLES = {
    "deck_versions",
    "deck_version_cards",
    "battle_logs",
    "battle_deck_versions",
    "battle_events",
}


def _strict_date(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        parsed = date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("--as-of doit être une date ISO stricte YYYY-MM-DD.") from exc
    if parsed.isoformat() != value:
        raise ValueError("--as-of doit être une date ISO stricte YYYY-MM-DD.")
    return value


def _date_part(value: Any) -> str | None:
    candidate = str(value or "")[:10]
    try:
        return date.fromisoformat(candidate).isoformat()
    except ValueError:
        return None


def _tables(connection: sqlite3.Connection) -> set[str]:
    return {
        str(row[0])
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }


def _unknown(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def _normalize_identity_text(value: Any) -> str:
    normalized = unicodedata.normalize("NFC", str(value or "")).strip()
    return " ".join(normalized.split()).casefold()


def _identity(row: sqlite3.Row) -> tuple[tuple[str, str, str, str], bool]:
    set_code = _normalize_identity_text(row["set_code"])
    collector_number = _normalize_identity_text(row["collector_number"])
    return (
        (
            _normalize_identity_text(row["card_type"]),
            set_code,
            collector_number,
            _normalize_identity_text(row["card_name"]),
        ),
        not bool(set_code and collector_number),
    )


def _comparison_base(
    deck_id: str,
    from_version: int,
    to_version: int,
    *,
    as_of: str | None,
    show_changes: bool,
) -> dict[str, Any]:
    return {
        "read_only": True,
        "network_used": False,
        "context": {
            "deck_id": deck_id,
            "from_version": from_version,
            "to_version": to_version,
            "as_of": as_of,
            "show_changes": show_changes,
        },
        "comparison_status": "DATA_UNAVAILABLE",
        "confidence": {"level": "faible", "basis": []},
        "facts": {
            "available_versions": 0,
            "from": None,
            "to": None,
            "changes": None,
            "legality": "unknown",
            "strategic_advantage": "unknown",
            "collection": "unknown",
        },
        "identity_limits": {
            "key_fields": [
                "card_type",
                "set_code",
                "collector_number",
                "card_name",
            ],
            "normalization": "Unicode NFC, espaces regroupés, casse ignorée",
            "functional_reprints_merged": False,
            "missing_set_or_number": 0,
            "message": (
                "Un nom seul, même identique en français ou en anglais, ne prouve pas "
                "l'identité d'une impression ni l'équivalence d'une réimpression."
            ),
        },
        "evidence": [],
        "unknowns": [],
        "next_evidence": [],
        "warnings": [
            "La comparaison est descriptive: elle ne prouve ni légalité, ni possession, ni avantage stratégique.",
        ],
    }


def _version_rows(
    connection: sqlite3.Connection, deck_id: str, version_number: int
) -> tuple[sqlite3.Row | None, list[sqlite3.Row]]:
    version = connection.execute(
        """SELECT id, version_number, imported_at, approved_at, effective_from,
                  exact_confirmed, total_cards, entry_count
           FROM deck_versions WHERE deck_id=? AND version_number=?""",
        (deck_id, version_number),
    ).fetchone()
    if version is None:
        return None, []
    cards = connection.execute(
        """SELECT ordinal, card_type, quantity, card_name, set_code, collector_number
           FROM deck_version_cards WHERE deck_version_id=? ORDER BY ordinal""",
        (version["id"],),
    ).fetchall()
    return version, cards


def _version_fact(
    version: sqlite3.Row, cards: list[sqlite3.Row], *, as_of: str | None
) -> tuple[dict[str, Any], dict[tuple[str, str, str, str], dict[str, Any]]]:
    quantities = {card_type: 0 for card_type in CARD_TYPES}
    lines = {card_type: 0 for card_type in CARD_TYPES}
    invalid_rows = 0
    identities: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    uncertain_lines = 0
    for row in cards:
        card_type = str(row["card_type"] or "")
        quantity = row["quantity"]
        if (
            card_type not in CARD_TYPES
            or isinstance(quantity, bool)
            or not isinstance(quantity, int)
            or not 1 <= quantity <= 60
        ):
            invalid_rows += 1
            continue
        quantities[card_type] += quantity
        lines[card_type] += 1
        key, uncertain = _identity(row)
        uncertain_lines += int(uncertain)
        current = identities.setdefault(
            key,
            {
                "card_type": card_type,
                "card_name": str(row["card_name"] or ""),
                "set_code": row["set_code"],
                "collector_number": row["collector_number"],
                "quantity": 0,
                "identity_uncertain": uncertain,
            },
        )
        current["quantity"] += quantity
        current["identity_uncertain"] = bool(
            current["identity_uncertain"] or uncertain
        )

    quantity_sum = sum(quantities.values())
    exact = bool(version["exact_confirmed"])
    recorded_total = int(version["total_cards"])
    effective_date = _date_part(version["effective_from"] or version["imported_at"])
    dates_valid = all(
        _date_part(version[field]) is not None
        for field in ("imported_at", "approved_at", "effective_from")
    )
    if as_of is None:
        applicability = "not_requested"
    elif effective_date is None:
        applicability = "unknown"
    else:
        applicability = "applicable" if effective_date <= as_of else "not_applicable"
    checks = {
        "exact_confirmed": exact,
        "recorded_total_is_60": recorded_total == 60,
        "quantity_sum_is_60": quantity_sum == 60,
        "recorded_total_matches_quantity_sum": recorded_total == quantity_sum,
        "entry_count_matches_rows": int(version["entry_count"]) == len(cards),
        "all_rows_valid": invalid_rows == 0,
        "dates_valid": dates_valid,
    }
    fact = {
        "version": int(version["version_number"]),
        "reference": f"deck-version:v{int(version['version_number'])}",
        "imported_at": version["imported_at"],
        "approved_at": version["approved_at"],
        "effective_from": version["effective_from"],
        "historical_applicability": applicability,
        "status": "valid" if all(checks.values()) else "invalid",
        "exact_confirmed": exact,
        "recorded_total": recorded_total,
        "quantity_sum": quantity_sum,
        "lines": {
            "total": len(cards),
            "denominator": int(version["entry_count"]),
            "by_section": lines,
        },
        "cards": {"total": quantity_sum, "denominator": recorded_total, "by_section": quantities},
        "sections": {
            "present": sum(1 for value in lines.values() if value > 0),
            "denominator": len(CARD_TYPES),
        },
        "identity": {
            "distinct_impressions": len(identities),
            "uncertain_lines": uncertain_lines,
            "line_denominator": len(cards),
        },
        "checks": checks,
    }
    return fact, identities


def compare_deck_versions(
    db_path: Path,
    deck_id: str,
    *,
    from_version: int,
    to_version: int,
    as_of: str | None = None,
    show_changes: bool = False,
) -> dict[str, Any]:
    """Compare deux numéros de version explicites sans écrire ni contacter le réseau."""
    if not DECK_ID_RE.fullmatch(deck_id):
        raise ValueError(
            "Identifiant de deck invalide (1-64 caractères: lettres, chiffres, . _ -)."
        )
    for value in (from_version, to_version):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValueError("Les numéros de version doivent être des entiers positifs.")
    as_of = _strict_date(as_of)
    report = _comparison_base(
        deck_id,
        from_version,
        to_version,
        as_of=as_of,
        show_changes=show_changes,
    )
    if from_version == to_version:
        report["comparison_status"] = "SAME_VERSION_NOT_ALLOWED"
        report["unknowns"].append(
            _unknown("SAME_VERSION_NOT_ALLOWED", "Choisir deux numéros de version différents.")
        )
        return report
    if not db_path.is_file():
        report["comparison_status"] = "DATABASE_MISSING"
        report["unknowns"].append(
            _unknown("DATABASE_MISSING", "La base locale est absente; aucun fichier n'a été créé.")
        )
        return report

    try:
        connection = connect_readonly(db_path)
        try:
            connection.execute("PRAGMA query_only = ON")
            schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            tables = _tables(connection)
            if not {"deck_versions", "deck_version_cards"}.issubset(tables):
                report["comparison_status"] = "SCHEMA_UNSUPPORTED"
                report["unknowns"].append(
                    _unknown("SCHEMA_UNSUPPORTED", "Le schéma local ne contient pas les tables requises.")
                )
                return report
            count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM deck_versions WHERE deck_id=?", (deck_id,)
                ).fetchone()[0]
            )
            report["facts"]["available_versions"] = count
            report["facts"]["database"] = {
                "schema_version": schema_version,
                "integrity": str(connection.execute("PRAGMA integrity_check").fetchone()[0]),
            }
            if count == 0:
                report["comparison_status"] = "DECK_NOT_FOUND"
                report["unknowns"].append(
                    _unknown("DECK_NOT_FOUND", "Aucune version locale du deck demandé n'est disponible.")
                )
                return report
            if count < 2:
                report["comparison_status"] = "INSUFFICIENT_DECK_VERSIONS"
                report["unknowns"].append(
                    _unknown(
                        "INSUFFICIENT_DECK_VERSIONS",
                        "Deux exports complets et confirmés du même deck sont requis.",
                    )
                )
                report["next_evidence"].append(
                    "Importer volontairement un second export complet de 60 cartes du même deck."
                )
                return report

            from_row, from_cards = _version_rows(connection, deck_id, from_version)
            to_row, to_cards = _version_rows(connection, deck_id, to_version)
            if from_row is None or to_row is None:
                report["comparison_status"] = "VERSION_NOT_FOUND"
                report["unknowns"].append(
                    _unknown(
                        "VERSION_NOT_FOUND",
                        "Au moins un numéro demandé n'appartient pas au deck choisi; aucune substitution n'a été faite.",
                    )
                )
                return report

            from_fact, from_identities = _version_fact(from_row, from_cards, as_of=as_of)
            to_fact, to_identities = _version_fact(to_row, to_cards, as_of=as_of)
            report["facts"]["from"] = from_fact
            report["facts"]["to"] = to_fact
            report["evidence"].extend(
                {
                    "source": "deck local",
                    "type": "version explicitement enregistrée",
                    "date": fact["imported_at"],
                    "identifier": fact["reference"],
                }
                for fact in (from_fact, to_fact)
            )
            if from_fact["status"] != "valid" or to_fact["status"] != "valid":
                report["comparison_status"] = "INVALID_DECK_VERSION"
                report["unknowns"].append(
                    _unknown(
                        "INVALID_DECK_VERSION",
                        "Les deux versions doivent être confirmées, cohérentes et totaliser exactement 60 cartes.",
                    )
                )
                return report

            keys = sorted(set(from_identities) | set(to_identities))
            details: list[dict[str, Any]] = []
            added = removed = changed_quantity = increased = decreased = 0
            uncertain_changes = 0
            for key in keys:
                old = from_identities.get(key)
                new = to_identities.get(key)
                old_quantity = int(old["quantity"]) if old else 0
                new_quantity = int(new["quantity"]) if new else 0
                delta = new_quantity - old_quantity
                if delta == 0:
                    continue
                identity = new or old
                assert identity is not None
                added += int(old_quantity == 0)
                removed += int(new_quantity == 0)
                changed_quantity += int(old_quantity > 0 and new_quantity > 0)
                increased += max(delta, 0)
                decreased += max(-delta, 0)
                uncertain = bool(identity["identity_uncertain"])
                uncertain_changes += int(uncertain)
                if show_changes:
                    details.append(
                        {
                            "card_type": identity["card_type"],
                            "card_name": identity["card_name"],
                            "set_code": identity["set_code"],
                            "collector_number": identity["collector_number"],
                            "from_quantity": old_quantity,
                            "to_quantity": new_quantity,
                            "delta": delta,
                            "identity_uncertain": uncertain,
                        }
                    )

            delta_total = to_fact["quantity_sum"] - from_fact["quantity_sum"]
            changes: dict[str, Any] = {
                "impressions_added": added,
                "impressions_removed": removed,
                "impressions_with_quantity_changed": changed_quantity,
                "quantity_increased": increased,
                "quantity_decreased": decreased,
                "delta_total": delta_total,
                "changed_impressions": len(details) if show_changes else added + removed + changed_quantity,
                "identity_uncertain_changes": uncertain_changes,
                "details_included": show_changes,
            }
            if show_changes:
                changes["details"] = details
                report["warnings"].append(
                    "PRIVÉ — détails de cartes affichés localement sur demande; ne pas partager."
                )
            report["facts"]["changes"] = changes
            missing_identity = (
                from_fact["identity"]["uncertain_lines"]
                + to_fact["identity"]["uncertain_lines"]
            )
            report["identity_limits"]["missing_set_or_number"] = missing_identity
            if missing_identity:
                report["unknowns"].append(
                    _unknown(
                        "IDENTITY_UNCERTAIN",
                        "Au moins une ligne sans code de set ou numéro demeure une identité incertaine.",
                    )
                )
            outside = [
                fact["version"]
                for fact in (from_fact, to_fact)
                if fact["historical_applicability"] != "applicable" and as_of is not None
            ]
            if outside:
                report["unknowns"].append(
                    _unknown(
                        "VERSION_OUTSIDE_AS_OF",
                        "Au moins une version n'est pas historiquement applicable à la date demandée; elle n'a pas été remplacée.",
                    )
                )
            report["comparison_status"] = "COMPARISON_AVAILABLE"
            report["confidence"] = {
                "level": "modérée" if not missing_identity and not outside else "faible",
                "basis": [
                    "deux versions explicitement choisies, confirmées et à 60 cartes",
                    "comparaison stricte par impression; aucune équivalence fonctionnelle inférée",
                    f"identités incertaines parmi les changements: {uncertain_changes}",
                ],
            }
            report["next_evidence"].extend(
                [
                    "Résoudre toute identité sans code de set et numéro avant une interprétation carte par carte.",
                    "Vérifier séparément légalité, support Live, collection et coût avant toute recommandation.",
                ]
            )
            return report
        finally:
            connection.close()
    except sqlite3.DatabaseError:
        report["comparison_status"] = "DATABASE_UNAVAILABLE"
        report["unknowns"].append(
            _unknown(
                "DATABASE_UNAVAILABLE",
                "La base locale ne peut pas être lue pour cette comparaison; le détail technique est caviardé.",
            )
        )
        return report


def _outcome_bucket(value: Any) -> str:
    normalized = str(value or "").strip().casefold()
    if normalized in {"w", "win", "victoire"}:
        return "wins"
    if normalized in {"l", "loss", "défaite", "defaite"}:
        return "losses"
    if normalized in {"d", "draw", "tie", "nul", "nulle"}:
        return "draws"
    return "ambiguous"


def _evidence_base(deck_id: str, as_of: str) -> dict[str, Any]:
    return {
        "read_only": True,
        "network_used": False,
        "context": {"deck_id": deck_id, "as_of": as_of},
        "evidence_status": "DATA_UNAVAILABLE",
        "confidence": {"level": "faible", "basis": []},
        "facts": {
            "versions": [],
            "battles": {
                "valid_unique_declared_deck": 0,
                "duplicates_excluded": 0,
                "excluded_after_as_of": 0,
                "excluded_invalid_date": 0,
                "explicit_links_present": 0,
                "proven_same_deck_links": 0,
                "unlinked": 0,
                "legacy_explicit_link_unattested": 0,
                "owner_attested_active": 0,
                "owner_attested_revoked": 0,
                "conflict": 0,
                "temporal_unknown": 0,
                "conflicting_links": 0,
                "temporal_doubts": 0,
                "event_count_inconsistencies": 0,
                "outcomes": {"wins": 0, "losses": 0, "draws": 0, "ambiguous": 0},
                "period": {"from": None, "to": None},
            },
            "performance_comparison": {
                "status": "not_produced",
                "rates": None,
                "reason": "Seuls des liens explicites, cohérents et des échantillons suffisants permettraient une comparaison descriptive ultérieure.",
            },
            "date_semantics": (
                "imported_at est la date d'import locale, pas nécessairement la date réelle de la partie; "
                "sa concordance ne prouve jamais seule la version jouée."
            ),
        },
        "evidence": [],
        "confirmations": [],
        "unknowns": [],
        "next_evidence": [],
        "warnings": [
            "Aucun taux prédictif, matchup, avantage de version ou causalité n'est calculé.",
            "Une attestation owner_asserted est une déclaration du propriétaire, pas une vérification indépendante.",
        ],
        "future_recommendation_contract": {
            "requires": [
                "versions exactes de 60 cartes",
                "liens explicites combat-version confirmés par l'utilisateur",
                "cohérence du deck et de la temporalité",
                "échantillons attribués suffisants avec n affiché",
                "légalité et identités d'impressions vérifiées séparément",
                "collection et coûts fournis volontairement si nécessaires",
            ],
            "automatic_attribution_allowed": False,
        },
    }


def _attestation_at_date(
    history: list[sqlite3.Row], as_of: str
) -> tuple[str | None, sqlite3.Row | None]:
    """Reconstitue l'état connu à la date demandée sans antidater la confirmation."""
    available: list[sqlite3.Row] = []
    invalid = False
    for row in history:
        confirmed = _date_part(row["confirmed_at"])
        if confirmed is None:
            invalid = True
            continue
        if confirmed <= as_of:
            available.append(row)
    if not available:
        if invalid:
            return "conflict", None
        return ("temporal_unknown", None) if history else (None, None)
    latest = max(available, key=lambda item: (str(item["confirmed_at"]), int(item["id"])))
    revoked = _date_part(latest["revoked_at"])
    if latest["revoked_at"] is not None and revoked is None:
        return "conflict", latest
    if revoked is not None and revoked <= as_of:
        return "owner_attested_revoked", latest
    return "owner_attested_active", latest


def version_evidence(db_path: Path, deck_id: str, *, as_of: str) -> dict[str, Any]:
    """Audite les liens stockés battle_deck_versions sans en créer ni en modifier."""
    if not DECK_ID_RE.fullmatch(deck_id):
        raise ValueError(
            "Identifiant de deck invalide (1-64 caractères: lettres, chiffres, . _ -)."
        )
    as_of = _strict_date(as_of) or ""
    report = _evidence_base(deck_id, as_of)
    if not db_path.is_file():
        report["evidence_status"] = "DATABASE_MISSING"
        report["unknowns"].append(
            _unknown("DATABASE_MISSING", "La base locale est absente; aucun fichier n'a été créé.")
        )
        return report

    try:
        connection = connect_readonly(db_path)
        try:
            connection.execute("PRAGMA query_only = ON")
            schema_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
            if not REQUIRED_TABLES.issubset(_tables(connection)):
                report["evidence_status"] = "SCHEMA_UNSUPPORTED"
                report["unknowns"].append(
                    _unknown("SCHEMA_UNSUPPORTED", "Le schéma local ne contient pas les tables requises.")
                )
                return report
            report["facts"]["database"] = {
                "schema_version": schema_version,
                "integrity": str(connection.execute("PRAGMA integrity_check").fetchone()[0]),
            }
            version_rows = connection.execute(
                """SELECT v.id, v.version_number, v.exact_confirmed, v.total_cards,
                          COALESCE(SUM(c.quantity), 0) AS quantity_sum
                   FROM deck_versions v
                   LEFT JOIN deck_version_cards c ON c.deck_version_id=v.id
                   WHERE v.deck_id=?
                   GROUP BY v.id ORDER BY v.version_number""",
                (deck_id,),
            ).fetchall()
            attribution: dict[int, dict[str, Any]] = {}
            for row in version_rows:
                version_number = int(row["version_number"])
                entry = {
                    "version": version_number,
                    "reference": f"deck-version:v{version_number}",
                    "exact_confirmed": bool(row["exact_confirmed"]),
                    "recorded_total": int(row["total_cards"]),
                    "quantity_sum": int(row["quantity_sum"]),
                    "linked_battles": 0,
                    "owner_attested_battles": 0,
                    "legacy_unattested_battles": 0,
                    "outcomes": {"wins": 0, "losses": 0, "draws": 0, "ambiguous": 0},
                    "rate": None,
                }
                attribution[int(row["id"])] = entry
                report["facts"]["versions"].append(entry)

            rows = connection.execute(
                """SELECT b.id, b.source_sha256, b.imported_at, b.outcome,
                          b.recognized_events,
                          (SELECT COUNT(*) FROM battle_events e WHERE e.battle_id=b.id) AS event_count,
                          link.deck_version_id, link.effective_from AS link_effective_from,
                          link.approved_at AS link_approved_at,
                          linked.deck_id AS linked_deck_id,
                          linked.version_number AS linked_version,
                          linked.effective_from AS version_effective_from,
                          linked.approved_at AS version_approved_at,
                          linked.exact_confirmed AS linked_exact_confirmed,
                          linked.total_cards AS linked_total_cards,
                          (SELECT COALESCE(SUM(c.quantity), 0)
                             FROM deck_version_cards c
                            WHERE c.deck_version_id=linked.id) AS linked_quantity_sum
                   FROM battle_logs b
                   LEFT JOIN battle_deck_versions link ON link.battle_id=b.id
                   LEFT JOIN deck_versions linked ON linked.id=link.deck_version_id
                   WHERE b.deck_id=? AND b.valid=1
                   ORDER BY b.imported_at, b.id""",
                (deck_id,),
            ).fetchall()

            attestation_history: dict[int, list[sqlite3.Row]] = defaultdict(list)
            if "battle_version_attestations" in _tables(connection):
                attestation_rows = connection.execute(
                    """SELECT a.id, a.battle_id, a.deck_version_id, a.confirmed_at,
                              a.status, a.revoked_at, a.asserted_battle_date,
                              a.provenance, a.actor,
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
                ).fetchall()
                for attestation in attestation_rows:
                    attestation_history[int(attestation["battle_id"])].append(attestation)

            seen: set[str] = set()
            kept: list[sqlite3.Row] = []
            counters = report["facts"]["battles"]
            for row in rows:
                observed_date = _date_part(row["imported_at"])
                if observed_date is None:
                    counters["excluded_invalid_date"] += 1
                    continue
                if observed_date > as_of:
                    counters["excluded_after_as_of"] += 1
                    continue
                identity = str(row["source_sha256"] or f"battle-id:{row['id']}")
                if identity in seen:
                    counters["duplicates_excluded"] += 1
                    continue
                seen.add(identity)
                kept.append(row)

            dates: list[str] = []
            for ordinal, row in enumerate(kept, start=1):
                reference = f"local-observation-{ordinal:03d}"
                observed_date = _date_part(row["imported_at"])
                assert observed_date is not None
                dates.append(observed_date)
                outcome = _outcome_bucket(row["outcome"])
                counters["outcomes"][outcome] += 1
                if int(row["recognized_events"] or 0) != int(row["event_count"] or 0):
                    counters["event_count_inconsistencies"] += 1

                linked_id = row["deck_version_id"]
                history = attestation_history.get(int(row["id"]), [])
                attestation_state, attestation = _attestation_at_date(history, as_of)
                if attestation_state == "temporal_unknown":
                    counters["temporal_unknown"] += 1
                    counters["temporal_doubts"] += 1
                    report["confirmations"].append(
                        {
                            "reference": reference,
                            "imported_date": observed_date,
                            "link_state": "temporal_unknown",
                            "reason": "OWNER_CONFIRMATION_NOT_AVAILABLE_AS_OF",
                            "request": "La confirmation propriétaire est postérieure à la date demandée.",
                        }
                    )
                    continue
                if attestation_state == "owner_attested_revoked":
                    assert attestation is not None
                    counters["owner_attested_revoked"] += 1
                    report["confirmations"].append(
                        {
                            "reference": reference,
                            "imported_date": observed_date,
                            "link_state": "owner_attested_revoked",
                            "confirmed_at": attestation["confirmed_at"],
                            "revoked_at": attestation["revoked_at"],
                            "reason": "OWNER_ATTESTATION_REVOKED",
                            "request": "Aucun ancien résultat n'est attribué après la révocation.",
                        }
                    )
                    continue
                if attestation_state == "owner_attested_active":
                    assert attestation is not None
                    owner_conflict = None
                    if attestation["attested_deck_id"] is None:
                        owner_conflict = "ATTESTED_VERSION_MISSING"
                    elif str(attestation["attested_deck_id"]) != deck_id:
                        owner_conflict = "ATTESTED_VERSION_OTHER_DECK"
                    elif not bool(attestation["attested_exact_confirmed"]):
                        owner_conflict = "ATTESTED_VERSION_UNCONFIRMED"
                    elif int(attestation["attested_total_cards"] or 0) != 60 or int(
                        attestation["attested_quantity_sum"] or 0
                    ) != 60:
                        owner_conflict = "ATTESTED_VERSION_NOT_60"
                    elif str(attestation["status"]) == "active" and (
                        linked_id is None
                        or int(linked_id) != int(attestation["deck_version_id"])
                    ):
                        owner_conflict = "ACTIVE_ATTESTATION_LINK_CONFLICT"
                    version_key = int(attestation["deck_version_id"])
                    if version_key not in attribution:
                        owner_conflict = owner_conflict or "ATTESTED_VERSION_NOT_SELECTED_DECK"
                    if owner_conflict:
                        counters["conflict"] += 1
                        counters["conflicting_links"] += 1
                        report["confirmations"].append(
                            {
                                "reference": reference,
                                "imported_date": observed_date,
                                "link_state": "conflict",
                                "reason": owner_conflict,
                                "request": "Corriger le conflit sans écraser l'historique d'attestation.",
                            }
                        )
                        continue
                    counters["explicit_links_present"] += 1
                    counters["owner_attested_active"] += 1
                    counters["proven_same_deck_links"] += 1
                    attribution[version_key]["linked_battles"] += 1
                    attribution[version_key]["owner_attested_battles"] += 1
                    attribution[version_key]["outcomes"][outcome] += 1
                    report["evidence"].append(
                        {
                            "source": "déclaration explicite du propriétaire",
                            "type": "owner_attested_active",
                            "provenance": "owner_asserted",
                            "externally_verified": False,
                            "date": attestation["confirmed_at"],
                            "asserted_battle_date": attestation["asserted_battle_date"] or "unknown",
                            "identifier": f"local-attestation-{ordinal:03d}",
                            "observation": reference,
                            "version": int(attestation["attested_version"]),
                        }
                    )
                    continue
                if attestation_state == "conflict":
                    counters["conflict"] += 1
                    counters["conflicting_links"] += 1
                    report["confirmations"].append(
                        {
                            "reference": reference,
                            "imported_date": observed_date,
                            "link_state": "conflict",
                            "reason": "ATTESTATION_DATE_INVALID",
                            "request": "Corriger la donnée d'audit sans inventer de date.",
                        }
                    )
                    continue
                if linked_id is None:
                    counters["unlinked"] += 1
                    report["confirmations"].append(
                        {
                            "reference": reference,
                            "imported_date": observed_date,
                            "link_state": "unlinked",
                            "reason": "NO_EXPLICIT_VERSION_LINK",
                            "request": "Confirmer volontairement l'export exact utilisé pour cette partie.",
                        }
                    )
                    continue

                counters["explicit_links_present"] += 1
                conflict_reason: str | None = None
                if row["linked_deck_id"] is None:
                    conflict_reason = "LINKED_VERSION_MISSING"
                elif str(row["linked_deck_id"]) != deck_id:
                    conflict_reason = "LINKED_VERSION_OTHER_DECK"
                elif not bool(row["linked_exact_confirmed"]):
                    conflict_reason = "LINKED_VERSION_UNCONFIRMED"
                elif int(row["linked_total_cards"] or 0) != 60 or int(
                    row["linked_quantity_sum"] or 0
                ) != 60:
                    conflict_reason = "LINKED_VERSION_NOT_60"
                elif (
                    _date_part(row["link_effective_from"]) is not None
                    and _date_part(row["version_effective_from"]) is not None
                    and _date_part(row["link_effective_from"])
                    != _date_part(row["version_effective_from"])
                ) or (
                    _date_part(row["link_approved_at"]) is not None
                    and _date_part(row["version_approved_at"]) is not None
                    and _date_part(row["link_approved_at"])
                    != _date_part(row["version_approved_at"])
                ):
                    conflict_reason = "LINK_PROVENANCE_MISMATCH"

                if conflict_reason:
                    counters["conflict"] += 1
                    counters["conflicting_links"] += 1
                    report["confirmations"].append(
                        {
                            "reference": reference,
                            "imported_date": observed_date,
                            "link_state": "conflict",
                            "reason": conflict_reason,
                            "request": "Confirmer le deck et la version; le lien stocké est incohérent.",
                        }
                    )
                    continue

                version_date = _date_part(row["version_effective_from"])
                link_date = _date_part(row["link_effective_from"])
                version_approved_date = _date_part(row["version_approved_at"])
                link_approved_date = _date_part(row["link_approved_at"])
                if (
                    version_date is None
                    or link_date is None
                    or version_approved_date is None
                    or link_approved_date is None
                    or version_date > observed_date
                    or link_date > observed_date
                    or version_approved_date > as_of
                    or link_approved_date > as_of
                ):
                    counters["temporal_unknown"] += 1
                    counters["temporal_doubts"] += 1
                    report["confirmations"].append(
                        {
                            "reference": reference,
                            "imported_date": observed_date,
                            "link_state": "temporal_unknown",
                            "reason": "TEMPORAL_COMPATIBILITY_UNCERTAIN",
                            "request": (
                                "Confirmer la date réelle de la partie et la version; "
                                "la date d'import ne suffit pas."
                            ),
                        }
                    )
                    continue

                counters["proven_same_deck_links"] += 1
                counters["legacy_explicit_link_unattested"] += 1
                version_key = int(linked_id)
                if version_key not in attribution:
                    counters["conflict"] += 1
                    counters["conflicting_links"] += 1
                    counters["proven_same_deck_links"] -= 1
                    counters["legacy_explicit_link_unattested"] -= 1
                    continue
                attribution[version_key]["linked_battles"] += 1
                attribution[version_key]["legacy_unattested_battles"] += 1
                attribution[version_key]["outcomes"][outcome] += 1
                report["evidence"].append(
                    {
                        "source": "lien local explicitement stocké",
                        "type": "legacy_explicit_link_unattested",
                        "provenance": "legacy_link_unattested",
                        "externally_verified": False,
                        "date": row["link_approved_at"],
                        "identifier": f"local-link-{ordinal:03d}",
                        "observation": reference,
                        "version": int(row["linked_version"]),
                    }
                )

            counters["valid_unique_declared_deck"] = len(kept)
            counters["period"] = {
                "from": min(dates) if dates else None,
                "to": max(dates) if dates else None,
            }
            report["evidence_status"] = "EVIDENCE_AUDIT_AVAILABLE"
            if not version_rows:
                report["unknowns"].append(
                    _unknown("DECK_VERSION_MISSING", "Le deck déclaré n'a aucune version exacte locale.")
                )
            if counters["unlinked"]:
                report["unknowns"].append(
                    _unknown(
                        "UNLINKED_BATTLES",
                        "Des combats déclarent ce deck sans prouver la version de 60 cartes utilisée.",
                    )
                )
            if counters["legacy_explicit_link_unattested"]:
                report["unknowns"].append(
                    _unknown(
                        "LEGACY_LINK_UNATTESTED",
                        "Des liens historiques explicites n'ont pas d'attestation propriétaire datée; leur preuve reste limitée.",
                    )
                )
            if counters["owner_attested_revoked"]:
                report["unknowns"].append(
                    _unknown(
                        "OWNER_ATTESTATION_REVOKED",
                        "Des attestations ont été révoquées et leurs résultats ne sont plus attribués.",
                    )
                )
            if counters["conflicting_links"]:
                report["unknowns"].append(
                    _unknown("CONFLICTING_VERSION_LINKS", "Des liens stockés sont incohérents avec le deck ou la version.")
                )
            if counters["temporal_doubts"]:
                report["unknowns"].append(
                    _unknown(
                        "TEMPORAL_LINK_DOUBTS",
                        "Des liens exigent une confirmation de date réelle; l'import n'est pas la date certaine de jeu.",
                    )
                )
            if counters["event_count_inconsistencies"]:
                report["unknowns"].append(
                    _unknown(
                        "BATTLE_EVENT_COUNT_INCONSISTENT",
                        "Au moins un compteur de journal diffère de ses événements normalisés.",
                    )
                )
            sample = counters["valid_unique_declared_deck"]
            linked = counters["proven_same_deck_links"]
            report["confidence"] = {
                "level": "faible" if linked < 5 else "modérée",
                "basis": [
                    f"combats valides uniques déclarés pour le deck: {sample}",
                    f"liens explicites cohérents: {linked}",
                    f"attestations propriétaire actives: {counters['owner_attested_active']}",
                    f"liens legacy non attestés: {counters['legacy_explicit_link_unattested']}",
                    f"combats sans lien: {counters['unlinked']}",
                    "la date d'import locale n'est pas une date certaine de partie",
                ],
            }
            report["facts"]["sample_conclusion"] = (
                "aucune observation exploitable"
                if sample == 0
                else "conclusion exploratoire; aucun taux de victoire prédictif"
            )
            report["next_evidence"].append(
                "Obtenir les confirmations listées avant toute attribution historique supplémentaire."
            )
            if len(version_rows) < 2:
                report["next_evidence"].append(
                    "Importer volontairement une seconde version complète avant toute comparaison d'évolution."
                )
            return report
        finally:
            connection.close()
    except sqlite3.DatabaseError:
        report["evidence_status"] = "DATABASE_UNAVAILABLE"
        report["unknowns"].append(
            _unknown(
                "DATABASE_UNAVAILABLE",
                "La base locale ne peut pas être lue pour cet audit; le détail technique est caviardé.",
            )
        )
        return report
