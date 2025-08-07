<template>
  <div class="h5-dashboard">
    <!-- 账户概览卡片 -->
    <van-card class="balance-card">
      <template #title>
        <div class="balance-header">
          <span>账户概览</span>
          <van-icon name="eye-o" @click="toggleBalanceVisibility" />
        </div>
      </template>
      <template #desc>
        <div class="balance-overview-two-rows">
          <div class="main-balance">
            <div class="overview-label">净资产</div>
            <div class="overview-amount large">
              {{ showBalance ? formatAmount(totalBalance) : "****" }}
            </div>
          </div>
          <div class="sub-balances">
            <div class="overview-item">
              <div class="overview-label">资产</div>
              <div class="overview-amount">
                {{ showBalance ? formatAmount(totalAssets) : "****" }}
              </div>
            </div>
            <div class="overview-item">
              <div class="overview-label">负债</div>
              <div class="overview-amount">
                {{ showBalance ? formatAmount(totalLiabilities) : "****" }}
              </div>
            </div>
          </div>
        </div>
      </template>
    </van-card>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <van-grid :column-num="4" :border="false">
        <van-grid-item
          v-for="action in quickActions"
          :key="action.name"
          :icon="action.icon"
          :text="action.text"
          @click="action.onClick"
        />
      </van-grid>
    </div>

    <!-- 收支趋势 -->
    <van-cell-group title="收支趋势">
      <div class="trend-chart-container">
        <div v-if="trendsOption" ref="chartContainer" class="chart-wrapper" />
        <div v-else class="loading-wrapper">
          <van-loading>加载中...</van-loading>
        </div>
      </div>
    </van-cell-group>

    <!-- 月度统计 -->
    <van-cell-group title="本月统计">
      <van-cell
        title="收入"
        :value="formatAmount(monthlyStats.income)"
        value-class="positive"
      />
      <van-cell
        title="支出"
        :value="formatAmount(monthlyStats.expense)"
        value-class="negative"
      />
      <van-cell title="结余" :value="formatAmount(monthlyStats.balance)" />
    </van-cell-group>
  </div>
</template>

<script setup lang="ts">
import { getBalanceSheet, getMonthlySummary, getTrends } from "@/api/reports";
import { useThemeStore } from "@/stores/theme";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
} from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { showToast } from "vant";
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

// 注册 ECharts 组件
echarts.use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
]);

const router = useRouter();
const themeStore = useThemeStore();

const isDark = computed(() => themeStore.isDark);

const showBalance = ref(true);
const totalBalance = ref(0);
const totalAssets = ref(0);
const totalLiabilities = ref(0);

const monthlyStats = ref({
  income: 0,
  expense: 0,
  balance: 0,
});

// 趋势图表相关
const chartContainer = ref<HTMLElement>();
const trendsOption = ref<any>(null);
const trendsData = ref<any>(null);
let chartInstance: echarts.ECharts | null = null;

const quickActions = [
  {
    name: "expense",
    icon: "minus",
    text: "支出",
    onClick: () => router.push("/h5/add-transaction?type=expense"),
  },
  {
    name: "income",
    icon: "plus",
    text: "收入",
    onClick: () => router.push("/h5/add-transaction?type=income"),
  },
  {
    name: "transfer",
    icon: "exchange",
    text: "转账",
    onClick: () => router.push("/h5/add-transaction?type=transfer"),
  },
  {
    name: "reports",
    icon: "bar-chart-o",
    text: "报表",
    onClick: () => router.push("/h5/reports"),
  },
];

const toggleBalanceVisibility = () => {
  showBalance.value = !showBalance.value;
};

const formatAmount = (amount: number) => {
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
  }).format(amount);
};

