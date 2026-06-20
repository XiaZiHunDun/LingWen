<!--
  StudioPage.vue — Phase 10.04: 灵文工作室控制台
  - 多项目切换（ProjectSwitcher 在 header）
  - 生产 preflight + batch 命令
  - 质量仪表盘（支柱 / 大纲 / Golden Set）
-->
<template>
  <div class="studio-page">
    <header class="page-header">
      <h1 class="page-title" data-testid="page-title">灵文工作室</h1>
      <button
        class="refresh-btn pixel-border"
        data-testid="refresh-btn"
        :disabled="loading"
        @click="refresh"
      >
        {{ loading ? '加载中…' : '刷新' }}
      </button>
    </header>

    <div v-if="error" class="error-banner pixel-border" data-testid="error-banner">
      {{ error }}
    </div>

    <section v-if="summary" class="studio-section pixel-card" data-testid="project-summary">
      <h2 class="section-title">{{ summary.name }}</h2>
      <div class="stats-row">
        <StatCard label="角色" :value="summary.role" />
        <StatCard label="正文章数" :value="String(summary.chapter_count)" />
        <StatCard label="最新章" :value="summary.latest_chapter ? `ch${String(summary.latest_chapter).padStart(3, '0')}` : '—'" />
        <StatCard label="上限" :value="String(summary.max_chapter)" />
      </div>
      <p class="meta-line">
        <code>{{ summary.root }}</code>
      </p>
    </section>

    <section v-if="quality" class="studio-section pixel-card" data-testid="quality-panel">
      <h2 class="section-title">质量仪表盘</h2>
      <ul class="quality-list">
        <li :class="quality.pillars_ok ? 'ok' : 'warn'">
          支柱文件：{{ quality.pillars_ok ? '✓' : '✗' }}
          <code>{{ quality.pillars_path }}</code>
        </li>
        <li>正文覆盖率：{{ quality.coverage_pct }}%（{{ quality.chapters_written }}/{{ quality.max_chapter }}）</li>
        <li>大纲数量：{{ quality.outlines_present }}</li>
        <li v-if="quality.missing_outlines.length">
          缺大纲：{{ quality.missing_outlines.map((n) => `ch${String(n).padStart(3, '0')}`).join(', ') }}
        </li>
        <li v-if="quality.missing_bodies.length">
          有大纲无正文：{{ quality.missing_bodies.map((n) => `ch${String(n).padStart(3, '0')}`).join(', ') }}
        </li>
        <li>
          Golden Set：{{ quality.golden_set_status === 'ready' ? '已配置' : '未配置' }}
          <code v-if="quality.golden_set_status === 'ready'">{{ quality.golden_regression_cmd }}</code>
        </li>
      </ul>
    </section>

    <section v-if="qualityReport" class="studio-section pixel-card" data-testid="quality-report-panel">
      <h2 class="section-title">Full-check 质检报告</h2>
      <div v-if="!qualityReport.available" class="report-empty">
        暂无报告。生成：<code>bash scripts/generate-full-check-report.sh {{ activeSlug || 'slug' }}</code>
      </div>
      <template v-else>
        <div class="report-summary">
          <StatCard label="合计" :value="String(qualityReport.total)" />
          <StatCard label="P0" :value="String(qualityReport.p0)" />
          <StatCard label="P1" :value="String(qualityReport.p1)" />
          <StatCard label="P2" :value="String(qualityReport.p2)" />
          <StatCard label="P3" :value="String(qualityReport.p3)" />
        </div>
        <p v-if="qualityReport.generated_at" class="meta-line">生成于 {{ qualityReport.generated_at }}</p>
        <p class="meta-line"><code>{{ qualityReport.path }}</code></p>
        <div
          v-if="qualityReport.prose_heatmap?.chapters?.length"
          class="prose-heatmap"
          data-testid="prose-heatmap"
        >
          <h3 class="subsection-title">Prose 热力图</h3>
          <p class="meta-line">
            prose P1 合计 {{ qualityReport.prose_heatmap.total_prose_p1 }}
            · prose 问题 {{ qualityReport.prose_heatmap.total_prose_issues }}
          </p>
          <div class="heatmap-bars">
            <div
              v-for="cell in qualityReport.prose_heatmap.chapters"
              :key="cell.chapter"
              class="heatmap-cell"
              :title="`ch${String(cell.chapter).padStart(3, '0')}: prose ${cell.prose_total} (P1 ${cell.prose_p1})`"
            >
              <div
                class="heatmap-bar"
                :style="{ opacity: Math.max(0.15, cell.heat) }"
              />
              <span class="heatmap-label">{{ String(cell.chapter).padStart(2, '0') }}</span>
            </div>
          </div>
        </div>
        <details v-for="ch in qualityReport.chapters" :key="ch.chapter" class="report-chapter">
          <summary>
            ch{{ String(ch.chapter).padStart(3, '0') }} · {{ ch.word_count }} 字 · {{ ch.issue_count }} 问题
          </summary>
          <ul v-if="ch.issues.length" class="report-issues">
            <li v-for="(issue, idx) in ch.issues" :key="idx" :class="`sev-${issue.severity.toLowerCase()}`">
              <strong>[{{ issue.severity }}]</strong> {{ issue.issue_type }} — {{ issue.description }}
            </li>
          </ul>
          <p v-else class="meta-line">（无）</p>
        </details>
      </template>
      <div
        v-if="proseDiff"
        class="prose-diff"
        data-testid="prose-diff-panel"
      >
        <h3 class="subsection-title">Prose 改稿对比</h3>
        <div v-if="!proseDiff.available" class="report-empty">
          <template v-if="proseDiff.reason === 'no_baseline'">
            尚无 prose 基线快照。定稿后执行：
            <code>{{ proseDiff.save_command || `bash scripts/run-prose-diff.sh ${activeSlug || 'slug'} --save` }}</code>
          </template>
          <template v-else-if="proseDiff.reason === 'no_report'">
            有基线（{{ proseDiff.before_captured_at }}）但缺少 full-check 报告。生成：
            <code>{{ proseDiff.save_command }}</code>
          </template>
          <template v-else>
            暂无法对比 prose 快照。
          </template>
        </div>
        <template v-else>
          <p class="meta-line">
            基线 {{ proseDiff.before_captured_at }}
            → 当前 {{ proseDiff.after_captured_at }}
          </p>
          <div
            class="diff-status"
            :class="proseDiff.has_regression ? 'diff-regressed' : 'diff-ok'"
            data-testid="prose-diff-status"
          >
            {{ proseDiff.has_regression ? '⚠ 检测到 prose 回归' : '✓ 无 prose 回归' }}
            · prose P1 Δ {{ formatDelta(proseDiff.net_prose_p1_delta) }}
            · 改善 {{ proseDiff.improved_count }} 章 · 回归 {{ proseDiff.regressed_count }} 章
          </div>
          <div v-if="proseDiff.total_delta" class="diff-totals">
            <span
              v-for="key in ['prose_p1', 'prose_total', 'total', 'p0']"
              :key="key"
              class="diff-total-chip"
              :class="deltaChipClass(proseDiff.total_delta[key])"
            >
              {{ key }} {{ formatDelta(proseDiff.total_delta[key]) }}
            </span>
          </div>
          <ul v-if="proseDiffChapters.length" class="diff-chapters">
            <li
              v-for="row in proseDiffChapters"
              :key="row.chapter"
              class="diff-chapter-row"
              :class="chapterDiffClass(row)"
            >
              ch{{ String(row.chapter).padStart(2, '0') }}
              · P1 {{ row.before_prose_p1 }}→{{ row.after_prose_p1 }}
              ({{ formatDelta(row.delta_prose_p1) }})
              · prose {{ row.before_prose_total }}→{{ row.after_prose_total }}
            </li>
          </ul>
          <p v-else class="meta-line">（无章级变化）</p>
        </template>
      </div>
    </section>

    <section class="studio-section pixel-card" data-testid="production-console">
      <h2 class="section-title">生产控制台</h2>
      <form class="prod-form" @submit.prevent="runPreflight">
        <div class="form-row">
          <label>起始章</label>
          <input v-model.number="startChapter" type="number" min="1" class="form-input pixel-border" data-testid="start-chapter" />
        </div>
        <div class="form-row">
          <label>结束章</label>
          <input v-model.number="endChapter" type="number" min="1" class="form-input pixel-border" data-testid="end-chapter" />
        </div>
        <div class="form-row">
          <label>模式</label>
          <select v-model="mode" class="form-input pixel-border" data-testid="production-mode">
            <option value="canon">canon</option>
            <option value="pilot">pilot</option>
          </select>
        </div>
        <div class="form-row">
          <label>预算 (USD)</label>
          <input v-model.number="budgetUsd" type="number" min="0" max="100" step="0.01" class="form-input pixel-border" data-testid="budget-usd" />
        </div>
        <button type="submit" class="run-btn pixel-border" data-testid="preflight-btn" :disabled="preflightLoading">
          {{ preflightLoading ? '检查中…' : 'Preflight 检查' }}
        </button>
      </form>

      <div v-if="preflightError" class="preflight-error" data-testid="preflight-error">{{ preflightError }}</div>

      <table v-if="preflightRows.length" class="preflight-table" data-testid="preflight-table">
        <thead>
          <tr>
            <th>章</th>
            <th>状态</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in preflightRows" :key="row.chapter">
            <td>ch{{ String(row.chapter).padStart(3, '0') }}</td>
            <td :class="row.ok ? 'status-ok' : 'status-fail'">{{ row.ok ? 'PASS' : 'FAIL' }}</td>
            <td>{{ row.message }}</td>
          </tr>
        </tbody>
      </table>

      <div v-if="batchCommand" class="command-block" data-testid="batch-command">
        <h3 class="subsection-title">Batch 命令</h3>
        <pre class="command-pre">{{ batchCommand }}</pre>
        <div class="command-actions">
          <button type="button" class="copy-btn pixel-border" data-testid="copy-command-btn" @click="copyCommand">
            复制命令
          </button>
          <button
            type="button"
            class="run-btn pixel-border"
            data-testid="run-batch-btn"
            :disabled="batchRunning || !preflightAllOk"
            @click="startBatch"
          >
            {{ batchRunning ? 'Batch 运行中…' : '后台启动 Batch' }}
          </button>
        </div>
        <p v-if="copyMessage" class="copy-msg">{{ copyMessage }}</p>
        <p v-if="batchRunError" class="batch-error" data-testid="batch-run-error">{{ batchRunError }}</p>
      </div>

      <div v-if="batchJob" class="job-block pixel-card" data-testid="batch-job-panel">
        <h3 class="subsection-title">Batch 任务 {{ batchJob.job_id }}</h3>
        <p class="job-meta">
          状态：<strong :class="`job-status-${batchJob.status}`">{{ batchJob.status }}</strong>
          · ch{{ String(batchJob.start_chapter).padStart(3, '0') }}–{{ String(batchJob.end_chapter).padStart(3, '0') }}
          · ${{ batchJob.budget_usd?.toFixed?.(2) ?? batchJob.budget_usd }}
        </p>
        <pre v-if="batchJob.log_tail" class="command-pre job-log">{{ batchJob.log_tail }}</pre>
      </div>
    </section>

    <section class="studio-section pixel-card" data-testid="onboarding-panel">
      <h2 class="section-title">快速上手</h2>
      <ol class="onboarding-steps">
        <li><code>python lingwen.py init-project &lt;slug&gt; --title "书名"</code></li>
        <li>填写 <code>03_内容仓库/04_正文/chNNN_大纲.md</code> 与 <code>docs/novel-pillars.md</code></li>
        <li>在此页 Preflight → 复制 Batch 命令 → 终端执行</li>
        <li><code>python lingwen.py check 1-10 --quick</code></li>
        <li><code>./scripts/run-golden-set-check.sh &lt;slug&gt;</code></li>
      </ol>
      <p class="meta-line">完整指南：<code>docs/studio-onboarding.md</code></p>
    </section>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, computed } from 'vue';
