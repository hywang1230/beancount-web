import { useAuthStore } from "@/stores/auth";
import axios, { AxiosRequestConfig } from "axios";

const getBaseURL = (): string => {
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
    // 处理取消请求的情况
    if (axios.isCancel(error)) {
      return Promise.reject({ cancelled: true, message: error.message });
    }

    // 统一错误处理
    if ((import.meta as any).env?.DEV) {
      console.error("API Error:", error);
    }

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

// 可取消的请求接口
export interface CancellableRequest<T> {
  promise: Promise<T>;
  cancel: () => void;
}

// 创建可取消的GET请求
export function createCancellableGet<T = any>(
  url: string,
  config?: AxiosRequestConfig
): CancellableRequest<T> {
  const controller = new AbortController();
  const promise = api.get<any, T>(url, {
    ...config,
    signal: controller.signal,
  });

  return {
    promise,
    cancel: () => controller.abort(),
  };
}

// 创建可取消的POST请求
export function createCancellablePost<T = any>(
  url: string,
  data?: any,
  config?: AxiosRequestConfig
): CancellableRequest<T> {
  const controller = new AbortController();
  const promise = api.post<any, T>(url, data, {
    ...config,
    signal: controller.signal,
  });

  return {
    promise,
    cancel: () => controller.abort(),
  };
}

// 防抖工具函数
export function createDebounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): T & { cancel: () => void } {
  let timeoutId: NodeJS.Timeout | null = null;

  const debounced = ((...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    return new Promise<ReturnType<T>>((resolve, reject) => {
      timeoutId = setTimeout(async () => {
        try {
          const result = await func(...args);
          resolve(result);
        } catch (error) {
          reject(error);
        }
      }, delay);
    });
  }) as T & { cancel: () => void };

  debounced.cancel = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
  };

  return debounced;
}

// 请求管理器 - 用于管理多个并发请求
export class RequestManager {
  private requests: Map<string, CancellableRequest<any>> = new Map();

  // 添加请求
  add<T>(key: string, request: CancellableRequest<T>): CancellableRequest<T> {
    // 如果已存在同key的请求，先取消
    this.cancel(key);
    this.requests.set(key, request);

    // 请求完成后自动清理
    request.promise.finally(() => {
      this.requests.delete(key);
    });

    return request;
  }

  // 取消特定请求
  cancel(key: string): void {
    const request = this.requests.get(key);
    if (request) {
      request.cancel();
      this.requests.delete(key);
    }
  }

  // 取消所有请求
  cancelAll(): void {
    this.requests.forEach((request) => request.cancel());
    this.requests.clear();
  }

  // 检查是否有进行中的请求
  hasRequest(key: string): boolean {
    return this.requests.has(key);
  }
}

export default api;
