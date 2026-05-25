# Unmanned Capture Implementation Plan


**Goal:** Walk away after setting up the scope at sunset; it starts automatically at dusk, aborts if weather turns bad, and sends a notification when done.

**Architecture:** Two new Celery Beat tasks in `automation_tasks.py` (dusk scheduler + weather watchdog). Webhook service extended with session events. One tiny frontend fix to remove the manual-save prerequisite on Send to Scope.

**Tech Stack:** Python 3.11, Celery Beat, FastAPI, SQLAlchemy, Skyfield (via EphemerisService), socket (TCP ping), Vue 3

---

## Branch

```bash
git checkout -b feature/unmanned-capture
```

---

## Task 0: Branch

Already done above.

---

## Task 1: `automation_tasks.py` — dusk scheduler + auto-execute task

**Files to create:**
- `backend/app/tasks/automation_tasks.py`

**Files to modify:**
- `backend/app/tasks/celery_app.py`

### What exists

`celery_app.py` has two Beat entries and includes three task modules. `planning_tasks.py` has `get_setting_value(db, key, default)` — we'll replicate that pattern. `EphemerisService.calculate_twilight_times(location, date)` returns a dict with key `"astronomical_twilight_end"` (a timezone-aware datetime). `execute_observation_plan_task` in `telescope_tasks.py` takes `execution_id`, `targets_data`, `telescope_host`, `telescope_port`, `park_when_done`, `saved_plan_id`. `SavedPlan.plan_data` is a JSON dict that is the full `ObservingPlan.model_dump(mode="json")` — its `"scheduled_targets"` list is directly usable as `targets_data`.

### Step 1: Write the failing test

Create `backend/tests/unit/tasks/test_automation_tasks.py`:

```python
"""Unit tests for automation_tasks (dusk scheduler and auto-execute)."""
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest
import pytz


def _make_db(plan_data=None, location=None):
    """Build a minimal mock db session."""
    db = MagicMock()
    # AppSetting query: return enabled
    setting_mock = MagicMock()
    setting_mock.value = "true"
    db.query.return_value.filter.return_value.first.return_value = setting_mock
    return db


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
        # First call (AppSetting enabled), second call (SavedPlan) → None
        enabled_setting = MagicMock()
        enabled_setting.value = "true"
        db.query.return_value.filter.return_value.first.side_effect = [enabled_setting, None]
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
        plan = MagicMock(); plan.id = 1; plan.plan_data = {"scheduled_targets": [{"target": {"name": "M31"}}]}
        db.query.return_value.filter.return_value.first.side_effect = [
            enabled, plan, host_setting, port_setting, retry_setting
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
        db.query.return_value.filter.return_value.first.side_effect = [enabled, plan, host_s, port_s]
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = plan
        mock_sl.return_value = db
        mock_exec.apply_async = MagicMock()
        result = auto_execute_plan_task(plan_id=5, retry_count=0)
    assert result["status"] == "started"
    mock_exec.apply_async.assert_called_once()
```

### Step 2: Run test to verify it fails

```bash
docker exec astronomus pytest tests/unit/tasks/test_automation_tasks.py -q --no-cov
```
Expected: `ModuleNotFoundError: No module named 'app.tasks.automation_tasks'`

### Step 3: Create `automation_tasks.py`

