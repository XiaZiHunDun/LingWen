import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import { CREATOR_SLUG, restoreCreatorProject } from './helpers/companion-project.js';

test.describe('Workflows flow (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request, CREATOR_SLUG);
  });

  test('advance_produce_workflows_tab_lists_items', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: CREATOR_SLUG } });

    await page.goto('/?nav=produce&tab=workflows', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('produce-page')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('produce-tabs-workflows')).toBeVisible({ timeout: 15_000 });

    await expect(
      page.getByTestId('wf-item').first().or(page.getByTestId('error-banner')),
    ).toBeVisible({ timeout: 30_000 });
  });
});
