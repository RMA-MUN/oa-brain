<script setup>
import { ref } from 'vue'
import AIChatWindow from './AIChatWindow.vue'

const showChatWindow = ref(false)
const isDragging = ref(false)
const ballStyle = ref({
  left: 'calc(100% - 90px)',
  top: 'calc(100% - 90px)'
})
const ballElement = ref(null)

const toggleChatWindow = () => {
  showChatWindow.value = !showChatWindow.value
}

const handleMouseDown = (event) => {
  event.preventDefault()
  isDragging.value = true

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
}

const handleMouseMove = (event) => {
  if (!isDragging.value || !ballElement.value) return

  const ballWidth = ballElement.value.offsetWidth
  const ballHeight = ballElement.value.offsetHeight

  let newLeft = event.clientX - ballWidth / 2
  let newTop = event.clientY - ballHeight / 2

  newLeft = Math.max(0, Math.min(window.innerWidth - ballWidth, newLeft))
  newTop = Math.max(0, Math.min(window.innerHeight - ballHeight, newTop))

  ballStyle.value.left = newLeft + 'px'
  ballStyle.value.top = newTop + 'px'
}

const handleMouseUp = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', handleMouseMove)
  document.removeEventListener('mouseup', handleMouseUp)
}
</script>

<template>
  <div>
    <button ref="ballElement" class="floating-ball" :style="ballStyle" @click="toggleChatWindow"
      @mousedown="handleMouseDown" :class="{ 'dragging': isDragging }" title="AI助手">
      <span class="ai-icon">🤖</span>
    </button>

    <AIChatWindow v-if="showChatWindow" @close="showChatWindow = false" />
  </div>
</template>

<style scoped>
.floating-ball {
  position: fixed;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #1a1a1a;
  border: 1px solid #333;
  color: white;
  font-size: 24px;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.6);
  z-index: 9999;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  user-select: none;
}

.floating-ball:hover {
  transform: scale(1.1);
  background: #2a2a2a;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.8);
}

.floating-ball.dragging {
  cursor: grabbing;
  transform: scale(1.15);
  background: #333;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.9);
  transition: none;
}

.ai-icon {
  display: block;
}
</style>