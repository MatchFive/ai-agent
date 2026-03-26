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
      <!-- 左侧 Agent 列表 -->
      <aside class="sidebar">
        <AgentSidebar v-model="selectedAgent" :agents="agentList" />
      </aside>

      <!-- 右侧面板 -->
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

        <!-- 选中 Agent 的聊天界面 -->
        <InvestmentChat v-else-if="selectedAgent === 'investment'" :key="selectedAgent" />
      </main>
    </div>

    <!-- 用户信息模态框 -->
    <UserModal v-model="showUserModal" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Connection, ArrowDown } from '@element-plus/icons-vue'
import { TrendCharts } from '@element-plus/icons-vue'
import { useUserStore } from '../store/user'
import AgentSidebar from '../components/AgentSidebar.vue'
import UserModal from '../components/UserModal.vue'
import InvestmentChat from './InvestmentChat.vue'

const userStore = useUserStore()

const selectedAgent = ref(null)
const showUserModal = ref(false)

// Agent 列表（数据驱动，后续扩展只需添加对象）
const agentList = [
  {
    id: 'investment',
    name: '投资理财',
    icon: 'TrendCharts',
    description: '提供黄金、股票市场分析和投资建议',
    color: '#667eea'
  }
]

onMounted(() => {
  if (!userStore.user) {
    userStore.fetchUser()
  }
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

/* 左侧栏 */
.sidebar {
  width: 220px;
  flex-shrink: 0;
  overflow: hidden;
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