```python
"""Celery tasks for unmanned capture automation."""

import logging
import os
import socket
import uuid
from datetime import date, datetime
from typing import Optional

import pytz

from app.database import SessionLocal
from app.models import Location
from app.models.plan_models import SavedPlan
from app.models.settings_models import AppSetting, ObservingLocation
from app.models.telescope_models import TelescopeExecution
from app.services.ephemeris_service import EphemerisService
from app.services.local_weather_service import LocalWeatherService
from app.services.webhook_service import WebhookService
from app.tasks.celery_app import celery_app
from app.tasks.telescope_tasks import abort_observation_plan_task, execute_observation_plan_task

logger = logging.getLogger(__name__)


def _get_setting(db, key: str, default: str) -> str:
    s = db.query(AppSetting).filter(AppSetting.key == key).first()
    return s.value if s else default


def _check_scope_reachable(host: str, port: int, timeout: float = 5.0) -> bool:
    """Return True if a TCP connection to host:port succeeds within timeout seconds."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _is_astronomical_night(db) -> bool:
    """Return True if the current wall-clock time is between astronomical dusk and dawn."""
    db_location = db.query(ObservingLocation).filter(ObservingLocation.is_default == True).first()
    if not db_location:
        return False
    location = Location(
        latitude=db_location.latitude,
        longitude=db_location.longitude,
        elevation=db_location.elevation or 0,
        timezone=db_location.timezone,
    )
    eph_svc = EphemerisService()
    twilight = eph_svc.calculate_twilight_times(location, datetime.now())
    dusk = twilight.get("astronomical_twilight_end")
    dawn = twilight.get("astronomical_twilight_start")
    if not dusk or not dawn:
        return False
    tz = pytz.timezone(db_location.timezone)
    now = datetime.now(tz=tz)
    return dusk <= now <= dawn


@celery_app.task(name="schedule_dusk_execution")
def schedule_dusk_execution_task() -> dict:
    """Run at 15:00 — compute tonight's astronomical dusk and schedule auto_execute_plan."""
    db = SessionLocal()
    try:
        enabled = _get_setting(db, "planning.auto_execute_enabled", "false")
        if enabled.lower() not in ("true", "1", "yes"):
            logger.info("Auto-execute disabled; skipping dusk scheduling")
            return {"status": "skipped", "reason": "disabled"}

        db_location = db.query(ObservingLocation).filter(ObservingLocation.is_default == True).first()
        if not db_location:
            logger.warning("No default location set; cannot compute dusk time")
            return {"status": "skipped", "reason": "no_location"}

        location = Location(
            latitude=db_location.latitude,
            longitude=db_location.longitude,
            elevation=db_location.elevation or 0,
            timezone=db_location.timezone,
        )
        eph_svc = EphemerisService()
        twilight = eph_svc.calculate_twilight_times(location, datetime.now())
        dusk_time = twilight.get("astronomical_twilight_end")

        if not dusk_time:
            logger.warning("Could not compute astronomical twilight end")
            return {"status": "skipped", "reason": "twilight_unavailable"}

        tz = pytz.timezone(db_location.timezone)
        now = datetime.now(tz=tz)
        if dusk_time <= now:
            logger.info(f"Dusk already passed ({dusk_time.isoformat()}), skipping")
            return {"status": "skipped", "reason": "dusk_already_passed"}

        # Schedule auto-execute to fire exactly at dusk
        auto_execute_plan_task.apply_async(eta=dusk_time)
        logger.info(f"Auto-execute scheduled for dusk: {dusk_time.isoformat()}")
        return {"status": "scheduled", "dusk_time": dusk_time.isoformat()}

    except Exception as e:
        logger.error(f"schedule_dusk_execution_task failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


@celery_app.task(name="auto_execute_plan")
def auto_execute_plan_task(plan_id: Optional[int] = None, retry_count: int = 0) -> dict:
    """Fire at astronomical dusk — load tonight's plan and start telescope execution."""
    db = SessionLocal()
    try:
        enabled = _get_setting(db, "planning.auto_execute_enabled", "false")
        if enabled.lower() not in ("true", "1", "yes"):
            return {"status": "skipped", "reason": "disabled"}

        # Find tonight's plan
        if plan_id is not None:
            plan = db.query(SavedPlan).filter(SavedPlan.id == plan_id).first()
        else:
            today = date.today().isoformat()
            plan = (
                db.query(SavedPlan)
                .filter(SavedPlan.observing_date == today)
                .order_by(SavedPlan.created_at.desc())
                .first()
            )

        if not plan:
            logger.warning("No saved plan found for tonight; auto-execute aborted")
            return {"status": "skipped", "reason": "no_plan"}

        targets_data = (plan.plan_data or {}).get("scheduled_targets", [])
        if not targets_data:
            logger.warning(f"Plan '{plan.name}' has no targets")
            return {"status": "skipped", "reason": "no_targets"}

        telescope_host = _get_setting(db, "user.pref.telescope_host", "192.168.2.47")
        telescope_port = int(_get_setting(db, "user.pref.telescope_port", "4700"))
        max_retries = int(_get_setting(db, "telescope.auto_execute_retry_count", "6"))

        if not _check_scope_reachable(telescope_host, telescope_port):
            if retry_count < max_retries:
                logger.info(
                    f"Scope not reachable at {telescope_host}:{telescope_port}; "
                    f"retrying in 5 min (attempt {retry_count + 1}/{max_retries})"
                )
                auto_execute_plan_task.apply_async(
                    kwargs={"plan_id": plan.id, "retry_count": retry_count + 1},
                    countdown=300,
                )
                return {"status": "retry", "retry_count": retry_count + 1}
            else:
                logger.error("Scope unreachable after max retries; giving up")
                _send_webhook(db, "scope_unreachable", plan_name=plan.name)
                return {"status": "failed", "reason": "scope_unreachable"}

        execution_id = str(uuid.uuid4())[:8]
        execute_observation_plan_task.apply_async(
            kwargs={
                "execution_id": execution_id,
                "targets_data": targets_data,
                "telescope_host": telescope_host,
                "telescope_port": telescope_port,
                "park_when_done": True,
                "saved_plan_id": plan.id,
            }
        )
        logger.info(f"Auto-execute started: plan='{plan.name}' execution_id={execution_id}")
        return {"status": "started", "execution_id": execution_id, "plan_id": plan.id, "plan_name": plan.name}

    except Exception as e:
        logger.error(f"auto_execute_plan_task failed: {e}", exc_info=True)
        raise
    finally:
        db.close()


def _send_webhook(db, event: str, **kwargs):
    """Fire-and-forget webhook; never raises."""
    try:
        webhook_url = _get_setting(db, "planning.webhook_url", os.getenv("WEBHOOK_URL", ""))
        svc = WebhookService(webhook_url=webhook_url)
        if not svc.is_configured():
            return
        if event == "scope_unreachable":
            svc.send_scope_unreachable_notification(plan_name=kwargs.get("plan_name", ""))
    except Exception as exc:
        logger.warning(f"Webhook send failed ({event}): {exc}")
```

