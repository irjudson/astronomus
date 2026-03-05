# Lumina-Style Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild astronomus Vue app to match Lumina's clean aesthetic (Tailwind defaults, spacious layout, inline styles)

**Architecture:** Copy Lumina's layout components and styling patterns, replace all custom astro-* colors with Tailwind defaults, rebuild views with Lumina's inline Tailwind approach while preserving existing Pinia stores and business logic.

**Tech Stack:** Vue 3, Tailwind CSS v4 (defaults only), Pinia stores (unchanged), Vite

---

## Task 1: Update Tailwind Config (Remove Custom Colors)

**Files:**
- Modify: `frontend/vue-app/tailwind.config.js`

**Step 1: Remove all custom colors**

Replace entire `tailwind.config.js` with Lumina's minimal config:

```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**Step 2: Verify Tailwind rebuild**

Run: `npm run dev` in `frontend/vue-app/`
Expected: No build errors, Tailwind compiles with default colors only

**Step 3: Commit**

```bash
git add frontend/vue-app/tailwind.config.js
git commit -m "refactor: remove custom colors, use Tailwind defaults"
```

---

## Task 2: Copy PanelContainer from Lumina

**Files:**
- Create: `frontend/vue-app/src/components/layout/PanelContainer.vue`

**Step 1: Create layout directory**

```bash
mkdir -p frontend/vue-app/src/components/layout
```

**Step 2: Create PanelContainer component**

Create `frontend/vue-app/src/components/layout/PanelContainer.vue`:

```vue
<template>
  <div
    class="panel-container"
    :class="layoutClasses"
  >
    <!-- Left Panel -->
    <aside class="left-panel overflow-y-auto border-r border-gray-800 bg-gray-900">
      <slot name="left" />
    </aside>

    <!-- Main Content -->
    <main class="main-content overflow-hidden bg-gray-950">
      <slot name="main" />
    </main>

    <!-- Right Panel -->
    <aside class="right-panel overflow-y-auto border-l border-gray-800 bg-gray-900">
      <slot name="right" />
    </aside>

    <!-- Console/Logs -->
    <footer class="console border-t border-gray-800 bg-gray-900">
      <slot name="console" />
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  leftPanelVisible: {
    type: Boolean,
    default: true
  },
  rightPanelVisible: {
    type: Boolean,
    default: true
  },
  consoleVisible: {
    type: Boolean,
    default: false
  }
})

const layoutClasses = computed(() => ({
  'left-collapsed': !props.leftPanelVisible,
  'right-collapsed': !props.rightPanelVisible,
  'console-collapsed': !props.consoleVisible
}))
</script>

<style scoped>
.panel-container {
  display: grid;
  width: 100%;
  height: 100%;
  grid-template-columns: minmax(0, 300px) 1fr minmax(0, 350px);
  grid-template-rows: 1fr 160px;
  grid-template-areas:
    "left main right"
    "console console console";
  transition: grid-template-columns 300ms ease-in-out, grid-template-rows 300ms ease-in-out;
}

.left-panel {
  grid-area: left;
  min-width: 0;
}

.main-content {
  grid-area: main;
  min-width: 0;
}

.right-panel {
  grid-area: right;
  min-width: 0;
}

.console {
  grid-area: console;
  min-height: 0;
}

/* Collapsed states */
.panel-container.left-collapsed {
  grid-template-columns: 0 1fr minmax(0, 350px);
}

.panel-container.left-collapsed .left-panel {
  overflow: hidden;
  visibility: hidden;
  border-right: none;
}

.panel-container.right-collapsed {
  grid-template-columns: minmax(0, 300px) 1fr 0;
}

.panel-container.right-collapsed .right-panel {
  overflow: hidden;
  visibility: hidden;
  border-left: none;
}

.panel-container.left-collapsed.right-collapsed {
  grid-template-columns: 0 1fr 0;
}

.panel-container.console-collapsed {
  grid-template-rows: 1fr 0;
}

