/**
 * useBatchDiff — 状态/diff/图表统计
 *
 * Phase 19 Task 4：从 useCreatorBatchHistory.js 拆出（完整实现）。
 * 负责: 各种 computed 图表/统计 (successRate / statusStack / durationDistribution /
 *       concurrencyChart / queueDepthChart / throughputChart / costEfficiency /
 *       retryRateStack / chapterFailureHeatmap / avgDuration / failureTrend) +
 *       opsSummary 状态 + statusClass/failureReasonLabel helpers。
 */
import { computed, ref } from 'vue';
import type { ComputedRef, Ref } from 'vue';
import type { BatchJob } from './useBatchList';

const BATCH_STACK_STATUS_COLORS: Record<string, string> = {
  completed: 'completed',
  failed: 'failed',
  running: 'running',
  other: 'other',
};

export interface BatchDiffDeps {
  uiProfile: ComputedRef<Record<string, unknown>>;
  batchHistory: Ref<BatchJob[]>;
  batchJobDurationMinutes: (job: BatchJob) => number | null;
}

interface ChartWithSegments { segments: Array<unknown>; [k: string]: unknown }
interface ChartWithBars { bars: Array<unknown>; [k: string]: unknown }
interface ChartWithPeak { peak: number; bars?: Array<unknown>; [k: string]: unknown }
interface ChartWithCells { cells: Array<unknown>; [k: string]: unknown }

export interface BatchDiffReturn {
  batchHistoryOpsSummaryOpen: Ref<boolean>;
  batchHistoryOpsSummaryLine: ComputedRef<string>;
  batchHistorySuccessRate: ComputedRef<{ total: number; completed: number; pct: number } | null>;
  batchHistorySuccessRateChart: ComputedRef<{ polyline: string; [k: string]: unknown } | null>;
  batchHistoryStatusStackChart: ComputedRef<ChartWithSegments | null>;
  batchHistoryDurationDistribution: ComputedRef<ChartWithBars | null>;
  batchHistoryConcurrencyChart: ComputedRef<ChartWithPeak | null>;
  batchHistoryQueueDepthChart: ComputedRef<ChartWithPeak | null>;
  batchHistoryThroughputChart: ComputedRef<ChartWithBars | null>;
  batchHistoryCostEfficiencyChart: ComputedRef<ChartWithBars | null>;
  batchHistoryRetryRateStack: ComputedRef<ChartWithSegments | null>;
  batchHistoryChapterFailureHeatmap: ComputedRef<ChartWithCells | null>;
  batchHistoryAvgDuration: ComputedRef<number | null>;
  batchHistoryFailureTrend: ComputedRef<Record<string, unknown> | null>;
  toggleBatchHistoryOpsSummary: () => void;
  batchHistoryStatusClass: (job: BatchJob | null | undefined) => Record<string, boolean>;
  batchHistoryFailureReasonLabel: (job: BatchJob | null | undefined) => string;
}

