<template>
  <button
    @click="$emit('toggle')"
    class="p-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-md transition-colors text-gray-400 hover:text-gray-200"
    :title="collapsed ? `Show ${position} panel` : `Hide ${position} panel`"
  >
    <ChevronLeftIcon v-if="position === 'left' && !collapsed" class="w-4 h-4" />
    <ChevronRightIcon v-if="position === 'left' && collapsed" class="w-4 h-4" />
    <ChevronRightIcon v-if="position === 'right' && !collapsed" class="w-4 h-4" />
    <ChevronLeftIcon v-if="position === 'right' && collapsed" class="w-4 h-4" />
    <ChevronDownIcon v-if="position === 'bottom' && !collapsed" class="w-4 h-4" />
    <ChevronUpIcon v-if="position === 'bottom' && collapsed" class="w-4 h-4" />
  </button>
</template>

<script setup>
import { ChevronLeftIcon, ChevronRightIcon, ChevronUpIcon, ChevronDownIcon } from 'lucide-vue-next'

defineProps({
  position: {
    type: String,
    required: true,
    validator: (value) => ['left', 'right', 'bottom'].includes(value)
  },
  collapsed: {
    type: Boolean,
    default: false
  }
})

defineEmits(['toggle'])
</script>
