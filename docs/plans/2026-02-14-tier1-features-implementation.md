# Tier 1 Features + UX Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement all 5 Tier 1 telescope features with optimized execution UX in 7 integrated phases

**Architecture:** Integrated Feature+UX approach - each phase delivers working backend + polished frontend simultaneously, building on previous phases

**Tech Stack:** Vue 3 + Pinia, FastAPI, Seestar S50 WebSocket API, Tailwind CSS, Axios

---

## Phase 1: Layout Foundation (UX-B)

### Task 1.1: Consolidate ExecutionView Layout

**Files:**
- Modify: `frontend/vue-app/src/views/ExecutionView.vue`

**Step 1: Review current layout structure**

Read the current ExecutionView to understand existing panel organization:

```bash
cat frontend/vue-app/src/views/ExecutionView.vue | grep -A 5 "class.*panel\|class.*grid"
```

Expected: See 8 separate panel components in current layout

**Step 2: Reorganize to 4-area flex layout**

Replace the main content grid section with consolidated 4-area layout:

```vue
<!-- Replace existing main content grid with this -->
<div class="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 p-4 overflow-auto">
  <!-- Left Column: Telescope Control + Imaging (2/3 width on large screens) -->
  <div class="lg:col-span-2 space-y-4">
    <!-- Telescope Control Area -->
    <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h2 class="text-lg font-semibold text-gray-100 mb-4">Telescope Control</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <TelescopePanel />
        <DirectionalControlPanel />
      </div>
    </div>

    <!-- Imaging Area -->
    <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h2 class="text-lg font-semibold text-gray-100 mb-4">Imaging</h2>
      <ImagingPanel />
    </div>

    <!-- Live Preview -->
    <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h2 class="text-lg font-semibold text-gray-100 mb-4">Live Preview</h2>
      <LivePreviewPanel />
    </div>
  </div>

  <!-- Right Column: Plan Execution + Messages (1/3 width on large screens) -->
  <div class="space-y-4">
    <!-- Plan Execution Area -->
    <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h2 class="text-lg font-semibold text-gray-100 mb-4">Plan Execution</h2>
      <PlanExecutionPanel />
    </div>

    <!-- Messages -->
    <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <h2 class="text-lg font-semibold text-gray-100 mb-4">Messages</h2>
      <MessagesPanel />
    </div>
  </div>
</div>
```

**Step 3: Test layout in browser**

Start dev server and verify layout:

```bash
cd frontend/vue-app && npm run dev
```

Expected:
- Large screens: 2/3 width left column (telescope/imaging/preview), 1/3 width right column (plan/messages)
- Small screens: Single column, stacked vertically
- All existing functionality still works

**Step 4: Remove unused panel components**

Remove these now-redundant panel imports and component registrations:
- HardwarePanel (already removed in previous work)
- Any other panels now integrated into 4 areas

**Step 5: Commit**

```bash
git add frontend/vue-app/src/views/ExecutionView.vue
git commit -m "feat(ui): consolidate ExecutionView to 4-area responsive layout"
```

---

## Phase 2: Video/Streaming + Live Preview (Tier 1 + UX-D)

### Task 2.1: Backend - File-Based Preview Frame Discovery

**Files:**
- Modify: `backend/app/clients/seestar_client.py`
- Create: `backend/app/services/preview_frame_service.py`

**Step 1: Write failing test for get_latest_preview_frame**

Create test file:

```python
# tests/test_seestar_client_preview.py
import pytest
from app.clients.seestar_client import SeestarClient

@pytest.mark.asyncio
async def test_get_latest_preview_frame_returns_jpeg_bytes():
    """Test that get_latest_preview_frame returns JPEG image bytes."""
    client = SeestarClient()
    await client.connect("192.168.2.47")

    # Start preview to ensure frames are being generated
    await client.start_view(mode="star")

    # Wait a moment for frames to be generated
    import asyncio
    await asyncio.sleep(2)

    # Get latest frame
    frame_bytes = await client.get_latest_preview_frame()

    assert frame_bytes is not None
    assert isinstance(frame_bytes, bytes)
    assert frame_bytes.startswith(b'\xff\xd8')  # JPEG magic bytes
    assert len(frame_bytes) > 1000  # Reasonable minimum size

    await client.disconnect()
```

**Step 2: Run test to verify it fails**

```bash
cd backend && pytest tests/test_seestar_client_preview.py::test_get_latest_preview_frame_returns_jpeg_bytes -v
```

Expected: FAIL - "AttributeError: 'SeestarClient' object has no attribute 'get_latest_preview_frame'"

**Step 3: Implement get_latest_preview_frame in seestar_client.py**

Add method to SeestarClient class (around line 2900, after existing imaging methods):

```python
async def get_latest_preview_frame(self) -> Optional[bytes]:
    """Get the latest preview frame from telescope's file system.

    The Seestar S50 writes preview frames to /mnt/sda1/seestar/preview/
    (or similar path). We need to:
    1. List files in preview directory
    2. Find most recent frame file
    3. Download and return as bytes

    Returns:
        JPEG image bytes or None if no frame available
    """
    try:
        # First, get list of files in preview directory
        # Note: This uses the file transfer API, not WebSocket commands
        # Path discovered from Android app analysis
        preview_path = "/mnt/sda1/seestar/preview"

        # Use get_target_list to list files (this is how Android app does it)
        response = await self._send_command("get_target_list", {
            "path": preview_path,
            "type": "file"  # List files, not directories
        })

        if response.get("code") != 0 or not response.get("files"):
            logger.warning(f"No preview frames found in {preview_path}")
            return None

        # Sort files by timestamp (newest first)
        files = response["files"]
        files.sort(key=lambda f: f.get("timestamp", 0), reverse=True)

        if not files:
            return None

        # Get the most recent file
        latest_file = files[0]
        file_path = f"{preview_path}/{latest_file['name']}"

        # Download file content
        download_response = await self._send_command("download_file", {
            "path": file_path
        })

        if download_response.get("code") != 0:
            logger.error(f"Failed to download preview frame: {file_path}")
            return None

        # File content is base64 encoded in response
        import base64
        file_content_b64 = download_response.get("content")
        if not file_content_b64:
            return None

        frame_bytes = base64.b64decode(file_content_b64)
        return frame_bytes

    except Exception as e:
        logger.error(f"Error getting preview frame: {e}")
        return None
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/test_seestar_client_preview.py::test_get_latest_preview_frame_returns_jpeg_bytes -v
```

Expected: PASS (may need to adjust paths/commands based on actual telescope API)

**Step 5: Commit**

```bash
git add backend/app/clients/seestar_client.py tests/test_seestar_client_preview.py
git commit -m "feat(backend): add file-based preview frame fetching"
```

### Task 2.2: Backend - Preview Frame API Endpoint

**Files:**
- Create: `backend/app/routers/preview.py`
- Modify: `backend/app/main.py`

**Step 1: Write failing test for preview endpoint**

```python
# tests/test_preview_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_preview_frame_returns_jpeg():
    """Test GET /api/telescope/preview/frame returns JPEG image."""
    # Note: Assumes telescope is connected (may need mock)
    response = client.get("/api/telescope/preview/frame")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 1000  # Reasonable minimum size
    assert response.content.startswith(b'\xff\xd8')  # JPEG magic bytes

def test_get_preview_frame_when_no_frames():
    """Test endpoint returns 404 when no preview frames available."""
    # Mock scenario: no frames available
    # May need to mock seestar_client.get_latest_preview_frame to return None

    response = client.get("/api/telescope/preview/frame")

    # Could be 404 or 503, depending on implementation
    assert response.status_code in [404, 503]
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_preview_api.py -v
```

