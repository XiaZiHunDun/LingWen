// Phase 9.65 F56: helpers for Playwright live-backend e2e (opt-in).
import { execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const NOVEL_FACTORY_ROOT = path.resolve(__dirname, '../../../../../..');

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
