from __future__ import annotations

import hashlib
import io
import json
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError

import pytest

from pokemind.cli import main
from pokemind.database import SCHEMA_VERSION, connect_writable, initialize_schema
from pokemind.scheduler import SchedulerError, scheduler_preview
from pokemind.updates import (
    OfficialSourceClient,
    OfficialNetworkFailure,
    UpdateError,
    UpdateLocked,
    deep_schedule_due,
    run_public_update,
    update_status,
)


class EmptyCatalogClient:
    def __init__(self, max_requests: int = 8) -> None:
        self.max_requests = max_requests
        self.requests_made = 0
        self.calls: list[tuple[str, dict[str, object] | None]] = []

    @property
    def remaining(self) -> int:
        return self.max_requests - self.requests_made

    def get_json(self, path: str, params: dict[str, object] | None = None):
        assert self.remaining > 0
        self.requests_made += 1
        self.calls.append((path, params))
        return [], f"https://api.tcgdex.net/v2{path}"


class EmptyMetaClient:
    def __init__(self, max_requests: int = 2) -> None:
        self.max_requests = max_requests
        self.requests_made = 0
        self.calls: list[tuple[str, dict[str, object] | None]] = []
        self.last_rate_limit = {}
        self.provider_remaining = None

    @property
    def remaining(self) -> int:
        return self.max_requests - self.requests_made

    def get_json(self, path: str, params: dict[str, object] | None = None):
        assert self.remaining > 0
        self.requests_made += 1
        self.calls.append((path, params))
        if path == "/games":
            return [{
                "id": "PTCG", "name": "Pokémon TCG",
                "formats": {"STANDARD": "Standard"},
                "platforms": {"PTCGL": "Pokémon TCG Live"}, "metagame": True,
            }], "https://play.limitlesstcg.com/api/games"
        assert path == "/tournaments"
        return [], "https://play.limitlesstcg.com/api/tournaments"


class FakeOfficialClient:
    def __init__(self, signature: str = "v1", *, fail: bool = False) -> None:
        self.max_requests = 1
        self.requests_made = 0
        self.signature = signature
        self.fail = fail
        self.calls: list[tuple[str, str | None, str | None]] = []

    def probe(self, url: str, *, etag: str | None = None, last_modified: str | None = None):
        self.requests_made += 1
        self.calls.append((url, etag, last_modified))
        if self.fail:
            raise OfficialNetworkFailure("synthetic failure")
        return {
            "source_url": url, "http_status": 200, "content_type": "text/html",
            "content_length": 20, "etag": self.signature, "last_modified": None,
            "content_sha256": hashlib.sha256(self.signature.encode()).hexdigest(),
            "truncated": False, "not_modified": etag == self.signature,
        }


class DebitingFailureClient:
    def __init__(self, max_requests: int = 5, *, fail_after: int = 3) -> None:
        self.max_requests = max_requests
        self.requests_made = 0
        self.fail_after = fail_after
        self.last_rate_limit = {}
        self.provider_remaining = None

    @property
    def remaining(self) -> int:
        return self.max_requests - self.requests_made

    def get_json(self, path: str, params=None):
        self.requests_made += 1
        if self.requests_made >= self.fail_after:
            raise RuntimeError("C:\\Users\\Synthetic Secret token=do-not-leak")
        if path.endswith("/cards"):
            return [{"id": "synthetic-1", "localId": "1", "name": "Synthétique"}], "https://api.tcgdex.net/v2/en/cards"
        if path == "/games":
            return [{"id": "PTCG", "name": "Pokémon TCG", "formats": {"STANDARD": "Standard"}, "platforms": {"PTCGL": "Live"}, "metagame": True}], "https://play.limitlesstcg.com/api/games"
        return [], "https://example.invalid/public"


class _Response(io.BytesIO):
    def __init__(self, body: bytes, *, url: str = "https://www.pokemon.com/us/news/synthetic") -> None:
        super().__init__(body)
        self.status = 200
        self.headers = {"Content-Type": "text/html", "Content-Length": str(len(body)), "ETag": "synthetic"}
        self._url = url

    def geturl(self) -> str:
        return self._url


class _Opener:
    def __init__(self, values: list[object]) -> None:
        self.values = list(values)
        self.calls = 0

    def open(self, request, timeout: float):
        self.calls += 1
        value = self.values.pop(0)
        if isinstance(value, Exception):
            raise value
        return value


