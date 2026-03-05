# Endpoint Integration Fixes Required

## Summary
The UI components are not properly integrated with available backend endpoints. Many components use fake/local data instead of real API calls.

---

## 1. Processing View - File Browser

### Current (WRONG):
```javascript
// frontend/vue-app/src/stores/processing.js
browseDirectory('/data')  // Wrong directory
GET /api/files/browse?path=/data  // Endpoint probably doesn't exist
```

### Should Be:
```javascript
// Browse FITS files from mounted volume
GET /api/captures?limit=100&offset=0

// Or scan for new files first
GET /api/processing/scan-new
```

### Fix Required:
- Update `processing.js` store to use `/api/captures`
- Add scan button to trigger `/api/processing/scan-new`
- Update FileBrowser to show captures from database
- Add target grouping (files grouped by object like M31, M81, etc.)

---

## 2. Hardware Panel - Dew Heater Control

### Current (WRONG):
```javascript
// frontend/vue-app/src/stores/execution.js
toggleDewHeater() {
  this.hardware.dewHeaterStatus =
    this.hardware.dewHeaterStatus === 'Off' ? 'On' : 'Off'
  // Just toggles local state - doesn't call API!
}
```

### Should Be:
```javascript
// Get current status
GET /api/telescope/features/hardware/dew-heater/status
Response: {"enabled": true, "power": 50}

// Toggle dew heater
POST /api/telescope/features/hardware/dew-heater
Body: {"enabled": true, "power": 50}
```

### Fix Required:
- Call actual dew heater API endpoints
- Fetch status when telescope connects
- Allow power level control (0-100%)

---

## 3. Missing: Focuser Control Panel

### Available Endpoints:
```
POST /api/telescope/features/focuser/move
Body: {"steps": 100, "direction": "in|out"}

POST /api/telescope/features/focuser/stop

POST /api/telescope/features/focuser/factory-reset
```

### Fix Required:
- Create `FocuserPanel.vue` component
- Add to ExecutionView sidebar
- Controls: In/Out buttons, step size input, auto-focus button

---

## 4. Missing: System Info Display

### Available Endpoints:
```
GET /api/telescope/features/system/info
Response: {
  "model": "Seestar S50",
  "firmware": "1.2.3",
  "serial": "ABC123",
  "temperature": 25.5
}

GET /api/telescope/features/system/time
```

### Fix Required:
- Add system info to TelescopePanel or create SystemInfoPanel
- Display: Model, firmware version, temperature, time
- Fetch on connection

---

## 5. Temperature Not From Telescope

### Current (WRONG):
```vue
<!-- HardwarePanel.vue -->
<span>{{ executionStore.hardware.sensorTemp || '--' }}</span>
<!-- Never populated from API -->
```

### Should Be:
```javascript
// Get from system info
GET /api/telescope/features/system/info
Response: {"temperature": 25.5}

// Or from status
GET /api/telescope/status
// Parse temperature from response
```

### Fix Required:
- Fetch temperature from system info endpoint
- Update HardwarePanel to display actual sensor temp

---

## 6. Preview Images Not Using Telescope

### Current (WRONG):
```javascript
// ExecutionView.vue
await axios.get('/api/telescope/features/images/list', {
  params: { image_type: 'preview', limit: 1 }
})
// This endpoint requires telescope connection
```

### Should ALSO Use:
```javascript
// For telescope images
GET /api/telescope/features/images/list?image_type=preview

// For local preview
GET /api/telescope/preview/latest

// For live stream info
GET /api/telescope/live-preview
```

### Fix Required:
- Add source selector (telescope vs local)
- Proper error handling when telescope not connected
- Fallback to local images

---

## 7. Local Image Library Not Connected

### Available But Not Used:
```
GET /api/captures  // List all captures from /fits
GET /api/captures/{catalog_id}  // Get captures for specific object
GET /api/captures/{catalog_id}/files  // List files for capture

// Should be used in ProcessingView
```

### Fix Required:
- Replace `/api/files/browse` with `/api/captures`
- Group images by target object
- Show metadata (exposure, date, filter, etc.)

---

## 8. Processing Not Using Batch Endpoints

### Available But Not Used:
```
GET /api/processing/scan-new
// Scans /fits for new files

POST /api/processing/batch-process-new
// Processes all unprocessed files

GET /api/processing/status/{task_id}
// Monitor processing progress
```

### Current (WRONG):
```javascript
POST /api/process/stack-and-stretch
// Endpoint probably doesn't match backend
```

### Fix Required:
- Add "Scan for New Images" button
- Use proper processing endpoints
- Show scan results before processing

---

## 9. Plan Execution Not Connected

### Available But Not Used:
```
POST /api/telescope/execute
Body: {
  "scheduled_targets": [...],
  "park_when_done": true
}

GET /api/telescope/progress?execution_id=abc123

POST /api/telescope/abort
```

### Current:
- PlanningView creates plans
- ExecutionView has plan execution UI
- But plan execution uses local state, not these endpoints

### Fix Required:
- Connect PlanningView "Execute" button to `/api/telescope/execute`
- Poll `/api/telescope/progress` during execution
- Show real progress from backend

---

## 10. Missing: WiFi & System Controls

### Available But No UI:
```
GET /api/telescope/features/wifi/scan
POST /api/telescope/features/wifi/connect
GET /api/telescope/features/wifi/saved

POST /api/telescope/features/system/shutdown
POST /api/telescope/features/system/reboot
POST /api/telescope/features/system/location
```

### Fix Required:
- Add WiFi management panel (settings view?)
- Add system controls (shutdown/reboot)
- Location configuration

---

## Priority Fixes (In Order):

### High Priority:
1. **Fix ProcessingView to use `/api/captures`** - Critical for accessing telescope images
2. **Fix HardwarePanel dew heater** - Actually control hardware
3. **Add FocuserPanel** - Essential for imaging
4. **Fix preview image source** - Currently broken when telescope disconnected

### Medium Priority:
5. **Add system info display** - Useful diagnostic info
6. **Connect plan execution** - Makes planning actually work
7. **Add scan button** - Discover new telescope images

### Low Priority:
8. **WiFi management UI** - Nice to have
9. **System controls UI** - Power management

---

## Implementation Plan:

### Phase 1: Fix Existing Components
- [ ] Update `processing.js` to use `/api/captures`
- [ ] Update `execution.js` dew heater to call API
- [ ] Update `execution.js` temperature from system info
- [ ] Fix preview image fallback logic

### Phase 2: Add Missing Components
- [ ] Create `FocuserPanel.vue`
- [ ] Create `SystemInfoPanel.vue`
- [ ] Add scan button to ProcessingView

### Phase 3: Connect Advanced Features
- [ ] Wire up plan execution to backend
- [ ] Add batch processing UI
- [ ] Add WiFi management (optional)

Would you like me to start implementing these fixes?
