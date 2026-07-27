// tests/unit/creator-write-workbench-component.spec.ts — CreatorWriteWorkbench.vue 挂载

import { describe, test, expect, vi } from 'vitest';
import { ref, reactive } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';
import CreatorWriteWorkbench from '../../src/components/creator/CreatorWriteWorkbench.vue';
import { CREATOR_WRITE_KEY } from '../../src/components/creator/creatorWriteKey.js';
import { byTestid } from '../helpers/by-testid';

// Mock child components
vi.mock('../../src/components/creator/CreatorWriteHeader.vue', () => ({
  default: {
    name: 'CreatorWriteHeader',
    template: `
      <div data-testid="stub-header">
        <button data-testid="stub-toggle-chat" @click="$emit('toggle-chat')">Chat</button>
        <button data-testid="stub-mode-change" @click="$emit('mode-change', 'advance')">Mode</button>
      </div>
    `,
  },
}));

vi.mock('../../src/components/creator/CreatorWriteSidebar.vue', () => ({
  default: {
    name: 'CreatorWriteSidebar',
    template: `<div data-testid="stub-sidebar"><slot name="chapters" /></div>`,
  },
}));

vi.mock('../../src/components/creator/CreatorWriteChat.vue', () => ({
  default: {
    name: 'CreatorWriteChat',
    props: ['showChatPanel'],
    template: `<div data-testid="stub-chat" v-if="showChatPanel">Chat Panel</div>`,
  },
}));

vi.mock('../../src/components/creator/CreatorWriteFooter.vue', () => ({
  default: {
    name: 'CreatorWriteFooter',
    template: `
      <div data-testid="stub-footer">
        <button @click="$emit('open-outline')">Outline</button>
        <button @click="$emit('open-stats')">Stats</button>
      </div>
    `,
  },
}));

function buildWorkbenchContext(overrides: Record<string, unknown> = {}) {
  const chapterBodyDraft = ref('测试正文章节内容');
  const selectedChapter = ref(1);
  const overview = ref({
    name: '测试作品',
    chapters_written: 5,
    max_chapter: 20,
    ...(overrides.overview as object || {}),
  });

  const wb = reactive({
    leftPanelCollapsed: false,
    creationMode: 'companion',
    intentText: '',
    intentMood: '',
    goalCardLines: { line1: '目标1', line2: '目标2' },
    generateRunning: false,
    agent: { generating: false },
    startQuickWrite: vi.fn(),
    updateCreationMode: vi.fn().mockResolvedValue(undefined),
    ...(overrides.wb as object || {}),
  });

  const ctx = reactive({
    wb,
    chapterBodyDraft,
    selectedChapter,
    overview,
    openOutline: vi.fn(),
    openStats: vi.fn(),
  });

  return { ctx, wb };
}

function mountWorkbench(overrides: Record<string, unknown> = {}) {
  const { ctx, wb } = buildWorkbenchContext(overrides);
  const wrapper = mount(CreatorWriteWorkbench, {
    global: {
      provide: {
        [CREATOR_WRITE_KEY]: ctx,
      },
    },
    slots: {
      default: '<div data-testid="editor-slot">编辑区</div>',
      chapters: '<div data-testid="chapter-slot">章节列表</div>',
    },
  });
  return { wrapper, ctx, wb };
}

describe('CreatorWriteWorkbench component', () => {
  test('renders workbench structure with all child components', () => {
    const { wrapper } = mountWorkbench();
    expect(wrapper.find(byTestid('writer-desk')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-header')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-sidebar')).exists()).toBe(true);
    expect(wrapper.find(byTestid('stub-footer')).exists()).toBe(true);
    expect(wrapper.find(byTestid('editor-slot')).exists()).toBe(true);
  });

  test('chat panel toggles visibility', async () => {
    const { wrapper } = mountWorkbench();
    // Initially chat should not be visible
    expect(wrapper.find(byTestid('stub-chat')).exists()).toBe(false);
    // Click toggle chat button
    await wrapper.find(byTestid('stub-toggle-chat')).trigger('click');
    await flushPromises();
    // Chat should now be visible
    expect(wrapper.find(byTestid('stub-chat')).exists()).toBe(true);
    // Click again to close
    await wrapper.find(byTestid('stub-toggle-chat')).trigger('click');
    await flushPromises();
    expect(wrapper.find(byTestid('stub-chat')).exists()).toBe(false);
  });

  test('handles mode change via header event', async () => {
    const { wrapper, wb } = mountWorkbench();
    await wrapper.find(byTestid('stub-mode-change')).trigger('click');
    await flushPromises();
    expect(wb.updateCreationMode).toHaveBeenCalledWith('advance');
  });

  test('sidebar collapse toggles via CSS class', async () => {
    const { wrapper, wb } = mountWorkbench();
    // Initially not collapsed
    expect(wrapper.find(byTestid('writer-desk')).classes()).not.toContain('writer-desk--sidebar-collapsed');
    // Simulate collapse
    wb.leftPanelCollapsed = true;
    await flushPromises();
    expect(wrapper.find(byTestid('writer-desk')).classes()).toContain('writer-desk--sidebar-collapsed');
  });

  test('shows empty state when no chapter body', async () => {
    const { wrapper, ctx } = mountWorkbench({
      wb: {
        creationMode: 'companion',
      },
    });
    // Set empty body directly on context
    ctx.chapterBodyDraft = '';
    await flushPromises();
    // Empty state should show
    expect(wrapper.text()).toContain('准备好开始写作了吗');
    expect(wrapper.text()).toContain('开始写作');
  });

  test('empty state changes based on creation mode', async () => {
    const { wrapper, ctx, wb } = mountWorkbench();
    wb.creationMode = 'advance';
    ctx.chapterBodyDraft = '';
    await flushPromises();
    expect(wrapper.text()).toContain('按卷纲推进');
    expect(wrapper.text()).toContain('推进章节');
  });

  test('footer outline and stats actions work', async () => {
    const { wrapper, ctx } = mountWorkbench();
    await wrapper.findAll('button').find(b => b.text() === 'Outline')!.trigger('click');
    expect(ctx.openOutline).toHaveBeenCalled();
    await wrapper.findAll('button').find(b => b.text() === 'Stats')!.trigger('click');
    expect(ctx.openStats).toHaveBeenCalled();
  });

  test('renders with studio mode configuration', async () => {
    const { wrapper, ctx, wb } = mountWorkbench({
      wb: {
        creationMode: 'studio',
      },
    });
    wb.creationMode = 'studio';
    ctx.chapterBodyDraft = '';
    await flushPromises();
    expect(wrapper.text()).toContain('工厂模式就绪');
    expect(wrapper.text()).toContain('启动产线');
  });

  test('editor slot content renders correctly', () => {
    const { wrapper } = mountWorkbench();
    expect(wrapper.find(byTestid('editor-slot')).text()).toContain('编辑区');
  });

  test('chapter slot content renders in sidebar', async () => {
    const { wrapper } = mountWorkbench();
    expect(wrapper.find(byTestid('chapter-slot')).text()).toContain('章节列表');
  });
});
