import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import PilotStartForm from '@/components/pilot/PilotStartForm.vue';

describe('PilotStartForm', () => {
  it('renders mode select + start/end/budget inputs', () => {
    const wrapper = mount(PilotStartForm, {
      props: {
        slug: 'proj',
        preflightRows: [],
        preflightLoading: false,
        startLoading: false,
        error: null,
      },
    });
    expect(wrapper.find('[data-testid="start-mode"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="start-chapter-from"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="start-chapter-to"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="start-budget-usd"]').exists()).toBe(true);
  });

  it('emits submit-start with form payload when Start clicked', async () => {
    const wrapper = mount(PilotStartForm, {
      props: {
        slug: 'proj',
        preflightRows: [{ chapter: 1, ok: true, message: 'ok' }],
        preflightLoading: false,
        startLoading: false,
        error: null,
        preflightAllOk: true,
      },
    });
    await wrapper.find('[data-testid="start-chapter-from"]').setValue('1');
    await wrapper.find('[data-testid="start-chapter-to"]').setValue('5');
    await wrapper.find('[data-testid="start-budget-usd"]').setValue('5');
    await wrapper.find('[data-testid="start-mode"]').setValue('pilot');
    await wrapper.find('[data-testid="start-submit-btn"]').trigger('click');
    const events = wrapper.emitted('submit-start');
    expect(events).toBeTruthy();
    expect(events![0][0]).toMatchObject({
      slug: 'proj',
      start_chapter: 1,
      end_chapter: 5,
      budget_usd: 5,
      mode: 'pilot',
    });
  });

  it('disables Start button when preflightAllOk=false', () => {
    const wrapper = mount(PilotStartForm, {
      props: {
        slug: 'proj',
        preflightRows: [],
        preflightLoading: false,
        startLoading: false,
        error: null,
        preflightAllOk: false,
      },
    });
    const btn = wrapper.find('[data-testid="start-submit-btn"]').element as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });

  it('emits submit-preflight when Preflight button clicked', async () => {
    const wrapper = mount(PilotStartForm, {
      props: {
        slug: 'proj',
        preflightRows: [],
        preflightLoading: false,
        startLoading: false,
        error: null,
      },
    });
    await wrapper.find('[data-testid="start-chapter-from"]').setValue('1');
    await wrapper.find('[data-testid="start-chapter-to"]').setValue('5');
    await wrapper.find('[data-testid="preflight-btn"]').trigger('click');
    expect(wrapper.emitted('submit-preflight')).toBeTruthy();
  });
});