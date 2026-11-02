"""One local entry point over the existing immutable battle memory and engines."""
from __future__ import annotations

import json
import os
import re
import stat
import uuid
from datetime import date
from pathlib import Path

from pokemind import battle_batch, legacy_bridge

REPORT_DIR = "data/local/battle-intelligence"
LOG_DIR = "data/local/battle_logs"
DB = "data/local/pokemind.sqlite3"
CANONICAL = re.compile(r"analysis-[0-9a-f]{64}\.json")
MAX_ENTRIES = 5000
MAX_DISCOVERY_BYTES = 256 * 1024 * 1024
MAX_CONTROL_BYTES = 16 * 1024
# Canonical reports are immutable and content-addressed. Their rank is cached by
# file identity so discovery stops re-parsing every historical report on each
# load and each coach question; any change of inode, size or mtime re-validates.
_RANKS = {}


class CoachError(ValueError):
    """Fixed codes only; private paths and payloads never become CLI errors."""


def _directory(root, relative):
    path = battle_batch.safe_path(root, root / relative, exists=False)
    created = not path.exists()
    path.mkdir(parents=True, exist_ok=True)
    battle_batch.safe_path(root, path)
    if not path.is_dir():
        raise CoachError("COACH_DIRECTORY_REQUIRED")
    return path, created


def _control(root, path):
    """Corrupt JSON can be repaired; redirected or multiply linked files cannot."""
    battle_batch.safe_path(root, path, exists=False)
    if not path.exists():
        return None, None
    stamp = legacy_bridge._stamp(path)
    if stamp[2] > MAX_CONTROL_BYTES:
        return None, stamp
    try:
        value, checked = legacy_bridge._json(root, path)
        if checked != stamp:
            raise CoachError("COACH_CONTROL_CHANGED")
        return value, stamp
    except legacy_bridge.BridgeError as error:
        if str(error) in {"BRIDGE_INVALID_JSON", "BRIDGE_DUPLICATE_JSON_KEY",
                          "BRIDGE_NONFINITE_JSON", "BRIDGE_JSON_COMPLEXITY_CAP",
                          "BRIDGE_JSON_STRING_CAP"}:
            return None, stamp
        raise


