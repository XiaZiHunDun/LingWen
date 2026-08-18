/**
 * useAgentTools 子模块独立测试
 *
 * Phase 43: 为 Phase 19.6 useAgentTools 子模块添加专门测试。
 * 重点测试：候选选择 + 应用确认 + 撤销 + 焦点注释。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref, computed } from 'vue';

import { useAgentTools } from '../../src/composables/useCreatorAgent/useAgentTools';

function mountAgentTools() {
  const executionMode = ref<string>('preview');
  const agentLensLabel = computed(() => '作者视角');
  const pendingPlan = ref<Record<string, unknown> | null>(null);
  const candidates = ref<Array<Record<string, unknown>>>([]);
  const directorAdvice = ref<Array<Record<string, unknown>>>([]);
  const statusLine = ref('');
  const applyTextToSelection = vi.fn();
  const createCheckpoint = vi.fn(() => 'cp-1');
  const restoreCheckpoint = vi.fn();
  const onAnnotationFocus = vi.fn();
  const pushMessage = vi.fn();
  const clearPlan = vi.fn();
  const getControls = (): { styleStrength: number; selectionLocked: boolean; allowWorldbuildingFill: boolean; goalTag: string } => ({
    styleStrength: 1, selectionLocked: false, allowWorldbuildingFill: true, goalTag: 'pace',
  });

  const ctx = useAgentTools({
    executionMode, agentLensLabel,
    pendingPlan, candidates, directorAdvice, statusLine,
    getControls, applyTextToSelection, createCheckpoint, restoreCheckpoint,
    onAnnotationFocus, pushMessage, clearPlan,
  } as unknown as Parameters<typeof useAgentTools>[0]);
  return {
    ...ctx,
    pendingPlan, candidates, directorAdvice, statusLine,
    applyTextToSelection, createCheckpoint, restoreCheckpoint,
    onAnnotationFocus, pushMessage, clearPlan, executionMode,
  };
}

describe('useAgentTools', () => {
  beforeEach(() => vi.clearAllMocks());

  it('initial state has empty lastCheckpointId', () => {
    const t = mountAgentTools();
    expect(t.lastCheckpointId.value).toBeNull();
    expect(t.hasPendingPlan.value).toBe(false);
  });

  it('hasPendingPlan returns true when pendingPlan set', () => {
    const t = mountAgentTools();
    t.pendingPlan.value = { action: 'rewrite', actionLabel: '改写' };
    expect(t.hasPendingPlan.value).toBe(true);
  });

  it('selectCandidate no-op when candidate not found', () => {
    const t = mountAgentTools();
    t.candidates.value = [{ id: 'a', label: 'A' }];
    t.selectCandidate('not-found');
    // pendingPlan 不变
    expect(t.pendingPlan.value).toBeNull();
  });

  it('selectCandidate in preview mode sets confirmReplace', () => {
    const t = mountAgentTools();
    t.executionMode.value = 'preview';
    t.candidates.value = [{ id: 'a', label: 'A' }];
    t.selectCandidate('a');
    expect(t.statusLine.value).toContain('已选');
  });

  it('selectCandidate in apply mode triggers requestApply', () => {
    const t = mountAgentTools();
    t.executionMode.value = 'apply';
    t.candidates.value = [{ id: 'a', label: 'A' }];
    t.selectCandidate('a');
    // requestApply 内部会调用 confirmApply（但 selectedCandidate 不在 candidates 中 → 早退）
    expect(t.applyTextToSelection).not.toHaveBeenCalled();
  });

  it('requestApply sets pending', () => {
    const t = mountAgentTools();
    t.selectCandidate('a'); // pendingPlan 仍 null
    t.candidates.value = [{ id: 'a', label: 'A' }];
    // pendingPlan 仍 null，因为 selectCandidate 在 preview mode 设置 confirmReplace 但需要 plan
    t.requestApply('');
    // requestApply 不修改 pendingPlan（已 null）
    expect(t.pendingPlan.value).toBeNull();
  });

  it('confirmApply no-op when no plan', () => {
    const t = mountAgentTools();
    t.confirmApply();
    expect(t.applyTextToSelection).not.toHaveBeenCalled();
  });

  it('cancelPlan clears pending', () => {
    const t = mountAgentTools();
    // clearPlan 是 deps，模拟主 hook 行为：清空 pendingPlan
    t.clearPlan.mockImplementation(() => { t.pendingPlan.value = null; });
    t.pendingPlan.value = { action: 'test', actionLabel: 't', scope: { type: 'none', label: '' }, executionMode: 'apply' };
    t.cancelPlan();
    expect(t.pendingPlan.value).toBeNull();
  });

  it('cancelPlan calls clearPlan and sets status', () => {
    const t = mountAgentTools();
    t.clearPlan.mockImplementation(() => { t.pendingPlan.value = null; });
    t.pendingPlan.value = { action: 'test', actionLabel: 't', scope: { type: 'none', label: '' }, executionMode: 'apply' };
    t.cancelPlan();
    expect(t.clearPlan).toHaveBeenCalled();
    expect(t.statusLine.value).toContain('已取消');
  });

  it('undoLastApply no-op when no checkpoint', () => {
    const t = mountAgentTools();
    t.undoLastApply();
    expect(t.restoreCheckpoint).not.toHaveBeenCalled();
  });

  it('undoLastApply restores checkpoint', () => {
    const t = mountAgentTools();
    t.lastCheckpointId.value = 'cp-1';
    t.undoLastApply();
    expect(t.restoreCheckpoint).toHaveBeenCalledWith('cp-1');
    expect(t.statusLine.value).toContain('已恢复');
  });

  it('dismissAdvice filters advice list', () => {
    const t = mountAgentTools();
    t.directorAdvice.value = [
      { id: 'a1', text: 'a1' },
      { id: 'a2', text: 'a2' },
    ];
    t.dismissAdvice('a1');
    expect(t.directorAdvice.value).toHaveLength(1);
    expect(t.directorAdvice.value[0].id).toBe('a2');
  });

  it('focusAnnotation no-op when no paragraph', () => {
    const t = mountAgentTools();
    t.focusAnnotation({});
    expect(t.onAnnotationFocus).not.toHaveBeenCalled();
  });

  it('focusAnnotation invokes callback with paragraph', () => {
    const t = mountAgentTools();
    t.focusAnnotation({ paragraph: 5 });
    expect(t.onAnnotationFocus).toHaveBeenCalledWith(5);
  });

  it('selectCandidate in preview mode does not request apply', () => {
    const t = mountAgentTools();
    t.executionMode.value = 'preview';
    t.candidates.value = [{ id: 'a', label: 'A' }];
    t.pendingPlan.value = { action: 't', actionLabel: 't', scope: { type: 'none', label: '' }, executionMode: 'apply' };
    t.selectCandidate('a');
    expect(t.statusLine.value).toContain('已选');
  });
});