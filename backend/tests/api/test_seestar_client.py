"""Tests for Seestar S50 client."""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.clients.seestar_client import (
    CommandError,
    ConnectionError,
    SeestarClient,
    SeestarState,
    SeestarStatus,
    TimeoutError,
)


class TestSeestarClient:
    """Test suite for SeestarClient."""

    @pytest.fixture
    def client(self):
        """Create test client instance."""
        return SeestarClient()

    def test_init(self, client):
        """Test client initialization."""
        assert not client.connected
        assert client.status.state == SeestarState.DISCONNECTED
        assert client.status.connected is False

    @pytest.mark.asyncio
    async def test_connect_timeout(self, client):
        """Test connection timeout."""
        with pytest.raises(ConnectionError, match="Failed to connect"):
            # Use invalid host to trigger connection error
            await client.connect("invalid.host.test", port=9999)

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self, client):
        """Test disconnect when not connected (should not raise error)."""
        await client.disconnect()
        assert not client.connected

    def test_command_when_not_connected(self, client):
        """Test sending command when not connected."""

        async def test():
            with pytest.raises(ConnectionError, match="Not connected"):
                await client._send_command("test_method")

        asyncio.run(test())

    def test_status_updates(self, client):
        """Test status property returns current status."""
        status = client.status
        assert isinstance(status, SeestarStatus)
        assert status.connected is False
        assert status.state == SeestarState.DISCONNECTED

    def test_connected_property(self, client):
        """Test connected property."""
        assert client.connected is False
        # Simulate connection
        client._connected = True
        assert client.connected is True

    @pytest.mark.asyncio
    async def test_disconnect_cleanup(self, client):
        """Test disconnect cleans up resources."""
        # Simulate partial connection state
        client._connected = True
        mock_writer = Mock()
        mock_writer.close = Mock()
        mock_writer.wait_closed = AsyncMock()
        client._writer = mock_writer

        await client.disconnect()

        assert not client.connected
        assert client._writer is None  # Should be cleared
        mock_writer.close.assert_called_once()

    def test_state_enum_values(self):
        """Test SeestarState enum has expected values."""
        assert SeestarState.DISCONNECTED.value == "disconnected"
        assert SeestarState.CONNECTED.value == "connected"
        assert SeestarState.SLEWING.value == "slewing"
        assert SeestarState.TRACKING.value == "tracking"
        assert SeestarState.FOCUSING.value == "focusing"
        assert SeestarState.IMAGING.value == "imaging"

    def test_custom_exceptions(self):
        """Test custom exception classes."""
        conn_err = ConnectionError("test")
        assert str(conn_err) == "test"
        assert isinstance(conn_err, Exception)

        cmd_err = CommandError("test")
        assert str(cmd_err) == "test"

        timeout_err = TimeoutError("test")
        assert str(timeout_err) == "test"

    @pytest.mark.asyncio
    async def test_status_callback(self, client):
        """Test status callback mechanism."""
        callback_called = []

        def status_callback(status):
            callback_called.append(status)

        client.set_status_callback(status_callback)

        # Trigger a status update
        client._update_status(connected=True, state=SeestarState.CONNECTED)

        assert len(callback_called) == 1
        assert callback_called[0].connected is True


# Note: Full integration tests would require either:
# 1. A real Seestar S50 telescope
# 2. A mock TCP server simulating the Seestar protocol
# 3. The seestar_alp simulator if available

# The tests above cover the basic functionality using mocks


@pytest.mark.asyncio
async def test_get_latest_preview_frame_success():
    """Test successful preview frame retrieval."""
    from unittest.mock import AsyncMock, patch

    client = SeestarClient()

    # Mock get_image_file_info to return file list
    mock_file_info = {
        "files": [
            {"name": "preview_002.jpg", "timestamp": "2026-02-15T14:30:00"},
            {"name": "preview_001.jpg", "timestamp": "2026-02-15T14:29:00"},
        ]
    }

    # Mock _download_file to return JPEG bytes
    jpeg_bytes = b"\xff\xd8\xff\xe0" + b"fake jpeg data"

    with patch.object(client, "get_image_file_info", new=AsyncMock(return_value=mock_file_info)):
        with patch.object(client, "_download_file", new=AsyncMock(return_value=jpeg_bytes)):
            # Execute
            frame = await client.get_latest_preview_frame()

            # Verify
            assert frame == jpeg_bytes
            client.get_image_file_info.assert_called_once_with("/mnt/sda1/seestar/preview/")
            client._download_file.assert_called_once_with("/mnt/sda1/seestar/preview/preview_002.jpg")


@pytest.mark.asyncio
async def test_get_latest_preview_frame_no_files():
    """Test when no preview frames available."""
    from unittest.mock import AsyncMock, patch

    client = SeestarClient()

    # Mock empty file list
    with patch.object(client, "get_image_file_info", new=AsyncMock(return_value={"files": []})):
        # Execute
        frame = await client.get_latest_preview_frame()

        # Verify
        assert frame is None


@pytest.mark.asyncio
async def test_get_latest_preview_frame_no_timestamps():
    """Test when files have no timestamps."""
    from unittest.mock import AsyncMock, patch

    client = SeestarClient()

    # Mock files without timestamps
    mock_file_info = {"files": [{"name": "preview.jpg"}]}

    with patch.object(client, "get_image_file_info", new=AsyncMock(return_value=mock_file_info)):
        # Execute
        frame = await client.get_latest_preview_frame()

        # Verify
        assert frame is None


