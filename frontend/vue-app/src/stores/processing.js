import { defineStore } from 'pinia'
import axios from 'axios'

export const useProcessingStore = defineStore('processing', {
  state: () => ({
    // Capture groups (by target)
    captures: [],
    selectedCapture: null,

    // Files for selected capture
    files: [],
    selectedFiles: [],

    // Scan results
    scanResults: null,
    scanning: false,

    // Processing
    previewImage: null,
    processingJobs: [],
    activeJob: null,

    loading: false,
    error: null
  }),

  getters: {
    selectedFileCount: (state) => state.selectedFiles.length,
    hasSelection: (state) => state.selectedFiles.length > 0
  },

  actions: {
    async loadCaptures() {
      this.loading = true
      this.error = null

      try {
        const response = await axios.get('/api/captures')
        this.captures = response.data
      } catch (err) {
        this.error = 'Failed to load captures: ' + err.message
        console.error('Load captures error:', err)
      } finally {
        this.loading = false
      }
    },

    async selectCapture(catalogId) {
      this.loading = true
      this.error = null
      this.selectedCapture = catalogId

      try {
        const response = await axios.get(`/api/captures/${catalogId}/files`)
        this.files = response.data.map(file => ({
          id: file.id,
          name: file.file_path.split('/').pop(),
          path: file.file_path,
          size: file.file_size_bytes,
          type: file.file_type,
          catalogId: file.catalog_id
        }))
      } catch (err) {
        this.error = 'Failed to load files: ' + err.message
        console.error('Load files error:', err)
      } finally {
        this.loading = false
      }
    },

    async scanForNewFiles() {
      this.scanning = true
      this.error = null

      try {
        const response = await axios.get('/api/processing/scan-new')
        this.scanResults = response.data

        // Reload captures to include newly scanned files
        await this.loadCaptures()
      } catch (err) {
        this.error = 'Failed to scan files: ' + err.message
        console.error('Scan error:', err)
      } finally {
        this.scanning = false
      }
    },

    selectFile(file) {
      if (!this.selectedFiles.includes(file)) {
        this.selectedFiles.push(file)
      }
    },

    deselectFile(file) {
      this.selectedFiles = this.selectedFiles.filter(f => f !== file)
    },

    clearSelection() {
      this.selectedFiles = []
    },

    async batchProcessNew() {
      this.loading = true
      this.error = null

      try {
        const response = await axios.post('/api/processing/batch-process-new')
        this.activeJob = response.data
        this.processingJobs.unshift(response.data)

        // Poll for completion if task_id returned
        if (response.data.task_id) {
          this.pollJobStatus(response.data.task_id)
        }
      } catch (err) {
        this.error = 'Failed to start batch processing: ' + err.message
        console.error('Batch process error:', err)
      } finally {
        this.loading = false
      }
    },

    async stackImages() {
      if (this.selectedFiles.length === 0) return

      this.loading = true
      this.error = null

      try {
        // Use the processing API with file IDs
        const response = await axios.post('/api/processing/stack', {
          file_ids: this.selectedFiles.map(f => f.id),
          method: 'sigma_clipped_mean'
        })

        this.activeJob = response.data
        this.processingJobs.unshift(response.data)

        // Poll for job completion
        if (response.data.task_id) {
          this.pollJobStatus(response.data.task_id)
        }
      } catch (err) {
        this.error = 'Failed to start stacking: ' + err.message
        console.error('Stack error:', err)
      } finally {
        this.loading = false
      }
    },

    async pollJobStatus(taskId) {
      const interval = setInterval(async () => {
        try {
          const response = await axios.get(`/api/processing/status/${taskId}`)
          const job = response.data

          // Update job in list
          const index = this.processingJobs.findIndex(j => j.task_id === taskId)
          if (index >= 0) {
            this.processingJobs[index] = job
          }

          if (job.status === 'completed' || job.status === 'failed') {
            clearInterval(interval)

            if (job.status === 'completed' && job.result_path) {
              this.previewImage = job.result_path
            }
          }
        } catch (err) {
          console.error('Job status poll error:', err)
          clearInterval(interval)
        }
      }, 2000)
    },

    async loadLibrary() {
      try {
        const response = await axios.get('/api/library/images')
        this.libraryImages = response.data
      } catch (err) {
        console.error('Library load error:', err)
      }
    }
  }
})
