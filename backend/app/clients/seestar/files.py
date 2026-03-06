"""Image file management: list, retrieve, delete, live preview."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

from .types import CommandError, ConnectionError


class SeestarFilesMixin:
    """Mixin providing image file management and live preview commands."""

    # ==========================================
    # Phase 10: Image Retrieval
    # ==========================================

    async def list_images(self, image_type: str = "stacked") -> List[Dict[str, Any]]:
        """List available images on telescope storage.

        Args:
            image_type: Type of images to list - "stacked", "raw", or "all"

        Returns:
            List of dicts with {filename, size, timestamp, format}

        Raises:
            CommandError: If query fails
        """
        self.logger.info(f"Listing images of type: {image_type}")

        # Use get_img_file_info to query directory
        # Seestar stores images in specific paths:
        # - Stacked images: typically in /mnt/seestar/stack/
        # - Raw frames: typically in /mnt/seestar/raw/

        images = []

        if image_type in ("stacked", "all"):
            stack_info = await self.get_image_file_info("/mnt/seestar/stack/")
            if "files" in stack_info:
                for file_info in stack_info["files"]:
                    images.append(
                        {
                            "filename": file_info.get("name", ""),
                            "size": file_info.get("size", 0),
                            "timestamp": file_info.get("timestamp", ""),
                            "format": file_info.get("format", "fits"),
                            "type": "stacked",
                        }
                    )

        if image_type in ("raw", "all"):
            raw_info = await self.get_image_file_info("/mnt/seestar/raw/")
            if "files" in raw_info:
                for file_info in raw_info["files"]:
                    images.append(
                        {
                            "filename": file_info.get("name", ""),
                            "size": file_info.get("size", 0),
                            "timestamp": file_info.get("timestamp", ""),
                            "format": file_info.get("format", "fits"),
                            "type": "raw",
                        }
                    )

        self.logger.info(f"Found {len(images)} images")
        return images

    async def get_stacked_image(self, filename: str) -> bytes:
        """Download stacked FITS/JPEG image from telescope.

        Uses file transfer protocol on port 4801.

        Args:
            filename: Name of stacked image file to download

        Returns:
            Raw image bytes

        Raises:
            ConnectionError: If file transfer connection fails
            CommandError: If download fails
        """
        self.logger.info(f"Downloading stacked image: {filename}")

        if not self._host:
            raise ConnectionError("Not connected to telescope")

        # Download file via port 4801
        image_data = await self._download_file(f"/mnt/seestar/stack/{filename}")

        self.logger.info(f"Downloaded {len(image_data)} bytes")
        return image_data

    async def get_raw_frame(self, filename: str) -> bytes:
        """Download individual raw frame from telescope.

        Uses file transfer protocol on port 4801.

        Args:
            filename: Name of raw frame file to download

        Returns:
            Raw frame bytes

        Raises:
            ConnectionError: If file transfer connection fails
            CommandError: If download fails
        """
        self.logger.info(f"Downloading raw frame: {filename}")

        if not self._host:
            raise ConnectionError("Not connected to telescope")

        # Download file via port 4801
        frame_data = await self._download_file(f"/mnt/seestar/raw/{filename}")

        self.logger.info(f"Downloaded {len(frame_data)} bytes")
        return frame_data

    async def delete_image(self, filename: str) -> bool:
        """Delete image from telescope storage.

        Args:
            filename: Full path to image file to delete

        Returns:
            True if deletion successful

        Raises:
            CommandError: If deletion fails
        """
        self.logger.info(f"Deleting image: {filename}")

        # Use system command to delete file
        # Note: This requires appropriate permissions and may not be available in all firmware versions
        response = await self._send_command("pi_execute_cmd", {"cmd": f"rm {filename}"})

        success = response.get("result") == 0
        self.logger.info(f"Delete {'successful' if success else 'failed'}")
        return success

    async def get_live_preview(self) -> bytes:
        """Capture current preview frame (RTMP stream frame grab).

        Note: This method requires RTMP stream access on ports 4554/4555.

        Returns:
            Preview frame bytes as JPEG

        Raises:
            ConnectionError: If RTMP stream not available
        """
        from app.services.rtmp_preview_service import get_preview_service

        # Get or create preview service (port 4554 is Seestar S50 RTMP port)
        preview_service = get_preview_service(host=self._host or "192.168.2.47", port=4554)

        # Start the service if not already running
        if not preview_service.is_running:
            preview_service.start()
            # Give it a moment to connect and capture first frame
            await asyncio.sleep(2.0)

        # Get latest frame
        frame_bytes = preview_service.get_latest_frame_jpeg(quality=85)

        if frame_bytes is None:
            raise ConnectionError("No preview frame available. RTMP stream may not be active.")

        return frame_bytes

    async def get_latest_preview_frame(self) -> Optional[bytes]:
        """Get latest preview frame from telescope filesystem.

        Uses file-based approach (not RTSP) to fetch preview frames.
        This is an alternative to get_live_preview() that works when RTSP is unavailable.

        Returns:
            JPEG bytes of latest preview frame, or None if no frames available

        Raises:
            ConnectionError: If not connected to telescope
            CommandError: If file listing or download fails
        """
        # List files - let exceptions propagate
        preview_info = await self.get_image_file_info("/mnt/sda1/seestar/preview/")

        if "files" not in preview_info or not preview_info["files"]:
            self.logger.warning("No preview frames available")
            return None

        # Filter out files without timestamps and sort
        files_with_timestamps = [f for f in preview_info["files"] if "timestamp" in f]
        if not files_with_timestamps:
            self.logger.warning("No timestamped preview frames available")
            return None

        files = sorted(files_with_timestamps, key=lambda f: f["timestamp"], reverse=True)

        latest_file = files[0]
        if "name" not in latest_file:
            raise CommandError("Invalid file info: missing 'name' field")
        file_path = f"/mnt/sda1/seestar/preview/{latest_file['name']}"

        self.logger.info(f"Downloading latest preview frame: {file_path}")

        # Download file - let exceptions propagate
        frame_bytes = await self._download_file(file_path)

        return frame_bytes

    async def _download_file(self, remote_path: str) -> bytes:
        """Download file from telescope via port 4801.

        Internal method for file transfer protocol.

        Args:
            remote_path: Full path to file on telescope

        Returns:
            File contents as bytes

        Raises:
            ConnectionError: If connection to file server fails
            CommandError: If file not found or transfer fails
        """
        if not self._host:
            raise ConnectionError("Not connected to telescope")

        self.logger.info(f"Opening file transfer connection to {self._host}:{self.FILE_TRANSFER_PORT}")

        try:
            # Open TCP connection to file transfer port
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self.FILE_TRANSFER_PORT), timeout=self.CONNECTION_TIMEOUT
            )

            # Send file request (protocol may vary - this is a basic implementation)
            # Format: JSON request with file path
            request = json.dumps({"file": remote_path}) + "\n"
            writer.write(request.encode("utf-8"))
            await writer.drain()

            # Read file data
            file_data = b""
            while True:
                chunk = await reader.read(self.RECEIVE_BUFFER_SIZE)
                if not chunk:
                    break
                file_data += chunk

            writer.close()
            await writer.wait_closed()

            if not file_data:
                raise CommandError(f"File not found or empty: {remote_path}")

            self.logger.info(f"Downloaded {len(file_data)} bytes from {remote_path}")
            return file_data

        except asyncio.TimeoutError:
            raise ConnectionError(f"Timeout connecting to file server on port {self.FILE_TRANSFER_PORT}")
        except Exception as e:
            raise CommandError(f"File download failed: {str(e)}")
