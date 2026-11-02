"""End-to-end selected workflow: invented logs, decks and temporary SQLite ONLY."""
from __future__ import annotations

import json
import os
import socket
import sqlite3
import subprocess
from contextlib import closing
from pathlib import Path

import pytest

from pokemind import attestations, battle_logs, cli, lessons, matchup_analytics as analytics
from pokemind import learning_loop as loop, selected_match_review as review
from test_competitive_advisor import AS_OF, tree_bytes
from test_deck_library_matchups import fictional_log, scenario
from test_public_deck_preflight import forbid_all


EVIDENCE = {
    "scope": "SYNTHETIC_OWNER_SELECTED_MATCH_REVIEW_ONLY", "distinct_consents": 3,
    "exact_exports60": 4, "import_does_not_attest": True, "dry_run_unchanged": True,
    "idempotent_resume": True, "versions_and_revocations": True,
    "hidden_cards_excluded": True, "network_forbidden": True,
    "real_personal_records_opened": False, "no_causal_improvement": True,
}


@pytest.fixture
def invented(local_tmp, monkeypatch):
    db, public, ref, ids = scenario(local_tmp, monkeypatch)
    log = db.with_name("invented-selected.txt")
    text = fictional_log(50, language="fr") + "InventedRival a pioché Hidden Creature.\n"
    log.write_text(text, encoding="utf-8")
    monkeypatch.setattr(battle_logs, "utc_now", lambda: AS_OF + "T12:00:00Z")
    monkeypatch.setattr(review, "utc_now", lambda: AS_OF + "T12:00:00Z")
    monkeypatch.setattr(attestations, "utc_now", lambda: AS_OF + "T12:00:00Z")
    monkeypatch.setattr(lessons, "utc_now", lambda: AS_OF + "T12:00:00Z")
    return local_tmp, db, public, ref, ids, log


def call(data, **kwargs):
    root, db, public, ref, ids, log = data
    options = dict(deck_id="invented", as_of=AS_OF, confirm_owner_read=True,
                   public_db=public, reference_db=ref, use_set_aliases=True)
    options.update(kwargs)
    if not options.get("apply"):
        options.setdefault("dry_run", True)
    return review.review_selected(root, db, **options)


