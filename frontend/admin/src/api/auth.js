import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export const authApi = {
  login: (credentials) => api.post('/auth/login', credentials),
  getMe: () => api.get('/auth/me')
}

export const adminApi = {
  // 统计
  getStats: () => api.get('/admin/stats'),

  // 邀请码
  getInviteCodes: (params) => api.get('/admin/invite-codes', { params }),
  createInviteCodes: (data) => api.post('/admin/invite-codes', data),
  deleteInviteCode: (id) => api.delete(`/admin/invite-codes/${id}`),

  // 用户
  getUsers: (params) => api.get('/admin/users', { params }),
  toggleUserActive: (id) => api.post(`/admin/users/${id}/toggle-active`)
}

export default api
