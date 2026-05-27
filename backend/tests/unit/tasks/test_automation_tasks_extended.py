"""Extended tests for automation_tasks — covering uncovered branches."""

from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# _is_astronomical_night
# ---------------------------------------------------------------------------


def test_is_astronomical_night_no_location_returns_false():
    from app.tasks.automation_tasks import _is_astronomical_night

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    assert _is_astronomical_night(db) is False


def test_is_astronomical_night_no_twilight_returns_false():
    from app.tasks.automation_tasks import _is_astronomical_night

    db = MagicMock()
    loc = MagicMock()
    loc.latitude = 40.0
    loc.longitude = -105.0
    loc.elevation = 1500
    loc.timezone = "UTC"
    db.query.return_value.filter.return_value.first.return_value = loc

    with patch("app.tasks.automation_tasks.EphemerisService") as MockEph:
        MockEph.return_value.calculate_twilight_times.return_value = {}
        result = _is_astronomical_night(db)
    assert result is False


def test_is_astronomical_night_currently_night():
    from datetime import datetime, timedelta

    import pytz

    from app.tasks.automation_tasks import _is_astronomical_night

    db = MagicMock()
    loc = MagicMock()
    loc.latitude = 40.0
    loc.longitude = -105.0
    loc.elevation = 0
    loc.timezone = "UTC"
    db.query.return_value.filter.return_value.first.return_value = loc

    tz = pytz.timezone("UTC")
    now = datetime.now(tz=tz)
    dusk = now - timedelta(hours=2)
    dawn = now + timedelta(hours=4)

    with patch("app.tasks.automation_tasks.EphemerisService") as MockEph:
        MockEph.return_value.calculate_twilight_times.return_value = {
            "astronomical_twilight_end": dusk,
            "astronomical_twilight_start": dawn,
        }
        result = _is_astronomical_night(db)
    assert result is True


def test_is_astronomical_night_currently_day():
    from datetime import datetime, timedelta

    import pytz

    from app.tasks.automation_tasks import _is_astronomical_night

    db = MagicMock()
    loc = MagicMock()
    loc.latitude = 40.0
    loc.longitude = -105.0
    loc.elevation = 0
    loc.timezone = "UTC"
    db.query.return_value.filter.return_value.first.return_value = loc

    tz = pytz.timezone("UTC")
    now = datetime.now(tz=tz)
    # dusk is 3 hours in the future — not yet night
    dusk = now + timedelta(hours=3)
    dawn = now + timedelta(hours=9)

    with patch("app.tasks.automation_tasks.EphemerisService") as MockEph:
        MockEph.return_value.calculate_twilight_times.return_value = {
            "astronomical_twilight_end": dusk,
            "astronomical_twilight_start": dawn,
        }
        result = _is_astronomical_night(db)
    assert result is False


# ---------------------------------------------------------------------------
# schedule_dusk_execution_task
# ---------------------------------------------------------------------------


def test_schedule_dusk_disabled_returns_skipped():
    from app.tasks.automation_tasks import schedule_dusk_execution_task

    with patch("app.tasks.automation_tasks.SessionLocal") as mock_sl:
        db = MagicMock()
        s = MagicMock()
        s.value = "false"
        db.query.return_value.filter.return_value.first.return_value = s
        mock_sl.return_value = db
        result = schedule_dusk_execution_task()
    assert result["status"] == "skipped"
    assert result["reason"] == "disabled"


def test_schedule_dusk_no_location_returns_skipped():
    from app.tasks.automation_tasks import schedule_dusk_execution_task

    with patch("app.tasks.automation_tasks.SessionLocal") as mock_sl:
        db = MagicMock()
        enabled = MagicMock()
        enabled.value = "true"
        db.query.return_value.filter.return_value.first.side_effect = [enabled, None]
        mock_sl.return_value = db
        result = schedule_dusk_execution_task()
    assert result["status"] == "skipped"
    assert result["reason"] == "no_location"


