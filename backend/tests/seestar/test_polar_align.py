"""Polar alignment tests - playback-based (field scenario).

These tests are skipped unless a polar alignment recording exists.
Create recordings with:
    python -m tests.seestar.record_session \\
        --host 192.168.x.x --scenario polar_align \\
        --output tests/fixtures/recordings/

Run:  pytest tests/seestar/test_polar_align.py -m playback
"""

from pathlib import Path

import pytest
import pytest_asyncio

from app.clients.seestar_client import SeestarClient
from tests.fixtures.seestar_playback import PlaybackServerContext

pytestmark = pytest.mark.playback

POLAR_ALIGN_RECORDING = Path("tests/fixtures/recordings/polar_align.json")


def _recording_exists() -> bool:
    return POLAR_ALIGN_RECORDING.exists()


@pytest.fixture(scope="module")
def playback_address(tmp_path_factory):
    """Start playback server from recording; skip if no recording file."""
    if not _recording_exists():
        pytest.skip(f"No polar align recording at {POLAR_ALIGN_RECORDING}")


class TestPolarAlign:
    """Playback-only polar alignment tests."""

    @pytest.mark.asyncio
    async def test_load_polar_align_recording(self):
        """Recording file can be loaded and has expected interaction count."""
        if not _recording_exists():
            pytest.skip(f"No polar align recording at {POLAR_ALIGN_RECORDING}")
        from tests.fixtures.seestar_recorder import SeestarSessionRecorder

        recorder = SeestarSessionRecorder.load(str(POLAR_ALIGN_RECORDING))
        assert len(recorder.interactions) > 0
        assert recorder.metadata.description != "" or recorder.metadata.telescope != ""

    @pytest.mark.asyncio
    async def test_polar_align_command_sequence(self, tmp_rsa_key: str):
        """Playback: start_polar_align → check_polar_alignment → stop_polar_align."""
        if not _recording_exists():
            pytest.skip(f"No polar align recording at {POLAR_ALIGN_RECORDING}")

        async with PlaybackServerContext.from_recording(str(POLAR_ALIGN_RECORDING)) as (host, port):
            client = SeestarClient(private_key_path=tmp_rsa_key)
            await client.connect(host, port)
            try:
                # start PA
                started = await client.start_polar_align()
                assert isinstance(started, bool)

                # check PA
                pa_info = await client.check_polar_alignment()
                assert isinstance(pa_info, dict)

                # stop PA
                stopped = await client.stop_polar_align()
                assert isinstance(stopped, bool)
            finally:
                await client.disconnect()

    @pytest.mark.asyncio
    async def test_clear_polar_alignment(self, tmp_rsa_key: str):
        """Playback: check_polar_alignment returns a structured result."""
        if not _recording_exists():
            pytest.skip(f"No polar align recording at {POLAR_ALIGN_RECORDING}")

        async with PlaybackServerContext.from_recording(str(POLAR_ALIGN_RECORDING)) as (host, port):
            client = SeestarClient(private_key_path=tmp_rsa_key)
            await client.connect(host, port)
            try:
                pa_info = await client.check_polar_alignment()
                assert isinstance(pa_info, dict)
            finally:
                await client.disconnect()
