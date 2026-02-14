<template>
  <PanelContainer
    :left-panel-visible="true"
    :right-panel-visible="false"
    :console-visible="false"
  >
    <!-- Left: Execution Controls -->
    <template #left>
      <div class="p-4 border-b border-gray-800">
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Execution</h3>
      </div>
      <div class="space-y-4 p-4">
        <!-- Plan Execution Panel -->
        <div v-if="executionStore.currentPlan" class="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h3 class="text-sm font-semibold text-gray-500 mb-3">
            PLAN EXECUTION
          </h3>

          <div class="space-y-3">
            <div class="text-sm text-gray-200">
              Target {{ executionStore.currentTargetIndex + 1 }} of {{ executionStore.currentPlan.targets.length }}
            </div>

            <button
              v-if="!executionStore.planExecuting"
              @click="executionStore.executePlan()"
              :disabled="!executionStore.connected"
              class="w-full px-4 py-2 rounded font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Execute Plan
            </button>

            <div v-else class="space-y-2">
              <button
                @click="executionStore.pausePlan()"
                class="w-full px-4 py-2 rounded font-medium transition-colors bg-gray-700 hover:bg-gray-600 text-gray-200 border border-gray-600"
              >
                Pause
              </button>

              <button
                @click="executionStore.stopPlan()"
                class="w-full px-4 py-2 rounded font-medium transition-colors bg-red-900 hover:bg-red-800 text-white"
              >
                Stop
              </button>
            </div>
          </div>
        </div>

        <TelescopePanel />
        <MotionControlPanel />
        <ImagingPanel />
        <HardwarePanel />
        <MessagesPanel />
      </div>
    </template>

    <!-- Main: Execution Display -->
    <template #main>
      <div class="flex flex-col h-full">
        <!-- View Header -->
        <div class="bg-gray-900/50 border-b border-gray-800 px-4 py-3 flex-none">
          <h2 class="text-lg font-semibold text-gray-200">Live Execution</h2>
          <p class="text-sm text-gray-500">
            {{ executionStore.currentTarget?.name || 'Ready' }}
          </p>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-auto">
          <div v-if="executionStore.currentTarget" class="p-6 space-y-6">
            <div class="text-center">
              <h2 class="text-3xl font-semibold text-gray-200 mb-2">
                {{ executionStore.currentTarget.name }}
              </h2>
              <p class="text-sm text-gray-500">
                {{ executionStore.currentTarget.type }}
              </p>
            </div>

            <div class="bg-gray-900 border border-gray-800 rounded-lg p-6">
              <div class="grid grid-cols-2 gap-4 text-center">
                <div>
                  <div class="text-xs text-gray-500">RA</div>
                  <div class="text-lg text-gray-200 font-mono">
                    {{ formatRA(executionStore.position.ra) }}
                  </div>
                </div>
                <div>
                  <div class="text-xs text-gray-500">Dec</div>
                  <div class="text-lg text-gray-200 font-mono">
                    {{ formatDec(executionStore.position.dec) }}
                  </div>
                </div>
                <div>
                  <div class="text-xs text-gray-500">Alt</div>
                  <div class="text-lg text-gray-200 font-mono">
                    {{ executionStore.position.alt.toFixed(1) }}°
                  </div>
                </div>
                <div>
                  <div class="text-xs text-gray-500">Az</div>
                  <div class="text-lg text-gray-200 font-mono">
                    {{ executionStore.position.az.toFixed(1) }}°
                  </div>
                </div>
              </div>
            </div>

            <div v-if="executionStore.imaging.active">
              <div class="text-sm text-gray-500 mb-2">
                Progress: {{ executionStore.progressPercent }}%
              </div>
              <div class="w-full bg-gray-800 rounded-full h-2">
                <div
                  class="bg-blue-500 h-2 rounded-full transition-all"
                  :style="{ width: executionStore.progressPercent + '%' }"
                ></div>
              </div>
            </div>
          </div>

          <div v-else class="flex items-center justify-center h-full">
            <div class="text-center">
              <p class="text-gray-500">
                Load a plan or connect telescope to begin
              </p>
            </div>
          </div>
        </div>
      </div>
    </template>
  </PanelContainer>
</template>

<script setup>
import { useExecutionStore } from '@/stores/execution'
import PanelContainer from '@/components/layout/PanelContainer.vue'
import TelescopePanel from '@/components/execution/TelescopePanel.vue'
import MotionControlPanel from '@/components/execution/MotionControlPanel.vue'
import ImagingPanel from '@/components/execution/ImagingPanel.vue'
import HardwarePanel from '@/components/execution/HardwarePanel.vue'
import MessagesPanel from '@/components/execution/MessagesPanel.vue'

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
