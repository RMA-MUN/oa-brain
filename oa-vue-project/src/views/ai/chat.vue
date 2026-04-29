<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import markdownIt from 'markdown-it'
import { ChatDotRound, Delete, CopyDocument } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()

const messages = ref([
  {
    id: 1,
    role: 'assistant',
    content: '你好！我是AI助手，有什么可以帮助你的吗？',
    loading: false,
    timestamp: new Date().toLocaleTimeString()
  }
])

const inputMessage = ref('')
const messagesContainer = ref(null)
const isLoading = ref(false)
const md = markdownIt()
const sessionId = ref('')

const fetchSessionHistory = async (session_id) => {
  const token = localStorage.getItem('TOKEN_KEY')
  if (!token || !session_id) return

  try {
    const response = await fetch(`http://127.0.0.1:8001/api/session/${session_id}`, {
      method: 'GET',
      headers: {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + token
      }
    })

    if (response.ok) {
      const result = await response.json()

      if (result.code === 200 && result.data && result.data.history && Array.isArray(result.data.history)) {
        const historyMessages = []
        let messageId = 1

        result.data.history.forEach((conversation, convIndex) => {
          if (Array.isArray(conversation) && conversation.length >= 2) {
            historyMessages.push({
              id: messageId++,
              role: 'user',
              content: conversation[0],
              loading: false,
              timestamp: new Date().toLocaleTimeString()
            })

            historyMessages.push({
              id: messageId++,
              role: 'assistant',
              content: conversation[1],
              loading: false,
              timestamp: new Date().toLocaleTimeString()
            })
          }
        })

        if (historyMessages.length > 0) {
          messages.value = historyMessages
        }
      }
    }
  } catch (error) {
    console.error('获取历史会话失败:', error)
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userMessage = inputMessage.value.trim()
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: userMessage,
    loading: false,
    timestamp: new Date().toLocaleTimeString()
  })

  inputMessage.value = ''
  isLoading.value = true

  const assistantMessage = {
    id: Date.now() + 1,
    role: 'assistant',
    content: '',
    loading: true,
    timestamp: new Date().toLocaleTimeString()
  }
  messages.value.push(assistantMessage)

  await scrollToBottom()
  await sendMessageToAPI(assistantMessage, userMessage)
}

const updateUrlWithSessionId = (newSessionId) => {
  if (!newSessionId || sessionId.value === newSessionId) return

  sessionId.value = newSessionId
  localStorage.setItem('AI_SESSION_ID', newSessionId)

  router.push(`/ai/chat/${newSessionId}`)
}

const sendMessageToAPI = async (message, userMessage) => {
  const token = localStorage.getItem('TOKEN_KEY')
  if (!token) {
    message.content = '请先登录系统'
    message.loading = false
    isLoading.value = false
    return
  }

  try {
    const response = await fetch('http://127.0.0.1:8001/api/main-agent/query/stream', {
      method: 'POST',
      headers: {
        'accept': 'application/json',
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        session_id: sessionId.value || '',
        query: userMessage
      })
    })

    if (!response.ok) {
      throw new Error('API请求失败')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const jsonStr = line.substring(6).trim()
            const data = JSON.parse(jsonStr)

            if (data.session_id) {
              updateUrlWithSessionId(data.session_id)
            }

            if (data.type === 'response' && data.content) {
              message.content += data.content
              await scrollToBottom()
            } else if (data.type === 'done') {
              break
            }
          } catch (e) {
            console.error('解析SSE数据失败:', e)
          }
        }
      }
    }

    message.loading = false
    isLoading.value = false
  } catch (error) {
    console.error('API请求错误:', error)
    message.content = '抱歉，服务器暂时不可用，请稍后重试。'
    message.loading = false
    isLoading.value = false
  }
}

const renderMarkdown = (content) => {
  return md.render(content)
}

const handleKeyPress = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    sendMessage()
  }
}

const createNewSession = () => {
  localStorage.removeItem('AI_SESSION_ID')
  sessionId.value = ''

  messages.value = [
    {
      id: Date.now(),
      role: 'assistant',
      content: '你好！我是AI助手，有什么可以帮助你的吗？',
      loading: false,
      timestamp: new Date().toLocaleTimeString()
    }
  ]

  router.push('/ai/chat')
  ElMessage.success('已创建新会话')
}

