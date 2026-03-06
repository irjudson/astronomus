import { defineStore } from 'pinia'
import axios from 'axios'
import { useSettingsStore, DEFAULT_SETTINGS } from './settings'
import { useCatalogStore } from './catalog'
import { useToastStore } from './toast'

export const usePlanningStore = defineStore('planning', {
  state: () => ({
    selectedTargets: [],
    currentPlan: null,
    planName: '',
    savedPlans: [],
    loading: false,
    error: null,
    observationDate: null,
    constraints: {
      min_altitude_degrees: DEFAULT_SETTINGS.planMinAltitude,
      max_altitude_degrees: DEFAULT_SETTINGS.planMaxAltitude,
      avoid_moon: DEFAULT_SETTINGS.planAvoidMoon,
      setup_time_minutes: DEFAULT_SETTINGS.planSetupMinutes,
      object_types: [...DEFAULT_SETTINGS.planObjectTypes],
      daytime_planning: false,
    },

    // Execution state
    executionId: null,
    executionStatus: null,
    executionProgress: null,
    progressPollInterval: null,
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

        // Wishlist DSO items are preferred gap-fillers (not primary targets)
        // The planner auto-selects the best objects for the night, then fills gaps
        // preferring wishlist items when possible.
        const wishlist = useCatalogStore().wishlist
        const SOLAR_TYPES = new Set(['planet', 'moon', 'sun'])
        const dsoTargets = wishlist.filter(t => !SOLAR_TYPES.has(t.type)).map(t => t.name)
        const solarTargets = wishlist.filter(t => SOLAR_TYPES.has(t.type))

        if (dsoTargets.length > 0) {
          request.preferred_gap_fillers = dsoTargets
        }

        const response = await axios.post('/api/plan', request)
        this.currentPlan = response.data
        const date = this.observationDate || new Date().toISOString().split('T')[0]
        this.planName = `Observation Plan ${date}`

        // Fetch visibility for solar system wishlist items and attach to plan
        if (solarTargets.length > 0) {
          try {
            const solarResponse = await axios.get('/api/solar-system/objects', {
              params: { lat: location.latitude, lon: location.longitude }
            })
            const allSolar = solarResponse.data.objects || []
            const wishlistNames = new Set(solarTargets.map(t => t.name))
            const minAlt = this.constraints.min_altitude_degrees
            this.currentPlan.solar_system_targets = allSolar.filter(o =>
              wishlistNames.has(o.name) &&
              o.altitude_deg != null &&
              o.altitude_deg >= minAlt
            )
          } catch (err) {
            console.warn('Failed to fetch solar system targets for plan:', err)
            this.currentPlan.solar_system_targets = []
          }
        } else {
          this.currentPlan.solar_system_targets = []
        }
      } catch (err) {
        this.error = 'Failed to generate plan: ' + (err.response?.data?.detail || err.message)
        useToastStore().error('Failed to generate plan: ' + (err.response?.data?.detail || err.message))
        throw err
      } finally {
        this.loading = false
      }
    },

    async savePlan(name) {
      const planName = name || this.planName
      if (!this.currentPlan || !planName) return
      name = planName
      try {
        const response = await axios.post('/api/plans/', { name, plan: this.currentPlan })
        this.savedPlans = [response.data, ...this.savedPlans]
        useToastStore().success(`Plan "${planName}" saved`)
        return response.data
      } catch (err) {
        this.error = 'Failed to save plan: ' + (err.response?.data?.detail || err.message)
        useToastStore().error('Failed to save plan')
        throw err
      }
    },

    async loadSavedPlans() {
      try {
        const response = await axios.get('/api/plans/')
        this.savedPlans = response.data
      } catch (err) {
        useToastStore().error('Failed to load saved plans')
      }
    },

    async loadPlan(id) {
      try {
        const response = await axios.get(`/api/plans/${id}`)
        this.currentPlan = response.data.plan
        this.planName = response.data.name
        // Restore constraints that were active when the plan was generated
        // Backend uses min_altitude/max_altitude; frontend state uses min_altitude_degrees/max_altitude_degrees
        const c = response.data.plan?.constraints
        if (c) {
          const minAlt = c.min_altitude_degrees ?? c.min_altitude
          const maxAlt = c.max_altitude_degrees ?? c.max_altitude
          if (minAlt != null) this.constraints.min_altitude_degrees = minAlt
          if (maxAlt != null) this.constraints.max_altitude_degrees = maxAlt
          if (c.avoid_moon != null) this.constraints.avoid_moon = c.avoid_moon
          if (c.setup_time_minutes != null) this.constraints.setup_time_minutes = c.setup_time_minutes
          if (c.object_types?.length) this.constraints.object_types = c.object_types
        }
        useToastStore().success(`Loaded plan: ${response.data.name}`)
        return response.data
      } catch (err) {
        this.error = 'Failed to load plan: ' + (err.response?.data?.detail || err.message)
        useToastStore().error('Failed to load plan')
        throw err
      }
    },

    async deleteSavedPlan(id) {
      try {
        await axios.delete(`/api/plans/${id}`)
        this.savedPlans = this.savedPlans.filter(p => p.id !== id)
      } catch (err) {
        this.error = 'Failed to delete plan: ' + (err.response?.data?.detail || err.message)
        throw err
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
    },

    removeFromPlan(index) {
      if (!this.currentPlan?.scheduled_targets) return
      this.currentPlan.scheduled_targets.splice(index, 1)
      this._recalcTimes()
    },

    moveTarget(fromIndex, toIndex) {
      const ts = this.currentPlan?.scheduled_targets
      if (!ts) return
      if (toIndex < 0 || toIndex >= ts.length) return
      const [t] = ts.splice(fromIndex, 1)
      ts.splice(toIndex, 0, t)
      this._recalcTimes()
    },

    updateTargetDuration(index, minutes) {
      const ts = this.currentPlan?.scheduled_targets
      if (!ts?.[index]) return
      const mins = Math.max(5, Math.min(300, Number(minutes)))
      if (!isNaN(mins)) {
        ts[index].duration_minutes = mins
        this._recalcTimes()
      }
    },

    _recalcTimes() {
      const ts = this.currentPlan?.scheduled_targets
      const s  = this.currentPlan?.session
      if (!ts || !s) return
      let cursor = new Date(s.imaging_start)
      for (const t of ts) {
        t.start_time = cursor.toISOString()
        cursor = new Date(cursor.getTime() + t.duration_minutes * 60000)
        t.end_time = cursor.toISOString()
      }
      const totalDarkMs    = new Date(s.imaging_end) - new Date(s.imaging_start)
      const totalImagingMs = ts.reduce((sum, t) => sum + t.duration_minutes * 60000, 0)
      this.currentPlan.coverage_percent = Math.round((totalImagingMs / totalDarkMs) * 100)
      this.currentPlan.total_targets    = ts.length
    }
  }
})
