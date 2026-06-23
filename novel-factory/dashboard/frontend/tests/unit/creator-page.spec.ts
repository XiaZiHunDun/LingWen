// tests/unit/creator-page.spec.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

const creatorMocks = vi.hoisted(() => ({
  fetchCreatorOverview: vi.fn(),
}));

vi.mock('../../src/api/index.js', () => ({
  fetchCreatorOverview: creatorMocks.fetchCreatorOverview,
}));

vi.mock('../../src/composables/useStudioProject.js', () => ({
  useStudioProject: () => ({
    projectRevision: { value: 0 },
  }),
}));

import CreatorPage from '../../src/pages/CreatorPage.vue';

describe('CreatorPage', () => {
  beforeEach(() => {
    creatorMocks.fetchCreatorOverview.mockResolvedValue({
      slug: 'demo-book',
      name: '演示书',
      creation_mode: 'companion',
      quality_profile: 'creator_relaxed',
      max_chapter: 12,
      chapters_written: 3,
      coverage_pct: 25,
      chapters: [
        { chapter: 1, has_body: true, has_outline: true, word_count: 2000, excerpt: '第一章' },
        { chapter: 2, has_body: false, has_outline: true, word_count: 0, excerpt: null },
      ],
      volume_summaries: [],
      pillars_excerpt: '支柱',
      pillars_path: '/docs/novel-pillars.md',
      global_outline_excerpt: '大纲',
      global_outline_path: '/全局大纲.md',
      p0_count: 0,
      quality_report_available: true,
      companion_check_cmd: 'bash scripts/run-companion-check.sh',
      advance_batch_hint: 'bash scripts/run-advance-volume.sh 1 10 10 0.30',
      notify_per_chapter: true,
      advance_volume_summary: false,
    });
  });

  it('renders three columns and mode badge', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();

    expect(wrapper.find('[data-testid="creator-grid"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="column-write"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="column-pulse"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="column-settings"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="creation-mode-badge"]').text()).toContain('陪伴');
  });
});
