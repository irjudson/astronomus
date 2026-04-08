# IA Redesign: Tonight / Sky / Plan / Observe / Archive

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Use `haiku` model for spec/quality reviewers; `sonnet` for implementers.

**Goal:** Replace the Discovery/Planning/Execution/Processing navigation with a user-intent-driven IA (Tonight/Sky/Plan/Observe/Archive) and overhaul the Observe view with progressive disclosure.

**Architecture:** The navigation is a top-level rename + new Tonight view + Observe view restructure. No backend changes. All changes are in `frontend/vue-app/src/`. The Observe view gets a unified left panel (collapsible sections replacing the mode toggle) and a Tier 2 Controls drawer for advanced settings. Tonight is a simple dashboard. Archive replaces the broken Processing tab.

**Tech Stack:** Vue 3 Composition API, Pinia, Tailwind CSS, lucide-vue-next icons, existing stores (`execution.js`, `planning.js`, `catalog.js`, `settings.js`)

**Scope note:** Responsive nav (sidebar desktop, bottom bar mobile) is out of scope. The existing top-nav `AppHeader` is kept; only labels and routes change. Full Settings restructure (WiFi, polar align) stays in the existing SettingsModal.

---

## Task 1: Rename routes and navigation labels

**Files:**
- Modify: `frontend/vue-app/src/router/index.js`
- Modify: `frontend/vue-app/src/components/shared/AppHeader.vue`

No tests needed — router test file exists at `frontend/vue-app/src/router/__tests__/router.test.js`, update route names there.

**Step 1: Update router/index.js**

Current routes:
- `/` → DiscoveryView (name: 'discovery')
- `/plan` → PlanningView (name: 'plan')
- `/execute` → ExecutionView (name: 'execute')
- `/process` → ProcessingView (name: 'process')

New routes:
```javascript
import TonightView from '@/views/TonightView.vue'

export const routes = [
  {
    path: '/',
    name: 'tonight',
    component: TonightView
  },
  {
    path: '/sky',
    name: 'sky',
    component: () => import('@/views/DiscoveryView.vue')
  },
  {
    path: '/plan',
    name: 'plan',
    component: () => import('@/views/PlanningView.vue')
  },
  {
    path: '/observe',
    name: 'observe',
    component: () => import('@/views/ExecutionView.vue')
  },
  {
    path: '/archive',
    name: 'archive',
    component: () => import('@/views/ProcessingView.vue')
  },
  // Legacy redirects so existing bookmarks keep working
  { path: '/execute', redirect: '/observe' },
  { path: '/process', redirect: '/archive' },
]
```

**Step 2: Update AppHeader.vue nav links**

Replace the four nav links with five:
```html
<router-link to="/">Tonight</router-link>
<router-link to="/sky">Sky</router-link>
<router-link to="/plan">Plan</router-link>
<router-link to="/observe">Observe</router-link>
<router-link to="/archive">Archive</router-link>
```

Update active-class checks to use `startsWith('/sky')`, `startsWith('/observe')`, `startsWith('/archive')`. Root `/` uses `$route.path === '/'`.

**Step 3: Update router test**

In `router/__tests__/router.test.js`, update expected route names and paths to match new values.

**Step 4: Verify**

```bash
cd /home/irjudson/Projects/astronomus/frontend/vue-app && npm run build 2>&1 | tail -5
```
Expected: no errors, build completes.

**Step 5: Commit**

```bash
git add frontend/vue-app/src/router/index.js frontend/vue-app/src/components/shared/AppHeader.vue frontend/vue-app/src/router/__tests__/
git commit -m "feat: rename nav sections to Tonight/Sky/Plan/Observe/Archive with legacy redirects"
```

---

## Task 2: Create TonightView.vue

**Files:**
- Create: `frontend/vue-app/src/views/TonightView.vue`

**Purpose:** Dashboard landing page. Shows tonight's conditions, moon phase, a quick-connect shortcut, and the active plan summary. No new API endpoints needed — reuses existing stores.

**Step 1: Create TonightView.vue**

