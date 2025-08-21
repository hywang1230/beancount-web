<template>
  <div class="h5-files">
    <!-- 顶部切换视图模式 -->
    <van-sticky>
      <div class="view-mode-section">
        <van-tabs v-model:active="viewMode" @change="onViewModeChange">
          <van-tab title="文件树" name="tree"></van-tab>
          <van-tab title="年份管理" name="yearly"></van-tab>
        </van-tabs>
      </div>
    </van-sticky>

    <!-- 搜索栏 -->
    <van-sticky :offset-top="44">
      <div class="search-section">
        <van-search
          v-model="searchKeyword"
          placeholder="搜索文件"
          @search="onSearch"
        />
      </div>
    </van-sticky>

    <!-- 文件树视图 -->
    <div v-if="viewMode === 'tree'">
      <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
        <div class="file-tree-container">
          <div v-if="fileTreeData" class="tree-summary">
            <van-cell title="文件统计" :value="`共 ${fileTreeData.total_files} 个文件`" />
          </div>
          
          <van-cell-group v-if="fileTreeData">
            <FileTreeNodeComponent 
              :node="fileTreeData.tree" 
              :level="0"
              @node-click="onTreeNodeClick"
              @validate-file="validateTreeFile"
              @edit-file="editTreeFile"
              @download-file="downloadTreeFile"
              @delete-file="deleteTreeFile"
            />
          </van-cell-group>
          
          <van-empty v-if="!fileTreeData" description="暂无文件数据" />
        </div>
      </van-pull-refresh>
    </div>



    <!-- 年份管理视图 -->
    <div v-if="viewMode === 'yearly'">
      <YearlyFileManager @file-changed="onFileChanged" />
    </div>

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

    <!-- 文件查看/编辑对话框 -->
    <van-popup
      v-model:show="showFileDialog"
      position="right"
      :style="{ width: '100%', height: '100%' }"
      :close-on-click-overlay="false"
      teleport="body"
    >
      <div class="file-dialog">
        <van-sticky>
          <van-nav-bar
            :title="dialogTitle"
            left-text="取消"
            :right-text="dialogMode === 'edit' ? '保存' : ''"
            @click-left="showFileDialog = false"
            @click-right="saveFile"
            class="dialog-nav"
          />
        </van-sticky>

        <div class="file-content">
          <van-field
            v-model="fileContent"
            type="textarea"
            :readonly="dialogMode === 'view'"
            placeholder="文件内容"
            autosize
          />
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import {
  deleteFile,
  getFileContent,
  getFileList,
  getFileTree,
  updateFileContent,
  uploadFile,
  validateFile,
  type FileTreeResponse,
  type FileTreeNode,
} from "@/api/files";
import {
  closeToast,
  showConfirmDialog,
  showLoadingToast,
  showToast,
} from "vant";
import { onMounted, ref } from "vue";
import FileTreeNodeComponent from "@/views/h5/components/FileTreeNode.vue";
import YearlyFileManager from "@/views/h5/components/YearlyFileManager.vue";

// 视图状态
const viewMode = ref<"tree" | "yearly">("tree");
const searchKeyword = ref("");
const refreshing = ref(false);
const loading = ref(false);
const finished = ref(false);
const fabOffset = ref({ x: -24, y: -100 });
const showUploadAction = ref(false);

// 文件树数据
const fileTreeData = ref<FileTreeResponse | null>(null);
interface FileItem {
  id: number;
  name: string;
  type: string;
  size: number;
  uploadDate: string;
  is_main?: boolean;
  validating?: boolean;
}

const files = ref<FileItem[]>([]);
const fileList = ref<any[]>([]);
const uploaderRef = ref();

// 新增状态变量
const showFileDialog = ref(false);
const dialogMode = ref<"view" | "edit">("view");
const dialogTitle = ref("");
const currentFileName = ref("");
const fileContent = ref("");
const saving = ref(false);

const uploadActions = [
  { name: "选择文件", icon: "folder-o" },
  { name: "拍照上传", icon: "photograph" },
];


// 保存文件
const saveFile = async () => {
  if (dialogMode.value !== "edit") return;

  try {
    saving.value = true;
    showLoadingToast({
      message: "保存中...",
      forbidClick: true,
    });

    await updateFileContent(currentFileName.value, fileContent.value);

    closeToast();
    showToast("文件保存成功");
    showFileDialog.value = false;

    // 重新加载文件列表
    await loadFiles(true);
  } catch (error) {
    closeToast();
    showToast("保存文件失败");
    // console.error("保存文件失败:", error);
  } finally {
    saving.value = false;
  }
};


const onSearch = () => {
  loadFiles(true);
};

const onRefresh = async () => {
  if (viewMode.value === "tree") {
    await loadFileTree();
  }
  refreshing.value = false;
};

// 视图模式切换
const onViewModeChange = (name: string | number) => {
  viewMode.value = name as "tree" | "yearly";
  if (viewMode.value === "tree" && !fileTreeData.value) {
    loadFileTree();
  }
  // yearly 模式由组件自己处理加载
};

// 文件变化处理函数
const onFileChanged = async () => {
  // 重新加载文件树
  if (viewMode.value === "tree") {
    await loadFileTree();
  }
};


