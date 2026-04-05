<template>
  <div class="chat-panel">
    <!-- 聊天面板顶栏 -->
    <div class="chat-header">
      <div class="chat-title">
        <div class="title-icon">{{ agentInfo.name.charAt(0) }}</div>
        <span>{{ chatStore.conversationTitle || agentInfo.description }}</span>
      </div>
      <div class="header-actions">
        <button
          class="clear-btn"
          @click="handleClearChat"
          :disabled="chatStore.messages.length === 0"
        >
          <el-icon :size="14"><Delete /></el-icon>
          <span>清空</span>
        </button>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="chat-messages" ref="messagesContainer">
      <!-- 欢迎消息 -->
      <div v-if="chatStore.messages.length === 0" class="welcome-message">
        <div class="welcome-icon-wrap">
          <div class="welcome-icon">{{ agentInfo.name.charAt(0) }}</div>
        </div>
        <h3>欢迎使用{{ agentInfo.description }}</h3>
        <p>{{ agentInfo.description }}，请在下方输入您的问题</p>
      </div>

      <!-- 消息列表 -->
      <div
        v-for="(message, index) in chatStore.messages"
        :key="index"
        :class="['message', message.role, { streaming: streamingIndex === index }]"
      >
        <div class="message-header">
          <el-avatar
            :size="28"
            :style="{ background: message.role === 'user' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : '#10b981' }"
          >
            <el-icon :size="14" style="color: white;">
              <component :is="message.role === 'user' ? User : ChatDotRound" />
            </el-icon>
          </el-avatar>
          <span class="role-name">{{ message.role === 'user' ? '你' : agentInfo.description }}</span>
          <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
          <el-button
            v-if="message.role === 'assistant' && message.content && !chatStore.isLoading"
            class="save-exp-btn"
            text
            size="small"
            :icon="CollectionTag"
            :loading="savingExperienceIndex === index"
            @click="handleSaveExperience(index)"
            title="存为经验"
          />
        </div>
        <div class="message-content markdown-body" v-html="renderMarkdown(message.content)"></div>
        <span v-if="streamingIndex === index" class="typing-cursor"></span>
      </div>

      <!-- Loading 指示器 -->
      <div v-if="chatStore.isLoading && streamingIndex === null" class="loading-indicator">
        <div class="loading-dots">
          <span></span><span></span><span></span>
        </div>
        <span>{{ chatStore.statusText }}</span>
      </div>

      <!-- 错误提示 -->
      <div v-if="chatStore.error" class="error-banner">
        <el-icon :size="16"><WarningFilled /></el-icon>
        <span>{{ chatStore.error }}</span>
        <button class="error-close" @click="chatStore.error = null">
          <el-icon :size="14"><Close /></el-icon>
        </button>
      </div>
    </div>

    <!-- 输入框 -->
    <div class="chat-input">
      <div class="input-wrapper">
        <el-input
          v-model="inputMessage"
          type="textarea"
          :rows="2"
          placeholder="输入你的问题..."
          @keydown.enter.ctrl="handleSend"
          :disabled="chatStore.isLoading"
          resize="none"
          class="msg-input"
        />
        <div class="input-actions">
          <span class="input-hint">Ctrl + Enter 发送</span>
          <button
            :class="['send-btn', { active: inputMessage.trim() && !chatStore.isLoading }]"
            :disabled="!inputMessage.trim() || chatStore.isLoading"
            @click="handleSend"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, ChatDotRound, CollectionTag, Delete, WarningFilled, Close } from '@element-plus/icons-vue'
import { useChatStore } from '../store/chat'
import { agentApi } from '../api/agent'
import { marked } from 'marked'
import hljs from 'highlight.js'

