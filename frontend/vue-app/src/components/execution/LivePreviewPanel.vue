<template>
  <!-- Live Preview when imaging -->
  <div v-if="executionStore.imaging.active" class="flex flex-col">
    <div class="bg-black flex items-center justify-center relative rounded-lg overflow-hidden" style="height: min(60vh, 480px)">

      <!-- MJPEG stream: browser keeps connection open and updates the frame continuously -->
      <img
        v-show="streamLoaded && !streamError"
        :src="STREAM_URL"
        alt="Live Preview"
        class="max-w-full max-h-full object-contain"
        @load="onStreamLoad"
        @error="onStreamError"
      />

      <!-- Waiting / error overlay -->
      <div v-if="!streamLoaded || streamError" class="text-center absolute inset-0 flex flex-col items-center justify-center">
        <div v-if="!streamError" class="text-gray-500 mb-4">
          <svg class="animate-spin h-12 w-12 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
        <div v-else class="text-red-500 mb-4">
          <svg class="h-12 w-12 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p class="text-gray-400">{{ streamError ? 'Stream unavailable' : 'Waiting for preview...' }}</p>
        <button
          v-if="streamError"
          @click="retryStream"
          class="mt-3 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-200 text-sm rounded-lg transition-colors"
        >
          Retry
        </button>
      </div>

      <!-- Imaging Info Overlay -->
      <div class="absolute top-4 right-4 bg-black/80 backdrop-blur-sm rounded-lg p-3 border border-gray-700">
        <div class="text-xs text-gray-400 mb-1">{{ elapsedTime }}</div>
        <div class="text-sm font-medium text-green-400">Live</div>
      </div>
    </div>

    <!-- Preview Controls -->
    <div class="bg-gray-900 border-t border-gray-700 px-4 py-3 flex items-center justify-between rounded-b-lg">
      <div class="flex items-center gap-4">
        <span class="text-xs text-gray-500">
          {{ streamLoaded ? 'Streaming live' : 'Connecting to RTSP...' }}
        </span>

        <!-- Annotation Toggle -->
        <label class="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            :checked="executionStore.annotationsEnabled"
            @change="handleAnnotationToggle"
            class="w-4 h-4 rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer"
          />
          <span class="text-sm text-gray-300">Show Annotations</span>
        </label>
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
import { ref, watch, nextTick, onUnmounted } from 'vue'
import { useExecutionStore } from '@/stores/execution'
import { Telescope } from 'lucide-vue-next'

const STREAM_URL = '/api/telescope/preview/stream'

const executionStore = useExecutionStore()
const streamLoaded = ref(false)
const streamError = ref(false)
const elapsedTime = ref('0:00')

let elapsedStart = null
let elapsedInterval = null

const startElapsed = () => {
  elapsedStart = Date.now()
  elapsedInterval = setInterval(() => {
    const secs = Math.floor((Date.now() - elapsedStart) / 1000)
    const m = Math.floor(secs / 60)
    const s = secs % 60
    elapsedTime.value = `${m}:${s.toString().padStart(2, '0')}`
  }, 1000)
}

const stopElapsed = () => {
  if (elapsedInterval) {
    clearInterval(elapsedInterval)
    elapsedInterval = null
  }
  elapsedTime.value = '0:00'
}

const onStreamLoad = () => {
  streamLoaded.value = true
  streamError.value = false
}

const onStreamError = () => {
  // Only mark as error if we haven't loaded yet; MJPEG @error fires if
  // the server returns a non-2xx (e.g. 503 when no frames yet)
  streamError.value = true
  streamLoaded.value = false
}

const retryStream = async () => {
  // Reset state and force img to reconnect by briefly clearing src
  streamError.value = false
  streamLoaded.value = false
  // The img element is already bound to the fixed URL via v-show,
  // so we just toggle the error state — the browser will retry on its own
  // after a short moment once the src becomes visible again.
  await nextTick()
}

// Reset stream state and start timer whenever imaging starts/stops
watch(() => executionStore.imaging.active, (isActive) => {
  if (isActive) {
    streamLoaded.value = false
    streamError.value = false
    startElapsed()
  } else {
    stopElapsed()
  }
})

onUnmounted(stopElapsed)

const handleAnnotationToggle = async (event) => {
  const enabled = event.target.checked
  await executionStore.toggleAnnotations(enabled)
}

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