import StatCard from '../components/StatCard.vue';
import {
  studioProductionPreflight,
  studioProductionRun,
  fetchStudioBatchJob,
  fetchStudioActiveBatchJob,
} from '../api/index.js';
import { useStudioProject } from '../composables/useStudioProject.js';

const { summary, quality, qualityReport, proseDiff, loading, error, refresh, bumpProjectRevision, activeSlug } = useStudioProject();

const proseDiffChapters = computed(() => {
  const rows = proseDiff.value?.chapters || [];
  return [...rows].sort((a, b) => a.chapter - b.chapter);
});

function formatDelta(n) {
  const v = Number(n) || 0;
  return v > 0 ? `+${v}` : String(v);
}

function chapterDiffClass(row) {
  if (row.delta_prose_p1 < 0 || (row.delta_prose_p1 === 0 && row.delta_prose_total < 0)) {
    return 'diff-improved';
  }
  if (row.delta_prose_p1 > 0 || (row.delta_prose_p1 === 0 && row.delta_prose_total > 0)) {
    return 'diff-regressed';
  }
  return 'diff-neutral';
}

function deltaChipClass(delta) {
  const v = Number(delta) || 0;
  if (v < 0) return 'diff-improved';
  if (v > 0) return 'diff-regressed';
  return 'diff-neutral';
}

