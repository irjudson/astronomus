<template>
  <div class="planning-controls space-y-4 p-4">
    <section>
      <h3 class="text-sm font-semibold text-astro-text-muted mb-3">
        OBSERVATION SESSION
      </h3>

      <div class="space-y-3">
        <div>
          <label class="block text-xs text-astro-text-muted mb-1">Date</label>
          <input
            v-model="planningStore.observationDate"
            type="date"
            class="w-full px-3 py-2 bg-astro-elevated border border-astro-border rounded text-astro-text focus:outline-none focus:border-astro-accent"
          />
        </div>

        <div>
          <label class="block text-xs text-astro-text-muted mb-1">Location</label>
          <div class="text-xs text-astro-text">
            {{ planningStore.location.latitude }}°N, {{ planningStore.location.longitude }}°W
          </div>
        </div>
      </div>
    </section>

    <section>
      <h3 class="text-sm font-semibold text-astro-text-muted mb-3">
        TARGETS ({{ planningStore.targetCount }})
      </h3>

      <div v-if="planningStore.hasTargets" class="space-y-2">
        <div
          v-for="target in planningStore.selectedTargets"
          :key="target.id"
          class="flex items-center justify-between p-2 bg-astro-elevated rounded"
        >
          <span class="text-sm text-astro-text">{{ target.name }}</span>
          <button
            @click="planningStore.removeTarget(target.id)"
            class="text-astro-error hover:text-red-400 text-xs"
          >
            Remove
          </button>
        </div>
      </div>

      <div v-else class="text-xs text-astro-text-dim">
        No targets selected. Add targets from Discovery view.
      </div>
    </section>

    <section>
      <h3 class="text-sm font-semibold text-astro-text-muted mb-3">
        CONSTRAINTS
      </h3>

      <div class="space-y-3">
        <div>
          <label class="block text-xs text-astro-text-muted mb-1">
            Altitude Range: {{ planningStore.constraints.min_altitude }}° - {{ planningStore.constraints.max_altitude }}°
          </label>
          <div class="flex gap-2">
            <input
              v-model.number="planningStore.constraints.min_altitude"
              type="range"
              min="0"
              max="90"
              class="flex-1"
            />
            <input
              v-model.number="planningStore.constraints.max_altitude"
              type="range"
              min="0"
              max="90"
              class="flex-1"
            />
          </div>
        </div>

        <div class="flex items-center gap-2">
          <input
            v-model="planningStore.constraints.avoid_moon"
            type="checkbox"
            id="avoid-moon"
            class="rounded border-astro-border"
          />
          <label for="avoid-moon" class="text-sm text-astro-text">
            Avoid Moon
          </label>
        </div>
      </div>
    </section>

    <section>
      <BaseButton
        variant="primary"
        @click="generatePlan"
        :disabled="!planningStore.hasTargets || planningStore.loading"
        class="w-full"
      >
        {{ planningStore.loading ? 'Generating...' : 'Generate Plan' }}
      </BaseButton>
    </section>
  </div>
</template>

<script setup>
import { usePlanningStore } from '@/stores/planning'
import BaseButton from '@/components/common/BaseButton.vue'

const planningStore = usePlanningStore()

const generatePlan = async () => {
  await planningStore.generatePlan()
}
</script>
