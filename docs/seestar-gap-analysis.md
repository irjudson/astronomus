# Seestar Android App vs Astronomus API - Comprehensive Gap Analysis

**Analysis Date:** 2026-02-14
**Android App Version:** 3.0.0
**Astronomus Backend:** Current implementation

---

## Executive Summary

The Seestar Android app contains **72 distinct telescope commands** across multiple functional categories. Our current implementation in `seestar_client.py` covers approximately **60-65% of the core imaging and telescope control functionality**, but is missing several advanced features, calibration commands, and configuration options.

**Key Gaps:**
- Advanced stacking and mosaic controls
- Calibration frames and dark frame management
- Video/streaming capabilities (RTMP, AVI recording)
- Advanced polar alignment features
- Planetary imaging modes
- Solar observation mode
- Time-lapse photography
- Many granular settings and configuration options

---

## 1. All Android App Commands

### 1.1 Core Telescope Control Commands

#### `iscope_start_view`
**Class:** StartViewCmd
**Purpose:** Start preview/viewing mode for observation
**Parameters:**
- `mode` - Viewing mode (scenery, star, etc.)
- `target_name` - Name of target object
- `target_ra_dec` - RA/Dec coordinates [ra_hours, dec_degrees]
- `lp_filter` - Light pollution filter setting
- `star_type` - Type of celestial object

**Usage:** Primary command to start telescope viewing session

---

#### `iscope_stop_view`
**Class:** StopViewCmd
**Purpose:** Stop current viewing session
**Parameters:**
- `stage` - Stage of operation to stop

---

#### `iscope_cancel_view`
**Class:** CancelViewCmd
**Purpose:** Cancel ongoing view operation
**Usage:** Aborts current viewing process

---

#### `scope_goto` / `iscope_start_view` (with goto)
**Class:** StartGoToCmd
**Purpose:** Slew telescope to target coordinates
**Parameters:**
- `mode` - Operation mode
- `ra` - Right Ascension (degrees, converted to hours internally)
- `dec` - Declination (degrees)
- `target_name` - Target object name
- `lp_filter` - Light pollution filter
- `scale` - Mosaic scale factor
- `angle` - Mosaic angle
- `star_map_angle` - Star map rotation angle

**Usage:** Full-featured goto with mosaic support

---

#### `scope_speed_move`
**Class:** ScopeSpeedMoveCmd
**Purpose:** Manual telescope movement at specified speed/direction
**Parameters:**
- `percent` - Speed percentage
- `angle` - Direction angle (degrees)
- `dur_sec` - Duration in seconds

---

#### `scope_park`
**Class:** ParkMountCmd
**Purpose:** Park the telescope mount
**Usage:** Returns telescope to home/park position

---

#### `scope_sync`
**Class:** AlignCmd
**Purpose:** Sync telescope coordinates with known star position
**Parameters:**
- Star entity with position data

**Usage:** Alignment/calibration command

---

#### `scope_sync_planet`
**Class:** SyncSunCmd
**Purpose:** Sync telescope to solar system object
**Usage:** Special sync for planets/sun/moon

---

#### `scope_get_state`
**Class:** GetScopeStateCmd
**Purpose:** Get current telescope mount state
**Returns:** Mount position, slewing status, etc.

---

#### `scope_get_equ_coord`
**Class:** ScopeRaDecCmd
**Purpose:** Get current equatorial coordinates
**Returns:** RA/Dec of current pointing

---

#### `scope_get_track_state`
**Class:** GetTrackStateCmd
**Purpose:** Get tracking state
**Returns:** Whether tracking is enabled

---

#### `scope_set_track_state`
**Class:** SetTrackStateCmd
**Purpose:** Enable/disable sidereal tracking
**Parameters:**
- `state` - true/false

---

#### `scope_set_location`
**Class:** SetPiLocationCmd2
**Purpose:** Set observer location for telescope
**Parameters:**
- `location` - LocationLatLng object (lat, lng)

---

#### `scope_set_time`
**Class:** SetPiTimeCmd2
**Purpose:** Set telescope internal time

---

### 1.2 Imaging and Stacking Commands

#### `iscope_start_stack`
**Class:** StartStackCmd
**Purpose:** Start image stacking process
**Parameters:**
- `restart` - Whether to restart stack from beginning

---

#### `start_batch_stack`
**Class:** StartDsoStackCmd
**Purpose:** Start deep sky object batch stacking
**Usage:** Automated stacking for DSO imaging

---

#### `stop_batch_stack`
**Class:** StopDsoStackCmd
**Purpose:** Stop DSO batch stacking

---

#### `start_planet_stack`
**Class:** StartPlanetStackCmd
**Purpose:** Start planetary stacking mode
**Parameters:**
- `file` - Output filename
- `mode` - Stacking mode

**Usage:** Optimized for planetary imaging (high frame rate)

---

#### `stop_planet_stack`
**Class:** StopPlanetStackCmd
**Purpose:** Stop planetary stacking

---

#### `start_scan_planet`
**Class:** StartScanPlanetCmd
**Purpose:** Start planetary scanning mode
**Usage:** Auto-scan for best planetary capture settings

---

#### `start_continuous_expose`
**Class:** StartContinuousExposeCmd
**Purpose:** Start continuous exposure mode
**Usage:** Rapid continuous imaging

---

#### `stop_exposure`
**Class:** StopExposeCmd
**Purpose:** Stop ongoing exposure

---

#### `get_stack_setting`
**Class:** GetStackConfigCmd
**Purpose:** Get current stack configuration
**Returns:** Stacking parameters

---

#### `set_stack_setting`
**Class:** SetStackOkConfigCmd
**Purpose:** Configure stacking settings
**Parameters:**
- `save_discrete_ok_frame` - Save individual good frames

---

#### `get_batch_stack_setting`
**Class:** GetDsoStackConfigCmd
**Purpose:** Get DSO batch stack settings

