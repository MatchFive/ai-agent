import { defineStore } from 'pinia'
import { agentApi } from '../api/agent'

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [],  // [{ role, content, timestamp }]
    conversationId: null,
    isLoading: false,
    error: null,
    statusText: '正在分析中...'
  }),

  getters: {
    lastMessage: (state) => state.messages[state.messages.length - 1] || null,
    messageCount: (state) => state.messages.length
  },

  actions: {
    /**
     * 发送消息（流式）
     */
    async sendMessage(userMessage) {
      // 添加用户消息
      this.messages.push({
        role: 'user',
        content: userMessage,
        timestamp: new Date().toISOString()
      })

      // 添加助手消息占位
      const assistantMessage = {
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString()
      }
      this.messages.push(assistantMessage)

      this.isLoading = true
      this.error = null
      this.statusText = '正在分析中...'

      return new Promise((resolve, reject) => {
        agentApi.chatStream(
          userMessage,
          this.conversationId,
          // onMessage
          (chunk, conversationId) => {
            assistantMessage.content += chunk
            this.statusText = '正在回复...'
            if (conversationId && !this.conversationId) {
              this.conversationId = conversationId
            }
          },
          // onError
          (error) => {
            this.error = error
            this.isLoading = false
            reject(new Error(error))
          },
          // onDone
          () => {
            this.isLoading = false
            this.statusText = '正在分析中...'
            resolve()
          },
          // onStatus
          (status) => {
            this.statusText = status
          }
        )
      })
    },

    /**
     * 发送消息（非流式）
     */
    async sendMessageSync(userMessage) {
      this.messages.push({
        role: 'user',
        content: userMessage,
        timestamp: new Date().toISOString()
      })

      this.isLoading = true
      this.error = null

      try {
        const response = await agentApi.chat(userMessage, this.conversationId)

        if (!this.conversationId) {
          this.conversationId = response.conversation_id
        }

        this.messages.push({
          role: 'assistant',
          content: response.message.content,
          timestamp: response.message.timestamp || new Date().toISOString()
        })
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.isLoading = false
      }
    },

    /**
     * 清空对话
     */
    async clearChat() {
      try {
        await agentApi.reset(this.conversationId)
        this.messages = []
        this.conversationId = null
        this.error = null
      } catch (error) {
        console.error('Clear chat error:', error)
      }
    },

    /**
     * 重置状态
     */
    reset() {
      this.messages = []
      this.conversationId = null
      this.isLoading = false
      this.error = null
      this.statusText = '正在分析中...'
    }
  }
})
