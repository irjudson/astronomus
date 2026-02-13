import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useTelescopeStore = defineStore('telescope', () => {
  const connected = ref(false)
  const ip = ref('')
  const currentTarget = ref(null)
  const ra = ref(0)
  const dec = ref(0)
  const alt = ref(0)
  const az = ref(0)

  const statusText = computed(() => {
    return connected.value ? 'Connected' : 'Disconnected'
  })

  const targetDisplay = computed(() => {
    return currentTarget.value?.name || 'No Target'
  })

  function setConnectionStatus(status, ipAddress = '') {
    connected.value = status
    ip.value = ipAddress
  }

  function updatePosition(position) {
    ra.value = position.ra
    dec.value = position.dec
    alt.value = position.alt
    az.value = position.az
  }

  function setCurrentTarget(target) {
    currentTarget.value = target
  }

  return {
    connected,
    ip,
    currentTarget,
    ra,
    dec,
    alt,
    az,
    statusText,
    targetDisplay,
    setConnectionStatus,
    updatePosition,
    setCurrentTarget
  }
})