.panel-container.console-collapsed .console {
  overflow: hidden;
  visibility: hidden;
  border-top: none;
}
</style>
```

**Step 3: Commit**

```bash
git add frontend/vue-app/src/components/layout/
git commit -m "feat: add PanelContainer layout component from Lumina"
```

---

## Task 3: Add Panel Toggle Components

**Files:**
- Create: `frontend/vue-app/src/components/layout/PanelToggle.vue`

**Step 1: Create PanelToggle component**

Create `frontend/vue-app/src/components/layout/PanelToggle.vue`:

```vue
<template>
  <button
    @click="$emit('toggle')"
    class="p-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md transition-colors text-gray-400 hover:text-gray-200"
    :title="collapsed ? `Show ${position} panel` : `Hide ${position} panel`"
  >
    <ChevronLeftIcon v-if="position === 'left' && !collapsed" class="w-4 h-4" />
    <ChevronRightIcon v-if="position === 'left' && collapsed" class="w-4 h-4" />
    <ChevronRightIcon v-if="position === 'right' && !collapsed" class="w-4 h-4" />
    <ChevronLeftIcon v-if="position === 'right' && collapsed" class="w-4 h-4" />
    <ChevronDownIcon v-if="position === 'bottom' && !collapsed" class="w-4 h-4" />
    <ChevronUpIcon v-if="position === 'bottom' && collapsed" class="w-4 h-4" />
  </button>
</template>

<script setup>
import { ChevronLeftIcon, ChevronRightIcon, ChevronUpIcon, ChevronDownIcon } from 'lucide-vue-next'

defineProps({
  position: {
    type: String,
    required: true,
    validator: (value) => ['left', 'right', 'bottom'].includes(value)
  },
  collapsed: {
    type: Boolean,
    default: false
  }
})

defineEmits(['toggle'])
</script>
```

**Step 2: Commit**

```bash
git add frontend/vue-app/src/components/layout/PanelToggle.vue
git commit -m "feat: add PanelToggle component for collapsible panels"
```

---

## Task 4: Rebuild App.vue with Lumina Layout

**Files:**
- Modify: `frontend/vue-app/src/App.vue`

**Step 1: Replace App.vue**

Replace entire content with Lumina-style structure:

```vue
<template>
  <div class="flex flex-col h-screen bg-gray-950 text-gray-100">
    <!-- Global Header -->
    <AppHeader />

    <!-- Main Content Area -->
    <main class="flex-1 overflow-hidden">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'
import AppHeader from '@/components/shared/AppHeader.vue'
</script>

<style scoped>
/* No custom styles - use Tailwind */
</style>
```

**Step 2: Verify structure**

Run: `npm run dev`
Expected: App renders with header (will update next)

**Step 3: Commit**

```bash
git add frontend/vue-app/src/App.vue
git commit -m "refactor: simplify App.vue layout to match Lumina"
```

---

## Task 5: Create shared/ Directory and Rebuild AppHeader

**Files:**
- Create: `frontend/vue-app/src/components/shared/AppHeader.vue`
- Delete: `frontend/vue-app/src/components/AppHeader.vue` (old location)

**Step 1: Create shared directory**

```bash
mkdir -p frontend/vue-app/src/components/shared
```

**Step 2: Create new AppHeader**

Create `frontend/vue-app/src/components/shared/AppHeader.vue`:

```vue
<template>
  <header class="flex items-center justify-between px-4 py-2 border-b border-gray-800 bg-gray-900 shrink-0 z-10">
    <!-- Left: Logo -->
    <div class="flex items-center space-x-4">
      <div class="font-bold text-xl tracking-tight text-blue-500 flex items-center gap-2">
        <span>🔭</span>
        <span>Astronomus</span>
      </div>
    </div>

    <!-- Center: Navigation -->
    <nav class="flex space-x-1 bg-gray-800 p-1 rounded-lg">
      <router-link
        to="/"
        class="px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-200"
        :class="$route.path === '/' ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'"
      >
        Discovery
      </router-link>
      <router-link
        to="/plan"
        class="px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-200"
        :class="$route.path.startsWith('/plan') ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'"
      >
        Planning
      </router-link>
      <router-link
        to="/execute"
        class="px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-200"
        :class="$route.path.startsWith('/execute') ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'"
      >
        Execution
      </router-link>
      <router-link
        to="/process"
        class="px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-200"
        :class="$route.path.startsWith('/process') ? 'bg-gray-700 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200 hover:bg-gray-700/50'"
      >
        Processing
      </router-link>
    </nav>

    <!-- Right: Weather, Settings -->
    <div class="flex items-center space-x-3">
      <WeatherWidget />
      <button
        class="p-2 text-gray-400 hover:text-white rounded-full hover:bg-gray-800 transition-colors"
        title="Settings"
      >
        <SettingsIcon class="w-5 h-5" />
      </button>
    </div>
  </header>
</template>