Expected: FAIL - "404 Not Found" (endpoint doesn't exist yet)

**Step 3: Create preview router**

```python
# backend/app/routers/preview.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
import logging

from app.clients.seestar_client import get_seestar_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/telescope/preview", tags=["preview"])


@router.get("/frame")
async def get_preview_frame():
    """Get the latest preview frame from telescope.

    Returns JPEG image bytes.
    """
    client = get_seestar_client()

    if not client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    frame_bytes = await client.get_latest_preview_frame()

    if frame_bytes is None:
        raise HTTPException(
            status_code=503,
            detail="No preview frames available - start imaging to generate frames"
        )

    return Response(content=frame_bytes, media_type="image/jpeg")
```

**Step 4: Register router in main.py**

Add import and include router:

```python
# backend/app/main.py
# Add to imports
from app.routers import preview

# Add to router includes (around line 30)
app.include_router(preview.router)
```

**Step 5: Run test to verify it passes**

```bash
pytest tests/test_preview_api.py -v
```

Expected: PASS (with real telescope connected) or mock-based pass

**Step 6: Commit**

```bash
git add backend/app/routers/preview.py backend/app/main.py tests/test_preview_api.py
git commit -m "feat(api): add preview frame endpoint"
```

### Task 2.3: Backend - Video Recording Commands

**Files:**
- Modify: `backend/app/clients/seestar_client.py`
- Modify: `backend/app/routers/telescope.py`

**Step 1: Write failing test for video recording**

```python
# tests/test_video_recording.py
import pytest
from app.clients.seestar_client import SeestarClient

@pytest.mark.asyncio
async def test_start_stop_video_recording():
    """Test starting and stopping video recording."""
    client = SeestarClient()
    await client.connect("192.168.2.47")

    # Start recording
    result = await client.start_record_avi(filename="test_recording")
    assert result is True

    # Wait briefly
    import asyncio
    await asyncio.sleep(2)

    # Stop recording
    result = await client.stop_record_avi()
    assert result is True

    await client.disconnect()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_video_recording.py -v
```

Expected: FAIL - "AttributeError: 'SeestarClient' object has no attribute 'start_record_avi'"

**Step 3: Implement video recording methods**

Add to SeestarClient class:

```python
async def start_record_avi(self, filename: str = None) -> bool:
    """Start AVI video recording.

    Args:
        filename: Optional filename for recording (without extension)

    Returns:
        True if recording started successfully
    """
    params = {}
    if filename:
        params["name"] = filename

    response = await self._send_command("start_record_avi", params)

    if response.get("code") == 0:
        logger.info(f"Video recording started: {filename or 'auto'}")
        return True
    else:
        logger.error(f"Failed to start video recording: {response}")
        return False

async def stop_record_avi(self) -> bool:
    """Stop AVI video recording.

    Returns:
        True if recording stopped successfully
    """
    response = await self._send_command("stop_record_avi", {})

    if response.get("code") == 0:
        logger.info("Video recording stopped")
        return True
    else:
        logger.error(f"Failed to stop video recording: {response}")
        return False
```

**Step 4: Add API endpoints for video recording**

Add to `backend/app/routers/telescope.py`:

```python
@router.post("/recording/start")
async def start_recording(filename: str = None):
    """Start video recording."""
    client = get_seestar_client()

    if not client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    success = await client.start_record_avi(filename=filename)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to start recording")

    return {"status": "recording_started", "filename": filename or "auto"}


@router.post("/recording/stop")
async def stop_recording():
    """Stop video recording."""
    client = get_seestar_client()

    if not client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    success = await client.stop_record_avi()

    if not success:
        raise HTTPException(status_code=500, detail="Failed to stop recording")

    return {"status": "recording_stopped"}
```

**Step 5: Run tests to verify they pass**

```bash
pytest tests/test_video_recording.py -v
```

Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/clients/seestar_client.py backend/app/routers/telescope.py tests/test_video_recording.py
git commit -m "feat(backend): add video recording (AVI) support"
```

### Task 2.4: Frontend - Fix Live Preview Polling

**Files:**
- Modify: `frontend/vue-app/src/views/ExecutionView.vue`
- Modify: `frontend/vue-app/src/stores/execution.js`

**Step 1: Update preview polling in ExecutionView**

Replace the existing `fetchPreview` function in ExecutionView.vue:

```vue
<script setup>
// ... existing imports ...

// Live preview polling
const previewImage = ref(null)
const previewUpdateKey = ref(0)
const previewInterval = ref(null)
const previewStale = ref(false)
const lastPreviewUpdate = ref(null)

const startPreviewPolling = () => {
  if (previewInterval.value) return

  previewInterval.value = setInterval(async () => {
    await fetchPreview()
  }, 1500) // Poll every 1.5 seconds

  // Also start immediately
  fetchPreview()
}

const stopPreviewPolling = () => {
  if (previewInterval.value) {
    clearInterval(previewInterval.value)
    previewInterval.value = null
  }
}

const fetchPreview = async () => {
  try {
    // Add timestamp to prevent caching
    const timestamp = Date.now()
    const response = await axios.get(`/api/telescope/preview/frame?t=${timestamp}`, {
      responseType: 'blob'
    })

    // Convert blob to object URL
    const imageUrl = URL.createObjectURL(response.data)

    // Revoke old URL to prevent memory leak
    if (previewImage.value && previewImage.value.startsWith('blob:')) {
      URL.revokeObjectURL(previewImage.value)
    }

    previewImage.value = imageUrl
    previewUpdateKey.value++
    lastPreviewUpdate.value = new Date()
    previewStale.value = false
  } catch (err) {
    if (err.response?.status === 503) {
      // No frames available - not an error, just no preview yet
      previewStale.value = true
    } else {
      console.warn('Preview fetch failed:', err)
    }
  }
}

// Check if preview is stale (>10 seconds old)
const checkPreviewStaleness = () => {
  if (lastPreviewUpdate.value) {
    const age = (new Date() - lastPreviewUpdate.value) / 1000
    previewStale.value = age > 10
  }
}

// Start/stop polling based on connection status
watch(() => executionStore.connected, (connected) => {
  if (connected) {
    startPreviewPolling()
  } else {
    stopPreviewPolling()
  }
})

// Check staleness every 5 seconds
onMounted(() => {
  const stalenessInterval = setInterval(checkPreviewStaleness, 5000)

  onUnmounted(() => {
    clearInterval(stalenessInterval)
    stopPreviewPolling()

    // Cleanup blob URLs
    if (previewImage.value && previewImage.value.startsWith('blob:')) {
      URL.revokeObjectURL(previewImage.value)
    }
  })
})
</script>
```

**Step 2: Update LivePreviewPanel component template**

Update the preview image display in ExecutionView.vue (in the LivePreviewPanel section):

```vue
<div class="relative bg-gray-900 rounded aspect-video flex items-center justify-center">
  <img
    v-if="previewImage"
    :key="previewUpdateKey"
    :src="previewImage"
    alt="Live Preview"
    class="w-full h-full object-contain rounded"
  />
  <div v-else class="text-gray-500 text-center p-8">
    <Camera class="w-16 h-16 mx-auto mb-4 opacity-50" />
    <p>No preview available</p>
    <p class="text-sm mt-2">Start imaging to see live view</p>
  </div>

  <!-- Stale indicator -->
  <div
    v-if="previewStale && previewImage"
    class="absolute top-2 right-2 bg-yellow-600 text-white text-xs px-2 py-1 rounded"
  >
    Preview may be stale
  </div>
</div>
```

**Step 3: Test in browser**

```bash
cd frontend/vue-app && npm run dev
```

Manual test:
1. Connect to telescope
2. Start imaging (deep sky mode)
3. Verify preview updates every 1-2 seconds
4. Stop imaging, verify "No preview available" placeholder
5. Wait >10 seconds, verify "Preview may be stale" indicator

**Step 4: Commit**

```bash
git add frontend/vue-app/src/views/ExecutionView.vue
git commit -m "feat(ui): fix live preview with file-based polling"
```

### Task 2.5: Frontend - Add Recording Controls

**Files:**
- Modify: `frontend/vue-app/src/stores/execution.js`
- Modify: `frontend/vue-app/src/components/execution/ImagingPanel.vue`

**Step 1: Add recording state to execution store**

Add to execution.js state:

```javascript
// In state() return object:
recording: {
  active: false,
  filename: null
},
```

**Step 2: Add recording actions to execution store**

Add to execution.js actions:

```javascript
async startRecording(filename = null) {
  if (!this.connected) {
    this.error = 'Telescope not connected'
    return
  }

  try {
    await axios.post('/api/telescope/recording/start', { filename })
    this.recording.active = true
    this.recording.filename = filename || 'auto'
    this.addMessage(`Video recording started${filename ? ': ' + filename : ''}`)
  } catch (err) {
    this.error = 'Failed to start recording: ' + err.message
    console.error('Recording start error:', err)
  }
},

async stopRecording() {
  try {
    await axios.post('/api/telescope/recording/stop')
    this.recording.active = false
    this.addMessage('Video recording stopped')
  } catch (err) {
    this.error = 'Failed to stop recording: ' + err.message
    console.error('Recording stop error:', err)
  }
},
```

**Step 3: Add recording controls to ImagingPanel**

Add recording section to ImagingPanel.vue (after existing imaging controls):

```vue
<!-- Recording Controls -->
<div class="mt-6 pt-6 border-t border-gray-700">
  <h3 class="text-sm font-semibold text-gray-300 mb-3">Video Recording</h3>

  <div class="space-y-3">
    <!-- Recording Status -->
    <div v-if="executionStore.recording.active" class="flex items-center gap-2 text-sm">
      <div class="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
      <span class="text-gray-300">Recording: {{ executionStore.recording.filename }}</span>
    </div>

    <!-- Record Button -->
    <button
      v-if="!executionStore.recording.active"
      @click="executionStore.startRecording()"
      :disabled="!executionStore.connected"
      class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-red-600 hover:bg-red-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
    >
      Start Recording
    </button>
    <button
      v-else
      @click="executionStore.stopRecording()"
      class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-gray-700 hover:bg-gray-600 text-gray-200"
    >
      Stop Recording
    </button>
  </div>
</div>
```

**Step 4: Test in browser**

Manual test:
1. Connect to telescope
2. Click "Start Recording"
3. Verify recording indicator shows (red pulsing dot)
4. Click "Stop Recording"
5. Verify recording indicator disappears

**Step 5: Commit**

```bash
git add frontend/vue-app/src/stores/execution.js frontend/vue-app/src/components/execution/ImagingPanel.vue
git commit -m "feat(ui): add video recording controls to imaging panel"
```

---

## Phase 3: Planetary Imaging (Tier 1)

### Task 3.1: Backend - Planetary Imaging Commands

**Files:**
- Modify: `backend/app/clients/seestar_client.py`

**Step 1: Write failing test for planetary imaging**

```python
# tests/test_planetary_imaging.py
import pytest
from app.clients.seestar_client import SeestarClient

@pytest.mark.asyncio
async def test_scan_planets():
    """Test scanning for visible planets."""
    client = SeestarClient()
    await client.connect("192.168.2.47")

    planets = await client.start_scan_planet()

    assert planets is not None
    assert isinstance(planets, list)
    # May be empty list if no planets visible

    await client.disconnect()

@pytest.mark.asyncio
async def test_start_stop_planet_stack():
    """Test planetary stacking."""
    client = SeestarClient()
    await client.connect("192.168.2.47")

    # Start planetary stacking
    result = await client.start_planet_stack(planet_name="Mars")
    assert result is True

    # Wait briefly
    import asyncio
    await asyncio.sleep(2)

    # Stop stacking
    result = await client.stop_planet_stack()
    assert result is True

    await client.disconnect()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_planetary_imaging.py -v
```

Expected: FAIL - AttributeError for missing methods

**Step 3: Implement planetary imaging methods**

Add to SeestarClient class:

```python
async def start_scan_planet(self) -> Optional[list]:
    """Scan for visible planets in current sky.

    Returns:
        List of planet dictionaries with name, ra, dec, etc.
        None if scan failed.
    """
    response = await self._send_command("iscope_start_scan_planet", {})

    if response.get("code") == 0:
        planets = response.get("planets", [])
        logger.info(f"Planet scan complete: {len(planets)} planets found")
        return planets
    else:
        logger.error(f"Planet scan failed: {response}")
        return None

async def start_planet_stack(
    self,
    planet_name: str,
    exposure: int = 10,
    gain: int = 80
) -> bool:
    """Start planetary imaging/stacking mode.

    Args:
        planet_name: Name of planet to image
        exposure: Exposure time in milliseconds
        gain: Gain value (0-100)

    Returns:
        True if stacking started successfully
    """
    params = {
        "target": planet_name,
        "exposure": exposure,
        "gain": gain
    }

    response = await self._send_command("iscope_start_planet_stack", params)

    if response.get("code") == 0:
        logger.info(f"Planetary stacking started: {planet_name}")
        return True
    else:
        logger.error(f"Failed to start planetary stacking: {response}")
        return False

async def stop_planet_stack(self) -> bool:
    """Stop planetary imaging/stacking.

    Returns:
        True if stacking stopped successfully
    """
    response = await self._send_command("iscope_stop_planet_stack", {})

    if response.get("code") == 0:
        logger.info("Planetary stacking stopped")
        return True
    else:
        logger.error(f"Failed to stop planetary stacking: {response}")
        return False
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_planetary_imaging.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/clients/seestar_client.py tests/test_planetary_imaging.py
git commit -m "feat(backend): add planetary imaging commands"
```

### Task 3.2: Backend - Planetary Imaging API Endpoints

**Files:**
- Modify: `backend/app/routers/telescope.py`

**Step 1: Add planetary imaging endpoints**

Add to telescope.py router:

```python
@router.post("/imaging/planet/scan")
async def scan_planets():
    """Scan for visible planets in current sky."""
    client = get_seestar_client()

    if not client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    planets = await client.start_scan_planet()

    if planets is None:
        raise HTTPException(status_code=500, detail="Planet scan failed")

    return {"planets": planets}


@router.post("/imaging/planet/start")
async def start_planetary_imaging(
    planet_name: str,
    exposure: int = 10,
    gain: int = 80
):
    """Start planetary imaging mode."""
    client = get_seestar_client()

    if not client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    success = await client.start_planet_stack(
        planet_name=planet_name,
        exposure=exposure,
        gain=gain
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to start planetary imaging")

    return {
        "status": "planetary_imaging_started",
        "planet": planet_name,
        "exposure": exposure,
        "gain": gain
    }


@router.post("/imaging/planet/stop")
async def stop_planetary_imaging():
    """Stop planetary imaging mode."""
    client = get_seestar_client()

    if not client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    success = await client.stop_planet_stack()

    if not success:
        raise HTTPException(status_code=500, detail="Failed to stop planetary imaging")

    return {"status": "planetary_imaging_stopped"}
```

**Step 2: Test endpoints**

Manual test with curl or API client:

```bash
# Scan for planets
curl -X POST http://localhost:9247/api/telescope/imaging/planet/scan

# Start planetary imaging
curl -X POST http://localhost:9247/api/telescope/imaging/planet/start \
  -H "Content-Type: application/json" \
  -d '{"planet_name": "Mars", "exposure": 10, "gain": 80}'

# Stop planetary imaging
curl -X POST http://localhost:9247/api/telescope/imaging/planet/stop
```

Expected: Success responses with appropriate status codes

**Step 3: Commit**

```bash
git add backend/app/routers/telescope.py
git commit -m "feat(api): add planetary imaging endpoints"
```

### Task 3.3: Frontend - Planetary Imaging Mode Toggle

**Files:**
- Modify: `frontend/vue-app/src/stores/execution.js`
- Modify: `frontend/vue-app/src/components/execution/ImagingPanel.vue`

**Step 1: Add planetary imaging state to store**

Update imaging state in execution.js:

```javascript
// In state() return object, update imaging:
imaging: {
  active: false,
  mode: 'deep-sky', // 'deep-sky' or 'planetary'
  framesCaptured: 0,
  currentExposure: 0,
  totalExposure: 0,
  selectedPlanet: null,
  availablePlanets: []
},
```

**Step 2: Add planetary imaging actions to store**

Add to execution.js actions:

```javascript
async scanPlanets() {
  if (!this.connected) {
    this.error = 'Telescope not connected'
    return
  }

  try {
    const response = await axios.post('/api/telescope/imaging/planet/scan')
    this.imaging.availablePlanets = response.data.planets || []
    this.addMessage(`Planet scan complete: ${this.imaging.availablePlanets.length} planets found`)
  } catch (err) {
    this.error = 'Failed to scan planets: ' + err.message
    console.error('Planet scan error:', err)
  }
},

async startPlanetaryImaging(params) {
  if (!this.connected) {
    this.error = 'Telescope not connected'
    return
  }

  try {
    await axios.post('/api/telescope/imaging/planet/start', {
      planet_name: params.planet,
      exposure: params.exposure || 10,
      gain: params.gain || 80
    })

    this.imaging.active = true
    this.imaging.mode = 'planetary'
    this.imaging.selectedPlanet = params.planet
    this.addMessage(`Planetary imaging started: ${params.planet}`)
  } catch (err) {
    this.error = 'Failed to start planetary imaging: ' + err.message
    console.error('Planetary imaging error:', err)
  }
},

async stopPlanetaryImaging() {
  try {
    await axios.post('/api/telescope/imaging/planet/stop')
    this.imaging.active = false
    this.imaging.selectedPlanet = null
    this.addMessage('Planetary imaging stopped')
  } catch (err) {
    this.error = 'Failed to stop planetary imaging: ' + err.message
    console.error('Stop planetary imaging error:', err)
  }
},
```

**Step 3: Add mode toggle to ImagingPanel**

Add mode selector at top of ImagingPanel.vue:

```vue
<template>
  <div class="space-y-4">
    <!-- Mode Toggle -->
    <div class="flex gap-2 p-1 bg-gray-900 rounded-lg">
      <button
        @click="setMode('deep-sky')"
        :class="[
          'flex-1 px-4 py-2 rounded-md font-medium transition-colors',
          executionStore.imaging.mode === 'deep-sky'
            ? 'bg-blue-600 text-white'
            : 'text-gray-400 hover:text-gray-200'
        ]"
      >
        Deep Sky
      </button>
      <button
        @click="setMode('planetary')"
        :class="[
          'flex-1 px-4 py-2 rounded-md font-medium transition-colors',
          executionStore.imaging.mode === 'planetary'
            ? 'bg-blue-600 text-white'
            : 'text-gray-400 hover:text-gray-200'
        ]"
      >
        Planetary
      </button>
    </div>

    <!-- Deep Sky Controls (existing) -->
    <div v-if="executionStore.imaging.mode === 'deep-sky'" class="space-y-3">
      <!-- Keep existing deep sky imaging controls here -->
    </div>

    <!-- Planetary Controls (new) -->
    <div v-else-if="executionStore.imaging.mode === 'planetary'" class="space-y-3">
      <!-- Planet Selection -->
      <div>
        <label class="block text-sm text-gray-400 mb-2">Target Planet</label>
        <div class="flex gap-2">
          <select
            v-model="selectedPlanet"
            class="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-gray-200"
          >
            <option value="">Select planet...</option>
            <option
              v-for="planet in executionStore.imaging.availablePlanets"
              :key="planet.name"
              :value="planet.name"
            >
              {{ planet.name }}
            </option>
          </select>
          <button
            @click="executionStore.scanPlanets()"
            :disabled="!executionStore.connected"
            class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded disabled:opacity-50"
          >
            Scan
          </button>
        </div>
      </div>

      <!-- Exposure/Gain (similar to deep sky) -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-sm text-gray-400 mb-2">Exposure (ms)</label>
          <input
            v-model.number="planetaryExposure"
            type="number"
            min="1"
            max="1000"
            class="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-gray-200"
          />
        </div>
        <div>
          <label class="block text-sm text-gray-400 mb-2">Gain</label>
          <input
            v-model.number="planetaryGain"
            type="number"
            min="0"
            max="100"
            class="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-gray-200"
          />
        </div>
      </div>

      <!-- Start/Stop Button -->
      <button
        v-if="!executionStore.imaging.active"
        @click="startPlanetary"
        :disabled="!executionStore.connected || !selectedPlanet"
        class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Start Planetary Imaging
      </button>
      <button
        v-else
        @click="executionStore.stopPlanetaryImaging()"
        class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-red-600 hover:bg-red-700 text-white"
      >
        Stop Planetary Imaging
      </button>
    </div>

    <!-- Recording Controls (keep existing from Task 2.5) -->
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()

