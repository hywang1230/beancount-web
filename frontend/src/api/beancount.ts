/**
 * Beancount 选项和价格管理 API
 */
import api from '@/utils/api'

// 主币种相关接口
export interface OperatingCurrencyResponse {
  operating_currency: string
}

export interface OperatingCurrencyUpdate {
  operating_currency: string
}

// 价格相关接口
export interface PriceEntry {
  date: string
  from_currency: string
  to_currency: string
  rate: number | string // 后端可能返回 Decimal 作为字符串
}

export interface PriceCreate {
  date: string
  from_currency: string
  to_currency?: string
  rate: number
}

export interface PriceResponse {
  prices: PriceEntry[]
  total: number
  page: number
  page_size: number
}

export interface PriceFilter {
  from_currency?: string
  to_currency?: string
  start_date?: string
  end_date?: string
  date?: string
  page?: number
  page_size?: number
}

export interface EffectiveRateResponse {
  rate: number | null
  date: string
  from_currency: string
  to_currency: string
  message?: string
}

// 主币种API
export const operatingCurrencyApi = {
  // 获取当前主币种
  getCurrent: (): Promise<OperatingCurrencyResponse> => {
    return api.get('/beancount/operating_currency')
  },

  // 更新主币种
  update: (data: OperatingCurrencyUpdate): Promise<{ message: string; success: boolean }> => {
    return api.put('/beancount/operating_currency', data)
  }
}

// 价格管理API
export const pricesApi = {
  // 获取价格列表
  getList: (params?: PriceFilter): Promise<PriceResponse> => {
    return api.get('/beancount/prices', { params })
  },

  // 创建或更新价格
  create: (data: PriceCreate): Promise<{ message: string; success: boolean }> => {
    return api.post('/beancount/prices', data)
  },

  // 删除价格
  delete: (params: {
    date: string
    from_currency: string
    to_currency?: string
  }): Promise<{ message: string; success: boolean }> => {
    return api.delete('/beancount/prices', { params })
  },

  // 获取有效汇率
  getEffectiveRate: (params: {
    date: string
    from_currency: string
    to_currency?: string
  }): Promise<EffectiveRateResponse> => {
    return api.get('/beancount/prices/effective_rate', { params })
  }
}
