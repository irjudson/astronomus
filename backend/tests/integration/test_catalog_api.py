"""Integration tests for catalog API."""

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.integration
def test_list_targets_with_visibility(client):
    """Test /api/targets endpoint with visibility calculations."""
    # Note: This requires location to be configured in settings
    response = client.get("/api/targets?limit=5&include_visibility=true")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 5

    # If location configured, should have visibility
    if len(data) > 0:
        target = data[0]
        assert "name" in target
        assert "catalog_id" in target
        # visibility may or may not be present depending on location config


@pytest.mark.integration
def test_list_targets_sort_by_magnitude(client):
    """Test sorting by magnitude."""
    response = client.get("/api/targets?limit=10&sort_by=magnitude")

    assert response.status_code == 200
    data = response.json()

    # Should be sorted by magnitude ascending (brightest first)
    if len(data) > 1:
        assert data[0]["magnitude"] <= data[1]["magnitude"]


@pytest.mark.integration
def test_list_targets_sort_by_size(client):
    """Test sorting by size."""
    response = client.get("/api/targets?limit=10&sort_by=size")

    assert response.status_code == 200
    data = response.json()

    # Should be sorted by size descending (largest first)
    if len(data) > 1:
        assert data[0]["size_arcmin"] >= data[1]["size_arcmin"]


@pytest.mark.integration
def test_list_targets_sort_by_name(client):
    """Test sorting by name."""
    response = client.get("/api/targets?limit=10&sort_by=name")

    assert response.status_code == 200
    data = response.json()

    # Should be sorted alphabetically
    if len(data) > 1:
        assert data[0]["catalog_id"] <= data[1]["catalog_id"]


@pytest.mark.integration
def test_nearby_objects_returns_sorted_results(client):
    """Test /api/targets/near returns results sorted by separation."""
    resp = client.get(
        "/api/targets/near",
        params={"ra_hours": 0.712, "dec_degrees": 41.27, "radius_deg": 5.0, "limit": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    for item in data:
        assert "separation_deg" in item
        assert item["separation_deg"] >= 0.0
    seps = [item["separation_deg"] for item in data]
    assert seps == sorted(seps)


@pytest.mark.integration
def test_nearby_objects_first_result_near_zero(client):
    """Test that the closest result when querying near M31 is M31 itself."""
    resp = client.get(
        "/api/targets/near",
        params={"ra_hours": 0.712, "dec_degrees": 41.27, "radius_deg": 1.0, "limit": 3},
    )
    assert resp.status_code == 200
    data = resp.json()
    if data:
        assert data[0]["separation_deg"] < 0.1
