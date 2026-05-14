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
    // fetchCurrentWeather calls /api/weather/local and /api/weather/astronomy in parallel.
    // Mock both: local returns null (ECONNREFUSED handled gracefully), astronomy returns a forecast.
    axios.get.mockImplementation((url) => {
      if (url.includes('/api/weather/local')) {
        return Promise.reject(new Error('no local station'))
      }
      return Promise.resolve({
        data: {
          forecast: [
            { temperature_c: 15, cloud_cover: 20, wind_speed_kmh: 5, seeing: 3, transparency: 3 }
          ]
        }
      })
    })

    const store = useWeatherStore()
    await store.fetchCurrentWeather()

    expect(store.current).toMatchObject({ temperature: 15, cloud_cover: 20 })
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('handles weather API errors gracefully', async () => {
    // When all requests fail, store.current remains null and loading returns to false.
    axios.get.mockRejectedValue(new Error('API error'))

    const store = useWeatherStore()
    await store.fetchCurrentWeather()

    expect(store.current).toBeNull()
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

  it('fetchMultiDayForecast populates multiDayForecast', async () => {
    const mockData = [
      { date: '2026-05-14', cloud_pct: 20, temp_min: 8, temp_max: 18, wind_mps: 3, precip_mm: 0, astronomy_score: 80 }
    ]
    axios.get.mockResolvedValue({ data: mockData })
    const store = useWeatherStore()
    await store.fetchMultiDayForecast()
    expect(store.multiDayForecast).toEqual(mockData)
  })

  it('fetchMultiDayForecast handles error gracefully', async () => {
    axios.get.mockRejectedValue(new Error('net error'))
    const store = useWeatherStore()
    await store.fetchMultiDayForecast()
    expect(store.multiDayForecast).toEqual([])
  })
})
