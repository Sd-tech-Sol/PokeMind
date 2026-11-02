from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from pokemind import cli, deck_exports
from pokemind.deck_exports import (
    copy_ready_file,
    copy_text_to_clipboard,
    export_confirmed_deck,
    load_proposal,
    prepare_proposal,
    serialize_deck,
)
from pokemind.decks import import_deck, parse_deck_export


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "decks" / "valid_fr.txt"
EN_FIXTURE = ROOT / "tests" / "fixtures" / "decks" / "valid_en.txt"


def _proposal(*, total_delta: int = 0, missing_printing: bool = False) -> dict[str, object]:
    parsed = parse_deck_export(FIXTURE.read_text(encoding="utf-8"))
    cards: list[dict[str, object]] = []
    for index, card in enumerate(parsed.cards):
        item: dict[str, object] = {
            "type": card.card_type,
            "quantity": card.quantity + (total_delta if index == 0 else 0),
            "name": card.name,
            "set_code": card.set_code,
            "collector_number": card.collector_number,
            "provenance": "fixture synthétique PM-0003E",
            "verification_tags": ["printing_verified"],
        }
        if missing_printing and index == 0:
            item.pop("set_code")
            item.pop("collector_number")
            item["verification_tags"] = ["printing_unresolved"]
        cards.append(item)
    return {
        "schema_version": 1,
        "name": "Candidat Éclair",
        "source": {"kind": "agent_proposal", "reference": "test synthétique"},
        "verification_tags": ["human_review_pending"],
        "cards": cards,
    }


