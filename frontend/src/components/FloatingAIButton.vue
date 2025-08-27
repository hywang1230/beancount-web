<template>
  <div class="floating-ai-button" v-if="shouldShowButton">
    <van-button
      type="primary"
      size="large"
      round
      @click="goToAIChat"
      class="ai-button"
      :style="{ background: '#1890ff', border: 'none' }"
    >
      <van-icon name="chat-o" size="20" />
      <span class="button-text">AI助手</span>
    </van-button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// 不显示悬浮按钮的页面
const excludePages = [
  'H5AIChat',      // AI聊天页面
  'Login',         // 登录页面
  'H5AddTransaction', // 添加交易页面
  'H5EditRecurring'   // 编辑周期记账页面
]

// 判断是否应该显示按钮
const shouldShowButton = computed(() => {
  return !excludePages.includes(route.name as string)
})

// 跳转到AI聊天页面
const goToAIChat = () => {
  router.push('/h5/ai-chat')
}
</script>

<style scoped>
.floating-ai-button {
  position: fixed;
  bottom: 80px; /* 避开底部导航栏 */
  right: 20px;
  z-index: 9999;
  filter: drop-shadow(0 4px 12px rgba(24, 144, 255, 0.3));
}

.ai-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 20px;
  min-width: 100px;
  height: 48px;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.4);
  transition: all 0.3s ease;
}

.ai-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.5);
}

.ai-button:active {
  transform: translateY(0);
}

.button-text {
  font-size: 14px;
  font-weight: 500;
  color: white;
}

/* 动画效果 */
.floating-ai-button {
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}

/* 小屏幕适配 */
@media (max-width: 360px) {
  .floating-ai-button {
    right: 15px;
    bottom: 75px;
  }
  
  .ai-button {
    padding: 10px 16px;
    min-width: 90px;
    height: 44px;
  }
  
  .button-text {
    font-size: 13px;
  }
}
</style>