const clearChat = () => {
  messages.value = [
    {
      id: Date.now(),
      role: 'assistant',
      content: '你好！我是AI助手，有什么可以帮助你的吗？',
      loading: false,
      timestamp: new Date().toLocaleTimeString()
    }
  ]
  ElMessage.success('对话已清空')
}

const copyMessage = (content) => {
  navigator.clipboard.writeText(content).then(() => {
    ElMessage.success('已复制到剪贴板')
  }).catch(() => {
    ElMessage.error('复制失败')
  })
}

const handleSessionIdChange = async (newSessionId) => {
  if (!newSessionId) return

  sessionId.value = newSessionId
  localStorage.setItem('AI_SESSION_ID', newSessionId)
  await fetchSessionHistory(newSessionId)
  await scrollToBottom()
}

onMounted(async () => {
  const routeSessionId = route.params.session_id

  if (routeSessionId) {
    await handleSessionIdChange(routeSessionId)
  } else {
    const storedSessionId = localStorage.getItem('AI_SESSION_ID')
    if (storedSessionId) {
      router.replace(`/ai/chat/${storedSessionId}`)
    }
  }

  scrollToBottom()
})

watch(() => route.params.session_id, async (newSessionId) => {
  if (newSessionId && newSessionId !== sessionId.value) {
    await handleSessionIdChange(newSessionId)
  }
})
</script>

<template>
  <div class="ai-chat-page">
    <!-- 顶部工具栏 -->
    <div class="chat-toolbar">
      <div class="toolbar-left">
        <el-icon class="ai-icon">
          <ChatDotRound />
        </el-icon>
        <span class="toolbar-title">AI助手</span>
      </div>
      <div class="toolbar-right">
        <el-button type="primary" plain size="small" @click="createNewSession">
          新建会话
        </el-button>
        <el-button type="danger" plain size="small" @click="clearChat" :icon="Delete">
          清空对话
        </el-button>
      </div>
    </div>

    <!-- 消息列表区域 -->
    <div ref="messagesContainer" class="messages-container">
      <div v-for="message in messages" :key="message.id" :class="['message-wrapper', message.role]">
        <!-- AI头像 -->
        <div v-if="message.role === 'assistant'" class="avatar ai-avatar">
          <el-icon>
            <ChatDotRound />
          </el-icon>
        </div>

        <!-- 消息内容 -->
        <div class="message-content-wrapper">
          <div :class="['message-bubble', message.role]">
            <div class="message-text" v-html="renderMarkdown(message.content)"
              v-if="!message.loading || message.content"></div>
            <div v-if="message.loading && !message.content" class="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
          <div class="message-actions" v-if="message.role === 'assistant' && !message.loading">
            <el-button link size="small" @click="copyMessage(message.content)" :icon="CopyDocument">
              复制
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <div class="input-wrapper">
        <el-input v-model="inputMessage" type="textarea" :rows="3" placeholder="输入你的问题，按Enter发送，Shift+Enter换行..."
          @keydown="handleKeyPress" resize="none" class="chat-input" />
        <div class="input-actions">
          <span class="input-hint">Enter 发送 · Shift + Enter 换行</span>
          <el-button type="primary" @click="sendMessage" :disabled="!inputMessage.trim() || isLoading"
            :loading="isLoading" class="send-btn">
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ai-chat-page {
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
  background: #ffffff;
}

/* 顶部工具栏 */
.chat-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: #ffffff;
  border-bottom: 1px solid #e8e8e8;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-icon {
  font-size: 24px;
  color: #409eff;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.toolbar-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

/* 消息列表区域 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: #ffffff;
}

.messages-container::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track {
  background: transparent;
}

.messages-container::-webkit-scrollbar-thumb {
  background: #d9d9d9;
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover {
  background: #bfbfbf;
}

.message-wrapper {
  display: flex;
  gap: 12px;
  max-width: 85%;
}

.message-wrapper.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-wrapper.assistant {
  align-self: flex-start;
}

/* 头像 */
.avatar {
  flex-shrink: 0;
}

