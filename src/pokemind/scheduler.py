"""Prévisualisation sûre du planificateur Windows, sans mutation du système."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape
from pokemind.toronto_tz import toronto_zone


TASK_DAILY = "PokeMind-PublicKnowledge-Daily"
TASK_DEEP = "PokeMind-PublicKnowledge-TueFri"
_TIME = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d\Z")
TORONTO_WINDOWS_TIMEZONE = "Eastern Standard Time"


class SchedulerError(ValueError):
    """Erreur contrôlée de préparation du planificateur."""


def _validated_time(value: str, field: str) -> str:
    if not _TIME.fullmatch(value):
        raise SchedulerError(f"{field} doit être HH:MM sur 24 heures.")
    return value


def _detected_windows_timezone() -> str | None:
    """Lit le fuseau Windows sans modifier le système; aucun shell n'est utilisé."""
    if os.name != "nt":
        return None
    try:
        result = subprocess.run(
            ["tzutil.exe", "/g"], capture_output=True, text=True,
            timeout=5, check=False, shell=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def _validated_windows_timezone(value: str | None) -> str:
    # A preview must not launch even a system utility. This is a declared
    # precondition; real OS timezone/DST proof is a separate owner action.
    detected = value.strip() if isinstance(value, str) and value.strip() else None
    if detected is None:
        raise SchedulerError(
            "WINDOWS_TIMEZONE_REQUIRED: fournir --windows-timezone avec la sortie de tzutil /g."
        )
    if detected != TORONTO_WINDOWS_TIMEZONE:
        raise SchedulerError(
            "WINDOWS_TIMEZONE_NOT_TORONTO: les déclencheurs locaux exigent Eastern Standard Time."
        )
    return detected


def _task_xml(*, task_name: str, start_time: str, days: tuple[str, ...], command: str, arguments: str, working_directory: str) -> str:
    if days:
        day_nodes = "".join(f"<{day} />" for day in days)
        trigger = (
            "<CalendarTrigger><StartBoundary>2000-01-01T" + start_time + ":00</StartBoundary>"
            "<Enabled>true</Enabled><ScheduleByWeek><WeeksInterval>1</WeeksInterval>"
            f"<DaysOfWeek>{day_nodes}</DaysOfWeek></ScheduleByWeek></CalendarTrigger>"
        )
    else:
        trigger = (
            "<CalendarTrigger><StartBoundary>2000-01-01T" + start_time + ":00</StartBoundary>"
            "<Enabled>true</Enabled><ScheduleByDay><DaysInterval>1</DaysInterval>"
            "</ScheduleByDay></CalendarTrigger>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">'
        f"<RegistrationInfo><Description>{escape(task_name)} — données publiques seulement; aucun LLM.</Description></RegistrationInfo>"
        f"<Triggers>{trigger}</Triggers>"
        '<Principals><Principal id="Author"><LogonType>InteractiveToken</LogonType>'
        '<RunLevel>LeastPrivilege</RunLevel></Principal></Principals>'
        '<Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>'
        '<StartWhenAvailable>true</StartWhenAvailable><DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>'
        '<StopIfGoingOnBatteries>false</StopIfGoingOnBatteries><ExecutionTimeLimit>PT30M</ExecutionTimeLimit>'
        '<Enabled>true</Enabled></Settings>'
        '<Actions Context="Author"><Exec>'
        f"<Command>{escape(command)}</Command><Arguments>{escape(arguments)}</Arguments>"
        f"<WorkingDirectory>{escape(working_directory)}</WorkingDirectory>"
        '</Exec></Actions></Task>'
    )


def scheduler_preview(
    project_root: Path,
    *,
    action: str = "preview",
    daily_time: str | None = None,
    deep_time: str | None = None,
    dry_run: bool = True,
    confirm_owner: bool = False,
    windows_timezone: str | None = None,
    public_database: Path | None = None,
) -> dict[str, Any]:
    if action not in {"preview", "install", "uninstall", "status"}:
        raise SchedulerError("Action scheduler invalide.")
    root = project_root.resolve()
    if public_database is not None:
        from pokemind.public_campaign import public_database_path
        public_database = public_database_path(root, public_database)
    script = (root / "scripts" / "pokemind_update.ps1").resolve()
    if not script.is_relative_to(root):
        raise SchedulerError("Le lanceur scheduler sort de la racine du projet.")
    if action in {"preview", "install"}:
        if daily_time is None or deep_time is None:
            raise SchedulerError("Les heures --daily-time et --deep-time sont requises; aucune heure n'est inventée.")
        daily_time = _validated_time(daily_time, "--daily-time")
        deep_time = _validated_time(deep_time, "--deep-time")
        windows_timezone = _validated_windows_timezone(windows_timezone)
    if not dry_run:
        if action in {"install", "uninstall"} and not confirm_owner:
            raise SchedulerError("Une mutation du planificateur exigerait --confirm-owner.")
        raise SchedulerError("SCHEDULER_ACTIVATION_DISABLED_IN_LOT_D")
    manifests: list[dict[str, Any]] = []
    if action in {"preview", "install"}:
        specs = (
            (TASK_DAILY, daily_time or "", (), "Daily"),
            (TASK_DEEP, deep_time or "", ("Tuesday", "Friday"), "Deep"),
        )
        for name, start, days, mode in specs:
            arguments = f'-NoProfile -NonInteractive -File "{script}" -Mode {mode}'
            database_argument = str(public_database) if public_database is not None else "<OWNER_PUBLIC_DATABASE_REQUIRED>"
            if any(character in database_argument for character in ('"', '\r', '\n', '\x00')):
                raise SchedulerError("PUBLIC_UPDATE_DATABASE_ARGUMENT_INVALID")
            arguments += f' -Database "{database_argument}"'
            if mode == "Deep":
                arguments += f" -DeepTime {deep_time}"
            xml = _task_xml(
                task_name=name, start_time=start, days=days, command="powershell.exe",
                arguments=arguments, working_directory=str(root),
            )
            manifests.append({
                "task_name": name, "local_time": start, "days": list(days) or ["EveryDay"],
                "timezone": "America/Toronto",
                "windows_timezone": windows_timezone,
                "timezone_precondition_verified": False,
                "timezone_precondition_asserted": True,
                "run_level": "LeastPrivilege", "multiple_instances": "IgnoreNew",
                "start_when_available": True, "working_directory": str(root),
                "command": "powershell.exe", "arguments": arguments,
                "manifest_sha256": hashlib.sha256(xml.encode("utf-8")).hexdigest(),
                "xml": xml,
            })
    commands = {
        "install": [f'schtasks /Create /TN "{name}" /XML "<generated-manifest-path>" /F' for name in (TASK_DAILY, TASK_DEEP)],
        "uninstall": [f'schtasks /Delete /TN "{name}" /F' for name in (TASK_DAILY, TASK_DEEP)],
        "status": [f'schtasks /Query /TN "{name}" /V /FO LIST' for name in (TASK_DAILY, TASK_DEEP)],
    }
    result = {
        "status": "DRY_RUN_ONLY", "action": action, "dry_run": True,
        "system_changed": False, "scheduler_contacted": False,
        "os_activation_status": "OWNER_ACTION_REQUIRED",
        "active_service_proven": False,
        "owner_confirmation_received": bool(confirm_owner),
        "activation_gate": "SCHEDULER_ACTIVATION_DISABLED_IN_LOT_D",
        "manifests": manifests,
        "simulated_commands": commands.get(action, commands["install"] if action == "preview" else []),
        "uninstall_recovery": commands["uninstall"],
        "configuration": {
            "public_data_only": True, "llm_started": False, "codex_started": False,
            "database_selection": "DECLARED_NOT_ATTESTED" if public_database is not None else "OWNER_SELECTION_REQUIRED",
            "runtime_public_workspace_check": True,
            "concurrency_lock": "data/local/knowledge-update.lock",
            "run_history": "SQLite knowledge_update_cycles + data/local/update-logs",
            "catch_up": "StartWhenAvailable plus déduplication des cycles Toronto",
            "windows_timezone_required": TORONTO_WINDOWS_TIMEZONE,
            "windows_timezone_observed": None,
            "windows_timezone_declared": windows_timezone,
            "timezone_strategy": "owner-declared precondition only; OS timezone and DST unverified",
        },
    }
    # Garantit que la structure est sérialisable avant de la retourner au CLI.
    json.dumps(result, ensure_ascii=False)
    return result


def cadence_preview(*, start_utc: datetime, daily_time: str, deep_time: str, days: int = 14):
    """Simulation of local Toronto deadlines; never attest Windows OS behavior.

    Missing spring minute moves forward; repeated fall minute uses first fold.
    Real Task Scheduler/DST behavior requires a separate owner-authorized trial.
    """
    if start_utc.tzinfo is None or type(days) is not int or not 1 <= days <= 60:
        raise SchedulerError("CADENCE_CLOCK_OR_WINDOW_INVALID")
    daily_time = _validated_time(daily_time, "daily_time")
    deep_time = _validated_time(deep_time, "deep_time")
    zone = toronto_zone()
    start = start_utc.astimezone(zone)
    events = []
    for offset in range(days):
        day = start.date() + timedelta(days=offset)
        specs = [("daily", daily_time)] + ([("deep", deep_time)] if day.weekday() in {1, 4} else [])
        for mode, clock in specs:
            requested = datetime.fromisoformat(f"{day.isoformat()}T{clock}:00")
            candidate = requested.replace(tzinfo=zone, fold=0)
            shifted = 0
            while candidate.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) != candidate.replace(tzinfo=None):
                shifted += 1
                candidate = (requested + timedelta(minutes=shifted)).replace(tzinfo=zone, fold=0)
                if shifted > 180:
                    raise SchedulerError("CADENCE_LOCAL_TIME_UNRESOLVED")
            if candidate.astimezone(timezone.utc) >= start_utc.astimezone(timezone.utc):
                events.append({"mode": mode, "scheduled_local_date": day.isoformat(),
                               "local_deadline": candidate.isoformat(), "utc_deadline": candidate.astimezone(timezone.utc).isoformat(),
                               "dst_shift_minutes": shifted, "fold": candidate.fold,
                               "deep_time_argument": deep_time if mode == "deep" else None})
    events.sort(key=lambda e: (e["utc_deadline"], e["mode"]))
    return {"status": "SIMULATION_ONLY", "os_activation_status": "OWNER_ACTION_REQUIRED",
            "system_changed": False, "scheduler_contacted": False, "network_used": False,
            "timezone": "America/Toronto", "windows_timezone": TORONTO_WINDOWS_TIMEZONE,
            "events": events, "dst_policy": "spring_forward_to_valid_minute; fall_first_fold",
            "real_os_dst_verified": False}
