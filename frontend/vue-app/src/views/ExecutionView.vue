<template>
  <PanelContainer v-model:left-panel-visible="leftPanelVisible" :console-visible="false">

    <!-- Left panel header -->
    <template #left-header>
      <h3 class="text-sm font-semibold text-gray-200">Telescope</h3>
    </template>
    <template #left-label>Scope</template>

    <!-- Left: collapsible sections -->
    <template #left>
      <div class="p-4 space-y-4">

        <!-- TelescopePanel — always visible -->
        <TelescopePanel />

        <!-- Goto — collapsible, default open -->
        <div class="border-t border-gray-800 pt-4">
          <button
            @click="gotoOpen = !gotoOpen"
            class="flex items-center justify-between w-full text-left mb-2 group"
          >
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide group-hover:text-gray-300 transition-colors">Goto</h4>
            <ChevronDownIcon
              class="w-3.5 h-3.5 text-gray-600 group-hover:text-gray-400 transition-all"
              :class="gotoOpen ? 'rotate-0' : '-rotate-90'"
            />
          </button>
          <div v-show="gotoOpen">
            <div class="flex gap-2">
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
              >
                Go
              </button>
            </div>
          </div>
        </div>

        <!-- Movement — collapsible, default closed -->
        <div class="border-t border-gray-800 pt-4">
          <button
            @click="moveOpen = !moveOpen"
            class="flex items-center justify-between w-full text-left mb-2 group"
          >
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide group-hover:text-gray-300 transition-colors">Movement</h4>
            <ChevronDownIcon
              class="w-3.5 h-3.5 text-gray-600 group-hover:text-gray-400 transition-all"
              :class="moveOpen ? 'rotate-0' : '-rotate-90'"
            />
          </button>
          <div v-show="moveOpen">
            <DirectionalControlPanel />
          </div>
        </div>

        <!-- Status — visible only when connected, not collapsible -->
        <div v-if="executionStore.connected" class="border-t border-gray-800 pt-4">
          <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Status</h4>
          <div class="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            <div>
              <span class="text-gray-500">RA:</span>
              <span class="font-mono text-gray-200 ml-1">
                {{ executionStore.position?.ra != null ? formatRA(executionStore.position.ra) : '--:--:--' }}
              </span>
            </div>
            <div>
              <span class="text-gray-500">Dec:</span>
              <span class="font-mono text-gray-200 ml-1">
                {{ executionStore.position?.dec != null ? formatDec(executionStore.position.dec) : '--°' }}
              </span>
            </div>
            <div>
              <span class="text-gray-500">Alt:</span>
              <span class="font-mono text-gray-200 ml-1">
                {{ executionStore.position?.alt != null ? executionStore.position.alt.toFixed(1) + '°' : '--°' }}
              </span>
            </div>
            <div>
              <span class="text-gray-500">Az:</span>
              <span class="font-mono text-gray-200 ml-1">
                {{ executionStore.position?.az != null ? executionStore.position.az.toFixed(1) + '°' : '--°' }}
              </span>
            </div>
            <div>
              <span class="text-gray-500">Track:</span>
              <span
                class="ml-1"
                :class="executionStore.hardware.trackingStatus === 'Active' ? 'text-green-400'
                  : executionStore.hardware.trackingStatus === 'Parked' ? 'text-yellow-400'
                  : 'text-gray-400'"
              >{{ executionStore.hardware.trackingStatus }}</span>
            </div>
            <div>
              <span class="text-gray-500">Level:</span>
              <span class="ml-1" :class="levelClass(executionStore.balance.angle)">
                {{ executionStore.balance.angle != null ? executionStore.balance.angle.toFixed(1) + '°' : '—' }}
              </span>
            </div>
            <div class="col-span-2">
              <span class="text-gray-500">Heading:</span>
              <span class="text-gray-300 ml-1">
                {{ executionStore.compass.heading != null ? executionStore.compass.heading + '° ' + cardinalDir(executionStore.compass.heading) : '—' }}
              </span>
            </div>
          </div>
        </div>

        <!-- Advanced controls (Tier 2) -->
        <ControlsDrawer v-if="executionStore.connected" />

        <!-- Messages — collapsible, default closed -->
        <div class="border-t border-gray-800 pt-4">
          <button
            @click="msgOpen = !msgOpen"
            class="flex items-center justify-between w-full text-left mb-2 group"
          >
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide group-hover:text-gray-300 transition-colors">Messages</h4>
            <ChevronDownIcon
              class="w-3.5 h-3.5 text-gray-600 group-hover:text-gray-400 transition-all"
              :class="msgOpen ? 'rotate-0' : '-rotate-90'"
            />
          </button>
          <div v-show="msgOpen">
            <MessagesPanel />
          </div>
        </div>

      </div>
    </template>

    <!-- Main -->
    <template #main>
      <div class="flex flex-col h-full">

        <!-- PlanTimeline — visible only when a plan is loaded -->
        <div
          v-if="planningStore.currentPlan"
          class="flex-none border-b border-gray-800 px-4 py-3 bg-gray-900/50"
        >
          <PlanTimeline
            :plan="planningStore.currentPlan"
            @select-target="() => {}"
          />
        </div>

        <!-- Preview area — fills remaining space -->
        <div class="flex-1 relative overflow-hidden">
          <LivePreviewPanel class="h-full" />

          <!-- NowPlayingPanel overlay — only when plan is loaded and not idle -->
          <div
            v-if="planningStore.currentPlan && executionStore.executionStatus !== 'idle'"
            class="absolute bottom-0 left-0 right-0 bg-gray-950/90 backdrop-blur-sm border-t border-gray-800"
          >
            <NowPlayingPanel />
          </div>
        </div>

        <!-- No-plan strip — visible only when no plan is loaded -->
        <div
          v-if="!planningStore.currentPlan"
          class="flex-none border-t border-gray-800 p-4"
        >
          <div class="flex flex-wrap items-center gap-3">
            <span class="text-sm text-gray-500">No plan loaded.</span>

            <!-- Up to 3 recent saved plans as small load buttons -->
            <template v-for="plan in planningStore.savedPlans.slice(0, 3)" :key="plan.id">
              <button
                @click="loadAndStagePlan(plan.id)"
                :disabled="loadingPlanId === plan.id"
                class="px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded border border-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {{ loadingPlanId === plan.id ? 'Loading…' : plan.name }}
              </button>
            </template>

            <router-link
              to="/plan"
              class="text-xs text-blue-400 hover:text-blue-300 transition-colors ml-auto"
            >
              → Plan
            </router-link>
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
import LivePreviewPanel from '@/components/execution/LivePreviewPanel.vue'
import MessagesPanel from '@/components/execution/MessagesPanel.vue'
import NowPlayingPanel from '@/components/execution/NowPlayingPanel.vue'
import PlanTimeline from '@/components/planning/PlanTimeline.vue'
import ControlsDrawer from '@/components/observe/ControlsDrawer.vue'

const executionStore = useExecutionStore()
const planningStore = usePlanningStore()
const toastStore = useToastStore()

const leftPanelVisible = ref(true)
const gotoOpen = ref(true)
const moveOpen = ref(false)
const msgOpen = ref(false)

const gotoInput = ref('')
const loadingPlanId = ref(null)

// Alert when connection drops during an active plan
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
