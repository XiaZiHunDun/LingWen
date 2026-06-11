// dashboard/frontend/tests/e2e-smoke/cascade-runs-filter.spec.js — Phase 9.23 T6
// Playwright e2e smoke tests for cascade runs filter UI (2 tests, 0 network, 0 LLM).
// Mirror cascade-runs-panel.spec.js pattern: page.route mock REST + block WS.
// Phase 9.23 cascade_runs endpoint mock 增强: 读 ?status= query param 并返不同
// payload (cancelled → 1 cancelled row, default → 1 completed row). 验证 filter
// dropdown → URL (window.history.replaceState) → fetchCascadeRuns → 1 new row.
//
// Testids: cascade-runs-filter, filter-status, filter-algorithm, filter-min-depth,
//   filter-max-depth, filter-reset, cascade-runs-table, cascade-run-row, status-badge-{status},
//   ripple-drawer, ripple-card, tab-cascade-runs.
//
// 2 case:
//   - status_filter_dropdown_changes_table_rows_and_updates_url
//   - deep_link_with_?status=cancelled_preserves_filter_on_mount

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

const FAKE_RUNS_COMPLETED = [
  { id: 1, ripple_id: 'rip-1', started_at: '2026-06-11T10:00:00Z', completed_at: '2026-06-11T10:00:05Z',
    max_depth: 3, depth_reached: 2, status: 'completed', algorithm_version: 'v2_weighted',
    cascade_nodes: [], cascade_edges: [], cascade_actions: [] },
];

const FAKE_RUNS_CANCELLED = [
  { id: 7, ripple_id: 'rip-1', started_at: '2026-06-11T11:00:00Z', completed_at: '2026-06-11T11:00:01Z',
    max_depth: 4, depth_reached: 1, status: 'cancelled', algorithm_version: 'v2_weighted',
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
  // Mock Phase 9.20 cascade_runs endpoints — query-param aware
  // BASE_URL is http://localhost:8765/api and api methods use relative paths
  // `/ripples/cascade/...` (no leading /api), so the actual request URL is
  // http://localhost:8765/api/ripples/cascade/rip-1/runs?status=... — single
  // /api prefix, matching the FastAPI backend. ?status=cancelled → cancelled
  // rows, anything else (or no status) → completed rows (sibling 既 contract).
  await page.route('**/api/ripples/cascade/**', async (route, request) => {
    const url = new URL(request.url());
    const path = url.pathname;
    if (path === '/api/ripples/cascade/rip-1/runs') {
      const status = url.searchParams.get('status');
      const body = status === 'cancelled' ? FAKE_RUNS_CANCELLED : FAKE_RUNS_COMPLETED;
      return route.fulfill({ status: 200, contentType: 'application/json',
        body: JSON.stringify(body) });
    }
    if (path === '/api/ripples/cascade/rip-1') {
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
  // Click 涟漪 (Ripples) sidebar nav item (mirror sibling spec)
  await page.locator('a.nav-item:has-text("涟漪")').click();
  await page.waitForSelector('[data-testid="ripple-filter-status"]', { timeout: 5000 });
  await page.waitForSelector('[data-testid="ripple-card"]', { timeout: 5000 });
}

test.describe('Phase 9.23: cascade runs filter e2e', () => {
  test('status_filter_dropdown_changes_table_rows_and_updates_url', async ({ page }) => {
    await installApiMocks(page);
    await gotoRipplesPage(page);
    // Open drawer → Cascade runs tab
    await page.locator('[data-testid="ripple-card"]').first().click();
    await page.waitForSelector('[data-testid="ripple-drawer"]', { timeout: 3000 });
    await page.locator('[data-testid="tab-cascade-runs"]').click();
    await page.waitForSelector('[data-testid="cascade-runs-filter"]', { timeout: 3000 });
    // Initial: 1 completed row (no ?status= filter yet)
    await page.waitForSelector('[data-testid="cascade-runs-table"]', { timeout: 3000 });
    const rows = page.locator('[data-testid="cascade-run-row"]');
    await expect(rows).toHaveCount(1);
    await expect(page.locator('[data-testid="status-badge-completed"]')).toBeVisible();
    // Select cancelled → URL should update with ?status=cancelled + table re-fetches
    await page.locator('[data-testid="filter-status"]').selectOption('cancelled');
    await expect(page).toHaveURL(/status=cancelled/);
    // Table re-renders with the cancelled row (id=7)
    await expect(page.locator('[data-testid="status-badge-cancelled"]')).toBeVisible();
    await expect(page.locator('[data-testid="cascade-run-row"]')).toHaveCount(1);
    await expect(page.locator('[data-testid="cascade-run-row"]').first()).toHaveAttribute('data-run-id', '7');
  });

  test('deep_link_with_?status=cancelled_preserves_filter_on_mount', async ({ page }) => {
    await installApiMocks(page);
    // Deep link with ?status=cancelled — vitest 既 3 个 T5b tests 验证
    // CascadeRunsPanel onMount 读 window.location.search → 调 fetchCascadeRuns with
    // { status: 'cancelled' } → mock 返 1 cancelled row. e2e 验证 mount 后
    // dropdown + table 反映 URL 状态.
    await page.goto('/?status=cancelled');
    await page.locator('a.nav-item:has-text("涟漪")').click();
    await page.waitForSelector('[data-testid="ripple-card"]', { timeout: 5000 });
    await page.locator('[data-testid="ripple-card"]').first().click();
    await page.waitForSelector('[data-testid="ripple-drawer"]', { timeout: 3000 });
    await page.locator('[data-testid="tab-cascade-runs"]').click();
    await page.waitForSelector('[data-testid="cascade-runs-filter"]', { timeout: 3000 });
    // Status dropdown reflects URL state on mount
    const statusSelect = page.locator('[data-testid="filter-status"]');
    await expect(statusSelect).toHaveValue('cancelled');
    // Table renders the filtered cancelled row (id=7) — the fetch with ?status=
    // must have hit the mock and returned FAKE_RUNS_CANCELLED
    await page.waitForSelector('[data-testid="cascade-runs-table"]', { timeout: 3000 });
    await expect(page.locator('[data-testid="cascade-run-row"]')).toHaveCount(1);
    await expect(page.locator('[data-testid="status-badge-cancelled"]')).toBeVisible();
    await expect(page.locator('[data-testid="cascade-run-row"]').first()).toHaveAttribute('data-run-id', '7');
  });
});
