import { describe, expect, it, vi, beforeEach } from 'vitest';
import { ref, computed } from 'vue';
import {
  AGENT_EXECUTION_MODES,
  AGENT_LENS_MODES,
  COMFORT_DIMENSION_WEIGHTS,
  isChapterTaskCardsVisible,
  isWriteWorkbenchLayoutEnabled,
  isWriteWorkbenchPanelVisible,
} from '../../src/config/creatorPanelMatrix.js';
import { useCreatorAgent } from '../../src/composables/useCreatorAgent.js';
import { useCreatorWriteWorkbench } from '../../src/composables/useCreatorWriteWorkbench.js';

vi.mock('../../src/api/index.js', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    runCreatorAgentPlan: vi.fn(),
    runCreatorAgentPlanStream: vi.fn(),
  };
});

import { runCreatorAgentPlan, runCreatorAgentPlanStream } from '../../src/api/index.js';

describe('creator write workbench matrix', () => {
  it('enables workbench layout for companion by default', () => {
    expect(isWriteWorkbenchPanelVisible('companion', 'workbenchLayout')).toBe(true);
    expect(isWriteWorkbenchLayoutEnabled('companion', {})).toBe(true);
    expect(isWriteWorkbenchLayoutEnabled('companion', { creator_write_workbench: true })).toBe(true);
    expect(isWriteWorkbenchLayoutEnabled('companion', { creator_write_workbench: false })).toBe(false);
  });

  it('hides workbench for studio and shows chapter task cards for advance/studio', () => {
    expect(isWriteWorkbenchPanelVisible('studio', 'workbenchLayout')).toBe(false);
    expect(isChapterTaskCardsVisible('companion')).toBe(false);
    expect(isChapterTaskCardsVisible('advance')).toBe(true);
    expect(isChapterTaskCardsVisible('studio')).toBe(true);
  });

  it('defines comfort dimension weights for three modes', () => {
    expect(COMFORT_DIMENSION_WEIGHTS.lowBurdenInput.companion).toBe('high');
    expect(COMFORT_DIMENSION_WEIGHTS.rhythmOrchestration.studio).toBe('high');
  });

  it('defaults agent to preview mode', () => {
    expect(AGENT_EXECUTION_MODES.preview).toBe('preview');
    expect(AGENT_EXECUTION_MODES.apply).toBe('apply');
  });

  it('defines agent lens modes', () => {
    expect(AGENT_LENS_MODES.map((m) => m.id)).toContain('editor');
    expect(isWriteWorkbenchPanelVisible('companion', 'agentLensSwitcher')).toBe(true);
  });
});

describe('useCreatorWriteWorkbench', () => {
  it('human-friendly goal card copy for advance desk', () => {
    const uiProfile = computed(() => ({ creator_write_workbench: true }));
    const overview = ref({ creation_mode: 'advance', name: '测试书' });
    const wb = useCreatorWriteWorkbench({
      uiProfile,
      overview,
      chapterBodyDraft: ref(''),
      selectedChapter: ref(1),
      saveMessage: ref(''),
    });
    expect(wb.goalCardLines.value.line2).toContain('卷纲');
    expect(wb.goalCardLines.value.line2).not.toContain('Batch');
    expect(wb.humanFirstDesk.value).toBe(true);
  });

  it('captures body selection from textarea', () => {
    const uiProfile = computed(() => ({ creator_write_workbench: true }));
    const overview = ref({ creation_mode: 'companion', name: '测试书' });
    const chapterBodyDraft = ref('hello world');
    const selectedChapter = ref(1);
    const saveMessage = ref('');

    const wb = useCreatorWriteWorkbench({
      uiProfile,
      overview,
      chapterBodyDraft,
      selectedChapter,
      saveMessage,
    });

    expect(wb.workbenchEnabled.value).toBe(true);

    const textarea = {
      selectionStart: 0,
      selectionEnd: 5,
      value: 'hello world',
    };
    wb.captureBodySelection(textarea);
    expect(wb.hasBodySelection.value).toBe(true);
    expect(wb.bodySelection.value.text).toBe('hello');
  });

  it('syncs quality hints from logic check result', () => {
    const uiProfile = computed(() => ({}));
    const overview = ref({ creation_mode: 'companion' });
    const wb = useCreatorWriteWorkbench({
      uiProfile,
      overview,
      chapterBodyDraft: ref(''),
      selectedChapter: ref(null),
      saveMessage: ref(''),
    });

    wb.syncQualityFromLogicCheck({
      passed: false,
      p0_count: 2,
      issues: [{ severity: 'P0', title: '时间线冲突' }],
    });
    expect(wb.qualityHints.value.length).toBeGreaterThan(0);
    expect(wb.qualityHints.value[0].level).toBe('warn');
  });
});

