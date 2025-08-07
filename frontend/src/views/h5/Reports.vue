<template>
  <div class="h5-reports">
    <!-- 报表类型选择 -->
    <div class="tabs-fixed-container">
      <div class="report-type-selector">
        <van-tabs v-model:active="activeTab" @change="onTabChange" swipeable>
          <van-tab title="资产负债表" name="balance-sheet" />
          <van-tab title="损益表" name="income-statement" />
          <van-tab title="趋势分析" name="trends" />
          <van-tab title="月度报告" name="monthly" />
        </van-tabs>
      </div>
    </div>

    <!-- 报表内容区域 -->
    <div class="reports-content-wrapper">
      <!-- 资产负债表 -->
      <div v-if="activeTab === 'balance-sheet'" class="report-content">
        <!-- 日期选择 -->
        <div class="date-selector">
          <van-cell-group inset>
            <van-cell
              title="截止日期"
              :value="formatDateDisplay(asOfDate)"
              is-link
              @click="showAsOfDateCalendar = true"
            />
          </van-cell-group>
        </div>

        <!-- 资产负债表内容 -->
        <div v-if="balanceSheet" class="balance-sheet">
          <!-- 资产 -->
          <van-cell-group title="资产" inset>
            <van-collapse v-model="assetExpandedItems">
              <van-collapse-item
                v-for="category in groupedAssetCategories"
                :key="category.name"
                :name="category.name"
                :title="category.name"
                :value="formatCurrency(category.total)"
              >
                <div class="account-list">
                  <template
                    v-for="account in category.accounts"
                    :key="account.fullName"
                  >
                    <!-- 如果是子分组，显示为可折叠的子分组 -->
                    <div v-if="account.isSubGroup" class="sub-group">
                      <van-collapse v-model="subGroupExpandedItems">
                        <van-collapse-item
                          :name="account.fullName"
                          :title="account.name"
                          :value="formatCurrency(account.balance)"
                        >
                          <div class="sub-account-list">
                            <div
                              v-for="subAccount in account.subAccounts"
                              :key="subAccount.fullName"
                              class="sub-account-item clickable-item"
                              @click="
                                goToAccountJournal(
                                  subAccount.fullName,
                                  '1990-01-01',
                                  asOfDate
                                )
                              "
                            >
                              <span class="account-name">{{
                                subAccount.name
                              }}</span>
                              <span class="account-amount">{{
                                formatCurrency(subAccount.balance)
                              }}</span>
                            </div>
                          </div>
                        </van-collapse-item>
                      </van-collapse>
                    </div>
                    <!-- 普通账户直接显示 -->
                    <div
                      v-else
                      class="account-item clickable-item"
                      @click="
                        goToAccountJournal(
                          account.fullName,
                          '1990-01-01',
                          asOfDate
                        )
                      "
                    >
                      <span class="account-name">{{ account.name }}</span>
                      <span class="account-amount">{{
                        formatCurrency(account.balance)
                      }}</span>
                    </div>
                  </template>
                </div>
              </van-collapse-item>
            </van-collapse>
            <div class="total-row">
              <span class="total-label">资产总计</span>
              <span class="total-amount">{{
                formatCurrency(balanceSheet.total_assets)
              }}</span>
            </div>
          </van-cell-group>

          <!-- 负债 -->
          <van-cell-group title="负债" inset>
            <van-collapse v-model="liabilityExpandedItems">
              <van-collapse-item
                v-for="category in groupedLiabilityCategories"
                :key="category.name"
                :name="category.name"
                :title="category.name"
                :value="formatCurrency(category.total)"
              >
                <div class="account-list">
                  <template
                    v-for="account in category.accounts"
                    :key="account.fullName"
                  >
                    <!-- 如果是子分组，显示为可折叠的子分组 -->
                    <div v-if="account.isSubGroup" class="sub-group">
                      <van-collapse v-model="subGroupExpandedItems">
                        <van-collapse-item
                          :name="account.fullName"
                          :title="account.name"
                          :value="formatCurrency(Math.abs(account.balance))"
                        >
                          <div class="sub-account-list">
                            <div
                              v-for="subAccount in account.subAccounts"
                              :key="subAccount.fullName"
                              class="sub-account-item clickable-item"
                              @click="
                                goToAccountJournal(
                                  subAccount.fullName,
                                  '1990-01-01',
                                  asOfDate
                                )
                              "
                            >
                              <span class="account-name">{{
                                subAccount.name
                              }}</span>
                              <span class="account-amount">{{
                                formatCurrency(Math.abs(subAccount.balance))
                              }}</span>
                            </div>
                          </div>
                        </van-collapse-item>
                      </van-collapse>
                    </div>
                    <!-- 普通账户直接显示 -->
                    <div
                      v-else
                      class="account-item clickable-item"
                      @click="
                        goToAccountJournal(
                          account.fullName,
                          '1990-01-01',
                          asOfDate
                        )
                      "
                    >
                      <span class="account-name">{{
                        formatAccountName(account.name)
                      }}</span>
                      <span class="account-amount">{{
                        formatCurrency(Math.abs(account.balance))
                      }}</span>
                    </div>
                  </template>
                </div>
              </van-collapse-item>
            </van-collapse>
            <div class="total-row">
              <span class="total-label">负债总计</span>
              <span class="total-amount">{{
                formatCurrency(Math.abs(balanceSheet.total_liabilities))
              }}</span>
            </div>
          </van-cell-group>

          <!-- 所有者权益 -->
          <van-cell-group title="所有者权益" inset>
            <van-collapse v-model="equityExpandedItems">
              <van-collapse-item
                v-for="category in groupedEquityCategories"
                :key="category.name"
                :name="category.name"
                :title="category.name"
                :value="formatCurrency(category.total)"
              >
                <div class="account-list">
                  <template
                    v-for="account in category.accounts"
                    :key="account.fullName"
                  >
                    <!-- 如果是子分组，显示为可折叠的子分组 -->
                    <div v-if="account.isSubGroup" class="sub-group">
                      <van-collapse v-model="subGroupExpandedItems">
                        <van-collapse-item
                          :name="account.fullName"
                          :title="account.name"
                          :value="formatCurrency(account.balance)"
                        >
                          <div class="sub-account-list">
                            <div
                              v-for="subAccount in account.subAccounts"
                              :key="subAccount.fullName"
                              class="sub-account-item clickable-item"
                              @click="
                                goToAccountJournal(
                                  subAccount.fullName,
                                  '1990-01-01',
                                  asOfDate
                                )
                              "
                            >
                              <span class="account-name">{{
                                subAccount.name
                              }}</span>
                              <span class="account-amount">{{
                                formatCurrency(subAccount.balance)
                              }}</span>
                            </div>
                          </div>
                        </van-collapse-item>
                      </van-collapse>
                    </div>
                    <!-- 普通账户直接显示 -->
                    <div
                      v-else
                      class="account-item clickable-item"
                      @click="
                        goToAccountJournal(
                          account.fullName,
                          '1990-01-01',
                          asOfDate
                        )
                      "
                    >
                      <span class="account-name">{{ account.name }}</span>
                      <span class="account-amount">{{
                        formatCurrency(account.balance)
                      }}</span>
                    </div>
                  </template>
                </div>
              </van-collapse-item>
            </van-collapse>
            <div class="total-row">
              <span class="total-label">所有者权益总计</span>
              <span class="total-amount">{{
                formatCurrency(balanceSheet.total_equity)
              }}</span>
            </div>
          </van-cell-group>
        </div>
      </div>

      <!-- 损益表 -->
      <div v-if="activeTab === 'income-statement'" class="report-content">
        <!-- 日期范围选择 -->
        <div class="date-range-selector">
          <van-cell-group inset>
            <van-cell
              title="日期范围"
              :value="formatDateRangeDisplay(startDate, endDate)"
              is-link
              @click="showDateRangeCalendar = true"
            />
          </van-cell-group>
        </div>

        <!-- 损益表内容 -->
        <div v-if="incomeStatement" class="income-statement">
          <!-- 收入 -->
          <van-cell-group title="收入" inset>
            <van-collapse v-model="incomeExpandedItems">
              <van-collapse-item
                v-for="category in groupedIncomeCategories"
                :key="category.name"
                :name="category.name"
                :title="category.name"
                :value="formatCurrency(category.total)"
              >
                <div class="account-list">
                  <div
                    v-for="account in category.accounts"
                    :key="account.name"
                    class="account-item clickable-item"
                    @click="
                      goToAccountJournal(account.fullName, startDate, endDate)
                    "
                  >
                    <span class="account-name">{{
                      formatAccountName(account.name)
                    }}</span>
                    <span class="account-amount positive">{{
                      formatCurrency(Math.abs(account.balance))
                    }}</span>
                  </div>
                </div>
              </van-collapse-item>
            </van-collapse>
            <div class="total-row">
              <span class="total-label">收入总计</span>
              <span class="total-amount positive">{{
                formatCurrency(Math.abs(incomeStatement.total_income))
              }}</span>
            </div>
          </van-cell-group>

          <!-- 支出 -->
          <van-cell-group title="支出" inset>
            <van-collapse v-model="expenseExpandedItems">
              <van-collapse-item
                v-for="category in groupedExpenseCategories"
                :key="category.name"
                :name="category.name"
                :title="category.name"
                :value="formatCurrency(category.total)"
              >
                <div class="account-list">
                  <div
                    v-for="account in category.accounts"
                    :key="account.name"
                    class="account-item clickable-item"
                    @click="
                      goToAccountJournal(account.fullName, startDate, endDate)
                    "
                  >
                    <span class="account-name">{{
                      formatAccountName(account.name)
                    }}</span>
                    <span class="account-amount negative">{{
                      formatCurrency(Math.abs(account.balance))
                    }}</span>
                  </div>
                </div>
              </van-collapse-item>
            </van-collapse>
            <div class="total-row">
              <span class="total-label">支出总计</span>
              <span class="total-amount negative">{{
                formatCurrency(Math.abs(incomeStatement.total_expenses))
              }}</span>
            </div>
          </van-cell-group>

          <!-- 净收益 -->
          <van-cell-group title="汇总" inset>
            <div class="net-income-card">
              <div
                class="net-income-value"
                :class="
                  incomeStatement.net_income >= 0 ? 'positive' : 'negative'
                "
              >
                {{ formatCurrency(incomeStatement.net_income) }}
              </div>
              <div class="net-income-label">净收益</div>
            </div>
          </van-cell-group>
        </div>
      </div>

      <!-- 趋势分析 -->
      <div v-if="activeTab === 'trends'" class="report-content">
        <!-- 时间范围选择 -->
        <div class="trends-selector">
          <van-cell-group inset>
            <van-cell
              title="统计周期"
              :value="trendsOptions.find((opt: any) => opt.value === trendsMonths)?.text"
              is-link
              @click="showTrendsPicker = true"
            />
          </van-cell-group>
        </div>

        <!-- 趋势图表 -->
        <div v-if="trendsOption" class="trends-chart">
          <van-cell-group title="收支趋势" inset>
            <div class="chart-container">
              <v-chart :option="trendsOption" style="height: 300px" />
            </div>
          </van-cell-group>
        </div>
      </div>

      <!-- 月度报告 -->
      <div v-if="activeTab === 'monthly'" class="report-content">
        <!-- 年月选择 -->
        <div class="monthly-selector">
          <van-cell-group inset>
            <van-cell
              title="年份"
              :value="`${selectedYear}年`"
              is-link
              @click="showYearPicker = true"
            />
            <van-cell
              title="月份"
              :value="`${selectedMonth}月`"
              is-link
              @click="showMonthPicker = true"
            />
          </van-cell-group>
        </div>

        <!-- 月度汇总 -->
        <div v-if="monthlySummary" class="monthly-summary">
          <!-- 概览卡片 -->
          <div class="summary-cards">
            <van-row gutter="8">
              <van-col span="12">
                <div class="summary-card income">
                  <div class="card-value">
                    {{
                      formatCurrency(
                        monthlySummary.income_statement.total_income
                      )
                    }}
                  </div>
                  <div class="card-label">本月收入</div>
                </div>
              </van-col>
              <van-col span="12">
                <div class="summary-card expense">
                  <div class="card-value">
                    {{
                      formatCurrency(
                        Math.abs(monthlySummary.income_statement.total_expenses)
                      )
                    }}
                  </div>
                  <div class="card-label">本月支出</div>
                </div>
              </van-col>
            </van-row>
            <div class="net-card">
              <div
                class="net-value"
                :class="
                  monthlySummary.income_statement.net_income >= 0
                    ? 'positive'
                    : 'negative'
                "
              >
                {{ formatCurrency(monthlySummary.income_statement.net_income) }}
              </div>
              <div class="net-label">本月净收益</div>
            </div>
            <div class="assets-card">
              <div class="assets-value">
                {{ formatCurrency(monthlySummary.balance_sheet.total_assets) }}
              </div>
              <div class="assets-label">月末总资产</div>
            </div>
          </div>

          <!-- 年度至今汇总 -->
          <div v-if="yearToDateSummary" class="ytd-summary">
            <van-cell-group :title="`${selectedYear}年度至今汇总`" inset>
              <van-cell
                title="累计收入"
                :value="
                  formatCurrency(
                    yearToDateSummary.income_statement.total_income
                  )
                "
                value-class="positive"
              />
              <van-cell
                title="累计支出"
                :value="
                  formatCurrency(
                    Math.abs(yearToDateSummary.income_statement.total_expenses)
                  )
                "
                value-class="negative"
              />
              <van-cell
                title="累计净收益"
                :value="
                  formatCurrency(yearToDateSummary.income_statement.net_income)
                "
                :value-class="
                  yearToDateSummary.income_statement.net_income >= 0
                    ? 'positive'
                    : 'negative'
                "
              />
            </van-cell-group>
          </div>

          <!-- 月度明细 -->
          <van-cell-group :title="`${selectedMonth}月收入明细`" inset>
            <van-cell
              v-for="account in sortedMonthlyIncomeAccounts"
              :key="account.name"
              :title="formatAccountName(account.name.replace('Income:', ''))"
              :value="formatCurrency(Math.abs(account.balance))"
              value-class="positive"
              is-link
              @click="
                goToAccountJournal(
                  account.name,
                  getMonthDateRange(selectedYear, selectedMonth).start,
                  getMonthDateRange(selectedYear, selectedMonth).end
                )
              "
            />
          </van-cell-group>

          <van-cell-group :title="`${selectedMonth}月支出明细`" inset>
            <van-cell
              v-for="account in sortedMonthlyExpenseAccounts"
              :key="account.name"
              :title="formatAccountName(account.name.replace('Expenses:', ''))"
              :value="formatCurrency(Math.abs(account.balance))"
              value-class="negative"
              is-link
              @click="
                goToAccountJournal(
                  account.name,
                  getMonthDateRange(selectedYear, selectedMonth).start,
                  getMonthDateRange(selectedYear, selectedMonth).end
                )
              "
            />
          </van-cell-group>
        </div>
      </div>
    </div>

    <van-popup
      v-model:show="showTrendsPicker"
      position="bottom"
      teleport="body"
    >
      <van-picker
        :columns="trendsOptions"
        @confirm="onTrendsConfirm"
        @cancel="showTrendsPicker = false"
      />
    </van-popup>

    <van-popup v-model:show="showYearPicker" position="bottom" teleport="body">
      <van-picker
        :columns="yearOptions"
        @confirm="onYearConfirm"
        @cancel="showYearPicker = false"
      />
    </van-popup>

    <van-popup v-model:show="showMonthPicker" position="bottom" teleport="body">
      <van-picker
        :columns="monthOptions"
        @confirm="onMonthConfirm"
        @cancel="showMonthPicker = false"
      />
    </van-popup>

    <!-- 日历组件 -->
    <van-calendar
      v-model:show="showAsOfDateCalendar"
      title="选择截止日期"
      :default-date="asOfDate ? new Date(asOfDate) : new Date()"
      :min-date="new Date(2020, 0, 1)"
      :max-date="new Date()"
      switch-mode="year-month"
      :show-confirm="false"
      @confirm="onAsOfDateConfirm"
      @close="showAsOfDateCalendar = false"
      teleport="body"
    />

    <van-calendar
      v-model:show="showDateRangeCalendar"
      title="选择日期范围"
      type="range"
      :default-date="getDefaultDateRange()"
      :min-date="new Date(2025, 5, 1)"
      :max-date="new Date()"
      switch-mode="year-month"
      :show-confirm="false"
      :allow-same-day="true"
      @confirm="onDateRangeConfirm"
      @close="showDateRangeCalendar = false"
      teleport="body"
    />

    <!-- 加载状态 -->
    <van-loading v-if="loading" type="spinner" vertical>加载中...</van-loading>
  </div>
