import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import { CREATOR_SLUG, STUDIO_SLUG, restoreCreatorProject } from './helpers/companion-project.js';

test.describe('Studio mode (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request, CREATOR_SLUG);
  });

  test('studio_produce_console_and_chapters_tabs', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: STUDIO_SLUG } });

    await page.goto('/?nav=produce', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('produce-page')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('produce-tabs-studio')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('production-console')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('preflight-btn')).toBeVisible();

    await page.getByTestId('produce-tabs-chapters').click();
    await expect(page.getByTestId('chapter-production-status')).toBeVisible({ timeout: 30_000 });
  });

  test('studio_sidebar_hides_write_nav', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: STUDIO_SLUG } });

    await page.goto('/?nav=more', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('more-page')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('nav-write')).toBeHidden();
    await expect(page.getByTestId('more-link-produce')).toBeVisible();
  });
});