const props = defineProps({
  agentInfo: {
    type: Object,
    required: true
  },
  conversationId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['refreshList'])

const chatStore = useChatStore()

const inputMessage = ref('')
const messagesContainer = ref(null)
const savingExperienceIndex = ref(null)
const streamingIndex = ref(null)

// 配置 marked
marked.setOptions({
  breaks: true,
  gfm: true,
})

// 自定义 renderer —— 代码块高亮
const renderer = new marked.Renderer()
renderer.code = ({ text, lang }) => {
  const language = lang && hljs.getLanguage(lang) ? lang : 'plaintext'
  const highlighted = hljs.highlight(text, { language }).value
  return `<pre class="hljs-pre"><div class="code-header"><span class="code-lang">${language}</span><button class="copy-btn" onclick="navigator.clipboard.writeText(this.closest('pre').querySelector('code').textContent);this.textContent='已复制!';setTimeout(()=>this.textContent='复制',1500)">复制</button></div><code class="hljs language-${language}">${highlighted}</code></pre>`
}
marked.use({ renderer })

// 加载历史对话
watch(() => props.conversationId, async (id) => {
  if (id) {
    await chatStore.loadConversation(id)
    await nextTick()
    scrollToBottom()
  }
}, { immediate: true })

const renderMarkdown = (content) => {
  if (!content) return ''
  try {
    return marked.parse(content)
  } catch (e) {
    return content.replace(/</g, '&lt;').replace(/>/g, '&gt;')
  }
}

const handleSend = async () => {
  const message = inputMessage.value.trim()
  if (!message || chatStore.isLoading) return

  inputMessage.value = ''
  const isFirstMessage = !chatStore.conversationId

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
  const msgIndex = chatStore.messages.length - 1

  chatStore.isLoading = true
  streamingIndex.value = msgIndex
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
        streamingIndex.value = null
        chatStore.statusText = '正在分析中...'
      },
      () => {
        chatStore.isLoading = false
        streamingIndex.value = null
        chatStore.statusText = '正在分析中...'
        nextTick(() => scrollToBottom())

        if (isFirstMessage && chatStore.conversationId) {
          const title = message.length > 20 ? message.slice(0, 20) + '...' : message
          chatStore.updateTitle(chatStore.conversationId, title, props.agentInfo.name)
        }

        emit('refreshList')
      },
      (status) => {
        chatStore.statusText = status
      },
      props.agentInfo.name
    )
  } catch (error) {
    chatStore.error = error.message
    chatStore.isLoading = false
    streamingIndex.value = null
  }
}

const handleClearChat = async () => {
  try {
    await ElMessageBox.confirm('确定要清空当前对话吗？', '确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await chatStore.clearChat(props.agentInfo.name)
    ElMessage.success('对话已清空')
    emit('refreshList')
  } catch {
    // 用户取消
  }
}

const handleSaveExperience = async (assistantIndex) => {
  if (!chatStore.conversationId) {
    ElMessage.warning('请先开始对话')
    return
  }

  savingExperienceIndex.value = assistantIndex
  try {
    await agentApi.saveExperience(chatStore.conversationId, -1)
    ElMessage.success('已保存为经验')
  } catch (error) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    savingExperienceIndex.value = null
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
  if (chatStore.messages.length > 0) {
    nextTick(() => scrollToBottom())
  }
})
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8fafc;
}

/* ===== 顶栏 ===== */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 48px;
  background: white;
  border-bottom: 1px solid #f1f5f9;
  flex-shrink: 0;
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.title-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.clear-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-btn:hover:not(:disabled) {
  background: #fef2f2;
  color: #ef4444;
}

.clear-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

/* ===== 消息区域 ===== */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px 20px;
}

/* 欢迎消息 */
.welcome-message {
  text-align: center;
  padding: 60px 20px;
  color: #64748b;
}

.welcome-icon-wrap {
  margin-bottom: 20px;
}

.welcome-icon {
  width: 64px;
  height: 64px;
  border-radius: 18px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  font-weight: 700;
  box-shadow: 0 12px 32px rgba(99, 102, 241, 0.2);
}

.welcome-message h3 {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.welcome-message p {
  font-size: 14px;
  color: #94a3b8;
}

/* ===== 消息卡片 ===== */
.message {
  max-width: 820px;
  margin: 0 auto 20px;
  padding: 16px 20px;
  border-radius: 16px;
  background: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02);
  animation: msgFadeIn 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;
  transition: border-color 0.3s;
}

@keyframes msgFadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message.user {
  background: white;
  border-left: 3px solid #6366f1;
}

.message.assistant {
  border-left: 3px solid #10b981;
}

.message.assistant.streaming {
  border-left-color: #6366f1;
  box-shadow: 0 1px 3px rgba(99,102,241,0.06);
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
  color: #334155;
}

.timestamp {
  margin-left: auto;
  font-size: 11px;
  color: #cbd5e1;
}

.save-exp-btn {
  margin-left: 4px;
  opacity: 0;
  transition: opacity 0.2s;
  color: #94a3b8;
}

.message:hover .save-exp-btn {
  opacity: 1;
}

.save-exp-btn:hover {
  color: #6366f1;
}

.message-content {
  line-height: 1.75;
  color: #334155;
  font-size: 14px;
  word-break: break-word;
}

