import { defineStore } from 'pinia'
import axios from 'axios'

export const useProcessingStore = defineStore('processing', {
  state: () => ({
    files: [],
    selectedFiles: [],
    currentDirectory: '/data',
    libraryImages: [],
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
    async browseDirectory(path) {
      this.loading = true
      this.error = null

      try {
        const response = await axios.get('/api/files/browse', {
          params: { path }
        })

        this.files = response.data.files
        this.currentDirectory = path
      } catch (err) {
        this.error = 'Failed to browse directory: ' + err.message
      } finally {
        this.loading = false
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

    async stackImages() {
      if (this.selectedFiles.length === 0) return

      try {
        const response = await axios.post('/api/process/stack-and-stretch', {
          files: this.selectedFiles.map(f => f.path),
          method: 'sigma_clipped_mean'
        })

        this.activeJob = response.data
        this.processingJobs.unshift(response.data)

        // Poll for job completion
        this.pollJobStatus(response.data.id)
      } catch (err) {
        this.error = 'Failed to start stacking: ' + err.message
      }
    },

    async pollJobStatus(jobId) {
      const interval = setInterval(async () => {
        try {
          const response = await axios.get(`/api/process/jobs/${jobId}`)
          const job = response.data

          // Update job in list
          const index = this.processingJobs.findIndex(j => j.id === jobId)
          if (index >= 0) {
            this.processingJobs[index] = job
          }

          if (job.status === 'completed' || job.status === 'failed') {
            clearInterval(interval)

            if (job.status === 'completed') {
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
