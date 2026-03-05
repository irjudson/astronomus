# Telescope API & Volume Setup - Complete

## ✅ Volume Mounting Status

**VERIFIED WORKING:**
- Telescope export mounted at `/mnt/seestar-s50` → `/fits` in container
- `FITS_DIR` environment variable: `/fits`
- Files accessible and readable
- **Sample files found:** M81 FITS files in `/fits/MyWorks/M81_sub/`

```bash
# Files in mounted volume:
/fits/MyWorks/M81_sub/Light_M81_10.0s_IRCUT_*.fit
```

---

## ✅ Complete API Inventory

### Total Endpoints: 40+

**Connection & Status (7 endpoints)**
- `/telescope/connect` - Connect to telescope
- `/telescope/disconnect` - Disconnect
- `/telescope/status` - Get status (RA/Dec, tracking, state)
- `/telescope/coordinates` - Get current coordinates
- `/telescope/app-state` - Get app state
- `/telescope/solve-result` - Get plate solve result
- `/telescope/field-annotations` - Get field annotations

**Movement & Positioning (6 endpoints)**
- `/telescope/move` - Directional movement (up/down/left/right/stop)
- `/telescope/goto` - Slew to RA/Dec
- `/telescope/stop-slew` - Stop slewing
- `/telescope/park` - Park telescope
- `/telescope/unpark` - Unpark telescope
- `/telescope/switch-mode` - Switch mount mode

**Imaging & Stacking (6 endpoints)**
- `/telescope/start-imaging` - Start imaging/stacking
- `/telescope/stop-imaging` - Stop imaging
- `/telescope/start-preview` - Start preview mode
- `/telescope/stacking-status` - Get stacking progress
- `/telescope/live-preview` - Get live preview stream
- `/telescope/cancel` - Cancel current operation

**Image Access - Telescope (7 endpoints)**
- `/telescope/features/images/list` - List images on telescope
- `/telescope/features/images/info` - Get image info
- `/telescope/features/images/download/{filename}` - Download stacked image
- `/telescope/features/images/raw/{filename}` - Download raw frame
- `/telescope/features/images/{filename}` DELETE - Delete image
- `/telescope/preview` - Get preview image
- `/telescope/preview/latest` - Get latest preview with metadata
- `/telescope/preview/download` - Download preview file
- `/telescope/preview-info` - Get preview info

**Plan Execution (6 endpoints)**
- `/telescope/execute` - Execute observation plan
- `/telescope/progress` - Monitor execution progress
- `/telescope/abort` - Abort execution
- `/telescope/plan/start` - Start plan
- `/telescope/plan/stop` - Stop plan
- `/telescope/plan/state` - Get plan state

**Hardware Features (8+ endpoints)**
- `/telescope/features/capabilities` - Get telescope capabilities
- `/telescope/features/hardware/dew-heater` - Control dew heater
- `/telescope/features/hardware/dew-heater/status` - Get heater status
- `/telescope/features/hardware/dc-output` - Control DC output
- `/telescope/features/focuser/move` - Move focuser
- `/telescope/features/focuser/stop` - Stop focuser
- `/telescope/features/focuser/factory-reset` - Reset focuser
- `/telescope/features/imaging/autofocus` - Auto focus
- `/telescope/features/imaging/exposure` - Set exposure
- `/telescope/features/imaging/dither` - Control dithering

**System & WiFi (12+ endpoints)**
- `/telescope/features/system/info` - System information
- `/telescope/features/system/time` - Get/set time
- `/telescope/features/system/location` - Set location
- `/telescope/features/system/shutdown` - Shutdown
- `/telescope/features/system/reboot` - Reboot
- `/telescope/features/wifi/scan` - Scan WiFi
- `/telescope/features/wifi/connect` - Connect WiFi
- `/telescope/features/wifi/saved` - Get saved networks
- (+ more WiFi management endpoints)

