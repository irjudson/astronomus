# Execution View Redesign


**Goal:** Replace the cluttered collapsible-panel execution view with a focused two-mode layout: Plan Mode (live timeline + now-playing panel) and Manual Mode (live preview + direct controls).

**Architecture:** Four small changes — two new store actions in `execution.js`, a live now-marker tick in `PlanTimeline.vue`, a new `NowPlayingPanel.vue` component, and a full rewrite of `ExecutionView.vue` layout. No backend changes.

**Tech Stack:** Vue 3 Composition API, Pinia, Tailwind CSS, existing execution/planning stores.

---

## Final Design

### Plan Mode (plan loaded, running or idle)
```
┌────────────────────────────── Header ────────────────────────────────┐
│ Live Execution  [Plan Mode ●] [Manual Mode ○]   RA Dec Alt Az Track  │
├──────────────────────────── PlanTimeline ────────────────────────────┤
│ Summary bar + SVG chart (interactive, live now-marker ticks)         │
├──────────────────────────┬───────────────────────────────────────────┤
│                          │ ▶ Now: M51 Whirlpool Galaxy   Stack       │
│   Live Preview           │   ████████░░░░░░░░  62 min remaining     │
│   (MJPEG stream)         │   Alt: 72° ↑ Score: 0.86                 │
│                          │ ─────────────────────────────────────     │
│                          │ ⏭ Next: M81 Bode's Galaxy               │
│                          │   Starts 11:45 PM · in 1h 12m            │
│                          │ ─────────────────────────────────────     │
│                          │ [Skip] [+15 min] [Abort Plan]            │
└──────────────────────────┴───────────────────────────────────────────┘
```

### Plan Mode (no plan loaded)
```
┌────────────────────────── Header ────────────────────────────────────┐
│ Live Execution  [Plan Mode ●] [Manual Mode ○]   (disconnected grey)  │
├──────────────────────────────────────────────────────────────────────┤
│                  No plan loaded for tonight                          │
│                                                                      │
│   Saved Plans                                                        │
│   ┌────────────────────────────────────────────────────────────┐    │
│   │ 2026-03-05 Observation Plan   6 targets                    │    │
│   │                              [Load Plan]                   │    │
│   └────────────────────────────────────────────────────────────┘    │
│                                                                      │
│            [→ Go to Planning to generate a plan]                     │
└──────────────────────────────────────────────────────────────────────┘
```

### Manual Mode
```
┌────────────────────────── Header ────────────────────────────────────┐
│ Live Execution  [Plan Mode ○] [Manual Mode ●]   RA Dec Alt Az Track  │
├──────────────────────────┬───────────────────────────────────────────┤
│                          │ Goto                                      │
│   Live Preview           │   [ Object name / RA Dec ___] [Slew]     │
│   (MJPEG stream)         │ ─────────────────────────────────────     │
│                          │ Capture                                   │
│                          │   [Start Stacking] [Start Preview]       │
│                          │   Dew Heater: Off [Toggle]               │
│                          │ ─────────────────────────────────────     │
│                          │ Status                                    │
│                          │   Track: Inactive  Mode: Alt/Az          │
│                          │   Hdg: 214°SW  Level: 0.3°              │
└──────────────────────────┴───────────────────────────────────────────┘
```

**Left panel (always):** Telescope connection (TelescopePanel) + Messages — same as today.

---

## Task 1: Add skipTarget and extendTarget to execution.js

**Files:**
- Modify: `frontend/vue-app/src/stores/execution.js` (after `resumeExecution` action)

**What to add:** Two new actions. No tests needed (pure store mutation + API calls, same pattern as existing pause/resume).

**skipTarget:**
- Guard: if not running or no plan, return
- Abort current execution: `POST /api/telescope/abort`
- Stop polling
- Increment `currentTargetIndex` (cap at targets.length - 1)
- If no remaining targets: set `executionStatus = 'completed'`, add message, return
- Update `resumeOffset = currentTargetIndex`
- Re-execute remaining targets from new index via `POST /api/telescope/execute`
- Set `executionStatus = 'running'`, restart polling
- Add message `'Skipped to ${nextTarget.name}'`

