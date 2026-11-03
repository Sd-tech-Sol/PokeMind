"""Registre officiel daté et moteur conservateur de légalité PM-0005A."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pokemind.database import connect_readonly, connect_writable, initialize_schema, utc_now


FORMATS = ("standard", "expanded")
PLATFORMS = ("live", "in_person")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._/-]{0,199}$")
_OFFICIAL_HOSTS = {"www.pokemon.com", "play.pokemon.com", "assets.pokemon.com"}


class RulesError(ValueError):
    """Erreur contrôlée du registre normatif."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _iso_date(value: str | None, field: str, *, required: bool = False) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str):
        raise RulesError(f"{field} doit être une date ISO.")
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise RulesError(f"{field} doit être au format YYYY-MM-DD.") from exc


def _safe_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise RulesError(f"{field} invalide.")
    return value


def _safe_official_url(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 1000:
        raise RulesError("URL officielle invalide.")
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname not in _OFFICIAL_HOSTS or parsed.username:
        raise RulesError("Seuls les domaines HTTPS officiels Pokémon sont permis.")
    return value


def default_registry_path(root: Path) -> Path:
    return root / "knowledge" / "curated" / "official_rules_2026.json"


def _read_registry(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("sources"), list):
        raise RulesError("Registre officiel JSON invalide.")
    if not isinstance(payload.get("assertions"), list):
        raise RulesError("Assertions officielles JSON invalides.")
    if not isinstance(payload.get("deck_structure_rules", []), list):
        raise RulesError("Règles de construction officielles JSON invalides.")
    if (
        len(payload["sources"]) > 100
        or len(payload["assertions"]) > 1000
        or len(payload.get("deck_structure_rules", [])) > 100
    ):
        raise RulesError("Registre officiel trop volumineux.")
    return payload


def load_official_registry(db_path: Path, registry_path: Path) -> dict[str, Any]:
    """Charge explicitement un petit registre versionné; aucun accès réseau."""
    payload = _read_registry(registry_path)
    captured_at = payload.get("consulted_at")
    if not isinstance(captured_at, str) or len(captured_at) > 40:
        raise RulesError("Horodatage de consultation invalide.")
    source_ids: set[str] = set()
    source_statuses: dict[str, str] = {}
    source_rows: list[tuple[Any, ...]] = []
    for source in payload["sources"]:
        if not isinstance(source, dict):
            raise RulesError("Source officielle invalide.")
        source_id = _safe_id(source.get("source_id"), "source_id")
        if source_id in source_ids:
            raise RulesError(f"Source en double: {source_id}.")
        source_ids.add(source_id)
        status = source.get("validation_status")
        if status not in {"verified", "navigation_only", "non_verified", "conflict"}:
            raise RulesError(f"Statut de source invalide: {source_id}.")
        source_statuses[source_id] = status
        source_consulted_at = source.get("consulted_at", captured_at)
        source_captured_at = source.get("captured_at", source_consulted_at)
        if (
            not isinstance(source_consulted_at, str)
            or not isinstance(source_captured_at, str)
            or len(source_consulted_at) > 40
            or len(source_captured_at) > 40
        ):
            raise RulesError(f"Horodatage de source invalide: {source_id}.")
        content_hash = hashlib.sha256(_canonical_json(source).encode("utf-8")).hexdigest()
        source_rows.append((
            source_id, str(source.get("source_type", ""))[:80],
            _safe_official_url(source.get("url")), str(source.get("title", ""))[:500],
            str(source.get("language", ""))[:10],
            _iso_date(source.get("published_date"), "published_date"), source_consulted_at,
            source_captured_at, content_hash, status,
            _iso_date(source.get("effective_from"), "effective_from"),
            _iso_date(source.get("effective_to"), "effective_to"),
            str(source.get("rights_note", ""))[:1000], str(source.get("notes", ""))[:2000] or None,
        ))
    assertion_rows: list[tuple[Any, ...]] = []
    assertion_ids: set[str] = set()
    kinds = {"rotation", "restriction", "restriction_coverage", "reprint_equivalence",
             "reprint_policy", "release_window", "promo", "errata"}
    for assertion in payload["assertions"]:
        if not isinstance(assertion, dict):
            raise RulesError("Assertion officielle invalide.")
        assertion_id = _safe_id(assertion.get("assertion_id"), "assertion_id")
        source_id = _safe_id(assertion.get("source_id"), "source_id")
        if assertion_id in assertion_ids or source_id not in source_ids:
            raise RulesError(f"Assertion en double ou source inconnue: {assertion_id}.")
        assertion_ids.add(assertion_id)
        kind = assertion.get("assertion_kind")
        fmt, platform = assertion.get("format"), assertion.get("platform")
        if kind not in kinds or fmt not in {*FORMATS, None} or platform not in {*PLATFORMS, None}:
            raise RulesError(f"Portée invalide: {assertion_id}.")
        status = assertion.get("validation_status")
        confidence = assertion.get("confidence")
        if status not in {"verified", "non_verified", "conflict"} or confidence not in {"high", "medium", "low"}:
            raise RulesError(f"Validation invalide: {assertion_id}.")
        if status == "verified" and source_statuses[source_id] != "verified":
            raise RulesError(
                f"Assertion verified sans source verified: {assertion_id} "
                f"({source_id}={source_statuses[source_id]})."
            )
        subject_id = assertion.get("subject_id")
        if subject_id is not None:
            subject_id = _safe_id(subject_id, "subject_id")
        assertion_rows.append((
            assertion_id, source_id, kind, fmt, platform,
            _iso_date(assertion.get("effective_from"), "effective_from"),
            _iso_date(assertion.get("effective_to"), "effective_to"), subject_id,
            _canonical_json(assertion.get("payload", {})), status, confidence, captured_at,
        ))
    structure_rows: list[tuple[Any, ...]] = []
    structure_ids: set[str] = set()
    for rule in payload.get("deck_structure_rules", []):
        if not isinstance(rule, dict):
            raise RulesError("Règle de construction officielle invalide.")
        rule_id = _safe_id(rule.get("rule_id"), "rule_id")
        source_id = _safe_id(rule.get("source_id"), "source_id")
        if rule_id in structure_ids or source_id not in source_ids:
            raise RulesError(f"Règle en double ou source inconnue: {rule_id}.")
        structure_ids.add(rule_id)
        fmt, platform = rule.get("format"), rule.get("platform")
        status, confidence = rule.get("validation_status"), rule.get("confidence")
        if fmt not in {*FORMATS, None} or platform not in {*PLATFORMS, None}:
            raise RulesError(f"Portée de construction invalide: {rule_id}.")
        if status not in {"verified", "non_verified", "conflict"}:
            raise RulesError(f"Validation de construction invalide: {rule_id}.")
        if confidence not in {"high", "medium", "low"}:
            raise RulesError(f"Confiance de construction invalide: {rule_id}.")
        if status == "verified" and source_statuses[source_id] != "verified":
            raise RulesError(
                f"Règle de construction verified sans source verified: {rule_id}."
            )
        rule_payload = rule.get("payload")
        if not isinstance(rule_payload, dict):
            raise RulesError(f"Payload de construction invalide: {rule_id}.")
        required_total = rule_payload.get("required_total")
        same_name_limit = rule_payload.get("same_name_limit")
        if (
            isinstance(required_total, bool)
            or not isinstance(required_total, int)
            or not 1 <= required_total <= 100
            or isinstance(same_name_limit, bool)
            or not isinstance(same_name_limit, int)
            or not 1 <= same_name_limit <= 60
        ):
            raise RulesError(f"Limites de construction invalides: {rule_id}.")
        for key in (
            "basic_energy_unlimited",
            "requires_basic_pokemon",
            "copy_limit_exceptions_complete",
            "special_rule_limits_complete",
        ):
            if not isinstance(rule_payload.get(key), bool):
                raise RulesError(f"Indicateur de construction invalide: {rule_id}.{key}.")
        structure_rows.append((
            rule_id, source_id, fmt, platform,
            _iso_date(rule.get("effective_from"), "effective_from"),
            _iso_date(rule.get("effective_to"), "effective_to"),
            _canonical_json(rule_payload), status, confidence, captured_at,
        ))
    connection = connect_writable(db_path)
    try:
        initialize_schema(connection)
        with connection:
            connection.executemany(
                """INSERT INTO official_rule_sources
                   (source_id, source_type, url, title, language, published_date, consulted_at,
                    captured_at, content_sha256, validation_status, effective_from, effective_to,
                    rights_note, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(source_id) DO UPDATE SET
                    source_type=excluded.source_type, url=excluded.url, title=excluded.title,
                    language=excluded.language, published_date=excluded.published_date,
                    consulted_at=excluded.consulted_at, captured_at=excluded.captured_at,
                    content_sha256=excluded.content_sha256, validation_status=excluded.validation_status,
                    effective_from=excluded.effective_from, effective_to=excluded.effective_to,
                    rights_note=excluded.rights_note, notes=excluded.notes""",
                source_rows,
            )
            connection.executemany(
                """INSERT INTO official_rule_assertions
                   (assertion_id, source_id, assertion_kind, format, platform, effective_from,
                    effective_to, subject_id, payload_json, validation_status, confidence, captured_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(assertion_id) DO UPDATE SET
                    source_id=excluded.source_id, assertion_kind=excluded.assertion_kind,
                    format=excluded.format, platform=excluded.platform,
                    effective_from=excluded.effective_from, effective_to=excluded.effective_to,
                    subject_id=excluded.subject_id, payload_json=excluded.payload_json,
                    validation_status=excluded.validation_status, confidence=excluded.confidence,
                    captured_at=excluded.captured_at""",
                assertion_rows,
            )
            connection.executemany(
                """INSERT INTO official_deck_structure_rules
                   (rule_id, source_id, format, platform, effective_from,
                    effective_to, payload_json, validation_status, confidence,
                    captured_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(rule_id) DO UPDATE SET
                    source_id=excluded.source_id, format=excluded.format,
                    platform=excluded.platform, effective_from=excluded.effective_from,
                    effective_to=excluded.effective_to,
                    payload_json=excluded.payload_json,
                    validation_status=excluded.validation_status,
                    confidence=excluded.confidence, captured_at=excluded.captured_at""",
                structure_rows,
            )
            connection.execute(
                """INSERT INTO metadata(key, value) VALUES('official_rules_loaded_at', ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""", (utc_now(),)
            )
            connection.execute(
                """INSERT INTO metadata(key, value) VALUES('official_rules_registry_version', ?)
                   ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                (str(payload.get("registry_version", "unknown"))[:100],),
            )
        return {
            "database": str(db_path), "registry": str(registry_path), "network_used": False,
            "sources_loaded": len(source_rows), "assertions_loaded": len(assertion_rows),
            "deck_structure_rules_loaded": len(structure_rows),
            "registry_version": payload.get("registry_version"), "consulted_at": captured_at,
        }
    finally:
        connection.close()


def _require_rules_db(db_path: Path) -> Any:
    if not db_path.is_file():
        raise FileNotFoundError("Base locale absente; charger d'abord le registre officiel.")
    connection = connect_readonly(db_path)
    if int(connection.execute("PRAGMA user_version").fetchone()[0]) < 6:
        connection.close()
        raise RulesError("Registre officiel non initialisé; exécuter 'rules load-official'.")
    return connection


def rules_sources(db_path: Path) -> dict[str, Any]:
    connection = _require_rules_db(db_path)
    try:
        rows = connection.execute(
            """SELECT source_id, source_type, url, title, language, published_date,
                      consulted_at, content_sha256, validation_status, effective_from,
                      effective_to, rights_note, notes
               FROM official_rule_sources ORDER BY source_id"""
        ).fetchall()
        return {"database": str(db_path), "offline": True, "count": len(rows),
                "sources": [dict(row) for row in rows]}
    finally:
        connection.close()


def rules_status(db_path: Path) -> dict[str, Any]:
    connection = _require_rules_db(db_path)
    try:
        metadata = dict(connection.execute("SELECT key, value FROM metadata").fetchall())
        source_counts = dict(connection.execute(
            "SELECT validation_status, COUNT(*) FROM official_rule_sources GROUP BY validation_status"
        ).fetchall())
        assertion_counts = dict(connection.execute(
            "SELECT validation_status, COUNT(*) FROM official_rule_assertions GROUP BY validation_status"
        ).fetchall())
        structure_counts = dict(connection.execute(
            """SELECT validation_status, COUNT(*)
               FROM official_deck_structure_rules GROUP BY validation_status"""
        ).fetchall())
        structure_windows = [dict(row) for row in connection.execute(
            """SELECT r.rule_id, r.format, r.platform, r.effective_from,
                      r.effective_to, r.validation_status, r.confidence,
                      r.source_id, s.validation_status AS source_validation_status,
                      s.consulted_at
               FROM official_deck_structure_rules r
               JOIN official_rule_sources s USING(source_id)
               ORDER BY r.effective_from, r.rule_id"""
        ).fetchall()]
        latest = connection.execute("SELECT MAX(consulted_at) FROM official_rule_sources").fetchone()[0]
        return {
            "database": str(db_path), "offline": True,
            "schema_version": int(connection.execute("PRAGMA user_version").fetchone()[0]),
            "registry_version": metadata.get("official_rules_registry_version"),
            "loaded_at": metadata.get("official_rules_loaded_at"), "latest_consulted_at": latest,
            "source_counts": source_counts, "assertion_counts": assertion_counts,
            "deck_structure_rule_counts": structure_counts,
            "deck_structure_windows": structure_windows,
            "coverage": {
                "standard_2026_rotation": "consult_dated_normative_evidence",
                "restriction_registry": "partial",
                "reprint_equivalences": "examples_not_mapped_to_tcgdex",
                "promos": "dynamic_source_known_but_entries_not_loaded",
                "expanded_live_support": "not_verified",
                "deck_structure": (
                    "verified_rules_with_incomplete_exception_registry"
                    if structure_counts.get("verified", 0) else "not_loaded"
                ),
            },
            "normative_evidence": normative_coverage(db_path),
        }
    finally:
        connection.close()


def normative_coverage(db_path: Path, *, as_of: str | None = None) -> dict[str, Any]:
    """Dated, source-backed dimensions; counts never certify exhaustive registries."""
    cutoff = _iso_date(as_of or date.today().isoformat(), "as_of", required=True)
    missing = {"status": "unknown", "complete": False, "verified_items": 0, "pending_items": 0}
    dimensions = {name: dict(missing) for name in (
        "standard_rotation_live", "standard_rotation_in_person", "restrictions",
        "deck_structure", "reprints", "errata", "promos", "expanded_eligibility", "live_support",
    )}
    result = {"as_of": cutoff, "read_only": True, "network_used": False, "complete": False, "dimensions": dimensions}
    if not db_path.is_file():
        return result
    connection = connect_readonly(db_path)
    try:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"official_rule_sources", "official_rule_assertions"}.issubset(tables):
            return result
        rows = connection.execute(
            """SELECT a.*,s.validation_status AS source_status,s.consulted_at,s.published_date,
                      s.effective_from AS source_effective_from,s.effective_to AS source_effective_to
               FROM official_rule_assertions a JOIN official_rule_sources s USING(source_id)"""
        ).fetchall()

        def active(row):
            return _active(row, cutoff) and _source_active(row, cutoff)

        def verified(row):
            return (row["validation_status"] == row["source_status"] == "verified"
                    and bool(row["consulted_at"]) and str(row["consulted_at"])[:10] <= cutoff
                    and bool(row["captured_at"]) and str(row["captured_at"])[:10] <= cutoff
                    and (not row["published_date"] or row["published_date"] <= cutoff))

        for platform in PLATFORMS:
            relevant = [row for row in rows if active(row) and row["assertion_kind"] == "rotation" and row["format"] == "standard" and row["platform"] == platform]
            trusted = [row for row in relevant if verified(row)]
            payload = json.loads(trusted[0]["payload_json"]) if len(trusted) == 1 else {}
            complete = len(relevant) == len(trusted) == 1 and isinstance(payload.get("allowed_regulation_marks"), list) and bool(payload["allowed_regulation_marks"])
            dimensions[f"standard_rotation_{platform}"] = {
                "status": "verified" if complete else "unknown", "complete": complete,
                "verified_items": len(trusted), "pending_items": len(relevant) - len(trusted),
                "sources": [{"source_id": row["source_id"], "consulted_at": row["consulted_at"], "assertion_id": row["assertion_id"]} for row in trusted],
            }
        for name, kinds in {"restrictions": {"restriction", "restriction_coverage"}, "reprints": {"reprint_equivalence", "reprint_policy"}, "errata": {"errata"}, "promos": {"promo", "release_window"}}.items():
            relevant = [row for row in rows if active(row) and row["assertion_kind"] in kinds]
            trusted = [row for row in relevant if verified(row)]
            # No schema-level complete registry attestation currently exists for
            # reprints/promos/errata/Live/Expanded. Do not mint it from one example.
            dimensions[name] = {**missing, "status": "partial" if trusted else "unknown", "verified_items": len(trusted), "pending_items": len(relevant) - len(trusted), "reason_code": "EXHAUSTIVE_DATED_REGISTRY_NOT_PROVEN"}
        if "official_deck_structure_rules" in tables:
            structures = connection.execute(
                """SELECT r.*,s.validation_status AS source_status,s.consulted_at,s.published_date,
                          s.effective_from AS source_effective_from,s.effective_to AS source_effective_to
                   FROM official_deck_structure_rules r JOIN official_rule_sources s USING(source_id)"""
            ).fetchall()
            trusted = [row for row in structures if active(row) and verified(row)]
            dimensions["deck_structure"] = {**missing, "status": "partial" if trusted else "unknown", "verified_items": len(trusted), "reason_code": "ALL_CONTEXTS_AND_EXCEPTIONS_NOT_PROVEN"}
        return result
    finally:
        connection.close()


def _active(row: Any, as_of: str) -> bool:
    return (row["effective_from"] is None or row["effective_from"] <= as_of) and (
        row["effective_to"] is None or row["effective_to"] >= as_of
    )


def _source_active(row: Any, as_of: str) -> bool:
    return (row["source_effective_from"] is None or row["source_effective_from"] <= as_of) and (
        row["source_effective_to"] is None or row["source_effective_to"] >= as_of
    )


def _relevant_to_printing(row: Any, tcgdex_id: str) -> bool:
    return row["subject_id"] is None or row["subject_id"] == tcgdex_id


def _source_refs(rows: list[Any]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        if row["source_id"] in seen:
            continue
        seen.add(row["source_id"])
        result.append({"source_id": row["source_id"], "title": row["title"],
                       "url": row["url"], "published_date": row["published_date"],
                       "consulted_at": row["consulted_at"],
                       "validation_status": row["source_validation_status"]})
    return result


def check_card(
    db_path: Path, tcgdex_id: str, *, format: str, platform: str, as_of: str
) -> dict[str, Any]:
    tcgdex_id = _safe_id(tcgdex_id, "tcgdex_id")
    if format not in FORMATS or platform not in PLATFORMS:
        raise RulesError("Format ou plateforme invalide.")
    as_of = _iso_date(as_of, "as_of", required=True) or ""
    connection = _require_rules_db(db_path)
    try:
        printing = connection.execute(
            """SELECT p.tcgdex_id, p.regulation_mark, p.set_id, p.local_id,
                      MAX(CASE WHEN t.status='present' THEN 1 ELSE 0 END) AS has_detail
               FROM catalog_printings p LEFT JOIN catalog_translations t
                 ON t.printing_id=p.tcgdex_id WHERE p.tcgdex_id=? GROUP BY p.tcgdex_id""",
            (tcgdex_id,),
        ).fetchone()
        base = {
            "tcgdex_id": tcgdex_id, "format": format, "platform": platform, "as_of": as_of,
            "jurisdiction": "Play! Pokémon international", "status": "unknown",
            "confidence": "low", "reason_codes": [], "sources": [], "missing_data": [],
            "live_printing_support": "unknown", "ownership": "unknown", "craftability": "unknown",
        }
        if printing is None:
            base["reason_codes"] = ["PRINTING_NOT_FOUND_LOCAL"]
            base["missing_data"] = ["catalog_printing"]
            return base
        rows = connection.execute(
            """SELECT a.*, a.validation_status AS assertion_validation_status,
                      s.title, s.url, s.published_date, s.consulted_at,
                      s.validation_status AS source_validation_status,
                      s.effective_from AS source_effective_from,
                      s.effective_to AS source_effective_to
               FROM official_rule_assertions a JOIN official_rule_sources s USING(source_id)
               WHERE (a.format=? OR a.format IS NULL) AND (a.platform=? OR a.platform IS NULL)""",
            (format, platform),
        ).fetchall()
        relevant = [row for row in rows if _active(row, as_of) and _relevant_to_printing(row, tcgdex_id)]
        # This command assesses effective rules retrospectively. Collection time
        # is not publication time; historical knowledge coverage is separate.
        unavailable = [row for row in relevant if _source_active(row, as_of)
                       and row["published_date"] and row["published_date"] > as_of]
        if unavailable:
            base["reason_codes"] = ["OFFICIAL_EVIDENCE_NOT_AVAILABLE_AS_OF"]
            base["sources"] = _source_refs(unavailable)
            return base
        source_conflicts = [
            row for row in relevant
            if _source_active(row, as_of) and row["source_validation_status"] == "conflict"
        ]
        if source_conflicts:
            base["reason_codes"] = ["CONFLICTING_OFFICIAL_SOURCES"]
            base["sources"] = _source_refs(source_conflicts)
            return base
        conflicts = [
            row for row in relevant
            if _source_active(row, as_of) and row["assertion_validation_status"] == "conflict"
        ]
        if conflicts:
            base["reason_codes"] = ["CONFLICTING_OFFICIAL_ASSERTIONS"]
            base["sources"] = _source_refs(conflicts)
            return base
        unverified_sources = [
            row for row in relevant
            if _source_active(row, as_of) and row["source_validation_status"] != "verified"
        ]
        if unverified_sources:
            base["reason_codes"] = ["UNVERIFIED_NORMATIVE_SOURCE"]
            base["sources"] = _source_refs(unverified_sources)
            base["missing_data"] = ["verified_normative_source"]
            return base
        unverified_assertions = [
            row for row in relevant
            if _source_active(row, as_of) and row["assertion_validation_status"] != "verified"
        ]
        if unverified_assertions:
            base["reason_codes"] = ["UNVERIFIED_OFFICIAL_ASSERTION"]
            base["sources"] = _source_refs(unverified_assertions)
            base["missing_data"] = ["verified_official_assertion"]
            return base
        active = [
            row for row in rows
            if _active(row, as_of)
            and _source_active(row, as_of)
            and row["assertion_validation_status"] == "verified"
            and row["source_validation_status"] == "verified"
        ]
        equivalents = [row for row in active if row["assertion_kind"] == "reprint_equivalence" and row["subject_id"] == tcgdex_id]
        payloads = [json.loads(row["payload_json"]) for row in equivalents]
        targets = {p.get("current_printing_id") for p in payloads if p.get("current_printing_id")}
        if len(targets) > 1 or (targets and any(p.get("no_current_equivalent") for p in payloads)):
            base.update(reason_codes=["CONFLICTING_OFFICIAL_ASSERTIONS"], sources=_source_refs(equivalents))
            return base
        restrictions = [row for row in active if row["assertion_kind"] == "restriction"
                        and row["subject_id"] == tcgdex_id]
        if restrictions:
            base.update(status="not_legal", confidence="high",
                        reason_codes=["EXPLICIT_OFFICIAL_RESTRICTION"],
                        sources=_source_refs(restrictions))
            return base
        if format == "expanded":
            base["reason_codes"] = ["EXPANDED_ELIGIBILITY_NOT_MAPPED"]
            if platform == "live":
                base["reason_codes"].append("EXPANDED_LIVE_SUPPORT_NOT_PROVEN")
            base["missing_data"] = ["expanded_identity_eligibility", "complete_restriction_registry"]
            return base
        rotations = [row for row in active if row["assertion_kind"] == "rotation"
                     ]
        if len(rotations) != 1:
            base["reason_codes"] = ["NO_UNIQUE_ACTIVE_ROTATION"]
            base["missing_data"] = ["dated_rotation"]
            return base
        rotation = rotations[0]
        payload = json.loads(rotation["payload_json"])
        allowed = set(payload.get("allowed_regulation_marks", []))
        mark = printing["regulation_mark"]
        base["regulation_mark"] = mark
        base["sources"] = _source_refs([rotation])
        release_rules = [row for row in active if row["assertion_kind"] in {"release_window", "promo"}
                         and row["subject_id"] in {None, tcgdex_id}]
        release_required = any(row["subject_id"] is None and
            json.loads(row["payload_json"]).get("requires_printing_legal_from") is True for row in release_rules)
        dated_release_rules = []
        for rule in (row for row in release_rules if row["subject_id"] == tcgdex_id):
            rule_payload = json.loads(rule["payload_json"])
            legal_from = rule_payload.get("legal_from")
            if legal_from is not None:
                try:
                    legal_from = _iso_date(legal_from, "legal_from", required=True)
                except RulesError:
                    base.update(reason_codes=["OFFICIAL_RELEASE_DATE_INVALID"], sources=_source_refs([rule]),
                                missing_data=["verified_printing_legal_from"])
                    return base
                dated_release_rules.append(rule)
            if legal_from and as_of < legal_from:
                base.update(status="not_legal", confidence="high",
                            reason_codes=["WAITING_PERIOD_ACTIVE"],
                            sources=_source_refs([rotation, rule]))
                return base
        if release_required and not dated_release_rules:
            base.update(reason_codes=["OFFICIAL_RELEASE_DATE_NOT_VERIFIED"],
                        sources=_source_refs([rotation, *release_rules]), missing_data=["verified_printing_legal_from"])
            return base
        coverage = [row for row in active if row["assertion_kind"] == "restriction_coverage"
                    and json.loads(row["payload_json"]).get("complete") is True]
        if mark not in allowed:
            equivalents = [row for row in active if row["assertion_kind"] == "reprint_equivalence"
                           and row["subject_id"] == tcgdex_id]
            if not equivalents:
                base["reason_codes"] = ["MARK_OUTSIDE_ROTATION" if mark else "REGULATION_MARK_UNKNOWN",
                                        "REPRINT_EQUIVALENCE_UNVERIFIED"]
                base["missing_data"] = ["functional_identity"] if mark else ["regulation_mark", "functional_identity"]
                return base
            if any(json.loads(row["payload_json"]).get("no_current_equivalent") for row in equivalents):
                base.update(status="not_legal", confidence="high",
                            reason_codes=["MARK_OUTSIDE_ROTATION", "NO_VERIFIED_CURRENT_REPRINT"],
                            sources=_source_refs([rotation, *equivalents]))
                return base
            targets = {
                json.loads(row["payload_json"]).get("current_printing_id")
                for row in equivalents
                if json.loads(row["payload_json"]).get("current_printing_id")
            }
            if len(targets) == 1 and coverage:
                target_id = next(iter(targets))
                target_evidence = [row for row in rows if _active(row, as_of) and _source_active(row, as_of)
                                   and row["subject_id"] == target_id]
                if any(row["source_validation_status"] != "verified" or row["assertion_validation_status"] != "verified"
                       or row["published_date"] and row["published_date"] > as_of
                       or row["assertion_kind"] == "restriction" for row in target_evidence):
                    base.update(reason_codes=["REPRINT_TARGET_NOT_VERIFIED_LEGAL"], sources=_source_refs(target_evidence))
                    return base
                try:
                    target_dates = [_iso_date(json.loads(row["payload_json"]).get("legal_from"), "legal_from")
                                    for row in target_evidence if row["assertion_kind"] in {"release_window", "promo"}]
                except RulesError:
                    target_dates = ["invalid"]
                if (release_required and not any(target_dates) or any(value and
                        (value == "invalid" or value > as_of) for value in target_dates)):
                    base.update(reason_codes=["REPRINT_TARGET_RELEASE_NOT_VERIFIED"],
                                missing_data=["verified_reprint_target_legal_from"])
                    return base
                target = connection.execute(
                    "SELECT regulation_mark FROM catalog_printings WHERE tcgdex_id=?",
                    (target_id,),
                ).fetchone()
                if target is not None and target["regulation_mark"] in allowed:
                    base.update(
                        status="legal", confidence="high",
                        reason_codes=["FUNCTIONAL_REPRINT_VERIFIED", "RESTRICTIONS_CHECKED"],
                        sources=_source_refs([rotation, *equivalents, *coverage]),
                    )
                    return base
            base["reason_codes"] = ["REPRINT_EQUIVALENCE_PRESENT_BUT_TARGET_NOT_EVALUATED"]
            base["missing_data"] = ["current_reprint_status"]
            return base
        if not coverage:
            base["reason_codes"] = ["MARK_ELIGIBLE", "RESTRICTIONS_NOT_FULLY_VERIFIED"]
            base["missing_data"] = ["complete_restriction_registry"]
            return base
        base.update(status="legal", confidence="high", reason_codes=["MARK_ELIGIBLE", "RESTRICTIONS_CHECKED"],
                    sources=_source_refs([rotation, *coverage]))
        return base
    finally:
        connection.close()


def _normalized_name(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return " ".join(unicodedata.normalize("NFC", value).casefold().split())


def _is_basic_stage(value: Any) -> bool:
    return _normalized_name(value) in {"basic", "base", "de base"}


def _is_basic_energy_type(value: Any) -> bool:
    return _normalized_name(value) in {
        "basic", "base", "normal", "basic energy", "energie de base", "énergie de base"
    }


def _structure_rule_context(
    connection: Any, *, format: str, platform: str, as_of: str
) -> dict[str, Any]:
    rows = connection.execute(
        """SELECT r.*, r.validation_status AS rule_validation_status,
                  s.title, s.url, s.published_date, s.consulted_at,
                  s.validation_status AS source_validation_status,
                  s.effective_from AS source_effective_from,
                  s.effective_to AS source_effective_to
           FROM official_deck_structure_rules r
           JOIN official_rule_sources s USING(source_id)
           WHERE (r.format=? OR r.format IS NULL)
             AND (r.platform=? OR r.platform IS NULL)""",
        (format, platform),
    ).fetchall()
    active = [row for row in rows if _active(row, as_of) and _source_active(row, as_of)]
    sources = _source_refs(active)
    if not active:
        return {
            "status": "unknown", "payload": None,
            "reason_codes": ["DECK_STRUCTURE_RULE_NOT_FOUND"], "sources": [],
        }
    if any(row["published_date"] and row["published_date"] > as_of for row in active):
        return {"status": "unknown", "payload": None,
                "reason_codes": ["DECK_STRUCTURE_EVIDENCE_NOT_AVAILABLE_AS_OF"], "sources": sources}
    if any(
        row["rule_validation_status"] == "conflict"
        or row["source_validation_status"] == "conflict"
        for row in active
    ):
        return {
            "status": "unknown", "payload": None,
            "reason_codes": ["CONFLICTING_DECK_STRUCTURE_RULES"], "sources": sources,
        }
    verified = [
        row for row in active
        if row["rule_validation_status"] == "verified"
        and row["source_validation_status"] == "verified"
    ]
    if len(verified) != len(active):
        return {
            "status": "unknown", "payload": None,
            "reason_codes": ["UNVERIFIED_DECK_STRUCTURE_SOURCE"], "sources": sources,
        }
    payloads = {str(row["payload_json"]) for row in verified}
    if len(payloads) != 1:
        return {
            "status": "unknown", "payload": None,
            "reason_codes": ["CONFLICTING_DECK_STRUCTURE_PAYLOADS"], "sources": sources,
        }
    return {
        "status": "verified", "payload": json.loads(next(iter(payloads))),
        "reason_codes": [], "sources": _source_refs(verified),
        "rule_ids": [str(row["rule_id"]) for row in verified],
    }


def _resolve_structure_identity(connection: Any, entry: Any, *, set_aliases: dict | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ids": [], "canonical_name": None, "canonical_name_proven": False,
        "category": None, "stage": None, "basic_energy": None,
        "basic_pokemon": None, "rarity": None, "resolution_reason": "PRINTING_IDENTITY_INCOMPLETE",
    }
    if not entry["set_code"] or not entry["collector_number"]:
        return result
    alias_evidence = []
    set_ids = []
    # Older or minimal catalogues have no rarity column: the special limits then stay unverified.
    rarity = "p.rarity" if any(row[1] == "rarity" for row in connection.execute(
        "PRAGMA table_info(catalog_printings)")) else "NULL AS rarity"
    if set_aliases is not None:
        from pokemind.set_code_aliases import alias_sets
        set_ids, alias_evidence = alias_sets(set_aliases, entry["set_code"])
        native_ids = [r[0] for r in connection.execute(
            "SELECT tcgdex_id FROM catalog_sets WHERE lower(tcg_online_code)=lower(?)", (entry["set_code"],))]
        if len(set(set_ids + native_ids)) > 1:
            result["resolution_reason"] = "SET_CODE_ALIAS_AMBIGUOUS"
            result["alias_evidence"] = alias_evidence
            return result
    rows = connection.execute(
        f"""SELECT p.tcgdex_id, p.category, p.stage, {rarity}, t.language, t.name,
                  t.energy_type
           FROM catalog_printings p
           JOIN catalog_sets s ON s.tcgdex_id=p.set_id
           LEFT JOIN catalog_translations t ON t.printing_id=p.tcgdex_id AND t.status='present'
           WHERE lower(s.tcg_online_code)=lower(?) AND p.local_id=?
           ORDER BY p.tcgdex_id, t.language""",
        (entry["set_code"], entry["collector_number"]),
    ).fetchall()
    if set_ids:
        from pokemind.set_code_aliases import collector_key
        candidates = connection.execute(
            f"""SELECT p.tcgdex_id,p.category,p.stage,{rarity},t.language,t.name,t.energy_type,p.local_id
               FROM catalog_printings p LEFT JOIN catalog_translations t
               ON t.printing_id=p.tcgdex_id AND t.status='present'
               WHERE p.set_id=? ORDER BY p.tcgdex_id,t.language""", (set_ids[0],)).fetchall()
        rows = [r for r in candidates if collector_key(r["local_id"]) == collector_key(entry["collector_number"])
                and any(m["id"] == r["tcgdex_id"] and collector_key(m["number"]) == collector_key(r["local_id"])
                        and _normalized_name(m["name"]) == _normalized_name(r["name"])
                        for e in alias_evidence if e["language"] == r["language"] for m in e["members"])]
        result["alias_evidence"] = [{k: v for k, v in e.items() if k != "members"} for e in alias_evidence]
        result["alias_version"] = set_aliases["version"]
    if not rows:
        mapped = connection.execute("SELECT 1 FROM catalog_sets WHERE lower(tcg_online_code)=lower(?) LIMIT 1",
                                    (entry["set_code"],)).fetchone()
        result["resolution_reason"] = "COLLECTOR_NUMBER_NOT_FOUND" if mapped or set_ids else "SET_CODE_MAPPING_MISSING"
        return result
    by_id: dict[str, list[Any]] = {}
    for row in rows:
        by_id.setdefault(str(row["tcgdex_id"]), []).append(row)
    matching = {
        printing_id: values for printing_id, values in by_id.items()
        if any(
            _normalized_name(value["name"]) == _normalized_name(entry["card_name"])
            for value in values
        )
    }
    result["ids"] = sorted(matching)
    result["resolution_reason"] = ("PRINTING_RESOLVED" if len(matching) == 1 else
                                   "PRINTING_AMBIGUOUS" if matching else "CATALOG_NAME_OR_PRESENT_TRANSLATION_MISSING")
    if len(matching) != 1:
        return result
    values = next(iter(matching.values()))
    first = values[0]
    english_names = [value["name"] for value in values if value["language"] == "en" and value["name"]]
    result.update(
        canonical_name=english_names[0] if len(set(english_names)) == 1 else None,
        canonical_name_proven=len(set(english_names)) == 1,
        category=first["category"],
        stage=first["stage"],
        rarity=first["rarity"],
    )
    category = _normalized_name(first["category"])
    energy_types = {value["energy_type"] for value in values if value["energy_type"]}
    energy_classes = {_is_basic_energy_type(value) for value in energy_types}
    result["basic_energy"] = (
        (next(iter(energy_classes)) if len(energy_classes) == 1 else None)
        if category == "energy" else False if category else None
    )
    known_stage = _normalized_name(first["stage"]) in {
        "basic", "base", "de base", "stage1", "stage2", "stage 1", "stage 2", "niveau 1", "niveau 2"
    }
    result["basic_pokemon"] = (
        (_is_basic_stage(first["stage"]) if known_stage else None)
        if category == "pokemon" else False if category else None
    )
    return result


def check_deck(
    db_path: Path, deck_id: str, *, format: str, platform: str, as_of: str
) -> dict[str, Any]:
    if not _ID_RE.fullmatch(deck_id):
        raise RulesError("Identifiant de deck invalide.")
    if format not in FORMATS or platform not in PLATFORMS:
        raise RulesError("Format ou plateforme invalide.")
    as_of = _iso_date(as_of, "as_of", required=True) or ""
    connection = _require_rules_db(db_path)
    try:
        version = connection.execute(
            """SELECT id, version_number, exact_confirmed, total_cards
               FROM deck_versions WHERE deck_id=? ORDER BY version_number DESC LIMIT 1""",
            (deck_id,),
        ).fetchone()
        if version is None:
            raise RulesError(f"Aucune version pour le deck {deck_id}.")
        entries = connection.execute(
            """SELECT ordinal, quantity, card_name, set_code, collector_number
               FROM deck_version_cards WHERE deck_version_id=? ORDER BY ordinal""",
            (version["id"],),
        ).fetchall()
    finally:
        connection.close()

    result = check_deck_entries(db_path, entries, total_cards=int(version["total_cards"]),
                                exact_confirmed=int(version["exact_confirmed"]) == 1,
                                format=format, platform=platform, as_of=as_of)
    return {"deck_id": deck_id, "deck_version_id": int(version["id"]),
            "deck_version": int(version["version_number"]), **result}


def latest_verified_rotation(db_path: Path, *, format: str, platform: str, as_of: str) -> dict[str, Any] | None:
    """Most recent verified rotation already in force on ``as_of``.

    Rotation assertions are recorded with the window in which they were
    observed, so ``check_card`` turns every card ``unknown`` once that window
    closes. A rotation stays in force until a later one, so the last verified
    one supports a dated *presumption*, never a strict verdict.
    """
    if format not in FORMATS or platform not in PLATFORMS:
        raise RulesError("Format ou plateforme invalide.")
    as_of = _iso_date(as_of, "as_of", required=True) or ""
    connection = _require_rules_db(db_path)
    try:
        rows = connection.execute(
            """SELECT a.payload_json, a.effective_from, a.captured_at,
                      a.validation_status AS assertion_validation_status,
                      s.source_id, s.title, s.url, s.published_date, s.consulted_at,
                      s.validation_status AS source_validation_status
               FROM official_rule_assertions a JOIN official_rule_sources s USING(source_id)
               WHERE a.assertion_kind='rotation' AND a.format=? AND (a.platform=? OR a.platform IS NULL)""",
            (format, platform),
        ).fetchall()
    finally:
        connection.close()
    candidates = []
    for row in rows:
        if row["assertion_validation_status"] != "verified" or row["source_validation_status"] != "verified":
            continue
        if row["published_date"] and row["published_date"] > as_of:
            continue
        payload = json.loads(row["payload_json"])
        since = payload.get("rotation_effective_date") or row["effective_from"]
        marks = payload.get("allowed_regulation_marks")
        if not since or since > as_of or not isinstance(marks, list) or not marks:
            continue
        candidates.append((since, row["captured_at"] or "", row, tuple(sorted(set(marks)))))
    if not candidates:
        return None
    since = max(candidate[0] for candidate in candidates)
    current = sorted((c for c in candidates if c[0] == since), key=lambda c: c[1])
    if len({c[3] for c in current}) != 1:
        return None
    _, captured, row, marks = current[-1]
    return {"format": format, "platform": platform, "allowed_regulation_marks": list(marks),
            "in_force_since": since, "last_verified_on": captured[:10] or None,
            "source": {"source_id": row["source_id"], "title": row["title"], "url": row["url"],
                       "published_date": row["published_date"]}}


def presume_mark(mark: str | None, rotation: dict[str, Any] | None) -> dict[str, Any]:
    """Presumed Standard status of a regulation mark under the last verified rotation."""
    if rotation is None:
        return {"status": "unknown", "confidence": "low", "reason": "NO_VERIFIED_ROTATION"}
    marks = rotation["allowed_regulation_marks"]
    if not mark:
        status, reason = "unknown", "REGULATION_MARK_MISSING"
    elif mark in marks:
        status, reason = "presumed_legal", "MARK_ALLOWED_BY_LAST_VERIFIED_ROTATION"
    elif mark < min(marks):
        status, reason = "presumed_not_legal", "MARK_ROTATED_OUT"
    else:
        status, reason = "unknown", "MARK_NEWER_THAN_VERIFIED_ROTATION"
    return {"status": status, "confidence": "medium" if status != "unknown" else "low",
            "reason": reason, "regulation_mark": mark,
            "basis": (f"Rotation officielle en vigueur depuis le {rotation['in_force_since']} "
                      f"(marques {', '.join(marks)}), dernière vérification le "
                      f"{rotation['last_verified_on'] or 'inconnue'}; aucune rotation plus récente connue.")}


# At most one ACE SPEC card and one Radiant Pokémon per deck (official rules, printed on the cards).
# TCGdex marks them by rarity (« ACE SPEC Rare », « Radiant Rare »).
SPECIAL_CARD_LIMITS = (
    ("acespec", "DECK_ACE_SPEC_LIMIT_EXCEEDED", "ace_spec_count"),
    ("radiant", "DECK_RADIANT_LIMIT_EXCEEDED", "radiant_count"),
)


def special_card_class(rarity: Any) -> str | None:
    key = re.sub(r"[^a-z]", "", unicodedata.normalize("NFKD", str(rarity or "")).casefold())
    if "acespec" in key:
        return "acespec"
    return "radiant" if "radiant" in key or "radieux" in key else None


def check_deck_entries(
    db_path: Path, entries: list, *, total_cards: int, exact_confirmed: bool,
    format: str, platform: str, as_of: str, set_aliases: dict | None = None,
) -> dict[str, Any]:
    """Evaluate in-memory entries against a read-only reference DB; never import a deck."""
    if format not in FORMATS or platform not in PLATFORMS:
        raise RulesError("Format ou plateforme invalide.")
    as_of = _iso_date(as_of, "as_of", required=True) or ""
    if type(total_cards) is not int or type(exact_confirmed) is not bool or not entries or any(
        type(entry["quantity"]) is not int or not 1 <= entry["quantity"] <= 60 for entry in entries
    ):
        raise RulesError("Entrées de deck invalides.")
    connection = _require_rules_db(db_path)
    try:
        resolved = [(entry, _resolve_structure_identity(connection, entry, set_aliases=set_aliases)) for entry in entries]
        structure_rule = _structure_rule_context(connection, format=format, platform=platform, as_of=as_of)
    finally:
        connection.close()

    cards: list[dict[str, Any]] = []
    for entry, identity in resolved:
        ids = identity["ids"]
        if len(ids) == 1:
            verdict = check_card(db_path, ids[0], format=format, platform=platform, as_of=as_of)
        else:
            verdict = {
                "status": "unknown", "confidence": "low",
                "reason_codes": ["PRINTING_AMBIGUOUS" if ids else "PRINTING_UNRESOLVED"],
                "sources": [], "missing_data": ["unique_printing_identity"],
            }
        cards.append({
            "ordinal": int(entry["ordinal"]), "quantity": int(entry["quantity"]),
            "card_name": entry["card_name"], "set_code": entry["set_code"],
            "collector_number": entry["collector_number"], "tcgdex_ids": ids,
            "structure_identity": identity, "verdict": verdict,
        })

    statuses = [card["verdict"]["status"] for card in cards]
    quantity_sum = sum(card["quantity"] for card in cards)
    recorded_total = total_cards
    structure_status = "unknown"
    structure_reasons = list(structure_rule["reason_codes"])
    checks: dict[str, Any] = {
        "exact_confirmed": exact_confirmed,
        "recorded_total": recorded_total,
        "quantity_sum": quantity_sum,
        "recorded_total_matches_quantity_sum": recorded_total == quantity_sum,
        "unique_printing_identities": sum(len(card["tcgdex_ids"]) == 1 for card in cards),
        "identity_denominator": len(cards),
    }
    unverified_rules: list[str] = []
    violations: list[str] = []
    payload = structure_rule.get("payload")
    if not exact_confirmed:
        structure_reasons.append("DECK_VERSION_UNCONFIRMED")
    if payload is not None:
        required_total = int(payload["required_total"])
        copy_limit = int(payload["same_name_limit"])
        checks.update(
            required_total=required_total,
            recorded_total_is_required=recorded_total == required_total,
            quantity_sum_is_required=quantity_sum == required_total,
        )
        if recorded_total != quantity_sum:
            structure_reasons.append("DECK_TOTAL_QUANTITY_MISMATCH")
        elif recorded_total != required_total:
            violations.append("DECK_TOTAL_NOT_REQUIRED_COUNT")

        identity_complete = all(len(card["tcgdex_ids"]) == 1 for card in cards)
        names_complete = all(card["structure_identity"]["canonical_name_proven"] for card in cards)
        basic_energy_complete = all(
            card["structure_identity"]["basic_energy"] is not None for card in cards
        )
        basic_pokemon_complete = all(
            card["structure_identity"]["basic_pokemon"] is not None for card in cards
        )
        checks.update(
            identity_complete=identity_complete,
            english_name_identity_complete=names_complete,
            basic_energy_classification_complete=basic_energy_complete,
            basic_pokemon_classification_complete=basic_pokemon_complete,
        )
        name_totals: dict[str, int] = {}
        display_names: dict[str, str] = {}
        over_limit: list[dict[str, Any]] = []
        if identity_complete and names_complete and basic_energy_complete:
            for card in cards:
                identity = card["structure_identity"]
                if payload["basic_energy_unlimited"] and identity["basic_energy"]:
                    continue
                name = _normalized_name(identity["canonical_name"])
                display_names.setdefault(name, str(identity["canonical_name"]))
                name_totals[name] = name_totals.get(name, 0) + int(card["quantity"])
            over_limit = [
                {"card_name": display_names[name], "quantity": quantity, "limit": copy_limit}
                for name, quantity in sorted(name_totals.items()) if quantity > copy_limit
            ]
            if over_limit:
                if payload["copy_limit_exceptions_complete"]:
                    violations.append("DECK_COPY_LIMIT_EXCEEDED")
                else:
                    structure_reasons.append("COPY_LIMIT_EXCEPTION_REGISTRY_INCOMPLETE")
        else:
            structure_reasons.append("COPY_LIMIT_INPUTS_INCOMPLETE")
        checks["over_copy_limit"] = over_limit
        # A resolved printing carries its rarity: more than one of a kind is decisive even when
        # other special limits stay unverified.
        for marker, code, field in SPECIAL_CARD_LIMITS:
            count = sum(int(card["quantity"]) for card in cards
                        if special_card_class(card["structure_identity"].get("rarity")) == marker)
            checks[field] = count
            if count > 1:
                violations.append(code)

        basic_count = sum(
            int(card["quantity"]) for card in cards
            if card["structure_identity"]["basic_pokemon"] is True
        )
        checks["basic_pokemon_count"] = basic_count
        if payload["requires_basic_pokemon"]:
            if basic_count == 0 and identity_complete and basic_pokemon_complete:
                violations.append("DECK_HAS_NO_BASIC_POKEMON")
            elif basic_count == 0:
                structure_reasons.append("BASIC_POKEMON_STATUS_INCOMPLETE")
        if not payload["copy_limit_exceptions_complete"]:
            unverified_rules.append("copy_limit_exceptions")
        if not payload["special_rule_limits_complete"]:
            unverified_rules.append("special_card_rule_limits")
        if violations:
            structure_status = "not_legal"
            structure_reasons.extend(violations)
        elif (
            exact_confirmed
            and recorded_total == quantity_sum == required_total
            and identity_complete and names_complete
            and basic_energy_complete and basic_pokemon_complete
            and (not payload["requires_basic_pokemon"] or basic_count > 0)
            and payload["copy_limit_exceptions_complete"]
            and payload["special_rule_limits_complete"]
        ):
            structure_status = "legal"
            structure_reasons.append("DECK_STRUCTURE_FULLY_VERIFIED")
        else:
            structure_reasons.append("DECK_STRUCTURE_NOT_VERIFIED")
    else:
        structure_reasons.append("DECK_STRUCTURE_NOT_VERIFIED")

    structure_reasons = list(dict.fromkeys(structure_reasons))
    if "not_legal" in statuses or structure_status == "not_legal":
        overall = "not_legal"
    elif statuses and all(status == "legal" for status in statuses) and structure_status == "legal":
        overall = "legal"
    else:
        overall = "unknown"
    reason_codes = list(structure_reasons)
    if "not_legal" in statuses:
        reason_codes.append("DECK_CONTAINS_NOT_LEGAL_CARD")
    if "unknown" in statuses:
        reason_codes.append("DECK_CARD_LEGALITY_UNKNOWN")
    return {
        "exact_confirmed": exact_confirmed,
        "total_cards": recorded_total, "quantity_sum": quantity_sum,
        "structure_validation": {
            "status": structure_status,
            "reason_codes": structure_reasons,
            "checks": checks,
            "unverified_rules": unverified_rules,
            "rule_ids": structure_rule.get("rule_ids", []),
            "sources": structure_rule["sources"],
        },
        "format": format, "platform": platform, "as_of": as_of,
        "status": overall, "reason_codes": list(dict.fromkeys(reason_codes)),
        "cards": cards, "read_only": True,
        "limits": [
            "Un verdict réglementaire ne prouve ni support Live de l'impression, ni possession ou fabrication."
        ],
    }
