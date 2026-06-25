<!--
  CreatorBatchHistoryPanel.vue — 脉络栏 Batch 历史（从 CreatorPage 拆出）
-->
<template>
        <div
          v-if="bh.uiProfile.batch_history_panel && bh.batchHistory.length"
          class="batch-history-panel pixel-border"
          data-testid="batch-history-panel"
        >
          <h3 class="subsection-title">Batch 历史</h3>
          <button
            v-if="bh.uiProfile.batch_history_ops_summary"
            type="button"
            class="mini-btn pixel-border batch-history-ops-summary-toggle"
            data-testid="batch-history-ops-summary-toggle"
            @click="bh.toggleBatchHistoryOpsSummary"
          >
            运维摘要{{ bh.batchHistoryOpsSummaryOpen ? '（收起）' : '（展开）' }}
            <span class="batch-history-ops-summary-line">{{ bh.batchHistoryOpsSummaryLine }}</span>
          </button>
          <div
            v-show="!bh.uiProfile.batch_history_ops_summary || bh.batchHistoryOpsSummaryOpen"
            class="batch-history-ops-summary-body"
            data-testid="batch-history-ops-summary-body"
          >
          <p
            v-if="bh.batchHistorySuccessRate"
            class="meta-line batch-history-success-rate"
            data-testid="batch-history-success-rate"
          >
            成功率 {{ bh.batchHistorySuccessRate.pct }}%（{{ bh.batchHistorySuccessRate.completed }}/{{ bh.batchHistorySuccessRate.total }} 已完成）
          </p>
          <div
            v-if="bh.batchHistorySuccessRateChart"
            class="batch-history-success-rate-chart"
            data-testid="batch-history-success-rate-chart"
          >
            <svg
              :viewBox="`0 0 ${bh.batchHistorySuccessRateChart.width} ${bh.batchHistorySuccessRateChart.height}`"
              class="batch-history-success-rate-chart-svg"
              role="img"
              aria-label="batch 历史成功率折线图"
            >
              <polyline
                :points="bh.batchHistorySuccessRateChart.polyline"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              />
            </svg>
            <p class="meta-line batch-history-success-rate-chart-label">
              累计成功率趋势（{{ bh.batchHistorySuccessRateChart.points.length }} 次）
            </p>
          </div>
          <div
            v-if="bh.batchHistoryStatusStackChart"
            class="batch-history-status-stack-chart"
            data-testid="batch-history-status-stack-chart"
          >
            <svg
              :viewBox="`0 0 ${bh.batchHistoryStatusStackChart.width} ${bh.batchHistoryStatusStackChart.height}`"
              class="batch-history-status-stack-chart-svg"
              role="img"
              aria-label="batch 历史状态堆叠图"
            >
              <rect
                v-for="segment in bh.batchHistoryStatusStackChart.segments"
                :key="`batch-stack-${segment.status}`"
                :x="segment.x"
                y="0"
                :width="segment.width"
                :height="bh.batchHistoryStatusStackChart.height"
                :class="`batch-history-stack-segment batch-history-stack-segment--${segment.status}`"
                :data-testid="`batch-history-stack-${segment.status}`"
              />
            </svg>
            <p class="meta-line batch-history-status-stack-label">
              状态分布：
              <span
                v-for="segment in bh.batchHistoryStatusStackChart.segments"
                :key="`batch-stack-label-${segment.status}`"
              >
                {{ segment.status }} {{ segment.count }}
              </span>
            </p>
          </div>
          <div
            v-if="bh.batchHistoryDurationDistribution"
            class="batch-history-duration-distribution"
            data-testid="batch-history-duration-distribution"
          >
            <svg
              :viewBox="`0 0 ${bh.batchHistoryDurationDistribution.width} ${bh.batchHistoryDurationDistribution.height}`"
              class="batch-history-duration-distribution-svg"
              role="img"
              aria-label="batch 历史耗时分布图"
            >
              <rect
                v-for="bar in bh.batchHistoryDurationDistribution.bars"
                :key="`duration-bar-${bar.id}`"
                :x="bar.x"
                :y="bar.y"
                :width="bar.barWidth"
                :height="bar.barHeight"
                class="batch-history-duration-bar"
                :data-testid="`batch-history-duration-${bar.id}`"
              />
            </svg>
            <p class="meta-line batch-history-duration-distribution-label">
              耗时分布：
              <span
                v-for="bar in bh.batchHistoryDurationDistribution.bars"
                :key="`duration-label-${bar.id}`"
              >
                {{ bar.label }} {{ bar.count }}
              </span>
            </p>
          </div>
          <div
            v-if="bh.batchHistoryConcurrencyChart"
            class="batch-history-concurrency-chart"
            data-testid="batch-history-concurrency-chart"
          >
            <svg
              :viewBox="`0 0 ${bh.batchHistoryConcurrencyChart.width} ${bh.batchHistoryConcurrencyChart.height}`"
              class="batch-history-concurrency-chart-svg"
              role="img"
              aria-label="batch 历史并发运行图"
            >
              <rect
                v-for="bar in bh.batchHistoryConcurrencyChart.bars"
                :key="`concurrency-bar-${bar.id}`"
                :x="bar.x"
                :y="bar.y"
                :width="bar.barWidth"
                :height="bar.barHeight"
                class="batch-history-concurrency-bar"
                :data-testid="`batch-history-concurrency-${bar.id}`"
              />
            </svg>
            <p class="meta-line batch-history-concurrency-chart-label">
              并发运行：峰值 {{ bh.batchHistoryConcurrencyChart.peak }}
            </p>
          </div>
          <div
            v-if="bh.batchHistoryQueueDepthChart"
            class="batch-history-queue-depth-chart"
            data-testid="batch-history-queue-depth-chart"
          >
            <svg
              :viewBox="`0 0 ${bh.batchHistoryQueueDepthChart.width} ${bh.batchHistoryQueueDepthChart.height}`"
              class="batch-history-queue-depth-chart-svg"
              role="img"
              aria-label="batch 历史队列深度图"
            >
              <rect
                v-for="bar in bh.batchHistoryQueueDepthChart.bars"
                :key="`queue-depth-bar-${bar.id}`"
                :x="bar.x"
                :y="bar.y"
                :width="bar.barWidth"
                :height="bar.barHeight"
                class="batch-history-queue-depth-bar"
                :data-testid="`batch-history-queue-depth-${bar.id}`"
              />
            </svg>
            <p class="meta-line batch-history-queue-depth-chart-label">
              队列深度：峰值 {{ bh.batchHistoryQueueDepthChart.peak }}
            </p>
          </div>
          <div
            v-if="bh.batchHistoryThroughputChart"
            class="batch-history-throughput-chart"
            data-testid="batch-history-throughput-chart"
          >
            <svg
              :viewBox="`0 0 ${bh.batchHistoryThroughputChart.width} ${bh.batchHistoryThroughputChart.height}`"
              class="batch-history-throughput-chart-svg"
              role="img"
              aria-label="batch 历史吞吐率图"
            >
              <rect
                v-for="bar in bh.batchHistoryThroughputChart.bars"
                :key="`throughput-bar-${bar.id}`"
                :x="bar.x"
                :y="bar.y"
                :width="bar.barWidth"
                :height="bar.barHeight"
                class="batch-history-throughput-bar"
                :data-testid="`batch-history-throughput-${bar.id}`"
              />
            </svg>
            <p class="meta-line batch-history-throughput-chart-label">
              吞吐率：均值 {{ bh.batchHistoryThroughputChart.avg }} 章/分 · 峰值 {{ bh.batchHistoryThroughputChart.peak }}
            </p>
          </div>
          <div
            v-if="bh.batchHistoryCostEfficiencyChart"
            class="batch-history-cost-efficiency-chart"
            data-testid="batch-history-cost-efficiency-chart"
          >
            <svg
              :viewBox="`0 0 ${bh.batchHistoryCostEfficiencyChart.width} ${bh.batchHistoryCostEfficiencyChart.height}`"
              class="batch-history-cost-efficiency-chart-svg"
              role="img"
              aria-label="batch 历史成本效率图"
            >
              <rect
                v-for="bar in bh.batchHistoryCostEfficiencyChart.bars"
                :key="`cost-bar-${bar.id}`"
                :x="bar.x"
                :y="bar.y"
                :width="bar.barWidth"
                :height="bar.barHeight"
                class="batch-history-cost-efficiency-bar"
                :data-testid="`batch-history-cost-${bar.id}`"
              />
            </svg>
            <p class="meta-line batch-history-cost-efficiency-chart-label">
              成本效率：均值 ${{ bh.batchHistoryCostEfficiencyChart.avg }} /章
            </p>
          </div>
          <div
            v-if="bh.batchHistoryRetryRateStack"
            class="batch-history-retry-rate-stack"
            data-testid="batch-history-retry-rate-stack"
          >
            <svg
              :viewBox="`0 0 ${bh.batchHistoryRetryRateStack.width} ${bh.batchHistoryRetryRateStack.height}`"
              class="batch-history-retry-rate-stack-svg"
              role="img"
              aria-label="batch 历史重试成功率堆叠图"
            >
              <rect
                v-for="segment in bh.batchHistoryRetryRateStack.segments"
                :key="`retry-seg-${segment.id}`"
                :x="segment.x"
                y="0"
                :width="segment.width"
                :height="bh.batchHistoryRetryRateStack.height"
                :class="`batch-history-retry-seg batch-history-retry-seg--${segment.id}`"
                :data-testid="`batch-history-retry-${segment.id}`"
              />
            </svg>
            <p class="meta-line batch-history-retry-rate-stack-label">
              重试分布：首次成功 {{ bh.batchHistoryRetryRateStack.firstSuccess }}
              · 重试成功 {{ bh.batchHistoryRetryRateStack.retriedSuccess }}
              · 失败 {{ bh.batchHistoryRetryRateStack.failed }}
            </p>
          </div>
          <div
            v-if="bh.batchHistoryChapterFailureHeatmap"
            class="batch-history-chapter-failure-heatmap"
            data-testid="batch-history-chapter-failure-heatmap"
          >
            <div class="batch-history-chapter-failure-grid">
              <span
                v-for="cell in bh.batchHistoryChapterFailureHeatmap.cells"
                :key="`heat-ch-${cell.chapter}`"
                class="batch-history-chapter-failure-cell"
                :class="{ 'batch-history-chapter-failure-cell--failed': cell.failed }"
                :data-testid="`batch-history-heat-ch${cell.chapter}`"
                :title="`ch${String(cell.chapter).padStart(3, '0')}`"
              />
            </div>
            <p class="meta-line batch-history-chapter-failure-heatmap-label">
              章节失败热力：{{ bh.batchHistoryChapterFailureHeatmap.failedCount }} / {{ bh.batchHistoryChapterFailureHeatmap.cells.length }}
            </p>
          </div>
          <p
            v-if="bh.batchHistoryAvgDuration != null"
            class="meta-line batch-history-avg-duration"
            data-testid="batch-history-avg-duration"
          >
            平均耗时 {{ bh.batchHistoryAvgDuration }} 分钟
          </p>
          <p
            v-if="bh.batchHistoryFailureTrend"
            class="meta-line batch-history-failure-trend"
            data-testid="batch-history-failure-trend"
          >
            失败率 {{ bh.batchHistoryFailureTrend.failurePct }}%（{{ bh.batchHistoryFailureTrend.failed }}/{{ bh.batchHistoryFailureTrend.total }}）
            · 近期趋势{{ bh.batchHistoryFailureTrend.trendLabel }}
          </p>
          </div>
          <ul
            v-if="bh.uiProfile.batch_history_weekly_summary && bh.batchHistoryWeeklySummary.length"
            class="batch-history-weekly-summary"
            data-testid="batch-history-weekly-summary"
          >
            <li
              v-for="week in bh.batchHistoryWeeklySummary"
              :key="`batch-week-${week.weekKey}`"
              class="meta-line batch-history-weekly-item"
              :data-testid="`batch-history-week-${week.weekKey}`"
            >
              {{ week.weekLabel }} · {{ week.total }} 次
              · 成功 {{ week.completed }} · 失败 {{ week.failed }}
            </li>
          </ul>
          <ul
            v-if="bh.uiProfile.batch_history_monthly_summary && bh.batchHistoryMonthlySummary.length"
            class="batch-history-monthly-summary"
            data-testid="batch-history-monthly-summary"
          >
            <li
              v-for="month in bh.batchHistoryMonthlySummary"
              :key="`batch-month-${month.monthKey}`"
              class="meta-line batch-history-monthly-item"
              :data-testid="`batch-history-month-${month.monthKey}`"
            >
              {{ month.monthLabel }} · {{ month.total }} 次
              · 成功 {{ month.completed }} · 失败 {{ month.failed }}
            </li>
          </ul>
          <div class="batch-history-actions">
            <button
              v-if="bh.uiProfile.batch_history_export"
              type="button"
              class="mini-btn pixel-border"
              data-testid="export-batch-history-btn"
              @click="bh.exportBatchHistory"
            >
              导出 JSON
            </button>
          </div>
          <label
            v-if="bh.uiProfile.batch_history_status_filter"
            class="meta-line batch-history-filter"
            data-testid="batch-history-filter-label"
          >
            状态筛选
            <select
              v-model="bh.batchHistoryStatusFilter"
              class="vol-input"
              data-testid="batch-history-status-filter"
            >
              <option value="">全部</option>
              <option
                v-for="status in bh.batchHistoryStatusOptions"
                :key="status"
                :value="status"
              >
                {{ status }}
              </option>
            </select>
          </label>
          <p
            v-if="!bh.filteredBatchHistory.length"
            class="meta-line"
            data-testid="batch-history-empty"
          >
            无匹配任务
          </p>
          <div
            v-else-if="bh.uiProfile.batch_history_date_group"
            class="batch-history-groups"
            data-testid="batch-history-date-groups"
          >
            <section
              v-for="group in bh.batchHistoryDateGroups"
              :key="`batch-date-${group.date}`"
              class="batch-history-date-group"
              :data-testid="`batch-history-date-${group.date}`"
            >
              <p class="meta-line batch-history-date-label">{{ group.date }}</p>
              <ul class="batch-history-list" data-testid="batch-history-list">
                <li
                  v-for="job in group.jobs"
                  :key="job.job_id"
                  class="batch-history-item"
                  :class="{
                    'batch-history-item--clickable': bh.uiProfile.batch_history_replay_range,
                    'batch-history-item--active': bh.highlightedBatchHistoryId === job.job_id,
                    ...bh.batchHistoryStatusClass(job),
                  }"
                  :role="bh.uiProfile.batch_history_replay_range ? 'button' : undefined"
                  :tabindex="bh.uiProfile.batch_history_replay_range ? 0 : undefined"
                  :data-testid="`batch-history-${job.job_id}`"
                  @click="bh.applyBatchHistoryRange(job)"
                  @keydown.enter="bh.applyBatchHistoryRange(job)"
                >
                  ch{{ String(job.start_chapter).padStart(3, '0') }}–ch{{ String(job.end_chapter).padStart(3, '0') }}
                  · {{ job.status }}
                  <span v-if="job.finished_at" class="meta-line">· {{ job.finished_at }}</span>
                  <span
                    v-if="bh.batchJobDurationLabel(job)"
                    class="meta-line batch-history-duration"
                    :data-testid="`batch-history-duration-${job.job_id}`"
                  >
                    · {{ bh.batchJobDurationLabel(job) }}
                  </span>
                  <span
                    v-if="bh.batchHistoryFailureReasonLabel(job)"
                    class="meta-line batch-history-failure-reason"
                    :data-testid="`batch-history-failure-reason-${job.job_id}`"
                  >
                    · {{ bh.batchHistoryFailureReasonLabel(job) }}
                  </span>
                  <button
                    v-if="bh.uiProfile.batch_history_failed_retry && String(job.status).toLowerCase() === 'failed'"
                    type="button"
                    class="mini-btn pixel-border batch-history-retry-btn"
                    :data-testid="`batch-history-retry-${job.job_id}`"
                    @click.stop="bh.retryBatchHistoryJob(job)"
                  >
                    重试
                  </button>
                </li>
              </ul>
            </section>
          </div>
          <ul v-else class="batch-history-list" data-testid="batch-history-list">
            <li
              v-for="job in bh.filteredBatchHistory"
              :key="job.job_id"
              class="batch-history-item"
              :class="{
                'batch-history-item--clickable': bh.uiProfile.batch_history_replay_range,
                'batch-history-item--active': bh.highlightedBatchHistoryId === job.job_id,
                ...bh.batchHistoryStatusClass(job),
              }"
              :role="bh.uiProfile.batch_history_replay_range ? 'button' : undefined"
              :tabindex="bh.uiProfile.batch_history_replay_range ? 0 : undefined"
              :data-testid="`batch-history-${job.job_id}`"
              @click="bh.applyBatchHistoryRange(job)"
              @keydown.enter="bh.applyBatchHistoryRange(job)"
            >
              ch{{ String(job.start_chapter).padStart(3, '0') }}–ch{{ String(job.end_chapter).padStart(3, '0') }}
              · {{ job.status }}
              <span v-if="job.finished_at" class="meta-line">· {{ job.finished_at }}</span>
              <span
                v-if="bh.batchJobDurationLabel(job)"
                class="meta-line batch-history-duration"
                :data-testid="`batch-history-duration-${job.job_id}`"
              >
                · {{ bh.batchJobDurationLabel(job) }}
              </span>
              <span
                v-if="bh.batchHistoryFailureReasonLabel(job)"
                class="meta-line batch-history-failure-reason"
                :data-testid="`batch-history-failure-reason-${job.job_id}`"
              >
                · {{ bh.batchHistoryFailureReasonLabel(job) }}
              </span>
              <button
                v-if="bh.uiProfile.batch_history_failed_retry && String(job.status).toLowerCase() === 'failed'"
                type="button"
                class="mini-btn pixel-border batch-history-retry-btn"
                :data-testid="`batch-history-retry-${job.job_id}`"
                @click.stop="bh.retryBatchHistoryJob(job)"
              >
                重试
              </button>
            </li>
          </ul>
        </div>
