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
  conversation_id?: string
  chat_history?: Array<{ role: string; content: string }>
}

export interface AIChatResponse {
  intent?: string
  status: string
  data: Record<string, any>
  chain_id?: string
  message: string
  conversation_id?: string
  context_used?: boolean
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

  // 创建流式聊天连接
  chatStream: (data: AIChatRequest, onMessage: (chunk: any) => void, onError?: (error: any) => void, onComplete?: () => void): void => {
    // 直接从localStorage获取token，使用正确的键名
    const token = localStorage.getItem('beancount-auth-token')
    
    // 创建POST请求发送数据，然后建立SSE连接
    fetch('/api/ai/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': token ? `Bearer ${token}` : ''
      },
      body: JSON.stringify(data)
    }).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      // 创建EventSource来接收流式数据
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      const readStream = async () => {
        try {
          while (true) {
            const { done, value } = await reader!.read()
            if (done) break
            
            const chunk = decoder.decode(value, { stream: true })
            const lines = chunk.split('\n')
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                try {
                  const data = JSON.parse(line.slice(6))
                  onMessage(data)
                  
                  if (data.type === 'done' || data.type === 'message_complete') {
                    onComplete?.()
                    return
                  }
                } catch (e) {
                  console.error('解析SSE数据失败:', e)
                }
              }
            }
          }
        } catch (error) {
          console.error('读取流式数据失败:', error)
          onError?.(error)
        }
      }
      
      readStream()
    }).catch(error => {
      console.error('流式聊天请求失败:', error)
      onError?.(error)
    })
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

// AI上下文管理API
export const aiContextApi = {
  // 初始化上下文配置
  initConfigs: (): Promise<{
    message: string
    created_count: number
  }> => {
    return api.post('/ai/context/init')
  },

  // 获取上下文统计信息
  getStats: (): Promise<{
    stats: {
      context_enabled: boolean
    }
    message: string
  }> => {
    return api.get('/ai/context/stats')
  },

  // 清除指定对话的上下文
  clearConversation: (conversationId: string): Promise<{
    message: string
    conversation_id: string
  }> => {
    return api.delete(`/ai/context/conversation/${conversationId}`)
  },

  // 清理过期的对话缓存
  cleanupExpired: (): Promise<{
    message: string
    cleaned_count: number
  }> => {
    return api.post('/ai/context/cleanup')
  },


}
