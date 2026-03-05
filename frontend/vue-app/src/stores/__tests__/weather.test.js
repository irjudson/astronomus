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

  it('calculates weather score with perfect conditions', () => {
    const store = useWeatherStore()
    store.current = { cloud_cover: 0, wind_speed: 0, humidity: 0 }
    expect(store.weatherScore).toBe(100)
  })

  it('calculates weather score with poor conditions', () => {
    const store = useWeatherStore()
    store.current = { cloud_cover: 100, wind_speed: 50, humidity: 90 }
    expect(store.weatherScore).toBe(0)  // Should clamp to 0
  })

  it('handles missing weather properties gracefully', () => {
    const store = useWeatherStore()
    store.current = {}  // No properties
    expect(store.weatherScore).toBe(100)  // Defaults to perfect
  })

  it('returns correct quality ratings', () => {
    const store = useWeatherStore()
    store.current = { cloud_cover: 10, wind_speed: 5, humidity: 50 }
    expect(store.weatherQuality).toBe('Excellent')  // Score ~90
  })

  it('returns Unknown quality when no weather data', () => {
    const store = useWeatherStore()
    expect(store.weatherQuality).toBe('Unknown')
  })
})
