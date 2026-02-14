import { defineStore } from 'pinia'
import axios from 'axios'

export const useWeatherStore = defineStore('weather', {
  state: () => ({
    current: null,
    forecast: [],
    seeing: null,
    loading: false,
    error: null,
    lastUpdated: null
  }),

  getters: {
    weatherScore: (state) => {
      if (!state.current) return null

      const { cloud_cover = 0, wind_speed = 0, humidity = 0 } = state.current

      // Validate inputs
      const clouds = Math.max(0, Math.min(100, cloud_cover))
      const wind = Math.max(0, wind_speed)
      const humid = Math.max(0, Math.min(100, humidity))

      let score = 100
      score -= clouds

      if (wind > 20) {
        score -= (wind - 20) * 2
      }

      if (humid > 80) {
        score -= (humid - 80)
      }

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
    }
  },

  actions: {
    async fetchCurrentWeather() {
      this.loading = true
      this.error = null

      try {
        // Get location from settings
        const settings = localStorage.getItem('astronomus_settings')
        let lat = 40.7128
        let lon = -74.0060

        if (settings) {
          const parsed = JSON.parse(settings)
          lat = parsed.latitude || lat
          lon = parsed.longitude || lon
        }

        // Fetch astronomy weather with location
        const response = await axios.get('/api/weather/astronomy', {
          params: { lat, lon, hours: 24 }
        })

        // The astronomy endpoint returns an object with a forecast array
        // Use the first forecast as "current" weather
        if (response.data && response.data.forecast && response.data.forecast.length > 0) {
          const forecast = response.data.forecast[0]
          this.current = {
            temperature: forecast.temperature_c || 15,
            cloud_cover: forecast.cloud_cover || 0,
            wind_speed: forecast.wind_speed_kmh || 0,
            humidity: 50, // Not provided by astronomy endpoint
            seeing: forecast.seeing || 3,
            transparency: forecast.transparency || 3
          }
          this.forecast = response.data.forecast
        }

        this.lastUpdated = new Date()
      } catch (err) {
        this.error = 'Failed to load weather data: ' + err.message
        console.error('Weather error:', err)
      } finally {
        this.loading = false
      }
    },

    async fetchForecast() {
      try {
        const response = await axios.get('/api/weather/forecast')
        this.forecast = response.data
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