```javascript
async skipTarget() {
  if (this.executionStatus !== 'running') return
  if (this.currentTargetIndex + 1 >= this.scheduledTargets.length) return
  try { await axios.post('/api/telescope/abort') } catch { /* best-effort */ }
  this.stopProgressPolling()
  this.currentTargetIndex++
  this.resumeOffset = this.currentTargetIndex
  const remaining = this.scheduledTargets.slice(this.currentTargetIndex)
  if (!remaining.length) {
    this.executionStatus = 'completed'
    this.addMessage('Plan completed')
    return
  }
  this.executionStatus = 'running'
  this.addMessage(`Skipped to ${this.currentPlan.targets[this.currentTargetIndex]?.name || 'next target'}`)
  try {
    await axios.post('/api/telescope/execute', { scheduled_targets: remaining, park_when_done: true })
    this.startProgressPolling()
  } catch (err) {
    this.executionStatus = 'idle'
    this.error = 'Failed to skip: ' + (err.response?.data?.detail || err.message)
  }
},
```

**extendTarget(minutes):**
- Guard: if not running or no scheduledTargets at current index, return
- Mutate `scheduledTargets[currentTargetIndex].end_time` += minutes * 60000
- Mutate `scheduledTargets[currentTargetIndex].duration_minutes` += minutes
- Abort + re-execute from current index (same as skip but without incrementing)
- Add message `'+15 min added to ${name}'`

```javascript
async extendTarget(minutes) {
  if (this.executionStatus !== 'running') return
  const st = this.scheduledTargets[this.currentTargetIndex]
  if (!st) return
  const newEndMs = new Date(st.end_time).getTime() + minutes * 60000
  st.end_time = new Date(newEndMs).toISOString()
  st.duration_minutes = (st.duration_minutes || 0) + minutes
  try { await axios.post('/api/telescope/abort') } catch { /* best-effort */ }
  this.stopProgressPolling()
  const remaining = this.scheduledTargets.slice(this.currentTargetIndex)
  this.resumeOffset = this.currentTargetIndex
  this.executionStatus = 'running'
  const name = this.currentPlan?.targets[this.currentTargetIndex]?.name || 'current target'
  this.addMessage(`+${minutes} min added to ${name}`)
  try {
    await axios.post('/api/telescope/execute', { scheduled_targets: remaining, park_when_done: true })
    this.startProgressPolling()
  } catch (err) {
    this.executionStatus = 'idle'
    this.error = 'Failed to extend: ' + (err.response?.data?.detail || err.message)
  }
},
```

**Step: Add both actions to `execution.js` after `resumeExecution` (around line 456), before `stopPlan`.**

**Step: Commit:**
```bash
git add frontend/vue-app/src/stores/execution.js
git commit -m "feat: add skipTarget and extendTarget actions to execution store"
```

---

## Task 2: Live now-marker in PlanTimeline.vue

**Files:**
- Modify: `frontend/vue-app/src/components/planning/PlanTimeline.vue`

**Problem:** `nowX` computed uses `Date.now()` which doesn't change reactively. The now-marker is computed once and stays frozen.

**Fix:** Add a `nowTick` ref that updates every 60 seconds, and use it inside `nowX`.

**Step: Find the import line:**
```javascript
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
```
(Already includes ref, onMounted, onUnmounted — good.)

**Step: Add `nowTick` ref and interval after `const planningStore = usePlanningStore()`:**
```javascript
const nowTick = ref(Date.now())
let _nowInterval = null
```

**Step: Update `onMounted` to start the tick interval.** The existing `onMounted` already adds document event listeners. Add to it:
```javascript
_nowInterval = setInterval(() => { nowTick.value = Date.now() }, 60_000)
```

