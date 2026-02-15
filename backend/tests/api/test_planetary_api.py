"""Tests for planetary imaging API endpoints."""

from unittest.mock import AsyncMock

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
    """Create mock Seestar client."""
    mock_client = AsyncMock(spec=SeestarClient)
    mock_client.start_scan_planet = AsyncMock(return_value=["Jupiter", "Saturn", "Mars"])
    mock_client.start_planet_mode = AsyncMock(return_value=True)
    mock_client.stop_planet_mode = AsyncMock(return_value=True)
    return mock_client


class TestPlanetaryScanEndpoint:
    """Test planetary scan endpoint."""

    def test_scan_planets_success(self, client, mock_seestar_client):
        """Test successful planetary scan."""
        from app.api import routes

        # Override dependency
        app.dependency_overrides[routes.get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/scan")

            assert response.status_code == 200
            data = response.json()
            assert "planets" in data
            assert data["planets"] == ["Jupiter", "Saturn", "Mars"]
            mock_seestar_client.start_scan_planet.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_scan_planets_empty_result(self, client, mock_seestar_client):
        """Test planetary scan with no planets found."""
        from app.api import routes

        mock_seestar_client.start_scan_planet = AsyncMock(return_value=None)

        # Override dependency
        app.dependency_overrides[routes.get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/scan")

            assert response.status_code == 200
            data = response.json()
            assert "planets" in data
            assert data["planets"] == []
        finally:
            app.dependency_overrides.clear()

    def test_scan_planets_no_telescope(self, client):
        """Test planetary scan when no telescope is connected."""
        from app.api import routes

        # Override dependency to return None
        app.dependency_overrides[routes.get_current_telescope] = lambda: None

        try:
            response = client.post("/api/telescope/imaging/planet/scan")

            assert response.status_code == 503
            assert "not connected" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    def test_scan_planets_client_error(self, client, mock_seestar_client):
        """Test planetary scan when client raises error."""
        from app.api import routes

        mock_seestar_client.start_scan_planet = AsyncMock(side_effect=Exception("Communication error"))

        # Override dependency
        app.dependency_overrides[routes.get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/scan")

            assert response.status_code == 500
            assert "scan planets" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()


class TestPlanetaryStartEndpoint:
    """Test planetary imaging start endpoint."""

    def test_start_planetary_imaging_success(self, client, mock_seestar_client):
        """Test successful start of planetary imaging."""
        from app.api import routes

        # Override dependency
        app.dependency_overrides[routes.get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/start")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "message" in data
            mock_seestar_client.start_planet_mode.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_start_planetary_imaging_failure(self, client, mock_seestar_client):
        """Test start planetary imaging when operation fails."""
        from app.api import routes

        mock_seestar_client.start_planet_mode = AsyncMock(return_value=False)

        # Override dependency
        app.dependency_overrides[routes.get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/start")

            assert response.status_code == 500
            assert "failed to start" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    def test_start_planetary_imaging_no_telescope(self, client):
        """Test start planetary imaging when no telescope is connected."""
        from app.api import routes

        # Override dependency to return None
        app.dependency_overrides[routes.get_current_telescope] = lambda: None

        try:
            response = client.post("/api/telescope/imaging/planet/start")

            assert response.status_code == 503
            assert "not connected" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    def test_start_planetary_imaging_client_error(self, client, mock_seestar_client):
        """Test start planetary imaging when client raises error."""
        from app.api import routes

        mock_seestar_client.start_planet_mode = AsyncMock(side_effect=Exception("Hardware error"))

        # Override dependency
        app.dependency_overrides[routes.get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/start")

            assert response.status_code == 500
            assert "start planetary imaging" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()


class TestPlanetaryStopEndpoint:
    """Test planetary imaging stop endpoint."""

    def test_stop_planetary_imaging_success(self, client, mock_seestar_client):
        """Test successful stop of planetary imaging."""
        from app.api import routes

        # Override dependency
        app.dependency_overrides[routes.get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/stop")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "message" in data
            mock_seestar_client.stop_planet_mode.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_stop_planetary_imaging_failure(self, client, mock_seestar_client):
        """Test stop planetary imaging when operation fails."""
        from app.api import routes

        mock_seestar_client.stop_planet_mode = AsyncMock(return_value=False)

        # Override dependency
        app.dependency_overrides[routes.get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/stop")

            assert response.status_code == 500
            assert "failed to stop" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    def test_stop_planetary_imaging_no_telescope(self, client):
        """Test stop planetary imaging when no telescope is connected."""
        from app.api import routes

        # Override dependency to return None
        app.dependency_overrides[routes.get_current_telescope] = lambda: None

        try:
            response = client.post("/api/telescope/imaging/planet/stop")

            assert response.status_code == 503
            assert "not connected" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    def test_stop_planetary_imaging_client_error(self, client, mock_seestar_client):
        """Test stop planetary imaging when client raises error."""
        from app.api import routes

        mock_seestar_client.stop_planet_mode = AsyncMock(side_effect=Exception("Hardware error"))

        # Override dependency
        app.dependency_overrides[routes.get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/stop")

            assert response.status_code == 500
            assert "stop planetary imaging" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()