<script setup>
import { SettingsIcon } from 'lucide-vue-next'
import WeatherWidget from './WeatherWidget.vue'
</script>
```

**Step 3: Move WeatherWidget to shared/**

```bash
mv frontend/vue-app/src/components/WeatherWidget.vue frontend/vue-app/src/components/shared/
```

**Step 4: Delete old AppHeader**

```bash
rm frontend/vue-app/src/components/AppHeader.vue
```

**Step 5: Commit**

```bash
git add frontend/vue-app/src/components/shared/
git rm frontend/vue-app/src/components/AppHeader.vue
git commit -m "refactor: rebuild AppHeader with Lumina centered nav style"
```

---

## Task 6: Create EmptyState Component

**Files:**
- Create: `frontend/vue-app/src/components/shared/EmptyState.vue`

**Step 1: Create EmptyState**

Create `frontend/vue-app/src/components/shared/EmptyState.vue`:

```vue
<template>
  <div class="flex flex-col items-center justify-center h-full text-gray-400 py-12">
    <div class="w-16 h-16 bg-gray-900 rounded-full flex items-center justify-center mb-4 border border-gray-800">
      <component :is="icon" class="w-8 h-8 text-blue-500" />
    </div>
    <h3 class="text-lg font-semibold text-gray-200 mb-2">{{ title }}</h3>
    <p class="text-sm text-center max-w-md text-gray-500">
      {{ message }}
    </p>
    <button
      v-if="actionLabel"
      @click="$emit('action')"
      class="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
    >
      {{ actionLabel }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  icon: {
    type: Object,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  message: {
    type: String,
    required: true
  },
  actionLabel: {
    type: String,
    default: null
  }
})

defineEmits(['action'])
</script>
```

**Step 2: Commit**

```bash
git add frontend/vue-app/src/components/shared/EmptyState.vue
git commit -m "feat: add reusable EmptyState component"
```

---

## Task 7: Rebuild DiscoveryView

**Files:**
- Modify: `frontend/vue-app/src/views/DiscoveryView.vue`
- Create: `frontend/vue-app/src/components/discovery/SearchFilters.vue`
- Modify: `frontend/vue-app/src/components/CatalogGrid.vue` → move to discovery/

**Step 1: Move CatalogGrid to discovery/**

```bash
mkdir -p frontend/vue-app/src/components/discovery
mv frontend/vue-app/src/components/CatalogGrid.vue frontend/vue-app/src/components/discovery/
```

**Step 2: Create SearchFilters component**

Create `frontend/vue-app/src/components/discovery/SearchFilters.vue` (copy content from CatalogSearchPanel but with Lumina styling):

```vue
<template>
  <div class="p-4 space-y-4">
    <div>
      <label class="block text-xs font-semibold text-gray-400 uppercase mb-2">
        Search Targets
      </label>
      <input
        v-model="searchQuery"
        type="search"
        placeholder="M31, NGC 7000, Andromeda..."
        @input="onSearchChange"
        class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
      />
    </div>

    <div>
      <label class="block text-xs font-semibold text-gray-400 uppercase mb-2">
        Object Type
      </label>
      <select
        v-model="selectedType"
        @change="applyFilters"
        class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:border-blue-500"
      >
        <option value="">All Types</option>
        <option value="galaxy">Galaxy</option>
        <option value="nebula">Nebula</option>
        <option value="cluster">Cluster</option>
        <option value="planetary_nebula">Planetary Nebula</option>
        <option value="double_star">Double Star</option>
      </select>
    </div>

    <div>
      <label class="block text-xs font-semibold text-gray-400 uppercase mb-2">
        Constellation
      </label>
      <select
        v-model="selectedConstellation"
        @change="applyFilters"
        class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:border-blue-500"
      >
        <option value="">All Constellations</option>
        <option v-for="constellation in constellations" :key="constellation" :value="constellation">
          {{ constellation }}
        </option>
      </select>
    </div>

    <div>
      <label class="block text-xs font-semibold text-gray-400 uppercase mb-2">
        Max Magnitude: {{ maxMagnitude || 'Any' }}
      </label>
      <input
        v-model.number="maxMagnitude"
        type="range"
        min="0"
        max="15"
        step="0.5"
        @change="applyFilters"
        class="w-full accent-blue-500"
      />
    </div>

    <button
      @click="clearFilters"
      class="w-full px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 text-sm rounded transition-colors"
    >
      Clear Filters
    </button>

    <div class="text-xs text-gray-500 pt-2 border-t border-gray-800">
      {{ catalogStore.totalItems }} objects found
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useCatalogStore } from '@/stores/catalog'

const catalogStore = useCatalogStore()

const searchQuery = ref('')
const selectedType = ref('')
const selectedConstellation = ref('')
const maxMagnitude = ref(null)

