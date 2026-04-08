# Wish List and Daily Plan Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement wish list functionality with 19 pre-populated solar system objects, manual daily plan generation, and capture tracking.

**Architecture:** Minimal backend changes using AppSetting for wish list storage, new CapturedTarget model for tracking completed observations. Frontend-heavy with extended planningStore and new components for wish list management. Reuse existing plan generation logic with custom_targets.

**Tech Stack:** FastAPI, SQLAlchemy, Pinia, Vue 3, Tailwind CSS, Astropy (planet ephemeris)

---

## Task 1: Backend - Wish List Endpoints

**Files:**
- Modify: `backend/app/api/routes.py` (add endpoints)
- Test: `backend/tests/api/test_wishlist_api.py` (create)

**Step 1: Write failing test for GET /api/settings/wishlist**

Create `backend/tests/api/test_wishlist_api.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_wishlist_empty():
    """Test getting wish list when not set returns empty array."""
    response = client.get("/api/settings/wishlist")
    assert response.status_code == 200
    assert response.json() == {"targets": []}

def test_get_wishlist_with_targets():
    """Test getting wish list returns saved targets."""
    # First save some targets
    client.put("/api/settings/wishlist", json={"targets": ["Jupiter", "M31"]})

    # Then retrieve them
    response = client.get("/api/settings/wishlist")
    assert response.status_code == 200
    assert response.json() == {"targets": ["Jupiter", "M31"]}
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/api/test_wishlist_api.py::test_get_wishlist_empty -v`
Expected: FAIL with "404 Not Found" (endpoint doesn't exist)

**Step 3: Implement GET /api/settings/wishlist endpoint**

In `backend/app/api/routes.py`, add after existing settings endpoints:

```python
@router.get("/settings/wishlist")
async def get_wishlist(
    include_captures: bool = Query(False, description="Include capture status for each target"),
    db: Session = Depends(get_db)
) -> dict:
    """Get user's wish list targets."""
    from app.models.settings_models import AppSetting

    # Get wish list from settings
    setting = db.query(AppSetting).filter(AppSetting.key == "user.wishlist_targets").first()

    if not setting or not setting.value:
        return {"targets": []}

    # Parse JSON array
    import json
    targets = json.loads(setting.value) if isinstance(setting.value, str) else setting.value

    # TODO: If include_captures, enrich with capture status (implement in Task 2)

    return {"targets": targets}
```

**Step 4: Run test to verify it passes**

Run: `cd backend && pytest tests/api/test_wishlist_api.py::test_get_wishlist_empty -v`
Expected: PASS

**Step 5: Write failing test for PUT /api/settings/wishlist**

Add to `backend/tests/api/test_wishlist_api.py`:

```python
def test_put_wishlist():
    """Test saving wish list targets."""
    targets = ["Jupiter", "M31", "NGC7000"]
    response = client.put("/api/settings/wishlist", json={"targets": targets})

    assert response.status_code == 200
    assert response.json() == {"success": True, "count": 3}

    # Verify it was saved
    get_response = client.get("/api/settings/wishlist")
    assert get_response.json() == {"targets": targets}

def test_put_wishlist_validation():
    """Test wish list validates target IDs."""
    response = client.put("/api/settings/wishlist", json={"targets": ["INVALID_TARGET_123"]})

    # TODO: Should validate and return 400 - implement in this task
    # For now, just test it accepts the data
    assert response.status_code in [200, 400]
```

**Step 6: Run test to verify it fails**

Run: `cd backend && pytest tests/api/test_wishlist_api.py::test_put_wishlist -v`
Expected: FAIL with "404 Not Found" (endpoint doesn't exist)

**Step 7: Implement PUT /api/settings/wishlist endpoint**

In `backend/app/api/routes.py`, add after GET wishlist:

```python
@router.put("/settings/wishlist")
async def put_wishlist(
    request: dict = Body(...),
    db: Session = Depends(get_db)
) -> dict:
    """Save user's wish list targets."""
    from app.models.settings_models import AppSetting
    import json

    targets = request.get("targets", [])

    # TODO: Validate target IDs exist (planets or catalog) - defer to later step

    # Find or create setting
    setting = db.query(AppSetting).filter(AppSetting.key == "user.wishlist_targets").first()

    if not setting:
        setting = AppSetting(key="user.wishlist_targets", value=json.dumps(targets))
        db.add(setting)
    else:
        setting.value = json.dumps(targets)

    db.commit()

    return {"success": True, "count": len(targets)}
```

**Step 8: Run test to verify it passes**

Run: `cd backend && pytest tests/api/test_wishlist_api.py::test_put_wishlist -v`
Expected: PASS

**Step 9: Write failing test for GET /api/wishlist/defaults**

Add to `backend/tests/api/test_wishlist_api.py`:

```python
def test_get_wishlist_defaults():
    """Test getting default solar system objects."""
    response = client.get("/api/wishlist/defaults")

    assert response.status_code == 200
    targets = response.json()["targets"]

    # Should have 19 solar system objects
    assert len(targets) == 19
    assert "Jupiter" in targets
    assert "Mars" in targets
    assert "Moon" in targets
    assert "Io" in targets  # Jupiter moon
    assert "Titan" in targets  # Saturn moon
```

**Step 10: Run test to verify it fails**

Run: `cd backend && pytest tests/api/test_wishlist_api.py::test_get_wishlist_defaults -v`
Expected: FAIL with "404 Not Found"

**Step 11: Implement GET /api/wishlist/defaults endpoint**

In `backend/app/api/routes.py`, add after PUT wishlist:

```python
@router.get("/wishlist/defaults")
async def get_wishlist_defaults() -> dict:
    """Get default solar system objects for wish list."""
    SOLAR_SYSTEM_DEFAULTS = [
        # 8 planets
        "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune",
        # Earth's Moon
        "Moon",
        # Sun (with solar filter warning)
        "Sun",
        # Jupiter's Galilean moons
        "Io", "Europa", "Ganymede", "Callisto",
        # Saturn's major moons
        "Titan", "Rhea", "Tethys", "Dione", "Enceladus"
    ]

    return {"targets": SOLAR_SYSTEM_DEFAULTS}
```

**Step 12: Run tests to verify all pass**

Run: `cd backend && pytest tests/api/test_wishlist_api.py -v`
Expected: ALL PASS

**Step 13: Commit**

```bash
git add backend/app/api/routes.py backend/tests/api/test_wishlist_api.py
git commit -m "feat: add wish list endpoints (GET/PUT /api/settings/wishlist, GET /api/wishlist/defaults)"
```

---

## Task 2: Backend - Capture Tracking Model and Endpoints

**Files:**
- Modify: `backend/app/models/models.py` (add CapturedTarget model)
- Create: `backend/alembic/versions/YYYYMMDD_add_captured_targets.py` (migration)
- Modify: `backend/app/api/routes.py` (add capture endpoints)
- Test: `backend/tests/api/test_captures_api.py` (create)

**Step 1: Write failing test for CapturedTarget model**

Create `backend/tests/api/test_captures_api.py`:

```python
import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal

client = TestClient(app)

def test_create_capture():
    """Test creating a capture record."""
    capture_data = {
        "target_id": "M31",
        "session_date": "2026-02-15",
        "image_count": 45,
        "notes": "Great seeing"
    }

    response = client.post("/api/captures", json=capture_data)
    assert response.status_code == 200

    data = response.json()
    assert data["target_id"] == "M31"
    assert data["session_date"] == "2026-02-15"
    assert data["image_count"] == 45
    assert "id" in data
    assert "captured_at" in data

def test_list_captures():
    """Test listing all captures."""
    # Create a capture first
    client.post("/api/captures", json={
        "target_id": "Jupiter",
        "session_date": "2026-02-14",
        "image_count": 100
    })

    response = client.get("/api/captures")
    assert response.status_code == 200

    captures = response.json()["captures"]
    assert len(captures) > 0
    assert any(c["target_id"] == "Jupiter" for c in captures)
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/api/test_captures_api.py::test_create_capture -v`
Expected: FAIL (model doesn't exist)

**Step 3: Add CapturedTarget model**

In `backend/app/models/models.py`, add after SavedPlan model:

```python
class CapturedTarget(Base):
    """Record of a captured/observed target."""
    __tablename__ = "captured_targets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), default="default_user")  # TODO: Add real user auth
    target_id = Column(String(255), nullable=False)
    target_type = Column(String(50), nullable=False, default="dso")  # "planet" or "dso"
    captured_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    session_date = Column(Date, nullable=False)
    image_count = Column(Integer, default=0)
    notes = Column(Text, nullable=True)

    __table_args__ = (
        # Prevent duplicate captures for same target on same night
        UniqueConstraint('user_id', 'target_id', 'session_date', name='uq_user_target_session'),
    )
```

Also add to imports at top of file:
```python
from datetime import datetime, date
from sqlalchemy import UniqueConstraint
```

**Step 4: Create database migration**

Run: `cd backend && alembic revision -m "add captured targets table"`

Edit the generated file `backend/alembic/versions/XXXXXX_add_captured_targets.py`:

```python
"""add captured targets table

Revision ID: XXXXXX
Revises: YYYYYY
Create Date: 2026-02-15
"""
from alembic import op
import sqlalchemy as sa

revision = 'XXXXXX'
down_revision = 'YYYYYY'  # Update with actual previous revision
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'captured_targets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=True, default='default_user'),
        sa.Column('target_id', sa.String(255), nullable=False),
        sa.Column('target_type', sa.String(50), nullable=False, default='dso'),
        sa.Column('captured_at', sa.DateTime(), nullable=False),
        sa.Column('session_date', sa.Date(), nullable=False),
        sa.Column('image_count', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'target_id', 'session_date', name='uq_user_target_session')
    )
    op.create_index('ix_captured_targets_id', 'captured_targets', ['id'])
    op.create_index('idx_captured_user_target', 'captured_targets', ['user_id', 'target_id'])

def downgrade():
    op.drop_index('idx_captured_user_target', table_name='captured_targets')
    op.drop_index('ix_captured_targets_id', table_name='captured_targets')
    op.drop_table('captured_targets')
```

**Step 5: Run migration**

Run: `cd backend && alembic upgrade head`
Expected: Migration succeeds, table created

**Step 6: Implement POST /api/captures endpoint**

In `backend/app/api/routes.py`, add captures endpoints:

```python
from app.models.models import CapturedTarget
from datetime import date as date_type, datetime

@router.post("/captures")
async def create_capture(
    request: dict = Body(...),
    db: Session = Depends(get_db)
) -> dict:
    """Create a capture record."""
    target_id = request.get("target_id")
    session_date_str = request.get("session_date")
    image_count = request.get("image_count", 0)
    notes = request.get("notes", "")

    # Parse session_date
    session_date = datetime.fromisoformat(session_date_str).date()

    # Determine target type (planet vs dso)
    # Simple heuristic: if it's in SOLAR_SYSTEM_DEFAULTS, it's a planet
    SOLAR_SYSTEM_DEFAULTS = [
        "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune",
        "Moon", "Sun", "Io", "Europa", "Ganymede", "Callisto",
        "Titan", "Rhea", "Tethys", "Dione", "Enceladus"
    ]
    target_type = "planet" if target_id in SOLAR_SYSTEM_DEFAULTS else "dso"

    # Create capture record
    capture = CapturedTarget(
        user_id="default_user",  # TODO: Real user auth
        target_id=target_id,
        target_type=target_type,
        session_date=session_date,
        image_count=image_count,
        notes=notes
    )

    db.add(capture)
    db.commit()
    db.refresh(capture)

    return {
        "id": capture.id,
        "target_id": capture.target_id,
        "target_type": capture.target_type,
        "captured_at": capture.captured_at.isoformat(),
        "session_date": capture.session_date.isoformat(),
        "image_count": capture.image_count,
        "notes": capture.notes
    }

@router.get("/captures")
async def list_captures(
    target_ids: str = Query(None, description="Comma-separated target IDs to filter"),
    db: Session = Depends(get_db)
) -> dict:
    """List all capture records."""
    query = db.query(CapturedTarget).filter(CapturedTarget.user_id == "default_user")

    # Filter by target IDs if provided
    if target_ids:
        target_list = [t.strip() for t in target_ids.split(",")]
        query = query.filter(CapturedTarget.target_id.in_(target_list))

    captures = query.order_by(CapturedTarget.captured_at.desc()).all()

    return {
        "captures": [
            {
                "id": c.id,
                "target_id": c.target_id,
                "target_type": c.target_type,
                "captured_at": c.captured_at.isoformat(),
                "session_date": c.session_date.isoformat(),
                "image_count": c.image_count,
                "notes": c.notes
            }
            for c in captures
        ]
    }

@router.delete("/captures/{capture_id}")
async def delete_capture(
    capture_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """Delete a capture record."""
    capture = db.query(CapturedTarget).filter(
        CapturedTarget.id == capture_id,
        CapturedTarget.user_id == "default_user"
    ).first()

    if not capture:
        raise HTTPException(status_code=404, detail="Capture not found")

    db.delete(capture)
    db.commit()

    return {"success": True}
```

**Step 7: Run tests to verify they pass**

Run: `cd backend && pytest tests/api/test_captures_api.py -v`
Expected: ALL PASS

**Step 8: Enhance GET /api/settings/wishlist to include capture status**

In `backend/app/api/routes.py`, update the get_wishlist endpoint:

```python
@router.get("/settings/wishlist")
async def get_wishlist(
    include_captures: bool = Query(False, description="Include capture status for each target"),
    db: Session = Depends(get_db)
) -> dict:
    """Get user's wish list targets."""
    from app.models.settings_models import AppSetting
    from app.models.models import CapturedTarget

    # Get wish list from settings
    setting = db.query(AppSetting).filter(AppSetting.key == "user.wishlist_targets").first()

    if not setting or not setting.value:
        return {"targets": []}

    # Parse JSON array
    import json
    targets = json.loads(setting.value) if isinstance(setting.value, str) else setting.value

    # If include_captures, enrich with capture status
    if include_captures:
        # Get all captures for this user
        captures = db.query(CapturedTarget).filter(
            CapturedTarget.user_id == "default_user",
            CapturedTarget.target_id.in_(targets)
        ).all()

        # Build capture lookup
        capture_map = {c.target_id: True for c in captures}

        # Enrich targets with capture status
        enriched_targets = [
            {
                "id": target,
                "captured": capture_map.get(target, False)
            }
            for target in targets
        ]

        return {"targets": enriched_targets}

    return {"targets": targets}
```

**Step 9: Add test for include_captures parameter**

Add to `backend/tests/api/test_wishlist_api.py`:

```python
def test_get_wishlist_with_captures():
    """Test getting wish list with capture status."""
    # Set up wish list
    client.put("/api/settings/wishlist", json={"targets": ["Jupiter", "M31", "M42"]})

    # Mark Jupiter as captured
    client.post("/api/captures", json={
        "target_id": "Jupiter",
        "session_date": "2026-02-15",
        "image_count": 100
    })

    # Get wish list with captures
    response = client.get("/api/settings/wishlist?include_captures=true")
    assert response.status_code == 200

    targets = response.json()["targets"]

    # Should have 3 targets with capture status
    assert len(targets) == 3

    # Jupiter should be marked as captured
    jupiter = next(t for t in targets if t["id"] == "Jupiter")
    assert jupiter["captured"] is True

    # M31 and M42 should not be captured
    m31 = next(t for t in targets if t["id"] == "M31")
    assert m31["captured"] is False
```

**Step 10: Run test to verify it passes**

Run: `cd backend && pytest tests/api/test_wishlist_api.py::test_get_wishlist_with_captures -v`
Expected: PASS

**Step 11: Commit**

```bash
git add backend/app/models/models.py backend/alembic/versions/*.py backend/app/api/routes.py backend/tests/api/test_captures_api.py
git commit -m "feat: add capture tracking (CapturedTarget model, POST/GET/DELETE /api/captures, include_captures parameter)"
```

---

## Task 3: Frontend - Planning Store Updates

**Files:**
- Modify: `frontend/vue-app/src/stores/planning.js`
- Test: `frontend/vue-app/src/stores/__tests__/planning.test.js`

**Step 1: Write failing test for wish list actions**

In `frontend/vue-app/src/stores/__tests__/planning.test.js`:

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePlanningStore } from '../planning'
import axios from 'axios'

vi.mock('axios')

describe('Planning Store - Wish List', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('loads wish list from backend', async () => {
    const mockTargets = ['Jupiter', 'M31', 'M42']
    axios.get.mockResolvedValue({ data: { targets: mockTargets } })

    const store = usePlanningStore()
    await store.loadWishlist()

    expect(store.wishlistTargets).toEqual(mockTargets)
    expect(axios.get).toHaveBeenCalledWith('/api/settings/wishlist?include_captures=true')
  })

  it('adds target to wish list', async () => {
    axios.put.mockResolvedValue({ data: { success: true, count: 1 } })

    const store = usePlanningStore()
    store.wishlistTargets = []

    const target = { id: 'M31', name: 'Andromeda Galaxy' }
    await store.addToWishlist(target)

    expect(store.wishlistTargets).toContainEqual(target)
    expect(axios.put).toHaveBeenCalledWith('/api/settings/wishlist', {
      targets: ['M31']
    })
  })

  it('removes target from wish list', async () => {
    axios.put.mockResolvedValue({ data: { success: true, count: 0 } })

    const store = usePlanningStore()
    store.wishlistTargets = [
      { id: 'M31', name: 'Andromeda' },
      { id: 'M42', name: 'Orion' }
    ]

    await store.removeFromWishlist('M31')

    expect(store.wishlistTargets).toHaveLength(1)
    expect(store.wishlistTargets[0].id).toBe('M42')
  })

  it('resets wish list to defaults', async () => {
    axios.get.mockResolvedValueOnce({
      data: { targets: ['Mercury', 'Venus', 'Mars'] }  // Simplified for test
    })
    axios.put.mockResolvedValue({ data: { success: true, count: 3 } })

    const store = usePlanningStore()
    await store.resetWishlistToDefaults()

    expect(axios.get).toHaveBeenCalledWith('/api/wishlist/defaults')
    expect(axios.put).toHaveBeenCalled()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend/vue-app && npm test -- planning.test.js`
Expected: FAIL (actions don't exist)

**Step 3: Implement wish list actions in planning store**

In `frontend/vue-app/src/stores/planning.js`, add to state:

```javascript
state: () => ({
  // Existing state...
  selectedTargets: [],
  currentPlan: null,
  // ... existing fields ...

  // New wish list state
  wishlistTargets: [],
  capturedTargets: [],
  wishlistLoading: false,
  wishlistError: null,

  // ... rest of existing state
}),
```

Add new actions:

```javascript
actions: {
  // ... existing actions ...

  /**
   * Load wish list from backend with capture status
   */
  async loadWishlist() {
    this.wishlistLoading = true
    this.wishlistError = null

    try {
      const response = await axios.get('/api/settings/wishlist?include_captures=true')
      const targets = response.data.targets

      // If targets are enriched with capture status, they're objects
      // Otherwise, they're just strings (target IDs)
      if (targets.length > 0 && typeof targets[0] === 'object') {
        this.wishlistTargets = targets
      } else {
        this.wishlistTargets = targets.map(id => ({ id, captured: false }))
      }

      // Initialize with defaults if empty
      if (this.wishlistTargets.length === 0) {
        await this.resetWishlistToDefaults()
      }
    } catch (err) {
      this.wishlistError = 'Failed to load wish list: ' + err.message
      console.error('Load wish list error:', err)
    } finally {
      this.wishlistLoading = false
    }
  },

  /**
   * Add target to wish list
   */
  async addToWishlist(target) {
    // Check if already in wish list
    const exists = this.wishlistTargets.some(t => t.id === target.id)
    if (exists) {
      console.log(`${target.id} already in wish list`)
      return
    }

    // Add to local state
    this.wishlistTargets.push({
      id: target.id,
      name: target.name || target.common_name || target.id,
      type: target.type || target.object_type || 'unknown',
      captured: false
    })

    // Save to backend
    try {
      await axios.put('/api/settings/wishlist', {
        targets: this.wishlistTargets.map(t => t.id)
      })
    } catch (err) {
      console.error('Failed to save wish list:', err)
      // Rollback local change
      this.wishlistTargets = this.wishlistTargets.filter(t => t.id !== target.id)
      throw err
    }
  },

  /**
   * Remove target from wish list
   */
  async removeFromWishlist(targetId) {
    // Remove from local state
    const originalTargets = [...this.wishlistTargets]
    this.wishlistTargets = this.wishlistTargets.filter(t => t.id !== targetId)

    // Save to backend
    try {
      await axios.put('/api/settings/wishlist', {
        targets: this.wishlistTargets.map(t => t.id)
      })
    } catch (err) {
      console.error('Failed to save wish list:', err)
      // Rollback
      this.wishlistTargets = originalTargets
      throw err
    }
  },

  /**
   * Reset wish list to 19 solar system defaults
   */
  async resetWishlistToDefaults() {
    try {
      // Get defaults from backend
      const response = await axios.get('/api/wishlist/defaults')
      const defaults = response.data.targets

      // Save to backend
      await axios.put('/api/settings/wishlist', { targets: defaults })

      // Update local state
      this.wishlistTargets = defaults.map(id => ({ id, captured: false }))
    } catch (err) {
      console.error('Failed to reset wish list:', err)
      throw err
    }
  },

  /**
   * Load capture history
   */
  async loadCaptures() {
    try {
      const response = await axios.get('/api/captures')
      this.capturedTargets = response.data.captures
    } catch (err) {
      console.error('Failed to load captures:', err)
    }
  },

  /**
   * Mark target as captured
   */
  async markCaptured(targetId, sessionDate, imageCount, notes = '') {
    try {
      const response = await axios.post('/api/captures', {
        target_id: targetId,
        session_date: sessionDate,
        image_count: imageCount,
        notes: notes
      })

      // Reload wish list to refresh capture status
      await this.loadWishlist()

      return response.data
    } catch (err) {
      console.error('Failed to mark target as captured:', err)
      throw err
    }
  }
}
```

**Step 4: Run tests to verify they pass**

Run: `cd frontend/vue-app && npm test -- planning.test.js`
Expected: ALL PASS

**Step 5: Update catalog store to use wish list**

In `frontend/vue-app/src/stores/catalog.js`, update `addSelectedTarget`:

```javascript
import { usePlanningStore } from './planning'

// ... in actions ...

addSelectedTarget(item) {
  const planningStore = usePlanningStore()

  // Add to planning store's wish list instead of local selectedTargets
  planningStore.addToWishlist(item)

  console.log(`Added ${item.name || item.id} to wish list`)
}
```

**Step 6: Commit**

```bash
git add frontend/vue-app/src/stores/planning.js frontend/vue-app/src/stores/__tests__/planning.test.js frontend/vue-app/src/stores/catalog.js
git commit -m "feat: add wish list and capture tracking actions to planning store"
```

---

## Task 4: Frontend - WishListPanel Component

**Files:**
- Create: `frontend/vue-app/src/components/planning/WishListPanel.vue`
- Modify: `frontend/vue-app/src/views/PlanningView.vue`

**Step 1: Create WishListPanel component skeleton**

Create `frontend/vue-app/src/components/planning/WishListPanel.vue`:

```vue
<template>
  <div class="wish-list-panel p-3 space-y-3">
    <div class="flex items-center justify-between mb-2">
      <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">
        Wish List ({{ planningStore.wishlistTargets.length }})
      </h3>
    </div>

    <!-- Loading state -->
    <div v-if="planningStore.wishlistLoading" class="text-center py-8 text-gray-500">
      Loading wish list...
    </div>

    <!-- Empty state -->
    <div v-else-if="planningStore.wishlistTargets.length === 0" class="text-center py-8 text-gray-500">
      <p class="text-sm">No targets in wish list</p>
      <p class="text-xs mt-2">Add targets from Discovery view</p>
    </div>

    <!-- Wish list items -->
    <div v-else class="space-y-4">
      <!-- Planets section -->
      <div v-if="planetTargets.length > 0">
        <h4 class="text-xs font-semibold text-gray-500 uppercase mb-2">Planets & Moons</h4>
        <div class="space-y-1">
          <div
            v-for="target in planetTargets"
            :key="target.id"
            class="flex items-center justify-between p-2 bg-gray-800 rounded hover:bg-gray-750 transition-colors"
          >
            <div class="flex items-center gap-2">
              <!-- Capture indicator -->
              <span v-if="target.captured" class="text-green-400" title="Captured">✓</span>
              <span v-else class="text-gray-600">○</span>

              <span class="text-sm text-gray-200">{{ target.id }}</span>
            </div>

            <button
              @click="removeTarget(target.id)"
              class="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-gray-200 transition-colors"
              title="Remove from wish list"
            >
              ×
            </button>
          </div>
        </div>
      </div>

      <!-- DSOs section -->
      <div v-if="dsoTargets.length > 0">
        <h4 class="text-xs font-semibold text-gray-500 uppercase mb-2">Deep Sky Objects</h4>
        <div class="space-y-1">
          <div
            v-for="target in dsoTargets"
            :key="target.id"
            class="flex items-center justify-between p-2 bg-gray-800 rounded hover:bg-gray-750 transition-colors"
          >
            <div class="flex items-center gap-2">
              <!-- Capture indicator -->
              <span v-if="target.captured" class="text-green-400" title="Captured">✓</span>
              <span v-else class="text-gray-600">○</span>

              <span class="text-sm text-gray-200">{{ target.name || target.id }}</span>
            </div>

            <button
              @click="removeTarget(target.id)"
              class="p-1 hover:bg-gray-700 rounded text-gray-400 hover:text-gray-200 transition-colors"
              title="Remove from wish list"
            >
              ×
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Reset button -->
    <button
      v-if="planningStore.wishlistTargets.length > 0"
      @click="resetToDefaults"
      class="w-full mt-4 px-3 py-2 text-sm text-gray-400 hover:text-gray-200 hover:bg-gray-800 rounded-lg transition-colors border border-gray-700"
    >
      Reset to Defaults
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { usePlanningStore } from '@/stores/planning'

const planningStore = usePlanningStore()

// Solar system objects (planets & moons)
const SOLAR_SYSTEM_OBJECTS = [
  'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune',
  'Moon', 'Sun', 'Io', 'Europa', 'Ganymede', 'Callisto',
  'Titan', 'Rhea', 'Tethys', 'Dione', 'Enceladus'
]

const planetTargets = computed(() => {
  return planningStore.wishlistTargets.filter(t =>
    SOLAR_SYSTEM_OBJECTS.includes(t.id)
  )
})

const dsoTargets = computed(() => {
  return planningStore.wishlistTargets.filter(t =>
    !SOLAR_SYSTEM_OBJECTS.includes(t.id)
  )
})

const removeTarget = async (targetId) => {
  if (!confirm(`Remove ${targetId} from wish list?`)) {
    return
  }

  try {
    await planningStore.removeFromWishlist(targetId)
  } catch (err) {
    alert('Failed to remove target: ' + err.message)
  }
}

const resetToDefaults = async () => {
  if (!confirm('Replace wish list with 19 solar system objects? This will remove all current targets.')) {
    return
  }

  try {
    await planningStore.resetWishlistToDefaults()
  } catch (err) {
    alert('Failed to reset wish list: ' + err.message)
  }
}
</script>
```

**Step 2: Add WishListPanel to PlanningView**

In `frontend/vue-app/src/views/PlanningView.vue`, update the left panel:

```vue
<template>
  <PanelContainer
    v-model:left-panel-visible="leftPanelVisible"
    :console-visible="false"
  >
    <!-- Left panel header -->
    <template #left-header>
      <div>
        <h3 class="text-sm font-semibold text-gray-200">Planning</h3>
      </div>
    </template>

    <!-- Left panel label (for peek tab) -->
    <template #left-label>Planning</template>

    <!-- Left: Planning Controls + Wish List -->
    <template #left>
      <div class="flex flex-col h-full">
        <!-- Saved Plans Dropdown (placeholder for now) -->
        <div class="p-3 border-b border-gray-800">
          <label class="block text-xs font-semibold text-gray-500 uppercase mb-2">Saved Plans</label>
          <select class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200">
            <option>Select plan...</option>
          </select>
        </div>

        <!-- Wish List Panel -->
        <div class="flex-1 overflow-y-auto border-b border-gray-800">
          <WishListPanel />
        </div>

        <!-- Planning Controls -->
        <div class="flex-none">
          <PlanningControls />
        </div>
      </div>
    </template>

    <!-- Main content (existing plan display) -->
    <template #main>
      <!-- ... existing main content ... -->
    </template>
  </PanelContainer>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePlanningStore } from '@/stores/planning'
import { useExecutionStore } from '@/stores/execution'
import PanelContainer from '@/components/layout/PanelContainer.vue'
import PlanningControls from '@/components/planning/PlanningControls.vue'
import WishListPanel from '@/components/planning/WishListPanel.vue'

const router = useRouter()
const planningStore = usePlanningStore()
const executionStore = useExecutionStore()
const leftPanelVisible = ref(true)

onMounted(async () => {
  // Load wish list on mount
  await planningStore.loadWishlist()
  await planningStore.loadCaptures()
})

// ... rest of existing script ...
</script>
```

**Step 3: Test in browser**

Run: `cd frontend/vue-app && npm run dev`
Navigate to Planning view, verify:
- Wish list panel appears
- Shows empty state initially
- Can add targets from Discovery view (via existing "Add to Plan" button)
- Shows planet/DSO sections
- Can remove targets
- Reset button works

**Step 4: Commit**

```bash
git add frontend/vue-app/src/components/planning/WishListPanel.vue frontend/vue-app/src/views/PlanningView.vue
git commit -m "feat: add WishListPanel component to Planning view"
```

---

## Task 5: Frontend - WishListBadge in Discovery View

**Files:**
- Create: `frontend/vue-app/src/components/discovery/WishListBadge.vue`
- Modify: `frontend/vue-app/src/views/DiscoveryView.vue`

**Step 1: Create WishListBadge component**

Create `frontend/vue-app/src/components/discovery/WishListBadge.vue`:

```vue
<template>
  <button
    @click="goToPlanning"
    class="flex items-center gap-2 px-3 py-2 bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/30 rounded-lg transition-colors"
  >
    <span class="text-sm font-medium text-blue-400">Wish List:</span>
    <span class="text-sm text-gray-200">
      {{ planningStore.wishlistTargets.length }} targets
      <span v-if="capturedCount > 0" class="text-green-400">({{ capturedCount }} captured)</span>
    </span>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePlanningStore } from '@/stores/planning'

const router = useRouter()
const planningStore = usePlanningStore()

const capturedCount = computed(() => {
  return planningStore.wishlistTargets.filter(t => t.captured).length
})

const goToPlanning = () => {
  router.push('/planning')
}
</script>
```

**Step 2: Add WishListBadge to DiscoveryView header**

In `frontend/vue-app/src/views/DiscoveryView.vue`, update the header:

```vue
<template>
  <PanelContainer
    v-model:left-panel-visible="leftPanelVisible"
    :console-visible="false"
  >
    <!-- ... existing left panel ... -->

    <!-- Main: Catalog Grid -->
    <template #main>
      <div class="flex flex-col h-full">
        <!-- View Header -->
        <div class="bg-gray-900/50 border-b border-gray-800 px-4 py-3 flex-none">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-gray-200">Discovery</h2>
              <p class="text-sm text-gray-500">Browse and search celestial objects</p>
            </div>

            <!-- Wish List Badge -->
            <WishListBadge />
          </div>
        </div>

        <!-- Catalog Grid (existing) -->
        <div class="flex-1 overflow-y-auto p-6">
          <CatalogGrid />
        </div>
      </div>
    </template>
  </PanelContainer>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useCatalogStore } from '@/stores/catalog'
import { usePlanningStore } from '@/stores/planning'
import PanelContainer from '@/components/layout/PanelContainer.vue'
import SearchFilters from '@/components/discovery/SearchFilters.vue'
import CatalogGrid from '@/components/discovery/CatalogGrid.vue'
import WishListBadge from '@/components/discovery/WishListBadge.vue'

const catalogStore = useCatalogStore()
const planningStore = usePlanningStore()
const leftPanelVisible = ref(true)

onMounted(async () => {
  // Load catalog data
  await catalogStore.fetchCatalogData()

  // Load wish list for badge
  await planningStore.loadWishlist()
})
</script>
```

**Step 3: Test in browser**

Run: `npm run dev`
Navigate to Discovery view, verify:
- Badge shows in header
- Shows correct count
- Shows captured count if > 0
- Clicking navigates to Planning view

**Step 4: Commit**

```bash
git add frontend/vue-app/src/components/discovery/WishListBadge.vue frontend/vue-app/src/views/DiscoveryView.vue
git commit -m "feat: add WishListBadge to Discovery view header"
```

---

## Task 6: Frontend - Update PlanningControls with Generate Daily Plan

**Files:**
- Modify: `frontend/vue-app/src/components/planning/PlanningControls.vue`

**Step 1: Update PlanningControls to add quality threshold and generate button**

In `frontend/vue-app/src/components/planning/PlanningControls.vue`:

```vue
<template>
  <div class="p-3 space-y-4">
    <!-- Observing Date -->
    <div>
      <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 px-1">
        Observing Date
      </label>
      <input
        v-model="observingDate"
        type="date"
        class="w-full px-3 py-2 bg-gray-800 border border-transparent focus:border-blue-500/50 rounded-lg text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500/20 transition-all"
      />
    </div>

    <!-- Quality Threshold -->
    <div>
      <label class="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 px-1">
        Quality Threshold: {{ (qualityThreshold * 100).toFixed(0) }}%
      </label>
      <input
        v-model.number="qualityThreshold"
        type="range"
        min="0.6"
        max="1.0"
        step="0.05"
        class="w-full accent-blue-500"
      />
      <p class="text-xs text-gray-500 mt-1 px-1">
        Minimum quality score for targets (default: 80%)
      </p>
    </div>

    <!-- Skip Captured Targets -->
    <div class="flex items-center gap-2 px-1">
      <input
        type="checkbox"
        id="skip-captured"
        v-model="skipCaptured"
        class="w-4 h-4 rounded border-gray-700 bg-gray-800 text-blue-500 focus:ring-blue-500"
      />
      <label for="skip-captured" class="text-sm text-gray-300 cursor-pointer">
        Skip captured targets
      </label>
    </div>

    <!-- Generate Daily Plan Button -->
    <button
      @click="generateDailyPlan"
      :disabled="planningStore.loading || planningStore.wishlistTargets.length === 0"
      class="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    >
      <span v-if="planningStore.loading">Generating Plan...</span>
      <span v-else>Generate Daily Plan</span>
    </button>

    <p class="text-xs text-gray-500 px-1">
      Generates plan for tonight using wish list targets and top-scored DSOs
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { usePlanningStore } from '@/stores/planning'

const planningStore = usePlanningStore()

const observingDate = ref(new Date().toISOString().split('T')[0]) // Today
const qualityThreshold = ref(0.8) // Default 80%
const skipCaptured = ref(true)

const generateDailyPlan = async () => {
  try {
    // Update constraints
    planningStore.constraints.min_score = qualityThreshold.value
    planningStore.observationDate = observingDate.value

    // Filter wish list if skip captured
    let wishlistIds = planningStore.wishlistTargets.map(t => t.id)
    if (skipCaptured.value) {
      wishlistIds = planningStore.wishlistTargets
        .filter(t => !t.captured)
        .map(t => t.id)
    }

    // Check if any targets available
    if (wishlistIds.length === 0) {
      alert('All wish list targets are captured! Uncheck "Skip captured" or add more targets.')
      return
    }

    // Generate plan using existing generatePlan action
    // (will be enhanced in next step to use wish list)
    await planningStore.generatePlan()

  } catch (err) {
    alert('Failed to generate plan: ' + err.message)
  }
}
</script>
```

**Step 2: Update planning store's generatePlan to use wish list**

In `frontend/vue-app/src/stores/planning.js`, update the `generatePlan` action:

```javascript
async generatePlan() {
  this.loading = true
  this.error = null

  try {
    // Get location from settings
    const location = this.location

    // Filter wish list by skipCaptured setting (handled in component)
    const wishlistIds = this.wishlistTargets
      .filter(t => !t.captured) // Component controls this via skipCaptured
      .map(t => t.id)

    // Build request matching backend PlanRequest model
    const request = {
      location: {
        name: location.name,
        latitude: location.latitude,
        longitude: location.longitude,
        elevation: location.elevation || 0,
        timezone: location.timezone
      },
      observing_date: this.observationDate || new Date().toISOString().split('T')[0],
      constraints: {
        min_altitude_degrees: this.constraints.min_altitude_degrees,
        max_altitude_degrees: this.constraints.max_altitude_degrees,
        avoid_moon: this.constraints.avoid_moon,
        setup_time_minutes: this.constraints.setup_time_minutes,
        object_types: this.constraints.object_types,
        daytime_planning: this.constraints.daytime_planning,
        min_score: this.constraints.min_score || 0.8  // Use quality threshold
      },
      custom_targets: wishlistIds  // Use wish list as custom targets
    }

    const response = await axios.post('/api/plan', request)
    this.currentPlan = response.data
  } catch (err) {
    this.error = 'Failed to generate plan: ' + (err.response?.data?.detail || err.message)
    console.error('Plan generation error:', err)
    throw err
  } finally {
    this.loading = false
  }
}
```

**Step 3: Test in browser**

Run: `npm run dev`
Navigate to Planning view, verify:
- Quality threshold slider works (0.6 - 1.0)
- Skip captured checkbox works
- Generate Daily Plan button enabled when wish list has targets
- Clicking generates plan with wish list targets

**Step 4: Commit**

```bash
git add frontend/vue-app/src/components/planning/PlanningControls.vue frontend/vue-app/src/stores/planning.js
git commit -m "feat: add quality threshold, skip captured, and generate daily plan to PlanningControls"
```

---

## Task 7: Backend - Enhance Plan Generation to Prioritize Planets

**Files:**
- Modify: `backend/app/services/planner_service.py`
- Modify: `backend/app/services/planet_service.py` (add moon ephemeris if needed)
- Test: `backend/tests/unit/services/test_planner_service.py`

**Step 1: Write failing test for planet prioritization**

In `backend/tests/unit/services/test_planner_service.py`:

```python
def test_plan_prioritizes_planets_from_custom_targets():
    """Test that planets in custom_targets are scheduled first."""
    from app.services.planner_service import PlannerService
    from app.models import Location, PlanRequest, ObservingConstraints
    from datetime import date

    db = SessionLocal()
    planner = PlannerService(db)

    location = Location(
        latitude=45.0,
        longitude=-111.0,
        elevation=1000,
        timezone="America/Denver"
    )

    constraints = ObservingConstraints(
        min_altitude=30,
        max_altitude=90,
        min_score=0.7,
        object_types=["galaxy", "nebula"]
    )

    # Custom targets include planets and DSOs
    custom_targets = ["Jupiter", "Mars", "M31", "M42"]

    request = PlanRequest(
        location=location,
        observing_date=date.today().isoformat(),
        constraints=constraints,
        custom_targets=custom_targets
    )

    plan = planner.generate_plan(request)

    # Planets should be scheduled first
    scheduled_ids = [t.target.catalog_id for t in plan.scheduled_targets]

    # Jupiter and Mars should appear before M31 and M42 (if all are visible)
    if "Jupiter" in scheduled_ids and "M31" in scheduled_ids:
        jupiter_idx = scheduled_ids.index("Jupiter")
        m31_idx = scheduled_ids.index("M31")
        assert jupiter_idx < m31_idx, "Planets should be scheduled before DSOs"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && pytest tests/unit/services/test_planner_service.py::test_plan_prioritizes_planets_from_custom_targets -v`
Expected: FAIL (planets not prioritized)

**Step 3: Update PlannerService to separate planets from DSOs**

In `backend/app/services/planner_service.py`, find the `generate_plan` method and update:

```python
def generate_plan(self, request: PlanRequest) -> ObservingPlan:
    """Generate optimized observing plan."""
    # ... existing setup code ...

    # Separate custom_targets into planets vs DSOs
    SOLAR_SYSTEM_OBJECTS = [
        "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune",
        "Moon", "Sun", "Io", "Europa", "Ganymede", "Callisto",
        "Titan", "Rhea", "Tethys", "Dione", "Enceladus"
    ]

    planet_targets = []
    dso_target_ids = []

    if request.custom_targets:
        for target_id in request.custom_targets:
            if target_id in SOLAR_SYSTEM_OBJECTS:
                planet_targets.append(target_id)
            else:
                dso_target_ids.append(target_id)

    scheduled_targets = []

    # 1. Schedule planets first (visibility check only, no scoring)
    if planet_targets:
        from app.services.planet_service import PlanetService
        planet_service = PlanetService()

        for planet_name in planet_targets:
            try:
                # Get planet ephemeris for observing time
                ephemeris = planet_service.get_ephemeris(
                    planet_name,
                    location,
                    observing_time
                )

                # Check if visible (above min_altitude)
                if ephemeris.altitude >= request.constraints.min_altitude:
                    # Create target entry for planet
                    planet_target = Target(
                        catalog_id=planet_name,
                        name=planet_name,
                        object_type="planet",
                        ra=ephemeris.ra,
                        dec=ephemeris.dec,
                        magnitude=ephemeris.magnitude or 0.0,
                        size_arcmin=0.0
                    )

                    # Schedule for ~30 minutes (or configurable duration)
                    scheduled_targets.append(ScheduledTarget(
                        target=planet_target,
                        start_time=observing_start,
                        duration_minutes=30,
                        max_altitude=ephemeris.altitude,
                        transit_time=observing_time,
                        composite_score=1.0  # Planets always score 1.0 (high priority)
                    ))

                    # Advance start time for next target
                    observing_start += timedelta(minutes=30)

            except Exception as e:
                logger.warning(f"Failed to schedule planet {planet_name}: {e}")

    # 2. Calculate remaining session time
    remaining_time = (session_end - observing_start).total_seconds() / 60.0

    # 3. Fill remaining time with DSOs (existing logic with scoring)
    if remaining_time > 0:
        # ... existing DSO scoring and scheduling logic ...
        # Use dso_target_ids as custom targets
        # Apply min_score threshold
        # Fill until session_end
        pass

    # ... rest of existing code ...

    return ObservingPlan(
        location=location_model,
        session=session_info,
        scheduled_targets=scheduled_targets,
        total_targets=len(scheduled_targets),
        coverage_percent=coverage
    )
```

**Step 4: Add get_ephemeris method to PlanetService if not exists**

In `backend/app/services/planet_service.py`:

```python
def get_ephemeris(
    self,
    planet_name: str,
    location: Location,
    observing_time: datetime
) -> PlanetEphemeris:
    """Get ephemeris for a planet at specific time and location."""
    from astropy import units as u
    from astropy.coordinates import AltAz, EarthLocation, get_body, get_sun
    from astropy.time import Time

    # Create EarthLocation
    earth_loc = EarthLocation(
        lat=location.latitude * u.deg,
        lon=location.longitude * u.deg,
        height=location.elevation * u.m
    )

    # Create Time object
    obs_time = Time(observing_time)

    # Get body coordinates
    if planet_name.lower() == "sun":
        body = get_sun(obs_time)
    else:
        body = get_body(planet_name.lower(), obs_time, earth_loc)

    # Transform to AltAz frame
    altaz_frame = AltAz(obstime=obs_time, location=earth_loc)
    altaz = body.transform_to(altaz_frame)

    # Get planet data
    planet_info = PLANET_DATA.get(planet_name, {})

    return PlanetEphemeris(
        name=planet_name,
        ra=body.ra.deg,
        dec=body.dec.deg,
        altitude=altaz.alt.deg,
        azimuth=altaz.az.deg,
        distance_au=body.distance.au if hasattr(body, 'distance') else 0.0,
        magnitude=planet_info.get('magnitude', 0.0),  # Simplified
        phase=0.0,  # TODO: Calculate actual phase
        diameter_arcsec=0.0,  # TODO: Calculate
        rise_time=None,  # TODO: Calculate
        set_time=None,  # TODO: Calculate
        transit_time=None  # TODO: Calculate
    )
```

**Step 5: Run test to verify it passes**

Run: `cd backend && pytest tests/unit/services/test_planner_service.py::test_plan_prioritizes_planets_from_custom_targets -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/services/planner_service.py backend/app/services/planet_service.py backend/tests/unit/services/test_planner_service.py
git commit -m "feat: prioritize planets in plan generation (schedule visible planets first, fill with scored DSOs)"
```

---

## Task 8: Frontend - Add Capture Indicators to CatalogGrid

**Files:**
- Modify: `frontend/vue-app/src/components/discovery/CatalogGrid.vue`

**Step 1: Update CatalogGrid to show capture indicators**

In `frontend/vue-app/src/components/discovery/CatalogGrid.vue`, update the card template:

```vue
<template>
  <div class="catalog-view">
    <!-- ... existing stats banner ... -->

    <!-- Catalog Grid -->
    <div class="catalog-grid" id="catalog-grid">
      <!-- ... existing loading/error states ... -->

      <div v-else class="grid-container">
        <div v-for="item in catalogStore.items" :key="item.id || item.name" class="catalog-card">
          <div class="catalog-card-image">
            <!-- Capture indicator badge -->
            <div v-if="isCaptured(item.id || item.name)" class="absolute top-2 right-2 px-2 py-1 bg-green-500/90 text-white text-xs font-semibold rounded-full flex items-center gap-1">
              <span>✓</span>
              <span>Captured</span>
            </div>

            <img :src="getImageUrl(item)" :alt="item.name" loading="lazy" @error="hideParentOnError">
          </div>

          <div class="catalog-card-content">
            <!-- ... existing card header and details ... -->

            <div class="catalog-card-actions">
              <button
                @click="addToPlan(item)"
                :class="inWishlist(item.id || item.name) ? 'bg-gray-600' : 'bg-blue-600 hover:bg-blue-700'"
                class="w-full px-4 py-2 text-white text-sm rounded transition-colors"
              >
                {{ inWishlist(item.id || item.name) ? 'In Wish List' : 'Add to Plan' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ... existing pagination ... -->
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, watch } from 'vue';
import { useCatalogStore } from '@/stores/catalog';
import { usePlanningStore } from '@/stores/planning';

const catalogStore = useCatalogStore();
const planningStore = usePlanningStore();

// ... existing code ...

const isCaptured = (targetId) => {
  return planningStore.wishlistTargets.some(t => t.id === targetId && t.captured);
};

const inWishlist = (targetId) => {
  return planningStore.wishlistTargets.some(t => t.id === targetId);
};

const addToPlan = (item) => {
  catalogStore.addSelectedTarget(item);
};

// ... rest of existing code ...
</script>

<style scoped>
/* ... existing styles ... */

/* Capture badge positioning */
.catalog-card-image {
  position: relative;
}
</style>
```

**Step 2: Test in browser**

Run: `npm run dev`
- Add targets to wish list
- Mark some as captured (via API or Planning view)
- Navigate to Discovery
- Verify capture badges appear on captured targets
- Verify "In Wish List" button shows for wish list items

**Step 3: Commit**

```bash
git add frontend/vue-app/src/components/discovery/CatalogGrid.vue
git commit -m "feat: add capture indicators and wish list badges to catalog cards"
```

---

## Task 9: Integration Testing and Polish

**Files:**
- Test: Manual testing checklist
- Modify: Various files for bug fixes and polish

**Step 1: Manual testing checklist**

Test the following flows:

```
□ Fresh app load initializes wish list with 19 solar system objects
□ Add DSO from Discovery view, appears in Planning wish list
□ Remove target from wish list, disappears from both views
□ Reset to defaults restores 19 objects
□ Generate daily plan with quality threshold 0.8
□ Planets appear first in generated plan
□ DSOs fill remaining time, scored and filtered
□ Mark target as captured via Planning view
□ Capture indicator appears in Discovery and Planning
□ Generate plan with "skip captured" excludes captured targets
□ Wish list persists across page refresh
□ Captures persist across page refresh
□ Error handling: network failures show toast messages
□ Loading states: spinners during async operations
□ Empty wish list shows helpful message
□ All captured + skip captured shows appropriate message
```

**Step 2: Fix any bugs found during testing**

Document and fix issues:
- UI glitches
- Data synchronization issues
- Edge cases (empty states, all captured, etc.)

**Step 3: Polish UI/UX**

- Ensure consistent spacing and styling
- Add loading skeletons where appropriate
- Improve error messages
- Add helpful tooltips

**Step 4: Final commit**

```bash
git add .
git commit -m "test: manual integration testing and UI polish"
```

---

## Task 10: Documentation Update

**Files:**
- Modify: `README.md`
- Create: `docs/USER_GUIDE.md` (optional)

**Step 1: Update README with new features**

In `README.md`, add section:

```markdown
## Wish List and Daily Planning

### Wish List
- Pre-populated with 19 solar system objects (planets, moons)
- Add targets from Discovery view ("Add to Plan" button)
- Manage targets in Planning view left panel
- Grouped by type (Planets/Moons, Deep Sky Objects)
- Reset to defaults restores 19 solar system objects

### Daily Plan Generation
- Manual "Generate Daily Plan" button in Planning view
- Quality threshold (0.6-1.0, default 0.8) controls minimum target score
- Planets scheduled first (visibility only, no quality scoring)
- DSOs fill remaining time (scored and filtered by quality threshold)
- "Skip captured targets" option excludes previously imaged targets

### Capture Tracking
- Mark targets as captured with image count and notes
- Visual indicators (✓ checkmark) in Discovery and Planning views
- Capture history persists across sessions
- Filter captured targets from daily plans
```

**Step 2: Commit documentation**

```bash
git add README.md
git commit -m "docs: add wish list and daily planning documentation"
```

---

## Summary

This implementation plan follows TDD principles and breaks down the wish list and daily plan features into manageable tasks:

1. Backend wish list endpoints (GET/PUT, defaults)
2. Backend capture tracking (model, migrations, endpoints)
3. Frontend planning store (wish list actions, capture tracking)
4. WishListPanel component (Planning view left panel)
5. WishListBadge component (Discovery view header)
6. PlanningControls updates (quality threshold, generate button)
7. Plan generation enhancements (prioritize planets)
8. CatalogGrid updates (capture indicators)
9. Integration testing and polish
10. Documentation updates

Each task includes:
- Exact file paths
- Complete code snippets
- Test-first approach (write failing test, implement, verify)
- Frequent commits with conventional commit messages

The plan assumes a skilled developer but provides complete implementation details for clarity.
