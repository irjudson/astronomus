# Astronomus UX Modernization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform Astronomus from garish cyan theme to professional dark scientific aesthetic, restore all deleted vanilla JS functionality using modern Vue 3 patterns, and fix all data loading issues.

**Architecture:** Parallel track approach - implement theme system (quick win), fix data loading (critical), and restore features progressively. Each track can proceed independently. Modern Vue 3 Composition API, Pinia stores, Tailwind CSS with custom dark scientific palette.

**Tech Stack:** Vue 3, Vite, Pinia, Vue Router, Tailwind CSS, Axios, Vitest, Playwright

---

## Track 1: Theme System (Quick Win)

### Task 1: Update Tailwind Config with Dark Scientific Palette

**Files:**
- Modify: `frontend/vue-app/tailwind.config.js`

**Step 1: Update Tailwind config with astro-* color palette**

Edit `frontend/vue-app/tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
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
      },
    },
  },
  plugins: [],
}
```

**Step 2: Verify build still works**

Run:
```bash
cd frontend/vue-app
npm run build
```

Expected: Build succeeds with no errors

**Step 3: Commit**

```bash
git add frontend/vue-app/tailwind.config.js
git commit -m "feat: add dark scientific color palette to Tailwind config"
```

---

### Task 2: Create Base Components with New Theme

**Files:**
- Create: `frontend/vue-app/src/components/common/BaseButton.vue`
- Create: `frontend/vue-app/src/components/common/BaseCard.vue`
- Create: `frontend/vue-app/src/components/common/BaseInput.vue`
- Create: `frontend/vue-app/src/components/common/SkeletonCard.vue`

**Step 1: Create common components directory**

Run:
```bash
mkdir -p frontend/vue-app/src/components/common
```

**Step 2: Create BaseButton component**

Create `frontend/vue-app/src/components/common/BaseButton.vue`:

```vue
<template>
  <button
    :type="type"
    :disabled="disabled"
    :class="buttonClasses"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'danger', 'ghost'].includes(value)
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  type: {
    type: String,
    default: 'button'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])

const buttonClasses = computed(() => {
  const base = 'rounded font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-astro-accent focus:ring-offset-2 focus:ring-offset-astro-bg disabled:opacity-50 disabled:cursor-not-allowed'

  const variants = {
    primary: 'bg-astro-accent hover:bg-astro-accent-hover text-white',
    secondary: 'bg-astro-surface hover:bg-astro-elevated text-astro-text border border-astro-border',
    danger: 'bg-astro-error hover:bg-red-600 text-white',
    ghost: 'hover:bg-astro-elevated text-astro-text'
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  }

  return `${base} ${variants[props.variant]} ${sizes[props.size]}`
})
</script>
```

**Step 3: Create BaseCard component**

Create `frontend/vue-app/src/components/common/BaseCard.vue`:

```vue
<template>
  <div :class="cardClasses">
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  padding: {
    type: String,
    default: 'md',
    validator: (value) => ['none', 'sm', 'md', 'lg'].includes(value)
  },
  hoverable: {
    type: Boolean,
    default: false
  }
})

const cardClasses = computed(() => {
  const base = 'bg-astro-surface border border-astro-border rounded-lg'

  const paddings = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6'
  }

  const hover = props.hoverable ? 'hover:border-astro-border-focus transition-colors cursor-pointer' : ''

  return `${base} ${paddings[props.padding]} ${hover}`
})
</script>
```

**Step 4: Create BaseInput component**

Create `frontend/vue-app/src/components/common/BaseInput.vue`:

```vue
<template>
  <div class="relative">
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="inputClasses"
      @input="$emit('update:modelValue', $event.target.value)"
      @blur="$emit('blur', $event)"
      @focus="$emit('focus', $event)"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  },
  placeholder: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  error: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:modelValue', 'blur', 'focus'])

const inputClasses = computed(() => {
  const base = 'w-full px-3 py-2 bg-astro-elevated border rounded text-astro-text placeholder-astro-text-dim focus:outline-none focus:ring-2 focus:ring-astro-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors'

  const borderColor = props.error ? 'border-astro-error' : 'border-astro-border focus:border-astro-accent'

  return `${base} ${borderColor}`
})
</script>
```

**Step 5: Create SkeletonCard component**

Create `frontend/vue-app/src/components/common/SkeletonCard.vue`:

```vue
<template>
  <div class="bg-astro-surface border border-astro-border rounded-lg overflow-hidden">
    <div class="h-40 bg-astro-elevated animate-pulse"></div>
    <div class="p-4 space-y-3">
      <div class="h-4 bg-astro-elevated rounded animate-pulse"></div>
      <div class="h-3 bg-astro-elevated rounded w-3/4 animate-pulse"></div>
      <div class="h-3 bg-astro-elevated rounded w-1/2 animate-pulse"></div>
    </div>
  </div>
</template>
```

**Step 6: Test base components render**

Run:
```bash
cd frontend/vue-app
npm run dev
```

Open browser to `http://localhost:5173` and verify no errors

**Step 7: Commit**

```bash
git add frontend/vue-app/src/components/common/
git commit -m "feat: add base UI components with dark scientific theme"
```

---

### Task 3: Update App.vue to Use New Theme

**Files:**
- Modify: `frontend/vue-app/src/App.vue`

**Step 1: Update App.vue background and text colors**

Edit `frontend/vue-app/src/App.vue`:

Replace:
```vue
<div class="flex flex-col h-screen bg-dark text-dark-text">
```

With:
```vue
<div class="flex flex-col h-screen bg-astro-bg text-astro-text">
```

Replace all panel background colors:
```vue
<aside class="left-panel overflow-y-auto border-r border-dark-border bg-dark-surface">
```

With:
```vue
<aside class="left-panel overflow-y-auto border-r border-astro-border bg-astro-surface">
```

Do the same for:
- `.main-content` → `bg-astro-bg`
- `.right-panel` → `bg-astro-surface border-l border-astro-border`
- `.console` → `bg-astro-surface border-t border-astro-border`

**Step 2: Verify app renders with new colors**

Run:
```bash
npm run dev
```