</template>

<script setup>
import { inject } from 'vue';
import { CREATOR_BATCH_HISTORY_KEY } from './creatorBatchHistoryKey.js';

const bh = inject(CREATOR_BATCH_HISTORY_KEY);
if (!bh) {
  throw new Error('CreatorBatchHistoryPanel requires CREATOR_BATCH_HISTORY_KEY provide');
}
</script>
<style scoped>
.batch-history-failure-reason {
  color: #a44;
}

.batch-history-success-rate-chart {
  margin: 0 0 var(--space-xs);
  color: var(--color-accent);
}

.batch-history-success-rate-chart-svg {
  width: 100%;
  max-width: 220px;
  height: 48px;
  display: block;
}

.batch-history-success-rate-chart-label {
  margin: 2px 0 0;
}

.batch-history-status-stack-chart {
  margin: 0 0 var(--space-xs);
}

.batch-history-status-stack-chart-svg {
  width: 100%;
  max-width: 220px;
  height: 14px;
  display: block;
}

.batch-history-stack-segment--completed {
  fill: rgba(80, 160, 100, 0.85);
}

.batch-history-stack-segment--failed {
  fill: rgba(180, 80, 80, 0.85);
}

.batch-history-stack-segment--running {
  fill: rgba(100, 140, 200, 0.85);
}

