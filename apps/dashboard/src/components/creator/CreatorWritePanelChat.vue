<template>
  <aside
    v-show="showChatPanel"
    class="write-workbench__chat-panel"
  >
    <div class="write-workbench__chat-header">
      <span class="write-workbench__chat-title">💬 AI 对话</span>
      <button class="write-workbench__chat-close" @click="$emit('close')">✕</button>
    </div>
    <div ref="chatContainerRef" class="write-workbench__chat-messages">
      <div
        v-for="(msg, idx) in chatMessages"
        :key="idx"
        class="write-workbench__chat-message"
        :class="{ 'write-workbench__chat-message--user': msg.role === 'user' }"
      >
        <span class="write-workbench__chat-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</span>
        <span class="write-workbench__chat-content">{{ msg.displayText || msg.content }}</span>
      </div>
      <div v-if="wb.agent?.generating" class="write-workbench__chat-typing">
        <span class="write-workbench__typing-dot"></span>
        <span class="write-workbench__typing-dot"></span>
        <span class="write-workbench__typing-dot"></span>
        <span>AI 思考中…</span>
      </div>
    </div>
    <div class="write-workbench__chat-input">
      <input
        v-model="chatInput"
        class="write-workbench__chat-textarea"
        placeholder="和AI讨论你的想法…"
        @keydown.enter="sendChatMessage"
      />
      <button
        class="write-workbench__chat-send"
        :disabled="!chatInput.trim() || wb.agent?.generating"
        @click="sendChatMessage"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 19V5m0 0l-6 6m6-6l6 6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { inject, ref, watch, onUnmounted } from 'vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';

defineProps({
  showChatPanel: {
    type: Boolean,
    default: false,
  },
});

defineEmits(['close']);

const w = inject(CREATOR_WRITE_KEY);
const wb = w.wb;

const chatInput = ref('');
const chatMessages = ref([
  { role: 'assistant', content: '你好！我是你的写作助手。有什么可以帮你的吗？', displayText: '你好！我是你的写作助手。有什么可以帮你的吗？' },
]);
const chatContainerRef = ref(null);
let typingInterval = null;

function scrollToBottom() {
  requestAnimationFrame(() => {
    if (chatContainerRef.value) {
      chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight;
    }
  });
}

function startTypingEffect(message) {
  if (typingInterval) {
    clearInterval(typingInterval);
  }
  const newMsg = {
    role: 'assistant',
    content: message,
    displayText: '',
  };
  chatMessages.value.push(newMsg);
  scrollToBottom();
  let index = 0;
  typingInterval = setInterval(() => {
    if (index < message.length) {
      newMsg.displayText += message[index];
      index++;
      scrollToBottom();
    } else {
      clearInterval(typingInterval);
      typingInterval = null;
    }
  }, 50);
}

async function sendChatMessage() {
  if (!chatInput.value.trim() || wb.agent?.generating) return;
  const userMsg = chatInput.value.trim();
  chatMessages.value.push({ role: 'user', content: userMsg, displayText: userMsg });
  chatInput.value = '';
  scrollToBottom();
  try {
    const response = await wb.agent?.ask?.(userMsg);
    startTypingEffect(response);
  } catch (error) {
    chatMessages.value.push({ role: 'assistant', content: '抱歉，我遇到了一些问题。', displayText: '抱歉，我遇到了一些问题。' });
    scrollToBottom();
  }
}

watch(() => wb.agent?.generating, (generating) => {
  if (!generating) {
    scrollToBottom();
  }
});

onUnmounted(() => {
  if (typingInterval) {
    clearInterval(typingInterval);
  }
});
</script>