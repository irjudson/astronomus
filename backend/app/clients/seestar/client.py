"""Composite SeestarClient combining all behavior mixins."""

from .files import SeestarFilesMixin
from .mount import SeestarMountMixin
from .observation import SeestarObservationMixin
from .system import SeestarSystemMixin
from .transport import SeestarTransport


class SeestarClient(
    SeestarTransport, SeestarMountMixin, SeestarObservationMixin, SeestarSystemMixin, SeestarFilesMixin
):
    """TCP client for Seestar S50 smart telescope.

    Combines transport, mount control, observation, system management,
    and file retrieval capabilities into a single unified client.
    See individual mixin modules for API documentation.
    """