Open browser and verify:
- Background is deep space (#0a0e1a)
- Panels are slightly lighter (#131720)
- Borders are subtle (#1e293b)
- No bright cyan visible

**Step 3: Commit**

```bash
git add frontend/vue-app/src/App.vue
git commit -m "feat: apply dark scientific theme to main app layout"
```

---

### Task 4: Update AppHeader Component

**Files:**
- Modify: `frontend/vue-app/src/components/AppHeader.vue`

**Step 1: Replace colors in AppHeader**

Edit `frontend/vue-app/src/components/AppHeader.vue`:

Replace:
```vue
<header class="h-14 bg-tron-panel border-b border-tron-border flex items-center px-4 gap-4">
```

With:
```vue
<header class="h-14 bg-astro-surface border-b border-astro-border flex items-center px-4 gap-4">
```

Replace text color:
```vue
<span class="text-2xl font-bold text-tron-accent">Astronomus</span>
```

With:
```vue
<span class="text-2xl font-semibold text-astro-text">Astronomus</span>
```

Replace input styling:
```vue
<input
  type="search"
  placeholder="Search targets..."
  class="w-full px-3 py-1.5 bg-tron-bg border border-tron-border rounded text-sm focus:outline-none focus:border-tron-accent"
/>
```

With:
```vue
<input
  type="search"
  placeholder="Search targets..."
  class="w-full px-3 py-1.5 bg-astro-elevated border border-astro-border rounded text-sm focus:outline-none focus:border-astro-accent text-astro-text placeholder-astro-text-dim"
/>
```

Replace button hover:
```vue
<button class="p-2 hover:bg-tron-bg rounded">
```

With:
```vue
<button class="p-2 hover:bg-astro-elevated rounded text-astro-text-muted hover:text-astro-text transition-colors">
```

**Step 2: Verify header appearance**

Run `npm run dev` and check:
- Header has dark surface background
- Text is readable light gray
- Search input has elevated background
- No cyan colors

**Step 3: Commit**

```bash
git add frontend/vue-app/src/components/AppHeader.vue
git commit -m "feat: apply dark scientific theme to app header"
```

---

### Task 5: Update AppSidebar Component

**Files:**
- Modify: `frontend/vue-app/src/components/AppSidebar.vue`

**Step 1: Replace all color references**

Edit `frontend/vue-app/src/components/AppSidebar.vue`:

Replace all `tron-*` color classes with `astro-*`:
- `bg-tron-panel` → `bg-astro-surface`
- `border-tron-border` → `border-astro-border`
- `bg-tron-bg` → `bg-astro-elevated`
- `hover:bg-tron-bg` → `hover:bg-astro-elevated`
- `bg-tron-accent/20` → `bg-astro-accent/20`
- `text-tron-accent` → `text-astro-accent`
- `text-tron-text/60` → `text-astro-text-muted`
- `text-tron-text/40` → `text-astro-text-dim`

**Step 2: Verify sidebar navigation**

Run `npm run dev` and check:
- Sidebar matches new theme
- Navigation links have subtle hover
- Active link has blue accent (not cyan)
- Collapse button works

**Step 3: Commit**

```bash
git add frontend/vue-app/src/components/AppSidebar.vue
git commit -m "feat: apply dark scientific theme to sidebar navigation"
```

---

### Task 6: Update Remaining Layout Components

**Files:**
- Modify: `frontend/vue-app/src/components/AppRightPanel.vue`
- Modify: `frontend/vue-app/src/components/AppConsole.vue`

**Step 1: Update AppRightPanel.vue**

Replace all `tron-*` references with `astro-*` in `AppRightPanel.vue`

**Step 2: Update AppConsole.vue**

Replace all `tron-*` references with `astro-*` in `AppConsole.vue`

**Step 3: Verify all panels**

Run `npm run dev` and verify:
- Right panel has new theme
- Console has new theme
- All collapsible panels work
- No bright colors anywhere

**Step 4: Commit**

```bash
git add frontend/vue-app/src/components/AppRightPanel.vue frontend/vue-app/src/components/AppConsole.vue
git commit -m "feat: complete dark scientific theme for all layout components"
```

---

### Task 7: Update CatalogGrid Component

**Files:**
- Modify: `frontend/vue-app/src/components/CatalogGrid.vue`

**Step 1: Remove all bright cyan colors**

Edit `frontend/vue-app/src/components/CatalogGrid.vue` in `<style scoped>` section:

Replace:
```css
.catalog-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 217, 255, 0.2);
```

With:
```css
.catalog-card {
  @apply bg-astro-surface border border-astro-border;
```

Replace:
```css
.catalog-card:hover {
  transform: translateY(-4px);
  border-color: #00d9ff;
  box-shadow: 0 4px 12px rgba(0, 217, 255, 0.3);
}
```

With:
```css
.catalog-card:hover {
  transform: translateY(-2px);
  @apply border-astro-border-focus;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}
```

Replace all cyan colors:
- `#00d9ff` → Use `@apply text-astro-accent`
- `rgba(0, 217, 255, 0.2)` → Use `@apply bg-astro-accent/20`

**Step 2: Update card title and type badge styling**

Replace:
```css
.catalog-card-title {
  color: #00d9ff;
  font-size: 14px;
  font-weight: 600;
}
```

With:
```css
.catalog-card-title {
  @apply text-astro-text font-semibold text-sm;
}
```

Replace:
```css
.catalog-card-type {
  background: rgba(0, 217, 255, 0.2);
  color: #00d9ff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 10px;
  text-transform: uppercase;
}
```

With:
```css
.catalog-card-type {
  @apply bg-astro-accent/20 text-astro-accent px-2 py-1 rounded text-xs uppercase;
}
```

**Step 3: Update button styling**

Replace:
```css
.btn-primary {
  /* old cyan styling */
}
```

With usage of BaseButton component in template section:

```vue
<BaseButton variant="primary" size="sm" @click="catalogStore.addSelectedTarget(item)">
  Add to Plan
</BaseButton>
```

Import BaseButton:
```vue
<script setup>
import BaseButton from '@/components/common/BaseButton.vue'
// ... rest of imports
</script>
```

**Step 4: Verify catalog grid appearance**

Run `npm run dev`, navigate to Discovery view:
- Cards have subtle dark theme
- No bright cyan
- Hover effect is subtle
- Buttons use new blue accent

**Step 5: Commit**

```bash
git add frontend/vue-app/src/components/CatalogGrid.vue
git commit -m "feat: apply dark scientific theme to catalog grid"
```

---

## Track 2: Data Loading (Critical Fix)

### Task 8: Fix Catalog Store Data Loading

**Files:**
- Modify: `frontend/vue-app/src/stores/catalog.js`
- Create: `frontend/vue-app/src/stores/__tests__/catalog.test.js`

**Step 1: Write test for catalog data fetching**

Create `frontend/vue-app/src/stores/__tests__/catalog.test.js`:

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCatalogStore } from '../catalog'
import axios from 'axios'

vi.mock('axios')

describe('Catalog Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetches catalog data from API', async () => {
    const mockData = {
      items: [
        { id: 'M31', name: 'Andromeda Galaxy', type: 'galaxy' },
        { id: 'M42', name: 'Orion Nebula', type: 'nebula' }
      ],
      total: 2
    }

    axios.get.mockResolvedValue({ data: mockData })

    const store = useCatalogStore()
    await store.fetchCatalogData()

    expect(store.items).toHaveLength(2)
    expect(store.items[0].id).toBe('M31')
    expect(store.totalItems).toBe(2)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('handles API errors gracefully', async () => {
    axios.get.mockRejectedValue(new Error('Network error'))

    const store = useCatalogStore()
    await store.fetchCatalogData()

    expect(store.error).toContain('Failed to load catalog data')
    expect(store.items).toHaveLength(0)
    expect(store.loading).toBe(false)
  })
})
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd frontend/vue-app
npm test catalog.test.js
```

Expected: Tests may pass if store already works, or fail if API path is wrong

**Step 3: Fix API endpoint if needed**

Check `frontend/vue-app/src/stores/catalog.js` line 62:

```javascript
const response = await axios.get(`/api/catalog/search?${queryParams.toString()}`);
```

Verify this matches backend API endpoint. Should be `/api/catalog/search` or `/api/targets/search`.

**Step 4: Run tests to verify they pass**

Run:
```bash
npm test catalog.test.js
```

Expected: All tests pass

**Step 5: Test with real backend**

Start backend:
```bash
cd backend
uvicorn app.main:app --reload
```

Start frontend:
```bash
cd frontend/vue-app
npm run dev
```

Navigate to Discovery view and verify data loads.

**Step 6: Commit**

```bash
git add frontend/vue-app/src/stores/catalog.js frontend/vue-app/src/stores/__tests__/catalog.test.js
git commit -m "test: add catalog store tests and verify API integration"
```

---

### Task 9: Create and Test Weather Store

**Files:**
- Create: `frontend/vue-app/src/stores/weather.js`
- Create: `frontend/vue-app/src/stores/__tests__/weather.test.js`

**Step 1: Write test for weather store**

Create `frontend/vue-app/src/stores/__tests__/weather.test.js`:

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useWeatherStore } from '../weather'
import axios from 'axios'

vi.mock('axios')

describe('Weather Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetches current weather from API', async () => {
    const mockWeather = {
      temperature: 15,
      humidity: 65,
      cloud_cover: 20,
      wind_speed: 5
    }

    axios.get.mockResolvedValue({ data: mockWeather })

    const store = useWeatherStore()
    await store.fetchCurrentWeather()

    expect(store.current).toEqual(mockWeather)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('handles weather API errors', async () => {
    axios.get.mockRejectedValue(new Error('API error'))

    const store = useWeatherStore()
    await store.fetchCurrentWeather()

    expect(store.error).toBeTruthy()
    expect(store.loading).toBe(false)
  })
})
```

**Step 2: Run test to verify it fails**

Run:
```bash
npm test weather.test.js
```

Expected: FAIL - weather store doesn't exist yet

**Step 3: Create weather store**

Create `frontend/vue-app/src/stores/weather.js`:

```javascript
import { defineStore } from 'pinia'
import axios from 'axios'

export const useWeatherStore = defineStore('weather', {
  state: () => ({
    current: null,
    forecast: [],
    seeing: null,
    loading: false,
    error: null,
    lastUpdated: null
  }),

  getters: {
    weatherScore: (state) => {
      if (!state.current) return null

      // Calculate score based on cloud cover, seeing, wind
      let score = 100

      // Cloud cover penalty (0-100%)
      score -= state.current.cloud_cover

      // Wind penalty (> 20 km/h is bad)
      if (state.current.wind_speed > 20) {
        score -= (state.current.wind_speed - 20) * 2
      }

      // Humidity penalty (> 80% is bad)
      if (state.current.humidity > 80) {
        score -= (state.current.humidity - 80)
      }

      return Math.max(0, Math.min(100, score))
    },

    weatherQuality: (state) => {
      const score = state.weatherScore
      if (score === null) return 'Unknown'
      if (score >= 80) return 'Excellent'
      if (score >= 60) return 'Good'
      if (score >= 40) return 'Fair'
      if (score >= 20) return 'Poor'
      return 'Very Poor'
    }
  },

  actions: {
    async fetchCurrentWeather() {
      this.loading = true
      this.error = null

      try {
        const response = await axios.get('/api/weather/current')
        this.current = response.data
        this.lastUpdated = new Date()
      } catch (err) {
        this.error = 'Failed to load weather data: ' + err.message
        console.error('Weather error:', err)
      } finally {
        this.loading = false
      }
    },

    async fetchForecast() {
      try {
        const response = await axios.get('/api/weather/forecast')
        this.forecast = response.data
      } catch (err) {
        console.error('Forecast error:', err)
      }
    },

    async fetchSeeing() {
      try {
        const response = await axios.get('/api/astronomy/weather/7timer')
        this.seeing = response.data
      } catch (err) {
        console.error('Seeing error:', err)
      }
    },

    async fetchAllWeatherData() {
      await Promise.all([
        this.fetchCurrentWeather(),
        this.fetchForecast(),
        this.fetchSeeing()
      ])
    }
  }
})
```

**Step 4: Run tests to verify they pass**

Run:
```bash
npm test weather.test.js
```

Expected: All tests pass

**Step 5: Commit**

```bash
git add frontend/vue-app/src/stores/weather.js frontend/vue-app/src/stores/__tests__/weather.test.js
git commit -m "feat: add weather store with current conditions and forecast"
```

---

### Task 10: Create Planning Store

**Files:**
- Modify: `frontend/vue-app/src/stores/planning.js` (if exists) or Create it
- Create: `frontend/vue-app/src/stores/__tests__/planning.test.js`

**Step 1: Write test for planning store**

Create `frontend/vue-app/src/stores/__tests__/planning.test.js`:

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePlanningStore } from '../planning'
import axios from 'axios'

vi.mock('axios')

describe('Planning Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('generates observation plan', async () => {
    const mockPlan = {
      id: 'plan-123',
      targets: [
        { name: 'M31', start_time: '20:00', duration: 60 }
      ],
      total_duration: 60
    }

    axios.post.mockResolvedValue({ data: mockPlan })

    const store = usePlanningStore()
    store.selectedTargets = [{ id: 'M31', name: 'Andromeda' }]

    await store.generatePlan()

    expect(store.currentPlan).toEqual(mockPlan)
    expect(store.loading).toBe(false)
  })
})
```

**Step 2: Run test to verify it fails**

Run:
```bash
npm test planning.test.js
```

Expected: FAIL - planning store doesn't exist or generatePlan not implemented

**Step 3: Create/update planning store**

Create `frontend/vue-app/src/stores/planning.js`:

```javascript
import { defineStore } from 'pinia'
import axios from 'axios'