def _registry(path: Path) -> Path:
    path.write_text(json.dumps({
        "sources": [{
            "source_id": "synthetic-official",
            "url": "https://www.pokemon.com/us/news/synthetic",
        }]
    }), encoding="utf-8")
    return path


def _run(
    db_path: Path,
    registry: Path,
    official: FakeOfficialClient,
    *,
    now: datetime,
) -> dict:
    return run_public_update(
        db_path, registry, mode="daily", dry_run=False, apply=True, confirm_owner=True,
        now_utc=now,
        budgets={"tcgdex": 8, "pokemon_official": 1, "limitless": 2},
        cards_client=EmptyCatalogClient(8), official_client=official,
        meta_client=EmptyMetaClient(2),
    )


def test_dry_run_has_zero_network_write_or_migration(local_tmp: Path) -> None:
    db_path = local_tmp / "absent.sqlite3"
    result = run_public_update(db_path, local_tmp / "unused.json", mode="daily")
    assert result["status"] == "PLANNED"
    assert result["network_used"] is False and result["writes"] == 0
    assert result["plan"]["dry_run_contract"] == {
        "network_used": False, "writes": 0, "would_migrate": True,
    }
    assert not db_path.exists() and not (local_tmp / "knowledge-update.lock").exists()


def test_official_client_counts_retries_bounds_body_and_rejects_other_hosts() -> None:
    opener = _Opener([URLError("offline"), _Response(b"x" * (512 * 1024 + 1))])
    client = OfficialSourceClient(2, opener=opener, interval=0, sleep=lambda _: None)
    result = client.probe("https://www.pokemon.com/us/news/synthetic")
    assert client.requests_made == 2 and opener.calls == 2
    assert result["truncated"] is True and result["content_sha256"] is not None
    forbidden = OfficialSourceClient(1, opener=_Opener([]), interval=0)
    with pytest.raises(UpdateError, match="pokemon.com"):
        forbidden.probe("https://example.com/private")
    assert forbidden.requests_made == 0


@pytest.mark.parametrize("body", [b"<noscript><title>Pardon Our Interruption</title></noscript>",
    b"<p>Something about your browser made us think you were a bot.</p>"])
def test_official_http200_interstitial_is_closed_and_blocks_the_next_get(body):
    response = _Response(body)
    opener = _Opener([response])
    client = OfficialSourceClient(2,opener=opener,interval=0,stop_on_access_denial=True)
    with pytest.raises(OfficialNetworkFailure,match="CHALLENGE_BLOCKED"):
        client.probe("https://www.pokemon.com/us/news/synthetic")
    assert response.closed and client.requests_made == opener.calls == 1
    with pytest.raises(OfficialNetworkFailure,match="CHALLENGE_BLOCKED"):
        client.probe("https://www.pokemon.com/us/news/another-synthetic")
    assert opener.calls == 1


def test_toronto_schedule_handles_winter_summer_catchup_and_duplicates() -> None:
    winter = deep_schedule_due(
        datetime(2026, 1, 6, 15, tzinfo=timezone.utc), local_time="09:00"
    )
    assert winter["due"] is True and winter["local_now"].endswith("-05:00")
    summer = deep_schedule_due(
        datetime(2026, 7, 7, 13, 30, tzinfo=timezone.utc), local_time="09:00"
    )
    assert summer["due"] is True and summer["local_now"].endswith("-04:00")
    duplicate = deep_schedule_due(
        datetime(2026, 7, 7, 13, 30, tzinfo=timezone.utc), local_time="09:00",
        completed_local_dates=["2026-06-26", "2026-06-30", "2026-07-03", "2026-07-07"],
    )
    assert duplicate["due"] is False
    catchup = deep_schedule_due(
        datetime(2026, 7, 13, 14, tzinfo=timezone.utc), local_time="09:00",
        completed_local_dates=["2026-07-07"],
    )
    assert catchup["due"] is True and catchup["scheduled_local_date"] == "2026-07-10"
    assert catchup["reason"] == "CATCH_UP_AFTER_DOWNTIME"
    unconfigured = deep_schedule_due(datetime(2026, 7, 7, 14, tzinfo=timezone.utc), local_time=None)
    assert unconfigured["reason"] == "SCHEDULE_TIME_NOT_CONFIGURED"


