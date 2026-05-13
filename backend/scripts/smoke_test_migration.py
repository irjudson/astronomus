#!/usr/bin/env python3
"""Smoke test for the seestar-api migration.

Verifies that the astronomus SeestarClient (now built on the seestar-api
shim in app/clients/seestar/transport.py) still talks to a live Seestar
correctly through both the low-level and mixin APIs.

Run:
    cd backend
    python scripts/smoke_test_migration.py [--host 169.254.100.100]

Non-destructive — only reads state. No slews, no exposures.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.clients.seestar_client import SeestarClient  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("smoke")


async def run(host: str) -> int:
    client = SeestarClient()
    failures: list[str] = []

    # 1. Connect
    try:
        ok = await client.connect(host)
        assert ok, "connect returned False"
        log.info("[OK] connect() → True, state=%s", client.status.state)
    except Exception as exc:
        log.error("[FAIL] connect: %s", exc)
        return 1

    # 2. Low-level _send_command returns astronomus dict shape
    try:
        resp = await client._send_command("get_device_state", {})
        assert resp.get("code") == 0, f"non-zero code: {resp.get('code')}"
        fw = resp.get("result", {}).get("device", {}).get("firmware_ver_string")
        assert fw, "no firmware_ver_string in response"
        log.info("[OK] _send_command get_device_state → code=0, firmware=%s", fw)
    except Exception as exc:
        log.error("[FAIL] _send_command get_device_state: %s", exc)
        failures.append("send_command")

    # 3. Low-level with params
    try:
        resp = await client._send_command("scope_get_equ_coord", {})
        r = resp.get("result", {})
        assert "ra" in r and "dec" in r, f"unexpected result: {r}"
        log.info("[OK] _send_command scope_get_equ_coord → ra=%.4f dec=%.4f", r["ra"], r["dec"])
    except Exception as exc:
        log.error("[FAIL] _send_command scope_get_equ_coord: %s", exc)
        failures.append("scope_get_equ_coord")

    # 4. Mount mixin method
    try:
        state = await client.get_device_state()
        assert state is not None, "get_device_state returned None"
        log.info("[OK] mount.get_device_state() → %s", type(state).__name__)
    except Exception as exc:
        log.error("[FAIL] get_device_state mixin: %s", exc)
        failures.append("get_device_state mixin")

    # 5. Observation mixin methods
    try:
        coords = await client.get_current_coordinates()
        assert "ra" in coords and "dec" in coords, f"unexpected: {coords}"
        log.info("[OK] obs.get_current_coordinates() → %s", coords)
    except Exception as exc:
        log.error("[FAIL] get_current_coordinates: %s", exc)
        failures.append("get_current_coordinates")

    try:
        app_state = await client.get_app_state()
        log.info("[OK] obs.get_app_state() → %d keys", len(app_state) if hasattr(app_state, "__len__") else -1)
    except Exception as exc:
        log.error("[FAIL] get_app_state: %s", exc)
        failures.append("get_app_state")

    # 6. Event subscription wiring (register, disconnect, verify no crash)
    try:
        received = []
        client.subscribe_all_events(lambda ev: received.append(ev))
        await asyncio.sleep(1.5)  # let any spontaneous events come through
        log.info("[OK] subscribed to events (received %d in 1.5s)", len(received))
    except Exception as exc:
        log.error("[FAIL] event subscription: %s", exc)
        failures.append("event subscription")

    # 7. Status snapshot
    try:
        s = client.status
        assert s.connected, f"status.connected is False: {s}"
        log.info("[OK] status snapshot: connected=%s state=%s fw=%s",
                 s.connected, s.state, getattr(s, "firmware_version", None))
    except Exception as exc:
        log.error("[FAIL] status snapshot: %s", exc)
        failures.append("status snapshot")

    # 8. Disconnect
    try:
        await client.disconnect()
        log.info("[OK] disconnect() → state=%s", client.status.state)
    except Exception as exc:
        log.error("[FAIL] disconnect: %s", exc)
        failures.append("disconnect")

    if failures:
        log.error("%d FAILURE(S): %s", len(failures), ", ".join(failures))
        return 1
    log.info("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="169.254.100.100")
    args = ap.parse_args()
    raise SystemExit(asyncio.run(run(args.host)))