```vue
<template>
  <div class="h-full overflow-y-auto bg-gray-950 p-6 space-y-6 max-w-4xl mx-auto">

    <!-- Header row -->
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-semibold text-gray-100">Tonight</h1>
      <div class="text-sm text-gray-500">{{ todayLabel }}</div>
    </div>

    <!-- Conditions + Connect row -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">

      <!-- Weather card -->
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <h2 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Conditions</h2>
        <div v-if="weather.local" class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-400">Temperature</span>
            <span class="text-sm font-mono text-gray-200">{{ weather.local.temperature_f?.toFixed(0) }}°F</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-400">Humidity</span>
            <span class="text-sm font-mono text-gray-200">{{ weather.local.humidity }}%</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-400">Wind</span>
            <span class="text-sm font-mono text-gray-200">{{ weather.local.wind_speed_mph?.toFixed(0) }} mph</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-gray-400">Suitability</span>
            <span
              class="text-sm font-medium"
              :class="weather.local.astronomy_score >= 0.7 ? 'text-green-400' : weather.local.astronomy_score >= 0.4 ? 'text-amber-400' : 'text-red-400'"
            >{{ suitabilityLabel }}</span>
          </div>
        </div>
        <div v-else class="text-sm text-gray-600">No local weather data</div>
      </div>

      <!-- Telescope connect card -->
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
        <h2 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Telescope</h2>
        <div v-if="executionStore.connected" class="space-y-2">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-green-400"></div>
            <span class="text-sm text-green-400">Connected</span>
          </div>
          <div class="text-xs text-gray-500">{{ executionStore.connectionInfo?.host }}</div>
          <router-link
            to="/observe"
            class="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
          >Go to Observe →</router-link>
        </div>
        <div v-else class="space-y-3">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-gray-600"></div>
            <span class="text-sm text-gray-500">Not connected</span>
          </div>
          <router-link
            to="/observe"
            class="inline-flex items-center gap-1 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded border border-gray-700 transition-colors"
          >Connect in Observe →</router-link>
        </div>
      </div>
    </div>

    <!-- Active plan card -->
    <div class="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <h2 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Tonight's Plan</h2>
      <template v-if="planningStore.currentPlan">
        <div class="flex items-center justify-between mb-3">
          <span class="text-sm font-medium text-gray-200">{{ planningStore.planName }}</span>
          <span class="text-xs text-gray-500">{{ planningStore.currentPlan.scheduled_targets?.length || 0 }} targets</span>
        </div>
        <div class="text-xs text-gray-500 mb-3">
          {{ planningStore.currentPlan.session?.imaging_start ? formatSessionTime(planningStore.currentPlan.session.imaging_start) : '' }}
          –
          {{ planningStore.currentPlan.session?.imaging_end ? formatSessionTime(planningStore.currentPlan.session.imaging_end) : '' }}
        </div>
        <router-link
          to="/observe"
          class="inline-flex items-center gap-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
        >Execute Plan →</router-link>
      </template>
      <template v-else>
        <p class="text-sm text-gray-500 mb-3">No plan loaded for tonight.</p>
        <router-link
          to="/plan"
          class="inline-flex items-center gap-1 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded border border-gray-700 transition-colors"
        >Create a Plan →</router-link>
      </template>
    </div>

    <!-- Quick links -->
    <div class="grid grid-cols-3 gap-3">
      <router-link to="/sky"
        class="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition-colors text-center"
      >
        <div class="text-2xl mb-1">🔭</div>
        <div class="text-xs font-medium text-gray-300">Browse Sky</div>
      </router-link>
      <router-link to="/plan"
        class="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition-colors text-center"
      >
        <div class="text-2xl mb-1">📅</div>
        <div class="text-xs font-medium text-gray-300">Plan Session</div>
      </router-link>
      <router-link to="/archive"
        class="bg-gray-900 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition-colors text-center"
      >
        <div class="text-2xl mb-1">🗂️</div>
        <div class="text-xs font-medium text-gray-300">Archive</div>
      </router-link>
    </div>

  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useExecutionStore } from '@/stores/execution'
import { usePlanningStore } from '@/stores/planning'
import { useWeatherStore } from '@/stores/weather'

const executionStore = useExecutionStore()
const planningStore = usePlanningStore()
const weather = useWeatherStore()

const todayLabel = computed(() =>
  new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })
)

const suitabilityLabel = computed(() => {
  const s = weather.local?.astronomy_score
  if (s == null) return '—'
  return s >= 0.7 ? 'Good' : s >= 0.4 ? 'Fair' : 'Poor'
})

const formatSessionTime = (iso) =>
  new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })

onMounted(() => {
  if (!weather.local) weather.fetchLocalWeather?.()
  planningStore.loadSavedPlans()
})
</script>
```

