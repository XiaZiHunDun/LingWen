<template>
  <section
    v-show="w.isWorkspaceColumnVisible('write')"
    class="creator-column"
    :class="{
      'creator-column--workbench': w.wb.workbenchEnabled,
      'creator-column--chat-open': showChatPanel,
    }"
    data-testid="column-write"
  >
    <div v-if="!w.wb.workbenchEnabled" class="creator-column__header">
      <h2 class="column-title">写</h2>
      <p class="column-hint">章节状态 · 偏离章高亮</p>
    </div>

    <div v-if="w.wb.workbenchEnabled" class="write-workbench">
      <div class="write-workbench__header">
        <div class="write-workbench__header-left">
          <button
            class="write-workbench__toggle-btn"
            @click="w.wb.leftPanelCollapsed = !w.wb.leftPanelCollapsed"
            :title="w.wb.leftPanelCollapsed ? '展开边栏' : '收起边栏'"
          >
            {{ w.wb.leftPanelCollapsed ? '☰' : '✕' }}
          </button>
          <div class="write-workbench__title-area">
            <h1 class="write-workbench__title">{{ w.overview?.name || '写作中' }}</h1>
            <span class="write-workbench__chapter">第 {{ w.selectedChapter }} 章</span>
          </div>
        </div>
        <div class="write-workbench__header-right">
          <button
            v-if="w.logicCheckResult"
            class="write-workbench__status-badge"
            :class="w.logicCheckResult.passed ? 'pass' : 'fail'"
          >
            {{ w.logicCheckResult.passed ? '✓ 通过' : '✗ 问题' }}
          </button>
          <button
            class="write-workbench__action-btn"
            :class="{ 'write-workbench__action-btn--loading': w.logicCheckRunning }"
            @click="w.runCompanionLogicCheck"
          >
            {{ w.logicCheckRunning ? '检查中…' : '检查逻辑' }}
          </button>
          <button
            class="write-workbench__action-btn write-workbench__action-btn--chat"
            :class="{ 'write-workbench__action-btn--active': showChatPanel }"
            @click="showChatPanel = !showChatPanel"
          >
            💬 {{ showChatPanel ? '收起' : '对话' }}
          </button>
        </div>
      </div>

      <div class="write-workbench__body">
        <aside
          v-show="!w.wb.leftPanelCollapsed"
          class="write-workbench__sidebar"
        >
          <div class="write-workbench__sidebar-section">
            <h3 class="write-workbench__sidebar-title">📚 章节</h3>
            <CreatorChapterList compact />
          </div>
          <div class="write-workbench__sidebar-section">
            <h3 class="write-workbench__sidebar-title">🎯 意图</h3>
            <input
              v-model="w.wb.intentText"
              class="write-workbench__intent-input"
              placeholder="本章要写什么…"
            />
            <div class="write-workbench__mood-tags">
              <button
                v-for="tag in moodTags"
                :key="tag"
                class="write-workbench__mood-tag"
                :class="{ 'write-workbench__mood-tag--active': w.wb.intentMood === tag }"
                @click="w.wb.intentMood = w.wb.intentMood === tag ? '' : tag"
              >
                {{ tag }}
              </button>
            </div>
          </div>
          <div class="write-workbench__sidebar-section">
            <h3 class="write-workbench__sidebar-title">📝 目标</h3>
            <p class="write-workbench__goal-line">{{ w.wb.goalCardLines.line1 }}</p>
            <p class="write-workbench__goal-line">{{ w.wb.goalCardLines.line2 }}</p>
          </div>
        </aside>

        <main class="write-workbench__editor">
          <div class="write-workbench__editor-inner">
            <slot />
          </div>
        </main>

        <aside
          v-show="showChatPanel"
          class="write-workbench__chat-panel"
        >
          <div class="write-workbench__chat-header">
            <span class="write-workbench__chat-title">💬 AI 对话</span>
            <button class="write-workbench__chat-close" @click="showChatPanel = false">✕</button>
          </div>
          <div class="write-workbench__chat-messages">
            <div
              v-for="(msg, idx) in chatMessages"
              :key="idx"
              class="write-workbench__chat-message"
              :class="{ 'write-workbench__chat-message--user': msg.role === 'user' }"
            >
              <span class="write-workbench__chat-avatar">{{ msg.role === 'user' ? '👤' : '🤖' }}</span>
              <span class="write-workbench__chat-content">{{ msg.displayText || msg.content }}</span>
            </div>
            <div v-if="w.wb.agent.generating" class="write-workbench__chat-typing">
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
              :disabled="!chatInput.trim() || w.wb.agent.generating"
              @click="sendChatMessage"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 19V5m0 0l-6 6m6-6l6 6" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
            </button>
          </div>
        </aside>
      </div>

      <div class="write-workbench__footer">
        <div class="write-workbench__footer-left">
          <span class="write-workbench__progress">📖 已完成 {{ w.overview?.chapters_written || 0 }}/{{ w.overview?.max_chapter || 0 }} 章</span>
        </div>
        <div class="write-workbench__footer-right">
          <button
            class="write-workbench__footer-btn write-workbench__footer-btn--primary"
            :class="{ 'write-workbench__footer-btn--loading': w.wb.generateRunning || w.wb.agent.generating }"
            @click="w.wb.startQuickWrite()"
          >
            ✨ {{ w.wb.generateRunning ? '生成中…' : 'AI 续写' }}
          </button>
          <button class="write-workbench__footer-btn" @click="c?.openExportModal('full')">
            📥 导出
          </button>
          <button class="write-workbench__footer-btn" @click="c?.openPublishWizard">
            🚀 发布
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { inject, ref, watch, nextTick } from 'vue';
import CreatorChapterList from './CreatorChapterList.vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';
import { CREATOR_PAGE_CHROME_KEY } from './creatorPageChromeKey.js';