</template>

<script setup lang="ts">
import { useThemeStore } from "@/stores/theme";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
} from "echarts/components";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { showToast } from "vant";
import { computed, onMounted, ref, watch } from "vue";
import VChart from "vue-echarts";
import { useRouter } from "vue-router";

import {
  getBalanceSheet,
  getIncomeStatement,
  getMonthlySummary,
  getTrends,
  getYearToDateSummary,
} from "@/api/reports";

// 路由
const router = useRouter();

// 主题 store
const themeStore = useThemeStore();

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
]);

// 基础数据
const loading = ref(false);
const activeTab = ref("balance-sheet");

// 资产负债表相关
const asOfDate = ref(new Date().toLocaleDateString("en-CA")); // 格式: YYYY-MM-DD
const balanceSheet = ref<any>(null);
const assetExpandedItems = ref<string[]>([]);
const liabilityExpandedItems = ref<string[]>([]);
const equityExpandedItems = ref<string[]>([]);
const subGroupExpandedItems = ref<string[]>([]); // 子分组展开状态

// 损益表相关
const today = new Date();
const thisMonthStart = new Date(today.getFullYear(), today.getMonth(), 1); // 本月第一天
const startDate = ref(thisMonthStart.toLocaleDateString("en-CA")); // 格式: YYYY-MM-DD
const endDate = ref(today.toLocaleDateString("en-CA")); // 今天
const incomeStatement = ref<any>(null);
const incomeExpandedItems = ref<string[]>([]);
const expenseExpandedItems = ref<string[]>([]);

