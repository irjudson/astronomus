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

      // Calculate score based on cloud cover, seeing, wind
      let score = 100

      // Cloud cover penalty (0-100%)
      score -= state.current.cloud_cover

      // Wind penalty (> 20 km/h is bad)
      if (state.current.wind_speed > 20) {
        score -= (state.current.wind_speed - 20) * 2
      }

      // Humidity penalty (> 80% is bad)
      if (state.current.humidity > 80) {
        score -= (state.current.humidity - 80)
      }

      return Math.max(0, Math.min(100, score))
    },

    weatherQuality: (state) => {
      const score = state.weatherScore
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
        const response = await axios.get('/api/weather/current')
        this.current = response.data
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
