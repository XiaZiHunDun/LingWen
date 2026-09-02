import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import PilotPreflightTable from '@/components/pilot/PilotPreflightTable.vue';

describe('PilotPreflightTable', () => {
  it('renders one row per preflight result', () => {
    const rows = [
      { chapter: 1, ok: true, message: 'ok' },
      { chapter: 2, ok: false, message: 'foreshadow unresolved' },
    ];
    const wrapper = mount(PilotPreflightTable, { props: { rows } });
    const trs = wrapper.findAll('tbody tr');
    expect(trs).toHaveLength(2);
  });

  it('shows PASS / FAIL pill matching ok flag', () => {
    const rows = [
      { chapter: 1, ok: true, message: 'ok' },
      { chapter: 2, ok: false, message: 'fail' },
    ];
    const wrapper = mount(PilotPreflightTable, { props: { rows } });
    expect(wrapper.text()).toContain('PASS');
    expect(wrapper.text()).toContain('FAIL');
  });

  it('renders empty state when no rows', () => {
    const wrapper = mount(PilotPreflightTable, { props: { rows: [] } });
    expect(wrapper.text()).toContain('无 preflight 结果');
  });
});