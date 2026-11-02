"""Synthetic one-command journeys; never use owner logs, settings or reports."""
from __future__ import annotations

import json
import os
import socket
import sqlite3
import stat
import subprocess
import sys
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace

import pytest

from pokemind import battle_batch as batch, battle_coach as coach, cli, database, legacy_bridge

AS_OF = "2026-10-25"
PLAYER = "InventedCoachSelf"


def log(winner="InventedCoachRival"):
    return (f"Joueur de référence : {PLAYER}\nTour de {PLAYER}\n"
        f"{PLAYER} a placé Créature Alpha en position Active.\n"
        "Tour de InventedCoachRival\nInventedCoachRival a placé Créature Oméga en position Active.\n"
        "InventedCoachRival a joué Outil Imaginaire.\n" + winner + " a gagné.\n")


def snapshot(root, *, version=4, as_of=AS_OF, note="invented", outcome="losses"):
    match = {"match": "M0001", "outcome": outcome, "opponent": {"label": "Invented Family"},
        "opponent_hypothesis": {}, "own_deck_hypothesis": {"label": "Invented Own"},
        "opponent_cards": [{"name": "Invented Omega"}], "own_cards": [],
        "max_observed_turn": 3, "personal_deck_version": "unknown", "battle_date": "unknown",
        "explicit_prize_totals": {"self": None, "opponent": None}, "exact_opponent_60": False,
        "warnings": [], "evidence": [{"sequence": 1, "turn": 3, "role": "opponent", "type": "use",
            "text": note, "confidence": "low", "target": None}], "causal_loss_reason": "unknown"}
    value = {"model_version": f"battle-batch-v{version}", "as_of": as_of,
        "scope": "OWNER_SELECTED_FOLDER_LOCAL_ONLY", "coverage": {"files_seen": 1, "valid": 1,
        "duplicate": 0, "refused_or_malformed": 0, "unknown_archetype": 0, "signature_only_archetype": 1},
        "outcomes": {key: int(key == outcome) for key in ("wins", "losses", "unknown")},
        "own_decks": {"Invented Own": 1}, "matches": [match], "groups": batch.group_matches([match]),
        "recommendations": [], "published_same_family_variants": [], "public_reference": {},
        "public_refresh": None, "fresh_public_decks": [], "registered_deck_references": [],
        "persistence": {"status": "BLOCKED_SCHEMA_NO_MIGRATION", "schema_version": 7, "can_import": False},
        "release_status": "NOT_RELEASE_READY", "limits": ["unknown"]}
    target = root / coach.REPORT_DIR
    target.mkdir(parents=True, exist_ok=True)
    if version == 4:
        memory = batch.save_memory(root, value, as_of=as_of)
        return root / memory["report"]
    path = target / ("analysis-" + batch.digest(value) + ".json")
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


def controls(root):
    target = root / coach.REPORT_DIR
    return target / "latest.json", target / "coach-settings.json"


def run(root, **kwargs):
    return coach.coach(root, as_of=AS_OF, **kwargs)


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("network forbidden")
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.delenv("POKEMIND_PLAYER_NAME", raising=False)


def test_absent_output_and_logs_create_directories_without_fiction(local_tmp):
    result = run(local_tmp)
    assert result["status"] == "COACH_NO_BATTLE_LOGS" and result["report"] is None
    assert result["writes_performed"] and not result["reanalysis_performed"]
    assert (local_tmp / coach.REPORT_DIR).is_dir() and (local_tmp / coach.LOG_DIR).is_dir()
    assert not (local_tmp / coach.DB).exists()
    assert not controls(local_tmp)[0].exists()


