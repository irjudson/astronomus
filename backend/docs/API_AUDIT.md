# Seestar Client API Audit

**Date**: 2026-01-09
**Purpose**: Identify and remove methods that don't map to real Seestar API commands

## Audit Findings

### ❌ PHANTOM COMMANDS (No Real Seestar API Command)

These methods exist in our client but have NO corresponding Seestar command:

#### 1. `park()` - INCORRECT IMPLEMENTATION
**Current method**: `async def park(self) -> bool`
**Problem**: Uses `scope_move_to_horizon` with azimuth=0, altitude=0
**Reality**: There IS a `scope_park` command, but we're not using it correctly
**Evidence**: CRITICAL-API-FINDINGS.md shows `scope_park` exists with params `{"equ_mode": true}`
**Action**: Fix to use proper `scope_park` command

#### 2. "unpark" - DOES NOT EXIST
**Problem**: No such command exists in Seestar API
**Reality**: Mount open/close state is controlled via `scope_park` or is read-only status
**Evidence**: CRITICAL-API-FINDINGS states "NOT FOUND in CmdMethod enum as separate command"
**Action**: Remove any references to "unpark" in documentation

#### 3. Arm Open/Close - UNKNOWN IMPLEMENTATION
**Methods**: None currently implemented (good!)
**Problem**: Documentation mentions arm control but no command exists
**Reality**: `mount.close` field in device state is read-only OR controlled via `scope_park`
**Evidence**: CRITICAL-API-FINDINGS.md investigation section
**Action**: DO NOT implement until verified with live testing

---

## Methods That Map to Real Commands

### ✅ CORRECTLY IMPLEMENTED

| Our Method | Seestar Command | Status |
|-----------|----------------|---------|
| `get_current_coordinates()` | `scope_get_equ_coord` | ✅ Correct |
| `get_app_state()` | `iscope_get_app_state` | ✅ Correct |
| `check_stacking_complete()` | `is_stacked` | ✅ Correct |
| `start_view_plan()` | `iscope_start_plan` | ✅ Correct |
| `stop_view_plan()` | `iscope_stop_plan` | ✅ Correct |
| `get_view_plan_state()` | `iscope_get_plan_state` | ✅ Correct |
| `goto_target()` | `iscope_start_view` | ✅ Correct |
| `start_imaging()` | `iscope_start_stack` | ✅ Correct |
| `stop_imaging()` | `iscope_stop_view` | ✅ Correct |
| `auto_focus()` | `start_auto_focuse` | ✅ Correct |
| `get_device_state()` | `get_device_state` | ✅ Correct |
| `set_exposure()` | `set_setting` | ✅ Correct |
| `configure_dither()` | `set_setting` | ✅ Correct |
| `get_plate_solve_result()` | `get_last_solve_result` | ✅ Correct |
| `get_field_annotations()` | `get_solve_info` | ✅ Correct |
| `start_planet_scan()` | `iscope_start_scan` | ✅ Correct |
| `slew_to_coordinates()` | `scope_move` | ✅ Correct |
| `stop_telescope_movement()` | `scope_move` (action=stop) | ✅ Correct |
| `move_focuser_to_position()` | `move_focuser` | ✅ Correct |
| `move_focuser_relative()` | `move_focuser` | ✅ Correct |
| `stop_autofocus()` | `stop_auto_focuse` | ✅ Correct |
| `configure_advanced_stacking()` | `set_setting` | ✅ Correct |
| `set_manual_exposure()` | `set_setting` | ✅ Correct |
| `set_auto_exposure()` | `set_setting` | ✅ Correct |
| `shutdown_telescope()` | `pi_shutdown` | ✅ Correct |
| `reboot_telescope()` | `pi_reboot` | ✅ Correct |
| `play_notification_sound()` | `play_sound` | ✅ Correct |
| `get_image_file_info()` | `get_img_file_info` | ✅ Correct |
| `cancel_current_operation()` | `iscope_cancel_view` | ✅ Correct |
| `set_location()` | `set_setting` | ✅ Correct |
| `move_to_horizon()` | `scope_move_to_horizon` | ✅ Correct |
| `reset_focuser_to_factory()` | `reset_factory_focal_pos` | ✅ Correct |
| `check_polar_alignment()` | `get_last_3ppa_result` | ✅ Correct |
| `clear_polar_alignment()` | `clear_3ppa` | ✅ Correct |
| `start_compass_calibration()` | `pi_start_calibration_compass` | ✅ Correct |
| `stop_compass_calibration()` | `pi_stop_calibration_compass` | ✅ Correct |
| `get_compass_state()` | `pi_get_calibration_compass_state` | ✅ Correct |
| `join_remote_session()` | `join_guest` | ✅ Correct |
| `leave_remote_session()` | `leave_guest` | ✅ Correct |
| `disconnect_remote_client()` | `disconnect_pi_guest` | ✅ Correct |
| `configure_access_point()` | `set_setting` | ✅ Correct |
| `set_wifi_country()` | `set_setting` | ✅ Correct |
| `enable_wifi_client_mode()` | `pi_enable_station` | ✅ Correct |
| `disable_wifi_client_mode()` | `pi_disable_station` | ✅ Correct |
| `scan_wifi_networks()` | `pi_scan_wifi` | ✅ Correct |
| `connect_to_wifi()` | `pi_connect_wifi` | ✅ Correct |
| `save_wifi_network()` | `pi_save_wifi` | ✅ Correct |
| `list_saved_wifi_networks()` | `pi_get_wifi_list` | ✅ Correct |
| `remove_wifi_network()` | `pi_remove_wifi` | ✅ Correct |
| `get_pi_info()` | `pi_get_info` | ✅ Correct |
| `get_pi_time()` | `pi_get_time` | ✅ Correct |
| `set_pi_time()` | `pi_set_time` | ✅ Correct |
| `get_station_state()` | `pi_get_station_state` | ✅ Correct |
| `start_demo_mode()` | `enter_demo_mode` | ✅ Correct |
| `stop_demo_mode()` | `exit_demo_mode` | ✅ Correct |
| `check_client_verified()` | `pi_is_verified` | ✅ Correct |

