<template>
  <div class="space-y-4">
    <!-- Scan Button -->
    <div class="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <button
        @click="scanFiles"
        :disabled="processingStore.scanning"
        class="w-full px-4 py-2 rounded-lg font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {{ processingStore.scanning ? 'Scanning...' : 'Scan for New Images' }}
      </button>

      <div v-if="processingStore.scanResults" class="mt-3 p-3 bg-gray-800 rounded-lg">
        <div class="text-xs text-gray-400 mb-1">Scan Results:</div>
        <div class="text-sm text-gray-200">
          {{ processingStore.scanResults.total_objects }} objects,
          {{ processingStore.scanResults.total_files }} files
        </div>
      </div>
    </div>

    <!-- Captures List -->
    <div class="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <h3 class="text-sm font-semibold text-gray-500 mb-3">
        CAPTURES BY TARGET
      </h3>

      <div v-if="processingStore.loading" class="text-sm text-gray-500">
        Loading captures...
      </div>

      <div v-else-if="processingStore.captures.length > 0" class="space-y-2 max-h-96 overflow-y-auto">
        <div
          v-for="capture in processingStore.captures"
          :key="capture.catalog_id"
          @click="selectCapture(capture.catalog_id)"
          class="p-3 rounded-lg cursor-pointer transition-colors border"
          :class="processingStore.selectedCapture === capture.catalog_id
            ? 'bg-blue-500/20 border-blue-500'
            : 'bg-gray-800 border-gray-700 hover:bg-gray-750'"
        >
          <div class="flex justify-between items-start mb-1">
            <span class="text-sm font-medium text-gray-200">{{ capture.catalog_id }}</span>
            <span class="text-xs text-gray-500">{{ capture.total_frames }} frames</span>
          </div>
          <div class="flex justify-between items-center text-xs text-gray-400">
            <span>{{ formatTime(capture.total_exposure_seconds) }}</span>
            <span v-if="capture.status" class="px-2 py-0.5 rounded bg-gray-700 text-gray-300">
              {{ capture.status }}
            </span>
          </div>
        </div>
      </div>

      <div v-else class="text-sm text-gray-400 text-center py-4">
        No captures found. Click "Scan for New Images" above.
      </div>
    </div>

    <!-- Files for Selected Capture -->
    <div v-if="processingStore.selectedCapture" class="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <h3 class="text-sm font-semibold text-gray-500 mb-3">
        FILES: {{ processingStore.selectedCapture }}
      </h3>

      <div v-if="processingStore.files.length > 0" class="space-y-1 max-h-64 overflow-y-auto">
        <div
          v-for="file in processingStore.files"
          :key="file.id"
          @click="toggleFileSelection(file)"
          class="flex items-center justify-between p-2 rounded hover:bg-gray-800 cursor-pointer transition-colors"
          :class="{ 'bg-blue-500/20 border border-blue-500': isSelected(file) }"
        >
          <span class="text-sm text-gray-200 truncate">{{ file.name }}</span>
          <span class="text-xs text-gray-400">{{ formatSize(file.size) }}</span>
        </div>
      </div>

      <div v-if="processingStore.selectedFileCount > 0" class="pt-2 border-t border-gray-800 mt-2">
        <div class="text-xs text-gray-500 mb-2">
          {{ processingStore.selectedFileCount }} files selected
        </div>

        <button
          @click="processingStore.clearSelection()"
          class="w-full px-3 py-1.5 rounded font-medium transition-colors text-sm bg-gray-700 hover:bg-gray-600 text-gray-200 border border-gray-600"
        >
          Clear Selection
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useProcessingStore } from '@/stores/processing'

const processingStore = useProcessingStore()

const scanFiles = async () => {
  await processingStore.scanForNewFiles()
}

const selectCapture = async (catalogId) => {
  await processingStore.selectCapture(catalogId)
}

const isSelected = (file) => {
  return processingStore.selectedFiles.some(f => f.id === file.id)
}

const toggleFileSelection = (file) => {
  if (isSelected(file)) {
    processingStore.deselectFile(file)
  } else {
    processingStore.selectFile(file)
  }
}

const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const formatTime = (seconds) => {
  if (!seconds) return '0s'
  const hours = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  if (hours > 0) return `${hours}h ${mins}m`
  if (mins > 0) return `${mins}m`
  return `${seconds}s`
}

onMounted(() => {
  processingStore.loadCaptures()
})
</script>
