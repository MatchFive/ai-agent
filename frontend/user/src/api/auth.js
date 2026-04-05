import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
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
    const status = error.response?.status
    const message = error.response?.data?.detail || '请求失败'

    // Token 过期或无效，自动跳转登录页
    if (status === 401 && message.includes('过期')) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      // 避免在登录页重复跳转
      if (window.location.hash !== '#/login') {
        window.location.hash = '#/login'
      }
      return Promise.reject(new Error('登录已过期，请重新登录'))
    }

    return Promise.reject(new Error(message))
  }
)

export const authApi = {
  login: (credentials) => api.post('/auth/login', credentials),
  register: (data) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
  changePassword: (data) => api.put('/auth/password', data),
  sendEmailCode: (email) => api.post('/auth/email/send-code', { email }),
  bindEmail: (data) => api.post('/auth/email/bind', data),
  unbindEmail: () => api.delete('/auth/email'),
}

export default api
