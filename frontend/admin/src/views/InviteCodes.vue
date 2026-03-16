<template>
  <div class="invite-codes">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>邀请码管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            生成邀请码
          </el-button>
        </div>
      </template>

      <!-- 筛选 -->
      <div class="filter-bar">
        <el-radio-group v-model="filter" @change="fetchCodes">
          <el-radio-button :value="null">全部</el-radio-button>
          <el-radio-button :value="false">未使用</el-radio-button>
          <el-radio-button :value="true">已使用</el-radio-button>
        </el-radio-group>
      </div>

      <!-- 表格 -->
      <el-table :data="codes" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="code" label="邀请码">
          <template #default="{ row }">
            <div class="code-cell">
              <code>{{ row.code }}</code>
              <el-button
                size="small"
                text
                @click="copyCode(row.code)"
              >
                复制
              </el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="is_used" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_used ? 'danger' : 'success'">
              {{ row.is_used ? '已使用' : '未使用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="used_by" label="使用者" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="used_at" label="使用时间" width="180">
          <template #default="{ row }">
            {{ row.used_at ? formatDate(row.used_at) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_used"
              type="danger"
              size="small"
              text
              @click="handleDelete(row)"
            >
              删除
            </el-button>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="page"
          :page-size="20"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="fetchCodes"
        />
      </div>
    </el-card>

    <!-- 生成邀请码对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="生成邀请码"
      width="400px"
    >
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="生成数量">
          <el-input-number
            v-model="createForm.count"
            :min="1"
            :max="100"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">
          生成
        </el-button>
      </template>
    </el-dialog>

    <!-- 生成结果对话框 -->
    <el-dialog
      v-model="showResultDialog"
      title="邀请码已生成"
      width="500px"
    >
      <div class="result-list">
        <div v-for="code in createdCodes" :key="code.code" class="result-item">
          <code>{{ code.code }}</code>
          <el-button size="small" text @click="copyCode(code.code)">复制</el-button>
        </div>
      </div>
      <template #footer>
        <el-button type="primary" @click="showResultDialog = false">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi } from '../api/auth'

const loading = ref(false)
const codes = ref([])
const page = ref(1)
const total = ref(0)
const filter = ref(null)

const showCreateDialog = ref(false)
const createLoading = ref(false)
const createForm = reactive({ count: 1 })

const showResultDialog = ref(false)
const createdCodes = ref([])

async function fetchCodes() {
  loading.value = true
  try {
    const params = { page: page.value, page_size: 20 }
    if (filter.value !== null) {
      params.is_used = filter.value
    }
    const response = await adminApi.getInviteCodes(params)
    codes.value = response.items
    total.value = response.total
  } catch (error) {
    ElMessage.error('获取邀请码列表失败')
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  createLoading.value = true
  try {
    createdCodes.value = await adminApi.createInviteCodes(createForm)
    showCreateDialog.value = false
    showResultDialog.value = true
    fetchCodes()
    ElMessage.success(`成功生成 ${createdCodes.value.length} 个邀请码`)
  } catch (error) {
    ElMessage.error(error.message || '生成失败')
  } finally {
    createLoading.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('确定要删除这个邀请码吗？', '确认删除', {
      type: 'warning'
    })
    await adminApi.deleteInviteCode(row.id)
    ElMessage.success('删除成功')
    fetchCodes()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除失败')
    }
  }
}

function copyCode(code) {
  navigator.clipboard.writeText(code)
  ElMessage.success('已复制到剪贴板')
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchCodes()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-bar {
  margin-bottom: 20px;
}

.code-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.code-cell code {
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: monospace;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.text-muted {
  color: #999;
}

.result-list {
  max-height: 300px;
  overflow-y: auto;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.result-item:last-child {
  border-bottom: none;
}

.result-item code {
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
  font-family: monospace;
}
</style>
