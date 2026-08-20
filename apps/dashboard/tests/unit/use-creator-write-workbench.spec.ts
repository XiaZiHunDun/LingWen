/**
 * useCreatorWriteWorkbench facade 集成测试（Phase 60.5）
 *
 * 验证 facade 聚合 4 个子模块的返回值完整（59 字段）、跨子模块 computed 联动正确、
 * agent 注入 Quality 子模块。Mock 4 个子模块以隔离 facade 行为。
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref, computed } from 'vue';
import type { ComputedRef } from 'vue';

// Mock 4 个子模块以验证 facade 调用顺序和聚合
// vi.hoisted 早于 imports 执行，所以 mocks 中只能用 plain values；
// 真正使用 ref/computed 时通过 setUpMocks() 在导入后再安装。
const hoisted = vi.hoisted(() => ({
  layout: {
    workbenchEnabled: { value: true },
    leftPanelCollapsed: { value: true },
    humanFirstDesk: { value: false },
    goalCardLines: { value: { line1: 'x', line2: 'y', line3: 'z' } },
    consistencyItems: { value: [] },
    consistencyPanelOpen: { value: false },
    chapterEntities: { value: [] },
    isPanelVisible: vi.fn(() => true),
    isPanelCollapsed: vi.fn(() => false),
    isLeftRailPanelVisible: vi.fn(() => false),
    creationMode: { value: 'companion' },
    updateCreationMode: vi.fn(),
  },
  selection: {
    bodySelection: { value: { start: 0, end: 0, text: '' } },
    hasBodySelection: { value: false },
    qualityHints: { value: [] as unknown[] },
    styleStrength: { value: 1 },
    selectionLocked: { value: false },
    allowWorldbuildingFill: { value: false },
    goalTag: { value: '' },
    captureBodySelection: vi.fn(),
    applyTextToSelection: vi.fn(),
    toggleSelectionLock: vi.fn(),
    getControls: vi.fn(() => ({ styleStrength: 1, selectionLocked: false, allowWorldbuildingFill: false, goalTag: '' })),
  },
  checkpoints: {
    checkpoints: { value: [] },
    diffCheckpointId: { value: null },
    diffView: { value: null },
    createCheckpoint: vi.fn(() => 'cp-1'),
    restoreCheckpoint: vi.fn(),
    openCheckpointDiff: vi.fn(),
    closeCheckpointDiff: vi.fn(),
  },
  quality: {
    intentText: { value: '' }, intentGenre: { value: '' }, intentMood: { value: '' }, intentType: { value: '' }, intentTheme: { value: '' },
    intentHistory: { value: [] }, saveIntentToHistory: vi.fn(), loadIntentFromHistory: vi.fn(), clearIntentHistory: vi.fn(),
    dismissQualityHint: vi.fn(),
    syncQualityFromLightValidation: vi.fn(), syncQualityFromLogicCheck: vi.fn(),
    lightValidationIssues: { value: [] }, lightValidationSummary: { value: { status: 'ok' } }, lightValidationRunning: { value: false },
    runLightValidationNow: vi.fn(), scheduleLightValidation: vi.fn(),
    inlineConflictMarkers: { value: [] }, activeInlineConflictId: { value: null }, chapterBodyConflictHighlightActive: { value: false },
    focusInlineConflict: vi.fn(), focusLightValidationIssue: vi.fn(), clearInlineConflictFocus: vi.fn(),
    generateIntensity: { value: 'balanced' }, generateRunning: { value: false },
    startQuickWrite: vi.fn(), stopGenerate: vi.fn(),
  },
}));

vi.mock('../../src/composables/useCreatorWriteWorkbench/useWorkbenchLayout', () => ({
  useWorkbenchLayout: vi.fn(() => hoisted.layout),
}));
vi.mock('../../src/composables/useCreatorWriteWorkbench/useWorkbenchSelection', () => ({
  useWorkbenchSelection: vi.fn(() => hoisted.selection),
}));
vi.mock('../../src/composables/useCreatorWriteWorkbench/useWorkbenchCheckpoints', () => ({
  useWorkbenchCheckpoints: vi.fn(() => hoisted.checkpoints),
}));
vi.mock('../../src/composables/useCreatorWriteWorkbench/useWorkbenchQuality', () => ({
  useWorkbenchQuality: vi.fn(() => hoisted.quality),
}));
vi.mock('../../src/composables/useCreatorAgent.js', () => ({
  useCreatorAgent: vi.fn(() => ({ runPlan: vi.fn(), generating: { value: false }, statusLine: { value: '' }, candidates: { value: [] }, directorAdvice: { value: [] } })),
}));

import { useCreatorWriteWorkbench } from '../../src/composables/useCreatorWriteWorkbench.js';
import { useWorkbenchSelection as useWorkbenchSelectionMocked } from '../../src/composables/useCreatorWriteWorkbench/useWorkbenchSelection.js';
import { useWorkbenchCheckpoints as useWorkbenchCheckpointsMocked } from '../../src/composables/useCreatorWriteWorkbench/useWorkbenchCheckpoints.js';
import { useWorkbenchLayout as useWorkbenchLayoutMocked } from '../../src/composables/useCreatorWriteWorkbench/useWorkbenchLayout.js';
import { useWorkbenchQuality as useWorkbenchQualityMocked } from '../../src/composables/useCreatorWriteWorkbench/useWorkbenchQuality.js';

function mountWorkbench() {
  const uiProfile = ref<Record<string, unknown>>({}) as unknown as ComputedRef<Record<string, unknown>>;
  const overview = ref<Record<string, unknown> | null>({ slug: 's', name: 'n', creation_mode: 'companion' });
  const chapterBodyDraft = ref<string>('');
  const selectedChapter = ref<number | null>(null);
  const saveMessage = ref<string>('');
  const ctx = useCreatorWriteWorkbench({
    uiProfile, overview, chapterBodyDraft, selectedChapter, saveMessage,
  });
  return { ctx, uiProfile, overview, chapterBodyDraft, selectedChapter, saveMessage };
}

const EXPECTED_FIELDS = [
  // 12 Layout
  'workbenchEnabled','leftPanelCollapsed','humanFirstDesk','goalCardLines','consistencyItems',
  'consistencyPanelOpen','chapterEntities','isPanelVisible','isPanelCollapsed','isLeftRailPanelVisible',
  'creationMode','updateCreationMode',
  // 10 Selection
  'bodySelection','hasBodySelection','styleStrength','selectionLocked','allowWorldbuildingFill',
  'goalTag','captureBodySelection','applyTextToSelection','toggleSelectionLock','getControls',
  // 7 Checkpoints
  'checkpoints','diffCheckpointId','diffView','createCheckpoint','restoreCheckpoint',
  'openCheckpointDiff','closeCheckpointDiff',
  // 28 Quality (5 intent + 4 history + 4 hints + 3 lightValidation + 2 lightVal methods + 1 inlineMarkers + 2 conflict state + 3 focus + 2 generation state + 2 generation methods = 28)
  'intentText','intentGenre','intentMood','intentType','intentTheme',
  'intentHistory','saveIntentToHistory','loadIntentFromHistory','clearIntentHistory',
  'qualityHints','dismissQualityHint','syncQualityFromLightValidation','syncQualityFromLogicCheck',
  'lightValidationIssues','lightValidationSummary','lightValidationRunning',
  'runLightValidationNow','scheduleLightValidation','inlineConflictMarkers',
  'activeInlineConflictId','chapterBodyConflictHighlightActive','focusInlineConflict',
  'focusLightValidationIssue','clearInlineConflictFocus','generateIntensity','generateRunning',
  'startQuickWrite','stopGenerate',
  // 1 跨 computed
  'showInlineConflictGutter',
  // 1 agent
  'agent',
];

describe('useCreatorWriteWorkbench facade', () => {
  beforeEach(() => vi.clearAllMocks());

  it('returns all 59 public fields', () => {
    const { ctx } = mountWorkbench();
    expect(EXPECTED_FIELDS).toHaveLength(59);
    for (const f of EXPECTED_FIELDS) {
      expect(f in ctx).toBe(true);
    }
  });

  it('qualityHints returned is the same ref as selection.qualityHints', () => {
    const { ctx } = mountWorkbench();
    expect(ctx.qualityHints).toBe(hoisted.selection.qualityHints);
  });

  it('agent field exposes useCreatorAgent result', () => {
    const { ctx } = mountWorkbench();
    expect(ctx.agent).toBeDefined();
    expect(typeof ctx.agent.runPlan).toBe('function');
  });

  it('showInlineConflictGutter uses layout.isPanelVisible + quality.inlineConflictMarkers', () => {
    // Case 1: initial state — markers empty, isPanelVisible default true → false
    const { ctx: ctx1 } = mountWorkbench();
    expect(ctx1.showInlineConflictGutter.value).toBe(false);

    // Case 2: setup conditions before mounting — markers populated, isPanelVisible returns true → true
    hoisted.quality.inlineConflictMarkers.value = [{ id: 'x', paragraph: 1 } as never];
    hoisted.layout.isPanelVisible.mockReturnValue(true);
    const { ctx: ctx2 } = mountWorkbench();
    expect(ctx2.showInlineConflictGutter.value).toBe(true);

    // Case 3: isPanelVisible returns false → false (even with markers)
    hoisted.layout.isPanelVisible.mockReturnValue(false);
    const { ctx: ctx3 } = mountWorkbench();
    expect(ctx3.showInlineConflictGutter.value).toBe(false);
  });

  it('calls 4 submodules (Selection first, Quality last)', () => {
    mountWorkbench();
    const selOrder = (useWorkbenchSelectionMocked as unknown as { mock: { invocationCallOrder: number[] } }).mock.invocationCallOrder[0];
    const cpOrder = (useWorkbenchCheckpointsMocked as unknown as { mock: { invocationCallOrder: number[] } }).mock.invocationCallOrder[0];
    const layoutOrder = (useWorkbenchLayoutMocked as unknown as { mock: { invocationCallOrder: number[] } }).mock.invocationCallOrder[0];
    const qualityOrder = (useWorkbenchQualityMocked as unknown as { mock: { invocationCallOrder: number[] } }).mock.invocationCallOrder[0];
    expect(selOrder).toBeLessThan(cpOrder);
    expect(cpOrder).toBeLessThan(layoutOrder);
    expect(layoutOrder).toBeLessThan(qualityOrder);
  });

  it('agent injected into Quality via getAgent() callback', () => {
    const { ctx } = mountWorkbench();
    const qualityCall = (useWorkbenchQualityMocked as unknown as { mock: { calls: unknown[] } }).mock.calls[0];
    const deps = (qualityCall as unknown as [Record<string, unknown>])[0];
    expect(typeof deps.getAgent).toBe('function');
    const agent = (deps.getAgent as () => unknown)();
    expect(agent).toBe(ctx.agent);
  });
});
