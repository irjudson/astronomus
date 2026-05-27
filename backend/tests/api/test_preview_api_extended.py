"""Extended tests for preview router — covering snapshot and stream endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_current_telescope
from app.main import app

client = TestClient(app)


def _make_mock_service(frame_bytes=None, is_running=True):
    svc = MagicMock()
    svc.is_running = is_running
    svc.latest_frame = frame_bytes
    svc.get_latest_frame_jpeg.return_value = frame_bytes
    return svc


# ---------------------------------------------------------------------------
# /snapshot endpoint
# ---------------------------------------------------------------------------


def test_snapshot_returns_jpeg():
    mock_frame = b"\xff\xd8\xff\xe0" + b"snapshot-jpeg"
    mock_svc = _make_mock_service(frame_bytes=mock_frame)
    mock_client = MagicMock()
    app.dependency_overrides[get_current_telescope] = lambda: mock_client

    try:
        with patch("app.services.rtmp_preview_service.get_preview_service", return_value=mock_svc):
            resp = client.get("/api/telescope/preview/snapshot")

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/jpeg"
        assert resp.content.startswith(b"\xff\xd8")
    finally:
        app.dependency_overrides.clear()


def test_snapshot_503_when_no_frames():
    mock_svc = _make_mock_service(frame_bytes=None)
    mock_client = MagicMock()
    app.dependency_overrides[get_current_telescope] = lambda: mock_client

    try:
        with patch("app.services.rtmp_preview_service.get_preview_service", return_value=mock_svc):
            resp = client.get("/api/telescope/preview/snapshot")

        assert resp.status_code == 503
        assert "no preview frames" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_snapshot_no_telescope_returns_400():
    def mock_no_telescope():
        raise HTTPException(status_code=400, detail="No telescope connected")

    app.dependency_overrides[get_current_telescope] = mock_no_telescope
    try:
        resp = client.get("/api/telescope/preview/snapshot")
        assert resp.status_code == 400
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /frame — service not running (starts it)
# ---------------------------------------------------------------------------


def test_frame_starts_service_when_not_running():
    mock_frame = b"\xff\xd8\xff\xe0" + b"started"
    mock_svc = _make_mock_service(frame_bytes=mock_frame, is_running=False)
    mock_client = MagicMock()
    app.dependency_overrides[get_current_telescope] = lambda: mock_client

    try:
        with patch("app.services.rtmp_preview_service.get_preview_service", return_value=mock_svc):
            resp = client.get("/api/telescope/preview/frame")

        assert resp.status_code == 200
        mock_svc.start.assert_called_once()
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /frame — frame arrives after polling
# ---------------------------------------------------------------------------


def test_frame_polls_until_frame_available():
    """Simulate latest_frame starting None, then becoming available after poll."""
    mock_frame = b"\xff\xd8\xff\xe0" + b"polled"

    call_count = [0]

    class PollingSvc:
        is_running = True

        @property
        def latest_frame(self):
            call_count[0] += 1
            # Return None for first 2 polls, then a frame
            if call_count[0] < 3:
                return None
            return mock_frame

        def get_latest_frame_jpeg(self, quality=85):
            return mock_frame

    mock_client = MagicMock()
    app.dependency_overrides[get_current_telescope] = lambda: mock_client

    try:
        with patch("app.services.rtmp_preview_service.get_preview_service", return_value=PollingSvc()):
            resp = client.get("/api/telescope/preview/frame")

        assert resp.status_code == 200
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# /stream endpoint — 400 when no telescope
# ---------------------------------------------------------------------------


def test_stream_no_telescope_returns_400():
    """Verify stream endpoint returns 400 when telescope not connected."""

    def mock_no_telescope():
        raise HTTPException(status_code=400, detail="No telescope connected")

    app.dependency_overrides[get_current_telescope] = mock_no_telescope
    try:
        resp = client.get("/api/telescope/preview/stream")
        assert resp.status_code == 400
    finally:
        app.dependency_overrides.clear()
