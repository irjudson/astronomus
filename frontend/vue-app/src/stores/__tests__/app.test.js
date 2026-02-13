import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAppStore } from '../app'

describe('App Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with correct defaults', () => {
    const store = useAppStore()
    expect(store.sidebarCollapsed).toBe(false)
    expect(store.rightPanelCollapsed).toBe(false)
    expect(store.consoleCollapsed).toBe(true)
  })

  it('toggles sidebar state', () => {
    const store = useAppStore()
    expect(store.sidebarCollapsed).toBe(false)
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(true)
    store.toggleSidebar()
    expect(store.sidebarCollapsed).toBe(false)
  })

  it('toggles right panel state', () => {
    const store = useAppStore()
    expect(store.rightPanelCollapsed).toBe(false)
    store.toggleRightPanel()
    expect(store.rightPanelCollapsed).toBe(true)
  })

  it('toggles console state', () => {
    const store = useAppStore()
    expect(store.consoleCollapsed).toBe(true)
    store.toggleConsole()
    expect(store.consoleCollapsed).toBe(false)
  })
})
