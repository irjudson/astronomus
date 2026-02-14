import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useWeatherStore } from '../weather'
import axios from 'axios'

vi.mock('axios')

describe('Weather Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetches current weather from API', async () => {
    const mockWeather = {
      temperature: 15,
      humidity: 65,
      cloud_cover: 20,
      wind_speed: 5
    }

    axios.get.mockResolvedValue({ data: mockWeather })

    const store = useWeatherStore()
    await store.fetchCurrentWeather()

    expect(store.current).toEqual(mockWeather)
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('handles weather API errors', async () => {
    axios.get.mockRejectedValue(new Error('API error'))

    const store = useWeatherStore()
    await store.fetchCurrentWeather()

    expect(store.error).toBeTruthy()
    expect(store.loading).toBe(false)
  })
})
