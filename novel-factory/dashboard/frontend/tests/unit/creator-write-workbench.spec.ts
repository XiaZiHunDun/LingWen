import type { AgentCandidate, AgentPendingPlan, QualityHint } from '../helpers/strict-test-types.js';
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
    ...(actual as object),
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
    expect((wb.qualityHints.value[0] as QualityHint).level).toBe('warn');
  });

  it('runs light validation and dismisses hints', () => {
    const uiProfile = computed(() => ({}));
    const overview = ref({ creation_mode: 'companion' });
    const chapterBodyDraft = ref('段落一\n段落二');
    const wb = useCreatorWriteWorkbench({
      uiProfile,
      overview,
      chapterBodyDraft,
      selectedChapter: ref(1),
      saveMessage: ref(''),
    });
    wb.runLightValidationNow();
    expect(wb.lightValidationSummary.value).toBeTruthy();
    wb.syncQualityFromLogicCheck({
      passed: false,
      issues: [{ severity: 'P0', title: '节奏偏慢' }],
    });
    const before = wb.qualityHints.value.length;
    expect(before).toBeGreaterThan(0);
    wb.dismissQualityHint(0);
    expect(wb.qualityHints.value.length).toBe(before - 1);
  });

  it('restores checkpoints after draft edits', () => {
    const uiProfile = computed(() => ({}));
    const overview = ref({ creation_mode: 'companion' });
    const chapterBodyDraft = ref('hello world');
    const saveMessage = ref('');
    const wb = useCreatorWriteWorkbench({
      uiProfile,
      overview,
      chapterBodyDraft,
      selectedChapter: ref(1),
      saveMessage,
    });
    const cpId = wb.createCheckpoint('before');
    chapterBodyDraft.value = 'mutated';
    wb.restoreCheckpoint(cpId);
    expect(chapterBodyDraft.value).toBe('hello world');
    expect(saveMessage.value).toContain('恢复');
  });

  it('studio desk uses factory-oriented goal copy', () => {
    const wb = useCreatorWriteWorkbench({
      uiProfile: computed(() => ({ creator_write_workbench: true })),
      overview: ref({ creation_mode: 'studio', name: 'Studio' }),
      chapterBodyDraft: ref(''),
      selectedChapter: ref(2),
      saveMessage: ref(''),
    });
    expect(wb.goalCardLines.value.line2).toBe('工厂模式');
    expect(wb.humanFirstDesk.value).toBe(false);
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
      applyTextToSelection: (text: string) => { applied = text; },
      createCheckpoint: (label: string) => {
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
    expect((agent.pendingPlan.value as AgentPendingPlan | null)?.adviceOnly).toBe(true);
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
    expect((agent.candidates.value[0] as AgentCandidate).text).toBe('API 候选');
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

  it('blocks plan when selection locked', async () => {
    const agent = makeAgent({
      getSelection: () => ({ text: '锁定', start: 0, end: 2 }),
      getControls: () => ({
        styleStrength: 2,
        selectionLocked: true,
        allowWorldbuildingFill: false,
        goalTag: '',
      }),
    });
    await agent.runRewritePreset('concrete');
    expect(agent.candidates.value).toHaveLength(0);
    expect(agent.statusLine.value).toContain('锁定');
  });

  it('falls back to non-stream API plan', async () => {
    vi.mocked(runCreatorAgentPlanStream).mockRejectedValue(new Error('stream down'));
    vi.mocked(runCreatorAgentPlan).mockResolvedValue({
      advice_only: false,
      candidates: [{ id: 'steady', label: '稳健', direction: '稳', text: 'REST 候选' }],
      advice: [],
      annotations: [],
      status_line: 'REST 就绪',
      provider: 'rest',
      lens: 'reviewer',
    });
    const agent = makeAgent();
    agent.setAgentLens('reviewer');
    await agent.runRewritePreset('dramatic');
    expect(runCreatorAgentPlan).toHaveBeenCalled();
    expect(agent.planProvider.value).toBe('rest');
    expect((agent.candidates.value[0] as AgentCandidate).text).toBe('REST 候选');
  });

  it('cancels pending plan and undoes last apply', async () => {
    vi.mocked(runCreatorAgentPlanStream).mockRejectedValue(new Error('offline'));
    vi.mocked(runCreatorAgentPlan).mockRejectedValue(new Error('offline'));
    let body = '原始正文';
    const agent = makeAgent({
      getBodyDraft: () => body,
      applyTextToSelection: (text: string) => { body = text; },
      createCheckpoint: () => 'cp-undo',
      restoreCheckpoint: () => { body = '原始正文'; },
    });
    await agent.runRewritePreset('concrete');
    agent.selectCandidate('steady');
    agent.confirmApply();
    expect(body).toContain('稳健候选');
    agent.undoLastApply();
    expect(body).toBe('原始正文');
    await agent.runRewritePreset('lyrical');
    agent.cancelPlan();
    expect(agent.pendingPlan.value).toBeNull();
    expect(agent.statusLine.value).toContain('取消');
  });

  it('skips empty prompt submit and none scope', async () => {
    const agent = makeAgent({
      getChapterNum: () => null,
      getSelection: () => ({ text: '', start: 0, end: 0 }),
    });
    await agent.submitPrompt();
    expect(runCreatorAgentPlanStream).not.toHaveBeenCalled();
    await agent.runPlan('noop', '空操作');
    expect(agent.statusLine.value).toContain('请先选中段落');
  });

  it('toggles execution mode and dismisses advice', async () => {
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
    const adviceId = (agent.directorAdvice.value[0] as { id: string }).id;
    agent.dismissAdvice(adviceId);
    expect(agent.directorAdvice.value.find((a) => (a as { id: string }).id === adviceId)).toBeUndefined();
    agent.toggleExecutionMode();
    expect(agent.isPreviewMode.value).toBe(false);
    agent.toggleExecutionMode();
    expect(agent.isPreviewMode.value).toBe(true);
  });

  it('focuses annotation paragraph via callback', () => {
    const onFocus = vi.fn();
    const agent = makeAgent({ onAnnotationFocus: onFocus });
    agent.focusAnnotation({ id: 'x', level: 'warn', text: '标注', paragraph: 2 });
    expect(onFocus).toHaveBeenCalledWith(2);
  });

  it('masks JSON stream preview while llm streams', () => {
    const agent = makeAgent();
    (agent.streamSource as { value: string | null }).value = 'llm';
    agent.streamPreviewText.value = '{"candidates":';
    expect(agent.streamDisplayText.value).toContain('模型输出中');
    agent.streamPreviewText.value = 'plain text chunk';
    expect(agent.streamDisplayText.value).toBe('plain text chunk');
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
