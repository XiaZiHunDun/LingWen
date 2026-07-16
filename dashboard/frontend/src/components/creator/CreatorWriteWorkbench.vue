<template>
  <div
    class="writer-desk"
    :class="{
      'writer-desk--sidebar-collapsed': wb.leftPanelCollapsed,
      'writer-desk--chat-open': showChatPanel,
    }"
    data-testid="writer-desk"
  >
    <header class="writer-desk__header">
      <div class="writer-desk__header-left">
        <button
          type="button"
          class="writer-desk__sidebar-toggle"
          data-testid="sidebar-toggle"
          @click="wb.leftPanelCollapsed = !wb.leftPanelCollapsed"
        >
          {{ wb.leftPanelCollapsed ? '☰' : '✕' }}
        </button>
        <span class="writer-desk__title">{{ w.overview?.name || '写作中' }}</span>
      </div>
      <div class="writer-desk__header-center">
        <span class="writer-desk__chapter-indicator">第 {{ w.selectedChapter }} 章</span>
        <button
          type="button"
          class="writer-desk__action-btn"
          :disabled="w.logicCheckRunning"
          @click="w.runCompanionLogicCheck"
        >
          <span>✓</span>
          <span>{{ w.logicCheckRunning ? '检查中…' : '逻辑检查' }}</span>
        </button>
        <span
          v-if="w.logicCheckResult"
          class="writer-desk__check-status"
          :class="{ 'writer-desk__check-status--passed': w.logicCheckResult.passed }"
        >
          {{ w.logicCheckResult.passed ? '✓ 通过' : '✗ 有问题' }}
        </span>
      </div>
      <div class="writer-desk__header-right">
        <button
          type="button"
          class="writer-desk__chat-toggle"
          :class="{ 'writer-desk__chat-toggle--active': showChatPanel }"
          @click="showChatPanel = !showChatPanel"
        >
          <span>💬</span>
          <span>{{ showChatPanel ? '收起对话' : 'AI对话' }}</span>
        </button>
      </div>
    </header>

    <div class="writer-desk__body">
      <aside class="writer-desk__sidebar" v-show="!wb.leftPanelCollapsed">
        <section class="writer-desk__sidebar-section">
          <h2 class="writer-desk__sidebar-title">章节列表</h2>
          <div class="writer-desk__chapter-list">
            <slot name="chapters" />
          </div>
        </section>

        <section class="writer-desk__sidebar-section">
          <h2 class="writer-desk__sidebar-title">本章意图</h2>
          <input
            v-model="wb.intentText"
            type="text"
            class="writer-desk__intent-input"
            placeholder="本章要写什么…"
          />
          <div class="writer-desk__mood-tags">
            <button
              v-for="tag in moodTags"
              :key="tag"
              type="button"
              class="writer-desk__mood-tag"
              :class="{ 'writer-desk__mood-tag--active': wb.intentMood === tag }"
              @click="wb.intentMood = wb.intentMood === tag ? '' : tag"
            >
              {{ tag }}
            </button>
          </div>
        </section>

        <section class="writer-desk__sidebar-section">
          <h2 class="writer-desk__sidebar-title">写作目标</h2>
          <p class="writer-desk__goal-line">{{ wb.goalCardLines.line1 }}</p>
          <p class="writer-desk__goal-line">{{ wb.goalCardLines.line2 }}</p>
        </section>
      </aside>

      <main class="writer-desk__editor">
        <div class="writer-desk__editor-inner">
          <slot />
        </div>
      </main>

      <aside class="writer-desk__chat-panel" v-show="showChatPanel">
        <div class="writer-desk__chat-header">
          <h2 class="writer-desk__chat-title">AI 对话</h2>
          <button type="button" class="writer-desk__chat-close" @click="showChatPanel = false">✕</button>
        </div>
        <div class="writer-desk__chat-messages">
          <div
            v-for="(msg, idx) in chatMessages"
            :key="idx"
            class="writer-desk__chat-message"
            :class="{ 'writer-desk__chat-message--user': msg.role === 'user' }"
          >
            <span class="writer-desk__chat-role">{{ msg.role === 'user' ? '你' : 'AI' }}</span>
            <p class="writer-desk__chat-content">{{ msg.content }}</p>
          </div>
          <div v-if="wb.agent.generating" class="writer-desk__chat-typing">
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
            :disabled="!chatInput.trim() || wb.agent.generating"
            @click="sendChatMessage"
          >
            发送
          </button>
        </div>
      </aside>
    </div>

    <footer class="writer-desk__footer">
      <div class="writer-desk__footer-left">
        <span class="writer-desk__progress">
          已完成 {{ w.overview?.chapters_written || 0 }}/{{ w.overview?.max_chapter || 0 }} 章
        </span>
      </div>
      <div class="writer-desk__footer-right">
        <button
          type="button"
          class="writer-desk__generate-btn"
          :disabled="wb.generateRunning || wb.agent.generating"
          @click="wb.startQuickWrite()"
        >
          <span>✨</span>
          <span>{{ wb.generateRunning ? '生成中…' : 'AI 生成' }}</span>
        </button>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { inject, ref } from 'vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';
