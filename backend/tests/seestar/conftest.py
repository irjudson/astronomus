"""Pytest fixtures and options for Seestar S50 hardware test suite."""

import asyncio
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Tuple

import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.clients.seestar_client import CommandError, SeestarClient
from tests.seestar.mock_server import MockSeestarServer

# ---------------------------------------------------------------------------
# CLI options
# ---------------------------------------------------------------------------


def pytest_addoption(parser):
    # --telescope-host and --telescope-port already defined in root conftest.py
    # Only add seestar-specific options here.
    parser.addoption(
        "--save-recordings",
        default=None,
        help="Directory to save session recordings when running hardware tests",
    )


# ---------------------------------------------------------------------------
# Temp RSA key fixture (shared between hardware and mock tests)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def tmp_rsa_key(tmp_path_factory) -> str:
    """Generate a temporary RSA private key for authentication during tests.

    Returns the file path as a string.
    """
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    tmp_dir = tmp_path_factory.mktemp("keys")
    key_path = tmp_dir / "test_seestar.pem"
    key_path.write_bytes(pem)
    return str(key_path)


# ---------------------------------------------------------------------------
# Mock server fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def mock_server() -> AsyncGenerator[Tuple[str, int], None]:
    """Start a MockSeestarServer; yields (host, port)."""
    server = MockSeestarServer()
    host, port = await server.start()
    yield host, port
    await server.stop()


@pytest_asyncio.fixture
async def mock_server_obj() -> AsyncGenerator[MockSeestarServer, None]:
    """Start a MockSeestarServer and yield the server object itself.

    Use this when tests need to inspect commands_received.
    """
    server = MockSeestarServer()
    await server.start()
    yield server
    await server.stop()


@pytest_asyncio.fixture
async def mock_client(mock_server_obj: MockSeestarServer, tmp_rsa_key: str) -> AsyncGenerator[SeestarClient, None]:
    """SeestarClient already connected to the mock server.

    The mock server handles auth automatically, so no real key is needed.
    A freshly generated key is used so the client's key-loading code path runs.
    """
    host = mock_server_obj._server.sockets[0].getsockname()[0]
    port = mock_server_obj._server.sockets[0].getsockname()[1]

    client = SeestarClient(private_key_path=tmp_rsa_key)
    await client.connect(host, port)
    yield client
    if client.connected:
        await client.disconnect()


# ---------------------------------------------------------------------------
# Real hardware fixture (skipped automatically without --telescope-host)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def telescope(request) -> AsyncGenerator[SeestarClient, None]:
    """Connected SeestarClient to the real S50.

    Requires --real-hardware flag to run (prevents accidental connection to
    telescope at the default IP in CI environments).
    Optionally override --telescope-host (default: 192.168.2.47) and
    --telescope-port (default: 4700).

    Uses the registered key from settings (secrets/seestar_private_key.pem),
    NOT the tmp_rsa_key fixture (which is only valid for mock tests).
    """
    real_hw = request.config.getoption("--real-hardware", default=False)
    if not real_hw:
        pytest.skip("Hardware tests require --real-hardware flag")

    host = request.config.getoption("--telescope-host")
    port = int(request.config.getoption("--telescope-port"))

    # Use default key path from settings (the registered key the S50 knows about)
    client = SeestarClient()
    await client.connect(host, port)
    yield client
    if client.connected:
        await client.disconnect()


# ---------------------------------------------------------------------------
# telescope_ready: arm open and in active viewing state
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def telescope_ready(telescope: SeestarClient) -> AsyncGenerator[SeestarClient, None]:
    """Telescope with arm open and ready for movement/imaging tests.

    Opens the arm by clearing equatorial mode (if set) then slewing to a safe
    southerly position (Az=180°, Alt=45°) via scope_move_to_horizon.  This is
    a prerequisite for directional moves, AVI recording, annotation, focusing,
    and planetary tests that fail with code 207 when the arm is parked.
    """
    # Clear equatorial mode if active — it silently blocks all movement
    try:
        device_state = await telescope.get_device_state()
        mount = device_state.get("mount", {})
        if mount.get("equ_mode", False):
            await telescope.clear_polar_alignment()
            await asyncio.sleep(1)
    except Exception:
        pass

    # Cancel any lingering operation
    try:
        await telescope.cancel_current_operation()
        await asyncio.sleep(0.5)
    except Exception:
        pass

    # Open arm to a safe position (due south, 45° altitude — always above horizon)
    try:
        await telescope.move_to_horizon(azimuth=180.0, altitude=45.0)
        await asyncio.sleep(3)
    except Exception as exc:
        pytest.skip(f"Could not open telescope arm: {exc}")
        return

    yield telescope

    # Best-effort cleanup
    try:
        await telescope.cancel_current_operation()
    except Exception:
        pass
