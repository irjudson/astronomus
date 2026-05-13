"""Horizon scanner: use the Seestar S50 camera to auto-detect local horizon."""

import asyncio
import io
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncGenerator, List, Optional

import httpx
from PIL import Image

logger = logging.getLogger(__name__)

SKY_RATIO_THRESHOLD = 1.2   # top/bottom brightness ratio above this = sky
TERRAIN_RATIO_THRESHOLD = 0.9
SETTLE_SECONDS = 1.8
BINARY_SEARCH_ITERATIONS = 5


def analyze_frame_brightness(jpeg_bytes: bytes) -> float:
    """Return top-third / bottom-third mean brightness ratio."""
    img = Image.open(io.BytesIO(jpeg_bytes)).convert("L")  # grayscale
    w, h = img.size
    third = h // 3
    top = list(img.crop((0, 0, w, third)).getdata())
    bottom = list(img.crop((0, h - third, w, h)).getdata())
    mean_top = sum(top) / len(top) if top else 1
    mean_bottom = sum(bottom) / len(bottom) if bottom else 1
    if mean_bottom == 0:
        return 999.0
    return mean_top / mean_bottom


@dataclass
class ScanProgress:
    current_az: float
    total_azimuths: int
    completed: int
    points: List[dict] = field(default_factory=list)
    status: str = "scanning"  # scanning | complete | error
    error: Optional[str] = None

    @property
    def progress_percent(self) -> float:
        if self.total_azimuths == 0:
            return 0.0
        return round(self.completed / self.total_azimuths * 100, 1)


class HorizonScannerService:
    """Scan local horizon by sweeping telescope azimuths and analyzing camera frames."""

    def __init__(
        self,
        telescope_host: str,
        telescope_port: int,
        az_step: int = 15,
        alt_min: float = 2.0,
        alt_max: float = 45.0,
    ):
        self.host = telescope_host
        self.port = telescope_port
        self.az_step = az_step
        self.alt_min = alt_min
        self.alt_max = alt_max
        self._snapshot_url = f"http://localhost:9247/api/telescope/preview/snapshot"

    def _is_sky(self, ratio: float) -> bool:
        return ratio >= SKY_RATIO_THRESHOLD

    async def scan(self) -> AsyncGenerator[ScanProgress, None]:
        """Sweep azimuths, binary-search altitude, yield progress after each az."""
        azimuths = list(range(0, 360, self.az_step))
        total = len(azimuths)
        points = []

        for i, az in enumerate(azimuths):
            try:
                alt = await self._find_horizon_altitude(az)
            except Exception as e:
                logger.warning("Scan failed at az=%.0f: %s", az, e)
                alt = self.alt_min  # fallback

            points.append({"az": float(az), "alt": round(alt, 1)})
            yield ScanProgress(
                current_az=float(az),
                total_azimuths=total,
                completed=i + 1,
                points=list(points),
                status="scanning" if i < total - 1 else "complete",
            )

    async def _find_horizon_altitude(self, azimuth: float) -> float:
        """Binary search for horizon altitude at the given azimuth."""
        low, high = self.alt_min, self.alt_max

        for _ in range(BINARY_SEARCH_ITERATIONS):
            mid = (low + high) / 2.0
            await self._move_scope(azimuth, mid)
            await asyncio.sleep(SETTLE_SECONDS)
            frame = await self._capture_frame()
            ratio = analyze_frame_brightness(frame)

            if self._is_sky(ratio):
                # We can see sky; horizon is at or below mid
                high = mid
            else:
                # Terrain in view; horizon is above mid
                low = mid

        return (low + high) / 2.0

    async def _move_scope(self, azimuth: float, altitude: float) -> None:
        """Command telescope to move to alt/az position."""
        import json as _json

        # Use the Seestar JSON-RPC protocol directly
        reader, writer = await asyncio.open_connection(self.host, self.port)
        cmd = _json.dumps({
            "id": 1, "method": "scope_move_to_horizon",
            "params": [azimuth, altitude]
        }) + "\r\n"
        writer.write(cmd.encode())
        await writer.drain()
        await asyncio.sleep(0.2)
        writer.close()
        await writer.wait_closed()

    async def _capture_frame(self) -> bytes:
        """Fetch a JPEG snapshot from the backend preview endpoint."""
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(self._snapshot_url)
            resp.raise_for_status()
            return resp.content
