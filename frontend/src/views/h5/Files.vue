<template>
  <div class="h5-files">
    <!-- 搜索栏 -->
    <van-sticky>
      <div class="search-section">
        <van-search
          v-model="searchKeyword"
          placeholder="搜索文件"
          @search="onSearch"
        />
      </div>
    </van-sticky>

    <!-- 文件列表 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="onLoad"
      >
        <van-cell-group>
          <van-swipe-cell
            v-for="file in files"
            :key="file.id"
          >
            <van-cell
              :title="file.name"
              :label="formatFileInfo(file)"
              is-link
              @click="viewFile(file)"
            >
              <template #icon>
                <div class="file-icon">
                  <van-icon :name="getFileIcon(file.type)" />
                </div>
              </template>
            </van-cell>
            
            <!-- 滑动操作 -->
            <template #right>
              <van-button
                square
                type="primary"
                text="下载"
                @click="downloadFile(file)"
              />
              <van-button
                square
                type="danger"
                text="删除"
                @click="deleteFile(file)"
              />
            </template>
          </van-swipe-cell>
        </van-cell-group>
      </van-list>
    </van-pull-refresh>

    <!-- 上传按钮 -->
    <van-floating-bubble
      v-model:offset="fabOffset"
      icon="plus"
      @click="showUploadAction = true"
    />

    <!-- 上传选项 -->
    <van-action-sheet
      v-model:show="showUploadAction"
      :actions="uploadActions"
      @select="onUploadSelect"
      cancel-text="取消"
    />

    <!-- 文件上传 -->
    <van-uploader
      ref="uploaderRef"
      v-model="fileList"
      :after-read="afterRead"
      :max-count="1"
      :show-upload="false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog, showLoadingToast, closeToast } from 'vant'

const router = useRouter()

const searchKeyword = ref('')
const refreshing = ref(false)
const loading = ref(false)
const finished = ref(false)
const fabOffset = ref({ x: -24, y: -100 })
const showUploadAction = ref(false)
interface FileItem {
  id: number
  name: string
  type: string
  size: number
  uploadDate: string
}

const files = ref<FileItem[]>([])
const fileList = ref<any[]>([])
const uploaderRef = ref()

const uploadActions = [
  { name: '选择文件', icon: 'folder-o' },
  { name: '拍照上传', icon: 'photograph' }
]

const formatFileInfo = (file: any) => {
  const sizeText = formatFileSize(file.size)
  const dateText = new Date(file.uploadDate).toLocaleDateString('zh-CN')
  return `${sizeText} • ${dateText}`
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getFileIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    'beancount': 'bill-o',
    'csv': 'records',
    'excel': 'records',
    'pdf': 'description',
    'image': 'photo-o',
    'other': 'folder-o'
  }
  return iconMap[type] || 'folder-o'
}

const viewFile = (file: any) => {
  router.push(`/h5/files/${file.id}`)
}

const downloadFile = async (file: FileItem) => {
  try {
    showLoadingToast({
      message: '下载中...',
      forbidClick: true
    })
    
    // 模拟下载
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    closeToast()
    showToast(`${file.name} 下载成功`)
  } catch (error) {
    closeToast()
    showToast('下载失败')
    console.error('下载文件失败:', error)
  }
}

const deleteFile = async (file: any) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: '确定要删除这个文件吗？'
    })
    
    // 这里应该调用API删除文件
    const index = files.value.findIndex(f => f.id === file.id)
    if (index > -1) {
      files.value.splice(index, 1)
    }
    
    showToast('删除成功')
  } catch {
    // 用户取消删除
  }
}

const onSearch = () => {
  loadFiles(true)
}

const onRefresh = async () => {
  await loadFiles(true)
  refreshing.value = false
}

const onLoad = async () => {
  await loadFiles(false)
}

const onUploadSelect = (action: any) => {
  showUploadAction.value = false
  
  if (action.name === '选择文件') {
    uploaderRef.value?.chooseFile()
  } else if (action.name === '拍照上传') {
    // 这里可以调用相机功能
    showToast('相机功能开发中')
  }
}

const afterRead = async (file: any) => {
  try {
    showLoadingToast({
      message: '上传中...',
      forbidClick: true
    })
    
    // 模拟上传
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    closeToast()
    showToast(`${file.file?.name || '文件'} 上传成功`)
    
    // 重新加载文件列表
    await loadFiles(true)
    
    // 清空文件列表
    fileList.value = []
  } catch (error) {
    closeToast()
    showToast('上传失败')
    console.error('上传文件失败:', error)
  }
}

const loadFiles = async (isRefresh = false) => {
  try {
    loading.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    const mockData = [
      {
        id: 1,
        name: 'accounts.beancount',
        type: 'beancount',
        size: 15420,
        uploadDate: '2024-01-15'
      },
      {
        id: 2,
        name: 'transactions_2024_01.csv',
        type: 'csv',
        size: 8540,
        uploadDate: '2024-01-14'
      },
      {
        id: 3,
        name: 'monthly_report.pdf',
        type: 'pdf',
        size: 245680,
        uploadDate: '2024-01-10'
      },
      {
        id: 4,
        name: 'backup_2024_01.beancount',
        type: 'beancount',
        size: 45120,
        uploadDate: '2024-01-08'
      }
    ]
    
    if (isRefresh) {
      files.value = mockData
    } else {
      files.value.push(...mockData)
    }
    
    finished.value = files.value.length >= 20 // 假设最多20个文件
  } catch (error) {
    console.error('加载文件列表失败:', error)
    showToast('加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadFiles(true)
})
</script>

<style scoped>
.h5-files {
  background-color: #f7f8fa;
  min-height: 100vh;
}

.search-section {
  background-color: white;
  padding: 8px 16px;
  border-bottom: 1px solid #ebedf0;
}

.file-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background-color: #f7f8fa;
  border-radius: 50%;
  margin-right: 12px;
  color: #1989fa;
}

:deep(.van-cell-group) {
  margin: 0;
}
</style>