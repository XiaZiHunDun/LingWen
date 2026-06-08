import { test, expect } from '@playwright/test'

/**
 * E2E: Phase 8.24 — CostTrendChart trend line (cost by day)
 * 验证 CostTrendChart 组件 (Phase 8.24 frontend) + WorkflowStatus 集成:
 * - CostTrendChart 在 cost-section 内, 跟 CostBarChart 串联 (在 CostBarChart 之后)
 * - ECharts canvas 渲染 (line type, .cost-trend-chart canvas)
 * - hasData gate 包含 dayHas (Phase 8.24 OR-check 扩 day 维度)
 * - 走 Phase 8.23 后端 cost_by_day 字段 (mock fixture)
 * - 走 useCostWindow 7d/30d 切窗 → 走 windowedCost.cost_by_day 透传
 *
 * 跟 dashboard_cost.spec.js (Phase 8.7) + cost-bar-chart-tier-mode.spec.js
 * (Phase 8.13) + time-window-tabs.spec.js (Phase 8.16) 同模式: page.route mock +
 * 断言 visible. 当前 Playwright runner 未装 (跟 Phase 7.6/8.7/8.8/8.11/8.13/8.14/
 * 8.15/8.16/8.23 一致),作为契约文档存在.
 *
 * 契约:
 *   - CostTrendChart 接收 costByDay prop (Object, {YYYY-MM-DD: USD})
 *   - 走 ECharts line + areaStyle (#ff6b6b 0.2 alpha) + pixel-border
 *   - hasData: Object.keys > 0 && Object.values > 0 (跟 CostBarChart 同样 pattern)
 *   - hasCost gate additive OR: scenarioHas || tierHas || dayHas (Phase 8.24 扩 day)
 *   - 走 windowedCost 透传: 切 7d/30d → cost_by_day 自动 filter
 *   - empty data 时 "暂无 trend 数据" 显示 (跟 CostBarChart 同样 empty pattern)
 */

test.describe('CostTrendChart trend line (Phase 8.24)', () => {
  test.setTimeout(30000)

  test('renders cost-trend-chart canvas when cost_by_day has data', async ({ page }) => {
    // Mock /api/workflows/active 返 cost_by_scenario + cost_by_tier + cost_by_day fixture
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
          node_count: 5,
          steps: 5,
          total_cost_usd: 0.025,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: {
            chapter_writing: 0.015,
            chapter_review: 0.010,
          },
          cost_by_tier: {
            sonnet: 0.020,
            haiku: 0.005,
          },
          // Phase 8.23 后端 cost_by_day: 3 days data → trend line 3 points
          cost_by_day: {
            '2026-06-05': 0.010,
            '2026-06-06': 0.008,
            '2026-06-07': 0.007,
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // CostTrendChart canvas 可见 (跟 CostBarChart canvas 一样)
    const trendCanvas = page.locator('.cost-trend-chart canvas')
    await expect(trendCanvas.first()).toBeVisible({ timeout: 10000 })
  })

  test('shows empty fallback when cost_by_day is empty', async ({ page }) => {
    // Mock 后端: cost_by_scenario/tier 仍返 (有数据, 触发 hasCost gate),
    // cost_by_day 返空 (empty trend)
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: true,
          completed: 1,
          failed: 0,
          paused: false,
          paused_nodes: [],
          node_count: 1,
          steps: 1,
          total_cost_usd: 0.01,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: { chapter_writing: 0.01 },
          cost_by_tier: { sonnet: 0.01 },
          cost_by_day: {},  // empty → 走 CostTrendChart hasData=false → empty UI
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // CostBarChart 仍渲染 (scenarioHas)
    const barCanvas = page.locator('.cost-bar-chart canvas')
    await expect(barCanvas.first()).toBeVisible({ timeout: 10000 })

    // CostTrendChart 也仍渲染 (hasCost=true, scenario OR tier OR day → scenario 触发)
    // 但 hasData (costByDay.length === 0) → 走 .cost-trend-chart-empty 提示
    const trendWrapper = page.locator('.cost-trend-chart-wrapper')
    await expect(trendWrapper).toBeVisible()
    const emptyMsg = page.locator('.cost-trend-chart-empty')
    await expect(emptyMsg).toBeVisible({ timeout: 10000 })
    await expect(emptyMsg).toContainText('暂无 trend 数据')
  })

  test('hasCost gate includes dayHas (day-only data shows cost section)', async ({ page }) => {
    // Mock 后端: 只 cost_by_day 有数据, scenario/tier 返空 → dayHas 触发 hasCost
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: true,
          completed: 1,
          failed: 0,
          paused: false,
          paused_nodes: [],
          node_count: 1,
          steps: 1,
          total_cost_usd: 0.02,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: {},  // empty
          cost_by_tier: {},       // empty
          cost_by_day: {          // ONLY data source for this test
            '2026-06-07': 0.02,
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // hasCost gate 走 dayHas → cost-section 仍渲染
    const costSection = page.locator('.cost-section')
    await expect(costSection).toBeVisible({ timeout: 10000 })

    // CostTrendChart 也仍渲染 (有 day data → hasData=true)
    const trendCanvas = page.locator('.cost-trend-chart canvas')
    await expect(trendCanvas.first()).toBeVisible({ timeout: 10000 })

    // CostBarChart 在 hasData=false (costByScenario + costByTier 都空)
    // → 走 .cost-bar-chart-empty
    const barEmpty = page.locator('.cost-bar-chart-empty')
    await expect(barEmpty).toBeVisible()
  })

  test('cost-section hidden when no scenario/tier/day data (all empty)', async ({ page }) => {
    // Mock 后端: 3 个 cost_* 字段都空 → hasCost 走 (false || false || false) = false
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: false,  // 0 records
          completed: 0,
          failed: 0,
          paused: false,
          paused_nodes: [],
          node_count: 0,
          steps: 0,
          total_cost_usd: 0,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: {},
          cost_by_tier: {},
          cost_by_day: {},
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // hasCost=false → cost-section 隐藏
    const costSection = page.locator('.cost-section')
    await expect(costSection).not.toBeVisible()
  })
})
