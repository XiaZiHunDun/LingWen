/**
 * useCreatorBatchHistory — Batch 历史面板逻辑（从 CreatorPage 抽出）
 */
import { computed, ref } from 'vue';
import { fetchCreatorBatchHistory, exportCreatorBatchHistory } from '../api/index.js';

const BATCH_DURATION_BUCKETS = [
  { id: 'lt1', label: '<1分', min: 0, max: 1 },
  { id: '1to5', label: '1-5分', min: 1, max: 5 },
  { id: '5to15', label: '5-15分', min: 5, max: 15 },
  { id: 'gte15', label: '15分+', min: 15, max: Number.POSITIVE_INFINITY },
];

/**
 * @param {{
 *   uiProfile: import('vue').ComputedRef<object>,
 *   batchStart: import('vue').Ref<number>,
 *   batchEnd: import('vue').Ref<number>,
 *   batchBudget: import('vue').Ref<number>,
 *   saveMessage: import('vue').Ref<string>,
 *   error: import('vue').Ref<string|null>,
 * }} deps
 */
export function useCreatorBatchHistory(deps) {
  const { uiProfile, batchStart, batchEnd, batchBudget, saveMessage, error } = deps;

const batchHistory = ref([]);
const batchHistoryStatusFilter = ref('');
const batchHistoryBudgetHint = ref('');
const batchHistoryOpsSummaryOpen = ref(false);
const highlightedBatchHistoryId = ref('');
const BATCH_STACK_STATUS_COLORS = {
  completed: 'completed',
  failed: 'failed',
  running: 'running',
  other: 'other',
};
const batchHistorySuccessRate = computed(() => {
  if (!uiProfile.value.batch_history_success_rate || !batchHistory.value.length) return null;
  const total = batchHistory.value.length;
  const completed = batchHistory.value.filter(
    (job) => String(job?.status).toLowerCase() === 'completed',
  ).length;
  return {
    total,
    completed,
    pct: Math.round((completed / total) * 100),
  };
});
const batchHistorySuccessRateChart = computed(() => {
  if (!uiProfile.value.batch_history_success_rate_chart || batchHistory.value.length < 2) return null;
  const jobs = [...batchHistory.value].sort((a, b) => {
    const ta = Date.parse(a.finished_at || a.started_at || 0);
    const tb = Date.parse(b.finished_at || b.started_at || 0);
    return ta - tb;
  });
  let completed = 0;
  const points = jobs.map((job, idx) => {
    if (String(job?.status).toLowerCase() === 'completed') completed += 1;
    return {
      index: idx,
      rate: Math.round((completed / (idx + 1)) * 100),
    };
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
const batchHistoryStatusStackChart = computed(() => {
  if (!uiProfile.value.batch_history_status_stack_chart || !batchHistory.value.length) return null;
  const counts = { completed: 0, failed: 0, running: 0, other: 0 };
  for (const job of batchHistory.value) {
    const status = String(job?.status).toLowerCase();
    if (status in counts) counts[status] += 1;
    else counts.other += 1;
  }
  const total = batchHistory.value.length;
  const width = 200;
  const height = 14;
  let x = 0;
  const segments = [];
  for (const status of ['completed', 'failed', 'running', 'other']) {
    const count = counts[status];
    if (!count) continue;
    const segmentWidth = (count / total) * width;
    segments.push({
      status: BATCH_STACK_STATUS_COLORS[status],
      count,
      x,
      width: segmentWidth,
    });
    x += segmentWidth;
  }
  return { segments, width, height, total };
});
const batchHistoryDurationDistribution = computed(() => {
  if (!uiProfile.value.batch_history_duration_distribution || !batchHistory.value.length) return null;
  const buckets = BATCH_DURATION_BUCKETS.map((bucket) => ({ ...bucket, count: 0 }));
  for (const job of batchHistory.value) {
    const minutes = batchJobDurationMinutes(job);
    if (minutes == null) continue;
    const bucket = buckets.find(
      (row) => minutes >= row.min && minutes < row.max,
    ) || buckets[buckets.length - 1];
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
const batchHistoryConcurrencyChart = computed(() => {
  if (!uiProfile.value.batch_history_concurrency_chart || !batchHistory.value.length) return null;
  const ranges = batchHistory.value
    .map((job) => {
      const start = job?.started_at ? Date.parse(job.started_at) : Number.NaN;
      let end = job?.finished_at ? Date.parse(job.finished_at) : Number.NaN;
      if (!Number.isFinite(start)) return null;
      if (!Number.isFinite(end) || end < start) end = Date.now();
      return { start, end };
    })
    .filter(Boolean);
  if (!ranges.length) return null;
  const minStart = Math.min(...ranges.map((row) => row.start));
  const maxEnd = Math.max(...ranges.map((row) => row.end));
  const span = maxEnd - minStart;
  if (span <= 0) return null;
  const events = [];
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
  const buckets = Array.from({ length: bucketCount }, (_, idx) => ({
    id: `b${idx}`,
    count: 0,
  }));
  for (let idx = 0; idx < bucketCount; idx += 1) {
    const bucketStart = minStart + (span * idx) / bucketCount;
    const bucketEnd = minStart + (span * (idx + 1)) / bucketCount;
    buckets[idx].count = ranges.filter(
      (row) => row.start < bucketEnd && row.end > bucketStart,
    ).length;
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
const batchHistoryQueueDepthChart = computed(() => {
  if (!uiProfile.value.batch_history_queue_depth_chart || !batchHistory.value.length) return null;
  const waits = batchHistory.value
    .map((job) => {
      const queued = Date.parse(job?.queued_at || job?.created_at || '');
      const started = Date.parse(job?.started_at || '');
      if (!Number.isFinite(queued)) return null;
      const end = Number.isFinite(started) && started > queued ? started : queued;
      if (end <= queued) return null;
      return { start: queued, end };
    })
    .filter(Boolean);
  if (!waits.length) return null;
  const events = [];
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
    buckets[idx].count = waits.filter(
      (row) => row.start < bucketEnd && row.end > bucketStart,
    ).length;
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
const batchHistoryThroughputChart = computed(() => {
  if (!uiProfile.value.batch_history_throughput_chart || !batchHistory.value.length) return null;
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
    .filter(Boolean);
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
  return {
    bars,
    width,
    height,
    peak: peak.toFixed(2),
    avg: avg.toFixed(2),
  };
});
const batchHistoryCostEfficiencyChart = computed(() => {
  if (!uiProfile.value.batch_history_cost_efficiency_chart || !batchHistory.value.length) return null;
  const rates = batchHistory.value
    .map((job) => {
      const budget = Number(job.budget_usd);
      if (!Number.isFinite(budget) || budget <= 0) return null;
      const start = Number(job.start_chapter) || 0;
      const end = Number(job.end_chapter) || start;
      const chapters = Math.max(1, end - start + 1);
      return {
        id: String(job.job_id || `${start}-${end}`),
        rate: budget / chapters,
      };
    })
    .filter(Boolean);
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
const batchHistoryRetryRateStack = computed(() => {
  if (!uiProfile.value.batch_history_retry_rate_stack || !batchHistory.value.length) return null;
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
  const segments = [];
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
const batchHistoryChapterFailureHeatmap = computed(() => {
  if (!uiProfile.value.batch_history_chapter_failure_heatmap || !batchHistory.value.length) return null;
  const chapterMap = new Map();
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
const batchHistoryAvgDuration = computed(() => {
  if (!uiProfile.value.batch_history_avg_duration || !batchHistory.value.length) return null;
  const durations = batchHistory.value
    .map((job) => batchJobDurationMinutes(job))
    .filter((minutes) => minutes != null);
  if (!durations.length) return null;
  return Math.round(durations.reduce((sum, minutes) => sum + minutes, 0) / durations.length);
});
const batchHistoryFailureTrend = computed(() => {
  if (!uiProfile.value.batch_history_failure_trend || batchHistory.value.length < 2) return null;
  const jobs = batchHistory.value;
  const total = jobs.length;
  const failed = jobs.filter((job) => String(job?.status).toLowerCase() === 'failed').length;
  const mid = Math.ceil(total / 2);
  const recent = jobs.slice(0, mid);
  const older = jobs.slice(mid);
  const rate = (items) => (
    items.filter((job) => String(job?.status).toLowerCase() === 'failed').length / items.length
  );
  const recentRate = rate(recent);
  const olderRate = older.length ? rate(older) : recentRate;
  let trendLabel = '持平';
  if (recentRate > olderRate + 0.01) trendLabel = '上升';
  else if (recentRate < olderRate - 0.01) trendLabel = '下降';
  return {
    total,
    failed,
    failurePct: Math.round((failed / total) * 100),
    trendLabel,
  };
});
const batchHistoryOpsSummaryLine = computed(() => {
  if (!uiProfile.value.batch_history_ops_summary || !batchHistory.value.length) return '';
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
const batchHistoryWeeklySummary = computed(() => {
  if (!uiProfile.value.batch_history_weekly_summary || !batchHistory.value.length) return [];
  const groups = new Map();
  for (const job of batchHistory.value) {
    const weekKey = batchJobIsoWeekKey(job);
    if (!groups.has(weekKey)) {
      groups.set(weekKey, { weekKey, weekLabel: weekKey, total: 0, completed: 0, failed: 0 });
    }
    const row = groups.get(weekKey);
    row.total += 1;
    const status = String(job?.status).toLowerCase();
    if (status === 'completed') row.completed += 1;
    if (status === 'failed') row.failed += 1;
  }
  return Array.from(groups.values()).sort((a, b) => b.weekKey.localeCompare(a.weekKey));
});
const batchHistoryMonthlySummary = computed(() => {
  if (!uiProfile.value.batch_history_monthly_summary || !batchHistory.value.length) return [];
  const groups = new Map();
  for (const job of batchHistory.value) {
    const monthKey = batchJobMonthKey(job);
    if (!groups.has(monthKey)) {
      groups.set(monthKey, { monthKey, monthLabel: monthKey, total: 0, completed: 0, failed: 0 });
    }
    const row = groups.get(monthKey);
    row.total += 1;
    const status = String(job?.status).toLowerCase();
    if (status === 'completed') row.completed += 1;
    if (status === 'failed') row.failed += 1;
  }
  return Array.from(groups.values()).sort((a, b) => b.monthKey.localeCompare(a.monthKey));
});
const batchHistoryStatusOptions = computed(() => {
  const statuses = new Set();
  for (const job of batchHistory.value) {
    if (job?.status) statuses.add(String(job.status));
  }
  return Array.from(statuses).sort();
});
const filteredBatchHistory = computed(() => {
  if (!uiProfile.value.batch_history_status_filter || !batchHistoryStatusFilter.value) {
    return batchHistory.value;
  }
  const status = batchHistoryStatusFilter.value;
  return batchHistory.value.filter((job) => String(job.status) === status);
});
const batchHistoryDateGroups = computed(() => {
  const jobs = filteredBatchHistory.value;
  if (!uiProfile.value.batch_history_date_group) {
    return [{ date: '', jobs }];
  }
  const groups = new Map();
  for (const job of jobs) {
    const raw = job.finished_at || job.started_at || '未知日期';
    const date = String(raw).slice(0, 10);
    if (!groups.has(date)) groups.set(date, []);
    groups.get(date).push(job);
  }
  return Array.from(groups.entries()).map(([date, groupedJobs]) => ({
    date,
    jobs: groupedJobs,
  }));
});
async function loadBatchHistory() {
  if (!uiProfile.value.batch_history_panel) {
    batchHistory.value = [];
    return;
  }
  try {
    const payload = await fetchCreatorBatchHistory();
    batchHistory.value = payload?.jobs || [];
  } catch {
    batchHistory.value = [];
  }
}
function batchJobDurationMinutes(job) {
  const start = job?.started_at ? Date.parse(job.started_at) : Number.NaN;
  const end = job?.finished_at ? Date.parse(job.finished_at) : Number.NaN;
  if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) return null;
  return Math.round((end - start) / 60000);
}
function batchJobIsoWeekKey(job) {
  const raw = job?.finished_at || job?.started_at;
  if (!raw) return '未知周';
  const date = new Date(`${String(raw).slice(0, 10)}T00:00:00Z`);
  if (Number.isNaN(date.getTime())) return '未知周';
  const day = (date.getUTCDay() + 6) % 7;
  date.setUTCDate(date.getUTCDate() - day + 3);
  const week1 = new Date(Date.UTC(date.getUTCFullYear(), 0, 4));
  const weekNum = 1 + Math.round(
    ((date.getTime() - week1.getTime()) / 86400000 - 3 + ((week1.getUTCDay() + 6) % 7)) / 7,
  );
  return `${date.getUTCFullYear()}-W${String(weekNum).padStart(2, '0')}`;
}
function batchJobMonthKey(job) {
  const raw = job?.finished_at || job?.started_at;
  if (!raw) return '未知月';
  const monthKey = String(raw).slice(0, 7);
  return /^\d{4}-\d{2}$/.test(monthKey) ? monthKey : '未知月';
}
function batchJobDurationLabel(job) {
  if (!uiProfile.value.batch_history_duration || !job) return '';
  const minutes = batchJobDurationMinutes(job);
  if (minutes == null) return '';
  if (minutes < 1) return '耗时 <1 分钟';
  return `耗时 ${minutes} 分钟`;
}
function batchHistoryFailureReasonLabel(job) {
  if (!uiProfile.value.batch_history_failure_reason_label || !job) return '';
  if (String(job?.status).toLowerCase() !== 'failed') return '';
  return job.failure_reason || job.error || '';
}
function applyBatchHistoryBudgetFromJob(job) {
  batchHistoryBudgetHint.value = '';
  if (!uiProfile.value.batch_history_budget_hint || !job) return;
  if (job.budget_usd == null || Number.isNaN(Number(job.budget_usd))) return;
  batchBudget.value = Number(job.budget_usd);
  batchHistoryBudgetHint.value = `已从历史任务回填预算 $${batchBudget.value}`;
}
function applyBatchHistoryRange(job) {
  if (!uiProfile.value.batch_history_replay_range || !job) return;
  batchStart.value = Number(job.start_chapter) || 1;
  batchEnd.value = Number(job.end_chapter) || batchStart.value;
  highlightedBatchHistoryId.value = job.job_id || '';
  applyBatchHistoryBudgetFromJob(job);
  saveMessage.value = `已填入 batch 范围 ch${String(batchStart.value).padStart(3, '0')}–ch${String(batchEnd.value).padStart(3, '0')}`;
}
function retryBatchHistoryJob(job) {
  if (!uiProfile.value.batch_history_failed_retry || !job) return;
  if (String(job.status).toLowerCase() !== 'failed') return;
  batchStart.value = Number(job.start_chapter) || 1;
  batchEnd.value = Number(job.end_chapter) || batchStart.value;
  applyBatchHistoryBudgetFromJob(job);
  highlightedBatchHistoryId.value = job.job_id || '';
  saveMessage.value = `已填入失败任务范围 ch${String(batchStart.value).padStart(3, '0')}–ch${String(batchEnd.value).padStart(3, '0')}，可重新运行 batch`;
}
function batchHistoryStatusClass(job) {
  if (!job?.status) return {};
  const status = String(job.status).toLowerCase();
  const classes = {};
  if (uiProfile.value.batch_history_status_color) {
    classes[`batch-history-item--status-${status}`] = true;
  }
  if (uiProfile.value.batch_history_running_pulse && status === 'running') {
    classes['batch-history-item--running-pulse'] = true;
  }
  return classes;
}
function downloadJsonExport(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
async function exportBatchHistory() {
  if (!uiProfile.value.batch_history_export) return;
  try {
    const payload = await exportCreatorBatchHistory();
    const jobs = payload?.jobs?.length
      ? payload.jobs
      : filteredBatchHistory.value;
    downloadJsonExport('creator-batch-history.json', {
      schema_version: payload?.schema_version || '1',
      count: jobs.length,
      jobs,
    });
    saveMessage.value = `已导出 ${jobs.length} 条 batch 历史`;
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
}
function toggleBatchHistoryOpsSummary() {
  batchHistoryOpsSummaryOpen.value = !batchHistoryOpsSummaryOpen.value;
}

  const panelContext = {
    uiProfile,
    batchHistory,
    batchHistoryBudgetHint,
    batchHistoryOpsSummaryOpen,
    toggleBatchHistoryOpsSummary,
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
    batchHistoryWeeklySummary,
    batchHistoryMonthlySummary,
    exportBatchHistory,
    batchHistoryStatusFilter,
    batchHistoryStatusOptions,
    filteredBatchHistory,
    batchHistoryDateGroups,
    highlightedBatchHistoryId,
    batchHistoryStatusClass,
    applyBatchHistoryRange,
    batchJobDurationLabel,
    batchHistoryFailureReasonLabel,
    retryBatchHistoryJob,
  };

  return {
    panelContext,
    batchHistoryBudgetHint,
    loadBatchHistory,
  };
}
