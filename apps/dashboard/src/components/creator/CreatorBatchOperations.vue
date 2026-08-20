<template>
  <section class="batch-operations" v-show="wb.creationMode === 'advance'">
    <h2 class="batch-operations__title">批量操作</h2>
    
    <div class="batch-operations__selection">
      <div class="batch-operations__checkbox-row">
        <input
          type="checkbox"
          id="batch-select-all"
          class="batch-operations__checkbox"
          :checked="allSelected"
          @change="toggleSelectAll"
        />
        <label for="batch-select-all" class="batch-operations__checkbox-label">全选</label>
      </div>
      
      <div class="batch-operations__range">
        <span class="batch-operations__range-label">范围选择：</span>
        <input
          type="number"
          v-model.number="rangeStart"
          class="batch-operations__range-input"
          min="1"
          :max="maxChapter"
          placeholder="开始"
        />
        <span class="batch-operations__range-separator">—</span>
        <input
          type="number"
          v-model.number="rangeEnd"
          class="batch-operations__range-input"
          min="1"
          :max="maxChapter"
          placeholder="结束"
        />
        <button
          type="button"
          class="batch-operations__range-btn"
          @click="selectRange"
        >
          选择范围
        </button>
      </div>
      
      <div class="batch-operations__selected-info">
        已选择 {{ selectedChapters.length }} 章
      </div>
    </div>

    <div class="batch-operations__actions">
      <button
        type="button"
        class="batch-operations__action-btn"
        :disabled="selectedChapters.length === 0 || isRunning"
        @click="runBatchWrite"
      >
        <span>✨</span>
        <span>{{ isRunning ? '批量生成中…' : '批量AI续写' }}</span>
      </button>
      <button
        type="button"
        class="batch-operations__action-btn"
        :disabled="selectedChapters.length === 0 || isRunning"
        @click="runBatchPolish"
      >
        <span>💎</span>
        <span>{{ isRunning ? '批量润色中…' : '批量润色' }}</span>
      </button>
    </div>

    <div class="batch-operations__progress" v-if="isRunning">
      <div class="batch-operations__progress-info">
        <span>进度：{{ currentChapterIndex }}/{{ selectedChapters.length }}</span>
        <span class="batch-operations__progress-percent">{{ batchProgress }}%</span>
      </div>
      <div class="batch-operations__progress-bar">
        <div class="batch-operations__progress-fill" :style="{ width: batchProgress + '%' }"></div>
      </div>
    </div>

    <div class="batch-operations__stats" v-if="selectedChapters.length > 0">
      <h3 class="batch-operations__stats-title">选中章节统计</h3>
      <div class="batch-operations__stats-grid">
        <div class="batch-operations__stat-item">
          <span class="batch-operations__stat-value">{{ totalWordCount }}</span>
          <span class="batch-operations__stat-label">总字数</span>
        </div>
        <div class="batch-operations__stat-item">
          <span class="batch-operations__stat-value">{{ completedCount }}</span>
          <span class="batch-operations__stat-label">已完成</span>
        </div>
        <div class="batch-operations__stat-item">
          <span class="batch-operations__stat-value">{{ outlineOnlyCount }}</span>
          <span class="batch-operations__stat-label">仅大纲</span>
        </div>
        <div class="batch-operations__stat-item">
          <span class="batch-operations__stat-value">{{ emptyCount }}</span>
          <span class="batch-operations__stat-label">空章节</span>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue';
import { inject } from 'vue';
import { CREATOR_WRITE_KEY } from './creatorWriteKey.js';
import { logger } from '../../utils/logger.js';

const w = inject(CREATOR_WRITE_KEY);
const wb = w.wb;

const selectedChapters = ref([]);
const rangeStart = ref(null);
const rangeEnd = ref(null);
const isRunning = ref(false);
const currentChapterIndex = ref(0);
const batchProgress = ref(0);

const maxChapter = computed(() => w.overview?.max_chapter || 0);

const allSelected = computed(() => {
  const visible = w.visibleChapters?.map(ch => ch.chapter) || [];
  return visible.length > 0 && visible.every(ch => selectedChapters.value.includes(ch));
});

const chapterStats = computed(() => {
  const chapters = w.overview?.chapters || [];
  const chapterMap = new Map(chapters.map(c => [c.chapter, c]));
  
  let totalWords = 0;
  let completed = 0;
  let outlineOnly = 0;
  let empty = 0;
  
  for (const ch of selectedChapters.value) {
    const chapter = chapterMap.get(ch);
    if (!chapter) {
      empty++;
      continue;
    }
    totalWords += chapter.word_count || 0;
    if (chapter.has_body) {
      completed++;
    } else if (chapter.has_outline) {
      outlineOnly++;
    } else {
      empty++;
    }
  }
  
  return { totalWords, completed, outlineOnly, empty };
});

const totalWordCount = computed(() => chapterStats.value.totalWords);
const completedCount = computed(() => chapterStats.value.completed);
const outlineOnlyCount = computed(() => chapterStats.value.outlineOnly);
const emptyCount = computed(() => chapterStats.value.empty);

function toggleSelectAll(e) {
  const visible = w.visibleChapters?.map(ch => ch.chapter) || [];
  if (e.target.checked) {
    selectedChapters.value = [...visible];
  } else {
    selectedChapters.value = [];
  }
}

