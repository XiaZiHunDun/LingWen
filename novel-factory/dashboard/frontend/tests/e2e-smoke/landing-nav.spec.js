import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import {
  COMPANION_SLUG,
  CREATOR_SLUG,
  clearWriteResume,
  restoreCreatorProject,
  setWriteResume,
} from './helpers/companion-project.js';

test.describe('Default landing nav (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('landing_defaults_to_ask_without_resume', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await clearWriteResume(page);
    await request.put('/api/studio/active', { data: { slug: CREATOR_SLUG } });

    await page.route('**/api/studio/summary', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ slug: 'fresh-book', name: 'Fresh', chapter_count: 0 }),
      });
    });
    await page.route('**/api/creator/overview', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ slug: 'fresh-book', name: 'Fresh', chapters_written: 0 }),
      });
    });

    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('ask-page')).toBeVisible({ timeout: 30_000 });
  });

  test('landing_defaults_to_write_with_resume', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await setWriteResume(page, COMPANION_SLUG, 1);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('creator-write-workbench')).toBeVisible({ timeout: 30_000 });
  });

  test('deep_link_nav_write_chapter', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.goto('/?nav=write&chapter=1', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('creator-write-workbench')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('chapter-row-1')).toHaveClass(/chapter-row--selected/);
  });

  test('landing_defaults_to_inbox_for_reviewer', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);

    await page.goto('/?role=reviewer', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('inbox-page')).toBeVisible({ timeout: 30_000 });
  });
});