// 趋势分析相关
const trendsMonths = ref(12);
const trendsData = ref<any>(null);
const trendsOption = ref<any>(null);

// 月度报告相关
const selectedYear = ref(new Date().getFullYear());
const selectedMonth = ref(new Date().getMonth() + 1);
const monthlySummary = ref<any>(null);
const yearToDateSummary = ref<any>(null);

// 日期选择器相关
const showTrendsPicker = ref(false);
const showYearPicker = ref(false);
const showMonthPicker = ref(false);

// 日历组件相关
const showAsOfDateCalendar = ref(false);
const showDateRangeCalendar = ref(false);

// 选择器选项
const trendsOptions = [
  { text: "最近6个月", value: 6 },
  { text: "最近12个月", value: 12 },
  { text: "最近24个月", value: 24 },
];

const yearOptions = computed(() => {
  const currentYear = new Date().getFullYear();
  const years = [];
  for (let i = currentYear; i >= currentYear - 5; i--) {
    years.push({ text: `${i}年`, value: i });
  }
  return years;
});

const monthOptions = [
  { text: "1月", value: 1 },
  { text: "2月", value: 2 },
  { text: "3月", value: 3 },
  { text: "4月", value: 4 },
  { text: "5月", value: 5 },
  { text: "6月", value: 6 },
  { text: "7月", value: 7 },
  { text: "8月", value: 8 },
  { text: "9月", value: 9 },
  { text: "10月", value: 10 },
  { text: "11月", value: 11 },
  { text: "12月", value: 12 },
];

