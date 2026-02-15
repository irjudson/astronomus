import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.api.deps import get_current_telescope
from app.clients.seestar_client import SeestarClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/telescope/preview", tags=["preview"])


@router.get("/frame")
async def get_preview_frame(
    client: SeestarClient = Depends(get_current_telescope),
):
    """Get the latest preview frame from telescope.

    Returns JPEG image bytes.

    Returns:
        Response: JPEG image

    Raises:
        HTTPException 400: Telescope not connected (raised by dependency)
        HTTPException 503: No preview frames available
    """
    frame_bytes = await client.get_latest_preview_frame()

    if frame_bytes is None:
        raise HTTPException(
            status_code=503,
            detail="No preview frames available - start imaging to generate frames",
        )

    return Response(content=frame_bytes, media_type="image/jpeg")
