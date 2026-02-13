<template>
  <div class="flex flex-col h-full">
    <!-- Panel Header -->
    <div class="px-4 py-3 border-b border-gray-800 bg-gray-900/50">
      <h2 class="text-sm font-semibold text-gray-200">Details</h2>
    </div>

    <!-- Panel Content -->
    <div class="flex-1 overflow-y-auto p-4">
      <div class="flex flex-col items-center justify-center h-full text-center">
        <div class="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mb-4">
          <InfoIcon class="w-8 h-8 text-gray-600" />
        </div>
        <p class="text-sm text-gray-500">
          Select a target to view details
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { InfoIcon } from 'lucide-vue-next'
</script>