// 格式化货币
const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat("zh-CN", {
    style: "currency",
    currency: "CNY",
  }).format(amount);
};

// 格式化日期显示
const formatDateDisplay = (dateStr: string) => {
  if (!dateStr) return "选择日期";
  const date = new Date(dateStr);
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
};

// 格式化日期范围显示
const formatDateRangeDisplay = (startDateStr: string, endDateStr: string) => {
  if (!startDateStr || !endDateStr) return "选择日期范围";
  const startDate = new Date(startDateStr);
  const endDate = new Date(endDateStr);
  const startFormatted = startDate.toLocaleDateString("zh-CN", {
    month: "short",
    day: "numeric",
  });
  const endFormatted = endDate.toLocaleDateString("zh-CN", {
    month: "short",
    day: "numeric",
  });
  return `${startFormatted} 至 ${endFormatted}`;
};

// 格式化账户名称 - 去掉字母前缀和连字符，但保持层级
const formatAccountName = (accountName: string) => {
  if (!accountName) return "未知账户";

  // 处理单个名称段：去掉字母前缀和连字符
  const dashIndex = accountName.indexOf("-");
  if (dashIndex > 0) {
    return accountName.substring(dashIndex + 1);
  }
  return accountName;
};

// 格式化分类名称
const formatCategoryName = (categoryName: string) => {
  return formatAccountName(categoryName);
};

