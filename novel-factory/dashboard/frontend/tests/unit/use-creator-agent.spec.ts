// tests/unit/use-creator-agent.spec.ts — useCreatorAgent 写作导演编排

import { describe, test, expect, vi, beforeEach } from 'vitest';
import { computed, defineComponent, ref } from 'vue';
import { mount } from '@vue/test-utils';
import { AGENT_EXECUTION_MODES } from '../../src/config/creatorPanelMatrix.js';

const agentMocks = vi.hoisted(() => ({
  runCreatorAgentPlan: vi.fn(),
  runCreatorAgentPlanStream: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  runCreatorAgentPlan: (...args: unknown[]) => agentMocks.runCreatorAgentPlan(...args),
  runCreatorAgentPlanStream: (...args: unknown[]) => agentMocks.runCreatorAgentPlanStream(...args),
}));

import { useCreatorAgent } from '../../src/composables/useCreatorAgent.js';

type AgentApi = ReturnType<typeof useCreatorAgent>;

function mountAgent(overrides: Record<string, unknown> = {}) {
  const uiProfile = computed(() => ({
    agent_execution_mode_default: AGENT_EXECUTION_MODES.preview,
    agent_lens_default: 'author',
    ...(overrides.uiProfile as object | undefined),
  }));

  const selection = ref({ text: '选区正文', start: 0, end: 4 });
  const chapterNum = ref<number | null>(3);
  const bodyDraft = ref('章节正文');
  const controls = ref({
    styleStrength: 2,
    selectionLocked: false,
    allowWorldbuildingFill: false,
    goalTag: '',
  });

  const applyTextToSelection = vi.fn((text: string) => {
    bodyDraft.value = text;
  });
  const createCheckpoint = vi.fn(() => 'cp-test-1');
  const restoreCheckpoint = vi.fn();
  const onAnnotationFocus = vi.fn();

  const deps = {
    uiProfile,
    getSelection: () => selection.value,
    getChapterNum: () => chapterNum.value,
    getBodyDraft: () => bodyDraft.value,
    getControls: () => controls.value,
    applyTextToSelection,
    createCheckpoint,
    restoreCheckpoint,
    onAnnotationFocus,
    ...(overrides.deps as object | undefined),
  };

  let api!: AgentApi;
  const Comp = defineComponent({
    setup() {
      api = useCreatorAgent(deps);
      return () => null;
    },
  });

  mount(Comp);
  return {
    api,
    selection,
    chapterNum,
    bodyDraft,
    controls,
    applyTextToSelection,
    createCheckpoint,
    restoreCheckpoint,
    onAnnotationFocus,
  };
}