def test_schedule_dusk_twilight_unavailable_returns_skipped():
    from app.tasks.automation_tasks import schedule_dusk_execution_task

    with (
        patch("app.tasks.automation_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.automation_tasks.EphemerisService") as MockEph,
    ):
        db = MagicMock()
        enabled = MagicMock()
        enabled.value = "true"
        loc = MagicMock()
        loc.latitude = 40.0
        loc.longitude = -105.0
        loc.elevation = 0
        loc.timezone = "UTC"
        db.query.return_value.filter.return_value.first.side_effect = [enabled, loc]
        mock_sl.return_value = db
        MockEph.return_value.calculate_twilight_times.return_value = {}
        result = schedule_dusk_execution_task()
    assert result["status"] == "skipped"
    assert result["reason"] == "twilight_unavailable"


def test_schedule_dusk_already_passed_returns_skipped():
    from datetime import datetime, timedelta

    import pytz

    from app.tasks.automation_tasks import schedule_dusk_execution_task

    tz = pytz.timezone("UTC")
    dusk = datetime.now(tz=tz) - timedelta(hours=1)  # dusk was 1 hour ago

    with (
        patch("app.tasks.automation_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.automation_tasks.EphemerisService") as MockEph,
    ):
        db = MagicMock()
        enabled = MagicMock()
        enabled.value = "true"
        loc = MagicMock()
        loc.latitude = 40.0
        loc.longitude = -105.0
        loc.elevation = 0
        loc.timezone = "UTC"
        db.query.return_value.filter.return_value.first.side_effect = [enabled, loc]
        mock_sl.return_value = db
        MockEph.return_value.calculate_twilight_times.return_value = {"astronomical_twilight_end": dusk}
        result = schedule_dusk_execution_task()
    assert result["status"] == "skipped"
    assert result["reason"] == "dusk_already_passed"


def test_schedule_dusk_schedules_future_dusk():
    from datetime import datetime, timedelta

    import pytz

    from app.tasks.automation_tasks import schedule_dusk_execution_task

    tz = pytz.timezone("UTC")
    dusk = datetime.now(tz=tz) + timedelta(hours=3)  # dusk 3 hours from now

    with (
        patch("app.tasks.automation_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.automation_tasks.EphemerisService") as MockEph,
        patch("app.tasks.automation_tasks.auto_execute_plan_task") as mock_task,
    ):
        db = MagicMock()
        enabled = MagicMock()
        enabled.value = "true"
        loc = MagicMock()
        loc.latitude = 40.0
        loc.longitude = -105.0
        loc.elevation = 0
        loc.timezone = "UTC"
        db.query.return_value.filter.return_value.first.side_effect = [enabled, loc]
        mock_sl.return_value = db
        MockEph.return_value.calculate_twilight_times.return_value = {"astronomical_twilight_end": dusk}
        mock_task.apply_async = MagicMock()
        result = schedule_dusk_execution_task()
    assert result["status"] == "scheduled"
    mock_task.apply_async.assert_called_once()


# ---------------------------------------------------------------------------
# auto_execute_plan_task — additional branches
# ---------------------------------------------------------------------------


def test_auto_execute_no_targets_returns_skipped():
    from app.tasks.automation_tasks import auto_execute_plan_task

    with patch("app.tasks.automation_tasks.SessionLocal") as mock_sl:
        db = MagicMock()
        enabled = MagicMock()
        enabled.value = "true"
        db.query.return_value.filter.return_value.first.return_value = enabled
        plan = MagicMock()
        plan.name = "empty-plan"
        plan.plan_data = {"scheduled_targets": []}
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = plan
        mock_sl.return_value = db
        result = auto_execute_plan_task()
    assert result["status"] == "skipped"
    assert result["reason"] == "no_targets"


def test_auto_execute_max_retries_sends_webhook():
    from app.tasks.automation_tasks import auto_execute_plan_task

    with (
        patch("app.tasks.automation_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.automation_tasks._check_scope_reachable", return_value=False),
        patch("app.tasks.automation_tasks._send_scope_unreachable_webhook") as mock_wh,
    ):
        db = MagicMock()
        enabled = MagicMock()
        enabled.value = "true"
        host_s = MagicMock()
        host_s.value = "192.168.2.47"
        port_s = MagicMock()
        port_s.value = "4700"
        retry_s = MagicMock()
        retry_s.value = "3"
        plan = MagicMock()
        plan.id = 1
        plan.name = "test-plan"
        plan.plan_data = {"scheduled_targets": [{"target": {"name": "M31"}}]}
        db.query.return_value.filter.return_value.first.side_effect = [
            enabled,
            host_s,
            port_s,
            retry_s,
        ]
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = plan
        mock_sl.return_value = db
        result = auto_execute_plan_task(plan_id=1, retry_count=3)
    assert result["status"] == "failed"
    assert result["reason"] == "scope_unreachable"
    mock_wh.assert_called_once()


