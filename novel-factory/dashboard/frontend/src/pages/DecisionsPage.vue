<!--
  DecisionsPage.vue — 决策列表页面 (Phase 6.2)
  - 顶部 pending tab + all tab
  - 卡片网格展示
  - resolve/defer/cancel 操作
-->
<template>
  <div class="decisions-page">
    <header class="page-header">
      <h1 class="page-title">决策中心</h1>
      <div class="header-actions">
        <span class="count-badge">
          待处理: {{ pending.length }} / 总计: {{ all.length }}
        </span>
        <button class="refresh-btn pixel-border" @click="refresh" :disabled="loading">
          {{ loading ? '加载中…' : '刷新' }}
        </button>
      </div>
    </header>

    <nav class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-btn"
        :class="{ 'tab-btn--active': activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        {{ tab.label }} ({{ tab.count }})
      </button>
    </nav>

    <div v-if="error" class="error-banner pixel-border">
      {{ error }}
    </div>

    <div v-if="loading && !displayList.length" class="loading">
      加载决策中…
    </div>

    <div v-else-if="!displayList.length" class="empty-state pixel-card">
      <p class="pixel-text">🎉 当前没有{{ activeTab === 'pending' ? '待处理' : '' }}决策</p>
      <p class="hint">启动一个工作流后,系统会扫描 DECISION 节点并创建待审核决策</p>
    </div>

    <div v-else class="decision-grid">
      <DecisionCard
        v-for="d in displayList"
        :key="d.decision_id"
        :decision="d"
        @resolve="handleResolve"
        @defer="handleDefer"
        @cancel="handleCancel"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import DecisionCard from '../components/DecisionCard.vue';
import {
  fetchPendingDecisions,
  fetchAllDecisions,
  resolveDecision,
  deferDecision,
  cancelDecision,
} from '../api/index.js';

const loading = ref(false);
const error = ref(null);
const pending = ref([]);
const all = ref([]);
const activeTab = ref('pending');

const displayList = computed(() => {
  if (activeTab.value === 'pending') {
    return pending.value.filter(d => d.status === 'pending');
  }
  return all.value;
});

const tabs = computed(() => [
  { id: 'pending', label: '待处理', count: pending.value.length },
  { id: 'all', label: '全部', count: all.value.length },
]);

async function refresh() {
  loading.value = true;
  error.value = null;
  try {
    const [p, a] = await Promise.all([
      fetchPendingDecisions(),
      fetchAllDecisions(),
    ]);
    pending.value = p;
    all.value = a;
  } catch (e) {
    error.value = e?.message || String(e);
  } finally {
    loading.value = false;
  }
}

async function handleResolve({ decisionId, option }) {
  try {
    await resolveDecision(decisionId, option);
    await refresh();
  } catch (e) {
    error.value = `解决失败: ${e?.message || e}`;
  }
}

async function handleDefer({ decisionId, reason }) {
  try {
    await deferDecision(decisionId, reason);
    await refresh();
  } catch (e) {
    error.value = `推迟失败: ${e?.message || e}`;
  }
}

async function handleCancel({ decisionId, reason }) {
  try {
    await cancelDecision(decisionId, reason);
    await refresh();
  } catch (e) {
    error.value = `取消失败: ${e?.message || e}`;
  }
}

onMounted(refresh);
</script>

<style scoped>
.decisions-page {
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

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.count-badge {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  padding: 6px 10px;
  border: 2px solid var(--border-color);
  background: var(--bg-secondary);
}

.tab-bar {
  display: flex;
  gap: var(--space-xs);
  border-bottom: 2px solid var(--border-color);
  padding-bottom: var(--space-xs);
}

.tab-btn {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  padding: 8px 12px;
  background: transparent;
  border: 2px solid transparent;
  border-bottom: none;
  cursor: pointer;
  color: var(--color-text-dim);
}

.tab-btn--active {
  background: var(--bg-secondary);
  border-color: var(--border-color);
  color: var(--color-text);
}

.error-banner {
  padding: var(--space-sm);
  background: #ffcdd2;
  color: #c62828;
  font-family: monospace;
  font-size: 11px;
}

.loading,
.empty-state {
  text-align: center;
  padding: var(--space-xl);
  color: var(--color-text-dim);
}

.empty-state .pixel-text {
  font-size: 14px;
  margin-bottom: var(--space-sm);
}

.empty-state .hint {
  font-size: 10px;
  color: var(--color-text-dim);
}

.decision-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: var(--space-md);
}
</style>
