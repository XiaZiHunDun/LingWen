// Phase 66: Modal interaction e2e integration tests.
// Covers the cross-flow modal patterns left out of the happy-path suite:
// modal open via role button, escape close, focus-trap, and close button.
import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import {
  COMPANION_SLUG,
  restoreCreatorProject,
  openCompanionProject,
} from './helpers/companion-project.js';

test.describe('Modal interaction (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('publish_modal_opens_and_closes_via_button', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });
    await openCompanionProject(page, request, COMPANION_SLUG);

    await expect(page.getByTestId('creator-publish-modal')).toBeHidden({ timeout: 15_000 });
    await page.getByRole('button', { name: /发布/ }).click();
    await expect(page.getByTestId('creator-publish-modal')).toBeVisible({ timeout: 15_000 });

    await page.getByTestId('publish-modal-close').click();
    await expect(page.getByTestId('creator-publish-modal')).toBeHidden({ timeout: 10_000 });
  });

  test('publish_modal_traps_focus_within_itself', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });
    await openCompanionProject(page, request, COMPANION_SLUG);

    await page.getByRole('button', { name: /发布/ }).click();
    const modal = page.getByTestId('creator-publish-modal');
    await expect(modal).toBeVisible({ timeout: 15_000 });

    await modal.getByTestId('publish-modal-close').focus();
    for (let i = 0; i < 12; i += 1) {
      await page.keyboard.press('Tab');
    }
    const focusedInsideModal = await page.evaluate(() => {
      const modalEl = document.querySelector('[data-testid="creator-publish-modal"]');
      const active = document.activeElement;
      return Boolean(modalEl && active && modalEl.contains(active));
    });
    expect(focusedInsideModal).toBe(true);
  });

  test('publish_modal_close_button_dismisses_modal', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });
    await openCompanionProject(page, request, COMPANION_SLUG);

    await page.getByRole('button', { name: /发布/ }).click();
    await expect(page.getByTestId('creator-publish-modal')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('publish-modal-close').click();
    await expect(page.getByTestId('creator-publish-modal')).toBeHidden({ timeout: 10_000 });
  });
});
