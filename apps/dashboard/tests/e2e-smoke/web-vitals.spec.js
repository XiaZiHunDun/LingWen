// apps/dashboard/tests/perf/web-vitals.spec.js — Phase 76 Web Vitals baseline
// Uses bundled Chromium + PerformanceObserver to measure Core Web Vitals.

import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ARTIFACTS_DIR = path.resolve(__dirname, '../../../../docs/perf/playwright');

const ROUTES = ['', 'creator', 'studio', 'production'];
const RUNS_PER_ROUTE = 3;

test.describe('Web Vitals baseline (Phase 76)', () => {
  for (const route of ROUTES) {
    for (let run = 1; run <= RUNS_PER_ROUTE; run++) {
      const slug = route || 'landing';
      const url = `/${route}`;

      test(`${slug} run ${run}`, async ({ page, baseURL }) => {
        // Capture console messages for debugging
        const consoleMsgs = [];
        page.on('console', (msg) => consoleMsgs.push(`[${msg.type()}] ${msg.text()}`));
        page.on('pageerror', (err) => consoleMsgs.push(`[error] ${err.message}`));

        // Inject PerformanceObserver before navigation
        await page.addInitScript(() => {
          window.__perfMetrics = {
            lcp: null,
            cls: null,
            fcp: null,
            tbt: 0,
            inp: null,
          };

          // LCP observer
          new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const last = entries[entries.length - 1];
            window.__perfMetrics.lcp = last.startTime;
          }).observe({ type: 'largest-contentful-paint', buffered: true });

          // CLS observer
          let clsValue = 0;
          new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              if (!entry.hadRecentInput) clsValue += entry.value;
            }
            window.__perfMetrics.cls = clsValue;
          }).observe({ type: 'layout-shift', buffered: true });

          // FCP via paint timing
          new PerformanceObserver((list) => {
            for (const entry of list.getEntries()) {
              if (entry.name === 'first-contentful-paint') {
                window.__perfMetrics.fcp = entry.startTime;
              }
            }
          }).observe({ type: 'paint', buffered: true });

          // INP via event timing (record last interaction)
          new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const last = entries[entries.length - 1];
            if (last) {
              window.__perfMetrics.inp = last.processingEnd - last.startTime;
            }
          }).observe({ type: 'event', buffered: true, durationThreshold: 16 });
        });

        // Navigate (SPA needs networkidle for route-specific render)
        await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });

        // Synthetic interaction for INP
        await page.evaluate(() => {
          const target = document.querySelector('button, a, [role="button"]');
          if (target) target.click();
        });

        // Wait for metrics to settle (SPA needs extra time)
        await page.waitForTimeout(3000);

        // Collect final metrics
        const metrics = await page.evaluate(() => {
          const longtasks = performance.getEntriesByType('longtask');
          const tbt = longtasks.reduce(
            (sum, t) => sum + Math.max(0, t.duration - 50),
            0
          );
          return {
            ...window.__perfMetrics,
            tbt,
          };
        });

        // Save JSON artifact
        fs.mkdirSync(ARTIFACTS_DIR, { recursive: true });
        const filename = `${slug}-run${run}.json`;
        fs.writeFileSync(
          path.join(ARTIFACTS_DIR, filename),
          JSON.stringify(
            {
              route: url,
              slug,
              run,
              timestamp: new Date().toISOString(),
              metrics,
            },
            null,
            2
          )
        );

        // Log metrics for debugging
        console.log(`[${slug} run ${run}]`, JSON.stringify(metrics));

        // Debug: log console messages if content missing
        const bodyText = await page.evaluate(() => document.body.innerText.length);
        if (bodyText === 0) {
          console.log(`[${slug} run ${run}] CONSOLE LOGS:`);
          for (const m of consoleMsgs.slice(0, 20)) console.log('  ', m);
        }

        // Sanity: route content rendered
        expect(bodyText).toBeGreaterThan(0);
      });
    }
  }
});
