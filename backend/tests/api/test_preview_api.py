from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_current_telescope
from app.main import app

client = TestClient(app)


def _make_mock_service(frame_bytes=None):
    """Create a mock RTMPPreviewService."""
    svc = MagicMock()
    svc.is_running = True
    svc.latest_frame = frame_bytes  # None triggers the poll loop
    svc.get_latest_frame_jpeg.return_value = frame_bytes
    return svc


def test_get_preview_frame_returns_jpeg():
    """Test GET /api/telescope/preview/frame returns JPEG image."""
    mock_frame = b"\xff\xd8\xff\xe0" + b"fake jpeg data"
    mock_svc = _make_mock_service(frame_bytes=mock_frame)

    mock_client = MagicMock()
    app.dependency_overrides[get_current_telescope] = lambda: mock_client

    try:
        with patch("app.services.rtmp_preview_service.get_preview_service", return_value=mock_svc):
            response = client.get("/api/telescope/preview/frame")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert len(response.content) > 10
        assert response.content.startswith(b"\xff\xd8")  # JPEG magic bytes
    finally:
        app.dependency_overrides.clear()


def test_get_preview_frame_when_not_connected():
    """Test endpoint returns 400 when telescope not connected."""

    def mock_no_telescope():
        raise HTTPException(status_code=400, detail="No telescope connected")

    app.dependency_overrides[get_current_telescope] = mock_no_telescope

    try:
        response = client.get("/api/telescope/preview/frame")

        assert response.status_code == 400
        assert "telescope" in response.json()["detail"].lower()
        assert "connected" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_get_preview_frame_when_no_frames():
    """Test endpoint returns 503 when no preview frames available."""
    mock_svc = _make_mock_service(frame_bytes=None)

    mock_client = MagicMock()
    app.dependency_overrides[get_current_telescope] = lambda: mock_client

    try:
        with patch("app.services.rtmp_preview_service.get_preview_service", return_value=mock_svc):
            response = client.get("/api/telescope/preview/frame")

        assert response.status_code == 503
        assert "no preview frames" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()
