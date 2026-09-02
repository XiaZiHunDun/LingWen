// tests/unit/pages/pilot-page.spec.ts — Phase 23 Task 12 (Part E1)
// PilotPage assembly test: composes 4 pilot components + usePilotBatch + useStudioProject.

import { describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';

const mockUsePilotBatch = {
  activeJob: { value: null as unknown },
  history: { value: [] as unknown[] },
  preflightRows: { value: [] as Array<{ chapter: number; ok: boolean; message: string }> },
  preflightLoading: { value: false },
  preflightError: { value: null as string | null },
  startLoading: { value: false },
  startError: { value: null as string | null },
  cancelLoading: { value: false },
  cancelError: { value: null as string | null },
  isJobActive: { value: false },
  chapterEvents: { value: [] as Array<{ chapter_num: number; receivedAt: string }> },
  eventTypeOptions: [] as Array<{ value: unknown; label: string }>,
  selectedEventTypes: { value: [] as unknown[] },
  toggleEventType: vi.fn(),
  previewChapter: { value: null as number | null },
  previewData: { value: null as unknown },
  previewLoading: { value: false },
  previewError: { value: null as string | null },
  openPreview: vi.fn(),
  closePreview: vi.fn(),
  refreshActive: vi.fn(),
  refreshHistory: vi.fn(),
  refreshQueue: vi.fn(),
  queue: { value: [] as Array<{ job_id: string; start_chapter: number; end_chapter: number; mode: string; status: string; started_at: string }> },
  templates: { value: [] as unknown[] },
  templateLoading: { value: false },
  templateSaveLoading: { value: false },
  templateError: { value: null as string | null },
  templateMessage: { value: null as string | null },
  loadTemplates: vi.fn(),
  saveTemplate: vi.fn(),
  deleteTemplate: vi.fn(),
  runPreflight: vi.fn(),
  startBatch: vi.fn(),
  cancelBatch: vi.fn(),
};

vi.mock('@/composables/usePilotBatch', () => ({
  usePilotBatch: () => mockUsePilotBatch,
}));

const mockStudioProject = { activeSlug: { value: 'test-slug' } };
vi.mock('@/composables', () => ({
  useStudioProject: () => mockStudioProject,
}));

import PilotPage from '@/pages/PilotPage.vue';

describe('PilotPage', () => {
  it('renders start form + live panel + history list', () => {
    const wrapper = mount(PilotPage);
    expect(wrapper.find('[data-testid="pilot-start-form"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="pilot-live-panel"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="pilot-history-list"]').exists()).toBe(true);
  });

  it('refreshes active + history + queue + templates on mount', () => {
    mount(PilotPage);
    expect(mockUsePilotBatch.refreshActive).toHaveBeenCalled();
    expect(mockUsePilotBatch.refreshHistory).toHaveBeenCalled();
    expect(mockUsePilotBatch.refreshQueue).toHaveBeenCalled();
    expect(mockUsePilotBatch.loadTemplates).toHaveBeenCalled();
  });

  it('renders template panel', () => {
    const wrapper = mount(PilotPage);
    expect(wrapper.find('[data-testid="pilot-template-panel"]').exists()).toBe(true);
  });

  it('renders queue panel when there are queued batch jobs', () => {
    mockUsePilotBatch.queue.value = [
      { job_id: 'job-q1', start_chapter: 5, end_chapter: 8, mode: 'canon', status: 'queued', started_at: '2026-09-03T00:00:00Z' },
    ];
    const wrapper = mount(PilotPage);
    expect(wrapper.find('[data-testid="pilot-queue-panel"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="pilot-queue-item-job-q1"]').exists()).toBe(true);
    mockUsePilotBatch.queue.value = [];
  });

  it('shows error banner when startError is set', async () => {
    mockUsePilotBatch.startError.value = 'batch failed';
    const wrapper = mount(PilotPage);
    expect(wrapper.text()).toContain('batch failed');
    mockUsePilotBatch.startError.value = null;
  });
});