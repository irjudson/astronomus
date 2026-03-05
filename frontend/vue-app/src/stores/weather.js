import { defineStore } from 'pinia'
import axios from 'axios'
import { useSettingsStore } from './settings'

export const useWeatherStore = defineStore('weather', {
  state: () => ({
    current: null,
    local: null,       // real-time data from local WS-2902 station
    forecast: [],
    seeing: null,
    loading: false,
    error: null,
    lastUpdated: null
  }),

  getters: {
    weatherScore: (state) => {
      // Prefer local station astronomy score if available
      if (state.local?.astronomy?.score != null) {
        return Math.round(state.local.astronomy.score * 100)
      }
      if (!state.current) return null

      const { cloud_cover = 0, wind_speed = 0, humidity = 0 } = state.current
      const clouds = Math.max(0, Math.min(100, cloud_cover))
      const wind = Math.max(0, wind_speed)
      const humid = Math.max(0, Math.min(100, humidity))

      let score = 100
      score -= clouds
      if (wind > 20) score -= (wind - 20) * 2
      if (humid > 80) score -= (humid - 80)

      return Math.max(0, Math.min(100, score))
    },

    weatherQuality() {
      const score = this.weatherScore
      if (score === null) return 'Unknown'
      if (score >= 80) return 'Excellent'
      if (score >= 60) return 'Good'
      if (score >= 40) return 'Fair'
      if (score >= 20) return 'Poor'
      return 'Very Poor'
    },

    // Current temperature — local station takes priority
    currentTempC: (state) => {
      if (state.local?.outdoor_temp_c != null) return state.local.outdoor_temp_c
      return state.current?.temperature ?? null
    },

    currentHumidity: (state) => state.local?.humidity_pct ?? state.current?.humidity ?? null,
    currentWindMph: (state) => state.local?.wind_speed_mph ?? null,
    isRaining: (state) => state.local?.is_raining ?? false,
    astronomyIssues: (state) => state.local?.astronomy?.issues ?? []
  },

  actions: {
    async fetchLocalWeather() {
      try {
        const resp = await axios.get('/api/weather/local')
        this.local = resp.data
      } catch {
        this.local = null
      }
    },

    async fetchCurrentWeather() {
      this.loading = true
      this.error = null

      try {
        // Fetch local station (real-time) and 7Timer (forecast) in parallel
        const [, forecastResp] = await Promise.allSettled([
          this.fetchLocalWeather(),
          axios.get('/api/weather/astronomy', {
            params: {
              lat: useSettingsStore().settings.latitude ?? 40.7128,
              lon: useSettingsStore().settings.longitude ?? -74.0060,
              hours: 24,
            }
          })
        ])

        if (forecastResp.status === 'fulfilled' && forecastResp.value.data?.forecast?.length > 0) {
          const fc = forecastResp.value.data.forecast[0]
          this.current = {
            temperature: fc.temperature_c ?? 15,
            cloud_cover: fc.cloud_cover ?? 0,
            wind_speed: fc.wind_speed_kmh ?? 0,
            humidity: this.local?.humidity_pct ?? 50,
            seeing: fc.seeing ?? 3,
            transparency: fc.transparency ?? 3,
          }
          this.forecast = forecastResp.value.data.forecast
        } else if (this.local) {
          // Fallback: build current from local station only
          this.current = {
            temperature: this.local.outdoor_temp_c,
            cloud_cover: 0,
            wind_speed: this.local.wind_speed_mph * 1.60934,
            humidity: this.local.humidity_pct,
          }
        }

        this.lastUpdated = new Date()
      } catch (err) {
        this.error = 'Failed to load weather data: ' + err.message
      } finally {
        this.loading = false
      }
    },

    async fetchForecast() {
      try {
        const settings = useSettingsStore().settings
        const response = await axios.get('/api/weather/astronomy', {
          params: {
            lat: settings.latitude ?? 40.7128,
            lon: settings.longitude ?? -74.0060,
            hours: 48,
          }
        })
        this.forecast = response.data.forecast ?? []
      } catch (err) {
        console.error('Forecast error:', err)
      }
    },

    async fetchSeeing() {
      try {
        const response = await axios.get('/api/astronomy/weather/7timer')
        this.seeing = response.data
      } catch (err) {
        console.error('Seeing error:', err)
      }
    },

    async fetchAllWeatherData() {
      await Promise.all([
        this.fetchCurrentWeather(),
        this.fetchForecast(),
        this.fetchSeeing()
      ])
    }
  }
})
