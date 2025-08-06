import api from "@/utils/api";

export interface RecurringTransaction {
  id: string;
  name: string;
  description?: string;
  recurrence_type: "daily" | "weekly" | "weekdays" | "monthly";
  start_date: string;
  end_date?: string | null;
  weekly_days?: number[];
  monthly_days?: number[];
  flag: string;
  payee?: string;
  narration: string;
  tags: string[];
  links: string[];
  postings: Array<{
    account: string;
    amount?: number;
    currency?: string;
  }>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_executed?: string;
  next_execution?: string;
}

export interface RecurringTransactionCreate {
  name: string;
  description?: string;
  recurrence_type: "daily" | "weekly" | "weekdays" | "monthly";
  start_date: string;
  end_date?: string | null;
  weekly_days?: number[];
  monthly_days?: number[];
  flag?: string;
  payee?: string;
  narration: string;
  tags?: string[];
  links?: string[];
  postings: Array<{
    account: string;
    amount?: number;
    currency?: string;
  }>;
  is_active?: boolean;
}

export interface RecurringTransactionUpdate {
  name?: string;
  description?: string;
  recurrence_type?: "daily" | "weekly" | "weekdays" | "monthly";
  start_date?: string;
  end_date?: string | null;
  weekly_days?: number[];
  monthly_days?: number[];
  flag?: string;
  payee?: string;
  narration?: string;
  tags?: string[];
  links?: string[];
  postings?: Array<{
    account: string;
    amount?: number;
    currency?: string;
  }>;
  is_active?: boolean;
}

export interface ExecutionLog {
  id: string;
  recurring_transaction_id: string;
  execution_date: string;
  success: boolean;
  error_message?: string;
  created_transaction_id?: string;
  created_at: string;
}

export interface ExecutionResult {
  success: boolean;
  message: string;
  executed_count: number;
  failed_count: number;
  details: Array<{
    name: string;
    success: boolean;
    message: string;
  }>;
}

export interface SchedulerJob {
  id: string;
  name: string;
  next_run?: string;
  trigger: string;
}

// 周期记账API
export const recurringApi = {
  // 创建周期记账
  create: (data: RecurringTransactionCreate): Promise<RecurringTransaction> =>
    api.post("/recurring/", data),

  // 获取周期记账列表
  list: (activeOnly = false): Promise<RecurringTransaction[]> =>
    api.get("/recurring/", { params: { active_only: activeOnly } }),

  // 获取单个周期记账
  get: (id: string): Promise<RecurringTransaction> =>
    api.get(`/recurring/${id}`),

  // 更新周期记账
  update: (
    id: string,
    data: RecurringTransactionUpdate
  ): Promise<RecurringTransaction> => api.put(`/recurring/${id}`, data),

  // 删除周期记账
  delete: (id: string): Promise<{ message: string; success: boolean }> =>
    api.delete(`/recurring/${id}`),

  // 切换启用状态
  toggle: (id: string): Promise<RecurringTransaction> =>
    api.put(`/recurring/${id}/toggle`),

  // 手动执行周期记账
  execute: (executionDate?: string): Promise<ExecutionResult> =>
    api.post("/recurring/execute", null, {
      params: executionDate ? { execution_date: executionDate } : {},
    }),

  // 获取执行日志
  getLogs: (transactionId?: string, days = 30): Promise<ExecutionLog[]> =>
    api.get("/recurring/logs/execution", {
      params: {
        ...(transactionId && { transaction_id: transactionId }),
        days,
      },
    }),

  // 手动触发定时任务
  triggerScheduler: (): Promise<{ message: string; success: boolean }> =>
    api.post("/recurring/scheduler/trigger"),

  // 获取调度器任务状态
  getSchedulerJobs: (): Promise<SchedulerJob[]> =>
    api.get("/recurring/scheduler/jobs"),
};
