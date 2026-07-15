import { test, expect } from '@playwright/test';
import { clickNav, skipUnlessLive } from './helpers/live-backend.js';
import { COMPANION_SLUG, CREATOR_SLUG, restoreCreatorProject } from './helpers/companion-project.js';

test.describe('Library flow (live)', () => {
  test('library_switch_book_then_write_visible', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: CREATOR_SLUG } });

    await page.goto('/?nav=library', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('library-page')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('library-grid')).toBeVisible({ timeout: 30_000 });

    await page.getByTestId(`library-card-${COMPANION_SLUG}`).click();
    await expect(page.getByTestId('creator-write-workbench')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('chapter-row-1')).toBeVisible({ timeout: 15_000 });

    await restoreCreatorProject(request);
  });

  test('library_nav_from_sidebar', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('creator-write-workbench')).toBeVisible({ timeout: 30_000 });

    await clickNav(page, '书架');
    await expect(page.getByTestId('library-page')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId(`library-card-${COMPANION_SLUG}`)).toBeVisible();

    await restoreCreatorProject(request);
  });
});
