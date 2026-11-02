"""Consent-separated orchestration of existing match engines; no default inputs."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sqlite3
from contextlib import closing
from pathlib import Path

from pokemind import attestations, battle_logs, competitive, deck_library, deck_knowledge
from pokemind import learning_loop as loop, matchup_analytics as analytics, opponent_observer
from pokemind.lessons import save_battle_note
from pokemind.counter_deck import counter_plan
from pokemind.database import SCHEMA_VERSION, connect_readonly, utc_now
from pokemind.recovery import _redirected


def _selection(root, path):
    """Lexical containment BEFORE metadata or resolve (including Windows ADS)."""
    candidate = Path(path).absolute()
    allowed = root.absolute() / "data/local"
    if (".." in candidate.parts or not candidate.is_relative_to(allowed)
            or any(":" in part for part in candidate.parts[1:])):
        raise ValueError("SELECTED_REVIEW_PATH_MUST_STAY_IN_PROJECT_LOCAL")
    return candidate


def _file(root, path, *, suffixes, must_exist=True):
    candidate = _selection(root, path)
    if candidate.suffix.lower() not in suffixes:
        raise ValueError("SELECTED_REVIEW_FILE_FORMAT_UNSUPPORTED")
    if any(_redirected(p) for p in (candidate, *candidate.parents)):
        raise ValueError("SELECTED_REVIEW_REDIRECTED_PATH")
    if not must_exist and not candidate.exists():
        if not candidate.parent.is_dir():
            raise ValueError("SELECTED_REVIEW_OUTPUT_PARENT_MISSING")
        return candidate
    info = candidate.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError("SELECTED_REVIEW_NOT_A_UNIQUE_REGULAR_FILE")
    return candidate


def _log(root, path):
    candidate = _file(root, path, suffixes={".txt", ".log"})
    before = candidate.stat()
    if before.st_size > battle_logs.MAX_LOG_BYTES:
        raise ValueError("SELECTED_REVIEW_LOG_TOO_LARGE")
    keys = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
    with candidate.open("rb") as handle:
        opened = os.fstat(handle.fileno())
        if (any(getattr(before, k) != getattr(opened, k) for k in keys)
                or opened.st_nlink != 1 or not stat.S_ISREG(opened.st_mode)
                or any(_redirected(p) for p in (candidate, *candidate.parents))):
            raise ValueError("SELECTED_REVIEW_SOURCE_CHANGED_BEFORE_READ")
        raw = handle.read(battle_logs.MAX_LOG_BYTES + 1)
        after = os.fstat(handle.fileno())
    final = candidate.stat()
    if any(getattr(before, k) != getattr(other, k) for other in (opened, after, final) for k in keys):
        raise ValueError("SELECTED_REVIEW_SOURCE_CHANGED")
    text, encoding = battle_logs.decode_log_bytes(raw)
    if not text.strip() or any(ord(c) < 32 and c not in "\n\r\t" for c in text):
        raise ValueError("SELECTED_REVIEW_LOG_MALFORMED")
    parsed = battle_logs.parse_battle_log(text)
    if not parsed.valid:
        raise ValueError("SELECTED_REVIEW_LOG_NOT_A_SUPPORTED_SINGLE_BATTLE")
    # The existing parser is deliberately tolerant. This UX accepts one game only.
    if sum(any(pattern.match(line.strip()) for pattern in battle_logs.REFERENCE_PATTERNS)
           for line in text.splitlines()) > 1:
        raise ValueError("SELECTED_REVIEW_MULTIPLE_REFERENCE_HEADERS")
    turns = [int(x) for x in re.findall(r"^(?:Turn\s*#\s*|Tour\s*(?:#|n[°ºo]?)?\s*)(\d+)\s*[-–:]", text, re.M | re.I)]
    if any(b <= a for a, b in zip(turns, turns[1:])):
        raise ValueError("SELECTED_REVIEW_MULTIPLE_OR_REORDERED_BATTLES")
    digest = hashlib.sha256(text.replace("\r\n", "\n").replace("\r", "\n").encode()).hexdigest()
    return text, parsed, digest, encoding


def _gates(*, db, deck_id, as_of, log_file, battle_id, dry_run, apply,
           confirm_owner_read, confirm_owner_import, confirm_owner_attest,
           version, revoke_version, battle_date, reason, learning_out, public_db, reference_db):
    """All authorization and argument checks are pure, before ANY path inspection."""
    analytics._context(as_of)
    if db is None or not confirm_owner_read:
        raise ValueError("SELECTED_REVIEW_EXPLICIT_DB_AND_OWNER_READ_REQUIRED")
    if not isinstance(deck_id, str) or not battle_logs.DECK_ID_RE.fullmatch(deck_id):
        raise ValueError("SELECTED_REVIEW_EXPLICIT_DECK_REQUIRED")
    if (log_file is None) == (battle_id is None):
        raise ValueError("SELECTED_REVIEW_EXACTLY_ONE_SOURCE_REQUIRED")
    if battle_id is not None and (type(battle_id) is not int or battle_id < 1):
        raise ValueError("SELECTED_REVIEW_POSITIVE_BATTLE_ID_REQUIRED")
    if dry_run == apply:
        raise ValueError("SELECTED_REVIEW_CHOOSE_DRY_RUN_OR_APPLY")
    if (public_db is None) != (reference_db is None):
        raise ValueError("SELECTED_REVIEW_BOTH_PUBLIC_DATABASES_OR_NEITHER")
    if version is not None and (type(version) is not int or version < 1):
        raise ValueError("SELECTED_REVIEW_POSITIVE_VERSION_REQUIRED")
    if version is not None and revoke_version:
        raise ValueError("SELECTED_REVIEW_ONE_ATTESTATION_ACTION_AT_A_TIME")
    if battle_date:
        analytics._context(battle_date)
        if battle_date > as_of or version is None:
            raise ValueError("SELECTED_REVIEW_PLAYED_DATE_REQUIRES_VERSION_AND_VALID_DATE")
    if revoke_version and (not isinstance(reason, str) or not reason.strip() or len(reason) > 512
                          or any(ord(c) < 32 for c in reason)):
        raise ValueError("SELECTED_REVIEW_REVOCATION_REASON_REQUIRED")
    if reason and not revoke_version:
        raise ValueError("SELECTED_REVIEW_REASON_REQUIRES_REVOCATION")
    attest_action = version is not None or revoke_version or learning_out is not None
    if log_file is not None and attest_action:
        raise ValueError("SELECTED_REVIEW_IMPORT_THEN_SEPARATE_BATTLE_ATTESTATION")
    if confirm_owner_import and (not apply or log_file is None):
        raise ValueError("SELECTED_REVIEW_IMPORT_CONSENT_ONLY_FOR_APPLIED_LOG")
    if confirm_owner_attest and (not apply or not attest_action):
        raise ValueError("SELECTED_REVIEW_ATTEST_CONSENT_ONLY_FOR_EXPLICIT_ACTION")
    if apply and log_file is not None and not confirm_owner_import:
        raise ValueError("SELECTED_REVIEW_SEPARATE_OWNER_IMPORT_REQUIRED")
    if apply and battle_id is not None and (not attest_action or not confirm_owner_attest):
        raise ValueError("SELECTED_REVIEW_SEPARATE_OWNER_ATTEST_REQUIRED")
    if apply and as_of < utc_now()[:10]:
        raise ValueError("SELECTED_REVIEW_WRITE_CANNOT_BE_BACKDATED")


def _journal(opponent, statistics, plan, *, as_of, selection_ref):
    journal = loop.append_record([], record_id="selected-observation", kind="observed_game_event",
        recorded_at=as_of, payload={"provenance": selection_ref,
            "cards": opponent["observed_partial"],
            "parser_version": opponent.get("parser_version") or (opponent["raw_parser_events"][0]["parser_version"]
                if opponent["raw_parser_events"] else "unknown")}, refs=["source:selected-battle"])
    journal = loop.append_record(journal, record_id="selected-statistics", kind="derived_statistic",
        recorded_at=as_of, payload=loop.statistics_snapshot(statistics), refs=["selected-observation"])
    journal = loop.append_record(journal, record_id="selected-hypothesis", kind="hypothesis_to_test",
        recorded_at=as_of, payload={"text": "Vérifier les ressources et séquences visibles; aucune carte responsable démontrée.",
            "archetype_hypothesis": opponent["archetype_hypothesis"],
            "causal_effect": "unknown"}, refs=["selected-observation", "selected-statistics"])
    protocol = plan["alternatives"][0]["test_plan"] if plan and plan["alternatives"] else {
        "protocol": ["Choisir volontairement plusieurs parties et attester séparément leurs versions.",
                     "Clarifier l'archétype adverse avant de choisir une réponse."]}
    return loop.append_record(journal, record_id="selected-test", kind="test_plan", recorded_at=as_of,
                              payload=protocol, refs=["selected-hypothesis"])


def _save_journal(path, journal):
    raw = (json.dumps(journal, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    if path.exists():
        if path.stat().st_size != len(raw) or path.read_bytes() != raw:
            raise ValueError("SELECTED_REVIEW_LEARNING_CONFLICT_NO_OVERWRITE")
        return "already_saved_identically"
    # No replacement, including on a concurrent creation; preserve partial output on failure.
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    return "saved_new_local_file"


def review_selected(root, db, *, deck_id, as_of, log_file=None, battle_id=None,
                    dry_run=False, apply=False, confirm_owner_read=False,
                    confirm_owner_import=False, confirm_owner_attest=False,
                    version=None, battle_date=None, revoke_version=False, reason=None,
                    public_db=None, reference_db=None, learning_out=None, use_set_aliases=False):
    _gates(**{k: v for k, v in locals().copy().items() if k not in {"root", "use_set_aliases"}})
    # Validate all lexical paths before touching any selected file.
    for path in (db, log_file, public_db, reference_db, learning_out):
        if path is not None:
            _selection(root, path)
    db = analytics.selected_database(root, db, confirm_owner_read=True)
    output = _file(root, learning_out, suffixes={".json"}, must_exist=False) if learning_out else None
    if output and output in {Path(p).absolute() for p in (db, public_db, reference_db) if p}:
        raise ValueError("SELECTED_REVIEW_OUTPUT_CONFLICT")
    text = parsed = digest = encoding = None
    if log_file is not None:
        text, parsed, digest, encoding = _log(root, log_file)
    with closing(connect_readonly(db)) as con:
        analytics._schema(con)
        if con.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
            raise ValueError("SELECTED_REVIEW_CURRENT_SCHEMA_REQUIRED_NO_MIGRATION")
        if not con.execute("SELECT 1 FROM deck_versions WHERE deck_id=?", (deck_id,)).fetchone():
            raise ValueError("SELECTED_REVIEW_SELECTED_DECK_NOT_FOUND")
        if digest:
            row = con.execute("SELECT * FROM battle_logs WHERE source_sha256=?", (digest,)).fetchone()
        else:
            row = con.execute("SELECT * FROM battle_logs WHERE id=?", (battle_id,)).fetchone()
            if row is None:
                raise ValueError("SELECTED_REVIEW_BATTLE_NOT_FOUND")
        if row is not None:
            if row["deck_id"] != deck_id:
                raise ValueError("SELECTED_REVIEW_BATTLE_DECK_CONFLICT")
            if not row["imported_at"] or row["imported_at"][:10] > as_of:
                raise ValueError("SELECTED_REVIEW_BATTLE_NOT_AVAILABLE_AS_OF")
            battle_id = row["id"]
    # PUBLIC engines validate their explicit caches read-only, before any write.
    index = deck_library.reference_index(root, public_db, as_of=as_of, reference_db=reference_db) if public_db else None
    shared = dict(as_of=as_of, confirm_owner_read=True, public_db=public_db, reference_db=reference_db)
    if row is not None:
        opponent = analytics.opponent_for_battle(root, db, battle_id=battle_id, **shared)
    else:
        opponent = opponent_observer.observe(parsed, index=index, as_of=as_of)
        opponent.update(outcome={"W": "wins", "L": "losses"}.get(parsed.outcome, "unknown"),
                        player_version={"status": "unattested", "version": None}, battle_id=None)
    target = opponent["classification"]["label"]
    plan = counter_plan(root, public_db, reference_db, as_of=as_of, target=target,
                        use_set_aliases=use_set_aliases) if public_db and target else None
    guides = [deck_knowledge.knowledge_show(root, public_db, reference_db, selector=p["selector"],
                as_of=as_of, use_set_aliases=use_set_aliases) for p in opponent["public_reference_proxy"][:1]] if public_db else []
    statistics = analytics.matchup_report(root, db, deck_id=deck_id, **shared)
    mutation = None
    if version is not None:
        mutation = attestations.confirm_battle_version(db, deck_id, battle_id, version, battle_date=battle_date)
    elif revoke_version:
        mutation = attestations.revoke_battle_version(db, deck_id, battle_id)
    if mutation and not mutation["eligible"]:
        raise ValueError("SELECTED_REVIEW_ATTESTATION_CONFLICT_" + mutation["status"])
    result = {"model_version": "selected-match-review-v1", "status": "PREVIEW" if dry_run else "COMPLETE_LOCAL",
        "as_of": as_of, "deck_id": deck_id, "battle_id": battle_id, "dry_run": dry_run,
        "access_plan": {"read": ["explicit_selected_database:chosen_battle_and_selected_deck_history"]
            + (["one_explicit_log_file"] if log_file else []) + (["two_explicit_public_caches"] if public_db else [])
            + (["selected_learning_output_metadata_and_existing_content_comparison_on_apply"] if output else []),
            "write_if_applied": (["one_log_events_no_raw_text_no_version_attestation"] if log_file else [])
                + (["one_battle_version_attestation_history"] if version is not None or revoke_version else [])
                + (["dated_idempotent_owner_note_explaining_revocation"] if revoke_version else [])
                + (["one_explicit_local_learning_json_no_overwrite"] if output else []),
            "automatic_discovery": False, "create_or_migrate_database": False},
        "consents": {"read": confirm_owner_read, "import": confirm_owner_import, "attest": confirm_owner_attest},
        "source": {"kind": "log_file" if log_file else "battle_id", "encoding": encoding,
            "exact_duplicate": bool(row is not None and log_file), "raw_stored": False,
            "preview_pending_import_excluded_from_statistics": bool(log_file and row is None)},
        "opponent": opponent, "statistics": statistics, "counter_plan": plan, "deck_knowledge": guides,
        "counter_unavailable_reason": None if plan else "EXPLICIT_PUBLIC_CACHES_OR_UNAMBIGUOUS_TARGET_MISSING",
        "attestation": mutation, "completed_steps": [], "local_only": True, "network_used": False,
        "validation_scope_at_delivery": "invented_matches_only", "release_status": "NOT_RELEASE_READY"}
    # Each existing engine owns its transaction. If a later step fails, retain the
    # committed import and report its ID; rerunning the same selection is idempotent.
    learning_write_attempted = False
    try:
        if apply and log_file:
            imported = battle_logs.import_battle_log(db, text, source_kind="file", deck_id=deck_id)
            battle_id = imported["battle_id"]
            if imported["deck_id"] != deck_id:
                raise ValueError("SELECTED_REVIEW_CONCURRENT_DECK_CONFLICT")
            result["battle_id"] = battle_id
            result["source"]["exact_duplicate"] = imported["duplicate"]
            result["source"]["preview_pending_import_excluded_from_statistics"] = False
            result["completed_steps"].append("import_already_present" if imported["duplicate"] else "import_committed")
        if apply and version is not None:
            result["attestation"] = attestations.confirm_battle_version(db, deck_id, battle_id, version,
                battle_date=battle_date, apply=True, confirm_owner=True)
            result["completed_steps"].append("version_attested")
        elif apply and revoke_version:
            result["attestation"] = attestations.revoke_battle_version(db, deck_id, battle_id,
                apply=True, confirm_owner=True)
            result["completed_steps"].append("version_revoked")
            result["correction_note"] = save_battle_note(db, deck_id=deck_id, battle_id=battle_id,
                text="Retrait de version attestée (" + str(mutation.get("confirmed_at")) + ") : " + reason,
                confidence="unknown", kind="owner_note", apply=True, confirm_owner=True)
            result["completed_steps"].append("correction_reason_saved")
        if apply:
            result["opponent"] = analytics.opponent_for_battle(root, db, battle_id=battle_id, **shared)
            result["statistics"] = analytics.matchup_report(root, db, deck_id=deck_id, **shared)
        result["learning_journal"] = _journal(result["opponent"], result["statistics"], plan,
            as_of=as_of, selection_ref="selected-battle:" + str(battle_id or "pending-import"))
        result["learning_persistence"] = "not_saved"
        if apply and output:
            # Recheck redirection/hardlinks immediately before optional persistence.
            _file(root, output, suffixes={".json"}, must_exist=False)
            learning_write_attempted = True
            result["learning_persistence"] = _save_journal(output, result["learning_journal"])
            result["completed_steps"].append("learning_saved")
    except (ValueError, OSError, sqlite3.DatabaseError) as exc:
        if not result["completed_steps"] and not learning_write_attempted:
            raise
        result.update(status="PARTIAL_LOCAL_REVIEW_REQUIRED", failure_category=type(exc).__name__,
            analysis_current_after_writes=False, learning_write_attempted=learning_write_attempted,
            resume="Rerun the same explicit selection with the same distinct consents; no deletion or reparse.")
    return result


def human_review(report):
    print(f"Revue choisie : {report['status']}, au {report['as_of']}; partie={report['battle_id'] or 'non importée'}.")
    print("Lecture : " + ", ".join(report["access_plan"]["read"]))
    print("Écritures prévues si appliqué : " + ", ".join(report["access_plan"]["write_if_applied"]))
    print("Consentements distincts : " + str(report["consents"]))
    print("Source/import : " + str(report["source"]))
    print("Issue observée de la partie choisie : " + report["opponent"]["outcome"] + "; aucune issue cachée déduite.")
    opponent_observer.human_opponent(report["opponent"])
    version = report["opponent"]["player_version"]
    print(f"Version jouée : {version.get('version') or 'unknown'}; {version['status']}; date jouée : {version.get('asserted_battle_date') or 'unknown'}.")
    analytics.human_matchups(report["statistics"])
    for guide in report["deck_knowledge"]:
        deck_knowledge.human_knowledge(guide)
    if report["counter_plan"]:
        from pokemind.counter_deck import human_counter
        human_counter(report["counter_plan"])
        print("Copie manuelle : sélectionner le texte de l'export PUBLIC 60/60 affiché, puis le copier soi-même.")
    else:
        print("Plan de réponse indisponible : " + report["counter_unavailable_reason"])
    print("Expérience Learning Loop : hypothèse et protocole dans --json; conservation locale = " + report.get("learning_persistence", "incomplète"))
    for entry in report.get("learning_journal", []):
        if entry["kind"] == "hypothesis_to_test":
            print("Hypothèse à tester : " + entry["payload"]["text"])
        elif entry["kind"] == "test_plan":
            for action in entry["payload"].get("protocol", []):
                print("Prochain test : " + action)
    print("Étapes terminées : " + str(report["completed_steps"]))
    print("Petits n, biais de sélection; aucun contre ou progrès causal démontré. V1 NOT_RELEASE_READY.")