def test_existing_report_no_log_enumeration_analysis_or_db(local_tmp, monkeypatch):
    path = snapshot(local_tmp)
    before = path.read_bytes()
    def forbidden(*args, **kwargs):
        pytest.fail("saved report must not inspect sources or DB")
    monkeypatch.setattr(batch, "batch_analyze", forbidden)
    monkeypatch.setattr(batch, "files_in_folder", forbidden)
    monkeypatch.setattr(sqlite3, "connect", forbidden)
    result = run(local_tmp)
    assert result["source_action"] == "SAVED_REPORT" and not result["database_opened"]
    assert not result["reanalysis_performed"] and result["learning"]
    assert result["learning_status"] == "VALIDATED_EXISTING_LEARNING_LOOP"
    assert result["db_import_status"] == "DB_IMPORT_BLOCKED_SCHEMA_7"
    assert result["report"]["outcomes"]["losses"] == 1 and path.read_bytes() == before
    assert not (local_tmp / coach.LOG_DIR).exists()


def test_v4_preferred_over_v3_same_date_even_if_v3_mtime_is_newer(local_tmp):
    corrected = snapshot(local_tmp, version=4)
    old = snapshot(local_tmp, version=3)
    os.utime(old, ns=(2_000_000_000_000_000_000,) * 2)
    alias = old.parent / "report-2099-01-01-battle-batch-v9.json"
    alias.write_text("do not read this alias", encoding="utf-8")
    before = {p: p.read_bytes() for p in (corrected, old, alias)}
    assert run(local_tmp)["report"]["model_version"] == "battle-batch-v4"
    assert json.loads(controls(local_tmp)[0].read_text())["snapshot"] == corrected.name
    assert before == {p: p.read_bytes() for p in before}


def test_date_then_model_then_mtime_then_name_select_latest(local_tmp):
    snapshot(local_tmp, version=4, as_of="2026-10-24")
    newer = snapshot(local_tmp, version=3)
    assert run(local_tmp)["report"]["model_version"] == "battle-batch-v3"
    second = snapshot(local_tmp, version=3, note="second")
    os.utime(newer, ns=(1_500_000_000_000_000_000,) * 2)
    os.utime(second, ns=(1_600_000_000_000_000_000,) * 2)
    run(local_tmp)
    assert json.loads(controls(local_tmp)[0].read_text())["snapshot"] == second.name
    os.utime(newer, ns=(1_600_000_000_000_000_000,) * 2)
    run(local_tmp)
    assert json.loads(controls(local_tmp)[0].read_text())["snapshot"] == max(newer.name, second.name)


@pytest.mark.parametrize("raw, expected", [(None, "MISSING"), ("{broken", "CORRUPT"),
    ('{"snapshot":"../../outside.json"}', "STALE"), ('{"snapshot":"analysis-missing.json"}', "STALE"),
    ('{"a":1,"a":2}', "CORRUPT"), ("x" * 17000, "CORRUPT")],
    ids=["missing", "corrupt", "traversal", "stale", "duplicate-keys", "oversized"])
def test_index_recovered_only_from_valid_canonical_discovery(local_tmp, raw, expected):
    selected = snapshot(local_tmp)
    index, _ = controls(local_tmp)
    if raw is not None:
        index.write_text(raw, encoding="utf-8")
    result = run(local_tmp)
    assert result["index_status"] == expected and result["index_written"]
    assert json.loads(index.read_text())["snapshot"] == selected.name
    before = index.read_bytes(), index.stat().st_mtime_ns
    assert not run(local_tmp)["index_written"]
    assert (index.read_bytes(), index.stat().st_mtime_ns) == before


def test_index_stale_after_new_corrected_snapshot(local_tmp):
    snapshot(local_tmp, version=3)
    run(local_tmp)
    new = snapshot(local_tmp)
    assert run(local_tmp)["index_status"] == "STALE"
    assert json.loads(controls(local_tmp)[0].read_text())["snapshot"] == new.name


def test_corrupt_canonical_is_refused_and_no_false_report(local_tmp):
    path = snapshot(local_tmp)
    path.write_text(path.read_text(encoding="utf-8") + "broken", encoding="utf-8")
    result = run(local_tmp)
    assert result["status"] == "COACH_NO_BATTLE_LOGS" and not controls(local_tmp)[0].exists()


