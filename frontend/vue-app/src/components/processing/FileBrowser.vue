<template>
  <BaseCard padding="md">
    <h3 class="text-sm font-semibold text-astro-text-muted mb-3">
      FILE BROWSER
    </h3>

    <div class="space-y-2">
      <div class="text-xs text-astro-text-dim">
        {{ processingStore.currentDirectory }}
      </div>

      <div v-if="processingStore.loading" class="text-sm text-astro-text-muted">
        Loading files...
      </div>

      <div v-else-if="processingStore.files.length > 0" class="space-y-1 max-h-96 overflow-y-auto">
        <div
          v-for="file in processingStore.files"
          :key="file.path"
          @click="toggleFileSelection(file)"
          class="flex items-center justify-between p-2 rounded hover:bg-astro-elevated cursor-pointer transition-colors"
          :class="{ 'bg-astro-accent/20 border border-astro-accent': isSelected(file) }"
        >
          <span class="text-sm text-astro-text truncate">{{ file.name }}</span>
          <span class="text-xs text-astro-text-dim">{{ formatSize(file.size) }}</span>
        </div>
      </div>

      <div v-else class="text-sm text-astro-text-dim">
        No FITS files found
      </div>

      <div v-if="processingStore.selectedFileCount > 0" class="pt-2 border-t border-astro-border">
        <div class="text-xs text-astro-text-muted mb-2">
          {{ processingStore.selectedFileCount }} files selected
        </div>

        <BaseButton
          variant="secondary"
          @click="processingStore.clearSelection()"
          size="sm"
          class="w-full"
        >
          Clear Selection
        </BaseButton>
      </div>
    </div>
  </BaseCard>
</template>

<script setup>
import { onMounted } from 'vue'
import { useProcessingStore } from '@/stores/processing'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const processingStore = useProcessingStore()

const isSelected = (file) => {
  return processingStore.selectedFiles.includes(file)
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

onMounted(() => {
  processingStore.browseDirectory('/data')
})
</script>
