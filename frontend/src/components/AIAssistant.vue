<template>
  <div class="ai-assistant">
    <!-- 悬浮按钮 -->
    <div 
      class="ai-fab" 
      :class="{ 'is-open': isOpen }"
      @click="toggleChat"
    >
      <van-icon :name="isOpen ? 'cross' : 'chat-o'" size="24" />
    </div>

    <!-- 对话框 -->
    <transition name="slide-up">
      <div v-if="isOpen" class="ai-dialog">
        <div class="ai-header">
          <div class="ai-title">
            <van-icon name="smile-o" size="20" />
            <span>AI财务助手</span>
          </div>
          <van-icon name="cross" size="20" @click="isOpen = false" class="close-btn" />
        </div>

        <div class="ai-messages" ref="messagesRef">
          <!-- 欢迎消息 -->
          <div v-if="messages.length === 0" class="welcome-message">
            <div class="welcome-icon">🤖</div>
            <h3>你好，我是AI财务助手</h3>
            <p>我可以帮你分析账本数据，回答财务相关问题。试试这些问题：</p>
            <div class="quick-questions">
              <van-tag 
                v-for="q in quickQuestions" 
                :key="q" 
                plain 
                type="primary"
                @click="sendQuickQuestion(q)"
              >
                {{ q }}
              </van-tag>
            </div>
          </div>

          <!-- 消息列表 -->
          <div 
            v-for="(msg, index) in messages" 
            :key="index"
            class="message"
            :class="msg.role"
          >
            <div class="message-content">
              <div class="message-text" v-html="formatMessage(msg.content)"></div>
            </div>
          </div>

          <!-- 加载中 - 只在流式内容还没开始时显示 -->
          <div v-if="isLoading && messages.length > 0 && messages[messages.length - 1].role === 'assistant' && !messages[messages.length - 1].content" class="message assistant">
            <div class="message-content">
              <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>

        <div class="ai-input">
          <van-field
            v-model="inputText"
            placeholder="输入你的问题..."
            :disabled="isLoading"
            @keyup.enter="sendMessage"
          >
            <template #button>
              <van-button 
                type="primary" 
                size="small" 
                :loading="isLoading"
                :disabled="!inputText.trim()"
                @click="sendMessage"
              >
                发送
              </van-button>
            </template>
          </van-field>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue';
import { showToast } from 'vant';
import { marked } from 'marked';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const isOpen = ref(false);
const inputText = ref('');
const messages = ref<Message[]>([]);
const isLoading = ref(false);
const messagesRef = ref<HTMLElement>();
const aiEnabled = ref(false);

const quickQuestions = [
  '这个月花了多少钱？',
  '分析我的消费习惯',
  '给我一些理财建议'
];

// 检查AI服务状态
const checkAIStatus = async () => {
  try {
    const response = await fetch('/api/ai/status');
    const data = await response.json();
    aiEnabled.value = data.enabled;
  } catch (error) {
    aiEnabled.value = false;
  }
};

onMounted(() => {
  checkAIStatus();
});

const toggleChat = () => {
  if (!aiEnabled.value && !isOpen.value) {
    showToast({
      message: '请先配置DASHSCOPE_API_KEY',
      position: 'top'
    });
    return;
  }
  isOpen.value = !isOpen.value;
};

const sendQuickQuestion = (question: string) => {
  inputText.value = question;
  sendMessage();
};

const sendMessage = async () => {
  const text = inputText.value.trim();
  if (!text || isLoading.value) return;

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: text
  });
  inputText.value = '';
  isLoading.value = true;

  // 滚动到底部
  await nextTick();
  scrollToBottom();

  // 添加一个空的 AI 消息用于流式更新
  const assistantMessageIndex = messages.value.length;
  messages.value.push({
    role: 'assistant',
    content: ''
  });

  try {
    const response = await fetch('/api/ai/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        messages: messages.value.slice(0, -1).map(m => ({
          role: m.role,
          content: m.content
        }))
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('无法获取响应流');
    }

    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      
      // 处理 SSE 数据 (格式: data: {...}\n\n)
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || ''; // 保留不完整的行

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            
            if (data.type === 'content') {
              // 追加内容到 AI 消息
              messages.value[assistantMessageIndex].content += data.content;
              // 滚动到底部
              await nextTick();
              scrollToBottom();
            } else if (data.type === 'error') {
              messages.value[assistantMessageIndex].content = `抱歉，出现了问题：${data.content}`;
            }
            // type === 'done' 时不需要处理
          } catch (e) {
            console.error('解析 SSE 数据失败:', e);
          }
        }
      }
    }

    // 如果没有收到任何内容，显示错误
    if (!messages.value[assistantMessageIndex].content) {
      messages.value[assistantMessageIndex].content = '抱歉，未能获取到回复';
    }

  } catch (error: any) {
    messages.value[assistantMessageIndex].content = `网络错误，请稍后重试：${error.message}`;
  } finally {
    isLoading.value = false;
    await nextTick();
    scrollToBottom();
  }
};

