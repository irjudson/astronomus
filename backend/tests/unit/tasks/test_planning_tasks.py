"""Unit tests for planning_tasks.generate_daily_plan_task."""

from unittest.mock import MagicMock, patch


def _make_db_with_settings(settings_map: dict, db_location=None, saved_plan_first=None):
    """Build a mock DB whose query().filter().first() chain serves settings by key."""
    db = MagicMock()

    def _filter_first(*args, **kwargs):
        mock = MagicMock()
        mock.first.return_value = None
        return mock

    # We'll use side_effect on query to intercept by model
    from app.models.settings_models import AppSetting, ObservingLocation
    from app.models.plan_models import SavedPlan

    def _query(model):
        q = MagicMock()
        if model is AppSetting:
            def _filter(condition):
                f = MagicMock()
                # Extract key from condition — use a counter instead
                f.first.side_effect = lambda: None
                return f
            q.filter = _filter
        elif model is ObservingLocation:
            q.filter.return_value.first.return_value = db_location
        elif model is SavedPlan:
            q.filter.return_value.first.return_value = saved_plan_first
        return q

    return db


def test_returns_skipped_when_disabled():
    from app.tasks.planning_tasks import generate_daily_plan_task

    with patch("app.tasks.planning_tasks.SessionLocal") as mock_sl:
        db = MagicMock()
        disabled = MagicMock()
        disabled.value = "false"
        db.query.return_value.filter.return_value.first.return_value = disabled
        mock_sl.return_value = db
        result = generate_daily_plan_task()

    assert result["status"] == "skipped"
    assert result["reason"] == "disabled_in_settings"


def test_uses_db_location_when_present():
    from app.tasks.planning_tasks import generate_daily_plan_task

    db_loc = MagicMock()
    db_loc.latitude = 46.0
    db_loc.longitude = -112.0
    db_loc.elevation = 1200
    db_loc.timezone = "America/Denver"
    db_loc.name = "TestObservatory"

    mock_plan = MagicMock()
    mock_plan.scheduled_targets = []
    mock_plan.session.imaging_start.isoformat.return_value = "2026-05-26T22:00:00"
    mock_plan.session.imaging_end.isoformat.return_value = "2026-05-27T04:00:00"

    mock_saved = MagicMock()
    mock_saved.id = 42

    with (
        patch("app.tasks.planning_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.planning_tasks.PlannerService") as mock_ps,
        patch("app.tasks.planning_tasks.WebhookService") as mock_ws,
    ):
        db = MagicMock()
        enabled = MagicMock()
        enabled.value = "true"
        count_s = MagicMock()
        count_s.value = "5"
        min_alt_s = MagicMock()
        min_alt_s.value = "30.0"
        moon_s = MagicMock()
        moon_s.value = "50"
        avoid_s = MagicMock()
        avoid_s.value = "true"
        webhook_s = MagicMock()
        webhook_s.value = ""

        db.query.return_value.filter.return_value.first.side_effect = [
            enabled, count_s, db_loc, None, min_alt_s, moon_s, avoid_s, webhook_s,
        ]
        mock_sl.return_value = db

        mock_ps.return_value.generate_plan.return_value = mock_plan

        ws_inst = MagicMock()
        ws_inst.is_configured.return_value = False
        mock_ws.return_value = ws_inst

        db.refresh.side_effect = lambda obj: setattr(obj, "id", 42)

        result = generate_daily_plan_task()

    assert result["status"] == "success"
    # PlannerService was instantiated with the db
    mock_ps.assert_called_once_with(db)


def test_falls_back_to_env_vars_when_no_db_location():
    from app.tasks.planning_tasks import generate_daily_plan_task

    mock_plan = MagicMock()
    mock_plan.scheduled_targets = []
    mock_plan.session.imaging_start.isoformat.return_value = "2026-05-26T22:00:00"
    mock_plan.session.imaging_end.isoformat.return_value = "2026-05-27T04:00:00"

    with (
        patch("app.tasks.planning_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.planning_tasks.PlannerService") as mock_ps,
        patch("app.tasks.planning_tasks.WebhookService") as mock_ws,
        patch("app.tasks.planning_tasks.os.getenv") as mock_getenv,
    ):
        db = MagicMock()
        enabled = MagicMock()
        enabled.value = "true"
        count_s = MagicMock()
        count_s.value = "5"
        min_alt_s = MagicMock()
        min_alt_s.value = "30.0"
        moon_s = MagicMock()
        moon_s.value = "50"
        avoid_s = MagicMock()
        avoid_s.value = "true"
        webhook_s = MagicMock()
        webhook_s.value = ""

        db.query.return_value.filter.return_value.first.side_effect = [
            enabled, count_s, None, None, min_alt_s, moon_s, avoid_s, webhook_s,
        ]
        mock_sl.return_value = db

        mock_getenv.side_effect = lambda key, default=None: {
            "DEFAULT_LAT": "47.5",
            "DEFAULT_LON": "-110.0",
            "DEFAULT_ELEVATION": "900",
            "CELERY_TIMEZONE": "America/Denver",
            "DEFAULT_TIMEZONE": "America/Denver",
            "DEFAULT_LOCATION_NAME": "EnvLocation",
            "WEBHOOK_URL": "",
        }.get(key, default)

        mock_ps.return_value.generate_plan.return_value = mock_plan

        ws_inst = MagicMock()
        ws_inst.is_configured.return_value = False
        mock_ws.return_value = ws_inst

        db.refresh.side_effect = lambda obj: setattr(obj, "id", 10)

        result = generate_daily_plan_task()

    assert result["status"] == "success"


