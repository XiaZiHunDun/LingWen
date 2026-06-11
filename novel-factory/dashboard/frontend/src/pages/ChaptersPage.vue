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
        <ul
          v-if="productionLines.length"
          class="production-summary-list"
          data-testid="chapter-production-summary"
        >
          <li v-for="(line, idx) in productionLines" :key="idx">{{ line }}</li>
        </ul>
        <p
          v-else-if="hasIncrementalBackfill"
          class="backfill-line"
          data-testid="chapter-backfill-badge"
        >
          CVG 增量 Backfill：{{ incrementalBackfillLabel }}
        </p>
      </template>
    </section>

    <section
      class="production-history pixel-card"
      data-testid="production-history-panel"
    >
      <h2 class="section-title">最近生产记录 (只读)</h2>
      <p v-if="recordsLoading" class="history-hint">加载记录…</p>
      <p v-else-if="recordsError" class="history-error">{{ recordsError }}</p>
      <p v-else-if="!historyRows.length" class="history-hint" data-testid="production-history-empty">
        暂无 pilot/batch 记录（CLI --save-record 写入 infra/.state/pilot_records/）
      </p>
      <table v-else class="history-table" data-testid="production-history-table">
        <thead>
          <tr>
            <th>章节</th>
            <th>类型</th>
            <th>成本</th>
            <th>Provider</th>
            <th>Memory</th>
            <th>状态</th>
            <th>操作者</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in historyRows" :key="row.key">
            <td>{{ row.chapter }}</td>
            <td>{{ row.type }}</td>
            <td>{{ row.cost }}</td>
            <td>{{ row.provider }}</td>
            <td>{{ row.memory }}</td>
            <td>{{ row.status }}</td>
            <td>{{ row.operator }}</td>
            <td>{{ row.at }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="table-section">
      <ChapterTable
        v-if="chapters.length > 0"
        :chapters="chapters"
        :production-by-chapter="productionByChapter"
        :decision-link-chapters="decisionLinkChapters"
        @decision-link="onChapterDecisionLink"
      />
      <p v-else-if="!loading" class="chapters-empty" data-testid="chapters-empty">
        暂无章节数据
      </p>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import ChapterTable from '../components/ChapterTable.vue';
import { fetchChapters, fetchProductionRecords } from '../api/index.js';
import { useWorkflowSocket } from '../composables/useWorkflowSocket.js';
import { useDashboardNav } from '../composables/useDashboardNav.js';
import {
  formatIncrementalBackfill,
  productionSummaryLines,
  resolveProductionSummary,
} from '../utils/productionSummary.js';
import {
  chapterProductionBadge,
  formatProductionRecordRows,
  indexRecordsByChapter,
} from '../utils/productionRecords.js';
import {
  chapterDecisionLinkEnabled,
  findPendingDecisionForChapter,
} from '../utils/chapterDecisionLink.js';

const rangeOptions = ['1-30', '1-50', '31-60', '61-90'];
const range = ref('1-30');
const chapters = ref([]);
const loading = ref(false);
const error = ref(null);
const productionRecords = ref([]);
const recordsLoading = ref(false);
const recordsError = ref(null);

const { status, pendingDecisions } = useWorkflowSocket();
const { navigateTo } = useDashboardNav();

const workflowActive = computed(() => Boolean(status.value?.is_active));
const paused = computed(() => Boolean(status.value?.paused));

const hasIncrementalBackfill = computed(() => {
  const bf = status.value?.incremental_backfill;
  return bf != null && typeof bf === 'object';
});

const productionLines = computed(() =>
  productionSummaryLines(resolveProductionSummary(status.value)),
);

const incrementalBackfillLabel = computed(() =>
  formatIncrementalBackfill(status.value?.incremental_backfill),
);

const historyRows = computed(() => formatProductionRecordRows(productionRecords.value));

const productionByChapter = computed(() => indexRecordsByChapter(productionRecords.value));

const decisionLinkChapters = computed(() => {
  const map = {};
  for (const ch of chapters.value) {
    const num = ch.chapter;
    if (chapterDecisionLinkEnabled(num, pendingDecisions.value, status.value)) {
      map[num] = true;
    }
  }
  return map;
});

function onChapterDecisionLink(chapterNum) {
  const decision = findPendingDecisionForChapter(
    chapterNum,
    pendingDecisions.value,
    status.value,
  );
  navigateTo('decisions', {
    chapter: chapterNum,
    decisionId: decision?.decision_id ?? null,
  });
}

async function loadProductionRecords() {
  recordsLoading.value = true;
  recordsError.value = null;
  try {
    const resp = await fetchProductionRecords({ limit: 30 });
    productionRecords.value = resp.records || [];
  } catch (err) {
    recordsError.value = err instanceof Error ? err.message : String(err);
    productionRecords.value = [];
  } finally {
    recordsLoading.value = false;
  }
}

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
  loadProductionRecords();
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

.production-summary-list {
  margin: var(--space-xs) 0 0;
  padding-left: 1.2em;
  font-size: 10px;
  font-family: monospace;
  line-height: 1.5;
}

.production-history {
  padding: var(--space-md);
  border: 2px solid var(--border-color);
  background: var(--bg-secondary);
}

.history-hint {
  font-size: 10px;
  font-family: monospace;
  margin: 0;
  opacity: 0.7;
}

.history-error {
  font-size: 10px;
  font-family: monospace;
  margin: 0;
  color: var(--color-danger);
}

.history-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 8px;
  font-family: monospace;
  margin-top: var(--space-xs);
}

.history-table th,
.history-table td {
  padding: 4px 6px;
  border-bottom: 1px solid var(--border-color);
  text-align: left;
}

.chapters-empty {
  font-size: 10px;
  font-family: monospace;
  opacity: 0.7;
}
</style>
