// 1280×720 layout metrics gate — clippedBelowFold should be empty on L1 primary surfaces.
import { test, expect } from '@playwright/test';
import { LIVE_E2E_ENABLED, clearInboxPending } from '../e2e-smoke/helpers/live-backend.js';
import {
  collectUiMetrics,
  findCriticalClipping,
  prepareCreatorDeskForAudit,
  waitForPaintSettle,
} from './helpers/capture-ui-audit.js';

const VIEWPORT = { width: 1280, height: 720 };

function skipUnlessLive(testInstance) {
  testInstance.skip(!LIVE_E2E_ENABLED, 'set LINGWEN_E2E_LIVE=1 for ui-metrics audit');
}

async function assertNoCriticalClip(page, pageLabel) {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await waitForPaintSettle(page);
  const metrics = await collectUiMetrics(page);
  const bad = findCriticalClipping(metrics);
  expect(
    bad,
    `${pageLabel}: clipped below fold without scroll parent:\n${bad.map((b) => `  ${b.testId} +${b.overflowBelow}px`).join('\n')}`,
  ).toEqual([]);
}

test.describe('UI metrics audit (1280×720)', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize(VIEWPORT);
  });

  test('ui_metrics_ask_no_clip', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.goto('/?nav=ask', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="ask-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await assertNoCriticalClip(page, 'ask');
  });

  test('ui_metrics_library_no_clip', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.goto('/?nav=library', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="library-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await assertNoCriticalClip(page, 'library');
  });

  test('ui_metrics_more_no_clip', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.goto('/?nav=more', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="more-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await assertNoCriticalClip(page, 'more');
  });

  test('ui_metrics_write_no_clip', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="creator-write-workbench"]').waitFor({ state: 'visible', timeout: 30_000 });
    await prepareCreatorDeskForAudit(page);
    await assertNoCriticalClip(page, 'creator-write');
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('ui_metrics_produce_no_clip', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
    await page.goto('/?nav=produce', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="produce-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await assertNoCriticalClip(page, 'produce');
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('ui_metrics_inbox_no_clip', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.goto('/?nav=inbox&tab=decisions', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="inbox-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await assertNoCriticalClip(page, 'inbox');
  });

  test('ui_metrics_settings_no_clip', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.goto('/?nav=settings', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="settings-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await assertNoCriticalClip(page, 'settings');
  });

  test('ui_metrics_today_no_clip', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    clearInboxPending();
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=today', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="today-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await page.getByTestId('today-loading').waitFor({ state: 'hidden', timeout: 45_000 });
    await assertNoCriticalClip(page, 'today');
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('ui_metrics_insight_no_clip', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=insight', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="insight-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await assertNoCriticalClip(page, 'insight');
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('ui_metrics_cascade_runs_no_clip', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
    await page.goto('/?nav=cascade-runs', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="cascade-runs-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await assertNoCriticalClip(page, 'cascade-runs');
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });
});
