<template>
  <div class="text-xs">
    <div v-if="capture" class="space-y-2">
      <!-- Metrics row -->
      <div class="grid grid-cols-3 gap-2 text-center">
        <div>
          <div class="text-gray-500">Exposure</div>
          <div class="text-gray-200 font-medium">{{ formatExposure(capture.total_exposure_seconds) }}</div>
        </div>
        <div>
          <div class="text-gray-500">FWHM</div>
          <div :class="fwhmClass(capture.best_fwhm)" class="font-medium">
            {{ capture.best_fwhm ? `${capture.best_fwhm.toFixed(1)}"` : '—' }}
          </div>
        </div>
        <div>
          <div class="text-gray-500">Sessions</div>
          <div class="text-gray-200 font-medium">{{ capture.total_sessions || '—' }}</div>
        </div>
      </div>

      <!-- System suggestion -->
      <div v-if="capture.suggested_status" class="text-gray-500">
        System suggests: <span class="text-gray-400">{{ formatSuggested(capture.suggested_status) }}</span>
      </div>

      <!-- Action buttons -->
      <div class="flex gap-1">
        <button
          @click="$emit('set-status', 'complete')"
          :class="isComplete
            ? 'bg-green-700 text-green-200'
            : 'bg-gray-700 text-gray-400 hover:bg-green-900/50 hover:text-green-400'"
          class="flex-1 px-2 py-1 rounded transition-colors"
        >
          ✓ Complete
        </button>
        <button
          @click="$emit('set-status', 'needs_more')"
          :class="isNeedsMore
            ? 'bg-amber-700 text-amber-200'
            : 'bg-gray-700 text-gray-400 hover:bg-amber-900/50 hover:text-amber-400'"
          class="flex-1 px-2 py-1 rounded transition-colors"
        >
          ↩ Needs More
        </button>
        <button
          v-if="capture.status"
          @click="$emit('set-status', null)"
          class="px-2 py-1 rounded bg-gray-700 text-gray-500 hover:text-gray-300 transition-colors"
        >
          Clear
        </button>
      </div>
    </div>
    <div v-else class="text-gray-600 italic">
      Not yet captured
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  capture: { type: Object, default: null },
})

defineEmits(['set-status'])

function formatExposure(seconds) {
  if (!seconds) return '—'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

function fwhmClass(v) {
  if (!v) return 'text-gray-500'
  if (v <= 2.0) return 'text-green-400'
  if (v <= 3.0) return 'text-blue-400'
  if (v <= 4.5) return 'text-amber-400'
  return 'text-red-400'
}

const isComplete = computed(() => props.capture?.status === 'complete')
const isNeedsMore = computed(() => props.capture?.status === 'needs_more' || props.capture?.status === 'needs_more_data')

function formatSuggested(s) {
  return s === 'needs_more_data' ? 'Needs More' : s === 'complete' ? 'Complete' : s
}
</script>
