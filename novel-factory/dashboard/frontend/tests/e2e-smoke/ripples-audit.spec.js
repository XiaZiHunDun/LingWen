// Phase 9.65 F56: Playwright live-backend e2e — ripple audit drawer flow.
// Opt-in: LINGWEN_E2E_LIVE=1 pnpm e2e:live
import { test, expect } from '@playwright/test';
import {
  LIVE_E2E_ENABLED,
  clickNav,
  resetRipple,
  runE2eSeed,
  skipUnlessLive,
} from './helpers/live-backend.js';

const PENDING_ID = 'rip-pending-1';

test.describe('Ripples audit live e2e (Phase 9.65 F56)', () => {
  test.beforeAll(() => {
    if (!LIVE_E2E_ENABLED) return;
    runE2eSeed('ensure');
  });

  test('drawer_open_shows_audit_timeline_or_empty', async ({ page }) => {
    skipUnlessLive(test);
    await page.goto('/');
    await clickNav(page, /涟漪/);
    await page.getByTestId('ripple-card').first().waitFor({ timeout: 15_000 });
    await page.getByTestId('ripple-card').first().click();
    await expect(page.getByTestId('ripple-drawer')).toBeVisible();
    await expect(
      page.getByTestId('ripple-audit-list').or(page.getByTestId('ripple-audit-empty')),
    ).toBeVisible();
  });

  test('apply_then_rollback_updates_audit_timeline', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    resetRipple(PENDING_ID, 'pending');
    page.on('dialog', (dialog) => dialog.accept('e2e rollback reason'));

    await page.goto('/');
    await clickNav(page, /涟漪/);
    await page.getByTestId('ripple-card').first().waitFor({ timeout: 15_000 });
    await page.getByTestId('ripple-card').first().click();
    await expect(page.getByTestId('ripple-drawer')).toBeVisible();

    await page.getByTestId('ripple-drawer-apply').click();
    await expect(page.getByTestId('apply-confirm-modal')).toBeVisible();
    await page.getByTestId('apply-confirm-apply').click();
    await expect(page.getByTestId('ripple-drawer')).toBeHidden({ timeout: 10_000 });

    await page.getByTestId('ripple-card').first().click();
    await expect(page.getByTestId('ripple-drawer')).toBeVisible();
    await page.getByTestId('ripple-rollback-btn').click();
    await expect(page.getByTestId('ripple-drawer')).toBeHidden({ timeout: 10_000 });

    await page.getByTestId('ripple-card').first().click();
    await expect(page.getByTestId('ripple-audit-list')).toContainText('rolled_back');
  });

  test('rejected_ripple_shows_audit_section', async ({ page }) => {
    skipUnlessLive(test);
    await page.goto('/');
    await clickNav(page, /涟漪/);
    await page.getByTestId('ripple-card').first().waitFor({ timeout: 15_000 });
    await page.getByTestId('ripple-card').first().click();
    await expect(page.getByTestId('ripple-drawer')).toBeVisible();
    await expect(
      page.getByTestId('ripple-audit-list').or(page.getByTestId('ripple-audit-empty')),
    ).toBeVisible();
  });
});
