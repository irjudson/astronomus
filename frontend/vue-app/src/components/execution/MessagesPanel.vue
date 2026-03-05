<template>
  <div>
    <div class="flex justify-between items-center mb-3">
      <h3 class="text-sm font-semibold text-gray-500">
        TELESCOPE MESSAGES
      </h3>
      <button
        v-if="executionStore.messages.length > 0"
        @click="executionStore.clearMessages()"
        class="text-xs text-gray-500 hover:text-gray-200"
      >
        Clear
      </button>
    </div>

    <div class="message-list">
      <div v-if="executionStore.messages.length === 0" class="text-xs text-gray-500 text-center py-4">
        No messages
      </div>
      <div
        v-for="message in executionStore.messages"
        :key="message.id"
        class="message-item text-xs font-mono text-gray-500 py-1"
      >
        [{{ formatTime(message.timestamp) }}] {{ message.text }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { useExecutionStore } from '@/stores/execution'

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
  background: rgb(31, 41, 55);
  border: 1px solid rgb(55, 65, 81);
  border-radius: 4px;
  padding: 8px;
}

.message-item {
  border-bottom: 1px dashed rgba(107, 114, 128, 0.2);
}

.message-item:last-child {
  border-bottom: none;
}
</style>
