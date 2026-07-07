import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import { COMPANION_SLUG, restoreCreatorProject } from './helpers/companion-project.js';

test.describe('Settings flow (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request, COMPANION_SLUG);
  });

  test('settings_page_basic_panel_visible', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.goto('/?nav=settings', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('settings-page')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('settings-basic-panel')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('display-settings-panel')).toBeVisible();
  });
});