### Step 4: Wire into `celery_app.py`

In `backend/app/tasks/celery_app.py`, change the `include` list and add two Beat entries:

```python
celery_app = Celery(
    "astro_planner",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.processing_tasks",
        "app.tasks.planning_tasks",
        "app.tasks.telescope_tasks",
        "app.tasks.automation_tasks",          # NEW
    ],
)
```

In `beat_schedule`, add after the existing entries:

```python
    "schedule-dusk-execution": {
        "task": "schedule_dusk_execution",
        "schedule": crontab(hour=15, minute=0),  # 3 PM daily — compute dusk, schedule auto-execute
        "args": (),
    },
    "weather-watchdog": {
        "task": "weather_watchdog",
        "schedule": crontab(minute="*/10"),  # Every 10 min — abort if conditions deteriorate
        "args": (),
    },
```

### Step 5: Run test to verify it passes

```bash
docker exec astronomus pytest tests/unit/tasks/test_automation_tasks.py -q --no-cov
```
Expected: 5 passed

### Step 6: Commit

```bash
git add backend/app/tasks/automation_tasks.py backend/app/tasks/celery_app.py \
        backend/tests/unit/tasks/__init__.py backend/tests/unit/tasks/test_automation_tasks.py
git commit -m "feat: add auto-execute at dusk Celery task and dusk scheduler"
```

---

## Task 2: `weather_watchdog_task` — abort on bad conditions

**Files to modify:**
- `backend/app/tasks/automation_tasks.py`

### What to add

Append to `automation_tasks.py` after `auto_execute_plan_task`:

