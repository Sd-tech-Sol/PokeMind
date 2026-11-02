"""Append-only, dated experiment records. Pure values; no file or DB selection."""
from __future__ import annotations

import copy
import hashlib
import json
import re

from pokemind import competitive

KINDS = {"source_fact", "observed_game_event", "derived_statistic", "hypothesis_to_test",
         "test_plan", "outcome_review", "withdrawn", "rejected"}
IMMUTABLE = {"source_fact", "observed_game_event", "derived_statistic"}


def _digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                   separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def validate(journal):
    if not isinstance(journal, list):
        raise ValueError("LEARNING_RECORD_LIST_REQUIRED")
    known, revised = {}, set()
    previous = None
    last_date = ""
    for row in journal:
        if (not isinstance(row, dict) or set(row) != {"id", "kind", "recorded_at", "payload", "refs", "revises", "previous", "digest"}
                or not isinstance(row["id"], str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", row["id"])
                or row["id"] in known or not isinstance(row["kind"], str) or row["kind"] not in KINDS or not isinstance(row["payload"], dict)
                or not row["payload"] or not isinstance(row["refs"], list) or not row["refs"]):
            raise ValueError("LEARNING_RECORD_SCHEMA_INVALID")
        competitive._advisor_context(row["recorded_at"])
        if row["kind"] in {"source_fact", "observed_game_event"} and not row["payload"].get("provenance"):
            raise ValueError("LEARNING_SOURCE_PROVENANCE_REQUIRED")
        if row["recorded_at"] < last_date or row["previous"] != previous:
            raise ValueError("LEARNING_DATE_OR_CHAIN_CONFLICT")
        if any(not isinstance(ref, str) or ref not in known for ref in row["refs"]):
            # First-layer facts/events carry explicit source references in payload.
            if row["kind"] not in {"source_fact", "observed_game_event"} or not row["payload"].get("provenance"):
                raise ValueError("LEARNING_PRIOR_EVIDENCE_REFERENCES_REQUIRED")
            if any(not isinstance(ref, str) or not ref.startswith("source:") for ref in row["refs"]):
                raise ValueError("LEARNING_EXTERNAL_SOURCE_PREFIX_REQUIRED")
        parent = row["revises"]
        if parent is not None:
            if (not isinstance(parent, str) or parent not in known or parent in revised or known[parent]["kind"] in IMMUTABLE
                    or row["kind"] in IMMUTABLE or parent not in row["refs"] or not row["payload"].get("reason")):
                raise ValueError("LEARNING_REVISION_MUST_EXTEND_LATEST_HYPOTHESIS_WITH_REASON")
            revised.add(parent)
        elif row["kind"] in {"withdrawn", "rejected"}:
            raise ValueError("LEARNING_WITHDRAWAL_REQUIRES_PREVIOUS_REVISION")
        if row["digest"] != _digest({k: v for k, v in row.items() if k != "digest"}):
            raise ValueError("LEARNING_IMMUTABLE_EVIDENCE_CHANGED")
        known[row["id"]] = row
        previous, last_date = row["digest"], row["recorded_at"]
    return True


def append_record(journal, *, record_id, kind, recorded_at, payload, refs, revises=None):
    validate(journal)
    existing = next((r for r in journal if r["id"] == record_id), None)
    row = {"id": record_id, "kind": kind, "recorded_at": recorded_at,
           "payload": copy.deepcopy(payload), "refs": list(refs), "revises": revises,
           "previous": existing["previous"] if existing else (journal[-1]["digest"] if journal else None)}
    row["digest"] = _digest(row)
    if existing:
        if row != existing:
            raise ValueError("LEARNING_ID_CONFLICT_NO_OVERWRITE")
        return copy.deepcopy(journal)
    candidate = [*copy.deepcopy(journal), row]
    validate(candidate)
    return candidate


def view(journal, *, as_of):
    competitive._advisor_context(as_of)
    validate(journal)
    history = [copy.deepcopy(r) for r in journal if r["recorded_at"] <= as_of]
    superseded = {r["revises"] for r in history if r["revises"]}
    return {"model_version": "learning-loop-v1", "as_of": as_of, "history": history,
            "current": [r for r in history if r["id"] not in superseded],
            "facts_preserved": True, "causal_effect": "unknown", "predicted_winrate": None,
            "persistence": "caller_owned_local_value_no_automatic_write"}


def statistics_snapshot(report):
    """Reuse the audited sample/attestation/observer engine without re-counting logs."""
    return {"as_of": report["as_of"], "deck_id": report["deck_id"],
            "period": copy.deepcopy(report["requested_period"]), "outcomes": copy.deepcopy(report["outcomes"]),
            "groups": copy.deepcopy(report["groups"]), "sample_review": copy.deepcopy(report["sample_review"]),
            "excluded": copy.deepcopy(report["excluded"]), "parser_versions": sorted({b["opponent"]["raw_parser_events"][0]["parser_version"]
                for b in report["battles"] if b["opponent"]["raw_parser_events"]}),
            "battle_refs": [b["battle_id"] for b in report["battles"]],
            "date_basis": "attested_battle_dates_separate_from_import_and_evaluation_dates",
            "causal_effect": "unknown"}


def compare_snapshots(before, after):
    for snapshot in (before, after):
        competitive._advisor_context(snapshot["as_of"])
    if (before["as_of"] > after["as_of"] or before["deck_id"] != after["deck_id"]
            or before["period"] != after["period"]):
        raise ValueError("LEARNING_COMPARABLE_DECK_PERIOD_AND_DATES_REQUIRED")
    def indexed(snapshot):
        return {(r["version"], r["opponent_archetype"], r["classification_basis"]): r for r in snapshot["groups"]}
    left, right = indexed(before), indexed(after)
    changes = []
    for key in sorted(left.keys() | right.keys(), key=str):
        a, b = left.get(key, {}), right.get(key, {})
        changes.append({"version": key[0], "opponent_archetype": key[1], "classification_basis": key[2],
            "before": {k: a.get(k, 0) for k in ("wins", "losses", "unknown", "n", "games")},
            "after": {k: b.get(k, 0) for k in ("wins", "losses", "unknown", "n", "games")},
            "delta": {k: b.get(k, 0) - a.get(k, 0) for k in ("wins", "losses", "unknown", "n", "games")}})
    return {"evaluations": [before["as_of"], after["as_of"]], "changes": changes,
            "new_battle_refs": sorted(set(after["battle_refs"]) - set(before["battle_refs"])),
            "removed_or_reclassified_refs": sorted(set(before["battle_refs"]) - set(after["battle_refs"])),
            "interpretation": "descriptive_changes_can_include_reclassification_or_deduplication",
            "improvement_demonstrated": False, "causal_effect": "unknown"}


def future_import_contract():
    return {"status": "DESIGN_ONLY_NOT_AN_IMPORT_COMMAND", "automatic_scan": False,
        "required_selection_per_log": ["one_explicit_path_or_existing_battle_id", "selected_local_db", "deck_id",
            "attested_deck_version_or_unknown", "played_date_or_unknown", "reference_player", "purpose_and_consent"],
        "existing_entrypoints": ["log import <one-selected-file> --deck <id> --db <selected-db>",
                                 "deck link-battle --help"],
        "policy": ["Le propriétaire fournit chaque journal; aucun dossier parcouru par défaut.",
            "Consentements séparés pour lecture, import, attestation et correction.",
            "Déduplication conservatrice existante, jamais de suppression de journal original.",
            "Correction datée/révocable ajoutée à l'historique, aucune réécriture des faits.",
            "Données et statistiques personnelles locales; aucune publication Git/API.",
            "Un proxy PUBLIC60 reste distinct de l'adversaire exact."],
        "real_import_authorized_by_this_feature": False}
