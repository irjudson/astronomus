"""
API dependencies.
"""

from fastapi import HTTPException

from app.api import telescope as telescope_module
from app.clients.seestar_client import SeestarClient


def get_current_telescope() -> SeestarClient:
    """
    Get the currently connected telescope client.

    Raises:
        HTTPException: If no telescope is connected (503 Service Unavailable)
    """
    if telescope_module.seestar_client is None:
        raise HTTPException(status_code=503, detail="Telescope not connected")
    return telescope_module.seestar_client
