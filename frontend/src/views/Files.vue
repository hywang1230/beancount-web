<template>
  <div class="page-container">
    <h1 class="page-title">文件管理</h1>
    
    <!-- 文件操作 -->
    <el-card class="mb-4">
      <el-upload
        :before-upload="beforeUpload"
        :http-request="handleUpload"
        :show-file-list="false"
        accept=".beancount,.bean"
      >
        <el-button type="primary">
          <el-icon><Upload /></el-icon>
          上传账本文件
        </el-button>
      </el-upload>
    </el-card>
    
    <!-- 文件列表 -->
    <el-card>
      <template #header>
        <div class="card-header">
          <span>账本文件</span>
          <el-button @click="loadFiles">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>
      
      <el-table :data="files" v-loading="loading">
        <el-table-column prop="name" label="文件名" min-width="200">
          <template #default="{ row }">
            <div class="file-name">
              <el-icon><Document /></el-icon>
              <span>{{ row.name }}</span>
              <el-tag v-if="row.is_main" type="success" size="small">主文件</el-tag>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="size" label="大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.size) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="modified" label="修改时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.modified) }}
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-button
              link
              size="small"
              @click="validateFile(row.name)"
              :loading="validatingFile === row.name"
            >
              验证
            </el-button>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button
              link
              size="small"
              @click="viewFile(row.name)"
            >
              查看
            </el-button>
            
            <el-button
              link
              size="small"
              @click="editFile(row.name)"
            >
              编辑
            </el-button>
            
            <el-button
              link
              size="small"
              @click="downloadFile(row.name)"
            >
              下载
            </el-button>
            
            <el-button
              v-if="!row.is_main"
              link
              size="small"
              @click="deleteFile(row.name)"
              style="color: #f56c6c"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 文件查看/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="80%"
      class="file-dialog"
    >
      <el-input
        v-model="fileContent"
        type="textarea"
        :rows="20"
        :readonly="dialogMode === 'view'"
        placeholder="文件内容"
        style="font-family: monospace; font-size: 14px;"
      />
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button
          v-if="dialogMode === 'edit'"
          type="primary"
          @click="saveFile"
          :loading="saving"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Upload, 
  Refresh, 
  Document 
} from '@element-plus/icons-vue'

import { 
  getFileList,
  getFileContent,
  updateFileContent,
  uploadFile,
  deleteFile as deleteFileApi,
  validateFile as validateFileApi
} from '@/api/files'

const loading = ref(false)
const saving = ref(false)
const validatingFile = ref('')
const files = ref<any[]>([])
const isMobile = ref(false)

const dialogVisible = ref(false)
const dialogMode = ref<'view' | 'edit'>('view')
const dialogTitle = ref('')
const currentFileName = ref('')
const fileContent = ref('')

// 格式化文件大小
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 格式化日期
const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('zh-CN')
}

// 加载文件列表
const loadFiles = async () => {
  loading.value = true
  
  try {
    const result = await getFileList()
    // 后端直接返回FileListResponse，不是包装在data字段中
    const fileData = result.data || result || {}
    files.value = fileData.files || []
  } catch (error) {
    console.error('加载文件列表失败:', error)
    files.value = []
  } finally {
    loading.value = false
  }
}

// 上传前验证
const beforeUpload = (file: File) => {
  const isValidType = file.name.endsWith('.beancount') || file.name.endsWith('.bean')
  
  if (!isValidType) {
    ElMessage.error('只能上传 Beancount 文件(.bean/.beancount)')
    return false
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB')
    return false
  }
  
  return true
}

// 处理上传
const handleUpload = async (options: any) => {
  try {
    await uploadFile(options.file)
    ElMessage.success('文件上传成功')
    loadFiles()
  } catch (error) {
    console.error('文件上传失败:', error)
  }
}

