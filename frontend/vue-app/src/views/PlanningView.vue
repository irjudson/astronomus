<template>
  <PanelContainer
    :left-panel-visible="true"
    :right-panel-visible="false"
    :console-visible="false"
  >
    <!-- Left: Planning Controls -->
    <template #left>
      <div class="p-4 border-b border-gray-800">
        <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Planning</h3>
      </div>
      <PlanningControls />
    </template>

    <!-- Main: Generated Plan -->
    <template #main>
      <div class="flex flex-col h-full">
        <!-- View Header -->
        <div class="bg-gray-900/50 border-b border-gray-800 px-4 py-3 flex-none">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-gray-200">Observation Plan</h2>
              <p class="text-sm text-gray-500">
                <span v-if="planningStore.currentPlan">
                  {{ planningStore.currentPlan.total_targets }} targets • {{ Math.round(planningStore.currentPlan.coverage_percent) }}% coverage
                </span>
                <span v-else>No plan generated</span>
              </p>
            </div>
            <div v-if="planningStore.currentPlan" class="flex gap-2">
              <button
                @click="savePlan"
                class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition-colors"
              >
                Save Plan
              </button>
              <button
                @click="exportPlan"
                class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors"
              >
                Export
              </button>
            </div>
          </div>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-hidden flex flex-col">
          <div v-if="planningStore.currentPlan" class="flex-1 overflow-y-auto p-6">
            <!-- Session Info -->
            <div class="mb-6 p-4 bg-gray-900 border border-gray-800 rounded-lg">
              <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Session Details</h3>
              <div class="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span class="text-gray-500">Date:</span>
                  <span class="text-gray-200 ml-2">{{ formatDate(planningStore.currentPlan.session.observing_date) }}</span>
                </div>
                <div>
                  <span class="text-gray-500">Location:</span>
                  <span class="text-gray-200 ml-2">{{ planningStore.currentPlan.location.name }}</span>
                </div>
                <div>
                  <span class="text-gray-500">Imaging Window:</span>
                  <span class="text-gray-200 ml-2">
                    {{ formatTime(planningStore.currentPlan.session.imaging_start) }} - {{ formatTime(planningStore.currentPlan.session.imaging_end) }}
                  </span>
                </div>
                <div>
                  <span class="text-gray-500">Total Time:</span>
                  <span class="text-gray-200 ml-2">{{ planningStore.currentPlan.session.total_imaging_minutes }} min</span>
                </div>
              </div>
            </div>

            <!-- Scheduled Targets -->
            <div class="space-y-3">
              <h3 class="text-sm font-semibold text-gray-400 uppercase tracking-wide">Scheduled Targets</h3>
              <div
                v-for="(target, index) in planningStore.currentPlan.scheduled_targets"
                :key="index"
                class="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-700 transition-colors"
              >
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-2">
                      <span class="text-gray-200 font-medium">{{ target.target.common_name || target.target.catalog_id }}</span>
                      <span class="px-2 py-0.5 bg-blue-600/20 text-blue-400 text-xs rounded">
                        {{ target.target.object_type }}
                      </span>
                      <span v-if="target.gap_filler" class="px-2 py-0.5 bg-yellow-600/20 text-yellow-400 text-xs rounded">
                        Gap Filler
                      </span>
                    </div>
                    <div class="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span class="text-gray-500">Time:</span>
                        <span class="text-gray-300 ml-2">{{ formatTime(target.start_time) }} ({{ target.duration_minutes }} min)</span>
                      </div>
                      <div>
                        <span class="text-gray-500">Altitude:</span>
                        <span class="text-gray-300 ml-2">{{ Math.round(target.max_altitude) }}° @ {{ formatTime(target.transit_time) }}</span>
                      </div>
                      <div>
                        <span class="text-gray-500">Magnitude:</span>
                        <span class="text-gray-300 ml-2">{{ target.target.magnitude?.toFixed(1) || 'N/A' }}</span>
                      </div>
                      <div v-if="target.target.size_arcmin">
                        <span class="text-gray-500">Size:</span>
                        <span class="text-gray-300 ml-2">{{ target.target.size_arcmin }}′</span>
                      </div>
                    </div>
                  </div>
                  <div class="text-right">
                    <div class="text-2xl font-bold text-blue-500">{{ index + 1 }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="flex-1 flex items-center justify-center">
            <div class="text-center max-w-md">
              <div class="text-6xl mb-4">🌌</div>
              <p class="text-gray-400 text-lg mb-2">
                No plan generated yet
              </p>
              <p class="text-sm text-gray-500">
                Add targets to your wishlist from the Discovery view, then click "Generate Plan" in the left panel
              </p>
            </div>
          </div>
        </div>
      </div>
    </template>
  </PanelContainer>
</template>

<script setup>
import { usePlanningStore } from '@/stores/planning'
import PanelContainer from '@/components/layout/PanelContainer.vue'
import PlanningControls from '@/components/planning/PlanningControls.vue'

const planningStore = usePlanningStore()

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const formatTime = (dateTimeStr) => {
  if (!dateTimeStr) return 'N/A'
  return new Date(dateTimeStr).toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  })
}

const savePlan = async () => {
  try {
    await planningStore.savePlan()
    alert('Plan saved successfully!')
  } catch (err) {
    alert('Failed to save plan: ' + err.message)
  }
}

const exportPlan = async () => {
  try {
    const exported = await planningStore.exportPlan('seestar_alp')
    if (exported) {
      // Trigger download
      const blob = new Blob([JSON.stringify(exported, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `observation-plan-${new Date().toISOString().split('T')[0]}.json`
      a.click()
      URL.revokeObjectURL(url)
    }
  } catch (err) {
    alert('Failed to export plan: ' + err.message)
  }
}
</script>
