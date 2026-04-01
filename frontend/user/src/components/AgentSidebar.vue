<template>
  <div class="agent-sidebar">
    <div v-if="loading" class="sidebar-loading">
      <el-icon :size="18" class="is-loading"><Loading /></el-icon>
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
          <div class="agent-icon">
            {{ agent.name.charAt(0) }}
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
  width: 60px;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: #f0f2f5;
  border-right: 1px solid #e8e8e8;
  padding-top: 8px;
}

.sidebar-loading {
  padding: 12px 0;
  color: #c0c4cc;
}

.agent-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  width: 100%;
  padding: 0 6px;
}

.agent-item {
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.2s;
}

.agent-item:hover .agent-icon {
  background: linear-gradient(135deg, #5a6fe0 0%, #6a4299 100%);
}

.agent-item.active .agent-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
}

.agent-icon {
  width: 42px;
  height: 42px;
  border-radius: 10px;
  background: #e0e3ea;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: 700;
  margin: 0 auto;
  transition: background 0.2s, box-shadow 0.2s;
}
</style>
