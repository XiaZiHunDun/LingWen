// tests/unit/cost-section-tier-only.spec.ts — Phase 8.30b
// vitest 真 e2e 改造 — WorkflowStatus hasCost gate (scenario + tier OR)
// 跟 ceremonial Playwright spec (tests/e2e/cost-section-tier-only.spec.js) 同契约
// 但用 @vue/test-utils + jsdom 真跑 component-level test.
//
// 契约 (跟 ceremonial 同步):
//   - 旧 hasCost 仅查 costByScenario → tier-only 数据时整 cost section 隐藏
//   - Phase 8.14 fix: scenarioHas || tierHas (1 行 additive OR)
//   - 双方都空 → cost section hidden (旧行为保)
//   - 双方有值 → visible (Phase 8.13 path 不破)

import { describe, test, expect } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import WorkflowStatus from '../../src/components/WorkflowStatus.vue'

const makeStatus = (
  costByScenario: Record<string, number> = {},
  costByTier: Record<string, number> = {},
) => ({
  workflow_name: 'novel_writing',
  is_active: true,
  paused: false,
  completed: 5,
  failed: 0,
  node_count: 7,
  steps: 12,
  cost_by_scenario: costByScenario,
  cost_by_tier: costByTier,
  total_cost_usd: 0.05,
})

describe('WorkflowStatus hasCost gate (Phase 8.14 scenario + tier OR)', () => {
  test('shows cost section when only tier data present', async () => {
    const wrapper = mount(WorkflowStatus, {
      props: { status: makeStatus({}, { haiku: 0.05 }) },
    })
    await flushPromises()

    // Phase 8.14 fix: tier-only 数据时 cost section 必须 visible
    expect(wrapper.get('[data-testid="cost-section"]').exists()).toBe(true)
    // Wrapper 也可见
    expect(wrapper.find('[data-testid="cost-section"]').isVisible()).toBe(true)
  })

  test('hides cost section when neither scenario nor tier present', async () => {
    const wrapper = mount(WorkflowStatus, {
      props: { status: makeStatus({}, {}) },
    })
    await flushPromises()

    // 旧行为保: 双方都空 → cost section hidden
    expect(wrapper.find('[data-testid="cost-section"]').exists()).toBe(false)
  })

  test('shows cost section when both scenario and tier present', async () => {
    const wrapper = mount(WorkflowStatus, {
      props: {
        status: makeStatus(
          { chapter_writing: 0.03 },
          { haiku: 0.01, sonnet: 0.02 },
        ),
      },
    })
    await flushPromises()

    // Sanity: 双方有值 → visible (Phase 8.13 path 不破)
    expect(wrapper.get('[data-testid="cost-section"]').exists()).toBe(true)
  })
})
