<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon users">
              <el-icon size="32"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.users?.total || 0 }}</div>
              <div class="stat-label">用户总数</div>
            </div>
          </div>
          <div class="stat-detail">
            活跃: {{ stats.users?.active || 0 }} | 禁用: {{ stats.users?.inactive || 0 }}
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon codes">
              <el-icon size="32"><Ticket /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.invite_codes?.total || 0 }}</div>
              <div class="stat-label">邀请码总数</div>
            </div>
          </div>
          <div class="stat-detail">
            已使用: {{ stats.invite_codes?.used || 0 }} | 未使用: {{ stats.invite_codes?.unused || 0 }}
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon rate">
              <el-icon size="32"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ usedRate }}%</div>
              <div class="stat-label">邀请码使用率</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="info-card" style="margin-top: 20px;">
      <template #header>
        <span>系统信息</span>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="管理员">
          {{ adminStore.user?.username }}
        </el-descriptions-item>
        <el-descriptions-item label="登录时间">
          {{ formatDate(new Date()) }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAdminStore } from '../store/admin'
import { adminApi } from '../api/auth'

const adminStore = useAdminStore()
const stats = ref({})

const usedRate = computed(() => {
  const total = stats.value.invite_codes?.total || 0
  const used = stats.value.invite_codes?.used || 0
  if (total === 0) return 0
  return Math.round((used / total) * 100)
})

async function fetchStats() {
  try {
    stats.value = await adminApi.getStats()
  } catch (error) {
    ElMessage.error('获取统计数据失败')
  }
}

function formatDate(date) {
  return date.toLocaleString('zh-CN')
}

onMounted(() => {
  fetchStats()
})
</script>

<style scoped>
.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-icon.users {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.codes {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.rate {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  color: #999;
  margin-top: 5px;
}

.stat-detail {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
  color: #666;
  font-size: 14px;
}

.info-card {
  margin-top: 20px;
}
</style>
