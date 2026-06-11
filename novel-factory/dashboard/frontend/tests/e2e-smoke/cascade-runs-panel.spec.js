// dashboard/frontend/tests/e2e-smoke/cascade-runs-panel.spec.js — Phase 9.22 T4
// Playwright e2e smoke tests for cascade runs panel (2 tests, 0 network, 0 LLM).
// Mirror cascade-realtime.spec.js pattern: page.route mock REST endpoints +
// block WS. Mocked API: Phase 9.20 /api/ripples/cascade/{id}/runs +
// /api/ripples/cascade/{id}?max_depth=N (Replay read-only path).
//
// Testids: tab-cascade-runs, cascade-runs-table, cascade-run-row, replay-btn,
//   cancel-btn, status-badge-{running,completed,cancelled}, cascade-runs-replay,
//   replay-graph, ripple-drawer, ripple-card.
//
// 2 case:
//   - panel_displays_runs_table_with_replay_and_cancel_buttons
//   - click_replay_renders_cascade_graph_below_table

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

const FAKE_RUNS = [
  { id: 1, ripple_id: 'rip-1', started_at: '2026-06-11T10:00:00Z', completed_at: '2026-06-11T10:00:05Z',
    max_depth: 3, depth_reached: 2, status: 'completed', algorithm_version: 'v2_weighted',
    cascade_nodes: [], cascade_edges: [], cascade_actions: [] },
  { id: 2, ripple_id: 'rip-1', started_at: '2026-06-11T11:00:00Z', completed_at: null,
    max_depth: 5, depth_reached: 0, status: 'running', algorithm_version: 'v2_weighted',
    cascade_nodes: [], cascade_edges: [], cascade_actions: [] },
];

const FAKE_REPLAY_CASCADE = {
  trigger_ripple_id: 'rip-1',
  cascade_nodes: [
    { id: 'n1', dimension: 'character', volume: 1, chapter: 1, title: 't', description: '', payload: {} },
  ],
  cascade_edges: [],
  cascade_actions: [],
  depth_reached: 1,
  generated_at: '2026-06-11T12:00:00Z',
  bfs_algorithm_version: 'v2_weighted',
};

async function installApiMocks(page) {
  // Mock legacy Phase 9.15 endpoints (drawer 仍 loadCascade/loadCascadePreview)
  await page.route('**/api/cvg/ripples**', async (route, request) => {
    const url = new URL(request.url());
    const path = url.pathname;
    if (path === '/api/cvg/ripples') {
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify([FAKE_RIPPLE]) });
    }
    if (path === '/api/cvg/ripples/stats') {
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ total: 1, by_status: { pending: 1 }, by_volume: { 1: 1 } }) });
    }
    if (path === '/api/cvg/ripples/rip-1') {
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify(FAKE_RIPPLE) });
    }
    if (path === '/api/cvg/ripples/rip-1/cascade') {
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ trigger_ripple_id: 'rip-1', cascade_nodes: [], cascade_edges: [],
          cascade_actions: [], depth_reached: 0, generated_at: '2026-06-11T10:00:00Z', bfs_algorithm_version: 'v2_weighted' }) });
    }
    if (path === '/api/cvg/ripples/rip-1/cascade/preview') {
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify({ ripple_id: 'rip-1', affected_chapter_count: 0, affected_character_count: 0,
          affected_setting_count: 0, estimated_change_count: 0, cascade_node_count: 0, cascade_edge_count: 0, max_depth: 0 }) });
    }
    if (path === '/api/cvg/ripples/rip-1/audit') {
      return route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) });
    }
    return route.continue();
  });
  // Mock Phase 9.20 cascade_runs endpoints
  // NOTE: BASE_URL is http://localhost:8765/api and fetchCascadeRuns path
  // starts with `/api/ripples/...`, so actual request URL has double `/api`
  // prefix: http://localhost:8765/api/api/ripples/cascade/rip-1/runs
  await page.route('**/api/ripples/cascade/**', async (route, request) => {
    const url = new URL(request.url());
    const path = url.pathname;
    if (path === '/api/api/ripples/cascade/rip-1/runs') {
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify(FAKE_RUNS) });
    }
    if (path === '/api/api/ripples/cascade/rip-1') {
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify(FAKE_REPLAY_CASCADE) });
    }
    return route.continue();
  });
  // Block WS connections so we don't pollute test logs
  await page.route('**/api/ws/**', route => route.abort());
}

async function gotoRipplesPage(page) {
  await page.goto('/');
  // Click 涟漪 (Ripples) sidebar nav item (mirror cascade-realtime.spec.js)
  await page.locator('a.nav-item:has-text("涟漪")').click();
  await page.waitForSelector('[data-testid="ripple-filter-status"]', { timeout: 5000 });
  await page.waitForSelector('[data-testid="ripple-card"]', { timeout: 5000 });
}

test.describe('Phase 9.22: cascade runs panel e2e', () => {
  test('panel_displays_runs_table_with_replay_and_cancel_buttons', async ({ page }) => {
    await installApiMocks(page);
    await gotoRipplesPage(page);
    // Open drawer
    await page.locator('[data-testid="ripple-card"]').first().click();
    await page.waitForSelector('[data-testid="ripple-drawer"]', { timeout: 3000 });
    // Click Cascade runs tab
    await page.locator('[data-testid="tab-cascade-runs"]').click();
    await page.waitForSelector('[data-testid="cascade-runs-panel"]', { timeout: 3000 });
    // Table renders with 2 rows
    const rows = page.locator('[data-testid="cascade-run-row"]');
    await expect(rows).toHaveCount(2);
    // Status badges: 1 completed, 1 running
    await expect(page.locator('[data-testid="status-badge-completed"]')).toBeVisible();
    await expect(page.locator('[data-testid="status-badge-running"]')).toBeVisible();
    // Replay button on every row
    const replayBtns = page.locator('[data-testid="replay-btn"]');
    await expect(replayBtns).toHaveCount(2);
    // Cancel button ONLY on running row
    const cancelBtns = page.locator('[data-testid="cancel-btn"]');
    await expect(cancelBtns).toHaveCount(1);
  });

  test('click_replay_renders_cascade_graph_below_table', async ({ page }) => {
    await installApiMocks(page);
    await gotoRipplesPage(page);
    await page.locator('[data-testid="ripple-card"]').first().click();
    await page.waitForSelector('[data-testid="ripple-drawer"]', { timeout: 3000 });
    // Click Cascade runs tab
    await page.locator('[data-testid="tab-cascade-runs"]').click();
    await page.waitForSelector('[data-testid="cascade-runs-panel"]', { timeout: 3000 });
    // Click Replay on the 2nd row (running, max_depth=5)
    const rows = page.locator('[data-testid="cascade-run-row"]');
    await rows.nth(1).locator('[data-testid="replay-btn"]').click();
    // Replay section + cascade graph appear below table
    await expect(page.locator('[data-testid="cascade-runs-replay"]')).toBeVisible();
    await expect(page.locator('[data-testid="replay-graph"]')).toBeVisible();
    // Replay note mentions run #2
    const replayNote = page.locator('[data-testid="replay-note"]');
    await expect(replayNote).toContainText('#2');
  });
});
