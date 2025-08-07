import { useAuthStore } from "@/stores/auth";
import axios from "axios";

// 根据环境确定API基础URL
const getBaseURL = (): string => {
  // 如果是开发环境，使用localhost
  // @ts-ignore
  // if (import.meta.env && import.meta.env.DEV) {
  //   return 'http://localhost:8000/api'
  // }
  // 生产环境使用相对路径
  return "/api";
};

const api = axios.create({
  baseURL: getBaseURL(),
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加认证token
    const authStore = useAuthStore();
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    // 统一错误处理
    console.error("API Error:", error);

    // 处理401未授权错误
    if (error.response?.status === 401) {
      const authStore = useAuthStore();
      authStore.logout();
      // 如果不是登录页面，重定向到登录页
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }

    return Promise.reject(error);
  }
);

export default api;