def test_auto_execute_loads_plan_by_id():
    from app.tasks.automation_tasks import auto_execute_plan_task

    with (
        patch("app.tasks.automation_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.automation_tasks._check_scope_reachable", return_value=True),
        patch("app.tasks.automation_tasks.execute_observation_plan_task") as mock_exec,
    ):
        db = MagicMock()
        enabled = MagicMock()
        enabled.value = "true"
        host_s = MagicMock()
        host_s.value = "192.168.2.47"
        port_s = MagicMock()
        port_s.value = "4700"
        plan = MagicMock()
        plan.id = 42
        plan.name = "plan-42"
        plan.plan_data = {"scheduled_targets": [{"target": {"name": "M31"}}]}
        db.get.return_value = plan
        db.query.return_value.filter.return_value.first.side_effect = [enabled, host_s, port_s]
        mock_sl.return_value = db
        mock_exec.apply_async = MagicMock()
        result = auto_execute_plan_task(plan_id=42, retry_count=0)
    assert result["status"] == "started"
    assert result["plan_id"] == 42


# ---------------------------------------------------------------------------
# _send_scope_unreachable_webhook
# ---------------------------------------------------------------------------


def test_send_scope_unreachable_webhook_configured():
    from app.tasks.automation_tasks import _send_scope_unreachable_webhook

    db = MagicMock()
    setting = MagicMock()
    setting.value = "http://example.com/hook"
    db.query.return_value.filter.return_value.first.return_value = setting

    with patch("app.tasks.automation_tasks.WebhookService") as MockWH:
        instance = MagicMock()
        instance.is_configured.return_value = True
        MockWH.return_value = instance
        _send_scope_unreachable_webhook(db, plan_name="test-plan")
    instance.send_scope_unreachable_notification.assert_called_once_with(plan_name="test-plan")


def test_send_scope_unreachable_webhook_not_configured():
    from app.tasks.automation_tasks import _send_scope_unreachable_webhook

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.tasks.automation_tasks.WebhookService") as MockWH:
        instance = MagicMock()
        instance.is_configured.return_value = False
        MockWH.return_value = instance
        _send_scope_unreachable_webhook(db, plan_name="test-plan")
    instance.send_scope_unreachable_notification.assert_not_called()


def test_send_scope_unreachable_webhook_exception_does_not_raise():
    from app.tasks.automation_tasks import _send_scope_unreachable_webhook

    db = MagicMock()

    with patch("app.tasks.automation_tasks.WebhookService", side_effect=Exception("boom")):
        # Should not raise
        _send_scope_unreachable_webhook(db, plan_name="test-plan")


# ---------------------------------------------------------------------------
# weather_watchdog — more branches
# ---------------------------------------------------------------------------


def test_weather_watchdog_skips_when_wx_unavailable():
    from app.tasks.automation_tasks import weather_watchdog_task

    with (
        patch("app.tasks.automation_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.automation_tasks._is_astronomical_night", return_value=True),
        patch("app.tasks.automation_tasks.LocalWeatherService") as mock_wx_cls,
    ):
        db = MagicMock()
        execution = MagicMock()
        execution.execution_id = "xyz"
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = execution
        s1 = MagicMock()
        s1.value = "true"
        s2 = MagicMock()
        s2.value = "25.0"
        s3 = MagicMock()
        s3.value = "95"
        db.query.return_value.filter.return_value.first.side_effect = [s1, s2, s3]
        mock_sl.return_value = db
        mock_wx_cls.return_value.get_current.return_value = None
        result = weather_watchdog_task()
    assert result["status"] == "skipped"
    assert result["reason"] == "wx_unavailable"


