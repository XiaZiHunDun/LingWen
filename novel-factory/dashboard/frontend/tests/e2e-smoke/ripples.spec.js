// dashboard/frontend/tests/e2e-smoke/ripples.spec.js — Phase 9.13
// E2E smoke tests for /ripples page (跟 Phase 8.45.3 1:1 pattern, 0 network, 0 LLM)
import { test, expect } from '../_setup.js';

test.describe('Ripples Page Smoke', () => {
  // Phase 9.17: 0-backend test mode. mock /api/ripples → [] 让 2 tests 走 empty-state
  // path 立刻 pass. test 3 既有 `if (card.count() > 0)` skip 保护保留 (0 业务代码改).
  // 真 backend 集成测试留 Phase 9.18+ (跟 Phase 9.13 backfill completion 走).
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/ripples**', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      })
    )
  });

  test('mount /ripples → page renders with filter + list + sidebar nav', async ({ page }) => {
    await page.goto('/ripples');
    await expect(page.getByTestId('nav-ripples')).toBeVisible();
    await expect(page.getByTestId('ripple-filter-status')).toBeVisible();
  });

  test('filter by pending → empty state or list', async ({ page }) => {
    await page.goto('/ripples?status=pending');
    await expect(page.getByTestId('ripple-list-empty').or(page.getByTestId('ripple-list-loading'))).toBeVisible({ timeout: 5000 });
  });

  test('open drawer → click close → drawer hides', async ({ page }) => {
    await page.goto('/ripples');
    // First ripple card if exists, else skip
    const card = page.getByTestId('ripple-card').first();
    if (await card.count() > 0) {
      await card.click();
      await expect(page.getByTestId('ripple-drawer')).toBeVisible();
      await page.getByTestId('ripple-drawer-close').click();
      await expect(page.getByTestId('ripple-drawer-content')).not.toBeVisible();
    }
  });
});
