<!--
  SettingsPage.vue — 设置：基础（运行状态 + 界面）+ 高级（预算 / 环境，伴侣模式只读）
-->
<template>
  <div class="settings-page l1-page" data-testid="settings-page">
    <div class="settings-page__body l1-page__body l1-panel-enter">
      <div class="l1-lead-row">
        <PageLeadBar
          page-id="settings"
          inline
          text="运行状态与界面偏好；预算与环境在「高级」里"
        />
        <button
          v-if="!isCompanionShell"
          type="button"
          class="l1-pill"
          data-testid="refresh-btn"
          :disabled="loading"
          @click="loadBudgets"
        >
          {{ loading ? '加载中…' : '刷新预算' }}
        </button>
      </div>

    <div v-if="displayError" class="error-banner" data-testid="error-banner">
      {{ displayError }}
    </div>
    <div v-if="saveMessage" class="success-banner" data-testid="save-banner">
      {{ saveMessage }}
    </div>

    <section class="settings-group" data-testid="settings-basic-panel">
      <h2 class="group-title">基础</h2>

      <div class="settings-block" data-testid="system-status-panel">
        <h3 class="section-title">运行状态</h3>
        <p class="empty-hint">接口与实时同步情况；成本与预算告警也会显示在这里。</p>
        <SidebarSystemStatusBody
          :status="workflowStatus"
          :api-offline="apiOffline"
          :api-checking="apiChecking"
          :ws-connected="wsConnected"
        />
        <SidebarCostBanner :status="workflowStatus" />
      </div>

      <div class="settings-block settings-block--divider" data-testid="display-settings-panel">
        <h3 class="section-title">界面</h3>
        <p class="empty-hint">调整全站字号，不影响正文排版宽度。</p>
        <TextScaleToggle />
      </div>
    </section>

    <details
      class="settings-advanced"
      data-testid="settings-advanced-panel"
      :open="!isCompanionShell"
      @toggle="onAdvancedToggle"
    >
      <summary class="settings-advanced__summary">高级</summary>
      <div class="settings-advanced__body">
        <p v-if="isCompanionShell" class="empty-hint" data-testid="settings-advanced-companion-hint">
          伴侣模式可查看预算用量；修改预算与环境配置请切换到进阶模式。
        </p>
        <button
          v-if="isCompanionShell"
          type="button"
          class="l1-pill settings-advanced__refresh"
          data-testid="settings-advanced-refresh-btn"
          :disabled="loading"
          @click="loadBudgets"
        >
          {{ loading ? '加载中…' : '刷新预算' }}
        </button>

        <section class="settings-block" data-testid="budget-panel">
          <h3 class="section-title">Token 预算</h3>
          <p v-if="!windowRows.length && !tierRows.length" class="empty-hint">
            {{ loading ? '加载预算中…' : '未配置预算阈值（per-run 仍随 workflow run 传参）' }}
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
          <h4 v-if="tierRows.length" class="subsection-title">按模型 Tier</h4>
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

        <template v-if="!isCompanionShell">
          <section class="settings-block settings-block--divider" data-testid="budget-edit-panel">
            <h3 class="section-title">修改预算</h3>
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
                class="l1-pill l1-pill--primary"
                data-testid="budget-save-btn"
                :disabled="saving"
              >
                {{ saving ? '保存中…' : '保存' }}
              </button>
            </form>
            <p v-if="editError" class="edit-error" data-testid="budget-edit-error">{{ editError }}</p>
          </section>

          <section class="settings-block settings-block--divider" data-testid="env-panel">
            <h3 class="section-title">生产环境变量</h3>
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

          <section class="settings-block settings-block--divider" data-testid="api-key-env-panel">
            <h3 class="section-title">LLM Provider 密钥</h3>
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
        </template>
      </div>
    </details>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, nextTick, onMounted, ref, watch } from 'vue';
import PageLeadBar from '../components/PageLeadBar.vue';
import TextScaleToggle from '../components/TextScaleToggle.vue';
import SidebarSystemStatusBody from '../components/SidebarSystemStatusBody.vue';
import SidebarCostBanner from '../components/SidebarCostBanner.vue';
import { resolveNavCreationMode } from '../config/dashboardNavByMode.js';
import { apiConnectivity } from '../api/connectivity.js';
import { useStudioProject } from '../composables/useStudioProject.js';
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
import { useFilteredPageError } from '../composables/useFilteredPageError.js';