describe('useCreatorAgent', () => {
  beforeEach(() => {
    vi.mocked(runCreatorAgentPlan).mockReset();
    vi.mocked(runCreatorAgentPlanStream).mockReset();
  });

  function makeAgent(overrides = {}) {
    return useCreatorAgent({
      uiProfile: computed(() => ({ agent_execution_mode_default: 'preview' })),
      getSelection: () => ({ text: '选区', start: 0, end: 2 }),
      getChapterNum: () => 3,
      getBodyDraft: () => '正文',
      getControls: () => ({
        styleStrength: 2,
        selectionLocked: false,
        allowWorldbuildingFill: false,
        goalTag: '',
      }),
      applyTextToSelection: () => {},
      createCheckpoint: () => 'cp-0',
      restoreCheckpoint: () => {},
      ...overrides,
    });
  }

  it('creates checkpoint on confirm apply', async () => {
    let applied = '';
    const checkpoints = [];

    vi.mocked(runCreatorAgentPlanStream).mockRejectedValue(new Error('offline'));
    vi.mocked(runCreatorAgentPlan).mockRejectedValue(new Error('offline'));

    const agent = makeAgent({
      applyTextToSelection: (text) => { applied = text; },
      createCheckpoint: (label) => {
        const id = `cp-${checkpoints.length}`;
        checkpoints.push({ id, label });
        return id;
      },
    });

    await agent.runRewritePreset('concrete');
    expect(agent.candidates.value.length).toBeGreaterThan(0);
    agent.selectCandidate('steady');
    agent.confirmApply();
    expect(applied).toContain('稳健候选');
    expect(checkpoints.length).toBe(1);
  });

  it('advice-only when style strength is zero', async () => {
    vi.mocked(runCreatorAgentPlanStream).mockRejectedValue(new Error('offline'));
    vi.mocked(runCreatorAgentPlan).mockRejectedValue(new Error('offline'));
    const agent = makeAgent({
      getControls: () => ({
        styleStrength: 0,
        selectionLocked: false,
        allowWorldbuildingFill: false,
        goalTag: '',
      }),
    });

    await agent.runDirectorPath('faster');
    expect(agent.directorAdvice.value.length).toBeGreaterThan(0);
    expect(agent.candidates.value).toHaveLength(0);
    expect(agent.pendingPlan.value?.adviceOnly).toBe(true);
  });

  it('uses API plan when available', async () => {
    const apiPlan = {
      advice_only: false,
      candidates: [
        { id: 'steady', label: '稳健', direction: '稳', text: 'API 候选' },
      ],
      advice: [],
      annotations: [{ id: 'e1', level: 'warn', text: '标注', paragraph: 1 }],
      status_line: '候选已就绪',
      provider: 'mock',
      lens: 'editor',
    };
    vi.mocked(runCreatorAgentPlanStream).mockImplementation(async (_body, onEvent) => {
      onEvent?.({ type: 'status', message: '正在生成候选…' });
      onEvent?.({ type: 'chunk', text: 'API' });
      onEvent?.({ type: 'done', plan: apiPlan });
      return apiPlan;
    });
    const agent = makeAgent();
    agent.setAgentLens('editor');
    await agent.runRewritePreset('concrete');
    expect(runCreatorAgentPlanStream).toHaveBeenCalledWith(
      expect.objectContaining({ lens: 'editor', provider_mode: 'auto' }),
      expect.any(Function),
    );
    expect(agent.planProvider.value).toBe('mock');
    expect(agent.candidates.value[0].text).toBe('API 候选');
    expect(agent.annotations.value).toHaveLength(1);
    expect(agent.agentLens.value).toBe('editor');
  });

  it('local fallback produces editor annotations', async () => {
    vi.mocked(runCreatorAgentPlanStream).mockRejectedValue(new Error('offline'));
    vi.mocked(runCreatorAgentPlan).mockRejectedValue(new Error('offline'));
    const agent = makeAgent();
    agent.setAgentLens('editor');
    await agent.runRewritePreset('concrete');
    expect(agent.annotations.value.length).toBeGreaterThan(0);
  });

  it('exposes director paths when chapter focused', () => {
    const agent = makeAgent({
      getSelection: () => ({ text: '', start: 0, end: 0 }),
      getControls: () => ({
        styleStrength: 1,
        selectionLocked: false,
        allowWorldbuildingFill: false,
        goalTag: 'suspense',
      }),
    });
    expect(agent.directorPaths.value.length).toBe(3);
    expect(agent.directorPaths.value[0].consequence).toBeTruthy();
  });
});

describe('textDiffUtils', () => {
  it('computes line diff between checkpoint and draft', async () => {
    const { computeLineDiff, countDiffChanges } = await import('../../src/utils/textDiffUtils.js');
    const lines = computeLineDiff('a\nb', 'a\nc');
    expect(countDiffChanges(lines)).toBeGreaterThan(0);
    expect(lines.some((l) => l.type === 'add')).toBe(true);
  });
});

describe('useCreatorWriteWorkbench controls', () => {
  it('opens checkpoint diff view', () => {
    const uiProfile = computed(() => ({}));
    const overview = ref({ creation_mode: 'companion' });
    const chapterBodyDraft = ref('line1\nline2-new');
    const wb = useCreatorWriteWorkbench({
      uiProfile,
      overview,
      chapterBodyDraft,
      selectedChapter: ref(1),
      saveMessage: ref(''),
    });
    const cpId = wb.createCheckpoint('测试');
    chapterBodyDraft.value = 'line1\nline2-old';
    wb.openCheckpointDiff(cpId);
    expect(wb.diffView.value?.changeCount).toBeGreaterThan(0);
  });
});
