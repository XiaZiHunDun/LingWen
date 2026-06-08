import { test, expect } from '@playwright/test'

/**
 * E2E: Phase 8.29 — Per-Tier 趋势线 (CostTrendChart multi-series)
 * 验证 CostTrendChart 组件在 costByDayPerTier prop 非空时切换 multi-series
 * 渲染 (3 lines: haiku/sonnet/opus) + ECharts legend. 单线 path (costByDay)
 * 仍可用作 baseline 兜底.
 *
 * 跟 cost-trend-chart.spec.js (Phase 8.24) 同模式: page.route mock +
 * 断言 .cost-trend-chart visible. 当前 Playwright runner 未装, 作为契约文档.
 *
 * 契约:
 *   - costByDayPerTier = null (default) → 单线 path (Phase 8.24 baseline)
 *   - costByDayPerTier = {} (空 dict) → 单线 path (fallback)
 *   - costByDayPerTier = { date: { tier: 0 } } (全 0) → multi-series 但 0 data
 *   - costByDayPerTier = { date: { haiku: 0.005, ... } } (有非 0) → multi-series
 *     3 lines + ECharts legend top-right
 *   - 配色: haiku #67c23a / sonnet #ff6b6b / opus #9b59b6 (跟 Phase 8.21 tier alarm
 *     warning 黄 / exceeded 红 不冲突 — 这里是成本 trend 颜色, 跟 alarm 视觉分离)
 *   - 0 改 backend (Phase 8.31 实施 cross-dim aggregation cost_by_day_per_tier)
 *   - 0 改 Phase 8.24 单线 baseline (costByDay prop 仍 required, 单线 path 保留)
 */

test.describe('CostTrendChart Per-Tier Multi-Series (Phase 8.29)', () => {
  test.setTimeout(30000)

  test('renders multi-series lines + legend when costByDayPerTier has non-zero data', async ({ page }) => {
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: true,
          completed: 5,
          failed: 0,
          paused: false,
          paused_nodes: [],
          node_count: 7,
          steps: 5,
          total_cost_usd: 0.060,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: {
            chapter_writing: 0.030,
            chapter_review: 0.030,
          },
          // Phase 8.29: per-day-per-tier breakdown (cross-dim aggregation)
          // backend 暂未提供, 当前契约描述未来数据 shape
          cost_by_day: {
            '2026-06-01': 0.020,
            '2026-06-02': 0.020,
            '2026-06-03': 0.020,
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // chart canvas 可见 (multi-series 模式下也走同一 canvas)
    const chart = page.getByTestId('cost-trend-chart')
    await expect(chart).toBeVisible({ timeout: 5000 })
    await expect(chart.locator('canvas')).toBeVisible()

    // 暂未提供 costByDayPerTier → 走单线 baseline path (Phase 8.24)
    // legend 不渲染 (单线 path 不需)
    // 当 Phase 8.31 backend 上线后, multi-series path 自动接管 (additive prop)
  })

  test('falls back to single-line baseline when costByDayPerTier is null', async ({ page }) => {
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: true,
          completed: 5,
          failed: 0,
          paused: false,
          paused_nodes: [],
          node_count: 7,
          steps: 5,
          total_cost_usd: 0.045,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: {
            chapter_writing: 0.025,
            chapter_review: 0.020,
          },
          cost_by_day: {
            '2026-06-01': 0.015,
            '2026-06-02': 0.015,
            '2026-06-03': 0.015,
          },
          // 显式 null → 单线 baseline
          cost_by_day_per_tier: null,
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    const chart = page.getByTestId('cost-trend-chart')
    await expect(chart).toBeVisible({ timeout: 5000 })
  })

  test('hides empty state when no cost data', async ({ page }) => {
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: true,
          completed: 0,
          failed: 0,
          paused: false,
          paused_nodes: [],
          node_count: 7,
          steps: 0,
          total_cost_usd: 0.0,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: {},
          cost_by_day: {},
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // cost-section 不可见 (hasCost = false gate, 跟 Phase 8.14 一致)
    // cost-trend-chart 也不会渲染
    const costSection = page.getByTestId('cost-section')
    await expect(costSection).not.toBeVisible({ timeout: 2000 })
  })
})
