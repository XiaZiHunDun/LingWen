import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import {
  CREATOR_SLUG,
  clickStable,
  openPulseDrawer,
  restoreCreatorProject,
} from './helpers/companion-project.js';

test.describe('Advance batch flow (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request, CREATOR_SLUG);
  });

  test('advance_batch_panel_preflight', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: CREATOR_SLUG } });

    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await openPulseDrawer(page);
    await expect(page.getByTestId('advance-batch-panel')).toBeVisible({ timeout: 30_000 });

    await clickStable(page.getByTestId('advance-preflight-btn'));
    await page.waitForResponse(
      (resp) => resp.url().includes('/api/studio/production/preflight') && resp.request().method() === 'POST',
      { timeout: 30_000 },
    );
    await expect(page.locator('.advance-batch-panel code, .batch-error').first()).toBeVisible({
      timeout: 15_000,
    });
  });

  test('advance_chapter_task_cards_reflect_running_batch', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: CREATOR_SLUG } });

    await page.route('**/api/studio/production/jobs/active', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'e2e-batch-mock',
          status: 'running',
          start_chapter: 1,
          end_chapter: 3,
          current_chapter: 2,
          message: 'E2E mock batch',
        }),
      });
    });

    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await openPulseDrawer(page);
    await expect(page.getByTestId('chapter-task-cards')).toBeVisible({ timeout: 30_000 });

    const summary = page.locator('[data-testid="chapter-task-cards"] summary');
    const isOpen = await summary.evaluate((el) => /** @type {HTMLDetailsElement} */ (el.parentElement).open);
    if (!isOpen) {
      await summary.click();
    }

    await expect(page.getByTestId('chapter-task-2')).toContainText('生成中', { timeout: 15_000 });
    await expect(page.getByTestId('chapter-task-1')).toContainText(/已完成|已生成/, { timeout: 15_000 });
    await expect(page.getByTestId('chapter-task-3')).toContainText('排队', { timeout: 15_000 });
  });

  test('advance_chapter_task_confirm_navigates_inbox', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: CREATOR_SLUG } });

    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await openPulseDrawer(page);
    await expect(page.getByTestId('chapter-task-cards')).toBeVisible({ timeout: 30_000 });

    const summary = page.locator('[data-testid="chapter-task-cards"] summary');
    const isOpen = await summary.evaluate((el) => /** @type {HTMLDetailsElement} */ (el.parentElement).open);
    if (!isOpen) {
      await summary.click();
    }

    const confirmBtn = page.getByTestId('chapter-task-confirm-1');
    await expect(confirmBtn).toBeEnabled({ timeout: 15_000 });
    await confirmBtn.click();
    await expect(page.getByTestId('inbox-page')).toBeVisible({ timeout: 30_000 });
    await expect(page).toHaveURL(/nav=inbox/);
  });
});
