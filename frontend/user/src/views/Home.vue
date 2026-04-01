<template>
  <div class="app-layout">
    <!-- 顶部栏 -->
    <header class="app-header">
      <div class="app-logo">
        <el-icon :size="22" color="#fff"><Connection /></el-icon>
        <span class="app-title">AI-Agent</span>
      </div>
      <div class="user-area" @click="showUserModal = true">
        <el-avatar :size="32" :style="{ background: '#667eea' }">
          {{ (userStore.user?.username || 'U')[0].toUpperCase() }}
        </el-avatar>
        <span class="user-name">{{ userStore.user?.username }}</span>
        <el-icon :size="14" color="rgba(255,255,255,0.7)"><ArrowDown /></el-icon>
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
            <div class="welcome-icon">
              <el-icon :size="56" color="#667eea"><Connection /></el-icon>
            </div>
            <h2>欢迎使用 AI-Agent</h2>
            <p>请从左侧选择一个助手开始对话</p>
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
import { Connection, ArrowDown } from '@element-plus/icons-vue'
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
}

/* 顶部栏 */
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  flex-shrink: 0;
}

.app-logo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.app-title {
  font-size: 18px;
  font-weight: 700;
  color: white;
  letter-spacing: 0.5px;
}

.user-area {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 12px 4px 4px;
  border-radius: 20px;
  transition: background 0.2s;
}

.user-area:hover {
  background: rgba(255, 255, 255, 0.15);
}

.user-name {
  font-size: 14px;
  color: white;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 主体 */
.app-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* 左侧 Agent 图标栏 */
.sidebar-narrow {
  width: 60px;
  flex-shrink: 0;
}

/* 中间对话列表 */
.conversation-panel {
  width: 220px;
  flex-shrink: 0;
}

/* 右侧面板 */
.main-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 欢迎面板 */
.welcome-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
}

.welcome-content {
  text-align: center;
  color: #666;
}

.welcome-icon {
  margin-bottom: 20px;
  opacity: 0.6;
}

.welcome-content h2 {
  margin: 0 0 10px;
  font-size: 22px;
  font-weight: 600;
  color: #333;
}

.welcome-content p {
  font-size: 15px;
  color: #999;
}
</style>