const w = inject(CREATOR_WRITE_KEY);
const c = inject(CREATOR_PAGE_CHROME_KEY);

const moodTags = ['克制', '戏剧', '幽默', '抒情'];
const showChatPanel = ref(false);
const chatInput = ref('');
const chatMessages = ref([
  { role: 'assistant', content: '你好！我是你的写作助手。有什么可以帮你的吗？', displayText: '你好！我是你的写作助手。有什么可以帮你的吗？' },
]);

let typingInterval = null;

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
  nextTick(() => {
    const chatContainer = document.querySelector('.write-workbench__chat-messages');
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  });
  let index = 0;
  typingInterval = setInterval(() => {
    if (index < message.length) {
      newMsg.displayText += message[index];
      index++;
      nextTick(() => {
        const chatContainer = document.querySelector('.write-workbench__chat-messages');
        if (chatContainer) {
          chatContainer.scrollTop = chatContainer.scrollHeight;
        }
      });
    } else {
      clearInterval(typingInterval);
      typingInterval = null;
    }
  }, 50);
}

async function sendChatMessage() {
  if (!chatInput.value.trim() || w.wb.agent.generating) return;
  const userMsg = chatInput.value.trim();
  chatMessages.value.push({ role: 'user', content: userMsg, displayText: userMsg });
  chatInput.value = '';
  nextTick(() => {
    const chatContainer = document.querySelector('.write-workbench__chat-messages');
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  });
  try {
    const response = await w.wb.agent.ask(userMsg);
    startTypingEffect(response);
  } catch (error) {
    chatMessages.value.push({ role: 'assistant', content: '抱歉，我遇到了一些问题。', displayText: '抱歉，我遇到了一些问题。' });
  }
}

watch(() => w.wb.agent.generating, (generating) => {
  if (!generating) {
    nextTick(() => {
      const chatContainer = document.querySelector('.write-workbench__chat-messages');
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    });
  }
});
</script>

<style scoped>
.write-workbench {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-elevated);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.write-workbench__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: linear-gradient(135deg, var(--bg-elevated) 0%, var(--bg-secondary) 100%);
  border-bottom: var(--border-width) solid var(--border-color);
}

.write-workbench__header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.write-workbench__toggle-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: 16px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.write-workbench__toggle-btn:hover {
  background: var(--bg-muted);
  border-color: var(--border-strong);
}