// 获取指定年月的开始和结束日期
const getMonthDateRange = (year: number, month: number) => {
  const startDate = new Date(year, month - 1, 1);
  const endDate = new Date(year, month, 0);
  return {
    start: startDate.toLocaleDateString("en-CA"),
    end: endDate.toLocaleDateString("en-CA"),
  };
};

// 跳转到账户日记账页面
const goToAccountJournal = (accountName: string, from: string, to: string) => {
  if (from && to) {
    router.push({
      name: "AccountJournal",
      params: { accountName: accountName },
      query: { from, to },
    });
  } else {
    router.push({
      name: "AccountJournal",
      params: { accountName: accountName },
    });
  }
};

// 分组账户数据
const groupedAssetCategories = computed(() => {
  if (!balanceSheet.value?.accounts) return [];

  const assetAccounts = balanceSheet.value.accounts.filter(
    (acc: any) => acc.account_type === "Assets"
  );
  return groupAccountsByCategory(assetAccounts, "Assets");
});

const groupedLiabilityCategories = computed(() => {
  if (!balanceSheet.value?.accounts) return [];

  const liabilityAccounts = balanceSheet.value.accounts.filter(
    (acc: any) => acc.account_type === "Liabilities"
  );
  return groupAccountsByCategory(liabilityAccounts, "Liabilities");
});

const groupedEquityCategories = computed(() => {
  if (!balanceSheet.value?.accounts) return [];

  const equityAccounts = balanceSheet.value.accounts.filter(
    (acc: any) => acc.account_type === "Equity"
  );
  return groupAccountsByCategory(equityAccounts, "Equity");
});

const groupedIncomeCategories = computed(() => {
  if (!incomeStatement.value?.income_accounts) return [];
  return groupAccountsByCategory(
    incomeStatement.value.income_accounts,
    "Income"
  );
});

const groupedExpenseCategories = computed(() => {
  if (!incomeStatement.value?.expense_accounts) return [];
  return groupAccountsByCategory(
    incomeStatement.value.expense_accounts,
    "Expenses"
  );
});

// 月度收入支出账户排序
const sortedMonthlyIncomeAccounts = computed(() => {
  if (!monthlySummary.value?.income_statement?.income_accounts) return [];
  return [...monthlySummary.value.income_statement.income_accounts].sort(
    (a, b) => Math.abs(b.balance) - Math.abs(a.balance)
  );
});

const sortedMonthlyExpenseAccounts = computed(() => {
  if (!monthlySummary.value?.income_statement?.expense_accounts) return [];
  return [...monthlySummary.value.income_statement.expense_accounts].sort(
    (a, b) => Math.abs(b.balance) - Math.abs(a.balance)
  );
});

// 按分类分组账户，支持层级结构
const groupAccountsByCategory = (accounts: any[], _prefix: string) => {
  const categories: { [key: string]: any } = {};

  // 调试：打印账户数据
  console.log(
    "账户数据:",
    accounts.map((acc) => ({ name: acc.name, balance: acc.balance }))
  );

  accounts.forEach((account) => {
    const parts = account.name.split(":");
    console.log(`处理账户: ${account.name}, parts:`, parts);

    let categoryName = "其他";

    if (parts.length > 1) {
      categoryName = parts[1]; // 取第二级作为分类名
    }

    if (!categories[categoryName]) {
      categories[categoryName] = {
        accounts: [],
        subGroups: {},
      };
    }

    // 从第三级开始构建子层级
    const remainingParts = parts.slice(2);
    console.log(`  remainingParts:`, remainingParts);

    if (remainingParts.length === 0) {
      // 如果没有更多层级，直接添加到accounts中
      categories[categoryName].accounts.push({
        name: formatAccountName(account.name.split(":").pop() || ""),
        balance: account.balance,
        fullName: account.name,
      });
    } else if (remainingParts.length === 1) {
      // 只有一级子账户，直接添加
      categories[categoryName].accounts.push({
        name: formatAccountName(remainingParts[0]),
        balance: account.balance,
        fullName: account.name,
      });
    } else {
      // 有多级子账户，按第一级分组
      const subGroupName = remainingParts[0];
      console.log(`  创建子分组: ${subGroupName}`);

      if (!categories[categoryName].subGroups[subGroupName]) {
        categories[categoryName].subGroups[subGroupName] = [];
      }

      // 剩余的层级作为子账户名称
      const finalAccountName = remainingParts
        .slice(1)
        .map((part: string) => formatAccountName(part))
        .join("-");
      console.log(`  子账户名称: ${finalAccountName}`);

      categories[categoryName].subGroups[subGroupName].push({
        name: finalAccountName,
        balance: account.balance,
        fullName: account.name,
      });
    }
  });

  // 构建最终的分类结构
  return Object.keys(categories).map((categoryName) => {
    const category = categories[categoryName];
    const allAccounts = [...category.accounts];

    // 添加子分组
    Object.keys(category.subGroups).forEach((subGroupName) => {
      const subGroupAccounts = category.subGroups[subGroupName];
      const subGroupTotal = subGroupAccounts.reduce(
        (sum: number, acc: any) => sum + (Number(acc.balance) || 0),
        0
      );

      // 为子分组创建一个汇总账户
      allAccounts.push({
        name: formatAccountName(subGroupName),
        balance: subGroupTotal,
        fullName: `${categoryName}-${subGroupName}`,
        isSubGroup: true,
        subAccounts: subGroupAccounts,
      });
    });

    // 根据账户类型决定汇总方式
    let total = allAccounts.reduce((sum, acc) => sum + Number(acc.balance), 0);
    // 负债类账户汇总后取相反数
    if (_prefix === "Liabilities") {
      total = -total;
    }

    const result = {
      name: formatCategoryName(categoryName),
      accounts: allAccounts,
      total: total,
    };

    // 调试：打印分组结果
    console.log(
      `分类 ${categoryName}:`,
      allAccounts.map((acc) => ({
        name: acc.name,
        isSubGroup: acc.isSubGroup,
        subAccounts: acc.subAccounts?.length || 0,
      }))
    );

    return result;
  });
};

