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
     * 清空对话
     */
    async clearChat(agentName = null) {
      try {
        await agentApi.reset(this.conversationId, agentName)
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
