// Product tools live e2e — 故事结构图 + 介入规则 UI（矩阵 §9 MVP）
import { test, expect } from '@playwright/test';
import { skipUnlessLive } from './helpers/live-backend.js';
import { dismissDeskDrawerIfOpen, openPulseDrawer } from './helpers/companion-project.js';

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
});
