import { defineStore } from 'pinia'
import axios from 'axios'
import { useSettingsStore, DEFAULT_SETTINGS } from './settings'

export const useExecutionStore = defineStore('execution', {
  state: () => ({
    // Connection state
    connected: false,
    telescopeIp: DEFAULT_SETTINGS.telescopeHost || null,
    loading: false,
    error: null,

    // Telescope position
    position: {
      ra: null,
      dec: null,
      alt: null,
      az: null
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
    annotationsEnabled: DEFAULT_SETTINGS.annotationsEnabled,

    // Hardware state
    hardware: {
      sensorTemp: null,
      batteryTemp: null,
      batteryCapacity: null,
      chargerStatus: null,
      isOvertemp: false,
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
    scheduledTargets: [],       // original ScheduledTarget list for backend submission
    currentTargetIndex: 0,
    resumeOffset: 0,            // index offset when resuming a paused plan
    executionStatus: 'idle',    // idle, running, paused, completed

    // Position polling
    positionInterval: null,
    progressPollInterval: null, // for polling /api/telescope/progress
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
    initFromSettings(s) {
      if (s.telescopeHost) this.telescopeIp = s.telescopeHost
      this.annotationsEnabled = s.annotationsEnabled ?? this.annotationsEnabled
    },

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

          // Persist telescope host so it's pre-filled next session
          useSettingsStore().save({ telescopeHost: ip }).catch(() => {})

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
        ra: positionData.ra ?? this.position.ra,
        dec: positionData.dec ?? this.position.dec,
        alt: positionData.alt ?? this.position.alt,
        az: positionData.az ?? this.position.az,
      }
    },

    async fetchPosition() {
      if (!this.connected) return

      try {
        const response = await axios.get('/api/telescope/status')

        if (response.data) {
          const d = response.data

          // RA/Dec: convert hours → degrees
          const raDeg = d.current_ra_hours != null ? d.current_ra_hours * 15 : null
          const decDeg = d.current_dec_degrees ?? null

          this.updatePosition({
            ra: raDeg,
            dec: decDeg,
            alt: d.alt_degrees ?? null,
            az: d.az_degrees ?? null,
          })

          // Tracking status
          if (d.state) {
            const state = d.state.toLowerCase()
            if (state === 'parked' || state === 'parking') {
              this.hardware.trackingStatus = 'Parked'
            } else if (state === 'tracking' || d.is_tracking) {
              this.hardware.trackingStatus = 'Active'
            } else {
              this.hardware.trackingStatus = 'Inactive'
            }
          } else if (d.is_tracking !== undefined) {
            this.hardware.trackingStatus = d.is_tracking ? 'Active' : 'Inactive'
          }

          // Mount mode, compass heading, level angle
          if (d.mount_mode) this.hardware.mountMode = d.mount_mode
          if (d.compass_heading != null) this.compass.heading = d.compass_heading
          if (d.level_angle != null) this.balance.angle = d.level_angle
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

    async moveDirection(direction, { percent, dur_sec } = {}) {
      if (!this.connected) {
        this.error = 'Telescope not connected'
        throw new Error('Telescope not connected')
      }

      try {
        await axios.post('/api/telescope/move', {
          action: direction,
          ...(percent != null && { percent }),
          ...(dur_sec != null && { dur_sec }),
        })
      } catch (err) {
        this.error = 'Failed to move telescope: ' + err.message
        console.error('Move error:', err)
        throw err
      }
    },

    async moveJoystick(angle, percent, dur_sec = 2) {
      if (!this.connected) throw new Error('Telescope not connected')
      try {
        await axios.post('/api/telescope/move-joystick', { angle, percent, dur_sec })
      } catch (err) {
        console.error('Joystick move error:', err)
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

    setPlan(plan, scheduledTargets = []) {
      this.currentPlan = plan
      this.scheduledTargets = scheduledTargets
      this.currentTargetIndex = 0
      this.resumeOffset = 0
      this.executionStatus = 'idle'
      this.addMessage(`Plan loaded: ${plan.name} (${plan.targets.length} targets)`)
    },

    async executePlan() {
      if (!this.currentPlan || !this.connected) return
      this.currentTargetIndex = 0
      this.resumeOffset = 0
      this.executionStatus = 'running'
      this.addMessage(`Starting plan execution: ${this.currentPlan.name}`)
      try {
        await axios.post('/api/telescope/execute', {
          scheduled_targets: this.scheduledTargets,
          park_when_done: true,
        })
        this.startProgressPolling()
      } catch (err) {
        this.executionStatus = 'idle'
        this.error = 'Failed to start execution: ' + (err.response?.data?.detail || err.message)
        this.addMessage('Plan execution failed to start')
      }
    },

    startProgressPolling() {
      if (this.progressPollInterval) clearInterval(this.progressPollInterval)
      this.progressPollInterval = setInterval(async () => {
        try {
          const resp = await axios.get('/api/telescope/progress')
          const p = resp.data
          if (!p || p.state === 'idle') {
            this.stopProgressPolling()
            return
          }
          // Map backend index (0-based within current execution) back to plan index
          const backendIndex = p.current_target_index ?? -1
          if (backendIndex >= 0) {
            this.currentTargetIndex = this.resumeOffset + backendIndex
          }
          if (p.state === 'completed') {
            this.executionStatus = 'completed'
            this.addMessage('Plan execution completed')
            this.stopProgressPolling()
          } else if (p.state === 'aborted' || p.state === 'error') {
            if (p.state === 'error') this.addMessage('Plan execution encountered an error')
            this.executionStatus = 'idle'
            this.stopProgressPolling()
          }
          // Add phase messages as they change
          if (p.current_phase && p.current_target_name) {
            // Avoid flooding messages; the phase appears in the progress display
          }
        } catch (e) { /* silent — polling failures shouldn't break UI */ }
      }, 3000)
    },

    stopProgressPolling() {
      if (this.progressPollInterval) {
        clearInterval(this.progressPollInterval)
        this.progressPollInterval = null
      }
    },

    async pausePlan() {
      // No server-side pause endpoint; abort execution and keep plan staged so
      // the user can resume from the current target.
      try {
        await axios.post('/api/telescope/abort')
      } catch (e) { /* best-effort */ }
      this.stopProgressPolling()
      this.executionStatus = 'paused'
      this.addMessage(`Plan paused at target ${this.currentTargetIndex + 1} — click Resume to continue`)
    },

    async resumeExecution() {
      if (!this.currentPlan || !this.connected) return
      // Re-submit remaining targets from where we paused
      const remaining = this.scheduledTargets.slice(this.currentTargetIndex)
      if (!remaining.length) return
      this.resumeOffset = this.currentTargetIndex
      this.executionStatus = 'running'
      this.addMessage(`Resuming from target ${this.currentTargetIndex + 1}`)
      try {
        await axios.post('/api/telescope/execute', {
          scheduled_targets: remaining,
          park_when_done: true,
        })
        this.startProgressPolling()
      } catch (err) {
        this.executionStatus = 'paused'
        this.error = 'Failed to resume: ' + (err.response?.data?.detail || err.message)
      }
    },

    async stopPlan() {
      try {
        await axios.post('/api/telescope/abort')
      } catch (e) { /* best-effort */ }
      this.stopProgressPolling()
      this.executionStatus = 'idle'
      this.currentPlan = null
      this.scheduledTargets = []
      this.currentTargetIndex = 0
      this.resumeOffset = 0
      this.addMessage('Plan stopped')
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
        useSettingsStore().save({ annotationsEnabled: enabled }).catch(() => {})
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
          const pi = response.data.pi_info || {}
          this.hardware.sensorTemp = pi.temp ?? null
          this.hardware.batteryTemp = pi.battery_temp ?? null
          this.hardware.batteryCapacity = pi.battery_capacity ?? null
          this.hardware.chargerStatus = pi.charger_status ?? null
          this.hardware.isOvertemp = pi.is_overtemp ?? false
          this.hardware.model = pi.model || null
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
