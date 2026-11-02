from __future__ import annotations

import os
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["POKEMIND_ROOT"] = str(ROOT)
    return environment


def test_cli_help_works() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "pokemind", "--help"],
        cwd=ROOT,
        env=_environment(),
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "import-seed" in completed.stdout
    assert "search" in completed.stdout
    assert "status" in completed.stdout
    assert "log" in completed.stdout
    assert "profile" in completed.stdout
    assert "deck" in completed.stdout
    assert "meta" in completed.stdout
    assert "analyze" in completed.stdout
    assert "match" in completed.stdout


def test_match_cli_synthetic_multiturn_path(local_tmp: Path) -> None:
    db_path = local_tmp / "match-cli.sqlite3"
    start = subprocess.run(
        [sys.executable, "-m", "pokemind", "match", "start", "--as-of", "2026-10-13",
         "--apply", "--confirm-owner", "--db", str(db_path), "--json"],
        cwd=ROOT, env=_environment(), text=True, encoding="utf-8", capture_output=True, check=False,
    )
    assert start.returncode == 0, start.stderr
    session_id = json.loads(start.stdout)["session_id"]
    for turn in (1, 2, 3):
        annotation = local_tmp / f"turn-{turn}.json"
        annotation.write_text(json.dumps({
            "turn": turn, "phase": "main", "turn_owner": "self",
            "sides": {"self": {"active": {"visibility": "unknown"}},
                      "opponent": {"hand": {"visibility": "hidden"},
                                   "prizes": {"apparent_count": 6}}},
            "unknown_fields": ["Identité de l'Actif"],
        }), encoding="utf-8")
        observe = subprocess.run(
            [sys.executable, "-m", "pokemind", "match", "observe", "--annotation", str(annotation),
             "--session", session_id, "--turn", str(turn), "--mode", "training",
             "--apply", "--confirm-owner", "--db", str(db_path), "--json"],
            cwd=ROOT, env=_environment(), text=True, encoding="utf-8", capture_output=True, check=False,
        )
        assert observe.returncode == 0, observe.stderr
        assert json.loads(observe.stdout)["status"] == "SAVED"
    show = subprocess.run(
        [sys.executable, "-m", "pokemind", "match", "show", "--session", session_id,
         "--db", str(db_path), "--json"],
        cwd=ROOT, env=_environment(), text=True, encoding="utf-8", capture_output=True, check=False,
    )
    payload = json.loads(show.stdout)
    assert show.returncode == 0 and len(payload["observations"]) == 3
    assert all(row["state"]["hidden_information_policy"]["prize_contents"] == "UNKNOWN" for row in payload["observations"])
    advise = subprocess.run(
        [sys.executable, "-m", "pokemind", "match", "advise", "--session", session_id,
         "--turn", "3", "--as-of", "2026-10-13", "--db", str(db_path), "--json"],
        cwd=ROOT, env=_environment(), text=True, encoding="utf-8", capture_output=True, check=False,
    )
    advice = json.loads(advise.stdout)
    assert advise.returncode == 0 and advice["status"] == "INSUFFICIENT_EVIDENCE"
    assert advice["next_annotation_or_capture"]


def test_historical_collection_status_is_explicit_in_json_and_human_output(local_tmp: Path) -> None:
    db_path = local_tmp / "old-schema.sqlite3"
    db_path.touch()
    for json_mode in (False, True):
        arguments = [
            sys.executable, "-m", "pokemind", "collection", "status",
            "--as-of", "2026-05-01", "--db", str(db_path),
        ]
        if json_mode:
            arguments.append("--json")
        completed = subprocess.run(
            arguments, cwd=ROOT, env=_environment(), text=True, encoding="utf-8",
            capture_output=True, check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert "NOT_AVAILABLE_AS_OF" in completed.stdout


def test_cli_json_round_trip_uses_only_local_data(local_tmp: Path) -> None:
    db_path = local_tmp / "cli.sqlite3"
    for arguments in (
        ["import-seed", "--db", str(db_path), "--json"],
        ["search", "gestion des récompenses", "--db", str(db_path), "--json"],
        ["status", "--db", str(db_path), "--json"],
    ):
        completed = subprocess.run(
            [sys.executable, "-m", "pokemind", *arguments],
            cwd=ROOT,
            env=_environment(),
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert '"ok": true' in completed.stdout


def test_cli_log_import_and_profile_json(local_tmp: Path) -> None:
    db_path = local_tmp / "battle-cli.sqlite3"
    log_path = ROOT / "tests" / "fixtures" / "battle_logs" / "victory_en.txt"
    commands = (
        ["log", "import", str(log_path), "--deck", "principal", "--db", str(db_path), "--json"],
        ["profile", "summary", "--deck", "principal", "--db", str(db_path), "--json"],
        ["profile", "review", "--deck", "principal", "--db", str(db_path), "--json"],
    )
    for arguments in commands:
        completed = subprocess.run(
            [sys.executable, "-m", "pokemind", *arguments],
            cwd=ROOT,
            env=_environment(),
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        assert '"ok": true' in completed.stdout


def test_cli_reparse_keeps_one_battle_and_same_deck(local_tmp: Path) -> None:
    db_path = local_tmp / "battle-reparse-cli.sqlite3"
    log_path = ROOT / "tests" / "fixtures" / "battle_logs" / "victory_en.txt"
    for extra in ([], ["--reparse"]):
        completed = subprocess.run(
            [
                sys.executable, "-m", "pokemind", "log", "import", str(log_path),
                "--deck", "principal", *extra, "--db", str(db_path), "--json",
            ],
            cwd=ROOT,
            env=_environment(),
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
    assert '"reparsed": true' in completed.stdout

    status = subprocess.run(
        [sys.executable, "-m", "pokemind", "status", "--db", str(db_path), "--json"],
        cwd=ROOT,
        env=_environment(),
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=True,
    )
    assert '"battle_logs": 1' in status.stdout


def test_local_databases_and_secret_file_names_are_ignored_by_git() -> None:
    candidates = [
        "data/local/pokemind.sqlite3",
        "data/local/private.log",
        ".env",
        "secret.pem",
        "secret.key",
    ]
    for candidate in candidates:
        completed = subprocess.run(
            ["git", "check-ignore", "-q", candidate],
            cwd=ROOT,
            check=False,
        )
        assert completed.returncode == 0, candidate

    tracked = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.splitlines()
    forbidden_suffixes = (".sqlite", ".sqlite3", ".db", ".pem", ".key")
    assert not any(path.startswith("data/local/") and path != "data/local/.gitkeep" for path in tracked)
    assert not any(path.lower().endswith(forbidden_suffixes) for path in tracked)
    assert not any(Path(path).name in {".env", ".env.local", ".env.production"} for path in tracked)


def test_repository_hygiene_script_passes_without_network() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/check_repo_hygiene.py"],
        cwd=ROOT, env=_environment(), text=True, capture_output=True, check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "repo_hygiene=ok" in completed.stdout
