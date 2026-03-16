<template>
  <div class="home-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>AI-Agent</h1>
          <div class="user-info">
            <span>{{ userStore.user?.username }}</span>
            <el-button type="danger" size="small" @click="handleLogout">
              退出登录
            </el-button>
          </div>
        </div>
      </el-header>

      <el-main>
        <el-card class="welcome-card">
          <h2>欢迎使用 AI-Agent</h2>
          <p>您已成功登录系统</p>
          <div class="info-section">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="用户名">
                {{ userStore.user?.username }}
              </el-descriptions-item>
              <el-descriptions-item label="角色">
                {{ userStore.user?.role === 'admin' ? '管理员' : '普通用户' }}
              </el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag type="success">正常</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="注册时间">
                {{ formatDate(userStore.user?.created_at) }}
              </el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()

onMounted(() => {
  if (!userStore.user) {
    userStore.fetchUser()
  }
})

function handleLogout() {
  userStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.el-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
}

.header-content {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 15px;
}

.el-main {
  padding: 40px;
}

.welcome-card {
  max-width: 600px;
  margin: 0 auto;
}

.welcome-card h2 {
  margin-bottom: 10px;
  color: #333;
}

.welcome-card p {
  color: #666;
  margin-bottom: 20px;
}

.info-section {
  margin-top: 20px;
}
</style>