const constellations = [
  'Andromeda', 'Aquarius', 'Aquila', 'Aries', 'Auriga',
  'Cancer', 'Canis Major', 'Cassiopeia', 'Cygnus',
  'Gemini', 'Leo', 'Orion', 'Perseus', 'Sagittarius',
  'Scorpius', 'Taurus', 'Ursa Major', 'Virgo'
]

let searchTimeout = null

const onSearchChange = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    applyFilters()
  }, 300)
}

const applyFilters = () => {
  catalogStore.applyFilters({
    search: searchQuery.value,
    type: selectedType.value,
    constellation: selectedConstellation.value,
    max_magnitude: maxMagnitude.value || ''
  })
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedType.value = ''
  selectedConstellation.value = ''
  maxMagnitude.value = null
  catalogStore.clearFilters()
}

onMounted(() => {
  // Initial load happens in DiscoveryView
})
</script>
```

**Step 3: Rebuild DiscoveryView**

Replace `frontend/vue-app/src/views/DiscoveryView.vue`:

```vue
<template>
  <PanelContainer
    :left-panel-visible="true"
    :right-panel-visible="false"
    :console-visible="false"
  >
    <!-- Left: Search Filters -->
    <template #left>
      <div class="p-4 border-b border-gray-800">
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Filters</h3>
      </div>
      <SearchFilters />
    </template>

    <!-- Main: Catalog Grid -->
    <template #main>
      <div class="flex flex-col h-full">
        <!-- View Header -->
        <div class="bg-gray-900/50 border-b border-gray-800 px-4 py-3 flex-none">
          <h2 class="text-lg font-semibold text-gray-200">Discovery</h2>
          <p class="text-sm text-gray-500">
            {{ catalogStore.totalItems }} celestial objects
          </p>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-hidden">
          <CatalogGrid />
        </div>
      </div>
    </template>
  </PanelContainer>
</template>

<script setup>
import { onMounted } from 'vue'
import { useCatalogStore } from '@/stores/catalog'
import PanelContainer from '@/components/layout/PanelContainer.vue'
import SearchFilters from '@/components/discovery/SearchFilters.vue'
import CatalogGrid from '@/components/discovery/CatalogGrid.vue'

const catalogStore = useCatalogStore()

onMounted(async () => {
  await catalogStore.fetchCatalogData()
})
</script>
```

**Step 4: Update CatalogGrid styling**

Update `frontend/vue-app/src/components/discovery/CatalogGrid.vue` to use Tailwind defaults (replace all astro-* with gray-*/blue-*).

**Step 5: Delete old CatalogSearchPanel**

```bash
rm frontend/vue-app/src/components/CatalogSearchPanel.vue
```

**Step 6: Commit**

```bash
git add frontend/vue-app/src/views/DiscoveryView.vue frontend/vue-app/src/components/discovery/
git rm frontend/vue-app/src/components/CatalogSearchPanel.vue
git commit -m "refactor: rebuild DiscoveryView with Lumina layout and styling"
```

---

## Task 8: Update CatalogGrid with Tailwind Defaults

**Files:**
- Modify: `frontend/vue-app/src/components/discovery/CatalogGrid.vue`

**Step 1: Replace all custom colors**

In `CatalogGrid.vue`, replace:
- `bg-astro-elevated` → `bg-gray-900`
- `border-astro-border` → `border-gray-800`
- `bg-astro-surface` → `bg-gray-900`
- `text-astro-text` → `text-gray-200`
- `text-astro-text-muted` → `text-gray-500`
- `astro-accent` → `blue-500`

**Step 2: Update card styling**

Update catalog card classes to match Lumina:

```vue
<div class="catalog-card bg-gray-900 border border-gray-800 rounded-lg overflow-hidden cursor-pointer transition-all duration-200 hover:border-gray-700 hover:shadow-lg hover:shadow-blue-500/10">
```

**Step 3: Update button styling**

Replace button with inline Tailwind:

```vue
<button
  @click="catalogStore.addSelectedTarget(item)"
  class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
>
  Add to Plan
