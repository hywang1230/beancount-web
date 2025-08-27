<template>
  <div class="ai-chat-page">

    <!-- 聊天消息列表 -->
    <div class="chat-container" ref="chatContainer">
      <div class="chat-messages">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-message">
          <div class="ai-avatar">🤖</div>
          <div class="welcome-text">
            <h3>你好！我是你的AI记账助手</h3>
            
            <!-- 上下文状态指示 -->
            <div class="context-status" :class="{ 'enabled': contextEnabled }">
              <van-icon :name="contextEnabled ? 'cluster-o' : 'cluster'" />
              <span>上下文记忆：{{ contextEnabled ? '已启用' : '已禁用' }}</span>
              <van-button 
                size="mini" 
                type="primary" 
                plain 
                @click="$router.push('/h5/ai-context')"
              >
                管理
              </van-button>
            </div>
            
            <p>我可以帮助你：</p>
            <ul>
              <li>🔍 自然语言记账：「今天在星巴克花了35元」</li>
              <li>📊 智能查询分析：「这个月餐饮花了多少钱」</li>
              <li>⚙️ 系统设置管理：「设置餐饮预算1000元」</li>
            </ul>
            <p>试试跟我聊聊吧！</p>
          </div>
        </div>

        <!-- 消息列表 -->
        <div 
          v-for="(message, index) in messages" 
          :key="index" 
          class="message-item"
          :class="{ 'user': message.isUser, 'ai': !message.isUser }"
        >
          <div class="message-avatar">
            <van-icon v-if="message.isUser" name="user-o" />
            <span v-else class="ai-avatar">🤖</span>
          </div>
          <div class="message-content">
            <div class="message-bubble">
              <div v-if="message.status === 'loading'" class="loading-content">
                <van-loading size="16" />
                <span>AI正在思考...</span>
              </div>
              <div v-else-if="message.status === 'streaming'" class="streaming-content">
                <div class="message-text">
                  {{ message.content }}
                  <span class="cursor-blink">|</span>
                </div>
              </div>
              <div v-else class="message-text">
                {{ message.content }}
              </div>
              <div v-if="message.intent || (!message.isUser && message.contextUsed)" class="message-meta">
                <span v-if="message.intent">意图：{{ getIntentText(message.intent) }}</span>
                <span v-if="!message.isUser && message.contextUsed" class="context-indicator" title="使用了上下文记忆">🧠</span>
              </div>
            </div>
            <div class="message-time">
              {{ formatTime(message.timestamp) }}
              <span v-if="!message.isUser && message.conversationId" class="conversation-id" :title="`对话ID: ${message.conversationId}`">💬</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <div class="input-container">
        <van-field
          v-model="inputMessage"
          placeholder="请输入消息..."
          type="textarea"
          rows="1"
          autosize
          @keyup.enter="sendMessage"
          :disabled="sending"
        />
        <van-button
          type="primary"
          size="small"
          @click="sendMessage"
          :loading="sending"
          :disabled="!inputMessage.trim()"
          class="send-button"
        >
          发送
        </van-button>
      </div>
    </div>


  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { showToast, showDialog } from 'vant'
import { aiChatApi, aiContextApi, type AIChatRequest } from '@/api/ai'

interface ChatMessage {
  content: string
  isUser: boolean
  timestamp: Date
  status?: 'loading' | 'completed' | 'failed' | 'streaming'
  intent?: string
  chainId?: string
  isStreaming?: boolean
  conversationId?: string
  contextUsed?: boolean
}

// 响应式数据
const messages = ref<ChatMessage[]>([])
const inputMessage = ref('')
const sending = ref(false)
const chatContainer = ref<HTMLElement>()
const conversationId = ref<string>('')
const contextEnabled = ref(true)
const contextStats = ref({
  context_enabled: false
})

// 意图文本映射
const intentMap: Record<string, string> = {
  transaction: '记账',
  query: '查询',
  management: '管理',
  general: '对话'
}

// 获取意图文本
const getIntentText = (intent: string): string => {
  return intentMap[intent] || intent
}

