import { defineStore } from 'pinia'
import axios from 'axios'
import { useToastStore } from './toast'

export const DEFAULT_SETTINGS = {
  // Location
  locationName: '',
  latitude: 40.7128,
  longitude: -74.0060,
  elevation: 0,
  timezone: 'America/New_York',
  // UI preferences
  temperatureUnit: 'F',
  distanceUnit: 'mi',
  showThumbnails: true,
  autoRefresh: false,
  // Telescope
  telescopeHost: '',
  telescopePort: 4700,
  // Planning constraints
  planMinAltitude: 30,
  planMaxAltitude: 70,
  planAvoidMoon: true,
  planSetupMinutes: 30,
  planObjectTypes: ['galaxy', 'nebula', 'cluster', 'planetary_nebula'],
  // Catalog filter defaults
  catalogSortBy: 'name',
  catalogVisibleNow: false,
  catalogUseScoring: false,
  // Imaging
  imagingMode: 'deep-sky',
  annotationsEnabled: false,
}

const LS_KEY = 'astronomus_settings'

/** Synchronous read of persisted settings from localStorage cache. */
export function savedSettings() {
  try { return JSON.parse(localStorage.getItem(LS_KEY) || '{}') } catch { return {} }
}

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
      try {
        await axios.put('/api/settings/user', this.settings)
        useToastStore().success('Settings saved')
      } catch (err) {
        useToastStore().error('Failed to save settings')
        throw err
      }
    },
  },
})
