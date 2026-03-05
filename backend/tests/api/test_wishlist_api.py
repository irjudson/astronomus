"""Tests for wish list API endpoints.

These tests verify the wish list functionality for saving and retrieving
favorite targets (planets, moons, DSOs) for astrophotography planning.
"""

import json

import pytest

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration


class TestWishListEndpoints:
    """Test wish list API endpoints."""

    def test_get_wishlist_when_empty(self, client):
        """Test GET /api/settings/wishlist returns empty array when not set."""
        response = client.get("/api/settings/wishlist")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_wishlist_returns_saved_targets(self, client, override_get_db):
        """Test GET /api/settings/wishlist returns saved targets."""
        from app.models.settings_models import AppSetting

        db = override_get_db

        # Create wishlist setting with sample targets
        wishlist_data = [
            {"name": "Jupiter", "type": "planet"},
            {"name": "M31", "type": "dso"},
            {"name": "Saturn", "type": "planet"},
        ]

        setting = AppSetting(
            key="user.wishlist_targets",
            value=json.dumps(wishlist_data),
            value_type="json",
            category="user",
            description="User's favorite targets wish list",
        )
        db.add(setting)
        db.commit()

        # Test retrieval
        response = client.get("/api/settings/wishlist")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["name"] == "Jupiter"
        assert data[0]["type"] == "planet"
        assert data[1]["name"] == "M31"
        assert data[1]["type"] == "dso"

    def test_put_wishlist_saves_targets(self, client, override_get_db):
        """Test PUT /api/settings/wishlist saves targets."""
        db = override_get_db

        wishlist_data = [
            {"name": "Mars", "type": "planet"},
            {"name": "Moon", "type": "moon"},
            {"name": "M42", "type": "dso"},
        ]

        # Save wishlist
        response = client.put("/api/settings/wishlist", json=wishlist_data)
        assert response.status_code == 200
        result = response.json()
        assert result["message"] == "Wishlist updated successfully"
        assert result["count"] == 3

        # Verify it was saved to database
        from app.models.settings_models import AppSetting

        setting = db.query(AppSetting).filter(AppSetting.key == "user.wishlist_targets").first()
        assert setting is not None
        assert setting.value_type == "json"
        assert setting.category == "user"

        saved_data = json.loads(setting.value)
        assert len(saved_data) == 3
        assert saved_data[0]["name"] == "Mars"
        assert saved_data[1]["name"] == "Moon"
        assert saved_data[2]["name"] == "M42"

    def test_put_wishlist_updates_existing(self, client, override_get_db):
        """Test PUT /api/settings/wishlist updates existing wishlist."""
        from app.models.settings_models import AppSetting

        db = override_get_db

        # Create initial wishlist
        initial_data = [{"name": "Jupiter", "type": "planet"}]
        setting = AppSetting(
            key="user.wishlist_targets",
            value=json.dumps(initial_data),
            value_type="json",
            category="user",
        )
        db.add(setting)
        db.commit()

        # Update wishlist
        updated_data = [
            {"name": "Saturn", "type": "planet"},
            {"name": "Venus", "type": "planet"},
        ]
        response = client.put("/api/settings/wishlist", json=updated_data)
        assert response.status_code == 200

        # Verify update
        db.refresh(setting)
        saved_data = json.loads(setting.value)
        assert len(saved_data) == 2
        assert saved_data[0]["name"] == "Saturn"
        assert saved_data[1]["name"] == "Venus"

    def test_get_wishlist_defaults(self, client):
        """Test GET /api/wishlist/defaults returns 19 solar system objects."""
        response = client.get("/api/wishlist/defaults")
        assert response.status_code == 200
        data = response.json()

        assert len(data) == 19

        # Verify structure
        assert all("name" in item for item in data)
        assert all("type" in item for item in data)

        # Verify all 8 planets present (including Pluto, excluding Earth)
        planet_names = [item["name"] for item in data if item["type"] == "planet"]
        assert "Mercury" in planet_names
        assert "Venus" in planet_names
        assert "Mars" in planet_names
        assert "Jupiter" in planet_names
        assert "Saturn" in planet_names
        assert "Uranus" in planet_names
        assert "Neptune" in planet_names
        assert "Pluto" in planet_names
        assert len(planet_names) == 8

        # Verify Moon present
        moon_names = [item["name"] for item in data]
        assert "Moon" in moon_names

        # Verify Sun present
        assert "Sun" in moon_names

        # Verify Jupiter's Galilean moons
        assert "Io" in moon_names
        assert "Europa" in moon_names
        assert "Ganymede" in moon_names
        assert "Callisto" in moon_names

        # Verify Saturn's major moons
        assert "Titan" in moon_names
        assert "Rhea" in moon_names
        assert "Tethys" in moon_names
        assert "Dione" in moon_names
        assert "Enceladus" in moon_names
