"""Échec CI si Git suit une donnée privée, un secret évident ou un gros binaire."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_TRACKED_BYTES = 10 * 1024 * 1024
FORBIDDEN_SUFFIXES = {".sqlite", ".sqlite3", ".db", ".pem", ".key", ".p12", ".pfx"}
SECRET_PATTERNS = {
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(rb"\bgh[psu]_[A-Za-z0-9]{30,}\b"),
    "aws_access_key": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "bearer_jwt": re.compile(rb"\bBearer\s+eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
}


def main() -> int:
    completed = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True,
    )
    paths = [Path(item.decode("utf-8")) for item in completed.stdout.split(b"\0") if item]
    failures: list[str] = []
    for relative in paths:
        normalized = relative.as_posix()
        if normalized.startswith("data/local/") and normalized != "data/local/.gitkeep":
            failures.append(f"private-path:{normalized}")
        if relative.suffix.casefold() in FORBIDDEN_SUFFIXES:
            failures.append(f"forbidden-suffix:{normalized}")
        if relative.name in {".env", ".env.local", ".env.production"}:
            failures.append(f"environment-secret:{normalized}")
        absolute = ROOT / relative
        if not absolute.is_file():
            continue
        size = absolute.stat().st_size
        if size > MAX_TRACKED_BYTES:
            failures.append(f"oversize:{normalized}:{size}")
            continue
        payload = absolute.read_bytes()
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(payload):
                failures.append(f"{label}:{normalized}")
    if failures:
        for failure in failures:
            print(failure)
        return 1
    print(f"repo_hygiene=ok tracked_files={len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
