<template>
  <button
    :type="type"
    :disabled="disabled"
    :class="buttonClasses"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'secondary', 'danger', 'ghost'].includes(value)
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  },
  type: {
    type: String,
    default: 'button'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])

const buttonClasses = computed(() => {
  const base = 'rounded font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-astro-accent focus:ring-offset-2 focus:ring-offset-astro-bg disabled:opacity-50 disabled:cursor-not-allowed'

  const variants = {
    primary: 'bg-astro-accent hover:bg-astro-accent-hover text-white',
    secondary: 'bg-astro-surface hover:bg-astro-elevated text-astro-text border border-astro-border',
    danger: 'bg-astro-error hover:bg-red-600 text-white',
    ghost: 'hover:bg-astro-elevated text-astro-text'
  }

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  }

  return `${base} ${variants[props.variant]} ${sizes[props.size]}`
})
</script>