---

#### `set_batch_stack_setting`
**Class:** SetDsoStackConfigCmd
**Purpose:** Set DSO batch stack configuration
**Parameters:**
- `name` - Configuration name/path

---

#### `is_stacked`
**Class:** GetHasStackedCmd
**Purpose:** Check if stacking has occurred
**Returns:** Boolean indicating stack status

---

### 1.3 Auto-Focus Commands

#### `start_auto_focuse`
**Class:** StartAutoFocuseCmd
**Purpose:** Start autofocus routine

---

#### `stop_auto_focuse`
**Class:** StopAutoFocuseCmd
**Purpose:** Stop autofocus

---

#### `move_focuser`
**Class:** MoveFocuserCmd
**Purpose:** Move focuser motor
**Parameters:**
- `step` - Number of steps to move (positive/negative)
- `ret_step` - Return step count

---

#### `get_focuser_position`
**Class:** GetCurrentFocalPosCmd
**Purpose:** Get current focuser position
**Parameters:**
- `ret_obj` - Return as object
**Returns:** Current position value

---

#### `reset_factory_focal_pos`
**Class:** ResetFactoryFocalPosCmd
**Purpose:** Reset focuser to factory position
**Parameters:**
- `wide_cam` - Reset for wide camera

---

### 1.4 Polar Alignment Commands

#### `start_polar_align`
**Class:** StartPolarAlignResetCmd
**Purpose:** Start polar alignment procedure
**Parameters:**
- `restart` - Restart alignment
- `dec_pos_index` - Declination position index

---

#### `stop_polar_align`
**Class:** StopPolarAlignCmd
**Purpose:** Stop polar alignment

---

#### `pause_polar_align`
**Class:** PausePolarAlignCmd
**Purpose:** Pause polar alignment process

---

#### `clear_polar_align` (implied)
**Class:** ClearPolarAlignCmd
**Purpose:** Clear polar alignment data

---

### 1.5 Calibration Frame Commands

#### `start_create_calib_frame` (implied)
**Class:** StartCreateCalibFrameCmd
**Purpose:** Create calibration frames (bias, flat, dark)

---

#### `start_create_calib_frame_wide` (implied)
**Class:** StartCreateCalibFrameWideCmd
**Purpose:** Create calibration frames for wide camera

---

#### `start_create_dark` (implied)
**Class:** StartCreateDarkCmd
**Purpose:** Create dark frames

---

#### `start_create_hpc` (implied)
**Class:** StartCreateHpcCmd
**Purpose:** Create hot pixel correction

---

### 1.6 Video/Streaming Commands

#### `start_avi_rtmp`
**Class:** StartAviRtmpCmd
**Purpose:** Start RTMP streaming
**Parameters:**
- `name` - Stream name/URL

**Usage:** Live streaming to RTMP server

---

#### `stop_avi_rtmp`
**Class:** StopAviRtmpCmd
**Purpose:** Stop RTMP streaming

---

#### `start_record_avi`
**Class:** StartTimeLapsePhotographyRecordCmd
**Purpose:** Start AVI video recording
**Parameters:**
- `timelapse` - Enable time-lapse mode
- `raw` - Record in raw format

---

#### `stop_record_avi`
**Class:** StopVideoRecordCmd
**Purpose:** Stop video recording

---

### 1.7 Annotation Commands

#### `start_annotate`
**Class:** StartAnnotateCmd
**Purpose:** Start field annotation (star names, etc.)
**Usage:** Overlay celestial object labels on image

---

#### `stop_annotate`
**Class:** StopAnnotateCmd
**Purpose:** Stop annotation overlay

---

#### `get_solve_result`
**Class:** GetSolveResCmd
**Purpose:** Get plate solving results
**Returns:** Solved coordinates and field info

---

### 1.8 Track Object Command

#### `start_track_object`
**Class:** StartTrackObjectCmd
**Purpose:** Track moving object in frame
**Parameters:**
- `x` - X coordinate
- `y` - Y coordinate
- `width` - Tracking box width
- `height` - Tracking box height

**Usage:** Track satellites, comets, asteroids, etc.

---

### 1.9 Compass/Gyro Calibration Commands

#### `start_compass_calibration`
**Class:** CompassCalibrationStartCmd
**Purpose:** Start compass calibration

---

#### `stop_compass_calibration`
**Class:** CompassCalibrationStopCmd
**Purpose:** Stop compass calibration
**Parameters:**
- `force` - Force stop (int)

---

#### `get_compass_state`
**Class:** CompassCalibrationGetCmd
**Purpose:** Get compass calibration state

---

#### `start_gsensor_calibration`
**Class:** StartGsensorCalibrationCmd
**Purpose:** Calibrate gyroscope/accelerometer

---

### 1.10 Device State & Settings Commands

#### `get_device_state`
**Class:** GetDeviceDeviceStateCmd
**Purpose:** Get comprehensive device state
**Parameters:**
- `keys` - Array of specific state keys to retrieve

**Returns:** Battery, temperature, storage, etc.

---

#### `get_setting`
**Class:** GetSettingCmd
**Purpose:** Get all device settings
**Returns:** Extensive settings object with ~30+ parameters including:
- `planet_correction`
- `frame_calib`
- `auto_3ppa_calib` (3-point polar alignment)
- `auto_power_off`
- `offset_deg_3ppax/y` (3PPA offsets)
- `offset_equ_3ppax/y` (equatorial offsets)
- `stack_masic` (mosaic stacking)
- `rec_stablzn` (recording stabilization)
- `wide_cam` (wide camera selected)
- `auto_af` (auto-focus)
- `always_make_dark` (auto dark frames)
- `ae_bri_percent` (auto-exposure brightness)
- `stack_after_goto`
- `mosaic` settings
- `isp_exp_ms` (exposure milliseconds)
- `guest_mode`
- `user_stack_sim` (user stacking simulation)
- `dark_mode`