export const usePlanningStore = defineStore('planning', {
  state: () => ({
    selectedTargets: [],
    currentPlan: null,
    savedPlans: [],
    loading: false,
    error: null,

    // Planning parameters
    location: {
      latitude: 45.9183,
      longitude: -111.5433,
      elevation: 1234,
      timezone: 'America/Denver'
    },
    observationDate: null,
    constraints: {
      min_altitude: 30,
      max_altitude: 70,
      avoid_moon: true,
      setup_time_minutes: 30
    }
  }),

  getters: {
    hasTargets: (state) => state.selectedTargets.length > 0,
    targetCount: (state) => state.selectedTargets.length
  },

  actions: {
    addTarget(target) {
      const exists = this.selectedTargets.some(t => t.id === target.id)
      if (!exists) {
        this.selectedTargets.push(target)
      }
    },

    removeTarget(targetId) {
      this.selectedTargets = this.selectedTargets.filter(t => t.id !== targetId)
    },

    clearTargets() {
      this.selectedTargets = []
    },

    async generatePlan() {
      this.loading = true
      this.error = null

      try {
        const response = await axios.post('/api/plan', {
          targets: this.selectedTargets.map(t => t.id),
          location: this.location,
          date: this.observationDate || new Date().toISOString().split('T')[0],
          constraints: this.constraints
        })

        this.currentPlan = response.data
      } catch (err) {
        this.error = 'Failed to generate plan: ' + err.message
        console.error('Plan generation error:', err)
      } finally {
        this.loading = false
      }
    },

    async savePlan() {
      if (!this.currentPlan) return

      try {
        const response = await axios.post('/api/plans', this.currentPlan)
        this.savedPlans.push(response.data)
      } catch (err) {
        this.error = 'Failed to save plan: ' + err.message
      }
    },

    async loadSavedPlans() {
      try {
        const response = await axios.get('/api/plans')
        this.savedPlans = response.data
      } catch (err) {
        console.error('Load plans error:', err)
      }
    },

    async exportPlan(format = 'seestar_alp') {
      if (!this.currentPlan) return null

      try {
        const response = await axios.get(`/api/plans/${this.currentPlan.id}/export/${format}`)
        return response.data
      } catch (err) {
        this.error = 'Failed to export plan: ' + err.message
        return null
      }
    }
  }
})
```

**Step 4: Run tests to verify they pass**

Run:
```bash
npm test planning.test.js
```

Expected: All tests pass

**Step 5: Commit**

```bash
git add frontend/vue-app/src/stores/planning.js frontend/vue-app/src/stores/__tests__/planning.test.js
git commit -m "feat: add planning store with plan generation and export"
```

---

### Task 11: Create Execution Store

**Files:**
- Modify: `frontend/vue-app/src/stores/execution.js` (if exists) or Create it
- Create: `frontend/vue-app/src/stores/__tests__/execution.test.js`

**Step 1: Write test for execution store**

Create `frontend/vue-app/src/stores/__tests__/execution.test.js`:

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useExecutionStore } from '../execution'
import axios from 'axios'

vi.mock('axios')

describe('Execution Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('connects to telescope', async () => {
    axios.post.mockResolvedValue({ data: { status: 'connected' } })

    const store = useExecutionStore()
    await store.connectTelescope('192.168.1.100')

    expect(store.connected).toBe(true)
    expect(store.telescopeIp).toBe('192.168.1.100')
  })

  it('updates telescope position', () => {
    const store = useExecutionStore()
    store.updatePosition({
      ra: 10.5,
      dec: 45.0,
      alt: 60.0,
      az: 180.0
    })

    expect(store.position.ra).toBe(10.5)
    expect(store.position.alt).toBe(60.0)
  })
})
```

