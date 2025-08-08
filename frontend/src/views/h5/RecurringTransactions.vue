<template>
  <div class="h5-recurring">
    <!-- 头部操作栏 -->
    <van-sticky>
      <div class="header-actions">
        <van-button
          type="success"
          size="small"
          icon="plus"
          @click="addRecurring"
        >
          新建周期记账
        </van-button>
        <van-button
          type="primary"
          size="small"
          @click="executeNow"
          :loading="executeLoading"
        >
          立即执行
        </van-button>
        <van-button size="small" @click="showExecutionLogs">
          执行日志
        </van-button>
        <van-button size="small" @click="showSchedulerJobs">
          定时任务
        </van-button>
      </div>
    </van-sticky>

    <!-- 筛选和搜索 -->
    <van-sticky>
      <div class="filter-section">
        <van-search
          v-model="searchKeyword"
          placeholder="搜索周期记账"
          @search="onSearch"
        />
        <van-dropdown-menu
          class="recurring-filter-menu"
          active-color="#1989fa"
          overlay
          :close-on-click-overlay="true"
        >
          <van-dropdown-item
            v-model="filterStatus"
            :options="statusOptions"
            :title="getStatusTitle()"
            @change="onFilterChange"
          />
          <van-dropdown-item
            v-model="filterFrequency"
            :options="frequencyOptions"
            :title="getFrequencyTitle()"
            @change="onFilterChange"
          />
        </van-dropdown-menu>

        <!-- 快速切换：只显示启用的 -->
        <div class="quick-filter">
          <van-switch
            v-model="showActiveOnly"
            @change="onActiveOnlyChange"
            size="20px"
          />
          <span class="filter-label">仅显示启用的</span>
        </div>
      </div>
    </van-sticky>

    <!-- 周期记账列表 -->
    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-list
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        @load="onLoad"
      >
        <!-- 空状态 -->
        <van-empty
          v-if="!loading && recurringList.length === 0"
          description="暂无周期记账数据"
          image="search"
        >
          <template #description>
            <div class="empty-description">
              <p>您还没有创建任何周期记账</p>
              <p>周期记账可以帮您自动处理重复的交易</p>
            </div>
          </template>
          <van-button
            type="primary"
            size="normal"
            round
            @click="addRecurring"
            icon="plus"
          >
            创建第一个周期记账
          </van-button>
        </van-empty>

        <van-cell-group v-else-if="recurringList.length > 0">
          <van-swipe-cell v-for="item in recurringList" :key="item.id">
            <van-cell
              :title="item.description"
              :label="getRecurringInfo(item)"
              is-link
              @click="viewRecurring(item)"
            >
              <template #icon>
                <div class="recurring-icon">
                  <van-icon :name="getRecurringIcon(item.type)" />
                </div>
              </template>
              <template #value>
                <div class="cell-value">
                  <div
                    :class="[
                      'amount',
                      item.amount > 0 ? 'positive' : 'negative',
                    ]"
                  >
                    {{ formatAmount(item.amount) }}
                  </div>
                  <van-tag :type="getStatusTagType(item.status)">
                    {{ getStatusText(item.status) }}
                  </van-tag>
                </div>
              </template>
            </van-cell>

            <!-- 滑动操作 -->
            <template #right>
              <van-button
                square
                type="primary"
                text="编辑"
                @click="editRecurring(item)"
              />
              <van-button
                square
                type="default"
                text="日志"
                @click="viewLogs(item)"
              />
              <van-button
                square
                :type="item.status === 'active' ? 'warning' : 'success'"
                :text="item.status === 'active' ? '暂停' : '启用'"
                @click="toggleStatus(item)"
              />
              <van-button
                square
                type="danger"
                text="删除"
                @click="deleteRecurring(item)"
              />
            </template>
          </van-swipe-cell>
        </van-cell-group>
      </van-list>
    </van-pull-refresh>

    <!-- 添加按钮 -->
    <van-floating-bubble
      v-model:offset="fabOffset"
      icon="plus"
      @click="addRecurring"
    />

    <!-- 执行日志弹窗 -->
    <van-popup
      v-model:show="showLogsPopup"
      position="bottom"
      :style="{ height: '60%' }"
      teleport="body"
    >
      <div class="logs-popup">
        <div class="logs-header">
          <h3>
            {{
              currentItem
                ? `${currentItem.description} - 执行日志`
                : "全部执行日志"
            }}
          </h3>
          <van-icon name="cross" @click="showLogsPopup = false" />
        </div>
        <van-list
          v-model:loading="logsLoading"
          :finished="logsFinished"
          finished-text="没有更多日志"
        >
          <van-cell
            v-for="log in executionLogs"
            :key="log.id"
            :title="log.execution_date"
            :label="log.error_message || '执行成功'"
            :value="formatDateTime(log.created_at)"
          >
            <template #icon>
              <van-icon
                :name="log.success ? 'success' : 'warning'"
                :color="
                  log.success ? 'var(--color-success)' : 'var(--color-danger)'
                "
              />
            </template>
          </van-cell>
        </van-list>
      </div>
    </van-popup>

    <!-- 定时任务状态弹窗 -->
    <van-popup
      v-model:show="showJobsPopup"
      position="bottom"
      :style="{ height: '70%' }"
      teleport="body"
    >
      <div class="jobs-popup">
        <div class="jobs-header">
          <h3>定时任务状态</h3>
          <van-icon name="cross" @click="showJobsPopup = false" />
        </div>

        <van-list
          v-model:loading="jobsLoading"
          :finished="jobsFinished"
          finished-text="数据加载完成"
        >
          <van-cell
            v-for="job in schedulerJobs"
            :key="job.name"
            :title="job.name"
            :label="job.trigger"
            :value="job.next_run ? formatDateTime(job.next_run) : '未安排'"
          >
            <template #icon>
              <van-icon name="clock-o" color="var(--color-primary)" />
            </template>
          </van-cell>
        </van-list>

        <div class="jobs-actions">
          <van-button
            type="primary"
            block
            @click="triggerScheduler"
            :loading="triggerLoading"
          >
            手动触发定时任务
          </van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import {
  recurringApi,
  type ExecutionLog,
  type SchedulerJob,
} from "@/api/recurring";
import { showConfirmDialog, showToast } from "vant";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