---

#### `get_view_state`
**Class:** GetStatusCmd
**Purpose:** Get current view/operation state

---

#### `iscope_get_app_state`
**Class:** IscopeGetAppStateCmd
**Purpose:** Get telescope application state

---

#### `set_setting`
**Purpose:** Generic setting command (used by many Set* classes)
**Usage:** Modify individual settings

---

### 1.11 Specific Setting Commands

All of these use `set_setting` method but control different parameters:

#### Frame & Calibration Settings
- `SetAfBeforeStackCmd` - Auto-focus before stacking
- `SetAlwaysMakeDarkCmd` - Always make dark frames
- `SetFrameCalibCmd` - Enable frame calibration
- `SetAuto3ppaCalibCmd` - Auto 3-point polar alignment calibration

#### Stacking Settings
- `SetDitherCmd` - Dithering (pixels, interval)
- `SetStackAfterGotoCmd` - Auto-stack after goto
- `SetStackMasicCmd` - Mosaic stacking
- `SetDrizzle2xCmd` - Drizzle 2x upsampling
- `SetDBECmd` - Dynamic Background Extraction
- `SetLenhanceCmd` - Luminance enhancement
- `SetAirCraftLineCmd` - Airplane trail removal
- `SetStarTrailsCmd` - Star trails mode
- `SetWideDenoiseCmd` - Wide camera denoise
- `SetStarCorrectionCmd` - Star correction
- `SetStackExpCmd` - Stack exposure time

#### Camera Settings
- `SetAutoAFCmd` - Auto-focus enable
- `SetSelectedCamCmd` - Select camera
- `SetPreviewExpCmd` - Preview exposure
- `SetSettingExpMsCmd` - Exposure milliseconds
- `SetSettingGainCmd` - Camera gain
- `SetSettingManualExpCmd` - Manual exposure mode
- `SetSettingAEBrightCmd` - Auto-exposure brightness
- `SetSettingPlanetCorrectionCmd` - Planetary atmospheric correction
- `SetROICmd` - Region of interest
- `SetRecSizeIndexCmd` - Recording resolution
- `SetRecStablznCmd` - Recording stabilization

#### Mosaic Settings
- `SetMosaicCmd` - Mosaic parameters (scale, angle, star_map_angle)
- `SetMosaicSwitchCmd` - Enable mosaic mode

#### Position/Calibration
- `SetFocalPosCmd` - Set focuser position
- `SetCalibrateLocationCmd` - Calibrate location
- `SetWideCrossOffsetCmd` - Wide camera cross offset

#### System Settings
- `SetAutoPowerOffCmd` - Auto power off
- `SetGuestModeCmd` - Guest mode
- `SetLanguageCmd` - Language
- `SetVolumeCmd` - Beep volume
- `SetExpHeaderCmd` - Exposure header
- `SetSinglePhotoSaveCmd` - Single photo save
- `SetScanPlanetTipCmd` - Scan planet tips
- `SetStarBurstShotCmd` - Starburst shot mode
- `SetUserStackSimCmd` - User stack simulation
- `SetUsbEthCmd` - USB ethernet
- `SetMastercliCmd` - Master client
- `SetcliNameCmd` - Client name/UUID

---

### 1.12 File Management Commands

#### `get_albums`
**Class:** GetAlbumsCmd
**Purpose:** Get photo albums/collections
**Parameters:**
- `id` - Album ID
- `filter` - Filter criteria
- `folder` - Folder path

---

#### `get_img_file_info`
**Class:** GetImgFileInfoCmd
**Purpose:** Get image file metadata
**Parameters:**
- `name` - Filename/path

---

#### `get_img_file_page_name`
**Class:** GetFilePageNameCmd
**Purpose:** Get image files by page
**Parameters:**
- `page` - Page number

---

#### `get_img_file_page_number`
**Class:** GetGFileTotalCmd
**Purpose:** Get total number of image file pages
**Parameters:**
- `dir` - Directory
- `skip_avi` - Skip AVI files

---

#### `delete_image`
**Class:** ClearStorageCmd
**Purpose:** Delete image/file
**Parameters:**
- `name` - Filename

---

#### `save_image`
**Class:** SaveImageCmd
**Purpose:** Save current image

---

#### `fits_to_jpg`
**Class:** FitsToJpgCmd
**Purpose:** Convert FITS to JPEG
**Parameters:**
- `name` - Filename

---

### 1.13 Hardware/System Commands

#### `get_control_value`
**Class:** GetCameraTempCmd
**Purpose:** Get camera temperature or other control values
**Parameters:**
- `name` - Control name

---

#### `pi_output_set2`
**Class:** SetHeaterCmd
**Purpose:** Control dew heater
**Parameters:**
- `state` - On/off
- `value` - Power level

---

#### `pi_shutdown`
**Class:** ShutdownCmd
**Purpose:** Shutdown telescope

---

#### `pi_set_time`
**Class:** SetPiTimeCmd
**Purpose:** Set system time
**Parameters:**
- `year`, `day`, `hour`, `min`, `sec`, `time_zone`

---

#### `pi_set_ap`
**Class:** SetApCmd
**Purpose:** Configure WiFi access point
**Parameters:**
- `ssid` - Network name
- `pwd` - Password

---

#### `pi_set_5g`
**Class:** SetAp5GCmd
**Purpose:** Enable/disable 5GHz WiFi
**Parameters:**
- Is 5G enabled (boolean)

---

#### `pi_is_verified`
**Class:** CheckVerifiedCmd
**Purpose:** Check if client is verified/authenticated

---

#### `format_emmc`
**Class:** ClearEmmcCmd
**Purpose:** Format internal storage (DANGEROUS)

---

#### `clear_app_state`
**Class:** ClearAppStateCmd
**Purpose:** Clear application state
**Parameters:**
- `name` - State name

