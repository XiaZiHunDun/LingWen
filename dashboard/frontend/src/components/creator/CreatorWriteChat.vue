<template>
  <aside class="writer-desk__chat-panel" v-show="showChatPanel">
    <div class="writer-desk__chat-header">
      <h2 class="writer-desk__chat-title">AI 对话</h2>
      <div class="writer-desk__chat-actions">
        <button type="button" class="writer-desk__chat-clear" @click="clearChat" title="清除对话">
          🗑️
        </button>
        <button type="button" class="writer-desk__chat-close" @click="$emit('close')">✕</button>
      </div>
    </div>
    <div ref="chatContainerRef" class="writer-desk__chat-messages">
      <div
        v-for="msg in chatMessages"
        :key="msg.id"
        class="writer-desk__chat-message"
        :class="{ 'writer-desk__chat-message--user': msg.role === 'user' }"
      >
        <span class="writer-desk__chat-role">{{ msg.role === 'user' ? '你' : 'AI' }}</span>
        <p class="writer-desk__chat-content">{{ msg.content }}</p>
      </div>
      <div v-if="wb.agent?.generating" class="writer-desk__chat-typing">
        AI 正在思考…
      </div>
    </div>
    <div class="writer-desk__chat-input">
      <input
        v-model="chatInput"
        type="text"
        class="writer-desk__chat-textarea"
        placeholder="和AI讨论你的想法…"
        @keydown.enter="sendChatMessage"
      />
      <button
        type="button"
        class="writer-desk__chat-send"
        :disabled="!chatInput.trim() || wb.agent?.generating"
        @click="sendChatMessage"
      >
        发送
      </button>
    </div>
  </aside>
</template>

<script setup>
import { inject, ref, nextTick, onMounted, watch } from 'vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';
import { logger } from '../../utils/logger.js';

defineProps({
  showChatPanel: {
    type: Boolean,
    default: false,
  },
});

defineEmits(['close']);

const STORAGE_KEY = 'lingwen_chat_messages';
const w = inject(CREATOR_WRITE_KEY);
const wb = w.wb;

const chatInput = ref('');
const chatMessages = ref([]);
const chatContainerRef = ref(null);

function loadChatMessages() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      chatMessages.value = JSON.parse(stored);
    } else {
      chatMessages.value = [
        { id: 1, role: 'assistant', content: '你好！我是你的写作助手。有什么可以帮你的吗？' },
      ];
    }
  } catch {
    chatMessages.value = [
      { id: 1, role: 'assistant', content: '你好！我是你的写作助手。有什么可以帮你的吗？' },
    ];
  }
}

function saveChatMessages() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(chatMessages.value));
  } catch {
    logger.warn('Failed to save chat messages');
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainerRef.value) {
      chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight;
    }
  });
}

function clearChat() {
  chatMessages.value = [
    { id: Date.now(), role: 'assistant', content: '你好！我是你的写作助手。有什么可以帮你的吗？' },
  ];
  saveChatMessages();
}

async function sendChatMessage() {
  if (!chatInput.value.trim() || wb.agent?.generating) return;
  const text = chatInput.value.trim();
  chatInput.value = '';
  chatMessages.value.push({ id: Date.now(), role: 'user', content: text });
  saveChatMessages();
  scrollToBottom();
  try {
    const response = await wb.agent?.chat?.(text);
    chatMessages.value.push({ id: Date.now(), role: 'assistant', content: response });
    saveChatMessages();
    scrollToBottom();
  } catch (error) {
    chatMessages.value.push({ id: Date.now(), role: 'assistant', content: '抱歉，我遇到了一些问题，请稍后再试。' });
    saveChatMessages();
    scrollToBottom();
  }
}

watch(chatMessages, () => {
  scrollToBottom();
}, { deep: true });

onMounted(() => {
  loadChatMessages();
});
</script>