<template>
  <PanelContainer
    v-model:left-panel-visible="leftPanelVisible"
    :console-visible="false"
  >
    <!-- Left panel header -->
    <template #left-header>
      <div>
        <h3 class="text-sm font-semibold text-gray-200">Controls</h3>
      </div>
    </template>

    <!-- Left panel label (for peek tab) -->
    <template #left-label>Controls</template>

    <!-- Left: All Controls -->
    <template #left>
      <div class="p-4 space-y-4">

        <!-- Connection & Control (collapsed by default; glows when not connected) -->
        <div>
          <button
            @click="controlOpen = !controlOpen"
            class="flex items-center justify-between w-full text-left mb-3 group"
          >
            <div class="flex items-center gap-2">
              <h4 class="text-xs font-semibold uppercase tracking-wide transition-colors"
                :class="executionStore.connected ? 'text-gray-500 group-hover:text-gray-300' : 'text-blue-400 group-hover:text-blue-300'"
              >Connection & Control</h4>
              <span v-if="!executionStore.connected && !controlOpen"
                class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"
              />
            </div>
            <ChevronDownIcon
              class="w-3.5 h-3.5 text-gray-600 group-hover:text-gray-400 transition-all"
              :class="controlOpen ? 'rotate-0' : '-rotate-90'"
            />
          </button>
          <TelescopePanel v-show="controlOpen" />
        </div>

        <!-- Object Tracking (collapsible, collapsed by default) -->
        <div class="border-t border-gray-800 pt-4">
          <button
            @click="trackingOpen = !trackingOpen"
            class="flex items-center justify-between w-full text-left mb-3 group"
          >
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide group-hover:text-gray-300 transition-colors">Object Tracking</h4>
            <ChevronDownIcon
              class="w-3.5 h-3.5 text-gray-600 group-hover:text-gray-400 transition-all"
              :class="trackingOpen ? 'rotate-0' : '-rotate-90'"
            />
          </button>
          <ObjectTrackingPanel v-show="trackingOpen" />
        </div>

        <!-- Movement -->
        <div>
          <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Movement</h4>
          <DirectionalControlPanel />
        </div>

        <!-- Plan Execution -->
        <div class="border-t border-gray-800 pt-4">
          <button
            @click="planOpen = !planOpen"
            class="flex items-center justify-between w-full text-left mb-3 group"
          >
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide group-hover:text-gray-300 transition-colors">Plan Execution</h4>
            <ChevronDownIcon
              class="w-3.5 h-3.5 text-gray-600 group-hover:text-gray-400 transition-all"
              :class="planOpen ? 'rotate-0' : '-rotate-90'"
            />
          </button>
          <div v-show="planOpen" class="space-y-3">
            <PlanExecutionPanel />

            <!-- Saved Plans Browser -->
            <div class="border-t border-gray-800 pt-3">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs text-gray-500 uppercase tracking-wide font-semibold">Saved Plans</span>
                <button @click="refreshPlans" class="text-xs text-gray-600 hover:text-gray-400 transition-colors">Refresh</button>
              </div>

              <div v-if="plansLoading" class="text-xs text-gray-500 text-center py-2">Loading...</div>
              <div v-else-if="planningStore.savedPlans.length === 0" class="text-xs text-gray-500 text-center py-2">
                No saved plans. Generate and save one from Planning.
              </div>
              <div v-else class="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                <div
                  v-for="plan in planningStore.savedPlans"
                  :key="plan.id"
                  class="p-2 bg-gray-800 rounded border border-gray-700 hover:border-gray-600 transition-colors"
                >
                  <div class="text-xs font-medium text-gray-200 truncate">{{ plan.name }}</div>
                  <div class="text-xs text-gray-500">{{ plan.observing_date }} · {{ plan.total_targets }} targets</div>
                  <button
                    @click="loadAndStagePlan(plan.id)"
                    :disabled="loadingPlanId === plan.id"
                    class="mt-1.5 w-full px-2 py-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs rounded transition-colors"
                  >
                    {{ loadingPlanId === plan.id ? 'Loading...' : 'Load Plan' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Messages -->
        <div class="border-t border-gray-800 pt-4">
          <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Messages</h4>
          <MessagesPanel />
        </div>

      </div>
    </template>

    <!-- Main: Live Preview & Imaging -->
    <template #main>
      <div class="flex flex-col h-full">
        <!-- View Header -->
        <div class="bg-gray-900/50 border-b border-gray-800 px-4 py-3 flex-none">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-gray-200">Live Execution</h2>
              <p class="text-sm text-gray-500">
                {{ executionStore.currentTarget?.name || 'Ready' }}
              </p>
            </div>

            <!-- Status Info -->
            <div v-if="executionStore.connected" class="flex items-center gap-6 text-xs">
              <!-- Position -->
              <div class="flex items-center gap-3">
                <div class="text-center">
                  <div class="text-gray-500">RA</div>
                  <div class="font-mono text-gray-200">{{ executionStore.position?.ra !== undefined ? formatRA(executionStore.position.ra) : '--:--:--' }}</div>
                </div>
                <div class="text-center">
                  <div class="text-gray-500">Dec</div>
                  <div class="font-mono text-gray-200">{{ executionStore.position?.dec !== undefined ? formatDec(executionStore.position.dec) : '--:--:--' }}</div>
                </div>
                <div class="text-center">
                  <div class="text-gray-500">Alt</div>
                  <div class="font-mono text-gray-200">{{ executionStore.position?.alt !== undefined ? executionStore.position.alt.toFixed(1) + '°' : '--°' }}</div>
                </div>
                <div class="text-center">
                  <div class="text-gray-500">Az</div>
                  <div class="font-mono text-gray-200">{{ executionStore.position?.az !== undefined ? executionStore.position.az.toFixed(1) + '°' : '--°' }}</div>
                </div>
              </div>

              <!-- Divider -->
              <div class="h-8 w-px bg-gray-700"></div>

              <!-- Hardware Status -->
              <div class="flex items-center gap-3">
                <div class="text-center">
                  <div class="text-gray-500">Tracking</div>
                  <div class="font-mono"
                    :class="executionStore.hardware.trackingStatus === 'Active' ? 'text-green-400' : executionStore.hardware.trackingStatus === 'Parked' ? 'text-yellow-400' : 'text-gray-400'">
                    {{ executionStore.hardware.trackingStatus }}
                  </div>
                </div>
                <div class="text-center">
                  <div class="text-gray-500">Temp</div>
                  <div class="font-mono text-gray-200">
                    {{ executionStore.hardware.sensorTemp !== null ? executionStore.hardware.sensorTemp.toFixed(1) + '°C' : '--' }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-y-auto p-4 space-y-4">
          <!-- Live Preview -->
          <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h3 class="text-base font-semibold text-gray-100 mb-3">Live Preview</h3>
            <LivePreviewPanel />
          </div>

          <!-- Imaging Controls -->
          <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h3 class="text-base font-semibold text-gray-100 mb-3">Imaging</h3>
            <ImagingPanel />
          </div>
        </div>
      </div>
    </template>

  </PanelContainer>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ChevronDownIcon } from 'lucide-vue-next'
import { useExecutionStore } from '@/stores/execution'
import { usePlanningStore } from '@/stores/planning'
import PanelContainer from '@/components/layout/PanelContainer.vue'
import TelescopePanel from '@/components/execution/TelescopePanel.vue'
import ObjectTrackingPanel from '@/components/execution/ObjectTrackingPanel.vue'
import DirectionalControlPanel from '@/components/execution/DirectionalControlPanel.vue'
import ImagingPanel from '@/components/execution/ImagingPanel.vue'
import LivePreviewPanel from '@/components/execution/LivePreviewPanel.vue'
import PlanExecutionPanel from '@/components/execution/PlanExecutionPanel.vue'
import MessagesPanel from '@/components/execution/MessagesPanel.vue'

const executionStore = useExecutionStore()
const planningStore = usePlanningStore()
const leftPanelVisible = ref(true)
const controlOpen = ref(false)
const trackingOpen = ref(false)
const planOpen = ref(true)
const plansLoading = ref(false)
const loadingPlanId = ref(null)

const refreshPlans = async () => {
  plansLoading.value = true
  await planningStore.loadSavedPlans()
  plansLoading.value = false
}

const PLANETARY_TYPES = new Set(['planet', 'moon', 'sun'])

// Transform an ObservingPlan from the API into the flat format execution store expects
const transformPlan = (name, observingPlan) => ({
  name,
  targets: (observingPlan.scheduled_targets || []).map(st => ({
    name: st.target.common_name || st.target.name || st.target.catalog_id,
    ra: st.target.ra_hours * 15,   // hours → degrees
    dec: st.target.dec_degrees,
    exposure: st.recommended_exposure || 10,
    frames: st.recommended_frames || 50,
    gain: 80,
    object_type: st.target.object_type,
    imaging_mode: PLANETARY_TYPES.has((st.target.object_type || '').toLowerCase())
      ? 'planetary'
      : 'deep-sky',
  })),
})

const loadAndStagePlan = async (id) => {
  loadingPlanId.value = id
  try {
    const detail = await planningStore.loadPlan(id)
    const transformed = transformPlan(detail.name, detail.plan)
    // Pass original scheduled_targets so executePlan can submit them to the backend
    executionStore.setPlan(transformed, detail.plan.scheduled_targets || [])
  } catch (err) {
    console.error('Failed to load plan:', err)
  } finally {
    loadingPlanId.value = null
  }
}

onMounted(refreshPlans)

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
