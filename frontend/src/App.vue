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

// 路由重定向逻辑
const redirectBasedOnDevice = () => {
  const currentPath = route.path
  const mobile = detectDevice()
  isMobile.value = mobile
  
  if (mobile) {
    // 移动端逻辑
    if (!currentPath.startsWith('/h5')) {
      // 将PC端路径转换为移动端路径
      const h5Path = currentPath === '/' ? '/h5/dashboard' : `/h5${currentPath}`
      router.replace(h5Path)
    }
  } else {
    // PC端逻辑
    if (currentPath.startsWith('/h5')) {
      // 将移动端路径转换为PC端路径
      const pcPath = currentPath.replace('/h5', '') || '/dashboard'
      router.replace(pcPath)
    } else if (currentPath === '/') {
      // 根路径重定向到仪表盘
      router.replace('/dashboard')
    }
  }
}

onMounted(() => {
  redirectBasedOnDevice()
  
  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    const newIsMobile = detectDevice()
    if (newIsMobile !== isMobile.value) {
      isMobile.value = newIsMobile
      redirectBasedOnDevice()
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