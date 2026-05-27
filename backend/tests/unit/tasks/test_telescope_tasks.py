"""Unit tests for telescope_tasks helpers and abort/execute tasks."""

from unittest.mock import MagicMock, patch


def test_get_db_setting_returns_value_when_exists():
    from app.tasks.telescope_tasks import _get_db_setting

    db = MagicMock()
    setting = MagicMock()
    setting.value = "http://hooks.example.com"
    db.query.return_value.filter.return_value.first.return_value = setting

    result = _get_db_setting(db, "planning.webhook_url", "")
    assert result == "http://hooks.example.com"


def test_get_db_setting_returns_default_when_missing():
    from app.tasks.telescope_tasks import _get_db_setting

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = _get_db_setting(db, "planning.webhook_url", "fallback")
    assert result == "fallback"


def test_webhook_session_started_sends_when_url_set():
    from app.tasks.telescope_tasks import _webhook_session_started

    db = MagicMock()
    setting = MagicMock()
    setting.value = "https://hooks.example.com"
    db.query.return_value.filter.return_value.first.return_value = setting

    with patch("app.tasks.telescope_tasks.WebhookService") as mock_ws:
        ws_inst = MagicMock()
        mock_ws.return_value = ws_inst
        _webhook_session_started(db, "exec-1", 5, [{"target": {"name": "M31"}}])

    ws_inst.send_session_started_notification.assert_called_once()
    call_kwargs = ws_inst.send_session_started_notification.call_args[1]
    assert call_kwargs["execution_id"] == "exec-1"
    assert call_kwargs["target_count"] == 1


def test_webhook_session_started_does_nothing_when_no_url():
    from app.tasks.telescope_tasks import _webhook_session_started

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with patch("app.tasks.telescope_tasks.WebhookService") as mock_ws:
        _webhook_session_started(db, "exec-2", None, [])

    mock_ws.assert_not_called()


def test_webhook_session_started_logs_warning_on_exception():
    from app.tasks.telescope_tasks import _webhook_session_started

    db = MagicMock()
    setting = MagicMock()
    setting.value = "https://hooks.example.com"
    db.query.return_value.filter.return_value.first.return_value = setting

    with (
        patch("app.tasks.telescope_tasks.WebhookService") as mock_ws,
        patch("app.tasks.telescope_tasks.logger") as mock_logger,
    ):
        mock_ws.return_value.send_session_started_notification.side_effect = Exception("timeout")
        _webhook_session_started(db, "exec-3", 1, [])

    mock_logger.warning.assert_called_once()


def test_webhook_session_completed_sends_when_url_set():
    from app.tasks.telescope_tasks import _webhook_session_completed

    db = MagicMock()
    setting = MagicMock()
    setting.value = "https://hooks.example.com"
    db.query.return_value.filter.return_value.first.return_value = setting

    final_progress = MagicMock()
    final_progress.state.value = "completed"
    final_progress.targets_completed = 3
    final_progress.targets_failed = 0
    final_progress.total_targets = 3
    final_progress.elapsed_time = None

    with patch("app.tasks.telescope_tasks.WebhookService") as mock_ws:
        ws_inst = MagicMock()
        mock_ws.return_value = ws_inst
        _webhook_session_completed(db, "exec-4", 7, final_progress)

    ws_inst.send_session_completed_notification.assert_called_once()


def test_webhook_session_completed_does_nothing_when_no_url():
    from app.tasks.telescope_tasks import _webhook_session_completed

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    final_progress = MagicMock()
    with patch("app.tasks.telescope_tasks.WebhookService") as mock_ws:
        _webhook_session_completed(db, "exec-5", None, final_progress)

    mock_ws.assert_not_called()


def test_webhook_session_completed_logs_warning_on_exception():
    from app.tasks.telescope_tasks import _webhook_session_completed

    db = MagicMock()
    setting = MagicMock()
    setting.value = "https://hooks.example.com"
    db.query.return_value.filter.return_value.first.return_value = setting

    final_progress = MagicMock()
    final_progress.state.value = "completed"
    final_progress.elapsed_time = None

    with (
        patch("app.tasks.telescope_tasks.WebhookService") as mock_ws,
        patch("app.tasks.telescope_tasks.logger") as mock_logger,
    ):
        mock_ws.return_value.send_session_completed_notification.side_effect = Exception("network error")
        _webhook_session_completed(db, "exec-6", 2, final_progress)

    mock_logger.warning.assert_called_once()


