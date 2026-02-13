import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const rightPanelCollapsed = ref(false)
  const consoleCollapsed = ref(true)

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function toggleRightPanel() {
    rightPanelCollapsed.value = !rightPanelCollapsed.value
  }

  function toggleConsole() {
    consoleCollapsed.value = !consoleCollapsed.value
  }

  return {
    sidebarCollapsed,
    rightPanelCollapsed,
    consoleCollapsed,
    toggleSidebar,
    toggleRightPanel,
    toggleConsole
  }
})
