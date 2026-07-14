// tests/unit/use-creator-pulse.spec.ts — useCreatorPulse 脉络栏编排

import { describe, test, expect, vi, beforeEach } from 'vitest';
import { computed, defineComponent, ref } from 'vue';
import { flushPromises, mount } from '@vue/test-utils';

const pulseMocks = vi.hoisted(() => ({
  generateCreatorVolumeSummary: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  generateCreatorVolumeSummary: (...args: unknown[]) => pulseMocks.generateCreatorVolumeSummary(...args),
}));

import { useCreatorPulse } from '../../src/composables/useCreatorPulse.js';

type PulseApi = ReturnType<typeof useCreatorPulse>;

function mountPulse(overrides: Record<string, unknown> = {}) {
  const uiProfile = computed(() => ({
    batch_deviation_prompt: true,
    batch_highlight_alert_volumes: true,
    batch_clear_pulse_no_alert: false,
    batch_auto_open_summary: false,
    ...(overrides.uiProfile as object | undefined),
  }));

  const overview = ref({
    creation_mode: 'advance',
    volume_pulse: {
      volume_count: 1,
      volumes: [
        { label: '卷一', status: 'alert', start_chapter: 1, end_chapter: 5 },
        { label: '卷二', status: 'ok', start_chapter: 6, end_chapter: 10 },
      ],
    },
    volume_summaries: [
      { name: 'volume-summary-ch001-005.md', label: '卷一摘要' },
    ],
    ...(overrides.overview as object | undefined),
  });

  const editableVolumes = ref([{ label: '卷一', start_chapter: 1, end_chapter: 5 }]);
  const error = ref<string | null>(null);
  const saveMessage = ref('');
  const highlightedDeviationChapter = ref<number | null>(null);
  const jumpToChapter = vi.fn(async () => undefined);
  const onAfterVolumeSummarySave = vi.fn(async () => undefined);
  const onBatchCompleted = vi.fn(async () => undefined);

  const deps = {
    uiProfile,
    overview,
    error,
    saveMessage,
    workspaceTabsEnabled: computed(() => true),
    isWorkspaceColumnVisible: () => true,
    setWorkspaceTab: vi.fn(),
    editableVolumes,
    visibleDeviations: computed(() => []),
    deviationHighlightEnabled: computed(() => true),
    highlightedDeviationChapter,
    handleDeviationClick: vi.fn(async () => undefined),
    jumpToChapter,
    onAfterVolumeSummarySave,
    batchJob: ref(null),
    ...(overrides.deps as object | undefined),
  };

  let api!: PulseApi;
  const Comp = defineComponent({
    setup() {
      api = useCreatorPulse(deps);
      return () => null;
    },
  });

  mount(Comp);
  return { api, deps, overview, error, saveMessage, jumpToChapter, onAfterVolumeSummarySave };
}

