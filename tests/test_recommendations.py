from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

import pokemind.recommendations as recommendations_module
from pokemind.attestations import confirm_battle_version
from pokemind.battle_logs import import_battle_log
from pokemind.database import connect_writable, initialize_schema
from pokemind.decks import import_deck
from pokemind.lessons import battle_lessons, save_battle_note
from pokemind.recommendations import recommend_deck
from pokemind.collection import import_collection, set_credits


DECK = """Pokémon: 1
5 Alpha SYN 1

Trainer: 1
50 Support Card SYN 2

Energy: 1
5 Basic Energy SYN 3

Total Cards: 60
"""

BATTLE_AS_OF = "2026-10-13"


def _battle(number: int, *, winner: str = "JoueurA") -> str:
    return (
        "Setup\nReference player: JoueurA\n"
        f"JoueurA played Alpha {number} to the Active Spot.\n"
        "Turn # 1 - JoueurA's Turn\n"
        "JoueurA drew Support Card.\nJoueurA played Support Card.\n"
        "Turn # 1 - JoueurB's Turn\nJoueurB played Rival Card.\n"
        f"All Prize cards taken. {winner} wins.\n"
    )


def _five_battles(db_path: Path) -> list[int]:
    ids = []
    for index in range(5):
        result = import_battle_log(
            db_path, _battle(index, winner="JoueurB" if index == 4 else "JoueurA"),
            source_kind="stdin", deck_id="synthetic",
        )
        ids.append(result["battle_id"])
    connection = sqlite3.connect(db_path)
    try:
        connection.executemany(
            "UPDATE battle_logs SET imported_at = '2026-10-13T12:00:00Z' WHERE id = ?",
            [(battle_id,) for battle_id in ids],
        )
        connection.commit()
    finally:
        connection.close()
    return ids


def _catalog(db_path: Path) -> None:
    connection = connect_writable(db_path)
    try:
        initialize_schema(connection)
        now = "2026-10-13T00:00:00Z"
        connection.execute(
            "INSERT INTO catalog_sets(tcgdex_id,name_en,tcg_online_code,discovered_at,updated_at) VALUES('syn','Syn','SYN',?,?)",
            (now, now),
        )
        for printing, number, name, attacks in (
            ("syn-1", "1", "Alpha", '[{"name":"Call","effect":"Search for Support Card."}]'),
            ("syn-2", "2", "Support Card", None),
            ("syn-3", "3", "Basic Energy", None),
        ):
            connection.execute(
                """INSERT INTO catalog_printings
                   (tcgdex_id,set_id,local_id,discovered_at,updated_at,brief_source_url,brief_retrieved_at)
                   VALUES(?,'syn',?,?,?,'https://api.tcgdex.net/v2/en/cards',?)""",
                (printing, number, now, now, now),
            )
            connection.execute(
                """INSERT INTO catalog_translations
                   (printing_id,language,status,name,attacks_json,source_url,retrieved_at)
                   VALUES(?,'en','present',?,?,?,?)""",
                (printing, name, attacks, f"https://api.tcgdex.net/v2/en/cards/{printing}", now),
            )
        connection.commit()
    finally:
        connection.close()


def test_lessons_keep_facts_hypotheses_unknowns_and_version_denominators(local_tmp: Path) -> None:
    db_path = local_tmp / "lessons.sqlite3"
    battles = _five_battles(db_path)
    imported = import_deck(db_path, DECK, deck_id="synthetic", source_kind="stdin")
    report = battle_lessons(db_path, "synthetic", as_of=BATTLE_AS_OF)
    assert report["sample"]["valid_battles"] == 5
    assert report["sample"]["wins"] == 4 and report["sample"]["losses"] == 1
    assert report["version_evidence"] == {"owner_attested": 0, "legacy_unattested": 0, "unlinked": 5}
    assert report["observed_facts"] and report["plausible_hypotheses"]
    assert report["demonstrated_errors"] == []
    assert any("causalité" in item.casefold() for item in report["unknowns"])

    confirm_battle_version(
        db_path, "synthetic", battles[0], imported["version"], apply=True, confirm_owner=True
    )
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            "UPDATE battle_version_attestations SET confirmed_at = '2026-10-13T12:30:00Z'"
        )
        connection.commit()
    finally:
        connection.close()
    linked = battle_lessons(db_path, "synthetic", as_of=BATTLE_AS_OF)
    assert linked["version_evidence"]["owner_attested"] == 1
    assert linked["version_evidence"]["unlinked"] == 4


