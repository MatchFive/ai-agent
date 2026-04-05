<template>
  <div class="app-layout">
    <!-- 顶部栏 -->
    <header class="app-header">
      <div class="app-logo">
        <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
          <rect width="32" height="32" rx="8" fill="url(#hgrad)" />
          <path d="M10 12L16 8L22 12V20L16 24L10 20V12Z" stroke="white" stroke-width="1.5" fill="none"/>
          <circle cx="16" cy="16" r="3" fill="white" opacity="0.9"/>
          <defs>
            <linearGradient id="hgrad" x1="0" y1="0" x2="32" y2="32">
              <stop stop-color="#6366f1"/>
              <stop offset="1" stop-color="#8b5cf6"/>
            </linearGradient>
          </defs>
        </svg>
        <span class="app-title">AI Agent</span>
      </div>
      <div class="user-area" @click="showUserModal = true">
        <el-avatar :size="32" :style="{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }">
          {{ (userStore.user?.username || 'U')[0].toUpperCase() }}
        </el-avatar>
        <span class="user-name">{{ userStore.user?.username }}</span>
        <svg width="12" height="12" viewBox="0 0 12 12" fill="none" class="arrow-icon">
          <path d="M3 4.5L6 7.5L9 4.5" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </header>

    <!-- 主体 -->
    <div class="app-body">
      <!-- 左侧 Agent 图标栏 -->
      <aside class="sidebar-narrow">
        <AgentSidebar v-model="selectedAgent" :agents="agentList" :loading="agentLoading" />
      </aside>

      <!-- 中间对话历史列表 -->
      <aside class="conversation-panel" v-if="selectedAgent">
        <ConversationList
          v-model="selectedConversation"
          :agent-name="selectedAgent"
          @new="handleNewConversation"
          @delete="handleDeleteConversation"
        />
      </aside>

      <!-- 右侧聊天面板 -->
      <main class="main-panel">
        <!-- 未选中 Agent -->
        <div v-if="!selectedAgent" class="welcome-panel">
          <div class="welcome-content">
            <div class="welcome-illustration">
              <div class="float-circle c1"></div>
              <div class="float-circle c2"></div>
              <div class="float-circle c3"></div>
              <div class="welcome-icon-box">
                <svg width="48" height="48" viewBox="0 0 32 32" fill="none">
                  <rect width="32" height="32" rx="8" fill="url(#wgrad)" />
                  <path d="M10 12L16 8L22 12V20L16 24L10 20V12Z" stroke="white" stroke-width="1.5" fill="none"/>
                  <circle cx="16" cy="16" r="3" fill="white" opacity="0.9"/>
                  <defs>
                    <linearGradient id="wgrad" x1="0" y1="0" x2="32" y2="32">
                      <stop stop-color="#6366f1"/>
                      <stop offset="1" stop-color="#8b5cf6"/>
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            </div>
            <h2 class="welcome-title">欢迎使用 AI Agent</h2>
            <p class="welcome-desc">从左侧选择一个智能助手，开始你的对话之旅</p>
            <div class="welcome-features" v-if="agentList.length > 0">
              <div class="feature-item" v-for="agent in agentList.slice(0, 3)" :key="agent.name">
                <span class="feature-dot"></span>
                {{ agent.description }}
              </div>
            </div>
          </div>
        </div>

        <!-- 聊天界面 -->
        <ChatPanel
          v-else
          :key="selectedAgent + '-' + (selectedConversation || 'new')"
          :agent-info="currentAgentInfo"
          :conversation-id="selectedConversation"
          @refresh-list="handleRefreshList"
        />
      </main>
    </div>

    <!-- 用户信息模态框 -->
    <UserModal v-model="showUserModal" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useUserStore } from '../store/user'
import { useChatStore } from '../store/chat'
import { agentApi } from '../api/agent'
import AgentSidebar from '../components/AgentSidebar.vue'
import ConversationList from '../components/ConversationList.vue'
import ChatPanel from '../components/ChatPanel.vue'
import UserModal from '../components/UserModal.vue'

