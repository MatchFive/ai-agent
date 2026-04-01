<template>
  <div class="conversation-panel">
    <div class="panel-header">
      <span class="panel-title">{{ agentName }}</span>
      <el-button
        text
        size="small"
        :icon="Plus"
        @click="$emit('new')"
        title="新建对话"
      />
    </div>

    <div v-if="chatStore.conversationsLoading" class="panel-loading">
      <el-icon :size="18" class="is-loading"><Loading /></el-icon>
    </div>

    <div v-else-if="chatStore.conversations.length === 0" class="panel-empty">
      <span>暂无对话</span>
    </div>

    <div v-else class="conversation-list">
      <div
        v-for="conv in chatStore.conversations"
        :key="conv.conversation_id"
        :class="['conv-item', { active: modelValue === conv.conversation_id }]"
        @click="$emit('update:modelValue', conv.conversation_id)"
      >
        <div class="conv-info">
          <div class="conv-title">{{ conv.title }}</div>
          <div class="conv-meta">
            {{ formatRelativeTime(conv.updated_at) }} · {{ conv.message_count }} 条消息
          </div>
        </div>
        <el-popconfirm
          title="确定删除此对话？"
          confirm-button-text="删除"
          cancel-button-text="取消"
          @confirm.stop="$emit('delete', conv.conversation_id)"
        >
          <template #reference>
            <el-button
              class="conv-delete"
              text
              size="small"
              :icon="Delete"
              @click.stop
            />
          </template>
        </el-popconfirm>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Plus, Delete, Loading } from '@element-plus/icons-vue'
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
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fafbfc;
  border-right: 1px solid #e8e8e8;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 12px 8px;
  flex-shrink: 0;
}

.panel-title {
  font-size: 13px;
  font-weight: 600;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 140px;
}

.panel-loading,
.panel-empty {
  display: flex;
  justify-content: center;
  padding: 30px 0;
  color: #c0c4cc;
  font-size: 13px;
}

.conversation-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 6px 16px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.conv-item {
  display: flex;
  align-items: center;
  padding: 10px 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  gap: 4px;
}

.conv-item:hover {
  background: #f0f2f5;
}

.conv-item.active {
  background: #667eea10;
}

.conv-info {
  flex: 1;
  min-width: 0;
}

.conv-title {
  font-size: 13px;
  color: #333;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-meta {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}

.conv-delete {
  opacity: 0;
  transition: opacity 0.2s;
  color: #999;
  flex-shrink: 0;
}

.conv-item:hover .conv-delete {
  opacity: 1;
}
</style>