---

#### `cali_user_location`
**Class:** GetCaliUserLocationCmd
**Purpose:** Get user calibration location

---

### 1.14 Demonstration/Special Modes

#### `start_demonstrate`
**Class:** SetDemonstrateCmd
**Purpose:** Enable demonstration/exhibition mode

---

#### `stop_demonstrate`
**Purpose:** Stop demonstration mode (via stop_func)

---

#### `play_sound`
**Class:** SpeakVoiceCmd
**Purpose:** Play notification sound
**Parameters:**
- `num` - Sound number/type

---

#### `stop_func`
**Class:** StopFuncCmd
**Purpose:** Generic stop function
**Parameters:**
- `name` - Function name to stop

---

#### `test_connection`
**Class:** HeartCmd
**Purpose:** Heartbeat/connection test

---

## 2. Our Current Implementation

Based on `seestar_client.py`, we have implemented:

### Core Telescope Control ✅
- `scope_goto()` - Slew to coordinates
- `initialize_equatorial_mode()` - Set EQ mode
- `set_mount_mode()` - Set mount mode (EQ/ALT-AZ)
- `goto_target()` - Full goto with target info
- `stop_slew()` / `stop_telescope_movement()` - Abort slewing
- `move_scope()` - Manual movement
- `park()` - Park mount
- `is_equatorial_mode()` - Check mode
- `get_current_coordinates()` - Get RA/Dec
- `slew_to_coordinates()` - Direct slew

### Preview/Imaging ✅
- `start_preview()` - Start view mode
- `start_imaging()` - Start stacking
- `stop_imaging()` - Stop imaging
- `check_stacking_complete()` - Check status

### Auto-Focus ✅
- `auto_focus()` - Start AF
- `stop_autofocus()` - Stop AF
- `move_focuser_to_position()` - Absolute move
- `move_focuser_relative()` - Relative move
- `reset_focuser_to_factory()` - Reset position

### Device State ✅
- `get_device_state()` - Get device info
- `get_app_state()` - Get app state
- `get_plate_solve_result()` - Get solve
- `get_field_annotations()` - Get annotations

### Settings/Configuration ✅
- `set_exposure()` - Set exposure times
- `configure_dither()` - Dithering settings
- `configure_advanced_stacking()` - Advanced stack settings
- `configure_planetary_imaging()` - Planetary settings
- `set_manual_exposure()` - Manual exposure
- `set_auto_exposure()` - Auto exposure
- `set_location()` - Observer location

### Image Management ✅
- `list_images()` - List image files
- `get_stacked_image()` - Download stacked
- `get_raw_frame()` - Download raw
- `delete_image()` - Delete file
- `get_live_preview()` - Get preview
- `get_image_file_info()` - Get file info

### System/Hardware ✅
- `shutdown_telescope()` - Shutdown
- `reboot_telescope()` - Reboot
- `play_notification_sound()` - Play sound
- `set_dew_heater()` - Dew heater control
- `set_dc_output()` - DC output control
- `get_dc_output()` - Get DC state

### Network/Remote ✅
- `configure_access_point()` - WiFi AP config
- `set_wifi_country()` - WiFi country
- `enable_wifi_client_mode()` - WiFi client
- `disable_wifi_client_mode()` - Disable WiFi
- `scan_wifi_networks()` - Scan WiFi
- `connect_to_wifi()` - Connect
- `save_wifi_network()` - Save network
- `list_saved_wifi_networks()` - List saved
- `remove_wifi_network()` - Remove network
- `join_remote_session()` - Join session
- `leave_remote_session()` - Leave session
- `disconnect_remote_client()` - Disconnect client

### Calibration (Partial) ⚠️
- `check_polar_alignment()` - Check PA
- `clear_polar_alignment()` - Clear PA
- `start_compass_calibration()` - Start compass
- `stop_compass_calibration()` - Stop compass
- `get_compass_state()` - Get compass

### Utility ✅
- `cancel_current_operation()` - Cancel op
- `move_to_horizon()` - Alt-Az move
- `get_pi_info()` - Get Pi info
- `get_pi_time()` - Get time
- `set_pi_time()` - Set time
- `get_station_state()` - Get station
- `start_demo_mode()` - Demo mode
- `stop_demo_mode()` - Stop demo
- `check_client_verified()` - Check auth

### Wait Helpers ✅
- `wait_for_goto_complete()` - Wait for goto
- `wait_for_focus_complete()` - Wait for AF
- `wait_for_imaging_complete()` - Wait for imaging

### Connection/Events ✅
- `connect()` - Connect to telescope
- `disconnect()` - Disconnect
- Event subscription system
- Progress callbacks
- Auto-reconnect

---

## 3. Gap Analysis

### 3.1 Implemented ✅

**Core Functionality:** ~65%
- Basic telescope control (goto, park, move)
- Preview and stacking
- Auto-focus
- Device state queries
- Basic settings
- Image file management
- WiFi/network configuration
- Dew heater control
- Remote session support

### 3.2 Missing ❌

#### High Priority - Core Features

**Polar Alignment (Advanced)**
- ❌ `start_polar_align` with restart/position parameters
- ❌ `stop_polar_align`
- ❌ `pause_polar_align`
- Current implementation only has check/clear

**Planetary Imaging**
- ❌ `start_planet_stack` - Planetary stacking mode
- ❌ `stop_planet_stack`
- ❌ `start_scan_planet` - Auto planetary scan
- Currently we only have `configure_planetary_imaging()` for settings

**Video & Streaming**
- ❌ `start_avi_rtmp` - RTMP streaming
- ❌ `stop_avi_rtmp`
- ❌ `start_record_avi` - AVI/time-lapse recording
- ❌ `stop_record_avi`
- No video capabilities at all

**Track Moving Objects**
- ❌ `start_track_object` - Track satellites, comets, asteroids
- No moving object tracking

