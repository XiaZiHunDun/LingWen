// tests/unit/cost-bar-chart-tier-mode.spec.ts — Phase 8.30 pilot
// vitest 真 e2e 改造 — CostBarChart tier-mode toggle
// 跟 ceremonial Playwright spec (tests/e2e/cost-bar-chart-tier-mode.spec.js)
// 同样契约但用 @vue/test-utils + jsdom 真跑 component-level test, 不需 browser.
//
// 契约 (跟 ceremonial 同步):
//   - 默认 mode='scenario' (向后兼容)
//   - 渲染 2 tab button (data-testid="mode-tab-scenario" / "mode-tab-tier")
//   - mode='scenario' 时 scenario tab .active + aria-selected="true"
//   - mode='tier' 时 tier tab .active + aria-selected="true"
//   - click tier tab → emit('update:mode', 'tier') → parent v-model 接
//   - data source 切换: scenario 走 costByScenario; tier 走 costByTier

import { describe, test, expect } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import CostBarChart from '../../src/components/CostBarChart.vue'
import { byTestid } from '../helpers/by-testid'

// ECharts 内部 canvas 渲染走 zrender.Painter, jsdom 无 HTMLCanvasElement.getContext('2d')
// 完整支持 → clearRect null deref 报错. stub 集中在 tests/unit/setup.ts (Phase 8.30).
// 测试只关 mode toggle (tab .active / aria-selected / emit), 不需 真实 canvas pixel.

const scenarioData = {
  chapter_writing: 0.015,
  chapter_review: 0.020,
  polish_merge: 0.010,
}
const tierData = {
  haiku: 0.005,
  sonnet: 0.030,
  opus: 0.010,
}

describe('CostBarChart tier-mode toggle (Phase 8.30 pilot)', () => {
  test('renders 2 tab buttons with data-testid (scenario | tier)', async () => {
    const wrapper = mount(CostBarChart, {
      props: {
        costByScenario: scenarioData,
        costByTier: tierData,
      },
    })
    await flushPromises()

    const scenarioTab = wrapper.get(byTestid('mode-tab-scenario'))
    const tierTab = wrapper.get(byTestid('mode-tab-tier'))

    expect(scenarioTab.exists()).toBe(true)
    expect(tierTab.exists()).toBe(true)
  })

  test('default mode is scenario, scenario tab .active', async () => {
    const wrapper = mount(CostBarChart, {
      props: {
        costByScenario: scenarioData,
        costByTier: tierData,
      },
    })
    await flushPromises()

    const scenarioTab = wrapper.get(byTestid('mode-tab-scenario'))
    expect(scenarioTab.classes()).toContain('active')
    expect(scenarioTab.attributes('aria-selected')).toBe('true')
  })

  test('click tier tab → emit update:mode with tier', async () => {
    const wrapper = mount(CostBarChart, {
      props: {
        costByScenario: scenarioData,
        costByTier: tierData,
        mode: 'scenario',
        'onUpdate:mode': (val) => wrapper.setProps({ mode: val }),
      },
    })
    await flushPromises()

    const tierTab = wrapper.get(byTestid('mode-tab-tier'))
    await tierTab.trigger('click')
    await flushPromises()

    const updateEvents = wrapper.emitted('update:mode')
    expect(updateEvents).toBeTruthy()
    expect(updateEvents![0]).toEqual(['tier'])
  })

  test('mode=tier shows tier tab .active + aria-selected=true', async () => {
    const wrapper = mount(CostBarChart, {
      props: {
        costByScenario: scenarioData,
        costByTier: tierData,
        mode: 'tier',
      },
    })
    await flushPromises()

    const tierTab = wrapper.get(byTestid('mode-tab-tier'))
    expect(tierTab.classes()).toContain('active')
    expect(tierTab.attributes('aria-selected')).toBe('true')
  })
})
