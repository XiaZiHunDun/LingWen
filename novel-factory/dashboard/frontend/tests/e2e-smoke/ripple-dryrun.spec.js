// dashboard/frontend/tests/e2e-smoke/ripple-dryrun.spec.js — Phase 9.15 T4
// E2E smoke tests for ripple dry-run mode + apply confirm modal flow.
// 3 tests, 0 LLM, 0 real backend (use page.route mock 跟 Phase 8.13 cost
// bar chart 1:1 pattern; vitest 单测已覆盖真实 backend 集成).
//
// Critical: App.vue has NO router — activeNav is hardcoded to 'overview'.
// Tests must click the 涟漪 sidebar nav (Chinese: "Ripples") to reach
// the RipplesPage, then click ripple-card to open RippleDrawer.
//
// Mocked API endpoints:
//   GET /api/cvg/ripples → 1 pending ripple fixture (rip-1)
//   GET /api/cvg/ripples/rip-1 → detail
//   GET /api/cvg/ripples/stats → 1 total
//   GET /api/cvg/ripples/rip-1/cascade → 2 nodes / 1 edge / 1 action
//   GET /api/cvg/ripples/rip-1/cascade/preview → counts (1/0/0/1)
//
// Testids: ripple-card (Phase 9.13), ripple-drawer-* (Phase 9.13/9.14),
//   dry-run-toggle / ripple-summary-chips / cascade-graph (T4 new),
//   apply-confirm-modal / apply-confirm-cancel / apply-confirm-apply (T4 new).

import { test, expect } from '../_setup.js';

const FAKE_RIPPLE = {
  ripple_id: 'rip-1',
  dimension: 'character',
  relationship_type: 'causes',
  source_chapter: 5,
  target_chapter: 10,
  status: 'pending',
  confidence: 4,
  created_at: '2026-06-10T12:00:00Z',
  evidence: 'mock evidence',
  source_payload: {},
  edge_payload: {},
};

const FAKE_CASCADE = {
  trigger_ripple_id: 'rip-1',
  cascade_nodes: [
    { id: 'n-trigger', dimension: 'character', volume: 1, chapter: 5, title: 'trigger', description: '', payload: {} },
    { id: 'n-down', dimension: 'character', volume: 1, chapter: 10, title: 'downstream', description: '', payload: {} },
  ],
  cascade_edges: [
    { id: 'e1', from_node_id: 'n-trigger', to_node_id: 'n-down', relationship_type: 'causes', weight: 0.9, payload: {} },
  ],
  cascade_actions: [
    { action: 'propagate', from: 'n-trigger', to: 'n-down', depth: 1, weight: 0.9 },
  ],
  depth_reached: 1,
  generated_at: '2026-06-10T12:00:00+00:00',
  bfs_algorithm_version: 'v1',
};

const FAKE_PREVIEW = {
  ripple_id: 'rip-1',
  affected_chapter_count: 1,
  affected_character_count: 1,
  affected_setting_count: 0,
  estimated_change_count: 1,
  cascade_node_count: 2,
  cascade_edge_count: 1,
  max_depth: 1,
};

async function installApiMocks(page) {
  // Mock ripples list (with status filter support)
  await page.route('**/api/cvg/ripples**', async (route, request) => {
    const url = new URL(request.url());
    const path = url.pathname;
    if (path === '/api/cvg/ripples/stats') {
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ total: 1, by_status: { pending: 1 }, by_volume: { 1: 1 } }) });
    }
    if (path === '/api/cvg/ripples') {
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify([FAKE_RIPPLE]) });
    }
    if (path === '/api/cvg/ripples/rip-1') {
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify(FAKE_RIPPLE) });
    }
    if (path === '/api/cvg/ripples/rip-1/cascade') {
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify(FAKE_CASCADE) });
    }
    if (path === '/api/cvg/ripples/rip-1/cascade/preview') {
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify(FAKE_PREVIEW) });
    }
    return route.continue();
  });
  // Block WS connections so we don't pollute test logs
  await page.route('**/api/ws/**', route => route.abort());
}

// Helper: navigate from app root to the ripples page via sidebar click
async function gotoRipplesPage(page) {
  await page.goto('/');
  // Click the 涟漪 (Ripples) sidebar nav item to set activeNav
  await page.locator('a.nav-item:has-text("涟漪")').click();
  // Wait for RipplesPage to mount + store.refresh() to finish
  await page.waitForSelector('[data-testid="ripple-filter-status"]', { timeout: 5000 });
  // Wait for the (mocked) ripple card to appear
  await page.waitForSelector('[data-testid="ripple-card"]', { timeout: 5000 });
}

test.describe('Phase 9.15: ripple dry-run + apply confirm e2e', () => {
  test('dry-run button toggles cascade preview section', async ({ page }) => {
    await installApiMocks(page);
    await gotoRipplesPage(page);
    // Open drawer
    await page.locator('[data-testid="ripple-card"]').first().click();
    await page.waitForSelector('[data-testid="ripple-drawer"]', { timeout: 3000 });
    // Dry-run section is visible (toggle inside it)
    const dryRunSection = page.locator('[data-testid="ripple-dryrun-section"]');
    await expect(dryRunSection).toBeVisible();
    const toggle = page.locator('[data-testid="dry-run-toggle"]');
    await expect(toggle).toBeVisible();
    // Click toggle to expand
    await toggle.click();
    // Summary chips appear (4 chips: depth + affected chapters/characters/settings)
    const chips = page.locator('[data-testid="ripple-summary-chips"]');
    await expect(chips).toBeVisible();
    // Cascade graph (mocked fixture has 2 nodes) — graph element should be visible
    const graph = page.locator('[data-testid="cascade-graph"]');
    await expect(graph).toBeVisible({ timeout: 3000 });
  });

  test('apply button shows confirmation modal with 4 chips', async ({ page }) => {
    await installApiMocks(page);
    await gotoRipplesPage(page);
    // Open drawer
    await page.locator('[data-testid="ripple-card"]').first().click();
    await page.waitForSelector('[data-testid="ripple-drawer"]');
    // Click apply
    await page.locator('[data-testid="ripple-drawer-apply"]').click();
    // Confirmation modal appears
    const modal = page.locator('[data-testid="apply-confirm-modal"]');
    await expect(modal).toBeVisible({ timeout: 3000 });
    // 4 chip counts visible
    await expect(page.locator('[data-testid="apply-confirm-chapter-count"]')).toBeVisible();
    await expect(page.locator('[data-testid="apply-confirm-character-count"]')).toBeVisible();
    await expect(page.locator('[data-testid="apply-confirm-setting-count"]')).toBeVisible();
    await expect(page.locator('[data-testid="apply-confirm-change-count"]')).toBeVisible();
  });

  test('apply modal cancel button closes modal without applying', async ({ page }) => {
    await installApiMocks(page);
    await gotoRipplesPage(page);
    await page.locator('[data-testid="ripple-card"]').first().click();
    await page.waitForSelector('[data-testid="ripple-drawer"]');
    // Open confirm modal
    await page.locator('[data-testid="ripple-drawer-apply"]').click();
    const modal = page.locator('[data-testid="apply-confirm-modal"]');
    await expect(modal).toBeVisible({ timeout: 3000 });
    // Click cancel
    await page.locator('[data-testid="apply-confirm-cancel"]').click();
    // Modal closes
    await expect(modal).not.toBeVisible();
    // Drawer still open (cancel did not navigate away)
    await expect(page.locator('[data-testid="ripple-drawer"]')).toBeVisible();
  });
});