def _write_proposal(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_serialize_round_trip_is_stable_and_uses_entry_headers() -> None:
    original = parse_deck_export(FIXTURE.read_text(encoding="utf-8"))
    serialized = serialize_deck(original.cards)
    reparsed = parse_deck_export(serialized)

    assert serialized.startswith("Pokémon: 3\n")
    assert "Trainer: 10\n" in serialized
    assert "Energy: 2\n" in serialized
    assert reparsed.total_cards == 60
    assert reparsed.coverage["section_header_count_mode"] == "entries"
    assert serialize_deck(reparsed.cards) == serialized
    assert [(card.name, card.set_code, card.collector_number, card.quantity) for card in reparsed.cards] == [
        (card.name, card.set_code, card.collector_number, card.quantity) for card in original.cards
    ]


def test_serialize_preserves_two_printings_of_same_name() -> None:
    original = parse_deck_export(EN_FIXTURE.read_text(encoding="utf-8"))
    reparsed = parse_deck_export(serialize_deck(original.cards))
    printings = {
        (card.set_code, card.collector_number, card.quantity)
        for card in reparsed.cards
        if card.name == "Creature Beta"
    }
    assert printings == {("SYN", "002", 3), ("OLD", "099", 2)}


@pytest.mark.parametrize("delta", [-1, 1])
def test_proposal_rejects_59_or_61_cards(local_tmp: Path, delta: int) -> None:
    proposal = local_tmp / f"invalid-{delta}.json"
    _write_proposal(proposal, _proposal(total_delta=delta))
    with pytest.raises(ValueError, match="exactement 60"):
        load_proposal(proposal)


def test_prepare_proposal_writes_only_import_text_and_local_report(local_tmp: Path) -> None:
    proposal = local_tmp / "proposal.json"
    _write_proposal(proposal, _proposal())
    prepared = prepare_proposal(proposal, local_tmp / "private-decks")

    assert prepared.report["status"] == "READY_TO_TRY_UNVERIFIED_FORMAT"
    assert prepared.report["format_validation"] == "OUTPUT_FORMAT_NOT_FIELD_VALIDATED"
    assert prepared.text_path.parent.name == "import_ready"
    assert prepared.text_path.read_text(encoding="utf-8") == prepared.text
    assert "fixture synthétique" not in prepared.text
    assert "status" not in prepared.text
    assert parse_deck_export(prepared.text).total_cards == 60
    report = json.loads(prepared.report_path.read_text(encoding="utf-8"))
    assert report["printing_codes"]["entries_resolved"] == report["printing_codes"]["entries_total"]
    assert all(card["possession"] == "unknown" for card in report["cards"])
    assert all(card["availability"] == "not_verified" for card in report["cards"])


def test_unresolved_printing_is_kept_out_of_import_ready(local_tmp: Path) -> None:
    proposal = local_tmp / "draft.json"
    _write_proposal(proposal, _proposal(missing_printing=True))
    prepared = prepare_proposal(proposal, local_tmp / "private-decks")

    assert prepared.report["status"] == "DRAFT_PRINTINGS_UNRESOLVED"
    assert prepared.text_path.parent.name == "drafts"
    assert prepared.report["printing_codes"]["unresolved_entry_ordinals"] == [1]


def test_unverified_printing_tag_is_kept_out_of_import_ready(local_tmp: Path) -> None:
    proposal = local_tmp / "unverified.json"
    payload = _proposal()
    payload["cards"][0]["verification_tags"] = ["human_review_pending"]
    _write_proposal(proposal, payload)
    prepared = prepare_proposal(proposal, local_tmp / "private-decks")

    assert prepared.report["status"] == "DRAFT_PRINTINGS_UNRESOLVED"
    assert prepared.report["printing_codes"]["unresolved_entry_ordinals"] == [1]


def test_confirmed_database_export_is_versioned_and_never_overwritten(local_tmp: Path) -> None:
    db_path = local_tmp / "deck.sqlite3"
    import_deck(
        db_path,
        FIXTURE.read_text(encoding="utf-8"),
        deck_id="principal",
        source_kind="stdin",
    )
    private_root = local_tmp / "private-decks"
    prepared = export_confirmed_deck(db_path, "principal", private_root)
    assert prepared.text_path.name == "principal_v1.txt"
    assert prepared.report["source"]["kind"] == "confirmed_deck_version"

    with pytest.raises(FileExistsError, match="aucun fichier écrasé"):
        export_confirmed_deck(db_path, "principal", private_root)
    assert prepared.text_path.read_text(encoding="utf-8") == prepared.text


def test_failed_report_write_removes_partial_text(
    local_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proposal = local_tmp / "proposal.json"
    _write_proposal(proposal, _proposal())
    private_root = local_tmp / "private-decks"
    real_write = deck_exports._atomic_write_new

    def fail_report(path: Path, data: bytes) -> None:
        if path.suffix == ".json":
            raise OSError("simulated report failure")
        real_write(path, data)

    monkeypatch.setattr(deck_exports, "_atomic_write_new", fail_report)
    with pytest.raises(OSError, match="simulated"):
        prepare_proposal(proposal, private_root)
    assert not list(private_root.rglob("*.txt"))
    assert not list(private_root.rglob("*.json"))


def test_export_refuses_observed_only_deck(local_tmp: Path) -> None:
    db_path = local_tmp / "observed.sqlite3"
    connection = sqlite3.connect(db_path)
    connection.execute(
        "CREATE TABLE observed_decks(deck_id TEXT PRIMARY KEY, status TEXT, created_at TEXT, last_seen_at TEXT)"
    )
    connection.execute(
        "INSERT INTO observed_decks VALUES ('principal', 'observé partiellement', 'x', 'x')"
    )
    connection.execute("PRAGMA user_version = 0")
    connection.commit()
    connection.close()
    with pytest.raises(ValueError, match="aucune version exacte"):
        export_confirmed_deck(db_path, "principal", local_tmp / "private-decks")


def test_clipboard_writer_passes_text_only_on_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> SimpleNamespace:
        captured["command"] = command
        captured.update(kwargs)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(deck_exports.sys, "platform", "win32")
    monkeypatch.setattr(deck_exports.subprocess, "run", fake_run)
    text = "Pokémon: 1\n60 Créature SYN 001\n"
    copy_text_to_clipboard(text)

    assert captured["input"] == text
    assert text not in " ".join(captured["command"])
    assert captured["timeout"] == 10


def test_copy_rejects_path_outside_private_import_ready(local_tmp: Path) -> None:
    outside = local_tmp / "outside.txt"
    outside.write_text("not a deck", encoding="utf-8")
    with pytest.raises(ValueError, match="import_ready"):
        copy_ready_file(outside, local_tmp / "private-decks")


def test_copy_ready_file_validates_then_copies_exact_text(
    local_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    proposal = local_tmp / "proposal.json"
    _write_proposal(proposal, _proposal())
    private_root = local_tmp / "private-decks"
    prepared = prepare_proposal(proposal, private_root)
    copied: list[str] = []
    monkeypatch.setattr(deck_exports, "copy_text_to_clipboard", copied.append)

    result = copy_ready_file(prepared.text_path, private_root)

    assert result["copied"] is True
    assert copied == [prepared.text]


def test_proposal_schema_rejects_unknown_fields(local_tmp: Path) -> None:
    proposal = local_tmp / "unknown.json"
    payload = _proposal()
    payload["invented_collection"] = True
    _write_proposal(proposal, payload)
    with pytest.raises(ValueError, match="champs inconnus"):
        load_proposal(proposal)


def test_cli_prepare_changes_clipboard_only_with_copy(
    local_tmp: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = local_tmp / "fake-project"
    proposal = root / "data" / "local" / "proposals" / "candidate.json"
    _write_proposal(proposal, _proposal())
    copied: list[str] = []
    monkeypatch.setattr(cli, "find_project_root", lambda: root)
    monkeypatch.setattr(cli, "copy_text_to_clipboard", copied.append)

    assert cli.main(["deck", "prepare", "--proposal", str(proposal), "--json"]) == 0
    assert copied == []

    second_payload = _proposal()
    second_payload["name"] = "Candidat Copié"
    second = proposal.with_name("candidate-copy.json")
    _write_proposal(second, second_payload)
    assert cli.main(["deck", "prepare", "--proposal", str(second), "--copy", "--json"]) == 0
    assert len(copied) == 1
    assert parse_deck_export(copied[0]).total_cards == 60
