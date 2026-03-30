<template>
  <div class="agent-sidebar">
    <div class="sidebar-title">助手列表</div>
    <div v-if="loading" class="sidebar-loading">
      <el-icon :size="20" class="is-loading"><Loading /></el-icon>
    </div>
    <div v-else class="agent-list">
      <div
        v-for="agent in agents"
        :key="agent.name"
        :class="['agent-item', { active: modelValue === agent.name }]"
        @click="$emit('update:modelValue', agent.name)"
      >
        <el-tooltip
          :content="agent.description"
          placement="right"
          :show-after="300"
          :offset="8"
        >
          <div class="agent-card">
            <div class="agent-icon">
              {{ agent.name.charAt(0) }}
            </div>
            <span class="agent-name">{{ agent.description }}</span>
          </div>
        </el-tooltip>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Loading } from '@element-plus/icons-vue'

defineProps({
  agents: {
    type: Array,
    default: () => []
  },
  modelValue: {
    type: String,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.agent-sidebar {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fafbfc;
  border-right: 1px solid #e8e8e8;
}

.sidebar-title {
  padding: 16px 16px 12px;
  font-size: 12px;
  font-weight: 600;
  color: #909399;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.sidebar-loading {
  display: flex;
  justify-content: center;
  padding: 20px;
  color: #c0c4cc;
}

.agent-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.agent-item {
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
}

.agent-item:hover .agent-card {
  background: #f0f2f5;
}

.agent-item.active .agent-card {
  background: #667eea10;
}

.agent-item.active {
  border-left: 3px solid #667eea;
  padding-left: 5px;
}

.agent-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  transition: background 0.2s;
}

.agent-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 16px;
  font-weight: 700;
}

.agent-name {
  font-size: 13px;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
