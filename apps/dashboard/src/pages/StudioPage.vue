<!--
  StudioPage.vue — Phase 10.04: 灵文工作室控制台
  - 多项目切换（ProjectSwitcher 在 header）
  - 质量仪表盘（支柱 / 大纲 / Golden Set）
  - Pilot / 批处理生命周期已迁至 /pilot 页面
-->
<template>
  <div class="studio-page">
    <header v-if="!embedded" class="page-header">
      <h1 class="page-title" data-testid="page-title">灵文工作室</h1>
      <button
        class="refresh-btn pixel-border"
        data-testid="refresh-btn"
        :disabled="loading"
        :aria-label="loading ? '正在加载，请稍后' : '刷新页面'"
        :aria-busy="loading"
        @click="refresh"
      >
        {{ loading ? '加载中…' : '刷新' }}
      </button>
    </header>

    <div v-if="displayError" class="error-banner pixel-border" data-testid="error-banner" role="alert" aria-live="polite">
      {{ displayError }}
    </div>

    <HubEmptyGuide
      v-if="showStudioEmptyGuide"
      title="本书尚未开始正文生产"
      hint="建议去 Pilot 页配置预飞 / 启动 Batch；若做人主笔，可去创作页写 ch001。"
      secondary-label="去创作页"
      secondary-test-id="studio-go-creator-btn"
      test-id="studio-empty-guide"
      @secondary="goCreator"
    />

    <section v-if="summary" class="studio-section pixel-card project-summary" data-testid="project-summary">
      <h2 class="section-title">{{ summary.name }}</h2>
      <div class="stats-row">
        <StatCard label="角色" :value="summary.role" />
        <StatCard label="正文章数" :value="String(summary.chapter_count)" />
        <StatCard label="最新章" :value="summary.latest_chapter ? `ch${String(summary.latest_chapter).padStart(3, '0')}` : '—'" />
        <StatCard label="上限" :value="String(summary.max_chapter)" />
      </div>
      <details class="studio-path-details">
        <summary class="meta-line studio-path-summary">项目路径（运维）</summary>
        <p class="meta-line"><code>{{ summary.root }}</code></p>
      </details>
    </section>

    <details v-if="quality" class="studio-section pixel-card quality-collapsible quality-panel" data-testid="quality-panel">
      <summary class="section-title">质量仪表盘</summary>
      <ul class="quality-list">
        <li :class="quality.pillars_ok ? 'ok' : 'warn'">
          支柱文件：{{ quality.pillars_ok ? '✓' : '✗' }}
          <details class="studio-path-details inline-details">
            <summary class="meta-line">查看路径</summary>
            <code>{{ quality.pillars_path }}</code>
          </details>
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
    </details>

    <section v-if="qualityReport" class="studio-section pixel-card quality-report-panel" data-testid="quality-report-panel">
      <h2 class="section-title">Full-check 质检报告</h2>
      <div v-if="!qualityReport.available" class="report-empty">
        <p>暂无质检报告。产章后可生成 full-check 报告查看 P0–P3 问题分布。</p>
        <p class="meta-line">
          CLI：<code>bash scripts/generate-full-check-report.sh {{ activeSlug || 'slug' }}</code>
        </p>
        <button type="button" class="empty-cta-btn pixel-border report-empty-go-production-btn" data-testid="report-empty-go-production-btn" @click="goPilot">
          去 Pilot 页跑预飞 / 启动 Batch
        </button>
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
          role="img"
          aria-label="章节质量热力图，显示各章节的Prose问题密度"
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
        class="prose-diff prose-diff-panel"
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
            class="diff-status prose-diff-status"
            :class="proseDiff.has_regression ? 'diff-regressed' : 'diff-ok'"
            data-testid="prose-diff-status"
            role="status"
            aria-live="polite"
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
      <div
        v-if="proseJudge"
        class="prose-judge prose-judge-panel"
        data-testid="prose-judge-panel"
      >
        <h3 class="subsection-title">Prose Judge（v2）</h3>
        <div v-if="!proseJudge.available" class="report-empty">
          尚无 judge 报告。生成：
          <code>{{ proseJudge.generate_command || `bash scripts/run-prose-judge.sh ${activeSlug || 'slug'}` }}</code>
        </div>
        <template v-else>
          <p class="meta-line">
            来源 {{ proseJudge.source }} · {{ proseJudge.judged_at }}
            · Golden ch{{ (proseJudge.golden_chapters || []).join(',') }}
            · 均分 {{ proseJudge.weighted_avg }}
          </p>
          <div class="judge-signals meta-line prose-judge-signals" data-testid="prose-judge-signals">
            高优先级 {{ proseJudge.high_priority_count }}
            · 误报候选 {{ proseJudge.false_positive_candidate_count }}
            · 待复核 {{ proseJudge.review_needed_count }}
          </div>
          <ul v-if="proseJudge.chapters?.length" class="judge-chapters">
            <li v-for="ch in proseJudge.chapters" :key="ch.chapter" class="judge-chapter-row">
              ch{{ String(ch.chapter).padStart(2, '0') }} · 均分 {{ ch.avg_score }}
              <span
                v-for="r in ch.ratings"
                :key="r.dimension"
                class="judge-dim-chip"
                :class="judgeScoreClass(r.score)"
                :title="r.evidence"
              >
                {{ r.dimension }} {{ r.score }}
              </span>
            </li>
          </ul>
          <p class="meta-line">
            LLM 刷新：<code>{{ proseJudge.generate_command }}</code>
            · 抽检导出：<code>bash scripts/run-prose-calibration-sample.sh {{ activeSlug || 'slug' }}</code>
          </p>
        </template>
      </div>
    </section>

    <section class="studio-section pixel-card onboarding-panel" data-testid="onboarding-panel">
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
import { onMounted, ref, computed } from 'vue';
import StatCard from '../components/StatCard.vue';
import HubEmptyGuide from '../components/HubEmptyGuide.vue';
import { useStudioProject, useDashboardNav, useFilteredPageError } from '../composables/index.js';

