#!/usr/bin/env python3
"""Reboot the Seestar telescope."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.seestar_client import SeestarClient


async def reboot_telescope():
    """Reboot the telescope."""
    client = SeestarClient()

    try:
        print("Connecting to telescope...")
        await client.connect("192.168.2.47", 4700)
        print(f"Connected. Current state: {client.status.state}")

        print("\nSending reboot command...")
        response = await client._send_command("pi_reboot", {})
        print(f"Reboot response: {response}")

        print("\nTelescope is rebooting. It will take about 30-60 seconds to come back online.")
        print("You can reconnect after it restarts.")

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        if client.connected:
            await client.disconnect()


if __name__ == "__main__":
    asyncio.run(reboot_telescope())
