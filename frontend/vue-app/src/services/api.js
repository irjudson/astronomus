import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export const catalogApi = {
  getTargets: (params) => api.get('/targets', { params }),
  getTarget: (id) => api.get(`/targets/${id}`),
  searchTargets: (query) => api.get('/targets/search', { params: { q: query } }),
  getStats: () => api.get('/targets/stats')
}

export const plannerApi = {
  generatePlan: (data) => api.post('/plan', data),
  getPlans: () => api.get('/plans'),
  getPlan: (id) => api.get(`/plans/${id}`),
  exportPlan: (id, format) => api.get(`/plans/${id}/export/${format}`)
}

export const weatherApi = {
  getCurrent: () => api.get('/weather/current'),
  getForecast: () => api.get('/weather/forecast')
}

export const telescopeApi = {
  connect: (ip) => api.post('/telescope/connect', { ip }),
  disconnect: () => api.post('/telescope/disconnect'),
  getStatus: () => api.get('/telescope/status'),
  slewTo: (target) => api.post('/telescope/slew', target),
  park: () => api.post('/telescope/park'),
  unpark: () => api.post('/telescope/unpark')
}

export default api
