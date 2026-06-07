// Phase 8.16: 时间窗口 segmented control ceremonial e2e spec
// 4 test cases: WorkflowStatus 3 tabs visible / SidebarCostBanner 3 tabs visible /
// click 7d emits time_window query param / active state class moves on click
//
// 跟 Phase 7.6/8.7/8.8/8.11/8.13/8.14/8.15 9 specs 同模式:
// Playwright runner 未装, 作为契约文档存在 (header note).
// Mock 走 page.route('**/api/workflows/active**') 模式 (接受 query string).

import { test, expect } from '@playwright/test'

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173'

const ACTIVE_WORKFLOW = (cost_by_scenario, cost_by_tier) => ({
  workflow_name: 'novel_writing',
  is_active: true,
  paused: false,
  completed: 5,
  failed: 0,
  node_count: 7,
  steps: 12,
  cost_by_scenario,
  cost_by_tier,
  total_cost_usd: 0.15,
})

test.describe('Phase 8.16: time window segmented control', () => {
  test('shows_3_tabs_in_workflow_status', async ({ page }) => {
    await page.route('**/api/workflows/active**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(ACTIVE_WORKFLOW({ chapter_writing: 0.10 }, { sonnet: 0.05 })),
      })
    })
    await page.goto(`${BASE_URL}/workflows`)
    await expect(page.locator('[data-testid="time-window-7d"]')).toBeVisible()
    await expect(page.locator('[data-testid="time-window-30d"]')).toBeVisible()
    await expect(page.locator('[data-testid="time-window-all"]')).toBeVisible()
    // default 'all' active
    await expect(page.locator('[data-testid="time-window-all"]')).toHaveClass(/active/)
  })

  test('shows_3_tabs_in_sidebar_banner', async ({ page }) => {
    await page.route('**/api/workflows/active**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(ACTIVE_WORKFLOW({ chapter_writing: 0.10 }, { sonnet: 0.05 })),
      })
    })
    await page.goto(`${BASE_URL}/overview`)  // SidebarCostBanner always visible
    await expect(page.locator('[data-testid="sidebar-time-window-7d"]')).toBeVisible()
    await expect(page.locator('[data-testid="sidebar-time-window-30d"]')).toBeVisible()
    await expect(page.locator('[data-testid="sidebar-time-window-all"]')).toBeVisible()
  })

  test('clicking_7d_fetches_with_time_window_param', async ({ page }) => {
    let lastRequestUrl = null
    await page.route('**/api/workflows/active**', (route) => {
      lastRequestUrl = route.request().url()
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(ACTIVE_WORKFLOW({ chapter_writing: 0.05 }, { haiku: 0.02 })),
      })
    })
    await page.goto(`${BASE_URL}/workflows`)
    await page.locator('[data-testid="time-window-7d"]').click()
    // Wait for fetch to fire with time_window=7d query param
    await expect.poll(() => lastRequestUrl, { timeout: 2000 }).toContain('time_window=7d')
  })

  test('active_state_class_moves_on_click', async ({ page }) => {
    await page.route('**/api/workflows/active**', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(ACTIVE_WORKFLOW({ chapter_writing: 0.10 }, { sonnet: 0.05 })),
      })
    })
    await page.goto(`${BASE_URL}/workflows`)
    await page.locator('[data-testid="time-window-30d"]').click()
    await expect(page.locator('[data-testid="time-window-30d"]')).toHaveClass(/active/)
    await expect(page.locator('[data-testid="time-window-all"]')).not.toHaveClass(/active/)
  })
})
