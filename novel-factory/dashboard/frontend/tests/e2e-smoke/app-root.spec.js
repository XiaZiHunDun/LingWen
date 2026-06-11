// Phase 9.48 F37: Playwright opt-in smoke — app shell loads in real browser.
// Primary gate remains vitest; this spec runs via workflow_dispatch or PR label e2e-smoke.
import { test, expect } from '@playwright/test';

test.describe('Dashboard app root smoke (Phase 9.48 F37)', () => {
  test('loads_app_root_and_sidebar_nav', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('app-root')).toBeVisible();
    await expect(page.getByText('追读力 Dashboard')).toBeVisible();
    await expect(page.getByRole('link', { name: /总览/ })).toBeVisible();
    await expect(page.getByRole('link', { name: /涟漪/ })).toBeVisible();
    await expect(page.getByTestId('page-title')).toBeVisible();
  });
});
