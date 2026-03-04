import { defineStore } from 'pinia'
import axios from 'axios'
import { useSettingsStore } from './settings'

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
    },

    // Execution state
    executionId: null,
    executionStatus: null,
    executionProgress: null,
    progressPollInterval: null
  }),

  getters: {
    hasTargets: (state) => state.selectedTargets.length > 0,
    targetCount: (state) => state.selectedTargets.length,

    // Get location from user settings store
    location: () => {
      const s = useSettingsStore().settings
      return {
        name: s.locationName || 'My Observatory',
        latitude: s.latitude || 40.7128,
        longitude: s.longitude || -74.0060,
        elevation: s.elevation || 0,
        timezone: s.timezone || 'America/New_York'
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
    },

    async executePlan(parkWhenDone = true) {
      if (!this.currentPlan || !this.currentPlan.scheduled_targets) {
        this.error = 'No plan to execute'
        return
      }

      this.loading = true
      this.error = null

      try {
        const response = await axios.post('/api/telescope/execute', {
          scheduled_targets: this.currentPlan.scheduled_targets,
          park_when_done: parkWhenDone
        })

        this.executionId = response.data.execution_id
        this.executionStatus = response.data.status

        // Start polling for progress
        this.startProgressPolling()
      } catch (err) {
        this.error = 'Failed to execute plan: ' + (err.response?.data?.detail || err.message)
        console.error('Execution error:', err)
        throw err
      } finally {
        this.loading = false
      }
    },

    startProgressPolling() {
      if (this.progressPollInterval) {
        clearInterval(this.progressPollInterval)
      }

      this.progressPollInterval = setInterval(async () => {
        if (!this.executionId) {
          this.stopProgressPolling()
          return
        }

        try {
          const response = await axios.get('/api/telescope/progress', {
            params: { execution_id: this.executionId }
          })

          this.executionProgress = response.data

          // Stop polling if execution completed or failed
          if (response.data.state === 'completed' || response.data.state === 'failed') {
            this.stopProgressPolling()
            this.executionStatus = response.data.state
          }
        } catch (err) {
          console.error('Progress poll error:', err)
        }
      }, 2000)
    },

    stopProgressPolling() {
      if (this.progressPollInterval) {
        clearInterval(this.progressPollInterval)
        this.progressPollInterval = null
      }
    },

    async abortExecution() {
      if (!this.executionId) return

      try {
        await axios.post('/api/telescope/abort')
        this.executionStatus = 'aborted'
        this.stopProgressPolling()
      } catch (err) {
        this.error = 'Failed to abort execution: ' + err.message
        console.error('Abort error:', err)
      }
    }
  }
})
