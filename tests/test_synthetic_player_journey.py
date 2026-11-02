"""One invented library -> selected loss -> counter/revision -> public views.

No real PUBLIC or owner cache is an input. Even the older fixture's static deck
file is replaced in memory by DECK below, before importing its helper modules.
"""
from __future__ import annotations

import io
import json
import os
import socket
import sqlite3
from contextlib import closing, redirect_stdout
from pathlib import Path

import pytest

from pokemind import cli, competitive, deck_knowledge, deck_library
from pokemind import public_deck_preflight as public, selected_match_review as review
from test_public_evidence_explain_cli import HtmlView, call as public_cli


AS_OF = "2026-10-23"
DECK = ("Pokémon: 3\n4 Creature Alpha SYN 001\n3 Creature Beta SYN 002\n3 Creature Gamma SYN 003\n\n"
        "Trainer: 4\n4 Invented Scout SYN 100\n4 Research Notes SYN 101\n4 Invented Tool SYN 102\n"
        "4 Invented Switch SYN 103\n\nEnergy: 2\n29 Basic Fire Energy SYN 201\n"
        "5 Basic Psychic Energy SYN 202\n\nTotal Cards: 60\n")


def forbidden(*a, **kw):
    raise AssertionError("JOURNEY_FORBIDDEN_DISCOVERY_OR_EXTERNAL_DATA")


def log_text(*, language="fr", outcome="L"):
    text = "Joueur de référence : InventedSelf\n" if language == "fr" else "Reference player: InventedSelf\n"
    for turn in range(1, 7):
        actor = "InventedSelf" if turn % 2 else "InventedRival"
        card = "Creature Beta" if turn % 2 else "Synthetic Delta"
        if language == "fr":
            text += f"Tour {turn} - Tour de {actor}\n{actor} a pioché une carte.\n{actor} a joué {card}.\n"
        else:
            text += f"Turn # {turn} - {actor}'s Turn\n{actor} drew a card.\n{actor} played {card}.\n"
    if outcome in {"L", "W"}:
        winner = "InventedSelf" if outcome == "W" else "InventedRival"
        text += winner + (" a gagné.\n" if language == "fr" else " wins.\n")
    return text + ("InventedRival a pioché Hidden Creature.\n" if language == "fr" else "InventedRival drew Hidden Creature.\n")


