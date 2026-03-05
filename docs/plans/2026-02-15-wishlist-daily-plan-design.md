# Wish List and Daily Plan Design

**Date:** 2026-02-15
**Goal:** Add wish list functionality with pre-populated solar system objects and manual daily plan generation

---

## Overview

This design adds:
1. **Wish List** - User-managed list of favorite targets (planets, moons, DSOs)
2. **Daily Plan Generation** - Manual button to generate optimized plan for tonight
3. **Capture Tracking** - Track completed observations with visual indicators
4. **Saved Plans** - Load previously generated plans from dropdown

Pre-populated with 19 solar system objects:
- **8 planets:** Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune
- **Earth's Moon**
- **Sun** (with solar filter warning)
- **Jupiter's Galilean moons:** Io, Europa, Ganymede, Callisto
- **Saturn's major moons:** Titan, Rhea, Tethys, Dione, Enceladus

---

## Architecture

### High-Level Structure

**Backend:**
- Extend `AppSetting` model to store wish list as JSON array: `user.wishlist_targets`
- New endpoints for wish list management and defaults
- New `CapturedTarget` model to track completed observations
- New endpoints for capture tracking
- Enhance existing `/api/planets` endpoint for ephemeris data
- Reuse existing `/api/plan` endpoint with `custom_targets` parameter

**Frontend:**
- Extend `planningStore` to manage wish list and captures
- New components: `WishListPanel.vue`, `WishListBadge.vue`
- Update `PlanningControls.vue`: saved plans dropdown, generate button, quality threshold
- Update catalog components: capture indicators, wish list badges
- Discovery view shows wish list count, Planning view shows full management

**Data Flow:**
1. App loads → fetch wish list + captures from settings
2. If empty → initialize with 19 solar system defaults
3. User adds/removes targets → update store + save to backend
4. "Generate Daily Plan" → build request with wish list as `custom_targets`
5. Backend schedules planets first (visibility only), then fills with scored DSOs
6. Mark targets as captured → visual indicators update

---

## Backend Components

### API Endpoints

#### Wish List Management

**`GET /api/settings/wishlist`**
- Returns: `{"targets": ["Jupiter", "M31", "NGC7000", ...]}`
- Query param: `?include_captures=true` enriches with capture status
- If not set, returns empty array (frontend initializes with defaults)

**`PUT /api/settings/wishlist`**
- Body: `{"targets": ["Jupiter", "M31", ...]}`
- Validates target IDs exist (planets or catalog entries)
- Saves to `AppSetting` with key `user.wishlist_targets`
- Returns: `{"success": true, "count": 15}`

**`GET /api/wishlist/defaults`**
- Returns static list of 19 solar system objects
- Response: `{"targets": ["Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Moon", "Sun", "Io", "Europa", "Ganymede", "Callisto", "Titan", "Rhea", "Tethys", "Dione", "Enceladus"]}`

#### Capture Tracking

**`GET /api/captures`**
- Query params: `?target_ids=M31,Jupiter` (optional filter)
- Returns: `{"captures": [{"target_id": "M31", "captured_at": "2026-02-14T22:30:00Z", "image_count": 45, "session_date": "2026-02-14"}, ...]}`

**`POST /api/captures`**
- Body: `{"target_id": "M31", "session_date": "2026-02-14", "image_count": 45, "notes": "Great seeing"}`
- Creates capture record
- Returns: `{"id": 123, "target_id": "M31", "captured_at": "...", ...}`

**`DELETE /api/captures/{capture_id}`**
- Removes capture record (for mistakes/corrections)
- Returns: `{"success": true}`

#### Planet Ephemeris (Enhancement)

**`GET /api/planets/ephemeris`**
- Add query param: `?names=Jupiter,Saturn,Moon` to get specific planets
- Returns ephemeris with visibility (alt/az) for each

### Data Models

**AppSetting (Extended):**
- Add key: `user.wishlist_targets`
- Value: JSON array of strings (target IDs)
- Example: `["Jupiter", "M31", "NGC7000", "Titan"]`

**CapturedTarget (New):**
```python
class CapturedTarget(Base):
    id: int (PK)
    user_id: str (FK to user settings)
    target_id: str (e.g., "M31", "Jupiter")
    target_type: str ("planet" or "dso")
    captured_at: datetime
    session_date: date (observing night)
    image_count: int (number of images captured)
    notes: str (optional)
```

### Service Layer

**PlanetService:**
- Already exists, minor enhancements for moon ephemeris

**PlannerService:**
- Reuse existing `generate_plan()` with `custom_targets` parameter
- Add logic to prioritize planets:
  1. Check visibility (min_altitude only, no quality scoring)
  2. Schedule visible planets first
  3. Fill remaining time with DSOs meeting quality threshold