const scrollToBottom = () => {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight;
  }
};

const formatMessage = (content: string): string => {
  try {
    // 使用marked解析markdown
    return marked(content, { breaks: true }) as string;
  } catch {
    return content;
  }
};
</script>

<style scoped>
.ai-assistant {
  position: fixed;
  bottom: 80px;
  right: 16px;
  z-index: 999;
}

.ai-fab {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 184, 148, 0.4);
  cursor: pointer;
  transition: all 0.3s ease;
}

.ai-fab:hover {
  transform: scale(1.05);
  box-shadow: 0 6px 16px rgba(0, 184, 148, 0.5);
}

.ai-fab.is-open {
  background: linear-gradient(135deg, #ff7675 0%, #fd79a8 100%);
}

.ai-dialog {
  position: fixed;
  top: 46px;  /* 顶部导航栏高度 */
  left: 0;
  right: 0;
  bottom: 50px;  /* 底部tabbar高度 */
  width: 100vw;
  height: auto;
  background: var(--van-background-2);
  border-radius: 0;
  box-shadow: none;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 1000;
}

.ai-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
  color: white;
}

.ai-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.close-btn {
  cursor: pointer;
  opacity: 0.8;
  transition: opacity 0.2s;
}

.close-btn:hover {
  opacity: 1;
}

.ai-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.welcome-message {
  text-align: center;
  padding: 20px;
  color: var(--van-text-color);
}

.welcome-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.welcome-message h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
}

.welcome-message p {
  margin: 0 0 16px 0;
  font-size: 14px;
  color: var(--van-text-color-2);
}

.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.quick-questions .van-tag {
  cursor: pointer;
  transition: transform 0.2s;
}

.quick-questions .van-tag:hover {
  transform: scale(1.05);
}

.message {
  display: flex;
  max-width: 85%;
}

.message.user {
  align-self: flex-end;
}

.message.assistant {
  align-self: flex-start;
}

.message-content {
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.message.user .message-content {
  background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);
  color: #ffffff;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-content {
  background: #f5f5f5;
  color: #333333;
  border-bottom-left-radius: 4px;
}

/* 深色模式适配 */
@media (prefers-color-scheme: dark) {
  .message.assistant .message-content {
    background: #2c2c2c;
    color: #e0e0e0;
  }
}

/* Vant深色模式类名适配 */
.van-theme-dark .message.assistant .message-content {
  background: #2c2c2c;
  color: #e0e0e0;
}

.message-text :deep(p) {
  margin: 0 0 8px 0;
}

.message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-text :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}

.loading-dots {
  display: flex;
  gap: 4px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--van-text-color-3);
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

.ai-input {
  padding: 12px;
  border-top: 1px solid var(--van-border-color);
  background: var(--van-background-2);
}

.ai-input :deep(.van-field) {
  background: #f5f5f5;
  border-radius: 20px;
  padding: 4px 4px 4px 16px;
}

.ai-input :deep(.van-field__control) {
  background: transparent;
  color: #333333 !important;
}

.ai-input :deep(.van-field__control::placeholder) {
  color: #999999;
}

/* 深色模式输入框适配 */
@media (prefers-color-scheme: dark) {
  .ai-input :deep(.van-field) {
    background: #3a3a3a;
  }
  .ai-input :deep(.van-field__control) {
    color: #ffffff !important;
  }
  .ai-input :deep(.van-field__control::placeholder) {
    color: #888888;
  }
}

.van-theme-dark .ai-input :deep(.van-field) {
  background: #3a3a3a;
}

.van-theme-dark .ai-input :deep(.van-field__control) {
  color: #ffffff !important;
}

.van-theme-dark .ai-input :deep(.van-field__control::placeholder) {
  color: #888888;
}

/* 动画 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
