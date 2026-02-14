<template>
  <div class="relative">
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="inputClasses"
      @input="$emit('update:modelValue', $event.target.value)"
      @blur="$emit('blur', $event)"
      @focus="$emit('focus', $event)"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  },
  placeholder: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  error: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:modelValue', 'blur', 'focus'])

const inputClasses = computed(() => {
  const base = 'w-full px-3 py-2 bg-astro-elevated border rounded text-astro-text placeholder-astro-text-dim focus:outline-none focus:ring-2 focus:ring-astro-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors'

  const borderColor = props.error ? 'border-astro-error' : 'border-astro-border focus:border-astro-accent'

  return `${base} ${borderColor}`
})
</script>