def test_public_cycle_is_idempotent_reports_changes_and_never_promotes_rules(local_tmp: Path) -> None:
    db_path = local_tmp / "updates.sqlite3"
    registry = _registry(local_tmp / "registry.json")
    first_cards, first_meta, first_official = EmptyCatalogClient(8), EmptyMetaClient(2), FakeOfficialClient("v1")
    first = run_public_update(
        db_path, registry, mode="daily", dry_run=False, apply=True, confirm_owner=True,
        now_utc=datetime(2026, 10, 13, 12, tzinfo=timezone.utc),
        budgets={"tcgdex": 8, "pokemon_official": 1, "limitless": 2},
        cards_client=first_cards, official_client=first_official, meta_client=first_meta,
    )
    assert first["status"] == "COMPLETED"
    assert first["report"]["sources"]["pokemon_official"] == {
        "state": "completed", "new": 1, "changed": 0, "missing": 0,
        "unknown": 0, "reason_code": None, "validation_status": "non_verified",
    }
    assert all(call[0].startswith("/en/") or call[0].startswith("/fr/") for call in first_cards.calls)
    assert {call[0] for call in first_meta.calls} == {"/games", "/tournaments"}
    assert first_official.calls[0][0] == "https://www.pokemon.com/us/news/synthetic"

    second = _run(
        db_path, registry, FakeOfficialClient("v2"),
        now=datetime(2026, 10, 14, 12, tzinfo=timezone.utc),
    )
    official = second["report"]["sources"]["pokemon_official"]
    assert official["changed"] == 1 and official["validation_status"] == "conflict"
    assert second["report"]["alerts"][0]["code"] == "OFFICIAL_SOURCE_CHANGED_REQUIRES_VALIDATION"
    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT COUNT(*) FROM official_rule_assertions").fetchone()[0] == 0
    assert connection.execute("SELECT COUNT(*) FROM public_source_observations").fetchone()[0] == 2
    assert connection.execute("SELECT COUNT(*) FROM knowledge_update_cycles").fetchone()[0] == 2
    connection.close()
    log_text = (local_tmp / "update-logs" / "knowledge-2026-10-14.jsonl").read_text(encoding="utf-8")
    assert str(local_tmp.resolve()) not in log_text and "synthetic-official" not in log_text


def test_failed_injected_collectors_report_debited_gets_without_exception_text(local_tmp: Path) -> None:
    db_path = local_tmp / "failed-counts.sqlite3"
    result = run_public_update(
        db_path, _registry(local_tmp / "registry.json"), mode="daily", dry_run=False,
        apply=True, confirm_owner=True, now_utc=datetime(2026, 10, 13, 12, tzinfo=timezone.utc),
        budgets={"tcgdex": 5, "pokemon_official": 1, "limitless": 5},
        cards_client=DebitingFailureClient(), official_client=FakeOfficialClient(),
        meta_client=DebitingFailureClient(fail_after=2),
    )
    assert result["report"]["sources"]["tcgdex"]["reason_code"] == "TCGDEX_COLLECTOR_FAILED"
    assert result["report"]["sources"]["limitless"]["reason_code"] == "LIMITLESS_COLLECTOR_FAILED"
    assert result["report"]["requests_attempted"] == 6
    serialized = json.dumps(result)
    assert "Synthetic Secret" not in serialized and "do-not-leak" not in serialized


def test_failed_internal_collectors_report_effective_client_counts(local_tmp: Path, monkeypatch) -> None:
    created: list[DebitingFailureClient] = []

    def factory(max_requests: int):
        client = DebitingFailureClient(max_requests, fail_after=3 if not created else 2)
        created.append(client)
        return client

    monkeypatch.setattr("pokemind.updates.CatalogApiClient", factory)
    monkeypatch.setattr("pokemind.updates.LimitlessApiClient", factory)
    result = run_public_update(
        local_tmp / "internal-failures.sqlite3", _registry(local_tmp / "registry.json"),
        mode="daily", dry_run=False, apply=True, confirm_owner=True,
        now_utc=datetime(2026, 10, 13, 12, tzinfo=timezone.utc),
        budgets={"tcgdex": 5, "pokemon_official": 1, "limitless": 5},
        official_client=FakeOfficialClient(),
    )
    assert [client.requests_made for client in created] == [3, 2]
    assert result["report"]["requests_attempted"] == 6
    assert result["network_used"] is True


