<template>
  <header class="writer-desk__header">
    <div class="writer-desk__header-left">
      <button
        type="button"
        class="writer-desk__sidebar-toggle sidebar-toggle"
        data-testid="sidebar-toggle"
        @click="wb.leftPanelCollapsed = !wb.leftPanelCollapsed"
      >
        {{ wb.leftPanelCollapsed ? '☰' : '✕' }}
      </button>
      <span class="writer-desk__title">{{ w.overview?.name || '写作中' }}</span>
    </div>
    <div class="writer-desk__header-center">
      <span class="writer-desk__chapter-indicator">第 {{ w.selectedChapter }} 章</span>
      <div class="writer-desk__tool-group">
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
      <button
        type="button"
        class="writer-desk__chat-toggle"
        :class="{ 'writer-desk__chat-toggle--active': showChatPanel }"
        @click="$emit('toggle-chat')"
      >
        <span>💬</span>
        <span>{{ showChatPanel ? '收起' : '对话' }}</span>
      </button>
    </div>
    <div class="writer-desk__header-right">
      <CreatorModeSwitch
        :current-mode="wb.creationMode || 'companion'"
        @update:current-mode="$emit('mode-change', $event)"
      />
    </div>
  </header>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';
import CreatorModeSwitch from './CreatorModeSwitch.vue';

defineProps({
  showChatPanel: {
    type: Boolean,
    default: false,
  },
});

defineEmits(['toggle-chat', 'mode-change']);

const w = inject(CREATOR_WRITE_KEY);
const wb = w.wb;
</script>