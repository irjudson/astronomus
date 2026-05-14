"""Unit tests for automation_tasks (dusk scheduler and auto-execute)."""
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest
import pytz


def test_check_scope_reachable_success():
    from app.tasks.automation_tasks import _check_scope_reachable
    with patch("socket.create_connection") as mock_conn:
        mock_conn.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        assert _check_scope_reachable("192.168.2.47", 4700) is True


def test_check_scope_reachable_failure():
    from app.tasks.automation_tasks import _check_scope_reachable
    with patch("socket.create_connection", side_effect=OSError("refused")):
        assert _check_scope_reachable("192.168.2.47", 4700) is False


def test_auto_execute_skips_when_disabled():
    from app.tasks.automation_tasks import auto_execute_plan_task
    with patch("app.tasks.automation_tasks.SessionLocal") as mock_sl:
        db = MagicMock()
        setting_disabled = MagicMock()
        setting_disabled.value = "false"
        db.query.return_value.filter.return_value.first.return_value = setting_disabled
        mock_sl.return_value = db
        result = auto_execute_plan_task()
    assert result["status"] == "skipped"
    assert result["reason"] == "disabled"


def test_auto_execute_skips_when_no_plan():
    from app.tasks.automation_tasks import auto_execute_plan_task
    with patch("app.tasks.automation_tasks.SessionLocal") as mock_sl:
        db = MagicMock()
        enabled_setting = MagicMock()
        enabled_setting.value = "true"
        # first call → enabled setting, subsequent plan query → None
        db.query.return_value.filter.return_value.first.return_value = enabled_setting
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_sl.return_value = db
        result = auto_execute_plan_task()
    assert result["status"] == "skipped"
    assert result["reason"] == "no_plan"


def test_auto_execute_retries_when_scope_unreachable():
    from app.tasks.automation_tasks import auto_execute_plan_task
    with patch("app.tasks.automation_tasks.SessionLocal") as mock_sl, \
         patch("app.tasks.automation_tasks._check_scope_reachable", return_value=False), \
         patch("app.tasks.automation_tasks.auto_execute_plan_task.apply_async") as mock_async:
        db = MagicMock()
        enabled = MagicMock(); enabled.value = "true"
        host_setting = MagicMock(); host_setting.value = "192.168.2.47"
        port_setting = MagicMock(); port_setting.value = "4700"
        retry_setting = MagicMock(); retry_setting.value = "6"
        plan = MagicMock()
        plan.id = 1
        plan.plan_data = {"scheduled_targets": [{"target": {"name": "M31"}}]}
        db.query.return_value.filter.return_value.first.side_effect = [
            enabled, host_setting, port_setting, retry_setting
        ]
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = plan
        mock_sl.return_value = db
        result = auto_execute_plan_task(plan_id=1, retry_count=0)
    assert result["status"] == "retry"
    mock_async.assert_called_once()


def test_auto_execute_starts_execution():
    from app.tasks.automation_tasks import auto_execute_plan_task
    targets = [{"target": {"name": "M31", "catalog_id": "M31", "ra_hours": 0.71,
                            "dec_degrees": 41.27, "object_type": "galaxy",
                            "magnitude": 3.4, "size_arcmin": 190.0}}]
    with patch("app.tasks.automation_tasks.SessionLocal") as mock_sl, \
         patch("app.tasks.automation_tasks._check_scope_reachable", return_value=True), \
         patch("app.tasks.automation_tasks.execute_observation_plan_task") as mock_exec:
        db = MagicMock()
        enabled = MagicMock(); enabled.value = "true"
        host_s = MagicMock(); host_s.value = "192.168.2.47"
        port_s = MagicMock(); port_s.value = "4700"
        plan = MagicMock(); plan.id = 5; plan.name = "2026-05-14-plan"
        plan.plan_data = {"scheduled_targets": targets}
        db.query.return_value.filter.return_value.first.side_effect = [enabled, host_s, port_s]
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = plan
        mock_sl.return_value = db
        mock_exec.apply_async = MagicMock()
        result = auto_execute_plan_task(plan_id=5, retry_count=0)
    assert result["status"] == "started"
    mock_exec.apply_async.assert_called_once()