def test_invalid_learning_does_not_trigger_reanalysis_or_erase_report(local_tmp, monkeypatch):
    path = snapshot(local_tmp)
    journal = path.with_name(path.stem + ".learning.json")
    journal.write_text("broken", encoding="utf-8")
    monkeypatch.setattr(batch, "batch_analyze", lambda *a, **k: pytest.fail("no reanalysis"))
    result = run(local_tmp)
    assert result["status"] == "COACH_LOCAL_REPORT"
    assert result["learning_status"] == "UNAVAILABLE_NOT_MODIFIED" and journal.read_text() == "broken"


def source_tree(root, version=None):
    folder = root / coach.LOG_DIR
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "invented.log").write_text(log(), encoding="utf-8")
    db = root / coach.DB
    if version is not None:
        with closing(sqlite3.connect(db)) as con:
            if version == 13:
                database.initialize_schema(con)
            else:
                con.executescript((Path(__file__).parent / "fixtures/legacy_schema7.sql").read_text(encoding="utf-8"))
            con.commit()
    return folder, db


@pytest.mark.parametrize("version", [None, 7, 13])
def test_integrated_first_analysis_and_update_use_existing_memory_idempotently(local_tmp, version):
    folder, db = source_tree(local_tmp, version)
    before = db.read_bytes() if db.exists() else None
    result = run(local_tmp, player=PLAYER)
    assert result["source_action"] == "LOCAL_BATCH_ANALYSIS" and result["reanalysis_performed"]
    assert result["report"]["coverage"]["valid"] == 1 and result["report"]["outcomes"]["losses"] == 1
    assert not result["network_used"] and result["player_configured"]
    index, settings = controls(local_tmp)
    assert json.loads(settings.read_text())["player"] == PLAYER
    immutable = {p: p.read_bytes() for p in index.parent.glob("analysis-*")}
    second = run(local_tmp)
    assert second["source_action"] == "SAVED_REPORT" and not second["writes_performed"]
    third = run(local_tmp, update=True)
    assert third["memory_status"] == "ALREADY_PRESENT_IDENTICALLY"
    assert immutable == {p: p.read_bytes() for p in immutable}
    assert set(index.parent.glob("analysis-*")) == set(immutable)
    if version == 13:
        with closing(sqlite3.connect(db)) as con:
            assert con.execute("SELECT count(*) FROM battle_logs").fetchone()[0] == 1
            assert con.execute("SELECT count(*) FROM battle_version_attestations").fetchone()[0] == 0
    elif version == 7:
        assert db.read_bytes() == before and result["db_import_status"] == "DB_IMPORT_BLOCKED_SCHEMA_7"
    else:
        assert not db.exists() and not result["database_opened"]
    (folder / "second.txt").write_text(log(PLAYER), encoding="utf-8")
    fourth = run(local_tmp, update=True)
    assert fourth["report"]["coverage"]["valid"] == 2
    assert fourth["report"]["outcomes"] == {"wins": 1, "losses": 1, "unknown": 0}
    assert immutable == {p: p.read_bytes() for p in immutable}


def test_update_invokes_engine_exactly_once_no_public_refresher(local_tmp, monkeypatch):
    from pokemind import batch_public_research
    source_tree(local_tmp)
    calls = []
    original = batch.batch_analyze
    def wrapped(*a, **kw):
        calls.append(kw)
        return original(*a, **kw)
    monkeypatch.setattr(batch, "batch_analyze", wrapped)
    monkeypatch.setattr(batch_public_research, "refresh_public", lambda *a, **k: pytest.fail("no GET"))
    run(local_tmp, player=PLAYER)
    assert len(calls) == 1 and calls[0]["apply"]


def test_update_no_sources_preserves_existing_report(local_tmp):
    snapshot(local_tmp)
    result = run(local_tmp, update=True)
    assert not result["reanalysis_performed"] and result["report"]
    assert result["memory_status"] == "NO_NEW_LOGS_SAVED_REPORT_RETAINED"


