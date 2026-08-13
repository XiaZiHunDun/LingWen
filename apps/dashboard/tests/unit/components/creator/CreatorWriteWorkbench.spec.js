import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { reactive, ref, nextTick } from 'vue';
import CreatorWriteWorkbench from '../../../../src/components/creator/CreatorWriteWorkbench.vue';
import { CREATOR_WRITE_KEY } from '../../../../src/components/creator/creatorWriteKey.js';

describe('CreatorWriteWorkbench', () => {
  let mockIntentText;
  let mockChapterBodyDraft;
  let mockWb;
  let mockProvide;

  beforeEach(() => {
    vi.clearAllMocks();
    mockIntentText = ref('');
    mockChapterBodyDraft = ref('');
    mockWb = reactive({
      intentText: mockIntentText,
      intentMood: ref(''),
      goalCardLines: { line1: '目标1', line2: '目标2' },
      leftPanelCollapsed: false,
      startQuickWrite: vi.fn(),
      saveDraft: vi.fn(),
      updateCreationMode: vi.fn(),
      generateRunning: false,
      agent: { generating: false },
      creationMode: ref('companion'),
    });
    mockProvide = {
      [CREATOR_WRITE_KEY]: reactive({
        wb: mockWb,
        overview: { chapters_written: 0, max_chapter: 36 },
        chapterBodyDraft: mockChapterBodyDraft,
        openOutline: vi.fn(),
        openStats: vi.fn(),
      }),
    };
  });

  it('renders writer-desk container with correct structure', () => {
    const wrapper = mount(CreatorWriteWorkbench, {
      global: { provide: mockProvide },
      slots: { chapters: '<div>章节列表</div>' },
    });
    expect(wrapper.find('[data-testid="writer-desk"]').exists()).toBe(true);
    expect(wrapper.find('.writer-desk__body').exists()).toBe(true);
    expect(wrapper.find('.writer-desk__editor').exists()).toBe(true);
  });

  it('shows empty state when body is empty', async () => {
    const wrapper = mount(CreatorWriteWorkbench, {
      global: { provide: mockProvide },
      slots: { chapters: '<div>章节列表</div>' },
    });
    await nextTick();
    expect(wrapper.find('.writer-desk__empty-state').exists()).toBe(true);
    expect(wrapper.find('.writer-desk__empty-state-title').text()).toContain('准备好开始写作');
  });

  it('empty state button triggers startQuickWrite', async () => {
    const wrapper = mount(CreatorWriteWorkbench, {
      global: { provide: mockProvide },
      slots: { chapters: '<div>章节列表</div>' },
    });
    await nextTick();
    const btn = wrapper.find('.writer-desk__empty-state-btn');
    expect(btn.exists()).toBe(true);
    await btn.trigger('click');
    expect(mockWb.startQuickWrite).toHaveBeenCalled();
  });

  it('applies different empty state config by creation mode', async () => {
    mockWb.creationMode = 'advance';
    const wrapper = mount(CreatorWriteWorkbench, {
      global: { provide: mockProvide },
      slots: { chapters: '<div>章节列表</div>' },
    });
    await nextTick();
    expect(wrapper.find('.writer-desk__empty-state--advance').exists()).toBe(true);
    expect(wrapper.find('.writer-desk__empty-state-title').text()).toContain('按卷纲推进');
  });

  it('applies sidebar collapsed class when leftPanelCollapsed is true', async () => {
    mockWb.leftPanelCollapsed = true;
    const wrapper = mount(CreatorWriteWorkbench, {
      global: { provide: mockProvide },
      slots: { chapters: '<div>章节列表</div>' },
    });
    await nextTick();
    expect(wrapper.find('.writer-desk--sidebar-collapsed').exists()).toBe(true);
  });

  it('renders default slot content in editor area', () => {
    const wrapper = mount(CreatorWriteWorkbench, {
      global: { provide: mockProvide },
      slots: {
        chapters: '<div>章节列表</div>',
        default: '<div class="custom-editor">自定义编辑器</div>',
      },
    });
    expect(wrapper.find('.custom-editor').exists()).toBe(true);
  });

  it('toggles chat panel when header chat button clicked', async () => {
    const wrapper = mount(CreatorWriteWorkbench, {
      global: { provide: mockProvide },
      slots: { chapters: '<div>章节列表</div>' },
    });
    expect(wrapper.find('.writer-desk--chat-open').exists()).toBe(false);
  });

  it('has studio mode empty state config', async () => {
    mockWb.creationMode = 'studio';
    const wrapper = mount(CreatorWriteWorkbench, {
      global: { provide: mockProvide },
      slots: { chapters: '<div>章节列表</div>' },
    });
    await nextTick();
    expect(wrapper.find('.writer-desk__empty-state--studio').exists()).toBe(true);
    expect(wrapper.find('.writer-desk__empty-state-title').text()).toContain('工厂模式就绪');
  });
});
