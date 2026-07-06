// Creator workspace live e2e (Phase creator v1.4)
import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';

/** 断言区域可滚动（overflow + 必要时 scrollTop 变化） */
async function expectScrollableRegion(locator) {
  const metrics = await locator.evaluate((el) => ({
    scrollHeight: el.scrollHeight,
    clientHeight: el.clientHeight,
    overflowY: getComputedStyle(el).overflowY,
  }));
  expect(metrics.overflowY).toMatch(/auto|scroll/);
  expect(metrics.clientHeight).toBeGreaterThan(0);
  if (metrics.scrollHeight <= metrics.clientHeight + 8) {
    return;
  }
  const before = await locator.evaluate((el) => el.scrollTop);
  await locator.evaluate((el) => {
    el.scrollTop = el.scrollHeight;
  });
  const after = await locator.evaluate((el) => el.scrollTop);
  expect(after).toBeGreaterThan(before);
}

async function openPulseDrawer(page) {
  const drawerTrigger = page.getByTestId('creator-desk-drawer-pulse');
  const tabPulse = page.getByTestId('creator-workspace-tab-pulse');
  try {
    await drawerTrigger.waitFor({ state: 'visible', timeout: 30_000 });
    await drawerTrigger.click();
    return;
  } catch {
    await tabPulse.waitFor({ state: 'visible', timeout: 10_000 });
    await tabPulse.click();
  }
}

test.describe('Creator workspace live e2e', () => {
  test('creator_nav_shows_three_columns', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('header-l1-page-name')).toHaveText('书桌');
    await expect(page.getByTestId('creator-workspace-tabs')).toBeVisible();
    await expect(page.getByTestId('column-write')).toBeVisible();
    const drawerPulse = page.getByTestId('creator-desk-drawer-pulse');
    const tabPulse = page.getByTestId('creator-workspace-tab-pulse');
    await expect(drawerPulse.or(tabPulse)).toBeVisible();
    await expect(page.getByTestId('creator-workspace-tab-settings')).toBeVisible();
  });

  test('creator_volume_plan_panel_visible', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await openPulseDrawer(page);
    await expect(page.getByTestId('volume-plan-panel')).toBeVisible();
    await expect(page.getByTestId('pillars-textarea')).toBeHidden();
    const closeDrawer = page.getByTestId('desk-drawer-close-pulse');
    if (await closeDrawer.isVisible().catch(() => false)) {
      await closeDrawer.click();
    }
    await page.getByTestId('creator-workspace-tab-settings').click();
    await page.getByTestId('settings-pillars-block').locator('summary').click();
    await expect(page.getByTestId('pillars-textarea')).toBeVisible();
  });

  test('companion_workspace_tabs_and_logic_check', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('companion-logic-check-write')).toBeVisible({ timeout: 30_000 });
    await openPulseDrawer(page);
    await expect(page.getByTestId('column-write')).toBeVisible();
    await expect(page.getByTestId('column-pulse')).toBeVisible();
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('companion_pulse_shows_deviation_badge', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    const drawerPulse = page.getByTestId('creator-desk-drawer-pulse');
    const tabPulse = page.getByTestId('creator-workspace-tab-pulse');
    const pulseTrigger = drawerPulse.or(tabPulse);
    const badge = pulseTrigger.locator('.hub-tab-badge');
    await expect(badge).toBeVisible({ timeout: 30_000 });
    await openPulseDrawer(page);
    await expect(page.getByTestId('deviation-list')).toBeVisible({ timeout: 30_000 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('creator_workspace_deep_link_opens_pulse_tab', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await page.goto('/?nav=write&workspace=pulse', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('column-pulse')).toBeVisible();
    await expect(page.getByTestId('column-write')).toBeVisible();
  });

  test('creator_write_and_pulse_scroll_regions', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 1280, height: 720 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('creator-write-workbench')).toBeVisible({ timeout: 30_000 });

    const pageBody = page.locator('.creator-page__body');
    await expect(pageBody).toBeVisible();
    const bodyOverflow = await pageBody.evaluate((el) => getComputedStyle(el).overflow);
    expect(bodyOverflow).toBe('hidden');

    const workbench = page.getByTestId('creator-write-workbench');
    const isHumanFirst = await workbench.evaluate((el) =>
      el.classList.contains('write-workbench--human-first'),
    );

    if (isHumanFirst) {
      const editorSlot = page.locator('.write-workbench__editor-slot--primary');
      await expect(editorSlot).toBeVisible();
      await expectScrollableRegion(editorSlot);

      const chapterRail = page.locator('.write-workbench__stack--chapters');
      await expect(chapterRail).toBeVisible();
      await expectScrollableRegion(chapterRail);
    } else {
      const writeMain = page.locator('.write-workbench__main');
      await expect(writeMain).toBeVisible();
      await expectScrollableRegion(writeMain);

      const writeLeft = page.locator('.write-workbench__left');
      await expect(writeLeft).toBeVisible();
      const leftOverflow = await writeLeft.evaluate((el) => getComputedStyle(el).overflowY);
      expect(leftOverflow).toMatch(/auto|scroll/);
    }

    await openPulseDrawer(page);
    await expect(page.getByTestId('column-pulse')).toBeVisible();
    const pulseScroll = page.locator('.pulse-desk__scroll');
    await expect(pulseScroll).toBeVisible();
    await expectScrollableRegion(pulseScroll);

    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('creator_share_link_apply_save_flow', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
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
    await page.goto(`/?nav=write#creator-diff=${token}`, { waitUntil: 'domcontentloaded' });
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
    await openPulseDrawer(page);
    const saveBtn = page.getByTestId('save-volume-plan-btn');
    await expect(saveBtn).toBeVisible({ timeout: 30_000 });
    await saveBtn.click();
    await expect(page.getByTestId('save-banner')).toBeVisible({ timeout: 20_000 });
  });

  test('companion_light_validation_bar', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('creator-write-workbench')).toBeVisible({ timeout: 30_000 });
    await page.getByTestId('chapter-row-1').click();
    await expect(page.getByTestId('write-light-validation-bar')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('chapter-body-textarea').evaluate((el) => {
      el.value = '角色说"未完待续';
      el.dispatchEvent(new Event('input', { bubbles: true }));
    });
    await expect(page.getByTestId('light-validation-unclosed_quote')).toBeVisible({ timeout: 5_000 });
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });

  test('companion_agent_stream_preview', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });

    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const sse = [
        'data: {"type":"status","message":"生成中…"}\n\n',
        'data: {"type":"preview_label","label":"候选预览 1/3"}\n\n',
        'data: {"type":"chunk","text":"流式预览测试"}\n\n',
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"段一"},{"id":"c2","label":"B","text":"段二"},{"id":"c3","label":"C","text":"段三"}],"provider":"mock","annotations":[]}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('creator-write-workbench')).toBeVisible({ timeout: 30_000 });
    await page.getByTestId('chapter-row-1').click();
    await page.getByTestId('write-advanced-tools').locator('summary').click();
    await page.getByTestId('write-agent-strip').locator('summary').click();
    await page.getByTestId('write-agent-input').fill('加快节奏');
    const [streamResponse] = await Promise.all([
      page.waitForResponse(
        (resp) => resp.url().includes('/api/creator/agent/plan/stream') && resp.ok(),
      ),
      page.getByTestId('write-agent-send-btn').click(),
    ]);
    expect(streamResponse.headers()['content-type'] || '').toContain('text/event-stream');
    await expect(page.getByTestId('write-director-plan-card')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('write-candidate-c1')).toBeVisible();
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-creator' } });
  });
});
