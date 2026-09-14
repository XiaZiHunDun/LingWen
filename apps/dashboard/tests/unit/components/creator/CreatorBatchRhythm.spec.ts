/**
 * Phase 75 — CreatorBatchRhythm.vue unit tests.
 *
 * CreatorBatchRhythm is the read-only batch progress visualization
 * (REQ-001 slice C). Renders batch range + chapter band cells
 * (done / deviating / pending) + deviations list + progress bar.
 *
 * Tests mock usePilotBatch composable + verify component handles
 * activeJob / chapterEvents / isJobActive reactive state correctly.
 *
 * 7 tests covering empty state + loaded states + deviations.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';

// Stub composable — return refs directly so component can do `.value`.
const activeJobRef = ref(null);
const chapterEventsRef = ref([]);
const isJobActiveRef = ref(false);
const refreshActiveMock = vi.fn();

vi.mock('@/composables/usePilotBatch', () => ({
  usePilotBatch: () => ({
    activeJob: activeJobRef,
    chapterEvents: chapterEventsRef,
    isJobActive: isJobActiveRef,
    refreshActive: refreshActiveMock,
  }),
}));

// Import after vi.mock so mocks are in place.
import { ref } from 'vue';
import CreatorBatchRhythm from '@/components/creator/CreatorBatchRhythm.vue';

beforeEach(() => {
  activeJobRef.value = null;
  chapterEventsRef.value = [];
  isJobActiveRef.value = false;
  refreshActiveMock.mockClear();
});

// ---------------------------------------------------------------------------
// Mount + empty state
// ---------------------------------------------------------------------------

describe('CreatorBatchRhythm — mount + empty state', () => {
  it('calls refreshActive on mount', async () => {
    mount(CreatorBatchRhythm);
    await flushPromises();
    expect(refreshActiveMock).toHaveBeenCalledTimes(1);
  });

  it('renders the empty-state message when no active batch', async () => {
    const wrapper = mount(CreatorBatchRhythm);
    await flushPromises();
    expect(wrapper.find('[data-testid="creator-batch-rhythm-empty"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="creator-batch-rhythm-band"]').exists()).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// Loaded state — happy path
// ---------------------------------------------------------------------------

describe('CreatorBatchRhythm — loaded state (no deviations)', () => {
  it('renders status label + range + progress for running batch', async () => {
    activeJobRef.value = { status: 'running', start_chapter: 1, end_chapter: 5 };
    chapterEventsRef.value = [
      { chapter_num: 1, status: 'completed' },
      { chapter_num: 2, status: 'completed' },
    ];
    const wrapper = mount(CreatorBatchRhythm);
    await flushPromises();
    expect(wrapper.find('[data-testid="creator-batch-rhythm-empty"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="creator-batch-rhythm-band"]').exists()).toBe(true);
    // Status label is '批改中' for running.
    expect(wrapper.text()).toContain('批改中');
    // Range (display text uses padded format ch001 / ch005).
    expect(wrapper.text()).toContain('ch001');
    expect(wrapper.text()).toContain('ch005');
    // Progress: 2/5.
    expect(wrapper.find('[data-testid="creator-batch-rhythm-progress"]').text()).toContain('2/5');
  });

  it('renders 5 band cells (one per chapter in range)', async () => {
    activeJobRef.value = { status: 'running', start_chapter: 1, end_chapter: 5 };
    chapterEventsRef.value = [];
    const wrapper = mount(CreatorBatchRhythm);
    await flushPromises();
    const cells = wrapper.findAll('[data-testid^="creator-batch-rhythm-cell-"]');
    expect(cells).toHaveLength(5);
    // Cells use raw chapter num in testid (padding is for display text only).
    expect(cells[0].attributes('data-testid')).toBe('creator-batch-rhythm-cell-1');
    expect(cells[4].attributes('data-testid')).toBe('creator-batch-rhythm-cell-5');
  });
});

// ---------------------------------------------------------------------------
// Deviations
// ---------------------------------------------------------------------------

describe('CreatorBatchRhythm — deviations', () => {
  it('marks cells as deviating when completed before prior chapters', async () => {
    // Chapter 3 completed but ch1 and ch2 not — deviation.
    activeJobRef.value = { status: 'running', start_chapter: 1, end_chapter: 5 };
    chapterEventsRef.value = [{ chapter_num: 3, status: 'completed' }];
    const wrapper = mount(CreatorBatchRhythm);
    await flushPromises();
    const cell3 = wrapper.find('[data-testid="creator-batch-rhythm-cell-3"]');
    expect(cell3.attributes('data-state')).toBe('deviating');
  });

  it('renders deviations section listing each deviation', async () => {
    activeJobRef.value = { status: 'running', start_chapter: 1, end_chapter: 5 };
    chapterEventsRef.value = [
      { chapter_num: 3, status: 'completed' },
      { chapter_num: 5, status: 'completed' },
    ];
    const wrapper = mount(CreatorBatchRhythm);
    await flushPromises();
    const deviations = wrapper.find('[data-testid="creator-batch-rhythm-deviations"]');
    expect(deviations.exists()).toBe(true);
    // 2 deviating chapters → 2 individual deviation <p> elements.
    const items = wrapper.findAll('[data-testid^="creator-batch-rhythm-deviation-"]');
    expect(items).toHaveLength(2);
    // Progress shows 2 deviations count.
    expect(wrapper.find('[data-testid="creator-batch-rhythm-progress"]').text()).toContain('2 处偏差');
  });
});

// ---------------------------------------------------------------------------
// Status labels
// ---------------------------------------------------------------------------

describe('CreatorBatchRhythm — status mapping', () => {
  it('renders "已完成" label for completed batch', async () => {
    activeJobRef.value = { status: 'completed', start_chapter: 1, end_chapter: 3 };
    isJobActiveRef.value = false;
    const wrapper = mount(CreatorBatchRhythm);
    await flushPromises();
    expect(wrapper.text()).toContain('已完成');
  });

  it('shows the "ended batch" hint when job is not active', async () => {
    activeJobRef.value = { status: 'completed', start_chapter: 1, end_chapter: 3 };
    isJobActiveRef.value = false;
    const wrapper = mount(CreatorBatchRhythm);
    await flushPromises();
    expect(wrapper.text()).toContain('当前批次已结束');
  });
});
