import { test, expect } from '@playwright/test';
import { clickNav, skipUnlessLive } from './helpers/live-backend.js';
import { COMPANION_SLUG, restoreCreatorProject } from './helpers/companion-project.js';

test.describe('Ask flow (live)', () => {
  test('ask_first_message_then_go_write', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.goto('/?nav=ask', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('ask-page')).toBeVisible({ timeout: 30_000 });

    await page.getByTestId('ask-input').fill('这本书写到哪了？');
    await page.getByTestId('ask-send-btn').click();

    await expect(
      page.getByTestId('ask-messages').locator('.ask-page__msg--assistant').last(),
    ).toBeVisible({ timeout: 30_000 });

    await page.getByTestId('ask-go-write-btn').click();
    await expect(page.getByTestId('creator-write-workbench')).toBeVisible({ timeout: 30_000 });

    await restoreCreatorProject(request);
  });

  test('ask_suggestion_chip_sends', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.goto('/?nav=ask', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('ask-topic-list')).toBeVisible({ timeout: 30_000 });

    await page.getByTestId('ask-suggestion-progress').click();
    await expect(page.getByTestId('ask-messages').locator('.ask-page__msg--user')).toBeVisible({
      timeout: 15_000,
    });

    await restoreCreatorProject(request);
  });

  test('ask_long_draft_hints_and_go_write', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.goto('/?nav=ask', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('ask-page')).toBeVisible({ timeout: 30_000 });

    const long = '续'.repeat(281);
    await page.getByTestId('ask-input').fill(long);
    await expect(page.getByTestId('ask-long-draft-hint')).toBeVisible();
    await expect(page.getByTestId('ask-send-btn')).toBeDisabled();

    await page.getByTestId('ask-long-go-write-btn').click();
    await expect(page.getByTestId('creator-write-workbench')).toBeVisible({ timeout: 30_000 });

    await restoreCreatorProject(request);
  });
});
