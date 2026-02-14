# Astronomus Lumina-Style Redesign

**Date:** 2026-02-14
**Goal:** Rebuild astronomus Vue app to match Lumina's clean aesthetic while preserving astronomy features and business logic

---

## 1. Architecture Overview

### Core Principle
Copy Lumina's visual shell, preserve astronomus business logic.

### What We Copy from Lumina
- Layout components (PanelContainer with resizable panels)
- Header structure (centered nav tabs, search, controls)
- Color system (Tailwind gray-900/800/700, blue-500)
- Spacing patterns (generous padding, clean borders)
- Component patterns (inline Tailwind, no base component abstraction)

### What We Keep from Current astronomus
- All Pinia stores (catalog, planning, execution, processing, weather)
- API integration layer
- Business logic and data flow
- Router structure (4 main views)
- All tests (27 passing tests)

### What We Replace
- tailwind.config.js - remove ALL custom astro-* colors
- App.vue layout - use Lumina's structure
- All view components - rebuild with Lumina styling
- AppHeader, AppSidebar - replace with Lumina-style versions
- Remove base components (BaseButton, BaseCard) - use inline Tailwind

### Result
Lumina's clean aesthetic applied to astronomy features.

---

## 2. Color System (Tailwind Defaults Only)

### Remove from tailwind.config.js
```javascript
// DELETE all custom colors:
colors: {
  'astro-bg': '#0a0e1a',
  'astro-surface': '#131720',
  'astro-elevated': '#1a1f2e',
  'astro-border': '#1e293b',
  'astro-text': '#e2e8f0',
  'astro-text-muted': '#94a3b8',
  'astro-text-dim': '#64748b',
  'astro-accent': '#3b82f6',
  'astro-success': '#10b981',
  'astro-error': '#ef4444',
}
```

### Use Standard Tailwind Instead
- **Backgrounds:** `bg-gray-950` (darkest), `bg-gray-900` (main), `bg-gray-800` (elevated)
- **Borders:** `border-gray-800`, `border-gray-700`
- **Text:** `text-gray-100` (primary), `text-gray-400` (muted), `text-gray-500` (dim)
- **Accent:** `text-blue-500`, `bg-blue-600`, `hover:bg-blue-700`
- **Status:** `text-green-500` (success), `text-red-500` (error), `text-yellow-500` (warning)

### Example Transformation
```vue
<!-- OLD (custom) -->
<div class="bg-astro-surface border-astro-border text-astro-text">

<!-- NEW (Tailwind defaults) -->
<div class="bg-gray-900 border-gray-800 text-gray-100">
```

This matches Lumina exactly - simple, clean, standard Tailwind palette.

---

## 3. Layout Structure

### PanelContainer Component
Copy Lumina's PanelContainer but adjust sizing for astronomy:

```vue
<template>
  <div class="panel-container" :class="layoutClasses">
    <!-- Left Panel: Navigation + Filters -->
    <aside class="left-panel overflow-y-auto border-r border-gray-800 bg-gray-900">
      <slot name="left" />
    </aside>

    <!-- Main Content: Primary view area -->
    <main class="main-content overflow-hidden bg-gray-950">
      <slot name="main" />
    </main>

    <!-- Right Panel: Details/Info -->
    <aside class="right-panel overflow-y-auto border-l border-gray-800 bg-gray-900">
      <slot name="right" />
    </aside>

    <!-- Console/Logs: Telescope messages, processing logs -->
    <footer class="console border-t border-gray-800 bg-gray-900">
      <slot name="console" />
    </footer>
  </div>
</template>
```

### Panel Sizing (Astronomy-Optimized)
- **Left:** 300px max (wider for detailed filters)
- **Main:** 1fr (flexible, takes remaining space)
- **Right:** 350px max (wider for target details, coordinates)
- **Console:** 160px height (taller for telescope logs)

### Header Structure (Copy Lumina)
- **Center:** Navigation tabs (Discovery | Planning | Execution | Processing)
- **Left:** Logo/app name
- **Right:** Weather widget, settings, user icon

### Future Enhancement (Phase 2)
- Add drag handles for user-adjustable panel widths
- Save panel sizes to localStorage
- Double-click to reset to defaults

---

## 4. Component Organization

