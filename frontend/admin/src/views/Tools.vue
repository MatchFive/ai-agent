<template>
  <div class="tools-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">工具管理</span>
          <div class="actions">
            <el-radio-group v-model="categoryFilter" size="small" @change="fetchTools">
              <el-radio-button :value="''">全部</el-radio-button>
              <el-radio-button value="finance">金融</el-radio-button>
              <el-radio-button value="communication">通讯</el-radio-button>
              <el-radio-button value="file">文件</el-radio-button>
              <el-radio-button value="http">HTTP</el-radio-button>
              <el-radio-button value="scheduler">调度</el-radio-button>
            </el-radio-group>
            <el-button type="primary" :loading="reloading" @click="handleReload">
              重新扫描
            </el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredTools" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" width="200" />
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column prop="category" label="分类" width="100">
          <template #default="{ row }">
            <el-tag :type="categoryTagType(row.category)" size="small">{{ categoryLabel(row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="handler_class" label="Handler 类" min-width="180" show-overflow-tooltip />
        <el-table-column prop="handler_method" label="方法" width="140" />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="同步" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.synced ? 'success' : 'warning'" size="small">
              {{ row.synced ? '已同步' : '未同步' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button
              :type="row.is_active ? 'danger' : 'success'"
              link
              size="small"
              @click="handleToggle(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑工具" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="名称">
          <el-input :value="editForm.name" disabled />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="editForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="editForm.category" style="width: 100%">
            <el-option label="通用" value="general" />
            <el-option label="金融" value="finance" />
            <el-option label="通讯" value="communication" />
            <el-option label="文件" value="file" />
            <el-option label="HTTP" value="http" />
            <el-option label="调度" value="scheduler" />
          </el-select>
        </el-form-item>
        <el-form-item label="参数">
          <el-input v-model="editForm.parameters_json" type="textarea" :rows="6" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi } from '../api/auth'

const loading = ref(false)
const reloading = ref(false)
const saving = ref(false)
const tools = ref([])
const categoryFilter = ref('')

const filteredTools = computed(() => {
  if (!categoryFilter.value) return tools.value
  return tools.value.filter(t => t.category === categoryFilter.value)
})

const categoryMap = {
  finance: { label: '金融', type: 'warning' },
  communication: { label: '通讯', type: 'success' },
  file: { label: '文件', type: 'primary' },
  http: { label: 'HTTP', type: 'info' },
  scheduler: { label: '调度', type: 'danger' },
  general: { label: '通用', type: '' }
}

function categoryLabel(cat) {
  return categoryMap[cat]?.label || cat
}

function categoryTagType(cat) {
  return categoryMap[cat]?.type || ''
}

async function fetchTools() {
  loading.value = true
  try {
    const res = await adminApi.getTools()
    tools.value = res.items || []
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function handleReload() {
  reloading.value = true
  try {
    const res = await adminApi.reloadTools()
    ElMessage.success(res.message)
    await fetchTools()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    reloading.value = false
  }
}

const editDialogVisible = ref(false)
const editForm = ref({
  id: null,
  name: '',
  description: '',
  category: '',
  parameters_json: ''
})

function openEditDialog(row) {
  editForm.value = {
    id: row.id,
    name: row.name,
    description: row.description,
    category: row.category,
    parameters_json: row.parameters_json
  }
  editDialogVisible.value = true
}

async function handleSave() {
  saving.value = true
  try {
    await adminApi.updateTool(editForm.value.id, {
      description: editForm.value.description,
      category: editForm.value.category,
      parameters_json: editForm.value.parameters_json
    })
    ElMessage.success('保存成功')
    editDialogVisible.value = false
    await fetchTools()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

async function handleToggle(row) {
  const action = row.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定要${action}工具 "${row.name}" 吗？`, '确认')
    await adminApi.toggleTool(row.id)
    ElMessage.success(`工具已${action}`)
    await fetchTools()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message)
  }
}

onMounted(() => {
  fetchTools()
})
</script>

<style scoped>
.tools-page {
  max-width: 1400px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header .title {
  font-size: 16px;
  font-weight: 600;
}

.card-header .actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
