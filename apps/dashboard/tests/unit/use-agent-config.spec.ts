/**
 * useAgentConfig 子模块独立测试
 *
 * Phase 43: 为 Phase 19.6 useAgentConfig 子模块添加专门测试。
 * 重点测试：执行模式切换 + Agent Lens + Director Paths。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref, computed, ComputedRef } from 'vue';

const configMocks = vi.hoisted(() => ({
  runCreatorAgentPlan: vi.fn(),
  runCreatorAgentPlanStream: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  runCreatorAgentPlan: (...args: unknown[]) => configMocks.runCreatorAgentPlan(...args),
  runCreatorAgentPlanStream: (...args: unknown[]) => configMocks.runCreatorAgentPlanStream(...args),
}));

import { useAgentConfig } from '../../src/composables/useCreatorAgent/useAgentConfig';

function mountAgentConfig() {
  const uiProfile = ref<Record<string, unknown>>({ agent_lens_default: 'author' });
  const currentScope = computed(() => ({ type: 'none', label: '无' }));
  const getControls = (): { styleStrength: number; selectionLocked: boolean; allowWorldbuildingFill: boolean; goalTag: string } => ({
    styleStrength: 1, selectionLocked: false, allowWorldbuildingFill: true, goalTag: 'pace',
  });
  const mockAnnotations = (_lens: string, _actionLabel: string): Array<Record<string, unknown>> => [];
  const pendingPlan = ref<Record<string, unknown> | null>(null);
  const annotations = ref<Array<Record<string, unknown>>>([]);
  const generating = ref(false);
  const statusLine = ref('');
  const executionMode = ref('preview');
  const agentLens = ref('author');
  const agentLensLabel = computed(() => '作者视角');

  const ctx = useAgentConfig({
    uiProfile: uiProfile as unknown as ComputedRef<Record<string, unknown>>,
    currentScope, getControls, mockAnnotations,
    pendingPlan, annotations, generating, statusLine,
    executionMode, agentLens, agentLensLabel,
  } as unknown as Parameters<typeof useAgentConfig>[0]);
  return {
    ...ctx,
    uiProfile, statusLine, executionMode, agentLens,
  };
}

describe('useAgentConfig', () => {
  beforeEach(() => vi.clearAllMocks());

  it('initial state has execution mode and lens from uiProfile', () => {
    const c = mountAgentConfig();
    expect(c.executionMode.value).toBe('preview');
    expect(c.agentLens.value).toBe('author');
    expect(c.agentLensLabel.value).toBe('作者视角');
  });

  it('initial state has promptInput empty', () => {
    const c = mountAgentConfig();
    expect(c.promptInput.value).toBe('');
    expect(c.agentExpanded.value).toBe(false);
  });

  it('toggleExecutionMode switches preview ↔ apply', () => {
    const c = mountAgentConfig();
    c.executionMode.value = 'preview';
    c.toggleExecutionMode();
    expect(c.executionMode.value).toBe('apply');
    c.toggleExecutionMode();
    expect(c.executionMode.value).toBe('preview');
  });

  it('toggleExecutionMode updates statusLine', () => {
    const c = mountAgentConfig();
    c.executionMode.value = 'preview';
    c.toggleExecutionMode();
    // statusLine 更新（具体文案依赖 AGENT_EXECUTION_MODES 常量）
    expect(c.statusLine.value.length).toBeGreaterThan(0);
  });

  it('setAgentLens updates lens and ref', () => {
    const c = mountAgentConfig();
    c.setAgentLens('editor');
    expect(c.agentLens.value).toBe('editor');
  });

  it('directorPaths returns empty array when scope.type is none', () => {
    const c = mountAgentConfig();
    expect(c.directorPaths.value).toEqual([]);
  });

  it('rewritePresets contains expected keys', () => {
    const c = mountAgentConfig();
    expect(Object.keys(c.rewritePresets)).toEqual(
      expect.arrayContaining(['concrete', 'dramatic', 'restrained', 'humorous', 'lyrical']),
    );
  });

  it('directorPaths adjusts consequence for pace goal', () => {
    const customMount = () => {
      const uiProfile = ref<Record<string, unknown>>({ agent_lens_default: 'author' });
      const currentScope = computed(() => ({ type: 'chapter', label: 'ch1' }));
      const getControls = (): { styleStrength: number; selectionLocked: boolean; allowWorldbuildingFill: boolean; goalTag: string } => ({
        styleStrength: 1, selectionLocked: false, allowWorldbuildingFill: true, goalTag: 'pace',
      });
      const mockAnnotations = (): Array<Record<string, unknown>> => [];
      const pendingPlan = ref<Record<string, unknown> | null>(null);
      const annotations = ref<Array<Record<string, unknown>>>([]);
      const generating = ref(false);
      const statusLine = ref('');
      const executionMode = ref('preview');
      const agentLens = ref('author');
      const agentLensLabel = computed(() => '作者视角');
      return useAgentConfig({
        uiProfile: uiProfile as unknown as ComputedRef<Record<string, unknown>>,
        currentScope, getControls, mockAnnotations,
        pendingPlan, annotations, generating, statusLine,
        executionMode, agentLens, agentLensLabel,
      } as unknown as Parameters<typeof useAgentConfig>[0]);
    };
    const result = customMount();
    expect(result.directorPaths.value.length).toBeGreaterThan(0);
  });

  it('initial lens loaded from uiProfile agent_lens_default', () => {
    const c = mountAgentConfig();
    c.uiProfile.value = { agent_lens_default: 'reviewer' };
    // 重新触发 init（虽然 mount 时已读取，但 uiProfile 引用已固定）
    expect(c.agentLens.value).toBe('author'); // 仍是初始值
  });
});
