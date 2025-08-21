<template>
  <div class="yearly-file-manager">
    <!-- 年份文件列表 -->
    <van-cell-group title="年份文件管理">
      <van-cell
        v-for="year in years"
        :key="year"
        :title="`${year}年交易文件`"
        :label="getYearFileStatus(year)"
        :is-link="true"
        @click="showYearActions(year)"
      >
        <template #right-icon>
          <van-tag v-if="year === currentYear" type="primary">当前</van-tag>
          <van-tag v-if="hasYearFile(year)" type="success">已创建</van-tag>
          <van-tag v-else type="default">未创建</van-tag>
        </template>
      </van-cell>
    </van-cell-group>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <van-button
        v-if="!hasYearFile(currentYear)"
        type="success"
        size="large"
        @click="createYearFile(currentYear)"
        block
        style="margin-bottom: 12px;"
      >
        创建{{currentYear}}年文件
      </van-button>
      
      <van-button
        type="primary"
        size="large"
        :loading="migrating"
        @click="showMigrateDialog"
        block
      >
        按年份迁移交易
      </van-button>
      
      <van-button
        type="warning"
        size="large"
        :loading="cleaning"
        @click="cleanupEmptyFiles"
        block
        style="margin-top: 12px;"
      >
        清理空文件
      </van-button>
    </div>

    <!-- 年份操作弹窗 -->
    <van-action-sheet
      v-model:show="showActions"
      :actions="yearActions"
      :title="`${selectedYear}年文件操作`"
      @select="onYearActionSelect"
      cancel-text="取消"
    />

    <!-- 迁移确认对话框 -->
    <van-dialog
      v-model:show="showMigrateConfirm"
      title="确认迁移"
      message="将主文件中的交易按年份自动分配到对应的年份文件中。此操作不可逆，建议先备份文件。"
      show-cancel-button
      @confirm="migrateTransactions"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import {
  getAvailableYears,
  createYearlyFile,
  migrateTransactionsByYear,
  cleanupEmptyYearlyFiles,
} from '@/api/transactions';
import {
  showToast,
  showLoadingToast,
  closeToast,
  showConfirmDialog,
} from 'vant';

const years = ref<number[]>([]);
const existingYears = ref<number[]>([]);
const currentYear = new Date().getFullYear();

const showActions = ref(false);
const selectedYear = ref<number>(currentYear);
const migrating = ref(false);
const cleaning = ref(false);
const showMigrateConfirm = ref(false);

const emit = defineEmits<{
  'file-changed': [];
}>();

// 计算属性
const yearActions = computed(() => {
  const actions = [];
  
  if (!hasYearFile(selectedYear.value)) {
    actions.push({
      name: '创建年份文件',
      icon: 'add-o',
    });
  }
  
  actions.push({
    name: '查看文件内容',
    icon: 'eye-o',
  });
  
  return actions;
});

// 方法
const hasYearFile = (year: number) => {
  return existingYears.value.includes(year);
};

const getYearFileStatus = (year: number) => {
  if (hasYearFile(year)) {
    return `transactions_${year}.beancount`;
  }
  return '文件未创建';
};

const loadYears = async () => {
  try {
    const allYears = await getAvailableYears();
    
    // 只显示已创建的年份文件和当前年份
    const displayYears = new Set<number>();
    
    // 添加当前年份（总是显示）
    displayYears.add(currentYear);
    
    // 只添加已存在的年份文件
    allYears.forEach(year => displayYears.add(year));
    
    years.value = Array.from(displayYears).sort((a, b) => b - a);
    existingYears.value = allYears;
    
  } catch (error) {
    showToast('加载年份列表失败');
    console.error('Load years failed:', error);
  }
};

const showYearActions = (year: number) => {
  selectedYear.value = year;
  showActions.value = true;
};

const onYearActionSelect = async (action: any) => {
  showActions.value = false;
  
  switch (action.name) {
    case '创建年份文件':
      await createYearFile(selectedYear.value);
      break;
    case '查看文件内容':
      await viewYearFile(selectedYear.value);
      break;
  }
};

const createYearFile = async (year: number) => {
  try {
    showLoadingToast({
      message: '创建中...',
      forbidClick: true,
    });
    
    await createYearlyFile(year);
    
    closeToast();
    showToast(`${year}年文件创建成功`);
    
    // 重新加载年份列表
    await loadYears();
    
    // 通知父组件文件发生变化
    emit('file-changed');
    
  } catch (error) {
    closeToast();
    showToast('创建年份文件失败');
    console.error('Create yearly file failed:', error);
  }
};

const viewYearFile = async (year: number) => {
  // 触发文件变化事件，让父组件重新加载文件树
  emit('file-changed');
  showToast(`请在文件树中查看 transactions_${year}.beancount`);
};

const showMigrateDialog = () => {
  showMigrateConfirm.value = true;
};

const migrateTransactions = async () => {
  try {
    migrating.value = true;
    showLoadingToast({
      message: '迁移中...',
      forbidClick: true,
    });
    
    await migrateTransactionsByYear();
    
    closeToast();
    showToast('交易迁移成功');
    
    // 重新加载年份列表
    await loadYears();
    
    // 通知父组件文件发生变化
    emit('file-changed');
    
  } catch (error) {
    closeToast();
    showToast('迁移交易失败');
    console.error('Migrate transactions failed:', error);
  } finally {
    migrating.value = false;
  }
};

const cleanupEmptyFiles = async () => {
  try {
    await showConfirmDialog({
      title: '确认清理',
      message: '将删除所有空的年份文件，此操作不可逆。',
    });
    
    cleaning.value = true;
    showLoadingToast({
      message: '清理中...',
      forbidClick: true,
    });
    
    const result = await cleanupEmptyYearlyFiles();
    
    closeToast();
    showToast(result.message || '清理完成');
    
    // 重新加载年份列表
    await loadYears();
    
    // 通知父组件文件发生变化
    emit('file-changed');
    
  } catch (error) {
    if (error === 'cancel') {
      return; // 用户取消
    }
    
    closeToast();
    showToast('清理文件失败');
    console.error('Cleanup files failed:', error);
  } finally {
    cleaning.value = false;
  }
};

onMounted(() => {
  loadYears();
});
</script>

<style scoped>
.yearly-file-manager {
  padding: 16px;
}

.action-buttons {
  margin-top: 24px;
}

:deep(.van-cell__title) {
  font-weight: 500;
}

:deep(.van-cell__label) {
  color: var(--text-color-secondary);
  font-size: 12px;
}

:deep(.van-cell__right-icon) {
  display: flex;
  align-items: center;
  gap: 6px;
}

:deep(.van-tag) {
  margin-left: 4px;
}
</style>