def test_generates_unique_plan_name_when_base_exists():
    from app.tasks.planning_tasks import generate_daily_plan_task

    mock_plan = MagicMock()
    mock_plan.scheduled_targets = []
    mock_plan.session.imaging_start.isoformat.return_value = "2026-05-26T22:00:00"
    mock_plan.session.imaging_end.isoformat.return_value = "2026-05-27T04:00:00"

    existing_plan = MagicMock()

    with (
        patch("app.tasks.planning_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.planning_tasks.PlannerService") as mock_ps,
        patch("app.tasks.planning_tasks.WebhookService") as mock_ws,
    ):
        db = MagicMock()
        enabled = MagicMock()
        enabled.value = "true"
        count_s = MagicMock()
        count_s.value = "3"
        db_loc = MagicMock()
        db_loc.latitude = 46.0
        db_loc.longitude = -112.0
        db_loc.elevation = 1200
        db_loc.timezone = "America/Denver"
        db_loc.name = "Test"
        min_alt_s = MagicMock()
        min_alt_s.value = "30.0"
        moon_s = MagicMock()
        moon_s.value = "50"
        avoid_s = MagicMock()
        avoid_s.value = "true"
        webhook_s = MagicMock()
        webhook_s.value = ""

        # First SavedPlan query: base name exists; second: name-2 also exists; third: name-3 free
        db.query.return_value.filter.return_value.first.side_effect = [
            enabled, count_s, db_loc, existing_plan, existing_plan, None,
            min_alt_s, moon_s, avoid_s, webhook_s,
        ]
        mock_sl.return_value = db

        mock_ps.return_value.generate_plan.return_value = mock_plan

        ws_inst = MagicMock()
        ws_inst.is_configured.return_value = False
        mock_ws.return_value = ws_inst

        db.refresh.side_effect = lambda obj: setattr(obj, "id", 99)

        result = generate_daily_plan_task()

    assert result["status"] == "success"
    # Plan name should have a numeric suffix
    assert result["plan_name"].endswith("-3")


def test_returns_success_with_correct_keys():
    from app.tasks.planning_tasks import generate_daily_plan_task

    target = MagicMock()
    target.target.name = "M31"
    target.composite_score = 0.9

    mock_plan = MagicMock()
    mock_plan.scheduled_targets = [target]
    mock_plan.session.imaging_start.isoformat.return_value = "2026-05-26T22:00:00"
    mock_plan.session.imaging_end.isoformat.return_value = "2026-05-27T04:00:00"

    with (
        patch("app.tasks.planning_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.planning_tasks.PlannerService") as mock_ps,
        patch("app.tasks.planning_tasks.WebhookService") as mock_ws,
    ):
        db = MagicMock()
        enabled = MagicMock()
        enabled.value = "true"
        count_s = MagicMock()
        count_s.value = "5"
        db_loc = MagicMock()
        db_loc.latitude = 46.0
        db_loc.longitude = -112.0
        db_loc.elevation = 1200
        db_loc.timezone = "America/Denver"
        db_loc.name = "Home"
        min_alt_s = MagicMock()
        min_alt_s.value = "30.0"
        moon_s = MagicMock()
        moon_s.value = "50"
        avoid_s = MagicMock()
        avoid_s.value = "true"
        webhook_s = MagicMock()
        webhook_s.value = ""

        db.query.return_value.filter.return_value.first.side_effect = [
            enabled, count_s, db_loc, None, min_alt_s, moon_s, avoid_s, webhook_s,
        ]
        mock_sl.return_value = db

        mock_ps.return_value.generate_plan.return_value = mock_plan

        ws_inst = MagicMock()
        ws_inst.is_configured.return_value = False
        mock_ws.return_value = ws_inst

        db.refresh.side_effect = lambda obj: setattr(obj, "id", 7)

        result = generate_daily_plan_task()

    assert result["status"] == "success"
    for key in ("plan_id", "plan_name", "observing_date", "target_count", "targets", "session_start", "session_end"):
        assert key in result
    assert result["target_count"] == 1
    assert result["targets"] == ["M31"]