/* ===== Markdown 样式 ===== */
.message-content.markdown-body :deep(h1),
.message-content.markdown-body :deep(h2),
.message-content.markdown-body :deep(h3),
.message-content.markdown-body :deep(h4) {
  margin: 16px 0 8px;
  font-weight: 600;
  color: #1e293b;
}
.message-content.markdown-body :deep(h1) { font-size: 1.35em; }
.message-content.markdown-body :deep(h2) { font-size: 1.2em; }
.message-content.markdown-body :deep(h3) { font-size: 1.08em; }

.message-content.markdown-body :deep(p) { margin: 8px 0; }

.message-content.markdown-body :deep(ul),
.message-content.markdown-body :deep(ol) {
  padding-left: 24px;
  margin: 8px 0;
}

.message-content.markdown-body :deep(li) { margin: 4px 0; }

.message-content.markdown-body :deep(blockquote) {
  border-left: 4px solid #c7d2fe;
  padding: 10px 16px;
  margin: 10px 0;
  color: #475569;
  background: #f8fafc;
  border-radius: 0 10px 10px 0;
}

.message-content.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 10px 0;
  font-size: 13px;
}

.message-content.markdown-body :deep(th),
.message-content.markdown-body :deep(td) {
  border: 1px solid #e2e8f0;
  padding: 8px 12px;
  text-align: left;
}

.message-content.markdown-body :deep(th) {
  background: #f8fafc;
  font-weight: 600;
  color: #334155;
}

.message-content.markdown-body :deep(a) {
  color: #6366f1;
  text-decoration: none;
}
.message-content.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

/* 代码块 */
.message-content.markdown-body :deep(.hljs-pre) {
  position: relative;
  background: #1e293b;
  border-radius: 12px;
  overflow: hidden;
  margin: 14px 0;
}

.message-content.markdown-body :deep(.code-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #334155;
  font-size: 12px;
}

.message-content.markdown-body :deep(.code-lang) {
  color: #94a3b8;
  font-family: 'Inter', 'Consolas', monospace;
  font-weight: 500;
}

.message-content.markdown-body :deep(.copy-btn) {
  color: #94a3b8;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 6px;
  transition: all 0.2s;
  font-family: 'Inter', sans-serif;
}

.message-content.markdown-body :deep(.copy-btn:hover) {
  color: #e2e8f0;
  background: #475569;
}

.message-content.markdown-body :deep(.hljs) {
  display: block;
  padding: 16px;
  overflow-x: auto;
  font-family: 'JetBrains Mono', 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.7;
  background: #1e293b;
}

.message-content.markdown-body :deep(code:not(.hljs)) {
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 6px;
  font-family: 'JetBrains Mono', 'Consolas', monospace;
  font-size: 13px;
  color: #7c3aed;
}

/* ===== 打字机光标 ===== */
.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1.2em;
  background: #6366f1;
  margin-left: 2px;
  vertical-align: text-bottom;
  border-radius: 1px;
  animation: cursorBlink 0.8s ease infinite;
}

@keyframes cursorBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* ===== Loading ===== */
.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 24px;
  color: #94a3b8;
  font-size: 13px;
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 5px;
  height: 5px;
  background: #6366f1;
  border-radius: 50%;
  animation: dotPulse 1.4s infinite;
}

.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dotPulse {
  0%, 60%, 100% { transform: scale(0.8); opacity: 0.3; }
  30% { transform: scale(1.2); opacity: 1; }
}

/* ===== 错误提示 ===== */
.error-banner {
  max-width: 820px;
  margin: 16px auto;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
  color: #dc2626;
  font-size: 13px;
}

.error-close {
  margin-left: auto;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #dc2626;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.error-close:hover {
  opacity: 1;
}

/* ===== 输入区域 ===== */
.chat-input {
  flex-shrink: 0;
  background: white;
  border-top: 1px solid #f1f5f9;
  padding: 16px 20px;
}

.input-wrapper {
  max-width: 820px;
  margin: 0 auto;
}

.msg-input :deep(.el-textarea__inner) {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.6;
  color: #1e293b;
  resize: none;
  transition: all 0.2s;
  box-shadow: none;
}

.msg-input :deep(.el-textarea__inner:focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.msg-input :deep(.el-textarea__inner::placeholder) {
  color: #cbd5e1;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}

.input-hint {
  font-size: 11px;
  color: #cbd5e1;
}

.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: none;
  background: #e2e8f0;
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: not-allowed;
  transition: all 0.25s;
}

.send-btn.active {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: white;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.send-btn.active:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
}

.send-btn.active:active {
  transform: translateY(0);
}
</style>
