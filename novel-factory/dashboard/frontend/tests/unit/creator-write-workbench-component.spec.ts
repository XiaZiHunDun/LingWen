// tests/unit/creator-write-workbench-component.spec.ts — CreatorWriteWorkbench.vue 挂载

import { describe, test, expect, vi, beforeEach } from 'vitest';
import { ref, computed, type Ref } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';
import CreatorWriteWorkbench from '../../src/components/creator/CreatorWriteWorkbench.vue';
import { CREATOR_WRITE_KEY, createCreatorWriteContext } from '../../src/components/creator/creatorWriteKey.js';
import {
  CREATOR_PRODUCT_TOOLS_KEY,
  createCreatorProductToolsContext,
} from '../../src/components/creator/creatorProductToolsKey.js';
import { useCreatorWriteWorkbench } from '../../src/composables/useCreatorWriteWorkbench.js';
import { byTestid } from '../helpers/by-testid';

type WriteWorkbench = ReturnType<typeof useCreatorWriteWorkbench>;

type WriteContext = {
  wb: WriteWorkbench;
  chapterBodyDraft: Ref<string>;
  overview: Ref<Record<string, unknown>>;
  selectedChapter: Ref<number | null>;
  uiProfile: Ref<Record<string, unknown>>;
};

vi.mock('../../src/api/index.js', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...(actual as object),
    runCreatorAgentPlan: vi.fn(),
    runCreatorAgentPlanStream: vi.fn(),
  };
});

import { runCreatorAgentPlan, runCreatorAgentPlanStream } from '../../src/api/index.js';

type WriteOverrides = {
  uiProfile?: Record<string, unknown>;
  overview?: Record<string, unknown>;
  body?: string;
  chapter?: number | null;
  deviations?: Array<Record<string, unknown>>;
  memoryAssets?: Array<Record<string, unknown>>;
  showLogicCheck?: boolean;
  logicCheckResult?: Record<string, unknown> | null;
};

function buildWriteContext(overrides: WriteOverrides = {}): { ctx: WriteContext; wb: WriteWorkbench } {
  const uiProfile = computed(() => ({
    creator_write_workbench: true,
    chapter_inline_edit: true,
    ...overrides.uiProfile,
  }));
  const overview = ref({
    creation_mode: 'companion',
    name: '测试书',
    chapters: [{ chapter: 1, has_body: false }],
    deviations: [],
    ...overrides.overview,
  });
  const chapterBodyDraft = ref(overrides.body ?? '林默走进雨里，望着远处的灯火。');
  const selectedChapter = ref(overrides.chapter ?? 1);
  const saveMessage = ref('');
  const logicCheckResult = ref(overrides.logicCheckResult ?? null);

  const wb = useCreatorWriteWorkbench({
    uiProfile,
    overview,
    chapterBodyDraft,
    selectedChapter,
    saveMessage,
    logicCheckResult,
    visibleDeviations: computed(() => overrides.deviations ?? []),
    memoryAssets: ref(overrides.memoryAssets ?? [
      { id: 'c1', kind: 'character', name: '林默', chapters: [1], excerpt: '主角' },
    ]),
  });

  const ctx = createCreatorWriteContext({
    wb,
    overview,
    chapterBodyDraft,
    selectedChapter,
    uiProfile,
    showCompanionLogicCheckInWrite: computed(() => overrides.showLogicCheck ?? false),
    logicCheckRunning: ref(false),
    logicCheckResult,
    runCompanionLogicCheck: vi.fn(),
    handleLogicCheckIssueClick: vi.fn(),
    onLogicCheckIssueKeydown: vi.fn(),
    activeLogicCheckIssueIdx: ref(null),
  }) as WriteContext;

  return { ctx, wb };
}

const productToolsStub = createCreatorProductToolsContext({
  focusMemoryEntity: vi.fn(),
  goToSettingsForAsset: vi.fn(),
});

