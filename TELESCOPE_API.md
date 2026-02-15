# Telescope API Documentation

Complete API reference for telescope control and image management.

## Base URLs
- **Main API**: `/api/telescope/*`
- **Features API**: `/api/telescope/features/*`

---

## Connection & Status

### POST /telescope/connect
Connect to telescope.
```json
Request: {"host": "192.168.2.47", "port": 4700}
Response: {"status": "connected", "connected": true}
```

### POST /telescope/disconnect
Disconnect from telescope.
```json
Response: {"status": "disconnected"}
```

### GET /telescope/status
Get current telescope status.
```json
Response: {
  "connected": true,
  "state": "idle|tracking|slewing|stacking",
  "firmware_version": "1.2.3",
  "is_tracking": true,
  "current_target": "M31",
  "current_ra_hours": 0.71,
  "current_dec_degrees": 41.27,
  "last_error": null
}
```

### GET /telescope/coordinates
Get current RA/Dec coordinates.
```json
Response: {"ra": 0.71, "dec": 41.27}
```

### GET /telescope/app-state
Get telescope application state.
```json
Response: {"stage": "Idle|AutoGoto|Stack|..."}
```

---

## Movement & Positioning

### POST /telescope/move
Direct mount movement control.
```json
Request: {"action": "up|down|left|right|stop|abort", "speed": 0.5}
Response: {"status": "moving|stopped", "action": "up"}
```

### POST /telescope/goto
Slew to RA/Dec coordinates.
```json
Request: {"ra": 0.71, "dec": 41.27, "target_name": "M31"}
Response: {"status": "slewing"}
```

### POST /telescope/stop-slew
Stop current slew/goto.
```json
Response: {"status": "stopped"}
```

### POST /telescope/park
Park telescope.
```json
Response: {"status": "parked"}
```

### POST /telescope/unpark
Unpark telescope.
```json
Response: {"status": "unparked"}
```

### POST /telescope/switch-mode
Switch mount mode (alt/az vs equatorial).
```json
Request: {"mode": "altaz|equatorial"}
Response: {"status": "mode_switched", "mode": "equatorial"}
```

---

## Imaging & Stacking

### POST /telescope/start-imaging
Start imaging/stacking.
```json
Request: {"restart": true}
Response: {"status": "imaging", "message": "Imaging started"}
```

### POST /telescope/stop-imaging
Stop imaging/stacking.
```json
Response: {"status": "stopped", "message": "Imaging stopped"}
```

### POST /telescope/start-preview
Start preview mode without coordinates.
```json
Request: {"mode": "terrestrial|solar|deepsky"}
Response: {"status": "preview_started"}
```

### GET /telescope/stacking-status
Get current stacking progress.
```json
Response: {
  "stage": "Stacking",
  "frames_captured": 50,
  "total_frames": 100,
  "progress_percent": 50
}
```

---

## Image Access

### GET /telescope/features/images/list
List available images on telescope.
```json
Query: ?image_type=stacked|preview|raw&limit=10
Response: {
  "images": [
    {"filename": "M31_stack.fit", "size": 12345678, "created": "2024-01-01T00:00:00Z"}
  ]
}
```

### GET /telescope/features/images/download/{filename}
Download stacked image from telescope.
```
Response: Binary image data (application/octet-stream)
```

### GET /telescope/features/images/raw/{filename}
Download raw frame from telescope.
```
Response: Binary image data (application/octet-stream)
```

### GET /telescope/features/images/info
Get image file information.
```json
Query: ?file_path=/path/to/image.fit
Response: {"width": 1920, "height": 1080, "format": "FITS"}
```

### DELETE /telescope/features/images/{filename}
Delete image from telescope.
```json
Response: {"success": true}
```

---

## Preview & Live Imaging

### GET /telescope/preview
Get latest preview image.
```
Response: Binary image data (image/jpeg)
```

### GET /telescope/preview/latest
Get latest preview with metadata.
```json
Response: {
  "image_data": "base64...",
  "timestamp": "2024-01-01T00:00:00Z",
  "exposure": 1.0
}
```

### GET /telescope/preview/download
Download preview image file.
```
Query: ?filename=preview.jpg
Response: Binary image data
```

### GET /telescope/live-preview
Get live preview stream info.
```json
Response: {"url": "rtmp://...", "active": true}
```

### GET /telescope/preview-info
Get preview stream information.
```json
Response: {"streaming": true, "resolution": "1920x1080"}
```

---

## Plan Execution

### POST /telescope/execute
Execute observation plan.
```json
Request: {
  "scheduled_targets": [
    {"name": "M31", "ra": 0.71, "dec": 41.27, "exposure": 10, "frames": 100}
  ],
  "park_when_done": true
}
Response: {"execution_id": "abc123", "status": "starting"}
```

### GET /telescope/progress
Monitor execution progress.
```json
Query: ?execution_id=abc123
Response: {
  "execution_id": "abc123",
  "state": "running",
  "current_target_index": 0,
  "total_targets": 5,
  "progress_percent": 20
}
```

### POST /telescope/abort
Abort current execution.
```json
Response: {"status": "aborted"}
```

### POST /telescope/plan/start
Start plan execution (alternate).
```json
Request: {"plan_id": "plan123"}
Response: {"status": "started"}
```

