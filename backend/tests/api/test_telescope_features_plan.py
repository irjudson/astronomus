"""Tests for plan upload/list/delete endpoints on telescope_features router."""

from unittest.mock import AsyncMock, Mock

import pytest
from app.api import telescope as telescope_module
from app.clients.seestar_client import SeestarClient
from app.main import app

pytestmark = pytest.mark.integration


@pytest.fixture
def mock_scope():
    c = Mock(spec=SeestarClient)
    c.connected = True
    c.list_plan = AsyncMock(return_value=[{"name": "2026-05-14-plan"}])
    c.set_plan = AsyncMock(return_value=True)
    c.delete_plan = AsyncMock(return_value=True)
    return c


@pytest.fixture
def no_telescope_client(client):
    """Client fixture that guarantees no telescope is connected."""
    old = telescope_module.seestar_client
    telescope_module.seestar_client = None
    yield client
    telescope_module.seestar_client = old


class TestPlanUploadEndpoints:
    def test_list_plans_no_telescope_returns_503(self, no_telescope_client):
        """When no telescope is connected, expect 503."""
        resp = no_telescope_client.get("/api/telescope/features/plan/list")
        assert resp.status_code == 503

    def test_upload_plan_no_telescope_returns_503(self, no_telescope_client):
        resp = no_telescope_client.post("/api/telescope/features/plan/upload", json={"plan_id": 1})
        assert resp.status_code == 503

    def test_upload_plan_not_found_returns_404(self, client, override_get_db, mock_scope):
        from app.api.deps import get_current_telescope

        app.dependency_overrides[get_current_telescope] = lambda: mock_scope
        try:
            resp = client.post("/api/telescope/features/plan/upload", json={"plan_id": 99999})
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.pop(get_current_telescope, None)

    def test_delete_plan_on_scope(self, client, mock_scope):
        from app.api.deps import get_current_telescope

        app.dependency_overrides[get_current_telescope] = lambda: mock_scope
        try:
            resp = client.delete("/api/telescope/features/plan/TestPlan")
            assert resp.status_code == 200
        finally:
            app.dependency_overrides.pop(get_current_telescope, None)