// Planetary imaging local state
const selectedPlanet = ref('')
const planetaryExposure = ref(10)
const planetaryGain = ref(80)

const setMode = (mode) => {
  if (!executionStore.imaging.active) {
    executionStore.imaging.mode = mode
  }
}

const startPlanetary = () => {
  executionStore.startPlanetaryImaging({
    planet: selectedPlanet.value,
    exposure: planetaryExposure.value,
    gain: planetaryGain.value
  })
}
</script>
```

**Step 4: Test in browser**

Manual test:
1. Connect to telescope
2. Toggle to "Planetary" mode
3. Click "Scan" to find planets
4. Select a planet from dropdown
5. Click "Start Planetary Imaging"
6. Verify imaging starts
7. Click "Stop Planetary Imaging"

**Step 5: Commit**

```bash
git add frontend/vue-app/src/stores/execution.js frontend/vue-app/src/components/execution/ImagingPanel.vue
git commit -m "feat(ui): add planetary imaging mode with planet selection"
```

---

## Phase 4: Polar Alignment (Tier 1)

### Task 4.1: Backend - Polar Alignment Commands

**Files:**
- Modify: `backend/app/clients/seestar_client.py`

**Step 1: Write failing test for polar alignment**

```python
# tests/test_polar_alignment.py
import pytest
from app.clients.seestar_client import SeestarClient

