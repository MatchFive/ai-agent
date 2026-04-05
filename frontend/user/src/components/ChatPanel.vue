<template>
  <div class="chat-panel">
    <!-- 聊天面板顶栏 -->
    <div class="chat-header">
      <div class="chat-title">
        <div class="title-icon">{{ agentInfo.name.charAt(0) }}</div>
        <span>{{ chatStore.conversationTitle || agentInfo.description }}</span>
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
        :class="['message', message.role, { streaming: streamingIndex === index }]"
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
        <!-- 打字机光标 -->
        <span v-if="streamingIndex === index" class="typing-cursor"></span>
      </div>

      <!-- Loading 指示器（仅在流式内容还没开始时显示） -->
      <div v-if="chatStore.isLoading && streamingIndex === null" class="loading-indicator">
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
import { ref, nextTick, onMounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, ChatDotRound, CollectionTag } from '@element-plus/icons-vue'
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
const streamingIndex = ref(null)  // 当前正在流式输出的消息索引

// 配置 marked
marked.setOptions({
  breaks: true,
  gfm: true,
})

// 自定义 marked renderer —— 代码块高亮
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

// Markdown 渲染（marked + highlight.js）
const renderMarkdown = (content) => {
  if (!content) return ''
  try {
    return marked.parse(content)
  } catch (e) {
    return content.replace(/</g, '&lt;').replace(/>/g, '&gt;')
  }
}

// 发送消息
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

        // 首条消息：自动设置标题
        if (isFirstMessage && chatStore.conversationId) {
          const title = message.length > 20 ? message.slice(0, 20) + '...' : message
          chatStore.updateTitle(chatStore.conversationId, title, props.agentInfo.name)
        }

        // 刷新对话列表
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
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
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
  flex-shrink: 0;
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
  transition: border-left-color 0.3s ease;
}

/* 流式输出中的消息卡片效果 */
.message.assistant.streaming {
  border-left-color: #667eea;
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

.save-exp-btn {
  margin-left: 4px;
  opacity: 0;
  transition: opacity 0.2s;
  color: #999;
}

.message:hover .save-exp-btn {
  opacity: 1;
}

.save-exp-btn:hover {
  color: #667eea;
}

.message-content {
  line-height: 1.8;
  color: #333;
  font-size: 14px;
  word-break: break-word;
}

/* Markdown 样式 */
.message-content.markdown-body :deep(h1),
.message-content.markdown-body :deep(h2),
.message-content.markdown-body :deep(h3),
.message-content.markdown-body :deep(h4) {
  margin: 16px 0 8px;
  font-weight: 600;
  color: #1a1a1a;
}
.message-content.markdown-body :deep(h1) { font-size: 1.4em; }
.message-content.markdown-body :deep(h2) { font-size: 1.25em; }
.message-content.markdown-body :deep(h3) { font-size: 1.1em; }

.message-content.markdown-body :deep(p) {
  margin: 8px 0;
}

.message-content.markdown-body :deep(ul),
.message-content.markdown-body :deep(ol) {
  padding-left: 24px;
  margin: 8px 0;
}

.message-content.markdown-body :deep(li) {
  margin: 4px 0;
}

.message-content.markdown-body :deep(blockquote) {
  border-left: 4px solid #dcdfe6;
  padding: 8px 16px;
  margin: 8px 0;
  color: #666;
  background: #f9f9f9;
  border-radius: 0 6px 6px 0;
}

.message-content.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
  font-size: 13px;
}

.message-content.markdown-body :deep(th),
.message-content.markdown-body :deep(td) {
  border: 1px solid #ebeef5;
  padding: 8px 12px;
  text-align: left;
}

.message-content.markdown-body :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
}

.message-content.markdown-body :deep(a) {
  color: #667eea;
  text-decoration: none;
}
.message-content.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

/* 代码块 */
.message-content.markdown-body :deep(.hljs-pre) {
  position: relative;
  background: #1e1e2e;
  border-radius: 8px;
  overflow: hidden;
  margin: 12px 0;
}

.message-content.markdown-body :deep(.code-header) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 14px;
  background: #313244;
  font-size: 12px;
}

.message-content.markdown-body :deep(.code-lang) {
  color: #a6adc8;
  font-family: 'Consolas', 'Monaco', monospace;
}

.message-content.markdown-body :deep(.copy-btn) {
  color: #a6adc8;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.message-content.markdown-body :deep(.copy-btn:hover) {
  color: #cdd6f4;
  background: #45475a;
}

.message-content.markdown-body :deep(.hljs) {
  display: block;
  padding: 14px;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

/* 行内代码 */
.message-content.markdown-body :deep(code:not(.hljs)) {
  background: #f0f2f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 13px;
  color: #e83e8c;
}

/* 打字机光标 */
.typing-cursor {
  display: inline-block;
  width: 2px;
  height: 1.1em;
  background: #67c23a;
  margin-left: 2px;
  vertical-align: text-bottom;
  animation: cursorBlink 0.8s infinite;
}

@keyframes cursorBlink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* Loading —— 仅在流式内容还没开始时显示（纯等待状态） */
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