// 格式化时间
const formatTime = (timestamp: Date): string => {
  return timestamp.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

// 生成新的对话ID
const generateConversationId = (): string => {
  const newId = 'conv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  // 保存到localStorage
  localStorage.setItem('ai-conversation-id', newId)
  return newId
}

// 构建聊天历史
const buildChatHistory = () => {
  return messages.value
    .filter(msg => msg.status === 'completed')
    .map(msg => ({
      role: msg.isUser ? 'user' : 'assistant',
      content: msg.content
    }))
}

// 获取上下文统计信息
const fetchContextStats = async () => {
  try {
    const result = await aiContextApi.getStats()
    contextStats.value = result.stats
    contextEnabled.value = result.stats.context_enabled
  } catch (error) {
    console.error('获取上下文统计失败:', error)
  }
}

// 清除当前对话上下文
const clearCurrentConversation = async () => {
  if (!conversationId.value) return
  
  try {
    await aiContextApi.clearConversation(conversationId.value)
    showToast('对话上下文已清除')
    // 重新开始新对话
    conversationId.value = ''
    messages.value = []
    // 清除localStorage中的对话ID
    localStorage.removeItem('ai-conversation-id')
    await fetchContextStats()
  } catch (error) {
    console.error('清除对话失败:', error)
    showToast('清除对话失败')
  }
}

// 显示上下文信息
const showContextInfo = async () => {
  await fetchContextStats()
  const stats = contextStats.value
  
  showDialog({
    title: '上下文信息',
    message: `
      <div style="text-align: left;">
        <p><strong>上下文状态:</strong> ${stats.context_enabled ? '已启用' : '已禁用'}</p>
        <p><strong>记忆类型:</strong> 缓冲记忆</p>
        <p><strong>当前对话ID:</strong> ${conversationId.value || '未创建'}</p>
        <p><strong>消息数量:</strong> ${messages.value.filter(m => m.status === 'completed').length}</p>
      </div>
    `,
    allowHtml: true,
    showCancelButton: conversationId.value ? true : false,
    cancelButtonText: '清除对话',
    confirmButtonText: '关闭'
  }).then(() => {
    // 确认按钮 - 关闭
  }).catch(() => {
    // 取消按钮 - 清除对话
    clearCurrentConversation()
  })
}

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || sending.value) return

  // 如果还没有对话ID，创建一个新的
  if (!conversationId.value) {
    conversationId.value = generateConversationId()
  }

  const userMessage: ChatMessage = {
    content: inputMessage.value.trim(),
    isUser: true,
    timestamp: new Date(),
    conversationId: conversationId.value
  }

  // 添加用户消息
  messages.value.push(userMessage)
  
  // 添加AI流式消息
  const aiMessage: ChatMessage = {
    content: '',
    isUser: false,
    timestamp: new Date(),
    status: 'loading',
    isStreaming: true,
    conversationId: conversationId.value
  }
  messages.value.push(aiMessage)

  // 清空输入框并滚动到底部
  const messageContent = inputMessage.value.trim()
  inputMessage.value = ''
  sending.value = true
  await scrollToBottom()

  try {
    // 构建请求，包含对话ID和历史记录
    const request: AIChatRequest = {
      message: messageContent,
      context: {},
      conversation_id: conversationId.value,
      chat_history: contextEnabled.value ? buildChatHistory() : undefined
    }

    // 使用流式API
    aiChatApi.chatStream(
      request,
      // onMessage: 处理流式数据
      (chunk) => {
        const lastMessage = messages.value[messages.value.length - 1]
        
        switch (chunk.type) {
          case 'start':
            lastMessage.status = 'loading'
            lastMessage.chainId = chunk.chain_id
            lastMessage.conversationId = chunk.conversation_id
            lastMessage.contextUsed = chunk.context_enabled
            break
            
          case 'intent':
            lastMessage.intent = chunk.intent
            break
            
          case 'context_loaded':
            lastMessage.content = chunk.message || 'AI正在思考...'
            break
            
          case 'thinking':
            lastMessage.status = 'loading'
            lastMessage.content = chunk.message
            lastMessage.contextUsed = chunk.context_used
            break
            
          case 'message_chunk':
            lastMessage.status = 'streaming'
            lastMessage.content = chunk.full_content || chunk.content
            lastMessage.contextUsed = chunk.context_used
            scrollToBottom()
            break
            
          case 'message':
            lastMessage.status = 'completed'
            lastMessage.content = chunk.message
            lastMessage.intent = chunk.intent
            lastMessage.conversationId = chunk.conversation_id
            lastMessage.contextUsed = chunk.context_used
            break
            
          case 'message_complete':
            lastMessage.status = 'completed'
            lastMessage.isStreaming = false
            lastMessage.conversationId = chunk.conversation_id
            lastMessage.contextUsed = chunk.context_used
            // 更新对话ID（如果后端返回了新的）
            if (chunk.conversation_id && chunk.conversation_id !== conversationId.value) {
              conversationId.value = chunk.conversation_id
            }
            break
            
          case 'error':
            lastMessage.status = 'failed'
            lastMessage.content = chunk.message || '处理失败，请重试'
            showToast(chunk.message || '发送失败，请重试')
            break
        }
        
        scrollToBottom()
      },
      // onError: 处理错误
      (error) => {
        console.error('流式聊天失败:', error)
        const lastMessage = messages.value[messages.value.length - 1]
        lastMessage.content = '抱歉，我暂时无法回复。请检查网络连接或AI配置。'
        lastMessage.status = 'failed'
        showToast('发送失败，请重试')
      },
      // onComplete: 完成回调
      () => {
        sending.value = false
        const lastMessage = messages.value[messages.value.length - 1]
        if (lastMessage.status === 'streaming') {
          lastMessage.status = 'completed'
        }
        lastMessage.isStreaming = false
      }
    )

  } catch (error: any) {
    console.error('发送消息失败:', error)
    
    // 更新AI消息为错误状态
    const lastMessage = messages.value[messages.value.length - 1]
    lastMessage.content = '抱歉，我暂时无法回复。请检查网络连接或AI配置。'
    lastMessage.status = 'failed'

    showToast('发送失败，请重试')
    sending.value = false
  }
}

