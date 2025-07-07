<template>
  <el-container class="layout-container">
    <!-- 移动端遮罩层 -->
    <div 
      v-if="isMobile && !isCollapse"
      class="mobile-overlay"
      @click="toggleCollapse"
    ></div>
    
    <!-- 侧边栏 -->
    <el-aside 
      :width="isMobile ? '250px' : (isCollapse ? '64px' : '200px')"
      :class="{ 'mobile-aside': isMobile, 'mobile-aside-hidden': isMobile && isCollapse }"
    >
      <div class="logo">
        <el-icon v-if="isCollapse && !isMobile" size="24"><Wallet /></el-icon>
        <span v-else>Beancount Web</span>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse && !isMobile"
        :unique-opened="true"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409eff"
        router
        @select="onMenuSelect"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <!-- 主内容区 -->
    <el-container>
      <!-- 顶栏 -->
      <el-header class="header" :class="{ 'mobile-header': isMobile }">
        <div class="header-left">
          <el-button 
            link
            @click="toggleCollapse"
            class="collapse-btn"
          >
            <el-icon size="20">
              <Menu />
            </el-icon>
          </el-button>
          
          <el-breadcrumb separator="/" v-if="!isMobile">
            <el-breadcrumb-item>首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
          
          <span v-else class="mobile-title">{{ currentPageTitle }}</span>
        </div>
      </el-header>
      
      <!-- 主内容 -->
      <el-main class="main-content" :class="{ 'mobile-main': isMobile }">
        <router-view />
      </el-main>
      
      <!-- 移动端底部导航栏 -->
      <div v-if="isMobile" class="mobile-bottom-nav">
        <div 
          v-for="item in mainMenuItems" 
          :key="item.path"
          class="nav-item"
          :class="{ active: activeMenu === item.path }"
          @click="navigateTo(item.path)"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span class="nav-label">{{ item.title }}</span>
        </div>
      </div>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Wallet,
  Menu,
  DataAnalysis,
  Money,
  Plus,
  User,
  Folder,
  Odometer,
  Refresh
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const isCollapse = ref(false)
const isMobile = ref(false)

const menuItems = [
  { path: '/dashboard', title: '仪表盘', icon: Odometer },
  { path: '/transactions', title: '交易流水', icon: Money },
  { path: '/add-transaction', title: '新增交易', icon: Plus },
  { path: '/recurring', title: '周期记账', icon: Refresh },
  { path: '/reports', title: '报表分析', icon: DataAnalysis },
  { path: '/accounts', title: '账户管理', icon: User },
  { path: '/files', title: '文件管理', icon: Folder }
]

// 移动端底部导航主要菜单项（最多5个）
const mainMenuItems = [
  { path: '/dashboard', title: '首页', icon: Odometer },
  { path: '/transactions', title: '流水', icon: Money },
  { path: '/add-transaction', title: '记账', icon: Plus },
  { path: '/reports', title: '报表', icon: DataAnalysis },
  { path: '/accounts', title: '账户', icon: User }
]

const activeMenu = computed(() => route.path)

const currentPageTitle = computed(() => {
  const currentItem = menuItems.find(item => item.path === route.path)
  return currentItem?.title || '首页'
})

// 检测屏幕尺寸
const checkScreenSize = () => {
  const wasMobile = isMobile.value
  isMobile.value = window.innerWidth < 768
  
  // 如果刚切换到移动端，收起侧边栏
  if (isMobile.value && !wasMobile) {
    isCollapse.value = true
  }
  // 如果从移动端切换到桌面端，展开侧边栏
  else if (!isMobile.value && wasMobile) {
    isCollapse.value = false
  }
}

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const onMenuSelect = () => {
  // 移动端选择菜单后自动收起侧边栏
  if (isMobile.value) {
    isCollapse.value = true
  }
}

const navigateTo = (path: string) => {
  router.push(path)
}

onMounted(() => {
  // 初始化时检查屏幕尺寸并设置正确的状态
  isMobile.value = window.innerWidth < 768
  isCollapse.value = isMobile.value // 移动端默认收起，桌面端默认展开
  
  window.addEventListener('resize', checkScreenSize)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkScreenSize)
})
</script>

<style scoped>
.layout-container {
  height: 100vh;
  position: relative;
}

.el-aside {
  background-color: #304156;
  transition: width 0.3s;
  position: relative;
  z-index: 1000;
}

.mobile-aside {
  position: fixed !important;
  height: 100vh;
  top: 0;
  left: 0;
  z-index: 1001;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.15);
  transform: translateX(0);
  transition: transform 0.3s ease;
}

.mobile-aside-hidden {
  transform: translateX(-100%);
}

.mobile-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 1000;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  border-bottom: 1px solid #3d4f5f;
}

.el-menu {
  border-right: none;
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  position: relative;
  z-index: 999;
}

.mobile-header {
  padding: 0 16px;
  height: 50px !important;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.mobile-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.collapse-btn {
  color: #606266;
}

.main-content {
  background-color: #f5f7fa;
  padding: 0;
  position: relative;
}

.mobile-main {
  padding-bottom: 60px; /* 为底部导航留出空间 */
}

.mobile-bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 60px;
  background-color: #fff;
  border-top: 1px solid #e6e6e6;
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 999;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 5px;
  color: #909399;
  transition: color 0.3s;
  min-width: 0;
  flex: 1;
}

.nav-item.active {
  color: #409eff;
}

.nav-item:hover {
  color: #409eff;
}

.nav-item .el-icon {
  font-size: 20px;
  margin-bottom: 2px;
}

.nav-label {
  font-size: 11px;
  line-height: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

/* 移动端响应式调整 */
@media (max-width: 768px) {
  .el-container > .el-aside {
    width: 0px !important;
    margin-left: 0 !important;
  }
  
  .mobile-aside {
    width: 250px !important;
  }
  
  .el-container > .el-container {
    margin-left: 0 !important;
  }
  
  .header {
    margin-left: 0 !important;
  }
  
  .main-content {
    margin-left: 0 !important;
  }
}
</style> 