import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useExecutionStore } from '../execution'
import axios from 'axios'

vi.mock('axios')

describe('Execution Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('connects to telescope', async () => {
    axios.post.mockResolvedValue({ data: { status: 'connected' } })

    const store = useExecutionStore()
    await store.connectTelescope('192.168.1.100')

    expect(store.connected).toBe(true)
    expect(store.telescopeIp).toBe('192.168.1.100')
  })

  it('updates telescope position', () => {
    const store = useExecutionStore()
    store.updatePosition({
      ra: 10.5,
      dec: 45.0,
      alt: 60.0,
      az: 180.0
    })

    expect(store.position.ra).toBe(10.5)
    expect(store.position.alt).toBe(60.0)
  })
})