import '../../assets/creator-write-workbench.css';

const w = inject(CREATOR_WRITE_KEY);
const wb = w.wb;

const moodTags = ['克制', '戏剧', '幽默', '抒情'];
const showChatPanel = ref(false);
const chatInput = ref('');
const chatMessages = ref([
  { role: 'assistant', content: '你好！我是你的写作助手。有什么可以帮你的吗？' },
]);

async function sendChatMessage() {
  if (!chatInput.value.trim() || wb.agent.generating) return;
  
  const text = chatInput.value.trim();
  chatMessages.value.push({ role: 'user', content: text });
  chatInput.value = '';
  
  await wb.agent.submitPrompt(text);
  
  if (wb.agent.streamDisplayText) {
    chatMessages.value.push({ role: 'assistant', content: wb.agent.streamDisplayText });
  }
}
</script>

<style scoped>
.writer-desk {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background: var(--bg-primary);
}

.writer-desk__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background: var(--bg-secondary);
  border-bottom: var(--border-width) solid var(--border-color);
  flex-shrink: 0;
  height: 48px;
  box-sizing: border-box;
}

.writer-desk__header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.writer-desk__sidebar-toggle {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 18px;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.writer-desk__sidebar-toggle:hover {
  background: var(--bg-muted);
  color: var(--color-text);
}

.writer-desk__title {
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
  font-family: var(--font-heading);
}

.writer-desk__header-center {
  display: flex;
  align-items: center;
  gap: 16px;
}

.writer-desk__chapter-indicator {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  padding: 4px 12px;
  background: var(--bg-muted);
  border-radius: var(--radius-sm);
}

.writer-desk__action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  padding: 6px 14px;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all 0.2s ease;
}

.writer-desk__action-btn:hover:not(:disabled) {
  background: var(--bg-muted);
  border-color: var(--color-accent-muted);
  color: var(--color-text);
}

.writer-desk__action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.writer-desk__check-status {
  font-size: var(--text-xs);
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(200, 80, 80, 0.1);
  color: var(--color-danger);
  font-weight: 500;
}

.writer-desk__check-status--passed {
  background: rgba(80, 180, 100, 0.1);
  color: var(--color-success);
}

.writer-desk__header-right {
  display: flex;
  align-items: center;
}

.writer-desk__chat-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--text-sm);
  padding: 6px 14px;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all 0.2s ease;
}

.writer-desk__chat-toggle:hover {
  background: var(--bg-muted);
  border-color: var(--color-accent-muted);
  color: var(--color-text);
}

.writer-desk__chat-toggle--active {
  background: var(--color-accent-soft);
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.writer-desk__body {
  display: flex;
  flex: 1;
  min-height: 0;
}

.writer-desk__sidebar {
  width: 260px;
  flex-shrink: 0;
  background: var(--bg-secondary);
  border-right: var(--border-width) solid var(--border-color);
  overflow-y: auto;
  transition: width 0.3s ease;
}

.writer-desk--sidebar-collapsed .writer-desk__sidebar {
  width: 0;
  overflow: hidden;
  border-right: none;
}

.writer-desk__sidebar-section {
  padding: 16px;
  border-bottom: var(--border-width) solid var(--border-color);
}

.writer-desk__sidebar-section:last-child {
  border-bottom: none;
}

.writer-desk__sidebar-title {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-dim);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 0 0 12px;
}

.writer-desk__chapter-list {
  max-height: 180px;
  overflow-y: auto;
}

.writer-desk__intent-input {
  width: 100%;
  padding: 8px 12px;
  font-size: var(--text-sm);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  margin-bottom: 10px;
  box-sizing: border-box;
}

.writer-desk__intent-input:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-soft);
}

.writer-desk__mood-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.writer-desk__mood-tag {
  font-size: var(--text-xs);
  padding: 5px 12px;
  border: var(--border-width) solid var(--border-color);
  border-radius: 999px;
  background: var(--bg-primary);
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all 0.2s ease;
}

