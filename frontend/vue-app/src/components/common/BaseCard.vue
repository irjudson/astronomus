<template>
  <div :class="cardClasses">
    <slot />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  padding: {
    type: String,
    default: 'md',
    validator: (value) => ['none', 'sm', 'md', 'lg'].includes(value)
  },
  hoverable: {
    type: Boolean,
    default: false
  }
})

const cardClasses = computed(() => {
  const base = 'bg-gray-900 border border-gray-800 rounded-lg'

  const paddings = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6'
  }

  const hover = props.hoverable ? 'hover:border-gray-700 transition-colors cursor-pointer' : ''

  return `${base} ${paddings[props.padding]} ${hover}`
})
</script>
