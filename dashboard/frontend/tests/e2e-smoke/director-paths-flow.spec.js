import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import {
  COMPANION_SLUG,
  openCompanionProject,
  restoreCreatorProject,
  selectChapter,
} from './helpers/companion-project.js';

test.describe('Director paths flow (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('companion_director_path_triggers_plan_card', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);

    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"导演路径产出"}],"provider":"mock","annotations":[],"scope":{"type":"chapter","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);

    await expect(page.getByTestId('write-director-paths-panel-main')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('write-director-paths')).toBeVisible();
    await page.getByTestId('director-path-run-faster').click();

    await expect(page.getByTestId('write-director-plan-card-main')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('write-candidate-c1')).toBeVisible();
  });

  test('companion_director_path_confirm_apply', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);

    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"导演路径确认替换正文"}],"provider":"mock","annotations":[],"scope":{"type":"chapter","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);

    await expect(page.getByTestId('write-director-paths-panel-main')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('director-path-run-faster').click();
    await expect(page.getByTestId('write-director-plan-card-main')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('write-candidate-c1').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect(page.getByTestId('chapter-body-textarea')).toHaveValue(/导演路径确认替换正文/, {
      timeout: 10_000,
    });
  });
});