**Step 2: Run test to verify it fails**

Run:
```bash
npm test execution.test.js
```

Expected: FAIL - execution store doesn't exist

**Step 3: Create execution store**

Create `frontend/vue-app/src/stores/execution.js`:

```javascript
import { defineStore } from 'pinia'
import axios from 'axios'

export const useExecutionStore = defineStore('execution', {
  state: () => ({
    connected: false,
    telescopeIp: '',
    currentPlan: null,
    planExecuting: false,
    currentTargetIndex: 0,

    position: {
      ra: 0,
      dec: 0,
      alt: 0,
      az: 0
    },

    imaging: {
      active: false,
      currentFrame: 0,
      totalFrames: 0,
      exposure: 10,
      progress: 0
    },

    hardware: {
      mount: 'idle',
      camera: 'idle',
      focuser: 0,
      battery: null
    },

    messages: [],
    error: null
  }),

  getters: {
    currentTarget: (state) => {
      if (!state.currentPlan || !state.currentPlan.targets) return null
      return state.currentPlan.targets[state.currentTargetIndex]
    },

    nextTarget: (state) => {
      if (!state.currentPlan || !state.currentPlan.targets) return null
      if (state.currentTargetIndex >= state.currentPlan.targets.length - 1) return null
      return state.currentPlan.targets[state.currentTargetIndex + 1]
    },

    progressPercent: (state) => {
      if (!state.imaging.totalFrames) return 0
      return Math.round((state.imaging.currentFrame / state.imaging.totalFrames) * 100)
    }
  },

  actions: {
    async connectTelescope(ip) {
      try {
        const response = await axios.post('/api/telescope/connect', { ip })
        this.connected = true
        this.telescopeIp = ip
        this.error = null

        // Start position updates
        this.startPositionUpdates()
      } catch (err) {
        this.error = 'Failed to connect: ' + err.message
        this.connected = false
      }
    },

    async disconnectTelescope() {
      try {
        await axios.post('/api/telescope/disconnect')
        this.connected = false
        this.telescopeIp = ''
        this.stopPositionUpdates()
      } catch (err) {
        console.error('Disconnect error:', err)
      }
    },

    updatePosition(position) {
      this.position = { ...position }
    },

    async startPositionUpdates() {
      // Poll position every second
      this.positionInterval = setInterval(async () => {
        if (!this.connected) {
          clearInterval(this.positionInterval)
          return
        }

        try {
          const response = await axios.get('/api/telescope/status')
          this.updatePosition(response.data.position)
          this.hardware = response.data.hardware
        } catch (err) {
          console.error('Position update error:', err)
        }
      }, 1000)
    },

    stopPositionUpdates() {
      if (this.positionInterval) {
        clearInterval(this.positionInterval)
      }
    },

    loadPlan(plan) {
      this.currentPlan = plan
      this.currentTargetIndex = 0
    },

    async executePlan() {
      if (!this.connected || !this.currentPlan) return

      this.planExecuting = true

      for (let i = 0; i < this.currentPlan.targets.length; i++) {
        if (!this.planExecuting) break

        this.currentTargetIndex = i
        const target = this.currentPlan.targets[i]

        // Slew to target
        await this.slewToTarget(target)

        // Start imaging
        await this.startImaging(target)
      }

      this.planExecuting = false
    },

    async slewToTarget(target) {
      try {
        await axios.post('/api/telescope/slew', {
          ra: target.ra,
          dec: target.dec
        })

        this.addMessage('info', `Slewing to ${target.name}`)
      } catch (err) {
        this.addMessage('error', `Failed to slew: ${err.message}`)
      }
    },

    async startImaging(target) {
      try {
        this.imaging.active = true
        this.imaging.currentFrame = 0
        this.imaging.totalFrames = target.frames || 10

        this.addMessage('info', `Starting imaging: ${target.name}`)

        // Imaging would happen here via telescope API
        // For now, just simulate progress
      } catch (err) {
        this.addMessage('error', `Imaging failed: ${err.message}`)
      } finally {
        this.imaging.active = false
      }
    },

    pausePlan() {
      this.planExecuting = false
    },

    resumePlan() {
      this.executePlan()
    },

    stopPlan() {
      this.planExecuting = false
      this.imaging.active = false
    },

    skipToNext() {
      if (this.currentTargetIndex < this.currentPlan.targets.length - 1) {
        this.currentTargetIndex++
      }
    },

    addMessage(type, text) {
      this.messages.unshift({
        timestamp: new Date().toISOString(),
        type,
        text
      })

      // Keep only last 100 messages
      if (this.messages.length > 100) {
        this.messages = this.messages.slice(0, 100)
      }
    }
  }
})
```

