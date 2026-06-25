// Creator workspace live e2e (Phase creator v1.4)
import { test, expect } from '@playwright/test';
import { LIVE_E2E_ENABLED, clickNav, skipUnlessLive } from './helpers/live-backend.js';

test.describe('Creator workspace live e2e', () => {
  test('creator_nav_shows_three_columns', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.goto('/?nav=creator', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('page-title')).toHaveText('创作伴侣');
    await expect(page.getByTestId('creator-workspace-tabs')).toBeVisible();
    await expect(page.getByTestId('column-write')).toBeVisible();
    await expect(page.getByTestId('creator-workspace-tab-pulse')).toBeVisible();
    await expect(page.getByTestId('creator-workspace-tab-settings')).toBeVisible();
  });

  test('creator_volume_plan_panel_visible', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.goto('/?nav=creator', { waitUntil: 'domcontentloaded' });
    await page.getByTestId('creator-workspace-tab-pulse').click();
    await expect(page.getByTestId('volume-plan-panel')).toBeVisible();
    await expect(page.getByTestId('pillars-textarea')).toBeHidden();
    await page.getByTestId('creator-workspace-tab-settings').click();
    await expect(page.getByTestId('pillars-textarea')).toBeVisible();
  });

  test('companion_workspace_tabs_and_logic_check', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=creator', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('companion-logic-check-write')).toBeVisible({ timeout: 30_000 });
    await page.getByTestId('creator-workspace-tab-pulse').click();
    await expect(page.getByTestId('column-write')).toBeHidden();
    await expect(page.getByTestId('column-pulse')).toBeVisible();
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('creator_workspace_deep_link_opens_pulse_tab', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.goto('/?nav=creator&workspace=pulse', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('column-pulse')).toBeVisible();
    await expect(page.getByTestId('column-write')).toBeHidden();
  });

  test('creator_share_link_apply_save_flow', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    const token = await page.evaluate(() => {
      const payload = {
        v: 2,
        c: 1,
        changes: [{ type: 'changed', label: '一', message: 'e2e 分享' }],
        d: [{
          label: '一',
          start_chapter: 1,
          end_chapter: 5,
          core_conflict: 'E2E 分享卷纲',
          locked: false,
        }],
      };
      return btoa(unescape(encodeURIComponent(JSON.stringify(payload))))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');
    });
    await page.goto(`/?nav=creator#creator-diff=${token}`, { waitUntil: 'domcontentloaded' });
    const preview = page.getByTestId('volume-plan-diff-share-link-preview');
    await expect(preview).toBeVisible({ timeout: 30_000 });
    const applyBtn = page.getByTestId('apply-volume-plan-diff-share-btn');
    if (await applyBtn.isVisible()) {
      await applyBtn.click();
      const confirm = page.getByTestId('confirm-share-apply-btn');
      if (await confirm.isVisible({ timeout: 3000 }).catch(() => false)) {
        await confirm.click();
      }
      const mergeShare = page.getByTestId('share-merge-use-share-btn');
      if (await mergeShare.isVisible({ timeout: 3000 }).catch(() => false)) {
        await mergeShare.click();
      }
    }
    await page.getByTestId('save-volume-plan-btn').click();
    await expect(page.getByTestId('save-banner')).toBeVisible({ timeout: 20_000 });
  });
});
