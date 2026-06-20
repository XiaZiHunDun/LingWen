// Phase 9.65 F56: helpers for Playwright live-backend e2e (opt-in).
import { execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { expect } from '@playwright/test';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const NOVEL_FACTORY_ROOT = path.resolve(__dirname, '../../../../..');

export const LIVE_E2E_ENABLED = process.env.LINGWEN_E2E_LIVE === '1';

export function skipUnlessLive(test) {
  test.skip(!LIVE_E2E_ENABLED, 'set LINGWEN_E2E_LIVE=1 to run live-backend e2e');
}

export function runE2eSeed(args) {
  execSync(`python -m infra.cross_volume.e2e_seed ${args}`, {
    cwd: NOVEL_FACTORY_ROOT,
    stdio: 'pipe',
    timeout: 30_000,
    env: { ...process.env },
  });
}

export function resetRipple(rippleId, toStatus) {
  runE2eSeed(`reset-ripple ${rippleId} ${toStatus}`);
}

export function resetE2eDecision() {
  runE2eSeed('reset-decision');
}

export async function clickNav(page, label) {
  await page.getByRole('link', { name: label }).click();
}

export async function waitForPendingDecisionCard(page, timeout = 30_000) {
  await page.getByTestId('decision-card').waitFor({ state: 'visible', timeout });
}

/** Wait until ripple list finished initial fetch (loading hidden). */
export async function waitForRippleListReady(page, timeout = 30_000) {
  const loading = page.getByTestId('ripple-list-loading');
  if (await loading.isVisible().catch(() => false)) {
    await loading.waitFor({ state: 'hidden', timeout });
  }
  await page
    .getByTestId('ripple-card')
    .first()
    .or(page.getByTestId('ripple-list-empty'))
    .waitFor({ timeout });
}

/** Open first ripple drawer after list + detail fetch complete. */
export async function openFirstRippleDrawer(page) {
  await waitForRippleListReady(page);
  for (let attempt = 0; attempt < 2; attempt += 1) {
    const detailResponse = page.waitForResponse(
      (resp) =>
        resp.url().includes('/api/cvg/ripples/') &&
        resp.request().method() === 'GET' &&
        resp.status() === 200,
      { timeout: 30_000 },
    );
    await page.getByTestId('ripple-card').first().click();
    try {
      await detailResponse;
      await expect(page.getByTestId('ripple-drawer')).toBeVisible({ timeout: 15_000 });
      return;
    } catch (err) {
      if (attempt === 1) throw err;
      await page.keyboard.press('Escape').catch(() => {});
    }
  }
}
