"""Webhook notification service for plan events."""

import logging
import os
from datetime import datetime
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for sending webhook notifications about plan events."""

    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize webhook service with configuration.

        Args:
            webhook_url: Webhook URL (optional, defaults to WEBHOOK_URL env var)
        """
        self.webhook_url = webhook_url or os.getenv("WEBHOOK_URL")
        self.timeout = 5  # seconds
        self.max_retries = 2

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
                logger.info(f"Webhook sent successfully to {self.webhook_url}")
                return True
            except requests.exceptions.RequestException as e:
                logger.warning(f"Webhook request failed: {e} (attempt {attempt + 1}/{self.max_retries + 1})")
                if attempt == self.max_retries:
                    logger.error(f"Webhook failed after {self.max_retries + 1} attempts: {e}")
                    return False
            except Exception as e:
                logger.error(f"Unexpected error sending webhook: {e}")
                return False
        return False

    def send_plan_created_notification(
        self,
        plan_id: int,
        plan_name: str,
        observing_date: str,
        target_names: List[str],
        session_start: Optional[str] = None,
        session_end: Optional[str] = None,
    ) -> bool:
        """
        Send webhook notification when a plan is created.

        Args:
            plan_id: Database ID of the created plan
            plan_name: Name of the plan (e.g., "2024-12-25-plan")
            observing_date: Date of observation (YYYY-MM-DD)
            target_names: List of target names in the plan
            session_start: Session start time (ISO format with timezone)
            session_end: Session end time (ISO format with timezone)

        Returns:
            True if webhook sent successfully, False otherwise
        """
        if not self.webhook_url:
            logger.debug("No webhook URL configured, skipping notification")
            return False

        # Build webhook payload
        payload = {
            "event": "plan_created",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "plan": {
                "id": plan_id,
                "name": plan_name,
                "observing_date": observing_date,
                "target_count": len(target_names),
                "targets": target_names,
            },
        }

        # Add optional session times if provided
        if session_start:
            payload["plan"]["session_start"] = session_start
        if session_end:
            payload["plan"]["session_end"] = session_end

        return self._post(payload)

    def send_scope_unreachable_notification(self, plan_name: str) -> bool:
        """Send webhook notification when telescope is unreachable after max retries.

        Args:
            plan_name: Name of the plan that could not be executed

        Returns:
            True if webhook sent successfully, False otherwise
        """
        if not self.webhook_url:
            logger.debug("No webhook URL configured, skipping scope_unreachable notification")
            return False

        payload = {
            "event": "scope_unreachable",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "plan_name": plan_name,
            "message": f"Auto-execute aborted: telescope unreachable for plan '{plan_name}'",
        }

        return self._post(payload)

    def send_weather_abort_notification(
        self,
        execution_id: str,
        reason: str,
        targets_completed: int,
    ) -> bool:
        """Send webhook notification when an execution is aborted due to weather.

        Args:
            execution_id: ID of the aborted execution
            reason: Human-readable abort reason (e.g. "Rain detected (0.12 in/hr)")
            targets_completed: Number of targets completed before abort

        Returns:
            True if webhook sent successfully, False otherwise
        """
        if not self.webhook_url:
            logger.debug("No webhook URL configured, skipping weather_abort notification")
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

    def send_session_started_notification(
        self,
        execution_id: str,
        plan_name: str,
        target_count: int,
        target_names: List[str],
    ) -> bool:
        """Send webhook notification when a telescope session begins executing.

        Args:
            execution_id: Unique execution ID
            plan_name: Name or label of the plan being executed
            target_count: Total number of targets in the session
            target_names: List of target names

        Returns:
            True if webhook sent successfully, False otherwise
        """
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
        """Send webhook notification when a telescope session finishes.

        Args:
            execution_id: Unique execution ID
            plan_name: Name or label of the plan that was executed
            state: Final state string (e.g. "completed", "aborted", "error")
            targets_completed: Number of targets successfully completed
            targets_failed: Number of targets that failed
            total_targets: Total targets in the session
            duration_str: Optional human-readable elapsed duration

        Returns:
            True if webhook sent successfully, False otherwise
        """
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

    def is_configured(self) -> bool:
        """Check if webhook URL is configured."""
        return bool(self.webhook_url)
