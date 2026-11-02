"""Sauvegarde et restauration SQLite locales, vérifiables et consenties."""

from __future__ import annotations

import hashlib
import heapq
import json
import os
import shutil
import socket
import sqlite3
import stat
import tempfile
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from pokemind.database import SCHEMA_VERSION, connect_readonly, connect_writable, initialize_schema, fts_checks
from pokemind.security import neutral_exception_code


MANIFEST_VERSION = 1
DEFAULT_MAX_BYTES = 8 * 1024 * 1024 * 1024
DEFAULT_MIN_FREE_BYTES = 64 * 1024 * 1024
COPY_PAGE_BATCH = 128


class RecoveryError(ValueError):
    """Erreur contrôlée ne contenant jamais de chemin ou secret externe."""


def _utc(value: datetime | None = None) -> str:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise RecoveryError("RECOVERY_CLOCK_TIMEZONE_REQUIRED")
    return current.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _file_attestation(path: Path) -> dict[str, Any]:
    """Return content-backed evidence suitable for a short-lived mutation plan."""
    candidate = _safe_file(path, label="RECOVERY_EVIDENCE")
    digest = hashlib.sha256()
    with candidate.open("rb") as handle:
        stat = os.fstat(handle.fileno())
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
        after = os.fstat(handle.fileno())
    keys = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
    # Windows fstat/path.stat expose different ctime semantics on hardlinks.
    if stat.st_ctime_ns != after.st_ctime_ns or any(getattr(stat, key) != getattr(after, key) for key in keys) or any(
        getattr(after, key) != getattr(candidate.stat(), key) for key in keys
    ):
        raise RecoveryError("RECOVERY_EVIDENCE_CHANGED_DURING_READ")
    return {
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "file_id": getattr(stat, "st_ino", 0),
        "sha256": digest.hexdigest(),
    }


def _same_attestation(path: Path, expected: dict[str, Any]) -> bool:
    try:
        current = _file_attestation(path)
    except (OSError, RecoveryError):
        return False
    return all(current.get(key) == expected.get(key) for key in current)


def _existing_parent(path: Path) -> Path:
    candidate = path.resolve(strict=False)
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


