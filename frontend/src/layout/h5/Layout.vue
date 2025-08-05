<template>
  <div class="h5-layout">
    <!-- 头部导航 -->
    <van-nav-bar 
      :title="currentPageTitle"
      left-arrow
      @click-left="onBack"
      class="top-nav"
    >
      <template #right v-if="showMenu">
        <van-icon name="wap-nav" @click="showMenuPopup = true" />
      </template>
    </van-nav-bar>

    <!-- 主内容 -->
    <div class="main-content">
      <router-view />
    </div>

    <!-- 底部导航 -->
    <van-tabbar v-model="activeTab" @change="onTabChange">
      <van-tabbar-item 
        v-for="item in tabbarItems" 
        :key="item.name"
        :name="item.name"
        :icon="item.icon"
        :to="item.path"
      >
        {{ item.title }}
      </van-tabbar-item>
    </van-tabbar>

    <!-- 菜单弹窗 -->
    <van-popup 
      v-model:show="showMenuPopup" 
      position="right" 
      :style="{ width: '80%', height: '100%' }"
    >
      <div class="menu-popup">
        <div class="menu-header">
          <h3>Beancount Web</h3>
          <van-icon name="cross" @click="showMenuPopup = false" />
        </div>
        <van-cell-group>
          <van-cell 
            v-for="item in allMenuItems"
            :key="item.path"
            :title="item.title"
            :icon="item.icon"
            is-link
            @click="navigateTo(item.path)"
          />
        </van-cell-group>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const showMenuPopup = ref(false)
const activeTab = ref('dashboard')

const tabbarItems = [
  { name: 'dashboard', title: '首页', icon: 'home-o', path: '/h5/dashboard' },
  { name: 'transactions', title: '流水', icon: 'bill-o', path: '/h5/transactions' },
  { name: 'add', title: '记账', icon: 'plus', path: '/h5/add-transaction' },
  { name: 'reports', title: '报表', icon: 'bar-chart-o', path: '/h5/reports' },
  { name: 'accounts', title: '账户', icon: 'manager-o', path: '/h5/accounts' }
]

const allMenuItems = [
  { path: '/h5/dashboard', title: '仪表盘', icon: 'home-o' },
  { path: '/h5/transactions', title: '交易流水', icon: 'bill-o' },
  { path: '/h5/add-transaction', title: '新增交易', icon: 'plus' },
  { path: '/h5/recurring', title: '周期记账', icon: 'replay' },
  { path: '/h5/reports', title: '报表分析', icon: 'bar-chart-o' },
  { path: '/h5/accounts', title: '账户管理', icon: 'manager-o' },
  { path: '/h5/files', title: '文件管理', icon: 'folder-o' }
]

// 监听路由变化，更新当前激活的标签
watch(() => route.path, (newPath) => {
  const currentItem = tabbarItems.find(item => item.path === newPath)
  if (currentItem) {
    activeTab.value = currentItem.name
  }
}, { immediate: true })

const currentPageTitle = computed(() => {
  const currentItem = allMenuItems.find(item => item.path === route.path)
  return currentItem?.title || '首页'
})

const showMenu = computed(() => {
  // 在非主要标签页面显示菜单按钮
  return !tabbarItems.some(item => item.path === route.path)
})

const onBack = () => {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/h5/dashboard')
  }
}

const onTabChange = (name: string) => {
  const item = tabbarItems.find(tab => tab.name === name)
  if (item) {
    router.push(item.path)
  }
}

const navigateTo = (path: string) => {
  showMenuPopup.value = false
  router.push(path)
}
</script>

<style scoped>
.h5-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f7f8fa;
}

.top-nav {
  flex-shrink: 0;
  z-index: 1000;
}

.main-content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 50px; /* 为底部导航留出空间 */
}

.menu-popup {
  height: 100%;
  background-color: #fff;
  display: flex;
  flex-direction: column;
}

.menu-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #ebedf0;
}

.menu-header h3 {
  margin: 0;
  color: #323233;
  font-size: 18px;
  font-weight: 500;
}
</style>