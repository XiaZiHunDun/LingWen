/**
 * Phase 76 — CreatorDeviationFinalize.vue unit tests.
 *
 * CreatorDeviationFinalize is the deviation close-out checklist
 * (REQ-001 slice E). For each batch deviation, renders a toggle
 * "标记已复核" / "已复核 ✓". Reviewed state persists per
 * job_id in localStorage. Reset button clears. All reviewed →
 * "全部差异已收尾".
 *
 * 8 tests covering render states + toggle + reset + persistence.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { ref } from 'vue';
import type { StudioBatchJobResponseDTO } from '@/api/studio';
import type { BatchEvent } from '@/composables/useBatchEventStream';

// Stub usePilotBatch — return refs (so component can do .value).
// Phase 110 fix: type refs explicitly to match usePilotBatch's actual
// `activeJob: ref<StudioBatchJobResponseDTO | null>(null)` shape.
// Bare `ref(null)` would give `Ref<null>` and tsc would reject object assignments.
// chapterEventsRef uses a permissive test-local shape because the component
// only reads .chapter_num + .status from the events; real BatchEvent has
// { type, data, receivedAt } but the test fixture here is a denormalized
// view (the real composable derives chapter_num from BatchEvent.data).
type TestChapterEvent = { chapter_num: number; status: string };
const activeJobRef = ref<StudioBatchJobResponseDTO | null>(null);
const chapterEventsRef = ref<TestChapterEvent[]>([]);

vi.mock('@/composables/usePilotBatch', () => ({
  usePilotBatch: () => ({
    activeJob: activeJobRef,
    chapterEvents: chapterEventsRef,
  }),
}));

import CreatorDeviationFinalize from '@/components/creator/CreatorDeviationFinalize.vue';

beforeEach(() => {
  activeJobRef.value = null;
  chapterEventsRef.value = [];
  window.localStorage.clear();
});

// ---------------------------------------------------------------------------
// Render states
// ---------------------------------------------------------------------------

describe('CreatorDeviationFinalize — render states', () => {
  it('renders empty state when no active batch', async () => {
    const wrapper = mount(CreatorDeviationFinalize);
    await flushPromises();
    expect(wrapper.find('[data-testid="creator-deviation-finalize-empty"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="creator-deviation-finalize-list"]').exists()).toBe(false);
  });

  it('renders clean state when batch exists but no deviations', async () => {
    activeJobRef.value = { job_id: 'job-1', status: 'running', start_chapter: 1, end_chapter: 5 } as unknown as StudioBatchJobResponseDTO;
    chapterEventsRef.value = [
      { chapter_num: 1, status: 'completed' },
      { chapter_num: 2, status: 'completed' },
      { chapter_num: 3, status: 'completed' },
    ];
    const wrapper = mount(CreatorDeviationFinalize);
    await flushPromises();
    expect(wrapper.find('[data-testid="creator-deviation-finalize-clean"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="creator-deviation-finalize-list"]').exists()).toBe(false);
  });

  it('renders list when there are deviations', async () => {
    // ch3 completed but ch1, ch2 not — deviations on ch3.
    activeJobRef.value = { job_id: 'job-1', status: 'running', start_chapter: 1, end_chapter: 5 } as unknown as StudioBatchJobResponseDTO;
    chapterEventsRef.value = [{ chapter_num: 3, status: 'completed' }];
    const wrapper = mount(CreatorDeviationFinalize);
    await flushPromises();
    expect(wrapper.find('[data-testid="creator-deviation-finalize-list"]').exists()).toBe(true);
    const toggles = wrapper.findAll('[data-testid^="creator-deviation-finalize-toggle-"]');
    expect(toggles).toHaveLength(1);
    expect(toggles[0].text()).toContain('标记已复核');
  });
});

// ---------------------------------------------------------------------------
// Toggle
// ---------------------------------------------------------------------------

describe('CreatorDeviationFinalize — toggle', () => {
  it('toggles a deviation from unreviewed to reviewed', async () => {
    activeJobRef.value = { job_id: 'job-1', status: 'running', start_chapter: 1, end_chapter: 5 } as unknown as StudioBatchJobResponseDTO;
    chapterEventsRef.value = [{ chapter_num: 3, status: 'completed' }];
    const wrapper = mount(CreatorDeviationFinalize);
    await flushPromises();

    const toggle = wrapper.find('[data-testid="creator-deviation-finalize-toggle-3"]');
    expect(toggle.text()).toContain('标记已复核');

    await toggle.trigger('click');
    expect(toggle.text()).toContain('已复核 ✓');
    expect(toggle.classes()).toContain('is-reviewed');
  });

  it('updates progress counter when toggling', async () => {
    activeJobRef.value = { job_id: 'job-1', status: 'running', start_chapter: 1, end_chapter: 5 } as unknown as StudioBatchJobResponseDTO;
    chapterEventsRef.value = [
      { chapter_num: 3, status: 'completed' },
      { chapter_num: 5, status: 'completed' },
    ];
    const wrapper = mount(CreatorDeviationFinalize);
    await flushPromises();
    expect(wrapper.find('[data-testid="creator-deviation-finalize-progress"]').text()).toContain('0/2');

    await wrapper.find('[data-testid="creator-deviation-finalize-toggle-3"]').trigger('click');
    expect(wrapper.find('[data-testid="creator-deviation-finalize-progress"]').text()).toContain('1/2');
  });

  it('shows "全部差异已收尾" when all deviations reviewed', async () => {
    activeJobRef.value = { job_id: 'job-1', status: 'running', start_chapter: 1, end_chapter: 5 } as unknown as StudioBatchJobResponseDTO;
    chapterEventsRef.value = [{ chapter_num: 3, status: 'completed' }];
    const wrapper = mount(CreatorDeviationFinalize);
    await flushPromises();

    expect(wrapper.find('[data-testid="creator-deviation-finalize-done"]').exists()).toBe(false);
    await wrapper.find('[data-testid="creator-deviation-finalize-toggle-3"]').trigger('click');
    expect(wrapper.find('[data-testid="creator-deviation-finalize-done"]').exists()).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// Reset
// ---------------------------------------------------------------------------

describe('CreatorDeviationFinalize — reset', () => {
  it('clears all reviewed state when reset is clicked', async () => {
    activeJobRef.value = { job_id: 'job-1', status: 'running', start_chapter: 1, end_chapter: 5 } as unknown as StudioBatchJobResponseDTO;
    chapterEventsRef.value = [
      { chapter_num: 3, status: 'completed' },
      { chapter_num: 5, status: 'completed' },
    ];
    const wrapper = mount(CreatorDeviationFinalize);
    await flushPromises();

    // Mark both reviewed.
    await wrapper.find('[data-testid="creator-deviation-finalize-toggle-3"]').trigger('click');
    await wrapper.find('[data-testid="creator-deviation-finalize-toggle-5"]').trigger('click');
    expect(wrapper.find('[data-testid="creator-deviation-finalize-progress"]').text()).toContain('2/2');

    // Reset.
    await wrapper.find('[data-testid="creator-deviation-finalize-reset"]').trigger('click');
    expect(wrapper.find('[data-testid="creator-deviation-finalize-progress"]').text()).toContain('0/2');
  });
});

// ---------------------------------------------------------------------------
// localStorage persistence per job_id
// ---------------------------------------------------------------------------

describe('CreatorDeviationFinalize — localStorage persistence', () => {
  it('restores reviewed state from localStorage on mount for the current job', async () => {
    // Pre-populate localStorage for job-1 with [3].
    window.localStorage.setItem(
      'creator-deviation-review:job-1',
      JSON.stringify([3]),
    );
    activeJobRef.value = { job_id: 'job-1', status: 'running', start_chapter: 1, end_chapter: 5 } as unknown as StudioBatchJobResponseDTO;
    chapterEventsRef.value = [{ chapter_num: 3, status: 'completed' }];
    const wrapper = mount(CreatorDeviationFinalize);
    await flushPromises();

    const toggle = wrapper.find('[data-testid="creator-deviation-finalize-toggle-3"]');
    expect(toggle.text()).toContain('已复核 ✓');
    // localStorage preserved + count updated.
    expect(wrapper.find('[data-testid="creator-deviation-finalize-progress"]').text()).toContain('1/1');
  });
});
