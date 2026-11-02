from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

from pokemind.capabilities import capability_status


ROOT = Path(__file__).resolve().parents[1]
DECK = """Pokémon: 1
4 Alpha SYN 1

Trainer: 1
52 Support SYN 2

Energy: 1
4 Basic Energy SYN 3

Total Cards: 60
"""

BATTLE_AS_OF = "2026-10-13"


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(ROOT / "src")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["POKEMIND_ROOT"] = str(ROOT)
    return environment


def _run(*args: str) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, "-m", "pokemind", *args], cwd=ROOT,
        env=_environment(), text=True, encoding="utf-8", capture_output=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return json.loads(completed.stdout)


def _battle(index: int, winner: str) -> str:
    return (
        "Setup\nReference player: JoueurA\n"
        f"JoueurA played Alpha {index} to the Active Spot.\n"
        "Turn # 1 - JoueurA's Turn\nJoueurA drew Support.\nJoueurA played Support.\n"
        "Turn # 1 - JoueurB's Turn\nJoueurB played Rival.\n"
        f"All Prize cards taken. {winner} wins.\n"
    )


def test_lot_b_cli_end_to_end_on_synthetic_private_files(local_tmp: Path) -> None:
    db_path = local_tmp / "e2e.sqlite3"
    deck_path = local_tmp / "deck.txt"
    deck_path.write_text(DECK, encoding="utf-8")
    imported = _run("deck", "import", str(deck_path), "--deck", "synthetic", "--db", str(db_path), "--json")
    assert imported["exact_confirmed"] is True and imported["total_cards"] == 60

    absent = _run("collection", "status", "--db", str(db_path), "--json")
    assert absent["available"] is False
    collection_path = local_tmp / "collection.json"
    collection_path.write_text(json.dumps({
        "schema_version": 1, "as_of": "2026-10-13", "source": {"kind": "owner_provided"},
        "entries": [
            {"name": "Alpha", "set_code": "SYN", "collector_number": "1", "variant": "normal", "quantity": 4, "ownership_status": "confirmed_owned"},
            {"name": "Support", "set_code": "SYN", "collector_number": "2", "variant": "normal", "quantity": 0, "ownership_status": "reported_missing"},
        ],
    }), encoding="utf-8")
    preview = _run("collection", "import", "--path", str(collection_path), "--dry-run", "--db", str(db_path), "--json")
    assert preview["mode"] == "dry_run"
    applied = _run("collection", "import", "--path", str(collection_path), "--apply", "--confirm-owner", "--db", str(db_path), "--json")
    assert applied["mode"] == "applied"
    missing = _run("collection", "missing", "--deck", "synthetic", "--db", str(db_path), "--json")
    assert missing["known_missing_total"] == 52 and missing["unknown_lines"] == 1
    credits = _run("credits", "set", "--amount", "1200", "--as-of", "2026-10-13", "--apply", "--confirm-owner", "--db", str(db_path), "--json")
    assert credits["credits_spent"] == 0

    empty_lessons = _run("battle", "lessons", "--deck", "synthetic", "--as-of", BATTLE_AS_OF, "--db", str(db_path), "--json")
    assert empty_lessons["sample"]["valid_battles"] == 0
    battles: list[int] = []
    for index in range(5):
        log_path = local_tmp / f"battle-{index}.txt"
        log_path.write_text(_battle(index, "JoueurB" if index == 4 else "JoueurA"), encoding="utf-8")
        result = _run("log", "import", str(log_path), "--deck", "synthetic", "--db", str(db_path), "--json")
        battles.append(int(result["battle_id"]))
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            "UPDATE battle_logs SET imported_at = '2026-10-13T12:00:00Z' WHERE deck_id = 'synthetic'"
        )
        connection.commit()
    finally:
        connection.close()
    lessons = _run("battle", "lessons", "--deck", "synthetic", "--as-of", BATTLE_AS_OF, "--db", str(db_path), "--json")
    assert lessons["sample"]["valid_battles"] == 5
    assert lessons["version_evidence"]["owner_attested"] == 0
    _run(
        "deck", "link-battle", "--deck", "synthetic", "--battle-id", str(battles[0]),
        "--version", "1", "--apply", "--confirm-owner", "--db", str(db_path), "--json",
    )
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            "UPDATE battle_version_attestations SET confirmed_at = '2026-10-13T12:30:00Z'"
        )
        connection.commit()
    finally:
        connection.close()
    linked = _run("battle", "lessons", "--deck", "synthetic", "--as-of", BATTLE_AS_OF, "--db", str(db_path), "--json")
    assert linked["version_evidence"]["owner_attested"] == 1

    advice = _run("recommend", "deck", "synthetic", "--as-of", BATTLE_AS_OF, "--collection", "--db", str(db_path), "--json")
    assert advice["status"] == "INSUFFICIENT_EVIDENCE"
    assert advice["credits"]["craft_cost"] == "unknown"
    assert advice["battle_lessons"]["sample"]["valid_battles"] == 5

    changes_path = local_tmp / "changes.json"
    changes_path.write_text(json.dumps({
        "schema_version": 1, "name": "Synthetic Candidate",
        "base_deck": {"deck_id": "synthetic", "version": 1},
        "context": {"format": "standard", "platform": "live", "as_of": "2026-10-13"},
        "source": {"kind": "owner_controlled_changes"},
        "changes": [
            {"action": "remove", "name": "Support", "set_code": "SYN", "collector_number": "2", "quantity": 1},
            {"action": "add", "type": "trainer", "name": "Alternative", "set_code": "SYN", "collector_number": "9", "quantity": 1},
        ],
    }), encoding="utf-8")
    candidate_preview = _run("deck", "candidate-create", "--changes", str(changes_path), "--dry-run", "--db", str(db_path), "--json")
    assert candidate_preview["status"] == "UNKNOWN_LEGALITY"
    candidate = _run("deck", "candidate-create", "--changes", str(changes_path), "--apply", "--confirm-owner", "--db", str(db_path), "--json")
    candidate_id = int(candidate["candidate_id"])
    export_preview = _run("deck", "candidate-export", "--candidate", str(candidate_id), "--dry-run", "--db", str(db_path), "--json")
    assert not Path(export_preview["text_path"]).exists()
    exported = _run("deck", "candidate-export", "--candidate", str(candidate_id), "--apply", "--confirm-owner", "--db", str(db_path), "--json")
    assert Path(exported["text_path"]).is_file() and exported["transmitted_to_game"] is False

    capacity = _run("capability", "status", "--db", str(db_path), "--json")
    assert capacity["objects"]["collection"]["exists"] is True
    assert capacity["objects"]["credits"]["exists"] is True
    assert "amount" not in capacity["objects"]["credits"]
    assert capacity["objects"]["owner_attested_battles"] == 1
    assert capacity["objects"]["deck_candidates"] == 1
    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT COUNT(*) FROM deck_versions").fetchone()[0] == 1
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    connection.close()


def test_capability_status_on_legacy_database_is_byte_for_byte_read_only(local_tmp: Path) -> None:
    db_path = local_tmp / "legacy.sqlite3"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    connection.execute("PRAGMA user_version=7")
    connection.commit()
    connection.close()
    before = hashlib.sha256(db_path.read_bytes()).hexdigest()
    status = capability_status(db_path)
    after = hashlib.sha256(db_path.read_bytes()).hexdigest()
    assert status["schema_version"] == 7 and status["schema_current"] is False
    assert "MIGRATION_REQUIRED_ON_EXPLICIT_WRITE" in status["gaps"]
    assert before == after


def test_deck_advisor_skill_has_portable_minimal_frontmatter() -> None:
    skill_path = ROOT / ".agents" / "skills" / "deck-advisor" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    frontmatter, body = content[4:].split("\n---\n", 1)
    fields = dict(
        line.split(":", 1) for line in frontmatter.splitlines() if ":" in line
    )
    assert fields["name"].strip() == "deck-advisor"
    assert fields["description"].strip()
    assert set(fields) == {"name", "description"}
    assert "python -m pokemind capability status --json" in body
    assert "--apply --confirm-owner" in body