const onUploadSelect = (action: any) => {
  showUploadAction.value = false;

  if (action.name === "选择文件") {
    uploaderRef.value?.chooseFile();
  } else if (action.name === "拍照上传") {
    // 这里可以调用相机功能
    showToast("相机功能开发中");
  }
};

// 上传前验证
const beforeUpload = (file: File) => {
  const isValidType =
    file.name.endsWith(".beancount") || file.name.endsWith(".bean");

  if (!isValidType) {
    showToast("只能上传 Beancount 文件(.bean/.beancount)");
    return false;
  }

  const isLt10M = file.size / 1024 / 1024 < 10;
  if (!isLt10M) {
    showToast("文件大小不能超过 10MB");
    return false;
  }

  return true;
};

const afterRead = async (file: any) => {
  try {
    // 验证文件
    if (!beforeUpload(file.file)) {
      fileList.value = [];
      return;
    }

    showLoadingToast({
      message: "上传中...",
      forbidClick: true,
    });

    // 调用真实上传API
    await uploadFile(file.file);

    closeToast();
    showToast(`${file.file?.name || "文件"} 上传成功`);

    // 重新加载文件列表
    await loadFiles(true);

    // 清空文件列表
    fileList.value = [];
  } catch (error) {
    closeToast();
    showToast("上传失败");
    // console.error("上传文件失败:", error);
    fileList.value = [];
  }
};

const loadFiles = async (isRefresh = false) => {
  try {
    loading.value = true;

    const response = (await getFileList()) as any;

    // 由于API拦截器已经返回response.data，所以response就是实际数据
    const fileData = response || { files: [] };

    // 确保 files 数组存在
    const filesArray = Array.isArray(fileData.files) ? fileData.files : [];

    // 如果没有文件，显示提示信息
    if (filesArray.length === 0) {
      files.value = [];
      finished.value = true;
      return;
    }

    // 转换API数据格式
    const convertedFiles = filesArray.map((file: any, index: number) => {
      // 根据文件扩展名确定类型
      let type = "other";
      const extension = file.name.split(".").pop()?.toLowerCase();
      if (extension === "beancount" || extension === "bean") {
        type = "beancount";
      } else if (extension === "csv") {
        type = "csv";
      } else if (extension === "xlsx" || extension === "xls") {
        type = "excel";
      } else if (extension === "pdf") {
        type = "pdf";
      } else if (
        ["jpg", "jpeg", "png", "gif", "svg"].includes(extension || "")
      ) {
        type = "image";
      }

      return {
        id: index + 1,
        name: file.name,
        type,
        size: file.size,
        uploadDate: file.modified || new Date().toLocaleDateString("en-CA"),
        is_main: file.is_main || false,
        validating: false,
      };
    });

    // 如果有搜索关键词，过滤结果
    let filteredFiles = convertedFiles;
    if (searchKeyword.value.trim()) {
      filteredFiles = convertedFiles.filter((file: any) =>
        file.name.toLowerCase().includes(searchKeyword.value.toLowerCase())
      );
    }

    if (isRefresh) {
      files.value = filteredFiles;
    } else {
      files.value.push(...filteredFiles);
    }

    // 所有文件一次性加载完成
    finished.value = true;
  } catch (error) {
    // console.error("加载文件列表失败:", error);

    // 提供更详细的错误信息
    if (error instanceof TypeError) {
      showToast("数据格式错误，请检查后端API");
    } else {
      showToast("加载文件列表失败");
    }

    // 设置空数组以避免页面崩溃
    files.value = [];
  } finally {
    loading.value = false;
  }
};

// 加载文件树
const loadFileTree = async () => {
  try {
    loading.value = true;
    const response = (await getFileTree()) as any;
    fileTreeData.value = response || null;
  } catch (error) {
    showToast("加载文件树失败");
    console.error("加载文件树失败:", error);
  } finally {
    loading.value = false;
  }
};

// 文件树节点点击事件
const onTreeNodeClick = async (node: FileTreeNode) => {
  await viewTreeFile(node);
};

// 查看树节点文件
const viewTreeFile = async (node: FileTreeNode) => {
  try {
    showLoadingToast({
      message: "加载中...",
      forbidClick: true,
    });

    const result = (await getFileContent(node.path)) as any;
    const contentData = result || {};

    currentFileName.value = node.name;
    fileContent.value = contentData.content || "";
    dialogMode.value = "view";
    dialogTitle.value = `查看文件: ${node.name}`;
    showFileDialog.value = true;

    closeToast();
  } catch (error) {
    closeToast();
    showToast("获取文件内容失败");
    console.error("获取文件内容失败:", error);
  }
};

// 编辑树节点文件
const editTreeFile = async (node: FileTreeNode) => {
  try {
    showLoadingToast({
      message: "加载中...",
      forbidClick: true,
    });

    const result = (await getFileContent(node.path)) as any;
    const contentData = result || {};

    currentFileName.value = node.name;
    fileContent.value = contentData.content || "";
    dialogMode.value = "edit";
    dialogTitle.value = `编辑文件: ${node.name}`;
    showFileDialog.value = true;

    closeToast();
  } catch (error) {
    closeToast();
    showToast("获取文件内容失败");
    console.error("获取文件内容失败:", error);
  }
};

