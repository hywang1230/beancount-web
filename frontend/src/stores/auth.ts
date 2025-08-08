import { defineStore } from "pinia";
import { computed, ref } from "vue";

export interface User {
  username: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export const useAuthStore = defineStore("auth", () => {
  // 状态
  const token = ref<string | null>(null);
  const user = ref<User | null>(null);
  const isLoading = ref(false);
  const lastAuthCheck = ref<number>(0); // 上次认证检查的时间戳
  const authCheckInterval = 5 * 60 * 1000; // 认证检查间隔：5分钟

  // 计算属性
  const isAuthenticated = computed(() => !!token.value);

  // 从localStorage加载token
  const loadToken = () => {
    const savedToken = localStorage.getItem("beancount-auth-token");
    if (savedToken) {
      token.value = savedToken;
    }
  };

  // 保存token到localStorage
  const saveToken = (newToken: string) => {
    token.value = newToken;
    localStorage.setItem("beancount-auth-token", newToken);
  };

  // 清除token
  const clearToken = () => {
    token.value = null;
    user.value = null;
    lastAuthCheck.value = 0;
    localStorage.removeItem("beancount-auth-token");
  };

  // 登录
  const login = async (credentials: LoginCredentials): Promise<void> => {
    isLoading.value = true;
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "登录失败");
      }

      const authData: AuthToken = await response.json();
      saveToken(authData.access_token);

      // 获取用户信息
      await fetchUserInfo();
    } catch (error) {
      clearToken();
      throw error;
    } finally {
      isLoading.value = false;
    }
  };

  // 登出
  const logout = async (): Promise<void> => {
    try {
      if (token.value) {
        await fetch("/api/auth/logout", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token.value}`,
          },
        });
      }
    } catch (error) {
      console.error("登出请求失败:", error);
    } finally {
      clearToken();
    }
  };

  // 获取用户信息
  const fetchUserInfo = async (): Promise<void> => {
    if (!token.value) return;

    try {
      const response = await fetch("/api/auth/me", {
        headers: {
          Authorization: `Bearer ${token.value}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          clearToken();
          return;
        }
        throw new Error("获取用户信息失败");
      }

      const userData: User = await response.json();
      user.value = userData;
    } catch (error) {
      console.error("获取用户信息失败:", error);
      clearToken();
    }
  };

  // 检查token有效性（优化版本）
  const checkAuth = async (forceCheck = false): Promise<boolean> => {
    if (!token.value) return false;

    // 如果用户信息已存在且不是强制检查，直接返回true
    if (user.value && !forceCheck) {
      return true;
    }

    // 检查是否需要重新验证（基于时间间隔）
    const now = Date.now();
    if (
      !forceCheck &&
      user.value &&
      now - lastAuthCheck.value < authCheckInterval
    ) {
      return true;
    }

    try {
      await fetchUserInfo();
      lastAuthCheck.value = now;
      return !!user.value;
    } catch (error) {
      clearToken();
      return false;
    }
  };

  // 轻量级认证检查（仅验证token存在和用户信息缓存）
  const isValidSession = (): boolean => {
    return !!(token.value && user.value);
  };

  return {
    // 状态
    token,
    user,
    isLoading,

    // 计算属性
    isAuthenticated,

    // 方法
    loadToken,
    login,
    logout,
    fetchUserInfo,
    checkAuth,
    isValidSession,
  };
});