**Step: Update `onUnmounted` to clear the interval:**
```javascript
if (_nowInterval) clearInterval(_nowInterval)
```

**Step: Update `nowX` computed to depend on `nowTick`:**
```javascript
const nowX = computed(() => {
  if (!sessionDur.value) return null
  const now = nowTick.value   // <-- was Date.now()
  if (now < sessionStart.value || now > sessionEnd.value) return null
  return ML + ((now - sessionStart.value) / sessionDur.value) * CW
})
```

**Step: Commit:**
```bash
git add frontend/vue-app/src/components/planning/PlanTimeline.vue
git commit -m "feat: live now-marker tick in PlanTimeline (updates every 60s)"
```

---

## Task 3: NowPlayingPanel.vue — new component

**Files:**
- Create: `frontend/vue-app/src/components/execution/NowPlayingPanel.vue`

**Props:** none (reads directly from `executionStore` and `planningStore`)

**What it shows:**
- Current target name + object type badge + imaging mode badge
- Progress bar: elapsed / duration
- Countdown: "X min Y sec remaining" — live, ticks every second
- Altitude at start + score
- Next target name + scheduled start time + relative ("in X h Y m")
- Three buttons: Skip, +15 min, Abort Plan
- When plan not running (idle/paused/completed): shows plan status + Resume / Execute / Clear buttons

**Countdown implementation:** `setInterval` every 1000ms updates a `now` ref. Countdown = `endMs - now.value`, formatted as `Xh Ym` or `X min Y sec`.

