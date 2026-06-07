import { test, expect } from '@playwright/test'

/**
 * E2E: Phase 8.15 — SidebarCostBanner per-tier budget rows (3 row)
 * 验证 Sidebar 底部 .sidebar-cost-banner 在 status.budget_by_tier 暴露时,
 * 加 3 个 tier row (haiku/sonnet/opus) 在 activeBudget 进度条**下方**:
 *   - 顺序 Enum 顺序: haiku → sonnet → opus (deterministic)
 *   - 每 row 含: tier label (英文名) + used/budget/pct 文本 + progress-bar (.ok | .exceeded fill)
 *   - 未设 tier (空 dict) → row 隐藏 (tierBudgets computed filter)
 *   - 跟 Phase 8.12 activeBudget cascade 兼容 (旧 row 不破, 旧 Phase 8.8 budget cascade 仍显)
 *
 * 跟 dashboard_budget.spec.js (Phase 8.8) + sidebar_banner_priority_cascade.spec.js (Phase 8.12) +
 * cost-bar-chart-tier-mode.spec.js (Phase 8.13) + sidebar_cost_banner.spec.js (Phase 8.11) 同模式:
 * page.route mock + 断言 .sidebar-cost-tier-row visible
 *
 * 当前 Playwright runner 未装 (跟 Phase 7.6/8.7/8.8/8.11/8.12/8.13 一致),作为契约文档存在。
 * 契约:
 *   - 当 status.budget_by_tier 含 3 tier (haiku/sonnet/opus 都 set), 渲染 3 个
 *     .sidebar-cost-tier-row, 顺序 haiku → sonnet → opus
 *   - 每 row 文本含 "预算:" (跟 activeBudget 文本一致), tier name (lowercase) +
 *     "$" + used_usd + "$" + budget_usd + "%"
 *   - 每 row 含 .progress-bar + .progress-bar-fill (复用 Phase 8.11 CSS 0 改)
 *   - status="exceeded" → fill class 含 "exceeded" (红色)
 *   - status="ok" → fill class 含 "ok" (绿色)
 *   - 未设 tier (空 dict) → row 隐藏 (filter out)
 *   - Phase 8.12 activeBudget cascade 仍工作 (跟 tier row 共存, 0 互破)
 *   - a11y: role="status" + aria-live="polite" + aria-label (跟 activeBudget 一致)
 *   - data-testid="sidebar-cost-tier-row" 跟 Phase 8.13 CostBarChart testid 同 convention
 */