**Annotation/Plate Solving**
- ❌ `start_annotate` - Start field annotation
- ❌ `stop_annotate`
- We can get solve results but can't control annotation overlay

**Continuous Exposure**
- ❌ `start_continuous_expose` - High-speed continuous imaging
- Only have stacking mode

**View Plan/Automated Observation**
- ❌ We have `start_view_plan()` but it may not be fully implemented
- ❌ `stop_view_plan()` exists but may not map correctly
- ❌ `get_view_plan_state()` exists

#### Medium Priority - Advanced Features

**Calibration Frames**
- ❌ `start_create_calib_frame` - Create bias/flat/dark frames
- ❌ `start_create_calib_frame_wide` - Wide camera calibration
- ❌ `start_create_dark` - Dark frame creation
- ❌ `start_create_hpc` - Hot pixel correction
- No calibration frame support

**Telescope Sync**
- ❌ `scope_sync` (alignment sync)
- ❌ `scope_sync_planet` (solar system sync)
- Missing plate solving sync features

**Advanced Stack Settings**
- ❌ Many granular stacking configuration options:
  - `SetDrizzle2xCmd` - Drizzle upsampling
  - `SetDBECmd` - Dynamic background extraction
  - `SetLenhanceCmd` - Luminance enhancement
  - `SetAirCraftLineCmd` - Airplane removal
  - `SetStarTrailsCmd` - Star trails mode
  - `SetWideDenoiseCmd` - Denoise
  - `SetStarCorrectionCmd` - Star correction
  - `SetStackMasicCmd` - Mosaic stacking

**Mosaic Settings**
- ❌ `SetMosaicCmd` - Detailed mosaic parameters (scale, angle, star_map_angle)
- ❌ `SetMosaicSwitchCmd` - Enable mosaic
- We pass mosaic in goto but don't have dedicated mosaic config

**Image Processing**
- ❌ `fits_to_jpg` - FITS conversion
- No image conversion features

**Albums/Organization**
- ❌ `get_albums` - Get photo albums
- ❌ File pagination commands (get_img_file_page_name, get_img_file_page_number)
- We have basic file listing but not organized albums

**Gyroscope Calibration**
- ❌ `start_gsensor_calibration` - Gyro calibration
- Only have compass calibration

**Storage Management**
- ❌ `format_emmc` - Format storage (dangerous but may be needed)
- ❌ `clear_app_state` - Clear app state

#### Low Priority - Nice to Have

**Specialized Camera Settings**
- ❌ `SetROICmd` - Region of interest
- ❌ `SetRecSizeIndexCmd` - Recording resolution
- ❌ `SetRecStablznCmd` - Recording stabilization
- ❌ `SetSelectedCamCmd` - Select camera
- ❌ `SetPreviewExpCmd` - Preview exposure
- ❌ `SetSettingPlanetCorrectionCmd` - Atmospheric correction
- ❌ `SetFocalPosCmd` - Set focuser position (we have move but not set)

**Auto-Focus Settings**
- ❌ `SetAutoAFCmd` - Enable auto-AF
- ❌ `SetAfBeforeStackCmd` - AF before stacking
- We have AF commands but not configuration

**3-Point Polar Alignment**
- ❌ `SetAuto3ppaCalibCmd` - Auto 3PPA
- ❌ 3PPA offset settings (offset_deg_3ppax/y, offset_equ_3ppax/y)

**Frame Calibration**
- ❌ `SetFrameCalibCmd` - Enable frame calibration
- ❌ `SetAlwaysMakeDarkCmd` - Always make dark frames

**System Settings**
- ❌ `SetLanguageCmd` - Language
- ❌ `SetVolumeCmd` - Beep volume
- ❌ `SetGuestModeCmd` - Guest mode
- ❌ `SetUserStackSimCmd` - User stack sim
- ❌ `SetUsbEthCmd` - USB ethernet
- ❌ `SetMastercliCmd` - Master client
- ❌ `SetcliNameCmd` - Client name/UUID
- ❌ `SetAutoPowerOffCmd` - Auto power off
- ❌ `SetCalibrateLocationCmd` - Calibrate location
- ❌ `SetExpHeaderCmd` - Exposure header
- ❌ `SetSinglePhotoSaveCmd` - Single photo save
- ❌ `SetScanPlanetTipCmd` - Scan planet tips
- ❌ `SetStarBurstShotCmd` - Starburst mode
- ❌ `SetWideCrossOffsetCmd` - Wide cross offset

**Utility**
- ❌ `cali_user_location` - Get calibration location
- ❌ Demonstration mode fully implemented

### 3.3 Unknown/Unclear ❓

**Commands we have that aren't clearly documented in Android app:**
- `wait_for_imaging_complete()` with progress tracking - may be our addition
- `goto_target()` with full target info - may wrap multiple commands
- Some WiFi commands - need to verify they match Android implementation exactly
- `configure_advanced_stacking()` - may not map 1:1 to Android settings

**Commands with potential parameter mismatches:**
- `start_preview()` vs `iscope_start_view` - need to verify param compatibility
- `start_imaging()` vs `iscope_start_stack` - check restart param
- Various get_device_state variants - multiple classes in Android

---

## 4. Priority Recommendations

### Tier 1: Critical for Full Functionality (Implement First)

1. **Polar Alignment Control** ⭐⭐⭐⭐⭐
   - Commands: `start_polar_align`, `stop_polar_align`, `pause_polar_align`
   - **Value:** Essential for accurate tracking
   - **Complexity:** Medium - state machine for PA process
   - **Dependencies:** None
   - **Estimate:** 2-3 days

2. **Planetary Imaging Mode** ⭐⭐⭐⭐⭐
   - Commands: `start_planet_stack`, `stop_planet_stack`, `start_scan_planet`
   - **Value:** Major use case for Seestar users
   - **Complexity:** Medium - different stacking algorithm
   - **Dependencies:** None
   - **Estimate:** 3-4 days

