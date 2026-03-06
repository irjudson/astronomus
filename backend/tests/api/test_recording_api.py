"""Tests for video recording API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.clients.seestar_client import SeestarClient
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_seestar_client():
    """Create mock Seestar client."""
    mock_client = AsyncMock(spec=SeestarClient)
    mock_client.connected = True
    mock_client.start_record_avi = AsyncMock(return_value=True)
    mock_client.stop_record_avi = AsyncMock(return_value=True)
    return mock_client


def test_start_recording(mock_seestar_client):
    """Test POST /api/telescope/recording/start endpoint."""
    with patch("app.api.telescope.seestar_client", mock_seestar_client):
        response = client.post("/api/telescope/recording/start", json={"filename": "test_video"})

        assert response.status_code == 200
        assert response.json()["status"] == "recording_started"
        assert response.json()["filename"] == "test_video"
        mock_seestar_client.start_record_avi.assert_called_once_with(filename="test_video")


def test_start_recording_without_filename(mock_seestar_client):
    """Test POST /api/telescope/recording/start without filename."""
    with patch("app.api.telescope.seestar_client", mock_seestar_client):
        response = client.post("/api/telescope/recording/start", json={})

        assert response.status_code == 200
        assert response.json()["status"] == "recording_started"
        assert response.json()["filename"] == "auto"
        mock_seestar_client.start_record_avi.assert_called_once_with(filename=None)


def test_stop_recording(mock_seestar_client):
    """Test POST /api/telescope/recording/stop endpoint."""
    with patch("app.api.telescope.seestar_client", mock_seestar_client):
        response = client.post("/api/telescope/recording/stop")

        assert response.status_code == 200
        assert response.json()["status"] == "recording_stopped"
        mock_seestar_client.stop_record_avi.assert_called_once()


def test_start_recording_not_connected():
    """Test start recording when telescope is not connected."""
    with patch("app.api.telescope.seestar_client", None):
        response = client.post("/api/telescope/recording/start", json={"filename": "test_video"})

        assert response.status_code == 400
        assert "not connected" in response.json()["detail"].lower()


def test_stop_recording_not_connected():
    """Test stop recording when telescope is not connected."""
    with patch("app.api.telescope.seestar_client", None):
        response = client.post("/api/telescope/recording/stop")

        assert response.status_code == 400
        assert "not connected" in response.json()["detail"].lower()
