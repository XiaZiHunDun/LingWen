// tests/unit/creator-page.spec.ts — CreatorPage 挂载

import { describe, test, expect, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import CreatorPage from '../../src/pages/CreatorPage.vue';
import { byTestid } from '../helpers/by-testid';

// Mock the layout component
vi.mock('../../src/components/creator/CreatorPageLayout.vue', () => ({
  default: {
    name: 'CreatorPageLayout',
    template: '<div data-testid="stub-creator-layout">Creator Layout</div>',
  },
}));

describe('CreatorPage', () => {
  test('renders CreatorPageLayout', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.find(byTestid('stub-creator-layout')).exists()).toBe(true);
    expect(wrapper.text()).toContain('Creator Layout');
  });

  test('is a valid Vue component', () => {
    const wrapper = mount(CreatorPage);
    expect(wrapper.exists()).toBe(true);
  });

  test('mounts without errors', async () => {
    const wrapper = mount(CreatorPage);
    await flushPromises();
    expect(wrapper.html()).toBeTruthy();
  });
});
