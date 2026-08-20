// Phase 66: Export flow e2e integration tests.
// Verifies the CreatorExportModal opens (via the publish wizard trigger),
// renders its format options, and accepts author metadata.
import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import {
  COMPANION_SLUG,
  restoreCreatorProject,
  openCompanionProject,
} from './helpers/companion-project.js';

test.describe('Export flow (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('export_modal_opens_via_publish_wizard', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });
    await openCompanionProject(page, request, COMPANION_SLUG);

    await expect(page.getByTestId('creator-export-modal')).toBeHidden({ timeout: 15_000 });
    await page.getByRole('button', { name: /发布/ }).click();
    await expect(page.getByTestId('creator-publish-modal')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('publish-open-export').click();
    await expect(page.getByTestId('creator-export-modal')).toBeVisible({ timeout: 15_000 });
  });

  test('export_modal_renders_format_options', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });
    await openCompanionProject(page, request, COMPANION_SLUG);

    await page.getByRole('button', { name: /发布/ }).click();
    await expect(page.getByTestId('creator-publish-modal')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('publish-open-export').click();
    await expect(page.getByTestId('creator-export-modal')).toBeVisible({ timeout: 15_000 });

    const modes = page.locator('[data-testid^="export-mode-"]');
    expect(await modes.count()).toBeGreaterThanOrEqual(2);
  });

  test('export_modal_accepts_author_metadata', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });
    await openCompanionProject(page, request, COMPANION_SLUG);

    await page.getByRole('button', { name: /发布/ }).click();
    await expect(page.getByTestId('creator-publish-modal')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('publish-open-export').click();
    await expect(page.getByTestId('creator-export-modal')).toBeVisible({ timeout: 15_000 });

    await page.getByTestId('export-author').fill('Phase 66 测试作者');
    await expect(page.getByTestId('export-author')).toHaveValue('Phase 66 测试作者');
  });
});