<!--
  AskPageTabs — 聊聊顶栏：问答 / 速记（与「当前作品」同一行）
-->
<template>
  <div class="ask-page-tabs" role="tablist" aria-label="聊聊分区" data-testid="ask-page-tabs">
    <button
      type="button"
      role="tab"
      class="ask-page-tabs__tab"
      :class="{ 'ask-page-tabs__tab--active': tab === 'chat' }"
      :aria-selected="tab === 'chat'"
      data-testid="ask-tab-chat"
      @click="tab = 'chat'"
    >
      问答
    </button>
    <button
      type="button"
      role="tab"
      class="ask-page-tabs__tab"
      :class="{ 'ask-page-tabs__tab--active': tab === 'note' }"
      :aria-selected="tab === 'note'"
      data-testid="ask-tab-note"
      @click="tab = 'note'"
    >
      速记
    </button>
  </div>
</template>

<script setup>
import { useAskPageTab } from '../composables/useAskAssistant.js';

const { tab } = useAskPageTab();
</script>

<style scoped>
.ask-page-tabs {
  display: inline-flex;
  gap: 0;
  padding: 3px;
  background: var(--bg-elevated);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}
.ask-page-tabs__tab {
  font-size: var(--text-sm);
  padding: 6px 16px;
  cursor: pointer;
  border: none;
  border-radius: calc(var(--radius-md) - 3px);
  background: transparent;
  color: var(--color-text-dim);
  font-weight: 500;
  transition: background-color 0.15s ease, color 0.15s ease;
}
.ask-page-tabs__tab--active {
  background: var(--color-accent);
  color: #fff;
  font-weight: 600;
}
</style>