</button>
```

**Step 4: Commit**

```bash
git add frontend/vue-app/src/components/discovery/CatalogGrid.vue
git commit -m "style: update CatalogGrid to use Tailwind default colors"
```

---

## Task 9: Rebuild PlanningView

**Files:**
- Modify: `frontend/vue-app/src/views/PlanningView.vue`
- Create: `frontend/vue-app/src/components/planning/PlanningControls.vue`
- Create: `frontend/vue-app/src/components/planning/TargetList.vue`

**Step 1: Create PlanningControls**

Create `frontend/vue-app/src/components/planning/PlanningControls.vue` with Lumina styling (copy from old PlanningControls but update all colors to gray-*/blue-*).

**Step 2: Create TargetList**

Create `frontend/vue-app/src/components/planning/TargetList.vue` to show selected targets.

**Step 3: Rebuild PlanningView**

Replace `frontend/vue-app/src/views/PlanningView.vue` with PanelContainer layout and Lumina styling.

**Step 4: Commit**

```bash
git add frontend/vue-app/src/views/PlanningView.vue frontend/vue-app/src/components/planning/
git commit -m "refactor: rebuild PlanningView with Lumina layout"
```

---

## Task 10: Rebuild ExecutionView

**Files:**
- Modify: `frontend/vue-app/src/views/ExecutionView.vue`
- Update all components in: `frontend/vue-app/src/components/execution/`

**Step 1: Update ExecutionView**

Rebuild with PanelContainer and Lumina colors.

**Step 2: Update all execution components**

Replace astro-* colors with gray-*/blue-* in all execution components.

**Step 3: Commit**

```bash
git add frontend/vue-app/src/views/ExecutionView.vue frontend/vue-app/src/components/execution/
git commit -m "refactor: rebuild ExecutionView with Lumina styling"
```

---

## Task 11: Rebuild ProcessingView

**Files:**
- Modify: `frontend/vue-app/src/views/ProcessingView.vue`
- Update all components in: `frontend/vue-app/src/components/processing/`

**Step 1: Update ProcessingView**

Rebuild with PanelContainer and Lumina colors.

**Step 2: Update all processing components**

Replace astro-* colors with gray-*/blue-*.

**Step 3: Commit**

```bash
git add frontend/vue-app/src/views/ProcessingView.vue frontend/vue-app/src/components/processing/
git commit -m "refactor: rebuild ProcessingView with Lumina styling"
```

---

## Task 12: Update Favicon Reference

**Files:**
- Modify: `frontend/vue-app/index.html`

**Step 1: Update favicon path**

In `index.html`, update the icon link:

```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
```

**Step 2: Copy favicon to public directory**

```bash
cp frontend/favicon.svg frontend/vue-app/public/
```

**Step 3: Commit**

```bash
git add frontend/vue-app/index.html frontend/vue-app/public/favicon.svg
git commit -m "fix: update favicon reference to use telescope icon"
```

---

## Task 13: Clean Up Old Components

**Files:**
- Delete: `frontend/vue-app/src/components/AppSidebar.vue`
- Delete: `frontend/vue-app/src/components/AppConsole.vue`
- Delete: `frontend/vue-app/src/components/AppRightPanel.vue`
- Delete: `frontend/vue-app/src/components/common/` (entire directory)

**Step 1: Remove old components**

```bash
rm frontend/vue-app/src/components/AppSidebar.vue
rm frontend/vue-app/src/components/AppConsole.vue
rm frontend/vue-app/src/components/AppRightPanel.vue
rm -rf frontend/vue-app/src/components/common/
```

**Step 2: Commit**

```bash
git add -A
git commit -m "cleanup: remove old components and base component abstractions"
```

---

## Task 14: Build and Test

**Files:**
- None (verification step)

**Step 1: Run tests**

```bash
cd frontend/vue-app
npm test
```

Expected: All 27 tests pass

**Step 2: Build production**

```bash
npm run build
```

Expected: Clean build, no errors, dist/ created

**Step 3: Verify in browser**

```bash
npm run dev
```

Open http://localhost:5173 and verify:
- ✅ Lumina-style layout
- ✅ Tailwind default colors (gray-900, gray-800, blue-500)
- ✅ All 4 views accessible
- ✅ Telescope favicon shows

**Step 4: Commit**

```bash
git add frontend/vue-app/dist/
git commit -m "build: production build with Lumina styling"
```

---

## Task 15: Rebuild Docker Container

**Files:**
- None (deployment step)

**Step 1: Rebuild container**

```bash
docker compose build
```

**Step 2: Start container**

```bash
docker compose up -d
```

**Step 3: Verify deployment**

Open http://localhost:9247/app/ and verify Lumina styling.

**Step 4: Final commit**

```bash
git commit --allow-empty -m "chore: complete Lumina-style redesign"
```

---

## Success Criteria

- ✅ No custom colors in tailwind.config.js
- ✅ All views use PanelContainer layout
- ✅ All components use inline Tailwind (gray-900, gray-800, blue-500)
- ✅ All 27 tests passing
- ✅ Production build successful
- ✅ Telescope favicon visible
- ✅ Container running with new UI
- ✅ Matches Lumina's clean, spacious aesthetic
