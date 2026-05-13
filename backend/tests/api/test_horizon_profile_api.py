"""Tests for horizon profile settings endpoints."""
import json
import pytest

pytestmark = pytest.mark.integration


class TestHorizonProfileEndpoints:

    def test_get_horizon_profile_when_empty(self, client):
        response = client.get("/api/settings/horizon-profile")
        assert response.status_code == 200
        assert response.json() == []

    def test_put_horizon_profile_saves_points(self, client):
        profile = [
            {"az": 0.0, "alt": 5.0},
            {"az": 90.0, "alt": 10.0},
            {"az": 180.0, "alt": 20.0},
            {"az": 270.0, "alt": 8.0},
        ]
        response = client.put("/api/settings/horizon-profile", json=profile)
        assert response.status_code == 200
        assert response.json()["count"] == 4

    def test_get_horizon_profile_returns_saved(self, client):
        profile = [{"az": 45.0, "alt": 12.0}]
        client.put("/api/settings/horizon-profile", json=profile)
        response = client.get("/api/settings/horizon-profile")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["az"] == 45.0
        assert data[0]["alt"] == 12.0

    def test_put_horizon_profile_replaces_existing(self, client):
        client.put("/api/settings/horizon-profile", json=[{"az": 0.0, "alt": 5.0}])
        client.put("/api/settings/horizon-profile", json=[{"az": 90.0, "alt": 15.0}, {"az": 180.0, "alt": 10.0}])
        response = client.get("/api/settings/horizon-profile")
        assert len(response.json()) == 2
