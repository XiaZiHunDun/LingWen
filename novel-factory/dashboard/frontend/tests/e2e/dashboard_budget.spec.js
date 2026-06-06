import { test, expect } from '@playwright/test'

/**
 * E2E: Phase 8.8 — Dashboard 成本预算告警横幅
 * 验证 WorkflowStatus 组件在 active workflow 含 cost_budget_status.exceeded 时
 * 渲染红色告警 banner;含 status:"ok" 时渲染绿色正常 banner。
 *
 * 跟 dashboard_cost.spec.js (Phase 8.7) + dashboard_radar.spec.js (Phase 7.6) 同模式:
 * page.route mock + 断言 .cost-budget-section visible
 *
 * 当前 Playwright runner 未装 (跟 Phase 7.6/8.7 一致),作为契约文档存在。
 * 契约:
 *   - 当 cost_budget_status.budget_usd != null,渲染 .cost-budget-section 块
 *   - status === "exceeded" 加 .exceeded class (红 border-left)
 *   - status === "ok" 加 .ok class (绿 border-left)
 *   - .cost-budget-text 含 "Budget exceeded" 或 "Budget: $" 文本
 */

test.describe('Dashboard Cost Budget Banner (Phase 8.8)', () => {
  test.setTimeout(30000)

  test('renders exceeded banner when cost_budget_status.exceeded', async ({ page }) => {
    // Mock /api/workflows/active 返 cost_budget_status fixture (exceeded)
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: true,
          completed: 2,
          failed: 1,
          paused: false,
          paused_nodes: [],
          node_count: 7,
          steps: 3,
          total_cost_usd: 0.045,
          pending_decisions: [],
          executions: {
            write_chapter: 'COMPLETED',
            review_chapter: 'COMPLETED',
          },
          score_data: {},
          cost_by_scenario: {
            chapter_writing: 0.025,
            chapter_review: 0.020,
          },
          cost_budget_status: {
            status: 'exceeded',
            budget_usd: 0.04,
            used_usd: 0.045,
            used_pct: 112.5,
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // banner 容器 + exceeded class 可见
    const banner = page.locator('.cost-budget-section')
    await expect(banner).toBeVisible({ timeout: 10000 })

    const exceeded = page.locator('.cost-budget-section.exceeded')
    await expect(exceeded).toBeVisible({ timeout: 5000 })

    // 文本断言
    const text = page.locator('.cost-budget-text')
    await expect(text).toContainText('Budget exceeded')
    await expect(text).toContainText('$0.0450')
    await expect(text).toContainText('$0.0400')
    await expect(text).toContainText('112.5%')
  })

  test('renders ok banner when cost_budget_status.ok', async ({ page }) => {
    // Mock /api/workflows/active 返 cost_budget_status fixture (ok, green)
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
          total_cost_usd: 0.02,
          pending_decisions: [],
          executions: {
            write_chapter: 'COMPLETED',
            review_chapter: 'COMPLETED',
            polish_emotional_pacing: 'COMPLETED',
            polish_ai_trace_removal: 'COMPLETED',
            polish_merge: 'COMPLETED',
          },
          score_data: {},
          cost_by_scenario: {
            chapter_writing: 0.012,
            chapter_review: 0.008,
          },
          cost_budget_status: {
            status: 'ok',
            budget_usd: 0.10,
            used_usd: 0.02,
            used_pct: 20.0,
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // banner 容器 + ok class 可见 (无 exceeded)
    const banner = page.locator('.cost-budget-section')
    await expect(banner).toBeVisible({ timeout: 10000 })

    const ok = page.locator('.cost-budget-section.ok')
    await expect(ok).toBeVisible({ timeout: 5000 })

    // 文本断言 (无 "exceeded")
    const text = page.locator('.cost-budget-text')
    await expect(text).toContainText('Budget:')
    await expect(text).toContainText('$0.0200')
    await expect(text).toContainText('$0.1000')
    await expect(text).toContainText('20.0%')
  })
})
