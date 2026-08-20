// Phase 66: Form validation e2e integration tests.
// Asserts that the ask input form (chat + notes) keeps send buttons disabled
// when empty and accepts non-empty input.
import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import { COMPANION_SLUG, restoreCreatorProject } from './helpers/companion-project.js';

test.describe('Form validation (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('ask_send_btn_disabled_when_input_empty', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.goto('/?nav=ask', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('ask-page')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('ask-input')).toBeVisible();

    await expect(page.getByTestId('ask-send-btn')).toBeDisabled();
  });

  test('note_save_btn_disabled_when_input_empty', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.goto('/?nav=ask', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('ask-page')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('ask-note-input')).toBeVisible();

    await expect(page.getByTestId('ask-note-save-btn')).toBeDisabled();
  });

  test('ask_send_btn_enabled_when_input_has_text', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.goto('/?nav=ask', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('ask-page')).toBeVisible({ timeout: 30_000 });
    const input = page.getByTestId('ask-input');
    await input.fill('写一个短篇大纲');

    await expect(page.getByTestId('ask-send-btn')).toBeEnabled();
  });
});