// 监听来自Layout的事件
const handleContextInfoEvent = () => {
  showContextInfo()
}

const handleClearConversationEvent = () => {
  clearCurrentConversation()
}

// 初始化
onMounted(async () => {
  await fetchContextStats()
  
  // 尝试恢复之前的对话ID
  const savedConversationId = localStorage.getItem('ai-conversation-id')
  if (savedConversationId) {
    conversationId.value = savedConversationId
  }
  
  // 监听Layout传来的事件
  window.addEventListener('ai-chat-show-context-info', handleContextInfoEvent)
  window.addEventListener('ai-chat-clear-conversation', handleClearConversationEvent)
})

// 组件卸载时清理事件监听器
onUnmounted(() => {
  window.removeEventListener('ai-chat-show-context-info', handleContextInfoEvent)
  window.removeEventListener('ai-chat-clear-conversation', handleClearConversationEvent)
})

</script>

<style scoped>
.ai-chat-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--van-background);
  transition: background-color 0.3s ease;
  position: relative;
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  padding-bottom: 100px; /* 为输入框留出空间 */
}

.chat-messages {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.welcome-message {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: var(--van-background-2);
  border-radius: 12px;
  box-shadow: var(--shadow-light);
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
}

.ai-avatar {
  font-size: 24px;
  flex-shrink: 0;
}

.welcome-text h3 {
  margin: 0 0 8px 0;
  color: var(--van-text-color);
  font-size: 16px;
  transition: color 0.3s ease;
}

.welcome-text p {
  margin: 8px 0;
  color: var(--van-text-color-2);
  font-size: 14px;
  transition: color 0.3s ease;
}

.welcome-text ul {
  margin: 8px 0;
  padding-left: 16px;
  color: var(--van-text-color-2);
  font-size: 14px;
  transition: color 0.3s ease;
}

.welcome-text li {
  margin: 4px 0;
}

.context-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin: 12px 0;
  background: var(--van-background);
  border-radius: 8px;
  border-left: 4px solid var(--van-border-color);
  font-size: 14px;
  color: var(--van-text-color-2);
  transition: all 0.3s ease;
}

.context-status.enabled {
  background: rgba(24, 144, 255, 0.1);
  border-left-color: #1890ff;
  color: #1890ff;
}

.van-theme-dark .context-status.enabled {
  background: rgba(24, 144, 255, 0.2);
}

.context-status .van-icon {
  font-size: 16px;
}

.context-status span {
  flex: 1;
}

.context-status .van-button {
  font-size: 12px;
}

.message-item {
  display: flex;
  gap: 8px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(24, 144, 255, 0.1);
  flex-shrink: 0;
  transition: background-color 0.3s ease;
}

.van-theme-dark .message-avatar {
  background-color: rgba(24, 144, 255, 0.2);
}

.message-item.user .message-avatar {
  background-color: #07c160;
  color: white;
}