def test_player_required_only_for_new_analysis_and_no_import_when_missing(local_tmp, monkeypatch):
    source_tree(local_tmp)
    monkeypatch.setattr(batch, "batch_analyze", lambda *a, **k: pytest.fail("no implicit player"))
    with pytest.raises(coach.CoachError, match="COACH_PLAYER_REQUIRED"):
        run(local_tmp)


@pytest.mark.parametrize("player", ["", " ", "x" * 101, "bad\x1bname"])
def test_invalid_player_never_saved(local_tmp, player):
    with pytest.raises(coach.CoachError, match="COACH_PLAYER_REQUIRED"):
        run(local_tmp, player=player)
    assert not controls(local_tmp)[1].exists()


def test_saved_player_conflict_never_reassigns_or_overwrites(local_tmp):
    snapshot(local_tmp)
    run(local_tmp, player=PLAYER)
    settings = controls(local_tmp)[1]
    before = settings.read_bytes()
    with pytest.raises(coach.CoachError, match="COACH_PLAYER_CONFLICT"):
        run(local_tmp, player="AnotherInventedPlayer")
    assert settings.read_bytes() == before


def test_malformed_logs_have_concrete_non_success_status(local_tmp):
    folder, _ = source_tree(local_tmp)
    (folder / "invented.log").write_text("invented malformed log", encoding="utf-8")
    result = run(local_tmp, player=PLAYER)
    assert result["status"] == "COACH_NO_VALID_MATCHES" and result["report"] is None
    assert not controls(local_tmp)[0].exists()


def test_hostile_saved_content_is_inert(local_tmp):
    snapshot(local_tmp, note='<script>hostile</script>\x1b[31m')
    result = run(local_tmp)
    assert "<script>" not in result["text"] and "\x1b" not in result["text"]
    assert "&lt;script&gt;" in result["text"]


@pytest.mark.parametrize("url", ["https://example.invalid/decks/1", "https://example.invalid/card?q=1&lang=fr"])
def test_public_https_provenance_not_mistaken_for_windows_drive(url):
    displayed = legacy_bridge._display({'source_url': url, 'text': 'Source : ' + url,
        'private': 'C:\\invented\\private.txt'})
    assert displayed['source_url'].startswith('https://example.invalid/')
    assert 'https://example.invalid/' in displayed['text']
    assert 'C:\\invented' not in displayed['private']


@pytest.mark.parametrize("url", ["javascript:invented()", "file:///invented", "https://user:secret@example.invalid/"])
def test_unsafe_source_urls_still_masked(url):
    assert legacy_bridge._display({'source_url': url})['source_url'] == '[source non HTTPS masquée]'


@pytest.mark.parametrize("relative", ["data", "data/local", coach.REPORT_DIR, coach.LOG_DIR])
def test_redirected_directory_refused(local_tmp, relative, monkeypatch):
    outside = local_tmp / "invented-unselected"
    outside.mkdir()
    target = local_tmp / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.symlink_to(outside, target_is_directory=True)
    except OSError:
        # Windows can deny symlink creation. Still exercise its reparse contract
        # without privileges, a junction command or any real redirected folder.
        original = Path.lstat
        def reparse(path, *a, **k):
            if path == target:
                return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=1024)
            return original(path, *a, **k)
        monkeypatch.setattr(Path, "lstat", reparse)
    with pytest.raises(coach.CoachError, match="UNAVAILABLE_OR_UNSAFE"):
        run(local_tmp, update=True)
    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("kind", ["index", "settings", "report"])
def test_hardlinked_files_not_read_or_overwritten(local_tmp, kind):
    path = snapshot(local_tmp)
    index, settings = controls(local_tmp)
    target = path if kind == "report" else index if kind == "index" else settings
    if kind != "report":
        target.write_text("{}", encoding="utf-8")
    linked = local_tmp / "invented-unselected.json"
    os.link(target, linked)
    before = target.read_bytes()
    if kind == "report":
        assert run(local_tmp)["status"] == "COACH_NO_BATTLE_LOGS"
    else:
        with pytest.raises(coach.CoachError):
            run(local_tmp)
    assert target.read_bytes() == linked.read_bytes() == before