function selectRange() {
  if (rangeStart.value == null || rangeEnd.value == null) return;
  const start = Math.min(rangeStart.value, rangeEnd.value);
  const end = Math.max(rangeStart.value, rangeEnd.value);
  selectedChapters.value = [];
  for (let i = start; i <= end; i++) {
    selectedChapters.value.push(i);
  }
}

async function runBatchOperation(operationType) {
  if (selectedChapters.value.length === 0) return;
  isRunning.value = true;
  currentChapterIndex.value = 0;
  batchProgress.value = 0;
  
  const toast = inject('toast', null);
  const actionLabel = operationType === 'write' ? '批量AI续写' : '批量润色';
  const skipCondition = operationType === 'write' 
    ? (chapter) => chapter?.has_body && (chapter?.word_count || 0) > 500
    : (chapter) => !chapter?.has_body;
  
  let successCount = 0;
  let skippedCount = 0;
  
  try {
    if (toast) {
      toast.info(`开始${actionLabel}，共 ${selectedChapters.value.length} 章`);
    }
    
    const chapters = w.overview?.chapters || [];
    const chapterMap = new Map(chapters.map(c => [c.chapter, c]));
    
    for (let i = 0; i < selectedChapters.value.length; i++) {
      if (!isRunning.value) break;
      
      const ch = selectedChapters.value[i];
      currentChapterIndex.value = i + 1;
      batchProgress.value = Math.round(((i + 1) / selectedChapters.value.length) * 100);
      
      const chapter = chapterMap.get(ch);
      if (skipCondition(chapter)) {
        skippedCount++;
        continue;
      }
      
      w.selectChapter(ch);
      await wb.saveDraft?.();
      await wb.startQuickWrite?.(`${actionLabel}：第 ${ch} 章`);
      await new Promise(resolve => setTimeout(resolve, 1000));
      successCount++;
    }
    
    if (toast) {
      const msg = `${actionLabel}完成，成功${successCount}章，跳过${skippedCount}章`;
      toast.success(msg);
    }
  } catch (error) {
    if (toast) {
      toast.error(`${actionLabel}失败`);
    }
    logger.error(`Batch ${operationType} failed:`, error);
  } finally {
    isRunning.value = false;
    currentChapterIndex.value = 0;
    batchProgress.value = 0;
  }
}

async function runBatchWrite() {
  await runBatchOperation('write');
}

async function runBatchPolish() {
  await runBatchOperation('polish');
}
</script>

<style scoped>
.batch-operations {
  padding: 12px;
  background: var(--bg-muted);
  border-radius: var(--radius-md);
}

.batch-operations__title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 12px 0;
}

.batch-operations__selection {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.batch-operations__checkbox-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.batch-operations__checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.batch-operations__checkbox-label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  cursor: pointer;
}

.batch-operations__range {
  display: flex;
  align-items: center;
  gap: 6px;
}

.batch-operations__range-label {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.batch-operations__range-input {
  width: 60px;
  padding: 4px 8px;
  font-size: var(--text-xs);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-xs);
  background: var(--bg-primary);
}

.batch-operations__range-separator {
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
}

.batch-operations__range-btn {
  font-size: var(--text-xs);
  padding: 4px 10px;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-xs);
  background: var(--bg-primary);
  cursor: pointer;
  color: var(--color-text-secondary);
}

.batch-operations__range-btn:hover {
  background: var(--bg-elevated);
}

.batch-operations__selected-info {
  font-size: var(--text-xs);
  color: var(--color-accent);
}

.batch-operations__actions {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.batch-operations__action-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: var(--text-xs);
  padding: 8px 12px;
  border: var(--border-width) solid var(--color-accent-muted);
  border-radius: var(--radius-sm);
  background: var(--color-accent-soft);
  cursor: pointer;
  color: var(--color-accent);
  transition: all 0.2s ease;
}

.batch-operations__action-btn:hover:not(:disabled) {
  background: var(--color-accent);
  color: var(--bg-primary);
}

.batch-operations__action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.batch-operations__progress {
  padding: 8px;
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
  margin-bottom: 12px;
}

.batch-operations__progress-info {
  display: flex;
  justify-content: space-between;
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
  margin-bottom: 6px;
}

.batch-operations__progress-percent {
  color: var(--color-accent);
  font-weight: 500;
}

.batch-operations__progress-bar {
  height: 4px;
  background: var(--bg-muted);
  border-radius: 2px;
  overflow: hidden;
}

.batch-operations__progress-fill {
  height: 100%;
  background: var(--color-accent);
  transition: width 0.3s ease;
}

.batch-operations__stats {
  padding-top: 12px;
  border-top: var(--border-width) solid var(--border-color);
}

.batch-operations__stats-title {
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-text-tertiary);
  margin: 0 0 8px 0;
}

.batch-operations__stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.batch-operations__stat-item {
  text-align: center;
  padding: 8px;
  background: var(--bg-primary);
  border-radius: var(--radius-sm);
}

.batch-operations__stat-value {
  display: block;
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text);
}

.batch-operations__stat-label {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-text-tertiary);
  margin-top: 2px;
}
</style>
