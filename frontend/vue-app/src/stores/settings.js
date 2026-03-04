import { defineStore } from 'pinia'
import axios from 'axios'

const DEFAULT_SETTINGS = {
  locationName: '',
  latitude: 40.7128,
  longitude: -74.0060,
  elevation: 0,
  timezone: 'America/New_York',
  temperatureUnit: 'F',
  distanceUnit: 'mi',
  showThumbnails: true,
  autoRefresh: false,
}

const LS_KEY = 'astronomus_settings'

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    settings: { ...DEFAULT_SETTINGS },
    loaded: false,
  }),

  actions: {
    async load() {
      if (this.loaded) return
      try {
        const { data } = await axios.get('/api/settings/user')
        this.settings = { ...DEFAULT_SETTINGS, ...data }
        localStorage.setItem(LS_KEY, JSON.stringify(this.settings))
      } catch {
        // Fall back to localStorage cache (works offline or before first save)
        try {
          const saved = localStorage.getItem(LS_KEY)
          if (saved) this.settings = { ...DEFAULT_SETTINGS, ...JSON.parse(saved) }
        } catch { /* use defaults */ }
      }
      this.loaded = true
    },

    async save(newSettings) {
      this.settings = { ...this.settings, ...newSettings }
      localStorage.setItem(LS_KEY, JSON.stringify(this.settings))
      await axios.put('/api/settings/user', this.settings)
    },
  },
})
