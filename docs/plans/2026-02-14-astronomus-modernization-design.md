# Astronomus UX Modernization Design

**Date:** 2026-02-14
**Status:** Approved
**Approach:** Parallel Track (Theme + Core Features)

---

## Executive Summary

Modernize Astronomus Vue.js frontend to professional astronomy application standards. Replace "childish" bright cyan theme with dark scientific aesthetic. Restore all functionality from deleted vanilla JS files using modern Vue 3 patterns. Design informed by research into top astronomy software (Stellarium, KStars/Ekos, N.I.N.A.).

**Goals:**
1. Professional dark scientific theme (no bright cyan)
2. Full feature restoration (Discovery, Planning, Execution, Processing)
3. All integrations working (Weather, Seestar S50, Catalog)
4. Modern Vue 3 architecture (Composition API, reactive stores)

**Current Issues:**
- JavaScript errors on Processing view
- No data loading in any view
- Garish bright cyan theme (#00d9ff everywhere)
- Incomplete component implementations

---

## Design Principles

Derived from research into top astronomy software:

### From Stellarium (9,400 GitHub stars)
- **Minimalist, clean design** - Don't overwhelm with controls
- **Progressive disclosure** - Advanced features accessible but hidden until needed
- **Search-first interface** - Prominent search, simple by default
- **Visual beauty** - Professional, polished aesthetic

### From KStars/Ekos (259 GitHub stars)
- **Integrated workflow** - All related tools in one view
- **Reliability focus** - Stability and visual feedback prioritized
- **Complete automation** - Control entire imaging session from one interface
- **Professional tool philosophy** - Feature-complete over simplified

### From N.I.N.A. (137 GitHub stars)
- **Modular plugin system** - Show only what you need
- **Customizable workspace** - Collapsible panels, user control
- **Simplify complex workflows** - Make automation "easier, faster, comfortable"
- **Full automation** - Set it and forget it capabilities

---

## Architecture & Component Organization

### Directory Structure

```
frontend/vue-app/src/
├── components/
│   ├── common/              # Reusable UI components
│   │   ├── BaseButton.vue
│   │   ├── BaseCard.vue
│   │   ├── BaseInput.vue
│   │   ├── LoadingSpinner.vue
│   │   └── SkeletonCard.vue
│   ├── catalog/             # Discovery view components
│   │   ├── CatalogGrid.vue
│   │   └── CatalogSearchPanel.vue
│   ├── planning/            # Planning view components
│   │   ├── LocationDevicePanel.vue
│   │   ├── ObservingPreferencesPanel.vue
│   │   └── MosaicPlanningPanel.vue
│   ├── execution/           # Execution view components
│   │   ├── ImagingPanel.vue
│   │   ├── TelescopePanel.vue
│   │   ├── HardwarePanel.vue
│   │   ├── MessagesPanel.vue
│   │   └── InfoPanel.vue
│   └── processing/          # Processing view components
│       ├── ProcessingPanel.vue
│       ├── LibraryBrowser.vue
│       ├── FileBrowser.vue
│       └── ProcessingPreview.vue
├── stores/
│   ├── app.js              # UI state
│   ├── catalog.js          # Catalog data & search
│   ├── planning.js         # Observation plans
│   ├── execution.js        # Live telescope state
│   ├── processing.js       # Image processing
│   └── weather.js          # Weather data
├── services/
│   └── api.js              # API client layer
└── views/
    ├── DiscoveryView.vue   # Catalog browser
    ├── PlanningView.vue    # Observation planner
    ├── ExecutionView.vue   # Live execution monitor
    └── ProcessingView.vue  # Image processing
```

### Component Philosophy

- **Keep existing structure** - Work with current DiscoveryView, PlanningView, etc.
- **Add common components** - Create reusable BaseButton, BaseCard for consistency
- **Domain-specific folders** - Each view has its own component folder
- **Single responsibility** - Components do one thing well
- **Composition over inheritance** - Use composables for shared logic

---

## Theme System - Dark Scientific

### Color Palette

Replace all bright cyan (#00d9ff) with professional dark scientific palette:

```javascript
// tailwind.config.js
theme: {
  extend: {
    colors: {
      // Base colors - deep space aesthetic
      'astro-bg': '#0a0e1a',           // Deep space background
      'astro-surface': '#131720',       // Panel/card backgrounds
      'astro-elevated': '#1a1f2e',      // Elevated elements

      // Borders and dividers
      'astro-border': '#1e293b',        // Subtle borders
      'astro-border-focus': '#334155',  // Focused borders

      // Text hierarchy
      'astro-text': '#e2e8f0',          // Primary text
      'astro-text-muted': '#94a3b8',    // Secondary text
      'astro-text-dim': '#64748b',      // Tertiary text

      // Accent colors - minimal, purposeful
      'astro-accent': '#3b82f6',        // Primary actions (blue, not cyan)
      'astro-accent-hover': '#60a5fa',  // Hover states

      // Status colors
      'astro-success': '#10b981',       // Success states
      'astro-warning': '#f59e0b',       // Warnings
      'astro-error': '#ef4444',         // Errors
      'astro-info': '#06b6d4',          // Info (subtle cyan, sparingly)
    }
  }
}
```

### Design Principles

- **No bright cyan everywhere** - Remove all #00d9ff garish colors
- **Subtle, scientific** - Low contrast, easy on night-adapted eyes
- **Purposeful color** - Each color has semantic meaning
- **Consistent spacing** - Use Tailwind's 4px increment scale
- **Professional typography** - Clean, readable, hierarchical

### Typography Scale

- **Headers:** `text-xl` to `text-3xl`, `font-semibold`
- **Body:** `text-sm` to `text-base`, `font-normal`
- **Labels:** `text-xs`, `font-medium`, `text-astro-text-muted`
- **Monospace:** `font-mono` for coordinates, numbers, technical data

### Component Styling Patterns

```vue
<!-- Cards -->
<div class="bg-astro-surface border border-astro-border rounded-lg p-4">

<!-- Inputs -->
<input class="bg-astro-elevated border-astro-border focus:border-astro-accent rounded px-3 py-2">

<!-- Buttons -->
<button class="bg-astro-accent hover:bg-astro-accent-hover text-white rounded px-4 py-2">

<!-- Panels -->
<aside class="bg-astro-surface border-r border-astro-border">
```

---

## Data Flow & State Management

### Pinia Store Architecture

Each store follows this standard pattern:

```javascript
export const useXStore = defineStore('x', {
  state: () => ({
    items: [],           // Current data
    loading: false,      // Loading state
    error: null,         // Error messages
    // Domain-specific state
  }),

  getters: {
    // Computed values
  },

  actions: {
    async fetchData() {
      this.loading = true
      this.error = null
      try {
        const data = await api.get('/endpoint')
        this.items = data
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    }
  }
})
```

### Store Responsibilities

**catalog.js** - Restored from deleted code
- Search deep sky objects (12,400+ OpenNGC catalog)
- Filter by type, constellation, magnitude
- Pagination with intelligent prefetch
- Selected targets for planning
- Cache management for performance

**weather.js** - New store
- Current conditions (OpenWeatherMap API)
- Astronomical seeing (7Timer API)
- Forecast data (7-day)
- Weather scoring for target visibility
- Auto-refresh every 30 minutes

**planning.js** - Restored from deleted code
- Current observation plan
- Saved plans list
- Target scheduling algorithm
- Location/device settings
- Plan generation and export
- Field rotation calculations

**execution.js** - Restored from deleted code
- Telescope connection status (Seestar S50)
- Current position (RA/Dec/Alt/Az)
- Active target and imaging status
- Hardware state (mount, camera, focuser)
- Plan execution state
- Message log from telescope

**processing.js** - New/restored
- File browser state (filesystem navigation)
- Processing jobs queue
- Library browser (saved images)
- Preview image state
- Processing parameters

**app.js** - Existing UI state
- Sidebar collapsed state
- Right panel collapsed state
- Console collapsed state
- Panel collapse persistence

### Data Flow Pattern

1. Component dispatches action → Store
2. Store calls API via services layer → Backend
3. Backend returns data → Store updates state
4. Component reactively updates UI (no manual updates)

### API Service Layer

All backend calls go through `services/api.js`:

```javascript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Request interceptor - logging
api.interceptors.request.use(config => {
  console.log(`API: ${config.method.toUpperCase()} ${config.url}`)
  return config
})

// Response interceptor - error handling
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    // Retry transient failures automatically
    if (error.response?.status >= 500 && error.config.retryCount < 3) {
      error.config.retryCount = (error.config.retryCount || 0) + 1
      return api.request(error.config)
    }
    return Promise.reject(error)
  }
)

export const catalogApi = {
  search: (params) => api.get('/catalog/search', { params }),
  getTarget: (id) => api.get(`/targets/${id}`),
  getStats: () => api.get('/targets/stats')
}

// Similar exports for weather, planner, telescope, processing APIs
```

---

## View-Specific Features

### DiscoveryView (Catalog Browser)

**Stellarium-inspired: Clean, search-first interface**

#### Search-First Design (Top of View)
- Prominent search bar with autocomplete
- Quick filter badges (galaxy, nebula, cluster) visible by default
- Advanced filters in collapsible panel
- Search as you type with debounce

#### Main Catalog Grid
- Card-based responsive layout
- Object thumbnail images
- Essential info: name, type, magnitude, constellation
- Hover for quick preview
- Click for full details in right panel
- **Smooth infinite scroll** with prefetch (no pagination buttons)
- Dynamic page size based on viewport

#### Left Sidebar - Filters (Collapsible)
- Object type checkboxes (galaxy, nebula, cluster, etc.)
- Constellation dropdown with search
- Magnitude range slider (visual feedback)
- Sort options (name, magnitude, size, RA)
- "Clear All Filters" button
- Collapse button to maximize grid space

#### Right Panel - Object Details (Auto-opens on Selection)
- Full object information (RA/Dec, size, surface brightness)
- Visibility chart for tonight (altitude graph)
- Best viewing times
- Field rotation estimate for Seestar S50
- **"Add to Plan" prominent button**
- Related objects suggestions
- Auto-closes when deselected (minimalist approach)

**Restored Features:**
- All OpenNGC catalog search (12,400+ objects)
- Messier, NGC, IC catalog filtering
- Image display from backend `/api/images/targets/{id}`
- Coordinate formatting (RA in HMS, Dec in DMS)
- Constellation full name + common name
- Dynamic page size calculation based on viewport
- Prefetch cache for next page (smooth scrolling)

---

### PlanningView (Observation Planner)

**KStars/Ekos-inspired: Integrated planning workflow**

#### Left Sidebar - Planning Controls

**Session Settings** (Collapsible Panel)
- Date/time picker with "Tonight" quick button
- Location dropdown (saved profiles)
- Observation window (sunset to sunrise auto-calc)
- Timezone display

**Targets List** (Collapsible Panel)
- Draggable target cards from Discovery view
- Reorder by drag-and-drop priority
- Quick remove button (trash icon)
- Target count badge
- "Clear All" button
- Import from saved plan

**Constraints** (Collapsible Panel)
- Min/Max altitude sliders (30° - 70° default)
- "Avoid Moon" checkbox with phase display
- Weather threshold slider
- Field rotation limits for alt-az mount
- Setup time input (minutes)

**Actions** (Always Visible)
- **"Generate Plan" button** (primary action, prominent)
- Save plan dropdown
- Load plan dropdown
- Export format selector

#### Main Area - Generated Plan Visualization

**Timeline View** (Horizontal)
- Target blocks with timing (7:00 PM - 11:30 PM)
- Color-coded by priority/status
- Weather overlay (cloud cover percentage, seeing quality)
- Moon position indicator
- Click target block to see details

**Altitude Chart** (Below Timeline)
- All targets plotted vs time
- Horizon line at configured min altitude
- Moon altitude in dimmed line
- Current time marker (if viewing today)

**Plan Statistics Panel**
- Total targets: X
- Total imaging time: X hours Y minutes
- Estimated coverage: X% of night
- Weather score: Good/Fair/Poor

#### Right Panel - Plan Details & Export

**Export Options**
- seestar_alp CSV (recommended, default)
- Seestar Plan Mode JSON
- Human-readable text
- Full JSON export
- **QR code generator** for mobile workflow

**Plan Metadata**
- Plan name (editable)
- Creation date
- Location used
- Last modified

**Warnings**
- High field rotation targets (red warning)
- Moon interference (yellow warning)
- Weather concerns (orange warning)
- Targets below altitude limit

**Restored Features:**
- Greedy algorithm with urgency-based lookahead
- Field rotation calculation for alt-az mounts
- Weather scoring integration
- Target urgency (setting soon = higher priority)
- Multiple export formats
- QR code generation for sharing

---

### ExecutionView (Live Monitor & Session Control)

**KStars/Ekos-inspired: Unified session interface with N.I.N.A.-style modularity**

#### Left Sidebar - Session Control Panels (All Collapsible)

**Panel 1: Plan Execution** (Primary Workflow)
- "Load Plan" dropdown (saved plans)
- Plan progress: "Target 3 of 10"
- Current target highlight with thumbnail
- "Execute Plan" button (green, primary)
- "Pause" / "Resume" buttons
- "Stop Execution" button (red)
- "Skip to Next Target" button
- Estimated completion time
- *Collapsed by default if no plan loaded*
- *Expands automatically when plan loaded*

**Panel 2: Telescope Connection**
- IP address input field
- "Connect" / "Disconnect" button
- Connection status indicator (green/red dot)
- Last connected timestamp
- *Auto-expands when not connected*
- *Collapses when connected and plan running*

**Panel 3: Imaging Controls**
- "Start" / "Stop" capture buttons
- Exposure time slider (1s - 10s for Seestar)
- Frame count input
- Current frame progress bar
- Dither settings (if supported)
- *Only enabled when telescope connected*

**Panel 4: Hardware Status**
- Mount status (Parked/Tracking/Slewing)
- Camera temperature (°C)
- Focuser position
- Battery level (if available)
- *Collapsible to save space*

**Panel 5: Messages**
- Recent telescope messages (last 5)
- Timestamp + message preview
- "View All Messages" button → expands console
- Auto-scroll toggle
- *Shows errors in red, warnings in yellow*

#### Main Area - Live Monitoring

**Large Current Target Display**
- Target name (e.g., "M31 - Andromeda Galaxy")
- Target thumbnail image
- Object type badge
- RA/Dec coordinates (live update every second)
- Alt/Az position (live update)
- **Progress ring** (current target % complete)
- Time on target / Total time

**Sky Chart** (Below Target Display)
- Current telescope pointing (crosshair)
- Planned targets visible as dots
- Field of view indicator (1.27° × 0.71° for Seestar)
- Horizon line
- Cardinal directions
- Field rotation indicator (degrees/hour)
- *Updates every 10 seconds*

**Next Target Countdown** (If Plan Running)
- "Next: M42 in 23 minutes"
- Next target thumbnail preview
- Transition time estimate

#### Right Panel - Session Status

**Weather Conditions** (Live Updates)
- Current cloud cover percentage
- Temperature, humidity, wind
- Seeing quality (arcseconds)
- Transparency rating
- "Refresh" button
- Last update timestamp
- *Auto-refresh every 5 minutes*

**Seeing Quality Graph**
- Last 4 hours of seeing data
- Forecast for next 4 hours (7Timer)
- Current marker

**Altitude Chart**
- Current target altitude vs time
- Next target altitude vs time (if plan running)
- Configured altitude limits (shaded)
- Current time marker

**Session Timeline** (If Plan Running)
- Completed targets (green checkmarks)
- Current target (highlighted)
- Upcoming targets (gray)
- Skipped targets (yellow warning)
- Failed targets (red X)

#### Bottom Console (Collapsible)

**Full Message Log**
- Timestamp | Source | Message format
- Color-coded by severity (info/warning/error)
- Search/filter messages
- Auto-scroll toggle
- "Clear Log" button
- Export log to file
- *Collapsed by default, expands on error*

**Key Workflow:**
1. User loads saved plan OR manually selects target
2. User connects telescope (IP input)
3. If plan loaded: Click "Execute Plan" → automated session
4. If manual: Use imaging controls to capture
5. Monitor live in main area
6. Console shows all telescope messages

**Restored Features:**
- Seestar S50 direct connection via IP
- Live RA/Dec/Alt/Az position updates
- Hardware status monitoring
- Message log from telescope API
- Plan execution automation
- Manual imaging control fallback

---

### ProcessingView (Image Processing)

**N.I.N.A.-inspired: Flexible workspace**

#### Left Panel - Dual-Mode Browser (Tabs)

**Tab 1: File Browser**
- Directory tree (collapsible folders)
- FITS file list with thumbnails
- Multi-select for stacking (checkboxes)
- File info tooltip (date, size, exposure)
- Search/filter files
- "Select All" / "Deselect All" buttons

**Tab 2: Library Browser**
- Processed images gallery grid
- Filter by date range
- Filter by target name
- Sort by (date, name, rating)
- Thumbnail view with metadata
- Click to preview

#### Main Area - Preview & Processing

**Large Image Preview**
- Full image display
- Zoom controls (toolbar overlay, minimal)
- Pan with mouse drag
- Fit to screen / 100% / 200% buttons
- *Clean, minimal UI - focus on image*

**Histogram** (Collapsible Overlay)
- RGB histogram graph
- Clip indicators (left/right)
- Toggle on/off with keyboard shortcut
- Semi-transparent overlay

**Before/After Split View**
- Toggle to compare original vs processed
- Draggable split line
- Labels: "Original" | "Processed"

#### Right Panel - Processing Tools (Collapsible Sections)

**Stack Images Section**
- Selected file count badge
- Stacking method dropdown:
  - Sigma-clipped mean (default)
  - Median
  - Average
  - Maximum
- GPU acceleration toggle (if available)
- "Stack Now" button (primary action)

**Stretch & Adjust Section**
- "Auto-Stretch" button (quick action)
- Manual stretch sliders (if needed):
  - Black point
  - White point
  - Gamma
- Histogram clip controls
- "Reset to Original" button

**Export Section**
- Output format dropdown (FITS, TIFF, PNG, JPG)
- Quality slider (for JPG)
- Color space (RGB, sRGB)
- Bit depth selector
- Filename input
- **"Save" button** (green, prominent)

#### Bottom - Processing Queue (Collapsible)

**Active Jobs**
- Job name (e.g., "Stacking 47 M31 frames")
- Progress bar with percentage
- Estimated time remaining
- "Cancel" button

**Job History** (Last 10)
- Completed jobs (green checkmark)
- Failed jobs (red X with error)
- Click to re-open result

**Queue Actions**
- "Clear Completed" button
- "Pause Queue" toggle

**Restored Features:**
- CUDA-accelerated stacking (CuPy)
- Sigma-clipped mean for outlier rejection
- Auto-stretch matching Seestar output
- FITS file handling
- File browser with directory navigation
- Processing job queue system
- Library of processed images

---

## Error Handling & Loading States

### Loading State Philosophy

**Skeleton Loaders** (Preferred over spinners)
- Catalog grid: Show card skeletons in layout position
- Charts/graphs: Show axis and grid while data loads
- Tables: Show row outlines with shimmer animation
- Images: Show placeholder with subtle pulse

**Progressive Loading:**
- Show cached/stale data immediately with "Refreshing..." indicator
- Update in background when fresh data arrives
- Never show blank screen while waiting
- Subtle indicator difference: "Loading" vs "Refreshing"

**Example:**
```vue
<!-- Bad: Spinner blocks entire view -->
<div v-if="loading" class="spinner-overlay">
  <LoadingSpinner />
</div>

<!-- Good: Skeleton maintains layout, shows structure -->
<div class="catalog-grid">
  <SkeletonCard v-for="i in 12" :key="i" v-if="catalogStore.loading" />
  <CatalogCard v-for="item in catalogStore.items" :key="item.id" v-else />
</div>

<!-- Better: Show stale data while refreshing -->
<div class="catalog-grid">
  <div v-if="catalogStore.loading && !catalogStore.items.length">
    <SkeletonCard v-for="i in 12" :key="i" />
  </div>
  <div v-else>
    <div v-if="catalogStore.loading" class="refreshing-indicator">
      Refreshing...
    </div>
    <CatalogCard v-for="item in catalogStore.items" :key="item.id" />
  </div>
</div>
```

### Error Handling Tiers

**Tier 1: Inline Errors** (Recoverable, user can retry)
- API call fails → Show error message in component with "Retry" button
- Image fails to load → Show placeholder with "Reload" icon
- Search returns no results → Helpful empty state
- Example: "Failed to load catalog. [Retry]"

**Tier 2: Toast Notifications** (Temporary, informational)
- Background tasks complete: "Plan generated successfully ✓"
- Non-critical warnings: "Weather data is 2 hours old"
- Auto-dismiss after 5 seconds
- Stack multiple toasts (max 3 visible)
- Click to dismiss early

**Tier 3: Modal Dialogs** (Critical, requires acknowledgment)
- Telescope connection lost during execution
- Plan execution failed due to hardware error
- Destructive actions: "Delete saved plan?"
- User must click "OK" / "Cancel" to proceed
- Cannot be dismissed by clicking outside

### Error Message Guidelines

**Clear Cause + Clear Action:**
```
❌ Bad:  "Error 500"
✅ Good: "Server error occurred. Please try again."

❌ Bad:  "Connection failed"
✅ Good: "Failed to connect to telescope at 192.168.1.100.
         Check IP address and network connection."

❌ Bad:  "Invalid input"
✅ Good: "Latitude must be between -90° and 90°"
```

**No Jargon:**
- Avoid: "HTTP 500", "ECONNREFUSED", "Promise rejected"
- Use: "Server error", "Connection refused", "Request failed"

**Helpful Context:**
- Link to documentation for complex issues
- Show last successful state: "Last weather update: 2 hours ago"
- Suggest next steps: "Try reconnecting the telescope"

### Offline/Degraded Mode

**Weather API Down:**
- Show last cached weather data
- Display timestamp: "Weather data from 2 hours ago"
- Banner: "Unable to fetch new weather data"

**Catalog API Slow:**
- Use prefetched cached data
- Show indicator: "Loading newer results..."
- Don't block user interaction

**Backend Unreachable:**
- Top banner: "Working offline - some features unavailable"
- Disable features requiring backend (plan generation, telescope control)
- Keep working features enabled (cached catalog browsing)

---

## Testing Strategy

### Test Philosophy

**Test what matters:** User workflows, not implementation details

### Unit Tests (Vitest)

Fast tests run on every file save during development.

**Focus on Stores (Business Logic):**
```javascript
describe('useCatalogStore', () => {
  it('fetches catalog data from API', async () => {
    const store = useCatalogStore()
    await store.fetchCatalogData()
    expect(store.items.length).toBeGreaterThan(0)
  })

  it('applies filters correctly', () => {
    const store = useCatalogStore()
    store.applyFilters({ type: 'galaxy' })
    expect(store.filters.type).toBe('galaxy')
  })

  it('handles pagination', () => {
    const store = useCatalogStore()
    expect(store.currentPage).toBe(1)
    store.setPage(2)
    expect(store.currentPage).toBe(2)
  })

  it('caches results for performance', async () => {
    const store = useCatalogStore()
    await store.fetchCatalogData()
    expect(store.prefetchCache.size).toBeGreaterThan(0)
  })

  it('manages error states', async () => {
    // Mock API to fail
    await store.fetchCatalogData()
    expect(store.error).toBeTruthy()
  })
})
```

### Component Tests (Vitest + Vue Test Utils)

Test user interactions, not implementation details.

```javascript
describe('CatalogSearchPanel', () => {
  it('allows user to type in search box', async () => {
    const wrapper = mount(CatalogSearchPanel)
    const input = wrapper.find('input[type="search"]')
    await input.setValue('M31')
    expect(input.element.value).toBe('M31')
  })

  it('triggers catalog fetch when clicking Search', async () => {
    const wrapper = mount(CatalogSearchPanel)
    const catalogStore = useCatalogStore()
    const spy = vi.spyOn(catalogStore, 'fetchCatalogData')

    await wrapper.find('button').trigger('click')
    expect(spy).toHaveBeenCalled()
  })

  it('updates catalog when filters change', async () => {
    const wrapper = mount(CatalogSearchPanel)
    const select = wrapper.find('select[name="type"]')
    await select.setValue('galaxy')

    const catalogStore = useCatalogStore()
    expect(catalogStore.filters.type).toBe('galaxy')
  })
})
```

### Integration Tests (Playwright)

Test complete user workflows end-to-end. Slower, run before commits.

```javascript
test('Discovery to Planning workflow', async ({ page }) => {
  // Navigate to Discovery
  await page.goto('/app')

  // Search for M31
  await page.fill('input[type="search"]', 'M31')
  await page.click('button:text("Search")')

  // Wait for results
  await page.waitForSelector('.catalog-card')

  // Add M31 to plan
  await page.click('.catalog-card:first-child button:text("Add to Plan")')

  // Navigate to Planning view
  await page.click('nav a:text("Plan")')

  // Verify M31 appears in targets list
  await expect(page.locator('.targets-list')).toContainText('M31')

  // Generate plan
  await page.click('button:text("Generate Plan")')

  // Verify plan shows M31 with timing
  await expect(page.locator('.plan-timeline')).toContainText('M31')
})

test('Plan execution workflow', async ({ page }) => {
  await page.goto('/app/execute')

  // Load saved plan
  await page.selectOption('select[name="plan"]', 'Test Plan')

  // Connect telescope (mock IP)
  await page.fill('input[name="telescope-ip"]', '192.168.1.100')
  await page.click('button:text("Connect")')

  // Wait for connection
  await expect(page.locator('.connection-status')).toHaveText('Connected')

  // Execute plan
  await page.click('button:text("Execute Plan")')

  // Verify first target begins
  await expect(page.locator('.current-target')).toBeVisible()

  // Verify console shows messages
  await expect(page.locator('.console')).toContainText('Slewing to')
})
```

### Test Coverage Goals

- **Stores:** 90%+ (critical business logic)
- **Components:** 70%+ (focus on interactive components)
- **Views:** 60%+ (main workflows covered)
- **Overall:** 75%+

### Testing Commands

```bash
npm test              # Run all tests in watch mode
npm run test:unit     # Unit tests only
npm run test:e2e      # Integration tests (Playwright)
npm run test:coverage # Generate coverage report
npm run test:ci       # Run all tests once (for CI)
```

### CI/CD Integration

- All tests run automatically on pull request
- Block merge if tests fail or coverage drops
- Coverage report posted as PR comment
- Visual regression screenshots uploaded as artifacts

### Manual Testing Checklist

Before each release, manually verify:

- [ ] All views load without console errors
- [ ] Catalog search returns results
- [ ] Filters work correctly
- [ ] Weather data displays
- [ ] Telescope connection works (if hardware available)
- [ ] Plan generation succeeds
- [ ] Plan execution starts (if hardware available)
- [ ] Image processing completes
- [ ] All panels collapse/expand smoothly
- [ ] Responsive layout works on tablet
- [ ] No console errors in browser DevTools
- [ ] All API endpoints respond correctly

---

## Implementation Approach: Parallel Track

### Track 1: Theme System (Quick Win)

**Goal:** Replace bright cyan with dark scientific palette

**Tasks:**
1. Update `tailwind.config.js` with astro-* color palette
2. Create `BaseButton.vue` component using new colors
3. Create `BaseCard.vue` component
4. Create `BaseInput.vue` component
5. Update all existing components to use new Tailwind classes
6. Remove all hardcoded `#00d9ff` colors
7. Test visual consistency across all views

**Success Criteria:**
- No bright cyan visible anywhere
- All components use astro-* colors
- Professional, subtle dark aesthetic

---

### Track 2: Data Loading (Critical Fix)

**Goal:** Restore data loading in all stores

**Tasks:**
1. Fix catalog store API integration
2. Restore weather store with OpenWeatherMap + 7Timer
3. Fix planning store data loading
4. Fix execution store telescope connection
5. Fix processing store file browsing
6. Add proper error handling to all stores
7. Add loading states to all stores

**Success Criteria:**
- Catalog search returns results
- Weather data displays
- Plans load and save
- Telescope status updates
- Processing files visible

---

### Track 3: Feature Restoration (Progressive)

**Goal:** Restore all features from deleted vanilla JS

**Phase 1: Discovery View**
- Restore search functionality
- Restore filtering (type, constellation, magnitude)
- Restore pagination with prefetch
- Add "Add to Plan" functionality
- Object details panel

**Phase 2: Planning View**
- Restore target list from Discovery
- Restore plan generation algorithm
- Restore export formats (seestar_alp, JSON, QR)
- Restore field rotation calculations
- Weather integration in planning

**Phase 3: Execution View**
- Restore telescope connection (Seestar S50)
- Restore plan execution automation
- Restore live position updates
- Restore imaging controls
- Restore hardware status monitoring
- Message console

**Phase 4: Processing View**
- Restore file browser
- Restore CUDA stacking
- Restore auto-stretch
- Restore processing queue
- Library browser

**Success Criteria:**
- All original features working
- Modern Vue 3 patterns used
- No vanilla JS legacy code
- Clean component architecture

---

## Success Metrics

### Professional Aesthetic
- ✅ No bright cyan colors visible
- ✅ Dark scientific palette consistently applied
- ✅ All components use Tailwind astro-* classes
- ✅ Typography hierarchy clear and readable
- ✅ Spacing consistent (4px increments)

### Functionality Restored
- ✅ Catalog search returns 12,400+ objects
- ✅ Filters work (type, constellation, magnitude)
- ✅ Weather data displays (current + forecast)
- ✅ Plans generate with proper scheduling
- ✅ Telescope connects and reports position
- ✅ Image processing stacks and stretches
- ✅ All exports work (CSV, JSON, QR)

### User Experience
- ✅ All panels collapsible
- ✅ Loading states smooth (skeletons, not spinners)
- ✅ Error messages helpful with retry
- ✅ No console errors
- ✅ Responsive on desktop (primary target)
- ✅ Keyboard shortcuts work

### Code Quality
- ✅ Test coverage > 75%
- ✅ All tests passing
- ✅ Modern Vue 3 patterns (Composition API)
- ✅ No vanilla JS legacy code
- ✅ Clean component architecture
- ✅ Stores follow standard pattern

---

## References

### Research Sources
- [Stellarium](https://stellarium.org/) - 9,400 GitHub stars, minimalist planetarium UI
- [KStars/Ekos](https://apps.kde.org/kstars/) - 259 GitHub stars, integrated astrophotography suite
- [N.I.N.A.](https://nighttime-imaging.eu/) - 137 GitHub stars, modular automation platform

### Original Documentation
- Phase 0 implementation plan: `docs/plans/2026-02-12-phase0-vue-setup.md`
- Deleted vanilla JS files (reference for features to restore)

### Backend APIs
- Catalog: `/api/catalog/search`, `/api/targets/{id}`
- Weather: `/api/weather/current`, `/api/weather/forecast`, `/api/astronomy/weather/7timer`
- Planner: `/api/plan`, `/api/plans`, `/api/plans/{id}/export/{format}`
- Telescope: `/api/telescope/connect`, `/api/telescope/status`, `/api/telescope/slew`
- Processing: `/api/process/stack-and-stretch`, `/api/process/auto`, `/api/process/jobs/{id}`

---

## Next Steps

After design approval:
1. Create detailed implementation plan using `superpowers:writing-plans`
2. Execute plan using `superpowers:executing-plans` or `superpowers:subagent-driven-development`
3. Implement Track 1 (Theme) first for quick visual win
4. Implement Track 2 (Data) to fix critical bugs
5. Implement Track 3 (Features) progressively by view
6. Test thoroughly at each phase
7. Deploy to production when all tracks complete

---

**Design Status:** ✅ Approved
**Ready for Implementation:** Yes
**Next Skill:** `superpowers:writing-plans`
