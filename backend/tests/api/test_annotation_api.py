"""Tests for annotation API endpoints."""

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
    """Create mock Seestar client."""
    client = AsyncMock(spec=SeestarClient)
    client.connected = True
    client.start_annotate = AsyncMock(return_value=True)
    client.stop_annotate = AsyncMock(return_value=True)
    return client


class TestAnnotationEndpoints:
    """Test annotation control endpoints."""

    def test_toggle_annotation_enable_success(self, client, mock_seestar_client):
        """Test successfully enabling annotations."""
        with patch("app.api.telescope.seestar_client", mock_seestar_client):
            response = client.post("/api/telescope/annotation/toggle", json={"enabled": True})

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["enabled"] is True
            mock_seestar_client.start_annotate.assert_called_once()
            mock_seestar_client.stop_annotate.assert_not_called()

    def test_toggle_annotation_disable_success(self, client, mock_seestar_client):
        """Test successfully disabling annotations."""
        with patch("app.api.telescope.seestar_client", mock_seestar_client):
            response = client.post("/api/telescope/annotation/toggle", json={"enabled": False})

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["enabled"] is False
            mock_seestar_client.stop_annotate.assert_called_once()
            mock_seestar_client.start_annotate.assert_not_called()

    def test_toggle_annotation_not_connected(self, client):
        """Test annotation toggle when telescope not connected (returns 503)."""
        with patch("app.api.telescope.seestar_client", None):
            response = client.post("/api/telescope/annotation/toggle", json={"enabled": True})

            assert response.status_code == 503
            assert "not connected" in response.json()["detail"].lower()

    def test_toggle_annotation_enable_failure(self, client, mock_seestar_client):
        """Test annotation enable returns success=False when operation fails."""
        mock_seestar_client.start_annotate = AsyncMock(return_value=False)
        with patch("app.api.telescope.seestar_client", mock_seestar_client):
            response = client.post("/api/telescope/annotation/toggle", json={"enabled": True})

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert data["enabled"] is True

    def test_toggle_annotation_disable_failure(self, client, mock_seestar_client):
        """Test annotation disable returns success=False when operation fails."""
        mock_seestar_client.stop_annotate = AsyncMock(return_value=False)
        with patch("app.api.telescope.seestar_client", mock_seestar_client):
            response = client.post("/api/telescope/annotation/toggle", json={"enabled": False})

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert data["enabled"] is False

    def test_toggle_annotation_exception(self, client, mock_seestar_client):
        """Test annotation toggle with exception."""
        mock_seestar_client.start_annotate = AsyncMock(side_effect=Exception("Annotation error"))
        with patch("app.api.telescope.seestar_client", mock_seestar_client):
            response = client.post("/api/telescope/annotation/toggle", json={"enabled": True})

            assert response.status_code == 500
            assert "annotation error" in response.json()["detail"].lower()

    def test_toggle_annotation_invalid_request(self, client, mock_seestar_client):
        """Test annotation toggle with invalid request body."""
        with patch("app.api.telescope.seestar_client", mock_seestar_client):
            response = client.post("/api/telescope/annotation/toggle", json={})

            assert response.status_code == 422  # FastAPI validation error

    def test_toggle_annotation_disconnected(self, client):
        """Test annotation toggle when no telescope is connected (seestar_client is None)."""
        with patch("app.api.telescope.seestar_client", None):
            response = client.post("/api/telescope/annotation/toggle", json={"enabled": True})

            assert response.status_code == 503
            assert "not connected" in response.json()["detail"].lower()