describe('useCreatorPulse', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    pulseMocks.generateCreatorVolumeSummary.mockResolvedValue({});
  });

  test('showPulseCompanionEmpty when companion has no volumes or deviations', () => {
    const { api } = mountPulse({
      overview: {
        creation_mode: 'companion',
        volume_pulse: null,
        volume_summaries: [],
      },
      deps: { editableVolumes: ref([]) },
    });
    expect(api.panelContext.showPulseCompanionEmpty.value).toBe(true);
  });

  test('showPulseCompanionEmpty is false when volumes exist', () => {
    const { api } = mountPulse({ overview: { creation_mode: 'companion' } });
    expect(api.panelContext.showPulseCompanionEmpty.value).toBe(false);
  });

  test('jumpToVolume highlights label and jumps to start chapter', async () => {
    const { api, jumpToChapter } = mountPulse();
    await api.panelContext.jumpToVolume({ label: '卷一', start_chapter: 3, end_chapter: 5 });
    expect(api.panelContext.highlightedVolumeLabel.value).toBe('卷一');
    expect(jumpToChapter).toHaveBeenCalledWith(3);
  });

  test('openVolumeSummaryForRange resolves summary block name', async () => {
    const { api } = mountPulse();
    api.openVolumeSummaryForRange(1, 5);
    await flushPromises();
    expect(api.panelContext.openVolumeSummaryName.value).toBe('volume-summary-ch001-005.md');
  });

  test('collectBatchAlertVolumeLabels filters alert volumes in range', () => {
    const { api } = mountPulse();
    const labels = api.collectBatchAlertVolumeLabels(1, 5);
    expect(labels).toEqual(['卷一']);
  });

  test('highlightBatchAlertVolumes sets highlightedVolumeLabel for alert row', async () => {
    const { api } = mountPulse();
    await api.highlightBatchAlertVolumes(1, 5);
    expect(api.panelContext.highlightedVolumeLabel.value).toBe('卷一');
  });

  test('generateVolumeSummaryForRow calls API and refreshes', async () => {
    const { api, saveMessage, onAfterVolumeSummarySave } = mountPulse();
    await api.panelContext.generateVolumeSummaryForRow({
      label: '卷一',
      start_chapter: 1,
      end_chapter: 5,
    });
    expect(pulseMocks.generateCreatorVolumeSummary).toHaveBeenCalledWith({
      startChapter: 1,
      endChapter: 5,
    });
    expect(saveMessage.value).toContain('卷一');
    expect(onAfterVolumeSummarySave).toHaveBeenCalled();
    expect(api.panelContext.openVolumeSummaryName.value).toBe('volume-summary-ch001-005.md');
  });

  test('generateVolumeSummaryForRow surfaces API errors', async () => {
    pulseMocks.generateCreatorVolumeSummary.mockRejectedValue(new Error('生成失败'));
    const { api, error } = mountPulse();
    await api.panelContext.generateVolumeSummaryForRow({
      label: '卷一',
      start_chapter: 1,
      end_chapter: 5,
    });
    expect(error.value).toBe('生成失败');
  });

  test('setBatchSummaryPrompt and dismissBatchSummaryPrompt', () => {
    const { api } = mountPulse();
    api.setBatchSummaryPrompt({ start: 1, end: 5, alert_volume_labels: [] });
    expect((api.batchSummaryPrompt.value as any)?.start).toBe(1);
    api.panelContext.dismissBatchSummaryPrompt();
    expect(api.batchSummaryPrompt.value).toBeNull();
  });

  test('onBatchCompleted enriches prompt with alert volume labels', async () => {
    const { api } = mountPulse();
    api.setBatchSummaryPrompt({ start: 1, end: 5, alert_volume_labels: [] });
    await api.onBatchCompleted(1, 5);
    expect((api.batchSummaryPrompt.value as any)?.alert_volume_labels).toEqual(['卷一']);
    expect(api.panelContext.highlightedVolumeLabel.value).toBe('卷一');
  });

  test('onBatchCompleted opens summary when batch_auto_open_summary enabled', async () => {
    const { api } = mountPulse({
      uiProfile: { batch_auto_open_summary: true, batch_highlight_alert_volumes: false },
    });
    api.setBatchSummaryPrompt({ start: 1, end: 5, alert_volume_labels: [] });
    await api.onBatchCompleted(1, 5);
    expect(api.panelContext.openVolumeSummaryName.value).toBe('volume-summary-ch001-005.md');
  });

  test('pulseSubpanelVisible respects creation mode matrix', () => {
    const { api } = mountPulse({ overview: { creation_mode: 'advance' } });
    expect(api.panelContext.isPulseSubpanelVisible('advanceBatch')).toBe(true);
  });

  test('deskDrawerActive reflects isDeskDrawerColumn', () => {
    const { api } = mountPulse({
      deps: { isDeskDrawerColumn: (col: string) => col === 'pulse' },
    });
    expect(api.panelContext.deskDrawerActive()).toBe(true);
  });
});
