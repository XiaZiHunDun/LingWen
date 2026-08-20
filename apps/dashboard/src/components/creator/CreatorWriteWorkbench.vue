<template>
  <div
    class="writer-desk"
    :class="{
      'writer-desk--sidebar-collapsed': wb.leftPanelCollapsed,
      'writer-desk--chat-open': showChatPanel,
    }"
    data-testid="writer-desk"
  >
    <CreatorWriteHeader
      :show-chat-panel="showChatPanel"
      @toggle-chat="showChatPanel = !showChatPanel"
      @mode-change="handleModeChange"
    />

    <div class="writer-desk__body">
      <CreatorWriteSidebar>
        <template #chapters>
          <slot name="chapters" />
        </template>
      </CreatorWriteSidebar>

      <main class="writer-desk__editor">
        <div class="writer-desk__editor-inner">
          <slot />
          <div v-if="!String(w.chapterBodyDraft ?? '').trim()" class="writer-desk__empty-state" :class="`writer-desk__empty-state--${wb.creationMode}`">
            <div class="writer-desk__empty-state-icon">{{ emptyStateIcon }}</div>
            <h3 class="writer-desk__empty-state-title">{{ emptyStateTitle }}</h3>
            <p class="writer-desk__empty-state-desc">{{ emptyStateDesc }}</p>
            <div class="writer-desk__empty-state-actions">
              <button type="button" class="writer-desk__empty-state-btn" @click="wb.startQuickWrite?.()">
                {{ emptyStateBtnText }}
              </button>
            </div>
          </div>
        </div>
      </main>

      <CreatorWriteChat
        :show-chat-panel="showChatPanel"
        @close="showChatPanel = false"
      />
    </div>

    <CreatorWriteFooter
      @open-outline="openOutline"
      @open-stats="openStats"
    />
  </div>
</template>

<script setup>
import { inject, ref, computed } from 'vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';
import CreatorWriteHeader from './CreatorWriteHeader.vue';
import CreatorWriteSidebar from './CreatorWriteSidebar.vue';
import CreatorWriteChat from './CreatorWriteChat.vue';
import CreatorWriteFooter from './CreatorWriteFooter.vue';
import { logger } from '../../utils/logger.js';
import '../../assets/creator-write-workbench.css';

/**
 * @typedef {Object} CreatorWriteInjected
 * @property {import('vue').Ref<import('vue').UnwrapRefSimple<object>>} wb
 * @property {() => void} openOutline
 * @property {() => void} openStats
 * @property {(mode: string) => void} handleModeChange
 */

/** @type {CreatorWriteInjected} */
const w = inject(CREATOR_WRITE_KEY);
const wb = w.wb;

const showChatPanel = ref(false);

const modeColors = {
  companion: '#3b82f6',
  advance: '#7c3aed',
  studio: '#f97316',
};

const modeColor = computed(() => {
  return modeColors[wb.creationMode] || '#3b82f6';
});

const emptyStateConfig = computed(() => {
  const configs = {
    companion: {
      icon: '🤝',
      title: '准备好开始写作了吗？',
      desc: 'AI 将陪伴你完成每一章。输入本章意图，让我们开始吧！',
      btnText: '开始写作',
    },
    advance: {
      icon: '🚀',
      title: '按卷纲推进',
      desc: '选择章节，输入意图，系统将辅助你高效完成本章内容。',
      btnText: '推进章节',
    },
    studio: {
      icon: '🏭',
      title: '工厂模式就绪',
      desc: '设置产线，配置阶段，让系统自动化批量生产内容。',
      btnText: '启动产线',
    },
  };
  return configs[wb.creationMode] || configs.companion;
});

const emptyStateIcon = computed(() => emptyStateConfig.value.icon);
const emptyStateTitle = computed(() => emptyStateConfig.value.title);
const emptyStateDesc = computed(() => emptyStateConfig.value.desc);
const emptyStateBtnText = computed(() => emptyStateConfig.value.btnText);

function openOutline() {
  w.openOutline();
}

function openStats() {
  w.openStats();
}

async function handleModeChange(newMode) {
  const toast = inject('toast', null);
  try {
    await wb.updateCreationMode(newMode);
    if (toast) {
      toast.success(`已切换到${newMode === 'companion' ? '陪伴' : newMode === 'advance' ? '推进' : '工厂'}模式`);
    }
  } catch (error) {
    if (toast) {
      toast.error('切换模式失败，请重试');
    }
    logger.error('Mode change failed:', error);
  }
}
</script>

<style scoped>
.writer-desk {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-primary);
}

.writer-desk--sidebar-collapsed .writer-desk__sidebar {
  display: none;
}

.writer-desk--chat-open .writer-desk__editor {
  right: 320px;
}

.writer-desk__body {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

.writer-desk__editor {
  flex: 1;
  overflow: auto;
  position: relative;
  background: var(--bg-primary);
}

.writer-desk__editor-inner {
  min-height: 100%;
  position: relative;
}
</style>
