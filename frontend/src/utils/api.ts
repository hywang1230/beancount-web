import axios from 'axios'

// 根据环境确定API基础URL
const getBaseURL = () => {
  // 如果是开发环境，使用localhost
  if (import.meta.env.DEV) {
    return 'http://localhost:8000/api'
  }
  // 生产环境使用相对路径
  return '/api'
}

const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 在这里可以添加认证token等
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // 统一错误处理
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default api 