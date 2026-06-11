<!--
  SettingsPage.vue — Phase 9.78 F68: 系统设置 MVP (read-only)
  - Budget 只读面板 (GET /api/budgets + WS snapshot)
  - 生产环境变量说明
-->
<template>
  <div class="settings-page">
    <header class="page-header">
      <h1 class="page-title" data-testid="page-title">系统设置</h1>
      <button
        class="refresh-btn pixel-border"
        data-testid="refresh-btn"
        :disabled="loading"
        @click="loadBudgets"
      >
        {{ loading ? '加载中…' : '刷新预算' }}
      </button>
    </header>

    <div v-if="error" class="error-banner pixel-border" data-testid="error-banner">
      {{ error }}
    </div>

    <section class="settings-section pixel-card" data-testid="budget-panel">
      <h2 class="section-title">Token 预算 (只读)</h2>
      <p v-if="!windowRows.length && !tierRows.length" class="empty-hint">
        未配置预算阈值（可在 API 或 workflow run 时设置 per-run budget）
      </p>
      <table v-if="windowRows.length" class="settings-table" data-testid="window-budget-table">
        <thead>
          <tr>
            <th>窗口</th>
            <th>预算 (USD)</th>
            <th>已用 (USD)</th>
            <th>占比</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in windowRows" :key="row.key">
            <td>{{ row.label }}</td>
            <td>{{ row.budget }}</td>
            <td>{{ row.used }}</td>
            <td>{{ row.pct }}</td>
            <td :class="`status-${row.status}`">{{ row.status }}</td>
          </tr>
        </tbody>
      </table>
      <h3 v-if="tierRows.length" class="subsection-title">按模型 Tier</h3>
      <table v-if="tierRows.length" class="settings-table" data-testid="tier-budget-table">
        <thead>
          <tr>
            <th>Tier</th>
            <th>预算 (USD)</th>
            <th>已用 (USD)</th>
            <th>占比</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in tierRows" :key="row.tier">
            <td>{{ row.label }}</td>
            <td>{{ row.budget }}</td>
            <td>{{ row.used }}</td>
            <td>{{ row.pct }}</td>
            <td :class="`status-${row.status}`">{{ row.status }}</td>
          </tr>
        </tbody>
      </table>
      <p class="readonly-note">只读面板 — 修改预算请使用 API `PUT /api/budgets/{scope}`</p>
    </section>

    <section class="settings-section pixel-card" data-testid="env-panel">
      <h2 class="section-title">生产环境变量</h2>
      <table class="settings-table" data-testid="production-env-table">
        <thead>
          <tr>
            <th>变量</th>
            <th>取值</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in productionEnvVars" :key="item.name">
            <td><code>{{ item.name }}</code></td>
            <td>{{ item.values }}</td>
            <td>{{ item.description }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="settings-section pixel-card" data-testid="api-key-env-panel">
      <h2 class="section-title">LLM Provider 密钥</h2>
      <table class="settings-table" data-testid="api-key-env-table">
        <thead>
          <tr>
            <th>变量</th>
            <th>格式</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in apiKeyEnvVars" :key="item.name">
            <td><code>{{ item.name }}</code></td>
            <td>{{ item.values }}</td>
            <td>{{ item.description }}</td>
          </tr>
        </tbody>
      </table>
      <p class="readonly-note">Dashboard 不读取或展示密钥值</p>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { fetchBudgets, fetchBudgetsByTier } from '../api/index.js';
import { useWorkflowSocket } from '../composables/useWorkflowSocket.js';
import { PRODUCTION_ENV_VARS, API_KEY_ENV_VARS } from '../utils/settingsEnv.js';
import {
  formatWindowBudgetRows,
  formatTierBudgetRows,
  formatWsBudgetFallback,
} from '../utils/settingsBudget.js';

const { status } = useWorkflowSocket();

const loading = ref(false);
const error = ref(null);
const budgetWindows = ref(null);
const tierLimits = ref(null);

const productionEnvVars = PRODUCTION_ENV_VARS;
const apiKeyEnvVars = API_KEY_ENV_VARS;

const windowRows = computed(() => {
  const fromApi = formatWindowBudgetRows(budgetWindows.value || {});
  if (fromApi.length) return fromApi;
  return formatWsBudgetFallback(status.value);
});

const tierRows = computed(() =>
  formatTierBudgetRows(tierLimits.value, status.value?.budget_by_tier),
);

async function loadBudgets() {
  loading.value = true;
  error.value = null;
  try {
    const [windows, tiers] = await Promise.all([
      fetchBudgets(),
      fetchBudgetsByTier(),
    ]);
    budgetWindows.value = windows;
    tierLimits.value = tiers;
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadBudgets();
});
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-md);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 12px;
  font-weight: bold;
  font-family: 'Press Start 2P', monospace;
}

.refresh-btn {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-secondary);
  cursor: pointer;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-banner {
  background: var(--color-danger);
  color: white;
  padding: var(--space-md);
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
}

.settings-section {
  padding: var(--space-md);
  border: 2px solid var(--border-color);
  background: var(--bg-secondary);
}

.section-title {
  font-size: 10px;
  font-family: 'Press Start 2P', monospace;
  color: var(--color-accent);
  margin: 0 0 var(--space-sm);
}

.subsection-title {
  font-size: 9px;
  font-family: 'Press Start 2P', monospace;
  margin: var(--space-md) 0 var(--space-xs);
}

.settings-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 10px;
  font-family: monospace;
}

.settings-table th,
.settings-table td {
  border: 1px solid var(--border-color);
  padding: 6px 8px;
  text-align: left;
}

.settings-table th {
  background: var(--bg-primary);
  font-family: 'Press Start 2P', monospace;
  font-size: 8px;
}

.status-exceeded {
  color: var(--color-danger);
  font-weight: bold;
}

.status-ok {
  color: var(--color-success);
}

.empty-hint,
.readonly-note {
  font-size: 10px;
  font-family: monospace;
  opacity: 0.8;
  margin: var(--space-xs) 0 0;
}

code {
  font-size: 9px;
}
</style>