```vue
<template>
  <div class="h-full flex flex-col gap-3 p-4 bg-gray-900 rounded-lg border border-gray-800">
    <!-- No plan -->
    <div v-if="!executionStore.currentPlan" class="flex-1 flex items-center justify-center text-sm text-gray-500">
      No plan loaded
    </div>

    <template v-else>
      <!-- Current target -->
      <div>
        <div class="flex items-center gap-2 mb-1 flex-wrap">
          <span class="text-xs text-gray-500 uppercase tracking-wide">Now</span>
          <span v-if="currentSt" class="px-1.5 py-0.5 text-xs rounded bg-blue-900/50 text-blue-300">
            {{ currentTarget?.imaging_mode === 'planetary' ? 'Video' : 'Stack' }}
          </span>
        </div>
        <div class="text-base font-semibold text-gray-100 leading-tight">
          {{ currentTarget?.name || '—' }}
        </div>
        <div class="text-xs text-gray-500 mt-0.5">
          <span v-if="currentSt">
            Alt {{ Math.round(currentSt.start_altitude ?? 0) }}°
            <span v-if="currentSt.score?.total_score != null">
              · Score {{ (currentSt.score.total_score * 100).toFixed(0) }}%
            </span>
          </span>
        </div>
      </div>

      <!-- Progress + countdown -->
      <div v-if="currentSt && executionStore.executionStatus === 'running'">
        <div class="flex justify-between text-xs text-gray-400 mb-1">
          <span>{{ elapsedLabel }}</span>
          <span class="text-gray-200 font-medium">{{ countdownLabel }} remaining</span>
        </div>
        <div class="h-1.5 bg-gray-800 rounded-full overflow-hidden">
          <div class="h-full bg-blue-500 transition-none" :style="{ width: progressPct + '%' }" />
        </div>
      </div>

      <!-- Status badge when not running -->
      <div v-if="executionStore.executionStatus !== 'running'" class="flex items-center gap-2">
        <span class="px-2 py-0.5 rounded text-xs font-medium"
          :class="{
            'bg-gray-700 text-gray-400': executionStore.executionStatus === 'idle',
            'bg-yellow-900/50 text-yellow-300': executionStore.executionStatus === 'paused',
            'bg-green-900/50 text-green-300': executionStore.executionStatus === 'completed',
          }">{{ executionStore.executionStatus }}</span>
      </div>

      <hr class="border-gray-800" />

      <!-- Next target -->
      <div v-if="nextTarget" class="text-sm">
        <div class="text-xs text-gray-500 uppercase tracking-wide mb-1">Next</div>
        <div class="text-gray-200 font-medium leading-tight">{{ nextTarget.name }}</div>
        <div v-if="nextSt" class="text-xs text-gray-500 mt-0.5">
          {{ formatTime(nextSt.start_time) }} · {{ relativeTime(nextSt.start_time) }}
        </div>
      </div>
      <div v-else class="text-xs text-gray-600 italic">Last target in plan</div>

      <div class="flex-1" />

      <!-- Controls -->
      <div class="space-y-2">
        <!-- Running controls -->
        <template v-if="executionStore.executionStatus === 'running'">
          <div class="flex gap-2">
            <button @click="executionStore.skipTarget()"
              :disabled="executionStore.currentTargetIndex + 1 >= (executionStore.scheduledTargets?.length ?? 0)"
              class="flex-1 px-3 py-2 text-sm rounded bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
              Skip ⏭
            </button>
            <button @click="executionStore.extendTarget(15)"
              class="flex-1 px-3 py-2 text-sm rounded bg-gray-800 hover:bg-gray-700 text-gray-200 border border-gray-700 transition-colors">
              +15 min
            </button>
          </div>
          <div class="flex gap-2">
            <button @click="executionStore.pausePlan()"
              class="flex-1 px-3 py-2 text-sm rounded bg-gray-700 hover:bg-gray-600 text-gray-300 border border-gray-600 transition-colors">
              Pause
            </button>
            <button @click="executionStore.stopPlan()"
              class="flex-1 px-3 py-2 text-sm rounded bg-red-900/60 hover:bg-red-900 text-red-300 border border-red-800 transition-colors">
              Abort
            </button>
          </div>
        </template>

        <!-- Paused controls -->
        <template v-else-if="executionStore.executionStatus === 'paused'">
          <button @click="executionStore.resumeExecution()"
            :disabled="!executionStore.connected"
            class="w-full px-4 py-2 text-sm rounded bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            Resume
          </button>
          <button @click="executionStore.stopPlan()"
            class="w-full px-3 py-1.5 text-xs text-gray-500 hover:text-red-400 transition-colors">
            Clear plan
          </button>
        </template>

        <!-- Idle controls (plan loaded but not started) -->
        <template v-else-if="executionStore.executionStatus === 'idle'">
          <button @click="executionStore.executePlan()"
            :disabled="!executionStore.connected"
            class="w-full px-4 py-2 text-sm rounded bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            Execute Plan
          </button>
          <div v-if="!executionStore.connected" class="text-xs text-blue-400 text-center">
            Connect telescope to execute
          </div>
        </template>

        <!-- Completed -->
        <template v-else-if="executionStore.executionStatus === 'completed'">
          <button @click="executionStore.stopPlan()"
            class="w-full px-3 py-2 text-sm rounded bg-gray-700 hover:bg-gray-600 text-gray-300 transition-colors">
            Clear Plan
          </button>
        </template>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useExecutionStore } from '@/stores/execution'

const executionStore = useExecutionStore()

// Live clock — ticks every second for countdown
const now = ref(Date.now())
let _ticker = null
onMounted(() => { _ticker = setInterval(() => { now.value = Date.now() }, 1000) })
onUnmounted(() => { if (_ticker) clearInterval(_ticker) })

const currentTarget = computed(() => executionStore.currentTarget)
const nextTarget = computed(() => executionStore.nextTarget)

// scheduledTargets hold start/end time info — currentPlan.targets holds name/mode
const currentSt = computed(() => executionStore.scheduledTargets?.[executionStore.currentTargetIndex] ?? null)
const nextSt = computed(() => executionStore.scheduledTargets?.[executionStore.currentTargetIndex + 1] ?? null)

const endMs = computed(() => {
  if (!currentSt.value?.end_time) return null
  return new Date(currentSt.value.end_time).getTime()
})
const startMs = computed(() => {
  if (!currentSt.value?.start_time) return null
  return new Date(currentSt.value.start_time).getTime()
})

const remainingMs = computed(() => {
  if (endMs.value == null) return null
  return Math.max(0, endMs.value - now.value)
})

const totalDurMs = computed(() => {
  if (startMs.value == null || endMs.value == null) return null
  return endMs.value - startMs.value
})

const progressPct = computed(() => {
  if (totalDurMs.value == null || totalDurMs.value === 0) return 0
  const elapsed = now.value - (startMs.value ?? now.value)
  return Math.min(100, Math.max(0, (elapsed / totalDurMs.value) * 100))
})

const countdownLabel = computed(() => {
  const ms = remainingMs.value
  if (ms == null) return '—'
  const h = Math.floor(ms / 3600000)
  const m = Math.floor((ms % 3600000) / 60000)
  const s = Math.floor((ms % 60000) / 1000)
  if (h > 0) return `${h}h ${m}m`
  if (m > 0) return `${m}m ${s}s`
  return `${s}s`
})

const elapsedLabel = computed(() => {
  if (startMs.value == null) return ''
  const elapsed = Math.max(0, now.value - startMs.value)
  const m = Math.floor(elapsed / 60000)
  return `${m}m elapsed`
})

const formatTime = (iso) => {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })
}

const relativeTime = (iso) => {
  if (!iso) return ''
  const diffMs = new Date(iso).getTime() - now.value
  if (diffMs < 0) return 'overdue'
  const h = Math.floor(diffMs / 3600000)
  const m = Math.floor((diffMs % 3600000) / 60000)
  if (h > 0) return `in ${h}h ${m}m`
  return `in ${m}m`
}
</script>
```

