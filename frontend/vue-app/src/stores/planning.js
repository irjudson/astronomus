import { defineStore } from 'pinia'
import axios from 'axios'
import { useSettingsStore, savedSettings, DEFAULT_SETTINGS } from './settings'
import { useCatalogStore } from './catalog'

export const usePlanningStore = defineStore('planning', {
  state: () => {
    const s = { ...DEFAULT_SETTINGS, ...savedSettings() }
    return {
      selectedTargets: [],
      currentPlan: null,
      savedPlans: [],
      loading: false,
      error: null,
      observationDate: null,
      constraints: {
        min_altitude_degrees: s.planMinAltitude,
        max_altitude_degrees: s.planMaxAltitude,
        avoid_moon: s.planAvoidMoon,
        setup_time_minutes: s.planSetupMinutes,
        object_types: s.planObjectTypes,
        daytime_planning: false,
      },

      // Execution state
      executionId: null,
      executionStatus: null,
      executionProgress: null,
      progressPollInterval: null,
    }
  },

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

    initFromSettings(s) {
      this.constraints.min_altitude_degrees = s.planMinAltitude ?? this.constraints.min_altitude_degrees
      this.constraints.max_altitude_degrees = s.planMaxAltitude ?? this.constraints.max_altitude_degrees
      this.constraints.avoid_moon = s.planAvoidMoon ?? this.constraints.avoid_moon
      this.constraints.setup_time_minutes = s.planSetupMinutes ?? this.constraints.setup_time_minutes
      if (s.planObjectTypes?.length) this.constraints.object_types = s.planObjectTypes
    },

    async saveConstraints() {
      await useSettingsStore().save({
        planMinAltitude: this.constraints.min_altitude_degrees,
        planMaxAltitude: this.constraints.max_altitude_degrees,
        planAvoidMoon: this.constraints.avoid_moon,
        planSetupMinutes: this.constraints.setup_time_minutes,
        planObjectTypes: this.constraints.object_types,
      })
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

        // Use DSO items from the persistent wishlist as custom_targets
        const wishlist = useCatalogStore().wishlist
        const dsoTargets = wishlist
          .filter(t => t.type !== 'planet' && t.type !== 'moon' && t.type !== 'sun')
          .map(t => t.name)
        if (dsoTargets.length > 0) {
          request.custom_targets = dsoTargets
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