.batch-history-stack-segment--other {
  fill: rgba(140, 140, 140, 0.65);
}

.batch-history-status-stack-label {
  margin: 2px 0 0;
}

.batch-history-duration-distribution {
  margin: 0 0 var(--space-xs);
}

.batch-history-duration-distribution-svg {
  width: 100%;
  max-width: 220px;
  height: 40px;
  display: block;
}

.batch-history-duration-bar {
  fill: rgba(100, 140, 200, 0.75);
}

.batch-history-duration-distribution-label {
  margin: 2px 0 0;
}

.batch-history-concurrency-chart {
  margin: 0 0 var(--space-xs);
}

.batch-history-concurrency-chart-svg {
  width: 100%;
  max-width: 220px;
  height: 40px;
  display: block;
}

.batch-history-concurrency-bar {
  fill: rgba(120, 160, 120, 0.8);
}

.batch-history-concurrency-chart-label {
  margin: 2px 0 0;
}

.batch-history-queue-depth-chart {
  margin: 0 0 var(--space-xs);
}

.batch-history-queue-depth-chart-svg {
  width: 100%;
  max-width: 220px;
  height: 40px;
  display: block;
}

.batch-history-queue-depth-bar {
  fill: rgba(160, 120, 180, 0.8);
}

.batch-history-queue-depth-chart-label {
  margin: 2px 0 0;
}