**Integration Points:**
- When execution completes a target → auto-create capture record
- Wish list endpoint enriched with capture status flags
- Daily plan generation can filter out captured targets

---

## Frontend Components

### Pinia Stores

**`planningStore.js` (Extended):**

New state:
```javascript
wishlistTargets: [],  // Array of target objects with capture status
capturedTargets: [],  // Array of capture records
```

New actions:
- `loadWishlist()` - Fetch from backend with capture status
- `addToWishlist(target)` - Add target, save to backend
- `removeFromWishlist(targetId)` - Remove, save to backend
- `resetWishlistToDefaults()` - Load 19 defaults, save to backend
- `markCaptured(targetId, sessionDate, imageCount, notes)` - Create capture record
- `loadCaptures()` - Fetch capture history
- `generateDailyPlan()` - Enhanced to use wish list, quality threshold, skip captured

**`catalogStore.js` (Updated):**
- Update `addSelectedTarget()` to call `planningStore.addToWishlist()`
- Add `captured: true/false` flag to items when displaying

### Vue Components

**`WishListPanel.vue` (New - Planning view left panel):**
- Shows list of wish list targets, grouped by type (Planets, DSOs)
- Each item displays:
  - Name and type badge
  - Capture indicator (✓ checkmark if captured, with date on hover)
  - Remove button (X icon)
- "Reset to Defaults" button at bottom (with confirmation dialog)
- Empty state: "Add targets from Discovery view"
- Props: none
- Emits: none (uses planningStore directly)

**`WishListBadge.vue` (New - Discovery view header):**
- Pill badge showing: "Wish List: 15 targets (8 captured)"
- Click navigates to Planning view
- Uses planningStore.wishlistTargets for count
- Props: none
- Emits: none (uses router.push)

**`PlanningControls.vue` (Updated):**

Top to bottom layout:
1. **Saved plans dropdown** - Load previously saved plans
2. **Date picker** - Observing date (defaults to tonight)
3. **Quality threshold slider** - Range 0.6-1.0, default 0.8, step 0.05
4. **Checkbox** - "Skip captured targets" (filters captured from plan)
5. **"Generate Daily Plan" button** - Primary blue button, prominent

**`CatalogGrid.vue` (Updated):**
- Add capture indicator: Checkmark badge on cards for captured targets
- "Add to Plan" button changes to "In Wish List" if already added
- Clicking captured targets shows tooltip: "Captured on Feb 14, 2026 (45 images)"

**`SearchFilters.vue` (Updated - Optional):**
- Add checkbox: "Hide captured targets"
- Filters catalog results to exclude captured items

### UI/UX Details

**Planning View Left Panel Structure:**
```
┌─────────────────────────────┐
│ Saved Plans                 │
│ [Dropdown: Select plan...]  │
├─────────────────────────────┤
│ Wish List (15)              │
│                             │
│ PLANETS                     │
│ ☑ Jupiter        [×]        │
│ ○ Saturn         [×]        │
│                             │
│ DSOs                        │
│ ☑ M31 - Andromeda [×]      │
│ ○ M42 - Orion     [×]       │
│ ...                         │
│                             │
│ [Reset to Defaults]         │
├─────────────────────────────┤
│ Observing Date              │
│ [Date picker: Tonight]      │
│                             │
│ Quality Threshold: 0.80     │
│ [────●──────────]           │
│                             │
│ ☑ Skip captured targets     │
│                             │
│ [Generate Daily Plan]       │
└─────────────────────────────┘

☑ = Captured
○ = Not captured
```

**Discovery View Header:**
```
┌────────────────────────────────────┐
│ Discovery         [Wish List: 15 (8 captured)] │
│                                    │
└────────────────────────────────────┘
```

---

## Data Flow

### 1. App Initialization

```
App loads
  → planningStore.loadWishlist()
  → GET /api/settings/wishlist?include_captures=true
  → If empty/null:
      → GET /api/wishlist/defaults
      → PUT /api/settings/wishlist (save 19 defaults)
  → planningStore.loadCaptures()
  → GET /api/captures
  → Store updated with wish list + capture status
  → UI renders with indicators
```

### 2. Adding to Wish List (Discovery → Planning)

```
User clicks "Add to Plan" on M31 card in Discovery
  → catalogStore.addSelectedTarget(M31)
  → planningStore.addToWishlist(M31)
  → PUT /api/settings/wishlist with updated array
  → Store updated
  → Badge updates: "Wish List: 16 targets"
  → Planning view wish list panel auto-refreshes
  → M31 card shows "In Wish List" button
```

### 3. Generate Daily Plan