**Step 2: Check weather store name**

Read `frontend/vue-app/src/stores/weather.js` to confirm store export name and `fetchLocalWeather` action name. Adjust imports if different.

**Step 3: Build verify**

```bash
cd /home/irjudson/Projects/astronomus/frontend/vue-app && npm run build 2>&1 | tail -5
```

**Step 4: Commit**

```bash
git add frontend/vue-app/src/views/TonightView.vue
git commit -m "feat: add TonightView dashboard with conditions, plan status, and quick links"
```

---

## Task 3: Refactor Observe left panel — unified collapsible sections

**Files:**
- Modify: `frontend/vue-app/src/views/ExecutionView.vue`

**Problem:** Current ExecutionView has a Plan/Manual mode toggle, showing different left panel content per mode. The mode concept is confusing and hides functionality.

**Solution:** Remove the mode toggle. The left panel always shows:
1. **Scope** (TelescopePanel) — always expanded
2. **Goto** — collapsible, contains the goto input + Slew button
3. **Movement** — collapsible, contains DirectionalControlPanel
4. **Messages** — collapsible (already exists)

The main area always shows:
- PlanTimeline (if plan loaded) — full width above
- LivePreviewPanel — main content, full remaining height
- NowPlayingPanel — overlaid bottom of preview as a strip (when plan running), not a side column

**Step 1: Read current ExecutionView.vue** (already read — 335 lines)

**Step 2: Rewrite ExecutionView.vue**

Key structural changes from the current file:
- Remove `activeMode` / `setMode` / localStorage mode toggle
- Remove the entire `v-else` manual mode template block
- Keep `gotoInput`, `doSlew` — move to always-visible Goto section in left panel
- Keep `loadAndStagePlan`, `loadingPlanId`, plan list when no plan
- Left panel: TelescopePanel + collapsible Goto + collapsible Movement + collapsible Messages
- Main area: PlanTimeline (if plan) + LivePreviewPanel (always) + NowPlayingPanel strip (if running)

