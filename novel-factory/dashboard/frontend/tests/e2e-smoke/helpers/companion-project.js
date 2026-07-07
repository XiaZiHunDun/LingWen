import { expect } from '@playwright/test';
import { waitForPaintSettle } from '../../visual-audit/helpers/capture-ui-audit.js';

export const COMPANION_SLUG = 'e2e-live-companion';
export const CREATOR_SLUG = 'e2e-live-creator';
export const STUDIO_SLUG = 'e2e-live-studio';
export const WRITE_RESUME_KEY = 'lingwen.writeResume.v1';

/** Activate companion fixture project and open write workbench. */
export async function openCompanionProject(page, request, slug = COMPANION_SLUG) {
  await request.put('/api/studio/active', { data: { slug } });
  await page.goto('/?nav=write', { waitUntil: 'domcontentloaded' });
  await expect(page.getByTestId('creator-write-workbench')).toBeVisible({ timeout: 30_000 });
}

/** Select chapter by row test id (e.g. chapter-row-1). */
export async function selectChapter(page, rowTestId = 'chapter-row-1') {
  await page.getByTestId(rowTestId).click();
  await expect(page.getByTestId('chapter-body-textarea')).toBeAttached({ timeout: 15_000 });
}

/** Expand advanced tools + agent strip for agent input. */
export async function openAdvancedTools(page) {
  await page.getByTestId('write-advanced-tools').locator('summary').click();
  await page.getByTestId('write-agent-strip').locator('summary').click();
  await expect(page.getByTestId('write-agent-input')).toBeVisible({ timeout: 10_000 });
}

/** Close desk drawer via backdrop or close control; wait until clicks reach the page. */
export async function dismissDeskDrawerIfOpen(page) {
  const backdrop = page.getByTestId('creator-desk-drawer-backdrop');
  if (await backdrop.isVisible().catch(() => false)) {
    await backdrop.click({ position: { x: 12, y: 12 } });
    await expect(backdrop).toBeHidden({ timeout: 10_000 });
    await waitForPaintSettle(page);
    return;
  }
  const closeDrawer = page.getByTestId('desk-drawer-close-pulse');
  if (await closeDrawer.isVisible().catch(() => false)) {
    await closeDrawer.click();
    await expect(page.getByTestId('column-pulse')).toBeHidden({ timeout: 10_000 }).catch(() => {});
    await waitForPaintSettle(page);
  }
}

/** Scroll into view and click when layout/overlay has settled. */
export async function clickStable(locator) {
  await locator.scrollIntoViewIfNeeded();
  await waitForPaintSettle(locator.page());
  await locator.click();
}

/** Open pulse via desk drawer or legacy tab; wait for column. */
export async function openPulseDrawer(page) {
  const drawerTrigger = page.getByTestId('creator-desk-drawer-pulse');
  const tabPulse = page.getByTestId('creator-workspace-tab-pulse');
  try {
    await drawerTrigger.waitFor({ state: 'visible', timeout: 30_000 });
    await drawerTrigger.click();
  } catch {
    await tabPulse.waitFor({ state: 'visible', timeout: 10_000 });
    await tabPulse.click();
  }
  await expect(page.getByTestId('column-pulse')).toBeVisible({ timeout: 15_000 });
}

/** Close pulse desk drawer when close control is present. */
export async function closePulseDrawer(page) {
  const closeDrawer = page.getByTestId('desk-drawer-close-pulse');
  if (await closeDrawer.isVisible().catch(() => false)) {
    await closeDrawer.click();
    await expect(page.getByTestId('column-pulse')).toBeHidden({ timeout: 10_000 });
  }
}

/** Restore default active project after companion tests. */
export async function restoreCreatorProject(request, slug = CREATOR_SLUG) {
  await request.put('/api/studio/active', { data: { slug } });
}

/** Set write-resume localStorage for landing tests. */
export async function setWriteResume(page, slug, chapter = 1) {
  await page.addInitScript(
    ({ key, slug: s, chapter: ch }) => {
      localStorage.setItem(key, JSON.stringify({ [s]: { chapter: ch, at: Date.now() } }));
    },
    { key: WRITE_RESUME_KEY, slug, chapter },
  );
}

/** Clear write-resume localStorage before landing tests. */
export async function clearWriteResume(page) {
  await page.addInitScript((key) => {
    localStorage.removeItem(key);
  }, WRITE_RESUME_KEY);
}