def test_weather_watchdog_aborts_on_high_wind():
    from app.tasks.automation_tasks import weather_watchdog_task

    with (
        patch("app.tasks.automation_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.automation_tasks._is_astronomical_night", return_value=True),
        patch("app.tasks.automation_tasks.LocalWeatherService") as mock_wx_cls,
        patch("app.tasks.automation_tasks.abort_observation_plan_task") as mock_abort,
        patch("app.tasks.automation_tasks.WebhookService") as mock_wh_cls,
    ):
        db = MagicMock()
        execution = MagicMock()
        execution.execution_id = "wind123"
        execution.targets_completed = 1
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = execution
        s1 = MagicMock()
        s1.value = "true"
        s2 = MagicMock()
        s2.value = "25.0"
        s3 = MagicMock()
        s3.value = "95"
        db.query.return_value.filter.return_value.first.side_effect = [s1, s2, s3]
        mock_sl.return_value = db
        wx = MagicMock()
        wx.is_raining = False
        wx.wind_speed_mph = 35.0
        wx.humidity_pct = 50
        mock_wx_cls.return_value.get_current.return_value = wx
        mock_abort.delay = MagicMock()
        wh = MagicMock()
        wh.is_configured.return_value = False
        mock_wh_cls.return_value = wh
        result = weather_watchdog_task()
    assert result["status"] == "aborted"
    assert "wind" in result["reason"].lower()


def test_weather_watchdog_aborts_on_extreme_humidity():
    from app.tasks.automation_tasks import weather_watchdog_task

    with (
        patch("app.tasks.automation_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.automation_tasks._is_astronomical_night", return_value=True),
        patch("app.tasks.automation_tasks.LocalWeatherService") as mock_wx_cls,
        patch("app.tasks.automation_tasks.abort_observation_plan_task") as mock_abort,
        patch("app.tasks.automation_tasks.WebhookService") as mock_wh_cls,
    ):
        db = MagicMock()
        execution = MagicMock()
        execution.execution_id = "humid123"
        execution.targets_completed = 0
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = execution
        s1 = MagicMock()
        s1.value = "true"
        s2 = MagicMock()
        s2.value = "25.0"
        s3 = MagicMock()
        s3.value = "95"
        db.query.return_value.filter.return_value.first.side_effect = [s1, s2, s3]
        mock_sl.return_value = db
        wx = MagicMock()
        wx.is_raining = False
        wx.wind_speed_mph = 5.0
        wx.humidity_pct = 97
        mock_wx_cls.return_value.get_current.return_value = wx
        mock_abort.delay = MagicMock()
        wh = MagicMock()
        wh.is_configured.return_value = False
        mock_wh_cls.return_value = wh
        result = weather_watchdog_task()
    assert result["status"] == "aborted"
    assert "humidity" in result["reason"].lower()


def test_weather_watchdog_sends_webhook_when_configured():
    from app.tasks.automation_tasks import weather_watchdog_task

    with (
        patch("app.tasks.automation_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.automation_tasks._is_astronomical_night", return_value=True),
        patch("app.tasks.automation_tasks.LocalWeatherService") as mock_wx_cls,
        patch("app.tasks.automation_tasks.abort_observation_plan_task") as mock_abort,
        patch("app.tasks.automation_tasks.WebhookService") as mock_wh_cls,
    ):
        db = MagicMock()
        execution = MagicMock()
        execution.execution_id = "wh-test"
        execution.targets_completed = 3
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = execution
        s1 = MagicMock()
        s1.value = "true"
        s2 = MagicMock()
        s2.value = "25.0"
        s3 = MagicMock()
        s3.value = "95"
        db.query.return_value.filter.return_value.first.side_effect = [s1, s2, s3]
        mock_sl.return_value = db
        wx = MagicMock()
        wx.is_raining = True
        wx.rain_rate_in_hr = 0.5
        wx.wind_speed_mph = 5.0
        wx.humidity_pct = 60
        mock_wx_cls.return_value.get_current.return_value = wx
        mock_abort.delay = MagicMock()
        wh = MagicMock()
        wh.is_configured.return_value = True
        mock_wh_cls.return_value = wh
        result = weather_watchdog_task()
    assert result["status"] == "aborted"
    wh.send_weather_abort_notification.assert_called_once()
