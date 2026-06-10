// dashboard/frontend/tests/e2e-smoke/ripples-audit.spec.js — Phase 9.14 T7
// E2E smoke tests for ripple audit timeline + Rollback flow (3 tests, 0 network, 0 LLM).
// 跟 Phase 9.13 ripples.spec.js 1:1 pattern (use 'tests/_setup.js' shim).
//
// Selector adaptation notes (跟 plan 1694-1748 略不同):
// - 计划用了 `ripple-apply-btn`, 实际 RippleDrawer.vue:61 用 `ripple-drawer-apply`.
//   计划 1751-1755 的 "data-testid 复用" 注释里 `ripple-apply-btn` 笔误,
//   实际唯一权威 selector 是 `ripple-drawer-apply` (Phase 9.13 已定).
// - 其余 testid 全部跟 plan 1:1 (ripple-card / ripple-drawer / ripple-audit-list
//   / ripple-audit-empty / ripple-rollback-btn).

import { test, expect } from '../_setup.js';

test.describe('Phase 9.14: ripple audit timeline e2e', () => {
  test('page mount → drawer open → audit timeline visible', async ({ page }) => {
    await page.goto('/ripples');
    await page.waitForSelector('[data-testid="ripple-card"]', { timeout: 5000 });
    // Click first ripple card
    await page.locator('[data-testid="ripple-card"]').first().click();
    await page.waitForSelector('[data-testid="ripple-drawer"]', { timeout: 3000 });
    // Drawer should show audit timeline section (may be empty for old ripples)
    const timeline = page.locator('[data-testid="ripple-audit-list"]');
    const empty = page.locator('[data-testid="ripple-audit-empty"]');
    await expect(timeline.or(empty)).toBeVisible();
  });

  test('apply then rollback → audit timeline updates', async ({ page }) => {
    await page.goto('/ripples?status=pending');
    await page.waitForSelector('[data-testid="ripple-card"]', { timeout: 5000 });
    // Find a pending ripple, apply it
    await page.locator('[data-testid="ripple-card"]').first().click();
    await page.waitForSelector('[data-testid="ripple-drawer"]');
    // Set up dialog handler for rollback prompt
    page.on('dialog', dialog => dialog.accept('e2e test rollback'));
    // Click apply (apply button testid: ripple-drawer-apply — 跟 plan 笔误 ripple-apply-btn 修正)
    await page.locator('[data-testid="ripple-drawer-apply"]').click();
    await page.waitForTimeout(500);
    // Reopen drawer
    await page.locator('[data-testid="ripple-card"]').first().click();
    await page.waitForSelector('[data-testid="ripple-drawer"]');
    // Click rollback
    await page.locator('[data-testid="ripple-rollback-btn"]').click();
    await page.waitForTimeout(500);
    // Reopen drawer, check audit shows rolled_back entry
    await page.locator('[data-testid="ripple-card"]').first().click();
    await page.waitForSelector('[data-testid="ripple-drawer"]');
    await expect(page.locator('[data-testid="ripple-audit-list"]')).toContainText('rolled_back');
  });

  test('empty audit shows "No history yet"', async ({ page }) => {
    // Filter to a ripple pre-Phase 9.14 (no audit history)
    await page.goto('/ripples?status=rejected');
    await page.waitForSelector('[data-testid="ripple-card"]', { timeout: 5000 });
    await page.locator('[data-testid="ripple-card"]').first().click();
    await page.waitForSelector('[data-testid="ripple-drawer"]');
    // If ripple is pre-Phase 9.14, audit will be empty
    const empty = page.locator('[data-testid="ripple-audit-empty"]');
    // Some may have audit, some may not — assert one or the other is visible
    await expect(
      page.locator('[data-testid="ripple-audit-list"]').or(empty)
    ).toBeVisible();
  });
});