describe('useCreatorAgent', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    agentMocks.runCreatorAgentPlan.mockRejectedValue(new Error('offline'));
    agentMocks.runCreatorAgentPlanStream.mockRejectedValue(new Error('offline'));
  });

  test('buildScope prefers selection over chapter', () => {
    const { api } = mountAgent();
    expect(api.buildScope().type).toBe('selection');
    expect(api.buildScope().label).toContain('选区');
  });

  test('buildScope falls back to chapter when selection empty', () => {
    const { api } = mountAgent({
      deps: {
        getSelection: () => ({ text: '  ', start: 0, end: 0 }),
      },
    });
    const scope = api.buildScope();
    expect(scope.type).toBe('chapter');
    expect(scope.label).toContain('ch003');
  });

  test('submitPrompt pushes user message and runs plan', async () => {
    const { api } = mountAgent();
    api.promptInput.value = '加快信息披露';
    await api.submitPrompt();
    expect(api.messages.value.some((m) => m.role === 'user' && m.text.includes('加快'))).toBe(true);
    expect(api.promptInput.value).toBe('');
    expect(api.candidates.value.length).toBeGreaterThan(0);
  });

  test('preview mode selectCandidate waits for confirm without applying', async () => {
    const { api, applyTextToSelection } = mountAgent();
    await api.runRewritePreset('concrete');
    api.selectCandidate('steady');
    expect(applyTextToSelection).not.toHaveBeenCalled();
    expect(api.pendingPlan.value?.selectedCandidateId).toBe('steady');
    expect(api.pendingPlan.value?.confirmReplace).toBe(true);
  });

  test('confirmApply blocked when adviceOnly', async () => {
    const { api, applyTextToSelection } = mountAgent({
      deps: {
        getControls: () => ({
          styleStrength: 0,
          selectionLocked: false,
          allowWorldbuildingFill: false,
          goalTag: '',
        }),
      },
    });
    await api.runDirectorPath('faster');
    api.confirmApply();
    expect(applyTextToSelection).not.toHaveBeenCalled();
    expect(api.statusLine.value).toContain('只建议');
  });

  test('confirmApply blocked when selection locked at apply time', async () => {
    const { api, controls, applyTextToSelection } = mountAgent();
    await api.runRewritePreset('dramatic');
    api.selectCandidate('steady');
    controls.value = { ...controls.value, selectionLocked: true };
    api.confirmApply();
    expect(applyTextToSelection).not.toHaveBeenCalled();
    expect(api.statusLine.value).toContain('锁定');
  });

  test('applies API advice_only plan without candidates', async () => {
    agentMocks.runCreatorAgentPlanStream.mockResolvedValue({
      advice_only: true,
      advice: [{ id: 'a1', text: 'API 建议' }],
      annotations: [],
      status_line: '只建议',
      provider: 'mock',
    });
    const { api } = mountAgent();
    await api.runPlan('prompt', '测试');
    expect(api.directorAdvice.value).toHaveLength(1);
    expect(api.candidates.value).toHaveLength(0);
    expect(api.pendingPlan.value?.adviceOnly).toBe(true);
    expect(api.planProvider.value).toBe('mock');
  });

  test('stream events update preview label and advice buffer while generating', async () => {
    let releasePlan!: () => void;
    const planGate = new Promise<void>((resolve) => {
      releasePlan = resolve;
    });
    agentMocks.runCreatorAgentPlanStream.mockImplementation(async (_body, onEvent) => {
      onEvent?.({ type: 'status', message: '流式生成中' });
      onEvent?.({ type: 'preview_label', label: '候选预览 1/3' });
      onEvent?.({ type: 'chunk', text: '片段', source: 'mock' });
      onEvent?.({ type: 'advice', text: '可先缩短铺垫' });
      await planGate;
      return {
        advice_only: false,
        candidates: [{ id: 'c1', label: 'A', direction: '稳', text: '流式结果' }],
        annotations: [],
        provider: 'mock',
      };
    });
    const { api } = mountAgent();
    const runPromise = api.runRewritePreset('concrete');
    await vi.waitFor(() => {
      expect(api.statusLine.value).toBe('流式生成中');
    });
    expect(api.streamPreviewLabel.value).toContain('候选预览');
    expect(api.streamAdvicePreview.value).toContain('可先缩短铺垫');
    releasePlan();
    await runPromise;
    expect(api.candidates.value[0]?.text).toBe('流式结果');
  });

  test('director paths adjust consequence for suspense goal', () => {
    const { api } = mountAgent({
      deps: {
        getSelection: () => ({ text: '', start: 0, end: 0 }),
        getControls: () => ({
          styleStrength: 1,
          selectionLocked: false,
          allowWorldbuildingFill: false,
          goalTag: 'suspense',
        }),
      },
    });
    const faster = api.directorPaths.value.find((p) => p.id === 'faster');
    expect(faster?.consequence).toContain('悬疑');
    const restrained = api.directorPaths.value.find((p) => p.id === 'restrained');
    expect(restrained?.consequence).toContain('悬疑目标下留白增加');
  });

  test('setAgentLens refreshes editor annotations when plan has annotations', async () => {
    agentMocks.runCreatorAgentPlanStream.mockResolvedValue({
      advice_only: false,
      candidates: [{ id: 'c1', label: 'A', direction: '稳', text: 'API 候选' }],
      annotations: [{ id: 'a0', level: 'info', text: '作者视角标注', paragraph: 1 }],
      provider: 'mock',
    });
    const { api } = mountAgent();
    await api.runRewritePreset('concrete');
    expect(api.annotations.value).toHaveLength(1);
    api.setAgentLens('editor');
    expect(api.annotations.value.length).toBeGreaterThan(0);
    expect(api.annotations.value[0]?.level).toBe('warn');
    expect(api.agentLensLabel.value).toBeTruthy();
  });

  test('focusAnnotation invokes paragraph callback', () => {
    const { api, onAnnotationFocus } = mountAgent();
    api.focusAnnotation({ id: 'n1', level: 'info', text: '提示', paragraph: 3 });
    expect(onAnnotationFocus).toHaveBeenCalledWith(3);
  });
});
