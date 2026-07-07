// Pixel-level visual regression (opt-in baseline update: pnpm e2e:visual-update)
import { test, expect } from '@playwright/test';
import { LIVE_E2E_ENABLED } from '../e2e-smoke/helpers/live-backend.js';
import { prepareCreatorDeskForAudit, prepareCreatorDeskAdvancedOpen, openCreatorPulseDrawerForAudit, prepareChapterEntityPanelForAudit, prepareDirectorPathsPanelForAudit, waitForPaintSettle, visualShotOptions } from './helpers/capture-ui-audit.js';
import { mockDelayedAgentPlanStream } from '../e2e-smoke/helpers/mock-agent-stream.js';
import { openAdvancedTools, selectChapter } from '../e2e-smoke/helpers/companion-project.js';

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
    await waitForPaintSettle(page);
    await expect(page).toHaveScreenshot('creator-write-1280x720.png', visualShotOptions());
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
    await waitForPaintSettle(page);
    await expect(page).toHaveScreenshot('creator-pulse-1280x720.png', visualShotOptions());
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('ask_viewport', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/?nav=ask', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="ask-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await waitForPaintSettle(page);
    await expect(page).toHaveScreenshot('ask-1280x720.png', visualShotOptions());
  });

  test('library_viewport', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/?nav=library', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="library-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await page.locator('[data-testid="library-grid"]').waitFor({ state: 'visible', timeout: 30_000 });
    await waitForPaintSettle(page);
    await expect(page).toHaveScreenshot('library-1280x720.png', visualShotOptions());
  });

  test('settings_viewport', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/?nav=settings', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="settings-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await waitForPaintSettle(page);
    await expect(page).toHaveScreenshot('settings-1280x720.png', visualShotOptions());
  });

  test('creator_write_advanced_open_viewport', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="creator-write-workbench"]').waitFor({ state: 'visible', timeout: 30_000 });
    await page.locator('[data-testid="chapter-row-1"]').click();
    await prepareCreatorDeskAdvancedOpen(page);
    await waitForPaintSettle(page);
    await expect(page).toHaveScreenshot('creator-write-advanced-open-1280x720.png', visualShotOptions());
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('creator_desk_drawer_pulse_viewport', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="creator-write-workbench"]').waitFor({ state: 'visible', timeout: 30_000 });
    await openCreatorPulseDrawerForAudit(page);
    await expect(page).toHaveScreenshot('creator-desk-drawer-pulse-1280x720.png', visualShotOptions());
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('more_viewport', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/?nav=more', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="more-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await waitForPaintSettle(page);
    await expect(page).toHaveScreenshot('more-1280x720.png', visualShotOptions());
  });

  test('today_viewport', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/?nav=today', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="today-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await waitForPaintSettle(page);
    await expect(page).toHaveScreenshot('today-1280x720.png', visualShotOptions());
  });

  test('inbox_viewport', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/?nav=inbox&tab=decisions', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="inbox-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await waitForPaintSettle(page);
    await expect(page).toHaveScreenshot('inbox-1280x720.png', visualShotOptions());
  });

  test('write_light_validation_bar_component', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="creator-write-workbench"]').waitFor({ state: 'visible', timeout: 30_000 });
    await page.locator('[data-testid="chapter-row-1"]').click();
    await prepareCreatorDeskForAudit(page);
    const bar = page.locator('[data-testid="write-light-validation-bar"]');
    await bar.waitFor({ state: 'visible', timeout: 15_000 });
    await waitForPaintSettle(page);
    await expect(bar).toHaveScreenshot('write-light-validation-bar.png', visualShotOptions(0.03));
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('agent_stream_preview_component', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await mockDelayedAgentPlanStream(page, { chunkText: '视觉回归流式', chunkDelayMs: 2000 });

    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="creator-write-workbench"]').waitFor({ state: 'visible', timeout: 30_000 });
    await selectChapter(page);
    await prepareCreatorDeskAdvancedOpen(page);
    await page.getByTestId('write-agent-input').fill('视觉快照');

    const preview = page.locator('[data-testid="agent-stream-preview"]');
    await page.getByTestId('write-agent-send-btn').click();
    await preview.waitFor({ state: 'visible', timeout: 15_000 });
    await waitForPaintSettle(page);

    await expect(preview).toHaveScreenshot('agent-stream-preview.png', visualShotOptions(0.04));

    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('produce_viewport', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
    await page.goto('/?nav=produce', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="produce-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await waitForPaintSettle(page);
    await expect(page).toHaveScreenshot('produce-1280x720.png', visualShotOptions());
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('insight_viewport', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=insight', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="insight-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await page.getByTestId('insight-tabs-analytics').click();
    await page.getByTestId('production-kpi').or(page.getByTestId('analytics-production-summary')).waitFor({
      state: 'visible',
      timeout: 30_000,
    });
    await waitForPaintSettle(page);
    await expect(page).toHaveScreenshot('insight-1280x720.png', visualShotOptions());
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('cascade_runs_viewport', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
    await page.goto('/?nav=cascade-runs', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="cascade-runs-page"]').waitFor({ state: 'visible', timeout: 30_000 });
    await page.locator('[data-testid="cascade-runs-panel"]').waitFor({ state: 'visible', timeout: 30_000 });
    await waitForPaintSettle(page);
    await expect(page).toHaveScreenshot('cascade-runs-1280x720.png', visualShotOptions());
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('write_chapter_entity_panel_component', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.route('**/api/creator/memory-assets', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          slug: 'e2e-live-companion',
          memory_available: false,
          memory_rag_enabled: true,
          items: [
            {
              id: 'memory-char-李逍遥',
              kind: 'character',
              name: '李逍遥',
              excerpt: 'E2E 角色',
              chapters: [1],
              placeholder: false,
              source: 'e2e',
            },
          ],
        }),
      });
    });
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="creator-write-workbench"]').waitFor({ state: 'visible', timeout: 30_000 });
    await selectChapter(page);
    await page.getByTestId('chapter-body-textarea').evaluate((el) => {
      el.value = '李逍遥在雨夜里停下脚步。';
      el.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await prepareChapterEntityPanelForAudit(page);
    await expect(page.getByTestId('chapter-entity-memory-char-李逍遥')).toBeVisible({ timeout: 15_000 });
    const panel = page.locator('[data-testid="write-chapter-entity-rail"]');
    await waitForPaintSettle(page);
    await expect(panel).toHaveScreenshot('write-chapter-entity-panel.png', visualShotOptions(0.04));
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('write_director_paths_panel_component', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="creator-write-workbench"]').waitFor({ state: 'visible', timeout: 30_000 });
    await selectChapter(page);
    await prepareDirectorPathsPanelForAudit(page);
    const panel = page.locator('[data-testid="write-director-paths-panel-main"]');
    await expect(panel).toHaveScreenshot('write-director-paths-panel.png', visualShotOptions(0.03));
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('write_checkpoint_diff_component', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"视觉回归 checkpoint 正文"}],"provider":"mock","annotations":[],"scope":{"type":"chapter","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await page.locator('[data-testid="creator-write-workbench"]').waitFor({ state: 'visible', timeout: 30_000 });
    await selectChapter(page);
    await openAdvancedTools(page);
    await page.getByTestId('write-agent-input').fill('checkpoint 视觉');
    await page.getByTestId('write-agent-send-btn').click();
    await page.getByTestId('write-director-plan-card').waitFor({ state: 'visible', timeout: 15_000 });
    await page.getByTestId('write-candidate-c1').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await page.locator('[data-testid^="checkpoint-diff-"]').first().click();
    const diff = page.locator('[data-testid="write-checkpoint-diff"]');
    await diff.waitFor({ state: 'visible', timeout: 15_000 });
    await waitForPaintSettle(page);
    await expect(diff).toHaveScreenshot('write-checkpoint-diff.png', visualShotOptions(0.04));
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });
});
