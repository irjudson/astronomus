"""RTSP Preview Service for Seestar S50 Telescope.

Captures frames from the RTSP video stream and serves them as preview images.
"""

import logging
import threading
from datetime import datetime
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class RTMPPreviewService:
    """Service to capture and serve preview frames from RTSP stream."""

    def __init__(self, host: str = "192.168.2.47", port: int = 4554):
        self.host = host
        self.port = port
        self.rtmp_url = f"rtsp://{host}:{port}/stream"

        self.latest_frame: Optional[np.ndarray] = None
        self.latest_frame_time: Optional[datetime] = None
        self.latest_frame_jpeg: Optional[bytes] = None  # cached, encoded once per capture
        self._frame_seq: int = 0  # increments with every new frame

        self.is_running: bool = False
        self.capture_thread: Optional[threading.Thread] = None
        self.cap: Optional[cv2.VideoCapture] = None
        self._first_frame_logged: bool = False

        # Condition variable: capture thread notifies when a new frame arrives
        self._frame_cond = threading.Condition(threading.Lock())

        logger.info(f"RTSPPreviewService initialized for {self.rtmp_url}")

    def start(self):
        """Start capturing frames from RTSP stream."""
        if self.is_running:
            logger.warning("RTSP preview service already running")
            return

        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        logger.info("RTSP preview service started")

    def stop(self):
        """Stop capturing frames."""
        self.is_running = False
        with self._frame_cond:
            self._frame_cond.notify_all()  # wake any waiting callers

        if self.capture_thread:
            self.capture_thread.join(timeout=5.0)
            self.capture_thread = None

        if self.cap:
            self.cap.release()
            self.cap = None

        logger.info("RTSP preview service stopped")

    def _capture_loop(self):
        """Background thread: read frames as fast as the stream delivers them."""
        retry_count = 0
        max_retries = 3

        while self.is_running:
            try:
                logger.info(f"Connecting to RTSP stream: {self.rtmp_url}")
                self.cap = cv2.VideoCapture(self.rtmp_url, cv2.CAP_FFMPEG)

                # Minimize internal buffer so we always get the freshest frame
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                if not self.cap.isOpened():
                    logger.error("Failed to open RTSP stream")
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"Max retries ({max_retries}) reached, stopping")
                        self.is_running = False
                        break

                    delay = min(5 * retry_count, 30)
                    logger.info(f"Retrying in {delay}s...")
                    for _ in range(delay * 10):
                        if not self.is_running:
                            break
                        threading.Event().wait(0.1)
                    continue

                logger.info("RTSP stream connected")
                retry_count = 0

                while self.is_running:
                    ret, frame = self.cap.read()

                    if not ret:
                        logger.warning("Failed to read frame — reconnecting")
                        break

                    # Encode JPEG once here; use cv2 (faster than PIL round-trip)
                    ok, jpeg_buf = cv2.imencode(
                        ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
                    )
                    if not ok:
                        continue

                    now = datetime.utcnow()

                    with self._frame_cond:
                        self.latest_frame = frame
                        self.latest_frame_jpeg = jpeg_buf.tobytes()
                        self.latest_frame_time = now
                        self._frame_seq += 1
                        self._frame_cond.notify_all()

                    if not self._first_frame_logged:
                        h, w = frame.shape[:2]
                        logger.info(f"First RTSP frame: {w}x{h}")
                        self._first_frame_logged = True

                    # cap.read() already blocks until the next frame arrives from
                    # the RTSP stream, so no additional sleep is needed here.
                    # This keeps us at the stream's native frame rate with minimal lag.

            except Exception as e:
                logger.error(f"Error in RTSP capture loop: {e}", exc_info=True)
                retry_count += 1
                if retry_count >= max_retries:
                    self.is_running = False
                    break
                delay = min(5 * retry_count, 30)
                for _ in range(delay * 10):
                    if not self.is_running:
                        break
                    threading.Event().wait(0.1)

            finally:
                if self.cap:
                    self.cap.release()
                    self.cap = None

    def get_latest_frame_jpeg(self, quality: int = 80) -> Optional[bytes]:
        """Return the cached JPEG of the most recently captured frame.

        The ``quality`` parameter is ignored — quality is fixed at encode time
        in the capture loop. It is kept for API compatibility.
        """
        with self._frame_cond:
            return self.latest_frame_jpeg

    def wait_for_new_frame(
        self, after_seq: int, timeout: float = 1.0
    ) -> Tuple[Optional[bytes], int]:
        """Block until a frame newer than *after_seq* is available, or timeout.

        Returns (jpeg_bytes, new_seq).  If the service stops or times out,
        returns whatever the latest frame is (may be None).
        """
        with self._frame_cond:
            self._frame_cond.wait_for(
                lambda: self._frame_seq > after_seq or not self.is_running,
                timeout=timeout,
            )
            return self.latest_frame_jpeg, self._frame_seq

    def get_frame_info(self) -> dict:
        with self._frame_cond:
            if self.latest_frame is None:
                return {"available": False, "message": "No frame available"}
            h, w = self.latest_frame.shape[:2]
            return {
                "available": True,
                "timestamp": self.latest_frame_time.isoformat() if self.latest_frame_time else None,
                "width": w,
                "height": h,
                "is_running": self.is_running,
                "frame_seq": self._frame_seq,
            }


# Global singleton
_preview_service: Optional[RTMPPreviewService] = None


def get_preview_service(host: str = "192.168.2.47", port: int = 4554) -> RTMPPreviewService:
    global _preview_service
    if _preview_service is None:
        _preview_service = RTMPPreviewService(host=host, port=port)
    return _preview_service
