<template>
  <div id="app">
    <!-- PC端 -->
    <el-config-provider v-if="!isMobile" :locale="zhCn">
      <router-view />
    </el-config-provider>
    
    <!-- 移动端 -->
    <van-config-provider v-else :locale="zhCn">
      <router-view />
    </van-config-provider>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
// VanConfigProvider 通过自动导入配置自动引入

const router = useRouter()
const route = useRoute()
const isMobile = ref(false)

// 检测设备类型
const detectDevice = () => {
  const userAgent = navigator.userAgent.toLowerCase()
  const mobileKeywords = ['mobile', 'android', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone']
  const isMobileDevice = mobileKeywords.some(keyword => userAgent.includes(keyword))
  const isSmallScreen = window.innerWidth <= 768
  
  return isMobileDevice || isSmallScreen
}



onMounted(() => {
  // 暂时禁用自动重定向，只设置设备类型
  isMobile.value = detectDevice()
  
  // 仅处理根路径重定向
  if (route.path === '/') {
    if (isMobile.value) {
      router.replace('/h5/dashboard')
    } else {
      router.replace('/dashboard')
    }
  }
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    const newIsMobile = detectDevice()
    if (newIsMobile !== isMobile.value) {
      isMobile.value = newIsMobile
    }
  })
})
</script>

<style>
#app {
  height: 100vh;
  width: 100vw;
}
</style> 