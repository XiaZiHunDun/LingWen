import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import PilotHistoryList from '@/components/pilot/PilotHistoryList.vue';

const sampleHistory = [
  { job_id: 'j1', slug: 'demo', status: 'completed', start_chapter: 1, end_chapter: 10, mode: 'pilot', started_at: '2026-09-01T00:00:00Z', budget_usd: 5, exit_code: 0 },
  { job_id: 'j2', slug: 'demo', status: 'failed', start_chapter: 11, end_chapter: 20, mode: 'pilot', started_at: '2026-09-02T00:00:00Z', budget_usd: 3, exit_code: 1 },
];

describe('PilotHistoryList', () => {
  it('renders one row per history entry', () => {
    const wrapper = mount(PilotHistoryList, { props: { history: sampleHistory } });
    const rows = wrapper.findAll('tbody tr');
    expect(rows.length).toBeGreaterThanOrEqual(2);
  });

  it('shows empty state when no history', () => {
    const wrapper = mount(PilotHistoryList, { props: { history: [] } });
    expect(wrapper.find('[data-testid="pilot-history-empty"]').exists()).toBe(true);
  });

  it('emits select-job when row clicked', async () => {
    const wrapper = mount(PilotHistoryList, { props: { history: sampleHistory } });
    await wrapper.find('[data-testid="history-row-j1"]').trigger('click');
    expect(wrapper.emitted('select-job')).toBeTruthy();
    expect(wrapper.emitted('select-job')![0][0]).toBe('j1');
  });

  it('shows status pill text for each row', () => {
    const wrapper = mount(PilotHistoryList, { props: { history: sampleHistory } });
    expect(wrapper.text()).toContain('completed');
    expect(wrapper.text()).toContain('failed');
  });
});