// 列表相关
const searchKeyword = ref("");
const refreshing = ref(false);
const loading = ref(false);
const finished = ref(false);
const fabOffset = ref({ x: -24, y: -100 });
const filterStatus = ref("all");
const filterFrequency = ref("all");
const showActiveOnly = ref(false);

// 执行相关
const executeLoading = ref(false);

// 日志相关
const showLogsPopup = ref(false);
const logsLoading = ref(false);
const logsFinished = ref(false);
const executionLogs = ref<ExecutionLog[]>([]);
const currentItem = ref<any>(null);

// 定时任务相关
const showJobsPopup = ref(false);
const jobsLoading = ref(false);
const jobsFinished = ref(false);
const schedulerJobs = ref<SchedulerJob[]>([]);
const triggerLoading = ref(false);
interface RecurringItem {
  id: number;
  description: string;
  type: string;
  amount: number;
  frequency: string;
  status: string;
  nextExecuteDate: string;
  account: string;
  category: string;
}

const recurringList = ref<RecurringItem[]>([]);

const statusOptions = [
  { text: "全部状态", value: "all" },
  { text: "启用中", value: "active" },
  { text: "已暂停", value: "paused" },
  { text: "已停止", value: "stopped" },
];

const frequencyOptions = [
  { text: "全部频率", value: "all" },
  { text: "每日", value: "daily" },
  { text: "工作日", value: "weekdays" },
  { text: "每周", value: "weekly" },
  { text: "每月", value: "monthly" },
];

const formatAmount = (amount: number) => {
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
  }).format(amount);
};

const getRecurringInfo = (item: any) => {
  const frequencyText = getFrequencyText(item.frequency);
  const nextDate = item.nextExecuteDate
    ? new Date(item.nextExecuteDate).toLocaleDateString("zh-CN")
    : "未安排";
  const account = item.account ? item.account.split(":").pop() : "未知账户";
  return `${frequencyText} • ${account} • 下次: ${nextDate}`;
};

const getFrequencyText = (frequency: string) => {
  const textMap: Record<string, string> = {
    daily: "每日",
    weekdays: "工作日",
    weekly: "每周",
    monthly: "每月",
  };
  return textMap[frequency] || frequency;
};

// 获取状态筛选的标题
const getStatusTitle = () => {
  const option = statusOptions.find((opt) => opt.value === filterStatus.value);
  return option ? option.text : "全部状态";
};

// 获取频率筛选的标题
const getFrequencyTitle = () => {
  const option = frequencyOptions.find(
    (opt) => opt.value === filterFrequency.value
  );
  return option ? option.text : "全部频率";
};

const getRecurringIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    income: "arrow-up",
    expense: "arrow-down",
    transfer: "exchange",
  };
  return iconMap[type] || "replay";
};

