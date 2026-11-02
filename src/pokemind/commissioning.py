"""Owner commissioning preflight. Pure read-only checks, no hidden activation.

Passing a preflight never authorizes the corresponding operation. Every future
owner act remains separate, and replacement/purge remain publicly disabled.
"""
from pathlib import Path

from pokemind.database import SCHEMA_VERSION, database_status
from pokemind.recovery import RecoveryError, _sqlite_checks, verify_backup, _redirected

STEPS = ("backup", "verify", "clone", "migration", "activate", "collection", "credits", "battle_attestation", "vision_trial", "scheduler", "retention", "replace_existing")


def commissioning_preflight(db_path: Path, *, step: str, backup_path: Path | None = None,
                            clone_path: Path | None = None):
    if step not in STEPS:
        raise ValueError("OWNER_STEP_INVALID")
    status = database_status(db_path)
    checks, blockers = {}, []
    if not status.get("database_exists") or status.get("integrity") != "ok":
        blockers.append("OWNER_DATABASE_NOT_HEALTHY")
    else:
        try:
            checks = _sqlite_checks(db_path)
        except (OSError, RecoveryError):
            blockers.append("OWNER_DATABASE_CHECKS_FAILED")
        if checks.get("status") != "ok":
            blockers.append("OWNER_DATABASE_FK_FTS_NOT_HEALTHY")
    backup = {"provided": backup_path is not None, "verified": False}
    if backup_path is not None:
        try:
            evidence = verify_backup(backup_path)
            backup.update(verified=True, schema_version=evidence["checks"]["schema_version"])
        except (OSError, RecoveryError):
            blockers.append("OWNER_BACKUP_NOT_VERIFIED")
    if step in {"verify", "clone", "migration", "activate"} and not backup["verified"]:
        blockers.append("SEPARATE_VERIFIED_BACKUP_REQUIRED")
    if step == "activate" and status.get("schema_version") != SCHEMA_VERSION:
        blockers.append("VALIDATED_CURRENT_SCHEMA_CLONE_REQUIRED")
    if step == "clone":
        if clone_path is None:
            blockers.append("EXPLICIT_NEW_CLONE_REQUIRED")
        elif clone_path.exists() or any(_redirected(p) for p in (clone_path, *clone_path.absolute().parents)):
            blockers.append("RESTORE_EXISTING_OR_UNSAFE_TARGET_BLOCKED")
    if step in {"retention", "replace_existing"}:
        blockers.append("RETENTION_EXTERNAL_EXCLUSION_UNPROVEN" if step == "retention" else "RESTORE_EXISTING_TARGET_BLOCKED")
    if step == "scheduler":
        blockers.append("SCHEDULER_OWNER_OPT_IN_AND_OS_PROOF_REQUIRED")
    if step == "vision_trial":
        blockers.append("SEPARATE_OCR_CALIBRATION_AND_PERMITTED_TRAINING_REQUIRED")
    if step == "migration" and status.get("schema_version", 0) > SCHEMA_VERSION:
        blockers.append("FUTURE_SCHEMA_UNSUPPORTED")
    return {"step": step, "mode": "dry_run", "read_only": True, "network_used": False,
            "writes": 0, "private_values_disclosed": False, "owner_authorization_inferred": False,
            "status": "BLOCKED_WITH_REASON" if blockers else "OWNER_ACTION_REQUIRED",
            "technical_preflight_passed": not blockers,
            "database": {"schema_version": status.get("schema_version"), "expected_schema_version": SCHEMA_VERSION,
                         "integrity": status.get("integrity"), "fk_fts_healthy": checks.get("status") == "ok"},
            "backup": backup, "blockers": list(dict.fromkeys(blockers)),
            "next_action": "SEPARATE_EXPLICIT_OWNER_ORDER_REQUIRED",
            "rollback": "PRESERVE_ORIGINAL_AND_VERIFIED_BACKUP; NEW_CLONE_ACTIVATION_SEPARATE",
            "optional": step in {"collection", "credits"}}
