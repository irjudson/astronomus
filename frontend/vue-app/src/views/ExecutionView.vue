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
              <button
                @click="setMode('plan')"
                :class="activeMode === 'plan' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-gray-200'"
                class="px-3 py-1.5 transition-colors font-medium"
              >
                Plan Mode
              </button>
              <button
                @click="setMode('manual')"
                :class="activeMode === 'manual' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-gray-200'"
                class="px-3 py-1.5 transition-colors font-medium border-l border-gray-700"
              >
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
                <div
                  class="font-mono"
                  :class="executionStore.hardware.trackingStatus === 'Active' ? 'text-green-400'
                    : executionStore.hardware.trackingStatus === 'Parked' ? 'text-yellow-400'
                    : 'text-gray-400'"
                >
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
              <!-- PlanTimeline full width -->
              <div class="px-4 pt-4 pb-2">
                <PlanTimeline
                  :plan="planningStore.currentPlan"
                  @select-target="() => {}"
                />
              </div>

              <!-- Two-column: preview + now-playing -->
              <div class="flex gap-4 px-4 pb-4" style="min-height: 320px">
                <div style="flex: 0 0 55%; min-width: 0">
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

                <div v-if="planningStore.savedPlans.length > 0" class="space-y-2 mb-6 max-w-lg">
                  <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Saved Plans</h3>
                  <div
                    v-for="plan in planningStore.savedPlans"
                    :key="plan.id"
                    class="flex items-center justify-between p-3 bg-gray-900 border border-gray-800 rounded-lg hover:border-gray-700 transition-colors"
                  >
                    <div>
                      <div class="text-sm font-medium text-gray-200">{{ plan.name }}</div>
                      <div class="text-xs text-gray-500">{{ plan.observing_date }} · {{ plan.total_targets }} targets</div>
                    </div>
                    <button
                      @click="loadAndStagePlan(plan.id)"
                      :disabled="loadingPlanId === plan.id"
                      class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors disabled:opacity-50"
                    >
                      {{ loadingPlanId === plan.id ? 'Loading...' : 'Load' }}
                    </button>
                  </div>
                </div>
                <div v-else class="text-sm text-gray-500 mb-6">No saved plans yet.</div>

                <router-link
                  to="/plan"
                  class="inline-flex items-center gap-1 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm rounded-lg border border-gray-700 transition-colors"
                >
                  → Go to Planning
                </router-link>
              </div>
            </template>
          </template>

          <!-- MANUAL MODE -->
          <template v-else>
            <div class="flex gap-4 p-4" style="min-height: 400px">

              <!-- Live preview -->
              <div style="flex: 0 0 55%; min-width: 0">
                <LivePreviewPanel />
              </div>

              <!-- Manual controls -->
              <div class="flex flex-col gap-4 min-w-0" style="flex: 0 0 45%">

                <!-- Goto -->
                <div class="bg-gray-900 border border-gray-800 rounded-lg p-3">
                  <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Goto</h4>
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
                    <div>
                      <span class="text-gray-500">Mode:</span>
                      <span class="text-gray-300 ml-1">{{ executionStore.hardware.mountMode === 'equatorial' ? 'EQ' : 'Alt/Az' }}</span>
                    </div>
                    <div>
                      <span class="text-gray-500">Track:</span>
                      <span
                        class="ml-1"
                        :class="executionStore.hardware.trackingStatus === 'Active' ? 'text-green-400' : 'text-gray-400'"
                      >{{ executionStore.hardware.trackingStatus }}</span>
                    </div>
                    <div>
                      <span class="text-gray-500">Heading:</span>
                      <span class="text-gray-300 ml-1">{{ executionStore.compass.heading != null ? executionStore.compass.heading + '° ' + cardinalDir(executionStore.compass.heading) : '—' }}</span>
                    </div>
                    <div>
                      <span class="text-gray-500">Level:</span>
                      <span class="ml-1" :class="levelClass(executionStore.balance.angle)">{{ executionStore.balance.angle != null ? executionStore.balance.angle.toFixed(1) + '°' : '—' }}</span>
                    </div>
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
