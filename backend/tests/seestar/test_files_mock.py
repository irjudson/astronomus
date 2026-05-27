"""Mock-server tests for SeestarFilesMixin methods (no real hardware required).

Run with:  pytest tests/seestar/test_files_mock.py -m mock
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.clients.seestar.types import CommandError, ConnectionError
from app.clients.seestar_client import SeestarClient
from tests.seestar.mock_server import MockSeestarServer, _COMMAND_RESPONSES

pytestmark = pytest.mark.mock


class TestFilesMixinListImages:
    @pytest.mark.asyncio
    async def test_list_images_stacked_returns_list(self, mock_client: SeestarClient):
        # Mock get_image_file_info to return empty files dict (no crash)
        with patch.object(mock_client, "get_image_file_info", new=AsyncMock(return_value={})):
            result = await mock_client.list_images(image_type="stacked")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_images_raw_returns_list(self, mock_client: SeestarClient):
        with patch.object(mock_client, "get_image_file_info", new=AsyncMock(return_value={})):
            result = await mock_client.list_images(image_type="raw")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_list_images_all_queries_both_paths(self, mock_client: SeestarClient):
        calls = []

        async def mock_get_info(path=""):
            calls.append(path)
            return {"files": [{"name": "test.fits", "size": 1024, "timestamp": "2026-01-01", "format": "fits"}]}

        with patch.object(mock_client, "get_image_file_info", new=mock_get_info):
            result = await mock_client.list_images(image_type="all")

        assert len(calls) == 2
        assert len(result) == 2
        assert result[0]["type"] == "stacked"
        assert result[1]["type"] == "raw"

    @pytest.mark.asyncio
    async def test_list_images_with_file_entries(self, mock_client: SeestarClient):
        file_entry = {"name": "img001.fits", "size": 2048000, "timestamp": "2026-01-01T20:00:00", "format": "fits"}

        async def mock_get_info(path=""):
            return {"files": [file_entry]}

        with patch.object(mock_client, "get_image_file_info", new=mock_get_info):
            result = await mock_client.list_images(image_type="stacked")

        assert len(result) == 1
        assert result[0]["filename"] == "img001.fits"
        assert result[0]["size"] == 2048000
        assert result[0]["type"] == "stacked"


class TestFilesMixinDeleteImage:
    @pytest.mark.asyncio
    async def test_delete_image_success(self, mock_client: SeestarClient, mock_server_obj: MockSeestarServer):
        original = _COMMAND_RESPONSES.get("pi_execute_cmd")
        _COMMAND_RESPONSES["pi_execute_cmd"] = {"result": 0, "code": 0}
        try:
            result = await mock_client.delete_image("/mnt/seestar/stack/img001.fits")
            assert isinstance(result, bool)
        finally:
            if original is not None:
                _COMMAND_RESPONSES["pi_execute_cmd"] = original
            else:
                _COMMAND_RESPONSES.pop("pi_execute_cmd", None)

    @pytest.mark.asyncio
    async def test_delete_image_failure(self, mock_client: SeestarClient):
        original = _COMMAND_RESPONSES.get("pi_execute_cmd")
        _COMMAND_RESPONSES["pi_execute_cmd"] = {"result": -1, "code": 105}
        try:
            result = await mock_client.delete_image("/mnt/seestar/stack/img001.fits")
            assert result is False
        finally:
            if original is not None:
                _COMMAND_RESPONSES["pi_execute_cmd"] = original
            else:
                _COMMAND_RESPONSES.pop("pi_execute_cmd", None)


class TestFilesMixinGetStacked:
    @pytest.mark.asyncio
    async def test_get_stacked_image_not_connected_raises(self, mock_client: SeestarClient):
        # Temporarily clear host to simulate disconnected
        original_host = mock_client._host
        mock_client._host = None
        try:
            with pytest.raises(ConnectionError):
                await mock_client.get_stacked_image("img001.fits")
        finally:
            mock_client._host = original_host

    @pytest.mark.asyncio
    async def test_get_stacked_image_calls_download(self, mock_client: SeestarClient):
        with patch.object(mock_client, "_download_file", new=AsyncMock(return_value=b"fits-data")):
            result = await mock_client.get_stacked_image("img001.fits")
        assert result == b"fits-data"


class TestFilesMixinGetRawFrame:
    @pytest.mark.asyncio
    async def test_get_raw_frame_not_connected_raises(self, mock_client: SeestarClient):
        original_host = mock_client._host
        mock_client._host = None
        try:
            with pytest.raises(ConnectionError):
                await mock_client.get_raw_frame("frame001.fits")
        finally:
            mock_client._host = original_host

    @pytest.mark.asyncio
    async def test_get_raw_frame_calls_download(self, mock_client: SeestarClient):
        with patch.object(mock_client, "_download_file", new=AsyncMock(return_value=b"raw-data")):
            result = await mock_client.get_raw_frame("frame001.fits")
        assert result == b"raw-data"


class TestFilesMixinGetLivePreview:
    @pytest.mark.asyncio
    async def test_get_live_preview_returns_jpeg_bytes(self, mock_client: SeestarClient):
        mock_svc = MagicMock()
        mock_svc.is_running = True
        mock_svc.get_latest_frame_jpeg.return_value = b"\xff\xd8\xff\xe0fake"

        # get_preview_service is imported locally inside get_live_preview, patch at source module
        with patch("app.services.rtmp_preview_service.get_preview_service", return_value=mock_svc):
            result = await mock_client.get_live_preview()

        assert result == b"\xff\xd8\xff\xe0fake"

    @pytest.mark.asyncio
    async def test_get_live_preview_starts_service_when_not_running(self, mock_client: SeestarClient):
        mock_svc = MagicMock()
        mock_svc.is_running = False
        mock_svc.get_latest_frame_jpeg.return_value = b"\xff\xd8frame"

        with (
            patch("app.services.rtmp_preview_service.get_preview_service", return_value=mock_svc),
            patch("asyncio.sleep", new=AsyncMock()),
        ):
            result = await mock_client.get_live_preview()

        mock_svc.start.assert_called_once()
        assert result == b"\xff\xd8frame"

    @pytest.mark.asyncio
    async def test_get_live_preview_raises_when_no_frame(self, mock_client: SeestarClient):
        mock_svc = MagicMock()
        mock_svc.is_running = True
        mock_svc.get_latest_frame_jpeg.return_value = None

        with patch("app.services.rtmp_preview_service.get_preview_service", return_value=mock_svc):
            with pytest.raises(ConnectionError, match="No preview frame available"):
                await mock_client.get_live_preview()


class TestFilesMixinGetLatestPreviewFrame:
    @pytest.mark.asyncio
    async def test_get_latest_preview_frame_returns_none_when_no_files(self, mock_client: SeestarClient):
        with patch.object(mock_client, "get_image_file_info", new=AsyncMock(return_value={})):
            result = await mock_client.get_latest_preview_frame()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_preview_frame_returns_none_when_empty_files(self, mock_client: SeestarClient):
        with patch.object(mock_client, "get_image_file_info", new=AsyncMock(return_value={"files": []})):
            result = await mock_client.get_latest_preview_frame()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_preview_frame_no_timestamps_returns_none(self, mock_client: SeestarClient):
        files = [{"name": "frame.jpg", "size": 1024}]
        with patch.object(mock_client, "get_image_file_info", new=AsyncMock(return_value={"files": files})):
            result = await mock_client.get_latest_preview_frame()
        assert result is None

    @pytest.mark.asyncio
    async def test_get_latest_preview_frame_downloads_most_recent(self, mock_client: SeestarClient):
        files = [
            {"name": "frame001.jpg", "timestamp": "2026-01-01T20:00:00", "size": 1024},
            {"name": "frame002.jpg", "timestamp": "2026-01-01T21:00:00", "size": 2048},
        ]
        with (
            patch.object(mock_client, "get_image_file_info", new=AsyncMock(return_value={"files": files})),
            patch.object(mock_client, "_download_file", new=AsyncMock(return_value=b"\xff\xd8frame")) as mock_dl,
        ):
            result = await mock_client.get_latest_preview_frame()

        # Should download the most recent (frame002)
        assert b"\xff\xd8frame" == result
        called_path = mock_dl.call_args[0][0]
        assert "frame002.jpg" in called_path

    @pytest.mark.asyncio
    async def test_get_latest_preview_frame_raises_when_name_missing(self, mock_client: SeestarClient):
        files = [{"timestamp": "2026-01-01T20:00:00", "size": 1024}]
        with patch.object(mock_client, "get_image_file_info", new=AsyncMock(return_value={"files": files})):
            with pytest.raises(CommandError, match="missing 'name'"):
                await mock_client.get_latest_preview_frame()


class TestFilesMixinDownloadFile:
    @pytest.mark.asyncio
    async def test_download_file_not_connected_raises(self, mock_client: SeestarClient):
        original = mock_client._host
        mock_client._host = None
        try:
            with pytest.raises(ConnectionError):
                await mock_client._download_file("/some/file.fits")
        finally:
            mock_client._host = original

    @pytest.mark.asyncio
    async def test_download_file_timeout_raises_connection_error(self, mock_client: SeestarClient):
        import asyncio

        with patch("asyncio.open_connection", side_effect=asyncio.TimeoutError()):
            with pytest.raises(ConnectionError, match="Timeout"):
                await mock_client._download_file("/some/file.fits")

    @pytest.mark.asyncio
    async def test_download_file_other_error_raises_command_error(self, mock_client: SeestarClient):
        with patch("asyncio.open_connection", side_effect=OSError("connection refused")):
            with pytest.raises(CommandError, match="File download failed"):
                await mock_client._download_file("/some/file.fits")
