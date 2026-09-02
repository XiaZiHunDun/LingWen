/**
 * creator-deviation-finalize.spec.ts — REQ-001 切片 E
 * 验证推进模式「差异收尾」清单：越序差异展示、复核开关、进度、localStorage 持久化。
 */
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import CreatorDeviationFinalize from '../../../../src/components/creator/CreatorDeviationFinalize.vue';

const mockUsePilotBatch = {
  activeJob: { value: null as unknown },
  chapterEvents: { value: [] as Array<{ chapter_num: number; receivedAt: string }> },
  refreshActive: vi.fn(),
};

function setBatch(opts: {
  jobId?: string;
  start?: number;
  end?: number;
  completed?: number[];
} = {}) {
  mockUsePilotBatch.activeJob.value = {
    job_id: opts.jobId ?? 'job-1',
    slug: 's',
    start_chapter: opts.start ?? 1,
    end_chapter: opts.end ?? 4,
    budget_usd: 1,
    mode: 'pilot',
    status: 'completed',
    log_path: '',
    started_at: '',
  };
  mockUsePilotBatch.chapterEvents.value = (opts.completed ?? []).map((chapter_num) => ({
    chapter_num,
    receivedAt: `${chapter_num}`,
  }));
}

vi.mock('@/composables/usePilotBatch', () => ({
  usePilotBatch: () => mockUsePilotBatch,
}));

describe('CreatorDeviationFinalize', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    setBatch();
  });

  it('无批次时显示空状态', () => {
    mockUsePilotBatch.activeJob.value = null;
    const wrapper = mount(CreatorDeviationFinalize);
    expect(wrapper.find('[data-testid="creator-deviation-finalize-empty"]').exists()).toBe(true);
  });

  it('批次无越序差异时显示无需收尾', () => {
    setBatch({ start: 1, end: 3, completed: [1, 2, 3] });
    const wrapper = mount(CreatorDeviationFinalize);
    expect(wrapper.find('[data-testid="creator-deviation-finalize-clean"]').exists()).toBe(true);
  });

  it('展示越序差异并可逐一标记已复核', async () => {
    setBatch({ start: 1, end: 4, completed: [1, 3] });
    const wrapper = mount(CreatorDeviationFinalize);
    expect(wrapper.find('[data-testid="creator-deviation-finalize-toggle-3"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="creator-deviation-finalize-progress"]').text()).toContain('0/1');
    await wrapper.find('[data-testid="creator-deviation-finalize-toggle-3"]').trigger('click');
    expect(wrapper.find('[data-testid="creator-deviation-finalize-progress"]').text()).toContain('1/1');
    expect(wrapper.find('[data-testid="creator-deviation-finalize-done"]').exists()).toBe(true);
  });

  it('复核状态按批次写入 localStorage，重挂载恢复', async () => {
    setBatch({ jobId: 'job-review', start: 1, end: 4, completed: [1, 3] });
    const wrapper = mount(CreatorDeviationFinalize);
    await wrapper.find('[data-testid="creator-deviation-finalize-toggle-3"]').trigger('click');
    expect(window.localStorage.getItem('creator-deviation-review:job-review')).toBe('[3]');
    const remounted = mount(CreatorDeviationFinalize);
    expect(remounted.find('[data-testid="creator-deviation-finalize-progress"]').text()).toContain('1/1');
  });

  it('重置清空复核状态', async () => {
    setBatch({ start: 1, end: 4, completed: [1, 3] });
    const wrapper = mount(CreatorDeviationFinalize);
    await wrapper.find('[data-testid="creator-deviation-finalize-toggle-3"]').trigger('click');
    await wrapper.find('[data-testid="creator-deviation-finalize-reset"]').trigger('click');
    expect(wrapper.find('[data-testid="creator-deviation-finalize-progress"]').text()).toContain('0/1');
    expect(wrapper.find('[data-testid="creator-deviation-finalize-done"]').exists()).toBe(false);
  });
});
