import { test, expect } from '@playwright/test'

/**
 * E2E: Phase 8.7 — Dashboard Token 成本柱状图
 * 验证 WorkflowStatus 组件在 active workflow 含 cost_by_scenario 时渲染柱状图
 *
 * 跟 dashboard_radar.spec.js (Phase 7.6) 同模式: page.route mock + 断言
 * .cost-bar-chart canvas + .cost-total-usd 总计显示
 */

test.describe('Dashboard Cost Bar Chart (Phase 8.7)', () => {
  test.setTimeout(30000)

  test('renders cost bar chart from workflow status when cost_by_scenario present', async ({ page }) => {
    // Mock /api/workflows/active 返 cost_by_scenario fixture
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
          executions: {
            write_chapter: 'COMPLETED',
            review_chapter: 'COMPLETED',
            polish_emotional_pacing: 'COMPLETED',
            polish_ai_trace_removal: 'COMPLETED',
            polish_merge: 'COMPLETED',
            emit_chapter: 'COMPLETED',
          },
          score_data: {},
          cost_by_scenario: {
            chapter_writing: 0.015,
            chapter_review: 0.008,
            polish_emotional_pacing: 0.012,
            polish_ai_trace_removal: 0.006,
            polish_merge: 0.004,
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/workflows')
    await page.waitForLoadState('networkidle')

    // cost 柱状图组件应可见
    const chart = page.locator('.cost-bar-chart')
    await expect(chart).toBeVisible({ timeout: 10000 })

    // 验证 ECharts canvas 渲染 (跟 radar 同模式)
    const canvas = page.locator('.cost-bar-chart canvas')
    await expect(canvas.first()).toBeVisible({ timeout: 5000 })

    // 验证总计 USD 显示
    const totalUsd = page.locator('.cost-total-usd')
    await expect(totalUsd).toContainText('$0.0450')
  })
})
