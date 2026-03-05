<template>
  <div class="fixed top-4 right-4 z-[200] flex flex-col gap-2 pointer-events-none w-80">
    <TransitionGroup name="toast">
      <div
        v-for="n in toastStore.notifications"
        :key="n.id"
        class="pointer-events-auto flex items-start gap-2 px-4 py-3 rounded-lg text-sm shadow-xl cursor-pointer select-none"
        :class="typeClass(n.type)"
        @click="toastStore.dismiss(n.id)"
      >
        <span class="shrink-0 mt-0.5">{{ icon(n.type) }}</span>
        <span class="flex-1 leading-snug">{{ n.message }}</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { useToastStore } from '@/stores/toast'

const toastStore = useToastStore()

const typeClass = (type) => {
  switch (type) {
    case 'success': return 'bg-green-900/90 border border-green-700 text-green-100'
    case 'error':   return 'bg-red-900/90 border border-red-700 text-red-100'
    case 'warning': return 'bg-yellow-900/90 border border-yellow-700 text-yellow-100'
    default:        return 'bg-gray-800/90 border border-gray-600 text-gray-100'
  }
}

const icon = (type) => {
  switch (type) {
    case 'success': return '✓'
    case 'error':   return '✗'
    case 'warning': return '⚠'
    default:        return 'ℹ'
  }
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}
.toast-enter-from {
  opacity: 0;
  transform: translateX(100%);
}
.toast-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
.toast-move {
  transition: transform 0.25s ease;
}
</style>
