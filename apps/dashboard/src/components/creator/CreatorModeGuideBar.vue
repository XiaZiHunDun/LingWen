<!--
  CreatorModeGuideBar.vue — 推进模式引导条（REQ-001 切片 D，只读轻 UI）

  在写栏头部下方显示一条随当前模式变化的引导条，说明该模式的目的与建议下一步。
  与空态卡互补：正文存在时也持续提供上下文引导（推进模式联动侧栏『批改节奏带』）。
  可关闭，关闭状态按模式本地记忆；切换模式会重新展示该模式的引导。
-->
<template>
  <div
    v-if="visible"
    class="creator-mode-guide-bar"
    :class="`creator-mode-guide-bar--${mode}`"
    data-testid="creator-mode-guide-bar"
  >
    <span class="creator-mode-guide-bar__icon">{{ guide.icon }}</span>
    <span class="creator-mode-guide-bar__name">{{ guide.name }}</span>
    <span class="creator-mode-guide-bar__text">{{ guide.text }}</span>
    <button
      type="button"
      class="creator-mode-guide-bar__dismiss creator-mode-guide-dismiss"
      data-testid="creator-mode-guide-dismiss"
      aria-label="收起引导"
      @click="dismiss"
    >
      ×
    </button>
  </div>
</template>

<script setup>
import { inject, ref, computed, watch } from 'vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';

const STORAGE_KEY = 'creator-mode-guide-dismissed';

const GUIDES = {
  companion: {
    icon: '🤝',
    name: '陪伴模式',
    text: 'AI 陪你写作、你来定稿。先输入本章意图，其余交给陪伴。',
  },
  advance: {
    icon: '🚀',
    name: '推进模式',
    text: '按卷纲推进。配合侧栏『批改节奏带』查看批次完成情况。',
  },
  studio: {
    icon: '🏭',
    name: '工厂模式',
    text: '调度产线、批量生产章节。',
  },
};

const w = inject(CREATOR_WRITE_KEY);
const wb = w.wb;

const mode = computed(() => {
  const value = wb.creationMode || 'companion';
  return GUIDES[value] ? value : 'companion';
});

const guide = computed(() => GUIDES[mode.value]);

const dismissedMode = ref(readDismiss());

function readDismiss() {
  try {
    return window.localStorage.getItem(STORAGE_KEY) || '';
  } catch {
    return '';
  }
}

const visible = computed(() => dismissedMode.value !== mode.value);

watch(mode, () => {
  // 切换模式后，仅当新模式已被关闭时才继续隐藏；否则重新展示。
  dismissedMode.value = readDismiss();
});

function dismiss() {
  try {
    window.localStorage.setItem(STORAGE_KEY, mode.value);
  } catch {
    /* localStorage 不可用时仅本次会话隐藏 */
  }
  dismissedMode.value = mode.value;
}
</script>

<style scoped>
.creator-mode-guide-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 14px;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  border-bottom: var(--border-width) solid transparent;
}

.creator-mode-guide-bar--companion {
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.3);
}

.creator-mode-guide-bar--advance {
  background: rgba(124, 58, 237, 0.08);
  border-color: rgba(124, 58, 237, 0.3);
}

.creator-mode-guide-bar--studio {
  background: rgba(249, 115, 22, 0.08);
  border-color: rgba(249, 115, 22, 0.3);
}

.creator-mode-guide-bar__icon {
  font-size: 14px;
}

.creator-mode-guide-bar__name {
  font-weight: 600;
  color: var(--color-text);
  white-space: nowrap;
}

.creator-mode-guide-bar__text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.creator-mode-guide-bar__dismiss {
  flex: none;
  width: 18px;
  height: 18px;
  line-height: 1;
  font-size: 14px;
  border: none;
  border-radius: var(--radius-xs);
  background: transparent;
  color: var(--color-text-tertiary);
  cursor: pointer;
}

.creator-mode-guide-bar__dismiss:hover {
  background: var(--bg-primary);
  color: var(--color-text);
}
</style>