```vue
<template>
  <PanelContainer v-model:left-panel-visible="leftPanelVisible" :console-visible="false">

    <template #left-header>
      <h3 class="text-sm font-semibold text-gray-200">Scope</h3>
    </template>
    <template #left-label>Scope</template>

    <template #left>
      <div class="p-4 space-y-4">

        <!-- Telescope connection -->
        <TelescopePanel />

        <!-- Goto -->
        <div class="border-t border-gray-800 pt-4">
          <button @click="gotoOpen = !gotoOpen"
            class="flex items-center justify-between w-full text-left mb-2 group">
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide group-hover:text-gray-300 transition-colors">Goto</h4>
            <ChevronDownIcon class="w-3.5 h-3.5 text-gray-600 group-hover:text-gray-400 transition-all"
              :class="gotoOpen ? 'rotate-0' : '-rotate-90'" />
          </button>
          <div v-show="gotoOpen" class="flex gap-2">
            <input
              v-model="gotoInput"
              placeholder="Object name or RA Dec"
              class="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200 placeholder-gray-600 focus:border-blue-500 focus:outline-none"
              @keydown.enter="doSlew"
            />
            <button
              @click="doSlew"
              :disabled="!executionStore.connected || !gotoInput.trim()"
              class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >Go</button>
          </div>
        </div>

        <!-- Movement -->
        <div class="border-t border-gray-800 pt-4">
          <button @click="moveOpen = !moveOpen"
            class="flex items-center justify-between w-full text-left mb-2 group">
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide group-hover:text-gray-300 transition-colors">Movement</h4>
            <ChevronDownIcon class="w-3.5 h-3.5 text-gray-600 group-hover:text-gray-400 transition-all"
              :class="moveOpen ? 'rotate-0' : '-rotate-90'" />
          </button>
          <div v-show="moveOpen">
            <DirectionalControlPanel />
          </div>
        </div>

        <!-- Status strip (when connected) -->
        <div v-if="executionStore.connected" class="border-t border-gray-800 pt-4">
          <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            <div><span class="text-gray-500">RA:</span>
              <span class="font-mono text-gray-200 ml-1">{{ executionStore.position?.ra != null ? formatRA(executionStore.position.ra) : '--' }}</span></div>
            <div><span class="text-gray-500">Dec:</span>
              <span class="font-mono text-gray-200 ml-1">{{ executionStore.position?.dec != null ? formatDec(executionStore.position.dec) : '--' }}</span></div>
            <div><span class="text-gray-500">Alt:</span>
              <span class="font-mono text-gray-200 ml-1">{{ executionStore.position?.alt != null ? executionStore.position.alt.toFixed(1) + '°' : '--' }}</span></div>
            <div><span class="text-gray-500">Az:</span>
              <span class="font-mono text-gray-200 ml-1">{{ executionStore.position?.az != null ? executionStore.position.az.toFixed(1) + '°' : '--' }}</span></div>
            <div><span class="text-gray-500">Track:</span>
              <span class="ml-1"
                :class="executionStore.hardware.trackingStatus === 'Active' ? 'text-green-400' : 'text-gray-400'"
              >{{ executionStore.hardware.trackingStatus }}</span></div>
            <div><span class="text-gray-500">Level:</span>
              <span class="ml-1" :class="levelClass(executionStore.balance.angle)">
                {{ executionStore.balance.angle != null ? executionStore.balance.angle.toFixed(1) + '°' : '—' }}
              </span></div>
          </div>
        </div>

        <!-- Messages -->
        <div class="border-t border-gray-800 pt-4">
          <button @click="msgOpen = !msgOpen"
            class="flex items-center justify-between w-full text-left mb-2 group">
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide group-hover:text-gray-300 transition-colors">Messages</h4>
            <ChevronDownIcon class="w-3.5 h-3.5 text-gray-600 group-hover:text-gray-400 transition-all"
              :class="msgOpen ? 'rotate-0' : '-rotate-90'" />
          </button>
          <MessagesPanel v-show="msgOpen" />
        </div>

      </div>
    </template>

    <!-- Main -->
    <template #main>
      <div class="flex flex-col h-full">

        <!-- Plan timeline (when plan loaded) -->
        <div v-if="planningStore.currentPlan" class="bg-gray-900/50 border-b border-gray-800 px-4 py-3 flex-none">
          <PlanTimeline
            :plan="planningStore.currentPlan"
            @select-target="() => {}"
          />
        </div>

        <!-- Live preview — fills remaining height -->
        <div class="flex-1 relative overflow-hidden">
          <LivePreviewPanel class="h-full" />

          <!-- NowPlayingPanel: overlaid strip at bottom when plan is running -->
          <div
            v-if="planningStore.currentPlan && executionStore.executionStatus !== 'idle'"
            class="absolute bottom-0 left-0 right-0 bg-gray-950/90 backdrop-blur-sm border-t border-gray-800"
          >
            <NowPlayingPanel />
          </div>
        </div>

        <!-- No plan loaded — show plan selector below preview -->
        <div v-if="!planningStore.currentPlan" class="border-t border-gray-800 p-4 flex-none">
          <div class="flex items-center gap-4 flex-wrap">
            <p class="text-sm text-gray-500">No plan loaded.</p>
            <div v-if="planningStore.savedPlans.length > 0" class="flex gap-2 flex-wrap">
              <button
                v-for="plan in planningStore.savedPlans.slice(0, 3)"
                :key="plan.id"
                @click="loadAndStagePlan(plan.id)"
                :disabled="loadingPlanId === plan.id"
                class="px-3 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded border border-gray-700 transition-colors disabled:opacity-50"
              >{{ loadingPlanId === plan.id ? '...' : plan.name }}</button>
            </div>
            <router-link to="/plan" class="text-xs text-blue-400 hover:text-blue-300">→ Plan</router-link>
          </div>
        </div>

      </div>
    </template>

  </PanelContainer>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { ChevronDownIcon } from 'lucide-vue-next'
import { useExecutionStore } from '@/stores/execution'
import { usePlanningStore } from '@/stores/planning'
import { useToastStore } from '@/stores/toast'
import PanelContainer from '@/components/layout/PanelContainer.vue'
import TelescopePanel from '@/components/execution/TelescopePanel.vue'
import DirectionalControlPanel from '@/components/execution/DirectionalControlPanel.vue'
import ImagingPanel from '@/components/execution/ImagingPanel.vue'
import LivePreviewPanel from '@/components/execution/LivePreviewPanel.vue'
import MessagesPanel from '@/components/execution/MessagesPanel.vue'
import NowPlayingPanel from '@/components/execution/NowPlayingPanel.vue'
import PlanTimeline from '@/components/planning/PlanTimeline.vue'

const executionStore = useExecutionStore()
const planningStore = usePlanningStore()
const toastStore = useToastStore()

const leftPanelVisible = ref(true)
const gotoOpen = ref(true)
const moveOpen = ref(false)
const msgOpen = ref(false)
const gotoInput = ref('')
const loadingPlanId = ref(null)

watch(() => executionStore.connected, (newVal, oldVal) => {
  if (oldVal && !newVal && executionStore.executionStatus === 'running') {
    toastStore.error('Telescope connection lost during plan execution')
  }
})

const doSlew = async () => {
  const input = gotoInput.value.trim()
  if (!input || !executionStore.connected) return
  await executionStore.slewToTarget({ name: input, ra: null, dec: null })
}

const PLANETARY_TYPES = new Set(['planet', 'moon', 'sun'])

const transformPlan = (name, observingPlan) => ({
  name,
  targets: (observingPlan.scheduled_targets || []).map(st => ({
    name: st.target.common_name || st.target.name || st.target.catalog_id,
    ra: st.target.ra_hours * 15,
    dec: st.target.dec_degrees,
    exposure: st.recommended_exposure || 10,
    frames: st.recommended_frames || 50,
    gain: 80,
    object_type: st.target.object_type,
    imaging_mode: PLANETARY_TYPES.has((st.target.object_type || '').toLowerCase()) ? 'planetary' : 'deep-sky',
  })),
})

const loadAndStagePlan = async (id) => {
  loadingPlanId.value = id
  try {
    const detail = await planningStore.loadPlan(id)
    const transformed = transformPlan(detail.name, detail.plan)
    executionStore.setPlan(transformed, detail.plan.scheduled_targets || [])
  } catch {
    // planningStore.loadPlan already shows a toast on failure
  } finally {
    loadingPlanId.value = null
  }
}

onMounted(async () => {
  await planningStore.loadSavedPlans()
})

function levelClass(angle) {
  if (angle == null) return 'text-gray-500'
  const abs = Math.abs(angle)
  if (abs <= 1.0) return 'text-green-400'
  if (abs <= 3.0) return 'text-amber-400'
  return 'text-red-400'
}

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

**Step 3: Build verify**

```bash
cd /home/irjudson/Projects/astronomus/frontend/vue-app && npm run build 2>&1 | tail -10
```

**Step 4: Commit**

```bash
git add frontend/vue-app/src/views/ExecutionView.vue
git commit -m "feat: unify Observe left panel — remove mode toggle, add collapsible Goto/Movement/Status/Messages"
```

---

## Task 4: Create ControlsDrawer.vue (Tier 2 advanced controls)

**Files:**
- Create: `frontend/vue-app/src/components/observe/ControlsDrawer.vue`
- Modify: `frontend/vue-app/src/views/ExecutionView.vue` (add drawer button + component)

**Purpose:** A collapsible drawer in the left panel exposing Tier 2 controls: Gain, Exposure, Focus (auto + manual slider), Dew Heater, Annotations, Stack Reset. Only shown when telescope is connected.

**Step 1: Create `frontend/vue-app/src/components/observe/` directory**

```bash
mkdir -p /home/irjudson/Projects/astronomus/frontend/vue-app/src/components/observe
```

**Step 2: Create ControlsDrawer.vue**

```vue
<template>
  <div class="border-t border-gray-800 pt-4">
    <button
      @click="open = !open"
      class="flex items-center justify-between w-full text-left mb-2 group"
    >
      <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide group-hover:text-gray-300 transition-colors">
        Controls
      </h4>
      <ChevronDownIcon
        class="w-3.5 h-3.5 text-gray-600 group-hover:text-gray-400 transition-all"
        :class="open ? 'rotate-0' : '-rotate-90'"
      />
    </button>

    <div v-show="open" class="space-y-4">

      <!-- Gain -->
      <div>
        <label class="flex items-center justify-between text-xs text-gray-500 mb-1">
          <span>Gain</span>
          <span class="font-mono text-gray-300">{{ gain }}</span>
        </label>
        <input
          type="range" min="0" max="100" step="1"
          v-model.number="gain"
          @change="applyExposure"
          class="w-full accent-blue-500"
        />
      </div>

      <!-- Exposure -->
      <div>
        <label class="text-xs text-gray-500 block mb-1">Exposure (ms)</label>
        <input
          type="number" min="100" max="60000" step="100"
          v-model.number="exposureMs"
          @change="applyExposure"
          class="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1 text-xs font-mono text-gray-200 focus:border-blue-500 focus:outline-none"
        />
      </div>

      <!-- Autofocus -->
      <div class="flex items-center gap-2">
        <button
          @click="runAutofocus"
          :disabled="autofocusing"
          class="flex-1 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded border border-gray-700 transition-colors disabled:opacity-50"
        >{{ autofocusing ? 'Focusing...' : 'Auto Focus' }}</button>
        <div class="text-xs font-mono text-gray-500">{{ focusPos ?? '—' }}</div>
      </div>

      <!-- Manual focus -->
      <div v-if="focusPos != null">
        <label class="flex items-center justify-between text-xs text-gray-500 mb-1">
          <span>Focus</span>
          <span class="font-mono text-gray-300">{{ focusTarget }}</span>
        </label>
        <input
          type="range" :min="0" :max="focusMax" step="10"
          v-model.number="focusTarget"
          @change="moveFocus"
          class="w-full accent-blue-500"
        />
      </div>

      <!-- Dew heater -->
      <div class="flex items-center justify-between">
        <label class="text-xs text-gray-500">Dew Heater</label>
        <div class="flex items-center gap-2">
          <span class="text-xs text-gray-400">{{ dewPower }}%</span>
          <button
            @click="toggleDewHeater"
            class="relative inline-flex h-5 w-9 items-center rounded-full transition-colors"
            :class="dewEnabled ? 'bg-blue-600' : 'bg-gray-700'"
          >
            <span
              class="inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform"
              :class="dewEnabled ? 'translate-x-4' : 'translate-x-1'"
            />
          </button>
        </div>
      </div>

      <!-- Stack reset -->
      <button
        @click="resetStack"
        class="w-full px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded border border-gray-700 transition-colors"
      >Reset Stack</button>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ChevronDownIcon } from 'lucide-vue-next'