function mountWorkbench(overrides: WriteOverrides = {}) {
  const { ctx, wb } = buildWriteContext(overrides);
  const wrapper = mount(CreatorWriteWorkbench, {
    global: {
      provide: {
        [CREATOR_WRITE_KEY]: ctx,
        [CREATOR_PRODUCT_TOOLS_KEY]: productToolsStub,
      },
    },
    slots: {
      default: '<textarea data-testid="editor-slot">编辑区</textarea>',
      chapters: '<div data-testid="chapter-slot">章节列表</div>',
    },
  });
  return { wrapper, writeCtx: ctx, wb };
}

async function openAdvancedTools(wrapper: ReturnType<typeof mount>) {
  const details = wrapper.find(byTestid('write-advanced-tools'));
  const el = details.element as HTMLDetailsElement;
  el.open = true;
  await details.trigger('toggle');
  await flushPromises();
}

describe('CreatorWriteWorkbench component', () => {
  beforeEach(() => {
    vi.mocked(runCreatorAgentPlan).mockReset();
    vi.mocked(runCreatorAgentPlanStream).mockReset();
    vi.mocked(runCreatorAgentPlanStream).mockRejectedValue(new Error('offline'));
    vi.mocked(runCreatorAgentPlan).mockRejectedValue(new Error('offline'));
  });

  test('human-first desk shows micro task bar and editor slot', () => {
    const { wrapper } = mountWorkbench({ body: '短稿' });
    expect(wrapper.find(byTestid('creator-write-workbench')).classes()).toContain('write-workbench--human-first');
    expect(wrapper.find(byTestid('write-micro-task-bar')).exists()).toBe(true);
    expect(wrapper.find(byTestid('write-micro-task-fill')).exists()).toBe(true);
    expect(wrapper.find(byTestid('editor-slot')).exists()).toBe(true);
  });

  test('collapses left chapter rail on human-first desk', async () => {
    const { wrapper, writeCtx } = mountWorkbench();
    expect(wrapper.find(byTestid('chapter-slot')).exists()).toBe(true);
    await wrapper.find(byTestid('write-workbench-collapse-btn')).trigger('click');
    expect(writeCtx.wb.leftPanelCollapsed).toBe(true);
    expect(wrapper.find(byTestid('chapter-slot')).exists()).toBe(false);
    await wrapper.find(byTestid('write-workbench-collapse-btn')).trigger('click');
    expect(wrapper.find(byTestid('chapter-slot')).exists()).toBe(true);
  });

  test('shows director paths in main area for companion desk', () => {
    const { wrapper } = mountWorkbench();
    expect(wrapper.find(byTestid('write-director-paths-panel-main')).exists()).toBe(true);
    expect(wrapper.find(byTestid('director-path-faster')).exists()).toBe(true);
  });

  test('studio layout uses non-human-first branch without advanced drawer', async () => {
    const { wrapper, wb } = mountWorkbench({
      overview: { creation_mode: 'studio', name: '工厂书' },
    });
    expect(wrapper.find(byTestid('creator-write-workbench')).classes()).not.toContain('write-workbench--human-first');
    expect(wrapper.find(byTestid('write-advanced-tools')).exists()).toBe(false);
    await wb.agent.runRewritePreset('concrete');
    await flushPromises();
    expect(wb.agent.candidates.value.length).toBeGreaterThan(0);
    expect(wrapper.find(byTestid('write-micro-task-bar')).exists()).toBe(false);
  });

  test('confirms director plan apply from human-first plan card', async () => {
    const { wrapper, writeCtx } = mountWorkbench();
    await writeCtx.wb.agent.runRewritePreset('concrete');
    await flushPromises();
    writeCtx.wb.agent.selectCandidate('steady');
    await flushPromises();
    const confirm = wrapper.findAll(byTestid('write-director-confirm-btn')).find((b) => !b.attributes('disabled'));
    expect(confirm).toBeTruthy();
    await confirm!.trigger('click');
    expect(String(writeCtx.chapterBodyDraft)).toContain('稳健候选');
  });

  test('toggles style strength slider on human-first main area', async () => {
    const { wrapper, writeCtx } = mountWorkbench();
    expect(wrapper.find(byTestid('write-style-bar-main')).exists()).toBe(true);
    const slider = wrapper.find(byTestid('style-strength-slider'));
    expect(slider.exists()).toBe(true);
    await slider.setValue('1');
    expect(writeCtx.wb.styleStrength).toBe(1);
  });

  test('toggles goal tag on human-first main area', async () => {
    const { wrapper, writeCtx } = mountWorkbench();
    expect(wrapper.find(byTestid('write-goal-tags-main')).exists()).toBe(true);
    const tag = wrapper.find(byTestid('goal-tag-suspense'));
    expect(tag.exists()).toBe(true);
    await tag.trigger('click');
    expect(writeCtx.wb.goalTag).toBe('suspense');
  });

  test('switches agent lens on human-first main area', async () => {
    const { wrapper, writeCtx } = mountWorkbench();
    expect(wrapper.find(byTestid('write-agent-lens-main')).exists()).toBe(true);
    const editorLens = wrapper.find(byTestid('agent-lens-editor'));
    expect(editorLens.exists()).toBe(true);
    await editorLens.trigger('click');
    expect(writeCtx.wb.agent.agentLens).toBe('editor');
  });

  test('shows agent annotations on human-first main area after local plan', async () => {
    const { wrapper, writeCtx } = mountWorkbench();
    writeCtx.wb.agent.setAgentLens('editor');
    await writeCtx.wb.agent.runRewritePreset('concrete');
    await flushPromises();
    expect(wrapper.find(byTestid('write-agent-annotations-main')).exists()).toBe(true);
    expect(wrapper.find(byTestid('agent-annotation-e1')).exists()).toBe(true);
  });

  test('toggles worldbuilding fill on human-first main area', async () => {
    const { wrapper, writeCtx } = mountWorkbench();
    expect(wrapper.find(byTestid('write-worldbuilding-toggle-main')).exists()).toBe(true);
    const toggle = wrapper.find(byTestid('allow-worldbuilding-toggle'));
    expect(toggle.exists()).toBe(true);
    await toggle.trigger('click');
    expect(writeCtx.wb.allowWorldbuildingFill).toBe(true);
  });

  test('shows companion logic check toolbar when enabled', async () => {
    const { wrapper } = mountWorkbench({
      showLogicCheck: true,
      uiProfile: { primary_action: 'logic_check' },
      logicCheckResult: {
        passed: false,
        p0_count: 1,
        issues: [{ severity: 'P0', title: '时间线', chapter: 1 }],
      },
    });
    expect(wrapper.find(byTestid('companion-logic-check-write')).exists()).toBe(true);
    expect(wrapper.find(byTestid('run-companion-logic-check-btn')).exists()).toBe(true);
    expect(wrapper.find(byTestid('companion-logic-check-write-result')).text()).toContain('未通过');
  });

  test('undo last apply from advanced tools version stack', async () => {
    const { wrapper, writeCtx } = mountWorkbench();
    await writeCtx.wb.agent.runRewritePreset('concrete');
    await flushPromises();
    writeCtx.wb.agent.selectCandidate('steady');
    writeCtx.wb.agent.confirmApply();
    await openAdvancedTools(wrapper);
    const undo = wrapper.find(byTestid('write-undo-last-btn'));
    expect(undo.exists()).toBe(true);
    await undo.trigger('click');
    expect(writeCtx.wb.agent.statusLine).toContain('恢复');
  });

  test('dismisses quality hint inside advanced tools', async () => {
    const { wrapper, wb } = mountWorkbench();
    wb.syncQualityFromLogicCheck({
      passed: false,
      issues: [{ severity: 'P0', title: '节奏偏慢' }],
    });
    await openAdvancedTools(wrapper);
    const dismiss = wrapper.findAll(byTestid('write-quality-bar')).flatMap((bar) =>
      bar.findAll('button').filter((b) => b.text() === '忽略'),
    );
    expect(dismiss.length).toBeGreaterThan(0);
    const before = wb.qualityHints.value.length;
    await dismiss[0].trigger('click');
    expect(wb.qualityHints.value.length).toBe(before - 1);
  });

  test('runs director path from main panel button', async () => {
    const { wrapper } = mountWorkbench();
    await wrapper.find(byTestid('director-path-run-faster')).trigger('click');
    await flushPromises();
    expect(wrapper.find(byTestid('write-candidate-dock')).exists()).toBe(true);
  });
});