3. **Video Recording & Streaming** ⭐⭐⭐⭐
   - Commands: `start_avi_rtmp`, `stop_avi_rtmp`, `start_record_avi`, `stop_record_avi`
   - **Value:** Live streaming is highly requested
   - **Complexity:** Medium - video protocols
   - **Dependencies:** None
   - **Estimate:** 4-5 days

4. **Object Tracking** ⭐⭐⭐⭐
   - Commands: `start_track_object`
   - **Value:** Satellites, ISS, comets, asteroids
   - **Complexity:** Medium - coordinate tracking
   - **Dependencies:** None
   - **Estimate:** 2-3 days

5. **Annotation Control** ⭐⭐⭐⭐
   - Commands: `start_annotate`, `stop_annotate`
   - **Value:** User-friendly feature for identification
   - **Complexity:** Low - simple on/off
   - **Dependencies:** None
   - **Estimate:** 1 day

### Tier 2: Advanced Features (Implement Next)

6. **Calibration Frames** ⭐⭐⭐⭐
   - Commands: `start_create_calib_frame`, `start_create_dark`, etc.
   - **Value:** Better image quality with proper calibration
   - **Complexity:** Medium - frame management
   - **Dependencies:** None
   - **Estimate:** 3-4 days

7. **Mosaic Configuration** ⭐⭐⭐
   - Commands: `SetMosaicCmd`, `SetMosaicSwitchCmd`
   - **Value:** Wide field imaging
   - **Complexity:** Low - settings only
   - **Dependencies:** None
   - **Estimate:** 1-2 days

8. **Advanced Stacking Options** ⭐⭐⭐
   - Commands: Drizzle, DBE, L-enhance, etc.
   - **Value:** Better image quality
   - **Complexity:** Low - pass-through settings
   - **Dependencies:** None
   - **Estimate:** 2-3 days

9. **Telescope Sync Commands** ⭐⭐⭐
   - Commands: `scope_sync`, `scope_sync_planet`
   - **Value:** Alignment accuracy
   - **Complexity:** Low
   - **Dependencies:** None
   - **Estimate:** 1-2 days

10. **Albums & File Organization** ⭐⭐⭐
    - Commands: `get_albums`, pagination commands
    - **Value:** Better file management
    - **Complexity:** Medium - data organization
    - **Dependencies:** None
    - **Estimate:** 2-3 days

### Tier 3: Configuration & Polish (Implement Last)

11. **Granular Camera Settings** ⭐⭐
    - Commands: ROI, recording settings, focal position
    - **Value:** Fine-tuning
    - **Complexity:** Low
    - **Estimate:** 2-3 days

12. **System Settings** ⭐⭐
    - Commands: Language, volume, guest mode, etc.
    - **Value:** User experience
    - **Complexity:** Low
    - **Estimate:** 2-3 days

13. **3PPA Configuration** ⭐⭐
    - Commands: 3-point polar alignment settings
    - **Value:** Advanced users
    - **Complexity:** Low
    - **Estimate:** 1-2 days

14. **FITS Conversion** ⭐
    - Commands: `fits_to_jpg`
    - **Value:** Nice to have
    - **Complexity:** Low
    - **Estimate:** 1 day

15. **Storage Management** ⭐
    - Commands: `format_emmc`, state clearing
    - **Value:** Maintenance
    - **Complexity:** Low (but dangerous)
    - **Estimate:** 1 day

---

## 5. Implementation Strategy

### Phase 1: Critical Gaps (4-6 weeks)
Implement Tier 1 features:
- Polar alignment control
- Planetary imaging
- Video/streaming
- Object tracking
- Annotation control

**Deliverable:** Core parity with Android app for major use cases

### Phase 2: Advanced Features (3-4 weeks)
Implement Tier 2 features:
- Calibration frames
- Mosaic configuration
- Advanced stacking
- Telescope sync
- Album management

**Deliverable:** Professional-grade feature set

### Phase 3: Configuration & Polish (2-3 weeks)
Implement Tier 3 features:
- All granular settings
- System configuration
- Utility commands
- Edge cases

**Deliverable:** 100% feature parity with Android app

---

## 6. Testing & Validation

For each implemented feature:

1. **Unit Tests**
   - Command encoding/decoding
   - Parameter validation
   - Error handling

2. **Integration Tests**
   - Send commands to real telescope
   - Verify responses
   - Test error cases

3. **End-to-End Tests**
   - Complete workflows (e.g., PA start to finish)
   - Multi-step operations
   - State transitions

4. **Comparison with Android App**
   - Side-by-side testing
   - Packet capture comparison
   - Result verification

---

## 7. Notes & Observations

### Command Patterns
- Most commands follow `iscope_*`, `scope_*`, or action pattern
- Settings use `set_setting` with parameter name
- Get/Set pairs for most features
- State queries return comprehensive objects

### Missing Documentation
- Some commands have minimal JavaDoc
- Parameter meanings sometimes unclear from code alone
- May need runtime testing to understand edge cases

### Potential Issues
- Command IDs and transaction management
- Error code handling (we see code 318 checks)
- State synchronization between app and telescope
- Some commands may be hardware-version specific

### Architecture Insights
- Android app has action/command separation
- Event-based architecture with callbacks
- Preferences/settings cached locally
- Some commands trigger multi-step processes

---

## 8. Conclusion

Our implementation covers the **core telescope control and imaging functionality** well, providing a solid foundation for most users. However, we're missing several **advanced features** that would make Astronomus a true professional tool:

**Strengths:**
- Excellent basic telescope control
- Good imaging/stacking support
- Strong network/WiFi management
- Well-designed async/event system

**Key Gaps:**
- No polar alignment control
- No planetary imaging mode
- No video/streaming
- No moving object tracking
- Limited calibration frame support
- Many advanced settings unavailable