```
User clicks "Generate Daily Plan"
  (Settings: quality threshold 0.8, skip captured: true)

  → planningStore.generateDailyPlan()
  → Build request:
      location: from settings
      observing_date: from date picker (default: tonight)
      custom_targets: wishlistTargets
                      .filter(t => !t.captured)
                      .map(t => t.id)
                      // ["Jupiter", "Saturn", "M31", "M42", ...]
      constraints:
        min_score: 0.8
        min_altitude: 30
        max_altitude: 90
        object_types: ["galaxy", "nebula", "cluster", ...]

  → POST /api/plan

  → Backend (PlannerService):
      1. Separate custom_targets into planets vs DSOs
      2. Fetch planet ephemeris for planet targets
      3. Schedule visible planets first:
         - Check min_altitude only (no quality scoring)
         - Add to scheduled_targets if visible
      4. Calculate remaining session time
      5. Fetch DSO catalog entries (custom + top scored)
      6. Score DSOs with visibility/weather/object components
      7. Filter DSOs by min_score >= 0.8
      8. Schedule DSOs to fill remaining time (no overlap)
      9. Return scheduled_targets list with timing

  → Response: ObservingPlan with scheduled_targets
  → planningStore.currentPlan updated
  → Main panel shows generated plan with timing
```

### 4. Mark Target as Captured

```
User completes imaging session
  → Clicks "Mark Captured" on M31 in wish list
  → Dialog: "How many images? [45] Notes: [Great seeing]"
  → planningStore.markCaptured("M31", "2026-02-15", 45, "Great seeing")
  → POST /api/captures {
      target_id: "M31",
      session_date: "2026-02-15",
      image_count: 45,
      notes: "Great seeing"
    }
  → Reload wish list to refresh capture status
  → M31 shows ✓ badge in wish list panel
  → M31 shows ✓ badge in catalog grid
  → Hover shows: "Captured on Feb 15, 2026 (45 images)"
```

### 5. Reset to Defaults

```
User clicks "Reset to Defaults"
  → Confirmation dialog:
      "Replace wish list with 19 solar system objects?
       This will remove all current targets."
      [Cancel] [Reset]

  → User clicks [Reset]
  → planningStore.resetWishlistToDefaults()
  → GET /api/wishlist/defaults
  → Response: ["Mercury", "Venus", ..., "Enceladus"]
  → PUT /api/settings/wishlist (19 objects)
  → planningStore.wishlistTargets updated
  → Wish list panel refreshes with 19 solar system objects
  → Badge updates: "Wish List: 19 targets (N captured)"
```

---

## Error Handling

### Network Failures
- Wish list save fails → Toast: "Failed to save wish list. Changes may not persist."
- Show retry button on failures
- Graceful degradation: keep local state even if save fails
- On app reload, attempt to sync local state with backend

### Invalid Targets
- Backend validates target IDs exist before adding
- Return 400: `{"error": "Target 'INVALID123' not found in catalog or planet list"}`
- Frontend filters invalid targets on load (log warning, skip)

### Plan Generation Failures
- No visible targets → "No targets visible tonight. Try adjusting date or adding more targets."
- All captured → "All wish list targets already captured! Add more or uncheck 'Skip captured'."
- Backend errors → Display error message with retry option
- Loading spinner during generation (disable button)

### User Feedback
- Success toasts:
  - "Added M31 to wish list"
  - "Plan generated with 8 targets"
  - "M31 marked as captured"
- Loading states:
  - Spinner on "Generate Daily Plan" button
  - Skeleton loader in wish list panel
- Confirmation dialogs:
  - Reset to defaults: "Replace wish list with 19 solar system objects?"
  - Remove target: "Remove M31 from wish list?"

---

## Testing Strategy

### Backend Tests

**Wish List Operations:**
- Create wish list with valid targets (planets + DSOs)
- Validate invalid target IDs rejected
- Reset to defaults returns 19 objects
- Include captures flag enriches response

**Capture Tracking:**
- Create capture record
- List captures (all, filtered by target)
- Delete capture record
- Prevent duplicate captures for same target+date

**Plan Generation:**
- Generate plan with custom_targets (planets + DSOs)
- Planets scheduled first if visible
- DSOs scored and filtered by min_score
- Skip captured targets when flag set

**Planet Ephemeris:**
- Calculate positions for all 19 solar system objects
- Verify visibility calculations (alt/az)
- Test moon ephemeris (Jupiter/Saturn moons)

### Frontend Tests

**WishListPanel Component:**
- Renders targets grouped by type
- Shows capture indicators correctly
- Remove button calls removeFromWishlist()
- Reset button shows confirmation, calls resetWishlistToDefaults()

**WishListBadge Component:**
- Displays correct count and captured count
- Navigates to Planning view on click

**PlanningControls Component:**
- Quality threshold slider updates value
- "Skip captured" checkbox toggles state
- Generate button disabled while loading
- Generate button calls generateDailyPlan()

**CatalogGrid Component:**
- Shows capture badges on captured targets
- "Add to Plan" becomes "In Wish List" when added
- Tooltip shows capture date/count

