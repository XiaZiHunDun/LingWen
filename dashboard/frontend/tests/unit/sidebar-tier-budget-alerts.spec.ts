// tests/unit/sidebar-tier-budget-alerts.spec.ts — Phase 9.27 F11
import { describe, test, expect, vi, beforeEach } from 'vitest';
import { ref } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';
import SidebarTierBudgetAlerts from '../../src/components/SidebarTierBudgetAlerts.vue';
import { clearTierBudgetAlerts } from '../../src/composables/useTierBudgetAlerts.js';
import { byTestid } from '../helpers/by-testid';

const timeWindowRef = ref('all');
const windowedCostRef = ref<{ cost_by_tier?: Record<string, number> } | null>(null);

vi.mock('../../src/composables/useCostWindow.js', () => ({
  useCostWindow: () => ({
    timeWindow: timeWindowRef,
    windowedCost: windowedCostRef,
    setTimeWindow: vi.fn(),
  }),
}));

const makeStatus = (budgetByTier: Record<string, object>) => ({
  workflow_name: 'novel_writing',
  budget_by_tier: budgetByTier,
});

describe('SidebarTierBudgetAlerts (Phase 9.27 F11)', () => {
  beforeEach(() => {
    clearTierBudgetAlerts();
    timeWindowRef.value = 'all';
    windowedCostRef.value = null;
  });

  test('renders alert list when tier exceeds budget threshold', async () => {
    const wrapper = mount(SidebarTierBudgetAlerts, {
      props: {
        status: makeStatus({
          opus: { budget_usd: 1.0, used_usd: 1.2, used_pct: 120.0, status: 'exceeded' },
        }),
      },
    });
    await flushPromises();

    expect(wrapper.find(byTestid('sidebar-tier-budget-alerts')).exists()).toBe(true);
    const item = wrapper.find(byTestid('sidebar-tier-budget-alert-opus'));
    expect(item.exists()).toBe(true);
    expect(item.text()).toContain('opus');
    expect(item.text()).toContain('超预算');
    expect(item.text()).toContain('120%');
    expect(item.text()).toContain('全部');
    expect(wrapper.find(byTestid('sidebar-tier-budget-alert-time-opus')).exists()).toBe(true);
  });

  test('hidden when no tier alerts logged', async () => {
    const wrapper = mount(SidebarTierBudgetAlerts, {
      props: {
        status: makeStatus({
          haiku: { budget_usd: 0.1, used_usd: 0.02, used_pct: 20.0, status: 'ok' },
        }),
      },
    });
    await flushPromises();

    expect(wrapper.find(byTestid('sidebar-tier-budget-alerts')).exists()).toBe(false);
  });

  test('logs windowed warning when 7d cost crosses 80%', async () => {
    timeWindowRef.value = '7d';
    windowedCostRef.value = { cost_by_tier: { sonnet: 0.42 } };

    const wrapper = mount(SidebarTierBudgetAlerts, {
      props: {
        status: makeStatus({
          sonnet: { budget_usd: 0.5, used_usd: 0.1, used_pct: 20.0, status: 'ok' },
        }),
      },
    });
    await flushPromises();

    const item = wrapper.find(byTestid('sidebar-tier-budget-alert-sonnet'));
    expect(item.exists()).toBe(true);
    expect(item.text()).toContain('接近上限');
    expect(item.text()).toContain('7天');
  });
});