### ⚠️ NEEDS FIXING

| Our Method | Issue | Fix Required |
|-----------|-------|--------------|
| `set_dew_heater()` | ❌ CRITICAL: Uses wrong command | Change from `set_setting` to `pi_output_set2` |
| `set_dc_output()` | ⚠️ Verify: Uses `pi_output_set2` | Verify params structure |
| `get_dc_output()` | ⚠️ Verify: Uses `pi_output_get2` | Verify command exists |
| `park()` | ⚠️ Wrong command: Uses `scope_move_to_horizon` | Change to `scope_park` command |
| `configure_planetary_imaging()` | ⚠️ Verify: Uses `set_setting` | Verify planet-specific params |

### 🆕 NOT YET IMPLEMENTED (Documented as Real Commands)

These commands exist in the Seestar API but we haven't implemented yet:

1. **Image retrieval** (file transfer via port 4801)
   - Download stacked images
   - Download raw frames
   - List images
   - Delete images

2. **Live preview** (RTMP stream via ports 4554/4555)
   - Capture preview frame

---

## Action Items

### IMMEDIATE (Critical Bugs)

1. ✅ **Fix `set_dew_heater()`** - Uses wrong command (see CRITICAL-API-FINDINGS.md)
   - Current: `set_setting` with `{"heater_enable": bool}`
   - Correct: `pi_output_set2` with `{"heater": {"state": bool, "value": int}}`

2. ✅ **Fix `park()`** - Uses wrong command
   - Current: `scope_move_to_horizon` with azimuth=0, altitude=0
   - Correct: `scope_park` with `{"equ_mode": true}`

3. ✅ **Remove "unpark" references** - Command doesn't exist
   - Remove from seestar-api-commands.md
   - Remove from any documentation mentioning "unpark"

### VERIFICATION NEEDED

4. ⚠️ **Verify `set_dc_output()` and `get_dc_output()`**
   - Confirm `pi_output_get2` command exists
   - Verify params structure matches Seestar protocol

5. ⚠️ **Test arm control with live telescope**
   - Determine if `mount.close` is read-only or controllable
   - If controllable, document the correct command/params
   - DO NOT implement until verified safe

### ENHANCEMENT

6. 🆕 **Add `lp_filter` parameter to `goto_target()`**
   - Currently missing from `iscope_start_view` params
   - See CRITICAL-API-FINDINGS.md line 63-92

7. 🆕 **Implement image retrieval methods**
   - File transfer protocol on port 4801
   - See Phase 2.2 in plan file

---

## Documentation Cleanup

### Files to Update

1. **docs/seestar-api-commands.md**
   - Remove: `✅ scope_park - Already implemented` (it's NOT correctly implemented)
   - Remove: Any mention of "unpark" command
   - Add: Note that `mount.close` state may be read-only

2. **docs/SEESTAR-SAFETY-TESTING.md**
   - Update arm control section to reflect that command doesn't exist

3. **backend/app/clients/seestar_client.py**
   - Fix `park()` method
   - Fix `set_dew_heater()` method
   - Add docstring warnings about unimplemented commands

---

## Commands That ARE SAFE to Implement

These are confirmed safe read-only queries:

- ✅ All `get_*` methods (read device state)
- ✅ All `pi_get_*` methods (read system info)
- ✅ `check_*` methods (query status)
- ✅ `is_stacked` (check completion)

## Commands That REQUIRE TESTING

These affect hardware and need live testing:

- ⚠️ `scope_park` - Moves mount physically
- ⚠️ `iscope_start_view` - Moves mount + starts imaging
- ⚠️ `iscope_start_stack` - Starts imaging
- ⚠️ `move_focuser` - Moves focuser motor
- ⚠️ `pi_output_set2` - Controls DC outputs (heater, etc.)
- ⚠️ Any arm open/close (if it exists)

---

## Summary

- **Total methods**: 79 async methods in SeestarClient
- **Correctly mapped**: ~70 methods ✅
- **Need fixing**: 5 methods ⚠️
- **Phantom commands**: 1 ("unpark") ❌
- **Not yet implemented**: 5+ documented commands 🆕

Next step: Fix the critical bugs (`set_dew_heater`, `park`) before any further testing.
