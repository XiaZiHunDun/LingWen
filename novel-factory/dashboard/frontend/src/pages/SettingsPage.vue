<!--
  SettingsPage.vue — Phase 9.78 F68 read-only + Phase 9.86 F78 budget write
  - Budget 面板 (GET + PUT day/week/tier)
  - 生产环境变量说明 (只读)
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
    <div v-if="saveMessage" class="success-banner pixel-border" data-testid="save-banner">
      {{ saveMessage }}
    </div>

    <section class="settings-section pixel-card" data-testid="budget-panel">
      <h2 class="section-title">Token 预算</h2>
      <p v-if="!windowRows.length && !tierRows.length" class="empty-hint">
        未配置预算阈值（per-run 仍随 workflow run 传参）
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
      <p class="readonly-note">per-run 预算在启动 workflow 时设置，此处不可编辑</p>
    </section>

    <section class="settings-section pixel-card" data-testid="budget-edit-panel">
      <h2 class="section-title">修改预算</h2>
      <form class="budget-edit-form" @submit.prevent="submitBudgetEdit">
        <label class="field-label" for="budget-target">目标</label>
        <select
          id="budget-target"
          v-model="editTargetId"
          class="budget-select pixel-border"
          data-testid="budget-target-select"
          @change="syncEditInputFromLoaded"
        >
          <option v-for="t in editTargets" :key="t.id" :value="t.id">
            {{ t.label }}
          </option>
        </select>
        <label class="field-label" for="budget-usd">预算 (USD)</label>
        <input
          id="budget-usd"
          v-model="editUsd"
          type="number"
          min="0"
          max="10000"
          step="0.01"
          class="budget-input pixel-border"
          data-testid="budget-usd-input"
          placeholder="例如 0.50"
        />
        <button
          type="submit"
          class="save-btn pixel-border"
          data-testid="budget-save-btn"
          :disabled="saving"
        >
          {{ saving ? '保存中…' : '保存' }}
        </button>
      </form>
      <p v-if="editError" class="edit-error" data-testid="budget-edit-error">{{ editError }}</p>
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
import { computed, onMounted, ref, watch } from 'vue';
import {
  fetchBudgets,
  fetchBudgetsByTier,
  setBudget,
  setBudgetByTier,
} from '../api/index.js';
import { useWorkflowSocket } from '../composables/useWorkflowSocket.js';
import { PRODUCTION_ENV_VARS, API_KEY_ENV_VARS } from '../utils/settingsEnv.js';
import {
  formatWindowBudgetRows,
  formatTierBudgetRows,
  formatWsBudgetFallback,
} from '../utils/settingsBudget.js';
import {
  BUDGET_EDIT_TARGETS,
  currentBudgetUsdForTarget,
  parseBudgetUsdInput,
} from '../utils/settingsBudgetEdit.js';

const { status } = useWorkflowSocket();

const loading = ref(false);
const saving = ref(false);
const error = ref(null);
const saveMessage = ref(null);
const editError = ref(null);
const budgetWindows = ref(null);
const tierLimits = ref(null);
const editTargetId = ref('day');
const editUsd = ref('');

const productionEnvVars = PRODUCTION_ENV_VARS;
const apiKeyEnvVars = API_KEY_ENV_VARS;
const editTargets = BUDGET_EDIT_TARGETS;

const windowRows = computed(() => {
  const fromApi = formatWindowBudgetRows(budgetWindows.value || {});
  if (fromApi.length) return fromApi;
  return formatWsBudgetFallback(status.value);
});

const tierRows = computed(() =>
  formatTierBudgetRows(tierLimits.value, status.value?.budget_by_tier),
);

const selectedTarget = computed(() =>
  editTargets.find((t) => t.id === editTargetId.value) || editTargets[0],
);

function syncEditInputFromLoaded() {
  const target = selectedTarget.value;
  if (!target) return;
  const current = currentBudgetUsdForTarget(
    target,
    budgetWindows.value,
    tierLimits.value,
  );
  editUsd.value = current === '' ? '' : String(current);
}

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
    syncEditInputFromLoaded();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
}

async function submitBudgetEdit() {
  editError.value = null;
  saveMessage.value = null;
  const parsed = parseBudgetUsdInput(editUsd.value);
  if (!parsed.ok) {
    editError.value = parsed.message;
    return;
  }
  const target = selectedTarget.value;
  saving.value = true;
  try {
    if (target.kind === 'window') {
      await setBudget(target.apiScope, parsed.usd);
    } else {
      await setBudgetByTier(target.apiScope, parsed.usd);
    }
    saveMessage.value = `已保存 ${target.label}: $${parsed.usd.toFixed(2)}`;
    await loadBudgets();
  } catch (e) {
    editError.value = e instanceof Error ? e.message : String(e);
  } finally {
    saving.value = false;
  }
}

watch(budgetWindows, () => syncEditInputFromLoaded());
watch(tierLimits, () => syncEditInputFromLoaded());

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

.refresh-btn,
.save-btn {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-secondary);
  cursor: pointer;
}

.refresh-btn:disabled,
.save-btn:disabled {
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

.success-banner {
  background: var(--color-success);
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

.budget-edit-form {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  align-items: flex-end;
  margin-top: var(--space-sm);
}

.field-label {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  width: 100%;
}

.budget-select,
.budget-input {
  font-size: 10px;
  font-family: monospace;
  padding: 6px 8px;
  background: var(--bg-primary);
  min-width: 160px;
}

.edit-error {
  font-size: 10px;
  font-family: monospace;
  color: var(--color-danger);
  margin: var(--space-xs) 0 0;
}

code {
  font-size: 9px;
}
</style>
