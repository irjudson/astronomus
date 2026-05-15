"""Celery tasks for telescope execution."""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

from celery import Task

from app.clients.seestar_client import SeestarClient
from app.database import SessionLocal
from app.models import ScheduledTarget
from app.models.telescope_models import TelescopeExecution, TelescopeExecutionTarget
from app.services.telescope_service import TelescopeService
from app.services.webhook_service import WebhookService
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_db_setting(db, key: str, default: str = "") -> str:
    from app.models.settings_models import AppSetting

    s = db.query(AppSetting).filter(AppSetting.key == key).first()
    return s.value if s else default


def _webhook_session_started(db, execution_id: str, saved_plan_id, targets_data: list) -> None:
    try:
        webhook_url = _get_db_setting(db, "planning.webhook_url")
        if not webhook_url:
            return
        target_names = [t.get("target", {}).get("name", "") for t in targets_data]
        plan_name = f"plan-{saved_plan_id}" if saved_plan_id else execution_id
        WebhookService(webhook_url=webhook_url).send_session_started_notification(
            execution_id=execution_id,
            plan_name=plan_name,
            target_count=len(targets_data),
            target_names=target_names,
        )
    except Exception as exc:
        logger.warning(f"session_started webhook failed: {exc}")


def _webhook_session_completed(db, execution_id: str, saved_plan_id, final_progress) -> None:
    try:
        webhook_url = _get_db_setting(db, "planning.webhook_url")
        if not webhook_url:
            return
        plan_name = f"plan-{saved_plan_id}" if saved_plan_id else execution_id
        WebhookService(webhook_url=webhook_url).send_session_completed_notification(
            execution_id=execution_id,
            plan_name=plan_name,
            state=final_progress.state.value,
            targets_completed=final_progress.targets_completed,
            targets_failed=final_progress.targets_failed,
            total_targets=final_progress.total_targets,
            duration_str=str(final_progress.elapsed_time) if final_progress.elapsed_time else None,
        )
    except Exception as exc:
        logger.warning(f"session_completed webhook failed: {exc}")


class TelescopeExecutionTask(Task):
    """Base task for telescope execution with state tracking."""

    def __init__(self):
        self._seestar_client = None
        self._telescope_service = None

    @property
    def seestar_client(self):
        """Get or create Seestar client (singleton per worker)."""
        if self._seestar_client is None:
            self._seestar_client = SeestarClient()
        return self._seestar_client

    @property
    def telescope_service(self):
        """Get or create telescope service (singleton per worker)."""
        if self._telescope_service is None:
            self._telescope_service = TelescopeService(client=self.seestar_client, logger=logger)
        return self._telescope_service


