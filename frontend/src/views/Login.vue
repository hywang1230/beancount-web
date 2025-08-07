<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">豆瓣记账</h1>
        <p class="login-subtitle">请登录您的账户</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username" class="form-label">用户名</label>
          <input
            id="username"
            v-model="loginForm.username"
            type="text"
            class="form-input"
            placeholder="请输入用户名"
            required
            :disabled="authStore.isLoading"
          />
        </div>

        <div class="form-group">
          <label for="password" class="form-label">密码</label>
          <input
            id="password"
            v-model="loginForm.password"
            type="password"
            class="form-input"
            placeholder="请输入密码"
            required
            :disabled="authStore.isLoading"
          />
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <button
          type="submit"
          class="login-button"
          :disabled="
            authStore.isLoading || !loginForm.username || !loginForm.password
          "
        >
          <span v-if="authStore.isLoading" class="loading-spinner"></span>
          {{ authStore.isLoading ? "登录中..." : "登录" }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { getDefaultRoute } from "@/utils/device";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const authStore = useAuthStore();

const loginForm = ref({
  username: "",
  password: "",
});

const errorMessage = ref("");

const handleLogin = async () => {
  errorMessage.value = "";

  try {
    await authStore.login(loginForm.value);

    // 登录成功，根据设备类型跳转到对应页面
    const redirectPath =
      (router.currentRoute.value.query.redirect as string) || getDefaultRoute();
    router.push(redirectPath);
  } catch (error: any) {
    errorMessage.value = error.message || "登录失败，请重试";
  }
};

// 如果已经登录，直接跳转
onMounted(() => {
  if (authStore.isAuthenticated) {
    router.push(getDefaultRoute());
  }
});
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
  animation: slideUp 0.6s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-title {
  font-size: 32px;
  font-weight: 700;
  color: #1a202c;
  margin: 0 0 8px 0;
}

.login-subtitle {
  color: #718096;
  margin: 0;
  font-size: 16px;
}

.login-form {
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 8px;
  color: #374151;
  font-weight: 500;
  font-size: 14px;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 16px;
  transition: all 0.2s ease;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-input:disabled {
  background-color: #f7fafc;
  cursor: not-allowed;
}

.error-message {
  background-color: #fed7d7;
  color: #c53030;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 14px;
  text-align: center;
}

.login-button {
  width: 100%;
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.login-footer {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #e2e8f0;
}

.default-hint {
  color: #718096;
  font-size: 14px;
  margin: 0;
  line-height: 1.5;
}

.default-hint strong {
  color: #4a5568;
  font-family: monospace;
  background: #f7fafc;
  padding: 2px 6px;
  border-radius: 4px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .login-container {
    padding: 16px;
  }

  .login-card {
    padding: 32px 24px;
  }

  .login-title {
    font-size: 28px;
  }
}

/* 暗黑模式适配 */
@media (prefers-color-scheme: dark) {
  .login-card {
    background: #2d3748;
    color: #e2e8f0;
  }

  .login-title {
    color: #e2e8f0;
  }

  .form-label {
    color: #cbd5e0;
  }

  .form-input {
    background: #4a5568;
    border-color: #4a5568;
    color: #e2e8f0;
  }

  .form-input:focus {
    border-color: #667eea;
    background: #4a5568;
  }

  .default-hint {
    color: #a0aec0;
  }

  .default-hint strong {
    color: #e2e8f0;
    background: #4a5568;
  }
}
</style>