**Step: Create file at `frontend/vue-app/src/components/execution/NowPlayingPanel.vue`.**

**Step: Verify it renders — will be integrated in Task 4.**

**Step: Commit:**
```bash
git add frontend/vue-app/src/components/execution/NowPlayingPanel.vue
git commit -m "feat: add NowPlayingPanel component for plan execution status"
```

---

## Task 4: Redesign ExecutionView.vue

**Files:**
- Modify: `frontend/vue-app/src/views/ExecutionView.vue`

**This is a complete rewrite of the `<template>` and `<script setup>` sections.**

**Mode toggle:** `activeMode` ref (`'plan'` | `'manual'`), persisted to `localStorage`. Initialize from `localStorage.getItem('execMode') || 'plan'`. Watch for changes and save.

**No-plan state:** when `activeMode === 'plan'` and `!executionStore.currentPlan`.

**Connection drop alert:** `watch(() => executionStore.connected, ...)` — if it goes `true → false` while `executionStatus === 'running'`, call `toastStore.error('Telescope connection lost during plan execution')`.

**Left panel:** Keep only TelescopePanel (always visible, not collapsed) + Messages (collapsed by default). Remove ObjectTrackingPanel, DirectionalControlPanel, PlanExecutionPanel, and the saved plans browser (those move to main area).

**Main area layout:**

```
Header: "Live Execution" | [Plan Mode] [Manual Mode] toggle | Status strip (if connected)

Plan Mode, plan loaded:
  PlanTimeline (full width, :plan="planningStore.currentPlan")
  [LivePreviewPanel (55%)] | [NowPlayingPanel (45%)]

Plan Mode, no plan:
  Centered no-plan state with saved plans list + link to planning

Manual Mode:
  [LivePreviewPanel (55%)] | [manual controls right column (45%)]
```

**Manual controls right column (inline in template, no new component):**
- **Goto:** text input (object name or RA/Dec) + Slew button → `executionStore.slewToTarget({ra, dec, name})`
  - Parse RA/Dec: if input contains "h"/":" treat as coords, else use as name (slew by name via existing API)
  - Actually simpler: just use `ObjectTrackingPanel` + an inline slew by name box