def test_sends_webhook_when_configured():
    from app.tasks.planning_tasks import generate_daily_plan_task

    target = MagicMock()
    target.target.name = "NGC 891"
    target.composite_score = 0.85

    mock_plan = MagicMock()
    mock_plan.scheduled_targets = [target]
    mock_plan.session.imaging_start.isoformat.return_value = "2026-05-26T22:00:00"
    mock_plan.session.imaging_end.isoformat.return_value = "2026-05-27T04:00:00"

    with (
        patch("app.tasks.planning_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.planning_tasks.PlannerService") as mock_ps,
        patch("app.tasks.planning_tasks.WebhookService") as mock_ws,
    ):
        db = MagicMock()
        enabled = MagicMock()
        enabled.value = "true"
        count_s = MagicMock()
        count_s.value = "5"
        db_loc = MagicMock()
        db_loc.latitude = 46.0
        db_loc.longitude = -112.0
        db_loc.elevation = 1200
        db_loc.timezone = "America/Denver"
        db_loc.name = "Home"
        min_alt_s = MagicMock()
        min_alt_s.value = "30.0"
        moon_s = MagicMock()
        moon_s.value = "50"
        avoid_s = MagicMock()
        avoid_s.value = "true"
        webhook_s = MagicMock()
        webhook_s.value = "https://hooks.example.com/notify"

        db.query.return_value.filter.return_value.first.side_effect = [
            enabled, count_s, db_loc, None, min_alt_s, moon_s, avoid_s, webhook_s,
        ]
        mock_sl.return_value = db

        mock_ps.return_value.generate_plan.return_value = mock_plan

        ws_inst = MagicMock()
        ws_inst.is_configured.return_value = True
        ws_inst.send_plan_created_notification.return_value = True
        mock_ws.return_value = ws_inst

        db.refresh.side_effect = lambda obj: setattr(obj, "id", 5)

        generate_daily_plan_task()

    ws_inst.send_plan_created_notification.assert_called_once()


def test_skips_webhook_when_not_configured():
    from app.tasks.planning_tasks import generate_daily_plan_task

    mock_plan = MagicMock()
    mock_plan.scheduled_targets = []
    mock_plan.session.imaging_start.isoformat.return_value = "2026-05-26T22:00:00"
    mock_plan.session.imaging_end.isoformat.return_value = "2026-05-27T04:00:00"

    with (
        patch("app.tasks.planning_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.planning_tasks.PlannerService") as mock_ps,
        patch("app.tasks.planning_tasks.WebhookService") as mock_ws,
    ):
        db = MagicMock()
        enabled = MagicMock()
        enabled.value = "true"
        count_s = MagicMock()
        count_s.value = "5"
        db_loc = MagicMock()
        db_loc.latitude = 46.0
        db_loc.longitude = -112.0
        db_loc.elevation = 1200
        db_loc.timezone = "America/Denver"
        db_loc.name = "Home"
        min_alt_s = MagicMock()
        min_alt_s.value = "30.0"
        moon_s = MagicMock()
        moon_s.value = "50"
        avoid_s = MagicMock()
        avoid_s.value = "true"
        webhook_s = MagicMock()
        webhook_s.value = ""

        db.query.return_value.filter.return_value.first.side_effect = [
            enabled, count_s, db_loc, None, min_alt_s, moon_s, avoid_s, webhook_s,
        ]
        mock_sl.return_value = db

        mock_ps.return_value.generate_plan.return_value = mock_plan

        ws_inst = MagicMock()
        ws_inst.is_configured.return_value = False
        mock_ws.return_value = ws_inst

        db.refresh.side_effect = lambda obj: setattr(obj, "id", 3)

        generate_daily_plan_task()

    ws_inst.send_plan_created_notification.assert_not_called()


def test_raises_on_planner_error():
    from app.tasks.planning_tasks import generate_daily_plan_task
    import pytest

    with (
        patch("app.tasks.planning_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.planning_tasks.PlannerService") as mock_ps,
    ):
        db = MagicMock()
        enabled = MagicMock()
        enabled.value = "true"
        count_s = MagicMock()
        count_s.value = "5"
        db_loc = MagicMock()
        db_loc.latitude = 46.0
        db_loc.longitude = -112.0
        db_loc.elevation = 1200
        db_loc.timezone = "America/Denver"
        db_loc.name = "Home"
        min_alt_s = MagicMock()
        min_alt_s.value = "30.0"
        moon_s = MagicMock()
        moon_s.value = "50"
        avoid_s = MagicMock()
        avoid_s.value = "true"

        db.query.return_value.filter.return_value.first.side_effect = [
            enabled, count_s, db_loc, None, min_alt_s, moon_s, avoid_s,
        ]
        mock_sl.return_value = db

        mock_ps.return_value.generate_plan.side_effect = RuntimeError("ephemeris unavailable")

        with pytest.raises(RuntimeError, match="ephemeris unavailable"):
            generate_daily_plan_task()