.writer-desk__mood-tag:hover {
  border-color: var(--color-accent-muted);
}

.writer-desk__mood-tag--active {
  background: var(--gradient-accent);
  color: var(--color-on-accent);
  border-color: transparent;
}

.writer-desk__goal-line {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
  margin: 4px 0;
  line-height: 1.6;
}

.writer-desk__editor {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  justify-content: center;
  padding: 24px;
  background: var(--bg-primary);
}

.writer-desk__editor-inner {
  width: 100%;
  max-width: 900px;
  min-height: 100%;
}

.writer-desk__chat-panel {
  width: 320px;
  flex-shrink: 0;
  background: var(--bg-secondary);
  border-left: var(--border-width) solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.writer-desk__chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: var(--border-width) solid var(--border-color);
  flex-shrink: 0;
}

.writer-desk__chat-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.writer-desk__chat-close {
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.writer-desk__chat-close:hover {
  background: var(--bg-muted);
  color: var(--color-text);
}

.writer-desk__chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.writer-desk__chat-message {
  margin-bottom: 16px;
}

.writer-desk__chat-message--user {
  text-align: right;
}

.writer-desk__chat-role {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
  margin-bottom: 4px;
  display: block;
}

.writer-desk__chat-content {
  font-size: var(--text-sm);
  color: var(--color-text);
  line-height: 1.6;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  margin: 0;
  display: inline-block;
  max-width: 100%;
}

.writer-desk__chat-message--user .writer-desk__chat-content {
  background: var(--color-accent-soft);
  color: var(--color-accent);
}

.writer-desk__chat-typing {
  font-size: var(--text-sm);
  color: var(--color-text-dim);
  padding: 8px 12px;
  background: var(--bg-muted);
  border-radius: var(--radius-sm);
}

.writer-desk__chat-input {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  border-top: var(--border-width) solid var(--border-color);
  flex-shrink: 0;
}

.writer-desk__chat-textarea {
  flex: 1;
  padding: 8px 12px;
  font-size: var(--text-sm);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
  background: var(--bg-primary);
  box-sizing: border-box;
}

.writer-desk__chat-textarea:focus {
  outline: none;
  border-color: var(--color-accent);
  box-shadow: 0 0 0 3px var(--color-accent-soft);
}

.writer-desk__chat-send {
  padding: 8px 16px;
  font-size: var(--text-sm);
  border: none;
  border-radius: var(--radius-sm);
  background: var(--gradient-accent);
  color: var(--color-on-accent);
  cursor: pointer;
  transition: all 0.2s ease;
}

.writer-desk__chat-send:hover:not(:disabled) {
  filter: brightness(1.08);
}

.writer-desk__chat-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.writer-desk__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  background: var(--bg-secondary);
  border-top: var(--border-width) solid var(--border-color);
  flex-shrink: 0;
  height: 48px;
  box-sizing: border-box;
}

.writer-desk__footer-left {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.writer-desk__progress {
  font-weight: 500;
}

.writer-desk__footer-right {
  display: flex;
  gap: 12px;
}

.writer-desk__generate-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--text-base);
  font-weight: 600;
  padding: 8px 24px;
  background: var(--gradient-accent);
  color: var(--color-on-accent);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s ease;
}

.writer-desk__generate-btn:hover:not(:disabled) {
  filter: brightness(1.08);
  box-shadow: 0 4px 16px rgba(168, 90, 50, 0.25);
  transform: translateY(-1px);
}

.writer-desk__generate-btn:active:not(:disabled) {
  transform: translateY(0);
}

.writer-desk__generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .writer-desk__header {
    padding: 10px 12px;
  }

  .writer-desk__header-center {
    gap: 8px;
  }

  .writer-desk__chapter-indicator {
    display: none;
  }

  .writer-desk__sidebar {
    position: fixed;
    left: 0;
    top: 48px;
    bottom: 48px;
    z-index: 100;
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.1);
  }

  .writer-desk--sidebar-collapsed .writer-desk__sidebar {
    left: -260px;
  }

  .writer-desk__chat-panel {
    position: fixed;
    right: 0;
    top: 48px;
    bottom: 48px;
    z-index: 100;
    box-shadow: -4px 0 20px rgba(0, 0, 0, 0.1);
    width: 280px;
  }

  .writer-desk__editor {
    padding: 16px;
  }

  .writer-desk__footer {
    padding: 10px 12px;
  }

  .writer-desk__generate-btn {
    padding: 8px 16px;
    font-size: var(--text-sm);
  }
}
</style>
