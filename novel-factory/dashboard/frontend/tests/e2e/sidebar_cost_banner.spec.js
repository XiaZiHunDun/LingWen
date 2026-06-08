import { test, expect } from '@playwright/test'

/**
 * E2E: Phase 8.11 — Sidebar 持续 cost banner
 * 验证 sidebar 底部 .sidebar-cost-banner 跨 4 page (Overview / Decisions / Workflows / placeholders) 可见;
 * 当 cost_by_scenario 有 entry 时显示,空时隐藏;budget 块有 budget_usd 时显示 budget line + progress bar。
 *
 * 跟 dashboard_budget.spec.js (Phase 8.8) + dashboard_cost.spec.js (Phase 8.7) + dashboard_radar.spec.js (Phase 7.6) 同模式:
 * page.route mock + 断言 .sidebar-cost-banner visible
 *
 * 当前 Playwright runner 未装 (跟 Phase 7.6/8.7/8.8 一致),作为契约文档存在。
 * 契约:
 *   - 当 cost_by_scenario 有 entry,渲染 .sidebar-cost-banner 块 (sidebar 底部)
 *   - 当 cost_by_scenario = {}, .sidebar-cost-banner NOT visible (v-if=hasCost 锁 false)
 *   - .sidebar-cost-total-text 含 "💰" + "$" (total USD)
 *   - 当 cost_budget_status.budget_usd != null, 渲染 .sidebar-cost-budget-text + .progress-bar
 *   - 当 cost_budget_status = {}, budget line + progress bar NOT visible (只 total)
 *   - 跨 page 切换 (Overview → Decisions → Workflows) banner 持续可见
 */

test.describe('Sidebar Cost Banner (Phase 8.11)', () => {
  test.setTimeout(30000)

  test('visible on Overview page when cost_by_scenario has entry', async ({ page }) => {
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: false,
          total_cost_usd: 0.0023,
          cost_by_scenario: { chapter_writing: 0.0023 },
          cost_budget_status: {
            status: 'ok',
            budget_usd: 0.1,
            used_usd: 0.0023,
            used_pct: 2.3,
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/')
    await page.waitForLoadState('networkidle')

    const banner = page.getByTestId('sidebar-cost-banner')
    await expect(banner).toBeVisible({ timeout: 10000 })

    const totalText = page.getByTestId('sidebar-cost-total-text')
    await expect(totalText).toContainText('💰')
    await expect(totalText).toContainText('$0.0023')

    const budgetText = page.getByTestId('sidebar-cost-budget-text')
    await expect(budgetText).toContainText('预算:')
    await expect(budgetText).toContainText('$0.0023')
    await expect(budgetText).toContainText('$0.1000')
    await expect(budgetText).toContainText('2.3%')

    const progressFill = page.getByTestId('progress-bar-fill')
    await expect(progressFill).toBeVisible({ timeout: 5000 })
  })

  test('hides when cost_by_scenario is empty', async ({ page }) => {
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: false,
          total_cost_usd: 0.0,
          cost_by_scenario: {},
          cost_budget_status: {},
        }),
      })
    })

    await page.goto('http://localhost:3000/')
    await page.waitForLoadState('networkidle')

    const banner = page.getByTestId('sidebar-cost-banner')
    await expect(banner).not.toBeVisible({ timeout: 5000 })
  })

  test('survives page navigation across Overview / Decisions / Workflows', async ({ page }) => {
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
          node_count: 7,
          steps: 1,
          total_cost_usd: 0.01,
          pending_decisions: [],
          executions: { write_chapter: 'COMPLETED' },
          score_data: {},
          cost_by_scenario: { chapter_writing: 0.01 },
          cost_budget_status: {
            status: 'ok',
            budget_usd: 0.1,
            used_usd: 0.01,
            used_pct: 10.0,
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/')
    await page.waitForLoadState('networkidle')
    await expect(page.getByTestId('sidebar-cost-banner')).toBeVisible({ timeout: 10000 })

    await page.click('a.nav-item:has-text("决策")')
    await page.waitForTimeout(500)
    await expect(page.getByTestId('sidebar-cost-banner')).toBeVisible({ timeout: 5000 })

    await page.click('a.nav-item:has-text("工作流")')
    await page.waitForTimeout(500)
    await expect(page.getByTestId('sidebar-cost-banner')).toBeVisible({ timeout: 5000 })
  })
})
