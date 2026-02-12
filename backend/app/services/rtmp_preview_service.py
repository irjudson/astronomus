"""RTSP Preview Service for Seestar S50 Telescope.

Captures frames from the RTSP video stream and serves them as preview images.
"""

import logging
import threading
from datetime import datetime
from io import BytesIO
from typing import Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class RTMPPreviewService:
    """Service to capture and serve preview frames from RTSP stream."""

    def __init__(self, host: str = "192.168.2.47", port: int = 4554):
        """Initialize RTSP preview service.

        Args:
            host: Telescope IP address
            port: RTSP port (4554 for Seestar S50 live stream)
        """
        self.host = host
        self.port = port
        # Seestar S50 uses RTSP format: rtsp://IP:PORT/stream
        self.rtmp_url = f"rtsp://{host}:{port}/stream"

        self.latest_frame: Optional[np.ndarray] = None
        self.latest_frame_time: Optional[datetime] = None
        self.is_running: bool = False
        self.capture_thread: Optional[threading.Thread] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self._first_frame_logged: bool = False

        logger.info(f"RTSPPreviewService initialized for {self.rtmp_url}")

    def start(self):
        """Start capturing frames from RTSP stream."""
        if self.is_running:
            logger.warning("RTSP preview service already running")
            return

        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        logger.info("RTMP preview service started")

    def stop(self):
        """Stop capturing frames."""
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=5.0)
            self.capture_thread = None

        if self.cap:
            self.cap.release()
            self.cap = None

        logger.info("RTMP preview service stopped")

    def _capture_loop(self):
        """Background thread loop to capture frames from RTMP stream."""
        retry_count = 0
        max_retries = 3

        while self.is_running:
            try:
                logger.info(f"Connecting to RTMP stream: {self.rtmp_url}")
                self.cap = cv2.VideoCapture(self.rtmp_url, cv2.CAP_FFMPEG)

                if not self.cap.isOpened():
                    logger.error("Failed to open RTMP stream")
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"Max retries ({max_retries}) reached, stopping")
                        self.is_running = False
                        break

                    # Wait before retry
                    retry_delay = min(5 * retry_count, 30)  # Cap at 30 seconds
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    for _ in range(retry_delay * 10):  # Check is_running every 0.1s
                        if not self.is_running:
                            break
                        threading.Event().wait(0.1)
                    continue

                logger.info("RTMP stream connected successfully")
                retry_count = 0

                while self.is_running:
                    ret, frame = self.cap.read()

                    if not ret:
                        logger.warning("Failed to read frame from RTMP stream")
                        break

                    # Store the latest frame
                    self.latest_frame = frame
                    self.latest_frame_time = datetime.utcnow()

                    # Log frame dimensions on first capture only
                    if not self._first_frame_logged and self.latest_frame is not None:
                        height, width = self.latest_frame.shape[:2]
                        logger.info(f"RTSP frame captured: {width}x{height} (WxH)")
                        self._first_frame_logged = True

                    # Capture at ~1 FPS (adjust as needed)
                    threading.Event().wait(1.0)

            except Exception as e:
                logger.error(f"Error in RTMP capture loop: {e}", exc_info=True)
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error(f"Max retries ({max_retries}) reached, stopping")
                    self.is_running = False
                    break

                # Wait before retry
                retry_delay = min(5 * retry_count, 30)
                logger.info(f"Retrying in {retry_delay} seconds...")
                for _ in range(retry_delay * 10):
                    if not self.is_running:
                        break
                    threading.Event().wait(0.1)

            finally:
                if self.cap:
                    self.cap.release()
                    self.cap = None

    def get_latest_frame_jpeg(self, quality: int = 85) -> Optional[bytes]:
        """Get the latest captured frame as JPEG bytes.

        Args:
            quality: JPEG quality (1-100)

        Returns:
            JPEG image bytes or None if no frame available
        """
        if self.latest_frame is None:
            return None

        try:
            # Convert BGR (OpenCV) to RGB (PIL)
            rgb_frame = cv2.cvtColor(self.latest_frame, cv2.COLOR_BGR2RGB)

            # Convert to PIL Image
            pil_image = Image.fromarray(rgb_frame)

            # Save to BytesIO as JPEG
            buffer = BytesIO()
            pil_image.save(buffer, format="JPEG", quality=quality)
            buffer.seek(0)

            return buffer.getvalue()

        except Exception as e:
            logger.error(f"Error converting frame to JPEG: {e}", exc_info=True)
            return None

    def get_frame_info(self) -> dict:
        """Get information about the latest captured frame.

        Returns:
            Dict with frame info (time, size, etc.)
        """
        if self.latest_frame is None:
            return {"available": False, "message": "No frame available"}

        height, width = self.latest_frame.shape[:2]
        return {
            "available": True,
            "timestamp": self.latest_frame_time.isoformat() if self.latest_frame_time else None,
            "width": width,
            "height": height,
            "is_running": self.is_running,
        }


# Global instance
_preview_service: Optional[RTMPPreviewService] = None


def get_preview_service(host: str = "192.168.2.47", port: int = 4554) -> RTMPPreviewService:
    """Get or create the global RTMP preview service instance.

    Args:
        host: Telescope IP address
        port: RTMP port

    Returns:
        RTMPPreviewService instance
    """
    global _preview_service

    if _preview_service is None:
        _preview_service = RTMPPreviewService(host=host, port=port)

    return _preview_service
