// Visual audit capture — opt-in screenshots + layout metrics for AI-assisted UI review.
// Run: LINGWEN_E2E_LIVE=1 pnpm e2e:visual-capture
// Output: tests/visual-audit/output/{pageId}.png + .json + manifest.json
import { test } from '@playwright/test';
import {
  capturePageAudit,
  writeAuditManifest,
} from './helpers/capture-ui-audit.js';
import { LIVE_E2E_ENABLED } from '../e2e-smoke/helpers/live-backend.js';
import { prepareCreatorDeskForAudit } from './helpers/capture-ui-audit.js';

/** @type {import('./helpers/capture-ui-audit.js').VisualAuditEntry[]} */
const captured = [];

function skipUnlessLive(testInstance) {
  testInstance.skip(!LIVE_E2E_ENABLED, 'set LINGWEN_E2E_LIVE=1 for visual capture (needs live API fixtures)');
}

test.describe('Visual UI capture (AI review)', () => {
  test.beforeAll(async () => {
    captured.length = 0;
  });

  test.afterAll(async () => {
    if (captured.length) writeAuditManifest(captured);
  });

  test('capture_ask', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/?nav=ask', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="ask-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    captured.push(await capturePageAudit(page, 'ask', { note: 'L1 聊聊' }));
  });

  test('capture_creator_write', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="creator-write-workbench"]').waitFor({ state: 'visible', timeout: 30_000 });
    await prepareCreatorDeskForAudit(page);
    captured.push(await capturePageAudit(page, 'creator-write', { note: '书桌 · 写作 Tab' }));
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('capture_creator_pulse', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=write&workspace=pulse', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="column-pulse"]').waitFor({ state: 'visible', timeout: 30_000 });
    await page.locator('.pulse-desk__scroll').waitFor({ state: 'visible', timeout: 15_000 });
    await prepareCreatorDeskForAudit(page);
    captured.push(await capturePageAudit(page, 'creator-pulse', { note: '书桌 · 脉络 Tab' }));
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('capture_library', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/?nav=library', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="library-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    captured.push(await capturePageAudit(page, 'library', { note: 'L1 书架' }));
  });

  test('capture_settings', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/?nav=settings', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="settings-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    captured.push(await capturePageAudit(page, 'settings', { note: 'L1 设置' }));
  });
});
