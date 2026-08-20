// Phase 66: URL deep-linking e2e integration tests.
// Verifies that direct navigation lands on the expected surface and that
// unknown routes fall back without crashing the app shell.
import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import { COMPANION_SLUG, restoreCreatorProject } from './helpers/companion-project.js';

test.describe('URL deep-linking (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('direct_url_to_write_loads_creator_workbench', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.goto('/?nav=write&chapter=1', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('app-root')).toBeVisible();
    await expect(page.getByTestId('creator-write-workbench')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('header-l1-page-name')).toHaveText('书桌');
  });

  test('url_query_params_preserve_nav_selection', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.goto('/?nav=write&chapter=2', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('creator-write-workbench')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('chapter-row-2')).toHaveClass(/chapter-row--selected/);
  });

  test('invalid_nav_param_falls_back_to_known_surface', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.goto('/?nav=does-not-exist', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('app-root')).toBeVisible();
    // App shell must stay interactive even with an unknown nav value.
    await expect(
      page.getByTestId('ask-page')
        .or(page.getByTestId('header-l1-page-name'))
        .or(page.getByTestId('more-page'))
        .or(page.getByTestId('creator-write-workbench')),
    ).toBeVisible({ timeout: 30_000 });
  });
});