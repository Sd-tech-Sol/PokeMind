from __future__ import annotations

import socket
from pathlib import Path

import pytest

from pokemind.database import SCHEMA_VERSION, database_status, import_seed
from pokemind.paths import PathSafetyError, resolve_seed_file
from pokemind.search import search_database


ROOT = Path(__file__).resolve().parents[1]


def test_import_is_idempotent_and_status_is_complete(local_tmp: Path) -> None:
    db_path = local_tmp / "pokemind.sqlite3"
    first = import_seed(ROOT, db_path)
    first_counts = (first["documents_total"], first["sections_total"])
    second = import_seed(ROOT, db_path)

    assert first["documents_inserted"] == 4
    assert first["documents_updated"] == 0
    assert first["sections_written"] == first["sections_total"]
    assert first_counts[0] == 4
    assert first_counts[1] > 40
    assert second["documents_inserted"] == 0
    assert second["documents_updated"] == 0
    assert second["documents_unchanged"] == 4
    assert second["sections_written"] == 0
    assert (second["documents_total"], second["sections_total"]) == first_counts

    status = database_status(db_path)
    assert status["integrity"] == "ok"
    assert status["schema_version"] == SCHEMA_VERSION
    assert status["documents"] == 4
    assert status["sections"] == first_counts[1]
    assert status["search_backend"] == "fts5"
    assert status["external_freshness"] == "jamais synchronisé"
    assert status["scheduler"] == "non installé"


def test_search_returns_precise_citation_and_handles_accents(local_tmp: Path) -> None:
    db_path = local_tmp / "pokemind.sqlite3"
    import_seed(ROOT, db_path)
    results = search_database(db_path, "gestion des recompenses", limit=5)

    assert results
    assert len(results) <= 5
    result = results[0]
    assert result["document"].startswith("VOLUME")
    assert result["path"].startswith("source_material/markdown/")
    assert result["start_line"] >= 1
    assert result["end_line"] >= result["start_line"]
    assert result["source_date"] == "2026-10-09"
    assert len(result["content_sha256"]) == 64
    assert ":L" in result["citation"]
    assert "source 2026-10-09" in result["citation"]


def test_path_traversal_and_unlisted_inputs_are_rejected() -> None:
    markdown_dir = ROOT / "source_material" / "markdown"
    with pytest.raises(PathSafetyError):
        resolve_seed_file(markdown_dir, "../AGENTS.md")
    with pytest.raises(PathSafetyError):
        resolve_seed_file(markdown_dir, "exercices.txt")
    with pytest.raises(PathSafetyError):
        resolve_seed_file(markdown_dir, "C:\\Windows\\win.ini")


def test_source_content_is_data_and_never_executed(local_tmp: Path) -> None:
    fake_root = local_tmp / "fake-root"
    markdown_dir = fake_root / "source_material" / "markdown"
    markdown_dir.mkdir(parents=True)
    marker = local_tmp / "should-not-exist.txt"
    malicious = f"# VOLUME TEST\n\n9 octobre 2026\n\n## Section\n$(Set-Content '{marker}' 'danger')\n"
    for filename in ("01_fondations.md", "02_strategie.md", "03_decks_meta.md", "04_entrainement.md"):
        (markdown_dir / filename).write_text(malicious, encoding="utf-8")

    result = import_seed(fake_root, local_tmp / "malicious.sqlite3")
    assert result["documents_total"] == 4
    assert not marker.exists()


def test_import_and_search_work_with_network_disabled(local_tmp: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*args, **kwargs):
        raise AssertionError("Un accès réseau a été tenté")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    db_path = local_tmp / "offline.sqlite3"
    import_seed(ROOT, db_path)
    assert search_database(db_path, "ordre des actions", limit=3)