**Step 4: Run tests to verify they pass**

Run:
```bash
npm test execution.test.js
```

Expected: All tests pass

**Step 5: Commit**

```bash
git add frontend/vue-app/src/stores/execution.js frontend/vue-app/src/stores/__tests__/execution.test.js
git commit -m "feat: add execution store with telescope control and plan execution"
```

---

### Task 12: Create Processing Store

**Files:**
- Modify: `frontend/vue-app/src/stores/processing.js` (if exists) or Create it

**Step 1: Create processing store**

Create `frontend/vue-app/src/stores/processing.js`:

```javascript
import { defineStore } from 'pinia'
import axios from 'axios'

export const useProcessingStore = defineStore('processing', {
  state: () => ({
    files: [],
    selectedFiles: [],
    currentDirectory: '/data',
    libraryImages: [],

    previewImage: null,

    processingJobs: [],
    activeJob: null,

    loading: false,
    error: null
  }),

  getters: {
    selectedFileCount: (state) => state.selectedFiles.length,
    hasSelection: (state) => state.selectedFiles.length > 0
  },

  actions: {
    async browseDirectory(path) {
      this.loading = true
      this.error = null

      try {
        const response = await axios.get('/api/files/browse', {
          params: { path }
        })

        this.files = response.data.files
        this.currentDirectory = path
      } catch (err) {
        this.error = 'Failed to browse directory: ' + err.message
      } finally {
        this.loading = false
      }
    },

    selectFile(file) {
      if (!this.selectedFiles.includes(file)) {
        this.selectedFiles.push(file)
      }
    },

    deselectFile(file) {
      this.selectedFiles = this.selectedFiles.filter(f => f !== file)
    },

    clearSelection() {
      this.selectedFiles = []
    },

    async stackImages() {
      if (this.selectedFiles.length === 0) return

      try {
        const response = await axios.post('/api/process/stack-and-stretch', {
          files: this.selectedFiles.map(f => f.path),
          method: 'sigma_clipped_mean'
        })

        this.activeJob = response.data
        this.processingJobs.unshift(response.data)

        // Poll for job completion
        this.pollJobStatus(response.data.id)
      } catch (err) {
        this.error = 'Failed to start stacking: ' + err.message
      }
    },

    async pollJobStatus(jobId) {
      const interval = setInterval(async () => {
        try {
          const response = await axios.get(`/api/process/jobs/${jobId}`)
          const job = response.data

          // Update job in list
          const index = this.processingJobs.findIndex(j => j.id === jobId)
          if (index >= 0) {
            this.processingJobs[index] = job
          }

          if (job.status === 'completed' || job.status === 'failed') {
            clearInterval(interval)

            if (job.status === 'completed') {
              this.previewImage = job.result_path
            }
          }
        } catch (err) {
          console.error('Job status poll error:', err)
          clearInterval(interval)
        }
      }, 2000)
    },

    async loadLibrary() {
      try {
        const response = await axios.get('/api/library/images')
        this.libraryImages = response.data
      } catch (err) {
        console.error('Library load error:', err)
      }
    }
  }
})
```

**Step 2: Verify store compiles**

Run:
```bash
npm run build
```

Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/vue-app/src/stores/processing.js
git commit -m "feat: add processing store with file browsing and stacking"
```

---

## Track 3: Feature Restoration (Progressive)

### Task 13: Fix DiscoveryView Data Loading

**Files:**
- Modify: `frontend/vue-app/src/views/DiscoveryView.vue`
- Modify: `frontend/vue-app/src/components/CatalogSearchPanel.vue`

**Step 1: Verify CatalogSearchPanel exists and add search functionality**

Check if `frontend/vue-app/src/components/CatalogSearchPanel.vue` exists. If not, create it:

```vue
<template>
  <div class="catalog-search-panel p-4 space-y-4">
    <div>
      <label class="block text-xs font-medium text-astro-text-muted mb-2">
        Search Targets
      </label>
      <BaseInput
        v-model="searchQuery"
        type="search"
        placeholder="M31, NGC 7000, Andromeda..."
        @input="onSearchChange"
      />
    </div>

    <div>
      <label class="block text-xs font-medium text-astro-text-muted mb-2">
        Object Type
      </label>
      <select
        v-model="selectedType"
        @change="applyFilters"
        class="w-full px-3 py-2 bg-astro-elevated border border-astro-border rounded text-astro-text focus:outline-none focus:border-astro-accent"
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
      <label class="block text-xs font-medium text-astro-text-muted mb-2">
        Constellation
      </label>
      <select
        v-model="selectedConstellation"
        @change="applyFilters"
        class="w-full px-3 py-2 bg-astro-elevated border border-astro-border rounded text-astro-text focus:outline-none focus:border-astro-accent"
      >
        <option value="">All Constellations</option>
        <option v-for="const in constellations" :key="const" :value="const">
          {{ const }}
        </option>
      </select>
    </div>

    <div>
      <label class="block text-xs font-medium text-astro-text-muted mb-2">
        Max Magnitude: {{ maxMagnitude || 'Any' }}
      </label>
      <input
        v-model.number="maxMagnitude"
        type="range"
        min="0"
        max="15"
        step="0.5"
        @change="applyFilters"
        class="w-full"
      />
    </div>

    <div>
      <BaseButton variant="secondary" @click="clearFilters" class="w-full">
        Clear Filters
      </BaseButton>
    </div>

    <div class="text-xs text-astro-text-dim">
      {{ catalogStore.totalItems }} objects found
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useCatalogStore } from '@/stores/catalog'
import BaseInput from '@/components/common/BaseInput.vue'
import BaseButton from '@/components/common/BaseButton.vue'

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
  // Add more as needed
]

let searchTimeout = null

const onSearchChange = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    applyFilters()
  }, 300) // Debounce 300ms
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

**Step 2: Ensure DiscoveryView triggers initial data fetch**

Verify `frontend/vue-app/src/views/DiscoveryView.vue` calls `catalogStore.fetchCatalogData()` on mount.

**Step 3: Test catalog loading**

Run:
```bash
npm run dev
```

Navigate to Discovery view and verify:
- Catalog data loads
- Search works
- Filters work
- No console errors

**Step 4: Commit**

```bash
git add frontend/vue-app/src/components/CatalogSearchPanel.vue frontend/vue-app/src/views/DiscoveryView.vue
git commit -m "feat: add catalog search and filtering to Discovery view"
```

---

