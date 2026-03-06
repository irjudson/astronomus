"""Tests for polar alignment API endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.clients.seestar_client import SeestarClient
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_seestar_client():
    """Create mock Seestar client for polar alignment tests."""
    client = AsyncMock(spec=SeestarClient)
    client.connected = True
    client.start_polar_align = AsyncMock(return_value=True)
    client.stop_polar_align = AsyncMock(return_value=True)
    client.pause_polar_align = AsyncMock(return_value=True)
    return client


class TestPolarAlignmentEndpoints:
    """Test polar alignment control endpoints."""

    def test_start_polar_align_success(self, client, mock_seestar_client):
        """Test successful polar alignment start."""
        with patch("app.api.telescope.seestar_client", mock_seestar_client):
            response = client.post("/api/telescope/polar-align/start")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "active"
            assert "message" in data
            assert "started" in data["message"].lower()
            mock_seestar_client.start_polar_align.assert_called_once()

    def test_start_polar_align_failure(self, client, mock_seestar_client):
        """Test failed polar alignment start."""
        mock_seestar_client.start_polar_align = AsyncMock(return_value=False)

        with patch("app.api.telescope.seestar_client", mock_seestar_client):
            response = client.post("/api/telescope/polar-align/start")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "failed" in data["message"].lower()
            mock_seestar_client.start_polar_align.assert_called_once()

    def test_start_polar_align_not_connected(self, client):
        """Test polar alignment start when telescope not connected."""
        with patch("app.api.telescope.seestar_client", None):
            response = client.post("/api/telescope/polar-align/start")

            assert response.status_code == 400
            assert "not connected" in response.json()["detail"].lower()

    def test_start_polar_align_exception(self, client, mock_seestar_client):
        """Test polar alignment start with exception."""
        mock_seestar_client.start_polar_align = AsyncMock(side_effect=Exception("Alignment system error"))

        with patch("app.api.telescope.seestar_client", mock_seestar_client):
            response = client.post("/api/telescope/polar-align/start")

            assert response.status_code == 500
            assert "Alignment system error" in response.json()["detail"]

    def test_stop_polar_align_success(self, client, mock_seestar_client):
        """Test successful polar alignment stop."""
        with patch("app.api.telescope.seestar_client", mock_seestar_client):
            response = client.post("/api/telescope/polar-align/stop")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "stopped"
            assert "message" in data
            assert "stopped" in data["message"].lower()
            mock_seestar_client.stop_polar_align.assert_called_once()

    def test_stop_polar_align_failure(self, client, mock_seestar_client):
        """Test failed polar alignment stop."""
        mock_seestar_client.stop_polar_align = AsyncMock(return_value=False)

        with patch("app.api.telescope.seestar_client", mock_seestar_client):
            response = client.post("/api/telescope/polar-align/stop")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "failed" in data["message"].lower()
            mock_seestar_client.stop_polar_align.assert_called_once()

    def test_stop_polar_align_not_connected(self, client):
        """Test polar alignment stop when telescope not connected."""
        with patch("app.api.telescope.seestar_client", None):
            response = client.post("/api/telescope/polar-align/stop")

            assert response.status_code == 400
            assert "not connected" in response.json()["detail"].lower()

    def test_stop_polar_align_exception(self, client, mock_seestar_client):
        """Test polar alignment stop with exception."""
        mock_seestar_client.stop_polar_align = AsyncMock(side_effect=Exception("Stop command failed"))

        with patch("app.api.telescope.seestar_client", mock_seestar_client):
            response = client.post("/api/telescope/polar-align/stop")

            assert response.status_code == 500
            assert "Stop command failed" in response.json()["detail"]

    def test_pause_polar_align_success(self, client, mock_seestar_client):
        """Test successful polar alignment pause."""
        with patch("app.api.telescope.seestar_client", mock_seestar_client):
            response = client.post("/api/telescope/polar-align/pause")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "paused"
            assert "message" in data
            assert "paused" in data["message"].lower()
            mock_seestar_client.pause_polar_align.assert_called_once()

    def test_pause_polar_align_failure(self, client, mock_seestar_client):
        """Test failed polar alignment pause."""
        mock_seestar_client.pause_polar_align = AsyncMock(return_value=False)

        with patch("app.api.telescope.seestar_client", mock_seestar_client):
            response = client.post("/api/telescope/polar-align/pause")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "error"
            assert "failed" in data["message"].lower()
            mock_seestar_client.pause_polar_align.assert_called_once()

    def test_pause_polar_align_not_connected(self, client):
        """Test polar alignment pause when telescope not connected."""
        with patch("app.api.telescope.seestar_client", None):
            response = client.post("/api/telescope/polar-align/pause")

            assert response.status_code == 400
            assert "not connected" in response.json()["detail"].lower()

    def test_pause_polar_align_exception(self, client, mock_seestar_client):
        """Test polar alignment pause with exception."""
        mock_seestar_client.pause_polar_align = AsyncMock(side_effect=Exception("Pause command failed"))

        with patch("app.api.telescope.seestar_client", mock_seestar_client):
            response = client.post("/api/telescope/polar-align/pause")

            assert response.status_code == 500
            assert "Pause command failed" in response.json()["detail"]
