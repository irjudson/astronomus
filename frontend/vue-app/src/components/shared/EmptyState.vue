<template>
  <div class="flex flex-col items-center justify-center h-full text-gray-400 py-12">
    <div class="w-16 h-16 bg-gray-900 rounded-full flex items-center justify-center mb-4 border border-gray-800">
      <component :is="icon" class="w-8 h-8 text-blue-500" />
    </div>
    <h3 class="text-lg font-semibold text-gray-200 mb-2">{{ title }}</h3>
    <p class="text-sm text-center max-w-md text-gray-500">
      {{ message }}
    </p>
    <button
      v-if="actionLabel"
      @click="$emit('action')"
      class="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors"
    >
      {{ actionLabel }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  icon: {
    type: Object,
    required: true
  },
  title: {
    type: String,
    required: true
  },
  message: {
    type: String,
    required: true
  },
  actionLabel: {
    type: String,
    default: null
  }
})

defineEmits(['action'])
</script>