defineProps({
  embedded: { type: Boolean, default: false },
});

const { summary, quality, qualityReport, proseDiff, proseJudge, loading, error, refresh, activeSlug } = useStudioProject();
const displayError = useFilteredPageError(error);
const { navigateTo } = useDashboardNav();

const showStudioEmptyGuide = computed(() => {
  if (loading || error || !quality) return false;
  return (quality.chapters_written ?? 0) === 0;
});

function goCreator() {
  navigateTo('creator');
}

function goPilot() {
  window.location.assign('/pilot');
}

const proseDiffChapters = computed(() => {
  const rows = proseDiff?.chapters || [];
  return [...rows].sort((a, b) => a.chapter - b.chapter);
});

function judgeScoreClass(score) {
  const v = Number(score) || 0;
  if (v >= 4) return 'diff-improved';
  if (v <= 2) return 'diff-regressed';
  return 'diff-neutral';
}

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

onMounted(() => {
  refresh();
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

.refresh-btn {
  font-size: var(--text-sm);
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
  font-size: var(--text-md);
  font-family: 'Press Start 2P', monospace;
  color: var(--color-accent);
  margin: 0 0 var(--space-sm);
}

.subsection-title {
  font-size: var(--text-sm);
  font-family: 'Press Start 2P', monospace;
  margin: var(--space-md) 0 var(--space-xs);
}

.stats-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.meta-line {
  font-size: var(--text-md);
  font-family: monospace;
  margin-top: var(--space-sm);
  opacity: 0.85;
}

.studio-path-summary {
  color: var(--color-text-secondary);
  opacity: 1;
}

.quality-list {
  font-size: var(--text-md);
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

.onboarding-steps {
  font-size: var(--text-md);
  font-family: monospace;
  padding-left: 1.2rem;
}

.error-banner {
  background: var(--color-danger);
  color: white;
  padding: var(--space-md);
  font-size: var(--text-sm);
  font-family: 'Press Start 2P', monospace;
}

.report-summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-bottom: var(--space-sm);
}

.report-chapter {
  margin-top: var(--space-sm);
  font-size: var(--text-md);
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

.studio-path-details {
  margin-top: var(--space-xs);
}

.studio-path-details summary {
  cursor: pointer;
  color: var(--color-accent);
}

.inline-details {
  display: inline-block;
  margin-left: var(--space-xs);
}

.report-empty {
  font-size: var(--text-md);
  font-family: monospace;
}

.empty-cta-btn {
  font-size: var(--text-sm);
  font-family: 'Press Start 2P', monospace;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-secondary);
  cursor: pointer;
  margin-top: var(--space-sm);
}

.empty-cta-btn:hover {
  background: var(--color-accent);
  color: white;
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
  font-size: var(--text-sm);
  font-family: monospace;
  margin-top: 2px;
}

.prose-diff {
  margin: var(--space-sm) 0 var(--space-md);
  padding-top: var(--space-sm);
  border-top: 1px dashed var(--border-color);
}

.diff-status {
  font-size: var(--text-md);
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
  font-size: var(--text-sm);
  font-family: monospace;
  padding: 2px 6px;
  border: 1px solid var(--border-color);
}

.diff-chapters {
  list-style: none;
  margin: 0;
  padding: 0;
  font-size: var(--text-md);
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

.prose-judge {
  margin: var(--space-sm) 0 0;
  padding-top: var(--space-sm);
  border-top: 1px dashed var(--border-color);
}

.judge-chapters {
  list-style: none;
  margin: var(--space-xs) 0;
  padding: 0;
  font-size: var(--text-md);
  font-family: monospace;
}

.judge-chapter-row {
  padding: 4px 0;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.judge-dim-chip {
  font-size: var(--text-sm);
  padding: 2px 4px;
  border: 1px solid var(--border-color);
}

.judge-signals {
  margin: var(--space-xs) 0;
}

code {
  font-size: var(--text-sm);
}
</style>