import axios from 'axios'
import { useToastStore } from '@/stores/toast'

const toastStore = useToastStore()

const open = ref(false)
const gain = ref(80)
const exposureMs = ref(10000)
const autofocusing = ref(false)
const focusPos = ref(null)
const focusTarget = ref(0)
const focusMax = 32767  // typical Seestar focuser range
const dewEnabled = ref(false)
const dewPower = ref(90)

async function applyExposure() {
  try {
    await axios.post('/api/telescope/features/exposure', {
      gain: gain.value,
      exposure_ms: exposureMs.value,
    })
  } catch {
    toastStore.error('Failed to set exposure/gain')
  }
}

async function runAutofocus() {
  autofocusing.value = true
  try {
    await axios.post('/api/telescope/features/focus/auto')
    // Refresh focus position
    const res = await axios.get('/api/telescope/features/focus/position')
    focusPos.value = res.data.position
    focusTarget.value = focusPos.value
  } catch {
    toastStore.error('Autofocus failed')
  } finally {
    autofocusing.value = false
  }
}

async function moveFocus() {
  try {
    await axios.post('/api/telescope/features/focus/move', { position: focusTarget.value })
    focusPos.value = focusTarget.value
  } catch {
    toastStore.error('Focus move failed')
  }
}

async function toggleDewHeater() {
  dewEnabled.value = !dewEnabled.value
  try {
    await axios.post('/api/telescope/features/dew-heater', {
      enabled: dewEnabled.value,
      power_level: dewPower.value,
    })
  } catch {
    dewEnabled.value = !dewEnabled.value  // revert
    toastStore.error('Dew heater control failed')
  }
}

