import api from '@/utils/api'

export interface Transaction {
  date: string
  flag: string
  payee?: string
  narration: string
  tags?: string[]
  links?: string[]
  postings: Posting[]
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