from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_preview_frame_returns_jpeg():
    """Test GET /api/telescope/preview/frame returns JPEG image."""
    # Mock telescope connected and frame available
    mock_frame = b"\xff\xd8\xff\xe0" + b"fake jpeg data"

    with patch("app.routers.preview.get_seestar_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.connected = True
        mock_client.get_latest_preview_frame = AsyncMock(return_value=mock_frame)
        mock_get_client.return_value = mock_client

        response = client.get("/api/telescope/preview/frame")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 10
    assert response.content.startswith(b"\xff\xd8")  # JPEG magic bytes


def test_get_preview_frame_when_not_connected():
    """Test endpoint returns 400 when telescope not connected."""
    with patch("app.routers.preview.get_seestar_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.connected = False
        mock_get_client.return_value = mock_client

        response = client.get("/api/telescope/preview/frame")

    assert response.status_code == 400
    assert "not connected" in response.json()["detail"].lower()


def test_get_preview_frame_when_no_frames():
    """Test endpoint returns 503 when no preview frames available."""
    with patch("app.routers.preview.get_seestar_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_client.connected = True
        mock_client.get_latest_preview_frame = AsyncMock(return_value=None)
        mock_get_client.return_value = mock_client

        response = client.get("/api/telescope/preview/frame")

    assert response.status_code == 503
    assert "no preview frames" in response.json()["detail"].lower()
