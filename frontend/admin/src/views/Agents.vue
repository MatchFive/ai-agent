<template>
  <div class="agents-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span class="title">Agent 管理</span>
          <el-button type="primary" @click="openCreateDialog">创建 Agent</el-button>
        </div>
      </template>

      <el-table :data="agents" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" width="180" />
        <el-table-column prop="description" label="描述" min-width="220" show-overflow-tooltip />
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="关联工具" width="200">
          <template #default="{ row }">
            <div class="tool-tags">
              <el-tag
                v-for="tool in row.tools"
                :key="tool.id"
                size="small"
                :type="categoryTagType(tool.category)"
                style="margin: 2px"
              >
                {{ tool.name }}
              </el-tag>
              <span v-if="!row.tools?.length" class="no-tools">未配置</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="工具数" width="70" align="center">
          <template #default="{ row }">
            {{ row.tools?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button type="warning" link size="small" @click="openToolDialog(row)">工具</el-button>
            <el-button
              :type="row.is_active ? 'danger' : 'success'"
              link
              size="small"
              @click="handleToggle(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="formDialogVisible" :title="isEditing ? '编辑 Agent' : '创建 Agent'" width="650px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" :disabled="isEditing" placeholder="Agent 标识名" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" placeholder="Agent 描述" />
        </el-form-item>
        <el-form-item label="系统提示词" prop="system_prompt">
          <el-input
            v-model="form.system_prompt"
            type="textarea"
            :rows="10"
            placeholder="输入系统提示词..."
          />
        </el-form-item>
        <el-form-item label="扩展配置" prop="config_json">
          <el-input
            v-model="form.config_json"
            type="textarea"
            :rows="3"
            placeholder='{"cache_ttl": 900}'
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="formDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSaveForm">保存</el-button>
      </template>
    </el-dialog>

    <!-- 工具配置对话框 -->
    <el-dialog v-model="toolDialogVisible" :title="`配置工具 - ${currentAgent?.name || ''}`" width="500px">
      <div class="tool-dialog-info">
        <span>当前关联 <strong>{{ selectedToolIds.length }}</strong> 个工具</span>
      </div>
      <el-checkbox-group v-model="selectedToolIds" class="tool-checkbox-group">
        <div v-for="cat in toolCategories" :key="cat.name" class="tool-category">
          <div class="category-label">{{ cat.label }}（{{ cat.tools.length }}）</div>
          <el-checkbox
            v-for="tool in cat.tools"
            :key="tool.id"
            :value="tool.id"
            border
            style="margin: 4px 8px 4px 0"
          >
            {{ tool.name }}
            <span class="tool-desc">- {{ tool.description }}</span>
          </el-checkbox>
        </div>
      </el-checkbox-group>
      <template #footer>
        <el-button @click="toolDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="savingTools" @click="handleSaveTools">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminApi } from '../api/auth'

const loading = ref(false)
const saving = ref(false)
const savingTools = ref(false)
const agents = ref([])

// ========== Agent 列表 ==========

async function fetchAgents() {
  loading.value = true
  try {
    const res = await adminApi.getAgents()
    agents.value = res.items || []
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

// ========== 创建/编辑 ==========

const formDialogVisible = ref(false)
const isEditing = ref(false)
const formRef = ref(null)
const form = ref({
  id: null,
  name: '',
  description: '',
  system_prompt: '',
  config_json: '{}'
})

const formRules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入描述', trigger: 'blur' }],
  system_prompt: [{ required: true, message: '请输入系统提示词', trigger: 'blur' }]
}

function openCreateDialog() {
  isEditing.value = false
  form.value = {
    id: null,
    name: '',
    description: '',
    system_prompt: '',
    config_json: '{}'
  }
  formDialogVisible.value = true
}

function openEditDialog(row) {
  isEditing.value = true
  form.value = {
    id: row.id,
    name: row.name,
    description: row.description,
    system_prompt: row.system_prompt,
    config_json: row.config_json || '{}'
  }
  formDialogVisible.value = true
}

async function handleSaveForm() {
  try {
    await formRef.value.validate()
  } catch {
    return
  }

  saving.value = true
  try {
    if (isEditing.value) {
      await adminApi.updateAgent(form.value.id, {
        description: form.value.description,
        system_prompt: form.value.system_prompt,
        config_json: form.value.config_json
      })
      ElMessage.success('保存成功')
    } else {
      await adminApi.createAgent({
        name: form.value.name,
        description: form.value.description,
        system_prompt: form.value.system_prompt,
        config_json: form.value.config_json
      })
      ElMessage.success('创建成功')
    }
    formDialogVisible.value = false
    await fetchAgents()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    saving.value = false
  }
}

// ========== 工具配置 ==========

const toolDialogVisible = ref(false)
const currentAgent = ref(null)
const selectedToolIds = ref([])
const allTools = ref([])

const toolCategories = computed(() => {
  const categoryMap = {
    finance: '金融',
    communication: '通讯',
    file: '文件',
    http: 'HTTP',
    scheduler: '调度',
    general: '通用'
  }
  const groups = {}
  for (const tool of allTools.value) {
    if (!tool.is_active) continue
    const cat = tool.category || 'general'
    if (!groups[cat]) groups[cat] = { name: cat, label: categoryMap[cat] || cat, tools: [] }
    groups[cat].tools.push(tool)
  }
  return Object.values(groups)
})

async function openToolDialog(row) {
  currentAgent.value = row
  selectedToolIds.value = (row.tools || []).map(t => t.id)

  try {
    const res = await adminApi.getTools()
    allTools.value = res.items || []
  } catch (e) {
    ElMessage.error(e.message)
    return
  }

  toolDialogVisible.value = true
}

async function handleSaveTools() {
  savingTools.value = true
  try {
    await adminApi.setAgentTools(currentAgent.value.id, selectedToolIds.value)
    ElMessage.success('工具配置已保存')
    toolDialogVisible.value = false
    await fetchAgents()
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    savingTools.value = false
  }
}

// ========== 操作 ==========

async function handleToggle(row) {
  const action = row.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定要${action} Agent "${row.name}" 吗？`, '确认')
    await adminApi.toggleAgent(row.id)
    ElMessage.success(`Agent 已${action}`)
    await fetchAgents()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message)
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定要删除 Agent "${row.name}" 吗？此操作不可恢复。`, '确认删除', {
      type: 'warning'
    })
    await adminApi.deleteAgent(row.id)
    ElMessage.success('Agent 已删除')
    await fetchAgents()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.message)
  }
}

// ========== 工具函数 ==========

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

const categoryTagType = (cat) => {
  const map = {
    finance: 'warning',
    communication: 'success',
    file: 'primary',
    http: 'info',
    scheduler: 'danger'
  }
  return map[cat] || ''
}

onMounted(() => {
  fetchAgents()
})
</script>

<style scoped>
.agents-page {
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

.tool-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
}

.no-tools {
  color: #999;
  font-size: 12px;
}

.tool-dialog-info {
  margin-bottom: 16px;
  color: #666;
}

.tool-checkbox-group {
  max-height: 400px;
  overflow-y: auto;
}

.tool-category {
  margin-bottom: 16px;
}

.category-label {
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
  font-size: 14px;
}

.tool-desc {
  color: #999;
  font-size: 12px;
  margin-left: 4px;
}
</style>