const getStatusText = (status: string) => {
  const textMap: Record<string, string> = {
    active: "启用",
    paused: "暂停",
    stopped: "停止",
  };
  return textMap[status] || status;
};

const getStatusTagType = (
  status: string
): "primary" | "success" | "danger" | "warning" | "default" => {
  const typeMap: Record<
    string,
    "primary" | "success" | "danger" | "warning" | "default"
  > = {
    active: "success",
    paused: "warning",
    stopped: "danger",
  };
  return typeMap[status] || "default";
};

const viewRecurring = (item: any) => {
  router.push(`/h5/recurring/${item.originalId}`);
};

const editRecurring = (item: any) => {
  router.push(`/h5/recurring/edit/${item.originalId}`);
};

const addRecurring = () => {
  router.push("/h5/recurring/add");
};

// 立即执行所有周期记账
const executeNow = async () => {
  try {
    executeLoading.value = true;
    const result = await recurringApi.execute();

    if (result.success) {
      showToast(
        `执行完成：成功 ${result.executed_count} 个，失败 ${result.failed_count} 个`
      );
    } else {
      showToast(result.message);
    }

    // 刷新列表
    await loadRecurringList(true);
  } catch (error) {
    // console.error("执行周期记账失败:", error);
    showToast("执行失败");
  } finally {
    executeLoading.value = false;
  }
};

// 查看单个周期记账的日志
const viewLogs = async (item: any) => {
  try {
    currentItem.value = item;
    showLogsPopup.value = true;
    logsLoading.value = true;

    const logs = await recurringApi.getLogs(item.originalId);
    executionLogs.value = logs;
    logsFinished.value = true;
  } catch (error) {
    // console.error("加载日志失败:", error);
    showToast("加载日志失败");
  } finally {
    logsLoading.value = false;
  }
};

// 查看全部执行日志
const showExecutionLogs = async () => {
  try {
    currentItem.value = null;
    showLogsPopup.value = true;
    logsLoading.value = true;

    const logs = await recurringApi.getLogs(); // 不传ID则获取全部日志
    executionLogs.value = logs;
    logsFinished.value = true;
  } catch (error) {
    // console.error("加载全部日志失败:", error);
    showToast("加载日志失败");
  } finally {
    logsLoading.value = false;
  }
};

// 筛选条件变化时重新加载
const onFilterChange = () => {
  loadRecurringList(true);
};

// 仅显示启用的切换
const onActiveOnlyChange = () => {
  // 当启用"仅显示启用的"时，自动将状态筛选设置为活跃
  if (showActiveOnly.value) {
    filterStatus.value = "active";
  } else {
    filterStatus.value = "all";
  }
  loadRecurringList(true);
};

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString("zh-CN");
};

// 查看定时任务状态
const showSchedulerJobs = async () => {
  try {
    showJobsPopup.value = true;
    jobsLoading.value = true;

    const jobs = await recurringApi.getSchedulerJobs();
    schedulerJobs.value = jobs;
    jobsFinished.value = true;
  } catch (error) {
    // console.error("加载定时任务状态失败:", error);
    showToast("加载定时任务状态失败");
  } finally {
    jobsLoading.value = false;
  }
};

// 手动触发定时任务
const triggerScheduler = async () => {
  try {
    triggerLoading.value = true;
    const result = await recurringApi.triggerScheduler();
    showToast(result.message || "触发成功");

    // 刷新定时任务状态和列表
    await showSchedulerJobs();
    await loadRecurringList(true);
  } catch (error) {
    // console.error("触发定时任务失败:", error);
    showToast("触发定时任务失败");
  } finally {
    triggerLoading.value = false;
  }
};

const toggleStatus = async (item: any) => {
  try {
    const newStatus = item.status === "active" ? "paused" : "active";
    const actionText = newStatus === "active" ? "启用" : "暂停";

    await showConfirmDialog({
      title: `确认${actionText}`,
      message: `确定要${actionText}这个周期记账吗？`,
    });

    // 调用API切换状态
    await recurringApi.toggle(item.originalId);

    // 更新本地状态
    item.status = newStatus;

    showToast(`${actionText}成功`);
  } catch (error) {
    if (error !== "cancel") {
      // 不是用户取消
      // showToast(`${newStatus === 'active' ? '启用' : '暂停'}失败`)
      // console.error("切换状态失败:", error);
    }
  }
};