// 加载资产负债表
const loadBalanceSheet = async () => {
  loading.value = true;
  try {
    balanceSheet.value = await getBalanceSheet(asOfDate.value);
  } catch (error) {
    console.error("加载资产负债表失败:", error);
    showToast("加载资产负债表失败");
  } finally {
    loading.value = false;
  }
};

// 加载损益表
const loadIncomeStatement = async () => {
  loading.value = true;
  try {
    if (startDate.value && endDate.value) {
      incomeStatement.value = await getIncomeStatement(
        startDate.value,
        endDate.value
      );
    }
  } catch (error) {
    console.error("加载损益表失败:", error);
    showToast("加载损益表失败");
  } finally {
    loading.value = false;
  }
};

// 加载趋势数据
const loadTrends = async () => {
  loading.value = true;
  try {
    trendsData.value = await getTrends(trendsMonths.value);
    generateTrendsChart();
  } catch (error) {
    console.error("加载趋势数据失败:", error);
    showToast("加载趋势数据失败");
  } finally {
    loading.value = false;
  }
};

// 生成趋势图表
const generateTrendsChart = () => {
  if (!trendsData.value?.trends) return;

  const isDark = themeStore.isDark;

  const periods = trendsData.value.trends.map((item: any) => item.period);
  const incomes = trendsData.value.trends.map((item: any) => item.total_income);
  const expenses = trendsData.value.trends.map((item: any) =>
    Math.abs(item.total_expenses)
  );
  const netIncomes = trendsData.value.trends.map(
    (item: any) => item.net_income
  );

  trendsOption.value = {
    title: {
      text: "收支趋势分析",
      textStyle: {
        fontSize: 14,
        color: isDark ? "#e8e8e8" : "#303133",
      },
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: isDark
        ? "rgba(40, 40, 40, 0.8)"
        : "rgba(255, 255, 255, 0.9)",
      borderColor: isDark ? "#434343" : "#dcdfe6",
      textStyle: {
        color: isDark ? "#e8e8e8" : "#303133",
      },
      formatter: (params: any) => {
        let result = `${params[0].axisValue}<br/>`;
        params.forEach((param: any) => {
          result += `${param.seriesName}: ${formatCurrency(param.value)}<br/>`;
        });
        return result;
      },
    },
    legend: {
      data: ["收入", "支出", "净收益"],
      bottom: 0,
      textStyle: {
        fontSize: 12,
        color: isDark ? "#c9c9c9" : "#606266",
      },
    },
    grid: {
      top: 40,
      bottom: 60,
      left: 10,
      right: 10,
      containLabel: true,
    },
    xAxis: {
      type: "category",
      data: periods,
      axisLabel: {
        fontSize: 10,
        rotate: 45,
        color: isDark ? "#c9c9c9" : "#606266",
      },
      axisLine: {
        lineStyle: {
          color: isDark ? "#434343" : "#dcdfe6",
        },
      },
    },
    yAxis: {
      type: "value",
      axisLabel: {
        fontSize: 10,
        color: isDark ? "#c9c9c9" : "#606266",
        formatter: (value: number) => {
          if (value >= 10000) {
            return (value / 10000).toFixed(1) + "万";
          }
          return value.toString();
        },
      },
      splitLine: {
        lineStyle: {
          color: isDark ? "#363636" : "#ebeef5",
        },
      },
    },
    series: [
      {
        name: "收入",
        type: "line",
        data: incomes,
        itemStyle: { color: isDark ? "#95d475" : "#67c23a" },
        lineStyle: { width: 2 },
      },
      {
        name: "支出",
        type: "line",
        data: expenses,
        itemStyle: { color: isDark ? "#ff7875" : "#f56c6c" },
        lineStyle: { width: 2 },
      },
      {
        name: "净收益",
        type: "line",
        data: netIncomes,
        itemStyle: { color: isDark ? "#79bbff" : "#409eff" },
        lineStyle: { width: 2 },
      },
    ],
  };
};