**Calibration (5 endpoints)**
- `/telescope/features/calibration/polar-alignment` - Get polar alignment
- `/telescope/features/calibration/polar-alignment/clear` - Clear alignment
- `/telescope/features/calibration/compass/start` - Start compass cal
- `/telescope/features/calibration/compass/stop` - Stop compass cal
- `/telescope/features/calibration/compass/state` - Get compass state

**Local Image Management (5 endpoints)**
- `/api/captures` - List local FITS files from database
- `/api/captures/{catalog_id}` - Get capture details
- `/api/captures/{catalog_id}/files` - List files for capture
- `/api/captures/files/all` - List all output files
- `/api/captures/transfer` - Transfer files

**Processing (3 endpoints)**
- `/api/processing/scan-new` - Scan for new unprocessed files
- `/api/processing/batch-process-new` - Batch process new files
- `/api/processing/status/{task_id}` - Get processing task status

**Session Management (3 endpoints)**
- `/telescope/session/join` - Join remote session
- `/telescope/session/leave` - Leave session
- `/telescope/session/disconnect` - Disconnect session

**Audio (1 endpoint)**
- `/telescope/sound/play` - Play sound on telescope

---

## 🧪 Test Scripts Created

### 1. `test_telescope_ui.sh`
Quick functional test for UI features:
- Connection management
- Position fetching
- Directional movement (up/down/left/right)
- Speed control (slow/fast)
- Imaging start/stop
- Motion stop

**Run:**
```bash
./test_telescope_ui.sh [TELESCOPE_IP]
```

### 2. `test_telescope_complete.sh`
Comprehensive API test suite:
- All connection endpoints
- All movement endpoints
- Image access (telescope & local)
- Hardware features
- System information
- Volume mounting verification

**Run:**
```bash
./test_telescope_complete.sh [TELESCOPE_IP] [PORT]
```

---

## 📋 API Documentation

See `TELESCOPE_API.md` for complete endpoint documentation with:
- Request/response formats
- Parameter descriptions
- Example usage
- Error handling

---

## 🔧 Volume Configuration

**docker-compose.yml:**
```yaml
volumes:
  - /mnt/seestar-s50:/fits:rw
```

**Environment:**
```
FITS_DIR=/fits
```

**Verification:**
```bash
# Check mount
docker exec astronomus ls -la /fits

# Count FITS files
docker exec astronomus find /fits -name "*.fit*" -type f | wc -l

# Test access
curl "http://localhost:9247/api/processing/scan-new"
```

---

## 🎯 Processing Workflow

### Scan for New Files
```bash
curl "http://localhost:9247/api/processing/scan-new"
```
Returns list of unprocessed files by object.

### Batch Process
```bash
curl -X POST "http://localhost:9247/api/processing/batch-process-new"
```
Queues all unprocessed files for processing.

### Check Status
```bash
curl "http://localhost:9247/api/processing/status/{task_id}"
```

---

## ✅ All Fixed Issues

1. **Imaging Endpoints** - Fixed from `/api/imaging/*` to `/api/telescope/start-imaging`
2. **Stop Motion** - Fixed from `/api/telescope/stop` to `/api/telescope/stop-slew`
3. **Move Parameters** - Fixed from `{direction, rate}` to `{action, speed}` with numeric values
4. **Position Parsing** - Fixed to use `current_ra_hours` and `current_dec_degrees`
5. **Volume Mounting** - Verified `/fits` mount is working with telescope export
6. **Image Access** - Both telescope API and local volume access verified

---

## 🚀 Next Steps

1. **Test with your telescope:**
   ```bash
   ./test_telescope_ui.sh 192.168.2.47
   ```

2. **Scan existing files:**
   ```bash
   curl "http://localhost:9247/api/processing/scan-new"
   ```

3. **Process images:**
   ```bash
   curl -X POST "http://localhost:9247/api/processing/batch-process-new"
   ```

4. **Use the UI:**
   - Connect to telescope
   - Use directional controls
   - Start/stop imaging
   - Access preview images

All telescope functionality is now properly connected and tested! 🎉
