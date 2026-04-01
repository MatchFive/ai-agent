import { defineStore } from 'pinia'
import { agentApi } from '../api/agent'

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [],  // [{ role, content, timestamp }]
    conversationId: null,
    conversationTitle: '',
    isLoading: false,
    error: null,
    statusText: '正在分析中...',
    conversations: [],
    conversationTotal: 0,
    conversationsLoading: false
  }),

  getters: {
    lastMessage: (state) => state.messages[state.messages.length - 1] || null,
    messageCount: (state) => state.messages.length
  },

  actions: {
    /**
     * 加载对话历史列表
     */
    async fetchConversations(agentName, page = 1) {
      this.conversationsLoading = true
      try {
        const res = await agentApi.getConversations(agentName, page)
        this.conversations = res.items || []
        this.conversationTotal = res.total || 0
      } catch (e) {
        console.error('获取对话列表失败:', e)
      } finally {
        this.conversationsLoading = false
      }
    },

    /**
     * 加载指定对话的消息
     */
    async loadConversation(conversationId) {
      try {
        const res = await agentApi.getConversation(conversationId)
        this.conversationId = res.conversation_id
        this.conversationTitle = res.title || '新对话'
        this.messages = (res.messages || []).map(m => ({
          role: m.role,
          content: m.content,
          timestamp: m.timestamp
        }))
      } catch (e) {
        console.error('加载对话失败:', e)
      }
    },

    /**
     * 新建对话
     */
    newConversation() {
      this.messages = []
      this.conversationId = null
      this.conversationTitle = ''
      this.error = null
    },

    /**
     * 清空对话
     */
    async clearChat(agentName = null) {
      try {
        await agentApi.reset(this.conversationId, agentName)
        this.messages = []
        this.conversationId = null
        this.conversationTitle = ''
        this.error = null
        if (agentName) {
          await this.fetchConversations(agentName)
        }
      } catch (error) {
        console.error('Clear chat error:', error)
      }
    },

    /**
     * 删除对话
     */
    async deleteConversation(conversationId, agentName) {
      try {
        await agentApi.deleteConversation(conversationId)
        await this.fetchConversations(agentName)
        if (this.conversationId === conversationId) {
          this.newConversation()
        }
      } catch (e) {
        console.error('删除对话失败:', e)
      }
    },

    /**
     * 更新对话标题
     */
    async updateTitle(conversationId, title, agentName) {
      try {
        await agentApi.updateConversationTitle(conversationId, title)
        if (this.conversationId === conversationId) {
          this.conversationTitle = title
        }
        if (agentName) {
          await this.fetchConversations(agentName)
        }
      } catch (e) {
        console.error('更新标题失败:', e)
      }
    },

    /**
     * 重置状态
     */
    reset() {
      this.messages = []
      this.conversationId = null
      this.conversationTitle = ''
      this.isLoading = false
      this.error = null
      this.statusText = '正在分析中...'
    }
  }
})