**Recommendation:** Focus on **Tier 1 features first** (polar alignment, planetary mode, video, tracking, annotation) as these have the highest user-facing value and fill critical gaps in functionality. Once those are complete, move to Tier 2 for professional features, then Tier 3 for completeness.

With focused effort, we could achieve **90%+ feature parity** within 8-10 weeks.

---

## Appendix A: Quick Reference Command Table

| Command | Android Class | We Have? | Priority | Category |
|---------|---------------|----------|----------|----------|
| `iscope_start_view` | StartViewCmd | ✅ Yes | - | Telescope Control |
| `iscope_stop_view` | StopViewCmd | ✅ Yes | - | Telescope Control |
| `iscope_cancel_view` | CancelViewCmd | ✅ Yes | - | Telescope Control |
| `scope_goto` | StartGoToCmd | ✅ Yes | - | Telescope Control |
| `scope_speed_move` | ScopeSpeedMoveCmd | ✅ Yes | - | Telescope Control |
| `scope_park` | ParkMountCmd | ✅ Yes | - | Telescope Control |
| `scope_sync` | AlignCmd | ❌ No | Tier 2 | Telescope Control |
| `scope_sync_planet` | SyncSunCmd | ❌ No | Tier 2 | Telescope Control |
| `scope_get_state` | GetScopeStateCmd | ✅ Yes | - | State Query |
| `scope_get_equ_coord` | ScopeRaDecCmd | ✅ Yes | - | State Query |
| `scope_get_track_state` | GetTrackStateCmd | ✅ Yes | - | State Query |
| `scope_set_track_state` | SetTrackStateCmd | ✅ Yes | - | Telescope Control |
| `scope_set_location` | SetPiLocationCmd2 | ✅ Yes | - | Configuration |
| `scope_set_time` | SetPiTimeCmd2 | ✅ Yes | - | Configuration |
| `iscope_start_stack` | StartStackCmd | ✅ Yes | - | Imaging |
| `start_batch_stack` | StartDsoStackCmd | ✅ Yes | - | Imaging |
| `stop_batch_stack` | StopDsoStackCmd | ✅ Yes | - | Imaging |
| `start_planet_stack` | StartPlanetStackCmd | ❌ No | **Tier 1** | Imaging |
| `stop_planet_stack` | StopPlanetStackCmd | ❌ No | **Tier 1** | Imaging |
| `start_scan_planet` | StartScanPlanetCmd | ❌ No | **Tier 1** | Imaging |
| `start_continuous_expose` | StartContinuousExposeCmd | ❌ No | Tier 2 | Imaging |
| `stop_exposure` | StopExposeCmd | ✅ Yes | - | Imaging |
| `start_auto_focuse` | StartAutoFocuseCmd | ✅ Yes | - | Auto-Focus |
| `stop_auto_focuse` | StopAutoFocuseCmd | ✅ Yes | - | Auto-Focus |
| `move_focuser` | MoveFocuserCmd | ✅ Yes | - | Auto-Focus |
| `get_focuser_position` | GetCurrentFocalPosCmd | ✅ Yes | - | State Query |
| `reset_factory_focal_pos` | ResetFactoryFocalPosCmd | ✅ Yes | - | Auto-Focus |
| `start_polar_align` | StartPolarAlignResetCmd | ❌ No | **Tier 1** | Calibration |
| `stop_polar_align` | StopPolarAlignCmd | ❌ No | **Tier 1** | Calibration |
| `pause_polar_align` | PausePolarAlignCmd | ❌ No | **Tier 1** | Calibration |
| `start_avi_rtmp` | StartAviRtmpCmd | ❌ No | **Tier 1** | Video |
| `stop_avi_rtmp` | StopAviRtmpCmd | ❌ No | **Tier 1** | Video |
| `start_record_avi` | StartTimeLapsePhotographyRecordCmd | ❌ No | **Tier 1** | Video |
| `stop_record_avi` | StopVideoRecordCmd | ❌ No | **Tier 1** | Video |
| `start_annotate` | StartAnnotateCmd | ❌ No | **Tier 1** | Annotation |
| `stop_annotate` | StopAnnotateCmd | ❌ No | **Tier 1** | Annotation |
| `get_solve_result` | GetSolveResCmd | ✅ Yes | - | State Query |
| `start_track_object` | StartTrackObjectCmd | ❌ No | **Tier 1** | Tracking |
| `start_compass_calibration` | CompassCalibrationStartCmd | ✅ Yes | - | Calibration |
| `stop_compass_calibration` | CompassCalibrationStopCmd | ✅ Yes | - | Calibration |
| `get_compass_state` | CompassCalibrationGetCmd | ✅ Yes | - | State Query |
| `start_gsensor_calibration` | StartGsensorCalibrationCmd | ❌ No | Tier 2 | Calibration |
| `get_device_state` | GetDeviceDeviceStateCmd | ✅ Yes | - | State Query |
| `get_setting` | GetSettingCmd | ✅ Partial | - | State Query |
| `get_view_state` | GetStatusCmd | ✅ Yes | - | State Query |
| `iscope_get_app_state` | IscopeGetAppStateCmd | ✅ Yes | - | State Query |
| `get_albums` | GetAlbumsCmd | ❌ No | Tier 2 | File Management |
| `get_img_file_info` | GetImgFileInfoCmd | ✅ Yes | - | File Management |
| `delete_image` | ClearStorageCmd | ✅ Yes | - | File Management |
| `save_image` | SaveImageCmd | ⚠️ Unclear | - | File Management |
| `fits_to_jpg` | FitsToJpgCmd | ❌ No | Tier 3 | File Management |
| `pi_output_set2` | SetHeaterCmd | ✅ Yes | - | Hardware |
| `pi_shutdown` | ShutdownCmd | ✅ Yes | - | System |
| `pi_set_time` | SetPiTimeCmd | ✅ Yes | - | System |
| `pi_set_ap` | SetApCmd | ✅ Yes | - | Network |
| `pi_set_5g` | SetAp5GCmd | ⚠️ Unclear | - | Network |
| `pi_is_verified` | CheckVerifiedCmd | ✅ Yes | - | System |
| `format_emmc` | ClearEmmcCmd | ❌ No | Tier 3 | System |
| `start_demonstrate` | SetDemonstrateCmd | ✅ Yes | - | Demo |
| `play_sound` | SpeakVoiceCmd | ✅ Yes | - | Utility |
| `test_connection` | HeartCmd | ✅ Yes | - | Connection |

