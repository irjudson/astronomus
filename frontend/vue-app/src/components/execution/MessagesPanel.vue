<template>
  <BaseCard padding="md">
    <div class="flex justify-between items-center mb-3">
      <h3 class="text-sm font-semibold text-astro-text-muted">
        TELESCOPE MESSAGES
      </h3>
      <button
        v-if="executionStore.messages.length > 0"
        @click="executionStore.clearMessages()"
        class="text-xs text-astro-text-muted hover:text-astro-text"
      >
        Clear
      </button>
    </div>

    <div class="message-list">
      <div v-if="executionStore.messages.length === 0" class="text-xs text-astro-text-muted text-center py-4">
        No messages
      </div>
      <div
        v-for="message in executionStore.messages"
        :key="message.id"
        class="message-item text-xs font-mono text-astro-text-muted py-1"
      >
        [{{ formatTime(message.timestamp) }}] {{ message.text }}
      </div>
    </div>
  </BaseCard>
</template>

<script setup>
import { useExecutionStore } from '@/stores/execution'
import BaseCard from '@/components/common/BaseCard.vue'

const executionStore = useExecutionStore()

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString()
}
</script>

<style scoped>
.message-list {
  max-height: 200px;
  overflow-y: auto;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(0, 217, 255, 0.2);
  border-radius: 4px;
  padding: 8px;
}

.message-item {
  border-bottom: 1px dashed rgba(255, 255, 255, 0.05);
}

.message-item:last-child {
  border-bottom: none;
}
</style>