- **Capture:** Start Stacking (`startImaging`) / Stop (`stopImaging`) / Start Preview buttons
- **Dew Heater:** On/Off toggle + power display
- **Status:** tracking, mount mode, heading, level (already in header but repeat here for manual mode where header may be compact)

**Important:** The `:plan` prop passed to PlanTimeline must be `planningStore.currentPlan` so it shows the in-memory plan (including any drag edits). When a plan is loaded from execution store, it should also update planningStore — the existing `loadAndStagePlan` calls `planningStore.loadPlan()`, which sets `planningStore.currentPlan`, so this works automatically.

**Full rewritten ExecutionView.vue:**

```vue
<template>
  <PanelContainer v-model:left-panel-visible="leftPanelVisible" :console-visible="false">

    <!-- Left panel header -->
    <template #left-header>
      <h3 class="text-sm font-semibold text-gray-200">Telescope</h3>
    </template>
    <template #left-label>Scope</template>

    <!-- Left: Telescope connection + Messages -->
    <template #left>
      <div class="p-4 space-y-4">
        <TelescopePanel />
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

        <!-- Header -->
        <div class="bg-gray-900/50 border-b border-gray-800 px-4 py-2 flex-none">
          <div class="flex items-center gap-4 flex-wrap">
            <h2 class="text-base font-semibold text-gray-200 flex-shrink-0">Live Execution</h2>

            <!-- Mode toggle -->
            <div class="flex rounded-lg overflow-hidden border border-gray-700 flex-shrink-0 text-xs">
              <button @click="setMode('plan')"
                :class="activeMode === 'plan'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-gray-200'"
                class="px-3 py-1.5 transition-colors font-medium">
                Plan Mode
              </button>
              <button @click="setMode('manual')"
                :class="activeMode === 'manual'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-gray-200'"
                class="px-3 py-1.5 transition-colors font-medium border-l border-gray-700">
                Manual
              </button>
            </div>

            <!-- Status strip -->
            <div v-if="executionStore.connected" class="flex items-center gap-2 text-xs min-w-0 overflow-hidden ml-auto">
              <div class="text-center">
                <div class="text-gray-500">RA</div>
                <div class="font-mono text-gray-200">{{ executionStore.position?.ra != null ? formatRA(executionStore.position.ra) : '--:--:--' }}</div>
              </div>
              <div class="text-center">
                <div class="text-gray-500">Dec</div>
                <div class="font-mono text-gray-200">{{ executionStore.position?.dec != null ? formatDec(executionStore.position.dec) : '--°' }}</div>
              </div>
              <div class="text-center">
                <div class="text-gray-500">Alt</div>
                <div class="font-mono text-gray-200">{{ executionStore.position?.alt != null ? executionStore.position.alt.toFixed(1) + '°' : '--°' }}</div>
              </div>
              <div class="text-center">
                <div class="text-gray-500">Az</div>
                <div class="font-mono text-gray-200">{{ executionStore.position?.az != null ? executionStore.position.az.toFixed(1) + '°' : '--°' }}</div>
              </div>
              <div class="h-6 w-px bg-gray-700 flex-shrink-0" />
              <div class="text-center">
                <div class="text-gray-500">Track</div>
                <div class="font-mono"
                  :class="executionStore.hardware.trackingStatus === 'Active' ? 'text-green-400'
                    : executionStore.hardware.trackingStatus === 'Parked' ? 'text-yellow-400'
                    : 'text-gray-400'">
                  {{ executionStore.hardware.trackingStatus }}
                </div>
              </div>
            </div>
            <div v-else class="ml-auto text-xs text-gray-600">Not connected</div>
          </div>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto">

          <!-- PLAN MODE -->
          <template v-if="activeMode === 'plan'">

            <!-- Plan loaded -->
            <template v-if="planningStore.currentPlan">
              <!-- PlanTimeline (full width) -->
              <div class="px-4 pt-4 pb-2">
                <PlanTimeline
                  :plan="planningStore.currentPlan"
                  @select-target="() => {}"
                />
              </div>

              <!-- Two-column: preview + now-playing -->
              <div class="flex gap-4 px-4 pb-4" style="min-height: 320px">
                <div class="flex-1" style="flex: 0 0 55%">
                  <LivePreviewPanel />
                </div>
                <div style="flex: 0 0 45%; min-width: 0">
                  <NowPlayingPanel />
                </div>
              </div>
            </template>

            <!-- No plan loaded -->
            <template v-else>
              <div class="p-6">
                <p class="text-gray-500 text-sm mb-4">No plan loaded for tonight.</p>

                <!-- Saved plans list -->
                <div v-if="planningStore.savedPlans.length > 0" class="space-y-2 mb-6 max-w-lg">
                  <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Saved Plans</h3>
                  <div v-for="plan in planningStore.savedPlans" :key="plan.id"
                    class="flex items-center justify-between p-3 bg-gray-900 border border-gray-800 rounded-lg hover:border-gray-700 transition-colors">
                    <div>
                      <div class="text-sm font-medium text-gray-200">{{ plan.name }}</div>
                      <div class="text-xs text-gray-500">{{ plan.observing_date }} · {{ plan.total_targets }} targets</div>
                    </div>
                    <button @click="loadAndStagePlan(plan.id)" :disabled="loadingPlanId === plan.id"
                      class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors disabled:opacity-50">
                      {{ loadingPlanId === plan.id ? 'Loading...' : 'Load' }}
                    </button>
                  </div>
                </div>
                <div v-else class="text-sm text-gray-500 mb-6">No saved plans yet.</div>

                <router-link to="/plan"
                  class="inline-flex items-center gap-1 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded-lg border border-gray-700 transition-colors">
                  → Go to Planning
                </router-link>
              </div>
            </template>
          </template>

          <!-- MANUAL MODE -->
          <template v-else>
            <div class="flex gap-4 p-4 h-full" style="min-height: 400px">
              <!-- Live preview -->
              <div style="flex: 0 0 55%">
                <LivePreviewPanel />
              </div>

              <!-- Manual controls -->
              <div class="flex flex-col gap-4 min-w-0" style="flex: 0 0 45%">

                <!-- Goto -->
                <div class="bg-gray-900 border border-gray-800 rounded-lg p-3">
                  <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Goto</h4>
                  <div class="flex gap-2">
                    <input v-model="gotoInput" placeholder="Object name or RA Dec"
                      class="flex-1 bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-sm text-gray-200 placeholder-gray-600 focus:border-blue-500 focus:outline-none"
                      @keydown.enter="doSlew" />
                    <button @click="doSlew" :disabled="!executionStore.connected || !gotoInput.trim()"
                      class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                      Slew
                    </button>
                  </div>
                </div>

                <!-- Capture -->
                <div class="bg-gray-900 border border-gray-800 rounded-lg p-3">
                  <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Capture</h4>
                  <ImagingPanel />
                </div>

                <!-- Status -->
                <div class="bg-gray-900 border border-gray-800 rounded-lg p-3">
                  <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Status</h4>
                  <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                    <div><span class="text-gray-500">Mode:</span> <span class="text-gray-300 ml-1">{{ executionStore.hardware.mountMode === 'equatorial' ? 'EQ' : 'Alt/Az' }}</span></div>
                    <div><span class="text-gray-500">Track:</span> <span class="ml-1"
                      :class="executionStore.hardware.trackingStatus === 'Active' ? 'text-green-400' : 'text-gray-400'">
                      {{ executionStore.hardware.trackingStatus }}</span></div>
                    <div><span class="text-gray-500">Heading:</span> <span class="text-gray-300 ml-1">{{ executionStore.compass.heading != null ? executionStore.compass.heading + '° ' + cardinalDir(executionStore.compass.heading) : '—' }}</span></div>
                    <div><span class="text-gray-500">Level:</span> <span class="ml-1" :class="levelClass(executionStore.balance.angle)">{{ executionStore.balance.angle != null ? executionStore.balance.angle.toFixed(1) + '°' : '—' }}</span></div>
                  </div>
                </div>

              </div>
            </div>
          </template>

        </div>
      </div>
    </template>
  </PanelContainer>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronDownIcon } from 'lucide-vue-next'
import { useExecutionStore } from '@/stores/execution'
import { usePlanningStore } from '@/stores/planning'
import { useToastStore } from '@/stores/toast'
import PanelContainer from '@/components/layout/PanelContainer.vue'
import TelescopePanel from '@/components/execution/TelescopePanel.vue'
import ImagingPanel from '@/components/execution/ImagingPanel.vue'
import LivePreviewPanel from '@/components/execution/LivePreviewPanel.vue'
import MessagesPanel from '@/components/execution/MessagesPanel.vue'
import NowPlayingPanel from '@/components/execution/NowPlayingPanel.vue'
import PlanTimeline from '@/components/planning/PlanTimeline.vue'

const router = useRouter()
const executionStore = useExecutionStore()
const planningStore = usePlanningStore()
const toastStore = useToastStore()

const leftPanelVisible = ref(true)
const msgOpen = ref(false)
const gotoInput = ref('')
const loadingPlanId = ref(null)

// Mode toggle — persisted to localStorage
const activeMode = ref(localStorage.getItem('execMode') || 'plan')
const setMode = (m) => {
  activeMode.value = m
  localStorage.setItem('execMode', m)
}

// Connection drop alert
watch(() => executionStore.connected, (newVal, oldVal) => {
  if (oldVal && !newVal && executionStore.executionStatus === 'running') {
    toastStore.error('Telescope connection lost during plan execution')
  }
})

const doSlew = async () => {
  const input = gotoInput.value.trim()
  if (!input || !executionStore.connected) return
  // Pass as name — backend resolves via catalog or accepts RA/Dec string
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
  } catch (err) {
    toastStore.error('Failed to load plan')
  } finally {
    loadingPlanId.value = null
  }
}

onMounted(async () => {
  await planningStore.loadSavedPlans()
})

function cardinalDir(deg) {
  const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  return dirs[Math.round(deg / 45) % 8]
}

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

**Step: Completely replace ExecutionView.vue content with the above.**

**Step: Verify `useToastStore` is importable — check `src/stores/toast.js` exists (it does, used elsewhere).**

**Step: Verify `router-link to="/plan"` — check the route. From the router config, the planning view is at `/plan` or `/planning`.**

Actually need to check the route. Look for the PlanningView route definition.

**Step: Check route name for planning view before writing:**
```bash
grep -r "PlanningView\|path.*plan" frontend/vue-app/src/router/
```

Then use the correct path in the router-link.

**Step: Build and verify:**
```bash
docker compose build astronomus && docker compose up -d astronomus
```

**Step: Commit:**
```bash
git add frontend/vue-app/src/views/ExecutionView.vue
git commit -m "feat: redesign execution view with Plan Mode + Manual Mode layout"
```

---

## Verification

1. **Plan Mode with plan:** Timeline shows at top (interactive, draggable), live preview left, NowPlayingPanel right with countdown ticking
2. **Plan Mode no plan:** Saved plans list shown, "Go to Planning" link works
3. **Manual Mode:** Live preview left, Goto + Capture + Status right; ImagingPanel renders in right column
4. **Mode toggle:** Switching persists across page refresh (localStorage)
5. **Connection drop:** Disconnect telescope while plan running → red toast appears
6. **Skip:** Advances to next target, plan timeline updates
7. **+15 min:** Extends current target, countdown increases by 15 min
8. **Now-marker:** Blue line in PlanTimeline moves as time passes (check after 60s)
9. **`docker exec astronomus pytest tests/ -q --no-cov`** still passes (pure frontend change)
