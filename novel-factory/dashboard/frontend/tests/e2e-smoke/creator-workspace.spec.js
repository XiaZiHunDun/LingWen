// Creator workspace live e2e (Phase creator v1.4)
import { test, expect } from '@playwright/test';
import { LIVE_E2E_ENABLED, clickNav, skipUnlessLive } from './helpers/live-backend.js';

test.describe('Creator workspace live e2e', () => {
  test('creator_nav_shows_three_columns', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.goto('/?nav=creator', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('page-title')).toHaveText('创作伴侣');
    await expect(page.getByTestId('creator-grid')).toBeVisible();
    await expect(page.getByTestId('column-write')).toBeVisible();
    await expect(page.getByTestId('column-pulse')).toBeVisible();
    await expect(page.getByTestId('column-settings')).toBeVisible();
  });

  test('creator_volume_plan_panel_visible', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.goto('/?nav=creator', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('volume-plan-panel')).toBeVisible();
    await expect(page.getByTestId('pillars-textarea')).toBeVisible();
  });
});