def test_battle_note_preview_is_byte_stable_and_apply_is_idempotent(local_tmp: Path) -> None:
    db_path = local_tmp / "note.sqlite3"
    battle_id = _five_battles(db_path)[0]
    before = hashlib.sha256(db_path.read_bytes()).hexdigest()
    preview = save_battle_note(
        db_path, deck_id="synthetic", battle_id=battle_id,
        text="Le choix visible doit être revu.", confidence="medium",
    )
    assert preview["read_only"] is True
    assert hashlib.sha256(db_path.read_bytes()).hexdigest() == before
    with pytest.raises(ValueError, match="--confirm-owner"):
        save_battle_note(
            db_path, deck_id="synthetic", battle_id=battle_id,
            text="Le choix visible doit être revu.", confidence="medium", apply=True,
        )
    saved = save_battle_note(
        db_path, deck_id="synthetic", battle_id=battle_id,
        text="Le choix visible doit être revu.", confidence="medium",
        public_source_url="https://www.pokemon.com/rules",
        public_source_date="2026-10-13", apply=True, confirm_owner=True,
    )
    duplicate = save_battle_note(
        db_path, deck_id="synthetic", battle_id=battle_id,
        text="Le choix visible doit être revu.", confidence="medium",
        public_source_url="https://www.pokemon.com/rules",
        public_source_date="2026-10-13", apply=True, confirm_owner=True,
    )
    assert saved["duplicate"] is False and duplicate["duplicate"] is True
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("UPDATE battle_lessons SET created_at = '2026-10-13T12:30:00Z'")
        connection.commit()
    finally:
        connection.close()
    report = battle_lessons(db_path, "synthetic", as_of=BATTLE_AS_OF)
    assert report["validated_notes"][0]["provenance"] == "owner_validated"


def test_recommendation_without_catalog_meta_or_collection_refuses_to_invent(local_tmp: Path) -> None:
    db_path = local_tmp / "recommend.sqlite3"
    import_deck(db_path, DECK, deck_id="synthetic", source_kind="stdin")
    report = recommend_deck(
        db_path, "synthetic", as_of="2026-10-13",
        format="standard", platform="live", use_collection=True,
    )
    assert report["status"] == "INSUFFICIENT_EVIDENCE"
    assert report["candidate_changes"] == []
    assert report["ownership"]["status"] == "unknown"
    assert report["credits"]["craft_cost"] == "unknown"
    assert report["matchups"]["status"] == "unknown" and report["matchups"]["n"] == 0
    assert report["network_used"] is False and report["read_only"] is True


def test_explicit_card_text_reference_is_reported_without_claiming_strategy(local_tmp: Path) -> None:
    db_path = local_tmp / "text.sqlite3"
    _catalog(db_path)
    import_deck(db_path, DECK, deck_id="synthetic", source_kind="stdin")
    references = recommendations_module._explicit_text_references(db_path, "synthetic")
    assert len(references) == 1
    assert references[0]["source_printing"] == "syn-1"
    assert references[0]["target_printing"] == "syn-2"
    assert references[0]["status"] == "verified_text_reference_not_strategy_proof"


def test_proven_copy_limit_yields_only_a_verified_removal_and_unknown_replacement(
    local_tmp: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    db_path = local_tmp / "copy-limit.sqlite3"
    import_deck(db_path, DECK, deck_id="synthetic", source_kind="stdin")
    fake_analysis = {
        "facts": {
            "deck": {"exact_confirmed": True, "quantity_sum": 60, "version_ref": "deck-version:1"},
            "rules": {
                "status": "not_legal",
                "structure_validation": {
                    "status": "not_legal",
                    "reason_codes": ["DECK_COPY_LIMIT_EXCEEDED"],
                    "checks": {"over_copy_limit": [{"card_name": "Alpha", "quantity": 5, "limit": 4}]},
                    "sources": [{"url": "https://www.pokemon.com/rules", "date": "2026-10-13"}],
                },
            },
            "metagame": {"n_exploitable_matches": 0},
        },
        "unknowns": [],
        "next_evidence": [],
    }
    monkeypatch.setattr(recommendations_module, "analyze_deck", lambda *args, **kwargs: fake_analysis)
    monkeypatch.setattr(recommendations_module, "battle_lessons", lambda *args, **kwargs: {
        "sample": {"valid_battles": 0}, "version_evidence": {"owner_attested": 0},
        "plausible_hypotheses": [],
    })
    report = recommend_deck(db_path, "synthetic", as_of="2026-10-13")
    change = report["candidate_changes"][0]
    assert report["status"] == "CONDITIONAL_CANDIDATES"
    assert change["remove"]["quantity"] == 1
    assert change["remove"]["status"] == "verified_structural_violation"
    assert change["add"]["status"] == "unknown_replacement"
    assert "meilleur" not in change["reason"].casefold()


def test_recommendation_does_not_use_snapshots_captured_after_as_of(local_tmp: Path) -> None:
    db_path = local_tmp / "historical-recommend.sqlite3"
    _catalog(db_path)
    import_deck(db_path, DECK, deck_id="synthetic", source_kind="stdin")
    source = local_tmp / "collection.json"
    source.write_text(json.dumps({
        "schema_version": 1, "as_of": "2026-10-13", "source": {"kind": "owner_provided"},
        "entries": [{"name": "Alpha", "set_code": "SYN", "collector_number": "1",
                     "variant": "normal", "quantity": 5, "ownership_status": "confirmed_owned"}],
    }), encoding="utf-8")
    import_collection(db_path, source, apply=True, confirm_owner=True)
    set_credits(db_path, 333, as_of="2026-10-13", apply=True, confirm_owner=True)
    report = recommend_deck(db_path, "synthetic", as_of="2026-05-01", use_collection=True)
    assert report["ownership"]["status"] == "unknown"
    assert report["ownership"]["availability_status"] == "NOT_AVAILABLE_AS_OF"
    assert report["ownership"]["missing"] is None
    assert report["credits"]["status"] == "unknown"
    assert report["credits"]["availability_status"] == "NOT_AVAILABLE_AS_OF"
    assert report["credits"]["amount"] is None