// 初始化图表
const initChart = async () => {
  await nextTick();
  if (!chartContainer.value) return;

  if (chartInstance) {
    chartInstance.dispose();
  }

  chartInstance = echarts.init(chartContainer.value);

  if (trendsOption.value) {
    chartInstance.setOption(trendsOption.value);
  }

  // 监听窗口大小变化
  const resizeHandler = () => {
    if (chartInstance) {
      chartInstance.resize();
    }
  };
  window.addEventListener("resize", resizeHandler);
};

// 生成趋势图表配置
const generateTrendsOption = () => {
  if (!trendsData.value?.trends) return;

  const periods = trendsData.value.trends.map((item: any) => item.period);
  const incomes = trendsData.value.trends.map((item: any) => item.total_income);
  const expenses = trendsData.value.trends.map((item: any) =>
    Math.abs(item.total_expenses)
  );

  trendsOption.value = {
    tooltip: {
      trigger: "axis",
      formatter: (params: any) => {
        let result = `${params[0].axisValue}<br/>`;
        params.forEach((param: any) => {
          result += `${param.seriesName}: ${formatAmount(param.value)}<br/>`;
        });
        return result;
      },
      backgroundColor: isDark.value ? "#262626" : "#ffffff",
      borderColor: isDark.value ? "#434343" : "#dcdfe6",
      textStyle: {
        color: isDark.value ? "#e8e8e8" : "#303133",
      },
    },
    legend: {
      data: ["收入", "支出"],
      bottom: 0,
      textStyle: {
        fontSize: 12,
        color: isDark.value ? "#c9c9c9" : "#606266",
      },
    },
    grid: {
      top: 20,
      left: 10,
      right: 10,
      bottom: 40,
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: periods,
      axisLabel: {
        fontSize: 10,
        rotate: 45,
        color: isDark.value ? "#8c8c8c" : "#909399",
      },
      axisLine: {
        lineStyle: {
          color: isDark.value ? "#434343" : "#dcdfe6",
        },
      },
    },
    yAxis: {
      type: "value",
      axisLabel: {
        fontSize: 10,
        formatter: (value: number) => {
          if (value >= 10000) {
            return (value / 10000).toFixed(1) + "w";
          }
          return value.toString();
        },
        color: isDark.value ? "#8c8c8c" : "#909399",
      },
      splitLine: {
        lineStyle: {
          color: isDark.value ? "#2d2d2d" : "#ebeef5",
        },
      },
    },
    series: [
      {
        name: "收入",
        type: "line",
        data: incomes,
        itemStyle: { color: "#07c160" },
        lineStyle: { width: 2 },
        symbol: "circle",
        symbolSize: 4,
      },
      {
        name: "支出",
        type: "line",
        data: expenses,
        itemStyle: { color: "#ee0a24" },
        lineStyle: { width: 2 },
        symbol: "circle",
        symbolSize: 4,
      },
    ],
  };

  // 如果图表已初始化，更新配置
  if (chartInstance) {
    chartInstance.setOption(trendsOption.value);
  }
};