**Store Actions:**
- loadWishlist() fetches and populates state
- addToWishlist() saves to backend
- markCaptured() creates capture record
- generateDailyPlan() builds correct request

### Integration Tests

**Full Flow:**
1. Discovery → Add to wish list → Planning view updates
2. Generate daily plan → Plan displayed with scheduled targets
3. Execute plan → Mark as captured → Indicators update
4. Generate new plan with "skip captured" → Captured targets excluded

**Persistence:**
- Wish list survives page refresh (loaded from backend)
- Captures survive page refresh
- Invalid targets filtered on load

**Edge Cases:**
- Empty wish list → Shows empty state
- All targets captured + skip captured → "All captured" message
- No visible targets → "No targets visible" message
- Network failure → Graceful degradation, retry option

### Manual Testing Checklist

- [ ] Fresh install initializes with 19 solar system defaults
- [ ] Add DSO from Discovery view, appears in wish list
- [ ] Remove target from wish list, disappears
- [ ] Reset to defaults, confirms and restores 19 objects
- [ ] Generate daily plan with quality threshold 0.8
- [ ] Verify planets scheduled first in plan
- [ ] Verify DSOs scored and filtered correctly
- [ ] Mark target as captured, indicator appears
- [ ] Generate plan with "skip captured", captured excluded
- [ ] Saved plans dropdown loads and displays plans
- [ ] Wish list persists across page refresh
- [ ] Captures persist across page refresh
- [ ] Error handling: network failures show toast + retry
- [ ] Loading states: spinners during async operations

---

## Implementation Notes

### Database Migration

**Add to AppSetting:**
- No migration needed (JSON value for existing model)
- Initialize `user.wishlist_targets` with empty array or 19 defaults

**Create CapturedTarget table:**
```sql
CREATE TABLE captured_targets (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    target_id VARCHAR(255) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    captured_at TIMESTAMP NOT NULL DEFAULT NOW(),
    session_date DATE NOT NULL,
    image_count INTEGER,
    notes TEXT,
    UNIQUE(user_id, target_id, session_date)
);
CREATE INDEX idx_captured_user_target ON captured_targets(user_id, target_id);
```

### Planet/Moon Data

**19 Solar System Defaults:**
```python
SOLAR_SYSTEM_DEFAULTS = [
    "Mercury", "Venus", "Mars", "Jupiter", "Saturn",
    "Uranus", "Neptune", "Moon", "Sun",
    "Io", "Europa", "Ganymede", "Callisto",  # Jupiter moons
    "Titan", "Rhea", "Tethys", "Dione", "Enceladus"  # Saturn moons
]
```

**Planet Service Enhancement:**
- Add moon ephemeris calculations (relative to parent planet)
- Use Astropy for Galilean moon positions
- Saturn moon positions from ephemeris tables

### Plan Generation Logic

**Priority Order:**
1. Check custom_targets for planets/moons
2. Calculate ephemeris, filter by visibility (min_altitude)
3. Schedule visible planets first (no quality scoring)
4. Calculate remaining session time after planets
5. Fetch DSOs (custom_targets DSOs + catalog)
6. Score DSOs (visibility + weather + object)
7. Filter by min_score threshold
8. Schedule DSOs to fill remaining time
9. Return combined scheduled_targets

**Quality Threshold:**
- User configurable: 0.6 - 1.0
- Default: 0.8 (80% - high quality)
- Only applies to DSOs, not planets

---

## Future Enhancements

- [ ] Multiple wish lists (e.g., "Galaxies", "Planets", "Faint Targets")
- [ ] Wish list sharing (export/import JSON)
- [ ] Automatic capture detection from FITS files
- [ ] Capture gallery (view images from captured targets)
- [ ] Completion percentage (15/20 targets captured)
- [ ] Capture statistics (total images, total time, best targets)
- [ ] Wish list sorting (manual drag-drop priority)
- [ ] Smart suggestions: "These targets are visible tonight!"
- [ ] Integration with calendar for observing reminders

---

## Success Criteria

**MVP Complete When:**
1. ✅ Wish list pre-populated with 19 solar system objects on first load
2. ✅ Add/remove targets from Discovery and Planning views
3. ✅ Reset to defaults restores 19 objects
4. ✅ Generate daily plan prioritizes wish list planets, fills with DSOs
5. ✅ Quality threshold configurable (default 0.8)
6. ✅ Mark targets as captured with visual indicators
7. ✅ Skip captured targets option works in plan generation
8. ✅ Saved plans dropdown loads and displays plans
9. ✅ Wish list persists to database (survives refresh)
10. ✅ Captures persist to database (survives refresh)

**User Experience Goals:**
- "I can see which planets are visible tonight without searching"
- "I can track which DSOs I've already captured"
- "I can generate an optimized plan for tonight in one click"
- "My wish list follows me across devices"
