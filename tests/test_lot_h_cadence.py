from datetime import datetime, timezone
import json

import pytest

from pokemind.scheduler import cadence_preview, scheduler_preview, SchedulerError
from pokemind.updates import deep_schedule_due, UpdateError
from pokemind.cli import main


def test_spring_dst_missing_time_and_tue_fri_deep_argument():
    result = cadence_preview(start_utc=datetime(2026, 3, 7, tzinfo=timezone.utc), daily_time="02:30", deep_time="04:25", days=8)
    daily = [e for e in result["events"] if e["mode"] == "daily"]
    march8 = next(e for e in daily if e["scheduled_local_date"] == "2026-03-08")
    assert march8["dst_shift_minutes"] == 30 and march8["local_deadline"].endswith("03:00:00-04:00")
    deep = [e for e in result["events"] if e["mode"] == "deep"]
    assert [e["scheduled_local_date"] for e in deep] == ["2026-03-10", "2026-03-13"]
    assert all(e["deep_time_argument"] == "04:25" for e in deep)
    assert not result["real_os_dst_verified"]


def test_fall_dst_is_one_daily_event_and_resume_covers_only_latest_deadline():
    result = cadence_preview(start_utc=datetime(2026, 10, 31, tzinfo=timezone.utc), daily_time="01:30", deep_time="05:00", days=5)
    event = [e for e in result["events"] if e["mode"] == "daily" and e["scheduled_local_date"] == "2026-11-01"]
    assert len(event) == 1 and event[0]["fold"] == 0
    assert event[0]["utc_deadline"].endswith("05:30:00+00:00")
    now = datetime(2026, 11, 4, 16, tzinfo=timezone.utc)
    due = deep_schedule_due(now, local_time="05:00")
    assert due["scheduled_local_date"] == "2026-11-03"
    assert not deep_schedule_due(now, local_time="05:00", completed_local_dates=["2026-11-03"])["due"]
    with pytest.raises(UpdateError, match="TIMEZONE_REQUIRED"):
        deep_schedule_due(datetime(2026, 11, 4), local_time="05:00")


def test_scheduler_install_cancel_uninstall_are_simulation_only(local_tmp, capsys):
    for action in ("install", "uninstall", "status"):
        result = scheduler_preview(local_tmp, action=action, daily_time="08:00", deep_time="09:00", windows_timezone="Eastern Standard Time")
        assert not result["scheduler_contacted"] and not result["system_changed"]
        assert result["os_activation_status"] == "OWNER_ACTION_REQUIRED" and not result["active_service_proven"]
    assert list(local_tmp.iterdir()) == []
    with pytest.raises(SchedulerError, match="ACTIVATION_DISABLED"):
        scheduler_preview(local_tmp, action="install", daily_time="08:00", deep_time="09:00", windows_timezone="Eastern Standard Time", dry_run=False, confirm_owner=True)
    assert main(["knowledge", "cadence", "--start-utc", "2026-10-31T00:00:00Z", "--daily-time", "01:30", "--deep-time", "05:00", "--days", "5", "--json"]) == 0
    assert not json.loads(capsys.readouterr().out)["scheduler_contacted"]