def test_discovery_caps_and_no_recursive_alias_open(local_tmp, monkeypatch):
    target = local_tmp / coach.REPORT_DIR
    target.mkdir(parents=True)
    (target / "unselected").mkdir()
    (target / "report-alias.json").write_text("do not read", encoding="utf-8")
    monkeypatch.setattr(coach, "MAX_ENTRIES", 1)
    with pytest.raises(coach.CoachError, match="DISCOVERY_CAP"):
        run(local_tmp)


def test_discovery_byte_budget(local_tmp, monkeypatch):
    snapshot(local_tmp)
    monkeypatch.setattr(coach, "MAX_DISCOVERY_BYTES", 10)
    with pytest.raises(coach.CoachError, match="REPORT_BYTES_CAP"):
        run(local_tmp)


def test_atomic_failure_preserves_old_index_and_all_snapshots(local_tmp, monkeypatch):
    original = snapshot(local_tmp, version=3)
    run(local_tmp)
    snapshot(local_tmp)
    index, _ = controls(local_tmp)
    before = index.read_bytes(), original.read_bytes()
    def fail(*args):
        raise OSError("invented failure with private content")
    monkeypatch.setattr(os, "replace", fail)
    with pytest.raises(coach.CoachError, match="UNAVAILABLE_OR_UNSAFE"):
        run(local_tmp)
    assert (index.read_bytes(), original.read_bytes()) == before


def test_concurrent_index_edit_not_overwritten(local_tmp, monkeypatch):
    snapshot(local_tmp, version=3)
    run(local_tmp)
    snapshot(local_tmp)
    index, _ = controls(local_tmp)
    def concurrent(*args):
        index.write_text('invented concurrent edit', encoding='utf-8')
    monkeypatch.setattr(os, "fsync", concurrent)
    with pytest.raises(coach.CoachError, match="COACH_CONTROL_CHANGED"):
        run(local_tmp)
    assert index.read_text() == 'invented concurrent edit'


def test_engine_memory_failure_retains_old_snapshot_and_index(local_tmp, monkeypatch):
    old = snapshot(local_tmp)
    run(local_tmp)
    source_tree(local_tmp)
    index, _ = controls(local_tmp)
    before = index.read_bytes(), old.read_bytes()
    monkeypatch.setattr(batch, 'save_memory', lambda *a, **k: (_ for _ in ()).throw(ValueError('invented failure')))
    with pytest.raises(coach.CoachError, match="COACH_MEMORY_NOT_SAVED"):
        run(local_tmp, player=PLAYER, update=True)
    assert (index.read_bytes(), old.read_bytes()) == before


@pytest.mark.parametrize("as_of", ["invalid", "2026-1-1"])
def test_invalid_date_neutral(local_tmp, as_of):
    with pytest.raises(coach.CoachError, match="COACH_DATE_INVALID"):
        coach.coach(local_tmp, as_of=as_of)


def test_backdated_update_does_not_regress_index(local_tmp):
    snapshot(local_tmp)
    run(local_tmp)
    before = controls(local_tmp)[0].read_bytes()
    with pytest.raises(coach.CoachError, match="DATE_BEFORE_SAVED_REPORT"):
        coach.coach(local_tmp, update=True, as_of="2026-10-24")
    assert controls(local_tmp)[0].read_bytes() == before


