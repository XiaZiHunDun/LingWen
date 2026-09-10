// Phase 9.48 F37: Playwright opt-in smoke — app shell loads in real browser.
// Primary gate remains vitest; this spec runs via workflow_dispatch or PR label e2e-smoke.
import { test, expect } from '@playwright/test';

test.describe('Dashboard app root smoke (Phase 9.48 F37)', () => {
  test('loads_app_root_and_sidebar_nav', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('app-root')).toBeVisible();
    await expect(page.getByTestId('sidebar-product-name')).toHaveText('灵文');
    await expect(page.getByRole('link', { name: '聊聊' })).toBeVisible();
    await expect(page.getByRole('link', { name: '书桌' })).toBeVisible();
    await expect(page.getByRole('link', { name: '书架' })).toBeVisible();
    await expect(page.getByRole('link', { name: '工具箱' })).toBeVisible();
    await expect(page.getByRole('link', { name: '设置' })).toBeVisible();
    // 伴侣壳：默认聊聊（AskPageTabs）或带 resume 时书桌（L1 页名）
    await expect(
      page.getByTestId('ask-page').or(page.getByTestId('header-l1-page-name')),
    ).toBeVisible({ timeout: 15_000 });
  });
});
