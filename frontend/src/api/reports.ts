import api from '@/utils/api'

export interface AccountInfo {
  name: string
  balance: number
  currency: string
  account_type: string
  // 添加原币金额和币种信息，用于多币种显示
  original_balance?: number
  original_currency?: string
}

export interface BalanceSheet {
  accounts: AccountInfo[]
  total_assets: number
  total_liabilities: number
  total_equity: number
  net_worth: number  // 净资产
  currency: string
}

export interface IncomeStatement {
  income_accounts: AccountInfo[]
  expense_accounts: AccountInfo[]
  total_income: number
  total_expenses: number
  net_income: number
  currency: string
}

// 获取资产负债表
export const getBalanceSheet = (asOfDate?: string) => {
  return api.get('/reports/balance-sheet', { 
    params: asOfDate ? { as_of_date: asOfDate } : {} 
  })
}

// 获取损益表
export const getIncomeStatement = (startDate?: string, endDate?: string) => {
  const params: any = {}
  if (startDate) params.start_date = startDate
  if (endDate) params.end_date = endDate
  
  return api.get('/reports/income-statement', { params })
}

// 获取月度汇总
export const getMonthlySummary = (year?: number, month?: number) => {
  const params: any = {}
  if (year) params.year = year
  if (month) params.month = month
  
  return api.get('/reports/monthly-summary', { params })
}

// 获取年度至今汇总
export const getYearToDateSummary = (year?: number) => {
  return api.get('/reports/year-to-date', { 
    params: year ? { year } : {} 
  })
}

// 获取趋势分析
export const getTrends = (months: number = 12) => {
  return api.get('/reports/trends', { params: { months } })
} 