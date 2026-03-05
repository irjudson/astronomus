import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response, StreamingResponse

from app.api.deps import get_current_telescope
from app.clients.seestar_client import SeestarClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/telescope/preview", tags=["preview"])


def _get_rtsp_service(client: SeestarClient):
    """Get (and lazily start) the RTSP preview capture service for this client."""
    from app.services.rtmp_preview_service import get_preview_service

    host = getattr(client, "_host", None) or "192.168.2.47"
    service = get_preview_service(host=host, port=4554)
    if not service.is_running:
        service.start()
    return service


@router.get("/frame")
async def get_preview_frame(
    client: SeestarClient = Depends(get_current_telescope),
):
    """Get the latest preview frame from the RTSP stream.

    Returns JPEG image bytes, or 503 if no frame is available yet.
    """
    service = _get_rtsp_service(client)

    # Poll up to 5s (50 × 100ms) for the RTSP service to deliver its first frame
    if service.latest_frame is None:
        for _ in range(50):
            await asyncio.sleep(0.1)
            if service.latest_frame is not None:
                break

    frame_bytes = service.get_latest_frame_jpeg(quality=85)

    if frame_bytes is None:
        raise HTTPException(
            status_code=503,
            detail="No preview frames available - RTSP stream may not be active yet",
        )

    return Response(
        content=frame_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-cache, no-store"},
    )


@router.get("/stream")
async def stream_preview(
    client: SeestarClient = Depends(get_current_telescope),
):
    """Stream live preview as MJPEG (multipart/x-mixed-replace).

    Connect an <img> element's src to this URL for a live video feed.
    The stream runs until the client disconnects.
    """
    service = _get_rtsp_service(client)

    async def generate():
        """Yield JPEG frames as they arrive — no polling, no artificial delay."""
        loop = asyncio.get_running_loop()
        last_seq = -1

        while True:
            # Block in a thread-pool worker until the capture thread signals
            # a new frame (or 1 s timeout so we don't hang forever if idle)
            frame_bytes, last_seq = await loop.run_in_executor(
                None,
                lambda seq=last_seq: service.wait_for_new_frame(seq, timeout=1.0),
            )

            if frame_bytes:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + frame_bytes
                    + b"\r\n"
                )

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache, no-store"},
    )