### Task 14: Add Weather Widget to Header

**Files:**
- Modify: `frontend/vue-app/src/components/AppHeader.vue`
- Create: `frontend/vue-app/src/components/WeatherWidget.vue` (if not exists)

**Step 1: Create WeatherWidget component**

Create/update `frontend/vue-app/src/components/WeatherWidget.vue`:

```vue
<template>
  <div class="weather-widget flex items-center gap-2 text-sm">
    <button
      @click="toggleModal"
      class="flex items-center gap-2 px-3 py-1.5 rounded hover:bg-astro-elevated transition-colors"
    >
      <span class="text-lg">{{ weatherIcon }}</span>
      <div class="text-left">
        <div class="text-astro-text font-medium">
          {{ weatherStore.current?.temperature }}°C
        </div>
        <div class="text-xs text-astro-text-muted">
          {{ weatherStore.weatherQuality }}
        </div>
      </div>
    </button>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useWeatherStore } from '@/stores/weather'

const weatherStore = useWeatherStore()

const weatherIcon = computed(() => {
  if (!weatherStore.current) return '🌤️'

  const cloudCover = weatherStore.current.cloud_cover || 0

  if (cloudCover < 20) return '☀️'
  if (cloudCover < 50) return '⛅'
  if (cloudCover < 80) return '☁️'
  return '🌧️'
})

const toggleModal = () => {
  // Emit event to parent to show weather modal
  // Or navigate to weather details page
  console.log('Show weather details')
}

onMounted(() => {
  weatherStore.fetchCurrentWeather()

  // Refresh every 30 minutes
  setInterval(() => {
    weatherStore.fetchCurrentWeather()
  }, 30 * 60 * 1000)
})
</script>
```

**Step 2: Add WeatherWidget to AppHeader**

Edit `frontend/vue-app/src/components/AppHeader.vue`:

```vue
<script setup>
import { computed } from 'vue'
import { useTelescopeStore } from '@/stores/telescope'
import WeatherWidget from '@/components/WeatherWidget.vue'

const telescopeStore = useTelescopeStore()
// ... rest of script
</script>

<template>
  <header class="h-14 bg-astro-surface border-b border-astro-border flex items-center px-4 gap-4">
    <!-- ... existing header content ... -->

    <div class="flex items-center gap-4">
      <!-- Weather Status -->
      <WeatherWidget />

      <!-- Connection Status -->
      <!-- ... rest of header ... -->
    </div>
  </header>
</template>
```

**Step 3: Test weather widget**

Run `npm run dev` and verify:
- Weather widget appears in header
- Shows temperature and quality
- Updates from backend API

**Step 4: Commit**

```bash
git add frontend/vue-app/src/components/WeatherWidget.vue frontend/vue-app/src/components/AppHeader.vue
git commit -m "feat: add weather widget to header with live updates"
```

---

### Task 15: Implement PlanningView UI

**Files:**
- Modify: `frontend/vue-app/src/views/PlanningView.vue`
- Create: `frontend/vue-app/src/components/planning/PlanningControls.vue`
- Create: `frontend/vue-app/src/components/planning/PlanTimeline.vue`

**Step 1: Create PlanningControls component**

Create `frontend/vue-app/src/components/planning/PlanningControls.vue`:

```vue
<template>
  <div class="planning-controls space-y-4 p-4">
    <section>
      <h3 class="text-sm font-semibold text-astro-text-muted mb-3">
        OBSERVATION SESSION
      </h3>

      <div class="space-y-3">
        <div>
          <label class="block text-xs text-astro-text-muted mb-1">Date</label>
          <input
            v-model="planningStore.observationDate"
            type="date"
            class="w-full px-3 py-2 bg-astro-elevated border border-astro-border rounded text-astro-text focus:outline-none focus:border-astro-accent"
          />
        </div>

        <div>
          <label class="block text-xs text-astro-text-muted mb-1">Location</label>
          <div class="text-xs text-astro-text">
            {{ planningStore.location.latitude }}°N, {{ planningStore.location.longitude }}°W
          </div>
        </div>
      </div>
    </section>

    <section>
      <h3 class="text-sm font-semibold text-astro-text-muted mb-3">
        TARGETS ({{ planningStore.targetCount }})
      </h3>

      <div v-if="planningStore.hasTargets" class="space-y-2">
        <div
          v-for="target in planningStore.selectedTargets"
          :key="target.id"
          class="flex items-center justify-between p-2 bg-astro-elevated rounded"
        >
          <span class="text-sm text-astro-text">{{ target.name }}</span>
          <button
            @click="planningStore.removeTarget(target.id)"
            class="text-astro-error hover:text-red-400 text-xs"
          >
            Remove
          </button>
        </div>
      </div>

      <div v-else class="text-xs text-astro-text-dim">
        No targets selected. Add targets from Discovery view.
      </div>
    </section>

    <section>
      <h3 class="text-sm font-semibold text-astro-text-muted mb-3">
        CONSTRAINTS
      </h3>

      <div class="space-y-3">
        <div>
          <label class="block text-xs text-astro-text-muted mb-1">
            Altitude Range: {{ planningStore.constraints.min_altitude }}° - {{ planningStore.constraints.max_altitude }}°
          </label>
          <div class="flex gap-2">
            <input
              v-model.number="planningStore.constraints.min_altitude"
              type="range"
              min="0"
              max="90"
              class="flex-1"
            />
            <input
              v-model.number="planningStore.constraints.max_altitude"
              type="range"
              min="0"
              max="90"
              class="flex-1"
            />
          </div>
        </div>

        <div class="flex items-center gap-2">
          <input
            v-model="planningStore.constraints.avoid_moon"
            type="checkbox"
            id="avoid-moon"
            class="rounded border-astro-border"
          />
          <label for="avoid-moon" class="text-sm text-astro-text">
            Avoid Moon
          </label>
        </div>
      </div>
    </section>

    <section>
      <BaseButton
        variant="primary"
        @click="generatePlan"
        :disabled="!planningStore.hasTargets || planningStore.loading"
        class="w-full"
      >
        {{ planningStore.loading ? 'Generating...' : 'Generate Plan' }}
      </BaseButton>
    </section>
  </div>
</template>

<script setup>
import { usePlanningStore } from '@/stores/planning'
import BaseButton from '@/components/common/BaseButton.vue'

const planningStore = usePlanningStore()

const generatePlan = async () => {
  await planningStore.generatePlan()
}
</script>
```

**Step 2: Update PlanningView to use controls**

Edit `frontend/vue-app/src/views/PlanningView.vue`:

