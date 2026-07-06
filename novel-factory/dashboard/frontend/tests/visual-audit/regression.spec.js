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

  test('ask_viewport', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/?nav=ask', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="ask-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await page.waitForTimeout(400);
    await expect(page).toHaveScreenshot('ask-1280x720.png', {
      maxDiffPixelRatio: 0.02,
      animations: 'disabled',
    });
  });

  test('library_viewport', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/?nav=library', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="library-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await page.locator('[data-testid="library-grid"]').waitFor({ state: 'visible', timeout: 30_000 });
    await page.waitForTimeout(400);
    await expect(page).toHaveScreenshot('library-1280x720.png', {
      maxDiffPixelRatio: 0.02,
      animations: 'disabled',
    });
  });

  test('settings_viewport', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/?nav=settings', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="settings-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await page.waitForTimeout(400);
    await expect(page).toHaveScreenshot('settings-1280x720.png', {
      maxDiffPixelRatio: 0.02,
      animations: 'disabled',
    });
  });
});
