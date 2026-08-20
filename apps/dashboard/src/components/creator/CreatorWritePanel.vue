<template>
  <section
    v-show="w.isWorkspaceColumnVisible('write')"
    class="creator-column column-write"
    :class="{
      'creator-column--workbench': w.wb.workbenchEnabled,
      'creator-column--chat-open': showChatPanel,
    }"
    data-testid="column-write"
  >
    <div v-if="!w.wb.workbenchEnabled" class="creator-column__header column-write">
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

        <CreatorWritePanelChat
          :show-chat-panel="showChatPanel"
          @close="showChatPanel = false"
        />
      </div>

      <CreatorWritePanelFooter />
    </div>
  </section>
</template>

<script setup>
import { inject, ref } from 'vue';
import CreatorChapterList from './CreatorChapterList.vue';
import CreatorWritePanelChat from './CreatorWritePanelChat.vue';
import CreatorWritePanelFooter from './CreatorWritePanelFooter.vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';

const w = inject(CREATOR_WRITE_KEY);

const moodTags = ['克制', '戏剧', '幽默', '抒情'];
const showChatPanel = ref(false);
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

  .write-workbench__editor {
    padding: 16px;
  }
}
</style>
