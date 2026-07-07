import { test, expect } from '@playwright/test';
import { clickNav, skipUnlessLive } from './helpers/live-backend.js';
import { CREATOR_SLUG, restoreCreatorProject } from './helpers/companion-project.js';

test.describe('Cascade runs flow (live)', () => {
  test.afterEach(async ({ request }) => {
    await restoreCreatorProject(request, CREATOR_SLUG);
  });

  test('advance_more_cascade_runs_reachable', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: CREATOR_SLUG } });

    await page.goto('/?nav=more', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('more-page')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('more-link-cascade-runs')).toBeVisible({ timeout: 15_000 });

    await page.getByTestId('more-link-cascade-runs').click();
    await expect(page.getByTestId('cascade-runs-page')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('cascade-runs-panel')).toBeVisible();
  });

  test('cascade_runs_deep_link', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(60_000);
    await request.put('/api/studio/active', { data: { slug: CREATOR_SLUG } });

    await page.goto('/?nav=cascade-runs', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('cascade-runs-page')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('cascade-runs-filter')).toBeVisible();
  });

  test('cascade_runs_from_sidebar_more', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: CREATOR_SLUG } });

    await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
    await clickNav(page, '工具箱');
    await page.getByTestId('more-link-cascade-runs').click();
    await expect(page.getByTestId('cascade-runs-page')).toBeVisible({ timeout: 30_000 });
  });

  test('cascade_runs_replay_shows_graph', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: CREATOR_SLUG } });

    await page.route('**/api/cascade/runs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          runs: [
            {
              id: 42,
              ripple_id: 'rip-pending-1',
              status: 'completed',
              algorithm: 'bfs',
              max_depth: 2,
              started_at: '2026-07-07T00:00:00Z',
            },
          ],
          total: 1,
        }),
      });
    });

    await page.route('**/api/ripples/cascade/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          trigger_ripple_id: 'rip-pending-1',
          cascade_nodes: [{ id: 'n1', label: 'E2E' }],
          cascade_edges: [],
          cascade_actions: [],
          depth_reached: 2,
          generated_at: '2026-07-07T00:00:00Z',
          bfs_algorithm_version: 'e2e',
        }),
      });
    });

    await page.goto('/?nav=cascade-runs', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('cascade-runs-table')).toBeVisible({ timeout: 30_000 });
    await page.getByTestId('replay-btn').first().click();
    await expect(page.getByTestId('cascade-runs-replay')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('replay-graph')).toBeVisible();
  });

  test('cascade_runs_replay_live_backend', async ({ page, request }) => {
    skipUnlessLive(test);
    test.setTimeout(90_000);
    await request.put('/api/studio/active', { data: { slug: CREATOR_SLUG } });

    // Runs list is live (e2e_seed.ensure_e2e_cascade_run). Replay read uses BFS;
    // e2e harness has no CVG graph — mock persist=false only.
    await page.route('**/api/ripples/cascade/**', async (route) => {
      if (!route.request().url().includes('persist=false')) {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          trigger_ripple_id: 'rip-pending-1',
          cascade_nodes: [{ id: 'n1', label: 'E2E live' }],
          cascade_edges: [],
          cascade_actions: [],
          depth_reached: 1,
          generated_at: '2026-07-07T00:00:00Z',
          bfs_algorithm_version: 'e2e',
        }),
      });
    });

    await page.goto('/?nav=cascade-runs', { waitUntil: 'domcontentloaded' });
    await expect(page.getByTestId('cascade-runs-table')).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId('cascade-run-row').first()).toBeVisible();
    await page.getByTestId('replay-btn').first().click();
    await expect(page.getByTestId('cascade-runs-replay')).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId('replay-graph')).toBeVisible();
    await expect(page.getByTestId('cascade-graph')).toBeVisible({ timeout: 15_000 });
  });
});
