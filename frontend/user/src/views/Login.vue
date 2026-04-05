<template>
  <div class="login-page">
    <!-- 动态背景 -->
    <div class="bg-gradient"></div>
    <div class="bg-dots"></div>

    <div class="login-container">
      <div class="login-card">
        <!-- Logo区域 -->
        <div class="brand">
          <div class="brand-icon">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
              <rect width="32" height="32" rx="8" fill="url(#grad)" />
              <path d="M10 12L16 8L22 12V20L16 24L10 20V12Z" stroke="white" stroke-width="1.5" fill="none"/>
              <circle cx="16" cy="16" r="3" fill="white" opacity="0.9"/>
              <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="32" y2="32">
                  <stop stop-color="#6366f1"/>
                  <stop offset="1" stop-color="#8b5cf6"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h1 class="brand-name">AI Agent</h1>
          <p class="brand-desc">智能对话，从这里开始</p>
        </div>

        <!-- 表单 -->
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="handleLogin"
          class="login-form"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名"
              prefix-icon="User"
              size="large"
              class="custom-input"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              show-password
              size="large"
              class="custom-input"
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item class="btn-item">
            <el-button
              type="primary"
              :loading="loading"
              size="large"
              class="login-btn"
              @click="handleLogin"
            >
              <span v-if="!loading">登录</span>
              <span v-else>登录中...</span>
            </el-button>
          </el-form-item>
        </el-form>

        <div class="footer-link">
          还没有账号？
          <router-link to="/register">立即注册</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ]
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.login(form)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    ElMessage.error(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: #0f172a;
}

/* 动态渐变背景 */
.bg-gradient {
  position: absolute;
  inset: 0;
  background: 
    radial-gradient(ellipse 80% 50% at 20% 40%, rgba(99, 102, 241, 0.3), transparent),
    radial-gradient(ellipse 60% 60% at 80% 60%, rgba(139, 92, 246, 0.25), transparent),
    radial-gradient(ellipse 50% 40% at 50% 20%, rgba(99, 102, 241, 0.15), transparent);
  animation: gradientShift 8s ease-in-out infinite alternate;
}

@keyframes gradientShift {
  0% { opacity: 0.8; }
  50% { opacity: 1; }
  100% { opacity: 0.8; }
}

/* 点阵背景 */
.bg-dots {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px);
  background-size: 24px 24px;
}

.login-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  padding: 20px;
}

.login-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  padding: 48px 40px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.3);
}

/* 品牌 */
.brand {
  text-align: center;
  margin-bottom: 36px;
}

.brand-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
}

.brand-name {
  font-size: 24px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: -0.02em;
}

.brand-desc {
  font-size: 14px;
  color: #94a3b8;
  margin-top: 6px;
}

/* 表单 */
.login-form :deep(.el-form-item__label) {
  color: #cbd5e1;
  font-size: 13px;
  font-weight: 500;
  padding-bottom: 6px;
}

.login-form :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  box-shadow: none;
  padding: 4px 16px;
  transition: all var(--transition);
}

.login-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(99, 102, 241, 0.3);
}

.login-form :deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.login-form :deep(.el-input__inner) {
  color: #f1f5f9;
  font-size: 14px;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: #475569;
}

.login-form :deep(.el-input__prefix .el-icon) {
  color: #64748b;
}

.login-form :deep(.el-input__suffix .el-icon) {
  color: #64748b;
}

/* 按钮 */
.btn-item {
  margin-top: 28px;
  margin-bottom: 0;
}

.login-btn {
  width: 100%;
  height: 44px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
  transition: all var(--transition);
  letter-spacing: 0.02em;
}

.login-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(99, 102, 241, 0.35);
}

.login-btn:active {
  transform: translateY(0);
}

/* 底部链接 */
.footer-link {
  text-align: center;
  margin-top: 24px;
  color: #64748b;
  font-size: 14px;
}

.footer-link a {
  color: #818cf8;
  text-decoration: none;
  font-weight: 500;
  transition: color var(--transition);
}

.footer-link a:hover {
  color: #a5b4fc;
}

/* 错误提示样式覆盖 */
:deep(.el-form-item__error) {
  color: #f87171;
  font-size: 12px;
}
</style>
