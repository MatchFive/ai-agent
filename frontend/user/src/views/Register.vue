<template>
  <div class="register-page">
    <!-- 动态背景 -->
    <div class="bg-gradient"></div>
    <div class="bg-dots"></div>

    <div class="register-container">
      <div class="register-card">
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
          <p class="brand-desc">创建你的账户</p>
        </div>

        <!-- 表单 -->
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="handleRegister"
          class="register-form"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="form.username"
              placeholder="请输入用户名（3-50字符）"
              prefix-icon="User"
              size="large"
              class="custom-input"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="请输入密码（至少6位）"
              prefix-icon="Lock"
              show-password
              size="large"
              class="custom-input"
            />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              prefix-icon="Lock"
              show-password
              size="large"
              class="custom-input"
            />
          </el-form-item>

          <el-form-item label="邀请码" prop="invite_code">
            <el-input
              v-model="form.invite_code"
              placeholder="请输入邀请码"
              prefix-icon="Ticket"
              size="large"
              class="custom-input"
            />
          </el-form-item>

          <el-form-item class="btn-item">
            <el-button
              type="primary"
              :loading="loading"
              size="large"
              class="register-btn"
              @click="handleRegister"
            >
              <span v-if="!loading">注册</span>
              <span v-else>注册中...</span>
            </el-button>
          </el-form-item>
        </el-form>

        <div class="footer-link">
          已有账号？
          <router-link to="/login">立即登录</router-link>
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
  password: '',
  confirmPassword: '',
  invite_code: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ],
  invite_code: [
    { required: true, message: '请输入邀请码', trigger: 'blur' }
  ]
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await userStore.register({
      username: form.username,
      password: form.password,
      invite_code: form.invite_code
    })
    ElMessage.success('注册成功')
    router.push('/')
  } catch (error) {
    ElMessage.error(error.message || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: #0f172a;
}

.bg-gradient {
  position: absolute;
  inset: 0;
  background: 
    radial-gradient(ellipse 80% 50% at 80% 40%, rgba(139, 92, 246, 0.3), transparent),
    radial-gradient(ellipse 60% 60% at 20% 60%, rgba(99, 102, 241, 0.25), transparent),
    radial-gradient(ellipse 50% 40% at 50% 80%, rgba(139, 92, 246, 0.15), transparent);
  animation: gradientShift 8s ease-in-out infinite alternate;
}

@keyframes gradientShift {
  0% { opacity: 0.8; }
  50% { opacity: 1; }
  100% { opacity: 0.8; }
}

.bg-dots {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px);
  background-size: 24px 24px;
}

.register-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  padding: 20px;
}

.register-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  padding: 44px 40px;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.3);
}

.brand {
  text-align: center;
  margin-bottom: 32px;
}

.brand-icon {
  width: 56px;
  height: 56px;
  margin: 0 auto 16px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(139, 92, 246, 0.3);
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

.register-form :deep(.el-form-item__label) {
  color: #cbd5e1;
  font-size: 13px;
  font-weight: 500;
  padding-bottom: 6px;
}

.register-form :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  box-shadow: none;
  padding: 4px 16px;
  transition: all var(--transition);
}

.register-form :deep(.el-input__wrapper:hover) {
  border-color: rgba(139, 92, 246, 0.3);
}

.register-form :deep(.el-input__wrapper.is-focus) {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.register-form :deep(.el-input__inner) {
  color: #f1f5f9;
  font-size: 14px;
}

.register-form :deep(.el-input__inner::placeholder) {
  color: #475569;
}

.register-form :deep(.el-input__prefix .el-icon) {
  color: #64748b;
}

.register-form :deep(.el-input__suffix .el-icon) {
  color: #64748b;
}

.btn-item {
  margin-top: 24px;
  margin-bottom: 0;
}

.register-btn {
  width: 100%;
  height: 44px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  border: none;
  transition: all var(--transition);
  letter-spacing: 0.02em;
}

.register-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(139, 92, 246, 0.35);
}

.register-btn:active {
  transform: translateY(0);
}

.footer-link {
  text-align: center;
  margin-top: 24px;
  color: #64748b;
  font-size: 14px;
}

.footer-link a {
  color: #a78bfa;
  text-decoration: none;
  font-weight: 500;
  transition: color var(--transition);
}

.footer-link a:hover {
  color: #c4b5fd;
}

:deep(.el-form-item__error) {
  color: #f87171;
  font-size: 12px;
}
</style>