```python
@celery_app.task(name="weather_watchdog")
def weather_watchdog_task() -> dict:
    """
    Run every 10 min — abort active telescope execution if weather deteriorates.

    Only acts during astronomical night and only when an execution is running.
    Checks local WS-2902 station (wx-service). If unavailable, skips silently.
    """
    db = SessionLocal()
    try:
        if not _is_astronomical_night(db):
            return {"status": "skipped", "reason": "daytime"}

        execution = (
            db.query(TelescopeExecution)
            .filter(TelescopeExecution.state.in_(["starting", "running"]))
            .order_by(TelescopeExecution.started_at.desc())
            .first()
        )
        if not execution:
            return {"status": "skipped", "reason": "no_active_execution"}

        abort_on_rain = _get_setting(db, "weather.abort_on_rain", "true").lower() in ("true", "1", "yes")
        max_wind = float(_get_setting(db, "weather.abort_wind_mph", "25.0"))
        max_humidity = int(_get_setting(db, "weather.abort_humidity_pct", "95"))

        wx = LocalWeatherService().get_current()
        if wx is None:
            logger.debug("wx-service unavailable; weather watchdog skipping check")
            return {"status": "skipped", "reason": "wx_unavailable"}

        abort_reason: Optional[str] = None
        if abort_on_rain and wx.is_raining:
            abort_reason = f"Rain detected ({wx.rain_rate_in_hr:.2f} in/hr)"
        elif wx.wind_speed_mph > max_wind:
            abort_reason = f"High wind ({wx.wind_speed_mph:.0f} mph > {max_wind:.0f} mph limit)"
        elif wx.humidity_pct >= max_humidity:
            abort_reason = f"Extreme humidity ({wx.humidity_pct}% >= {max_humidity}%)"

        if not abort_reason:
            return {
                "status": "ok",
                "wind_mph": wx.wind_speed_mph,
                "humidity_pct": wx.humidity_pct,
                "raining": wx.is_raining,
            }

        logger.warning(f"Weather abort triggered: {abort_reason} (execution {execution.execution_id})")
        abort_observation_plan_task.delay(execution.execution_id)

        # Webhook notification
        webhook_url = _get_setting(db, "planning.webhook_url", os.getenv("WEBHOOK_URL", ""))
        svc = WebhookService(webhook_url=webhook_url)
        if svc.is_configured():
            svc.send_weather_abort_notification(
                execution_id=execution.execution_id,
                reason=abort_reason,
                targets_completed=execution.targets_completed or 0,
            )

        return {"status": "aborted", "reason": abort_reason, "execution_id": execution.execution_id}

    except Exception as e:
        logger.error(f"weather_watchdog_task failed: {e}", exc_info=True)
        raise
    finally:
        db.close()
```

### Step 1: Write the failing tests (append to `test_automation_tasks.py`)