@pytest.mark.asyncio
async def test_start_stop_video_recording():
    """Test starting and stopping video recording."""
    client = SeestarClient()

    # Mock the command sending
    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        # Test start recording
        mock_send.return_value = {"code": 0}

        result = await client.start_record_avi(filename="test_recording")
        assert result is True
        mock_send.assert_called_with("start_record_avi", {"name": "test_recording"})

        # Test stop recording
        mock_send.reset_mock()
        result = await client.stop_record_avi()
        assert result is True
        mock_send.assert_called_with("stop_record_avi", {})


@pytest.mark.asyncio
async def test_start_record_avi_without_filename():
    """Test starting recording without specifying filename."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 0}

        result = await client.start_record_avi()
        assert result is True
        mock_send.assert_called_with("start_record_avi", {})


@pytest.mark.asyncio
async def test_start_polar_align():
    """Test starting polar alignment process."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 0}

        result = await client.start_polar_align()
        assert result is True
        mock_send.assert_called_with("start_polar_align")


@pytest.mark.asyncio
async def test_stop_polar_align():
    """Test stopping polar alignment process."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 0}

        result = await client.stop_polar_align()
        assert result is True
        mock_send.assert_called_with("stop_polar_align")


@pytest.mark.asyncio
async def test_pause_polar_align():
    """Test pausing polar alignment process."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 0}

        result = await client.pause_polar_align()
        assert result is True
        mock_send.assert_called_with("pause_polar_align")


@pytest.mark.asyncio
async def test_start_scan_planet():
    """Test scanning for visible planets."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 0}

        result = await client.start_scan_planet()
        assert result is True
        mock_send.assert_called_with("iscope_start_scan_planet", {})


@pytest.mark.asyncio
async def test_start_scan_planet_failure():
    """Test planet scan failure."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 1, "message": "Scan failed"}

        with pytest.raises(CommandError, match="Failed to start planet scan"):
            await client.start_scan_planet()


@pytest.mark.asyncio
async def test_start_planet_stack():
    """Test starting planetary imaging stack."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 0}

        result = await client.start_planet_stack(planet_name="Jupiter", exposure=50, gain=100)
        assert result is True
        mock_send.assert_called_with("iscope_start_planet_stack", {"target": "Jupiter", "exposure": 50, "gain": 100})


@pytest.mark.asyncio
async def test_start_planet_stack_failure():
    """Test planet stack start failure."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 1, "message": "Target not found"}

        with pytest.raises(CommandError, match="Failed to start planet stack"):
            await client.start_planet_stack(planet_name="Mars", exposure=30, gain=80)


@pytest.mark.asyncio
async def test_stop_planet_stack():
    """Test stopping planetary imaging stack."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 0}

        result = await client.stop_planet_stack()
        assert result is True
        mock_send.assert_called_with("iscope_stop_planet_stack", {})


@pytest.mark.asyncio
async def test_stop_planet_stack_failure():
    """Test planet stack stop failure."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 1, "message": "No active stack"}

        with pytest.raises(CommandError, match="Failed to stop planet stack"):
            await client.stop_planet_stack()


@pytest.mark.asyncio
async def test_start_track_object_satellite():
    """Test starting satellite tracking."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 0}

        result = await client.start_track_object("satellite", "ISS (ZARYA)")
        assert result is True
        mock_send.assert_called_with("start_track_object", {"type": "satellite", "id": "ISS (ZARYA)"})


@pytest.mark.asyncio
async def test_start_track_object_comet():
    """Test starting comet tracking."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 0}

        result = await client.start_track_object("comet", "C/2023 A3")
        assert result is True
        mock_send.assert_called_with("start_track_object", {"type": "comet", "id": "C/2023 A3"})


@pytest.mark.asyncio
async def test_start_track_object_asteroid():
    """Test starting asteroid tracking."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 0}

        result = await client.start_track_object("asteroid", "433 Eros")
        assert result is True
        mock_send.assert_called_with("start_track_object", {"type": "asteroid", "id": "433 Eros"})


@pytest.mark.asyncio
async def test_start_track_object_failure():
    """Test object tracking failure."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 1, "message": "Object not found"}

        with pytest.raises(CommandError, match="Failed to start tracking"):
            await client.start_track_object("satellite", "UNKNOWN")


@pytest.mark.asyncio
async def test_stop_track_object_success():
    """Test stopping object tracking."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 0}

        result = await client.stop_track_object()
        assert result is True
        mock_send.assert_called_with("stop_track_object", {})


@pytest.mark.asyncio
async def test_stop_track_object_failure():
    """Test stopping object tracking failure."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 1, "message": "No tracking active"}

        with pytest.raises(CommandError, match="Failed to stop tracking"):
            await client.stop_track_object()


@pytest.mark.asyncio
async def test_start_annotate_success():
    """Test starting annotations successfully."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 0}

        result = await client.start_annotate()
        assert result is True
        mock_send.assert_called_with("start_annotate")


@pytest.mark.asyncio
async def test_start_annotate_failure():
    """Test starting annotations failure."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 1, "message": "Annotation error"}

        with pytest.raises(CommandError, match="Failed to start annotations"):
            await client.start_annotate()


@pytest.mark.asyncio
async def test_stop_annotate_success():
    """Test stopping annotations successfully."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 0}

        result = await client.stop_annotate()
        assert result is True
        mock_send.assert_called_with("stop_annotate", {})


@pytest.mark.asyncio
async def test_stop_annotate_failure():
    """Test stopping annotations failure."""
    client = SeestarClient()

    with patch.object(client, "_send_command", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"code": 1, "message": "Annotation error"}

        with pytest.raises(CommandError, match="Failed to stop annotations"):
            await client.stop_annotate()
