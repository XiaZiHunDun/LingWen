import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import {
  COMPANION_SLUG,
  clearBodySelection,
  getBodyDraft,
  openAdvancedTools,
  openCompanionProject,
  restoreCreatorProject,
  selectBodyRange,
  selectChapter,
  setBodyDraft,
} from './helpers/companion-project.js';

const BODY = '开头段落。\n\n中间待改。\n\n结尾。';
const SELECTED = '中间待改';
const REPLACED = '中间已润色';
const REPLACED_C2 = '中间更大胆';
const EXPECTED = '开头段落。\n\n中间已润色。\n\n结尾。';
const EXPECTED_C2 = '开头段落。\n\n中间更大胆。\n\n结尾。';
const INSERTED = 'E2E插入的新段落。';
const INSERT_EXPECTED = `${EXPECTED}\n\n${INSERTED}`;

function mockAgentPlanStream(page, { selectionText = REPLACED, chapterText = INSERTED } = {}) {
  return page.route('**/api/creator/agent/plan/stream', async (route) => {
    const payload = route.request().postDataJSON?.() ?? {};
    const isSelection = payload.scope?.type === 'selection';
    const text = isSelection ? selectionText : chapterText;
    const sse = [
      'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"' + text + '"}],"provider":"mock","annotations":[],"scope":{"type":"' + (isSelection ? 'selection' : 'chapter') + '","chapter":1}}}\n\n',
    ].join('');
    await route.fulfill({
      status: 200,
      contentType: 'text/event-stream; charset=utf-8',
      body: sse,
    });
  });
}

test.describe('Companion selection agent (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('companion_selection_rewrite_and_insert', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    await mockAgentPlanStream(page);

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    await openAdvancedTools(page);
    await expect(page.getByTestId('write-scope-bar')).toContainText('选中', { timeout: 10_000 });
    await page.getByTestId('write-agent-input').fill('润色选中段落');
    await page.getByTestId('write-agent-send-btn').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('write-candidate-c1').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect.poll(async () => getBodyDraft(page)).toBe(EXPECTED);

    await clearBodySelection(page);

    await page.getByTestId('write-agent-input').fill('在章末插入一段');
    await page.getByTestId('write-agent-send-btn').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('write-candidate-c1').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect.poll(async () => getBodyDraft(page)).toBe(INSERT_EXPECTED);
  });

  test('companion_selection_preset_confirm_undo', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    let capturedPayload = null;
    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      capturedPayload = route.request().postDataJSON?.() ?? {};
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"稳健","text":"' + REPLACED + '"},{"id":"c2","label":"大胆","text":"中间更大胆"}],"provider":"mock","annotations":[],"scope":{"type":"selection","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    await expect(page.getByTestId('write-scope-bar')).toContainText('选中', { timeout: 10_000 });
    await expect(page.getByTestId('write-selection-tools')).toBeVisible({ timeout: 10_000 });
    await page.getByTestId('rewrite-preset-concrete').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    expect(capturedPayload?.action).toBe('rewrite:concrete');
    expect(capturedPayload?.scope?.type).toBe('selection');

    await page.getByTestId('write-candidate-c1').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect.poll(async () => getBodyDraft(page)).toBe(EXPECTED);

    await expect(page.getByTestId('write-undo-bar-main')).toBeVisible({ timeout: 10_000 });
    await page.locator('[data-testid^="checkpoint-diff-"]').first().click();
    await expect(page.getByTestId('write-checkpoint-diff')).toBeVisible({ timeout: 10_000 });
    await page.getByTestId('write-undo-last-btn').click();
    await expect.poll(async () => getBodyDraft(page)).toBe(BODY);
  });

  test('companion_selection_preset_blocked_when_locked', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    let streamCalls = 0;
    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      streamCalls += 1;
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: 'data: {"type":"done","plan":{"advice_only":false,"candidates":[],"provider":"mock"}}\n\n',
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    await openAdvancedTools(page);
    await page.getByTestId('selection-lock-toggle').click();
    await page.getByTestId('rewrite-preset-concrete').click();

    await expect(page.getByTestId('write-director-plan-card')).toBeHidden();
    await expect(page.getByTestId('write-quality-bar')).toContainText('锁定', { timeout: 10_000 });
    expect(streamCalls).toBe(0);
  });

  test('companion_selection_preset_pick_c2_confirms_body', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"稳健","text":"' + REPLACED + '"},{"id":"c2","label":"大胆","text":"' + REPLACED_C2 + '"}],"provider":"mock","annotations":[],"scope":{"type":"selection","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, BODY);
    await selectBodyRange(page, SELECTED);

    await page.getByTestId('rewrite-preset-dramatic').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('write-candidate-c2').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect.poll(async () => getBodyDraft(page)).toBe(EXPECTED_C2);
  });
});