def _redirected(path: Path) -> bool:
    """Windows junctions are reparse points even when is_symlink is false."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _safe_file(path: Path, *, label: str) -> Path:
    if _redirected(path) or any(_redirected(parent) for parent in path.absolute().parents):
        raise RecoveryError(f"{label}_NOT_REGULAR_FILE")
    candidate = path.resolve(strict=True)
    if path.is_symlink() or not candidate.is_file():
        raise RecoveryError(f"{label}_NOT_REGULAR_FILE")
    return candidate


def _safe_directory(path: Path, *, create: bool, writable: bool = False) -> Path:
    if _redirected(path) or any(_redirected(parent) for parent in path.absolute().parents):
        raise RecoveryError("RECOVERY_DIRECTORY_NOT_SAFE")
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise RecoveryError("RECOVERY_DIRECTORY_NOT_SAFE")
        resolved = path.resolve(strict=True)
    else:
        parent = _existing_parent(path)
        if parent.is_symlink() or not parent.is_dir():
            raise RecoveryError("RECOVERY_DIRECTORY_PARENT_NOT_SAFE")
        if not create:
            resolved = path.resolve(strict=False)
        else:
            path.mkdir(parents=True, exist_ok=False)
            resolved = path.resolve(strict=True)
    probe = resolved if resolved.exists() else _existing_parent(resolved)
    if (create or writable) and not os.access(probe, os.W_OK):
        raise RecoveryError("RECOVERY_DIRECTORY_NOT_WRITABLE")
    return resolved


def _schema_version(path: Path) -> int:
    connection = connect_readonly(path)
    try:
        return int(connection.execute("PRAGMA user_version").fetchone()[0])
    finally:
        connection.close()


def _sqlite_checks(path: Path) -> dict[str, Any]:
    connection = connect_readonly(path)
    try:
        integrity_rows = [str(row[0]) for row in connection.execute("PRAGMA integrity_check").fetchall()]
        foreign_keys = len(connection.execute("PRAGMA foreign_key_check").fetchall())
        fts = fts_checks(connection)
        status = "ok" if integrity_rows == ["ok"] and foreign_keys == 0 and all(
            item["status"] == "ok" for item in fts.values()
        ) else "failed"
        return {
            "status": status,
            "integrity": integrity_rows[0] if len(integrity_rows) == 1 else "failed",
            "foreign_key_violations": foreign_keys,
            "fts": fts,
            "schema_version": int(connection.execute("PRAGMA user_version").fetchone()[0]),
        }
    except sqlite3.DatabaseError as exc:
        raise RecoveryError("SQLITE_VERIFICATION_FAILED") from exc
    finally:
        connection.close()


def _disk_capacity(path: Path, required: int, min_free_bytes: int) -> dict[str, Any]:
    usage = shutil.disk_usage(_existing_parent(path))
    enough = usage.free >= required + min_free_bytes
    return {
        "required_bytes": required,
        "minimum_free_reserve_bytes": min_free_bytes,
        "free_bytes": usage.free,
        "enough": enough,
    }


def backup_plan(
    db_path: Path,
    destination: Path,
    *,
    max_source_bytes: int = DEFAULT_MAX_BYTES,
    min_free_bytes: int = DEFAULT_MIN_FREE_BYTES,
) -> dict[str, Any]:
    source = _safe_file(db_path, label="SOURCE_DATABASE")
    if source.stat().st_size > max_source_bytes:
        raise RecoveryError("SOURCE_DATABASE_TOO_LARGE")
    destination_resolved = _safe_directory(destination, create=False)
    capacity = _disk_capacity(destination_resolved, max(source.stat().st_size * 2, 1024 * 1024), min_free_bytes)
    checks = _sqlite_checks(source)
    if checks["status"] != "ok":
        raise RecoveryError("SOURCE_DATABASE_NOT_HEALTHY")
    return {
        "mode": "dry_run",
        "read_only": True,
        "network_used": False,
        "source": {
            "kind": "sqlite_local",
            "size_bytes": source.stat().st_size,
            "schema_version": checks["schema_version"],
            "integrity": checks["integrity"],
        },
        "destination": {"kind": "owner_selected_private_directory", "exists": destination_resolved.exists()},
        "capacity": capacity,
        "method": "sqlite3.backup",
        "atomic_publish": False,
        "publication": "individual_files_no_overwrite",
        "durability": {"multifile_atomic": False, "power_loss_guaranteed": False,
                       "windows_acl_verified": False},
        "would_write": capacity["enough"],
        "reason_code": None if capacity["enough"] else "INSUFFICIENT_DISK_SPACE",
    }


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        # Sous Windows, os.kill(pid, 0) peut produire un événement console. Une
        # ouverture read-only du processus évite tout signal ou changement d'état.
        try:
            import ctypes

            process = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if process:
                ctypes.windll.kernel32.CloseHandle(process)
                return True
            error = ctypes.windll.kernel32.GetLastError()
            return error == 5  # accès refusé signifie que le processus existe
        except (AttributeError, OSError):
            return True  # échec indéterminé : ne jamais voler le verrou
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


@dataclass(slots=True)
class _ProcessLock:
    path: Path
    stale_after: timedelta = timedelta(hours=6)
    acquired: bool = False
    token: str | None = None
    preserve_on_error: bool = False

    def __enter__(self) -> "_ProcessLock":
        payload = {
            "kind": "pokemind-recovery-lock",
            "pid": os.getpid(),
            "hostname": socket.gethostname(),
            "created_at": _utc(),
            "token": uuid.uuid4().hex,
        }
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                current = json.loads(self.path.read_text(encoding="utf-8"))
                created = datetime.fromisoformat(str(current["created_at"]).replace("Z", "+00:00"))
                same_host = current.get("hostname") == socket.gethostname()
                alive = same_host and _pid_alive(int(current.get("pid", 0)))
                stale = datetime.now(timezone.utc) - created.astimezone(timezone.utc) > self.stale_after
            except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
                raise RecoveryError("RECOVERY_LOCK_UNREADABLE") from None
            if alive:
                raise RecoveryError("RECOVERY_ALREADY_RUNNING")
            if not stale:
                raise RecoveryError("RECOVERY_LOCK_RECENT")
            # An old PID is not an ownership proof (PID reuse, another host or a
            # replacement between read and rename). Preserve for offline review.
            raise RecoveryError("RECOVERY_STALE_LOCK_OWNER_REVIEW_REQUIRED")
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical(payload))
            handle.flush()
            os.fsync(handle.fileno())
        self.acquired = True
        self.token = payload["token"]
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        if exc_type is not None and self.preserve_on_error:
            # Backup diagnostics are owner-reviewed, never automatically erased.
            return
        if self.acquired:
            try:
                current = json.loads(self.path.read_text(encoding="utf-8"))
                if current.get("token") != self.token:
                    raise RecoveryError("RECOVERY_LOCK_OWNERSHIP_CHANGED")
                self.path.unlink()
            except (OSError, ValueError) as error:
                if exc is None:
                    raise RecoveryError("RECOVERY_LOCK_CLEANUP_REQUIRED") from error
            self.acquired = False


def _sync_directory(path: Path) -> bool:
    """POSIX namespace flush; Windows has no portable directory fsync here."""
    if os.name == "nt":
        return False
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return True


def _atomic_bytes(
    path: Path, value: bytes, *, overwrite: bool = True, keep_temporary: bool = False,
) -> None:
    if keep_temporary and overwrite:
        raise ValueError("RECOVERY_TEMPORARY_REQUIRES_NO_OVERWRITE")
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temp.open("xb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        if overwrite:
            os.replace(temp, path)
        else:
            os.link(temp, path)
        _sync_directory(path.parent)
    finally:
        if not keep_temporary:
            temp.unlink(missing_ok=True)


def _copy_database(source_path: Path, target_path: Path, *, max_duration_seconds: float) -> None:
    started = time.monotonic()

    def progress(status: int, remaining: int, total: int) -> None:
        del status, remaining, total
        if time.monotonic() - started > max_duration_seconds:
            raise RecoveryError("RECOVERY_DURATION_LIMIT_EXCEEDED")

    source = connect_readonly(source_path)
    target = sqlite3.connect(target_path)
    try:
        source.backup(target, pages=COPY_PAGE_BATCH, progress=progress, sleep=0.02)
        target.commit()
        # A published backup must be a self-contained DELETE-journal database,
        # independent of source WAL settings and any unhashed sidecar state.
        if str(target.execute("PRAGMA journal_mode=DELETE").fetchone()[0]).lower() != "delete":
            raise RecoveryError("BACKUP_CLONE_JOURNAL_MODE_UNSAFE")
    except sqlite3.DatabaseError as exc:
        raise RecoveryError("SQLITE_BACKUP_FAILED") from exc
    finally:
        target.close()
        source.close()


def create_backup(
    db_path: Path,
    destination: Path,
    *,
    apply: bool = False,
    confirm_owner: bool = False,
    max_source_bytes: int = DEFAULT_MAX_BYTES,
    min_free_bytes: int = DEFAULT_MIN_FREE_BYTES,
    max_duration_seconds: float = 1800,
    now: datetime | None = None,
) -> dict[str, Any]:
    if not apply:
        return backup_plan(
            db_path, destination, max_source_bytes=max_source_bytes, min_free_bytes=min_free_bytes
        )
    if not confirm_owner:
        raise RecoveryError("OWNER_CONFIRMATION_REQUIRED")
    plan = backup_plan(
        db_path, destination, max_source_bytes=max_source_bytes, min_free_bytes=min_free_bytes
    )
    if not plan["capacity"]["enough"]:
        raise RecoveryError("INSUFFICIENT_DISK_SPACE")
    source = _safe_file(db_path, label="SOURCE_DATABASE")
    directory = _safe_directory(destination, create=True)
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    nonce = hashlib.sha256(f"{stamp}:{os.getpid()}:{time.monotonic_ns()}".encode()).hexdigest()[:10]
    schema = _schema_version(source)
    filename = f"pokemind-v{schema}-{stamp}-{nonce}.sqlite3"
    final = directory / filename
    temporary = directory / f".{filename}.inprogress"
    manifest_path = directory / f"{filename}.manifest.json"
    source_sha = _sha256_file(source)
    manifest_temporary = manifest_path.with_name(f".{manifest_path.name}.{os.getpid()}.tmp")
    with _ProcessLock(directory / ".pokemind-backup.lock", preserve_on_error=True):
        try:
            # sqlite3.connect would otherwise open an occupied work name for
            # writing. Reserve it exclusively, including against dangling links.
            with temporary.open("xb") as handle:
                work_identity = os.fstat(handle.fileno())
            _copy_database(source, temporary, max_duration_seconds=max_duration_seconds)
            work_stat = _safe_file(temporary, label="BACKUP_WORK").stat()
            if (work_stat.st_dev, work_stat.st_ino) != (work_identity.st_dev, work_identity.st_ino):
                raise RecoveryError("BACKUP_WORK_OWNERSHIP_CHANGED")
            checks = _sqlite_checks(temporary)
            if checks["status"] != "ok":
                raise RecoveryError("BACKUP_VERIFICATION_FAILED")
            backup_sha = _sha256_file(temporary)
            size = temporary.stat().st_size
            with temporary.open("r+b") as handle:
                os.fsync(handle.fileno())
            # Never overwrite a collision, including one created by an external
            # process which does not honor our cooperative lock.
            os.link(temporary, final)
            namespace_synced = _sync_directory(directory)
            try:
                os.chmod(final, 0o600)
            except OSError:
                pass
            manifest = {
                "manifest_version": MANIFEST_VERSION,
                "state": "verified",
                "created_at": _utc(now),
                "verified_at": _utc(),
                "backup_file": filename,
                "method": "sqlite3.backup",
                "schema_version": checks["schema_version"],
                "application_schema_version": SCHEMA_VERSION,
                "size_bytes": size,
                "sha256": backup_sha,
                "source": {
                    "kind": "sqlite_local",
                    "schema_version": schema,
                    "size_bytes": source.stat().st_size,
                    "content_changed_during_backup": _sha256_file(source) != source_sha,
                },
                "checks": checks,
                "contains_private_data": True,
                "cloud_uploaded": False,
            }
            _atomic_bytes(manifest_path, _canonical(manifest), overwrite=False, keep_temporary=True)
            # Public verification still refuses ALL hardlink aliases. Only this
            # private check accepts our two exact work aliases, before cleanup.
            evidence = _verify_backup(final, work_aliases=(temporary, manifest_temporary))
            result = {
                "mode": "applied",
                "state": "verified",
                "network_used": False,
                "backup_file": filename,
                "manifest_file": manifest_path.name,
                "schema_version": schema,
                "size_bytes": evidence["size_bytes"],
                "sha256": evidence["sha256"],
                "verified_at": manifest["verified_at"],
                "source_unchanged_during_backup": not manifest["source"]["content_changed_during_backup"],
                "durability": {"file_fsynced": True, "directory_fsynced": namespace_synced,
                               "power_loss_guaranteed": False, "multifile_atomic": False},
            }
        except Exception as exc:
            # Do not rename, replace or unlink ANY residue on error. Even a
            # diagnostic rename can fail or overwrite an existing .failed file.
            if isinstance(exc, RecoveryError):
                raise
            raise RecoveryError("BACKUP_CREATE_FAILED") from exc
    # Normal cleanup only AFTER all publication, sync, SHA/SQLite/FTS/FK checks
    # and cooperative lock release succeeded. Final files retain the same bytes.
    # A cleanup error leaves remaining aliases and blocks public verification.
    try:
        for alias, published, key in (
            (temporary, final, "backup_evidence"),
            (manifest_temporary, manifest_path, "manifest_evidence"),
        ):
            if (not _same_attestation(alias, evidence[key])
                    or not _same_attestation(published, evidence[key])
                    or alias.stat().st_nlink != 2 or not alias.samefile(published)):
                raise RecoveryError("BACKUP_WORK_OWNERSHIP_CHANGED")
            alias.unlink()
    except OSError as exc:
        raise RecoveryError("BACKUP_WORK_CLEANUP_REQUIRED") from exc
    return result


def _manifest_for(backup_path: Path) -> Path:
    return backup_path.with_name(f"{backup_path.name}.manifest.json")


def _assert_backup_offline(backup: Path) -> None:
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = Path(f"{backup}{suffix}")
        if sidecar.exists() or sidecar.is_symlink():
            raise RecoveryError("BACKUP_IN_USE_OR_WAL_ACTIVE")
    with backup.open("rb") as handle:
        header = handle.read(20)
    if header[:16] == b"SQLite format 3\x00" and (header[18:19] == b"\x02" or header[19:20] == b"\x02"):
        raise RecoveryError("BACKUP_IN_USE_OR_WAL_ACTIVE")


def verify_backup(backup_path: Path) -> dict[str, Any]:
    return _verify_backup(backup_path)


def _verify_backup(
    backup_path: Path, *, work_aliases: tuple[Path, Path] | None = None,
) -> dict[str, Any]:
    backup = _safe_file(backup_path, label="BACKUP")
    manifest_path = _safe_file(_manifest_for(backup), label="BACKUP_MANIFEST")

    def check_aliases() -> None:
        for index, path in enumerate((backup, manifest_path)):
            if work_aliases is None:
                if path.stat().st_nlink != 1:
                    raise RecoveryError("BACKUP_HARDLINK_ALIAS_BLOCKED")
            else:
                alias = _safe_file(work_aliases[index], label="BACKUP_WORK")
                if path.stat().st_nlink != 2 or not path.samefile(alias):
                    raise RecoveryError("BACKUP_WORK_OWNERSHIP_CHANGED")
        failed = backup.with_name(f".{backup.name}.failed")
        inprogress = backup.with_name(f".{backup.name}.inprogress")
        if (failed.exists() or failed.is_symlink()
                or (work_aliases is None and (
                    inprogress.exists() or inprogress.is_symlink()
                    or next(backup.parent.glob(f".{manifest_path.name}.*.tmp"), None) is not None
                ))):
            raise RecoveryError("BACKUP_WORK_REQUIRES_OWNER_REVIEW")

    check_aliases()
    _assert_backup_offline(backup)
    if manifest_path.stat().st_size > 64_000:
        raise RecoveryError("BACKUP_MANIFEST_TOO_LARGE")
    manifest_evidence = _file_attestation(manifest_path)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RecoveryError("BACKUP_MANIFEST_INVALID") from exc
    if not isinstance(manifest, dict):
        raise RecoveryError("BACKUP_MANIFEST_INVALID")
    if (
        manifest.get("manifest_version") != MANIFEST_VERSION
        or manifest.get("state") != "verified"
        or manifest.get("backup_file") != backup.name
    ):
        raise RecoveryError("BACKUP_MANIFEST_MISMATCH")
    backup_evidence = _file_attestation(backup)
    checksum = backup_evidence["sha256"]
    if checksum != manifest.get("sha256") or backup.stat().st_size != manifest.get("size_bytes"):
        raise RecoveryError("BACKUP_CHECKSUM_MISMATCH")
    checks = _sqlite_checks(backup)
    if checks["status"] != "ok" or checks["schema_version"] != manifest.get("schema_version"):
        raise RecoveryError("BACKUP_VERIFICATION_FAILED")
    _assert_backup_offline(backup)
    if not _same_attestation(backup, backup_evidence) or not _same_attestation(manifest_path, manifest_evidence):
        raise RecoveryError("BACKUP_CONTENT_CHANGED_DURING_VERIFICATION")
    check_aliases()
    return {
        "state": "verified",
        "read_only": True,
        "network_used": False,
        "backup_file": backup.name,
        "manifest_state": manifest.get("state"),
        "created_at": manifest.get("created_at"),
        "verified_at": manifest.get("verified_at"),
        "size_bytes": backup.stat().st_size,
        "sha256": checksum,
        "backup_evidence": backup_evidence,
        "manifest_evidence": manifest_evidence,
        "checks": checks,
    }


def backup_status(destination: Path) -> dict[str, Any]:
    directory = _safe_directory(destination, create=False)
    if not directory.exists():
        return {"read_only": True, "network_used": False, "counts": {}, "total_bytes": 0, "backups": []}
    manifests = heapq.nsmallest(1001, directory.glob("*.sqlite3.manifest.json"))
    inventory_complete = len(manifests) <= 1000
    manifests = manifests[:1000]
    backups: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    total = 0
    for manifest_path in manifests:
        state = "unknown"
        try:
            # Derive the sibling from the directory entry, never from untrusted
            # manifest content (absolute paths and ../ must never be followed).
            filename = manifest_path.name.removesuffix(".manifest.json")
            backup = directory / filename
            if backup.is_symlink() or manifest_path.is_symlink():
                raise RecoveryError("BACKUP_ENTRY_NOT_SAFE")
            if not backup.exists():
                state, evidence, size = "missing", {}, 0
            else:
                evidence = verify_backup(backup)
                state, size = "verified", int(evidence["size_bytes"])
            total += size
            backups.append({
                "backup_file": filename,
                "state": state,
                "created_at": evidence.get("created_at"),
                "verified_at": evidence.get("verified_at"),
                "schema_version": evidence.get("checks", {}).get("schema_version"),
                "size_bytes": size,
            })
        except RecoveryError as exc:
            state = "corrupt" if str(exc) in {
                "BACKUP_CHECKSUM_MISMATCH", "BACKUP_VERIFICATION_FAILED", "SQLITE_VERIFICATION_FAILED",
                "BACKUP_MANIFEST_MISMATCH", "BACKUP_MANIFEST_INVALID",
            } else "unknown"
            backups.append({"backup_file": None, "state": state, "reason_code": "BACKUP_ENTRY_REJECTED"})
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, sqlite3.Error):
            backups.append({"backup_file": None, "state": "unknown", "reason_code": "BACKUP_ENTRY_UNREADABLE"})
            state = "unknown"
        counts[state] = counts.get(state, 0) + 1
    for item in directory.iterdir():
        if item.is_symlink() or not item.is_file():
            continue
        if item.name.endswith(".inprogress"):
            counts["in_progress"] = counts.get("in_progress", 0) + 1
        elif item.name.endswith(".failed"):
            counts["failed"] = counts.get("failed", 0) + 1
    return {
        "read_only": True,
        "network_used": False,
        "counts": counts,
        "total_bytes": total,
        "backups": backups,
        "scan_limited_to": 1000,
        "inventory_complete": inventory_complete,
        "residues": recovery_residues(directory),
    }


def recovery_residues(directory: Path) -> dict[str, Any]:
    """Read-only bounded inventory. Never infer permission to repair/delete."""
    base = _safe_directory(directory, create=False)
    counts: dict[str, int] = {}
    entries = 0
    if base.exists():
        for item in base.iterdir():
            if entries >= 10000:
                return {"counts": counts, "scan_complete": False, "automatic_repair": False}
            entries += 1
            category = None
            if item.is_symlink():
                category = "unsafe_link"
            elif item.name.startswith(".retention-"):
                category = "legacy_retention_staging"
            elif ".quarantine-" in item.name:
                category = "quarantine"
            elif item.name.endswith((".inprogress", ".restore-inprogress", ".failed", ".tmp")):
                category = "interrupted_work"
            elif item.name.endswith(("-wal", "-shm", "-journal")):
                category = "sqlite_sidecar"
            elif item.name.endswith(".manifest.json") and not item.with_name(item.name.removesuffix(".manifest.json")).exists():
                category = "orphan_manifest"
            elif item.name.endswith(".lock"):
                category = "lock_requires_owner_review"
            elif item.is_file() and item.suffix == ".sqlite3" and not _manifest_for(item).exists():
                category = "unattested_database"
            if category:
                counts[category] = counts.get(category, 0) + 1
    return {"counts": counts, "scan_complete": True, "automatic_repair": False,
            "next_action": "OWNER_OFFLINE_REVIEW_REQUIRED" if counts else None}


def restore_plan(
    backup_path: Path,
    target_path: Path,
    *,
    migrate_clone: bool = False,
    min_free_bytes: int = DEFAULT_MIN_FREE_BYTES,
) -> dict[str, Any]:
    verified = verify_backup(backup_path)
    target = target_path.resolve(strict=False)
    _safe_directory(target_path.parent, create=False)
    if target_path.is_symlink() or (target.exists() and not target.is_file()):
        raise RecoveryError("RESTORE_TARGET_NOT_SAFE")
    if target == backup_path.resolve(strict=True):
        raise RecoveryError("RESTORE_TARGET_EQUALS_BACKUP")
    capacity = _disk_capacity(target.parent, max(verified["size_bytes"] * 2, 1024 * 1024), min_free_bytes)
    return {
        "mode": "dry_run",
        "read_only": True,
        "network_used": False,
        "backup": verified,
        "target": {
            "exists": target.exists(),
            "would_quarantine_existing": False,
            "atomic_replace": False,
            "publication": "new_clone_no_overwrite",
            "existing_target_apply_allowed": False,
        },
        "migrate_clone": migrate_clone,
        "target_schema_version": SCHEMA_VERSION if migrate_clone else verified["checks"]["schema_version"],
        "capacity": capacity,
        "would_write": capacity["enough"] and not target.exists(),
        "reason_code": (
            "RESTORE_EXISTING_TARGET_BLOCKED" if target.exists()
            else None if capacity["enough"] else "INSUFFICIENT_DISK_SPACE"
        ),
    }


def _assert_target_quiescent(target: Path) -> None:
    """Fail closed when replacing a live SQLite target could split its WAL state."""
    for suffix in ("-wal", "-shm", "-journal"):
        sidecar = Path(f"{target}{suffix}")
        if sidecar.exists() or sidecar.is_symlink():
            raise RecoveryError("TARGET_IN_USE_OR_WAL_ACTIVE")
    if not target.exists():
        return
    try:
        with target.open("rb") as handle:
            header = handle.read(20)
    except OSError as exc:
        raise RecoveryError("TARGET_IN_USE_OR_WAL_ACTIVE") from exc
    if header[:16] == b"SQLite format 3\x00" and (header[18:19] == b"\x02" or header[19:20] == b"\x02"):
        raise RecoveryError("TARGET_IN_USE_OR_WAL_ACTIVE")
    # This is a read-only sidecar/header screen, NEVER an isolation guarantee.
    # Existing targets are blocked by the public apply path, even with no writer.


def _assert_backup_attestation(backup_path: Path, expected: dict[str, Any]) -> None:
    manifest_path = _manifest_for(backup_path)
    if not _same_attestation(backup_path, expected["backup_evidence"]):
        raise RecoveryError("BACKUP_SOURCE_CHANGED_DURING_RESTORE")
    if not _same_attestation(manifest_path, expected["manifest_evidence"]):
        raise RecoveryError("BACKUP_SOURCE_CHANGED_DURING_RESTORE")
    verified = verify_backup(backup_path)
    if (
        verified["backup_evidence"] != expected["backup_evidence"]
        or verified["manifest_evidence"] != expected["manifest_evidence"]
    ):
        raise RecoveryError("BACKUP_SOURCE_CHANGED_DURING_RESTORE")


def restore_verify(
    backup_path: Path,
    *,
    migrate_clone: bool = False,
    work_directory: Path | None = None,
) -> dict[str, Any]:
    before = verify_backup(backup_path)
    base = _safe_directory(work_directory or backup_path.parent, create=False)
    with tempfile.TemporaryDirectory(prefix="pokemind-restore-verify-", dir=base) as raw:
        clone = Path(raw) / "clone.sqlite3"
        _copy_database(backup_path, clone, max_duration_seconds=1800)
        if migrate_clone:
            connection = connect_writable(clone)
            try:
                initialize_schema(connection)
            finally:
                connection.close()
        checks = _sqlite_checks(clone)
        if checks["status"] != "ok":
            raise RecoveryError("RESTORE_CLONE_VERIFICATION_FAILED")
    _assert_backup_attestation(backup_path, before)
    after_sha = _sha256_file(backup_path)
    return {
        "state": "verified",
        "read_only_target": True,
        "network_used": False,
        "backup_unchanged": before["sha256"] == after_sha,
        "source_schema_version": before["checks"]["schema_version"],
        "clone_schema_version": checks["schema_version"],
        "migrated_on_clone": migrate_clone,
        "checks": checks,
        "temporary_clone_removed": True,
    }


def _publish_isolated_restore(
    temporary: Path, target: Path, checks: dict[str, Any], *, _allow_existing_fixture: bool = False,
) -> dict[str, Any]:
    """Publication transaction for an isolated fixture or a NEW owner-selected clone.

    Existing-target support is exercised only by synthetic unit tests. Public
    restore_backup NEVER calls this helper with an existing target: SQLite's
    momentary exclusive lock cannot exclude external programs across a rename.
    This is exception-safe, not a claim of power-loss durability or live restore.
    """
    if target.exists() and not _allow_existing_fixture:
        raise RecoveryError("RESTORE_TARGET_APPEARED")
    original = _file_attestation(target) if target.exists() else None
    candidate_evidence = _file_attestation(temporary)
    quarantine = target.with_name(f"{target.name}.quarantine-{uuid.uuid4().hex}") if original else None
    quarantined = published = False
    publication_id = None
    try:
        if quarantine is not None:
            if quarantine.exists() or quarantine.is_symlink():
                raise RecoveryError("RESTORE_QUARANTINE_COLLISION")
            os.replace(target, quarantine)
            quarantined = True
        _assert_target_quiescent(target)
        with temporary.open("r+b") as handle:
            os.fsync(handle.fileno())
        # Hard-link publication is atomic and fails if another process creates
        # the target after the last gate. os.replace would overwrite that file.
        os.link(temporary, target)
        published = True
        publication_id = target.stat().st_ino
        _assert_target_quiescent(target)
        published_checks = _sqlite_checks(target)
        if published_checks["status"] != "ok" or published_checks["schema_version"] != checks["schema_version"]:
            raise RecoveryError("RESTORE_PUBLISHED_TARGET_INVALID")
        if not _same_attestation(target, candidate_evidence):
            raise RecoveryError("RESTORE_PUBLISHED_TARGET_CHANGED")
        temporary.unlink()
        namespace_synced = _sync_directory(target.parent)
        return {
            "schema_version": published_checks["schema_version"], "checks": published_checks,
            "quarantine_file": quarantine.name if quarantine else None,
            "directory_fsynced": namespace_synced,
        }
    except BaseException as exc:
        try:
            if quarantined:
                if quarantine is None or not _same_attestation(quarantine, original):
                    raise RecoveryError("RESTORE_ROLLBACK_INCOMPLETE")
                os.replace(quarantine, target)
                if _sha256_file(target) != original["sha256"]:
                    raise RecoveryError("RESTORE_ROLLBACK_INCOMPLETE")
            elif published:
                if target.is_symlink() or target.stat().st_ino != publication_id or not _same_attestation(target, candidate_evidence):
                    raise RecoveryError("RESTORE_ROLLBACK_INCOMPLETE")
                target.unlink()
                if target.exists() or target.is_symlink():
                    raise RecoveryError("RESTORE_ROLLBACK_INCOMPLETE")
        except BaseException as rollback_error:
            # Quarantine is deliberately preserved on failure. Do not clean up
            # uncertain original bytes or conceal that recovery is incomplete.
            raise RecoveryError("RESTORE_ROLLBACK_INCOMPLETE") from rollback_error
        if isinstance(exc, RecoveryError):
            raise RecoveryError(neutral_exception_code(exc, "RESTORE")) from exc
        raise RecoveryError("RESTORE_APPLY_FAILED") from exc


def restore_backup(
    backup_path: Path,
    target_path: Path,
    *,
    apply: bool = False,
    confirm_owner: bool = False,
    migrate_clone: bool = False,
    min_free_bytes: int = DEFAULT_MIN_FREE_BYTES,
) -> dict[str, Any]:
    if not apply:
        return restore_plan(
            backup_path, target_path, migrate_clone=migrate_clone, min_free_bytes=min_free_bytes
        )
    if not confirm_owner:
        raise RecoveryError("OWNER_CONFIRMATION_REQUIRED")
    target = target_path.resolve(strict=False)
    _assert_target_quiescent(target)
    if target.exists() or target_path.is_symlink():
        raise RecoveryError("RESTORE_EXISTING_TARGET_BLOCKED")
    plan = restore_plan(
        backup_path, target_path, migrate_clone=migrate_clone, min_free_bytes=min_free_bytes
    )
    if not plan["capacity"]["enough"]:
        raise RecoveryError("INSUFFICIENT_DISK_SPACE")
    target = target_path.resolve(strict=False)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.restore-inprogress")
    with _ProcessLock(target.parent / ".pokemind-restore.lock"):
        try:
            locked_source = verify_backup(backup_path)
            if (
                locked_source["backup_evidence"] != plan["backup"]["backup_evidence"]
                or locked_source["manifest_evidence"] != plan["backup"]["manifest_evidence"]
            ):
                raise RecoveryError("BACKUP_SOURCE_CHANGED_DURING_RESTORE")
            _assert_target_quiescent(target)
            if target.exists() or target.is_symlink():
                raise RecoveryError("RESTORE_TARGET_APPEARED")
            _copy_database(backup_path, temporary, max_duration_seconds=1800)
            if migrate_clone:
                connection = connect_writable(temporary)
                try:
                    initialize_schema(connection)
                finally:
                    connection.close()
            checks = _sqlite_checks(temporary)
            if checks["status"] != "ok":
                raise RecoveryError("RESTORE_CLONE_VERIFICATION_FAILED")
            # Last content-backed gate before any byte of the target is published.
            _assert_backup_attestation(backup_path, locked_source)
            _assert_target_quiescent(target)
            if target.exists() or target.is_symlink():
                raise RecoveryError("RESTORE_TARGET_APPEARED")
            published = _publish_isolated_restore(temporary, target, checks)
        except Exception as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                if not isinstance(exc, RecoveryError):
                    raise RecoveryError("RESTORE_CLEANUP_REQUIRED") from exc
            if isinstance(exc, RecoveryError):
                raise
            raise RecoveryError("RESTORE_APPLY_FAILED") from exc
    return {
        "mode": "applied",
        "state": "verified",
        "network_used": False,
        "schema_version": published["schema_version"],
        "checks": published["checks"],
        "backup_source_preserved": True,
        "quarantine_file": published["quarantine_file"],
        "atomic_replace": False,
        "publication": "new_clone_no_overwrite",
        "existing_target_apply_allowed": False,
        "activation": "OWNER_OFFLINE_ACTION_REQUIRED",
        "durability": {"directory_fsynced": published["directory_fsynced"],
                       "power_loss_guaranteed": False},
    }


def retention_plan(
    destination: Path,
    *,
    local_root: Path | None = None,
    keep_last: int = 7,
    max_age_days: int = 90,
    max_total_bytes: int = 20 * 1024 * 1024 * 1024,
    work_max_age_days: int = 7,
    log_max_age_days: int = 30,
    now: datetime | None = None,
) -> dict[str, Any]:
    if (type(keep_last) is not int or not 1 <= keep_last <= 1000
        or type(max_age_days) is not int or not 1 <= max_age_days <= 3650
        or any(type(n) is not int or n < 1 for n in (max_total_bytes, work_max_age_days, log_max_age_days))):
        raise RecoveryError("RETENTION_POLICY_INVALID")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise RecoveryError("RECOVERY_CLOCK_TIMEZONE_REQUIRED")
    directory = _safe_directory(destination, create=False)
    status = backup_status(directory)
    verified: list[dict[str, Any]] = []
    rejected = 0
    for item in status["backups"]:
        filename = item.get("backup_file")
        if not filename:
            rejected += 1
            continue
        try:
            evidence = verify_backup(directory / str(filename))
        except (OSError, RecoveryError):
            rejected += 1
            continue
        verified.append({**item, **evidence})
    verified.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    verified_inventory = [
        {
            "name": item["backup_file"],
            "backup_evidence": item["backup_evidence"],
            "manifest_evidence": item["manifest_evidence"],
        }
        for item in verified
    ]
    candidates: list[dict[str, Any]] = []
    retained_bytes = sum(int(item.get("size_bytes") or 0) for item in verified)
    for index, item in enumerate(verified):
        created_raw = str(item.get("created_at") or "1970-01-01T00:00:00Z")
        try:
            created = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        too_old = current.astimezone(timezone.utc) - created.astimezone(timezone.utc) > timedelta(days=max_age_days)
        over_size = retained_bytes > max_total_bytes
        if index >= keep_last and (too_old or over_size):
            candidates.append({
                "category": "verified_backup",
                "name": item["backup_file"],
                "manifest": f"{item['backup_file']}.manifest.json",
                "size_bytes": item["size_bytes"],
                "backup_evidence": item["backup_evidence"],
                "manifest_evidence": item["manifest_evidence"],
                "reason_code": "AGE_LIMIT" if too_old else "TOTAL_SIZE_LIMIT",
            })
            retained_bytes -= int(item.get("size_bytes") or 0)
    if directory.exists():
        for item in directory.iterdir():
            if item.is_symlink() or not item.is_file() or not item.name.endswith((".inprogress", ".failed")):
                continue
            age = current.timestamp() - item.stat().st_mtime
            if age > work_max_age_days * 86400:
                candidates.append({
                    "category": "work_file", "name": item.name,
                    "size_bytes": item.stat().st_size,
                    "file_evidence": _file_attestation(item),
                    "reason_code": "WORK_FILE_EXPIRED",
                })
    if local_root is not None:
        root = _safe_directory(local_root, create=False)
        log_dir = root / "update-logs"
        if log_dir.is_dir() and not log_dir.is_symlink():
            for item in log_dir.glob("*.jsonl"):
                age = current.timestamp() - item.stat().st_mtime
                if not item.is_symlink() and age > log_max_age_days * 86400:
                    candidates.append({
                        "category": "public_update_log", "name": f"update-logs/{item.name}",
                        "size_bytes": item.stat().st_size,
                        "file_evidence": _file_attestation(item),
                        "reason_code": "PUBLIC_LOG_EXPIRED",
                    })
    canonical_candidates = sorted(candidates, key=lambda item: (item["category"], item["name"]))
    token = hashlib.sha256(_canonical({
        "candidates": canonical_candidates,
        "verified_inventory": verified_inventory,
    })).hexdigest()
    return {
        "mode": "dry_run",
        "read_only": True,
        "network_used": False,
        "policy": {
            "keep_last": keep_last,
            "max_age_days": max_age_days,
            "max_total_bytes": max_total_bytes,
            "work_max_age_days": work_max_age_days,
            "log_max_age_days": log_max_age_days,
        },
        "candidates": canonical_candidates,
        "candidate_count": len(canonical_candidates),
        "candidate_bytes": sum(int(item["size_bytes"]) for item in canonical_candidates),
        "plan_sha256": token,
        "verified_backup_count": len(verified),
        "rejected_backup_count": rejected,
        "inventory_complete": status.get("inventory_complete", True),
        "retained_evidence": [item for item in verified_inventory if item["name"] not in {
            candidate["name"] for candidate in canonical_candidates if candidate["category"] == "verified_backup"
        }],
        "preserved": [
            "SQLite application data and attestations",
            "normative source provenance and public source observations",
            "catalog indexes and snapshots stored inside SQLite",
            "every backup inside keep_last",
        ],
        "apply_requires": ["--apply", "--confirm-owner", "--plan-sha256"],
        "apply_allowed": False,
        "reason_code": "RETENTION_EXTERNAL_EXCLUSION_UNPROVEN",
    }


def apply_retention(
    destination: Path,
    *,
    local_root: Path | None = None,
    plan_sha256: str,
    apply: bool = False,
    confirm_owner: bool = False,
    **policy: Any,
) -> dict[str, Any]:
    plan = retention_plan(destination, local_root=local_root, **policy)
    if not apply:
        return plan
    if not confirm_owner:
        raise RecoveryError("OWNER_CONFIRMATION_REQUIRED")
    if not plan["inventory_complete"]:
        raise RecoveryError("RETENTION_INVENTORY_LIMIT_EXCEEDED")
    if not plan_sha256 or plan_sha256 != plan["plan_sha256"]:
        raise RecoveryError("RETENTION_PLAN_CHANGED")
    # A cooperative lock cannot keep another process from deleting keep_last
    # or replacing staging paths. Multi-file rollback can overwrite new files;
    # power-loss recovery has no durable transaction. No private bypass exists.
    raise RecoveryError("RETENTION_EXTERNAL_EXCLUSION_UNPROVEN")
