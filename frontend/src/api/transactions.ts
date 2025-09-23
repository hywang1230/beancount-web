import api from "@/utils/api";

export interface Transaction {
  date: string;
  flag: string;
  payee?: string;
  narration: string;
  tags?: string[];
  links?: string[];
  postings: Posting[];
  // 添加唯一标识字段
  filename?: string;
  lineno?: number;
  transaction_id?: string; // 由filename+lineno组成的唯一标识
}

export interface Posting {
  account: string;
  amount?: string | number;
  currency?: string;
  price?: any;
  // 原始金额和货币信息（用于汇率转换显示）
  original_amount?: string | number;
  original_currency?: string;
}

export interface TransactionFilter {
  start_date?: string;
  end_date?: string;
  account?: string;
  payee?: string;
  narration?: string;
  transaction_type?: string; // 交易类型：income, expense, transfer
  page?: number;
  page_size?: number;
}

export interface TransactionResponse {
  data: Transaction[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// 获取交易列表
export const getTransactions = (
  params?: TransactionFilter
): Promise<TransactionResponse> => {
  return api.get("/transactions/", { params });
};

// 校验交易数据
export const validateTransaction = (data: Transaction) => {
  return api.post("/transactions/validate", data);
};

// 创建新交易
export const createTransaction = (data: Transaction) => {
  return api.post("/transactions/", data);
};

// 获取最近交易
export const getRecentTransactions = (days: number = 30) => {
  return api.get("/transactions/recent", { params: { days } });
};

// 获取账户列表
export const getAccounts = () => {
  return api.get("/transactions/accounts");
};

// 获取收付方列表
export const getPayees = () => {
  return api.get("/transactions/payees");
};

// 根据transaction_id获取单个交易
export const getTransactionById = (transactionId: string) => {
  return api.get(`/transactions/${transactionId}`);
};

// 根据transaction_id更新交易
export const updateTransaction = (transactionId: string, data: Transaction) => {
  return api.put(`/transactions/${transactionId}`, data);
};

// 根据transaction_id删除交易
export const deleteTransaction = (transactionId: string) => {
  return api.delete(`/transactions/${transactionId}`);
};

// 获取指定账户的日记账
export const getTransactionsByAccount = (
  account: string,
  startDate?: string,
  endDate?: string
): Promise<Transaction[]> => {
  const params: any = { account };
  if (startDate) {
    params.start_date = startDate;
  }
  if (endDate) {
    params.end_date = endDate;
  }
  return api.get("/transactions/account-journal", { params });
};

// 获取可用年份列表
export const getAvailableYears = (): Promise<number[]> => {
  return api.get("/transactions/years");
};

// 创建年份文件
export const createYearlyFile = (year: number) => {
  return api.post(`/transactions/years/${year}/create`);
};

// 按年份迁移交易
export const migrateTransactionsByYear = () => {
  return api.post("/transactions/migrate-by-year");
};

// 清理空的年份文件
export const cleanupEmptyYearlyFiles = () => {
  return api.delete("/transactions/years/cleanup");
};
