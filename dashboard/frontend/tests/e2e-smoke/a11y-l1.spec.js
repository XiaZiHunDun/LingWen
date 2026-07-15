// L1 accessibility smoke — axe-core critical / serious / moderate
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { LIVE_E2E_ENABLED, clearInboxPending } from './helpers/live-backend.js';
import { waitForPaintSettle } from '../visual-audit/helpers/capture-ui-audit.js';

const L1_PAGES = [
  { name: 'ask', path: '/?nav=ask', testId: 'ask-page' },
  { name: 'library', path: '/?nav=library', testId: 'library-page' },
  { name: 'more', path: '/?nav=more', testId: 'more-page' },
  { name: 'write', path: '/?nav=write', testId: 'creator-write-workbench' },
  { name: 'today', path: '/?nav=today', testId: 'today-page', waitLoading: true, clearInbox: true },
  { name: 'produce', path: '/?nav=produce', testId: 'produce-page', slug: 'e2e-live-creator' },
  { name: 'inbox', path: '/?nav=inbox&tab=decisions', testId: 'inbox-page' },
];

function skipUnlessLive(testInstance) {
  testInstance.skip(!LIVE_E2E_ENABLED, 'set LINGWEN_E2E_LIVE=1 for a11y smoke');
}

test.describe('L1 accessibility smoke (axe)', () => {
  for (const pageDef of L1_PAGES) {
    test(`a11y_${pageDef.name}_no_critical_violations`, async ({ page, request }) => {
      skipUnlessLive(test);
      test.setTimeout(90_000);
      if (pageDef.clearInbox) {
        clearInboxPending();
      }
      const slug = pageDef.slug || 'e2e-live-companion';
      await request.put('/api/studio/active', { data: { slug } });

      await page.emulateMedia({ reducedMotion: 'reduce' });
      await page.goto(pageDef.path, { waitUntil: 'domcontentloaded' });
      await page.locator(`[data-testid="${pageDef.testId}"]`).waitFor({ state: 'visible', timeout: 30_000 });
      if (pageDef.waitLoading) {
        await page.getByTestId('today-loading').waitFor({ state: 'hidden', timeout: 45_000 }).catch(() => {});
      }
      await waitForPaintSettle(page);

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      const blocking = results.violations.filter((v) =>
        ['critical', 'serious', 'moderate'].includes(v.impact),
      );
      expect(
        blocking,
        blocking.map((v) => `${v.id}: ${v.help} (${v.nodes.length} nodes)`).join('\n'),
      ).toEqual([]);

      await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
    });
  }
});
