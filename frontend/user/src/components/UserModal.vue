<template>
  <el-dialog
    v-model="visible"
    title="个人信息"
    width="420px"
    :close-on-click-modal="true"
    class="user-modal"
  >
    <div class="user-info">
      <div class="user-avatar-section">
        <el-avatar :size="64" :style="{ background: '#667eea' }">
          <el-icon :size="32"><User /></el-icon>
        </el-avatar>
        <h3 class="username">{{ userStore.user?.username || '未知用户' }}</h3>
        <el-tag
          :type="userStore.user?.role === 'admin' ? 'danger' : 'info'"
          size="small"
        >
          {{ userStore.user?.role === 'admin' ? '管理员' : '普通用户' }}
        </el-tag>
      </div>

      <el-descriptions :column="1" border size="small" class="user-details">
        <el-descriptions-item label="用户名">
          {{ userStore.user?.username }}
        </el-descriptions-item>
        <el-descriptions-item label="角色">
          {{ userStore.user?.role === 'admin' ? '管理员' : '普通用户' }}
        </el-descriptions-item>
        <el-descriptions-item label="注册时间">
          {{ formatDate(userStore.user?.created_at) }}
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <template #footer>
      <div class="modal-footer">
        <el-button type="danger" plain @click="handleLogout">
          退出登录
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User } from '@element-plus/icons-vue'
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
.user-modal :deep(.el-dialog__header) {
  padding: 16px 20px;
  margin: 0;
  border-bottom: 1px solid #f0f0f0;
}

.user-modal :deep(.el-dialog__body) {
  padding: 20px;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.user-avatar-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-bottom: 20px;
}

.username {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.user-details {
  width: 100%;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
}
</style>