const startChapter = ref(1);
const endChapter = ref(3);
const mode = ref('canon');
const budgetUsd = ref(0.15);
const preflightLoading = ref(false);
const preflightError = ref(null);
const preflightRows = ref([]);
const batchCommand = ref('');
const copyMessage = ref('');
const batchRunError = ref(null);
const batchJob = ref(null);
const batchRunning = ref(false);
let pollTimer = null;

const preflightAllOk = computed(() =>
  preflightRows.value.length > 0 && preflightRows.value.every((row) => row.ok),
);

async function runPreflight() {
  preflightLoading.value = true;
  preflightError.value = null;
  preflightRows.value = [];
  batchCommand.value = '';
  try {
    const data = await studioProductionPreflight({
      start_chapter: startChapter.value,
      end_chapter: endChapter.value,
      mode: mode.value,
      budget_usd: budgetUsd.value,
    });
    preflightRows.value = data.chapters || [];
    batchCommand.value = data.batch_command || '';
  } catch (e) {
    preflightError.value = e instanceof Error ? e.message : String(e);
  } finally {
    preflightLoading.value = false;
  }
}

async function copyCommand() {
  if (!batchCommand.value) return;
  try {
    await navigator.clipboard.writeText(batchCommand.value);
    copyMessage.value = '已复制到剪贴板';
  } catch {
    copyMessage.value = '复制失败，请手动选择命令';
  }
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function pollBatchJob(jobId) {
  try {
    const job = await fetchStudioBatchJob(jobId);
    batchJob.value = job;
    batchRunning.value = job.status === 'running';
    if (job.status !== 'running') {
      stopPolling();
      bumpProjectRevision();
    }
  } catch (e) {
    batchRunError.value = e instanceof Error ? e.message : String(e);
    stopPolling();
    batchRunning.value = false;
  }
}

function startPolling(jobId) {
  stopPolling();
  pollTimer = setInterval(() => pollBatchJob(jobId), 3000);
}

async function loadActiveBatchJob() {
  try {
    const job = await fetchStudioActiveBatchJob();
    if (job) {
      batchJob.value = job;
      batchRunning.value = job.status === 'running';
      if (job.status === 'running') {
        startPolling(job.job_id);
      }
    }
  } catch {
    // ignore — no active job
  }
}

async function startBatch() {
  batchRunError.value = null;
  batchRunning.value = true;
  try {
    const job = await studioProductionRun({
      start_chapter: startChapter.value,
      end_chapter: endChapter.value,
      mode: mode.value,
      budget_usd: budgetUsd.value,
    });
    batchJob.value = job;
    startPolling(job.job_id);
  } catch (e) {
    batchRunError.value = e instanceof Error ? e.message : String(e);
    batchRunning.value = false;
  }
}

onMounted(() => {
  refresh();
  loadActiveBatchJob();
});

onUnmounted(() => {
  stopPolling();
});
</script>

<style scoped>
.studio-page {
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
  font-family: 'Press Start 2P', monospace;
}

.refresh-btn,
.run-btn,
.copy-btn {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-secondary);
  cursor: pointer;
}

