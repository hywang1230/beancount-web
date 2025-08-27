import api from '@/utils/api'

export interface AIConfig {
  id: number
  key: string
  value: string | null
  description: string | null
  created_at: string
  updated_at: string
}

export interface AIConfigCreate {
  key: string
  value?: string
  description?: string
}

export interface AIConfigUpdate {
  value?: string
  description?: string
}

export interface AIConfigDict {
  configs: Record<string, string>
}

export interface AIChatRequest {
  message: string
  context?: Record<string, any>
}

export interface AIChatResponse {
  intent?: string
  status: string
  data: Record<string, any>
  chain_id?: string
  message: string
}

export interface AIConfirmRequest {
  token: string
  action: string
  data?: Record<string, any>
}

// AI配置管理API
export const aiConfigApi = {
  // 获取所有配置
  getConfigs: (): Promise<AIConfig[]> => {
    return api.get('/ai/config')
  },

  // 获取配置字典
  getConfigsDict: (): Promise<AIConfigDict> => {
    return api.get('/ai/config/dict')
  },

  // 获取单个配置
  getConfig: (key: string): Promise<AIConfig> => {
    return api.get(`/ai/config/${key}`)
  },

  // 创建配置
  createConfig: (data: AIConfigCreate): Promise<AIConfig> => {
    return api.post('/ai/config', data)
  },

  // 更新配置
  updateConfig: (key: string, data: AIConfigUpdate): Promise<AIConfig> => {
    return api.put(`/ai/config/${key}`, data)
  },

  // 删除配置
  deleteConfig: (key: string): Promise<{ message: string }> => {
    return api.delete(`/ai/config/${key}`)
  },



  // 验证配置
  validateConfig: (): Promise<{
    valid: boolean
    errors: Record<string, string>
    message: string
  }> => {
    return api.post('/ai/config/validate')
  }
}

// AI聊天API
export const aiChatApi = {
  // 发送聊天消息
  chat: (data: AIChatRequest): Promise<AIChatResponse> => {
    return api.post('/ai/chat', data)
  },

  // 确认操作
  confirm: (data: AIConfirmRequest): Promise<{
    message: string
    token: string
    status: string
  }> => {
    return api.post('/ai/confirm', data)
  }
}