// 验证树节点文件
const validateTreeFile = async (node: FileTreeNode) => {
  try {
    const result = (await validateFile(node.name)) as any;
    const validationData = result || {};

    if (validationData.valid) {
      showToast(
        `文件验证通过，包含 ${validationData.entries_count || 0} 条记录`
      );
    } else {
      showToast(
        `文件验证失败，发现 ${validationData.errors_count || 0} 个错误`
      );
    }
  } catch (error) {
    showToast("验证文件失败");
    console.error("验证文件失败:", error);
  }
};

// 下载树节点文件
const downloadTreeFile = async (node: FileTreeNode) => {
  try {
    showLoadingToast({
      message: "下载中...",
      forbidClick: true,
    });

    const result = (await getFileContent(node.path)) as any;
    const contentData = result || {};
    const content = contentData.content || "";

    const blob = new Blob([content], { type: "text/plain" });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = node.name;
    link.click();

    window.URL.revokeObjectURL(url);

    closeToast();
    showToast(`${node.name} 下载成功`);
  } catch (error) {
    closeToast();
    showToast("下载失败");
    console.error("下载文件失败:", error);
  }
};

// 删除树节点文件
const deleteTreeFile = async (node: FileTreeNode) => {
  if (node.is_main) {
    showToast("不能删除主账本文件");
    return;
  }

  try {
    await showConfirmDialog({
      title: "确认删除",
      message: "确定要删除这个文件吗？",
    });

    showLoadingToast({
      message: "删除中...",
      forbidClick: true,
    });

    await deleteFile(node.name);

    closeToast();
    showToast("删除成功");
    
    // 重新加载文件树
    await loadFileTree();
  } catch (error) {
    closeToast();
    showToast("删除失败");
    console.error("删除文件失败:", error);
  }
};

onMounted(() => {
  // 默认加载文件树
  loadFileTree();
});
</script>

<style scoped>
.h5-files {
  background-color: var(--bg-color-secondary);
  min-height: 100vh;
  transition: background-color 0.3s ease;
  /* 移除自己的滚动，让父容器 main-content 处理 */
  height: 100%;
  overflow: visible;
}

.view-mode-section {
  background-color: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
}

.view-mode-section :deep(.van-tabs) {
  background-color: var(--bg-color);
}

.view-mode-section :deep(.van-tab) {
  color: var(--text-color-secondary);
}

.view-mode-section :deep(.van-tab--active) {
  color: var(--color-primary);
}

.file-tree-container {
  padding: 8px 0;
}

.tree-summary {
  margin-bottom: 8px;
}

.tree-summary :deep(.van-cell) {
  background-color: var(--bg-color);
  font-weight: 500;
}

.search-section {
  background-color: var(--bg-color);
  padding: 8px 16px;
  border-bottom: 1px solid var(--border-color);
}
.search-section :deep(.van-search) {
  background-color: var(--bg-color) !important;
}
.search-section :deep(.van-search__content) {
  background-color: var(--bg-color-secondary);
}

.file-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background-color: var(--bg-color-tertiary);
  border-radius: 50%;
  margin-right: 12px;
  color: var(--color-primary);
}
.file-icon .van-icon {
  color: var(--text-color);
}

:deep(.van-cell-group) {
  margin: 0;
}

.file-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.validate-btn {
  min-width: 50px;
  height: 28px;
  padding: 0 8px;
  font-size: 12px;
}

.file-actions .van-tag {
  font-size: 11px;
  padding: 2px 6px;
  height: 20px;
  line-height: 16px;
}

.file-dialog {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color-secondary);
}

.dialog-nav {
  background-color: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
  z-index: 1;
}

.file-content {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch; /* 解决 iOS 滚动问题 */
  min-height: 0; /* 修复 flex + overflow 在 iOS 上的问题 */
  /* iOS 专门修复 */
  height: calc(100vh - 120px); /* 固定高度而不是依赖flex */
  position: relative;
  touch-action: pan-y; /* 只允许垂直滚动 */
}

.file-content :deep(.van-field__control) {
  font-family: "Monaco", "Menlo", "Ubuntu Mono", monospace;
  font-size: 13px;
  line-height: 1.5;
  background-color: var(--bg-color);
  color: var(--text-color);
}

.file-content :deep(.van-field__control--disabled) {
  background-color: var(--bg-color-tertiary);
  color: var(--text-color-secondary);
}

/* iOS van-field textarea 滚动修复 */
.file-content :deep(.van-field) {
  height: calc(100vh - 180px);
  overflow: hidden;
}

.file-content :deep(.van-field__control) {
  height: 100% !important;
  min-height: calc(100vh - 200px) !important;
  overflow-y: auto !important;
  -webkit-overflow-scrolling: touch !important;
  resize: none !important;
  /* iOS Safari 特定修复 */
  -webkit-appearance: none;
  appearance: none;
  border-radius: 0;
  touch-action: pan-y;
  position: relative;
}
</style>
