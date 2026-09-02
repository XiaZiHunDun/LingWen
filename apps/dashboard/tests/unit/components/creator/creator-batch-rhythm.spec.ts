/**
 * creator-batch-rhythm.spec.ts — REQ-001 切片 C
 * 验证推进模式「批改节奏带」：空状态 / 序完成 / 越序偏差，只读复用 usePilotBatch。
 */
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import CreatorBatchRhythm from '../../../../src/components/creator/CreatorBatchRhythm.vue';

const mockUsePilotBatch = {
  refreshActive: vi.fn(),
  activeJob: { value: null as unknown },
  chapterEvents: { value: [] as Array<{ chapter_num: number; receivedAt: string }> },
  isJobActive: { value: false },
};

function setMock(opts: {
  status?: string;
  start?: number;
  end?: number;
  completed?: number[];
  running?: boolean;
} = {}) {
  mockUsePilotBatch.activeJob.value = opts.status
    ? {
        job_id: 'job-1',
        slug: 's',
        start_chapter: opts.start ?? 1,
        end_chapter: opts.end ?? 5,
        budget_usd: 1,
        mode: 'pilot',
        status: opts.status,
        log_path: '',
        started_at: '',
      }
    : null;
  mockUsePilotBatch.chapterEvents.value = (opts.completed ?? []).map((chapter_num) => ({
    chapter_num,
    receivedAt: `${chapter_num}`,
  }));
  mockUsePilotBatch.isJobActive.value = opts.running ?? false;
}

vi.mock('@/composables/usePilotBatch', () => ({
  usePilotBatch: () => mockUsePilotBatch,
}));

describe('CreatorBatchRhythm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setMock();
  });

  it('无批次时渲染空状态并在挂载时刷新活跃批次', () => {
    const wrapper = mount(CreatorBatchRhythm);
    expect(wrapper.find('[data-testid="creator-batch-rhythm-empty"]').exists()).toBe(true);
    expect(mockUsePilotBatch.refreshActive).toHaveBeenCalled();
  });

  it('序完成后渲染节奏带与进度，无偏差', () => {
    setMock({ status: 'running', start: 1, end: 5, completed: [1, 2, 3], running: true });
    const wrapper = mount(CreatorBatchRhythm);
    expect(wrapper.find('[data-testid="creator-batch-rhythm-empty"]').exists()).toBe(false);
    expect(wrapper.find('[data-testid="creator-batch-rhythm-progress"]').text()).toContain('3/5');
    expect(wrapper.find('[data-testid="creator-batch-rhythm-cell-1"]').attributes('data-state')).toBe('done');
    expect(wrapper.find('[data-testid="creator-batch-rhythm-cell-3"]').attributes('data-state')).toBe('done');
    expect(wrapper.find('[data-testid="creator-batch-rhythm-cell-4"]').attributes('data-state')).toBe('pending');
    expect(wrapper.find('[data-testid="creator-batch-rhythm-deviations"]').exists()).toBe(false);
  });

  it('越序改定被标记为偏差', () => {
    setMock({ status: 'completed', start: 1, end: 4, completed: [1, 3] });
    const wrapper = mount(CreatorBatchRhythm);
    expect(wrapper.find('[data-testid="creator-batch-rhythm-cell-1"]').attributes('data-state')).toBe('done');
    expect(wrapper.find('[data-testid="creator-batch-rhythm-cell-3"]').attributes('data-state')).toBe('deviating');
    expect(wrapper.find('[data-testid="creator-batch-rhythm-deviation-3"]').exists()).toBe(true);
  });
});
