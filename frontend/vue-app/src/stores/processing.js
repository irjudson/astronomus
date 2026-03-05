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

    // Processing jobs
    previewImage: null,
    previewImageUrl: null,
    previewLoading: false,
    previewError: null,
    processingJobs: [],
    activeJob: null,

    // Library browser state (for LibraryBrowser.vue)
    libraryItems: [],
    librarySearch: '',
    libraryFilter: 'all',

    // ProcessingPanel.vue operation config
    operationType: '',
    outputFormat: 'tiff',
    outputFilename: '',

    loading: false,
    error: null,
  }),

  getters: {
    selectedFileCount: (state) => state.selectedFiles.length,
    hasSelection: (state) => state.selectedFiles.length > 0,

    filteredLibraryItems: (state) => {
      let items = state.libraryItems
      if (state.librarySearch) {
        const q = state.librarySearch.toLowerCase()
        items = items.filter(i => i.name.toLowerCase().includes(q))
      }
      if (state.libraryFilter && state.libraryFilter !== 'all') {
        items = items.filter(i => i.status === state.libraryFilter)
      }
      return items
    },
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
          catalogId: file.catalog_id,
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

    // Used by LibraryBrowser.vue and ProcessingPanel.vue (addTestFile)
    addSelectedFile(file) {
      const key = file.id ?? file.name
      if (!this.selectedFiles.some(f => (f.id ?? f.name) === key)) {
        this.selectedFiles.push(file)
      }
    },

    // Used by ProcessingPanel.vue (passes filename string)
    removeSelectedFile(name) {
      this.selectedFiles = this.selectedFiles.filter(f => f.name !== name)
    },

    // ProcessingPanel.vue operation config setters
    setOperationType(val) { this.operationType = val },
    setOutputFormat(val) { this.outputFormat = val },
    setOutputFilename(val) { this.outputFilename = val },

    // Library browser setters
    setLibrarySearch(query) { this.librarySearch = query },
    setLibraryFilter(filter) { this.libraryFilter = filter },

    // Fetch processed outputs for LibraryBrowser.vue
    async fetchLibraryItems() {
      this.loading = true
      this.error = null
      try {
        const response = await axios.get('/api/processing/outputs')
        this.libraryItems = (response.data.files || []).map(f => ({
          id: f.name,
          name: f.name,
          status: f.is_previewable ? 'complete' : 'new',
          preview_url: f.preview_url,
          download_url: f.download_url,
        }))
      } catch (err) {
        this.error = 'Failed to load library: ' + err.message
        console.error('Library load error:', err)
      } finally {
        this.loading = false
      }
    },

    // Fetch most recent preview image for ProcessingPreview.vue
    async fetchPreview() {
      this.previewLoading = true
      this.previewError = null
      try {
        const response = await axios.get('/api/processing/outputs')
        const previewable = (response.data.files || []).filter(f => f.is_previewable)
        if (previewable.length > 0) {
          this.previewImageUrl = previewable[0].preview_url
          this.previewImage = previewable[0].preview_url
        } else {
          this.previewImageUrl = null
        }
      } catch (err) {
        this.previewError = 'Failed to load preview: ' + err.message
        console.error('Preview fetch error:', err)
      } finally {
        this.previewLoading = false
      }
    },

    async clearProcessingJobs() {
      this.processingJobs = []
      this.activeJob = null
    },

    async batchProcessNew() {
      this.loading = true
      this.error = null
      try {
        const response = await axios.post('/api/processing/batch-process-new')
        const job = { id: response.data.job_id ?? response.data.id, status: response.data.status, progress_percent: 0 }
        this.activeJob = job
        this.processingJobs.unshift(job)
        if (job.id) {
          this.pollJobStatus(job.id)
        }
      } catch (err) {
        this.error = 'Failed to start batch processing: ' + err.message
        console.error('Batch process error:', err)
      } finally {
        this.loading = false
      }
    },

    // Stack selected images — calls POST /api/processing/auto per selected file
    async stackImages() {
      if (this.selectedFiles.length === 0) return
      this.loading = true
      this.error = null
      try {
        const file = this.selectedFiles[0]
        const response = await axios.post('/api/processing/auto', {
          file_path: file.path,
          formats: ['jpg', 'png', 'tiff'],
        })
        const job = {
          id: response.data.job_id,
          name: file.name,
          status: response.data.status,
          progress_percent: 0,
        }
        this.activeJob = job
        this.processingJobs.unshift(job)
        this.pollJobStatus(response.data.job_id)
      } catch (err) {
        this.error = 'Failed to start processing: ' + err.message
        console.error('Stack error:', err)
      } finally {
        this.loading = false
      }
    },

    // Start processing with configured operation type (ProcessingPanel.vue)
    async startProcessing() {
      if (this.selectedFiles.length === 0 || !this.operationType) return
      this.loading = true
      this.error = null
      try {
        const file = this.selectedFiles[0]
        const formats = this.outputFormat === 'fits' ? ['tiff'] : [this.outputFormat]
        const response = await axios.post('/api/processing/auto', {
          file_path: file.path,
          formats,
        })
        const job = {
          id: response.data.job_id,
          name: file.name,
          status: response.data.status,
          progress_percent: 0,
        }
        this.activeJob = job
        this.processingJobs.unshift(job)
        this.pollJobStatus(response.data.job_id)
      } catch (err) {
        this.error = 'Failed to start processing: ' + err.message
        console.error('Start processing error:', err)
      } finally {
        this.loading = false
      }
    },

    // Poll GET /api/processing/jobs/{job_id} until complete or failed
    pollJobStatus(jobId) {
      const interval = setInterval(async () => {
        try {
          const response = await axios.get(`/api/processing/jobs/${jobId}`)
          const updated = response.data

          // Update in job list by id
          const index = this.processingJobs.findIndex(j => j.id === jobId)
          if (index >= 0) {
            this.processingJobs[index] = { ...this.processingJobs[index], ...updated }
          }
          if (this.activeJob && this.activeJob.id === jobId) {
            this.activeJob = { ...this.activeJob, ...updated }
          }

          if (updated.status === 'complete' || updated.status === 'failed') {
            clearInterval(interval)
            if (updated.status === 'complete' && updated.output_files?.length > 0) {
              const filename = updated.output_files[0].split('/').pop()
              this.previewImage = `/api/process/outputs/${filename}`
              this.previewImageUrl = this.previewImage
            }
          }
        } catch (err) {
          console.error('Job status poll error:', err)
          clearInterval(interval)
        }
      }, 2000)
    },
  },
})
