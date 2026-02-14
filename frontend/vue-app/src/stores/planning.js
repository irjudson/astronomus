import { defineStore } from 'pinia'
import axios from 'axios'

export const usePlanningStore = defineStore('planning', {
  state: () => ({
    selectedTargets: [],
    currentPlan: null,
    savedPlans: [],
    loading: false,
    error: null,

    // Planning parameters
    location: {
      latitude: 45.9183,
      longitude: -111.5433,
      elevation: 1234,
      timezone: 'America/Denver'
    },
    observationDate: null,
    constraints: {
      min_altitude: 30,
      max_altitude: 70,
      avoid_moon: true,
      setup_time_minutes: 30
    }
  }),

  getters: {
    hasTargets: (state) => state.selectedTargets.length > 0,
    targetCount: (state) => state.selectedTargets.length
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
        const response = await axios.post('/api/plan', {
          targets: this.selectedTargets.map(t => t.id),
          location: this.location,
          date: this.observationDate || new Date().toISOString().split('T')[0],
          constraints: this.constraints
        })

        this.currentPlan = response.data
      } catch (err) {
        this.error = 'Failed to generate plan: ' + err.message
        console.error('Plan generation error:', err)
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