.studio-section {
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

.stats-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.meta-line {
  font-size: 10px;
  font-family: monospace;
  margin-top: var(--space-sm);
  opacity: 0.85;
}

.quality-list {
  font-size: 10px;
  font-family: monospace;
  margin: 0;
  padding-left: 1.2rem;
}

.quality-list li.ok {
  color: var(--color-success);
}

.quality-list li.warn {
  color: var(--color-danger);
}

.prod-form {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  align-items: flex-end;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-row label {
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
}

.form-input {
  font-size: 10px;
  font-family: monospace;
  padding: 6px 8px;
  background: var(--bg-primary);
  min-width: 100px;
}

.preflight-table {
  width: 100%;
  margin-top: var(--space-md);
  border-collapse: collapse;
  font-size: 10px;
  font-family: monospace;
}

.preflight-table th,
.preflight-table td {
  border: 1px solid var(--border-color);
  padding: 6px 8px;
  text-align: left;
}

.status-ok {
  color: var(--color-success);
}

.status-fail {
  color: var(--color-danger);
}

.command-pre {
  font-size: 10px;
  font-family: monospace;
  background: var(--bg-primary);
  padding: var(--space-sm);
  overflow-x: auto;
  white-space: pre-wrap;
}

.onboarding-steps {
  font-size: 10px;
  font-family: monospace;
  padding-left: 1.2rem;
}

.error-banner,
.preflight-error {
  background: var(--color-danger);
  color: white;
  padding: var(--space-md);
  font-size: 8px;
  font-family: 'Press Start 2P', monospace;
}

.copy-msg {
  font-size: 10px;
  font-family: monospace;
  margin-top: var(--space-xs);
}

.command-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}

.batch-error {
  font-size: 10px;
  font-family: monospace;
  color: var(--color-danger);
  margin-top: var(--space-xs);
}

.job-block {
  margin-top: var(--space-md);
  padding: var(--space-sm);
  border: 1px solid var(--border-color);
}

.job-meta {
  font-size: 10px;
  font-family: monospace;
}

.job-status-running {
  color: var(--color-warning);
}

.job-status-completed {
  color: var(--color-success);
}

.job-status-failed {
  color: var(--color-danger);
}

.job-log {
  max-height: 200px;
  overflow-y: auto;
}

.report-summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.report-chapter {
  margin-top: var(--space-sm);
  font-size: 10px;
  font-family: monospace;
}

.report-issues {
  margin: var(--space-xs) 0 0 1rem;
  padding: 0;
}

.report-issues li {
  margin-bottom: 4px;
}

.sev-p0 {
  color: var(--color-danger);
}

.sev-p1 {
  color: var(--color-warning);
}

.report-empty {
  font-size: 10px;
  font-family: monospace;
}

.prose-heatmap {
  margin: var(--space-sm) 0 var(--space-md);
}

.heatmap-bars {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: var(--space-xs);
}

.heatmap-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 28px;
}

