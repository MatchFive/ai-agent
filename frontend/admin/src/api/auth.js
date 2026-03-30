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
  toggleUserActive: (id) => api.post(`/admin/users/${id}/toggle-active`),

  // 工具管理
  getTools: () => api.get('/admin/tools'),
  reloadTools: () => api.post('/admin/tools/reload'),
  getTool: (id) => api.get(`/admin/tools/${id}`),
  updateTool: (id, data) => api.put(`/admin/tools/${id}`, data),
  toggleTool: (id) => api.patch(`/admin/tools/${id}`),

  // Agent管理
  getAgents: () => api.get('/admin/agents'),
  getAgent: (id) => api.get(`/admin/agents/${id}`),
  createAgent: (data) => api.post('/admin/agents', data),
  updateAgent: (id, data) => api.put(`/admin/agents/${id}`, data),
  toggleAgent: (id) => api.patch(`/admin/agents/${id}`),
  deleteAgent: (id) => api.delete(`/admin/agents/${id}`),
  setAgentTools: (agentId, toolIds) => api.post(`/admin/agents/${agentId}/tools`, { tool_ids: toolIds }),
  removeAgentTool: (agentId, toolId) => api.delete(`/admin/agents/${agentId}/tools/${toolId}`)
}

export default api