### New Directory Structure
```
src/
├── components/
│   ├── layout/
│   │   ├── PanelContainer.vue       (copied from Lumina)
│   │   ├── PanelToggle.vue          (toggle buttons)
│   │   ├── LeftPanel.vue            (wrapper with toggle)
│   │   └── RightPanel.vue           (wrapper with toggle)
│   ├── discovery/
│   │   ├── CatalogGrid.vue          (rebuilt with Lumina styling)
│   │   ├── CatalogCard.vue          (individual target card)
│   │   └── SearchFilters.vue        (type, constellation, magnitude)
│   ├── planning/
│   │   ├── PlanningControls.vue     (date, location, constraints)
│   │   ├── TargetList.vue           (selected targets)
│   │   └── PlanDisplay.vue          (generated plan visualization)
│   ├── execution/
│   │   ├── TelescopeControls.vue    (connect, position, imaging)
│   │   ├── PlanExecutor.vue         (run saved plans)
│   │   ├── HardwareStatus.vue       (telescope state)
│   │   └── MessageLog.vue           (telescope messages)
│   ├── processing/
│   │   ├── FileBrowser.vue          (navigate /data directory)
│   │   ├── ProcessingControls.vue   (stack, stretch options)
│   │   └── JobMonitor.vue           (processing job status)
│   └── shared/
│       ├── AppHeader.vue            (rebuilt with Lumina style)
│       ├── NavigationSidebar.vue    (left sidebar nav)
│       ├── WeatherWidget.vue        (keep existing)
│       └── EmptyState.vue           (reusable empty state)
├── views/
│   ├── DiscoveryView.vue
│   ├── PlanningView.vue
│   ├── ExecutionView.vue
│   └── ProcessingView.vue
├── stores/ (KEEP ALL - no changes)
│   ├── catalog.js
│   ├── planning.js
│   ├── execution.js
│   ├── processing.js
│   └── weather.js
```

### Key Changes
- ✅ Add `layout/` directory (from Lumina)
- ✅ Organize by feature (discovery/, planning/, execution/, processing/)
- ✅ Remove `common/` (inline Tailwind instead of base components)
- ✅ Add `shared/` for app-wide components
- ✅ Keep all stores unchanged

### Favicon
- ✅ Keep existing `frontend/favicon.svg` (telescope emoji 🔭)
- ✅ Update `vue-app/index.html` to reference: `<link rel="icon" href="/favicon.svg" />`

---

## 5. Views Implementation Pattern

Each view follows this pattern (using Discovery as example):

```vue
<template>
  <PanelContainer
    :left-panel-visible="true"
    :right-panel-visible="true"
    :console-visible="false"
  >
    <!-- Left: Filters -->
    <template #left>
      <div class="p-4 border-b border-gray-800">
        <h3 class="text-sm font-semibold text-gray-400 uppercase">Search</h3>
      </div>
      <SearchFilters />
    </template>

    <!-- Main: Catalog Grid -->
    <template #main>
      <!-- View Header (Lumina pattern) -->
      <div class="bg-gray-900/50 border-b border-gray-800 px-4 py-3">
        <h2 class="text-lg font-semibold text-gray-200">Discovery</h2>
        <p class="text-sm text-gray-500">
          {{ catalogStore.totalItems }} objects
        </p>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-hidden">
        <CatalogGrid />
      </div>
    </template>

    <!-- Right: Target Details -->
    <template #right>
      <TargetDetails />
    </template>
  </PanelContainer>
</template>
```

### Styling Principles (Lumina Style)
- Use inline Tailwind classes
- `bg-gray-900/50` for subtle headers
- `text-gray-200` for headings, `text-gray-500` for counts/meta
- `border-gray-800` for all borders
- `px-4 py-3` for consistent padding
- No custom components - direct HTML + Tailwind

---

## 6. Data Flow (Preserve Existing Stores)

### Keep All Existing Pinia Stores Unchanged
- ✅ `catalog.js` - search, filtering, pagination
- ✅ `planning.js` - plan generation, saving
- ✅ `execution.js` - telescope control, position tracking
- ✅ `processing.js` - file browsing, job monitoring
- ✅ `weather.js` - weather data and scoring

### Only Change: How Components Consume Stores

**OLD pattern (with base components):**
```vue
<BaseButton variant="primary" @click="catalogStore.addSelectedTarget(item)">
  Add to Plan
</BaseButton>
```

**NEW pattern (Lumina style - inline Tailwind):**
```vue
<button
  @click="catalogStore.addSelectedTarget(item)"
  class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
>
  Add to Plan
</button>
```

### Store Usage Stays Identical
- Same computed properties
- Same actions/methods
- Same reactive state
- All 27 existing tests still pass

### API Integration Unchanged
- All `/api/catalog/*`, `/api/plan/*`, `/api/process/*` endpoints stay the same
- Backend doesn't need any changes
- Only the UI presentation layer changes

---

## Implementation Strategy

1. **Phase 1: Foundation**
   - Update tailwind.config.js (remove custom colors)
   - Copy Lumina's layout components
   - Rebuild App.vue with new structure
   - Update AppHeader with Lumina styling

2. **Phase 2: Views (One at a Time)**
   - Rebuild DiscoveryView
   - Rebuild PlanningView
   - Rebuild ExecutionView
   - Rebuild ProcessingView

3. **Phase 3: Polish**
   - Add empty states
   - Loading states with Lumina styling
   - Error states
   - Verify all 27 tests pass

4. **Phase 4: Enhancement (Future)**
   - Resizable panels with drag handles
   - Panel size persistence
   - Additional Lumina patterns as needed

---

## Success Criteria

- ✅ Matches Lumina's clean, spacious aesthetic
- ✅ Uses only Tailwind default colors (no custom colors)
- ✅ All 4 features working (Discovery, Planning, Execution, Processing)
- ✅ All 27 tests passing
- ✅ All Pinia stores unchanged
- ✅ Backend API unchanged
- ✅ Telescope favicon preserved
- ✅ Astronomy-optimized panel sizing (300px/350px/160px)