// 监听主题变化，重新生成图表
watch(
  () => themeStore.isDark,
  () => {
    if (activeTab.value === "trends") {
      generateTrendsChart();
    }
  }
);

// 加载月度报告
const loadMonthlyReport = async () => {
  loading.value = true;
  try {
    const [monthlyRes, ytdRes] = await Promise.all([
      getMonthlySummary(selectedYear.value, selectedMonth.value),
      getYearToDateSummary(selectedYear.value),
    ]);
    monthlySummary.value = monthlyRes;
    yearToDateSummary.value = ytdRes;
  } catch (error) {
    console.error("加载月度报告失败:", error);
    showToast("加载月度报告失败");
  } finally {
    loading.value = false;
  }
};

// 标签页切换处理
const onTabChange = (tabName: string) => {
  switch (tabName) {
    case "balance-sheet":
      loadBalanceSheet();
      break;
    case "income-statement":
      if (startDate.value && endDate.value) {
        loadIncomeStatement();
      }
      break;
    case "trends":
      loadTrends();
      break;
    case "monthly":
      loadMonthlyReport();
      break;
  }
};

const onTrendsConfirm = ({ selectedOptions }: any) => {
  trendsMonths.value = selectedOptions[0].value;
  showTrendsPicker.value = false;
  loadTrends();
};

const onYearConfirm = ({ selectedOptions }: any) => {
  selectedYear.value = selectedOptions[0].value;
  showYearPicker.value = false;
  loadMonthlyReport();
};

const onMonthConfirm = ({ selectedOptions }: any) => {
  selectedMonth.value = selectedOptions[0].value;
  showMonthPicker.value = false;
  loadMonthlyReport();
};

// 日历确认处理函数
const onAsOfDateConfirm = (date: Date) => {
  asOfDate.value = date.toLocaleDateString("en-CA");
  showAsOfDateCalendar.value = false;
  loadBalanceSheet();
};

// 获取默认日期范围
const getDefaultDateRange = () => {
  if (startDate.value && endDate.value) {
    return [new Date(startDate.value), new Date(endDate.value)];
  }
  // 默认返回本月第一天到今天
  const today = new Date();
  const thisMonthStart = new Date(today.getFullYear(), today.getMonth(), 1);
  return [thisMonthStart, today];
};

// 日期范围确认处理函数
const onDateRangeConfirm = (dates: Date[]) => {
  if (dates && dates.length === 2) {
    startDate.value = dates[0].toLocaleDateString("en-CA");
    endDate.value = dates[1].toLocaleDateString("en-CA");
    showDateRangeCalendar.value = false;
    loadIncomeStatement();
  }
};

onMounted(() => {
  // 默认加载资产负债表
  loadBalanceSheet();
});
</script>

<style scoped>
.h5-reports {
  background-color: var(--bg-color-secondary);
  min-height: 100vh;
  padding-bottom: 20px;
}

/* 固定标签页容器 */
.tabs-fixed-container {
  position: fixed;
  top: 46px; /* 导航栏的高度 */
  left: 0;
  right: 0;
  z-index: 999;
  background-color: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
}

/* 报表类型选择器 */
.report-type-selector {
  background-color: transparent;
}

/* 报表内容包装器 */
.reports-content-wrapper {
  margin-top: 50px; /* 为固定标签页留出空间 */
}
.report-type-selector :deep(.van-tabs__nav) {
  background-color: var(--bg-color);
}
.report-type-selector :deep(.van-tab) {
  color: var(--text-color-secondary);
}
.report-type-selector :deep(.van-tab--active) {
  color: var(--color-primary);
}
.report-type-selector :deep(.van-tabs__line) {
  background-color: var(--color-primary);
}

/* 报表内容区域 */
.report-content {
  padding-bottom: 60px;
}

/* 日期选择器 */
.date-selector,
.date-range-selector,
.trends-selector,
.monthly-selector {
  margin-bottom: 16px;
}

/* 资产负债表样式 */
.balance-sheet {
  padding: 0;
}

.account-list {
  padding: 0;
}

.account-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  border-bottom: 1px solid var(--border-color-lighter);
  font-size: 14px;
}

.account-item:last-child {
  border-bottom: none;
}

.clickable-item {
  cursor: pointer;
}

.clickable-item:hover {
  background-color: var(--bg-color-tertiary);
}

.account-name {
  flex: 1;
  color: var(--text-color);
}

.account-amount {
  color: var(--text-color-secondary);
  font-family: "Monaco", "Menlo", "Ubuntu Mono", monospace;
  font-size: 13px;
}

/* 子分组样式 */
.sub-group {
  margin-bottom: 8px;
}

.sub-group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 16px;
  background-color: var(--bg-color-tertiary);
  border-bottom: 1px solid var(--border-color);
  font-weight: 500;
}

.sub-group-name {
  flex: 1;
  color: var(--text-color);
  font-size: 14px;
}

