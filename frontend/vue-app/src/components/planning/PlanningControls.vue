<template>
  <div class="planning-controls space-y-4 p-4">
    <section>
      <h3 class="text-sm font-semibold text-gray-500 mb-3">
        OBSERVATION SESSION
      </h3>

      <div class="space-y-3">
        <div>
          <label class="block text-xs text-gray-500 mb-1">Date</label>
          <input
            v-model="planningStore.observationDate"
            type="date"
            class="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-gray-200 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label class="block text-xs text-gray-500 mb-1">Location</label>
          <div class="text-xs text-gray-200">
            {{ planningStore.location.latitude }}°N, {{ planningStore.location.longitude }}°W
          </div>
        </div>
      </div>
    </section>

    <section>
      <h3 class="text-sm font-semibold text-gray-500 mb-3">
        TARGETS ({{ planningStore.targetCount }})
      </h3>

      <div v-if="planningStore.hasTargets" class="space-y-2">
        <div
          v-for="target in planningStore.selectedTargets"
          :key="target.id"
          class="flex items-center justify-between p-2 bg-gray-800 rounded"
        >
          <span class="text-sm text-gray-200">{{ target.name }}</span>
          <button
            @click="planningStore.removeTarget(target.id)"
            class="text-red-500 hover:text-red-400 text-xs"
          >
            Remove
          </button>
        </div>
      </div>

      <div v-else class="text-xs text-gray-400">
        No targets selected. Add targets from Discovery view.
      </div>
    </section>

    <section>
      <h3 class="text-sm font-semibold text-gray-500 mb-3">
        CONSTRAINTS
      </h3>

      <div class="space-y-3">
        <div>
          <label class="block text-xs text-gray-500 mb-1">
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
            class="rounded border-gray-700"
          />
          <label for="avoid-moon" class="text-sm text-gray-200">
            Avoid Moon
          </label>
        </div>
      </div>
    </section>

    <section>
      <button
        @click="generatePlan"
        :disabled="!planningStore.hasTargets || planningStore.loading"
        class="w-full px-4 py-2 rounded font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {{ planningStore.loading ? 'Generating...' : 'Generate Plan' }}
      </button>
    </section>
  </div>
</template>

<script setup>
import { usePlanningStore } from '@/stores/planning'

const planningStore = usePlanningStore()

const generatePlan = async () => {
  await planningStore.generatePlan()
}
</script>
