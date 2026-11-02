"""Exercise real synthetic CLI processes with isolated UTC/local clocks."""

import socket
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from pokemind import collection, demo
from pokemind.toronto_tz import toronto_zone


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "utc_time, expected_local_date, expected_offset",
    [
        ("2026-01-16T00:30:00+00:00", "2026-01-15", -5),
        ("2026-01-16T05:01:00+00:00", "2026-01-16", -5),
        ("2026-07-16T00:30:00+00:00", "2026-07-15", -4),
        ("2026-07-16T04:01:00+00:00", "2026-07-16", -4),
    ],
    ids=["winter-utc-tomorrow", "winter-local-midnight", "summer-utc-tomorrow", "summer-local-midnight"],
)
def test_demo_dates_complete_offline_with_real_future_date_guard(
    monkeypatch, utc_time, expected_local_date, expected_offset,
):
    instant = datetime.fromisoformat(utc_time)
    local = instant.astimezone(toronto_zone())
    assert local.date().isoformat() == expected_local_date
    assert local.utcoffset() == timedelta(hours=expected_offset)

    class LocalDate(date):
        @classmethod
        def today(cls):
            return cls.fromisoformat(expected_local_date)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return instant.astimezone(tz) if tz is not None else local.replace(tzinfo=None)

    def block_network(*args, **kwargs):
        raise AssertionError("Network prohibited in synthetic date regression")

    monkeypatch.setattr(demo, "datetime", FrozenDatetime)
    monkeypatch.setattr(demo, "date", LocalDate, raising=False)
    monkeypatch.setattr(collection, "date", LocalDate)
    monkeypatch.setattr(socket, "create_connection", block_network)
    monkeypatch.setattr(socket, "getaddrinfo", block_network)
    assert collection._strict_date(expected_local_date, "as_of") == expected_local_date
    with pytest.raises(ValueError, match="futur"):
        collection._strict_date((local.date() + timedelta(days=1)).isoformat(), "as_of")

    # Freeze the child processes before importing the CLI. No TZ environment,
    # OS clock change, production clock override, or caller-selected database.
    bootstrap = f"""
import socket
from datetime import date
import pokemind.database as database
database.utc_now = lambda: {utc_time!r}
import pokemind.collection as collection
class LocalDate(date):
    @classmethod
    def today(cls):
        return cls.fromisoformat({expected_local_date!r})
collection.date = LocalDate
def block_network(*args, **kwargs):
    raise AssertionError("Network prohibited in synthetic date regression")
socket.create_connection = socket.getaddrinfo = block_network
from pokemind.cli import main
raise SystemExit(main())
"""
    real_run = demo.subprocess.run
    recommendation_dates = []
    databases = set()

    def run_frozen_cli(command, **kwargs):
        assert command[1:3] == ["-m", "pokemind"]
        if "--db" in command:
            database = Path(command[command.index("--db") + 1])
        else:
            assert tuple(command[3:5]) in {("knowledge", "scheduler"), ("knowledge", "cadence")}
            assert len(databases) == 1
            database = next(iter(databases))
        assert database.name == "synthetic.sqlite3"
        assert database.parent.parent == ROOT / "data/local/demo-runs"
        databases.add(database)
        if command[3] == "recommend":
            recommendation_dates.append(command[command.index("--as-of") + 1])
        return real_run([command[0], "-c", bootstrap, *command[3:]], **kwargs)

    monkeypatch.setattr(demo.subprocess, "run", run_frozen_cli)
    report = demo.run_demo(ROOT)
    assert recommendation_dates == [expected_local_date]
    assert report["status"] == "SYNTHETIC_REHEARSAL_PASSED"
    assert report["battles"]["n"] == 5  # UTC-dated imports remain visible to lessons.
    assert report["coach"]["conflicting_context_rejected"]
    assert report["temporary_workspace_removed"] and report["cli_processes"] >= 40
    assert not any(report[key] for key in (
        "network_used", "owner_database_opened", "real_ocr_executed", "scheduler_contacted",
    ))
    assert len(databases) == 1 and not next(iter(databases)).parent.exists()