@pytest.mark.asyncio
async def test_polar_alignment_workflow():
    """Test polar alignment start/pause/stop workflow."""
    client = SeestarClient()
    await client.connect("192.168.2.47")

    # Check mount mode (polar align only works in equatorial mode)
    app_state = await client.get_app_state()
    if not app_state.get("equ_mode"):
        pytest.skip("Polar alignment requires equatorial mode")

    # Start polar alignment
    result = await client.start_polar_align()
    assert result is True

    # Pause
    import asyncio
    await asyncio.sleep(2)
    result = await client.pause_polar_align()
    assert result is True

    # Stop
    result = await client.stop_polar_align()
    assert result is True

    await client.disconnect()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_polar_alignment.py -v
```

Expected: FAIL - AttributeError for missing methods

**Step 3: Implement polar alignment methods**

Add to SeestarClient class:

```python
async def start_polar_align(self) -> bool:
    """Start polar alignment process.

    Only works in equatorial mode.

    Returns:
        True if polar alignment started successfully
    """
    # Check mount mode first
    app_state = await self.get_app_state()
    if not app_state.get("equ_mode"):
        logger.error("Polar alignment requires equatorial mode")
        return False

    response = await self._send_command("iscope_start_polar_align", {})

    if response.get("code") == 0:
        logger.info("Polar alignment started")
        return True
    else:
        logger.error(f"Failed to start polar alignment: {response}")
        return False

async def stop_polar_align(self) -> bool:
    """Stop polar alignment process.

    Returns:
        True if polar alignment stopped successfully
    """
    response = await self._send_command("iscope_stop_polar_align", {})

    if response.get("code") == 0:
        logger.info("Polar alignment stopped")
        return True
    else:
        logger.error(f"Failed to stop polar alignment: {response}")
        return False

async def pause_polar_align(self) -> bool:
    """Pause polar alignment process.

    Returns:
        True if polar alignment paused successfully
    """
    response = await self._send_command("iscope_pause_polar_align", {})

    if response.get("code") == 0:
        logger.info("Polar alignment paused")
        return True
    else:
        logger.error(f"Failed to pause polar alignment: {response}")
        return False
```

**Step 4: Run tests to verify they pass**

```bash
pytest tests/test_polar_alignment.py -v
```

Expected: PASS (or SKIP if not in equatorial mode)

**Step 5: Commit**

```bash
git add backend/app/clients/seestar_client.py tests/test_polar_alignment.py
git commit -m "feat(backend): add polar alignment commands"
```

### Task 4.2: Backend - Polar Alignment API Endpoints

**Files:**
- Create: `backend/app/routers/polar_align.py`
- Modify: `backend/app/main.py`

**Step 1: Create polar alignment router**

```python
# backend/app/routers/polar_align.py
from fastapi import APIRouter, HTTPException
import logging