@celery_app.task(bind=True, base=TelescopeExecutionTask, name="execute_observation_plan", track_started=True)
def execute_observation_plan_task(
    self,
    execution_id: str,
    targets_data: List[Dict[str, Any]],
    telescope_host: str,
    telescope_port: int = 4700,
    park_when_done: bool = True,
    saved_plan_id: int = None,
):
    """
    Execute an observation plan on the telescope.

    This task runs the entire observation sequence and streams progress
    updates via database and Celery state.

    Args:
        execution_id: Unique execution ID
        targets_data: List of scheduled target dictionaries
        telescope_host: Telescope IP address
        telescope_port: Telescope TCP port
        park_when_done: Whether to park telescope when done
        saved_plan_id: Optional ID of saved plan this execution is based on
    """
    db = SessionLocal()

    try:
        # Create execution record
        execution = TelescopeExecution(
            execution_id=execution_id,
            celery_task_id=self.request.id,
            state="starting",
            total_targets=len(targets_data),
            telescope_host=telescope_host,
            telescope_port=telescope_port,
            park_when_done=park_when_done,
            saved_plan_id=saved_plan_id,
            started_at=datetime.utcnow(),
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)

        logger.info(f"Starting execution {execution_id} with {len(targets_data)} targets")

        # Update Celery state
        self.update_state(
            state="PROGRESS",
            meta={
                "execution_id": execution_id,
                "state": "starting",
                "current": 0,
                "total": len(targets_data),
                "status": "Connecting to telescope...",
            },
        )

        # Connect to telescope
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Connect
            loop.run_until_complete(self.seestar_client.connect(telescope_host, telescope_port))

            logger.info(f"Connected to telescope at {telescope_host}:{telescope_port}")

            # Convert targets_data to ScheduledTarget objects
            targets = [ScheduledTarget(**t) for t in targets_data]

            # Create database records for each target
            for i, target in enumerate(targets):
                target_record = TelescopeExecutionTarget(
                    execution_id=execution.id,
                    target_index=i,
                    target_name=target.target.name,
                    catalog_id=target.target.catalog_id,
                    ra_hours=target.target.ra_hours,
                    dec_degrees=target.target.dec_degrees,
                    object_type=target.target.object_type,
                    magnitude=target.target.magnitude,
                    scheduled_start_time=target.start_time,
                    scheduled_duration_minutes=target.duration_minutes,
                    recommended_frames=target.recommended_frames,
                    recommended_exposure_seconds=target.recommended_exposure,
                )
                db.add(target_record)
            db.commit()

            # Set up progress callback to update database
            def progress_callback(progress):
                try:
                    # Update execution record
                    db.query(TelescopeExecution).filter(TelescopeExecution.id == execution.id).update(
                        {
                            "state": progress.state.value,
                            "current_target_index": progress.current_target_index,
                            "current_target_name": progress.current_target_name,
                            "current_phase": progress.current_phase,
                            "targets_completed": progress.targets_completed,
                            "targets_failed": progress.targets_failed,
                            "progress_percent": progress.progress_percent,
                            "elapsed_seconds": (
                                int(progress.elapsed_time.total_seconds()) if progress.elapsed_time else 0
                            ),
                            "estimated_remaining_seconds": (
                                int(progress.estimated_remaining.total_seconds())
                                if progress.estimated_remaining
                                else None
                            ),
                            "updated_at": datetime.utcnow(),
                        }
                    )
                    db.commit()

                    # Update Celery state for streaming
                    self.update_state(
                        state="PROGRESS",
                        meta={
                            "execution_id": execution_id,
                            "state": progress.state.value,
                            "current": progress.targets_completed,
                            "total": progress.total_targets,
                            "current_target": progress.current_target_name,
                            "current_phase": progress.current_phase,
                            "progress_percent": progress.progress_percent,
                            "elapsed_time": str(progress.elapsed_time) if progress.elapsed_time else None,
                            "estimated_remaining": (
                                str(progress.estimated_remaining) if progress.estimated_remaining else None
                            ),
                            "targets_completed": progress.targets_completed,
                            "targets_failed": progress.targets_failed,
                            "status": f"{progress.current_target_name or 'Processing'} - {progress.current_phase or 'Running'}",
                        },
                    )

                    logger.debug(
                        f"Progress update: {progress.state.value} - {progress.current_target_name} - {progress.progress_percent:.1f}%"
                    )

                except Exception as e:
                    logger.error(f"Error in progress callback: {e}")

            # Set progress callback on telescope service
            self.telescope_service.set_progress_callback(progress_callback)

            # Update execution state to running
            execution.state = "running"
            db.commit()

            # Notify session started
            _webhook_session_started(db, execution_id, saved_plan_id, targets_data)

            # Execute the plan (blocks until complete)
            final_progress = loop.run_until_complete(
                self.telescope_service.execute_plan(
                    execution_id=execution_id, targets=targets, configure_settings=True, park_when_done=park_when_done
                )
            )

            # Update final execution state
            execution.state = final_progress.state.value
            execution.completed_at = datetime.utcnow()
            execution.progress_percent = (
                100.0 if final_progress.state.value == "completed" else final_progress.progress_percent
            )
            execution.execution_result = {
                "state": final_progress.state.value,
                "targets_completed": final_progress.targets_completed,
                "targets_failed": final_progress.targets_failed,
                "total_targets": final_progress.total_targets,
                "final_time": str(final_progress.elapsed_time) if final_progress.elapsed_time else None,
            }
            if final_progress.errors:
                execution.error_log = [
                    {
                        "timestamp": err.timestamp.isoformat(),
                        "target": err.target_name,
                        "phase": err.phase,
                        "message": err.error_message,
                        "retries": err.retry_count,
                    }
                    for err in final_progress.errors
                ]
            db.commit()

            # Notify session completed
            _webhook_session_completed(db, execution_id, saved_plan_id, final_progress)

            logger.info(f"Execution {execution_id} completed: {final_progress.state.value}")

            return {
                "execution_id": execution_id,
                "state": final_progress.state.value,
                "targets_completed": final_progress.targets_completed,
                "targets_failed": final_progress.targets_failed,
                "total_targets": final_progress.total_targets,
            }

        finally:
            # Disconnect from telescope
            try:
                if self.seestar_client.connected:
                    loop.run_until_complete(self.seestar_client.disconnect())
            except Exception as e:
                logger.error(f"Error disconnecting telescope: {e}")

            loop.close()

    except Exception as e:
        logger.error(f"Execution {execution_id} failed: {e}", exc_info=True)

        # Update execution record with error
        try:
            execution.state = "error"
            execution.completed_at = datetime.utcnow()
            execution.error_log = [{"error": str(e), "timestamp": datetime.utcnow().isoformat()}]
            db.commit()
        except Exception as db_err:
            logger.error(f"Failed to write error state to DB for execution {execution_id}: {db_err}")

        # Update Celery state
        self.update_state(
            state="FAILURE", meta={"execution_id": execution_id, "error": str(e), "exc_type": type(e).__name__}
        )

        raise

    finally:
        db.close()


@celery_app.task(name="abort_observation_plan")
def abort_observation_plan_task(execution_id: str):
    """
    Abort a running observation plan.

    Args:
        execution_id: Execution ID to abort
    """
    db = SessionLocal()

    try:
        execution = db.query(TelescopeExecution).filter(TelescopeExecution.execution_id == execution_id).first()

        if not execution:
            logger.warning(f"Execution {execution_id} not found")
            return {"success": False, "error": "Execution not found"}

        if execution.state not in ["starting", "running"]:
            logger.warning(f"Execution {execution_id} is not running (state: {execution.state})")
            return {"success": False, "error": f"Execution is {execution.state}"}

        # Revoke the Celery task
        celery_app.control.revoke(execution.celery_task_id, terminate=True)

        # Update execution state
        execution.state = "aborted"
        execution.completed_at = datetime.utcnow()
        db.commit()

        logger.info(f"Aborted execution {execution_id}")

        return {"success": True, "execution_id": execution_id}

    except Exception as e:
        logger.error(f"Error aborting execution {execution_id}: {e}")
        return {"success": False, "error": str(e)}

    finally:
        db.close()