### POST /telescope/plan/stop
Stop plan execution.
```json
Response: {"status": "stopped"}
```

### GET /telescope/plan/state
Get plan execution state.
```json
Response: {"state": "idle|running|paused|completed"}
```

---

## Focuser & Imaging Controls

### POST /telescope/features/focuser/move
Move focuser.
```json
Request: {"steps": 100, "direction": "in|out"}
Response: {"status": "moving"}
```

### POST /telescope/features/focuser/stop
Stop focuser movement.
```json
Response: {"status": "stopped"}
```

### POST /telescope/features/focuser/factory-reset
Reset focuser to factory position.
```json
Response: {"status": "reset"}
```

### POST /telescope/features/imaging/autofocus
Start autofocus routine.
```json
Response: {"status": "autofocus_started"}
```

### POST /telescope/features/imaging/exposure
Set exposure time.
```json
Request: {"exposure_seconds": 10}
Response: {"status": "exposure_set"}
```

### POST /telescope/features/imaging/dither
Enable/disable dithering.
```json
Request: {"enabled": true, "pixels": 5}
Response: {"status": "dithering_enabled"}
```

---

## Hardware Control

### POST /telescope/features/hardware/dew-heater
Control dew heater.
```json
Request: {"enabled": true, "power": 50}
Response: {"status": "on", "power": 50}
```

### GET /telescope/features/hardware/dew-heater/status
Get dew heater status.
```json
Response: {"enabled": true, "power": 50}
```

### POST /telescope/features/hardware/dc-output
Control DC output ports.
```json
Request: {"port": 1, "enabled": true}
Response: {"status": "enabled"}
```

---

## System Info & Control

### GET /telescope/features/system/info
Get telescope system information.
```json
Response: {
  "model": "Seestar S50",
  "firmware": "1.2.3",
  "serial": "ABC123"
}
```

### GET /telescope/features/system/time
Get telescope system time.
```json
Response: {"time": "2024-01-01T00:00:00Z"}
```

### POST /telescope/features/system/time
Set telescope system time.
```json
Request: {"time": "2024-01-01T00:00:00Z"}
Response: {"status": "time_set"}
```

### POST /telescope/features/system/location
Set telescope location.
```json
Request: {"latitude": 45.0, "longitude": -111.0, "elevation": 1234}
Response: {"status": "location_set"}
```

### POST /telescope/features/system/shutdown
Shutdown telescope.
```json
Response: {"status": "shutting_down"}
```

### POST /telescope/features/system/reboot
Reboot telescope.
```json
Response: {"status": "rebooting"}
```

---

## WiFi Management

### GET /telescope/features/wifi/scan
Scan for WiFi networks.
```json
Response: {"networks": [{"ssid": "MyNetwork", "signal": -50}]}
```

### POST /telescope/features/wifi/connect
Connect to WiFi network.
```json
Request: {"ssid": "MyNetwork", "password": "secret"}
Response: {"status": "connected"}
```

### GET /telescope/features/wifi/saved
Get saved WiFi networks.
```json
Response: {"networks": ["MyNetwork", "OtherNetwork"]}
```

---

## Calibration

### GET /telescope/features/calibration/polar-alignment
Get polar alignment status.
```json
Response: {"aligned": true, "error_arcmin": 2.5}
```

### POST /telescope/features/calibration/polar-alignment/clear
Clear polar alignment.
```json
Response: {"status": "cleared"}
```

### POST /telescope/features/calibration/compass/start
Start compass calibration.
```json
Response: {"status": "calibrating"}
```

### POST /telescope/features/calibration/compass/stop
Stop compass calibration.
```json
Response: {"status": "stopped"}
```

### GET /telescope/features/calibration/compass/state
Get compass calibration state.
```json
Response: {"state": "calibrated|uncalibrated"}
```

---

## Local Image Management (from mounted volume)

### GET /api/captures
List local FITS files from mounted volume.
```json
Query: ?target=M31&limit=50&offset=0
Response: {
  "captures": [
    {
      "id": 1,
      "filename": "M31_001.fit",
      "target_name": "M31",
      "exposure_seconds": 10,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 100
}
```

### GET /api/captures/{id}
Get capture details.
```json
Response: {
  "id": 1,
  "filename": "M31_001.fit",
  "file_path": "/fits/M31/M31_001.fit",
  "target_name": "M31",
  "catalog_id": "M31"
}
```

---

## Processing

### POST /api/processing/stack
Stack multiple FITS files.
```json
Request: {
  "capture_ids": [1, 2, 3],
  "output_name": "M31_stacked",
  "algorithm": "median|average"
}
Response: {"task_id": "task123", "status": "queued"}
```

### GET /api/processing/status/{task_id}
Get processing task status.
```json
Response: {
  "task_id": "task123",
  "status": "pending|running|completed|failed",
  "progress": 75
}
```

---

## Volume Mounting Configuration

The telescope's image export is mounted at:
```yaml
volumes:
  - /mnt/seestar-s50:/fits:rw
```

Environment variable:
```
FITS_DIR=/fits
```

Images are accessible at `/fits/` inside the container and automatically scanned on startup if configured.