```python
def test_weather_watchdog_skips_daytime():
    from app.tasks.automation_tasks import weather_watchdog_task
    with patch("app.tasks.automation_tasks.SessionLocal") as mock_sl, \
         patch("app.tasks.automation_tasks._is_astronomical_night", return_value=False):
        mock_sl.return_value = MagicMock()
        result = weather_watchdog_task()
    assert result["status"] == "skipped"
    assert result["reason"] == "daytime"


def test_weather_watchdog_skips_no_execution():
    from app.tasks.automation_tasks import weather_watchdog_task
    with patch("app.tasks.automation_tasks.SessionLocal") as mock_sl, \
         patch("app.tasks.automation_tasks._is_astronomical_night", return_value=True):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_sl.return_value = db
        result = weather_watchdog_task()
    assert result["status"] == "skipped"
    assert result["reason"] == "no_active_execution"


def test_weather_watchdog_aborts_on_rain():
    from app.tasks.automation_tasks import weather_watchdog_task
    with patch("app.tasks.automation_tasks.SessionLocal") as mock_sl, \
         patch("app.tasks.automation_tasks._is_astronomical_night", return_value=True), \
         patch("app.tasks.automation_tasks.LocalWeatherService") as mock_wx_cls, \
         patch("app.tasks.automation_tasks.abort_observation_plan_task") as mock_abort:
        db = MagicMock()
        execution = MagicMock()
        execution.execution_id = "abc123"
        execution.targets_completed = 2
        # Query chain: settings return "true"/"25.0"/"95", execution found
        abort_setting = MagicMock(); abort_setting.value = "true"
        wind_setting = MagicMock(); wind_setting.value = "25.0"
        humid_setting = MagicMock(); humid_setting.value = "95"
        db.query.return_value.filter.return_value.first.side_effect = [
            abort_setting, wind_setting, humid_setting
        ]
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = execution
        mock_sl.return_value = db

        wx = MagicMock()
        wx.is_raining = True
        wx.rain_rate_in_hr = 0.12
        wx.wind_speed_mph = 5.0
        wx.humidity_pct = 70
        mock_wx_cls.return_value.get_current.return_value = wx
        mock_abort.delay = MagicMock()

        result = weather_watchdog_task()
    assert result["status"] == "aborted"
    assert "Rain" in result["reason"]
    mock_abort.delay.assert_called_once_with("abc123")


def test_weather_watchdog_ok_when_clear():
    from app.tasks.automation_tasks import weather_watchdog_task
    with patch("app.tasks.automation_tasks.SessionLocal") as mock_sl, \
         patch("app.tasks.automation_tasks._is_astronomical_night", return_value=True), \
         patch("app.tasks.automation_tasks.LocalWeatherService") as mock_wx_cls:
        db = MagicMock()
        execution = MagicMock(); execution.execution_id = "xyz"
        abort_s = MagicMock(); abort_s.value = "true"
        wind_s = MagicMock(); wind_s.value = "25.0"
        humid_s = MagicMock(); humid_s.value = "95"
        db.query.return_value.filter.return_value.first.side_effect = [abort_s, wind_s, humid_s]
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = execution
        mock_sl.return_value = db

        wx = MagicMock()
        wx.is_raining = False
        wx.wind_speed_mph = 8.0
        wx.humidity_pct = 55
        mock_wx_cls.return_value.get_current.return_value = wx
        result = weather_watchdog_task()
    assert result["status"] == "ok"
```

### Step 2: Run tests

```bash
docker exec astronomus pytest tests/unit/tasks/test_automation_tasks.py -q --no-cov
```
Expected: tests fail because `weather_watchdog_task` doesn't exist yet.

### Step 3: Add `weather_watchdog_task` to `automation_tasks.py`

(code given above)

### Step 4: Run tests

```bash
docker exec astronomus pytest tests/unit/tasks/test_automation_tasks.py -q --no-cov
```
Expected: 9 passed

### Step 5: Commit

```bash
git add backend/app/tasks/automation_tasks.py backend/tests/unit/tasks/test_automation_tasks.py
git commit -m "feat: add weather watchdog task — abort execution on rain, high wind, or humidity"
```

---

## Task 3: Webhook session events

**Files to modify:**
- `backend/app/services/webhook_service.py`
- `backend/app/tasks/telescope_tasks.py`

### What to add to `webhook_service.py`

After `send_plan_created_notification`, add three new methods:

```python
def send_session_started_notification(
    self,
    execution_id: str,
    plan_name: str,
    target_count: int,
    target_names: List[str],
) -> bool:
    if not self.webhook_url:
        return False
    payload = {
        "event": "session_started",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "execution": {
            "id": execution_id,
            "plan_name": plan_name,
            "target_count": target_count,
            "targets": target_names,
        },
    }
    return self._post(payload)

def send_session_completed_notification(
    self,
    execution_id: str,
    plan_name: str,
    state: str,
    targets_completed: int,
    targets_failed: int,
    total_targets: int,
    duration_str: Optional[str] = None,
) -> bool:
    if not self.webhook_url:
        return False
    payload = {
        "event": "session_completed",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "execution": {
            "id": execution_id,
            "plan_name": plan_name,
            "state": state,
            "targets_completed": targets_completed,
            "targets_failed": targets_failed,
            "total_targets": total_targets,
            "duration": duration_str,
        },
    }
    return self._post(payload)

def send_weather_abort_notification(
    self,
    execution_id: str,
    reason: str,
    targets_completed: int,
) -> bool:
    if not self.webhook_url:
        return False
    payload = {
        "event": "weather_abort",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "execution": {
            "id": execution_id,
            "reason": reason,
            "targets_completed": targets_completed,
        },
    }
    return self._post(payload)

def send_scope_unreachable_notification(self, plan_name: str) -> bool:
    if not self.webhook_url:
        return False
    payload = {
        "event": "scope_unreachable",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "plan_name": plan_name,
        "message": "Auto-execute failed: telescope not reachable at dusk after retries",
    }
    return self._post(payload)
```

