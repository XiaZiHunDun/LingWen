// Phase 66: Cross-tab persistence e2e integration tests.
// Asserts that localStorage-based preferences and auth-style signals survive
// across tabs in the same browser context.
import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import {
  COMPANION_SLUG,
  WRITE_RESUME_KEY,
  restoreCreatorProject,
} from './helpers/companion-project.js';

test.describe('Cross-tab persistence (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request);
  });

  test('write_resume_flag_visible_across_tabs', async ({ browser, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    const context = await browser.newContext();
    try {
      const tabA = await context.newPage();
      await tabA.addInitScript(
        ({ key, slug, chapter }) => {
          localStorage.setItem(
            key,
            JSON.stringify({ [slug]: { chapter, at: Date.now() } }),
          );
        },
        { key: WRITE_RESUME_KEY, slug: COMPANION_SLUG, chapter: 5 },
      );
      await tabA.goto('/', { waitUntil: 'domcontentloaded' });
      await expect(tabA.getByTestId('writer-desk')).toBeVisible({ timeout: 30_000 });

      const tabB = await context.newPage();
      await tabB.goto('/', { waitUntil: 'domcontentloaded' });
      const storedValue = await tabB.evaluate((key) => localStorage.getItem(key), WRITE_RESUME_KEY);
      expect(storedValue).toBeTruthy();
      const parsed = JSON.parse(storedValue);
      expect(parsed[COMPANION_SLUG]?.chapter).toBe(5);
    } finally {
      await context.close();
    }
  });

  test('clearing_localstorage_in_one_tab_propagates_to_other', async ({ browser, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    const context = await browser.newContext();
    try {
      const tabA = await context.newPage();
      await tabA.addInitScript(
        ({ key, slug }) => {
          localStorage.setItem(
            key,
            JSON.stringify({ [slug]: { chapter: 7, at: Date.now() } }),
          );
        },
        { key: WRITE_RESUME_KEY, slug: COMPANION_SLUG },
      );
      await tabA.goto('/', { waitUntil: 'domcontentloaded' });
      await expect(tabA.getByTestId('writer-desk')).toBeVisible({ timeout: 30_000 });

      // Open tabB and ensure the key is present before clearing.
      const tabB = await context.newPage();
      await tabB.goto('/', { waitUntil: 'domcontentloaded' });
      const beforeClear = await tabB.evaluate((key) => localStorage.getItem(key), WRITE_RESUME_KEY);
      expect(beforeClear).toBeTruthy();

      // Open tabC and arm a storage-event listener BEFORE the mutation in tabB,
      // so we can prove the cross-tab propagation actually fires.
      const tabC = await context.newPage();
      const storageEventPromise = tabC.waitForEvent('storage');
      await tabC.goto('/', { waitUntil: 'domcontentloaded' });

      // Clear in tabB — must fire a 'storage' event in tabC (same context).
      await tabB.evaluate((key) => localStorage.removeItem(key), WRITE_RESUME_KEY);

      const event = await storageEventPromise;
      expect(event.key).toBe(WRITE_RESUME_KEY);
      expect(event.storageArea).toBeTruthy();
      // Verify tabC is on a known surface (post-goto('/') lands on /creator/ via init script)
      await expect(tabC).toHaveURL(/\/creator\/?$/);

      // Cleanup
      await tabC.close();
      await tabB.close();
    } finally {
      await context.close();
    }
  });
});
