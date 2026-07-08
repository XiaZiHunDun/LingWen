import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import {
  COMPANION_SLUG,
  openAdvancedTools,
  openCompanionProject,
  restoreCreatorProject,
  selectChapter,
} from './helpers/companion-project.js';

const BODY = '开头段落。\n\n中间待改。\n\n结尾。';
const SELECTED = '中间待改';
const REPLACED = '中间已润色';
const EXPECTED = '开头段落。\n\n中间已润色。\n\n结尾。';
const INSERTED = 'E2E插入的新段落。';
const INSERT_EXPECTED = `${EXPECTED}\n\n${INSERTED}`;

async function setBodyDraft(page, text) {
  const textarea = page.getByTestId('chapter-body-textarea');
  await textarea.scrollIntoViewIfNeeded();
  await textarea.evaluate((el, value) => {
    el.value = String(value);
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }, text);
}

async function selectBodyRange(page, needle) {
  const textarea = page.getByTestId('chapter-body-textarea');
  await textarea.scrollIntoViewIfNeeded();
  await textarea.evaluate((el, part) => {
    el.focus();
    const start = el.value.indexOf(String(part));
    if (start < 0) throw new Error(`selection needle not found: ${part}`);
    el.setSelectionRange(start, start + String(part).length);
    el.dispatchEvent(new Event('select', { bubbles: true }));
    el.dispatchEvent(new Event('mouseup', { bubbles: true }));
  }, needle);
}

test.describe('Companion selection agent (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('companion_selection_rewrite_and_insert', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(120_000);

    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const payload = route.request().postDataJSON?.() ?? {};
      const isSelection = payload.scope?.type === 'selection';
      const text = isSelection ? REPLACED : INSERTED;
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"' + text + '"}],"provider":"mock","annotations":[],"scope":{"type":"' + (isSelection ? 'selection' : 'chapter') + '","chapter":1}}}\n\n',
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

    await openAdvancedTools(page);
    await expect(page.getByTestId('write-scope-bar')).toContainText('选中', { timeout: 10_000 });
    await page.getByTestId('write-agent-input').fill('润色选中段落');
    await page.getByTestId('write-agent-send-btn').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('write-candidate-c1').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect.poll(async () => page.getByTestId('chapter-body-textarea').inputValue()).toBe(EXPECTED);

    const textarea = page.getByTestId('chapter-body-textarea');
    await textarea.evaluate((el) => {
      el.focus();
      el.setSelectionRange(el.value.length, el.value.length);
      el.dispatchEvent(new Event('select', { bubbles: true }));
      el.dispatchEvent(new Event('mouseup', { bubbles: true }));
    });

    await page.getByTestId('write-agent-input').fill('在章末插入一段');
    await page.getByTestId('write-agent-send-btn').click();
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('write-candidate-c1').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect.poll(async () => page.getByTestId('chapter-body-textarea').inputValue()).toBe(INSERT_EXPECTED);
  });
});
