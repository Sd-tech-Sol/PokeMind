from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

from pokemind import cli
from pokemind.database import import_seed
from pokemind.knowledge import knowledge_audit, knowledge_status
from pokemind.rules import default_registry_path, load_official_registry


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_knowledge_status_is_offline_read_only_and_actionable(local_tmp: Path) -> None:
    db_path = local_tmp / "knowledge.sqlite3"
    import_seed(ROOT, db_path)
    load_official_registry(db_path, default_registry_path(ROOT))
    before = _sha256(db_path)

    result = knowledge_status(db_path)

    assert _sha256(db_path) == before
    assert result["offline"] is True
    assert result["read_only"] is True
    assert result["network_used"] is False
    assert result["schema_current"] is True
    assert result["cards"]["unique_printings"] == 0
    assert result["rules"]["deck_structure_rule_counts"]["verified"] == 1
    assert result["reprints"] == {
        "verified_assertions": 0, "status": "none_verified", "completeness": "unknown"
    }
    assert result["metagame"]["tournaments"]["complete_snapshots"] == 0
    assert result["actions"] == sorted(
        result["actions"], key=lambda item: (item["priority"], item["code"])
    )
    assert all("estimated_network_gets" in action for action in result["actions"])
    assert any(
        action["estimate_status"] == "unknown_without_provider_total"
        for action in result["actions"]
    )


def test_knowledge_audit_checks_indexes_without_exposing_rows(local_tmp: Path) -> None:
    db_path = local_tmp / "audit.sqlite3"
    import_seed(ROOT, db_path)
    before = _sha256(db_path)

    result = knowledge_audit(db_path)

    assert _sha256(db_path) == before
    assert result["audit"]["status"] == "healthy_with_partial_coverage"
    checks = result["audit"]["checks"]
    assert checks["foreign_key_violations"] == 0
    assert checks["sections_fts"]["status"] == "ok"
    assert checks["catalog_fts"]["status"] == "ok"
    assert result["audit"]["acceptance"]["A5_integrated_audit"]["status"] == "DONE"
    serialized = json.dumps(result, ensure_ascii=False)
    assert "PRIVATE-" not in serialized


def test_knowledge_status_supports_legacy_schema_without_migrating(local_tmp: Path) -> None:
    db_path = local_tmp / "legacy.sqlite3"
    import_seed(ROOT, db_path)
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA user_version = 7")
    connection.commit()
    connection.close()
    before = _sha256(db_path)

    result = knowledge_status(db_path)

    assert _sha256(db_path) == before
    assert result["schema_version"] == 7
    assert result["schema_current"] is False
    assert result["cards"]["state"] == "requires_schema_migration"
    assert result["rules"]["state"] == "requires_schema_migration"
    assert result["actions"][0]["code"] == "MIGRATE_WITH_BACKUP"
    connection = sqlite3.connect(db_path)
    assert connection.execute("PRAGMA user_version").fetchone()[0] == 7
    connection.close()


def test_knowledge_status_does_not_create_an_absent_database(local_tmp: Path) -> None:
    db_path = local_tmp / "absent.sqlite3"

    result = knowledge_status(db_path)

    assert not db_path.exists()
    assert result["schema_version"] == 0
    assert result["cards"]["state"] == "absent"
    assert result["actions"][0]["code"] == "INITIALIZE_LOCAL_DATABASE"


def test_knowledge_cli_json_and_human_outputs(local_tmp: Path, capsys) -> None:
    db_path = local_tmp / "cli.sqlite3"
    import_seed(ROOT, db_path)

    assert cli.main(["knowledge", "status", "--db", str(db_path), "--json"]) == 0
    machine = json.loads(capsys.readouterr().out)
    assert machine["ok"] is True
    assert machine["offline"] is True

    assert cli.main(["knowledge", "audit", "--db", str(db_path)]) == 0
    human = capsys.readouterr().out
    assert "Connaissances hors ligne" in human
    assert "Audit: healthy_with_partial_coverage" in human
