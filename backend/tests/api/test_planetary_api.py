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
    mock_client.start_planet_stack = AsyncMock(return_value=True)
    mock_client.stop_planet_stack = AsyncMock(return_value=True)
    return mock_client


class TestPlanetaryScanEndpoint:
    """Test planetary scan endpoint.

    Note: scan_planets uses astronomical calculations (not telescope) to return
    all major solar system objects available for imaging.
    """

    def test_scan_planets_returns_all_planets(self, client):
        """Test that scan returns all major planets and Moon."""
        response = client.post("/api/telescope/imaging/planet/scan")

        assert response.status_code == 200
        data = response.json()
        assert "planets" in data
        planets = data["planets"]
        # Should return major planets and Moon (Sun excluded for safety)
        assert len(planets) >= 7
        assert "Jupiter" in planets
        assert "Saturn" in planets
        assert "Mars" in planets
        assert "Moon" in planets
        # Sun excluded for safety
        assert "Sun" not in planets

    def test_scan_planets_works_without_telescope(self, client):
        """Test that planetary scan works without telescope connection.

        Scan uses astronomical calculations, not telescope, so it always works.
        """
        response = client.post("/api/telescope/imaging/planet/scan")

        assert response.status_code == 200
        data = response.json()
        assert "planets" in data
        assert len(data["planets"]) > 0


class TestPlanetaryStartEndpoint:
    """Test planetary imaging start endpoint."""

    def test_start_planetary_imaging_success(self, client, mock_seestar_client):
        """Test successful start of planetary imaging."""
        from app.api.deps import get_current_telescope

        app.dependency_overrides[get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/start?planet_name=Jupiter")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "message" in data
            mock_seestar_client.start_planet_stack.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_start_planetary_imaging_failure(self, client, mock_seestar_client):
        """Test start planetary imaging when operation fails."""
        from app.api.deps import get_current_telescope

        mock_seestar_client.start_planet_stack = AsyncMock(return_value=False)
        app.dependency_overrides[get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/start?planet_name=Jupiter")

            assert response.status_code == 500
            assert "failed to start" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    def test_start_planetary_imaging_no_telescope(self, client):
        """Test start planetary imaging when no telescope is connected."""
        response = client.post("/api/telescope/imaging/planet/start?planet_name=Jupiter")

        assert response.status_code == 503
        assert "not connected" in response.json()["detail"].lower()

    def test_start_planetary_imaging_missing_planet_name(self, client, mock_seestar_client):
        """Test start planetary imaging without required planet_name parameter."""
        from app.api.deps import get_current_telescope

        app.dependency_overrides[get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/start")

            assert response.status_code == 422  # Unprocessable Entity - missing required param
        finally:
            app.dependency_overrides.clear()

    def test_start_planetary_imaging_client_error(self, client, mock_seestar_client):
        """Test start planetary imaging when client raises error."""
        from app.api.deps import get_current_telescope

        mock_seestar_client.start_planet_stack = AsyncMock(side_effect=Exception("Hardware error"))
        app.dependency_overrides[get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/start?planet_name=Jupiter")

            assert response.status_code == 500
            assert "failed to start planetary imaging" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()


class TestPlanetaryStopEndpoint:
    """Test planetary imaging stop endpoint."""

    def test_stop_planetary_imaging_success(self, client, mock_seestar_client):
        """Test successful stop of planetary imaging."""
        from app.api.deps import get_current_telescope

        app.dependency_overrides[get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/stop")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "message" in data
            mock_seestar_client.stop_planet_stack.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_stop_planetary_imaging_failure(self, client, mock_seestar_client):
        """Test stop planetary imaging when operation fails."""
        from app.api.deps import get_current_telescope

        mock_seestar_client.stop_planet_stack = AsyncMock(return_value=False)
        app.dependency_overrides[get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/stop")

            assert response.status_code == 500
            assert "failed to stop" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()

    def test_stop_planetary_imaging_no_telescope(self, client):
        """Test stop planetary imaging when no telescope is connected."""
        response = client.post("/api/telescope/imaging/planet/stop")

        assert response.status_code == 503
        assert "not connected" in response.json()["detail"].lower()

    def test_stop_planetary_imaging_client_error(self, client, mock_seestar_client):
        """Test stop planetary imaging when client raises error."""
        from app.api.deps import get_current_telescope

        mock_seestar_client.stop_planet_stack = AsyncMock(side_effect=Exception("Hardware error"))
        app.dependency_overrides[get_current_telescope] = lambda: mock_seestar_client

        try:
            response = client.post("/api/telescope/imaging/planet/stop")

            assert response.status_code == 500
            assert "failed to stop planetary imaging" in response.json()["detail"].lower()
        finally:
            app.dependency_overrides.clear()
