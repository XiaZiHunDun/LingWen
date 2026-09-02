import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import PilotCancelDialog from '@/components/pilot/PilotCancelDialog.vue';

describe('PilotCancelDialog', () => {
  it('renders nothing when visible=false', () => {
    const wrapper = mount(PilotCancelDialog, {
      props: { visible: false, jobId: 'j1', loading: false },
    });
    expect(wrapper.find('[data-testid="pilot-cancel-dialog"]').exists()).toBe(false);
  });

  it('shows jobId when visible=true', () => {
    const wrapper = mount(PilotCancelDialog, {
      props: { visible: true, jobId: 'abc-123', loading: false },
    });
    expect(wrapper.text()).toContain('abc-123');
  });

  it('emits confirm when confirm button clicked', async () => {
    const wrapper = mount(PilotCancelDialog, {
      props: { visible: true, jobId: 'j1', loading: false },
    });
    await wrapper.find('[data-testid="cancel-confirm-btn"]').trigger('click');
    expect(wrapper.emitted('confirm')).toBeTruthy();
  });

  it('emits hold-on when hold-on button clicked', async () => {
    const wrapper = mount(PilotCancelDialog, {
      props: { visible: true, jobId: 'j1', loading: false },
    });
    await wrapper.find('[data-testid="cancel-hold-btn"]').trigger('click');
    expect(wrapper.emitted('hold-on')).toBeTruthy();
  });
});
