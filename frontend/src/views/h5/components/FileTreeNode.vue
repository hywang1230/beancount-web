<template>
  <div class="file-tree-node">
    <!-- 当前节点 -->
    <van-swipe-cell>
      <van-cell 
        :title="node.name"
        :label="getFileInfo()"
        :is-link="!node.error"
        :class="getNodeClass()"
        :style="getNodeStyle()"
        @click="handleNodeClick"
      >
        <template #icon>
          <div class="tree-node-icon">
            <van-icon 
              v-if="hasChildren()" 
              :name="expanded ? 'arrow-down' : 'arrow'" 
              class="expand-icon"
              @click.stop="toggleExpand"
            />
            <van-icon 
              :name="getFileIcon()" 
              :class="{ 'main-file-icon': node.is_main }"
            />
          </div>
        </template>
        
        <template #right-icon>
          <div class="file-node-actions">
            <van-tag v-if="node.is_main" type="success">主文件</van-tag>
            <van-tag v-if="node.error" type="danger">错误</van-tag>
            <van-button
              size="small"
              type="primary"
              plain
              :loading="validating"
              @click.stop="handleValidate"
              class="validate-btn"
            >
              验证
            </van-button>
          </div>
        </template>
      </van-cell>

      <!-- 滑动操作 -->
      <template #right>
        <van-button
          square
          type="primary"
          text="编辑"
          @click="handleEdit"
        />
        <van-button
          square
          type="success"
          text="下载"
          @click="handleDownload"
        />
        <van-button
          v-if="!node.is_main"
          square
          type="danger"
          text="删除"
          @click="handleDelete"
        />
      </template>
    </van-swipe-cell>

    <!-- 子节点 -->
    <div v-if="hasChildren() && expanded" class="tree-children">
      <FileTreeNode
        v-for="(child, index) in node.includes"
        :key="`${child.path}-${index}`"
        :node="child"
        :level="level + 1"
        @node-click="$emit('node-click', $event)"
        @validate-file="$emit('validate-file', $event)"
        @edit-file="$emit('edit-file', $event)"
        @download-file="$emit('download-file', $event)"
        @delete-file="$emit('delete-file', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { FileTreeNode as FileTreeNodeType } from '@/api/files';

interface Props {
  node: FileTreeNodeType;
  level: number;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'node-click': [node: FileTreeNodeType];
  'validate-file': [node: FileTreeNodeType];
  'edit-file': [node: FileTreeNodeType];
  'download-file': [node: FileTreeNodeType];
  'delete-file': [node: FileTreeNodeType];
}>();

// 组件状态
const expanded = ref(props.level === 0); // 主文件默认展开
const validating = ref(false);

// 计算属性
const hasChildren = () => {
  return props.node.includes && props.node.includes.length > 0;
};

const getFileInfo = () => {
  const size = formatFileSize(props.node.size);
  const errorText = props.node.error ? ` • ${props.node.error}` : '';
  return `${size}${errorText}`;
};

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

const getFileIcon = () => {
  if (props.node.error) return 'warning-o';
  if (props.node.is_main) return 'star-o';
  return 'description';
};

const getNodeClass = () => {
  const classes = ['tree-node'];
  if (props.node.error) classes.push('error-node');
  if (props.node.is_main) classes.push('main-node');
  return classes.join(' ');
};

const getNodeStyle = () => {
  return {
    paddingLeft: `${props.level * 16 + 16}px`
  };
};

// 事件处理
const toggleExpand = () => {
  if (hasChildren()) {
    expanded.value = !expanded.value;
  }
};

const handleNodeClick = () => {
  if (!props.node.error) {
    emit('node-click', props.node);
  }
};

const handleValidate = async () => {
  if (props.node.error) return;
  
  validating.value = true;
  try {
    emit('validate-file', props.node);
  } finally {
    validating.value = false;
  }
};

const handleEdit = () => {
  if (!props.node.error) {
    emit('edit-file', props.node);
  }
};

const handleDownload = () => {
  if (!props.node.error) {
    emit('download-file', props.node);
  }
};

const handleDelete = () => {
  if (!props.node.is_main && !props.node.error) {
    emit('delete-file', props.node);
  }
};
</script>

<style scoped>
.file-tree-node {
  position: relative;
}

.tree-node-icon {
  display: flex;
  align-items: center;
  gap: 8px;
}

.expand-icon {
  cursor: pointer;
  transition: transform 0.2s ease;
  color: var(--text-color-secondary);
}

.expand-icon:hover {
  color: var(--color-primary);
}

.main-file-icon {
  color: var(--color-success);
}

.file-node-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.validate-btn {
  min-width: 50px;
  height: 28px;
  padding: 0 8px;
  font-size: 12px;
}

.tree-children {
  border-left: 1px solid var(--border-color);
  margin-left: 16px;
}

.error-node {
  background-color: var(--color-warning-light);
}

.error-node :deep(.van-cell__title) {
  color: var(--color-danger);
}

.main-node {
  background-color: var(--color-success-light);
}

.main-node :deep(.van-cell__title) {
  font-weight: 600;
  color: var(--color-success-dark);
}

/* 节点缩进样式 */
.tree-node :deep(.van-cell) {
  position: relative;
  border-bottom: 1px solid var(--border-color-light);
}

.tree-node :deep(.van-cell):last-child {
  border-bottom: none;
}

/* 响应式调整 */
@media (max-width: 480px) {
  .file-node-actions {
    gap: 4px;
  }
  
  .validate-btn {
    min-width: 40px;
    font-size: 11px;
  }
  
  .tree-children {
    margin-left: 12px;
  }
}
</style>
