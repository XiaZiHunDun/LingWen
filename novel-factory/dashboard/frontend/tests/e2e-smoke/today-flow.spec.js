import { test, expect } from '@playwright/test';
import { clearInboxPending, restoreInboxFixture, skipUnlessLive } from './helpers/live-backend.js';
import { COMPANION_SLUG, restoreCreatorProject } from './helpers/companion-project.js';

/** Primary CTA labels vary by fixture state (micro-task, onboarding, inbox). */
const TODAY_FALLBACK_CTA = /继续创作|处理|审阅|向导|Batch|查看|再写/;

test.describe('Today flow (live)', () => {
  test.beforeEach(async ({ request }) => {
    clearInboxPending();
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });
  });

  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('today_page_primary_or_health_visible', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);

    await page.goto('/?nav=today', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('today-page')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('today-loading')).toBeHidden({ timeout: 45_000 });

    await expect(page.getByTestId('today-primary-action')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('today-health-section')).toBeVisible();
  });

  test('today_micro_task_cta_navigates_to_write_chapter', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);

    await page.goto('/?nav=today', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('today-loading')).toBeHidden({ timeout: 45_000 });

    const cta = page.getByTestId('today-primary-cta');
    await expect(cta).toBeVisible({ timeout: 15_000 });
    const label = (await cta.textContent()) || '';
    if (label.includes('再写')) {
      await expect(page.getByTestId('today-micro-task-stat')).toBeVisible();
      await cta.click();
      await expect(page.getByTestId('creator-write-workbench')).toBeVisible({ timeout: 30_000 });
      await expect(page).toHaveURL(/chapter=\d+/);
    } else {
      expect(label).toMatch(TODAY_FALLBACK_CTA);
    }
  });

  test('today_prioritizes_pending_decisions_over_micro_task', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);

    restoreInboxFixture();
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.goto('/?nav=today', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('today-loading')).toBeHidden({ timeout: 45_000 });

    const cta = page.getByTestId('today-primary-cta');
    await expect(cta).toBeVisible({ timeout: 15_000 });
    await expect(cta).toContainText(/待决策/);
    await expect(page.getByTestId('today-secondary-ripples')).toBeVisible();
    await cta.click();
    await expect(page.getByTestId('inbox-page')).toBeVisible({ timeout: 30_000 });
    await expect(page).toHaveURL(/nav=inbox/);
  });
});
