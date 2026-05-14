import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


class TestCustomTargetsAPI:
    def test_list_custom_targets_empty(self, client):
        resp = client.get("/api/targets/custom/")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_create_custom_target(self, client):
        payload = {
            "name": "My Nebula",
            "ra_hours": 5.0,
            "dec_degrees": 10.0,
            "object_type": "nebula",
        }
        resp = client.post("/api/targets/custom/", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Nebula"
        assert data["catalog_id"].startswith("USER:")

    def test_create_custom_target_duplicate_returns_400(self, client):
        payload = {"name": "Dup Nebula", "ra_hours": 5.0, "dec_degrees": 10.0, "object_type": "nebula"}
        client.post("/api/targets/custom/", json=payload)
        resp = client.post("/api/targets/custom/", json=payload)
        assert resp.status_code == 400

    def test_update_custom_target(self, client):
        payload = {"name": "Test Star", "ra_hours": 1.0, "dec_degrees": 45.0, "object_type": "other"}
        create_resp = client.post("/api/targets/custom/", json=payload)
        tid = create_resp.json()["id"]
        update_resp = client.put(f"/api/targets/custom/{tid}", json={**payload, "notes": "updated"})
        assert update_resp.status_code == 200
        assert update_resp.json()["notes"] == "updated"

    def test_delete_custom_target(self, client):
        payload = {"name": "Delete Me", "ra_hours": 2.0, "dec_degrees": 30.0, "object_type": "galaxy"}
        create_resp = client.post("/api/targets/custom/", json=payload)
        tid = create_resp.json()["id"]
        del_resp = client.delete(f"/api/targets/custom/{tid}")
        assert del_resp.status_code == 200
        list_resp = client.get("/api/targets/custom/")
        ids = [t["id"] for t in list_resp.json()]
        assert tid not in ids
