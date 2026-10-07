import axios from 'axios'

// Same-origin in production: FastAPI serves both the React app and /api/v1.
// Set VITE_API_URL only when intentionally using a separate API server.
const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'
export const API_ORIGIN = API_BASE.replace(/\/api\/v1\/?$/, '')

const api = axios.create({ baseURL: API_BASE })

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('civicconnect_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const authApi = {
  login: (payload) => api.post('/auth/login', payload),
  register: (payload) => api.post('/auth/register', payload),
  me: () => api.get('/auth/me'),
}

export const complaintApi = {
  list: () => api.get('/complaints'),
  officerList: () => api.get('/officer/complaints'),
  get: (id) => api.get(`/complaints/${id}`),
  create: (payload) => api.post('/complaints', payload),
  update: (id, payload) => api.patch(`/complaints/${id}`, payload),
  verify: (id, accepted) => api.post(`/complaints/${id}/verify`, null, { params: { accepted } }),
  accept: (id) => api.post(`/officer/complaints/${id}/accept`),
  start: (id) => api.post(`/officer/complaints/${id}/start`),
  resolve: (id) => api.post(`/officer/complaints/${id}/resolve`),
  upload: (file) => {
    const body = new FormData()
    body.append('file', file)
    return api.post('/uploads', body, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
}

export const adminApi = {
  dashboard: () => api.get('/admin/dashboard'),
  officers: () => api.get('/admin/officers'),
}

export const notificationApi = {
  list: () => api.get('/notifications'),
  markRead: (id) => api.post(`/notifications/${id}/read`),
}

export default api
