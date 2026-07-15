import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import {
  COMPANION_SLUG,
  openCompanionProject,
  openMemoryDrawer,
  restoreCreatorProject,
} from './helpers/companion-project.js';

test.describe('Memory gateway flow (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('memory_status_shows_offline_when_gateway_unavailable', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);

    await page.route('**/api/creator/memory-assets', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          slug: COMPANION_SLUG,
          memory_available: false,
          memory_rag_enabled: true,
          items: [],
        }),
      });
    });

    const memoryReady = page.waitForResponse(
      (resp) => resp.url().includes('/api/creator/memory-assets') && resp.ok(),
    );
    await openCompanionProject(page, request, COMPANION_SLUG);
    await memoryReady;
    await openMemoryDrawer(page);

    const status = page.getByTestId('memory-status-bar');
    await expect(status).toBeVisible();
    await expect(status).toContainText(/离线|降级/);
    await expect(page.getByTestId('intervention-item-memory-offline')).toBeVisible({ timeout: 15_000 });
  });

  test('memory_live_status_and_no_offline_banner_when_gateway_live', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);

    await page.route('**/api/creator/memory-assets', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          slug: COMPANION_SLUG,
          memory_available: true,
          memory_rag_enabled: true,
          items: [
            {
              id: 'memory-char-live',
              kind: 'character',
              name: '网关角色',
              excerpt: 'E2E live gateway',
              chapters: [1],
              placeholder: false,
              source: 'memory',
            },
          ],
        }),
      });
    });

    const memoryReady = page.waitForResponse(
      (resp) => resp.url().includes('/api/creator/memory-assets') && resp.ok(),
    );
    await openCompanionProject(page, request, COMPANION_SLUG);
    await memoryReady;

    await openMemoryDrawer(page);
    await expect(page.getByTestId('memory-status-bar')).toContainText('已连接');
    await expect(page.getByTestId('intervention-item-memory-offline')).toHaveCount(0);
  });

  test('memory_search_shows_local_fallback_hint_when_offline', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);

    await page.route('**/api/creator/memory/query', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          slug: COMPANION_SLUG,
          memory_available: false,
          used_fallback: true,
          results: [
            {
              id: 'local-1',
              kind: 'character',
              asset_name: '李逍遥',
              snippet: '本地匹配结果',
              score: 0.42,
              source: 'local',
              matched_terms: ['李逍遥'],
            },
          ],
        }),
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await openMemoryDrawer(page);

    await page.getByTestId('memory-search-input').fill('李逍遥');
    await page.getByTestId('memory-search-btn').click();
    await expect(page.getByTestId('memory-search-hint')).toContainText('本地匹配', { timeout: 15_000 });
    await expect(page.getByTestId('memory-search-result-local-1')).toBeVisible();
  });
});