.sub-group-amount {
  color: var(--text-color-secondary);
  font-family: "Monaco", "Menlo", "Ubuntu Mono", monospace;
  font-size: 13px;
  font-weight: 600;
}

.sub-account-list {
  background-color: var(--bg-color);
}

.sub-account-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px 8px 32px; /* 左侧增加缩进表示层级 */
  border-bottom: 1px solid var(--border-color-lighter);
  font-size: 14px;
}

.sub-account-item:last-child {
  border-bottom: none;
}

/* 子分组折叠样式 */
.sub-group-collapse {
  margin: 0;
}

.sub-group-collapse :deep(.van-collapse-item__title) {
  background-color: var(--bg-color-tertiary);
  font-size: 14px;
  font-weight: 500;
  padding: 10px 16px;
}

.sub-group-collapse :deep(.van-collapse-item__content) {
  padding: 0;
  background-color: var(--bg-color);
}

.total-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background-color: var(--bg-color-tertiary);
  border-top: 1px solid var(--border-color);
  font-weight: 600;
  color: var(--text-color);
}

.total-label {
  font-size: 14px;
}

.total-amount {
  font-family: "Monaco", "Menlo", "Ubuntu Mono", monospace;
  font-size: 14px;
}

/* 损益表样式 */
.income-statement {
  padding: 0;
}

.net-income-card {
  padding: 20px;
  text-align: center;
  background-color: var(--bg-color);
  margin: 16px;
  border-radius: 8px;
  border-left: 4px solid var(--color-primary);
}

.net-income-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 8px;
}

.net-income-label {
  font-size: 14px;
  color: var(--text-color-placeholder);
}

/* 趋势分析样式 */
.trends-chart {
  margin-top: 16px;
}

.chart-container {
  padding: 16px;
  background-color: var(--bg-color);
}

/* 月度报告样式 */
.monthly-summary {
  padding: 0;
}

.summary-cards {
  padding: 16px;
}

.summary-card {
  background-color: var(--bg-color);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  margin-bottom: 8px;
}

.summary-card.income {
  border-left: 4px solid var(--color-success);
}

.summary-card.expense {
  border-left: 4px solid var(--color-danger);
}

.card-value {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 4px;
}

.summary-card.income .card-value {
  color: var(--color-success);
}
html[data-theme="dark"] .summary-card.income .card-value {
  color: #95d475;
}

.summary-card.expense .card-value {
  color: var(--color-danger);
}
html[data-theme="dark"] .summary-card.expense .card-value {
  color: #ff7875;
}

.card-label {
  font-size: 12px;
  color: var(--text-color-placeholder);
}

.net-card {
  background-color: var(--bg-color);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  margin-top: 8px;
  border-left: 4px solid var(--color-primary);
}

.net-value {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 4px;
}

.net-label {
  font-size: 12px;
  color: var(--text-color-placeholder);
}

.assets-card {
  background-color: var(--bg-color);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
  margin-top: 8px;
  border-left: 4px solid var(--color-info);
}

.assets-value {
  font-size: 18px;
  font-weight: bold;
  color: var(--color-info);
  margin-bottom: 4px;
}

.assets-label {
  font-size: 12px;
  color: var(--text-color-placeholder);
}

.ytd-summary {
  margin-top: 16px;
}

/* 通用样式 */
:deep(.van-cell-group--inset) {
  margin: 16px;
}

:deep(.van-cell-group__title) {
  padding-left: 16px;
  font-weight: 600;
  color: var(--text-color);
}

:deep(.van-collapse-item__content) {
  padding: 0;
}

:deep(.van-collapse-item__title) {
  font-weight: 500;
}

:deep(.van-tabs__line) {
  background-color: var(--color-primary);
}

:deep(.van-tab--active) {
  color: var(--color-primary);
}

:deep(.positive) {
  color: #07c160 !important;
  font-weight: 500;
}
html[data-theme="dark"] :deep(.positive) {
  color: #95d475 !important;
}

:deep(.negative) {
  color: #ee0a24 !important;
  font-weight: 500;
}
html[data-theme="dark"] :deep(.negative) {
  color: #ff7875 !important;
}

/* 加载状态 */
:deep(.van-loading) {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 999;
}

/* 移动端优化 */
@media (max-width: 375px) {
  .account-item {
    padding: 6px 12px;
    font-size: 13px;
  }

  .account-amount {
    font-size: 12px;
  }

  .total-row {
    padding: 10px 12px;
    font-size: 13px;
  }

  .total-amount {
    font-size: 13px;
  }

  .summary-card {
    padding: 12px;
  }

  .card-value {
    font-size: 14px;
  }

  .net-value {
    font-size: 18px;
  }

  .assets-value {
    font-size: 16px;
  }

  .net-income-value {
    font-size: 20px;
  }
}

/* 横屏适配 */
@media (orientation: landscape) {
  .chart-container {
    height: 250px;
  }

  :deep(.v-chart) {
    height: 250px !important;
  }
}

/* 大屏手机适配 */
@media (min-width: 414px) {
  .account-item {
    padding: 10px 16px;
  }

  .summary-cards {
    padding: 20px;
  }

  .summary-card {
    padding: 20px;
  }
}
</style>
