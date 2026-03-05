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
})
