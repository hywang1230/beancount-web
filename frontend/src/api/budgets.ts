import api from "@/utils/api";

export interface Budget {
  id?: number;
  category: string;
  period_type: string;
  period_value: string;
  amount: number;
  currency: string;
  created_at?: string;
  updated_at?: string;
}

export interface BudgetProgress {
  budget: Budget;
  spent: number;
  remaining: number;
  percentage: number;
  is_exceeded: boolean;
  days_remaining: number | null;
}

export interface BudgetSummary {
  total_budget: number;
  total_spent: number;
  total_remaining: number;
  overall_percentage: number;
  budgets: BudgetProgress[];
  currency: string;
}

// 创建预算
export const createBudget = (data: Omit<Budget, 'id' | 'created_at' | 'updated_at'>): Promise<Budget> => {
  return api.post("/budgets/", data);
};

// 获取预算列表
export const getBudgets = (params?: {
  period_type?: string;
  period_value?: string;
}): Promise<Budget[]> => {
  return api.get("/budgets/", { params });
};

// 获取预算汇总
export const getBudgetSummary = (params?: {
  period_type?: string;
  period_value?: string;
}): Promise<BudgetSummary> => {
  return api.get("/budgets/summary", { params });
};

// 获取预算详情
export const getBudget = (id: number): Promise<Budget> => {
  return api.get(`/budgets/${id}`);
};

// 获取预算进度
export const getBudgetProgress = (id: number): Promise<BudgetProgress> => {
  return api.get(`/budgets/${id}/progress`);
};

// 更新预算
export const updateBudget = (id: number, data: { amount: number }): Promise<Budget> => {
  return api.put(`/budgets/${id}`, data);
};

// 删除预算
export const deleteBudget = (id: number): Promise<{ success: boolean; message: string }> => {
  return api.delete(`/budgets/${id}`);
};