test.describe('SidebarCostBanner per-tier budget rows (Phase 8.15)', () => {
  test.setTimeout(30000)

  test('renders 3 tier rows when all budgets set (haiku/sonnet/opus)', async ({ page }) => {
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
          total_cost_usd: 0.1234,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: { chapter_writing: 0.1234 },
          cost_by_tier: { haiku: 0.0, sonnet: 0.0, opus: 0.1234 },
          budget_by_tier: {
            haiku: { status: 'ok', budget_usd: 0.10, used_usd: 0.0, used_pct: 0.0 },
            sonnet: { status: 'ok', budget_usd: 0.50, used_usd: 0.0, used_pct: 0.0 },
            opus: { status: 'ok', budget_usd: 1.00, used_usd: 0.1234, used_pct: 12.34 },
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/')
    await page.waitForLoadState('networkidle')

    const banner = page.locator('.sidebar-cost-banner')
    await expect(banner).toBeVisible({ timeout: 10000 })

    // 3 tier rows
    const rows = page.locator('[data-testid="sidebar-cost-tier-row"]')
    await expect(rows).toHaveCount(3, { timeout: 5000 })
  })

  test('hides row when budget unset (empty dict)', async ({ page }) => {
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: true,
          total_cost_usd: 0.5,
          cost_by_scenario: { chapter_writing: 0.5 },
          cost_by_tier: { haiku: 0.0, sonnet: 0.5, opus: 0.0 },
          // haiku empty dict → 隐藏; sonnet set; opus empty dict → 隐藏
          budget_by_tier: {
            haiku: {},
            sonnet: { status: 'ok', budget_usd: 0.50, used_usd: 0.0, used_pct: 0.0 },
            opus: {},
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/')
    await page.waitForLoadState('networkidle')

    const banner = page.locator('.sidebar-cost-banner')
    await expect(banner).toBeVisible({ timeout: 10000 })

    // 只 sonnet 可见
    const rows = page.locator('[data-testid="sidebar-cost-tier-row"]')
    await expect(rows).toHaveCount(1, { timeout: 5000 })
  })

  test('progress bar shows exceeded class when status=exceeded', async ({ page }) => {
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: true,
          total_cost_usd: 1.5,
          cost_by_scenario: { chapter_writing: 1.5 },
          cost_by_tier: { haiku: 0.0, sonnet: 0.0, opus: 1.5 },
          budget_by_tier: {
            haiku: { status: 'ok', budget_usd: 0.10, used_usd: 0.0, used_pct: 0.0 },
            sonnet: { status: 'ok', budget_usd: 0.50, used_usd: 0.0, used_pct: 0.0 },
            // opus exceeded: used 1.20 / budget 1.00 = 120% (clipped 100% width)
            opus: { status: 'exceeded', budget_usd: 1.00, used_usd: 1.20, used_pct: 120.0 },
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/')
    await page.waitForLoadState('networkidle')

    const banner = page.locator('.sidebar-cost-banner')
    await expect(banner).toBeVisible({ timeout: 10000 })

    // opus row 含 exceeded fill
    const opusRow = page.locator('[data-testid="sidebar-cost-tier-row"]').filter({ hasText: 'opus' })
    await expect(opusRow).toBeVisible({ timeout: 5000 })
    const fill = opusRow.locator('.progress-bar-fill')
    const fillClass = await fill.getAttribute('class')
    expect(fillClass).toContain('exceeded')

    // Width clipped to 100%
    const widthStyle = await fill.getAttribute('style')
    expect(widthStyle).toContain('width: 100%')
  })

  test('progress bar shows ok class when status=ok', async ({ page }) => {
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: true,
          total_cost_usd: 0.05,
          cost_by_scenario: { chapter_writing: 0.05 },
          cost_by_tier: { haiku: 0.0, sonnet: 0.05, opus: 0.0 },
          budget_by_tier: {
            haiku: { status: 'ok', budget_usd: 0.10, used_usd: 0.0, used_pct: 0.0 },
            sonnet: { status: 'ok', budget_usd: 0.50, used_usd: 0.05, used_pct: 10.0 },
            opus: { status: 'ok', budget_usd: 1.00, used_usd: 0.0, used_pct: 0.0 },
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/')
    await page.waitForLoadState('networkidle')

    const banner = page.locator('.sidebar-cost-banner')
    await expect(banner).toBeVisible({ timeout: 10000 })

    // sonnet row 含 ok fill
    const sonnetRow = page.locator('[data-testid="sidebar-cost-tier-row"]').filter({ hasText: 'sonnet' })
    await expect(sonnetRow).toBeVisible({ timeout: 5000 })
    const fill = sonnetRow.locator('.progress-bar-fill')
    const fillClass = await fill.getAttribute('class')
    expect(fillClass).toContain('ok')

    // Width 10% (sonnet 10%)
    const widthStyle = await fill.getAttribute('style')
    expect(widthStyle).toContain('width: 10%')
  })

  test('order is haiku → sonnet → opus (Enum 顺序 deterministic)', async ({ page }) => {
    await page.route('**/api/workflows/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          workflow_name: 'novel_writing',
          is_active: true,
          total_cost_usd: 0.5,
          cost_by_scenario: { chapter_writing: 0.5 },
          cost_by_tier: { haiku: 0.1, sonnet: 0.2, opus: 0.2 },
          budget_by_tier: {
            haiku: { status: 'ok', budget_usd: 0.10, used_usd: 0.05, used_pct: 50.0 },
            sonnet: { status: 'ok', budget_usd: 0.50, used_usd: 0.2, used_pct: 40.0 },
            opus: { status: 'ok', budget_usd: 1.00, used_usd: 0.5, used_pct: 50.0 },
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/')
    await page.waitForLoadState('networkidle')

    const banner = page.locator('.sidebar-cost-banner')
    await expect(banner).toBeVisible({ timeout: 10000 })

    // 顺序: haiku → sonnet → opus
    const rows = page.locator('[data-testid="sidebar-cost-tier-row"]')
    await expect(rows).toHaveCount(3, { timeout: 5000 })
    const texts = await rows.allTextContents()
    expect(texts[0]).toContain('haiku')
    expect(texts[1]).toContain('sonnet')
    expect(texts[2]).toContain('opus')
  })

  test('Phase 8.12 active budget cascade unchanged (tier rows coexist)', async ({ page }) => {
    // Mock with cost_budget_status (Phase 8.8) + budget_per_day (Phase 8.12) + budget_by_tier (Phase 8.15)
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
          total_cost_usd: 0.075,
          pending_decisions: [],
          executions: {},
          score_data: {},
          cost_by_scenario: { chapter_writing: 0.075 },
          cost_by_tier: { haiku: 0.0, sonnet: 0.0, opus: 0.075 },
          // Phase 8.8 per-run cost_budget_status (exceeded, used_pct 75.0% — 未 clip)
          cost_budget_status: {
            status: 'exceeded',
            budget_usd: 0.10,
            used_usd: 0.075,
            used_pct: 75.0,
          },
          // Phase 8.15 per-tier (opus set, others empty)
          budget_by_tier: {
            haiku: {},
            sonnet: {},
            opus: { status: 'ok', budget_usd: 1.00, used_usd: 0.075, used_pct: 7.5 },
          },
        }),
      })
    })

    await page.goto('http://localhost:3000/')
    await page.waitForLoadState('networkidle')

    const banner = page.locator('.sidebar-cost-banner')
    await expect(banner).toBeVisible({ timeout: 10000 })

    // Phase 8.12 activeBudget cascade 仍显 (per-run cost_budget_status exceeded, label "本次")
    const activeBudgetText = page.locator('.sidebar-cost-budget-text')
    await expect(activeBudgetText).toBeVisible({ timeout: 5000 })
    await expect(activeBudgetText).toContainText('本次')
    await expect(activeBudgetText).toContainText('75.0%')

    // Phase 8.15 tier row 也可见 (opus)
    const tierRows = page.locator('[data-testid="sidebar-cost-tier-row"]')
    await expect(tierRows).toHaveCount(1, { timeout: 5000 })
    await expect(tierRows.first()).toContainText('opus')
  })
})