.heatmap-bar {
  width: 100%;
  height: 48px;
  background: var(--color-warning);
  border: 1px solid var(--border-color);
}

.heatmap-label {
  font-size: 8px;
  font-family: monospace;
  margin-top: 2px;
}

.prose-diff {
  margin: var(--space-sm) 0 var(--space-md);
  padding-top: var(--space-sm);
  border-top: 1px dashed var(--border-color);
}

.diff-status {
  font-size: 10px;
  font-family: monospace;
  margin: var(--space-xs) 0;
}

.diff-status.diff-ok {
  color: var(--color-success);
}

.diff-status.diff-regressed {
  color: var(--color-danger);
}

.diff-totals {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: var(--space-xs) 0 var(--space-sm);
}

.diff-total-chip {
  font-size: 9px;
  font-family: monospace;
  padding: 2px 6px;
  border: 1px solid var(--border-color);
}

.diff-chapters {
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: 10px;
  font-family: monospace;
}

.diff-chapter-row {
  padding: 4px 0;
  border-bottom: 1px solid var(--border-color);
}

.diff-improved {
  color: var(--color-success);
}

.diff-regressed {
  color: var(--color-danger);
}

.diff-neutral {
  opacity: 0.75;
}

code {
  font-size: 9px;
}
</style>
