// tests/e2e-smoke/smoke.spec.js — Phase 8.45.3
// E2E smoke (4 tests, 走真实 Chromium browser).
// 0 browser 装 = 0 跑 (header note: dev 需 npx playwright install chromium opt-in).
// 走 vitest 不跑 (vitest.config.js exclude 'tests/e2e/**', e2e-smoke/ 也加 exclude).
//
// Pre-conditions:
//   1. 启 vite dev server: pnpm dev (port 5173)
//   2. 装 browser: npx playwright install chromium (~500MB opt-in)
//   3. 跑 smoke: pnpm e2e:smoke
//
// 0 CI integration (Phase 8.45 留 followup, vitest 仍 primary gate)

import { test, expect } from '@playwright/test'

test.describe('Dashboard smoke (Phase 8.45.3)', () => {
  test('page title contains "Dashboard"', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/Dashboard/)
  })

  test('navigate to /workflows via nav click', async ({ page }) => {
    await page.goto('/')
    // 点击 "工作流" nav
    await page.click('a.nav-item:has-text("工作流")')
    await expect(page).toHaveURL(/#\/workflows|workflows/)
  })

  test('WS connect indicator visible (load complete)', async ({ page }) => {
    await page.goto('/')
    // Phase 8.45.3 加 data-testid="ws-status" 在 SidebarCostBanner 元素 (Vue 3.5
    // fallthrough to root). WS connect status = sidebar-cost-banner visible.
    await expect(page.locator('[data-testid="ws-status"]')).toBeVisible({ timeout: 5000 })
  })

  test('error banner on API failure', async ({ page }) => {
    // mock all api calls 失败, 验证 error-banner 显
    await page.route('**/api/**', route => route.abort())
    await page.goto('/')
    await expect(page.locator('[data-testid="error-banner"]')).toBeVisible({ timeout: 5000 })
  })
})
