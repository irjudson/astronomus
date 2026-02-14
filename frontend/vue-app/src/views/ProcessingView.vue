<template>
  <div class="processing-view flex h-full">
    <div class="processing-sidebar w-80 border-r border-astro-border bg-astro-surface overflow-y-auto p-4">
      <FileBrowser />
    </div>

    <div class="processing-main flex-1 flex flex-col">
      <div class="flex-1 p-6">
        <div v-if="processingStore.previewImage" class="h-full flex items-center justify-center">
          <img
            :src="processingStore.previewImage"
            alt="Preview"
            class="max-w-full max-h-full object-contain rounded"
          />
        </div>

        <div v-else class="h-full flex items-center justify-center">
          <p class="text-astro-text-muted">
            No preview available
          </p>
        </div>
      </div>
    </div>

    <div class="processing-controls w-80 border-l border-astro-border bg-astro-surface overflow-y-auto p-4 space-y-4">
      <BaseCard padding="md">
        <h3 class="text-sm font-semibold text-astro-text-muted mb-3">
          PROCESSING
        </h3>

        <div class="space-y-3">
          <BaseButton
            variant="primary"
            @click="processingStore.stackImages()"
            :disabled="!processingStore.hasSelection"
            class="w-full"
          >
            Stack Images
          </BaseButton>

          <div v-if="processingStore.activeJob" class="space-y-2">
            <div class="text-xs text-astro-text-muted">
              Status: {{ processingStore.activeJob.status }}
            </div>
            <div v-if="processingStore.activeJob.progress !== undefined" class="w-full bg-astro-elevated rounded-full h-2">
              <div
                class="bg-astro-accent h-2 rounded-full transition-all duration-300"
                :style="{ width: `${processingStore.activeJob.progress}%` }"
              ></div>
            </div>
          </div>
        </div>
      </BaseCard>

      <BaseCard v-if="processingStore.processingJobs.length > 0" padding="md">
        <h3 class="text-sm font-semibold text-astro-text-muted mb-3">
          JOB HISTORY
        </h3>

        <div class="space-y-2 max-h-64 overflow-y-auto">
          <div
            v-for="job in processingStore.processingJobs"
            :key="job.id"
            class="p-2 rounded bg-astro-elevated text-xs"
          >
            <div class="flex justify-between items-center">
              <span class="text-astro-text truncate">{{ job.name || 'Stack Job' }}</span>
              <span
                class="text-xs font-semibold"
                :class="{
                  'text-astro-success': job.status === 'completed',
                  'text-astro-error': job.status === 'failed',
                  'text-astro-warning': job.status === 'processing',
                  'text-astro-text-dim': job.status === 'pending'
                }"
              >
                {{ job.status }}
              </span>
            </div>
          </div>
        </div>
      </BaseCard>
    </div>
  </div>
</template>

<script setup>
import { useProcessingStore } from '@/stores/processing'
import FileBrowser from '@/components/processing/FileBrowser.vue'
import BaseCard from '@/components/common/BaseCard.vue'
import BaseButton from '@/components/common/BaseButton.vue'

const processingStore = useProcessingStore()
</script>
