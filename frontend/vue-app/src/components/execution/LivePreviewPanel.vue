<template>
  <!-- Live Preview when imaging -->
  <div v-if="executionStore.imaging.active" class="flex flex-col h-full min-h-[400px]">
    <div class="flex-1 bg-black flex items-center justify-center relative rounded-lg overflow-hidden">
      <img
        v-if="previewImage"
        :src="previewImage"
        :key="previewUpdateKey"
        alt="Live Preview"
        class="max-w-full max-h-full object-contain"
      />
      <div v-else class="text-center">
        <div class="text-gray-500 mb-4">
          <svg class="animate-spin h-12 w-12 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
        <p class="text-gray-400">Waiting for preview...</p>
      </div>

      <!-- Imaging Info Overlay -->
      <div class="absolute top-4 right-4 bg-black/80 backdrop-blur-sm rounded-lg p-3 border border-gray-700">
        <div class="text-xs text-gray-400 mb-1">Frame {{ executionStore.imaging.framesCaptured }}</div>
        <div class="text-sm font-medium text-green-400">Imaging...</div>
      </div>
    </div>

    <!-- Preview Controls -->
    <div class="bg-gray-900 border-t border-gray-700 px-4 py-3 flex items-center justify-between rounded-b-lg">
      <div class="flex items-center gap-4">
        <button
          @click="refreshPreview"
          class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm rounded-lg transition-colors"
        >
          Refresh Preview
        </button>
        <span class="text-xs text-gray-500">
          Auto-refreshing every 3s
        </span>
      </div>
      <div class="text-sm text-gray-400">
        {{ executionStore.currentTarget?.name || 'Imaging' }}
      </div>
    </div>
  </div>

  <!-- Position Display when not imaging -->
  <div v-else-if="executionStore.currentTarget" class="space-y-4">
    <div class="text-center">
      <h3 class="text-2xl font-semibold text-gray-200 mb-2">
        {{ executionStore.currentTarget.name }}
      </h3>
      <p class="text-sm text-gray-500">
        {{ executionStore.currentTarget.type }}
      </p>
    </div>

    <div class="bg-gray-900 border border-gray-700 rounded-lg p-6">
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
  </div>

  <!-- Empty State -->
  <div v-else class="flex items-center justify-center min-h-[400px]">
    <div class="text-center">
      <Telescope class="w-16 h-16 mx-auto text-gray-600 mb-4" />
      <p class="text-gray-400 text-lg mb-2">
        Ready to observe
      </p>
      <p class="text-sm text-gray-500">
        Connect telescope and start imaging
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onUnmounted } from 'vue'
import { useExecutionStore } from '@/stores/execution'
import { Telescope } from 'lucide-vue-next'

const executionStore = useExecutionStore()
const previewImage = ref(null)
const previewUpdateKey = ref(0)
let previewInterval = null

// Fetch latest preview image from live RTMP stream
const fetchPreview = async () => {
  try {
    // Get live frame from RTMP stream
    // Add timestamp to prevent caching and force refresh
    // NOTE: Using legacy endpoint for now - will be updated to /api/telescope/preview/frame in Task 2.2
    previewImage.value = `/api/telescope/features/images/preview/live?t=${Date.now()}`
    previewUpdateKey.value++
  } catch (err) {
    console.warn('Preview fetch failed:', err)
  }
}

const refreshPreview = () => {
  fetchPreview()
}

// Watch imaging state to start/stop preview updates
watch(() => executionStore.imaging.active, (isActive) => {
  if (isActive) {
    // Start auto-refresh when imaging begins
    previewImage.value = null
    fetchPreview()
    previewInterval = setInterval(fetchPreview, 3000) // Every 3 seconds
  } else {
    // Stop auto-refresh when imaging ends
    if (previewInterval) {
      clearInterval(previewInterval)
      previewInterval = null
    }
  }
})

onUnmounted(() => {
  if (previewInterval) {
    clearInterval(previewInterval)
  }
})

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
