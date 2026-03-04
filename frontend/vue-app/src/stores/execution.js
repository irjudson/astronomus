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
      mode: 'deep-sky',
      framesCaptured: 0,
      currentExposure: 0,
      totalExposure: 0,
      selectedPlanet: null,
      availablePlanets: []
    },

    // Recording state
    recording: { active: false },

    // Polar alignment state
    polarAlignment: { active: false, status: 'idle', errorArcmin: null },

    // Compass calibration state
    compass: { status: 'idle', heading: null },

    // Object tracking state
    tracking: { active: false, objectType: null, objectId: null },

    // Balance / leveling
    balance: { x: 0, y: 0, z: 0, angle: 0 },

    // Annotations
    annotationsEnabled: false,

    // Hardware state
    hardware: {
      sensorTemp: null,
      dewHeaterStatus: 'Off',
      dewHeaterPower: 50,
      trackingStatus: 'Inactive',
      mountMode: null, // 'equatorial' or 'altaz'
      firmwareVersion: null,
      model: null
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
        // Backend expects 'host' parameter, not 'ip'
        const response = await axios.post('/api/telescope/connect', { host: ip })

        if (response.data.status === 'connected' || response.data.connected) {
          this.connected = true
          this.telescopeIp = ip
          this.startPositionPolling()

          // Fetch initial hardware status
          this.fetchSystemInfo()
          this.fetchDewHeaterStatus()

          this.addMessage('Telescope connected successfully')
        } else {
          this.error = response.data.message || 'Connection failed'
          this.connected = false
        }
      } catch (err) {
        this.error = 'Failed to connect: ' + (err.response?.data?.detail || err.message)
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

        // Parse telescope status response
        if (response.data) {
          // Convert RA hours to degrees (15 degrees per hour)
          const raDeg = (response.data.current_ra_hours || 0) * 15
          const decDeg = response.data.current_dec_degrees || 0

          this.updatePosition({
            ra: raDeg,
            dec: decDeg,
            alt: 0, // Not provided by API
            az: 0   // Not provided by API
          })

          // Update tracking status from state field (not just is_tracking boolean)
          if (response.data.state) {
            const state = response.data.state.toLowerCase()
            if (state === 'parked' || state === 'parking') {
              this.hardware.trackingStatus = 'Parked'
            } else if (state === 'tracking' || response.data.is_tracking) {
              this.hardware.trackingStatus = 'Active'
            } else {
              this.hardware.trackingStatus = 'Inactive'
            }
          } else if (response.data.is_tracking !== undefined) {
            // Fallback to is_tracking if state not available
            this.hardware.trackingStatus = response.data.is_tracking ? 'Active' : 'Inactive'
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

    async stopMotion() {
      try {
        await axios.post('/api/telescope/stop-slew')
        this.addMessage('Motion stopped')
      } catch (err) {
        this.error = 'Failed to stop motion: ' + err.message
        console.error('Stop motion error:', err)
        throw err
      }
    },

    async autoFocus() {
      try {
        await axios.post('/api/telescope/features/imaging/autofocus')
        this.addMessage('Auto focus started')
      } catch (err) {
        this.error = 'Failed to start auto focus: ' + err.message
        console.error('Auto focus error:', err)
        throw err
      }
    },

    async moveDirection(direction, speed) {
      if (!this.connected) {
        this.error = 'Telescope not connected'
        throw new Error('Telescope not connected')
      }

      try {
        // Convert speed string to numeric multiplier
        const speedMap = {
          slow: 0.5,
          fast: 2.0
        }

        // API expects 'action' (up/down/left/right) and numeric 'speed'
        await axios.post('/api/telescope/move', {
          action: direction,
          speed: speedMap[speed] || 1.0
        })

        this.addMessage(`Moving ${direction} (${speed})`)
      } catch (err) {
        this.error = 'Failed to move telescope: ' + err.message
        console.error('Move error:', err)
        throw err
      }
    },

    async startImaging(params) {
      this.imaging.active = true
      this.imaging.framesCaptured = 0
      this.imaging.currentExposure = params.exposure || 10
      this.addMessage(`Started live preview`)

      try {
        // Start preview/live view mode (not stacking)
        await axios.post('/api/telescope/start-preview', {
          mode: 'star',  // Star mode for deep sky imaging
          brightness: 50
        })
      } catch (err) {
        this.error = 'Failed to start preview: ' + err.message
        this.imaging.active = false
        console.error('Imaging error:', err)
        throw err
      }
    },

    async stopImaging() {
      try {
        // Stop preview/live view
        await axios.post('/api/telescope/stop-imaging')
        this.imaging.active = false
        this.addMessage('Preview stopped')
      } catch (err) {
        this.error = 'Failed to stop preview: ' + err.message
        console.error('Stop imaging error:', err)
        throw err
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

    async fetchDewHeaterStatus() {
      if (!this.connected) return

      try {
        const response = await axios.get('/api/telescope/features/hardware/dew-heater/status')
        if (response.data) {
          this.hardware.dewHeaterStatus = response.data.enabled ? 'On' : 'Off'
          this.hardware.dewHeaterPower = response.data.power || 0
        }
      } catch (err) {
        console.error('Failed to fetch dew heater status:', err)
      }
    },

    async setDewHeater(enabled, power = 50) {
      if (!this.connected) {
        this.error = 'Telescope not connected'
        return
      }

      try {
        await axios.post('/api/telescope/features/hardware/dew-heater', {
          enabled,
          power
        })

        this.hardware.dewHeaterStatus = enabled ? 'On' : 'Off'
        this.hardware.dewHeaterPower = power
        this.addMessage(`Dew heater ${enabled ? 'on' : 'off'}${enabled ? ` (${power}%)` : ''}`)
      } catch (err) {
        this.error = 'Failed to set dew heater: ' + err.message
        console.error('Dew heater error:', err)
      }
    },

    async toggleDewHeater() {
      const newState = this.hardware.dewHeaterStatus !== 'On'
      await this.setDewHeater(newState, this.hardware.dewHeaterPower || 50)
    },

    async startRecording(filename) {
      try {
        await axios.post("/api/telescope/recording/start", { filename })
        this.recording.active = true
        this.addMessage(`Recording started${filename ? ": " + filename : ""}`)
      } catch (err) {
        this.error = "Failed to start recording: " + (err.response?.data?.detail || err.message)
      }
    },

    async stopRecording() {
      try {
        await axios.post("/api/telescope/recording/stop")
        this.recording.active = false
        this.addMessage("Recording stopped")
      } catch (err) {
        this.error = "Failed to stop recording: " + (err.response?.data?.detail || err.message)
      }
    },

    async scanPlanets() {
      try {
        const response = await axios.post("/api/telescope/imaging/planet/scan")
        this.imaging.availablePlanets = response.data.planets || []
        this.addMessage(`Found ${this.imaging.availablePlanets.length} planets`)
      } catch (err) {
        this.error = "Failed to scan planets: " + (err.response?.data?.detail || err.message)
      }
    },

    async startPlanetaryImaging(params) {
      try {
        await axios.post("/api/telescope/imaging/planet/start", {
          planet_name: params.planet, exposure: params.exposure || 10, gain: params.gain || 80
        })
        this.imaging.active = true
        this.imaging.mode = "planetary"
        this.imaging.selectedPlanet = params.planet
        this.addMessage(`Planetary imaging started: ${params.planet}`)
      } catch (err) {
        this.error = "Failed to start planetary imaging: " + (err.response?.data?.detail || err.message)
      }
    },

    async stopPlanetaryImaging() {
      try {
        await axios.post("/api/telescope/imaging/planet/stop")
        this.imaging.active = false
        this.addMessage("Planetary imaging stopped")
      } catch (err) {
        this.error = "Failed to stop planetary imaging: " + (err.response?.data?.detail || err.message)
      }
    },

    async startPolarAlign() {
      try {
        await axios.post("/api/telescope/polar-align/start")
        this.polarAlignment.active = true
        this.polarAlignment.status = "active"
        this.addMessage("Polar alignment started")
      } catch (err) {
        this.error = "Failed to start polar alignment: " + (err.response?.data?.detail || err.message)
      }
    },

    async pausePolarAlign() {
      try {
        await axios.post("/api/telescope/polar-align/pause")
        this.polarAlignment.status = "paused"
        this.addMessage("Polar alignment paused")
      } catch (err) {
        this.error = "Failed to pause polar alignment: " + (err.response?.data?.detail || err.message)
      }
    },

    async stopPolarAlign() {
      try {
        await axios.post("/api/telescope/polar-align/stop")
        this.polarAlignment.active = false
        this.polarAlignment.status = "idle"
        this.addMessage("Polar alignment stopped")
      } catch (err) {
        this.error = "Failed to stop polar alignment: " + (err.response?.data?.detail || err.message)
      }
    },

    async fetchPolarAlignStatus() {
      if (!this.connected) return
      try {
        const response = await axios.get('/api/telescope/features/calibration/polar-alignment')
        const d = response.data || {}
        const state = d.state
        if (state) {
          const stateMap = { working: 'active', complete: 'complete', fail: 'idle', cancel: 'idle', idle: 'idle' }
          this.polarAlignment.status = stateMap[state] ?? this.polarAlignment.status
          // Update errorArcmin only when firmware reports a completed measurement
          if (state === 'complete' && d.x_arcsec != null) {
            this.polarAlignment.errorArcmin = Math.abs(d.x_arcsec) / 60
          } else if (state === 'idle' || state === 'fail' || state === 'cancel') {
            this.polarAlignment.errorArcmin = null
          }
          // During 'working', preserve the last known errorArcmin value
        }
      } catch { /* silent */ }
    },

    async startCompassCalibration() {
      try {
        await axios.post('/api/telescope/features/calibration/compass/start')
        this.compass.status = 'calibrating'
      } catch (err) {
        this.error = 'Failed to start compass calibration: ' + (err.response?.data?.detail || err.message)
      }
    },

    async stopCompassCalibration() {
      try {
        await axios.post('/api/telescope/features/calibration/compass/stop')
        this.compass.status = 'idle'
      } catch (err) {
        this.error = 'Failed to stop compass calibration: ' + (err.response?.data?.detail || err.message)
      }
    },

    async fetchCompassState() {
      if (!this.connected) return
      try {
        const response = await axios.get('/api/telescope/features/calibration/compass/state')
        const d = response.data || {}
        // heading field name varies by firmware: 'direction' (confirmed), 'heading', 'angle', 'yaw'
        const heading = d.direction ?? d.heading ?? d.angle ?? d.yaw ?? null
        if (heading !== null) this.compass.heading = Math.round(heading)
      } catch { /* silent */ }
    },

    async startTracking(type, id) {
      try {
        await axios.post("/api/telescope/tracking/start", { object_type: type, object_id: id })
        this.tracking.active = true
        this.tracking.objectType = type
        this.tracking.objectId = id
        this.addMessage(`Started tracking ${type}: ${id}`)
      } catch (err) {
        this.error = "Failed to start tracking: " + (err.response?.data?.detail || err.message)
      }
    },

    async stopTracking() {
      try {
        await axios.post("/api/telescope/tracking/stop")
        this.tracking.active = false
        this.tracking.objectType = null
        this.tracking.objectId = null
        this.addMessage("Stopped tracking")
      } catch (err) {
        this.error = "Failed to stop tracking: " + (err.response?.data?.detail || err.message)
      }
    },

    async toggleAnnotations(enabled) {
      try {
        await axios.post("/api/telescope/annotation/toggle", { enabled })
        this.annotationsEnabled = enabled
        this.addMessage(`Annotations ${enabled ? "enabled" : "disabled"}`)
      } catch (err) {
        this.error = "Failed to toggle annotations: " + (err.response?.data?.detail || err.message)
      }
    },

    async fetchSystemInfo() {
      if (!this.connected) return

      try {
        const response = await axios.get('/api/telescope/features/system/info')
        if (response.data) {
          this.hardware.sensorTemp = response.data.temperature || null
          this.hardware.firmwareVersion = response.data.firmware || null
          this.hardware.model = response.data.model || null
        }
      } catch (err) {
        console.error('Failed to fetch system info:', err)
      }
    },

    async startLeveling() {
      await axios.post('/api/telescope/features/calibration/balance/start')
    },

    async fetchBalance() {
      if (!this.connected) return
      try {
        const response = await axios.get('/api/telescope/features/calibration/balance')
        this.balance = { ...this.balance, ...response.data }
      } catch { /* silent — called frequently, don't spam errors */ }
    },

    async calibrateGsensor() {
      await axios.post('/api/telescope/features/calibration/gsensor/start')
    },

    async startLandscapeImaging(brightness = 50) {
      try {
        await axios.post('/api/telescope/start-preview', { mode: 'scenery', brightness })
        this.imaging.active = true
        this.imaging.mode = 'landscape'
        this.addMessage('Landscape view started')
      } catch (err) {
        this.error = 'Failed to start landscape view: ' + (err.response?.data?.detail || err.message)
        throw err
      }
    },

    async stopLandscapeImaging() {
      try {
        await axios.post('/api/telescope/stop-imaging')
        this.imaging.active = false
        this.addMessage('Landscape view stopped')
      } catch (err) {
        this.error = 'Failed to stop landscape view: ' + (err.response?.data?.detail || err.message)
        throw err
      }
    }
  }
})