```vue
<template>
  <div class="planning-view flex h-full">
    <div class="planning-sidebar w-80 border-r border-astro-border bg-astro-surface overflow-y-auto">
      <PlanningControls />
    </div>

    <div class="planning-main flex-1 p-6">
      <div v-if="planningStore.currentPlan">
        <h2 class="text-2xl font-semibold text-astro-text mb-4">
          Generated Plan
        </h2>

        <BaseCard>
          <div class="space-y-4">
            <div v-for="target in planningStore.currentPlan.targets" :key="target.name">
              <div class="flex justify-between items-center">
                <span class="text-astro-text font-medium">{{ target.name }}</span>
                <span class="text-sm text-astro-text-muted">
                  {{ target.start_time }} - {{ target.duration }}min
                </span>
              </div>
            </div>
          </div>
        </BaseCard>
      </div>

      <div v-else class="flex items-center justify-center h-full">
        <div class="text-center">
          <p class="text-astro-text-muted mb-4">
            No plan generated yet
          </p>
          <p class="text-sm text-astro-text-dim">
            Add targets and click "Generate Plan"
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { usePlanningStore } from '@/stores/planning'
import PlanningControls from '@/components/planning/PlanningControls.vue'
import BaseCard from '@/components/common/BaseCard.vue'

const planningStore = usePlanningStore()
</script>
```

**Step 3: Test planning view**

Run `npm run dev`, navigate to Planning view:
- Add targets from Discovery
- Verify targets appear in list
- Click "Generate Plan"
- Verify plan displays

**Step 4: Commit**

```bash
git add frontend/vue-app/src/views/PlanningView.vue frontend/vue-app/src/components/planning/
git commit -m "feat: implement planning view with controls and plan display"
```

---

### Task 16: Implement ExecutionView with Plan Execution

**Files:**
- Modify: `frontend/vue-app/src/views/ExecutionView.vue`
- Modify: `frontend/vue-app/src/components/execution/TelescopePanel.vue`

**Step 1: Update TelescopePanel**

Edit `frontend/vue-app/src/components/execution/TelescopePanel.vue`:

```vue
<template>
  <BaseCard padding="md">
    <h3 class="text-sm font-semibold text-astro-text-muted mb-3">
      TELESCOPE CONNECTION
    </h3>

    <div v-if="!executionStore.connected" class="space-y-3">
      <BaseInput
        v-model="telescopeIp"
        type="text"
        placeholder="192.168.1.100"
        :error="!!executionStore.error"
      />

      <BaseButton
        variant="primary"
        @click="connect"
        class="w-full"
      >
        Connect
      </BaseButton>

      <div v-if="executionStore.error" class="text-xs text-astro-error">
        {{ executionStore.error }}
      </div>
    </div>

    <div v-else class="space-y-3">
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 bg-astro-success rounded-full"></span>
        <span class="text-sm text-astro-text">Connected to {{ executionStore.telescopeIp }}</span>
      </div>

      <BaseButton
        variant="secondary"
        @click="executionStore.disconnectTelescope()"
        class="w-full"
      >
        Disconnect
      </BaseButton>
    </div>
  </BaseCard>
</template>

<script setup>
import { ref } from 'vue'
import { useExecutionStore } from '@/stores/execution'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseInput from '@/components/common/BaseInput.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const executionStore = useExecutionStore()
const telescopeIp = ref('192.168.1.100')

const connect = async () => {
  await executionStore.connectTelescope(telescopeIp.value)
}
</script>
```

**Step 2: Update ExecutionView**

Edit `frontend/vue-app/src/views/ExecutionView.vue`:

```vue
<template>
  <div class="execution-view flex h-full">
    <div class="execution-sidebar w-80 border-r border-astro-border bg-astro-surface overflow-y-auto space-y-4 p-4">
      <!-- Plan Execution Panel -->
      <BaseCard v-if="executionStore.currentPlan" padding="md">
        <h3 class="text-sm font-semibold text-astro-text-muted mb-3">
          PLAN EXECUTION
        </h3>

        <div class="space-y-3">
          <div class="text-sm text-astro-text">
            Target {{ executionStore.currentTargetIndex + 1 }} of {{ executionStore.currentPlan.targets.length }}
          </div>

          <BaseButton
            v-if="!executionStore.planExecuting"
            variant="primary"
            @click="executionStore.executePlan()"
            :disabled="!executionStore.connected"
            class="w-full"
          >
            Execute Plan
          </BaseButton>

          <div v-else class="space-y-2">
            <BaseButton
              variant="secondary"
              @click="executionStore.pausePlan()"
              class="w-full"
            >
              Pause
            </BaseButton>

            <BaseButton
              variant="danger"
              @click="executionStore.stopPlan()"
              class="w-full"
            >
              Stop
            </BaseButton>
          </div>
        </div>
      </BaseCard>

      <TelescopePanel />
      <ImagingPanel />
      <HardwarePanel />
      <MessagesPanel />
    </div>

    <div class="execution-main flex-1 p-6">
      <div v-if="executionStore.currentTarget" class="space-y-6">
        <div class="text-center">
          <h2 class="text-3xl font-semibold text-astro-text mb-2">
            {{ executionStore.currentTarget.name }}
          </h2>
          <p class="text-sm text-astro-text-muted">
            {{ executionStore.currentTarget.type }}
          </p>
        </div>

        <BaseCard>
          <div class="grid grid-cols-2 gap-4 text-center">
            <div>
              <div class="text-xs text-astro-text-muted">RA</div>
              <div class="text-lg text-astro-text font-mono">
                {{ formatRA(executionStore.position.ra) }}
              </div>
            </div>
            <div>
              <div class="text-xs text-astro-text-muted">Dec</div>
              <div class="text-lg text-astro-text font-mono">
                {{ formatDec(executionStore.position.dec) }}
              </div>
            </div>
            <div>
              <div class="text-xs text-astro-text-muted">Alt</div>
              <div class="text-lg text-astro-text font-mono">
                {{ executionStore.position.alt.toFixed(1) }}°
              </div>
            </div>
            <div>
              <div class="text-xs text-astro-text-muted">Az</div>
              <div class="text-lg text-astro-text font-mono">
                {{ executionStore.position.az.toFixed(1) }}°
              </div>
            </div>
          </div>
        </BaseCard>

        <div v-if="executionStore.imaging.active">
          <div class="text-sm text-astro-text-muted mb-2">
            Progress: {{ executionStore.progressPercent }}%
          </div>
          <div class="w-full bg-astro-elevated rounded-full h-2">
            <div
              class="bg-astro-accent h-2 rounded-full transition-all"
              :style="{ width: executionStore.progressPercent + '%' }"
            ></div>
          </div>
        </div>
      </div>

      <div v-else class="flex items-center justify-center h-full">
        <p class="text-astro-text-muted">
          Load a plan or connect telescope to begin
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useExecutionStore } from '@/stores/execution'
import TelescopePanel from '@/components/execution/TelescopePanel.vue'
import ImagingPanel from '@/components/execution/ImagingPanel.vue'
import HardwarePanel from '@/components/execution/HardwarePanel.vue'
import MessagesPanel from '@/components/execution/MessagesPanel.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const executionStore = useExecutionStore()

const formatRA = (ra) => {
  const hours = ra / 15
  const h = Math.floor(hours)
  const m = Math.floor((hours - h) * 60)
  const s = Math.floor(((hours - h) * 60 - m) * 60)
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const formatDec = (dec) => {
  const sign = dec >= 0 ? '+' : '-'
  const absDec = Math.abs(dec)
  const d = Math.floor(absDec)
  const m = Math.floor((absDec - d) * 60)
  const s = Math.floor(((absDec - d) * 60 - m) * 60)
  return `${sign}${d.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}