def test_abort_returns_error_when_execution_not_found():
    from app.tasks.telescope_tasks import abort_observation_plan_task

    with patch("app.tasks.telescope_tasks.SessionLocal") as mock_sl:
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        mock_sl.return_value = db

        result = abort_observation_plan_task("nonexistent-exec")

    assert result["success"] is False
    assert "not found" in result["error"]


def test_abort_returns_error_when_not_running():
    from app.tasks.telescope_tasks import abort_observation_plan_task

    with patch("app.tasks.telescope_tasks.SessionLocal") as mock_sl:
        db = MagicMock()
        execution = MagicMock()
        execution.state = "completed"
        db.query.return_value.filter.return_value.first.return_value = execution
        mock_sl.return_value = db

        result = abort_observation_plan_task("done-exec")

    assert result["success"] is False
    assert "completed" in result["error"]


def test_abort_updates_state_and_revokes():
    from app.tasks.telescope_tasks import abort_observation_plan_task

    with (
        patch("app.tasks.telescope_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.telescope_tasks.celery_app") as mock_celery,
    ):
        db = MagicMock()
        execution = MagicMock()
        execution.state = "running"
        execution.celery_task_id = "celery-task-abc"
        db.query.return_value.filter.return_value.first.return_value = execution
        mock_sl.return_value = db

        result = abort_observation_plan_task("running-exec")

    assert result["success"] is True
    assert result["execution_id"] == "running-exec"
    assert execution.state == "aborted"
    mock_celery.control.revoke.assert_called_once_with("celery-task-abc", terminate=True)
    db.commit.assert_called()


def test_execute_observation_plan_creates_db_record():
    from app.tasks.telescope_tasks import TelescopeExecutionTask, execute_observation_plan_task

    targets_data = [{"target": {"name": "M31"}, "duration_minutes": 120}]

    final_progress = MagicMock()
    final_progress.state.value = "completed"
    final_progress.targets_completed = 1
    final_progress.targets_failed = 0
    final_progress.total_targets = 1
    final_progress.progress_percent = 100.0
    final_progress.elapsed_time = None
    final_progress.errors = []

    seestar_mock = MagicMock()
    seestar_mock.connected = False
    telescope_service_mock = MagicMock()

    # run_until_complete: first call = connect, second = execute_plan → final_progress
    mock_loop = MagicMock()
    mock_loop.run_until_complete.side_effect = [None, final_progress]

    # Build a mock target that has .target.name etc so DB record creation works
    mock_target = MagicMock()
    mock_target.target.name = "M31"
    mock_target.target.catalog_id = "M31"
    mock_target.target.ra_hours = 0.71
    mock_target.target.dec_degrees = 41.27
    mock_target.target.object_type = "galaxy"
    mock_target.target.magnitude = 3.4
    mock_target.start_time = None
    mock_target.duration_minutes = 120
    mock_target.recommended_frames = 60
    mock_target.recommended_exposure = 60

    with (
        patch("app.tasks.telescope_tasks.SessionLocal") as mock_sl,
        patch("app.tasks.telescope_tasks.asyncio.new_event_loop", return_value=mock_loop),
        patch("app.tasks.telescope_tasks.asyncio.set_event_loop"),
        patch("app.tasks.telescope_tasks.ScheduledTarget", return_value=mock_target),
        patch.object(
            TelescopeExecutionTask, "seestar_client", new_callable=lambda: property(lambda self: seestar_mock)
        ),
        patch.object(
            TelescopeExecutionTask,
            "telescope_service",
            new_callable=lambda: property(lambda self: telescope_service_mock),
        ),
        patch.object(TelescopeExecutionTask, "update_state", lambda self, **kw: None),
        patch.object(
            TelescopeExecutionTask, "request", new_callable=lambda: property(lambda self: MagicMock(id="fake-task-id"))
        ),
    ):
        db = MagicMock()
        db.refresh.side_effect = lambda obj: None
        mock_sl.return_value = db

        result = execute_observation_plan_task(
            execution_id="exec-test",
            targets_data=targets_data,
            telescope_host="192.168.2.47",
            telescope_port=4700,
            park_when_done=True,
            saved_plan_id=None,
        )

    assert result["execution_id"] == "exec-test"
    assert result["state"] == "completed"
    db.add.assert_called()
    db.commit.assert_called()
