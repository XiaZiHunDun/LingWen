import { mount } from '@vue/test-utils';
import { describe, expect, test } from 'vitest';
import SidebarSystemStatusBody from '../../src/components/SidebarSystemStatusBody.vue';

describe('SidebarSystemStatusBody', () => {
  test('shows api and ws rows when expanded', () => {
    const wrapper = mount(SidebarSystemStatusBody, {
      props: {
        status: {},
        apiOffline: false,
        apiChecking: false,
        wsConnected: true,
      },
    });
    expect(wrapper.find('[data-testid="sidebar-system-status-body"]').exists()).toBe(true);
    expect(wrapper.find('[data-testid="sidebar-system-api-row"]').text()).toContain('正常');
    expect(wrapper.find('[data-testid="sidebar-system-ws-row"]').text()).toContain('已连接');
    expect(wrapper.find('[data-testid="sidebar-system-healthy-hint"]').exists()).toBe(true);
  });

  test('shows warning states when offline', () => {
    const wrapper = mount(SidebarSystemStatusBody, {
      props: {
        status: {},
        apiOffline: true,
        apiChecking: false,
        wsConnected: false,
      },
    });
    expect(wrapper.find('[data-testid="sidebar-system-api-row"]').text()).toContain('不可用');
    expect(wrapper.find('[data-testid="sidebar-system-ws-row"]').text()).toContain('未连接');
    expect(wrapper.find('[data-testid="sidebar-system-healthy-hint"]').exists()).toBe(false);
  });
});
