import api from '@/utils/api'

export interface AccountStructure {
  name: string
  full_path: string
  children: AccountStructure[]
}

// 获取所有账户
export const getAllAccounts = () => {
  return api.get('/accounts/')
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