const { status, connected: wsConnected } = useWorkflowSocket();
const studio = useStudioProject();
const injectedCreationMode = inject('creationMode', null);

const workflowStatus = computed(() => status.value ?? {});
const apiOffline = computed(() => apiConnectivity.value.offline);
const apiChecking = computed(() => apiConnectivity.value.checking);
const resolvedCreationMode = computed(
  () => injectedCreationMode?.value
    ?? studio.summary.value?.creation_mode
    ?? null,
);
const isCompanionShell = computed(
  () => resolveNavCreationMode(resolvedCreationMode.value) === 'companion',
);

const loading = ref(false);
const saving = ref(false);
const error = ref(null);
const displayError = useFilteredPageError(error);
const saveMessage = ref(null);
const editError = ref(null);
const budgetWindows = ref(null);
const tierLimits = ref(null);
const editTargetId = ref('day');
const editUsd = ref('');
const advancedBudgetLoaded = ref(false);

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
    advancedBudgetLoaded.value = true;
    syncEditInputFromLoaded();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  } finally {
    loading.value = false;
  }
}

async function onAdvancedToggle(event) {
  if (!isCompanionShell.value) return;
  await nextTick();
  const panel = event.target;
  if (!panel?.open || advancedBudgetLoaded.value) return;
  await loadBudgets();
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
  if (!isCompanionShell.value) {
    loadBudgets();
  }
});
</script>

<style scoped>
.settings-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  width: 100%;
  max-width: none;
  padding: 0;
}

.settings-page__body {
  /* 见 style.css .l1-page__body */
}

.error-banner {
  background: var(--color-danger);
  color: white;
  padding: var(--space-md);
  font-size: var(--text-sm);
  font-family: var(--font-ui);
}

.success-banner {
  background: var(--color-success);
  color: white;
  padding: var(--space-md);
  font-size: var(--text-sm);
  font-family: var(--font-ui);
}

.settings-group,
.settings-advanced {
  padding: var(--space-md);
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-muted);
}

.group-title {
  font-size: var(--text-md);
  font-family: var(--font-ui);
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 var(--space-md);
}

.settings-advanced {
  overflow: hidden;
}

.settings-advanced__summary {
  cursor: pointer;
  list-style: none;
  font-size: var(--text-md);
  font-family: var(--font-ui);
  font-weight: 700;
  color: var(--color-text);
  user-select: none;
}

.settings-advanced__summary::-webkit-details-marker {
  display: none;
}

.settings-advanced__summary::before {
  content: '▸';
  display: inline-block;
  margin-right: 8px;
  color: var(--color-text-dim);
  transition: transform 0.15s ease;
}

.settings-advanced[open] .settings-advanced__summary::before {
  transform: rotate(90deg);
}

.settings-advanced__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: var(--border-width) solid var(--border-color);
}

.settings-advanced__refresh {
  align-self: flex-start;
}

.settings-block--divider {
  padding-top: var(--space-md);
  border-top: var(--border-width) solid var(--border-color);
}

.section-title {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  font-weight: 600;
  color: var(--color-accent);
  margin: 0 0 var(--space-xs);
}

.subsection-title {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  font-weight: 600;
  margin: var(--space-md) 0 var(--space-xs);
}

.settings-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
  font-family: var(--font-mono);
}

.settings-table th,
.settings-table td {
  border: 1px solid var(--border-color);
  padding: 10px 12px;
  text-align: left;
}

.settings-table th {
  background: var(--bg-muted);
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
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
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  color: var(--color-text-secondary);
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
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  width: 100%;
}

.budget-select,
.budget-input {
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  padding: 6px 8px;
  background: var(--bg-primary);
  min-width: 160px;
  border: var(--border-width) solid var(--border-color);
  border-radius: var(--radius-sm);
}

.edit-error {
  font-size: var(--text-sm);
  font-family: var(--font-ui);
  color: var(--color-danger);
  margin: var(--space-xs) 0 0;
}

code {
  font-size: var(--text-sm);
}
</style>
