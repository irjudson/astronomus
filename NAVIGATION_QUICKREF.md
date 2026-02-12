# Navigation Quick Reference

## TLDR - What We Did

Implemented telescope directional navigation using `scope_speed_move` command.

## Key Command

```python
await client._send_command("scope_speed_move", {
    "angle": 90,      # 0=right, 90=up, 180=left, 270=down
    "percent": 10,    # Speed percentage
    "level": 1,       # Speed level
    "dur_sec": 3      # Always 3
})
```

## Angle Mapping

```
     up (90°)
        ▲
        |
left ◄──┼──► right
(180°)  |  (0°)
        ▼
    down (270°)
```

## Test It

```bash
# Backend test
cd /home/irjudson/Projects/astronomus/backend
python3 test_altaz_simple.py

# Web UI
http://localhost:9247
# → Observe view → Manual Navigation → Arrow buttons
```

## Switch to Alt/Az Mode

```bash
curl -X POST http://localhost:9247/api/telescope/switch-mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "altaz"}'

curl -X POST http://localhost:9247/api/telescope/unpark
```

## Files Changed

- `backend/app/clients/seestar_client.py` - move_scope() method
- `frontend/js/telescope-controls.js` - handleNavigation() method

## Status

✅ WORKING - Tested and confirmed
