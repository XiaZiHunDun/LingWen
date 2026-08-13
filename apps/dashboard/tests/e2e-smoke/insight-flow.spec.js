import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import { COMPANION_SLUG, restoreCreatorProject } from './helpers/companion-project.js';

test.describe('Insight flow (live)', () => {
  test.beforeEach(async ({ request }) => {
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });
  });

  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('insight_analytics_tab_shows_production_kpi', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);

    await page.goto('/?nav=insight', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('insight-page')).toBeVisible({ timeout: 30_000 });

    await page.getByTestId('insight-tabs-analytics').click();
    await expect(
      page.getByTestId('production-kpi').or(page.getByTestId('analytics-production-summary')),
    ).toBeVisible({ timeout: 30_000 });
  });
});
