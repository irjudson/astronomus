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
          <h2 class="text-lg font-semibold text-gray-200">Observation Plan</h2>
          <p class="text-sm text-gray-500">
            {{ planningStore.currentPlan?.targets?.length || 0 }} targets scheduled
          </p>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-hidden flex flex-col">
          <div v-if="planningStore.currentPlan" class="flex-1 overflow-y-auto p-6">
            <div class="space-y-4">
              <div v-for="target in planningStore.currentPlan.targets" :key="target.name">
                <BaseCard padding="md">
                  <div class="flex justify-between items-center">
                    <div>
                      <span class="text-gray-200 font-medium block">{{ target.name }}</span>
                      <span class="text-xs text-gray-500">{{ target.type || 'Unknown' }}</span>
                    </div>
                    <div class="text-right">
                      <span class="text-sm text-gray-400 block">
                        {{ target.start_time }} - {{ target.duration }}min
                      </span>
                    </div>
                  </div>
                </BaseCard>
              </div>
            </div>
          </div>

          <div v-else class="flex-1 flex items-center justify-center">
            <div class="text-center">
              <p class="text-gray-500 mb-4">
                No plan generated yet
              </p>
              <p class="text-sm text-gray-400">
                Add targets and click "Generate Plan" in the left panel
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
import BaseCard from '@/components/common/BaseCard.vue'

const planningStore = usePlanningStore()
</script>