def _atomic_control(root, path, value, stamp):
    """Replace only our mutable control file, retaining every immutable snapshot."""
    raw = (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if len(raw) > MAX_CONTROL_BYTES:
        raise CoachError("COACH_CONTROL_SIZE_CAP")
    battle_batch.safe_path(root, path, exists=False)
    if stamp is not None:
        if legacy_bridge._stamp(path) != stamp:
            raise CoachError("COACH_CONTROL_CHANGED")
        if stamp[2] <= MAX_CONTROL_BYTES:
            previous, _ = legacy_bridge._bytes(root, path, maximum=MAX_CONTROL_BYTES)
            if previous == raw:
                return False
    temporary = path.with_name(".coach-" + uuid.uuid4().hex + ".tmp")
    battle_batch.safe_path(root, temporary, exists=False)
    with temporary.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    battle_batch.safe_path(root, path, exists=False)
    if (stamp is None and path.exists()) or (stamp is not None and legacy_bridge._stamp(path) != stamp):
        # Preserve a failed staging file for inspection; never delete user files.
        raise CoachError("COACH_CONTROL_CHANGED")
    battle_batch.safe_path(root, temporary)
    os.replace(temporary, path)
    battle_batch.safe_path(root, path)
    return True


def _player(value):
    if (not isinstance(value, str) or not value.strip() or len(value) > 100
            or any(not c.isprintable() for c in value)):
        raise CoachError("COACH_PLAYER_REQUIRED")
    return value.strip()


def _settings(root, target, explicit):
    path = target / "coach-settings.json"
    value, stamp = _control(root, path)
    remembered = None
    if value is not None:
        if (not isinstance(value, dict) or set(value) != {"schema_version", "player"}
                or type(value["schema_version"]) is not int or value["schema_version"] != 1):
            raise CoachError("COACH_SETTINGS_INVALID")
        remembered = _player(value["player"])
    elif stamp is not None:
        raise CoachError("COACH_SETTINGS_INVALID")
    selected = _player(explicit) if explicit is not None else remembered
    if remembered and selected != remembered:
        raise CoachError("COACH_PLAYER_CONFLICT")
    changed = False
    if selected and remembered is None:
        changed = _atomic_control(root, path, {"schema_version": 1, "player": selected}, stamp)
    return selected, changed


def _discover(root, target):
    candidates, refused, total = [], 0, 0
    with os.scandir(target) as entries:
        for number, entry in enumerate(entries, 1):
            if number > MAX_ENTRIES:
                raise CoachError("COACH_REPORT_DISCOVERY_CAP")
            if not CANONICAL.fullmatch(entry.name):
                continue
            path = Path(entry.path)
            try:
                battle_batch.safe_path(root, path)
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    refused += 1
                    continue
                if info.st_size > legacy_bridge.MAX_REPORT_BYTES:
                    refused += 1
                    continue
                total += info.st_size
                if total > MAX_DISCOVERY_BYTES:
                    raise CoachError("COACH_REPORT_BYTES_CAP")
                identity = (str(path), info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)
                if identity not in _RANKS:
                    result = legacy_bridge.saved_report(root, report=path)
                    _RANKS[identity] = None if result["report"]["coverage"]["valid"] == 0 else (
                        result["stored_as_of"], int(result["report"]["model_version"].rsplit("v", 1)[1]),
                        info.st_mtime_ns, path.name)
                    del result
                rank = _RANKS[identity]
                if rank is None:
                    refused += 1
                    continue
                candidates.append((rank, path))
            except CoachError:
                raise
            except (ValueError, OSError):
                refused += 1
    return max(candidates)[1] if candidates else None, refused


def _empty(status, text, *, writes):
    return {"status": status, "text": text + "\n", "report": None,
            "reanalysis_performed": False, "database_opened": False,
            "network_used": False, "writes_performed": writes}


def coach(root, *, player=None, update=False, as_of=None, cancelled=None, progress=None, complete_only=False):
    """Fixed project paths; --update refreshes local knowledge, with zero GETs."""
    try:
        if cancelled and cancelled():
            raise CoachError('COACH_CANCELLED')
        root = Path(root).absolute()
        evaluated = as_of or date.today().isoformat()
        try:
            valid_date = date.fromisoformat(evaluated).isoformat() == evaluated
        except (ValueError, TypeError):
            valid_date = False
        if not valid_date:
            raise CoachError("COACH_DATE_INVALID")
        target, directories_created = _directory(root, REPORT_DIR)
        selected_player, settings_written = _settings(root, target, player)
        index_path = target / "latest.json"
        old_index, index_stamp = _control(root, index_path)
        selected, refused = _discover(root, target)
        if update and selected is not None and legacy_bridge.saved_report(root, report=selected)["stored_as_of"] > evaluated:
            raise CoachError("COACH_DATE_BEFORE_SAVED_REPORT")
        analyzed, memory_status, database_opened = False, None, False
        if selected is None or update:
            folder, created = _directory(root, LOG_DIR)
            directories_created |= created
            paths, _, _ = battle_batch.files_in_folder(root, folder)
            if not paths:
                if selected is None:
                    return _empty("COACH_NO_BATTLE_LOGS",
                        "Aucun rapport réel valide ni journal .txt/.log admissible dans data/local/battle_logs. "
                        "Ajoutez vos journaux dans ce dossier, puis relancez battle coach.", writes=settings_written or directories_created)
                memory_status = "NO_NEW_LOGS_SAVED_REPORT_RETAINED"
            else:
                if selected_player is None:
                    raise CoachError("COACH_PLAYER_REQUIRED")
                # Exactly one existing batch-engine invocation. No public refresher,
                # new database, migration or alternative persistence engine.
                try:
                    result = battle_batch.batch_analyze(root, folder=folder, player=selected_player,
                        db=root / DB, as_of=evaluated, apply=True, cancelled=cancelled, progress=progress, complete_only=complete_only)
                except ValueError as error:
                    if str(error) == 'BATCH_CANCELLED':
                        raise CoachError('COACH_CANCELLED') from None
                    raise
                analyzed = True
                database_opened = ("schema_version" in result["persistence"]
                    or result["persistence"]["status"] == "BLOCKED_INTEGRITY")
                memory = result.get("memory", {})
                memory_status = memory.get("status")
                if memory_status not in {"SAVED_LOCAL", "ALREADY_PRESENT_IDENTICALLY"}:
                    raise CoachError("COACH_MEMORY_NOT_SAVED")
                relative = memory.get("report", "")
                selected = battle_batch.safe_path(root, root / relative)
                if selected.parent != target or not CANONICAL.fullmatch(selected.name):
                    raise CoachError("COACH_CANONICAL_REPORT_REQUIRED")
                if not result["coverage"]["valid"]:
                    return _empty("COACH_NO_VALID_MATCHES",
                        "Les journaux présents ne fournissent aucun match valide pour le joueur configuré. "
                        "Diagnostic conservé localement; aucun bilan de victoires inventé.", writes=True) | {
                            "reanalysis_performed": True, "database_opened": database_opened,
                            "database_preflight_performed": True}
        if cancelled and cancelled():
            raise CoachError('COACH_CANCELLED')
        result = legacy_bridge.saved_report(root, report=selected)
        learning_path = selected.with_name(selected.stem + ".learning.json")
        learning_status = "ABSENT"
        if learning_path.exists() or learning_path.is_symlink():
            try:
                result = legacy_bridge.saved_report(root, report=selected, learning=learning_path)
                learning_status = "VALIDATED_EXISTING_LEARNING_LOOP"
            except (ValueError, OSError):
                learning_status = "UNAVAILABLE_NOT_MODIFIED"
        new_index = {"schema_version": 1, "snapshot": selected.name,
                     "as_of": result["stored_as_of"], "model_version": result["report"]["model_version"]}
        index_state = ("CURRENT" if old_index == new_index else "MISSING" if index_stamp is None
                       else "CORRUPT" if old_index is None else "STALE")
        index_written = _atomic_control(root, index_path, new_index, index_stamp)
        result.update(status="COACH_LOCAL_REPORT", snapshot_selection="LATEST_VALID_CANONICAL",
            source_action="LOCAL_BATCH_ANALYSIS" if analyzed else "SAVED_REPORT",
            reanalysis_performed=analyzed, database_opened=database_opened, network_used=False,
            database_preflight_performed=analyzed,
            writes_performed=settings_written or index_written or analyzed or directories_created,
            index_status=index_state, index_written=index_written,
            learning_status=learning_status, memory_status=memory_status,
            refused_report_candidates=refused, player_configured=selected_player is not None)
        result["text"] = ("PokeMind — coach local; " + ("analyse des journaux effectuée." if analyzed else
            "rapport conservé, sans retraitement des journaux.") + "\n" + result["db_import_status"]
            + "\nLearning Loop : " + learning_status + "\n"
            + ("Aucun journal admissible; rapport conservé affiché.\n" if memory_status == "NO_NEW_LOGS_SAVED_REPORT_RETAINED" else "")
            + battle_batch.human_report(result["report"]).replace("analyse réelle locale", "analyse conservée")
                .replace("Mémoire PUBLIC enrichie :", "Mémoire PUBLIC conservée (collecte historique, aucun GET dans cet appel) :")
                .replace("Autres références publiques nouvellement récupérées", "Autres références publiques déjà conservées")
            + "\nPour intégrer les nouvelles parties et connaissances locales : battle coach --update (hors ligne).\n")
        return result
    except CoachError:
        raise
    except (ValueError, OSError, KeyError, TypeError, AttributeError, IndexError, RecursionError):
        raise CoachError("COACH_LOCAL_DATA_UNAVAILABLE_OR_UNSAFE") from None