.batch-history-throughput-chart {
  margin: 0 0 var(--space-xs);
}

.batch-history-throughput-chart-svg {
  width: 100%;
  max-width: 220px;
  height: 40px;
  display: block;
}

.batch-history-throughput-bar {
  fill: rgba(200, 140, 80, 0.8);
}

.batch-history-throughput-chart-label {
  margin: 2px 0 0;
}

.batch-history-cost-efficiency-chart {
  margin: 0 0 var(--space-xs);
}

.batch-history-cost-efficiency-chart-svg {
  width: 100%;
  max-width: 220px;
  height: 40px;
  display: block;
}

.batch-history-cost-efficiency-bar {
  fill: rgba(220, 160, 80, 0.85);
}

.batch-history-cost-efficiency-chart-label {
  margin: 2px 0 0;
}

.batch-history-retry-rate-stack {
  margin: 0 0 var(--space-xs);
}

.batch-history-retry-rate-stack-svg {
  width: 100%;
  max-width: 220px;
  height: 14px;
  display: block;
}

.batch-history-retry-seg--first {
  fill: rgba(100, 160, 100, 0.85);
}

.batch-history-retry-seg--retried {
  fill: rgba(100, 140, 200, 0.85);
}

.batch-history-retry-seg--failed {
  fill: rgba(200, 90, 90, 0.85);
}