async function resetStack() {
  try {
    await axios.post('/api/telescope/features/stack/reset')
    toastStore.info('Stack reset')
  } catch {
    toastStore.error('Stack reset failed')
  }
}

onMounted(async () => {
  // Fetch current focus position if possible
  try {
    const res = await axios.get('/api/telescope/features/focus/position')
    focusPos.value = res.data.position
    focusTarget.value = focusPos.value
  } catch {
    // Not connected yet — will refresh when opened
  }
})
</script>
```

**Step 3: Add ControlsDrawer to ExecutionView.vue left panel**

In the `<template #left>` section, add after the Movement section and before Messages:

```html
<!-- Advanced controls (Tier 2) — only when connected -->
<ControlsDrawer v-if="executionStore.connected" />
```

Add the import:
```javascript
import ControlsDrawer from '@/components/observe/ControlsDrawer.vue'
```

**Step 4: Verify `/api/telescope/features/focus/position` endpoint exists**

Run:
```bash
docker exec astronomus grep -n "focus/position" /app/app/api/telescope_features.py | head -5
```
If missing, note it as a gap (the drawer gracefully handles 404 — `focusPos` stays null, slider is hidden).

**Step 5: Build verify**

```bash
cd /home/irjudson/Projects/astronomus/frontend/vue-app && npm run build 2>&1 | tail -10
```

