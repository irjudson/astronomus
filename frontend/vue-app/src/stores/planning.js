import { defineStore } from 'pinia'
import axios from 'axios'

export const usePlanningStore = defineStore('planning', {
  state: () => ({
    selectedTargets: [],
    currentPlan: null,
    savedPlans: [],
    loading: false,
    error: null,
    observationDate: null,
    constraints: {
      min_altitude_degrees: 30,
      max_altitude_degrees: 70,
      avoid_moon: true,
      setup_time_minutes: 30,
      object_types: ['galaxy', 'nebula', 'cluster', 'planetary_nebula'],
      daytime_planning: false
    }
  }),

  getters: {
    hasTargets: (state) => state.selectedTargets.length > 0,
    targetCount: (state) => state.selectedTargets.length,

    // Get location from user settings
    location: () => {
      const settings = localStorage.getItem('astronomus_settings')
      if (settings) {
        const parsed = JSON.parse(settings)
        return {
          name: parsed.locationName || 'My Observatory',
          latitude: parsed.latitude || 40.7128,
          longitude: parsed.longitude || -74.0060,
          elevation: 0,
          timezone: parsed.timezone || 'America/New_York'
        }
      }
      return {
        name: 'Default Location',
        latitude: 40.7128,
        longitude: -74.0060,
        elevation: 0,
        timezone: 'America/New_York'
      }
    }
  },

  actions: {
    addTarget(target) {
      const exists = this.selectedTargets.some(t => t.id === target.id)
      if (!exists) {
        this.selectedTargets.push(target)
      }
    },

    removeTarget(targetId) {
      this.selectedTargets = this.selectedTargets.filter(t => t.id !== targetId)
    },

    clearTargets() {
      this.selectedTargets = []
    },

    async generatePlan() {
      this.loading = true
      this.error = null

      try {
        // Get location from settings
        const location = this.location

        // Build request matching backend PlanRequest model
        const request = {
          location: {
            name: location.name,
            latitude: location.latitude,
            longitude: location.longitude,
            elevation: location.elevation || 0,
            timezone: location.timezone
          },
          observing_date: this.observationDate || new Date().toISOString().split('T')[0],
          constraints: {
            min_altitude_degrees: this.constraints.min_altitude_degrees,
            max_altitude_degrees: this.constraints.max_altitude_degrees,
            avoid_moon: this.constraints.avoid_moon,
            setup_time_minutes: this.constraints.setup_time_minutes,
            object_types: this.constraints.object_types,
            daytime_planning: this.constraints.daytime_planning
          }
        }

        // If we have selected targets (wishlist), add them as custom_targets
        if (this.selectedTargets.length > 0) {
          request.custom_targets = this.selectedTargets.map(t => t.catalog_id || t.id)
        }

        const response = await axios.post('/api/plan', request)
        this.currentPlan = response.data
      } catch (err) {
        this.error = 'Failed to generate plan: ' + (err.response?.data?.detail || err.message)
        console.error('Plan generation error:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    async savePlan() {
      if (!this.currentPlan) return

      try {
        const response = await axios.post('/api/plans', this.currentPlan)
        this.savedPlans.push(response.data)
      } catch (err) {
        this.error = 'Failed to save plan: ' + err.message
      }
    },

    async loadSavedPlans() {
      try {
        const response = await axios.get('/api/plans')
        this.savedPlans = response.data
      } catch (err) {
        console.error('Load plans error:', err)
      }
    },

    async exportPlan(format = 'seestar_alp') {
      if (!this.currentPlan) return null

      try {
        const response = await axios.get(`/api/plans/${this.currentPlan.id}/export/${format}`)
        return response.data
      } catch (err) {
        this.error = 'Failed to export plan: ' + err.message
        return null
      }
    }
  }
})
