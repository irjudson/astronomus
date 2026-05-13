"""Horizon scanning API endpoints."""

import asyncio
import uuid
from typing import Dict

from fastapi import APIRouter, HTTPException

from app.services.horizon_scanner_service import HorizonScannerService

router = APIRouter(prefix="/horizon", tags=["horizon"])

# In-memory store for scan tasks (single-user app)
_scans: Dict[str, dict] = {}


@router.post("/scan")
async def start_horizon_scan(
    telescope_host: str = "192.168.2.47",
    telescope_port: int = 4700,
    az_step: int = 15,
):
    """Start a background horizon scan. Returns a scan_id to poll for status."""
    scan_id = str(uuid.uuid4())[:8]
    _scans[scan_id] = {"status": "scanning", "progress": 0, "points": [], "current_az": 0}

    async def _run():
        svc = HorizonScannerService(telescope_host, telescope_port, az_step=az_step)
        async for progress in svc.scan():
            _scans[scan_id].update({
                "status": progress.status,
                "progress": progress.progress_percent,
                "current_az": progress.current_az,
                "points": progress.points,
            })

    asyncio.create_task(_run())
    return {"scan_id": scan_id, "message": "Horizon scan started"}


@router.get("/scan/{scan_id}/status")
async def get_scan_status(scan_id: str):
    """Get current scan progress and detected horizon points."""
    if scan_id not in _scans:
        raise HTTPException(status_code=404, detail="Scan not found")
    return _scans[scan_id]


@router.delete("/scan/{scan_id}")
async def clear_scan(scan_id: str):
    """Remove a completed scan record."""
    _scans.pop(scan_id, None)
    return {"deleted": scan_id}
