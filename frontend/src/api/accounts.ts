import api from '@/utils/api'

export interface AccountStructure {
  name: string
  full_path: string
  children: AccountStructure[]
}

export interface AccountCreateRequest {
  name: string
  open_date: string
  currencies?: string[]
  booking_method?: string
}

export interface AccountCloseRequest {
  name: string
  close_date: string
}

export interface AccountRestoreRequest {
  name: string
}

export interface AccountActionResponse {
  success: boolean
  message: string
  account_name: string
}

// 获取所有账户
export const getAllAccounts = () => {
  return api.get('/accounts/')
}

// 获取已归档账户
export const getArchivedAccounts = () => {
  return api.get('/accounts/archived')
}

// 获取账户结构
export const getAccountStructure = () => {
  return api.get('/accounts/structure')
}

// 按类型获取账户
export const getAccountsByType = () => {
  return api.get('/accounts/types')
}

// 账户建议
export const suggestAccounts = (partialName: string) => {
  return api.get(`/accounts/suggest/${partialName}`)
}

// 创建账户
export const createAccount = (data: AccountCreateRequest): Promise<AccountActionResponse> => {
  return api.post('/accounts/create', data)
}

// 归档账户
export const closeAccount = (data: AccountCloseRequest): Promise<AccountActionResponse> => {
  return api.post('/accounts/close', data)
}

// 恢复账户
export const restoreAccount = (data: AccountRestoreRequest): Promise<AccountActionResponse> => {
  return api.post('/accounts/restore', data)
} 