<template>
  <div class="ai-chat-page">
    <!-- 头部 -->
    <van-nav-bar 
      title="AI智能助手" 
      left-arrow 
      @click-left="$router.back()"
      fixed
      placeholder
    >

    </van-nav-bar>

    <!-- 聊天消息列表 -->
    <div class="chat-container" ref="chatContainer">
      <div class="chat-messages">
        <!-- 欢迎消息 -->
        <div v-if="messages.length === 0" class="welcome-message">
          <div class="ai-avatar">🤖</div>
          <div class="welcome-text">
            <h3>你好！我是你的AI记账助手</h3>
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
              <div v-if="message.intent" class="message-meta">
                意图：{{ getIntentText(message.intent) }}
              </div>
            </div>
            <div class="message-time">
              {{ formatTime(message.timestamp) }}
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
import { ref, reactive, onMounted, nextTick } from 'vue'
import { showToast, showDialog } from 'vant'
import { aiChatApi, aiConfigApi, type AIChatRequest, type AIConfig } from '@/api/ai'

interface ChatMessage {
  content: string
  isUser: boolean
  timestamp: Date
  status?: 'loading' | 'completed' | 'failed' | 'streaming'
  intent?: string
  chainId?: string
  isStreaming?: boolean
}

// 响应式数据
const messages = ref<ChatMessage[]>([])
const inputMessage = ref('')
const sending = ref(false)
const chatContainer = ref<HTMLElement>()

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

// 发送消息
const sendMessage = async () => {
  if (!inputMessage.value.trim() || sending.value) return

  const userMessage: ChatMessage = {
    content: inputMessage.value.trim(),
    isUser: true,
    timestamp: new Date()
  }

  // 添加用户消息
  messages.value.push(userMessage)
  
  // 添加AI流式消息
  const aiMessage: ChatMessage = {
    content: '',
    isUser: false,
    timestamp: new Date(),
    status: 'loading',
    isStreaming: true
  }
  messages.value.push(aiMessage)

  // 清空输入框并滚动到底部
  const messageContent = inputMessage.value.trim()
  inputMessage.value = ''
  sending.value = true
  await scrollToBottom()

  try {
    const request: AIChatRequest = {
      message: messageContent,
      context: {}
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
            break
            
          case 'intent':
            lastMessage.intent = chunk.intent
            break
            
          case 'thinking':
            lastMessage.status = 'loading'
            lastMessage.content = chunk.message
            break
            
          case 'message_chunk':
            lastMessage.status = 'streaming'
            lastMessage.content = chunk.full_content || chunk.content
            scrollToBottom()
            break
            
          case 'message':
            lastMessage.status = 'completed'
            lastMessage.content = chunk.message
            lastMessage.intent = chunk.intent
            break
            
          case 'message_complete':
            lastMessage.status = 'completed'
            lastMessage.isStreaming = false
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


</script>

<style scoped>
.ai-chat-page {
  height: 100vh;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
  padding-bottom: 60px; /* 为底部导航栏留出空间 */
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  margin-bottom: 100px; /* 增加底部边距以避开输入框 */
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
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.ai-avatar {
  font-size: 24px;
  flex-shrink: 0;
}

.welcome-text h3 {
  margin: 0 0 8px 0;
  color: #333;
  font-size: 16px;
}

.welcome-text p {
  margin: 8px 0;
  color: #666;
  font-size: 14px;
}

.welcome-text ul {
  margin: 8px 0;
  padding-left: 16px;
  color: #666;
  font-size: 14px;
}

.welcome-text li {
  margin: 4px 0;
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
  background-color: #e8f4fd;
  flex-shrink: 0;
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
  background: white;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
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
  color: #999;
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
  border-top: 1px solid rgba(0, 0, 0, 0.1);
  font-size: 12px;
  color: #999;
}

.message-item.user .message-meta {
  border-top-color: rgba(255, 255, 255, 0.3);
  color: rgba(255, 255, 255, 0.8);
}

.message-time {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

.input-area {
  position: fixed;
  bottom: 60px; /* 位于底部导航栏之上 */
  left: 0;
  right: 0;
  background: white;
  border-top: 1px solid #eee;
  padding: 12px 16px;
  z-index: 999; /* 低于导航栏的z-index */
  /* 适配安全区域 */
  padding-bottom: max(12px, env(safe-area-inset-bottom));
}

.input-container {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.input-container :deep(.van-field) {
  flex: 1;
  background: #f7f8fa;
  border-radius: 20px;
}

.input-container :deep(.van-field__control) {
  padding: 8px 16px;
  border: none;
  max-height: 80px;
}

.send-button {
  height: 36px;
  min-width: 60px;
  border-radius: 18px;
}


</style>
