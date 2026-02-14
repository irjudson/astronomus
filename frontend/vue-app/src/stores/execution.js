import { defineStore } from 'pinia'
import axios from 'axios'

export const useExecutionStore = defineStore('execution', {
  state: () => ({
    // Connection state
    connected: false,
    telescopeIp: null,
    loading: false,
    error: null,

    // Telescope position
    position: {
      ra: 0,
      dec: 0,
      alt: 0,
      az: 0
    },

    // Imaging state
    imaging: {
      active: false,
      framesCaptured: 0,
      currentExposure: 0,
      totalExposure: 0
    },

    // Hardware state
    hardware: {
      sensorTemp: null,
      dewHeaterStatus: 'Off',
      trackingStatus: 'Inactive'
    },

    // Messages
    messages: [],

    // Plan execution
    currentPlan: null,
    currentTargetIndex: 0,
    executionStatus: 'idle', // idle, running, paused, completed

    // Position polling
    positionInterval: null
  }),

  getters: {
    currentTarget: (state) => {
      if (!state.currentPlan || !state.currentPlan.targets) return null
      return state.currentPlan.targets[state.currentTargetIndex]
    },

    nextTarget: (state) => {
      if (!state.currentPlan || !state.currentPlan.targets) return null
      const nextIndex = state.currentTargetIndex + 1
      if (nextIndex >= state.currentPlan.targets.length) return null
      return state.currentPlan.targets[nextIndex]
    },

    progressPercent: (state) => {
      if (!state.currentPlan || !state.currentPlan.targets) return 0
      const total = state.currentPlan.targets.length
      return Math.round((state.currentTargetIndex / total) * 100)
    },

    planExecuting: (state) => {
      return state.executionStatus === 'running'
    }
  },

  actions: {
    async connectTelescope(ip) {
      this.loading = true
      this.error = null

      try {
        const response = await axios.post('/api/telescope/connect', { ip })

        if (response.data.status === 'connected') {
          this.connected = true
          this.telescopeIp = ip
          this.startPositionPolling()
          this.addMessage('Telescope connected successfully')
        }
      } catch (err) {
        this.error = 'Failed to connect: ' + err.message
        this.connected = false
        console.error('Connection error:', err)
      } finally {
        this.loading = false
      }
    },

    async disconnectTelescope() {
      try {
        await axios.post('/api/telescope/disconnect')
        this.connected = false
        this.telescopeIp = null
        this.stopPositionPolling()
        this.addMessage('Telescope disconnected')
      } catch (err) {
        this.error = 'Failed to disconnect: ' + err.message
        console.error('Disconnect error:', err)
      }
    },

    updatePosition(positionData) {
      this.position = {
        ra: positionData.ra || this.position.ra,
        dec: positionData.dec || this.position.dec,
        alt: positionData.alt || this.position.alt,
        az: positionData.az || this.position.az
      }
    },

    async fetchPosition() {
      if (!this.connected) return

      try {
        const response = await axios.get('/api/telescope/status')
        this.updatePosition(response.data.position)

        if (response.data.hardware) {
          this.hardware = {
            ...this.hardware,
            ...response.data.hardware
          }
        }
      } catch (err) {
        console.error('Failed to fetch position:', err)
      }
    },

    startPositionPolling() {
      if (this.positionInterval) return

      this.positionInterval = setInterval(() => {
        this.fetchPosition()
      }, 2000) // Poll every 2 seconds
    },

    stopPositionPolling() {
      if (this.positionInterval) {
        clearInterval(this.positionInterval)
        this.positionInterval = null
      }
    },

    async slewToTarget(target) {
      if (!this.connected) {
        this.error = 'Telescope not connected'
        return false
      }

      try {
        await axios.post('/api/telescope/slew', {
          ra: target.ra,
          dec: target.dec,
          name: target.name
        })

        this.addMessage(`Slewing to ${target.name}`)
        return true
      } catch (err) {
        this.error = 'Failed to slew: ' + err.message
        console.error('Slew error:', err)
        return false
      }
    },

    async parkTelescope() {
      try {
        await axios.post('/api/telescope/park')
        this.hardware.trackingStatus = 'Parked'
        this.addMessage('Telescope parked')
      } catch (err) {
        this.error = 'Failed to park: ' + err.message
        console.error('Park error:', err)
      }
    },

    async unparkTelescope() {
      try {
        await axios.post('/api/telescope/unpark')
        this.hardware.trackingStatus = 'Active'
        this.addMessage('Telescope unparked')
      } catch (err) {
        this.error = 'Failed to unpark: ' + err.message
        console.error('Unpark error:', err)
      }
    },

    async startImaging(params) {
      this.imaging.active = true
      this.imaging.framesCaptured = 0
      this.imaging.currentExposure = params.exposure || 10
      this.addMessage(`Started imaging: ${params.frames} frames @ ${params.exposure}s`)

      try {
        await axios.post('/api/imaging/start', params)
      } catch (err) {
        this.error = 'Failed to start imaging: ' + err.message
        this.imaging.active = false
        console.error('Imaging error:', err)
      }
    },

    async stopImaging() {
      try {
        await axios.post('/api/imaging/stop')
        this.imaging.active = false
        this.addMessage('Imaging stopped')
      } catch (err) {
        this.error = 'Failed to stop imaging: ' + err.message
        console.error('Stop imaging error:', err)
      }
    },

    updateImagingProgress(data) {
      this.imaging.framesCaptured = data.framesCaptured || this.imaging.framesCaptured
      this.imaging.totalExposure = data.totalExposure || this.imaging.totalExposure
    },

    async executePlan(plan) {
      if (!this.connected) {
        this.error = 'Telescope not connected'
        return
      }

      this.currentPlan = plan
      this.currentTargetIndex = 0
      this.executionStatus = 'running'
      this.addMessage(`Starting plan execution: ${plan.name}`)

      await this.executeNextTarget()
    },

    async executeNextTarget() {
      const target = this.currentTarget

      if (!target) {
        this.executionStatus = 'completed'
        this.addMessage('Plan execution completed')
        return
      }

      // Slew to target
      const slewed = await this.slewToTarget(target)
      if (!slewed) {
        this.pauseExecution()
        return
      }

      // Wait for slew to complete (simplified - in reality would poll until settled)
      await new Promise(resolve => setTimeout(resolve, 3000))

      // Start imaging
      await this.startImaging({
        exposure: target.exposure || 10,
        frames: target.frames || 50,
        gain: target.gain || 80
      })

      // Wait for imaging to complete (simplified)
      await new Promise(resolve => setTimeout(resolve, 5000))

      // Move to next target
      if (this.executionStatus === 'running') {
        this.currentTargetIndex++
        await this.executeNextTarget()
      }
    },

    pauseExecution() {
      this.executionStatus = 'paused'
      this.stopImaging()
      this.addMessage('Plan execution paused')
    },

    pausePlan() {
      this.pauseExecution()
    },

    resumeExecution() {
      this.executionStatus = 'running'
      this.addMessage('Plan execution resumed')
      this.executeNextTarget()
    },

    cancelExecution() {
      this.executionStatus = 'idle'
      this.currentPlan = null
      this.currentTargetIndex = 0
      this.stopImaging()
      this.addMessage('Plan execution cancelled')
    },

    stopPlan() {
      this.cancelExecution()
    },

    addMessage(text) {
      this.messages.push({
        id: Date.now(),
        text,
        timestamp: new Date()
      })

      // Keep only last 100 messages
      if (this.messages.length > 100) {
        this.messages = this.messages.slice(-100)
      }
    },

    clearMessages() {
      this.messages = []
    },

    toggleDewHeater() {
      this.hardware.dewHeaterStatus =
        this.hardware.dewHeaterStatus === 'Off' ? 'On' : 'Off'
      this.addMessage(`Dew heater ${this.hardware.dewHeaterStatus.toLowerCase()}`)
    }
  }
})