def test_failure_does_not_advance_last_successful_and_offline_status_is_read_only(local_tmp: Path) -> None:
    db_path = local_tmp / "failure.sqlite3"
    registry = _registry(local_tmp / "registry.json")
    _run(db_path, registry, FakeOfficialClient("v1"), now=datetime(2026, 10, 13, 12, tzinfo=timezone.utc))
    before = hashlib.sha256(db_path.read_bytes()).hexdigest()
    first_status = update_status(db_path, now_utc=datetime(2026, 10, 13, 13, tzinfo=timezone.utc))
    after = hashlib.sha256(db_path.read_bytes()).hexdigest()
    assert before == after and first_status["offline"] is True
    last_success = first_status["sources"]["pokemon_official"]["last_successful"]
    failed = _run(db_path, registry, FakeOfficialClient(fail=True), now=datetime(2026, 10, 14, 12, tzinfo=timezone.utc))
    assert failed["status"] == "PARTIAL"
    status = update_status(db_path, now_utc=datetime(2026, 10, 14, 13, tzinfo=timezone.utc))
    assert status["sources"]["pokemon_official"]["last_successful"] == last_success
    assert status["sources"]["pokemon_official"]["consecutive_incomplete"] == 1
    _run(db_path, registry, FakeOfficialClient(fail=True), now=datetime(2026, 10, 15, 12, tzinfo=timezone.utc))
    third = _run(db_path, registry, FakeOfficialClient(fail=True), now=datetime(2026, 10, 16, 12, tzinfo=timezone.utc))
    assert any(alert["code"] == "SOURCE_FAILURE_PROLONGED" for alert in third["report"]["alerts"])


def test_active_lock_refuses_second_process_without_database_write(local_tmp: Path) -> None:
    db_path = local_tmp / "locked.sqlite3"
    registry = _registry(local_tmp / "registry.json")
    lock = local_tmp / "knowledge-update.lock"
    lock.write_text(json.dumps({
        "created_at": "2026-10-13T12:00:00Z", "kind": "pokemind-public-update-lock",
    }), encoding="utf-8")
    with pytest.raises(UpdateLocked, match="UPDATE_ALREADY_RUNNING"):
        _run(db_path, registry, FakeOfficialClient(), now=datetime(2026, 10, 13, 13, tzinfo=timezone.utc))
    assert not db_path.exists()


def test_schema_11_migration_backs_up_and_removes_historical_state_unique(local_tmp: Path) -> None:
    db_path = local_tmp / "schema11.sqlite3"
    connection = sqlite3.connect(db_path)
    connection.executescript(
        """
        CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE training_sessions (
          session_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, closed_at TEXT,
          status TEXT NOT NULL, mode TEXT NOT NULL, format TEXT NOT NULL,
          platform TEXT NOT NULL, context_date TEXT NOT NULL,
          image_storage TEXT NOT NULL, assistance_scope TEXT NOT NULL
        );
        CREATE TABLE training_observations (
          id INTEGER PRIMARY KEY, session_id TEXT NOT NULL, turn_number INTEGER NOT NULL,
          recorded_at TEXT NOT NULL, source_kind TEXT NOT NULL, confidence TEXT NOT NULL,
          state_json TEXT NOT NULL, state_sha256 TEXT NOT NULL, status TEXT NOT NULL,
          revision_of_id INTEGER, UNIQUE(session_id,turn_number,state_sha256)
        );
        PRAGMA user_version=11;
        """
    )
    connection.commit()
    connection.close()
    writable = connect_writable(db_path)
    initialize_schema(writable)
    assert writable.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    assert "knowledge_update_cycles" in {
        row[0] for row in writable.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    table_sql = writable.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='training_observations'"
    ).fetchone()[0]
    assert "UNIQUE(session_id, turn_number, state_sha256)" not in table_sql
    backup = Path(writable.execute("SELECT value FROM metadata WHERE key='last_schema_backup'").fetchone()[0])
    writable.close()
    restored = sqlite3.connect(backup)
    assert restored.execute("PRAGMA user_version").fetchone()[0] == 11
    restored.close()