.batch-history-retry-rate-stack-label {
  margin: 2px 0 0;
}

.batch-history-chapter-failure-heatmap {
  margin: 0 0 var(--space-xs);
}

.batch-history-chapter-failure-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  max-width: 220px;
}

.batch-history-chapter-failure-cell {
  width: 12px;
  height: 12px;
  background: rgba(100, 160, 100, 0.75);
  display: inline-block;
}

.batch-history-chapter-failure-cell--failed {
  background: rgba(200, 90, 90, 0.9);
}

.batch-history-chapter-failure-heatmap-label {
  margin: 2px 0 0;
}

.batch-history-ops-summary-toggle {
  margin: var(--space-xs) 0;
  width: 100%;
  text-align: left;
}

.batch-history-ops-summary-line {
  display: block;
  font-size: var(--text-md);
  opacity: 0.85;
}

.batch-history-ops-summary-body {
  margin-top: var(--space-xs);
}

.batch-history-avg-duration {
  margin: 0 0 var(--space-xs);
  color: var(--color-accent);
}

.batch-history-failure-trend {
  margin: 0 0 var(--space-xs);
  color: #a44;
}

.batch-history-monthly-summary,
.batch-history-weekly-summary {
  list-style: none;
  padding: 0;
  margin: 0 0 var(--space-xs);
}

