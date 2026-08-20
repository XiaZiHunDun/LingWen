// Phase 66: Error states e2e integration tests.
// Asserts that the dashboard surfaces failures (offline API, 404, retry)
// rather than rendering an infinite loading skeleton.
import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import { COMPANION_SLUG, restoreCreatorProject } from './helpers/companion-project.js';

test.describe('Error states (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('network_failure_surfaces_offline_banner', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.route('**/api/**', (route) => route.abort('failed'));
    await page.goto('/?nav=ask', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('api-offline-banner')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('api-offline-retry-btn')).toBeVisible();
  });

  test('dashboard_shell_remains_when_api_returns_404', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.route('**/api/studio/summary', (route) =>
      route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'not found' }),
      }),
    );
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('app-root')).toBeVisible();
    await expect(page.getByTestId('sidebar-product-name')).toBeVisible();
  });

  test('api_offline_retry_button_is_present_and_clickable', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.route('**/api/**', (route) => route.abort('failed'));
    await page.goto('/?nav=ask', { waitUntil: 'domcontentloaded' });
    const retry = page.getByTestId('api-offline-retry-btn');
    await expect(retry).toBeVisible({ timeout: 30_000 });
    await expect(retry).toBeEnabled();
  });
});
