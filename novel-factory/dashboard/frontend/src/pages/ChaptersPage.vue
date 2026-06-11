<!--
  ChaptersPage.vue — Phase 9.71 F63: 章节管理 MVP
  - 章节指标表格 (ChapterTable + /api/chapters?range=)
  - 正文生产状态 (WS workflow status + incremental_backfill from F60)
-->
<template>
  <div class="chapters-page">
    <header class="page-header">
      <h1 class="page-title" data-testid="page-title">章节管理</h1>
      <div class="header-actions">
        <label class="range-label">
          范围
          <select
            v-model="range"
            class="range-select pixel-border"
            data-testid="chapter-range-select"
          >
            <option v-for="opt in rangeOptions" :key="opt" :value="opt">
              {{ opt }}
            </option>
          </select>
        </label>
        <button
          class="refresh-btn pixel-border"
          data-testid="refresh-btn"
          :disabled="loading"
          @click="loadChapters"
        >
          {{ loading ? '加载中…' : '刷新' }}
        </button>
      </div>
    </header>

    <div v-if="error" class="error-banner pixel-border" data-testid="error-banner">
      {{ error }}
    </div>

    <section
      class="production-section pixel-card"
      data-testid="chapter-production-status"
    >
      <h2 class="section-title">正文生产状态</h2>
      <p v-if="!workflowActive" class="production-idle">当前无活跃工作流</p>
      <template v-else>
        <p class="production-meta">
          <span>{{ status.workflow_name || '未知工作流' }}</span>
          <span class="status-pill" :class="paused ? 'status-paused' : 'status-running'">
            {{ paused ? '已暂停' : '运行中' }}
          </span>
        </p>
        <p
          v-if="hasIncrementalBackfill"
          class="backfill-line"
          data-testid="chapter-backfill-badge"
        >
          CVG 增量 Backfill：{{ incrementalBackfillLabel }}
        </p>
      </template>
    </section>

    <section class="table-section">
      <ChapterTable v-if="chapters.length > 0" :chapters="chapters" />
      <p v-else-if="!loading" class="chapters-empty" data-testid="chapters-empty">
        暂无章节数据
      </p>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import ChapterTable from '../components/ChapterTable.vue';
import { fetchChapters } from '../api/index.js';
import { useWorkflowSocket } from '../composables/useWorkflowSocket.js';

const rangeOptions = ['1-30', '1-50', '31-60', '61-90'];
const range = ref('1-30');
const chapters = ref([]);
const loading = ref(false);
const error = ref(null);

const { status } = useWorkflowSocket();

const workflowActive = computed(() => Boolean(status.value?.is_active));
const paused = computed(() => Boolean(status.value?.paused));

const hasIncrementalBackfill = computed(() => {
  const bf = status.value?.incremental_backfill;
  return bf != null && typeof bf === 'object';
});

const incrementalBackfillLabel = computed(() => {
  const bf = status.value?.incremental_backfill;
  if (!bf) return '';
  const parts = [];
  if (bf.nodes_written != null) parts.push(`写入 ${bf.nodes_written} 节点`);
  if (bf.nodes_skipped != null) parts.push(`跳过 ${bf.nodes_skipped}`);
  if (bf.total_count != null) parts.push(`抽取 ${bf.total_count}`);
  if (bf.elapsed_s != null) parts.push(`${Number(bf.elapsed_s).toFixed(2)}s`);
  return parts.length ? parts.join(' · ') : JSON.stringify(bf);
});

async function loadChapters() {
  loading.value = true;
  error.value = null;
  try {
    const resp = await fetchChapters(range.value);
    chapters.value = resp.chapters || [];
  } catch (err) {
    error.value = err instanceof Error ? err.message : String(err);
    chapters.value = [];
  } finally {
    loading.value = false;
  }
}

watch(range, () => {
  loadChapters();
});

onMounted(() => {
  loadChapters();
});
</script>

<style scoped>
.chapters-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-md);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.page-title {
  font-size: 12px;
  font-weight: bold;
  color: var(--color-text);
  font-family: 'Press Start 2P', monospace;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.range-label {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.range-select {
  font-size: 8px;
  font-family: monospace;
  padding: 4px 8px;
  background: var(--bg-secondary);
}

.refresh-btn {
  background-color: var(--bg-secondary);
  color: var(--color-text);
  padding: var(--space-sm) var(--space-md);
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  cursor: pointer;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-banner {
  background-color: var(--color-danger);
  color: white;
  padding: var(--space-md);
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
}

.production-section {
  padding: var(--space-md);
  border: 2px solid var(--border-color);
  background: var(--bg-secondary);
}

.section-title {
  font-size: 10px;
  font-family: 'Press Start 2P', monospace;
  margin: 0 0 var(--space-sm) 0;
  color: var(--color-accent);
}

.production-idle {
  font-size: 10px;
  font-family: monospace;
  margin: 0;
  opacity: 0.7;
}

.production-meta {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 10px;
  font-family: monospace;
  margin: 0 0 var(--space-xs) 0;
}

.status-pill {
  font-size: 8px;
  padding: 2px 6px;
  border: 1px solid var(--border-color);
  font-family: 'Press Start 2P', monospace;
}

.status-paused {
  background: #fff59d;
}

.status-running {
  background: #c8e6c9;
}

.backfill-line {
  font-size: 10px;
  font-family: monospace;
  margin: var(--space-xs) 0 0;
}

.chapters-empty {
  font-size: 10px;
  font-family: monospace;
  opacity: 0.7;
}
</style>