// 查看文件
const viewFile = async (filename: string) => {
  try {
    const result = await getFileContent(filename)
    
    currentFileName.value = filename
    // 后端直接返回内容对象，不是包装在data字段中
    const contentData = result.data || result || {}
    fileContent.value = contentData.content || ''
    dialogMode.value = 'view'
    dialogTitle.value = `查看文件: ${filename}`
    dialogVisible.value = true
    
  } catch (error) {
    console.error('获取文件内容失败:', error)
  }
}

// 编辑文件
const editFile = async (filename: string) => {
  try {
    const result = await getFileContent(filename)
    
    currentFileName.value = filename
    // 后端直接返回内容对象，不是包装在data字段中
    const contentData = result.data || result || {}
    fileContent.value = contentData.content || ''
    dialogMode.value = 'edit'
    dialogTitle.value = `编辑文件: ${filename}`
    dialogVisible.value = true
    
  } catch (error) {
    console.error('获取文件内容失败:', error)
  }
}

// 保存文件
const saveFile = async () => {
  saving.value = true
  
  try {
    await updateFileContent(currentFileName.value, fileContent.value)
    ElMessage.success('文件保存成功')
    dialogVisible.value = false
    loadFiles()
  } catch (error) {
    console.error('保存文件失败:', error)
  } finally {
    saving.value = false
  }
}

// 下载文件
const downloadFile = async (filename: string) => {
  try {
    const result = await getFileContent(filename)
    
    // 后端直接返回内容对象，不是包装在data字段中
    const contentData = result.data || result || {}
    const content = contentData.content || ''
    
    const blob = new Blob([content], { type: 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    
    link.href = url
    link.download = filename
    link.click()
    
    window.URL.revokeObjectURL(url)
    
  } catch (error) {
    console.error('下载文件失败:', error)
  }
}

// 删除文件
const deleteFile = async (filename: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文件 "${filename}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteFileApi(filename)
    ElMessage.success('文件删除成功')
    loadFiles()
    
  } catch (error) {
    if (error === 'cancel') {
      return
    }
    console.error('删除文件失败:', error)
  }
}

// 验证文件
const validateFile = async (filename: string) => {
  validatingFile.value = filename
  
  try {
    const result = await validateFileApi(filename)
    
    // 后端直接返回验证结果对象，不是包装在data字段中
    const validationData = result.data || result || {}
    
    if (validationData.valid) {
      ElMessage.success(`文件验证通过，包含 ${validationData.entries_count || 0} 条记录`)
    } else {
      ElMessage.warning(`文件验证失败，发现 ${validationData.errors_count || 0} 个错误`)
      
      if (validationData.errors && validationData.errors.length > 0) {
        ElMessageBox.alert(
          validationData.errors.join('\n'),
          '验证错误详情',
          { type: 'warning' }
        )
      }
    }
    
  } catch (error) {
    console.error('验证文件失败:', error)
  } finally {
    validatingFile.value = ''
  }
}

// 检测屏幕尺寸
const checkScreenSize = () => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkScreenSize()
  window.addEventListener('resize', checkScreenSize)
  loadFiles()
})

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize)
})
</script>

<style scoped>
.page-title {
  margin-bottom: 24px;
  color: #303133;
  font-size: 24px;
  font-weight: 500;
}

.file-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-dialog :deep(.el-dialog__body) {
  padding: 10px 20px;
}

.file-dialog :deep(.el-textarea__inner) {
  resize: none;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .el-table {
    font-size: 12px;
  }
  
  .el-table .cell {
    padding: 6px 4px;
  }
  
  .file-name {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .file-name .el-tag {
    font-size: 10px;
    padding: 1px 4px;
  }
  
  .el-button--small {
    padding: 4px 8px;
    font-size: 11px;
  }
  
  .file-dialog {
    width: 95% !important;
    margin-top: 5vh !important;
  }
  
  .file-dialog :deep(.el-dialog__body) {
    padding: 10px;
  }
  
  .file-dialog .el-textarea {
    font-size: 12px;
  }
  
  .file-dialog .el-textarea__inner {
    font-size: 12px;
    line-height: 1.4;
  }
}
</style> 