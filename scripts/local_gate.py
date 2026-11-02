"""Porte de qualité locale : les étapes de la CI, hors du dépôt et sans data/local.

Copie les fichiers suivis et non ignorés (jamais data/local, build, dist ou venv)
dans un dossier temporaire court, puis y lance compilation, hygiène Git, tests Qt
et tests du cœur hors ligne. Le dépôt et les données personnelles ne sont jamais
le répertoire de travail des tests.

    python scripts/local_gate.py                 # suite complète
    python scripts/local_gate.py -k motion       # arguments pytest transmis aux deux passes
    python scripts/local_gate.py --keep          # conserve la copie pour inspection
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QT_TESTS = ["tests/test_desktop_qt.py", "tests/test_desktop_workflow_qt.py"]
SUMMARY = re.compile(r"^=*\s*(\d+ (?:passed|failed|error|skipped|deselected).*?) in [\d.]+s", re.M)


def tracked_files() -> list[Path]:
    output = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                            cwd=ROOT, capture_output=True, check=True).stdout
    paths = [Path(item.decode("utf-8")) for item in output.split(b"\0") if item]
    return [p for p in paths if p.parts[:2] != ("data", "local") and (ROOT / p).is_file()]


def copy_tree(target: Path) -> int:
    files = tracked_files()
    for relative in files:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    (target / "data/local").mkdir(parents=True, exist_ok=True)
    # Some repository tests inspect Git metadata; a local repository keeps them offline.
    git = ["git", "-c", "core.autocrlf=false", "-c", "core.safecrlf=false"]
    for command in (["init", "-q"], ["add", "-A"],
                    ["-c", "user.name=gate", "-c", "user.email=gate@invalid", "commit", "-q", "-m", "gate"]):
        subprocess.run(git + command, cwd=target, check=True, capture_output=True)
    return len(files)


def remove_copy(target: Path) -> None:
    """Git marks its objects read-only on Windows; clear the flag, then retry."""
    def writable(function, path, _):
        os.chmod(path, stat.S_IWRITE)
        function(path)
    shutil.rmtree(target, onerror=writable)


def run(label: str, command: list[str], cwd: Path, env: dict[str, str], *, allowed=(0,)) -> tuple[bool, str]:
    started = time.monotonic()
    completed = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
    elapsed = time.monotonic() - started
    output = completed.stdout + completed.stderr
    found = SUMMARY.findall(output)
    detail = found[-1] if found else ("ok" if completed.returncode == 0 else "échec")
    passed = completed.returncode in allowed
    status = "OK " if passed else "ÉCHEC"
    print(f"[{status}] {label} · {detail} · {elapsed:.0f}s", flush=True)
    if not passed:
        failures = [line for line in output.splitlines() if line.startswith(("FAILED", "ERROR"))]
        print("\n".join(failures[:40]) or output[-4000:], flush=True)
    return passed, output


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--keep", action="store_true", help="conserver la copie temporaire")
    options, pytest_args = parser.parse_known_args(argv)
    # Short base path: nested synthetic project roots exceed Windows MAX_PATH otherwise.
    base = Path(os.environ.get("POKEMIND_GATE_DIR") or tempfile.gettempdir()) / "pmg"
    target = base / uuid.uuid4().hex[:8]
    target.mkdir(parents=True)
    env = dict(os.environ, POKEMIND_TEST_OFFLINE="1", QT_QPA_PLATFORM="offscreen",
               PYTHONDONTWRITEBYTECODE="1")
    for name in ("POKEMIND_SYNTHETIC_QA_ROOT", "POKEMIND_SYNTHETIC_QA_TOKEN"):
        env.pop(name, None)
    python = [sys.executable]
    extra = pytest_args
    # A filtered run may select nothing in one of the two passes (pytest exit 5).
    allowed = (0, 5) if extra else (0,)
    results = []
    try:
        print(f"Copie de {copy_tree(target)} fichiers vers {target}", flush=True)
        results.append(run("compilation", python + ["-m", "compileall", "-q", "src", "tests", "scripts"], target, env)[0])
        results.append(run("hygiène Git", python + ["scripts/check_repo_hygiene.py"], target, env)[0])
        pytest = python + ["-m", "pytest", "-q", "-p", "no:cacheprovider"]
        results.append(run("tests Qt", pytest + QT_TESTS + extra, target, env, allowed=allowed)[0])
        ignored = [f"--ignore={path}" for path in QT_TESTS]
        results.append(run("tests du cœur", pytest + ignored + extra, target, env, allowed=allowed)[0])
    finally:
        if options.keep:
            print(f"Copie conservée : {target}")
        else:
            remove_copy(target)
    print("PORTE LOCALE : " + ("VERTE" if all(results) else "ROUGE"))
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
