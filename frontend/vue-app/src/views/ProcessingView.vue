<template>
  <PanelContainer
    v-model:left-panel-visible="leftPanelVisible"
    :console-visible="false"
  >
    <!-- Left panel header -->
    <template #left-header>
      <div>
        <h3 class="text-sm font-semibold text-gray-200">Files & Processing</h3>
      </div>
    </template>

    <!-- Left panel label (for peek tab) -->
    <template #left-label>Files</template>

    <!-- Left: File Browser & Processing Controls -->
    <template #left>
      <div class="space-y-4">
        <!-- File Browser -->
        <div>
          <FileBrowser />
        </div>

        <!-- Processing Controls -->
        <div class="p-4 space-y-4 border-t border-gray-800">
          <!-- Batch Processing -->
          <div class="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Batch Processing
            </h3>

            <div class="space-y-3">
              <button
                @click="processingStore.batchProcessNew()"
                :disabled="processingStore.loading"
                class="w-full px-4 py-2 rounded font-medium transition-colors bg-green-600 hover:bg-green-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Process All New Files
              </button>

              <p class="text-xs text-gray-500">
                Automatically processes all unprocessed FITS files
              </p>
            </div>
          </div>

          <!-- Stack Selected Images -->
          <div class="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Stack Selected
            </h3>

            <div class="space-y-3">
              <button
                @click="processingStore.stackImages()"
                :disabled="!processingStore.hasSelection || processingStore.loading"
                class="w-full px-4 py-2 rounded font-medium transition-colors bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Stack {{ processingStore.selectedFileCount }} Image{{ processingStore.selectedFileCount !== 1 ? 's' : '' }}
              </button>

              <div v-if="processingStore.activeJob" class="space-y-2">
                <div class="text-xs text-gray-500">
                  Status: {{ processingStore.activeJob.status }}
                </div>
                <div v-if="processingStore.activeJob.progress_percent !== undefined" class="w-full bg-gray-800 rounded-full h-2">
                  <div
                    class="bg-blue-500 h-2 rounded-full transition-all duration-300"
                    :style="{ width: `${processingStore.activeJob.progress_percent}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Job History -->
          <div v-if="processingStore.processingJobs.length > 0" class="bg-gray-900 border border-gray-800 rounded-lg p-4">
            <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Job History
            </h3>

            <div class="space-y-2 max-h-64 overflow-y-auto">
              <div
                v-for="job in processingStore.processingJobs"
                :key="job.id"
                class="p-2 rounded bg-gray-800 text-xs"
              >
                <div class="flex justify-between items-center">
                  <span class="text-gray-200 truncate">{{ job.name || 'Stack Job' }}</span>
                  <span
                    class="text-xs font-semibold"
                    :class="{
                      'text-green-500': job.status === 'completed',
                      'text-red-500': job.status === 'failed',
                      'text-yellow-500': job.status === 'processing',
                      'text-gray-400': job.status === 'pending'
                    }"
                  >
                    {{ job.status }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- Main: Image Preview -->
    <template #main>
      <div class="flex flex-col h-full">
        <!-- View Header -->
        <div class="bg-gray-900/50 border-b border-gray-800 px-4 py-3 flex-none">
          <h2 class="text-lg font-semibold text-gray-200">Preview</h2>
          <p class="text-sm text-gray-500">
            {{ processingStore.previewImage ? 'Image ready' : 'Select a file to preview' }}
          </p>
        </div>

        <!-- Content -->
        <div class="flex-1 overflow-hidden flex items-center justify-center bg-gray-950">
          <div v-if="processingStore.previewImage" class="flex items-center justify-center h-full">
            <img
              :src="processingStore.previewImage"
              alt="Preview"
              class="max-w-full max-h-full object-contain"
            />
          </div>

          <div v-else class="text-center">
            <p class="text-gray-500">
              No preview available
            </p>
          </div>
        </div>
      </div>
    </template>

  </PanelContainer>
</template>

<script setup>
import { ref } from 'vue'
import { useProcessingStore } from '@/stores/processing'
import PanelContainer from '@/components/layout/PanelContainer.vue'
import FileBrowser from '@/components/processing/FileBrowser.vue'

const processingStore = useProcessingStore()
const leftPanelVisible = ref(true)
</script>
