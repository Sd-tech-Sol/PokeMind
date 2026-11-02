"""Invented text and PUBLIC fixtures only, including actual Windows streams."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from contextlib import closing

import pytest

from pokemind import deck_knowledge
from test_competitive_advisor import AS_OF, tree_bytes
from test_deck_knowledge import enriched
from test_public_deck_preflight import forbid_all


SPEC = importlib.util.spec_from_file_location("qa_public_decks", Path(__file__).parents[1] / "scripts/qa_public_decks.py")
qa = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(qa)


def observation(*, effect=None, abilities=None, attacks=None):
    return {"fields": {"effect": effect, "abilities": abilities, "attacks": attacks},
            "dated_provenance": {"url": "https://example.invalid/invented", "retrieved_at": AS_OF}}


@pytest.mark.parametrize("limit", ["You can't use more than one such Ability each turn.",
                                  "You can’t use more than one such Ability each turn."])
def test_positive_draw_is_preserved_with_separate_usage_limit(limit):
    source = observation(abilities=[{"name": "Invented restricted engine",
        "effect": "If your opponent took a Prize last turn, draw 3 cards. " + limit}])
    roles = deck_knowledge._roles(source)
    assert {r["role"] for r in roles} == {"draw"}
    assert roles[0]["source"] == source["dated_provenance"]
    assert roles[0]["support_field"] == "abilities" and roles[0]["kind"] == "inference"


@pytest.mark.parametrize("source", [
    observation(effect="Use only if your opponent has fewer Prizes. Attach up to 2 Energy from your discard pile."),
    observation(abilities=[{"effect": "Check your opponent's Prize count."},
                           {"effect": "Discard a card from your hand, then draw a card."}]),
    observation(attacks=[{"name": "Opponent hand discard", "effect": "Draw a card."}]),
])
def test_disruption_cannot_be_assembled_from_unrelated_effects_or_names(source):
    roles = {r["role"] for r in deck_knowledge._roles(source)}
    assert "disruption" not in roles


@pytest.mark.parametrize("text", ["You can't draw cards.", "You can’t draw cards.",
                                  "You cannot draw cards."])
def test_prohibited_draw_never_becomes_a_resource_engine(text):
    assert "draw" not in {r["role"] for r in deck_knowledge._roles(observation(effect=text))}


def test_real_disruption_and_separate_available_search_remain_supported():
    source = observation(effect="Your opponent can't draw cards. Search your deck for a card.")
    roles = {r["role"] for r in deck_knowledge._roles(source)}
    assert roles == {"disruption", "search"}


def test_full_offline_field_qa_on_invented_caches(local_tmp, monkeypatch):
    db, reference = enriched(local_tmp)
    before = tree_bytes(local_tmp)
    forbid_all(monkeypatch)
    # The QA runner must not discover cache siblings or open a writable DB.
    monkeypatch.setattr(Path, "rglob", lambda *a, **kw: pytest.fail("no recursive discovery"))
    monkeypatch.setattr(Path, "iterdir", lambda *a, **kw: pytest.fail("no directory discovery"))
    report = qa.assess(local_tmp, db, reference, as_of=AS_OF)
    assert report["placements"] == report["exports60"] == 6
    assert report["compositions"] == report["families"] == 4
    assert len(report["counter_plans"]) == 4
    assert all(p["exports60"] == 4 and p["matchup_advantage"] == "unknown" for p in report["counter_plans"])
    assert not any(p["target_is_exact_opponent_deck"] for p in report["counter_plans"])
    assert report["text_rows"] == report["row_denominator"]
    assert all(row["reparsed_cards"] == 60 and row["list_url"] and row["fetched_at"] for row in report["lists"])
    assert report["live"] == {"unknown": 4}
    assert report["cache_bytes_and_metadata_unchanged"] and report["provider_gets"] == 0
    assert not report["owner_database_opened"]
    # Restore only test monkeypatches before checking exact fixture bytes.
    monkeypatch.undo()
    assert tree_bytes(local_tmp) == before
    assert "DO_NOT_STORE" not in json.dumps(report)


def test_missing_explicit_cache_has_no_download_or_discovery(local_tmp, monkeypatch):
    db, reference = enriched(local_tmp)
    reference.unlink()  # disposable synthetic fixture only
    forbid_all(monkeypatch)
    monkeypatch.setattr(Path, "iterdir", lambda *a: pytest.fail("no cache discovery"))
    with pytest.raises(ValueError, match="PUBLIC_QA_SOURCE_UNSAFE"):
        qa.assess(local_tmp, db, reference, as_of=AS_OF)


def test_source_mutation_during_qa_is_not_reported_unchanged(local_tmp, monkeypatch):
    db, reference = enriched(local_tmp)
    original = qa.deck_library.library_list
    def change_source(*a, **kw):
        result = original(*a, **kw)
        marker = db.parent / "PUBLIC_ONLY.json"
        marker.write_text(marker.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        return result
    monkeypatch.setattr(qa.deck_library, "library_list", change_source)
    with pytest.raises(ValueError, match="PUBLIC_QA_CACHE_MUTATED_STOP"):
        qa.assess(local_tmp, db, reference, as_of=AS_OF)


@pytest.mark.parametrize("mode", ["human", "json", "export"])
def test_cli_with_cp1252_startup_and_unicode_sources(local_tmp, mode):
    db, reference = enriched(local_tmp)
    # Card text source has a Unicode-only character, without changing identity.
    from test_deck_knowledge import _canonical_sha256
    import sqlite3
    with closing(sqlite3.connect(reference)) as connection, connection:
        row = connection.execute("SELECT entity_id,payload_json FROM catalog_detail_payloads WHERE kind='cards' AND entity_id='syn-001'").fetchone()
        payload = json.loads(row[1])
        payload["effect"] = "Search your deck for a card. Invented symbol: →."
        digest = _canonical_sha256(payload)
        connection.execute("UPDATE catalog_detail_payloads SET payload_json=?,payload_sha256=? WHERE kind='cards' AND entity_id=?",
                           (json.dumps(payload), digest, row[0]))
        connection.execute("UPDATE catalog_translations SET payload_sha256=?,effect=? WHERE printing_id=?",
                           (digest, payload["effect"], row[0]))
    before = tree_bytes(local_tmp)
    child = """
