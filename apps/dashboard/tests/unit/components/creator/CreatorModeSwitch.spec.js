import { describe, it, expect, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import CreatorModeSwitch from '../../../../src/components/creator/CreatorModeSwitch.vue';

describe('CreatorModeSwitch', () => {
  it('renders current mode correctly', () => {
    const wrapper = mount(CreatorModeSwitch, {
      props: { currentMode: 'companion' },
    });
    expect(wrapper.find('.mode-switch__label').text()).toBe('陪伴模式');
    expect(wrapper.find('.mode-switch__icon').text()).toBe('🤝');
  });

  it('shows correct mode label for advance', () => {
    const wrapper = mount(CreatorModeSwitch, {
      props: { currentMode: 'advance' },
    });
    expect(wrapper.find('.mode-switch__label').text()).toBe('推进模式');
    expect(wrapper.find('.mode-switch__icon').text()).toBe('🚀');
  });

  it('shows correct mode label for studio', () => {
    const wrapper = mount(CreatorModeSwitch, {
      props: { currentMode: 'studio' },
    });
    expect(wrapper.find('.mode-switch__label').text()).toBe('工厂模式');
    expect(wrapper.find('.mode-switch__icon').text()).toBe('🏭');
  });

  it('toggles panel on button click', async () => {
    const wrapper = mount(CreatorModeSwitch, {
      props: { currentMode: 'companion' },
    });
    expect(wrapper.find('.mode-switch__panel').exists()).toBe(false);
    await wrapper.find('.mode-switch__current').trigger('click');
    expect(wrapper.find('.mode-switch__panel').exists()).toBe(true);
    await wrapper.find('.mode-switch__current').trigger('click');
    expect(wrapper.find('.mode-switch__panel').exists()).toBe(false);
  });

  it('emits update:currentMode when selecting different mode', async () => {
    const wrapper = mount(CreatorModeSwitch, {
      props: { currentMode: 'companion' },
    });
    await wrapper.find('.mode-switch__current').trigger('click');
    await wrapper.findAll('.mode-switch__item')[1].trigger('click');
    expect(wrapper.emitted('update:currentMode')).toEqual([['advance']]);
  });

  it('does not emit when selecting current mode', async () => {
    const wrapper = mount(CreatorModeSwitch, {
      props: { currentMode: 'companion' },
    });
    await wrapper.find('.mode-switch__current').trigger('click');
    await wrapper.findAll('.mode-switch__item')[0].trigger('click');
    expect(wrapper.emitted('update:currentMode')).toBeUndefined();
  });

  it('closes panel after selecting mode', async () => {
    const wrapper = mount(CreatorModeSwitch, {
      props: { currentMode: 'companion' },
    });
    await wrapper.find('.mode-switch__current').trigger('click');
    expect(wrapper.find('.mode-switch__panel').exists()).toBe(true);
    await wrapper.findAll('.mode-switch__item')[1].trigger('click');
    expect(wrapper.find('.mode-switch__panel').exists()).toBe(false);
  });

  it('applies correct class based on mode', () => {
    const wrapper = mount(CreatorModeSwitch, {
      props: { currentMode: 'companion' },
    });
    expect(wrapper.find('.mode-switch__current').classes()).toContain('mode-switch__current--companion');
  });
});