@pytest.fixture
def journey(local_tmp, monkeypatch):
    # Reuse existing invented page/catalog builders, replacing their disk deck
    # input with this lot's literal list. No real/static deck file is opened.
    original_read = Path.read_text
    fixture_deck = Path(__file__).parent / "fixtures/decks/valid_en.txt"
    def read_text(path, *args, **kwargs):
        if path == fixture_deck:
            return DECK
        return original_read(path, *args, **kwargs)
    monkeypatch.setattr(Path, "read_text", read_text)
    from test_deck_knowledge import enriched
    import builtins
    original_open, original_io_open = builtins.open, io.open
    def checked_open(opener, file, *args, **kwargs):
        if not isinstance(file, int):
            path = Path(file).absolute()
            if not path.is_relative_to(local_tmp.absolute()):
                mode = args[0] if args else kwargs.get("mode", "r")
                assert path.suffix in {".py", ".pyc"} and not any(c in mode for c in "wax+"), "FILE_OUTSIDE_FIXTURE"
        return opener(file, *args, **kwargs)
    monkeypatch.setattr(builtins, "open", lambda file, *a, **kw: checked_open(original_open, file, *a, **kw))
    monkeypatch.setattr(io, "open", lambda file, *a, **kw: checked_open(original_io_open, file, *a, **kw))
    for name in ("glob", "rglob", "iterdir"):
        monkeypatch.setattr(Path, name, forbidden)
    for name in ("listdir", "scandir", "walk"):
        monkeypatch.setattr(os, name, forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(competitive.BoundedPages, "__init__", forbidden)
    monkeypatch.setattr(review.battle_logs, "read_clipboard", forbidden)
    monkeypatch.setattr(cli, "default_db_path", forbidden)
    original_connect = sqlite3.connect
    def connect(database, *args, **kwargs):
        value = str(database)
        if value != ":memory:":
            if kwargs.get("uri"):
                assert value.startswith(local_tmp.as_uri() + "/"), "DATABASE_OUTSIDE_FIXTURE"
            else:
                assert Path(value).absolute().is_relative_to(local_tmp.absolute()), "DATABASE_OUTSIDE_FIXTURE"
        return original_connect(database, *args, **kwargs)
    monkeypatch.setattr(sqlite3, "connect", connect)
    public_db, reference_db = enriched(local_tmp)
    db = local_tmp / "data/local/invented-player.sqlite3"
    for selector in ("123:1", "123:4"):
        event, rank = selector.split(":")
        exported = competitive.competitive_export(local_tmp, public_db, event, int(rank))
        assert competitive.parse_deck_export(exported).total_cards == 60
        cli.import_deck(db, exported, deck_id="invented", source_kind="stdin")
    with closing(sqlite3.connect(db)) as con, con:
        con.execute("UPDATE deck_versions SET imported_at='2026-01-01',approved_at='2026-01-01',effective_from='2026-01-01'")
    for module in (review, review.battle_logs, review.attestations):
        monkeypatch.setattr(module, "utc_now", lambda: AS_OF + "T12:00:00Z")
    # Two copies of *invented* databases at the bounded reader's literal paths.
    pair = [local_tmp / name for name in public.SCOPED_PUBLIC_CACHES]
    for source, destination in zip((public_db, reference_db), pair):
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
    log = db.with_name("invented-selected-loss.txt")
    log.write_text(log_text(), encoding="utf-8")
    return dict(root=local_tmp, db=db, public_db=public_db, reference_db=reference_db,
                log=log, pair=pair)


def selected(data, **kwargs):
    options = dict(deck_id="invented", as_of=AS_OF, confirm_owner_read=True,
                   public_db=data["public_db"], reference_db=data["reference_db"], use_set_aliases=True)
    options.update(kwargs)
    options.setdefault("dry_run", not options.get("apply", False))
    return review.review_selected(data["root"], data["db"], **options)


def public_snapshot(data):
    # Literal fixture paths/ledger-referenced pages only, never directory listing.
    paths = [data["public_db"], data["reference_db"], *data["pair"]]
    ledger = data["public_db"].with_name("requests.json")
    paths.extend([ledger, ledger.with_name("PUBLIC_ONLY.json"), data["reference_db"].with_name("PUBLIC_ONLY.json")])
    for entry in json.loads(ledger.read_text(encoding="utf-8"))["requests"]:
        paths.append(ledger.parent / "pages" / (entry["sha256"] + ".body"))
    return {str(path.relative_to(data["root"])): path.read_bytes() for path in paths}


def test_integrated_player_journey(journey, capsys, record_testsuite_property):
    data = journey
    before = public_snapshot(data)
    library = deck_library.library_list(data["root"], data["public_db"], as_of=AS_OF)
    assert (library["matching_placements"], library["matching_compositions"]) == (6, 4)
    guide = deck_knowledge.knowledge_show(data["root"], data["public_db"], data["reference_db"],
                                         selector="123:1", as_of=AS_OF, use_set_aliases=True)
    assert guide["export"]["total_cards"] == competitive.parse_deck_export(guide["export"]["text"]).total_cards == 60
    assert guide["strategic_claim"] and all(c["support"] for c in guide["strategic_claim"])
    assert guide["variant"]["selector"] == "123:1" and guide["uncertainty"]["matchups"] == "unknown"
    deck_knowledge.human_knowledge(guide)
    assert "60/60" in capsys.readouterr().out

    player_before = data["db"].read_bytes()
    preview = selected(data, log_file=data["log"])
    assert data["db"].read_bytes() == player_before
    assert preview["status"] == "PREVIEW" and preview["statistics"]["valid_games"] == 0
    assert preview["source"]["preview_pending_import_excluded_from_statistics"]
    assert preview["opponent"]["outcome"] == "losses"
    imported = selected(data, log_file=data["log"], apply=True, confirm_owner_import=True)
    battle_id = imported["battle_id"]
    resumed = selected(data, log_file=data["log"], apply=True, confirm_owner_import=True)
    assert resumed["battle_id"] == battle_id and resumed["source"]["exact_duplicate"]
    assert resumed["statistics"]["valid_games"] == 1
    assert resumed["opponent"]["player_version"]["version"] is None
    linked = selected(data, battle_id=battle_id, version=1, battle_date="2026-10-10", apply=True, confirm_owner_attest=True)
    assert linked["opponent"]["player_version"]["version"] == 1
    assert linked["opponent"]["player_version"]["asserted_battle_date"] == "2026-10-10"
    opponent = linked["opponent"]
    assert [c["name"] for c in opponent["observed_partial"]["cards"]] == ["Synthetic Delta"]
    assert opponent["observed_partial"]["cards"][0]["minimum_quantity"] == 1
    assert opponent["classification"]["basis"] == "hypothesized"
    assert opponent["exact_confirmed_60"] is None and opponent["public_reference_proxy"]
    assert all(not proxy["is_exact_opponent_deck"] for proxy in opponent["public_reference_proxy"])
    plan = linked["counter_plan"]
    assert plan["target"]["label"] == opponent["classification"]["label"]
    assert len(plan["alternatives"]) == 4 and plan["predicted_winrate"] is None
    for alternative in plan["alternatives"]:
        assert competitive.parse_deck_export(alternative["export"]["text"]).total_cards == 60
        assert alternative["selector"] in {item["selector"] for item in library["library"]}
        diff = alternative["construction_changes"]["counts"]
        assert diff["shared"] + diff["removed"] == 60 and diff["removed"] == diff["added"]
        assert alternative["test_plan"]["causal_effect"] == "unknown"
        assert alternative["switch_cost"]["credits"] == "unknown"
    assert plan["adaptation"]["export"] is None and plan["matchup_advantage"] == "unknown"

    journal = linked["learning_journal"]
    loop = review.loop
    assert loop.validate(journal)
    journal = loop.append_record(journal, record_id="withdraw", kind="withdrawn", recorded_at=AS_OF,
        payload={"reason": "Invented one-loss hypothesis insufficient"}, refs=["selected-hypothesis"], revises="selected-hypothesis")
    journal = loop.append_record(journal, record_id="reopen", kind="hypothesis_to_test", recorded_at=AS_OF,
        payload={"reason": "Invented revised test protocol"}, refs=["withdraw"], revises="withdraw")
    assert "reopen" in {r["id"] for r in loop.view(journal, as_of=AS_OF)["current"]}
    assert loop.append_record(journal, record_id="reopen", kind="hypothesis_to_test", recorded_at=AS_OF,
        payload={"reason": "Invented revised test protocol"}, refs=["withdraw"], revises="withdraw") == journal
    revoked = selected(data, battle_id=battle_id, revoke_version=True, reason="Invented version correction", apply=True, confirm_owner_attest=True)
    assert revoked["opponent"]["player_version"]["version"] is None
    corrected = selected(data, battle_id=battle_id, version=2, battle_date="2026-10-10", apply=True, confirm_owner_attest=True)
    delta = loop.compare_snapshots(loop.statistics_snapshot(linked["statistics"]), loop.statistics_snapshot(corrected["statistics"]))
    assert corrected["opponent"]["player_version"]["version"] == 2
    assert not delta["improvement_demonstrated"] and delta["causal_effect"] == "unknown"
    assert all(g["observed_win_ratio"] is None for g in corrected["statistics"]["groups"])
    review.human_review(corrected)
    assert "Petits n" in capsys.readouterr().out
    assert public_snapshot(data) == before
    record_testsuite_property("synthetic_player_journey_reproduction", json.dumps({
        "scope": "INVENTED_PLAYER_JOURNEY_ONLY", "placements": 6, "compositions": 4,
        "exports60": 4, "selected_games": 1, "separate_consents": 3,
        "exact_opponent_60": False, "hidden_draw_excluded": True, "causal_improvement": False,
        "real_cache_opened": False, "network_used": False}))


@pytest.mark.parametrize("selector", [None, "123:1"])
def test_same_invented_library_public_human_json_html(journey, selector):
    data = journey
    before = public_snapshot(data)
    args = ["meta", "public-identity-explain", "--as-of", AS_OF]
    if selector:
        args += ["--selector", selector]
    reports = [public_cli(data["root"], args + mode, guarded=True) for mode in ([], ["--json"], ["--html"])]
    assert all(r.returncode == 0 and not r.stderr for r in reports)
    human, json_text, html = [r.stdout.decode("utf-8", errors="strict") for r in reports]
    report = json.loads(json_text)
    view = HtmlView(html)
    assert report["totals"]["placements"] == 6 and report["totals"]["compositions"] == 4
    assert len(report["compositions"]) == (1 if selector else 4)
    assert human.count("\nComposition ") == sum(tag == "article" for tag, _ in view.elements) == len(report["compositions"])
    t = report["selected_totals"]
    assert view.tables[0][2] == ["Vue sélectionnée", str(t["placements"]), str(t["compositions"]),
        f'{t["resolved_rows"]}/{t["row_denominator"]}', f'{t["resolved_copies"]}/{t["copy_denominator"]}']
    for output in (human, json_text, html):
        assert "SOURCE_UNREVALIDATED" in output and "BLOCKED_SOURCE_SCOPE" in output and "unknown" in output
        assert str(data["root"]) not in output and "DO_NOT_STORE" not in output
    assert all(c["in_person"] == c["live"] == "unknown" for c in report["compositions"])
    repeated = public_cli(data["root"], args + ["--html"], guarded=True)
    assert repeated.returncode == 0 and repeated.stdout == reports[2].stdout
    assert public_snapshot(data) == before


@pytest.mark.parametrize("language", ["en", "fr"])
@pytest.mark.parametrize("outcome,expected", [("W", "wins"), ("L", "losses"), ("unknown", "unknown")])
def test_outcome_transition_and_small_n_stay_separate(journey, language, outcome, expected):
    data = journey
    data["log"].write_text(log_text(language=language, outcome=outcome), encoding="utf-8")
    result = selected(data, log_file=data["log"], apply=True, confirm_owner_import=True)
    assert result["opponent"]["outcome"] == expected and result["statistics"]["outcomes"][expected] == 1
    assert result["statistics"]["valid_games"] == 1
    assert result["opponent"]["player_version"]["version"] is None
    assert result["opponent"]["exact_confirmed_60"] is None
    assert all(g["observed_win_ratio"] is None for g in result["statistics"]["groups"])


@pytest.mark.parametrize("fault", ["read", "import", "attest", "combined"])
def test_consents_rejected_before_fixture_or_any_other_io(monkeypatch, fault):
    options = dict(deck_id="invented", as_of=AS_OF, log_file=Path("unused.txt"), dry_run=True, confirm_owner_read=True)
    if fault == "read": options["confirm_owner_read"] = False
    if fault == "import": options.update(dry_run=False, apply=True)
    if fault == "attest": options.update(log_file=None, battle_id=1, version=1, dry_run=False, apply=True)
    if fault == "combined": options.update(version=1, dry_run=False, apply=True, confirm_owner_import=True, confirm_owner_attest=True)
    with monkeypatch.context() as guard:
        guard.setattr(Path, "stat", forbidden)
        guard.setattr(Path, "lstat", forbidden)
        guard.setattr(Path, "open", forbidden)
        guard.setattr(review, "connect_readonly", forbidden)
        with pytest.raises(ValueError):
            review.review_selected(Path("unused"), Path("unused.sqlite3"), **options)


@pytest.mark.parametrize("fault", ["missing_native_text", "future_native_text"])
def test_missing_evidence_propagates_from_guide_to_counter(journey, fault):
    data = journey
    with closing(sqlite3.connect(data["reference_db"])) as con, con:
        if fault == "missing_native_text":
            con.execute("DELETE FROM catalog_detail_payloads WHERE kind='cards'")
        else:
            con.execute("UPDATE catalog_translations SET retrieved_at='2099-01-01'")
    result = selected(data, log_file=data["log"])
    assert result["status"] == "PREVIEW" and result["statistics"]["valid_games"] == 0
    assert all(guide["uncertainty"]["missing_card_text"] for guide in result["deck_knowledge"])
    plan = result["counter_plan"]
    assert plan and plan["target"]["missing_evidence"] and not plan["target"]["mechanics"]
    assert all(not alt["mechanics"] and not alt["conditional_questions"] for alt in plan["alternatives"])
    assert plan["predicted_winrate"] is None and plan["matchup_advantage"] == "unknown"


def test_no_public_pair_leaves_opponent_and_counter_unknown(journey):
    data = journey
    before = data["db"].read_bytes()
    result = selected(data, log_file=data["log"], public_db=None, reference_db=None)
    assert result["opponent"]["classification"]["basis"] == "unknown"
    assert result["opponent"]["exact_confirmed_60"] is None
    assert result["counter_plan"] is None and not result["deck_knowledge"]
    assert result["counter_unavailable_reason"] == "EXPLICIT_PUBLIC_CACHES_OR_UNAMBIGUOUS_TARGET_MISSING"
    assert data["db"].read_bytes() == before


@pytest.mark.parametrize("json_mode", [False, True])
def test_selected_cli_contract_uses_same_fixture_engines(journey, monkeypatch, capsys, json_mode):
    data = journey
    monkeypatch.setattr(cli, "find_project_root", lambda: data["root"])
    monkeypatch.setattr(cli, "_db_for", forbidden)
    args = ["battle", "review-selected", "--db", str(data["db"]), "--deck", "invented", "--as-of", AS_OF,
            "--public-db", str(data["public_db"]), "--reference-db", str(data["reference_db"]), "--set-aliases",
            "--log-file", str(data["log"]), "--dry-run"]
    if json_mode:
        args.append("--json")
    before = data["db"].read_bytes()
    assert cli.main(args) == 2
    refused = capsys.readouterr()
    assert str(data["root"]) not in refused.out + refused.err
    assert cli.main(args + ["--confirm-owner-read"]) == 0
    output = capsys.readouterr()
    assert not output.err and str(data["root"]) not in output.out
    if json_mode:
        result = json.loads(output.out)
        assert result["status"] == "PREVIEW" and result["counter_plan"]["predicted_winrate"] is None
        assert result["opponent"]["exact_confirmed_60"] is None
    else:
        assert "60/60" in output.out and "Petits n" in output.out
    assert data["db"].read_bytes() == before