def test_cli_update_status_and_dry_run_json(local_tmp: Path, capsys: pytest.CaptureFixture[str]) -> None:
    db_path = local_tmp / "cli.sqlite3"
    assert main(["knowledge", "update", "--mode", "daily", "--dry-run", "--db", str(db_path), "--json"]) == 0
    planned = json.loads(capsys.readouterr().out)
    assert planned["status"] == "PLANNED" and planned["network_used"] is False
    assert main(["knowledge", "update", "status", "--db", str(db_path), "--json"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert status["status"] == "NOT_CONFIGURED" and status["offline"] is True


def test_scheduler_manifests_are_dry_run_least_privilege_and_real_changes_refuse(local_tmp: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    preview = scheduler_preview(
        root, action="install", daily_time="08:15", deep_time="19:40", dry_run=True,
        windows_timezone="Eastern Standard Time",
    )
    assert preview["system_changed"] is False and preview["scheduler_contacted"] is False
    assert len(preview["manifests"]) == 2
    assert all(item["run_level"] == "LeastPrivilege" for item in preview["manifests"])
    assert "<Tuesday />" in preview["manifests"][1]["xml"]
    assert "<Friday />" in preview["manifests"][1]["xml"]
    assert "<StartWhenAvailable>true</StartWhenAvailable>" in preview["manifests"][1]["xml"]
    assert "-DeepTime 19:40" in preview["manifests"][1]["arguments"]
    assert all(item["timezone_precondition_asserted"] and not item["timezone_precondition_verified"] for item in preview["manifests"])
    assert all(ET.fromstring(item["xml"]).tag.endswith("Task") for item in preview["manifests"])
    assert "Register-ScheduledTask" not in json.dumps(preview)
    with pytest.raises(SchedulerError, match="confirm-owner"):
        scheduler_preview(
            root, action="install", daily_time="08:15", deep_time="19:40", dry_run=False
            , windows_timezone="Eastern Standard Time"
        )
    with pytest.raises(SchedulerError, match="DISABLED_IN_LOT_D"):
        scheduler_preview(
            root, action="install", daily_time="08:15", deep_time="19:40",
            dry_run=False, confirm_owner=True, windows_timezone="Eastern Standard Time",
        )


def test_scheduler_refuses_non_toronto_windows_timezone_and_missing_times() -> None:
    root = Path(__file__).resolve().parents[1]
    with pytest.raises(SchedulerError, match="NOT_TORONTO"):
        scheduler_preview(
            root, action="install", daily_time="08:15", deep_time="19:40",
            windows_timezone="Pacific Standard Time",
        )
    with pytest.raises(SchedulerError, match="requises"):
        scheduler_preview(root, action="install", windows_timezone="Eastern Standard Time")


def test_cli_scheduler_preview_never_contacts_windows(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([
        "knowledge", "scheduler", "--action", "install", "--daily-time", "08:15",
        "--deep-time", "19:40", "--windows-timezone", "Eastern Standard Time",
        "--dry-run", "--json",
    ]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "DRY_RUN_ONLY"
    assert payload["system_changed"] is False and payload["scheduler_contacted"] is False


def test_launcher_transmits_deep_time_and_deep_cycle_deduplicates(local_tmp: Path) -> None:
    script = (Path(__file__).resolve().parents[1] / "scripts" / "pokemind_update.ps1").read_text(encoding="utf-8-sig")
    assert "@('--deep-time', $DeepTime)" in script
    db_path = local_tmp / "deep-cycle.sqlite3"
    result = run_public_update(
        db_path, _registry(local_tmp / "registry.json"), mode="deep", deep_local_time="09:00",
        dry_run=False, apply=True, confirm_owner=True,
        now_utc=datetime(2026, 7, 7, 13, 30, tzinfo=timezone.utc),
        budgets={"tcgdex": 8, "pokemon_official": 1, "limitless": 2},
        cards_client=EmptyCatalogClient(8), official_client=FakeOfficialClient(),
        meta_client=EmptyMetaClient(2),
    )
    assert result["status"] == "COMPLETED"
    assert result["plan"]["scheduled_local_date"] == "2026-07-07"
    follow_up = run_public_update(
        db_path, local_tmp / "unused.json", mode="auto", deep_local_time="09:00",
        now_utc=datetime(2026, 7, 7, 14, tzinfo=timezone.utc),
    )
    assert follow_up["plan"]["mode"] == "daily"
    assert follow_up["plan"]["schedule"]["due"] is False