const userStore = useUserStore()
const chatStore = useChatStore()

const selectedAgent = ref(null)
const selectedConversation = ref(null)
const showUserModal = ref(false)
const agentList = ref([])
const agentLoading = ref(true)

const currentAgentInfo = computed(() => {
  const agent = agentList.value.find(a => a.name === selectedAgent.value)
  return agent || { name: selectedAgent.value, description: '' }
})

const fetchAgentList = async () => {
  agentLoading.value = true
  try {
    const res = await agentApi.getList()
    agentList.value = res.items || []
  } catch (e) {
    console.error('获取 Agent 列表失败:', e)
  } finally {
    agentLoading.value = false
  }
}

const handleRefreshList = () => {
  if (selectedAgent.value) {
    chatStore.fetchConversations(selectedAgent.value)
  }
}

const handleNewConversation = () => {
  chatStore.newConversation()
  selectedConversation.value = null
}

const handleDeleteConversation = async (conversationId) => {
  await chatStore.deleteConversation(conversationId, selectedAgent.value)
}

// 切换 Agent 时加载对话列表
watch(selectedAgent, (agentName) => {
  if (agentName) {
    chatStore.newConversation()
    selectedConversation.value = null
    chatStore.fetchConversations(agentName)
  }
})

onMounted(() => {
  if (!userStore.user) {
    userStore.fetchUser()
  }
  fetchAgentList()
})
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: #f8fafc;
}

/* 顶部栏 */
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  padding: 0 16px;
  background: white;
  flex-shrink: 0;
  border-bottom: 1px solid #f1f5f9;
  z-index: 10;
}

.app-logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.app-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.02em;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 10px 4px 4px;
  border-radius: 10px;
  transition: background 0.2s;
}

.user-area:hover {
  background: #f1f5f9;
}

.user-name {
  font-size: 13px;
  color: #334155;
  font-weight: 500;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.arrow-icon {
  flex-shrink: 0;
}

/* 主体 */
.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar-narrow {
  width: 64px;
  flex-shrink: 0;
}

.conversation-panel {
  width: 260px;
  flex-shrink: 0;
}

.main-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f8fafc;
}

/* 欢迎面板 */
.welcome-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.welcome-content {
  text-align: center;
  max-width: 400px;
}

.welcome-illustration {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 32px;
}

.welcome-icon-box {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 12px 32px rgba(99, 102, 241, 0.25);
  animation: iconFloat 3s ease-in-out infinite;
}

@keyframes iconFloat {
  0%, 100% { transform: translate(-50%, -50%) translateY(0); }
  50% { transform: translate(-50%, -50%) translateY(-6px); }
}

.float-circle {
  position: absolute;
  border-radius: 50%;
  animation: circleFloat 4s ease-in-out infinite;
}

.c1 {
  width: 20px; height: 20px;
  top: 5px; right: 10px;
  background: #c7d2fe;
  animation-delay: 0s;
}

.c2 {
  width: 14px; height: 14px;
  bottom: 10px; left: 8px;
  background: #ddd6fe;
  animation-delay: 1s;
}

.c3 {
  width: 10px; height: 10px;
  top: 15px; left: 15px;
  background: #a5b4fc;
  animation-delay: 2s;
}

@keyframes circleFloat {
  0%, 100% { transform: translateY(0) scale(1); opacity: 0.6; }
  50% { transform: translateY(-8px) scale(1.1); opacity: 1; }
}

.welcome-title {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 8px;
  letter-spacing: -0.02em;
}

.welcome-desc {
  font-size: 15px;
  color: #64748b;
  margin: 0 0 28px;
  line-height: 1.6;
}

.welcome-features {
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px 20px;
  background: white;
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  border: 1px solid #f1f5f9;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #475569;
}

.feature-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6366f1;
  flex-shrink: 0;
}
</style>
