import { describe, expect, it, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import AskPage from '../../src/pages/AskPage.vue';

vi.mock('../../src/composables/useDashboardNav.js', () => ({
  useDashboardNav: () => ({
    navigateTo: vi.fn(),
  }),
}));

vi.mock('../../src/composables/useStudioProject.js', () => ({
  useStudioProject: () => ({
    activeSlug: { value: 'demo' },
  }),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorOverview: vi.fn().mockResolvedValue({ name: '测试书', chapters_written: 2 }),
  fetchStudioSummary: vi.fn().mockResolvedValue({ slug: 'demo', name: '测试书' }),
  queryCreatorMemory: vi.fn().mockResolvedValue({ hits: [] }),
}));

describe('AskPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders welcome and suggestions', async () => {
    const w = mount(AskPage);
    await flushPromises();
    expect(w.find('[data-testid="ask-page"]').exists()).toBe(true);
    expect(w.find('[data-testid="ask-suggestion-new-book"]').exists()).toBe(true);
    expect(w.text()).toContain('问进度');
  });

  it('sends message on submit', async () => {
    const w = mount(AskPage);
    await flushPromises();
    await w.find('[data-testid="ask-input"]').setValue('这本书进度如何');
    await w.find('[data-testid="ask-send-btn"]').trigger('click');
    await flushPromises();
    expect(w.find('[data-testid="ask-messages"]').text()).toContain('进度');
  });
});