Also add a private `_post` helper to DRY the retry loop (extract the existing loop from `send_plan_created_notification`):

```python
def _post(self, payload: dict) -> bool:
    """POST payload to webhook_url with retries. Returns True on success."""
    for attempt in range(self.max_retries + 1):
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json", "User-Agent": "AstroPlanner/1.0"},
            )
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            if attempt == self.max_retries:
                logger.error(f"Webhook failed after {self.max_retries + 1} attempts: {e}")
                return False
    return False
```

And update `send_plan_created_notification` to call `self._post(payload)` instead of its inline loop.

### Wire into `telescope_tasks.py`

In `execute_observation_plan_task`, after `execution.state = "running"` and `db.commit()` (line ~189), add:

```python
# Notify webhook that session started
webhook_url = get_setting_value_from_db(db, "planning.webhook_url")
if webhook_url:
    wh = WebhookService(webhook_url=webhook_url)
    target_names_list = [t.get("target", {}).get("name", "") for t in targets_data]
    wh.send_session_started_notification(
        execution_id=execution_id,
        plan_name=f"plan-{saved_plan_id}" if saved_plan_id else execution_id,
        target_count=len(targets_data),
        target_names=target_names_list,
    )
```

And after `db.commit()` at the end (line ~223), add:

```python
# Notify webhook that session completed
if webhook_url:
    wh = WebhookService(webhook_url=webhook_url)
    wh.send_session_completed_notification(
        execution_id=execution_id,
        plan_name=f"plan-{saved_plan_id}" if saved_plan_id else execution_id,
        state=final_progress.state.value,
        targets_completed=final_progress.targets_completed,
        targets_failed=final_progress.targets_failed,
        total_targets=final_progress.total_targets,
        duration_str=str(final_progress.elapsed_time) if final_progress.elapsed_time else None,
    )
```

Add a small helper at module level in `telescope_tasks.py`:

```python
def get_setting_value_from_db(db, key: str, default: str = "") -> str:
    from app.models.settings_models import AppSetting
    s = db.query(AppSetting).filter(AppSetting.key == key).first()
    return s.value if s else default
```

Also add `from app.services.webhook_service import WebhookService` to imports in `telescope_tasks.py`.

### Step 1: Run existing telescope task tests

```bash
docker exec astronomus pytest tests/unit/ -q --no-cov -k "telescope"
```
Make sure baseline passes before changes.

### Step 2: Make changes described above to `webhook_service.py` and `telescope_tasks.py`

### Step 3: Run automation tests + full unit suite

```bash
docker exec astronomus pytest tests/unit/ -q --no-cov
```
Expected: all pass

### Step 4: Commit

```bash
git add backend/app/services/webhook_service.py backend/app/tasks/telescope_tasks.py
git commit -m "feat: add session started/completed/weather-abort webhook notifications"
```

---

## Task 4: Auto-save before Send to Scope

**Files to modify:**
- `frontend/vue-app/src/views/PlanningView.vue`

### What exists

`PlanningView.vue` around line 55–65 has the Send to Scope button:

```html
<button
  :disabled="planningStore.loading || !lastSavedPlanId"
  @click="sendToScope"
  ...
>Send to Scope</button>
```

And `sendToScope()` (line ~297):

```javascript
async function sendToScope() {
  if (!lastSavedPlanId.value) return
  try {
    await planningStore.sendToTelescope(lastSavedPlanId.value)
  } catch { /* handled in store */ }
}
```

