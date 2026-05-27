"""Extended tests for captures API — covering uncovered branches."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.database import get_db
from app.main import app
from app.models.capture_models import CaptureHistory, OutputFile

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# list_captures — filter paths
# ---------------------------------------------------------------------------


def test_list_captures_filter_by_status(client, override_get_db):
    db = override_get_db
    c1 = CaptureHistory(
        catalog_id="M31",
        total_exposure_seconds=3600,
        total_frames=360,
        total_sessions=1,
        status="complete",
    )
    c2 = CaptureHistory(
        catalog_id="M42",
        total_exposure_seconds=1800,
        total_frames=180,
        total_sessions=1,
        status="needs_more_data",
    )
    db.add_all([c1, c2])
    db.commit()

    resp = client.get("/api/captures?status=complete")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["catalog_id"] == "M31"


def test_list_captures_filter_by_min_exposure(client, override_get_db):
    db = override_get_db
    db.add(
        CaptureHistory(
            catalog_id="M31",
            total_exposure_seconds=7200,
            total_frames=720,
            total_sessions=2,
        )
    )
    db.add(
        CaptureHistory(
            catalog_id="M42",
            total_exposure_seconds=900,
            total_frames=90,
            total_sessions=1,
        )
    )
    db.commit()

    resp = client.get("/api/captures?min_exposure_seconds=3600")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["catalog_id"] == "M31"


def test_list_captures_filter_by_max_exposure(client, override_get_db):
    db = override_get_db
    db.add(
        CaptureHistory(
            catalog_id="M31",
            total_exposure_seconds=7200,
            total_frames=720,
            total_sessions=2,
        )
    )
    db.add(
        CaptureHistory(
            catalog_id="M42",
            total_exposure_seconds=1800,
            total_frames=180,
            total_sessions=1,
        )
    )
    db.commit()

    resp = client.get("/api/captures?max_exposure_seconds=3600")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["catalog_id"] == "M42"


# ---------------------------------------------------------------------------
# update_capture_status — covered/uncovered paths
# ---------------------------------------------------------------------------


def test_update_capture_status_creates_new_record(client):
    resp = client.put("/api/captures/NGC7000", json={"status": "complete"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["catalog_id"] == "NGC7000"
    assert data["status"] == "complete"


def test_update_capture_status_updates_existing(client, override_get_db):
    db = override_get_db
    record = CaptureHistory(
        catalog_id="M45",
        total_exposure_seconds=1200,
        total_frames=120,
        total_sessions=1,
        status="needs_more_data",
    )
    db.add(record)
    db.commit()

    resp = client.put("/api/captures/M45", json={"status": "complete"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "complete"


def test_update_capture_status_clear_status(client, override_get_db):
    db = override_get_db
    record = CaptureHistory(
        catalog_id="M57",
        total_exposure_seconds=600,
        total_frames=60,
        total_sessions=1,
        status="complete",
    )
    db.add(record)
    db.commit()

    resp = client.put("/api/captures/M57", json={"status": None})
    assert resp.status_code == 200
    assert resp.json()["status"] is None


def test_update_capture_status_invalid_status_422(client):
    resp = client.put("/api/captures/M31", json={"status": "invalid_value"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# get_capture_files — filter paths
# ---------------------------------------------------------------------------


def test_get_capture_files_empty(client, override_get_db):
    db = override_get_db
    db.add(
        CaptureHistory(
            catalog_id="M81",
            total_exposure_seconds=0,
            total_frames=0,
            total_sessions=0,
        )
    )
    db.commit()

    resp = client.get("/api/captures/M81/files")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_capture_files_filter_by_file_type(client, override_get_db):
    db = override_get_db
    db.add(
        OutputFile(
            file_path="/data/M31/stacked.fits",
            file_type="stacked_fits",
            file_size_bytes=1024000,
            catalog_id="M31",
            catalog_id_confidence=0.99,
        )
    )
    db.add(
        OutputFile(
            file_path="/data/M31/frame.jpg",
            file_type="jpg",
            file_size_bytes=102400,
            catalog_id="M31",
            catalog_id_confidence=0.95,
        )
    )
    db.commit()

    resp = client.get("/api/captures/M31/files?file_type=stacked_fits")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["file_type"] == "stacked_fits"


def test_get_capture_files_filter_by_min_confidence(client, override_get_db):
    db = override_get_db
    db.add(
        OutputFile(
            file_path="/data/M31/high.fits",
            file_type="stacked_fits",
            file_size_bytes=1024000,
            catalog_id="M31",
            catalog_id_confidence=0.99,
        )
    )
    db.add(
        OutputFile(
            file_path="/data/M31/low.fits",
            file_type="stacked_fits",
            file_size_bytes=512000,
            catalog_id="M31",
            catalog_id_confidence=0.50,
        )
    )
    db.commit()

    resp = client.get("/api/captures/M31/files?min_confidence=0.9")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["catalog_id_confidence"] >= 0.9


# ---------------------------------------------------------------------------
# list_all_output_files
# ---------------------------------------------------------------------------


def test_list_all_output_files_empty(client):
    resp = client.get("/api/captures/files/all")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_list_all_output_files_with_filters(client, override_get_db):
    db = override_get_db
    db.add(
        OutputFile(
            file_path="/data/NGC7000/stacked.fits",
            file_type="stacked_fits",
            file_size_bytes=2048000,
            catalog_id="NGC7000",
            catalog_id_confidence=0.97,
        )
    )
    db.add(
        OutputFile(
            file_path="/data/M42/preview.jpg",
            file_type="jpg",
            file_size_bytes=204800,
            catalog_id="M42",
            catalog_id_confidence=0.88,
        )
    )
    db.commit()

    resp = client.get("/api/captures/files/all?file_type=stacked_fits&min_confidence=0.9")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["file_type"] == "stacked_fits"


def test_list_all_output_files_pagination(client, override_get_db):
    db = override_get_db
    for i in range(5):
        db.add(
            OutputFile(
                file_path=f"/data/M{i}/f.fits",
                file_type="stacked_fits",
                file_size_bytes=1000,
                catalog_id=f"M{i}",
                catalog_id_confidence=0.9,
            )
        )
    db.commit()

    resp = client.get("/api/captures/files/all?limit=2&offset=0")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


# ---------------------------------------------------------------------------
# file_transfer error path
# ---------------------------------------------------------------------------


def test_trigger_file_transfer_exception_returns_500(client):
    with patch("app.api.captures.FileTransferService") as MockService:
        MockService.return_value.transfer_and_scan_all.side_effect = RuntimeError("disk error")

        resp = client.post("/api/captures/transfer")
        assert resp.status_code == 500
        assert "Transfer failed" in resp.json()["detail"]
