<template>
  <div class="conversation-panel">
    <div class="panel-header">
      <div class="header-left">
        <span class="panel-title">{{ agentName }}</span>
        <span class="conv-count" v-if="chatStore.conversations.length > 0">
          {{ chatStore.conversations.length }}
        </span>
      </div>
      <button class="new-btn" @click="$emit('new')" title="新建对话">
        <el-icon :size="16"><Plus /></el-icon>
      </button>
    </div>

    <!-- 搜索框 -->
    <div class="search-box" v-if="chatStore.conversations.length > 0">
      <el-icon :size="14" class="search-icon"><Search /></el-icon>
      <input
        type="text"
        placeholder="搜索对话..."
        v-model="searchQuery"
        class="search-input"
      />
    </div>

    <div v-if="chatStore.conversationsLoading" class="panel-loading">
      <el-icon :size="18" class="is-loading"><Loading /></el-icon>
    </div>

    <div v-else-if="filteredConversations.length === 0 && chatStore.conversations.length > 0" class="panel-empty">
      <span>没有匹配的对话</span>
    </div>

    <div v-else-if="chatStore.conversations.length === 0" class="panel-empty">
      <div class="empty-icon">
        <el-icon :size="32"><ChatDotRound /></el-icon>
      </div>
      <span>暂无对话</span>
      <button class="empty-create" @click="$emit('new')">开始新对话</button>
    </div>

    <div v-else class="conversation-list">
      <div
        v-for="conv in filteredConversations"
        :key="conv.conversation_id"
        :class="['conv-item', { active: modelValue === conv.conversation_id }]"
        @click="$emit('update:modelValue', conv.conversation_id)"
      >
        <div class="conv-icon">
          <el-icon :size="14"><ChatDotRound /></el-icon>
        </div>
        <div class="conv-info">
          <div class="conv-title">{{ conv.title }}</div>
          <div class="conv-meta">
            {{ formatRelativeTime(conv.updated_at) }}
          </div>
        </div>
        <el-popconfirm
          title="确定删除此对话？"
          confirm-button-text="删除"
          cancel-button-text="取消"
          @confirm.stop="$emit('delete', conv.conversation_id)"
        >
          <template #reference>
            <button class="conv-delete" @click.stop>
              <el-icon :size="14"><Delete /></el-icon>
            </button>
          </template>
        </el-popconfirm>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Plus, Delete, Loading, Search, ChatDotRound } from '@element-plus/icons-vue'
import { useChatStore } from '../store/chat'

defineProps({
  agentName: {
    type: String,
    required: true
  },
  modelValue: {
    type: String,
    default: null
  }
})

defineEmits(['update:modelValue', 'new', 'delete'])

const chatStore = useChatStore()
const searchQuery = ref('')

const filteredConversations = computed(() => {
  if (!searchQuery.value.trim()) return chatStore.conversations
  const query = searchQuery.value.toLowerCase()
  return chatStore.conversations.filter(c =>
    c.title?.toLowerCase().includes(query)
  )
})

function formatRelativeTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}
</script>

<style scoped>
.conversation-panel {
  width: 260px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fafbfd;
  border-right: 1px solid #e8ecf1;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 14px 12px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 140px;
}

.conv-count {
  font-size: 11px;
  font-weight: 600;
  color: #6366f1;
  background: #eef2ff;
  padding: 1px 7px;
  border-radius: 10px;
}

.new-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s;
}

.new-btn:hover {
  background: #6366f1;
  border-color: #6366f1;
  color: white;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

/* 搜索框 */
.search-box {
  margin: 0 14px 8px;
  position: relative;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
}

.search-input {
  width: 100%;
  height: 32px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0 10px 0 32px;
  font-size: 13px;
  background: white;
  color: #1e293b;
  outline: none;
  transition: all 0.2s;
}

.search-input::placeholder {
  color: #94a3b8;
}

.search-input:focus {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

/* 加载和空状态 */
.panel-loading {
  display: flex;
  justify-content: center;
  padding: 30px 0;
  color: #6366f1;
}

.panel-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #94a3b8;
  font-size: 13px;
  gap: 8px;
}

.empty-icon {
  color: #cbd5e1;
  margin-bottom: 4px;
}

.empty-create {
  margin-top: 8px;
  color: #6366f1;
  background: none;
  border: none;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 6px;
  transition: all 0.2s;
}

.empty-create:hover {
  background: #eef2ff;
}

/* 对话列表 */
.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 4px 8px 16px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.conv-item {
  display: flex;
  align-items: center;
  padding: 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  gap: 10px;
  position: relative;
}

.conv-item:hover {
  background: #f1f5f9;
}

.conv-item.active {
  background: #eef2ff;
}

.conv-item.active .conv-title {
  color: #4338ca;
  font-weight: 600;
}

.conv-item.active .conv-icon {
  color: #6366f1;
  background: #e0e7ff;
}

.conv-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: #f1f5f9;
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.conv-info {
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 13px;
  color: #334155;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.conv-meta {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
}

.conv-delete {
  opacity: 0;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #94a3b8;
  flex-shrink: 0;
  transition: all 0.2s;
}

.conv-item:hover .conv-delete {
  opacity: 1;
}

.conv-delete:hover {
  background: #fee2e2;
  color: #ef4444;
}
</style>
