// Phase 9.65 F56: Playwright live-backend e2e — decisions resolve flow.
// Opt-in: LINGWEN_E2E_LIVE=1 pnpm e2e:live
import { test, expect } from '@playwright/test';
import {
  LIVE_E2E_ENABLED,
  clickNav,
  resetE2eDecision,
  restoreInboxFixture,
  runE2eSeed,
  skipUnlessLive,
  waitForPendingDecisionCard,
} from './helpers/live-backend.js';

test.describe('Decisions resolve live e2e (Phase 9.65 F56)', () => {
  test.beforeAll(() => {
    if (!LIVE_E2E_ENABLED) return;
    restoreInboxFixture();
  });

  test('decisions_page_renders_title', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.goto('/?nav=inbox&tab=decisions', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('inbox-page')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('header-l1-page-name')).toHaveText('待办');
    await expect(page.getByTestId('inbox-tabs')).toBeVisible();
    await expect(
      page.getByTestId('decision-card')
        .or(page.locator('.decisions-page .empty-state')),
    ).toBeVisible({ timeout: 30_000 });
  });

  test('resolve_pending_decision_shows_readonly_state', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    resetE2eDecision();

    await page.goto('/?nav=inbox&tab=decisions', { waitUntil: 'domcontentloaded' });
    await waitForPendingDecisionCard(page);
    const resolveResponse = page.waitForResponse(
      (resp) =>
        resp.request().method() === 'POST'
        && resp.url().includes('/api/decisions/')
        && resp.url().includes('/resolve')
        && resp.status() === 200,
      { timeout: 30_000 },
    );
    await page.getByTestId('option-btn').first().click();
    await resolveResponse;
    // Pending tab clears after resolve (WS authority); resolved card lives under 已完成.
    await page.getByRole('button', { name: /已完成/ }).click();
    const expandBtn = page.getByRole('button', { name: /展开/ });
    await expandBtn.waitFor({ state: 'visible', timeout: 15_000 });
    await expandBtn.click();
    await expect(page.getByTestId('readonly-hint')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('readonly-hint')).toContainText('已解决');
  });
});
