"""Tests for object tracking API endpoints."""

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
    mock_client.start_track_object = AsyncMock(return_value=True)
    mock_client.stop_track_object = AsyncMock(return_value=True)
    return mock_client


def test_start_tracking_satellite(mock_seestar_client):
    """Test POST /api/telescope/tracking/start endpoint with satellite."""
    with patch("app.api.telescope.seestar_client", mock_seestar_client):
        response = client.post("/api/telescope/tracking/start", json={"object_type": "satellite", "object_id": "25544"})

        assert response.status_code == 200
        assert response.json()["status"] == "tracking_started"
        assert response.json()["object_type"] == "satellite"
        assert response.json()["object_id"] == "25544"
        mock_seestar_client.start_track_object.assert_called_once_with(object_type="satellite", object_id="25544")


def test_start_tracking_comet(mock_seestar_client):
    """Test POST /api/telescope/tracking/start endpoint with comet."""
    with patch("app.api.telescope.seestar_client", mock_seestar_client):
        response = client.post("/api/telescope/tracking/start", json={"object_type": "comet", "object_id": "C/2023 A3"})

        assert response.status_code == 200
        assert response.json()["status"] == "tracking_started"
        assert response.json()["object_type"] == "comet"
        assert response.json()["object_id"] == "C/2023 A3"
        mock_seestar_client.start_track_object.assert_called_once_with(object_type="comet", object_id="C/2023 A3")


def test_start_tracking_asteroid(mock_seestar_client):
    """Test POST /api/telescope/tracking/start endpoint with asteroid."""
    with patch("app.api.telescope.seestar_client", mock_seestar_client):
        response = client.post("/api/telescope/tracking/start", json={"object_type": "asteroid", "object_id": "433"})

        assert response.status_code == 200
        assert response.json()["status"] == "tracking_started"
        assert response.json()["object_type"] == "asteroid"
        assert response.json()["object_id"] == "433"
        mock_seestar_client.start_track_object.assert_called_once_with(object_type="asteroid", object_id="433")


def test_start_tracking_missing_object_type(mock_seestar_client):
    """Test POST /api/telescope/tracking/start with missing object_type."""
    with patch("app.api.telescope.seestar_client", mock_seestar_client):
        response = client.post("/api/telescope/tracking/start", json={"object_id": "25544"})

        assert response.status_code == 422  # Validation error


def test_start_tracking_missing_object_id(mock_seestar_client):
    """Test POST /api/telescope/tracking/start with missing object_id."""
    with patch("app.api.telescope.seestar_client", mock_seestar_client):
        response = client.post("/api/telescope/tracking/start", json={"object_type": "satellite"})

        assert response.status_code == 422  # Validation error


def test_start_tracking_not_connected():
    """Test start tracking when telescope is not connected."""
    with patch("app.api.telescope.seestar_client", None):
        response = client.post("/api/telescope/tracking/start", json={"object_type": "satellite", "object_id": "25544"})

        assert response.status_code == 503
        assert "not connected" in response.json()["detail"].lower()


def test_start_tracking_failure(mock_seestar_client):
    """Test start tracking when the operation fails."""
    mock_seestar_client.start_track_object = AsyncMock(return_value=False)

    with patch("app.api.telescope.seestar_client", mock_seestar_client):
        response = client.post("/api/telescope/tracking/start", json={"object_type": "satellite", "object_id": "25544"})

        assert response.status_code == 500
        assert "Failed to start tracking" in response.json()["detail"]


def test_stop_tracking(mock_seestar_client):
    """Test POST /api/telescope/tracking/stop endpoint."""
    with patch("app.api.telescope.seestar_client", mock_seestar_client):
        response = client.post("/api/telescope/tracking/stop")

        assert response.status_code == 200
        assert response.json()["status"] == "tracking_stopped"
        mock_seestar_client.stop_track_object.assert_called_once()


def test_stop_tracking_not_connected():
    """Test stop tracking when telescope is not connected."""
    with patch("app.api.telescope.seestar_client", None):
        response = client.post("/api/telescope/tracking/stop")

        assert response.status_code == 503
        assert "not connected" in response.json()["detail"].lower()


def test_stop_tracking_failure(mock_seestar_client):
    """Test stop tracking when the operation fails."""
    mock_seestar_client.stop_track_object = AsyncMock(return_value=False)

    with patch("app.api.telescope.seestar_client", mock_seestar_client):
        response = client.post("/api/telescope/tracking/stop")

        assert response.status_code == 500
        assert "Failed to stop tracking" in response.json()["detail"]
