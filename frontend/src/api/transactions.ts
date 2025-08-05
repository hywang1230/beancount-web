import api from '@/utils/api'

export interface Transaction {
  date: string
  flag: string
  payee?: string
  narration: string
  tags?: string[]
  links?: string[]
  postings: Posting[]
  // 添加唯一标识字段
  filename?: string
  lineno?: number
  transaction_id?: string  // 由filename+lineno组成的唯一标识
}

export interface Posting {
  account: string
  amount?: string | number
  currency?: string
  price?: any
}

export interface TransactionFilter {
  start_date?: string
  end_date?: string
  account?: string
  payee?: string
  narration?: string
  transaction_type?: string  // 交易类型：income, expense, transfer
  page?: number
  page_size?: number
}

export interface TransactionResponse {
  data: Transaction[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 获取交易列表
export const getTransactions = (params?: TransactionFilter): Promise<TransactionResponse> => {
  return api.get('/transactions/', { params })
}

// 创建新交易
export const createTransaction = (data: Transaction) => {
  return api.post('/transactions/', data)
}

// 获取最近交易
export const getRecentTransactions = (days: number = 30) => {
  return api.get('/transactions/recent', { params: { days } })
}

// 获取账户列表
export const getAccounts = () => {
  return api.get('/transactions/accounts')
}

// 获取收付方列表
export const getPayees = () => {
  return api.get('/transactions/payees')
}

// 根据transaction_id获取单个交易
export const getTransactionById = (transactionId: string) => {
  return api.get(`/transactions/${transactionId}`)
}

// 根据transaction_id更新交易
export const updateTransaction = (transactionId: string, data: Transaction) => {
  return api.put(`/transactions/${transactionId}`, data)
}

// 根据transaction_id删除交易
export const deleteTransaction = (transactionId: string) => {
  return api.delete(`/transactions/${transactionId}`)
} 