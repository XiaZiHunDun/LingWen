import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { defineComponent, h, nextTick } from 'vue';
import { mount } from '@vue/test-utils';

const mockStartBatch = vi.fn();
const mockActive = vi.fn();
const mockGetJob = vi.fn();
const mockList = vi.fn();
const mockCancel = vi.fn();
const mockFetchPreview = vi.fn();

vi.mock('@/api/studio', () => ({
  studioProductionRun: (...args: unknown[]) => mockStartBatch(...args),
  fetchStudioActiveBatchJob: () => mockActive(),
  listStudioBatchJobs: (...args: unknown[]) => mockList(...args),
  cancelStudioBatchJob: (...args: unknown[]) => mockCancel(...args),
}));

vi.mock('@/api/content', () => ({
  fetchCreatorChapterPreview: (...args: unknown[]) => mockFetchPreview(...args),
}));

/** Minimal EventSource stub (jsdom doesn't implement it) that records instances. */
class MockEventSource {
  static instances: MockEventSource[] = [];
  url: string;
  named: Record<string, (event: { data: string }) => void> = {};
  onopen: (() => void) | null = null;
  onerror: (() => void) | null = null;
  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }
  addEventListener(type: string, handler: (event: { data: string }) => void): void {
    this.named[type] = handler;
  }
  close(): void {
    // no-op
  }
}

function fireNamed(type: string, data: string): void {
  const source = MockEventSource.instances.at(-1);
  source?.named[type]?.({ data });
}

function withComposable<T>(cb: (api: ReturnType<typeof usePilotBatch>) => Promise<T>) {
  let captured!: ReturnType<typeof usePilotBatch>;
  const Host = defineComponent({
    setup() {
      captured = usePilotBatch();
      return () => h('div');
    },
  });
  const wrapper = mount(Host);
  return cb(captured).finally(() => wrapper.unmount());
}

import { usePilotBatch } from '@/composables/usePilotBatch';

beforeEach(() => {
  vi.useFakeTimers();
  vi.stubGlobal('EventSource', MockEventSource as unknown as typeof EventSource);
  MockEventSource.instances = [];
  mockStartBatch.mockReset();
  mockActive.mockReset();
  mockGetJob.mockReset();
  mockList.mockReset();
  mockCancel.mockReset();
  mockFetchPreview.mockReset();
});

afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('usePilotBatch', () => {
  it('exposes initial empty state', async () => {
    await withComposable(async (api) => {
      expect(api.activeJob.value).toBeNull();
      expect(api.history.value).toEqual([]);
      expect(api.chapterEvents.value).toEqual([]);
    });
  });

  it('refreshActive populates activeJob', async () => {
    const fakeJob = { job_id: 'j1', status: 'running', log_path: '/tmp/x' };
    mockActive.mockResolvedValue(fakeJob);
    await withComposable(async (api) => {
      await api.refreshActive();
      expect(api.activeJob.value).toEqual(fakeJob);
    });
  });

  it('startBatch calls fetchStudioStartBatchJob and refreshes active', async () => {
    const started = { job_id: 'new-j', status: 'running', log_path: '/tmp/y' };
    mockStartBatch.mockResolvedValue(started);
    mockActive.mockResolvedValue(started);
    await withComposable(async (api) => {
      await api.startBatch({ slug: 's1', start_chapter: 1, end_chapter: 10, budget_usd: 5, mode: 'pilot' });
      expect(mockStartBatch).toHaveBeenCalledOnce();
      expect(api.activeJob.value?.job_id).toBe('new-j');
    });
  });

  it('cancelBatch calls cancelStudioBatchJob', async () => {
    mockCancel.mockResolvedValue({ job_id: 'j1', status: 'cancelled' });
    await withComposable(async (api) => {
      await api.cancelBatch('j1');
      expect(mockCancel).toHaveBeenCalledWith('j1');
    });
  });

  it('refreshHistory populates history list', async () => {
    mockList.mockResolvedValue({ jobs: [{ job_id: 'h1', status: 'completed' }] });
    await withComposable(async (api) => {
      await api.refreshHistory('s1', 20);
      expect(api.history.value).toHaveLength(1);
      expect(api.history.value[0].job_id).toBe('h1');
    });
  });

  it('applies SSE chapter_completed and job_completed events to state', async () => {
    const running = { job_id: 'j1', status: 'running', log_path: '/tmp/x' };
    mockActive.mockResolvedValue(running);
    await withComposable(async (api) => {
      await api.refreshActive();
      await nextTick();
      fireNamed('chapter_completed', JSON.stringify({ chapter_num: 3 }));
      fireNamed('job_completed', JSON.stringify({ exit_code: 0, finished_at: 't0' }));
      await nextTick();
      expect(api.chapterEvents.value).toHaveLength(1);
      expect(api.chapterEvents.value[0].chapter_num).toBe(3);
      expect(api.activeJob.value?.status).toBe('completed');
    });
  });

  it('connects SSE with replay=1 so history is replayed on connect', async () => {
    mockActive.mockResolvedValue({ job_id: 'j1', status: 'running', log_path: '/tmp/x' });
    await withComposable(async (api) => {
      await api.refreshActive();
      await nextTick();
      const source = MockEventSource.instances.at(-1);
      expect(source?.url).toContain('replay=1');
      expect(source?.url).not.toContain('event_types=');
    });
  });

  it('exposes event-type options and reconnects the stream when filter toggles', async () => {
    mockActive.mockResolvedValue({ job_id: 'j1', status: 'running', log_path: '/tmp/x' });
    await withComposable(async (api) => {
      expect(api.eventTypeOptions.length).toBeGreaterThan(0);
      await api.refreshActive();
      await nextTick();
      api.toggleEventType('job_state');
      await nextTick();
      expect(api.selectedEventTypes.value).toEqual(['job_state']);
      expect(MockEventSource.instances.at(-1)?.url).toContain('event_types=job_state');
      api.toggleEventType('job_state');
      await nextTick();
      expect(api.selectedEventTypes.value).toEqual([]);
      expect(MockEventSource.instances.at(-1)?.url).not.toContain('event_types=');
    });
  });

  it('openPreview fetches preview content and opens the drawer', async () => {
    mockFetchPreview.mockResolvedValue({ chapter_id: 3, project_slug: 's1', outline: '大纲', body: '正文' });
    await withComposable(async (api) => {
      await api.openPreview(3);
      expect(mockFetchPreview).toHaveBeenCalledWith(3, { full: true });
      expect(api.previewChapter.value).toBe(3);
      expect(api.previewData.value?.chapter_id).toBe(3);
      expect(api.previewLoading.value).toBe(false);
      expect(api.previewError.value).toBeNull();
    });
  });

  it('openPreview surfaces errors and closePreview resets state', async () => {
    mockFetchPreview.mockRejectedValue(new Error('boom'));
    await withComposable(async (api) => {
      await api.openPreview(7);
      expect(api.previewError.value).toContain('boom');
      expect(api.previewData.value).toBeNull();
      expect(api.previewLoading.value).toBe(false);
      api.closePreview();
      expect(api.previewChapter.value).toBeNull();
    });
  });
});