def test_synthetic_demo(invented, monkeypatch, record_testsuite_property, capsys):
    """Reproducible demonstration, with no real-file argument or discovery."""
    root, db, public, ref, ids, log = invented
    before = tree_bytes(root)
    forbid_all(monkeypatch)
    monkeypatch.setattr(battle_logs, "read_clipboard", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    preview = call(invented, log_file=log)
    assert tree_bytes(root) == before
    assert preview["status"] == "PREVIEW" and preview["opponent"]["player_version"]["version"] is None
    assert preview["source"]["preview_pending_import_excluded_from_statistics"]
    assert preview["statistics"]["valid_games"] == 5
    assert [c["name"] for c in preview["opponent"]["observed_partial"]["cards"]] == ["Synthetic Delta"]
    assert preview["opponent"]["classification"]["basis"] == "hypothesized"
    assert preview["opponent"]["exact_confirmed_60"] is None
    assert all(not p["is_exact_opponent_deck"] for p in preview["opponent"]["public_reference_proxy"])
    plan = preview["counter_plan"]
    assert len(plan["alternatives"]) == 4
    for option in plan["alternatives"]:
        assert review.competitive.parse_deck_export(option["export"]["text"]).total_cards == 60
        assert option["switch_cost"]["credits"] == "unknown"
    assert preview["deck_knowledge"] and not plan["predicted_winrate"]
    original = analytics.opponent_for_battle
    with monkeypatch.context() as failure:
        failure.setattr(analytics, "opponent_for_battle", lambda *a, **kw: (_ for _ in ()).throw(
            sqlite3.OperationalError("invented failure after import")))
        partial = call(invented, log_file=log, apply=True, confirm_owner_import=True)
    assert partial["status"] == "PARTIAL_LOCAL_REVIEW_REQUIRED"
    assert partial["completed_steps"] == ["import_committed"] and partial["battle_id"]
    assert analytics.opponent_for_battle is original
    imported = call(invented, log_file=log, apply=True, confirm_owner_import=True)
    battle_id = imported["battle_id"]
    assert battle_id == partial["battle_id"] and imported["source"]["exact_duplicate"]
    assert imported["statistics"]["valid_games"] == 6
    assert imported["opponent"]["player_version"]["version"] is None
    with closing(sqlite3.connect(db)) as con:
        assert con.execute("SELECT count(*) FROM battle_logs").fetchone()[0] == 6
        assert not con.execute("SELECT 1 FROM battle_version_attestations WHERE battle_id=?", (battle_id,)).fetchone()
    linked = call(invented, battle_id=battle_id, version=2, battle_date="2026-10-11", apply=True, confirm_owner_attest=True)
    assert linked["opponent"]["player_version"]["version"] == 2
    assert linked["opponent"]["player_version"]["asserted_battle_date"] == "2026-10-11"
    assert all(g["observed_win_ratio"] is None for g in linked["statistics"]["groups"])
    revoked = call(invented, battle_id=battle_id, revoke_version=True, reason="Invented mistaken version",
                   apply=True, confirm_owner_attest=True)
    assert revoked["opponent"]["player_version"]["version"] is None
    assert call(invented, battle_id=battle_id, revoke_version=True, reason="same correction",
                apply=True, confirm_owner_attest=True)["attestation"]["idempotent"]
    corrected = call(invented, battle_id=battle_id, version=1, battle_date="2026-10-11", apply=True, confirm_owner_attest=True)
    assert corrected["opponent"]["player_version"]["version"] == 1
    with closing(sqlite3.connect(db)) as con:
        history = con.execute("SELECT status,revocation_reason FROM battle_version_attestations WHERE battle_id=? ORDER BY id", (battle_id,)).fetchall()
    assert history == [("revoked", "owner_explicit_revocation"), ("active", None)]
    with closing(sqlite3.connect(db)) as con:
        assert con.execute("SELECT count(*) FROM battle_lessons WHERE note_text LIKE '%Invented mistaken version%'").fetchone()[0] == 1
    output = db.with_name("invented-learning.json")
    saved = call(invented, battle_id=battle_id, learning_out=output, apply=True, confirm_owner_attest=True)
    assert saved["learning_persistence"] == "saved_new_local_file"
    assert loop.validate(json.loads(output.read_text(encoding="utf-8")))
    assert "archetype_hypothesis" not in saved["learning_journal"][0]["payload"]
    assert "archetype_hypothesis" in saved["learning_journal"][2]["payload"]
    assert call(invented, battle_id=battle_id, learning_out=output, apply=True,
                confirm_owner_attest=True)["learning_persistence"] == "already_saved_identically"
    # Check only the two explicit PUBLIC fixture trees: writes target the match DB/output.
    after = tree_bytes(root)
    for key, value in before.items():
        if key != str(db.relative_to(root)):
            assert after[key] == value
    review.human_review(preview)
    human = capsys.readouterr().out
    assert "Copie manuelle" in human and "unknown" in human and "60/60" in human
    record_testsuite_property("owner_selected_match_review_reproduction", json.dumps(EVIDENCE))
    print("DÉMO INVENTÉE : choix d'un journal FR -> aperçu sans écriture -> import sans attestation; "
          "reprise idempotente après échec partiel -> v2 attestée -> retrait motivé -> v1 corrigée; "
          "6 parties, petits n, proxy adverse partiel, 4 exports60, Learning Loop locale. Aucune donnée réelle.")


def forbidden(*args, **kwargs):
    raise AssertionError("Any implicit/private/file/network access is forbidden")


@pytest.mark.parametrize("fault", ["read", "db", "deck", "none", "both", "import", "attest", "combine", "date", "badid", "mode", "extra_import", "public_pair", "backdate"])
def test_authorization_refused_before_any_io(local_tmp, monkeypatch, fault):
    kwargs = dict(deck_id="invented", as_of=AS_OF, log_file=local_tmp / "data/local/no-read.txt",
                  dry_run=True, confirm_owner_read=True)
    db = local_tmp / "data/local/no-read.sqlite3"
    if fault == "read": kwargs["confirm_owner_read"] = False
    if fault == "db": db = None
    if fault == "deck": kwargs["deck_id"] = "bad/id"
    if fault == "none": kwargs["log_file"] = None
    if fault == "both": kwargs["battle_id"] = 1
    if fault == "import": kwargs.update(dry_run=False, apply=True)
    if fault == "attest": kwargs.update(log_file=None, battle_id=1, version=1, dry_run=False, apply=True)
    if fault == "combine": kwargs.update(version=1, apply=True, dry_run=False, confirm_owner_import=True, confirm_owner_attest=True)
    if fault == "date": kwargs["as_of"] = "not-a-date"
    if fault == "badid": kwargs.update(log_file=None, battle_id=0)
    if fault == "mode": kwargs["apply"] = True
    if fault == "extra_import": kwargs["confirm_owner_import"] = True
    if fault == "public_pair": kwargs["public_db"] = local_tmp / "data/local/public.sqlite3"
    if fault == "backdate": kwargs.update(dry_run=False, apply=True, confirm_owner_import=True, as_of="2000-01-01")
    with monkeypatch.context() as guard:
        guard.setattr(Path, "stat", forbidden)
        guard.setattr(Path, "lstat", forbidden)
        guard.setattr(Path, "open", forbidden)
        guard.setattr(review, "connect_readonly", forbidden)
        guard.setattr(analytics, "selected_database", forbidden)
        with pytest.raises(ValueError):
            review.review_selected(local_tmp, db, **kwargs)


@pytest.mark.parametrize("fault", ["outside_db", "outside_log", "outside_output", "dotdot", "ads"])
def test_lexical_paths_refused_before_metadata(local_tmp, monkeypatch, fault):
    db = local_tmp / "data/local/invented.sqlite3"
    log = local_tmp / "data/local/invented.txt"
    kw = dict(log_file=log, deck_id="invented", as_of=AS_OF, dry_run=True, confirm_owner_read=True)
    if fault == "outside_db": db = local_tmp / "outside.sqlite3"
    if fault == "outside_log": kw["log_file"] = local_tmp / "outside.txt"
    if fault == "outside_output": kw.update(log_file=None, battle_id=1, learning_out=local_tmp / "outside.json")
    if fault == "dotdot": kw["log_file"] = local_tmp / "data/local/../redirect.txt"
    if fault == "ads": kw["log_file"] = local_tmp / "data/local/file:stream.txt"
    with monkeypatch.context() as guard:
        guard.setattr(Path, "lstat", forbidden)
        guard.setattr(Path, "stat", forbidden)
        with pytest.raises(ValueError): review.review_selected(local_tmp, db, **kw)


@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
def test_sidecars_no_sqlite_open(invented, monkeypatch, suffix):
    _, db, _, _, ids, _ = invented
    db.with_name(db.name + suffix).write_bytes(b"invented sidecar")
    monkeypatch.setattr(review, "connect_readonly", forbidden)
    with pytest.raises(ValueError, match="SIDECAR"):
        call(invented, battle_id=ids[0])


@pytest.mark.parametrize("which", ["db", "log", "output"])
def test_redirections_and_hardlinks(invented, monkeypatch, which):
    _, db, _, _, ids, log = invented
    target = {"db": db, "log": log, "output": db.with_name("invented.json")}[which]
    target.touch(exist_ok=True)
    alias = target.with_name("hardlink-" + target.name)
    os.link(target, alias)
    kwargs = dict(log_file=log) if which == "log" else dict(battle_id=ids[0])
    if which == "output": kwargs["learning_out"] = target
    with pytest.raises(ValueError): call(invented, **kwargs)


def test_redirected_parent_is_not_resolved(invented, monkeypatch):
    _, db, _, _, _, log = invented
    original = review._redirected
    monkeypatch.setattr(review, "_redirected", lambda p: p == log.parent or original(p))
    monkeypatch.setattr(Path, "resolve", forbidden)
    with pytest.raises(ValueError, match="REDIRECTED"):
        call(invented, log_file=log)


@pytest.mark.parametrize("text", ["", "not a supported log", "\x00\x01", "Reference player: X\nX wins."])
def test_malformed_or_inactive_import_no_writes(invented, text):
    root, db, _, _, _, log = invented
    log.write_text(text, encoding="utf-8")
    before = tree_bytes(root)
    with pytest.raises(ValueError): call(invented, log_file=log, apply=True, confirm_owner_import=True)
    assert tree_bytes(root) == before


def test_log_size_format_multigame_and_source_change(invented, monkeypatch):
    root, db, _, _, _, log = invented
    original = log.read_bytes()
    log.write_bytes(b"x" * (battle_logs.MAX_LOG_BYTES + 1))
    with pytest.raises(ValueError, match="TOO_LARGE"): call(invented, log_file=log)
    wrong = log.with_suffix(".exe")
    wrong.write_bytes(original)
    with pytest.raises(ValueError, match="FORMAT"): call(invented, log_file=wrong)
    log.write_text(fictional_log(90) + fictional_log(91), encoding="utf-8")
    with pytest.raises(ValueError, match="MULTIPLE"): call(invented, log_file=log)
    log.write_bytes(original)
    actual = battle_logs.decode_log_bytes
    def mutate(raw):
        log.write_bytes(original + b"changed while decoding")
        return actual(raw)
    # Changes during byte reading are checked; changes after decoding cannot
    # alter the captured text (import consumes the same in-memory selection).
    monkeypatch.setattr(battle_logs, "decode_log_bytes", mutate)
    result = call(invented, log_file=log)
    assert result["opponent"]["classification"]["label"] == "Hydrapple"


def test_unknown_outcome_ambiguous_target_and_missing_public_caches(invented):
    _, _, _, _, _, log = invented
    log.write_text(fictional_log(77, outcome="unknown", card="Creature Alpha"), encoding="utf-8")
    result = call(invented, log_file=log)
    assert result["opponent"]["outcome"] == "unknown"
    assert result["opponent"]["classification"]["basis"] == "ambiguous"
    assert result["counter_plan"] is None
    result = call(invented, log_file=log, public_db=None, reference_db=None)
    assert result["opponent"]["classification"]["basis"] == "unknown"
    assert result["counter_plan"] is None and not result["deck_knowledge"]


@pytest.mark.parametrize("fault", ["schema", "deck", "battle", "date", "duplicate_deck"])
def test_explicit_conflicts_never_migrate_or_reassign(invented, fault):
    root, db, _, _, ids, log = invented
    kwargs = dict(battle_id=ids[0])
    with closing(sqlite3.connect(db)) as con, con:
        if fault == "schema": con.execute("PRAGMA user_version=7")
        if fault == "deck": kwargs["deck_id"] = "other"
        if fault == "battle": kwargs["battle_id"] = 99999
        if fault == "date": kwargs["as_of"] = "2026-01-01"
        if fault == "duplicate_deck":
            battle_logs.import_battle_log(db, log.read_text(encoding="utf-8"), deck_id="other", source_kind="stdin")
            kwargs = dict(log_file=log, apply=True, confirm_owner_import=True)
    before = tree_bytes(root)
    with pytest.raises(ValueError): call(invented, **kwargs)
    assert tree_bytes(root) == before


def test_dated_revoke_preview_preserves_old_classification_and_versions(invented, monkeypatch):
    root, db, _, _, ids, _ = invented
    before = tree_bytes(root)
    preview = call(invented, battle_id=ids[0], revoke_version=True, reason="invented correction")
    assert preview["attestation"]["eligible"] and tree_bytes(root) == before
    call(invented, battle_id=ids[0], revoke_version=True, reason="invented correction", apply=True, confirm_owner_attest=True)
    current = call(invented, battle_id=ids[0])
    historical = call(invented, battle_id=ids[0], as_of="2026-10-21")
    assert current["opponent"]["player_version"]["version"] is None
    assert historical["opponent"]["player_version"]["version"] == 1
    assert current["opponent"]["archetype_hypothesis"] == historical["opponent"]["archetype_hypothesis"]
    with pytest.raises(ValueError, match="CONFLICT"):
        call(invented, battle_id=ids[1], version=2)


def test_learning_conflict_keeps_existing_file(invented):
    _, db, _, _, ids, _ = invented
    out = db.with_name("existing-invented.json")
    out.write_text("[]", encoding="utf-8")
    result = call(invented, battle_id=ids[0], apply=True, learning_out=out, confirm_owner_attest=True)
    assert result["status"] == "PARTIAL_LOCAL_REVIEW_REQUIRED" and result["learning_write_attempted"]
    assert out.read_text(encoding="utf-8") == "[]"


def test_cli_explicit_selection_human_json_and_redacted_error(invented, monkeypatch, capsys):
    root, db, public, ref, ids, log = invented
    monkeypatch.setattr(cli, "find_project_root", lambda: root)
    forbid_all(monkeypatch)
    args = ["battle", "review-selected", "--db", str(db), "--deck", "invented", "--as-of", AS_OF,
            "--log-file", str(log), "--dry-run"]
    assert cli.main(args + ["--json"]) == 2
    refused = json.loads(capsys.readouterr().out)
    assert refused["status"] == "BLOCKED_WITH_REASON" and str(log) not in json.dumps(refused)
    assert cli.main(args + ["--confirm-owner-read", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "PREVIEW" and result["opponent"]["player_version"]["version"] is None
    assert cli.main(args + ["--confirm-owner-read"]) == 0
    assert "Lecture :" in capsys.readouterr().out
    with pytest.raises(SystemExit): cli.build_parser().parse_args(["battle", "review-selected", "--deck", "invented"])


def test_import_transaction_failure_rolls_back_and_retry_is_unique(invented, monkeypatch):
    _, db, _, _, ids, log = invented
    with closing(sqlite3.connect(db)) as con:
        before = con.execute("SELECT count(*) FROM battle_logs").fetchone()[0]
    with monkeypatch.context() as failure:
        failure.setattr(battle_logs, "_insert_events", lambda *a: (_ for _ in ()).throw(sqlite3.OperationalError("invented write failure")))
        with pytest.raises(sqlite3.OperationalError):
            call(invented, log_file=log, apply=True, confirm_owner_import=True)
    with closing(sqlite3.connect(db)) as con:
        assert con.execute("SELECT count(*) FROM battle_logs").fetchone()[0] == before
    first = call(invented, log_file=log, apply=True, confirm_owner_import=True)
    second = call(invented, log_file=log, apply=True, confirm_owner_import=True)
    assert first["battle_id"] == second["battle_id"] and second["source"]["exact_duplicate"]


def test_probable_duplicates_and_legacy_parser_keep_version_unknown(local_tmp):
    from test_battle_sample import _pair
    from test_deck_library_matchups import DECK
    from pokemind.decks import import_deck
    db = local_tmp / "data/local/invented-duplicates.sqlite3"
    import_deck(db, DECK, deck_id="synthetic", source_kind="stdin")
    first, second = _pair(db)
    result = review.review_selected(local_tmp, db, deck_id="synthetic", battle_id=first,
        as_of="2099-01-01", dry_run=True, confirm_owner_read=True)
    assert result["statistics"]["valid_games"] == 1
    assert result["statistics"]["sample_review"]["probable_duplicates_excluded"] == 1
    assert result["opponent"]["player_version"]["version"] is None
    assert result["learning_journal"][0]["payload"]["parser_version"] == "legacy"
    assert result["statistics"]["groups"][0]["observed_win_ratio"] is None


def test_partial_learning_output_is_retained_and_not_overwritten(invented, monkeypatch):
    _, db, _, _, ids, _ = invented
    out = db.with_name("invented-interrupted-learning.json")
    with monkeypatch.context() as failure:
        failure.setattr(os, "fsync", lambda *a: (_ for _ in ()).throw(OSError("invented interrupted write")))
        result = call(invented, battle_id=ids[0], apply=True, learning_out=out, confirm_owner_attest=True)
    assert result["status"] == "PARTIAL_LOCAL_REVIEW_REQUIRED" and out.is_file()
    retained = out.read_bytes()
    retry = call(invented, battle_id=ids[0], apply=True, learning_out=out, confirm_owner_attest=True)
    assert retry["learning_persistence"] == "already_saved_identically" and out.read_bytes() == retained


def test_played_date_is_not_import_date(invented):
    root, db, public, ref, ids, log = invented
    result = call(invented, battle_id=ids[0])
    stats = result["statistics"]
    first = next(b for b in stats["battles"] if b["battle_id"] == ids[0])
    assert first["imported_at"].startswith("2026-10-20")
    assert first["player_version"]["asserted_battle_date"] == "2026-10-10"
    assert stats["requested_period"]["basis"] == "owner_asserted_battle_date_only"


def test_replaced_open_handle_refused_before_content(invented, monkeypatch):
    from types import SimpleNamespace
    _, _, _, _, _, log = invented
    actual = os.fstat
    def different_file(fd):
        original = actual(fd)
        return SimpleNamespace(st_dev=original.st_dev, st_ino=original.st_ino + 1,
            st_size=original.st_size, st_mtime_ns=original.st_mtime_ns,
            st_nlink=original.st_nlink, st_mode=original.st_mode)
    monkeypatch.setattr(os, "fstat", different_file)
    with pytest.raises(ValueError, match="SOURCE_CHANGED_BEFORE_READ"):
        review._log(invented[0], log)
