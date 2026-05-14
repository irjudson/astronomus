import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePlanningStore } from '../planning'
import axios from 'axios'

vi.mock('axios')

describe('Planning Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('generates observation plan', async () => {
    const mockPlan = {
      id: 'plan-123',
      targets: [
        { name: 'M31', start_time: '20:00', duration: 60 }
      ],
      total_duration: 60
    }

    axios.post.mockResolvedValue({ data: mockPlan })

    const store = usePlanningStore()
    store.selectedTargets = [{ id: 'M31', name: 'Andromeda' }]

    await store.generatePlan()

    expect(store.currentPlan).toEqual(mockPlan)
    expect(store.loading).toBe(false)
  })

  it('sendToTelescope posts plan_id to upload endpoint', async () => {
    axios.post.mockResolvedValue({ data: { success: true } })
    const store = usePlanningStore()
    await store.sendToTelescope(42)
    expect(axios.post).toHaveBeenCalledWith(
      '/api/telescope/features/plan/upload',
      { plan_id: 42 }
    )
  })

  it('sendToTelescope throws on failure', async () => {
    axios.post.mockRejectedValue({ response: { data: { detail: 'scope error' } } })
    const store = usePlanningStore()
    await expect(store.sendToTelescope(1)).rejects.toBeTruthy()
  })
})
