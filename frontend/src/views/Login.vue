<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">Beancount Web</h1>
        <p class="login-subtitle">请登录您的账户</p>
      </div>

      <form @submit.prevent="handleLogin" class="login-form">
        <van-cell-group inset>
          <van-field
            v-model="loginForm.username"
            label="用户名"
            placeholder="请输入用户名"
            required
            :disabled="authStore.isLoading"
            clearable
          />
          <van-field
            v-model="loginForm.password"
            type="password"
            label="密码"
            placeholder="请输入密码"
            required
            :disabled="authStore.isLoading"
          />
        </van-cell-group>

        <van-notice-bar
          v-if="errorMessage"
          type="danger"
          :text="errorMessage"
          class="error-notice"
        />

        <van-button
          type="primary"
          size="large"
          block
          :loading="authStore.isLoading"
          :disabled="!loginForm.username || !loginForm.password"
          @click="handleLogin"
          class="login-button"
        >
          {{ authStore.isLoading ? "登录中..." : "登录" }}
        </van-button>
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
  background: var(--van-background);
  padding: 20px;
}

.login-card {
  background: var(--van-background-2);
  border-radius: 16px;
  padding: 32px 24px;
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
  font-size: 28px;
  font-weight: 600;
  color: var(--van-text-color);
  margin: 0 0 8px 0;
}

.login-subtitle {
  color: var(--van-text-color-2);
  margin: 0;
  font-size: 16px;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.error-notice {
  margin: 0;
}

.login-button {
  margin-top: 8px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .login-container {
    padding: 16px;
  }

  .login-card {
    padding: 24px 20px;
  }

  .login-title {
    font-size: 24px;
  }

  .login-subtitle {
    font-size: 14px;
  }
}
</style>