### What to change

1. Change the button `disabled` condition to `!planningStore.currentPlan` (no longer requires pre-save):
   ```html
   :disabled="planningStore.loading || !planningStore.currentPlan"
   ```

2. Replace `sendToScope()` to auto-save if needed:
   ```javascript
   async function sendToScope() {
     if (!planningStore.currentPlan) return
     if (!lastSavedPlanId.value) {
       try {
         const saved = await planningStore.savePlan()
         if (saved?.id) lastSavedPlanId.value = saved.id
       } catch {
         return // savePlan already shows error toast
       }
     }
     try {
       await planningStore.sendToTelescope(lastSavedPlanId.value)
     } catch { /* handled in store */ }
   }
   ```

### Step 1: Find the exact lines

```bash
grep -n "lastSavedPlanId\|sendToScope\|Send to Scope" frontend/vue-app/src/views/PlanningView.vue
```

### Step 2: Apply the changes using Edit tool

### Step 3: Commit

```bash
git add frontend/vue-app/src/views/PlanningView.vue
git commit -m "fix: auto-save plan before Send to Scope upload"
```

---

## Task 5: Automation settings in backend + Settings UI

### Step A: Backend — add automation keys to settings API

**File to modify:** `backend/app/api/settings.py`

In `_PREF_KEYS` dict (around line 490), add after the existing planning entries:

```python
    # Automation
    "autoExecuteEnabled": "planning.auto_execute_enabled",
    "autoExecuteRetryCount": "telescope.auto_execute_retry_count",
    "weatherAbortOnRain": "weather.abort_on_rain",
    "weatherAbortWindMph": "weather.abort_wind_mph",
    "weatherAbortHumidityPct": "weather.abort_humidity_pct",
```

In `_PREF_DEFAULTS` (a few lines below), add:

```python
    "autoExecuteEnabled": "false",
    "autoExecuteRetryCount": "6",
    "weatherAbortOnRain": "true",
    "weatherAbortWindMph": "25.0",
    "weatherAbortHumidityPct": "95",
```

### Step B: Frontend — add Automation tab to SettingsModal

**File to modify:** `frontend/vue-app/src/components/shared/SettingsModal.vue`

1. Add `{ id: 'automation', label: 'Automation' }` to the `tabs` array (after `{ id: 'horizon', label: 'Horizon' }`).

2. Add the tab content block after the `<div v-else-if="activeTab === 'horizon'" ...>` block:

```html
<!-- Automation tab -->
<div v-else-if="activeTab === 'automation'" class="flex-1 overflow-y-auto p-6 space-y-6">
  <!-- Auto-execute at dusk -->
  <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
    <div class="text-sm font-semibold text-gray-300 mb-4">Auto-Execute at Dusk</div>
    <label class="flex items-center gap-3 cursor-pointer mb-4">
      <input
        type="checkbox"
        v-model="localSettings.autoExecuteEnabled"
        class="w-4 h-4 rounded"
      />
      <span class="text-sm text-gray-300">
        Automatically start tonight's plan at astronomical dusk
      </span>
    </label>
    <p class="text-xs text-gray-500 leading-relaxed">
      Requires a saved plan for today (auto-generated at noon). The scope must be
      reachable on your home network — retries every 5 min for up to
      {{ localSettings.autoExecuteRetryCount || 6 }} attempts.
    </p>
    <div class="mt-3 flex items-center gap-2">
      <label class="text-xs text-gray-400 w-28">Scope retry attempts</label>
      <input
        v-model.number="localSettings.autoExecuteRetryCount"
        type="number" min="1" max="12" step="1"
        class="input-sm w-16"
      />
    </div>
  </div>

  <!-- Weather abort -->
  <div class="bg-gray-900 border border-gray-800 rounded-xl p-5">
    <div class="text-sm font-semibold text-gray-300 mb-4">Weather Abort</div>
    <label class="flex items-center gap-3 cursor-pointer mb-3">
      <input
        type="checkbox"
        v-model="localSettings.weatherAbortOnRain"
        class="w-4 h-4 rounded"
      />
      <span class="text-sm text-gray-300">Stop session if rain detected</span>
    </label>
    <div class="space-y-2">
      <div class="flex items-center gap-2">
        <label class="text-xs text-gray-400 w-36">Max wind (mph)</label>
        <input
          v-model.number="localSettings.weatherAbortWindMph"
          type="number" min="0" max="60" step="1"
          class="input-sm w-16"
        />
      </div>
      <div class="flex items-center gap-2">
        <label class="text-xs text-gray-400 w-36">Max humidity (%)</label>
        <input
          v-model.number="localSettings.weatherAbortHumidityPct"
          type="number" min="50" max="100" step="1"
          class="input-sm w-16"
        />
      </div>
    </div>
    <p class="text-xs text-gray-500 mt-3">
      Checked every 10 minutes using your local weather station. Sends a
      webhook notification if a session is aborted.
    </p>
  </div>

  <!-- Webhook URL (already in Planning tab, show reminder) -->
  <p class="text-xs text-gray-600">
    Notifications are sent to the Webhook URL configured in the Planning tab.
  </p>
</div>
```

