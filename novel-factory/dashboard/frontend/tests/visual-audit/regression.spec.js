// Pixel-level visual regression (opt-in baseline update: pnpm e2e:visual-update)
import { test, expect } from '@playwright/test';
import { LIVE_E2E_ENABLED } from '../e2e-smoke/helpers/live-backend.js';
import { prepareCreatorDeskForAudit } from './helpers/capture-ui-audit.js';

function skipUnlessLive(testInstance) {
  testInstance.skip(!LIVE_E2E_ENABLED, 'set LINGWEN_E2E_LIVE=1 for visual regression');
}

test.describe('Visual regression baselines', () => {
  test('creator_write_viewport', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="creator-write-workbench"]').waitFor({ state: 'visible', timeout: 30_000 });
    await prepareCreatorDeskForAudit(page);
    await page.waitForTimeout(400);
    await expect(page).toHaveScreenshot('creator-write-1280x720.png', {
      maxDiffPixelRatio: 0.02,
      animations: 'disabled',
    });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('creator_pulse_viewport', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=write&workspace=pulse', { waitUntil: 'domcontentloaded' });
    await page.locator('.pulse-desk__scroll').waitFor({ state: 'visible', timeout: 30_000 });
    await prepareCreatorDeskForAudit(page);
    await page.waitForTimeout(400);
    await expect(page).toHaveScreenshot('creator-pulse-1280x720.png', {
      maxDiffPixelRatio: 0.02,
      animations: 'disabled',
    });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });
});
