<template>
  <el-dialog
    v-model="visible"
    width="400px"
    :close-on-click-modal="true"
    :show-close="false"
    class="user-modal"
  >
    <!-- 自定义头部 -->
    <div class="modal-header">
      <button class="close-btn" @click="visible = false">
        <el-icon :size="16"><Close /></el-icon>
      </button>
    </div>

    <div class="user-info">
      <!-- 头像区 -->
      <div class="avatar-section">
        <div class="avatar-bg">
          <el-avatar :size="72" :style="{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }">
            <span style="font-size: 28px; font-weight: 700; color: white;">
              {{ (userStore.user?.username || 'U')[0].toUpperCase() }}
            </span>
          </el-avatar>
        </div>
        <h3 class="username">{{ userStore.user?.username || '未知用户' }}</h3>
        <span class="user-role" :class="userStore.user?.role === 'admin' ? 'admin' : 'user'">
          {{ userStore.user?.role === 'admin' ? '管理员' : '普通用户' }}
        </span>
      </div>

      <!-- 信息卡片 -->
      <div class="info-cards">
        <div class="info-card">
          <span class="info-label">用户名</span>
          <span class="info-value">{{ userStore.user?.username }}</span>
        </div>
        <div class="info-card">
          <span class="info-label">角色</span>
          <span class="info-value">{{ userStore.user?.role === 'admin' ? '管理员' : '普通用户' }}</span>
        </div>
        <div class="info-card">
          <span class="info-label">注册时间</span>
          <span class="info-value">{{ formatDate(userStore.user?.created_at) }}</span>
        </div>
      </div>
    </div>

    <div class="modal-footer">
      <button class="logout-btn" @click="handleLogout">
        <el-icon :size="16"><SwitchButton /></el-icon>
        退出登录
      </button>
    </div>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Close, SwitchButton } from '@element-plus/icons-vue'
import { useUserStore } from '../store/user'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const router = useRouter()
const userStore = useUserStore()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}

const handleLogout = () => {
  visible.value = false
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.user-modal :deep(.el-dialog) {
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.15);
  padding: 0;
}

.user-modal :deep(.el-dialog__header) {
  display: none;
}

.user-modal :deep(.el-dialog__body) {
  padding: 0;
}

.modal-header {
  display: flex;
  justify-content: flex-end;
  padding: 12px 12px 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: #f1f5f9;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e2e8f0;
  color: #334155;
}

.user-info {
  padding: 0 28px;
}

.avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-bottom: 24px;
  border-bottom: 1px solid #f1f5f9;
}

.avatar-bg {
  padding: 4px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366f1, #8b5cf6, #a78bfa);
  margin-bottom: 12px;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.2);
}

.username {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.01em;
}

.user-role {
  font-size: 12px;
  font-weight: 600;
  padding: 3px 12px;
  border-radius: 20px;
  letter-spacing: 0.02em;
}

.user-role.admin {
  background: #fef3c7;
  color: #d97706;
}

.user-role.user {
  background: #eef2ff;
  color: #6366f1;
}

.info-cards {
  padding: 16px 0 4px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #f8fafc;
  border-radius: 10px;
}

.info-label {
  font-size: 13px;
  color: #64748b;
}

.info-value {
  font-size: 13px;
  color: #1e293b;
  font-weight: 500;
}

.modal-footer {
  padding: 16px 28px 24px;
}

.logout-btn {
  width: 100%;
  height: 40px;
  border-radius: 10px;
  border: 1px solid #fecaca;
  background: #fff5f5;
  color: #dc2626;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: #fef2f2;
  border-color: #fca5a5;
}
</style>
