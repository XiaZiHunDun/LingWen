import { test, expect } from '@playwright/test'

/**
 * E2E: Phase 8.28 — Soft Warning 三态 (ok / warning / exceeded)
 * 验证 SidebarCostBanner 组件 progress-bar-fill 颜色根据 used_pct 自动切换:
 *   - used_pct < 80% → .ok (绿)
 *   - 80% ≤ used_pct < 100% → .warning (黄)
 *   - used_pct ≥ 100% → .exceeded (红)
 *
 * 跟 sidebar_cost_banner.spec.js (Phase 8.11+) + sidebar-tier-budget.spec.js
 * (Phase 8.21 tier alarm) 同模式: page.route mock + 断言 CSS class.
 *
 * 当前 Playwright runner 未装 (跟 Phase 7.6/8.7/8.8/8.13/8.17/8.27 一致),
 * 作为契约文档存在.
 *
 * 契约:
 *   - activeBudget 进度条 + tier 进度条 (3 行) 都应用 budgetState(used_pct)
 *   - budgetState 阈值: <80% ok / 80-100% warning / >=100% exceeded
 *   - 跟 Phase 8.21 tier alarm 阈值一致 (TIER_ALARM_WARNING_PCT=80)
 *   - 0 改 backend cost_budget_status (二态 'ok'/'exceeded' 保留)
 *   - 0 改 Phase 8.12 budget cascade / Phase 8.15 tier row layout
 *   - warning 黄色 #e6a23c 跟 Phase 8.21 tier alarm warning 一致
 */

test.describe('Sidebar Soft Warning Three-State (Phase 8.28)', () => {
  test.setTimeout(30000)

  test('progress bar shows ok class when used_pct < 80%', async ({ page }) => {
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: true,
          completed: 3,
          failed: 0,
          paused: false,
          paused_nodes: [],
          node_count: 7,
          steps: 3,
          total_cost_usd: 0.020,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: {
            chapter_writing: 0.012,
            chapter_review: 0.008,
          },
          cost_budget_status: {
            status: 'ok',
            budget_usd: 0.10,
            used_usd: 0.020,
            used_pct: 20.0,  // < 80% → ok (绿)
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    const fill = page.getByTestId('progress-bar-fill').first()
    await expect(fill).toHaveClass(/ok/)
    await expect(fill).not.toHaveClass(/warning/)
    await expect(fill).not.toHaveClass(/exceeded/)
  })

  test('progress bar shows warning class when 80% <= used_pct < 100%', async ({ page }) => {
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
          total_cost_usd: 0.085,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: {
            chapter_writing: 0.050,
            chapter_review: 0.035,
          },
          cost_budget_status: {
            status: 'ok',  // backend 二态: ok (前端按 85% 升级 warning)
            budget_usd: 0.10,
            used_usd: 0.085,
            used_pct: 85.0,  // 80% ≤ 85% < 100% → warning (黄)
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    const fill = page.getByTestId('progress-bar-fill').first()
    await expect(fill).toHaveClass(/warning/)
    await expect(fill).not.toHaveClass(/ok/)
    await expect(fill).not.toHaveClass(/exceeded/)
  })

  test('progress bar shows exceeded class when used_pct >= 100%', async ({ page }) => {
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: true,
          completed: 5,
          failed: 1,
          paused: false,
          paused_nodes: [],
          node_count: 7,
          steps: 5,
          total_cost_usd: 0.120,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: {
            chapter_writing: 0.070,
            chapter_review: 0.050,
          },
          cost_budget_status: {
            status: 'exceeded',  // backend 二态: exceeded (跟 frontend 一致)
            budget_usd: 0.10,
            used_usd: 0.120,
            used_pct: 120.0,  // >= 100% → exceeded (红)
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    const fill = page.getByTestId('progress-bar-fill').first()
    await expect(fill).toHaveClass(/exceeded/)
    await expect(fill).not.toHaveClass(/ok/)
    await expect(fill).not.toHaveClass(/warning/)
  })
})
