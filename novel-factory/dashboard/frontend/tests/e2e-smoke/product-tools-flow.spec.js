// Product tools live e2e — 故事结构图 + 介入规则 UI（矩阵 §9 MVP）
import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import {
  COMPANION_SLUG,
  dismissDeskDrawerIfOpen,
  openCompanionProject,
  openPulseDrawer,
  restoreCreatorProject,
} from './helpers/companion-project.js';

test.describe('Creator product tools live e2e', () => {
  test('structure_graph_timeline_toggle', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await openPulseDrawer(page);
    const graph = page.getByTestId('creator-structure-graph');
    await expect(graph).toBeVisible({ timeout: 30_000 });
    await page.getByTestId('structure-view-timeline').click();
    await expect(page.getByTestId('structure-timeline')).toBeVisible();
    await page.getByTestId('structure-view-tree').click();
    await expect(page.getByTestId('structure-chapter-1')).toBeVisible();
    await dismissDeskDrawerIfOpen(page);
  });

  test('intervention_rules_toggle_in_settings', async ({ page }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await page.getByTestId('creator-workspace-tab-settings').click();
    await expect(page.getByTestId('creator-preferences-section')).toBeVisible({ timeout: 30_000 });
    const rulesBlock = page.getByTestId('intervention-rules-block');
    await rulesBlock.locator('summary').click();
    const logicRule = page.getByTestId('pref-intervention-logicP0');
    await expect(logicRule).toBeVisible();
    const before = await logicRule.isChecked();
    await logicRule.click();
    await expect(logicRule).toBeChecked({ checked: !before });
    await logicRule.click();
    await expect(logicRule).toBeChecked({ checked: before });
  });

  test('companion_export_modal_open_preview', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await openCompanionProject(page, request, COMPANION_SLUG);
    await page.getByTestId('export-btn').click();
    await expect(page.getByTestId('creator-export-modal')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('export-preview-btn').click();
    await expect(page.getByTestId('export-preview-text')).toBeVisible({ timeout: 15_000 });
    await page.getByTestId('export-modal-close').click();
    await expect(page.getByTestId('creator-export-modal')).toBeHidden({ timeout: 10_000 });
    await restoreCreatorProject(request);
  });

  test('companion_micro_task_bar_on_write_desk', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await openCompanionProject(page, request, COMPANION_SLUG);
    const bar = page.getByTestId('write-micro-task-bar');
    await expect(bar).toBeVisible({ timeout: 30_000 });
    await expect(bar).toContainText(/再写|已达标/);
    await expect(bar.getByRole('progressbar')).toBeVisible();
    await expect(page.getByTestId('write-micro-task-fill')).toBeAttached();
    await restoreCreatorProject(request);
  });
});
