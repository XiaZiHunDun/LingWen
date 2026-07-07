import { test, expect } from '@playwright/test';
import { clickNav, skipUnlessLive } from './helpers/live-backend.js';
import { COMPANION_SLUG, restoreCreatorProject } from './helpers/companion-project.js';

test.describe('More hub (live)', () => {
  test.beforeEach(async ({ request }) => {
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });
  });

  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('more_hub_today_inbox_insight_reachable', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);

    await page.goto('/?nav=more', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('more-page')).toBeVisible({ timeout: 30_000 });

    await page.getByTestId('more-link-today').click();
    await expect(page.getByTestId('today-page')).toBeVisible({ timeout: 30_000 });

    await clickNav(page, '工具箱');
    await expect(page.getByTestId('more-page')).toBeVisible({ timeout: 15_000 });

    await page.getByTestId('more-link-inbox').click();
    await expect(page.getByTestId('inbox-page')).toBeVisible({ timeout: 30_000 });

    await clickNav(page, '工具箱');
    await page.getByTestId('more-link-insight').click();
    await expect(page.getByTestId('insight-page')).toBeVisible({ timeout: 30_000 });
  });

  test('more_nav_from_sidebar', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);

    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await clickNav(page, '工具箱');
    await expect(page.getByTestId('more-page')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('more-link-inbox')).toBeVisible();
  });
});
