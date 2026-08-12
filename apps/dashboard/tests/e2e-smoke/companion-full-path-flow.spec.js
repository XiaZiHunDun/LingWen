import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import {
  COMPANION_SLUG,
  getBodyDraft,
  openAdvancedTools,
  openCompanionProject,
  restoreCreatorProject,
  selectAllBody,
  selectChapter,
  setBodyDraft,
} from './helpers/companion-project.js';

const HANDWRITTEN = '林默在雨里写下第一段，灯影摇晃。';
const AGENT_TEXT = 'E2E全路径：Agent改写后的正文。';

test.describe('Companion full path (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('companion_handwrite_agent_save_logic_check', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"' + AGENT_TEXT + '"}],"provider":"mock","annotations":[],"scope":{"type":"chapter","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, HANDWRITTEN);
    await expect.poll(async () => getBodyDraft(page)).toBe(HANDWRITTEN);
    await selectAllBody(page);

    await openAdvancedTools(page);
    await page.getByTestId('write-agent-input').fill('润色这一段');
    await page.getByTestId('write-agent-send-btn').click();
    await expect(page.getByTestId('write-director-plan-card-main')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('write-candidate-c1').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect.poll(async () => getBodyDraft(page)).toBe(AGENT_TEXT);

    const saveResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes('/api/creator/chapters/1') &&
        resp.request().method() === 'PUT' &&
        resp.ok(),
      { timeout: 30_000 },
    );
    await page.getByTestId('save-chapter-body-btn').click();
    await saveResponse;
    await expect(page.getByTestId('chapter-body-save-status')).toBeVisible({ timeout: 15_000 });

    const logicBtn = page.getByTestId('run-companion-logic-check-btn');
    await expect(logicBtn).toBeVisible({ timeout: 15_000 });
    const logicResponse = page.waitForResponse(
      (resp) => resp.url().includes('/api/creator/logic-check') && resp.request().method() === 'POST',
      { timeout: 30_000 },
    );
    await logicBtn.click();
    await logicResponse;
    await expect(page.getByTestId('companion-logic-check-write-result')).toBeVisible({ timeout: 15_000 });
  });
});
