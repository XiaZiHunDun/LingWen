// Phase 9.65 F56: Playwright live-backend e2e — ripple audit drawer flow.
// Opt-in: LINGWEN_E2E_LIVE=1 pnpm e2e:live
import { test, expect } from '@playwright/test';
import {
  LIVE_E2E_ENABLED,
  gotoInbox,
  openFirstRippleDrawer,
  resetRipple,
  restoreInboxFixture,
  skipUnlessLive,
  waitForRippleListReady,
} from './helpers/live-backend.js';

const PENDING_ID = 'rip-pending-1';

test.describe('Ripples audit live e2e (Phase 9.65 F56)', () => {
  test.beforeAll(() => {
    if (!LIVE_E2E_ENABLED) return;
    restoreInboxFixture();
  });

  test('drawer_open_shows_audit_timeline_or_empty', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await gotoInbox(page, 'ripples');
    await openFirstRippleDrawer(page);
    await expect(
      page.getByTestId('ripple-audit-list').or(page.getByTestId('ripple-audit-empty')),
    ).toBeVisible();
  });

  test('apply_then_rollback_updates_audit_timeline', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    restoreInboxFixture();
    resetRipple(PENDING_ID, 'pending');
    page.on('dialog', (dialog) => dialog.accept('e2e rollback reason'));

    await gotoInbox(page, 'ripples');
    await openFirstRippleDrawer(page);

    await page.getByTestId('ripple-drawer-apply').click();
    await expect(page.getByTestId('apply-confirm-modal')).toBeVisible();
    await page.getByTestId('apply-confirm-apply').click();
    await expect(page.getByTestId('ripple-drawer')).toBeHidden({ timeout: 15_000 });

    await openFirstRippleDrawer(page);
    await page.getByTestId('ripple-rollback-btn').click();
    await expect(page.getByTestId('ripple-drawer')).toBeHidden({ timeout: 15_000 });

    await openFirstRippleDrawer(page);
    await expect(page.getByTestId('ripple-audit-list')).toContainText('rolled_back');
  });

  test('rejected_ripple_shows_audit_section', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await gotoInbox(page, 'ripples');
    await waitForRippleListReady(page);
    const rejectedCard = page
      .getByTestId('ripple-card')
      .filter({ has: page.getByTestId('ripple-status').filter({ hasText: 'rejected' }) })
      .first();
    const detailResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes('/api/cvg/ripples/') &&
        resp.request().method() === 'GET' &&
        resp.status() === 200,
      { timeout: 20_000 },
    );
    await rejectedCard.click();
    await detailResponse;
    await expect(page.getByTestId('ripple-drawer')).toBeVisible({ timeout: 15_000 });
    await expect(
      page.getByTestId('ripple-audit-list').or(page.getByTestId('ripple-audit-empty')),
    ).toBeVisible();
  });
});