export function useBatchDiff(deps: BatchDiffDeps): BatchDiffReturn {
  const { uiProfile, batchHistory, batchJobDurationMinutes } = deps;

  const batchHistoryOpsSummaryOpen = ref(false);

  const batchHistorySuccessRate = computed(() => {
    if (!(uiProfile.value as { batch_history_success_rate?: boolean }).batch_history_success_rate || !batchHistory.value.length) return null;
    const total = batchHistory.value.length;
    const completed = batchHistory.value.filter(
      (job) => String(job?.status).toLowerCase() === 'completed',
    ).length;
    return { total, completed, pct: Math.round((completed / total) * 100) };
  });

  const batchHistorySuccessRateChart = computed<{ polyline: string; [k: string]: unknown } | null>(() => {
    if (!(uiProfile.value as { batch_history_success_rate_chart?: boolean }).batch_history_success_rate_chart || batchHistory.value.length < 2) return null;
    const jobs = [...batchHistory.value].sort((a, b) => {
      const ta = Date.parse(a.finished_at || a.started_at || '');
      const tb = Date.parse(b.finished_at || b.started_at || '');
      return ta - tb;
    });
    let completed = 0;
    const points = jobs.map((job, idx) => {
      if (String(job?.status).toLowerCase() === 'completed') completed += 1;
      return { index: idx, rate: Math.round((completed / (idx + 1)) * 100) };
    });
    const width = 200;
    const height = 48;
    const maxX = Math.max(points.length - 1, 1);
    const polyline = points.map((point, idx) => {
      const x = (idx / maxX) * width;
      const y = height - (point.rate / 100) * height;
      return `${x},${y}`;
    }).join(' ');
    return { points, polyline, width, height };
  });

  const batchHistoryStatusStackChart = computed<ChartWithSegments | null>(() => {
    if (!(uiProfile.value as { batch_history_status_stack_chart?: boolean }).batch_history_status_stack_chart || !batchHistory.value.length) return null;
    const counts: Record<string, number> = { completed: 0, failed: 0, running: 0, other: 0 };
    for (const job of batchHistory.value) {
      const status = String(job?.status).toLowerCase();
      if (status in counts) counts[status] += 1;
      else counts.other += 1;
    }
    const total = batchHistory.value.length;
    const width = 200;
    const height = 14;
    let x = 0;
    const segments: Array<{ status: string; count: number; x: number; width: number }> = [];
    for (const status of ['completed', 'failed', 'running', 'other']) {
      const count = counts[status];
      if (!count) continue;
      const segmentWidth = (count / total) * width;
      segments.push({ status: BATCH_STACK_STATUS_COLORS[status], count, x, width: segmentWidth });
      x += segmentWidth;
    }
    return { segments, width, height, total };
  });

  const batchHistoryDurationDistribution = computed<ChartWithBars | null>(() => {
    if (!(uiProfile.value as { batch_history_duration_distribution?: boolean }).batch_history_duration_distribution || !batchHistory.value.length) return null;
    const buckets = [
      { id: 'lt1', label: '<1分', min: 0, max: 1 },
      { id: '1to5', label: '1-5分', min: 1, max: 5 },
      { id: '5to15', label: '5-15分', min: 5, max: 15 },
      { id: 'gte15', label: '15分+', min: 15, max: Number.POSITIVE_INFINITY },
    ].map((bucket) => ({ ...bucket, count: 0 }));
    for (const job of batchHistory.value) {
      const minutes = batchJobDurationMinutes(job);
      if (minutes == null) continue;
      const bucket = buckets.find((row) => minutes >= row.min && minutes < row.max) || buckets[buckets.length - 1];
      bucket.count += 1;
    }
    const measured = buckets.reduce((sum, row) => sum + row.count, 0);
    if (!measured) return null;
    const max = Math.max(...buckets.map((row) => row.count), 1);
    const width = 200;
    const height = 40;
    const slot = width / buckets.length;
    const bars = buckets.map((row, idx) => {
      const barHeight = (row.count / max) * (height - 8);
      return {
        ...row,
        x: idx * slot + 2,
        y: height - barHeight,
        barWidth: slot - 4,
        barHeight,
      };
    });
    return { bars, width, height, measured };
  });

  const batchHistoryConcurrencyChart = computed<ChartWithPeak | null>(() => {
    if (!(uiProfile.value as { batch_history_concurrency_chart?: boolean }).batch_history_concurrency_chart || !batchHistory.value.length) return null;
    const ranges = batchHistory.value
      .map((job) => {
        const start = job?.started_at ? Date.parse(job.started_at) : Number.NaN;
        let end = job?.finished_at ? Date.parse(job.finished_at) : Number.NaN;
        if (!Number.isFinite(start)) return null;
        if (!Number.isFinite(end) || end < start) end = Date.now();
        return { start, end };
      })
      .filter((r): r is { start: number; end: number } => r != null);
    if (!ranges.length) return null;
    const minStart = Math.min(...ranges.map((row) => row.start));
    const maxEnd = Math.max(...ranges.map((row) => row.end));
    const span = maxEnd - minStart;
    if (span <= 0) return null;
    const events: Array<{ t: number; delta: number }> = [];
    for (const row of ranges) {
      events.push({ t: row.start, delta: 1 });
      events.push({ t: row.end, delta: -1 });
    }
    events.sort((a, b) => a.t - b.t || a.delta - b.delta);
    let current = 0;
    let peak = 0;
    for (const event of events) {
      current += event.delta;
      peak = Math.max(peak, current);
    }
    const bucketCount = Math.min(8, Math.max(4, ranges.length));
    const buckets = Array.from({ length: bucketCount }, (_, idx) => ({ id: `b${idx}`, count: 0 }));
    for (let idx = 0; idx < bucketCount; idx += 1) {
      const bucketStart = minStart + (span * idx) / bucketCount;
      const bucketEnd = minStart + (span * (idx + 1)) / bucketCount;
      buckets[idx].count = ranges.filter((row) => row.start < bucketEnd && row.end > bucketStart).length;
    }
    const max = Math.max(...buckets.map((row) => row.count), 1);
    const width = 200;
    const height = 40;
    const slot = width / bucketCount;
    const bars = buckets.map((row, idx) => {
      const barHeight = (row.count / max) * (height - 8);
      return {
        ...row,
        x: idx * slot + 2,
        y: height - barHeight,
        barWidth: slot - 4,
        barHeight,
      };
    });
    return { bars, width, height, peak };
  });

  const batchHistoryQueueDepthChart = computed<ChartWithPeak | null>(() => {
    if (!(uiProfile.value as { batch_history_queue_depth_chart?: boolean }).batch_history_queue_depth_chart || !batchHistory.value.length) return null;
    const waits = batchHistory.value
      .map((job) => {
        const queued = Date.parse(job?.queued_at || job?.created_at || '');
        const started = Date.parse(job?.started_at || '');
        if (!Number.isFinite(queued)) return null;
        const end = Number.isFinite(started) && started > queued ? started : queued;
        if (end <= queued) return null;
        return { start: queued, end };
      })
      .filter((w): w is { start: number; end: number } => w != null);
    if (!waits.length) return null;
    const events: Array<{ t: number; delta: number }> = [];
    for (const row of waits) {
      events.push({ t: row.start, delta: 1 });
      events.push({ t: row.end, delta: -1 });
    }
    events.sort((a, b) => a.t - b.t || a.delta - b.delta);
    let current = 0;
    let peak = 0;
    for (const event of events) {
      current += event.delta;
      peak = Math.max(peak, current);
    }
    const minStart = Math.min(...waits.map((row) => row.start));
    const maxEnd = Math.max(...waits.map((row) => row.end));
    const span = maxEnd - minStart;
    if (span <= 0) return { peak, bars: [], width: 200, height: 40 };
    const bucketCount = Math.min(8, Math.max(4, waits.length));
    const buckets = Array.from({ length: bucketCount }, (_, idx) => ({ id: `q${idx}`, count: 0 }));
    for (let idx = 0; idx < bucketCount; idx += 1) {
      const bucketStart = minStart + (span * idx) / bucketCount;
      const bucketEnd = minStart + (span * (idx + 1)) / bucketCount;
      buckets[idx].count = waits.filter((row) => row.start < bucketEnd && row.end > bucketStart).length;
    }
    const max = Math.max(...buckets.map((row) => row.count), 1);
    const width = 200;
    const height = 40;
    const slot = width / bucketCount;
    const bars = buckets.map((row, idx) => {
      const barHeight = (row.count / max) * (height - 8);
      return {
        ...row,
        x: idx * slot + 2,
        y: height - barHeight,
        barWidth: slot - 4,
        barHeight,
      };
    });
    return { bars, width, height, peak };
  });

  const batchHistoryThroughputChart = computed<ChartWithBars | null>(() => {
    if (!(uiProfile.value as { batch_history_throughput_chart?: boolean }).batch_history_throughput_chart || !batchHistory.value.length) return null;
    const rates = batchHistory.value
      .map((job) => {
        const minutes = batchJobDurationMinutes(job);
        if (minutes == null || minutes < 1) return null;
        const start = Number(job.start_chapter) || 0;
        const end = Number(job.end_chapter) || start;
        const chapters = Math.max(1, end - start + 1);
        return {
          id: String(job.job_id || `${start}-${end}`),
          rate: chapters / minutes,
          chapters,
          minutes,
        };
      })
      .filter((r): r is { id: string; rate: number; chapters: number; minutes: number } => r != null);
    if (!rates.length) return null;
    const peak = Math.max(...rates.map((row) => row.rate), 0.1);
    const avg = rates.reduce((sum, row) => sum + row.rate, 0) / rates.length;
    const width = 200;
    const height = 40;
    const shown = rates.slice(0, 8);
    const slot = width / shown.length;
    const bars = shown.map((row, idx) => {
      const barHeight = (row.rate / peak) * (height - 8);
      return {
        ...row,
        x: idx * slot + 2,
        y: height - barHeight,
        barWidth: slot - 4,
        barHeight,
      };
    });
    return { bars, width, height, peak: peak.toFixed(2), avg: avg.toFixed(2) };
  });

  const batchHistoryCostEfficiencyChart = computed<ChartWithBars | null>(() => {
    if (!(uiProfile.value as { batch_history_cost_efficiency_chart?: boolean }).batch_history_cost_efficiency_chart || !batchHistory.value.length) return null;
    const rates = batchHistory.value
      .map((job) => {
        const budget = Number(job.budget_usd);
        if (!Number.isFinite(budget) || budget <= 0) return null;
        const start = Number(job.start_chapter) || 0;
        const end = Number(job.end_chapter) || start;
        const chapters = Math.max(1, end - start + 1);
        return { id: String(job.job_id || `${start}-${end}`), rate: budget / chapters };
      })
      .filter((r): r is { id: string; rate: number } => r != null);
    if (!rates.length) return null;
    const peak = Math.max(...rates.map((row) => row.rate), 0.01);
    const avg = rates.reduce((sum, row) => sum + row.rate, 0) / rates.length;
    const width = 200;
    const height = 40;
    const shown = rates.slice(0, 8);
    const slot = width / shown.length;
    const bars = shown.map((row, idx) => {
      const barHeight = (row.rate / peak) * (height - 8);
      return {
        ...row,
        x: idx * slot + 2,
        y: height - barHeight,
        barWidth: slot - 4,
        barHeight,
      };
    });
    return { bars, width, height, avg: avg.toFixed(3) };
  });

  const batchHistoryRetryRateStack = computed<ChartWithSegments | null>(() => {
    if (!(uiProfile.value as { batch_history_retry_rate_stack?: boolean }).batch_history_retry_rate_stack || !batchHistory.value.length) return null;
    let firstSuccess = 0;
    let retriedSuccess = 0;
    let failed = 0;
    for (const job of batchHistory.value) {
      const status = String(job?.status).toLowerCase();
      const retries = Number(job?.retry_count) || 0;
      if (status === 'completed') {
        if (retries > 0) retriedSuccess += 1;
        else firstSuccess += 1;
      } else if (status === 'failed') {
        failed += 1;
      }
    }
    const total = firstSuccess + retriedSuccess + failed;
    if (!total) return null;
    const width = 200;
    const height = 14;
    const segments: Array<{ id: string; count: number; x: number; width: number }> = [];
    let x = 0;
    for (const segment of [
      { id: 'first', count: firstSuccess },
      { id: 'retried', count: retriedSuccess },
      { id: 'failed', count: failed },
    ]) {
      if (!segment.count) continue;
      const segmentWidth = (segment.count / total) * width;
      segments.push({ ...segment, x, width: segmentWidth });
      x += segmentWidth;
    }
    return { segments, width, height, firstSuccess, retriedSuccess, failed, total };
  });

  const batchHistoryChapterFailureHeatmap = computed<ChartWithCells | null>(() => {
    if (!(uiProfile.value as { batch_history_chapter_failure_heatmap?: boolean }).batch_history_chapter_failure_heatmap || !batchHistory.value.length) return null;
    const chapterMap = new Map<number, boolean>();
    for (const job of batchHistory.value) {
      const start = Number(job.start_chapter) || 1;
      const end = Number(job.end_chapter) || start;
      const failed = String(job?.status).toLowerCase() === 'failed';
      for (let chapter = start; chapter <= end; chapter += 1) {
        chapterMap.set(chapter, failed);
      }
    }
    const cells = [...chapterMap.entries()]
      .sort((a, b) => a[0] - b[0])
      .map(([chapter, failed]) => ({ chapter, failed }));
    if (!cells.length) return null;
    const failedCount = cells.filter((cell) => cell.failed).length;
    return { cells, failedCount };
  });

  const batchHistoryAvgDuration = computed<number | null>(() => {
    if (!(uiProfile.value as { batch_history_avg_duration?: boolean }).batch_history_avg_duration || !batchHistory.value.length) return null;
    const durations = batchHistory.value
      .map((job) => batchJobDurationMinutes(job))
      .filter((minutes): minutes is number => minutes != null);
    if (!durations.length) return null;
    return Math.round(durations.reduce((sum, minutes) => sum + minutes, 0) / durations.length);
  });

  const batchHistoryFailureTrend = computed<Record<string, unknown> | null>(() => {
    if (!(uiProfile.value as { batch_history_failure_trend?: boolean }).batch_history_failure_trend || batchHistory.value.length < 2) return null;
    const jobs = batchHistory.value;
    const total = jobs.length;
    const failed = jobs.filter((job) => String(job?.status).toLowerCase() === 'failed').length;
    const mid = Math.ceil(total / 2);
    const recent = jobs.slice(0, mid);
    const older = jobs.slice(mid);
    const rate = (items: BatchJob[]) => (
      items.filter((job) => String(job?.status).toLowerCase() === 'failed').length / items.length
    );
    const recentRate = rate(recent);
    const olderRate = older.length ? rate(older) : recentRate;
    let trendLabel = '持平';
    if (recentRate > olderRate + 0.01) trendLabel = '上升';
    else if (recentRate < olderRate - 0.01) trendLabel = '下降';
    return { total, failed, failurePct: Math.round((failed / total) * 100), trendLabel };
  });

  const batchHistoryOpsSummaryLine = computed<string>(() => {
    if (!(uiProfile.value as { batch_history_ops_summary?: boolean }).batch_history_ops_summary || !batchHistory.value.length) return '';
    const total = batchHistory.value.length;
    const completed = batchHistory.value.filter(
      (job) => String(job?.status).toLowerCase() === 'completed',
    ).length;
    const pct = Math.round((completed / total) * 100);
    const parts = [`${total} 任务`, `成功率 ${pct}%`];
    if (batchHistoryAvgDuration.value != null) {
      parts.push(`均时 ${batchHistoryAvgDuration.value} 分`);
    }
    return ` · ${parts.join(' · ')}`;
  });

  function toggleBatchHistoryOpsSummary(): void {
    batchHistoryOpsSummaryOpen.value = !batchHistoryOpsSummaryOpen.value;
  }

  function batchHistoryStatusClass(job: BatchJob | null | undefined): Record<string, boolean> {
    if (!job?.status) return {};
    const status = String(job.status).toLowerCase();
    const classes: Record<string, boolean> = {};
    if ((uiProfile.value as { batch_history_status_color?: boolean }).batch_history_status_color) {
      classes[`batch-history-item--status-${status}`] = true;
    }
    if ((uiProfile.value as { batch_history_running_pulse?: boolean }).batch_history_running_pulse && status === 'running') {
      classes['batch-history-item--running-pulse'] = true;
    }
    return classes;
  }

  function batchHistoryFailureReasonLabel(job: BatchJob | null | undefined): string {
    if (!(uiProfile.value as { batch_history_failure_reason_label?: boolean }).batch_history_failure_reason_label || !job) return '';
    if (String(job?.status).toLowerCase() !== 'failed') return '';
    return job.failure_reason || job.error || '';
  }

  return {
    batchHistoryOpsSummaryOpen,
    batchHistoryOpsSummaryLine,
    batchHistorySuccessRate,
    batchHistorySuccessRateChart,
    batchHistoryStatusStackChart,
    batchHistoryDurationDistribution,
    batchHistoryConcurrencyChart,
    batchHistoryQueueDepthChart,
    batchHistoryThroughputChart,
    batchHistoryCostEfficiencyChart,
    batchHistoryRetryRateStack,
    batchHistoryChapterFailureHeatmap,
    batchHistoryAvgDuration,
    batchHistoryFailureTrend,
    toggleBatchHistoryOpsSummary,
    batchHistoryStatusClass,
    batchHistoryFailureReasonLabel,
  };
}