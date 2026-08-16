/**
 * useAgentTask 子模块独立测试
 *
 * Phase 43: 为 Phase 19.6 useAgentTask 子模块添加专门测试。
 * 重点测试：消息 + 流式预览 + runPlan + 模拟数据生成。
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ref, computed } from 'vue';

const taskMocks = vi.hoisted(() => ({
  runCreatorAgentPlan: vi.fn(),
  runCreatorAgentPlanStream: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  runCreatorAgentPlan: (...args: unknown[]) => taskMocks.runCreatorAgentPlan(...args),
  runCreatorAgentPlanStream: (...args: unknown[]) => taskMocks.runCreatorAgentPlanStream(...args),
}));

import { useAgentTask } from '../../src/composables/useCreatorAgent/useAgentTask';

function mountAgentTask() {
  const executionMode = ref('preview');
  const agentLens = ref('author');
  const agentLensLabel = computed(() => '作者视角');
  const getSelection = () => ({ text: '', start: 0, end: 0 });
  const getChapterNum = (): number | null => 1;
  const getBodyDraft = (): string => '正文内容';
  const getControls = (): { styleStrength: number; selectionLocked: boolean; allowWorldbuildingFill: boolean; goalTag: string } => ({
    styleStrength: 1, selectionLocked: false, allowWorldbuildingFill: true, goalTag: 'pace',
  });
  const pendingPlan = ref<Record<string, unknown> | null>(null);
  const candidates = ref<Array<Record<string, unknown>>>([]);
  const directorAdvice = ref<Array<Record<string, unknown>>>([]);
  const annotations = ref<Array<Record<string, unknown>>>([]);
  const memoryAssetsCache = ref<Array<Record<string, unknown>>>([]);

  const ctx = useAgentTask({
    executionMode, agentLens, agentLensLabel,
    getSelection, getChapterNum, getBodyDraft, getControls,
    pendingPlan, candidates, directorAdvice, annotations, memoryAssetsCache,
  } as unknown as Parameters<typeof useAgentTask>[0]);
  return {
    ...ctx,
    pendingPlan, directorAdvice, annotations, candidates,
  };
}

describe('useAgentTask', () => {
  beforeEach(() => vi.clearAllMocks());

  it('initial state has empty messages', () => {
    const t = mountAgentTask();
    expect(t.messages.value).toEqual([]);
    expect(t.generating.value).toBe(false);
    expect(t.statusLine.value).toBe('');
  });

  it('initial streamDisplayText is empty', () => {
    const t = mountAgentTask();
    expect(t.streamDisplayText.value).toBe('');
    expect(t.streamPreviewText.value).toBe('');
  });

  it('pushMessage adds message to history', () => {
    const t = mountAgentTask();
    t.pushMessage('user', '帮我写章节');
    expect(t.messages.value).toHaveLength(1);
    expect(t.messages.value[0].role).toBe('user');
    expect(t.messages.value[0].text).toBe('帮我写章节');
  });

  it('pushMessage caps history at 12 entries', () => {
    const t = mountAgentTask();
    for (let i = 0; i < 20; i += 1) {
      t.pushMessage('user', `message-${i}`);
    }
    expect(t.messages.value.length).toBeLessThanOrEqual(13);
  });

  it('buildScope returns none when no selection and no chapter', () => {
    const executionMode = ref('preview');
    const agentLens = ref('author');
    const agentLensLabel = computed(() => '作者视角');
    const getSelection = () => ({ text: '', start: 0, end: 0 });
    const getChapterNum = (): number | null => null;
    const getBodyDraft = (): string => '正文内容';
    const getControls = (): { styleStrength: number; selectionLocked: boolean; allowWorldbuildingFill: boolean; goalTag: string } => ({
      styleStrength: 1, selectionLocked: false, allowWorldbuildingFill: true, goalTag: 'pace',
    });
    const pendingPlan = ref<Record<string, unknown> | null>(null);
    const candidates = ref<Array<Record<string, unknown>>>([]);
    const directorAdvice = ref<Array<Record<string, unknown>>>([]);
    const annotations = ref<Array<Record<string, unknown>>>([]);
    const memoryAssetsCache = ref<Array<Record<string, unknown>>>([]);
    const t = useAgentTask({
      executionMode, agentLens, agentLensLabel,
      getSelection, getChapterNum, getBodyDraft, getControls,
      pendingPlan, candidates, directorAdvice, annotations, memoryAssetsCache,
    } as unknown as Parameters<typeof useAgentTask>[0]);
    const scope = t.buildScope();
    expect(scope.type).toBe('none');
  });

  it('mockCandidates returns 3 candidates when styleStrength > 0', () => {
    const t = mountAgentTask();
    const cands = t.mockCandidates('base text', 'action', { styleStrength: 1, selectionLocked: false, allowWorldbuildingFill: true, goalTag: 'pace' });
    expect(cands).toHaveLength(3);
    expect(cands[0].id).toBe('steady');
    expect(cands[1].id).toBe('balanced');
    expect(cands[2].id).toBe('bold');
  });

  it('mockAdvice returns 3 advice items', () => {
    const t = mountAgentTask();
    const advice = t.mockAdvice('改写', { consequence: '风险' });
    expect(advice).toHaveLength(3);
  });

  it('mockAnnotations returns editor lens items', () => {
    const t = mountAgentTask();
    const items = t.mockAnnotations('editor', '改写');
    expect(items.length).toBeGreaterThan(0);
  });

  it('mockAnnotations returns reviewer lens items', () => {
    const t = mountAgentTask();
    const items = t.mockAnnotations('reviewer', '改写');
    expect(items.length).toBeGreaterThan(0);
  });

  it('mockAnnotations returns empty array for other lenses', () => {
    const t = mountAgentTask();
    expect(t.mockAnnotations('author', '改写')).toEqual([]);
  });

  it('scopeToApiPayload builds correct payload for selection', () => {
    const t = mountAgentTask();
    const payload = t.scopeToApiPayload({
      type: 'selection', label: '选区 · 10 字', selection: { text: 'hello', start: 0, end: 5 },
    });
    expect(payload.type).toBe('selection');
    expect(payload.selection_text).toBe('hello');
  });

  it('scopeToApiPayload builds correct payload for chapter', () => {
    const t = mountAgentTask();
    const payload = t.scopeToApiPayload({
      type: 'chapter', label: 'ch1 正文', chapter: 1,
    });
    expect(payload.type).toBe('chapter');
    expect(payload.chapter).toBe(1);
  });
});