@pytest.mark.parametrize("json_mode", [False, True])
def test_cli_utf8_fixed_paths_and_no_production_or_source_access(local_tmp, json_mode):
    snapshot(local_tmp, note="Évolution → relève inventée")
    program = '''
import sys, os
from pathlib import Path
from pokemind import cli, battle_batch, database
def forbidden(*a, **k): raise AssertionError('UNEXPECTED_OPERATION')
cli.find_project_root = forbidden
battle_batch.batch_analyze = battle_batch.files_in_folder = forbidden
database.initialize_schema = database.connect_writable = forbidden
root = Path.cwd()
project = Path(cli.__file__).parents[2]
def guard(event, args):
 if event.startswith('socket.') or event in {'sqlite3.connect', 'os.remove', 'os.rmdir'}: forbidden()
 if event == 'os.scandir' and Path(args[0]) != root / 'data/local/battle-intelligence': forbidden()
 if event == 'open' and not isinstance(args[0], int):
  path = Path(args[0]).absolute()
  if path.is_relative_to(project / 'data/local') and not path.is_relative_to(root): forbidden()
  if path.is_relative_to(root) and not path.is_relative_to(root / 'data/local/battle-intelligence'): forbidden()
sys.addaudithook(guard)
raise SystemExit(cli.main(sys.argv[1:]))
'''
    env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONDONTWRITEBYTECODE": "1",
        "POKEMIND_ROOT": "invented-unselected", "POKEMIND_BATTLE_LOGS_DIR": "invented-unselected"}
    args = ["battle", "coach", *( ["--json"] if json_mode else [])]
    result = subprocess.run([sys.executable, "-B", "-c", program, *args], cwd=local_tmp,
        env=env, capture_output=True, timeout=30)
    assert result.returncode == 0 and not result.stderr
    output = result.stdout.decode("utf-8")
    assert "Évolution" in output and "→" in output and str(local_tmp) not in output
    if json_mode:
        assert json.loads(output)["ok"]


def test_cli_empty_and_neutral_error_statuses(local_tmp, monkeypatch, capsys):
    # Release the Windows current-directory handle before local_tmp teardown;
    # the autouse network guard also depends on the outer monkeypatch fixture.
    with monkeypatch.context() as scoped:
        scoped.chdir(local_tmp)
        assert cli.main(["battle", "coach", "--json"]) == 1
        assert json.loads(capsys.readouterr().out)["status"] == "COACH_NO_BATTLE_LOGS"
        source_tree(local_tmp)
        assert cli.main(["battle", "coach", "--json"]) == 2
        result = json.loads(capsys.readouterr().out)
        assert result["error_code"] == "COACH_PLAYER_REQUIRED" and str(local_tmp) not in str(result)


def test_cli_integrated_new_logs_update_and_restart_without_player_argument(local_tmp):
    folder, db = source_tree(local_tmp)
    env = {**os.environ, "PYTHONIOENCODING": "cp1252", "PYTHONDONTWRITEBYTECODE": "1",
        "POKEMIND_ROOT": "invented-unselected", "POKEMIND_BATTLE_LOGS_DIR": "invented-unselected"}
    program = '''
import sys
from pokemind import cli, database, batch_public_research
def forbidden(*a, **k): raise AssertionError('UNEXPECTED_OPERATION')
cli.find_project_root = forbidden
database.initialize_schema = database.connect_writable = forbidden
batch_public_research.refresh_public = forbidden
def guard(event, args):
 if event.startswith('socket.') or event in {'os.remove', 'os.rmdir', 'sqlite3.connect'}: forbidden()
sys.addaudithook(guard)
raise SystemExit(cli.main(sys.argv[1:]))
'''
    def invoke(extra):
        result = subprocess.run([sys.executable, '-B', '-c', program, 'battle', 'coach',
            '--json', '--as-of', AS_OF, *extra], cwd=local_tmp, env=env,
            capture_output=True, timeout=30)
        assert result.returncode == 0 and not result.stderr
        return json.loads(result.stdout.decode('utf-8'))
    assert invoke(['--player', PLAYER])['report']['coverage']['valid'] == 1
    (folder / 'new.txt').write_text(log(PLAYER), encoding='utf-8')
    assert invoke(['--update'])['report']['outcomes'] == {'wins': 1, 'losses': 1, 'unknown': 0}
    assert invoke([])['reanalysis_performed'] is False
    assert not db.exists()
