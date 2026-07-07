import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import {
  COMPANION_SLUG,
  openCompanionProject,
  restoreCreatorProject,
  selectChapter,
} from './helpers/companion-project.js';

async function expandChapterEntityPanel(page) {
  const panel = page.getByTestId('write-chapter-entity-panel');
  await expect(panel).toBeVisible({ timeout: 30_000 });
  if (!(await panel.evaluate((el) => el.open))) {
    await panel.locator('summary').click();
  }
  await expect(page.getByTestId('write-chapter-entity-rail')).toBeVisible({ timeout: 15_000 });
}

test.describe('Entity rail → memory tab (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('companion_body_mention_entity_opens_memory_tab', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);

    await page.route('**/api/creator/memory-assets', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          slug: COMPANION_SLUG,
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

    const memoryReady = page.waitForResponse(
      (resp) => resp.url().includes('/api/creator/memory-assets') && resp.ok(),
    );
    await openCompanionProject(page, request, COMPANION_SLUG);
    await memoryReady;
    await selectChapter(page);

    await page.getByTestId('chapter-body-textarea').evaluate((el) => {
      el.value = '李逍遥在雨夜里停下脚步。';
      el.dispatchEvent(new Event('input', { bubbles: true }));
    });

    await expandChapterEntityPanel(page);
    await expect(page.getByTestId('chapter-entity-memory-char-李逍遥')).toBeVisible({
      timeout: 15_000,
    });

    await page.getByTestId('chapter-entity-goto-memory').first().click();

    await expect(
      page.getByTestId('desk-drawer-chrome-memory').or(page.getByTestId('creator-workspace-tab-memory')),
    ).toBeVisible({ timeout: 15_000 });

    const memoryRoot = page.getByTestId('column-memory');
    await expect(memoryRoot).toBeVisible({ timeout: 15_000 });
    const focusedAsset = memoryRoot.getByTestId('memory-asset-memory-char-李逍遥');
    await expect(focusedAsset).toBeVisible({ timeout: 15_000 });
    await expect(focusedAsset).toHaveClass(/asset-row--focused/);
    await expect(memoryRoot.getByTestId('creator-memory-assets')).toBeVisible({
      timeout: 15_000,
    });
  });
});