from app.clients.seestar_client import get_seestar_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/telescope/polar-align", tags=["polar-align"])


@router.post("/start")
async def start_polar_alignment():
    """Start polar alignment process."""
    client = get_seestar_client()

    if not client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    # Check mount mode
    app_state = await client.get_app_state()
    if not app_state.get("equ_mode"):
        raise HTTPException(
            status_code=400,
            detail="Polar alignment only works in equatorial mode"
        )

    success = await client.start_polar_align()

    if not success:
        raise HTTPException(status_code=500, detail="Failed to start polar alignment")

    return {"status": "polar_alignment_started"}


@router.post("/stop")
async def stop_polar_alignment():
    """Stop polar alignment process."""
    client = get_seestar_client()

    if not client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    success = await client.stop_polar_align()

    if not success:
        raise HTTPException(status_code=500, detail="Failed to stop polar alignment")

    return {"status": "polar_alignment_stopped"}


@router.post("/pause")
async def pause_polar_alignment():
    """Pause polar alignment process."""
    client = get_seestar_client()

    if not client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    success = await client.pause_polar_align()

    if not success:
        raise HTTPException(status_code=500, detail="Failed to pause polar alignment")

    return {"status": "polar_alignment_paused"}
```

**Step 2: Register router in main.py**

```python
# backend/app/main.py
from app.routers import polar_align

# Add to router includes
app.include_router(polar_align.router)
```

**Step 3: Test endpoints**

```bash
curl -X POST http://localhost:9247/api/telescope/polar-align/start
curl -X POST http://localhost:9247/api/telescope/polar-align/pause
curl -X POST http://localhost:9247/api/telescope/polar-align/stop
```

Expected: Success responses or appropriate error if not in equatorial mode

**Step 4: Commit**

```bash
git add backend/app/routers/polar_align.py backend/app/main.py
git commit -m "feat(api): add polar alignment endpoints"
```

### Task 4.3: Frontend - Polar Alignment Panel

**Files:**
- Create: `frontend/vue-app/src/components/execution/PolarAlignmentPanel.vue`
- Modify: `frontend/vue-app/src/views/ExecutionView.vue`
- Modify: `frontend/vue-app/src/stores/execution.js`

**Step 1: Add polar alignment state to store**

```javascript
// In execution.js state():
polarAlignment: {
  active: false,
  paused: false,
  progress: 0,
  status: 'idle' // idle, running, paused, completed
},
```

**Step 2: Add polar alignment actions to store**

```javascript
// In execution.js actions:
async startPolarAlignment() {
  if (!this.connected) {
    this.error = 'Telescope not connected'
    return
  }

  try {
    await axios.post('/api/telescope/polar-align/start')
    this.polarAlignment.active = true
    this.polarAlignment.paused = false
    this.polarAlignment.status = 'running'
    this.addMessage('Polar alignment started')
  } catch (err) {
    this.error = err.response?.data?.detail || 'Failed to start polar alignment'
    console.error('Polar alignment error:', err)
  }
},

async pausePolarAlignment() {
  try {
    await axios.post('/api/telescope/polar-align/pause')
    this.polarAlignment.paused = true
    this.polarAlignment.status = 'paused'
    this.addMessage('Polar alignment paused')
  } catch (err) {
    this.error = 'Failed to pause polar alignment: ' + err.message
    console.error('Pause polar alignment error:', err)
  }
},

async stopPolarAlignment() {
  try {
    await axios.post('/api/telescope/polar-align/stop')
    this.polarAlignment.active = false
    this.polarAlignment.paused = false
    this.polarAlignment.status = 'idle'
    this.addMessage('Polar alignment stopped')
  } catch (err) {
    this.error = 'Failed to stop polar alignment: ' + err.message
    console.error('Stop polar alignment error:', err)
  }
},
```

**Step 3: Create PolarAlignmentPanel component**

```vue
<!-- frontend/vue-app/src/components/execution/PolarAlignmentPanel.vue -->
<template>
  <div class="space-y-4">
    <!-- Mount Mode Warning -->
    <div
      v-if="executionStore.hardware.mountMode !== 'equatorial'"
      class="bg-yellow-900/30 border border-yellow-600 rounded-lg p-3 text-sm text-yellow-200"
    >
      <p>⚠️ Polar alignment requires equatorial mode</p>
      <p class="text-xs mt-1 text-yellow-300">
        Current mode: {{ executionStore.hardware.mountMode || 'Unknown' }}
      </p>
    </div>

    <!-- Status -->
    <div v-if="executionStore.polarAlignment.active" class="space-y-2">
      <div class="flex items-center justify-between text-sm">
        <span class="text-gray-400">Status</span>
        <span
          :class="[
            'font-medium',
            executionStore.polarAlignment.paused ? 'text-yellow-400' : 'text-blue-400'
          ]"
        >
          {{ executionStore.polarAlignment.paused ? 'Paused' : 'Running' }}
        </span>
      </div>

      <!-- Progress indicator (if available from telescope state) -->
      <div class="w-full bg-gray-900 rounded-full h-2">
        <div
          class="bg-blue-600 h-2 rounded-full transition-all"
          :style="{ width: executionStore.polarAlignment.progress + '%' }"
        ></div>
      </div>
    </div>

    <!-- Controls -->
    <div class="space-y-2">
      <button
        v-if="!executionStore.polarAlignment.active"
        @click="executionStore.startPolarAlignment()"
        :disabled="!executionStore.connected || executionStore.hardware.mountMode !== 'equatorial'"
        class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Start Polar Alignment
      </button>

      <template v-else>
        <button
          v-if="!executionStore.polarAlignment.paused"
          @click="executionStore.pausePolarAlignment()"
          class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-yellow-600 hover:bg-yellow-700 text-white"
        >
          Pause
        </button>
        <button
          v-else
          @click="executionStore.startPolarAlignment()"
          class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white"
        >
          Resume
        </button>

        <button
          @click="executionStore.stopPolarAlignment()"
          class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-gray-700 hover:bg-gray-600 text-gray-200"
        >
          Stop Alignment
        </button>
      </template>
    </div>

    <!-- Instructions -->
    <div class="text-xs text-gray-500 space-y-1">
      <p>1. Center Polaris in the view</p>
      <p>2. Follow on-screen instructions</p>
      <p>3. Adjust mount until alignment complete</p>
    </div>
  </div>
</template>

<script setup>
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()
</script>
```

**Step 4: Add panel to ExecutionView**

In ExecutionView.vue, add PolarAlignmentPanel to the left column (after Imaging Area):

```vue
<!-- Polar Alignment Area -->
<div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
  <h2 class="text-lg font-semibold text-gray-100 mb-4">Polar Alignment</h2>
  <PolarAlignmentPanel />
</div>
```

Import the component:

```javascript
import PolarAlignmentPanel from '@/components/execution/PolarAlignmentPanel.vue'
```

**Step 5: Test in browser**

Manual test:
1. Connect to telescope in equatorial mode
2. Navigate to Execution view
3. Find Polar Alignment panel
4. Click "Start Polar Alignment"
5. Click "Pause" and "Resume"
6. Click "Stop Alignment"
7. Test with Alt/Az mode (should show warning, disable button)

**Step 6: Commit**

```bash
git add frontend/vue-app/src/components/execution/PolarAlignmentPanel.vue frontend/vue-app/src/views/ExecutionView.vue frontend/vue-app/src/stores/execution.js
git commit -m "feat(ui): add polar alignment panel with mount mode check"
```

---

## Phase 5: Object Tracking (Tier 1)

### Task 5.1: Backend - Object Tracking Commands

**Files:**
- Modify: `backend/app/clients/seestar_client.py`

**Step 1: Write failing test**

```python
# tests/test_object_tracking.py
import pytest
from app.clients.seestar_client import SeestarClient

@pytest.mark.asyncio
async def test_object_tracking():
    """Test object tracking for satellites."""
    client = SeestarClient()
    await client.connect("192.168.2.47")

    # Start tracking a satellite
    result = await client.start_track_object(
        object_type="satellite",
        object_id="ISS"
    )
    assert result is True

    # Wait briefly
    import asyncio
    await asyncio.sleep(2)

    # Stop tracking
    result = await client.stop_track_object()
    assert result is True

    await client.disconnect()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_object_tracking.py -v