const deleteRecurring = async (item: any) => {
  try {
    await showConfirmDialog({
      title: "确认删除",
      message: "确定要删除这个周期记账吗？删除后无法恢复。",
    });

    // 调用API删除
    await recurringApi.delete(item.originalId);

    // 从列表中移除
    const index = recurringList.value.findIndex((r) => r.id === item.id);
    if (index > -1) {
      recurringList.value.splice(index, 1);
    }

    showToast("删除成功");
  } catch (error) {
    if (error !== "cancel") {
      // 不是用户取消
      showToast("删除失败");
      // console.error("删除周期记账失败:", error);
    }
  }
};

const onSearch = () => {
  loadRecurringList(true);
};

const onRefresh = async () => {
  await loadRecurringList(true);
  refreshing.value = false;
};

const onLoad = async () => {
  await loadRecurringList(false);
};

const loadRecurringList = async (isRefresh = false) => {
  try {
    loading.value = true;

    // 根据筛选条件调用API
    // 如果启用了"仅显示启用的"开关，或者状态筛选为active，则传递true
    const activeOnly = showActiveOnly.value || filterStatus.value === "active";
    const recurringData = await recurringApi.list(activeOnly);

    // 转换API数据格式
    let convertedList = recurringData.map((item: any, index: number) => {
      // 获取第一个posting来确定金额和账户
      const posting = item.postings?.[0];
      const amount = posting?.amount || 0;
      const parsedAmount =
        typeof amount === "string" ? parseFloat(amount) : amount;

      // 转换状态
      let status = "stopped";
      if (item.is_active) {
        status = "active";
      }

      return {
        id: index + 1,
        originalId: item.id, // 保存原始ID用于API调用
        description: item.name || item.narration || "未知",
        type: parsedAmount > 0 ? "income" : "expense",
        amount: parsedAmount,
        frequency: item.recurrence_type,
        status,
        nextExecuteDate:
          item.next_execution || new Date().toLocaleDateString("en-CA"),
        account: posting?.account || "未知账户",
        category: "", // API中没有category字段，暂时留空
      };
    });

    // 根据状态筛选
    if (filterStatus.value !== "all") {
      convertedList = convertedList.filter(
        (item: any) => item.status === filterStatus.value
      );
    }

    // 根据频率筛选
    if (filterFrequency.value !== "all") {
      convertedList = convertedList.filter(
        (item: any) => item.frequency === filterFrequency.value
      );
    }

    // 根据搜索关键词筛选
    if (searchKeyword.value.trim()) {
      convertedList = convertedList.filter((item: any) =>
        item.description
          .toLowerCase()
          .includes(searchKeyword.value.toLowerCase())
      );
    }

    if (isRefresh) {
      recurringList.value = convertedList;
    } else {
      recurringList.value.push(...convertedList);
    }

    // 所有数据一次性加载完成
    finished.value = true;
  } catch (error) {
    // console.error("加载周期记账列表失败:", error);
    showToast("加载周期记账数据失败");
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadRecurringList(true);
});
</script>

<style scoped>
.h5-recurring {
  background-color: var(--bg-color-secondary);
  min-height: 100vh;
}

.header-actions {
  background-color: var(--bg-color);
  padding: 12px 16px;
  display: flex;
  gap: 8px;
  border-bottom: 1px solid var(--border-color);
  overflow-x: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
}
.header-actions :deep(.van-button--default) {
  background-color: var(--bg-color-tertiary) !important;
  color: var(--text-color) !important;
  border-color: var(--border-color) !important;
}

.header-actions::-webkit-scrollbar {
  display: none;
}

.filter-section {
  background-color: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
}

.filter-section :deep(.van-search) {
  padding: 8px 16px;
  background-color: var(--bg-color) !important;
}
.filter-section :deep(.van-search__content) {
  background-color: var(--bg-color-secondary);
}
/* 周期记账筛选菜单样式 */
.recurring-filter-menu {
  background-color: var(--van-background);
}

/* 自定义筛选菜单栏样式 */
:deep(.recurring-filter-menu .van-dropdown-menu__bar) {
  background-color: var(--van-background);
  box-shadow: none;
  border-bottom: none;
  height: 48px;
  display: flex;
}

/* 确保筛选项宽度平均分配 */
:deep(.recurring-filter-menu .van-dropdown-menu__item) {
  flex: 1;
  min-width: 0;
}

/* 筛选项标题样式 */
:deep(.recurring-filter-menu .van-dropdown-menu__title) {
  font-size: 14px;
  font-weight: 500;
  color: var(--van-text-color);
  display: flex;
  align-items: center;
  justify-content: center;
  height: 48px;
  padding: 0 32px 0 12px;
  position: relative;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
  box-sizing: border-box;
}