.write-workbench__title-area {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.write-workbench__title {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 600;
  font-family: var(--font-heading);
  color: var(--color-text);
}

.write-workbench__chapter {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.write-workbench__header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.write-workbench__status-badge {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: var(--text-sm);
  font-weight: 500;
  border: none;
  cursor: default;
}

.write-workbench__status-badge.pass {
  background: var(--color-success-soft);
  color: var(--color-success);
}

.write-workbench__status-badge.fail {
  background: var(--color-danger-soft);
  color: var(--color-danger);
}

.write-workbench__action-btn {
  padding: 8px 16px;
  background: transparent;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.write-workbench__action-btn:hover {
  background: var(--bg-muted);
  border-color: var(--border-strong);
}

.write-workbench__action-btn--loading {
  opacity: 0.7;
  pointer-events: none;
}

.write-workbench__action-btn--chat {
  background: var(--color-accent-soft);
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.write-workbench__action-btn--chat:hover,
.write-workbench__action-btn--chat.write-workbench__action-btn--active {
  background: var(--color-accent);
  color: var(--color-on-accent);
}

.write-workbench__body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.write-workbench__sidebar {
  width: 280px;
  flex-shrink: 0;
  padding: 16px;
  background: var(--bg-secondary);
  border-right: var(--border-width) solid var(--border-color);
  overflow-y: auto;
}

.write-workbench__sidebar-section {
  margin-bottom: 20px;
  padding: 14px;
  background: var(--bg-elevated);
  border-radius: var(--radius-md);
}

.write-workbench__sidebar-section:last-child {
  margin-bottom: 0;
}

.write-workbench__sidebar-title {
  margin: 0 0 12px 0;
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}

.write-workbench__intent-input {
  width: 100%;
  padding: 10px 12px;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  background: var(--bg-primary);
  transition: border-color var(--transition-fast);
  box-sizing: border-box;
}

.write-workbench__intent-input:focus {
  outline: none;
  border-color: var(--color-accent);
}

.write-workbench__mood-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.write-workbench__mood-tag {
  padding: 4px 12px;
  border: var(--border-width) solid var(--border-color);
  border-radius: 16px;
  font-size: var(--text-xs);
  cursor: pointer;
  transition: all var(--transition-fast);
  background: transparent;
}

.write-workbench__mood-tag:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.write-workbench__mood-tag--active {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-on-accent);
}

.write-workbench__goal-line {
  margin: 6px 0;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.write-workbench__editor {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: var(--bg-primary);
}

.write-workbench__editor-inner {
  max-width: 800px;
  margin: 0 auto;
}

.write-workbench__chat-panel {
  width: 360px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-elevated);
  border-left: var(--border-width) solid var(--border-color);
}

.write-workbench__chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-bottom: var(--border-width) solid var(--border-color);
}

.write-workbench__chat-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}

.write-workbench__chat-close {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  cursor: pointer;
  color: var(--color-text-secondary);
}

.write-workbench__chat-close:hover {
  background: var(--bg-muted);
}

.write-workbench__chat-messages {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.write-workbench__chat-message {
  display: flex;
  gap: 10px;
}

.write-workbench__chat-message--user {
  flex-direction: row-reverse;
}

.write-workbench__chat-avatar {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-muted);
  border-radius: 50%;
  font-size: 14px;
}

.write-workbench__chat-message--user .write-workbench__chat-avatar {
  background: var(--color-accent-soft);
}

.write-workbench__chat-content {
  max-width: calc(100% - 42px);
  padding: 10px 14px;
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  line-height: 1.6;
  background: var(--bg-muted);
  color: var(--color-text);
}

.write-workbench__chat-message--user .write-workbench__chat-content {
  background: var(--color-accent);
  color: var(--color-on-accent);
}

.write-workbench__chat-typing {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
}

.write-workbench__typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-text-secondary);
  animation: typing-dot 1.4s infinite ease-in-out;
}

.write-workbench__typing-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.write-workbench__typing-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing-dot {
  0%, 80%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  40% {
    opacity: 1;
    transform: scale(1);
  }
}

.write-workbench__chat-input {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: var(--border-width) solid var(--border-color);
}

.write-workbench__chat-textarea {
  flex: 1;
  padding: 10px 14px;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  background: var(--bg-primary);
  transition: border-color var(--transition-fast);
  box-sizing: border-box;
}

.write-workbench__chat-textarea:focus {
  outline: none;
  border-color: var(--color-accent);
}

.write-workbench__chat-send {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-accent);
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-on-accent);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.write-workbench__chat-send:hover:not(:disabled) {
  background: var(--color-accent-hover);
}

.write-workbench__chat-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.write-workbench__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 24px;
  background: var(--bg-secondary);
  border-top: var(--border-width) solid var(--border-color);
}

.write-workbench__footer-left {
  display: flex;
  align-items: center;
}

.write-workbench__progress {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.write-workbench__footer-right {
  display: flex;
  gap: 12px;
}

.write-workbench__footer-btn {
  padding: 10px 20px;
  background: transparent;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.write-workbench__footer-btn:hover {
  background: var(--bg-muted);
  border-color: var(--border-strong);
}

.write-workbench__footer-btn--primary {
  background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-gradient-end) 100%);
  border-color: var(--color-accent);
  color: var(--color-on-accent);
}

.write-workbench__footer-btn--primary:hover {
  background: linear-gradient(135deg, var(--color-accent-hover) 0%, var(--color-accent-gradient-end) 100%);
}

.write-workbench__footer-btn--loading {
  opacity: 0.7;
  pointer-events: none;
}

@media (max-width: 768px) {
  .write-workbench__header {
    padding: 12px 16px;
  }

  .write-workbench__header-right {
    gap: 8px;
  }

  .write-workbench__action-btn {
    padding: 6px 12px;
    font-size: var(--text-xs);
  }

  .write-workbench__sidebar {
    width: 240px;
  }

  .write-workbench__chat-panel {
    width: 100%;
    position: absolute;
    right: 0;
    top: 60px;
    bottom: 60px;
    z-index: 100;
  }

  .write-workbench__editor {
    padding: 16px;
  }

  .write-workbench__footer {
    padding: 12px 16px;
  }

  .write-workbench__footer-btn {
    padding: 8px 14px;
    font-size: var(--text-xs);
  }
}
</style>
