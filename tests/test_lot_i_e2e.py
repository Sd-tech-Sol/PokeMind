import json
import socket
from pathlib import Path

import pytest

from pokemind.demo import run_demo, DemoCatalogClient, _deck
from pokemind.decks import parse_deck_export
from pokemind.public_campaign import run_campaign


ROOT = Path(__file__).resolve().parents[1]


def test_demo_windows_junction_is_rejected_before_any_directory_creation(local_tmp, monkeypatch):
    import pokemind.demo as module
    real = module._redirected
    monkeypatch.setattr(module, "_redirected", lambda p: p.name == "demo-runs" or real(p))
    with pytest.raises(ValueError, match="DEMO_DIRECTORY_UNSAFE"):
        run_demo(local_tmp)
    assert list(local_tmp.iterdir()) == []


def test_first_use_cli_offline_synthetic_and_fresh_session():
    report = run_demo(ROOT)
    assert report["status"] == "SYNTHETIC_REHEARSAL_PASSED"
    assert report["library"]["questions"] == 10
    for citation in report["library"]["citations"]:
        lines = (ROOT / citation["path"]).read_text(encoding="utf-8").splitlines()
        assert 1 <= citation["start_line"] <= citation["end_line"] <= len(lines)
        assert citation["source_date"] == "2026-10-09" and citation["path"].endswith(".md")
    assert report["deck"]["versions"] == 2 and report["deck"]["legality"] == "unknown"
    assert report["deck"]["structure_status"] == "unknown"
    assert report["battles"]["n"] == 5 and report["battles"]["deduplicated"]
    assert report["battles"]["collection"] == report["battles"]["credits"] == "unknown"
    assert report["coach"]["correction_history_preserved"] and report["coach"]["conflicting_context_rejected"]
    assert report["temporary_workspace_removed"] and report["cli_processes"] >= 40
    assert report["release_status"] == "NOT_RELEASE_READY"
    assert not any(report[k] for k in ("network_used", "owner_database_opened", "real_ocr_executed", "scheduler_contacted"))
    assert str(ROOT) not in json.dumps(report)


def test_demo_synthetic_versions_keep_sixty_and_screen_copy_counts():
    for second in (False, True):
        parsed = parse_deck_export(_deck(second))
        assert sum(card.quantity for card in parsed.cards) == 60
        assert all(card.quantity <= 4 for card in parsed.cards)
    with pytest.raises(ValueError):
        parse_deck_export(_deck().replace("4 Twin Name", "3 Twin Name"))


def test_campaign_no_network_by_default_and_resumes_only_public_workspace(local_tmp, monkeypatch):
    import pokemind.public_campaign as module
    def block(*args, **kwargs):
        raise AssertionError("Network prohibited in fixture tests")
    monkeypatch.setattr(socket, "create_connection", block)
    monkeypatch.setattr(socket, "getaddrinfo", block)
    plan = run_campaign(local_tmp, "fixture", create=True)
    assert not plan["network_used"] and list(local_tmp.iterdir()) == []
    def client(budget, **kwargs):
        fixture = DemoCatalogClient(ROOT)
        fixture.max_requests = budget
        return fixture
    monkeypatch.setattr(module, "CatalogApiClient", client)
    first = run_campaign(local_tmp, "fixture", create=True, execute=True,
                         tcgdex_budget=12, meta_budget=0, official_budget=0)
    assert len(first["tcgdex"]["snapshots"]) == 4 and first["tcgdex"]["printing_union"] == 3
    second = run_campaign(local_tmp, "fixture", execute=True, phase="details",
                          tcgdex_budget=12, meta_budget=0, official_budget=0)
    assert second["tcgdex"]["snapshots"]["cards:en"]["details_present_fresh"] == 3
    assert second["maximum_gets_respected"] and not second["owner_database_opened"]
    assert second["normative_assertions_added"] == 0 and second["winrate"] is None
    assert str(local_tmp) not in json.dumps(second)
    with pytest.raises(FileExistsError):
        run_campaign(local_tmp, "fixture", create=True, execute=True)
    with pytest.raises(ValueError, match="UNATTESTED"):
        run_campaign(local_tmp, "missing", execute=True)
    for bad in ("../private", "C:/private", "", "A"):
        with pytest.raises(ValueError):
            run_campaign(local_tmp, bad)
    with pytest.raises(ValueError, match="BUDGET_INVALID"):
        run_campaign(local_tmp, "fixture", tcgdex_budget=25)