const loadDashboardData = async () => {
  try {
    // 并行加载各种数据
    const [balanceSheetRes, monthlySummaryRes, trendsRes] =
      await Promise.allSettled([
        getBalanceSheet(),
        getMonthlySummary(),
        getTrends(6), // 获取最近6个月的趋势数据
      ]);

    // 处理资产负债表数据
    if (balanceSheetRes.status === "fulfilled") {
      const balanceData = balanceSheetRes.value as any;
      totalBalance.value = balanceData?.net_worth || 0;
      totalAssets.value =
        balanceData?.accounts
          ?.filter((acc: any) => acc.account_type === "Assets")
          .reduce(
            (sum: number, acc: any) => sum + parseFloat(acc.balance),
            0
          ) || 0;
      totalLiabilities.value =
        balanceData?.accounts
          ?.filter((acc: any) => acc.account_type === "Liabilities")
          .reduce(
            (sum: number, acc: any) => sum + parseFloat(acc.balance),
            0
          ) || 0;
    } else {
      console.error("获取资产负债表失败:", balanceSheetRes.reason);
    }

    // 处理月度统计数据
    if (monthlySummaryRes.status === "fulfilled") {
      const monthlyData = monthlySummaryRes.value as any;
      monthlyStats.value = {
        income: monthlyData?.income_statement?.total_income || 0,
        expense: monthlyData?.income_statement?.total_expenses || 0,
        balance: monthlyData?.income_statement?.net_income || 0,
      };
    } else {
      console.error("获取月度统计失败:", monthlySummaryRes.reason);
    }

    // 处理趋势数据
    if (trendsRes.status === "fulfilled") {
      trendsData.value = trendsRes.value;
      generateTrendsOption();
      // 在下次tick时初始化图表
      await nextTick();
      initChart();
    } else {
      console.error("获取趋势数据失败:", trendsRes.reason);
    }
  } catch (error: any) {
    console.error("加载仪表盘数据失败:", error);

    // 详细错误信息
    if (error.response) {
      // 服务器响应了错误状态码
      console.error("API错误响应:", error.response.status, error.response.data);
      showToast(`API错误: ${error.response.status}`);
    } else if (error.request) {
      // 请求发出了但没有收到响应
      console.error("网络错误:", error.request);
      showToast("网络连接失败，请检查后端服务");
    } else {
      // 其他错误
      console.error("未知错误:", error.message);
      showToast("加载数据失败");
    }
  }
};

onMounted(() => {
  loadDashboardData();
});

watch(isDark, () => {
  // 当主题变化时，重新生成图表配置，ECharts实例会自动更新
  generateTrendsOption();
});
</script>

<style scoped>
.h5-dashboard {
  padding: 16px;
  background-color: var(--van-background);
  min-height: 100vh;
  transition: background-color 0.3s ease;
}

.balance-card {
  margin-bottom: 16px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.balance-card :deep(.van-card__header) {
  padding: 16px;
}

.balance-card :deep(.van-card__content) {
  padding: 0 16px 16px;
}

.balance-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  opacity: 0.8;
}

.balance-amount {
  font-size: 32px;
  font-weight: bold;
  margin-top: 8px;
}

.balance-overview-two-rows {
  display: flex;
  flex-direction: column;
}

.main-balance {
  text-align: center;
  margin-bottom: 12px;
}

.sub-balances {
  display: flex;
  justify-content: space-around;
}

.overview-item {
  text-align: center;
}

.overview-label {
  font-size: 12px;
  opacity: 0.8;
  margin-bottom: 4px;
}

.overview-amount {
  font-weight: bold;
}

.overview-amount.large {
  font-size: 28px;
}

.quick-actions {
  margin-bottom: 16px;
  background-color: var(--van-background-2);
  border-radius: 12px;
  padding: 16px;
  transition: background-color 0.3s ease;
}

.quick-actions :deep(.van-grid-item__content) {
  padding: 16px 8px;
}

.quick-actions :deep(.van-grid-item__icon) {
  font-size: 24px;
  color: #1989fa;
}

.quick-actions :deep(.van-grid-item__text) {
  margin-top: 8px;
  font-size: 12px;
  color: #646566;
}

:deep(.van-cell-group) {
  margin-bottom: 16px;
  border-radius: 12px;
  overflow: hidden;
}

:deep(.van-cell-group__title) {
  padding: 16px 16px 8px;
  font-weight: 500;
  color: #323233;
}

:deep(.positive) {
  color: #07c160;
}

:deep(.negative) {
  color: #ee0a24;
}

:deep(.van-cell__left-icon) {
  margin-right: 12px;
  color: #969799;
}

/* 趋势图表样式 */
.trend-chart-container {
  padding: 16px;
  background-color: var(--van-background-2);
  transition: background-color 0.3s ease;
}

.chart-wrapper {
  width: 100%;
  height: 200px;
}

.loading-wrapper {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