.ai-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e8f4fd 0%, #f0e6fa 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667eea;
  font-size: 20px;
}

.user-avatar {
  width: 40px;
  height: 40px;
}

/* 消息内容包装器 */
.message-content-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.message-wrapper.user .message-content-wrapper {
  align-items: flex-end;
}

/* 消息气泡 */
.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  word-break: break-word;
}

.message-bubble.user {
  background: #f5f5f5;
  color: #303133;
  border: 1px solid #e8e8e8;
  border-bottom-right-radius: 4px;
}

.message-bubble.assistant {
  background: #f5f5f5;
  color: #303133;
  border: 1px solid #e8e8e8;
  border-bottom-left-radius: 4px;
}

/* 消息操作按钮 */
.message-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.3s;
}

.message-wrapper.assistant:hover .message-actions {
  opacity: 1;
}

/* 输入区域 */
.input-area {
  padding: 20px 24px;
  background: #ffffff;
  border-top: 1px solid #e8e8e8;
}

.input-wrapper {
  max-width: 900px;
  margin: 0 auto;
  background: #fafafa;
  border-radius: 12px;
  border: 1px solid #e8e8e8;
  padding: 16px;
}

.chat-input :deep(.el-textarea__inner) {
  background: transparent;
  border: none;
  color: #303133;
  font-size: 15px;
  resize: none;
  padding: 0;
  box-shadow: none;
}

.chat-input :deep(.el-textarea__inner::placeholder) {
  color: #909399;
}

.chat-input :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.input-hint {
  font-size: 12px;
  color: #909399;
}

.send-btn {
  background: linear-gradient(135deg, #a5d8ff 0%, #cbb8fc 100%);
  border: none;
  padding: 10px 24px;
  border-radius: 8px;
  color: #303133;
}

.send-btn:hover:not(:disabled) {
  opacity: 0.85;
  transform: translateY(-1px);
}

.send-btn:disabled {
  background: #e8e8e8;
  opacity: 0.5;
}

/* 加载动画 */
.loading-dots {
  display: flex;
  gap: 6px;
  padding: 8px 4px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #667eea;
  animation: bounce 1.4s infinite ease-in-out both;
}

.loading-dots span:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dots span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes bounce {

  0%,
  80%,
  100% {
    transform: scale(0);
  }

  40% {
    transform: scale(1);
  }
}

/* Markdown样式 */
.message-text :deep(h1),
.message-text :deep(h2),
.message-text :deep(h3),
.message-text :deep(h4),
.message-text :deep(h5),
.message-text :deep(h6) {
  margin: 16px 0 12px 0;
  color: #303133;
  font-weight: 600;
}

.message-text :deep(p) {
  margin: 8px 0;
  color: #606266;
}

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
  color: #606266;
}

.message-text :deep(li) {
  margin: 4px 0;
}

.message-text :deep(code) {
  background: #f2f6fc;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 13px;
  color: #e74c3c;
}

.message-text :deep(pre) {
  background: #fafafa;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
  border: 1px solid #e8e8e8;
}

.message-text :deep(pre code) {
  background: none;
  padding: 0;
  color: #303133;
}

.message-text :deep(blockquote) {
  border-left: 4px solid #667eea;
  padding-left: 16px;
  margin: 12px 0;
  color: #909399;
  font-style: italic;
}

.message-text :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.message-text :deep(th),
.message-text :deep(td) {
  border: 1px solid #e8e8e8;
  padding: 8px 12px;
  text-align: left;
  color: #606266;
}

.message-text :deep(th) {
  background: #f5f5f5;
  font-weight: 600;
}

.message-text :deep(a) {
  color: #409eff;
  text-decoration: none;
}

.message-text :deep(a:hover) {
  text-decoration: underline;
}

.message-text :deep(strong) {
  color: #303133;
  font-weight: 600;
}

.message-text :deep(hr) {
  border: none;
  border-top: 1px solid #e8e8e8;
  margin: 16px 0;
}
</style>
