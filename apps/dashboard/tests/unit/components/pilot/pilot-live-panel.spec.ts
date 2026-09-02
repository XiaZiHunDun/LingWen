import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import PilotLivePanel from '@/components/pilot/PilotLivePanel.vue';

const runningJob = {
  job_id: 'j1', slug: 's1', status: 'running',
  start_chapter: 1, end_chapter: 14, budget_usd: 5,
  mode: 'pilot', pid: 12345, log_path: '/tmp/x', log_tail: 'last log line',
  started_at: new Date().toISOString(), finished_at: null,
  exit_code: null, error: null,
};

describe('PilotLivePanel', () => {
  it('renders nothing when activeJob is null', () => {
    const wrapper = mount(PilotLivePanel, { props: { activeJob: null, etaSeconds: null, cancelLoading: false } });
    expect(wrapper.find('[data-testid="pilot-live-empty"]').exists()).toBe(true);
  });

  it('shows status pill for running job', () => {
    const wrapper = mount(PilotLivePanel, { props: { activeJob: runningJob, etaSeconds: 60, cancelLoading: false } });
    expect(wrapper.find('[data-testid="pilot-status"]').text()).toContain('running');
  });

  it('displays ETA when provided is', () => {
    const wrapper = mount(PilotLivePanel, { props: { activeJob: runningJob, etaSeconds: 90, cancelLoading: false } });
    expect(wrapper.text()).toMatch(/ETA|预计剩余/);
    expect(wrapper.text()).toContain('1分');
  });

  it('shows waiting message when ETA is null', () => {
    const wrapper = mount(PilotLivePanel, { props: { activeJob: runningJob, etaSeconds: null, cancelLoading: false } });
    expect(wrapper.text()).toContain('等待');
  });

  it('emits request-cancel when Cancel button clicked', async () => {
    const wrapper = mount(PilotLivePanel, { props: { activeJob: runningJob, etaSeconds: 60, cancelLoading: false } });
    await wrapper.find('[data-testid="pilot-cancel-btn"]').trigger('click');
    expect(wrapper.emitted('request-cancel')).toBeTruthy();
  });

  it('renders log_tail when present', () => {
    const wrapper = mount(PilotLivePanel, { props: { activeJob: runningJob, etaSeconds: null, cancelLoading: false } });
    expect(wrapper.find('[data-testid="pilot-log-tail"]').text()).toContain('last log line');
  });

  it('handles cancelled status', () => {
    const wrapper = mount(PilotLivePanel, {
      props: { activeJob: { ...runningJob, status: 'cancelled' }, etaSeconds: null, cancelLoading: false },
    });
    expect(wrapper.find('[data-testid="pilot-status"]').text()).toContain('cancelled');
  });

  it('renders the most recent 5 chapter_completed events', () => {
    const chapterEvents = Array.from({ length: 7 }, (_, i) => ({
      chapter_num: i + 1,
      receivedAt: `t${i}`,
    }));
    const wrapper = mount(PilotLivePanel, {
      props: { activeJob: runningJob, etaSeconds: null, cancelLoading: false, chapterEvents },
    });
    const items = wrapper.findAll('[data-testid="pilot-chapter-events"] .chapter-event-item');
    expect(items).toHaveLength(5);
    expect(items[0].text()).toContain('ch003');
    expect(wrapper.text()).toContain('ch007');
  });
});