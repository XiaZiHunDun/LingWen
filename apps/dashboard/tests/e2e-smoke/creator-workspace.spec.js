// Creator workspace live e2e (Phase creator v1.4)
import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import {
  COMPANION_SLUG,
  CREATOR_SLUG,
  closePulseDrawer,
  clickStable,
  dismissDeskDrawerIfOpen,
  openAdvancedTools,
  getBodyDraft,
  openCompanionProject,
  openPulseDrawer,
  restoreCreatorProject,
  selectChapter,
  setBodyDraft,
} from './helpers/companion-project.js';
import { mockDelayedAgentPlanStream } from './helpers/mock-agent-stream.js';

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
    await restoreCreatorProject(request);
  });

  test('creator_volume_merge_wizard_three_steps', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: CREATOR_SLUG } });
    await request.put('/api/creator/volume-plan', {
      data: {
        volumes: [
          { label: '一', start_chapter: 1, end_chapter: 6, core_conflict: 'E2E 卷一', locked: false },
          { label: '二', start_chapter: 7, end_chapter: 12, core_conflict: 'E2E 卷二', locked: false },
        ],
      },
    });

    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await openPulseDrawer(page);
    await expect(page.getByTestId('volume-plan-panel')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('merge-wizard-steps')).toBeVisible({ timeout: 15_000 });

    await page.getByTestId('merge-wizard-next-btn').click();
    await expect(page.getByTestId('merge-conflict-preview')).toBeVisible({ timeout: 10_000 });
    await page.getByTestId('merge-wizard-confirm-btn').click();
    await expect(page.getByTestId('apply-merge-btn')).toBeVisible({ timeout: 10_000 });

    await restoreCreatorProject(request);
  });

  test('creator_share_merge_wizard_on_conflict', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: CREATOR_SLUG } });
    await request.put('/api/creator/volume-plan', {
      data: {
        volumes: [
          { label: '一', start_chapter: 1, end_chapter: 6, core_conflict: '本地卷一冲突', locked: false },
          { label: '二', start_chapter: 7, end_chapter: 12, core_conflict: '本地卷二冲突', locked: false },
        ],
      },
    });
    const token = await page.evaluate(() => {
      const payload = {
        v: 2,
        c: 2,
        changes: [
          { type: 'changed', label: '一', message: '冲突：核心冲突变更' },
          { type: 'changed', label: '二', message: '冲突：章范围变更' },
        ],
        d: [
          { label: '一', start_chapter: 1, end_chapter: 6, core_conflict: '分享冲突卷一', locked: false },
          { label: '二', start_chapter: 7, end_chapter: 12, core_conflict: '分享冲突卷二', locked: false },
        ],
      };
      return btoa(unescape(encodeURIComponent(JSON.stringify(payload))))
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');
    });

    await page.goto(`/?nav=write&workspace=pulse#creator-diff=${token}`, { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('volume-plan-panel')).toBeVisible({ timeout: 30_000 });
    await expect(page.locator('[data-testid="volume-row-0"] .vol-conflict')).toHaveValue(/本地卷一冲突/, {
      timeout: 15_000,
    });
    await expect(page.getByTestId('volume-plan-diff-share-link-preview')).toBeVisible({ timeout: 30_000 });
    await dismissDeskDrawerIfOpen(page);
    await clickStable(page.getByTestId('apply-volume-plan-diff-share-btn'));

    await expect(page.getByTestId('confirm-share-apply-btn')).toBeVisible({ timeout: 10_000 });
    await clickStable(page.getByTestId('confirm-share-apply-btn'));

    const mergeWizard = page.getByTestId('volume-plan-diff-share-merge-wizard');
    await expect(mergeWizard).toBeVisible({ timeout: 15_000 });
    await expect(mergeWizard).toContainText(/冲突|分享/);
    await clickStable(page.getByTestId('share-merge-use-share-btn'));
    await openPulseDrawer(page);
    await expect(page.locator('[data-testid="volume-row-0"] .vol-conflict')).toHaveValue(/分享冲突卷一/, {
      timeout: 15_000,
    });

    await restoreCreatorProject(request);
  });

  test('companion_light_validation_bar', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: 'e2e-live-companion' } });
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('creator-write-workbench')).toBeVisible({ timeout: 30_000 });
    await page.getByTestId('chapter-row-1').click();
    await expect(page.getByTestId('write-light-validation-bar')).toBeVisible({ timeout: 15_000 });
    await setBodyDraft(page, '角色说"未完待续');
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
    await openAdvancedTools(page);
    await page.getByTestId('write-agent-input').fill('加快节奏');
    const [streamResponse] = await Promise.all([
      page.waitForResponse(
        (resp) => resp.url().includes('/api/creator/agent/plan/stream') && resp.ok(),
      ),
      page.getByTestId('write-agent-send-btn').click(),
    ]);
    expect(streamResponse.headers()['content-type'] || '').toContain('text/event-stream');
    await expect(page.getByTestId('write-director-plan-card-main')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('write-candidate-c1')).toBeVisible();
    await restoreCreatorProject(request);
  });

  test('companion_agent_stream_preview_ui_visible_during_sse', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });
    await mockDelayedAgentPlanStream(page, { chunkText: '流式预览可见性', chunkDelayMs: 1500 });

    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await selectChapter(page);
    await openAdvancedTools(page);
    await page.getByTestId('write-agent-input').fill('测试流式可见性');

    const preview = page.getByTestId('write-agent-stream-preview-main');
    await Promise.all([
      expect(preview).toBeVisible({ timeout: 15_000 }),
      page.getByTestId('write-agent-send-btn').click(),
    ]);
    await expect(preview).toContainText(/流式预览可见性|候选预览/);

    await expect(page.getByTestId('write-director-plan-card-main')).toBeVisible({ timeout: 15_000 });
    await restoreCreatorProject(request);
  });

  test('companion_desk_drawer_pulse_open_close', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await openCompanionProject(page, request, COMPANION_SLUG);
    await openPulseDrawer(page);
    await expect(page.getByTestId('column-pulse')).toBeVisible();
    await closePulseDrawer(page);
    await restoreCreatorProject(request);
  });

  test('companion_agent_candidate_confirms_body_change', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"E2E确认替换正文"}],"provider":"mock","annotations":[],"scope":{"type":"chapter","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await selectChapter(page);
    await openAdvancedTools(page);
    await page.getByTestId('write-agent-input').fill('测试确认流');
    await page.getByTestId('write-agent-send-btn').click();
    await expect(page.getByTestId('write-director-plan-card-main')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('write-candidate-c1').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect(page.getByTestId('chapter-body-textarea')).toHaveValue(/E2E确认替换正文/, {
      timeout: 10_000,
    });
    await restoreCreatorProject(request);
  });

  test('companion_agent_multi_candidate_pick_c2_confirms_body', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"E2E候选一段正文"},{"id":"c2","label":"B","text":"E2E候选二段正文"},{"id":"c3","label":"C","text":"E2E候选三段正文"}],"provider":"mock","annotations":[],"scope":{"type":"chapter","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await selectChapter(page);
    await openAdvancedTools(page);
    await page.getByTestId('write-agent-input').fill('多候选对比测试');
    await page.getByTestId('write-agent-send-btn').click();
    await expect(page.getByTestId('write-director-plan-card-main')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('write-candidate-dock-main')).toBeVisible();
    await page.getByTestId('write-candidate-c2').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect(page.getByTestId('chapter-body-textarea')).toHaveValue(/E2E候选二段正文/, {
      timeout: 10_000,
    });
    await restoreCreatorProject(request);
  });

  test('companion_agent_confirm_checkpoint_diff_and_undo', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: COMPANION_SLUG } });

    await page.route('**/api/creator/agent/plan/stream', async (route) => {
      const sse = [
        'data: {"type":"done","plan":{"advice_only":false,"candidates":[{"id":"c1","label":"A","text":"E2E checkpoint 替换正文"}],"provider":"mock","annotations":[],"scope":{"type":"chapter","chapter":1}}}\n\n',
      ].join('');
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: sse,
      });
    });

    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await selectChapter(page);
    const beforeBody = await getBodyDraft(page);
    await openAdvancedTools(page);
    await page.getByTestId('write-agent-input').fill('checkpoint 测试');
    await page.getByTestId('write-agent-send-btn').click();
    await expect(page.getByTestId('write-director-plan-card-main')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('write-candidate-c1').click();
    await page.getByTestId('write-director-confirm-btn').click();
    await expect(page.getByTestId('chapter-body-textarea')).toHaveValue(/E2E checkpoint 替换正文/, {
      timeout: 10_000,
    });

    await expect(page.getByTestId('write-undo-last-btn')).toBeVisible({ timeout: 10_000 });
    const diffBtn = page.locator('[data-testid^="checkpoint-diff-"]').first();
    await diffBtn.click();
    await expect(page.getByTestId('write-checkpoint-diff')).toBeVisible({ timeout: 10_000 });
    await page.getByTestId('write-undo-last-btn').click();
    await expect(page.getByTestId('chapter-body-textarea')).toHaveValue(beforeBody, { timeout: 10_000 });
    await restoreCreatorProject(request);
  });

  test('companion_light_validation_pill_focuses_editor', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await openCompanionProject(page, request, COMPANION_SLUG);
    await selectChapter(page);
    await setBodyDraft(page, '角色说"未完待续');
    const pill = page.getByTestId('light-validation-stub_chapter');
    await expect(pill).toBeVisible({ timeout: 5_000 });
    await pill.click();
    await expect(page.getByTestId('chapter-body-textarea')).toHaveClass(/chapter-body-textarea--conflict/);
    await restoreCreatorProject(request);
  });
});
