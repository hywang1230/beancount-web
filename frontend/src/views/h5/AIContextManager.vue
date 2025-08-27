<template>
  <div class="context-manager-page">
    <!-- 头部 -->
    <van-nav-bar 
      title="上下文管理" 
      left-arrow 
      @click-left="$router.back()"
      fixed
      placeholder
    >
      <template #right>
        <van-icon 
          name="refresh" 
          @click="refreshData"
          style="font-size: 18px;"
        />
      </template>
    </van-nav-bar>

    <!-- 内容区域 -->
    <div class="page-content">
      <!-- 统计信息卡片 -->
      <van-card class="stats-card">
        <template #title>
          <div class="stats-title">
            <van-icon name="chart-trending-o" />
            上下文统计
          </div>
        </template>
        <template #desc>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-value">{{ contextStats.context_enabled ? '启用' : '禁用' }}</div>
              <div class="stat-label">上下文状态</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">缓冲记忆</div>
              <div class="stat-label">记忆类型</div>
            </div>
          </div>
        </template>
      </van-card>

      <!-- 配置管理 -->
      <van-cell-group inset title="上下文配置">
        <van-cell 
          title="启用上下文记忆"
          :value="contextEnabled ? '已启用' : '已禁用'"
          is-link
          @click="showContextSettings"
        />

        <van-cell 
          title="缓冲窗口大小"
          :value="`${memorySettings.bufferWindow} 条消息`"
          is-link
          @click="showMemoryLengthSettings"
        />
      </van-cell-group>

      <!-- 对话管理 -->
      <van-cell-group inset title="对话管理">
        <van-cell 
          title="清理过期对话"
          value="释放内存空间"
          is-link
          @click="cleanupExpiredConversations"
        />
        <van-cell 
          title="重置所有对话"
          value="清除所有缓存"
          is-link
          @click="resetAllConversations"
        />
      </van-cell-group>

      <!-- 高级设置 -->
      <van-cell-group inset title="高级设置">
        <van-cell 
          title="初始化上下文配置"
          value="恢复默认设置"
          is-link
          @click="initializeContextConfigs"
        />
        <van-cell 
          title="导出配置"
          value="备份当前设置"
          is-link
          @click="exportConfigs"
        />
      </van-cell-group>

      <!-- 帮助信息 -->
      <van-cell-group inset title="帮助信息">
        <van-collapse v-model="activeHelp">
          <van-collapse-item title="什么是上下文记忆？" name="1">
            <div class="help-content">
              上下文记忆允许AI助手记住之前的对话内容，使对话更加连贯和智能。系统采用缓冲记忆策略：
              <ul>
                <li><strong>缓冲记忆</strong>：保持最近的N条消息，简单可靠</li>
                <li><strong>窗口设置</strong>：可调整保存的消息数量（建议5-20条）</li>
                <li><strong>自动清理</strong>：过期对话会自动清理以释放内存</li>
              </ul>
            </div>
          </van-collapse-item>
          <van-collapse-item title="如何优化记忆性能？" name="2">
            <div class="help-content">
              <ul>
                <li>定期清理过期对话可以释放内存</li>
                <li>合理设置缓冲窗口大小（5-20条为宜）</li>
                <li>窗口太小会影响上下文连贯性</li>
                <li>窗口太大会消耗更多内存和处理时间</li>
                <li>禁用上下文可以提高响应速度</li>
              </ul>
            </div>
          </van-collapse-item>
        </van-collapse>
      </van-cell-group>
    </div>

    <!-- 上下文设置弹窗 -->
    <van-popup 
      v-model:show="showContextSettingsPopup" 
      position="bottom" 
      round
      style="height: 40%"
    >
      <div class="popup-content">
        <div class="popup-header">
          <h3>上下文设置</h3>
        </div>
        <div class="settings-content">
          <van-cell-group>
            <van-cell title="启用上下文记忆">
              <template #right-icon>
                <van-switch v-model="contextEnabled" @change="updateContextEnabled" />
              </template>
            </van-cell>
          </van-cell-group>
        </div>
      </div>
    </van-popup>



    <!-- 记忆长度设置弹窗 -->
    <van-popup 
      v-model:show="showMemoryLengthPopup" 
      position="bottom" 
      round
      style="height: 50%"
    >
      <div class="popup-content">
        <div class="popup-header">
          <h3>记忆长度设置</h3>
        </div>
        <div class="settings-content">
          <van-cell-group>
            <van-field
              v-model="memorySettings.bufferWindow"
              label="缓冲窗口大小"
              placeholder="消息条数"
              type="number"
            />
          </van-cell-group>
          <div class="popup-actions">
            <van-button type="primary" block @click="saveMemorySettings">
              保存设置
            </van-button>
          </div>
        </div>
      </div>
    </van-popup>


  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { showToast, showConfirmDialog } from 'vant'
import { aiConfigApi, aiContextApi } from '@/api/ai'

// 响应式数据
const contextStats = ref({
  context_enabled: false
})

const contextEnabled = ref(true)
const activeHelp = ref([])

// 弹窗控制
const showContextSettingsPopup = ref(false)
const showMemoryLengthPopup = ref(false)

