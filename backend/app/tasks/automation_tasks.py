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
from app.services.ephemeris_service import EphemerisService
from app.services.webhook_service import WebhookService
from app.tasks.celery_app import celery_app
from app.tasks.telescope_tasks import execute_observation_plan_task

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
    """Return True if current wall-clock time is between astronomical dusk and dawn."""
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

        if plan_id is not None:
            plan = db.get(SavedPlan, plan_id)
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

        if not _check_scope_reachable(telescope_host, telescope_port):
            max_retries = int(_get_setting(db, "telescope.auto_execute_retry_count", "6"))
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
                _send_scope_unreachable_webhook(db, plan_name=plan.name)
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


def _send_scope_unreachable_webhook(db, plan_name: str) -> None:
    """Fire-and-forget webhook for scope unreachable event; never raises."""
    try:
        webhook_url = _get_setting(db, "planning.webhook_url", os.getenv("WEBHOOK_URL", ""))
        svc = WebhookService(webhook_url=webhook_url)
        if svc.is_configured():
            svc.send_scope_unreachable_notification(plan_name=plan_name)
    except Exception as exc:
        logger.warning(f"Webhook send failed (scope_unreachable): {exc}")