**Step 6: Commit**

```bash
git add frontend/vue-app/src/components/observe/ControlsDrawer.vue frontend/vue-app/src/views/ExecutionView.vue
git commit -m "feat: add Tier 2 ControlsDrawer to Observe — gain, exposure, focus, dew heater, stack reset"
```

---

## Task 5: Archive view — rename and wire basic file listing

**Files:**
- Modify: `frontend/vue-app/src/views/ProcessingView.vue`

**Purpose:** Rename "Processing" to "Archive" in the view heading, and surface whatever the current ProcessingView shows (even if minimal). If it's broken/empty, replace with a helpful stub that links to image management and capture history.

**Step 1: Read current ProcessingView.vue**

```bash
head -60 /home/irjudson/Projects/astronomus/frontend/vue-app/src/views/ProcessingView.vue
```

**Step 2: Update heading and broken state**

If the view has missing store actions (known P1 issue), wrap broken sections in `v-if` guards to prevent runtime errors. Replace the broken "Processing" heading with "Archive". Show a placeholder for unimplemented sections instead of blank/error state.

Minimal change:
```html
<!-- Replace "Processing" heading with "Archive" -->
<h2 class="text-base font-semibold text-gray-200">Archive</h2>
```

Add stub for unimplemented sections:
```html
<div class="p-6 text-center text-gray-500 text-sm border border-dashed border-gray-700 rounded-lg">
  Image export and TIFF processing coming soon.
  <br/>
  <router-link to="/sky" class="text-blue-400 hover:text-blue-300 mt-2 inline-block">Browse capture history in Sky →</router-link>
</div>
```

**Step 3: Build verify and commit**

```bash
cd /home/irjudson/Projects/astronomus/frontend/vue-app && npm run build 2>&1 | tail -5
git add frontend/vue-app/src/views/ProcessingView.vue
git commit -m "feat: rename Processing to Archive, add placeholder for unimplemented sections"
```

---

## Verification

After all tasks complete, deploy and verify in browser:

```bash
docker compose build && docker compose up -d astronomus
```

1. `/` → Tonight view shows conditions, plan status, quick links
2. Top nav shows: Tonight | Sky | Plan | Observe | Archive
3. `/execute` → redirects to `/observe` (legacy redirect works)
4. `/process` → redirects to `/archive`
5. Observe left panel: TelescopePanel → Goto (open) → Movement (collapsed) → Status (when connected) → Controls (when connected, collapsed) → Messages (collapsed)
6. Controls drawer opens → Gain slider, Exposure input, Auto Focus button, Dew Heater toggle, Reset Stack
7. Observe main area: PlanTimeline when plan loaded; LivePreviewPanel full height; NowPlayingPanel overlaid at bottom when running; plan selector strip when no plan
8. Archive shows "Archive" heading, no runtime errors
9. `docker exec astronomus pytest tests/ -q --no-cov` — still passes (pure frontend changes)