/* 筛选项激活状态 */
:deep(.recurring-filter-menu .van-dropdown-menu__title--active) {
  color: #1989fa;
}

/* 下拉箭头样式 - 收起状态（向下箭头）*/
:deep(.recurring-filter-menu .van-dropdown-menu__title::after) {
  border-color: #969799 transparent transparent;
  border-width: 4px 4px 0;
  border-style: solid;
  content: "";
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-25%);
  transition: all 0.3s ease;
  flex-shrink: 0;
  width: 0;
  height: 0;
}

/* 展开状态（向上箭头）*/
:deep(.recurring-filter-menu .van-dropdown-menu__title--active::after) {
  border-color: #1989fa transparent transparent;
  transform: translateY(-75%) rotate(180deg);
}

/* 下拉选项样式优化 */
:deep(.recurring-filter-menu .van-dropdown-item__content) {
  max-height: 50vh;
  overflow-y: auto;
  border-radius: 0 !important;
  border-top-left-radius: 0 !important;
  border-top-right-radius: 0 !important;
  border-bottom-left-radius: 0 !important;
  border-bottom-right-radius: 0 !important;
}

/* 移除下拉容器的圆角 */
:deep(.recurring-filter-menu .van-dropdown-item) {
  border-radius: 0 !important;
}

:deep(.recurring-filter-menu .van-dropdown-item__wrapper) {
  border-radius: 0 !important;
}

/* 选项样式 */
:deep(.recurring-filter-menu .van-dropdown-item__option) {
  padding: 12px 16px;
  font-size: 14px;
  color: var(--van-text-color);
  border-bottom: 1px solid var(--van-border-color);
  transition: all 0.3s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-height: 48px;
  display: flex;
  align-items: center;
  border-left: 3px solid transparent;
  position: relative;
}

:deep(.recurring-filter-menu .van-dropdown-item__option:last-child) {
  border-bottom: none;
}

:deep(.recurring-filter-menu .van-dropdown-item__option:not([disabled]):hover) {
  background-color: var(--van-gray-1);
  border-left-color: transparent;
}

:deep(.recurring-filter-menu .van-dropdown-item__option--active) {
  background-color: var(--van-blue-light) !important;
  color: #1989fa !important;
  border-left-color: transparent !important;
  font-weight: 500;
}

/* 移除选中选项的对勾图标 */
:deep(.recurring-filter-menu .van-dropdown-item__option--active::after) {
  display: none;
}

.filter-section :deep(.van-dropdown-menu__bar) {
  background-color: var(--bg-color);
  box-shadow: none;
}
.filter-section :deep(.van-dropdown-menu__title) {
  color: var(--text-color);
}

.quick-filter {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding: 8px 16px;
  background-color: var(--bg-color);
  border-top: 1px solid var(--border-color);
}

.filter-label {
  margin-left: 8px;
  font-size: 14px;
  color: var(--text-color-secondary);
}

.recurring-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background-color: var(--bg-color-tertiary);
  border-radius: 50%;
  margin-right: 12px;
}
.recurring-icon .van-icon {
  color: var(--text-color);
}

html[data-theme="dark"] .amount.positive {
  color: #95d475 !important;
}

html[data-theme="dark"] .amount.negative {
  color: #ff7875 !important;
}

:deep(.van-cell-group) {
  margin: 0;
}

:deep(.van-tag) {
  margin-left: 8px;
}

.cell-value {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.amount {
  font-weight: 500;
  font-size: 14px;
}

.amount.positive {
  color: #07c160;
}

.amount.negative {
  color: #ee0a24;
}

/* 日志弹窗样式 */
.logs-popup,
.jobs-popup {
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--bg-color-secondary);
  color: var(--text-color);
}

.logs-header,
.jobs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.logs-header h3,
.jobs-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-color);
}

/* 空状态样式 */
.empty-description {
  margin: 8px 0 24px 0;
}

.empty-description p {
  margin: 4px 0;
  color: var(--text-color-placeholder);
  font-size: 14px;
  line-height: 20px;
}

/* 浮动按钮样式修复 */
:deep(.van-floating-bubble) {
  z-index: 1000 !important;
  position: fixed !important;
  bottom: 80px !important; /* 避免被底部导航栏遮挡 */
}

/* 定时任务弹窗样式 */
.jobs-popup {
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.jobs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.jobs-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: var(--text-color);
}

.jobs-actions {
  margin-top: 16px;
  padding: 16px 0;
  border-top: 1px solid var(--border-color);
}
</style>
