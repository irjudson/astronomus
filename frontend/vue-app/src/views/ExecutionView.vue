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
        <!-- Connection & Control (collapsible) -->
        <div>
          <button
            @click="controlOpen = !controlOpen"
            class="flex items-center justify-between w-full text-left mb-3 group"
          >
            <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide group-hover:text-gray-300 transition-colors">Connection & Control</h4>
            <ChevronDownIcon
              class="w-3.5 h-3.5 text-gray-600 group-hover:text-gray-400 transition-all"
              :class="controlOpen ? 'rotate-0' : '-rotate-90'"
            />
          </button>
          <TelescopePanel v-show="controlOpen" />
        </div>

        <!-- Object Tracking (always visible) -->
        <div class="border-t border-gray-800 pt-4">
          <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Object Tracking</h4>
          <ObjectTrackingPanel />
        </div>

        <!-- Movement -->
        <div>
          <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Movement</h4>
          <DirectionalControlPanel />
        </div>

        <!-- Plan Execution -->
        <div class="border-t border-gray-800 pt-4">
          <h4 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Plan Execution</h4>
          <PlanExecutionPanel />
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
import { ref } from 'vue'
import { ChevronDownIcon } from 'lucide-vue-next'
import { useExecutionStore } from '@/stores/execution'
import PanelContainer from '@/components/layout/PanelContainer.vue'
import TelescopePanel from '@/components/execution/TelescopePanel.vue'
import ObjectTrackingPanel from '@/components/execution/ObjectTrackingPanel.vue'
import DirectionalControlPanel from '@/components/execution/DirectionalControlPanel.vue'
import ImagingPanel from '@/components/execution/ImagingPanel.vue'
import LivePreviewPanel from '@/components/execution/LivePreviewPanel.vue'
import PlanExecutionPanel from '@/components/execution/PlanExecutionPanel.vue'
import MessagesPanel from '@/components/execution/MessagesPanel.vue'

const executionStore = useExecutionStore()
const leftPanelVisible = ref(true)
const controlOpen = ref(true)

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