**Legend:**
- ✅ **Yes** - Fully implemented
- ⚠️ **Unclear** - May be implemented, needs verification
- ❌ **No** - Not implemented
- **Tier 1** - High priority, critical features
- **Tier 2** - Medium priority, advanced features
- **Tier 3** - Low priority, polish/edge cases

---

## Appendix B: Settings Commands Summary

We're missing most of the granular settings commands. Here's a breakdown:

### Implemented Settings ✅
- Basic exposure settings (`set_exposure`, `set_manual_exposure`, `set_auto_exposure`)
- Dithering (`configure_dither`)
- Location/time
- Network/WiFi configuration
- Dew heater control

### Missing Settings ❌

**Stacking Quality (High Priority)**
- Drizzle 2x upsampling
- Dynamic Background Extraction (DBE)
- Luminance enhancement
- Airplane trail removal
- Star trails mode
- Wide denoise
- Star correction

**Auto-Focus (Medium Priority)**
- Auto-AF enable/disable
- AF before stacking
- Always make dark frames

**Mosaic (Medium Priority)**
- Mosaic parameters (scale, angle, star_map_angle)
- Mosaic enable/disable switch

**Camera (Medium Priority)**
- ROI (Region of Interest)
- Recording resolution
- Recording stabilization
- Focal position setting
- Planetary atmospheric correction
- Camera selection

**3-Point Polar Alignment (Low Priority)**
- Auto 3PPA calibration
- 3PPA offset settings (deg and equ)

**System (Low Priority)**
- Language
- Volume
- Guest mode
- User stack simulation
- USB ethernet
- Master client
- Client name/UUID
- Auto power off
- Frame calibration
- Calibrate location
- Various flags and toggles

**Total Missing Settings:** ~40+ individual setting commands

---

## Appendix C: Feature Comparison Matrix

| Feature Category | Android App | Our Implementation | Gap |
|------------------|-------------|-------------------|-----|
| **Basic Telescope Control** | ✅✅✅✅✅ | ✅✅✅✅✅ | None |
| **Goto & Slewing** | ✅✅✅✅✅ | ✅✅✅✅✅ | None |
| **Tracking** | ✅✅✅✅✅ | ✅✅✅✅ | Sync commands |
| **DSO Imaging** | ✅✅✅✅✅ | ✅✅✅✅ | Some settings |
| **Planetary Imaging** | ✅✅✅✅✅ | ⚠️⚠️ | No stack/scan |
| **Solar Imaging** | ✅✅✅ | ❌ | Complete gap |
| **Auto-Focus** | ✅✅✅✅✅ | ✅✅✅✅ | Config options |
| **Polar Alignment** | ✅✅✅✅✅ | ⚠️⚠️ | No start/stop/pause |
| **Video/Streaming** | ✅✅✅✅ | ❌ | Complete gap |
| **Time-Lapse** | ✅✅✅✅ | ❌ | Complete gap |
| **Object Tracking** | ✅✅✅✅ | ❌ | Complete gap |
| **Annotation** | ✅✅✅✅ | ⚠️ | Can get, can't control |
| **Calibration Frames** | ✅✅✅✅ | ❌ | Complete gap |
| **Image Stacking** | ✅✅✅✅✅ | ✅✅✅✅ | Advanced options |
| **Mosaic Imaging** | ✅✅✅✅ | ⚠️⚠️ | Passed in goto only |
| **File Management** | ✅✅✅✅✅ | ✅✅✅✅ | Albums/pagination |
| **Network/WiFi** | ✅✅✅✅✅ | ✅✅✅✅✅ | None |
| **Hardware Control** | ✅✅✅✅✅ | ✅✅✅✅ | Some settings |
| **System Settings** | ✅✅✅✅✅ | ✅✅✅ | Many granular settings |

**Overall Feature Parity:** ~65%

---

## Appendix D: Implementation Effort Estimate

| Feature | Commands | Complexity | Days | Dependencies |
|---------|----------|------------|------|--------------|
| **Polar Alignment Control** | 3 | Medium | 2-3 | None |
| **Planetary Imaging** | 3 | Medium | 3-4 | None |
| **Video/Streaming** | 4 | Medium-High | 4-5 | RTMP protocol |
| **Object Tracking** | 1 | Medium | 2-3 | None |
| **Annotation Control** | 2 | Low | 1 | None |
| **Calibration Frames** | 4 | Medium | 3-4 | None |
| **Mosaic Config** | 2 | Low | 1-2 | None |
| **Advanced Stacking** | 10+ | Low | 2-3 | None |
| **Telescope Sync** | 2 | Low | 1-2 | None |
| **Albums & Files** | 3 | Medium | 2-3 | None |
| **Camera Settings** | 10+ | Low | 2-3 | None |
| **System Settings** | 15+ | Low | 2-3 | None |
| **3PPA Config** | 3 | Low | 1-2 | None |
| **FITS Conversion** | 1 | Low | 1 | Image lib |
| **Storage Mgmt** | 2 | Low | 1 | None |

**Total Estimated Effort:** 28-40 working days (~6-8 weeks)

**With testing, documentation, and polish:** 8-10 weeks to 90%+ parity
