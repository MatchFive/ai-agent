import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000  // Agent 响应可能较慢
})

// 请求拦截器 - 添加 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export const agentApi = {
  /**
   * 获取 Agent 信息
   */
  getInfo: () => api.get('/agent/info'),

  /**
   * 非流式对话
   */
  chat: (message, conversationId = null) =>
    api.post('/agent/chat', {
      message,
      stream: false,
      conversation_id: conversationId
    }),

  /**
   * 流式对话
   */
  chatStream: async (message, conversationId, onMessage, onError, onDone) => {
    const token = localStorage.getItem('token')

    try {
      const response = await fetch('/api/agent/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message,
          stream: true,
          conversation_id: conversationId
        })
      })

      if (!response.ok) {
        throw new Error('请求失败')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)

            if (data === '[DONE]') {
              onDone()
              return
            }

            try {
              const parsed = JSON.parse(data)
              if (parsed.error) {
                onError(parsed.error)
              } else if (parsed.content) {
                onMessage(parsed.content, parsed.conversation_id)
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }
    } catch (error) {
      onError(error.message)
    }
  },

  /**
   * 重置对话
   */
  reset: () => api.post('/agent/reset'),

  /**
   * 获取工具列表
   */
  getTools: () => api.get('/agent/tools')
}

export default api
