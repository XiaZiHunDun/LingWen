// Visual audit helpers — screenshots + structured layout metrics for AI/human review.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const VISUAL_AUDIT_OUTPUT_DIR = path.resolve(__dirname, '../output');

/** 伴侣书桌审计前：折叠入门向导与写作工具，避免截图被向导遮挡 */
export async function prepareCreatorDeskForAudit(page) {
  const wizard = page.locator('[data-testid="onboarding-wizard-panel"]');
  if (await wizard.isVisible().catch(() => false)) {
    const isOpen = await wizard.evaluate((el) => /** @type {HTMLDetailsElement} */ (el).open);
    if (isOpen) {
      await wizard.locator('summary').click();
      await page.waitForTimeout(200);
    }
  }
  const advanced = page.locator('[data-testid="write-advanced-tools"]');
  if (await advanced.isVisible().catch(() => false)) {
    const isOpen = await advanced.evaluate((el) => /** @type {HTMLDetailsElement} */ (el).open);
    if (isOpen) {
      await advanced.locator('summary').click();
      await page.waitForTimeout(200);
    }
  }
}

/** @typedef {{ pageId: string, url: string, capturedAt: string, viewport: { width: number, height: number } | null, screenshot: string, metrics: object }} VisualAuditEntry */

/**
 * Collect scroll/overflow/layout metrics from key shell selectors.
 * @param {import('@playwright/test').Page} page
 */
export async function collectUiMetrics(page) {
  return page.evaluate(() => {
    const scrollSelectors = [
      '[data-testid="app-root"]',
      '.main-wrapper',
      '.main-content',
      '.creator-page',
      '.creator-page__body',
      '.write-workbench',
      '.write-workbench__main',
      '.write-workbench__left',
      '.pulse-desk',
      '.pulse-desk__scroll',
      '.l1-page__body',
      '.ask-page__panel',
    ];

    /** @param {Element} el */
    function regionMetrics(el, selector) {
      const style = getComputedStyle(el);
      return {
        selector,
        scrollHeight: el.scrollHeight,
        clientHeight: el.clientHeight,
        scrollWidth: el.scrollWidth,
        clientWidth: el.clientWidth,
        overflowY: style.overflowY,
        overflowX: style.overflowX,
        isScrollableY: el.scrollHeight > el.clientHeight + 2,
        isScrollableX: el.scrollWidth > el.clientWidth + 2,
        rect: {
          top: Math.round(el.getBoundingClientRect().top),
          left: Math.round(el.getBoundingClientRect().left),
          width: Math.round(el.getBoundingClientRect().width),
          height: Math.round(el.getBoundingClientRect().height),
          bottom: Math.round(el.getBoundingClientRect().bottom),
        },
      };
    }

    const scrollRegions = scrollSelectors.map((selector) => {
      const el = document.querySelector(selector);
      if (!el) return { selector, found: false };
      return { found: true, ...regionMetrics(el, selector) };
    });

    const viewport = { width: window.innerWidth, height: window.innerHeight };

    /** Large interactive blocks whose bottom extends below viewport without internal scroll */
    const clippedBelowFold = [];
    document.querySelectorAll('[data-testid]').forEach((el) => {
      const rect = el.getBoundingClientRect();
      if (rect.height < 48) return;
      if (rect.top >= viewport.height) return;
      if (rect.bottom <= viewport.height + 4) return;
      const style = getComputedStyle(el);
      const parentScrollable = el.closest(
        '[style*="overflow"], .pulse-desk__scroll, .write-workbench__editor-slot--primary, .write-workbench__main, .main-wrapper',
      );
      clippedBelowFold.push({
        testId: el.getAttribute('data-testid'),
        tag: el.tagName.toLowerCase(),
        bottom: Math.round(rect.bottom),
        viewportHeight: viewport.height,
        overflowBelow: Math.round(rect.bottom - viewport.height),
        overflowY: style.overflowY,
        hasScrollParent: Boolean(parentScrollable),
      });
    });

    clippedBelowFold.sort((a, b) => b.overflowBelow - a.overflowBelow);

    return {
      viewport,
      documentScrollHeight: document.documentElement.scrollHeight,
      bodyOverflow: getComputedStyle(document.body).overflow,
      scrollRegions,
      clippedBelowFold: clippedBelowFold.slice(0, 15),
      visibleL1TestIds: [...document.querySelectorAll('[data-testid]')]
        .filter((el) => {
          const r = el.getBoundingClientRect();
          return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < viewport.height;
        })
        .map((el) => el.getAttribute('data-testid'))
        .filter(Boolean)
        .slice(0, 40),
    };
  });
}

/**
 * @param {import('@playwright/test').Page} page
 * @param {string} pageId
 * @param {{ fullPage?: boolean, note?: string }} [options]
 * @returns {Promise<VisualAuditEntry>}
 */
export async function capturePageAudit(page, pageId, options = {}) {
  const { fullPage = false, note = '' } = options;
  fs.mkdirSync(VISUAL_AUDIT_OUTPUT_DIR, { recursive: true });

  await page.waitForTimeout(350);

  const metrics = await collectUiMetrics(page);
  const screenshotFile = `${pageId}.png`;
  const screenshotPath = path.join(VISUAL_AUDIT_OUTPUT_DIR, screenshotFile);

  await page.screenshot({ path: screenshotPath, fullPage });

  /** @type {VisualAuditEntry} */
  const entry = {
    pageId,
    note,
    url: page.url(),
    capturedAt: new Date().toISOString(),
    viewport: page.viewportSize(),
    screenshot: screenshotFile,
    metrics,
  };

  fs.writeFileSync(
    path.join(VISUAL_AUDIT_OUTPUT_DIR, `${pageId}.json`),
    `${JSON.stringify(entry, null, 2)}\n`,
    'utf8',
  );

  return entry;
}

/** @param {VisualAuditEntry[]} entries */
export function writeAuditManifest(entries) {
  fs.mkdirSync(VISUAL_AUDIT_OUTPUT_DIR, { recursive: true });
  const manifest = {
    generatedAt: new Date().toISOString(),
    outputDir: VISUAL_AUDIT_OUTPUT_DIR,
    pages: entries.map((e) => ({
      pageId: e.pageId,
      screenshot: e.screenshot,
      metricsFile: `${e.pageId}.json`,
      url: e.url,
      note: e.note,
    })),
    aiReviewHint: 'Read manifest.json, each *.json metrics, and *.png screenshots; prioritize clippedBelowFold and non-scrollable overflow.',
  };
  fs.writeFileSync(
    path.join(VISUAL_AUDIT_OUTPUT_DIR, 'manifest.json'),
    `${JSON.stringify(manifest, null, 2)}\n`,
    'utf8',
  );
}
