"""Unit tests for WebhookService."""

from unittest.mock import MagicMock, patch


def test_is_configured_false_when_no_url():
    from app.services.webhook_service import WebhookService

    svc = WebhookService(webhook_url=None)
    with patch.dict("os.environ", {}, clear=True):
        svc2 = WebhookService(webhook_url="")
    assert svc.is_configured() is False
    assert svc2.is_configured() is False


def test_is_configured_true_when_url_set():
    from app.services.webhook_service import WebhookService

    svc = WebhookService(webhook_url="https://hooks.example.com")
    assert svc.is_configured() is True


def test_post_returns_true_on_http_200():
    from app.services.webhook_service import WebhookService

    svc = WebhookService(webhook_url="https://hooks.example.com")
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None

    with patch("app.services.webhook_service.requests.post", return_value=mock_resp) as mock_post:
        result = svc._post({"event": "test"})

    assert result is True
    mock_post.assert_called_once()


def test_post_returns_false_after_max_retries():
    from app.services.webhook_service import WebhookService
    import requests as req_lib

    svc = WebhookService(webhook_url="https://hooks.example.com")
    svc.max_retries = 2

    with patch(
        "app.services.webhook_service.requests.post",
        side_effect=req_lib.exceptions.ConnectionError("refused"),
    ) as mock_post:
        result = svc._post({"event": "test"})

    assert result is False
    assert mock_post.call_count == 3  # initial + 2 retries


def test_send_plan_created_calls_post_with_correct_shape():
    from app.services.webhook_service import WebhookService

    svc = WebhookService(webhook_url="https://hooks.example.com")

    with patch.object(svc, "_post", return_value=True) as mock_post:
        result = svc.send_plan_created_notification(
            plan_id=1,
            plan_name="2026-05-26-plan",
            observing_date="2026-05-26",
            target_names=["M31", "NGC 891"],
            session_start="2026-05-26T22:00:00",
            session_end="2026-05-27T04:00:00",
        )

    assert result is True
    payload = mock_post.call_args[0][0]
    assert payload["event"] == "plan_created"
    assert payload["plan"]["id"] == 1
    assert payload["plan"]["name"] == "2026-05-26-plan"
    assert payload["plan"]["target_count"] == 2
    assert payload["plan"]["session_start"] == "2026-05-26T22:00:00"


def test_send_plan_created_noop_when_not_configured():
    from app.services.webhook_service import WebhookService

    svc = WebhookService(webhook_url="")

    with patch.object(svc, "_post") as mock_post:
        result = svc.send_plan_created_notification(
            plan_id=1, plan_name="x", observing_date="2026-05-26", target_names=[]
        )

    assert result is False
    mock_post.assert_not_called()


def test_send_session_started_calls_post():
    from app.services.webhook_service import WebhookService

    svc = WebhookService(webhook_url="https://hooks.example.com")

    with patch.object(svc, "_post", return_value=True) as mock_post:
        result = svc.send_session_started_notification(
            execution_id="exec-1",
            plan_name="my-plan",
            target_count=3,
            target_names=["M31", "M33", "M42"],
        )

    assert result is True
    payload = mock_post.call_args[0][0]
    assert payload["event"] == "session_started"
    assert payload["execution"]["target_count"] == 3


def test_send_session_started_noop_when_not_configured():
    from app.services.webhook_service import WebhookService

    svc = WebhookService(webhook_url="")

    with patch.object(svc, "_post") as mock_post:
        result = svc.send_session_started_notification(
            execution_id="e", plan_name="p", target_count=0, target_names=[]
        )

    assert result is False
    mock_post.assert_not_called()


def test_send_session_completed_calls_post():
    from app.services.webhook_service import WebhookService

    svc = WebhookService(webhook_url="https://hooks.example.com")

    with patch.object(svc, "_post", return_value=True) as mock_post:
        result = svc.send_session_completed_notification(
            execution_id="exec-2",
            plan_name="my-plan",
            state="completed",
            targets_completed=5,
            targets_failed=0,
            total_targets=5,
            duration_str="2:00:00",
        )

    assert result is True
    payload = mock_post.call_args[0][0]
    assert payload["event"] == "session_completed"
    assert payload["execution"]["state"] == "completed"
    assert payload["execution"]["targets_completed"] == 5
    assert payload["execution"]["duration"] == "2:00:00"


def test_send_session_completed_noop_when_not_configured():
    from app.services.webhook_service import WebhookService

    svc = WebhookService(webhook_url="")

    with patch.object(svc, "_post") as mock_post:
        result = svc.send_session_completed_notification(
            execution_id="e",
            plan_name="p",
            state="completed",
            targets_completed=0,
            targets_failed=0,
            total_targets=0,
        )

    assert result is False
    mock_post.assert_not_called()