</script>
```

**Step 3: Test execution view**

Run `npm run dev`, navigate to Execution:
- Verify panels render
- Test telescope connection (if backend running)
- Verify position displays

**Step 4: Commit**

```bash
git add frontend/vue-app/src/views/ExecutionView.vue frontend/vue-app/src/components/execution/
git commit -m "feat: implement execution view with telescope control and plan execution"
```

---

### Task 17: Implement ProcessingView

**Files:**
- Modify: `frontend/vue-app/src/views/ProcessingView.vue`
- Create: `frontend/vue-app/src/components/processing/FileBrowser.vue`

**Step 1: Create FileBrowser component**

Create `frontend/vue-app/src/components/processing/FileBrowser.vue`:

```vue
<template>
  <BaseCard padding="md">
    <h3 class="text-sm font-semibold text-astro-text-muted mb-3">
      FILE BROWSER
    </h3>

    <div class="space-y-2">
      <div class="text-xs text-astro-text-dim">
        {{ processingStore.currentDirectory }}
      </div>

      <div v-if="processingStore.loading" class="text-sm text-astro-text-muted">
        Loading files...
      </div>

      <div v-else-if="processingStore.files.length > 0" class="space-y-1 max-h-96 overflow-y-auto">
        <div
          v-for="file in processingStore.files"
          :key="file.path"
          @click="processingStore.selectFile(file)"
          class="flex items-center justify-between p-2 rounded hover:bg-astro-elevated cursor-pointer"
          :class="{ 'bg-astro-accent/20': isSelected(file) }"
        >
          <span class="text-sm text-astro-text truncate">{{ file.name }}</span>
          <span class="text-xs text-astro-text-dim">{{ formatSize(file.size) }}</span>
        </div>
      </div>

      <div v-else class="text-sm text-astro-text-dim">
        No FITS files found
      </div>

      <div v-if="processingStore.selectedFileCount > 0" class="pt-2 border-t border-astro-border">
        <div class="text-xs text-astro-text-muted mb-2">
          {{ processingStore.selectedFileCount }} files selected
        </div>

        <BaseButton
          variant="secondary"
          @click="processingStore.clearSelection()"
          size="sm"
          class="w-full"
        >
          Clear Selection
        </BaseButton>
      </div>
    </div>
  </BaseCard>
</template>

<script setup>
import { onMounted } from 'vue'
import { useProcessingStore } from '@/stores/processing'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const processingStore = useProcessingStore()

const isSelected = (file) => {
  return processingStore.selectedFiles.includes(file)
}

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

onMounted(() => {
  processingStore.browseDirectory('/data')
})
</script>
```

**Step 2: Update ProcessingView**

Edit `frontend/vue-app/src/views/ProcessingView.vue`:

```vue
<template>
  <div class="processing-view flex h-full">
    <div class="processing-sidebar w-80 border-r border-astro-border bg-astro-surface overflow-y-auto p-4">
      <FileBrowser />
    </div>

    <div class="processing-main flex-1 flex flex-col">
      <div class="flex-1 p-6">
        <div v-if="processingStore.previewImage" class="h-full flex items-center justify-center">
          <img
            :src="processingStore.previewImage"
            alt="Preview"
            class="max-w-full max-h-full object-contain"
          />
        </div>

        <div v-else class="h-full flex items-center justify-center">
          <p class="text-astro-text-muted">
            No preview available
          </p>
        </div>
      </div>
    </div>

    <div class="processing-controls w-80 border-l border-astro-border bg-astro-surface overflow-y-auto p-4 space-y-4">
      <BaseCard padding="md">
        <h3 class="text-sm font-semibold text-astro-text-muted mb-3">
          PROCESSING
        </h3>

        <div class="space-y-3">
          <BaseButton
            variant="primary"
            @click="processingStore.stackImages()"
            :disabled="!processingStore.hasSelection"
            class="w-full"
          >
            Stack Images
          </BaseButton>

          <div v-if="processingStore.activeJob" class="text-xs text-astro-text-muted">
            Processing: {{ processingStore.activeJob.status }}
          </div>
        </div>
      </BaseCard>
    </div>
  </div>
</template>

<script setup>
import { useProcessingStore } from '@/stores/processing'
import FileBrowser from '@/components/processing/FileBrowser.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const processingStore = useProcessingStore()
</script>
```

**Step 3: Test processing view**

Run `npm run dev`, navigate to Processing:
- Verify file browser renders
- Test file selection
- Verify stack button enables/disables

**Step 4: Commit**

```bash
git add frontend/vue-app/src/views/ProcessingView.vue frontend/vue-app/src/components/processing/FileBrowser.vue
git commit -m "feat: implement processing view with file browser and stacking"
```

---

## Final Verification

### Task 18: Run Full Test Suite

**Step 1: Run all unit tests**

Run:
```bash
cd frontend/vue-app
npm test
```

Expected: All tests pass

**Step 2: Check test coverage**

Run:
```bash
npm run test:coverage
```

Expected: Coverage > 75%

**Step 3: Build production**

Run:
```bash
npm run build
```

Expected: Build succeeds with no errors

**Step 4: Manual testing checklist**

With backend running, verify:
- [ ] Discovery view loads catalog data
- [ ] Search and filters work
- [ ] Can add targets to plan
- [ ] Planning view generates plan
- [ ] Weather widget shows data
- [ ] Execution view connects to telescope
- [ ] Processing view browses files
- [ ] All panels collapse/expand
- [ ] Theme is dark scientific (no cyan)
- [ ] No console errors

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete astronomus UX modernization

- Dark scientific theme applied throughout
- All stores functional with API integration
- Discovery, Planning, Execution, Processing views working
- Weather integration complete
- Telescope control implemented
- Test coverage > 75%
"
```

---

## Success Criteria

**Theme:**
- ✅ No bright cyan (#00d9ff) visible anywhere
- ✅ Dark scientific palette (astro-*) consistently applied
- ✅ Professional, subtle aesthetic
- ✅ Readable text hierarchy

**Functionality:**
- ✅ Catalog search returns results
- ✅ Filters work (type, constellation, magnitude)
- ✅ Weather data displays
- ✅ Plans generate successfully
- ✅ Telescope connects (if hardware available)
- ✅ Processing stacks images

**Code Quality:**
- ✅ Test coverage > 75%
- ✅ All tests passing
- ✅ Modern Vue 3 Composition API
- ✅ No vanilla JS legacy code
- ✅ Clean component architecture

---

## Execution Choice

Plan complete and saved to `docs/plans/2026-02-14-astronomus-modernization-implementation.md`.

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
