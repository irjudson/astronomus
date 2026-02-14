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
