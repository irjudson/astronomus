# Tier 1 Features + UX Optimization Implementation Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement all 5 Tier 1 features (Polar Alignment, Planetary Imaging, Video/Streaming, Object Tracking, Annotation Control) with optimized execution UX (Layout, Live Preview, Visual Polish)

**Architecture:** Integrated Feature+UX approach - build each Tier 1 feature with polished UI from the start, interleaving backend work with UX improvements across 7 phases

**Tech Stack:** Vue 3 + Pinia, FastAPI, Seestar S50 WebSocket API, file-based preview frames

---

## 1. Architecture Overview

### Integrated Feature+UX Implementation Architecture

We'll build this in 7 phases, each delivering working functionality:

**Phase 1: Layout Foundation (UX-B)**
- Consolidate 8 existing execution panels → 4 main areas (Connection, Telescope Control, Imaging, Plan Execution)
- Move position/hardware status to header (already done, expand on it)
- Create flex-based responsive layout with better space usage
- Establish UI component patterns for new features

**Phase 2: Video/Streaming + Live Preview (Tier 1 + UX-D)**
- Backend: Implement file-based preview frame fetching (not RTSP - we know that doesn't work)
- Backend: Add start_record_avi/stop_record_avi for video recording
- Frontend: Fix live preview to poll for file-based frames every 1-2 seconds
- Frontend: Add recording controls to imaging panel

**Phase 3: Planetary Imaging (Tier 1)**
- Backend: Implement start_planet_stack, stop_planet_stack, start_scan_planet
- Frontend: Add "Planetary" mode toggle to imaging panel (existing panel, new mode)
- Frontend: Add planet scanning controls (scan, select, stack)

**Phase 4: Polar Alignment (Tier 1)**
- Backend: Implement start_polar_align, stop_polar_align, pause_polar_align
- Frontend: Add new "Polar Alignment" panel with start/stop/pause controls
- Frontend: Add alignment status indicators (progress, quality metrics)

**Phase 5: Object Tracking (Tier 1)**
- Backend: Implement start_track_object for satellites/comets/asteroids
- Frontend: Add "Object Tracking" section to telescope control panel
- Frontend: Add object type selector (satellite/comet/asteroid) and tracking controls

**Phase 6: Annotation Control (Tier 1)**
- Backend: Implement start_annotate/stop_annotate
- Frontend: Add annotation toggle to imaging preview
- Frontend: Add annotation controls (enable/disable, maybe basic config)

**Phase 7: Visual Polish (UX-F)**
- Add loading states and transitions throughout
- Improve status indicators (color coding, icons, animations)
- Add better error feedback (toasts/notifications instead of just error state)
- Add confirmation dialogs for destructive actions
- Polish button states, hover effects, focus states

---

## 2. Components

### Backend Components

**seestar_client.py additions** (~500 lines total):
- `start_planet_stack()`, `stop_planet_stack()`, `start_scan_planet()` - Planetary imaging commands
- `start_polar_align()`, `stop_polar_align()`, `pause_polar_align()` - Polar alignment commands
- `start_track_object(object_type, object_id)` - Object tracking (satellites/comets/asteroids)
- `start_annotate()`, `stop_annotate()` - Annotation control
- `start_record_avi()`, `stop_record_avi()` - Video recording (AVI format)
- `get_latest_preview_frame()` - File-based frame fetching (replaces RTSP approach)

**New API endpoints in routers/** (~200 lines):
- `POST /api/telescope/imaging/planet/start` - Start planetary stacking
- `POST /api/telescope/imaging/planet/stop` - Stop planetary stacking
- `POST /api/telescope/imaging/planet/scan` - Scan for planets
- `POST /api/telescope/polar-align/start` - Start polar alignment
- `POST /api/telescope/polar-align/stop` - Stop polar alignment
- `POST /api/telescope/polar-align/pause` - Pause polar alignment
- `POST /api/telescope/tracking/start` - Start object tracking
- `POST /api/telescope/tracking/stop` - Stop object tracking
- `POST /api/telescope/annotation/toggle` - Toggle annotations
- `POST /api/telescope/recording/start` - Start AVI recording
- `POST /api/telescope/recording/stop` - Stop AVI recording
- `GET /api/telescope/preview/frame` - Get latest preview frame (file-based)

### Frontend Components

**Stores (Pinia state management)**:
- `execution.js` - Extend with planetary imaging state, polar alignment state, tracking state, annotation state, recording state
- Keep imaging state flat and simple (no nested complexity)

**View updates**:
- `ExecutionView.vue` - Reorganize layout (4 main areas instead of 8 panels), move to flex-based responsive grid
- Update preview component to poll `/api/telescope/preview/frame` every 1-2 seconds

**New/Updated Panels** (Vue components):
- `TelescopePanel.vue` - Add object tracking controls (already has connect, park, dew heater)
- `ImagingPanel.vue` - Add mode toggle (Deep Sky vs Planetary), add recording controls
- `PolarAlignmentPanel.vue` - NEW: Polar alignment controls and status
- `PlanExecutionPanel.vue` - Keep as-is (already handles plan execution)

**Visual Polish Components** (Phase 7):
- `StatusIndicator.vue` - Reusable status badge (idle/active/error with colors)
- `ConfirmDialog.vue` - Confirmation for destructive actions
- Toast/notification system (possibly use existing library like vue-toastification)

---

## 3. Data Flow

### User Action → Telescope Command Flow

```
User clicks button (e.g., "Start Planetary Imaging")
  ↓
Vue component calls store action (executionStore.startPlanetaryImaging())
  ↓
Store action makes HTTP POST to backend (/api/telescope/imaging/planet/start)
  ↓
FastAPI endpoint validates request, calls seestar_client method
  ↓
seestar_client.start_planet_stack() sends WebSocket command to telescope
  ↓
Telescope responds with success/error code
  ↓
Response flows back: telescope → client → endpoint → store → UI
  ↓
Store updates state (imaging.mode = 'planetary', imaging.active = true)
  ↓
Vue reactivity updates UI (button changes to "Stop Planetary Imaging")
```

### Telescope State → UI Flow (Polling)

```
Every 2 seconds (existing position polling interval):
  ↓
executionStore.fetchPosition() calls GET /api/telescope/status
  ↓
Backend calls seestar_client.get_app_state() (existing method)
  ↓
Telescope returns full state object (position, tracking, imaging, recording, etc.)
  ↓
Store updates all relevant state:
  - position (RA/Dec/Alt/Az)
  - hardware.trackingStatus
  - imaging.active, imaging.framesCaptured
  - recording.active (NEW)
  - polarAlignment.active, polarAlignment.progress (NEW)
  ↓
Vue reactivity updates all UI elements automatically
```

### Live Preview Flow (File-Based, Not RTSP)

```
Every 1-2 seconds (separate interval from position polling):
  ↓
Preview component calls GET /api/telescope/preview/frame
  ↓
Backend calls seestar_client.get_latest_preview_frame()
  ↓
Client checks telescope's file system for latest preview frame
  (Telescope writes frames to /mnt/sda1/preview/ or similar)
  ↓
Return frame as JPEG bytes (or URL to cached frame)
  ↓
Frontend updates <img> src with new frame data/URL
  ↓
Browser displays updated preview
```

### State Synchronization Strategy

- **Single source of truth**: Backend telescope state
- **Polling interval**: 2 seconds for position/status (existing), 1-2 seconds for preview frames (new)
- **Optimistic updates**: UI updates immediately on user action, reverts if backend returns error
- **Error recovery**: If polling fails, show "Connection Lost" indicator, retry with backoff

---

## 4. Error Handling

### Backend Error Handling

**Command Failures**:
- Telescope returns error code (code != 0) → Return HTTP 400 with error message from telescope
- WebSocket timeout → Return HTTP 504 Gateway Timeout with "Telescope not responding"
- Telescope disconnected → Return HTTP 400 with "Telescope not connected"
- Invalid parameters → Return HTTP 422 Unprocessable Entity with validation error

**State Checks**:
- Before starting imaging: Check if already imaging (can't start planet stack while deep sky imaging)
- Before polar alignment: Check mount mode (only works in equatorial mode)
- Before tracking object: Check if telescope is parked (can't track while parked)

### Frontend Error Handling

**Store Actions**:
```javascript
async startPlanetaryImaging(params) {
  this.loading = true
  this.error = null  // Clear previous error

  try {
    const response = await axios.post('/api/telescope/imaging/planet/start', params)

    // Optimistic update
    this.imaging.mode = 'planetary'
    this.imaging.active = true

    this.addMessage('Planetary imaging started')
  } catch (err) {
    // Revert optimistic update
    this.imaging.active = false

    // Set error state
    this.error = err.response?.data?.detail || 'Failed to start planetary imaging'

    // Show toast notification (Phase 7 - Visual Polish)
    this.showErrorToast(this.error)

    console.error('Planetary imaging error:', err)
  } finally {
    this.loading = false
  }
}
```

**Network Error Recovery**:
- Polling failure → Show "Connection Lost" indicator in header
- 3 consecutive polling failures → Stop polling, show reconnect button
- Manual reconnect → Clear error, restart polling
- Automatic retry with exponential backoff (2s, 4s, 8s, 16s, max 30s)

**User Feedback Mechanisms**:
- **Immediate feedback**: Loading spinners on buttons during async operations
- **Success feedback**: Toast notifications (Phase 7) or message log entry
- **Error feedback**: Toast notifications (Phase 7) + error state in store (red text/border)
- **Validation feedback**: Disable buttons when action not allowed (e.g., "Start Imaging" disabled when already imaging)

**Preview Frame Handling**:
- Frame fetch fails → Keep showing last successful frame + "Preview stale" indicator
- No frames available → Show placeholder "No preview available - start imaging to see live view"
- Stale frame (>10 seconds old) → Show timestamp + "Preview may be stale" warning

---

## 5. Testing Strategy

### Per-Phase Testing Approach

Each phase follows the same testing pattern:

**Backend Testing**:
1. **Unit tests** for new seestar_client methods (mock WebSocket responses)
2. **API endpoint tests** (FastAPI TestClient) - verify request/response handling
3. **Manual verification** with real telescope - send commands, verify telescope responds correctly

**Frontend Testing**:
1. **Store action tests** - verify state updates, error handling, API calls
2. **Component tests** - verify UI renders correctly, buttons call correct actions
3. **Manual browser testing** - click through UI, verify visual appearance

**Integration Testing** (per phase):
1. Start backend + frontend locally
2. Connect to real telescope (or mock telescope server if available)
3. Execute full user workflow (e.g., start planetary imaging → verify preview updates → stop imaging)
4. Verify state synchronization (polling updates UI correctly)
5. Test error cases (disconnect telescope mid-operation, send invalid commands)

### Phase-Specific Test Cases

**Phase 1 (Layout)**:
- Verify all 8 existing panels consolidated to 4 areas
- Test responsive layout on different screen sizes
- Verify header shows position/hardware status correctly

**Phase 2 (Video/Streaming + Live Preview)**:
- Verify file-based preview polling works (frames update every 1-2 seconds)
- Test recording start/stop (verify telescope creates AVI file)
- Test preview with no imaging active (shows placeholder)
- Test preview with stale frames (shows warning)

**Phase 3 (Planetary Imaging)**:
- Test planet scan (returns list of visible planets)
- Test planetary stacking start/stop
- Verify mode toggle switches between deep sky and planetary
- Test error case: start planetary while deep sky imaging active

**Phase 4 (Polar Alignment)**:
- Test start/stop/pause polar alignment
- Verify only works in equatorial mode (error in alt/az mode)
- Test alignment progress updates in UI

**Phase 5 (Object Tracking)**:
- Test tracking for each object type (satellite, comet, asteroid)
- Verify tracking stops when telescope parked
- Test object type selector UI

**Phase 6 (Annotation Control)**:
- Test annotation toggle on/off
- Verify annotations appear in preview (if visible in frames)

**Phase 7 (Visual Polish)**:
- Manual visual testing of all loading states, transitions, animations
- Test toast notifications for errors and success
- Test confirmation dialogs for destructive actions
- Accessibility testing (keyboard navigation, screen reader)

### Regression Testing

After each phase, verify existing functionality still works:
- Connection/disconnection
- Park/unpark
- Slew to target
- Plan execution
- Dew heater control

### Acceptance Criteria (per phase)

- All new backend tests passing
- All new frontend tests passing
- Manual verification with real telescope successful
- No regressions in existing functionality
- Code committed with clear commit message

---

## Implementation Notes

### File-Based Preview Discovery

Based on Android app analysis, the Seestar S50 does NOT provide RTSP streaming despite accepting `start_avi_rtmp` commands. Instead, it writes preview frames to the file system. The backend must:

1. Use file transfer API to access telescope's preview frame directory
2. Poll for latest frame file (by timestamp/filename)
3. Serve frame to frontend as JPEG/PNG

### Mount Mode Dependencies

Some features require specific mount modes:
- **Polar Alignment**: Only works in Equatorial mode (`equ_mode: true`)
- **Object Tracking**: Works in both modes but behavior differs

The UI should check mount mode before allowing these operations and show appropriate error messages.

### State Machine Considerations

Based on Android app analysis (StartRtmpAction.java), some commands require state checks:
- Check if operation already running before starting
- Stop existing operation before starting new one of same type
- Proper sequencing with delays for state transitions

### API Command Reference

All Tier 1 commands identified in gap analysis (`docs/seestar-gap-analysis.md`):
- Polar Alignment: `iscope_start_polar_align`, `iscope_stop_polar_align`, `iscope_pause_polar_align`
- Planetary Imaging: `iscope_start_planet_stack`, `iscope_stop_planet_stack`, `iscope_start_scan_planet`
- Video Recording: `start_avi_rtmp`, `stop_avi_rtmp`, `start_record_avi`, `stop_record_avi`
- Object Tracking: `start_track_object` with parameters for object type (satellite/comet/asteroid)
- Annotation: `start_annotate`, `stop_annotate`

---

## Success Metrics

Implementation complete when:
- All 5 Tier 1 features functional with real telescope
- Live preview displays file-based frames reliably (1-2 second refresh)
- Layout optimized (4 main areas, responsive, good space usage)
- Visual polish applied (loading states, status indicators, error feedback)
- All tests passing (backend unit tests, frontend component tests, integration tests)
- No regressions in existing features
- Documentation updated (API docs, user guide)
