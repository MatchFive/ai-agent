<template>
  <div class="investment-chat">
    <el-container>
      <!-- 顶部导航 -->
      <el-header>
        <div class="header-content">
          <h2>投资理财分析助手</h2>
          <div class="header-actions">
            <el-button
              type="danger"
              size="small"
              @click="handleClearChat"
              :disabled="chatStore.messages.length === 0"
            >
              清空对话
            </el-button>
            <el-button
              type="info"
              size="small"
              @click="handleLogout"
            >
              退出
            </el-button>
          </div>
        </div>
      </el-header>

      <!-- 消息列表 -->
      <el-main ref="mainContainer">
        <div class="messages-container" ref="messagesContainer">
          <!-- 欢迎消息 -->
          <div v-if="chatStore.messages.length === 0" class="welcome-message">
            <el-icon :size="48" color="#667eea"><TrendCharts /></el-icon>
            <h3>欢迎使用投资理财分析助手</h3>
            <p>我可以帮您分析黄金、股票等投资产品的走势</p>
            <div class="quick-actions">
              <el-button @click="sendQuickMessage('黄金现在多少钱？')">
                黄金价格
              </el-button>
              <el-button @click="sendQuickMessage('苹果股票怎么样？')">
                苹果股票
              </el-button>
              <el-button @click="sendQuickMessage('最近有什么财经新闻？')">
                财经新闻
              </el-button>
            </div>
          </div>

          <!-- 消息列表 -->
          <div
            v-for="(message, index) in chatStore.messages"
            :key="index"
            :class="['message', message.role]"
          >
            <div class="message-header">
              <el-avatar
                :size="36"
                :style="{ background: message.role === 'user' ? '#667eea' : '#67c23a' }"
              >
                <el-icon :size="20"><component :is="message.role === 'user' ? User : ChatDotRound" /></el-icon>
              </el-avatar>
              <span class="role-name">
                {{ message.role === 'user' ? '我' : '投资助手' }}
              </span>
              <span class="timestamp">
                {{ formatTime(message.timestamp) }}
              </span>
            </div>
            <div class="message-content" v-html="renderMarkdown(message.content)"></div>
          </div>

          <!-- Loading 指示器 -->
          <div v-if="chatStore.isLoading && !chatStore.messages[chatStore.messages.length - 1]?.content" class="loading-indicator">
            <div class="typing-animation">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span>{{ chatStore.statusText }}</span>
          </div>

          <!-- 错误提示 -->
          <el-alert
            v-if="chatStore.error"
            :title="chatStore.error"
            type="error"
            :closable="true"
            @close="chatStore.error = null"
            show-icon
            class="error-alert"
          />
        </div>
      </el-main>

      <!-- 输入框 -->
      <el-footer height="auto">
        <div class="input-container">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="3"
            placeholder="输入您的投资问题，例如：黄金现在多少钱？苹果股票怎么样？"
            @keydown.enter.ctrl="handleSend"
            :disabled="chatStore.isLoading"
            resize="none"
          />
          <div class="input-actions">
            <span class="input-tip">Ctrl + Enter 发送</span>
            <el-button
              type="primary"
              @click="handleSend"
              :disabled="!inputMessage.trim() || chatStore.isLoading"
              :loading="chatStore.isLoading"
            >
              发送
            </el-button>
          </div>
        </div>
      </el-footer>
    </el-container>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, ChatDotRound, TrendCharts } from '@element-plus/icons-vue'
import { useUserStore } from '../store/user'
import { useChatStore } from '../store/chat'
import { agentApi } from '../api/agent'

const router = useRouter()
const userStore = useUserStore()
const chatStore = useChatStore()

const inputMessage = ref('')
const messagesContainer = ref(null)

// 简单的 Markdown 渲染
const renderMarkdown = (content) => {
  if (!content) return ''

  // 转义 HTML
  let html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')

  // 代码块
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')

  // 行内代码
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')

  // 粗体
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')

  // 斜体
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')

  // 换行
  html = html.replace(/\n/g, '<br>')

  return html
}

// 发送消息
const handleSend = async () => {
  const message = inputMessage.value.trim()
  if (!message || chatStore.isLoading) return

  inputMessage.value = ''

  // 添加用户消息
  chatStore.messages.push({
    role: 'user',
    content: message,
    timestamp: new Date().toISOString()
  })

  // 添加助手消息占位
  const assistantMessage = {
    role: 'assistant',
    content: '',
    timestamp: new Date().toISOString()
  }
  chatStore.messages.push(assistantMessage)

  chatStore.isLoading = true
  chatStore.error = null

  // 滚动到底部
  await nextTick()
  scrollToBottom()

  try {
    await agentApi.chatStream(
      message,
      chatStore.conversationId,
      // onMessage
      (chunk, conversationId) => {
        assistantMessage.content += chunk
        chatStore.statusText = '正在回复...'
        if (conversationId) {
          chatStore.conversationId = conversationId
        }
        // 滚动到底部
        nextTick(() => scrollToBottom())
      },
      // onError
      (error) => {
        chatStore.error = error
        chatStore.isLoading = false
        chatStore.statusText = '正在分析中...'
      },
      // onDone
      () => {
        chatStore.isLoading = false
        chatStore.statusText = '正在分析中...'
        nextTick(() => scrollToBottom())
      },
      // onStatus
      (status) => {
        chatStore.statusText = status
      }
    )
  } catch (error) {
    chatStore.error = error.message
    chatStore.isLoading = false
  }
}

// 快捷消息
const sendQuickMessage = (message) => {
  inputMessage.value = message
  handleSend()
}

// 清空对话
const handleClearChat = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有对话记录吗？',
      '确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await chatStore.clearChat()
    ElMessage.success('对话已清空')
  } catch (error) {
    // 用户取消
  }
}

// 退出登录
const handleLogout = () => {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

// 格式化时间
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

onMounted(() => {
  scrollToBottom()
})
</script>

<style scoped>
.investment-chat {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f7fa;
}

.el-container {
  height: 100%;
}

.el-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
  height: 60px !important;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h2 {
  margin: 0;
  font-size: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.el-main {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #f5f7fa;
}

.messages-container {
  max-width: 900px;
  margin: 0 auto;
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.welcome-message h3 {
  margin: 20px 0 10px;
  color: #333;
}

.welcome-message p {
  margin-bottom: 30px;
}

.quick-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

.message {
  margin-bottom: 20px;
  padding: 16px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  border-left: 4px solid #667eea;
}

.message.assistant {
  background: white;
  border-left: 4px solid #67c23a;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.role-name {
  font-weight: 600;
  color: #333;
}

.timestamp {
  margin-left: auto;
  font-size: 12px;
  color: #999;
}

.message-content {
  line-height: 1.8;
  color: #333;
  font-size: 15px;
}

.message-content :deep(pre) {
  background: #f6f8fa;
  padding: 12px 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 10px 0;
}

.message-content :deep(code) {
  background: #f6f8fa;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  color: #e83e8c;
}

.message-content :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  color: #666;
}

.typing-animation {
  display: flex;
  gap: 4px;
}

.typing-animation span {
  width: 8px;
  height: 8px;
  background: #667eea;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-animation span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-animation span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-8px); }
}

.error-alert {
  margin-top: 20px;
}

.el-footer {
  background: white;
  border-top: 1px solid #e4e7ed;
  padding: 16px 20px !important;
}

.input-container {
  max-width: 900px;
  margin: 0 auto;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.input-tip {
  font-size: 12px;
  color: #909399;
}
</style>
