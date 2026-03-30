<template>
  <div class="chat-panel">
    <!-- 聊天面板顶栏 -->
    <div class="chat-header">
      <div class="chat-title">
        <div class="title-icon">{{ agentInfo.name.charAt(0) }}</div>
        <span>{{ agentInfo.description }}</span>
      </div>
      <el-button
        text
        size="small"
        @click="handleClearChat"
        :disabled="chatStore.messages.length === 0"
      >
        清空对话
      </el-button>
    </div>

    <!-- 消息列表 -->
    <div class="chat-messages" ref="messagesContainer">
      <!-- 欢迎消息 -->
      <div v-if="chatStore.messages.length === 0" class="welcome-message">
        <div class="welcome-icon">{{ agentInfo.name.charAt(0) }}</div>
        <h3>欢迎使用{{ agentInfo.description }}</h3>
        <p>{{ agentInfo.description }}，请输入您的问题</p>
      </div>

      <!-- 消息列表 -->
      <div
        v-for="(message, index) in chatStore.messages"
        :key="index"
        :class="['message', message.role]"
      >
        <div class="message-header">
          <el-avatar
            :size="32"
            :style="{ background: message.role === 'user' ? '#667eea' : '#67c23a' }"
          >
            <el-icon :size="16"><component :is="message.role === 'user' ? User : ChatDotRound" /></el-icon>
          </el-avatar>
          <span class="role-name">{{ message.role === 'user' ? '我' : agentInfo.description }}</span>
          <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
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

    <!-- 输入框 -->
    <div class="chat-input">
      <div class="input-container">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="2"
          placeholder="输入您的问题..."
          @keydown.enter.ctrl="handleSend"
          :disabled="chatStore.isLoading"
          resize="none"
        />
        <div class="input-actions">
          <span class="input-tip">Ctrl + Enter 发送</span>
          <el-button
            type="primary"
            size="small"
            @click="handleSend"
            :disabled="!inputMessage.trim() || chatStore.isLoading"
            :loading="chatStore.isLoading"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, ChatDotRound } from '@element-plus/icons-vue'
import { useChatStore } from '../store/chat'
import { agentApi } from '../api/agent'

const props = defineProps({
  agentInfo: {
    type: Object,
    required: true
  }
})

const chatStore = useChatStore()

const inputMessage = ref('')
const messagesContainer = ref(null)

// 切换 agent 时重置对话状态
watch(() => props.agentInfo.name, () => {
  chatStore.reset()
})

// 简单的 Markdown 渲染
const renderMarkdown = (content) => {
  if (!content) return ''
  let html = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  html = html.replace(/\n/g, '<br>')
  return html
}

// 发送消息
const handleSend = async () => {
  const message = inputMessage.value.trim()
  if (!message || chatStore.isLoading) return

  inputMessage.value = ''

  chatStore.messages.push({
    role: 'user',
    content: message,
    timestamp: new Date().toISOString()
  })

  const assistantMessage = {
    role: 'assistant',
    content: '',
    timestamp: new Date().toISOString()
  }
  chatStore.messages.push(assistantMessage)

  chatStore.isLoading = true
  chatStore.error = null

  await nextTick()
  scrollToBottom()

  try {
    await agentApi.chatStream(
      message,
      chatStore.conversationId,
      (chunk, conversationId) => {
        assistantMessage.content += chunk
        chatStore.statusText = '正在回复...'
        if (conversationId) {
          chatStore.conversationId = conversationId
        }
        nextTick(() => scrollToBottom())
      },
      (error) => {
        chatStore.error = error
        chatStore.isLoading = false
        chatStore.statusText = '正在分析中...'
      },
      () => {
        chatStore.isLoading = false
        chatStore.statusText = '正在分析中...'
        nextTick(() => scrollToBottom())
      },
      (status) => {
        chatStore.statusText = status
      },
      props.agentInfo.name
    )
  } catch (error) {
    chatStore.error = error.message
    chatStore.isLoading = false
  }
}

const handleClearChat = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有对话记录吗？', '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await chatStore.clearChat(props.agentInfo.name)
    ElMessage.success('对话已清空')
  } catch {
    // 用户取消
  }
}

const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

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
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f7fa;
}

/* 顶栏 */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 48px;
  background: white;
  border-bottom: 1px solid #ebeef5;
  flex-shrink: 0;
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.title-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.welcome-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 16px;
}

.welcome-message h3 {
  margin: 0 0 10px;
  color: #333;
}

.welcome-message p {
  margin-bottom: 0;
  font-size: 14px;
}

/* 消息卡片 */
.message {
  max-width: 800px;
  margin: 0 auto 16px;
  padding: 14px 16px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%);
  border-left: 3px solid #667eea;
}

.message.assistant {
  border-left: 3px solid #67c23a;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.role-name {
  font-weight: 600;
  font-size: 13px;
  color: #333;
}

.timestamp {
  margin-left: auto;
  font-size: 11px;
  color: #999;
}

.message-content {
  line-height: 1.8;
  color: #333;
  font-size: 14px;
}

.message-content :deep(pre) {
  background: #f6f8fa;
  padding: 10px 14px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-content :deep(code) {
  background: #f6f8fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #e83e8c;
}

.message-content :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
}

/* Loading */
.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 20px;
  color: #999;
  font-size: 13px;
}

.typing-animation {
  display: flex;
  gap: 4px;
}

.typing-animation span {
  width: 6px;
  height: 6px;
  background: #667eea;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-animation span:nth-child(2) { animation-delay: 0.2s; }
.typing-animation span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-6px); }
}

.error-alert {
  max-width: 800px;
  margin: 16px auto;
}

/* 输入区域 */
.chat-input {
  flex-shrink: 0;
  background: white;
  border-top: 1px solid #ebeef5;
  padding: 12px 20px;
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.input-tip {
  font-size: 12px;
  color: #c0c4cc;
}
</style>