.batch-history-success-rate {
  margin: 0 0 var(--space-xs);
  color: var(--color-accent);
}

.batch-history-budget-hint {
  margin: var(--space-xs) 0 0;
  color: var(--color-accent);
}

.batch-history-duration {
  color: var(--color-accent);
}

.batch-history-retry-btn {
  margin-left: var(--space-xs);
  font-size: var(--text-xs);
}

.batch-history-item--status-completed {
  border-left: 3px solid #4a9;
}

.batch-history-item--status-failed {
  border-left: 3px solid #c44;
}

.batch-history-item--status-running {
  border-left: 3px solid #48c;
}

.batch-history-item--running-pulse {
  animation: batch-history-running-pulse 1.4s ease-in-out infinite;
}

.batch-history-date-label {
  margin: var(--space-xs) 0 0;
  font-family: 'Press Start 2P', monospace;
  font-size: var(--text-xs);
}

.batch-history-date-group + .batch-history-date-group {
  margin-top: var(--space-xs);
}

.batch-history-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: var(--space-xs);
}

.batch-history-filter {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  margin-bottom: var(--space-xs);
}

.batch-history-panel {
  margin-top: var(--space-sm);
  padding: var(--space-xs);
}

.batch-history-list {
  list-style: none;
  padding: 0;
  margin: var(--space-xs) 0 0;
  font-size: var(--text-sm);
}

.batch-history-item {
  padding: 4px 0;
}

.batch-history-item--clickable {
  cursor: pointer;
}

.batch-history-item--clickable:hover,
.batch-history-item--active {
  background: rgba(100, 140, 200, 0.12);
}

.subsection-title {
  font-size: var(--text-sm);
  margin: var(--space-md) 0 var(--space-xs);
}

.vol-input {
  font-size: var(--text-sm);
  padding: 2px 4px;
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--color-text);
}

.vol-num { width: 3em; }

.mini-btn,
.save-btn {
  font-size: var(--text-xs);
  padding: 2px 6px;
  cursor: pointer;
}

.save-btn {
  margin-top: var(--space-xs);
}

.batch-range {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: var(--text-sm);
  margin-bottom: 6px;
}

.batch-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.advance-batch-panel {
  margin-top: var(--space-md);
  padding: var(--space-sm);
}

.batch-error {
  color: #c44;
  font-size: var(--text-sm);
  margin-top: 4px;
}

.meta-line {
  font-size: var(--text-sm);
  opacity: 0.75;
}

.mini-btn--danger {
  color: #c44;
}

.pulse-empty-guide .meta-line {
  margin: var(--space-xs) 0 var(--space-sm);
}

.companion-logic-check-write .subsection-title {
  margin-bottom: var(--space-xs);
}
</style>
