/**
 * Today hub — aggregate task-oriented snapshot from existing APIs.
 */
import { ref } from 'vue';
import {
  fetchCreatorOnboarding,
  fetchCreatorOverview,
  fetchPendingDecisions,
  fetchRippleStats,
  fetchStudioActiveBatchJob,
  fetchStudioQuality,
  fetchStudioQualityReport,
  fetchStudioSummary,
} from '../api/index.js';
import { resolveTodayPrimaryAction } from '../utils/creationModeHint.js';
import { buildTodaySecondaryLinks } from '../utils/todaySecondaryLinks.js';

function pendingRippleCount(stats) {
  if (!stats?.by_status) return 0;
  return Number(stats.by_status.pending ?? stats.by_status.PENDING ?? 0) || 0;
}

async function loadTodaySnapshot(options = {}) {
  const isReviewer = Boolean(options.isReviewer);
  const [
    summary,
    creator,
    pending,
    rippleStats,
    quality,
    qualityReport,
    batchJob,
    onboarding,
  ] = await Promise.all([
    fetchStudioSummary().catch(() => null),
    fetchCreatorOverview().catch(() => null),
    fetchPendingDecisions().catch(() => []),
    fetchRippleStats().catch(() => null),
    fetchStudioQuality().catch(() => null),
    fetchStudioQualityReport().catch(() => null),
    fetchStudioActiveBatchJob().catch(() => null),
    fetchCreatorOnboarding().catch(() => null),
  ]);

  const creationMode = creator?.creation_mode || summary?.creation_mode || 'companion';
  const projectName = creator?.name || summary?.name || summary?.slug || '当前项目';
  const chaptersWritten = quality?.chapters_written ?? creator?.chapters_written ?? 0;
  const maxChapter = quality?.max_chapter ?? creator?.max_chapter ?? 0;
  const coveragePct = quality?.coverage_pct ?? creator?.coverage_pct ?? 0;
  const pendingDecisions = Array.isArray(pending) ? pending.length : 0;
  const pendingRipples = pendingRippleCount(rippleStats);
  const batchActive = Boolean(batchJob?.active || batchJob?.job_id);
  const wizardProgressPct = onboarding?.progress_pct ?? 100;
  const p0Count = qualityReport?.p0 ?? creator?.p0_count ?? 0;

  const primaryAction = resolveTodayPrimaryAction({
    creationMode,
    pendingDecisions,
    pendingRipples,
    batchActive,
    wizardProgressPct,
    chaptersWritten,
    coveragePct,
    alertCount: creator?.alert_count ?? 0,
    isReviewer,
  });

  const todoCards = [
    {
      id: 'decisions',
      label: '待决策',
      value: pendingDecisions,
      nav: 'inbox',
      tab: 'decisions',
      hint: pendingDecisions ? '需要人工确认' : '暂无',
    },
    {
      id: 'ripples',
      label: '一致性变更',
      value: pendingRipples,
      nav: 'inbox',
      tab: 'ripples',
      hint: pendingRipples ? '待审阅 apply/reject' : '暂无',
    },
    {
      id: 'p0',
      label: '质检 P0',
      value: p0Count,
      nav: 'produce',
      tab: 'studio',
      hint: p0Count ? '建议先处理' : '通过',
    },
    {
      id: 'alerts',
      label: '脉络预警',
      value: creator?.alert_count ?? 0,
      nav: 'creator',
      hint: (creator?.alert_count ?? 0) > 0 ? '查看偏离' : '正常',
    },
  ].filter((card) => !isReviewer || ['decisions', 'ripples'].includes(card.id));

  const secondaryLinks = buildTodaySecondaryLinks(todoCards, primaryAction);

  const health = {
    chaptersWritten,
    maxChapter,
    coveragePct,
    batchActive,
    batchStatus: batchJob?.status || (batchActive ? 'running' : 'idle'),
    qualityReportReady: Boolean(qualityReport?.available),
  };

  return {
    projectName,
    creationMode,
    primaryAction,
    secondaryLinks,
    health,
    wizardProgressPct,
  };
}

const snapshot = ref(null);
const loading = ref(false);
const lastError = ref(null);

async function refresh(options = {}) {
  loading.value = true;
  lastError.value = null;
  try {
    snapshot.value = await loadTodaySnapshot(options);
  } catch (e) {
    lastError.value = e?.message || String(e);
  } finally {
    loading.value = false;
  }
}

export function useTodayHub() {
  return {
    snapshot,
    loading,
    lastError,
    refresh,
  };
}
