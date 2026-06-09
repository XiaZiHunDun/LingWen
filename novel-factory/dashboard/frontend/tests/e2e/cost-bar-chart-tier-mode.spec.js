import { test, expect } from '@playwright/test'

/**
 * E2E: Phase 8.13 — CostBarChart tier-mode toggle
 * 验证 CostBarChart 组件在 mode='scenario' / mode='tier' 之间切换时:
 * - 2 tab 按钮 (data-testid="mode-tab-scenario" / "mode-tab-tier") 渲染
 * - scenario tab 默认 .active
 * - v-model:mode 更新到 'tier' 后 tier tab 变 .active
 * - 点击 tier tab 触发 update:mode emit('tier')
 * - data source 切换: scenario 走 costByScenario; tier 走 costByTier
 *
 * 跟 dashboard_cost.spec.js (Phase 8.7) + dashboard_budget.spec.js (Phase 8.8) +
 * sidebar_cost_banner.spec.js (Phase 8.11) 同模式: page.route mock + 断言 visible
 *
 * Phase 8.45.3: Playwright runner 已装 (@playwright/test ^1.49.0, dev opt-in),
 * 走 pnpm e2e:smoke 跑 (需 npx playwright install chromium 先装 browser, ~500MB).
 * 0 CI integration (vitest 仍 primary gate, Playwright 留 manual + future Phase 8.46+).
 * 契约:
 *   - 默认 mode='scenario' (向后兼容; 旧 caller 不传 mode 也走 scenario)
 *   - 渲染 2 tab button (data-testid="mode-tab-scenario" / "mode-tab-tier")
 *   - mode='scenario' 时 scenario tab .active + aria-selected="true"
 *   - mode='tier' 时 tier tab .active + aria-selected="true"
 *   - click tier tab → emit('update:mode', 'tier') → parent v-model 接
 *   - data source 切换: scenario 走 costByScenario; tier 走 costByTier
 *   - 切换 mode 后 chart option rebuild (data prop 走 displayData computed)
 *   - a11y: role="tablist" / role="tab" + aria-selected
 */

test.describe('CostBarChart tier-mode toggle (Phase 8.13)', () => {
  test.setTimeout(30000)

  test('renders 2 tab buttons with data-testid (scenario | tier)', async ({ page }) => {
    // Mock /api/workflows/active 返 cost_by_scenario + cost_by_tier fixture
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: true,
          completed: 7,
          failed: 0,
          paused: false,
          paused_nodes: [],
          node_count: 7,
          steps: 7,
          total_cost_usd: 0.045,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: {
            chapter_writing: 0.015,
            chapter_review: 0.008,
            polish_emotional_pacing: 0.012,
          },
          cost_by_tier: {
            premium: 0.025,
            standard: 0.015,
            budget: 0.005,
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // 2 tab button 可见
    const scenarioTab = page.locator('[data-testid="mode-tab-scenario"]')
    const tierTab = page.locator('[data-testid="mode-tab-tier"]')
    await expect(scenarioTab).toBeVisible({ timeout: 10000 })
    await expect(tierTab).toBeVisible({ timeout: 10000 })
  })

  test('defaults to scenario mode (scenario tab .active)', async ({ page }) => {
    // Mock 同上 (cost_by_scenario + cost_by_tier 都返)
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
          cost_by_tier: { standard: 0.01 },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // 默认 scenario tab .active, aria-selected="true"
    const scenarioTab = page.locator('[data-testid="mode-tab-scenario"]')
    await expect(scenarioTab).toHaveClass(/active/, { timeout: 10000 })
    await expect(scenarioTab).toHaveAttribute('aria-selected', 'true')

    // tier tab 相反
    const tierTab = page.locator('[data-testid="mode-tab-tier"]')
    await expect(tierTab).not.toHaveClass(/active/)
    await expect(tierTab).toHaveAttribute('aria-selected', 'false')
  })

  test('switches to tier mode when v-model:mode updates to "tier"', async ({ page }) => {
    // Mock 后端 fixture
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
          total_cost_usd: 0.05,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: { chapter_writing: 0.05 },
          cost_by_tier: {
            premium: 0.03,
            standard: 0.015,
            budget: 0.005,
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // 初始: scenario tab .active
    const scenarioTab = page.locator('[data-testid="mode-tab-scenario"]')
    const tierTab = page.locator('[data-testid="mode-tab-tier"]')
    await expect(scenarioTab).toHaveClass(/active/, { timeout: 10000 })

    // click tier tab → 触发 update:mode('tier') → WorkflowStatus.costMode 变 'tier'
    // → v-model:mode 把 mode prop 设为 'tier' → tier tab 变 .active
    await tierTab.click()
    await expect(tierTab).toHaveClass(/active/, { timeout: 5000 })
    await expect(tierTab).toHaveAttribute('aria-selected', 'true')

    // scenario tab 失活
    await expect(scenarioTab).not.toHaveClass(/active/)
    await expect(scenarioTab).toHaveAttribute('aria-selected', 'false')
  })

  test('chart re-renders with cost_by_tier data when mode=tier', async ({ page }) => {
    // Mock 后端 fixture (cost_by_tier 有数据, cost_by_scenario 也返作对照)
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
          total_cost_usd: 0.05,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: {
            chapter_writing: 0.05,
          },
          cost_by_tier: {
            premium: 0.03,
            standard: 0.015,
            budget: 0.005,
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // 切到 tier mode
    const tierTab = page.locator('[data-testid="mode-tab-tier"]')
    await tierTab.click()
    await expect(tierTab).toHaveClass(/active/, { timeout: 5000 })

    // ECharts canvas 仍渲染 (displayData 切到 costByTier 后 chart 重新 setOption)
    const canvas = page.locator('.cost-bar-chart canvas')
    await expect(canvas.first()).toBeVisible({ timeout: 5000 })
  })
})
