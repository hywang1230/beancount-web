import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import PcLayout from '@/layout/pc/Layout.vue'
import H5Layout from '@/layout/h5/Layout.vue'

const routes: RouteRecordRaw[] = [
  // 根路由重定向逻辑在App.vue中处理
  {
    path: '/',
    redirect: () => {
      // 这里的重定向逻辑将在App.vue中处理
      return '/dashboard'
    }
  },
  // PC端路由
  {
    path: '/pc',
    redirect: '/dashboard'
  },
  {
    path: '/',
    component: PcLayout,
    children: [
      {
        path: 'dashboard',
        name: 'PcDashboard',
        component: () => import('@/views/pc/Dashboard.vue'),
        meta: { title: '仪表盘', platform: 'pc' }
      },
      {
        path: 'transactions',
        name: 'PcTransactions',
        component: () => import('@/views/pc/Transactions.vue'),
        meta: { title: '交易流水', platform: 'pc' }
      },
      {
        path: 'add-transaction',
        name: 'PcAddTransaction',
        component: () => import('@/views/pc/AddTransaction.vue'),
        meta: { title: '新增交易', platform: 'pc' }
      },
      {
        path: 'reports',
        name: 'PcReports',
        component: () => import('@/views/pc/Reports.vue'),
        meta: { title: '报表分析', platform: 'pc' }
      },
      {
        path: 'accounts',
        name: 'PcAccounts',
        component: () => import('@/views/pc/Accounts.vue'),
        meta: { title: '账户管理', platform: 'pc' }
      },
      {
        path: 'files',
        name: 'PcFiles',
        component: () => import('@/views/pc/Files.vue'),
        meta: { title: '文件管理', platform: 'pc' }
      },
      {
        path: 'recurring',
        name: 'PcRecurringTransactions',
        component: () => import('@/views/pc/RecurringTransactions.vue'),
        meta: { title: '周期记账', platform: 'pc' }
      }
    ]
  },
  // 移动端路由
  {
    path: '/h5',
    component: H5Layout,
    redirect: '/h5/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'H5Dashboard',
        component: () => import('@/views/h5/Dashboard.vue'),
        meta: { title: '仪表盘', platform: 'h5' }
      },
      {
        path: 'transactions',
        name: 'H5Transactions',
        component: () => import('@/views/h5/Transactions.vue'),
        meta: { title: '交易流水', platform: 'h5' }
      },
      {
        path: 'add-transaction',
        name: 'H5AddTransaction',
        component: () => import('@/views/h5/AddTransaction.vue'),
        meta: { title: '新增交易', platform: 'h5' }
      },
      {
        path: 'reports',
        name: 'H5Reports',
        component: () => import('@/views/h5/Reports.vue'),
        meta: { title: '报表分析', platform: 'h5' }
      },
      {
        path: 'accounts',
        name: 'H5Accounts',
        component: () => import('@/views/h5/Accounts.vue'),
        meta: { title: '账户管理', platform: 'h5' }
      },
      {
        path: 'files',
        name: 'H5Files',
        component: () => import('@/views/h5/Files.vue'),
        meta: { title: '文件管理', platform: 'h5' }
      },
      {
        path: 'recurring',
        name: 'H5RecurringTransactions',
        component: () => import('@/views/h5/RecurringTransactions.vue'),
        meta: { title: '周期记账', platform: 'h5' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router 