import sys
from pathlib import Path
from pokemind import cli
root = Path(sys.argv.pop(1))
allowed = {str(p) for p in [root / 'data/local/public-campaigns/lot-i-advisor-synthetic/public.sqlite3', root / 'data/local/public-campaigns/lot-i-preflight-reference/public.sqlite3']}
allowed = {Path(p).as_uri() + '?mode=ro' for p in allowed}
def guard(event, args):
    if event.startswith('socket.') or event in {'subprocess.Popen', 'os.system'}:
        raise RuntimeError('synthetic CLI network/client forbidden')
    if event == 'sqlite3.connect' and str(args[0]) not in allowed:
        raise RuntimeError('synthetic CLI exact read-only databases only')
sys.addaudithook(guard)
cli.find_project_root = lambda: root
raise SystemExit(cli.main(sys.argv[1:]))
"""
    args = ["meta", "deck-knowledge", "--db", str(db), "--reference-db", str(reference),
            "--selector", "123:1", "--as-of", AS_OF, "--set-aliases"]
    if mode == "json":
        args.append("--json")
    elif mode == "export":
        args = ["meta", "competitive-export", "--db", str(db), "--event", "123", "--placement", "1"]
    result = subprocess.run([sys.executable, "-B", "-c", child, str(local_tmp), *args],
        env={**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, timeout=60)
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    output = result.stdout.decode("utf-8", errors="strict")
    if mode == "json":
        report = json.loads(output)
        assert report["ok"] and report["export"]["total_cards"] == 60
    elif mode == "human":
        assert "→" in output and "60/60" in output and "unknown" in output
    else:
        from pokemind.decks import parse_deck_export
        assert parse_deck_export(output).total_cards == 60
    assert tree_bytes(local_tmp) == before
