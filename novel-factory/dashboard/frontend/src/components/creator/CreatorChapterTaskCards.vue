<!--
  CreatorChapterTaskCards.vue — 推进/工厂：章节任务卡（节奏编排 P1）
-->
<template>
  <details
    v-if="visible"
    class="chapter-task-cards"
    :open="!collapsedByDefault"
    data-testid="chapter-task-cards"
  >
    <summary class="chapter-task-cards__summary">章节任务（批量生成）</summary>
    <div class="chapter-task-cards__body">
      <p class="meta-line">需要时再展开：生成 · 校验 · 确认</p>
      <ul class="chapter-task-list">
        <li
          v-for="card in cards"
          :key="card.chapter"
          class="chapter-task-card"
          :data-testid="`chapter-task-${card.chapter}`"
          :class="`chapter-task-card--${card.status}`"
        >
          <div class="chapter-task-card__head">
            <strong>ch{{ String(card.chapter).padStart(3, '0') }}</strong>
            <span class="chapter-task-card__status">{{ card.statusLabel }}</span>
          </div>
          <p class="meta-line chapter-task-card__goal">{{ card.goal }}</p>
          <p v-if="card.summary" class="meta-line">{{ card.summary }}</p>
          <div class="chapter-task-card__actions">
            <button
              type="button"
              class="mini-btn"
              :data-testid="`chapter-task-generate-${card.chapter}`"
              @click="$emit('generate', card.chapter)"
            >
              生成
            </button>
            <button
              type="button"
              class="mini-btn"
              :disabled="card.status === 'empty'"
              :data-testid="`chapter-task-confirm-${card.chapter}`"
              @click="$emit('confirm', card.chapter)"
            >
              确认
            </button>
          </div>
        </li>
      </ul>
    </div>
  </details>
</template>

<script setup>
import { computed, inject } from 'vue';
import {
  isChapterTaskCardsVisible,
  isHumanFirstDeskMode,
  isPanelDefaultCollapsed,
} from '../../config/creatorPanelMatrix.js';
import { CREATOR_WRITE_WORKBENCH_MATRIX } from '../../config/creatorPanelMatrix.js';
import { CREATOR_PULSE_KEY } from './creatorPulseKey.js';

defineEmits(['generate', 'confirm']);

const p = inject(CREATOR_PULSE_KEY);

const visible = computed(() =>
  isChapterTaskCardsVisible(p.overview?.creation_mode),
);

const collapsedByDefault = computed(() => {
  const mode = p.overview?.creation_mode;
  if (isHumanFirstDeskMode(mode)) {
    return isPanelDefaultCollapsed(CREATOR_WRITE_WORKBENCH_MATRIX, mode, 'chapterTaskCards');
  }
  return false;
});

const cards = computed(() => {
  const chapters = p.overview?.chapters || [];
  const job = p.batchJob?.value ?? p.batchJob ?? null;
  const jobRunning = job?.status === 'running';
  const jobStart = job?.start_chapter ?? job?.chapter_start;
  const jobEnd = job?.end_chapter ?? job?.chapter_end;
  const jobCurrent = job?.current_chapter ?? job?.chapter_num;

  return chapters
    .filter((ch) => ch.chapter <= 20)
    .map((ch) => {
      let status = 'empty';
      let statusLabel = '未开始';
      if (jobRunning && jobStart != null && jobEnd != null
        && ch.chapter >= jobStart && ch.chapter <= jobEnd) {
        if (jobCurrent === ch.chapter) {
          status = 'generating';
          statusLabel = '生成中';
        } else if (ch.chapter < jobCurrent) {
          status = 'ready';
          statusLabel = '批次已完成';
        } else {
          status = 'queued';
          statusLabel = '排队中';
        }
      } else if (ch.has_body) {
        status = 'ready';
        statusLabel = '已生成';
      } else if (ch.has_outline) {
        status = 'outlined';
        statusLabel = '有大纲';
      }
      return {
        chapter: ch.chapter,
        status,
        statusLabel,
        goal: ch.has_outline ? '按大纲产正文' : '先补大纲或直写',
        summary: ch.has_body ? `${ch.word_count} 字` : (jobRunning ? job?.message : null),
      };
    });
});
</script>

<style scoped>
.chapter-task-cards {
  margin-bottom: var(--space-md);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-elevated);
  padding: var(--space-sm) var(--space-md);
}
.chapter-task-cards__summary {
  cursor: pointer;
  font-weight: 600;
  font-size: var(--text-sm);
  list-style: none;
  user-select: none;
}
.chapter-task-cards__summary::-webkit-details-marker {
  display: none;
}
.chapter-task-cards__body {
  margin-top: var(--space-sm);
}
.chapter-task-list {
  list-style: none;
  margin: var(--space-sm) 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}
.chapter-task-card {
  padding: var(--space-sm);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
}
.chapter-task-card--generating {
  border-color: var(--color-accent);
  background: var(--color-accent-soft);
}
.chapter-task-card--queued {
  opacity: 0.85;
}
.chapter-task-card__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.chapter-task-card__status {
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}
.chapter-task-card__actions {
  display: flex;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}
.meta-line {
  margin: 4px 0 0;
  font-size: var(--text-xs);
  color: var(--color-text-dim);
}
.mini-btn {
  font-size: var(--text-xs);
  padding: 4px 8px;
  cursor: pointer;
}
</style>
