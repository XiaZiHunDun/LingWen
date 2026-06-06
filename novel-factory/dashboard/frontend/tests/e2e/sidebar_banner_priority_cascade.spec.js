import { test, expect } from '@playwright/test'

/**
 * E2E: Phase 8.12 — Sidebar Cost Banner priority cascade (3 档 budget)
 * 验证当 3 档 budget (per-run/per-day/per-week) 同时被 server 暴露时,
 * Sidebar 底部 .sidebar-cost-banner 只显 "最紧急" 那一档:
 *   - priority cascade 规则: exceeded 优先, 同 status 按 used_pct desc
 *   - 测试场景: per-run ok 50% + per-day exceeded 120% + per-week ok 80%
 *     → 期望 banner 显 "今日" (per-day, exceeded 优先 over per-run/per-week)
 *   - active 只 1 个 budget block, 其他档 label (本次/本周) 不显
 *   - progress bar 100% (exceeded 红色 fill, clip 在 100%)
 *   - fill class 'exceeded' (exceeded 状态视觉)
 *
 * 跟 dashboard_budget.spec.js (Phase 8.8) + dashboard_cost.spec.js (Phase 8.7) +
 * dashboard_radar.spec.js (Phase 7.6) + sidebar_cost_banner.spec.js (Phase 8.11) 同模式:
 * page.route mock + 断言 .sidebar-cost-banner visible
 *
 * 当前 Playwright runner 未装 (跟 Phase 7.6/8.7/8.8/8.11 一致),作为契约文档存在。
 * 契约:
 *   - 当 status 含 3 档 budget (cost_budget_status + budget_per_day + budget_per_week),
 *     .sidebar-cost-banner 显最紧急档 (exceeded 优先 → used_pct desc)
 *   - .sidebar-cost-budget-text 含 active 档 label ("本次" / "今日" / "本周")
 *   - 仅 active 档 label 显, 其他档 label 不显 (banner 只 1 budget block)
 *   - progress-bar-fill width = Math.min(100, used_pct)% (clip 在 100%)
 *   - progress-bar-fill class 含 "exceeded" when active.status === 'exceeded'
 */

test.describe('Sidebar Cost Banner Priority Cascade (Phase 8.12)', () => {
  test.setTimeout(30000)

  test('shows most urgent budget (exceeded priority over ok)', async ({ page }) => {
    // Stub the active workflow status endpoint with 3 budget tiers
    //   per-run:    ok       50%   (used 0.05 / budget 0.1)
    //   per-day:    exceeded 120%  (used 0.06 / budget 0.05)  ← 期望 active (exceeded 优先)
    //   per-week:   ok       80%   (used 0.16 / budget 0.2)
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
          total_cost_usd: 0.06,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: { chapter_writing: 0.06 },
          cost_budget_status: {
            status: 'ok',
            budget_usd: 0.1,
            used_usd: 0.05,
            used_pct: 50.0,
          },
          budget_per_day: {
            status: 'exceeded',
            budget_usd: 0.05,
            used_usd: 0.06,
            used_pct: 120.0,
          },
          budget_per_week: {
            status: 'ok',
            budget_usd: 0.2,
            used_usd: 0.16,
            used_pct: 80.0,
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/')
    await page.waitForLoadState('networkidle')

    // Sidebar banner 可见
    const banner = page.locator('.sidebar-cost-banner')
    await expect(banner).toBeVisible({ timeout: 10000 })

    // Total USD 正常显 (cost_by_scenario has entry)
    const totalText = page.locator('.sidebar-cost-total-text')
    await expect(totalText).toContainText('💰')
    await expect(totalText).toContainText('$0.0600')

    // Banner 文本含 "今日" (per-day, exceeded 优先 over per-run/per-week)
    const budgetText = page.locator('.sidebar-cost-budget-text')
    await expect(budgetText).toContainText('今日')
    await expect(budgetText).toContainText('$0.0600') // active.used_usd (per-day)
    await expect(budgetText).toContainText('$0.0500') // active.budget_usd (per-day)
    await expect(budgetText).toContainText('100.0%')  // clipped from 120% to 100%

    // Per-run "本次" / per-week "本周" label 不显示 (active 只 1 个 budget block)
    await expect(budgetText).not.toContainText('本次')
    await expect(budgetText).not.toContainText('本周')

    // Progress bar 100% (exceeded 红色 fill, clip 在 100%)
    const fill = page.locator('.progress-bar-fill')
    await expect(fill).toBeVisible({ timeout: 5000 })
    const widthStyle = await fill.getAttribute('style')
    expect(widthStyle).toContain('width: 100%')

    // Fill class 是 'exceeded'
    const fillClass = await fill.getAttribute('class')
    expect(fillClass).toContain('exceeded')
  })
})
