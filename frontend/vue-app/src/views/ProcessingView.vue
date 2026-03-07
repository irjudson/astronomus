<template>
  <PanelContainer
    v-model:left-panel-visible="leftPanelVisible"
    :console-visible="false"
  >
    <!-- Left panel header -->
    <template #left-header>
      <div>
        <h3 class="text-sm font-semibold text-gray-200">Files & Review</h3>
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

        <!-- Processing Controls placeholder -->
        <div class="p-4 border-t border-gray-800">
          <div class="p-6 text-center text-gray-500 text-sm border border-dashed border-gray-700 rounded-lg mt-4">
            Image export and advanced processing coming soon.
          </div>
        </div>
      </div>
    </template>

    <!-- Main: Image Preview -->
    <template #main>
      <div class="flex flex-col h-full">
        <!-- View Header -->
        <div class="bg-gray-900/50 border-b border-gray-800 px-4 py-3 flex-none">
          <h2 class="text-lg font-semibold text-gray-200">Review</h2>
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