// 记忆设置
const memorySettings = ref({
  bufferWindow: '10'
})



// 刷新数据
const refreshData = async () => {
  await Promise.all([
    fetchContextStats(),
    loadCurrentConfigs()
  ])
  showToast('数据已刷新')
}

// 获取上下文统计
const fetchContextStats = async () => {
  try {
    const result = await aiContextApi.getStats()
    contextStats.value = result.stats
    contextEnabled.value = result.stats.context_enabled
  } catch (error) {
    console.error('获取统计信息失败:', error)
    showToast('获取统计信息失败')
  }
}

// 加载当前配置
const loadCurrentConfigs = async () => {
  try {
    const configs = await aiConfigApi.getConfigsDict()
    const configData = configs.configs
    
    memorySettings.value = {
      bufferWindow: configData.context_buffer_window || '10'
    }
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

// 显示上下文设置
const showContextSettings = () => {
  showContextSettingsPopup.value = true
}

// 更新上下文启用状态
const updateContextEnabled = async (enabled: boolean) => {
  try {
    await aiConfigApi.updateConfig('context_enabled', {
      value: enabled ? 'true' : 'false'
    })
    showToast(enabled ? '上下文已启用' : '上下文已禁用')
    await fetchContextStats()
  } catch (error) {
    console.error('更新配置失败:', error)
    showToast('更新配置失败')
    // 恢复原状态
    contextEnabled.value = !enabled
  }
}



// 显示记忆长度设置
const showMemoryLengthSettings = () => {
  showMemoryLengthPopup.value = true
}

// 保存记忆设置
const saveMemorySettings = async () => {
  try {
    await aiConfigApi.updateConfig('context_buffer_window', {
      value: memorySettings.value.bufferWindow
    })
    showToast('缓冲窗口设置已保存')
    showMemoryLengthPopup.value = false
  } catch (error) {
    console.error('保存设置失败:', error)
    showToast('保存设置失败')
  }
}



// 清理过期对话
const cleanupExpiredConversations = async () => {
  try {
    const result = await showConfirmDialog({
      title: '清理过期对话',
      message: '确定要清理所有过期的对话缓存吗？这将释放内存空间。'
    })
    
    if (result === 'confirm') {
      const cleanupResult = await aiContextApi.cleanupExpired()
      showToast(`已清理 ${cleanupResult.cleaned_count} 个过期对话`)
      await fetchContextStats()
    }
  } catch (error) {
    console.error('清理过期对话失败:', error)
    showToast('清理失败')
  }
}

// 重置所有对话
const resetAllConversations = async () => {
  try {
    const result = await showConfirmDialog({
      title: '重置所有对话',
      message: '确定要重置所有对话缓存吗？这将清除所有对话历史，无法恢复。'
    })
    
    if (result === 'confirm') {
      // 这里需要实现重置所有对话的API
      showToast('功能开发中，敬请期待')
    }
  } catch (error) {
    console.error('重置对话失败:', error)
    showToast('重置失败')
  }
}

// 初始化上下文配置
const initializeContextConfigs = async () => {
  try {
    const result = await showConfirmDialog({
      title: '初始化配置',
      message: '确定要重置上下文配置为默认值吗？'
    })
    
    if (result === 'confirm') {
      const initResult = await aiContextApi.initConfigs()
      showToast(initResult.message)
      await refreshData()
    }
  } catch (error) {
    console.error('初始化配置失败:', error)
    showToast('初始化失败')
  }
}

// 导出配置
const exportConfigs = async () => {
  try {
    const configs = await aiConfigApi.getConfigsDict()
    const contextConfigs = Object.entries(configs.configs)
      .filter(([key]) => key.startsWith('context_'))
      .reduce((acc, [key, value]) => {
        acc[key] = value
        return acc
      }, {} as Record<string, string>)
    
    const configText = JSON.stringify(contextConfigs, null, 2)
    
    // 创建下载链接
    const blob = new Blob([configText], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `context-config-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    
    showToast('配置已导出')
  } catch (error) {
    console.error('导出配置失败:', error)
    showToast('导出失败')
  }
}

// 初始化
onMounted(async () => {
  await refreshData()
})
</script>

<style scoped>
.context-manager-page {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding-bottom: 60px;
}

.page-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stats-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  margin-bottom: 8px;
}

.stats-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: white;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-top: 16px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: white;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
}

.popup-content {
  padding: 16px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 16px;
  border-bottom: 1px solid #eee;
  margin-bottom: 16px;
}

.popup-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.settings-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.popup-actions {
  margin-top: auto;
  padding-top: 16px;
}



.help-content {
  font-size: 14px;
  line-height: 1.6;
  color: #666;
}

.help-content ul {
  margin: 8px 0;
  padding-left: 20px;
}

.help-content li {
  margin: 4px 0;
}

.help-content strong {
  color: #333;
}

/* 深色主题适配 */
@media (prefers-color-scheme: dark) {
  .context-manager-page {
    background-color: #1a1a1a;
  }
  
  .help-content {
    color: #999;
  }
  
  .help-content strong {
    color: #e6e6e6;
  }
}
</style>
