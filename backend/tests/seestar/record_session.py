"""CLI tool for recording live Seestar S50 sessions for playback tests.

Usage:
    python -m tests.seestar.record_session \\
        --host 192.168.1.100 \\
        --scenario polar_align \\
        --output tests/fixtures/recordings/

Scenarios:
    polar_align   - polar alignment sequence
    full_goto     - slew to a deep-sky target
    autofocus     - autofocus run
    stacking      - short stacking session

The recording is saved as <output>/<scenario>.json and can be replayed
in tests without hardware using SeestarPlaybackServer.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Ensure backend app is importable (pytest adds pythonpath; CLI needs explicit help)
_backend = Path(__file__).resolve().parent.parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from app.clients.seestar_client import SeestarClient  # noqa: E402
from tests.fixtures.seestar_recorder import SeestarSessionRecorder  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scenario implementations
# ---------------------------------------------------------------------------


async def scenario_polar_align(client: SeestarClient):
    logger.info("=== polar_align scenario ===")
    await client.start_polar_align()
    await asyncio.sleep(5)
    pa = await client.check_polar_alignment()
    logger.info(f"PA result: {pa}")
    await client.stop_polar_align()
    logger.info("polar_align scenario complete")


async def scenario_full_goto(client: SeestarClient):
    logger.info("=== full_goto scenario ===")
    result = await client.slew_to_coordinates(ra_hours=5.5755, dec_degrees=-5.39)  # Orion Nebula
    logger.info(f"Slew result: {result}")
    await asyncio.sleep(10)
    await client.stop_telescope_movement()
    logger.info("full_goto scenario complete")


async def scenario_autofocus(client: SeestarClient):
    logger.info("=== autofocus scenario ===")
    result = await client.auto_focus()
    logger.info(f"Autofocus result: {result}")
    await asyncio.sleep(30)
    await client.stop_autofocus()
    logger.info("autofocus scenario complete")


async def scenario_stacking(client: SeestarClient):
    logger.info("=== stacking scenario ===")
    await client.set_exposure(stack_exposure_ms=5000)
    result = await client.start_imaging()
    logger.info(f"Start imaging: {result}")
    await asyncio.sleep(15)
    await client.stop_imaging()
    logger.info("stacking scenario complete")


_SCENARIOS = {
    "polar_align": scenario_polar_align,
    "full_goto": scenario_full_goto,
    "autofocus": scenario_autofocus,
    "stacking": scenario_stacking,
}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main():
    parser = argparse.ArgumentParser(description="Record a live Seestar session for offline test playback")
    parser.add_argument("--host", required=True, help="Telescope IP or hostname")
    parser.add_argument("--port", type=int, default=4700, help="Telescope port (default: 4700)")
    parser.add_argument(
        "--scenario",
        required=True,
        choices=list(_SCENARIOS.keys()),
        help="Scenario to record",
    )
    parser.add_argument(
        "--output",
        default="tests/fixtures/recordings",
        help="Directory to save recording (default: tests/fixtures/recordings)",
    )
    parser.add_argument(
        "--key",
        default=None,
        help="Path to RSA private key (uses config default if not set)",
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{args.scenario}.json"

    recorder = SeestarSessionRecorder(description=f"Live recording: {args.scenario}")

    logger.info(f"Recording scenario '{args.scenario}' from {args.host}:{args.port}")
    logger.info(f"Output: {output_file}")

    async with recorder.intercept_connection(args.host, args.port) as (proxy_host, proxy_port):
        client = SeestarClient(private_key_path=args.key) if args.key else SeestarClient()
        await client.connect(proxy_host, proxy_port)
        try:
            scenario_fn = _SCENARIOS[args.scenario]
            await scenario_fn(client)
        finally:
            await client.disconnect()

    recorder.save(str(output_file), description=f"Live recording: {args.scenario}")
    logger.info(f"Recording saved to {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
