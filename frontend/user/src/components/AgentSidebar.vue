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
          effect="dark"
        >
          <div class="agent-icon">
            {{ agent.name.charAt(0) }}
          </div>
        </el-tooltip>
        <!-- 活跃指示条 -->
        <div v-if="modelValue === agent.name" class="active-indicator"></div>
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
  width: 64px;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  background: linear-gradient(180deg, #1e1b4b 0%, #0f172a 100%);
  padding-top: 12px;
  position: relative;
}

.sidebar-loading {
  padding: 12px 0;
  color: #6366f1;
}

.agent-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  padding: 0 10px;
}

.agent-item {
  position: relative;
  cursor: pointer;
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.agent-item:hover .agent-icon {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.agent-item.active .agent-icon {
  background: linear-gradient(135deg, #6366f1 0%, #a78bfa 100%);
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.4);
}

.active-indicator {
  position: absolute;
  left: -10px;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 24px;
  background: #6366f1;
  border-radius: 0 3px 3px 0;
  box-shadow: 0 0 8px rgba(99, 102, 241, 0.6);
}

.agent-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  font-weight: 700;
  margin: 0 auto;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.agent-item:hover .agent-icon,
.agent-item.active .agent-icon {
  color: #fff;
  border-color: transparent;
}
</style>