.message-content {
  flex: 1;
  max-width: calc(100% - 48px);
}

.message-item.user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-bubble {
  background: var(--van-background-2);
  color: var(--van-text-color);
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: var(--shadow-base);
  word-wrap: break-word;
  transition: all 0.3s ease;
}

.message-item:not(.user) .message-bubble {
  position: relative;
}

.streaming-content .message-bubble::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 12px;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.3);
  animation: streaming-pulse 2s infinite;
  pointer-events: none;
}

@keyframes streaming-pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(24, 144, 255, 0.4);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(24, 144, 255, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(24, 144, 255, 0);
  }
}

.message-item.user .message-bubble {
  background: #07c160;
  color: white;
}

.loading-content {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--van-text-color-3);
  transition: color 0.3s ease;
}

.streaming-content {
  position: relative;
}

.cursor-blink {
  display: inline-block;
  animation: blink 1s infinite;
  color: #1890ff;
  font-weight: bold;
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}

.message-text {
  line-height: 1.5;
  white-space: pre-wrap;
}

.message-meta {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--van-border-color);
  font-size: 12px;
  color: var(--van-text-color-3);
  transition: all 0.3s ease;
}

.message-item.user .message-meta {
  border-top-color: rgba(255, 255, 255, 0.3);
  color: rgba(255, 255, 255, 0.8);
}

.message-time {
  margin-top: 4px;
  font-size: 12px;
  color: var(--van-text-color-3);
  display: flex;
  align-items: center;
  gap: 4px;
  transition: color 0.3s ease;
}

.context-indicator {
  font-size: 14px;
  margin-left: 8px;
  opacity: 0.7;
  cursor: help;
}

.conversation-id {
  font-size: 12px;
  opacity: 0.6;
  cursor: help;
}

.input-area {
  position: fixed;
  bottom: 0; /* 贴底显示 */
  left: 0;
  right: 0;
  background: var(--van-background-2);
  border-top: 1px solid var(--van-border-color);
  padding: 12px 16px;
  z-index: 999;
  /* 适配安全区域 */
  padding-bottom: max(12px, env(safe-area-inset-bottom));
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.input-container {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.input-container :deep(.van-field) {
  flex: 1;
  background: var(--van-background);
  border-radius: 20px;
  transition: background-color 0.3s ease;
}

.input-container :deep(.van-field__control) {
  padding: 8px 16px;
  border: none;
  max-height: 80px;
  color: var(--van-text-color);
  transition: color 0.3s ease;
}

.send-button {
  height: 36px;
  min-width: 60px;
  border-radius: 18px;
  flex-shrink: 0; /* 防止按钮被压缩 */
}

/* PWA模式和移动端特殊优化 */
@media screen and (max-width: 768px) {
  .input-area {
    /* 使用env()来适配不同的移动设备 */
    padding-bottom: max(12px, env(safe-area-inset-bottom));
    /* 确保在虚拟键盘环境下的最小高度 */
    min-height: 60px;
  }
  
  .input-container {
    /* 移动端对齐优化 */
    align-items: center;
    min-height: 36px;
  }
  
  .input-container :deep(.van-field) {
    /* 移动端输入框优化 */
    border: 1px solid var(--van-border-color);
  }
  
  .input-container :deep(.van-field__control) {
    /* 移动端文本输入优化 */
    font-size: 16px; /* 防止iOS缩放 */
    line-height: 1.4;
    /* 优化触摸目标大小 */
    min-height: 20px;
    padding: 10px 16px;
  }
  
  /* 聚焦状态优化 */
  .input-container :deep(.van-field--focused) {
    border-color: var(--van-primary-color);
    box-shadow: 0 0 0 1px var(--van-primary-color);
  }
}

/* PWA模式特殊适配 */
:global(.pwa-mode) .input-area {
  /* PWA模式下的额外安全区域适配 */
  padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px));
}

:global(.pwa-ios) .input-area {
  /* iOS PWA模式的特殊处理 */
  padding-bottom: calc(16px + env(safe-area-inset-bottom, 0px));
}

/* 修复iOS Safari中的输入框问题 */
@supports (-webkit-touch-callout: none) {
  .message-input :deep(.van-field__control) {
    /* iOS Safari特定修复 */
    -webkit-user-select: text;
    user-select: text;
    -webkit-touch-callout: default;
    /* 确保光标正确显示 */
    caret-color: var(--van-primary-color);
  }
}
</style>