```

Expected: FAIL - AttributeError

**Step 3: Implement object tracking methods**

```python
async def start_track_object(
    self,
    object_type: str,
    object_id: str
) -> bool:
    """Start tracking an object (satellite, comet, asteroid).

    Args:
        object_type: Type of object ('satellite', 'comet', 'asteroid')
        object_id: Identifier for the object (name or catalog number)

    Returns:
        True if tracking started successfully
    """
    params = {
        "type": object_type,
        "id": object_id
    }

    response = await self._send_command("start_track_object", params)

    if response.get("code") == 0:
        logger.info(f"Object tracking started: {object_type} {object_id}")
        return True
    else:
        logger.error(f"Failed to start object tracking: {response}")
        return False

async def stop_track_object(self) -> bool:
    """Stop object tracking.

    Returns:
        True if tracking stopped successfully
    """
    response = await self._send_command("stop_track_object", {})

    if response.get("code") == 0:
        logger.info("Object tracking stopped")
        return True
    else:
        logger.error(f"Failed to stop object tracking: {response}")
        return False
```

**Step 4: Run tests**

```bash
pytest tests/test_object_tracking.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/clients/seestar_client.py tests/test_object_tracking.py
git commit -m "feat(backend): add object tracking commands"
```

### Task 5.2: Backend - Object Tracking API Endpoints

**Files:**
- Modify: `backend/app/routers/telescope.py`

**Step 1: Add tracking endpoints**

```python
@router.post("/tracking/start")
async def start_object_tracking(
    object_type: str,
    object_id: str
):
    """Start tracking an object (satellite, comet, asteroid)."""
    client = get_seestar_client()

    if not client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    # Validate object type
    valid_types = ["satellite", "comet", "asteroid"]
    if object_type not in valid_types:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid object type. Must be one of: {valid_types}"
        )

    success = await client.start_track_object(
        object_type=object_type,
        object_id=object_id
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to start object tracking")

    return {
        "status": "tracking_started",
        "object_type": object_type,
        "object_id": object_id
    }


@router.post("/tracking/stop")
async def stop_object_tracking():
    """Stop object tracking."""
    client = get_seestar_client()

    if not client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    success = await client.stop_track_object()

    if not success:
        raise HTTPException(status_code=500, detail="Failed to stop object tracking")

    return {"status": "tracking_stopped"}
```

**Step 2: Test endpoints**

```bash
curl -X POST http://localhost:9247/api/telescope/tracking/start \
  -H "Content-Type: application/json" \
  -d '{"object_type": "satellite", "object_id": "ISS"}'

curl -X POST http://localhost:9247/api/telescope/tracking/stop
```

Expected: Success responses

**Step 3: Commit**

```bash
git add backend/app/routers/telescope.py
git commit -m "feat(api): add object tracking endpoints"
```

### Task 5.3: Frontend - Object Tracking Controls

**Files:**
- Modify: `frontend/vue-app/src/stores/execution.js`
- Modify: `frontend/vue-app/src/components/execution/TelescopePanel.vue`

**Step 1: Add tracking state to store**

```javascript
// In execution.js state():
tracking: {
  active: false,
  objectType: null, // satellite, comet, asteroid
  objectId: null
},
```

**Step 2: Add tracking actions**

```javascript
async startTracking(objectType, objectId) {
  if (!this.connected) {
    this.error = 'Telescope not connected'
    return
  }

  try {
    await axios.post('/api/telescope/tracking/start', {
      object_type: objectType,
      object_id: objectId
    })

    this.tracking.active = true
    this.tracking.objectType = objectType
    this.tracking.objectId = objectId
    this.addMessage(`Tracking ${objectType}: ${objectId}`)
  } catch (err) {
    this.error = err.response?.data?.detail || 'Failed to start tracking'
    console.error('Tracking error:', err)
  }
},

async stopTracking() {
  try {
    await axios.post('/api/telescope/tracking/stop')
    this.tracking.active = false
    this.tracking.objectType = null
    this.tracking.objectId = null
    this.addMessage('Object tracking stopped')
  } catch (err) {
    this.error = 'Failed to stop tracking: ' + err.message
    console.error('Stop tracking error:', err)
  }
},
```

**Step 3: Add tracking section to TelescopePanel**

Add after dew heater controls in TelescopePanel.vue:

```vue
<!-- Object Tracking -->
<div class="mt-6 pt-6 border-t border-gray-700">
  <h3 class="text-sm font-semibold text-gray-300 mb-3">Object Tracking</h3>

  <div v-if="executionStore.tracking.active" class="space-y-2">
    <div class="text-sm text-gray-400">
      Tracking: <span class="text-blue-400">{{ executionStore.tracking.objectId }}</span>
      <span class="text-gray-500 ml-2">({{ executionStore.tracking.objectType }})</span>
    </div>

    <button
      @click="executionStore.stopTracking()"
      class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-gray-700 hover:bg-gray-600 text-gray-200"
    >
      Stop Tracking
    </button>
  </div>

  <div v-else class="space-y-3">
    <div>
      <label class="block text-sm text-gray-400 mb-2">Object Type</label>
      <select
        v-model="trackingType"
        class="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-gray-200"
      >
        <option value="satellite">Satellite</option>
        <option value="comet">Comet</option>
        <option value="asteroid">Asteroid</option>
      </select>
    </div>

    <div>
      <label class="block text-sm text-gray-400 mb-2">Object ID/Name</label>
      <input
        v-model="trackingId"
        type="text"
        placeholder="e.g., ISS, Halley, Ceres"
        class="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-gray-200"
      />
    </div>

    <button
      @click="startTracking"
      :disabled="!executionStore.connected || !trackingId"
      class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
    >
      Start Tracking
    </button>
  </div>
</div>
```

Add to script:

```javascript
const trackingType = ref('satellite')
const trackingId = ref('')

const startTracking = () => {
  executionStore.startTracking(trackingType.value, trackingId.value)
}
```

**Step 4: Test in browser**

Manual test:
1. Connect to telescope
2. Select object type (satellite/comet/asteroid)
3. Enter object ID
4. Click "Start Tracking"
5. Verify tracking indicator shows
6. Click "Stop Tracking"

**Step 5: Commit**

```bash
git add frontend/vue-app/src/stores/execution.js frontend/vue-app/src/components/execution/TelescopePanel.vue
git commit -m "feat(ui): add object tracking controls to telescope panel"
```

---

## Phase 6: Annotation Control (Tier 1)

### Task 6.1: Backend - Annotation Commands

**Files:**
- Modify: `backend/app/clients/seestar_client.py`

**Step 1: Write failing test**

```python
# tests/test_annotation.py
import pytest
from app.clients.seestar_client import SeestarClient

@pytest.mark.asyncio
async def test_annotation_toggle():
    """Test annotation on/off."""
    client = SeestarClient()
    await client.connect("192.168.2.47")

    # Start annotation
    result = await client.start_annotate()
    assert result is True

    # Wait briefly
    import asyncio
    await asyncio.sleep(1)

    # Stop annotation
    result = await client.stop_annotate()
    assert result is True

    await client.disconnect()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/test_annotation.py -v
```

Expected: FAIL - AttributeError

**Step 3: Implement annotation methods**

```python
async def start_annotate(self) -> bool:
    """Enable target annotations on preview/imaging.

    Returns:
        True if annotations enabled successfully
    """
    response = await self._send_command("start_annotate", {})

    if response.get("code") == 0:
        logger.info("Annotations enabled")
        return True
    else:
        logger.error(f"Failed to enable annotations: {response}")
        return False

async def stop_annotate(self) -> bool:
    """Disable target annotations.

    Returns:
        True if annotations disabled successfully
    """
    response = await self._send_command("stop_annotate", {})

    if response.get("code") == 0:
        logger.info("Annotations disabled")
        return True
    else:
        logger.error(f"Failed to disable annotations: {response}")
        return False
```

**Step 4: Run tests**

```bash
pytest tests/test_annotation.py -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/app/clients/seestar_client.py tests/test_annotation.py
git commit -m "feat(backend): add annotation control commands"
```

### Task 6.2: Backend - Annotation API Endpoint

**Files:**
- Modify: `backend/app/routers/telescope.py`

**Step 1: Add annotation endpoint**

```python
@router.post("/annotation/toggle")
async def toggle_annotation(enabled: bool):
    """Toggle target annotations on/off."""
    client = get_seestar_client()

    if not client.connected:
        raise HTTPException(status_code=400, detail="Telescope not connected")

    if enabled:
        success = await client.start_annotate()
    else:
        success = await client.stop_annotate()

    if not success:
        raise HTTPException(status_code=500, detail="Failed to toggle annotations")

    return {
        "status": "annotations_enabled" if enabled else "annotations_disabled",
        "enabled": enabled
    }
```

**Step 2: Test endpoint**

```bash
curl -X POST http://localhost:9247/api/telescope/annotation/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'

curl -X POST http://localhost:9247/api/telescope/annotation/toggle \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

Expected: Success responses

**Step 3: Commit**

```bash
git add backend/app/routers/telescope.py
git commit -m "feat(api): add annotation toggle endpoint"
```

### Task 6.3: Frontend - Annotation Toggle

**Files:**
- Modify: `frontend/vue-app/src/stores/execution.js`
- Modify: `frontend/vue-app/src/views/ExecutionView.vue`

**Step 1: Add annotation state**

```javascript
// In execution.js state():
annotation: {
  enabled: false
},
```

**Step 2: Add annotation action**

```javascript
async toggleAnnotation(enabled) {
  if (!this.connected) {
    this.error = 'Telescope not connected'
    return
  }

  try {
    await axios.post('/api/telescope/annotation/toggle', { enabled })
    this.annotation.enabled = enabled
    this.addMessage(`Annotations ${enabled ? 'enabled' : 'disabled'}`)
  } catch (err) {
    this.error = 'Failed to toggle annotations: ' + err.message
    console.error('Annotation error:', err)
  }
},
```

**Step 3: Add toggle to Live Preview section**

In ExecutionView.vue, add annotation toggle above the preview image:

```vue
<!-- In Live Preview panel -->
<div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
  <div class="flex items-center justify-between mb-4">
    <h2 class="text-lg font-semibold text-gray-100">Live Preview</h2>

    <!-- Annotation Toggle -->
    <label class="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        :checked="executionStore.annotation.enabled"
        @change="executionStore.toggleAnnotation($event.target.checked)"
        :disabled="!executionStore.connected"
        class="w-4 h-4 rounded bg-gray-900 border-gray-700"
      />
      <span class="text-sm text-gray-400">Show Annotations</span>
    </label>
  </div>

  <!-- Preview image (existing) -->
  <div class="relative bg-gray-900 rounded aspect-video flex items-center justify-center">
    <!-- ... existing preview code ... -->
  </div>
</div>
```

**Step 4: Test in browser**

Manual test:
1. Connect to telescope
2. Start imaging
3. Toggle "Show Annotations" checkbox
4. Verify annotations appear/disappear in preview (if visible)

**Step 5: Commit**

```bash
git add frontend/vue-app/src/stores/execution.js frontend/vue-app/src/views/ExecutionView.vue
git commit -m "feat(ui): add annotation toggle to live preview"
```

---

## Phase 7: Visual Polish (UX-F)

### Task 7.1: Add Loading States

**Files:**
- Modify: `frontend/vue-app/src/stores/execution.js`
- Modify: All panel components

**Step 1: Add loading state to store**

Already exists as `loading: false` in state. Ensure all async actions set it:

```javascript
// Pattern for all async actions:
async someAction() {
  this.loading = true
  this.error = null

  try {
    // ... action logic ...
  } catch (err) {
    this.error = 'Error message'
  } finally {
    this.loading = false
  }
}
```

**Step 2: Add loading spinners to buttons**

Update button pattern in all panels:

```vue
<button
  @click="doAction"
  :disabled="executionStore.loading || !executionStore.connected"
  class="..."
>
  <span v-if="executionStore.loading" class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></span>
  Button Text
</button>
```

**Step 3: Test loading states**

Manual test all buttons to verify spinners appear during API calls

**Step 4: Commit**

```bash
git add frontend/vue-app/src/stores/execution.js frontend/vue-app/src/components/execution/*.vue
git commit -m "feat(ui): add loading spinners to all action buttons"
```

### Task 7.2: Improve Status Indicators

**Files:**
- Create: `frontend/vue-app/src/components/StatusBadge.vue`
- Modify: Panel components to use StatusBadge

**Step 1: Create reusable StatusBadge component**

```vue
<!-- frontend/vue-app/src/components/StatusBadge.vue -->
<template>
  <span
    :class="[
      'inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium',
      colorClasses
    ]"
  >
    <span
      v-if="showDot"
      :class="['w-1.5 h-1.5 rounded-full', dotClasses]"
    ></span>
    <slot>{{ label }}</slot>
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true,
    validator: (value) => ['idle', 'active', 'error', 'warning', 'success', 'parked'].includes(value)
  },
  label: {
    type: String,
    default: ''
  },
  showDot: {
    type: Boolean,
    default: true
  }
})

const colorClasses = computed(() => {
  const colors = {
    idle: 'bg-gray-700 text-gray-300',
    active: 'bg-green-900/30 text-green-400 border border-green-600',
    error: 'bg-red-900/30 text-red-400 border border-red-600',
    warning: 'bg-yellow-900/30 text-yellow-400 border border-yellow-600',
    success: 'bg-blue-900/30 text-blue-400 border border-blue-600',
    parked: 'bg-purple-900/30 text-purple-400 border border-purple-600'
  }
  return colors[props.status] || colors.idle
})

const dotClasses = computed(() => {
  const dots = {
    idle: 'bg-gray-500',
    active: 'bg-green-500 animate-pulse',
    error: 'bg-red-500',
    warning: 'bg-yellow-500',
    success: 'bg-blue-500',
    parked: 'bg-purple-500'
  }
  return dots[props.status] || dots.idle
})
</script>
```

**Step 2: Use StatusBadge in panels**

Example in ExecutionView header:

```vue
<template>
  <StatusBadge
    :status="trackingStatus"
    :label="executionStore.hardware.trackingStatus"
  />
</template>

<script setup>
import StatusBadge from '@/components/StatusBadge.vue'

const trackingStatus = computed(() => {
  const status = executionStore.hardware.trackingStatus
  if (status === 'Active') return 'active'
  if (status === 'Parked') return 'parked'
  return 'idle'
})
</script>
```

**Step 3: Update all status displays to use StatusBadge**

Replace text-based status indicators with StatusBadge in:
- TelescopePanel (tracking status, dew heater)
- ImagingPanel (imaging active, recording active)
- PolarAlignmentPanel (alignment status)
- Header status indicators

**Step 4: Test visual appearance**

Verify all status badges look consistent and use proper colors

**Step 5: Commit**

```bash
git add frontend/vue-app/src/components/StatusBadge.vue frontend/vue-app/src/components/execution/*.vue frontend/vue-app/src/views/ExecutionView.vue
git commit -m "feat(ui): add StatusBadge component for consistent status indicators"
```

### Task 7.3: Add Toast Notifications

**Files:**
- Add package: `vue-toastification`
- Modify: `frontend/vue-app/src/main.js`
- Modify: `frontend/vue-app/src/stores/execution.js`

**Step 1: Install toast library**

```bash
cd frontend/vue-app
npm install vue-toastification@next
```

**Step 2: Configure in main.js**

```javascript
// frontend/vue-app/src/main.js
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'

// ... other imports ...

app.use(Toast, {
  position: 'top-right',
  timeout: 3000,
  closeOnClick: true,
  pauseOnHover: true,
  draggable: true,
  draggablePercent: 0.6,
  showCloseButtonOnHover: false,
  hideProgressBar: false,
  closeButton: 'button',
  icon: true,
  rtl: false,
  transition: 'Vue-Toastification__fade',
  maxToasts: 5,
  newestOnTop: true
})
```

**Step 3: Add toast methods to execution store**

```javascript
// In execution.js, import at top:
import { useToast } from 'vue-toastification'

// In store definition, before state():
const toast = useToast()

// Add helper methods:
showSuccessToast(message) {
  toast.success(message)
},

showErrorToast(message) {
  toast.error(message)
},

showWarningToast(message) {
  toast.warning(message)
},

showInfoToast(message) {
  toast.info(message)
},
```

**Step 4: Update all actions to use toasts**

Replace or supplement `this.addMessage()` calls with toasts:

```javascript
// Success example:
this.showSuccessToast('Telescope connected successfully')

// Error example:
this.showErrorToast('Failed to connect: ' + err.message)
```

**Step 5: Test toasts**

Trigger various actions and verify toasts appear with correct styling

**Step 6: Commit**

```bash
git add frontend/vue-app/package.json frontend/vue-app/package-lock.json frontend/vue-app/src/main.js frontend/vue-app/src/stores/execution.js
git commit -m "feat(ui): add toast notifications for user feedback"
```

### Task 7.4: Add Confirmation Dialogs

**Files:**
- Create: `frontend/vue-app/src/components/ConfirmDialog.vue`
- Modify: Components with destructive actions

**Step 1: Create ConfirmDialog component**

```vue
<!-- frontend/vue-app/src/components/ConfirmDialog.vue -->
<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      @click.self="cancel"
    >
      <div class="bg-gray-800 rounded-lg shadow-xl max-w-md w-full border border-gray-700">
        <div class="p-6">
          <h3 class="text-lg font-semibold text-gray-100 mb-2">
            {{ title }}
          </h3>
          <p class="text-gray-400 text-sm mb-6">
            {{ message }}
          </p>

          <div class="flex gap-3 justify-end">
            <button
              @click="cancel"
              class="px-4 py-2 rounded-lg font-medium transition-colors bg-gray-700 hover:bg-gray-600 text-gray-200"
            >
              {{ cancelText }}
            </button>
            <button
              @click="confirm"
              :class="[
                'px-4 py-2 rounded-lg font-medium transition-colors',
                danger
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              ]"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
const props = defineProps({
  show: Boolean,
  title: {
    type: String,
    default: 'Confirm Action'
  },
  message: {
    type: String,
    required: true
  },
  confirmText: {
    type: String,
    default: 'Confirm'
  },
  cancelText: {
    type: String,
    default: 'Cancel'
  },
  danger: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['confirm', 'cancel'])

const confirm = () => {
  emit('confirm')
}

const cancel = () => {
  emit('cancel')
}
</script>
```

**Step 2: Add confirmation to destructive actions**

Example in PlanExecutionPanel for stopping plan:

```vue
<template>
  <!-- Stop Plan button -->
  <button @click="showStopConfirm = true">
    Stop Plan
  </button>

  <!-- Confirmation dialog -->
  <ConfirmDialog
    :show="showStopConfirm"
    title="Stop Plan Execution?"
    message="This will stop the current plan execution. Progress will be lost."
    confirm-text="Stop Plan"
    cancel-text="Keep Running"
    danger
    @confirm="stopPlan"
    @cancel="showStopConfirm = false"
  />
</template>

<script setup>
import { ref } from 'vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const showStopConfirm = ref(false)

const stopPlan = () => {
  executionStore.stopPlan()
  showStopConfirm.value = false
}
</script>
```

**Step 3: Add confirmations to these actions**

- Stop plan execution
- Disconnect telescope
- Stop imaging (if frames captured > 0)
- Stop polar alignment (if in progress)

**Step 4: Test confirmations**

Verify dialogs appear and actions only execute on confirmation

**Step 5: Commit**

```bash
git add frontend/vue-app/src/components/ConfirmDialog.vue frontend/vue-app/src/components/execution/*.vue
git commit -m "feat(ui): add confirmation dialogs for destructive actions"
```

### Task 7.5: Polish Animations and Transitions

**Files:**
- Modify: `frontend/vue-app/src/views/ExecutionView.vue`
- Modify: All panel components

**Step 1: Add smooth transitions to conditional rendering**

Wrap conditional content in transitions:

```vue
<Transition name="fade">
  <div v-if="executionStore.imaging.active">
    <!-- Content -->
  </div>
</Transition>
```

Add CSS for fade transition in App.vue or a global CSS file:

```css
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
```

**Step 2: Add hover effects to interactive elements**

Update button classes to include smooth hover transitions (already mostly done via Tailwind `transition-colors`)

**Step 3: Add focus states for accessibility**

Add focus-visible styles:

```vue
<button
  class="... focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800"
>
```

**Step 4: Test animations**

Verify:
- Smooth transitions when showing/hiding panels
- Hover effects on buttons
- Focus rings visible when navigating with keyboard

**Step 5: Commit**

```bash
git add frontend/vue-app/src/views/ExecutionView.vue frontend/vue-app/src/components/execution/*.vue frontend/vue-app/src/App.vue
git commit -m "feat(ui): add smooth transitions and accessibility improvements"
```

---

## Final Integration Testing

### Task 8.1: End-to-End Testing

**Step 1: Test all Tier 1 features with real telescope**

Manual test checklist:

**Video/Streaming + Preview:**
- [ ] Connect to telescope
- [ ] Start deep sky imaging
- [ ] Verify preview updates every 1-2 seconds
- [ ] Start recording
- [ ] Stop recording
- [ ] Verify preview shows "stale" indicator after 10 seconds of no updates

**Planetary Imaging:**
- [ ] Switch to Planetary mode
- [ ] Scan for planets
- [ ] Select a planet
- [ ] Start planetary imaging
- [ ] Verify preview works
- [ ] Stop planetary imaging

**Polar Alignment:**
- [ ] Verify mount mode shows in UI
- [ ] Start polar alignment
- [ ] Pause alignment
- [ ] Resume alignment
- [ ] Stop alignment
- [ ] Test with Alt/Az mode (should show warning)

**Object Tracking:**
- [ ] Select satellite
- [ ] Enter object ID (e.g., "ISS")
- [ ] Start tracking
- [ ] Verify tracking indicator
- [ ] Stop tracking
- [ ] Test with comet and asteroid

**Annotation Control:**
- [ ] Enable annotations
- [ ] Verify checkbox state
- [ ] Disable annotations
- [ ] Verify preview updates

**Step 2: Test error cases**

- [ ] Disconnect telescope mid-operation
- [ ] Start imaging while already imaging
- [ ] Start polar alignment in Alt/Az mode
- [ ] Network timeout scenarios

**Step 3: Test UX polish**

- [ ] Verify loading spinners appear on all buttons
- [ ] Verify toast notifications for success/error
- [ ] Verify confirmation dialogs on destructive actions
- [ ] Verify status badges use correct colors
- [ ] Test keyboard navigation (tab, enter, space)
- [ ] Verify responsive layout on different screen sizes

**Step 4: Document any issues**

Create GitHub issues for any bugs found during testing

**Step 5: Final commit**

```bash
git add -A
git commit -m "test: complete end-to-end testing of all Tier 1 features"
```

---

## Completion Checklist

- [ ] Phase 1: Layout Foundation - 4-area responsive layout
- [ ] Phase 2: Video/Streaming + Live Preview - File-based preview polling, recording controls
- [ ] Phase 3: Planetary Imaging - Mode toggle, planet scanning, planetary stacking
- [ ] Phase 4: Polar Alignment - Start/pause/stop controls, mount mode check
- [ ] Phase 5: Object Tracking - Satellite/comet/asteroid tracking
- [ ] Phase 6: Annotation Control - Toggle annotations on preview
- [ ] Phase 7: Visual Polish - Loading states, status badges, toasts, confirmations, transitions
- [ ] All backend tests passing
- [ ] All frontend components tested
- [ ] End-to-end testing complete
- [ ] No regressions in existing features
- [ ] Documentation updated

---

## Notes

- This plan assumes working on the current branch, not a worktree (per CLAUDE.md instructions)
- Backend WebSocket command names may need adjustment based on actual telescope API
- File paths for preview frames may need discovery via telescope filesystem exploration
- Some features may require specific telescope firmware versions
- Mount mode detection (`equ_mode` field) should be added to position polling
- Progress indicators for polar alignment may require additional state polling
- Preview frame polling interval (1.5s) can be tuned for performance vs. responsiveness
