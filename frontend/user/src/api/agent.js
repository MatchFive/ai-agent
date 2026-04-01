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
   * 获取所有可用 Agent 列表
   */
  getList: () => api.get('/agent/list'),

  /**
   * 获取 Agent 信息
   */
  getInfo: (agentName) => api.get('/agent/info', { params: { agent_name: agentName } }),

  /**
   * 非流式对话
   */
  chat: (message, conversationId = null, agentName = null) =>
    api.post('/agent/chat', {
      message,
      stream: false,
      conversation_id: conversationId
    }, { params: agentName ? { agent_name: agentName } : {} }),

  /**
   * 流式对话
   */
  chatStream: async (message, conversationId, onMessage, onError, onDone, onStatus, agentName = null) => {
    const token = localStorage.getItem('token')

    const params = agentName ? `?agent_name=${encodeURIComponent(agentName)}` : ''

    try {
      const response = await fetch(`/api/agent/chat/stream${params}`, {
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
              } else if (parsed.type === 'status') {
                if (onStatus) onStatus(parsed.content)
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
  reset: (conversationId = null, agentName = null) => api.post('/agent/reset', {
    conversation_id: conversationId
  }, { params: agentName ? { agent_name: agentName } : {} }),

  /**
   * 获取工具列表
   */
  getTools: (agentName) => api.get('/agent/tools', { params: agentName ? { agent_name: agentName } : {} }),

  /**
   * 获取对话历史列表
   */
  getConversations: (agentName, page = 1, pageSize = 20) =>
    api.get('/agent/conversations', { params: { agent_name: agentName, page, page_size: pageSize } }),

  /**
   * 获取对话详情
   */
  getConversation: (conversationId) =>
    api.get(`/agent/conversations/${conversationId}`),

  /**
   * 更新对话标题
   */
  updateConversationTitle: (conversationId, title) =>
    api.put(`/agent/conversations/${conversationId}/title`, { title }),

  /**
   * 删除对话
   */
  deleteConversation: (conversationId) =>
    api.delete(`/agent/conversations/${conversationId}`),

  // ==================== 经验知识库 ====================

  /**
   * 保存经验
   */
  saveExperience: (conversationId, questionIndex = -1) =>
    api.post('/agent/experiences', { conversation_id: conversationId, question_index: questionIndex }),

  // ==================== 长期记忆 ====================

  /**
   * 获取长期记忆列表
   */
  getMemories: (page = 1, pageSize = 20, category = null) =>
    api.get('/agent/memories', { params: { page, page_size: pageSize, ...(category ? { category } : {}) } }),

  /**
   * 删除长期记忆
   */
  deleteMemory: (memoryId) =>
    api.delete(`/agent/memories/${memoryId}`),

  /**
   * 清空长期记忆
   */
  clearMemories: () =>
    api.delete('/agent/memories'),
}

export default api