3. `localSettings` already maps to the settings store — no additional wiring needed because the existing `saveSettings()` call in the modal already writes all `_PREF_KEYS` fields through the settings API.

(Note: `input-sm` class needs to exist or reuse `input-dark`. Add to modal's `<style scoped>` if missing:)
```css
.input-sm {
  background: #1f2937;
  border: 1px solid #374151;
  border-radius: 0.375rem;
  color: #e5e7eb;
  padding: 0.25rem 0.375rem;
  font-size: 0.75rem;
  outline: none;
}
.input-sm:focus { border-color: #3b82f6; }
```

### Step 3: Commit

```bash
git add backend/app/api/settings.py \
        frontend/vue-app/src/components/shared/SettingsModal.vue
git commit -m "feat: add Automation tab to settings (auto-execute at dusk + weather abort thresholds)"
```

---

## Task 6: Run full test suite and fix failures

```bash
docker exec astronomus pytest tests/ -q --no-cov
```

Common failures and fixes:

**`tests/unit/tasks/` — missing `__init__.py`:** Create empty `backend/tests/unit/tasks/__init__.py`.

**Import errors in `automation_tasks.py`:** If `pytz` not available in container, replace `pytz.timezone(...)` with `zoneinfo.ZoneInfo(...)` (Python 3.9+) or add `import pytz` after verifying it's installed:
```bash
docker exec astronomus python3 -c "import pytz; print('ok')"
```

**`webhook_service.py` changes break existing tests:** Verify `send_plan_created_notification` still works after extracting `_post`.

**CI formatting:**
```bash
docker exec astronomus bash -c "cd /app && python3 -m py_compile app/tasks/automation_tasks.py && echo ok"
```

Once tests pass, commit any fixes:
```bash
git add -u && git commit -m "fix: test suite failures from unmanned-capture features"
```

---

## Task 7: PR to main

```bash
git push -u origin feature/unmanned-capture
gh pr create \
  --title "feat: unmanned capture — auto-execute at dusk, weather abort, session webhooks" \
  --body "..."
```

After CI passes:
```bash
gh pr merge <N> --squash --delete-branch
git checkout main
docker compose build astronomus && docker compose up -d astronomus
```

---

## Migration chain

No new DB migrations needed. New settings use the existing `app_settings` key-value table via `AppSetting` rows.

---

## Verification checklist

- [ ] `docker exec astronomus pytest tests/ -q --no-cov` → all pass, no new failures
- [ ] Settings → Automation tab visible and saves correctly
- [ ] Send to Scope no longer requires manual save first
- [ ] Celery Beat schedule includes `schedule-dusk-execution` (15:00) and `weather-watchdog` (*/10)
- [ ] `auto_execute_plan_task` dispatches `execute_observation_plan_task` with correct args
- [ ] `weather_watchdog_task` calls `abort_observation_plan_task` when rain detected
