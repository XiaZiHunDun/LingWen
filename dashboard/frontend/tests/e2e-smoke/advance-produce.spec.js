import { test, expect } from '@playwright/test';
import { clickNav, skipUnlessLive } from './helpers/live-backend.js';
import { CREATOR_SLUG, COMPANION_SLUG, restoreCreatorProject } from './helpers/companion-project.js';

test.describe('Advance produce hub (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request, CREATOR_SLUG);
  });

  test('advance_more_produce_link_opens_produce_page', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: CREATOR_SLUG } });

    await page.goto('/?nav=more', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('more-page')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('more-link-produce')).toBeVisible({ timeout: 15_000 });

    await page.getByTestId('more-link-produce').click();
    await expect(page.getByTestId('produce-page')).toBeVisible({ timeout: 30_000 });
  });

  test('advance_produce_nav_from_write_sidebar', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: CREATOR_SLUG } });

    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await clickNav(page, '工具箱');
    await page.getByTestId('more-link-produce').click();
    await expect(page.getByTestId('produce-page')).toBeVisible({ timeout: 30_000 });

    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });
  });
});
