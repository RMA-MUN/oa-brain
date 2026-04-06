<script setup>
import { ref, onMounted, watch } from 'vue'
import markdownIt from 'markdown-it'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'update:modelValue'])

const messages = ref([
  {
    id: 1,
    role: 'assistant',
    content: '你好！我是AI助手，有什么可以帮助你的吗？',
    loading: false
  }
])

const inputMessage = ref('')
const isTyping = ref(false)
const md = markdownIt()

const closeChat = () => {
  emit('close')
}

const sendMessage = async () => {
  if (!inputMessage.value.trim()) return

  const userMessage = inputMessage.value.trim()
  messages.value.push({
    id: Date.now(),
    role: 'user',
    content: userMessage,
    loading: false
  })

  inputMessage.value = ''

  const assistantMessage = {
    id: Date.now() + 1,
    role: 'assistant',
    content: '',
    loading: true
  }
  messages.value.push(assistantMessage)

  await simulateTyping(assistantMessage)
}

const simulateTyping = async (message) => {
  const responses = [
    '我理解你的问题了，让我为你分析一下...',
    '这是一个很好的问题！根据我的分析：\n\n1. 首先需要考虑问题的核心要点\n2. 然后分析可能的解决方案\n3. 最后给出建议',
    '谢谢你的提问。关于这个话题，我可以提供一些参考信息：\n\n- **优点**：操作简单，效率高\n- **缺点**：需要一定的学习成本\n\n你可以根据实际情况选择最适合的方案。'
  ]

  const response = responses[Math.floor(Math.random() * responses.length)]
  let currentIndex = 0
  message.loading = true

  return new Promise((resolve) => {
    const timer = setInterval(() => {
      if (currentIndex < response.length) {
        message.content = response.substring(0, currentIndex + 1)
        currentIndex++
      } else {
        clearInterval(timer)
        message.loading = false
        resolve()
      }
    }, 30)
  })
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
</script>
<template>
  <div class="chat-window">
    <div class="chat-header">
      <h3>AI助手</h3><button class="close-btn" @click="closeChat">×</button>
    </div>
    <div class="chat-messages">
      <div v-for="message in messages" :key="message.id" :class="['message', message.role]">
        <div class="message-content" v-html="renderMarkdown(message.content)"></div>
        <div v-if="message.loading" class="typing-indicator"><span></span><span></span><span></span></div>
      </div>
    </div>
    <div class="chat-input"><textarea v-model="inputMessage" @keydown="handleKeyPress" placeholder="输入你的问题..."
        rows="1"></textarea><button class="send-btn" @click="sendMessage" :disabled="!inputMessage.trim()">发送</button>
    </div>
  </div>
</template>
<style scoped>
.chat-window {
  position: fixed;
  bottom: 100px;
  right: 30px;
  width: 400px;
  height: 500px;
  background: #1a1a1a;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.8);
  z-index: 9998;
  display: flex;
  flex-direction: column;
  border: 1px solid #333;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #2a2a2a;
  color: white;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  border-bottom: 1px solid #333;
}

.chat-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
}

.close-btn:hover {
  color: #ccc;
}

.chat-messages {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  background: #1a1a1a;
}

.chat-messages::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track {
  background: #2a2a2a;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #444;
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.message {
  margin-bottom: 16px;
  max-width: 85%;
}

.message.user {
  margin-left: auto;
}

.message.assistant {
  margin-right: auto;
}

.message-content {
  padding: 12px 16px;
  border-radius: 18px;
  line-height: 1.5;
  word-break: break-word;
}

.message.user .message-content {
  background: #333;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-content {
  background: #2a2a2a;
  color: #e0e0e0;
  border-bottom-left-radius: 4px;
  border: 1px solid #444;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: #2a2a2a;
  border-radius: 18px;
  border-bottom-left-radius: 4px;
  border: 1px solid #444;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #666;
  animation: typing 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) {
  animation-delay: -0.32s;
}

.typing-indicator span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes typing {
  0% {
    transform: scale(0);
  }

  50% {
    transform: scale(1);
  }

  100% {
    transform: scale(0);
  }
}

.chat-input {
  display: flex;
  padding: 12px;
  border-top: 1px solid #333;
  background: #1a1a1a;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
}

.chat-input textarea {
  flex: 1;
  border: 1px solid #444;
  border-radius: 20px;
  padding: 10px 16px;
  resize: none;
  font-size: 14px;
  outline: none;
  min-height: 20px;
  max-height: 120px;
  overflow-y: auto;
  background: #2a2a2a;
  color: #e0e0e0;
}

.chat-input textarea:focus {
  border-color: #555;
}

.chat-input textarea::placeholder {
  color: #666;
}

.send-btn {
  margin-left: 8px;
  padding: 10px 20px;
  background: #333;
  color: white;
  border: 1px solid #444;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.send-btn:hover:not(:disabled) {
  background: #444;
  transform: translateY(-1px);
}

.send-btn:disabled {
  background: #2a2a2a;
  border-color: #333;
  color: #666;
  cursor: not-allowed;
}

.message-content h1,
.message-content h2,
.message-content h3,
.message-content h4,
.message-content h5,
.message-content h6 {
  margin: 12px 0 8px 0;
  line-height: 1.2;
  color: #ffffff;
}

.message-content p {
  margin: 8px 0;
  color: #e0e0e0;
}

.message-content ul,
.message-content ol {
  margin: 8px 0;
  padding-left: 20px;
  color: #e0e0e0;
}

.message-content li {
  margin: 4px 0;
}

.message-content code {
  background: #333;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 13px;
  color: #e0e0e0;
}

.message-content pre {
  background: #2a2a2a;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
  border: 1px solid #444;
}

.message-content pre code {
  background: none;
  padding: 0;
}

.message-content blockquote {
  border-left: 4px solid #555;
  padding-left: 16px;
  margin: 12px 0;
  color: #999;
  font-style: italic;
}

.message-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
}

.message-content th,
.message-content td {
  border: 1px solid #444;
  padding: 8px;
  text-align: left;
  color: #e0e0e0;
}

.message-content th {
  background: #2a2a2a;
}

.message-content a {
  color: #888;
  text-decoration: none;
}

.message-content a:hover {
  text-decoration: underline;
  color: #aaa;
}

.message-content img {
  max-width: 100%;
  border-radius: 4px;
  margin: 8px 0;
}
</style>