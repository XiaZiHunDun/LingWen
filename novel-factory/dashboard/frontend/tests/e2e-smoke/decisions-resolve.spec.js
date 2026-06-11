// Phase 9.65 F56: Playwright live-backend e2e — decisions resolve flow.
// Opt-in: LINGWEN_E2E_LIVE=1 pnpm e2e:live
import { test, expect } from '@playwright/test';
import {
  LIVE_E2E_ENABLED,
  clickNav,
  resetE2eDecision,
  runE2eSeed,
  skipUnlessLive,
} from './helpers/live-backend.js';

test.describe('Decisions resolve live e2e (Phase 9.65 F56)', () => {
  test.beforeAll(() => {
    if (!LIVE_E2E_ENABLED) return;
    runE2eSeed('ensure');
  });

  test('decisions_page_renders_title', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await clickNav(page, /决策/);
    await expect(page.getByTestId('page-title')).toHaveText('决策中心');
  });

  test('resolve_pending_decision_shows_readonly_state', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    resetE2eDecision();

    await page.goto('/', { waitUntil: 'domcontentloaded' });
    await clickNav(page, /决策/);
    await page.getByTestId('decision-card').waitFor({ timeout: 20_000 });
    await page.getByTestId('option-btn').first().click();
    // Pending tab clears after resolve (WS authority); resolved card lives under 已完成.
    await page.getByRole('button', { name: /已完成/ }).click();
    const expandBtn = page.getByRole('button', { name: /展开/ });
    if (await expandBtn.isVisible()) {
      await expandBtn.click();
    }
    await expect(page.getByTestId('readonly-hint')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('readonly-hint')).toContainText('已解决');
  });
});
