# Phase 76 Implementation Plan — Playwright Web Vitals Baseline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate 1 Playwright-based Web Vitals baseline doc for 4 representative dashboard routes (production build). Establishes quantified baseline for Phase 77+ perf optimization.

**Architecture:** Production build + vite preview (port 4173) + Playwright spec (uses bundled Chromium) + PerformanceObserver API for LCP/CLS/FCP/TBT + synthetic click for INP. 4 routes × 3 runs × 5 metrics = 60 measurements → 12 JSON artifacts → 1 baseline doc.

**Tech Stack:** Playwright 1.40+ (project deps), Chromium bundled, Node fs for JSON output, vite preview, vite build, PerformanceObserver API.

**Reference spec**: `docs/superpowers/specs/2026-08-21-phase76-lighthouse-baseline-design.md` (commit `6eac78c5` amendment)

**Pivot note**: Originally spec'd as Lighthouse CLI baseline (commit `9204d2be`), pivoted to Playwright due to sandbox env lacking Chrome binary. Playwright's bundled Chromium = no new dep.

---

## File Structure

| File | Action | Purpose |
|------|--------|---------|
| `apps/dashboard/tests/perf/web-vitals.spec.js` | **Create** (~80 lines) | 12 Playwright tests (4 routes × 3 runs) |
| `docs/perf/playwright-web-vitals-baseline.md` | **Create** (~250 lines) | Baseline doc with 6 sections |
| `docs/perf/playwright/{landing,creator,studio,production}-run{1,2,3}.json` | **Create** (12 files) | Raw metric data per run |

**Total**: 14 new files (1 spec + 1 doc + 12 JSON), 0 modifications.

---

## Task 1: Pre-flight checks

**Files:** None (verification only)

- [ ] **Step 1.1: Verify Playwright available**

Run: `cd apps/dashboard && pnpm exec playwright --version 2>&1 | head -3`
Expected: `Version 1.4x.x`

- [ ] **Step 1.2: Verify Chromium browser available**

Run: `cd apps/dashboard && pnpm exec playwright install --dry-run chromium 2>&1 | head -5`
Expected: Reports Chromium installed (or "needs install" — if so, run `pnpm exec playwright install chromium`)

- [ ] **Step 1.3: Verify port 4173 free**

Run: `lsof -i :4173 2>&1 | head -3 || echo "port 4173 free"`
Expected: Empty (or "port 4173 free")

- [ ] **Step 1.4: Verify dist/ exists (Phase 75 build OK)**

Run: `ls apps/dashboard/dist 2>&1 | head -3 || echo "no dist, need rebuild"`
Expected: `index.html` listed (or "no dist, need rebuild")

---

## Task 2: Create perf test directory

**Files:**
- Create: `apps/dashboard/tests/perf/` (directory)

- [ ] **Step 2.1: Create directory**

Run: `mkdir -p apps/dashboard/tests/perf`

- [ ] **Step 2.2: Verify directory exists**

Run: `ls -la apps/dashboard/tests/perf/`
Expected: empty directory listing (`.` and `..`)

---

## Task 3: Write Playwright spec

**Files:**
- Create: `apps/dashboard/tests/perf/web-vitals.spec.js` (~80 lines)

- [ ] **Step 3.1: Write spec file**

Use Write tool with full content:

```js
// apps/dashboard/tests/perf/web-vitals.spec.js — Phase 76 Web Vitals baseline
// Uses bundled Chromium + PerformanceObserver to measure Core Web Vitals.

import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ARTIFACTS_DIR = path.resolve(__dirname, '../../../docs/perf/playwright');

const ROUTES = ['', 'creator', 'studio', 'production'];
const RUNS_PER_ROUTE = 3;

test.describe('Web Vitals baseline (Phase 76)', () => {
  for (const route of ROUTES) {
    for (let run = 1; run <= RUNS_PER_ROUTE; run++) {
      const slug = route || 'landing';
      const url = `/${route}`;

      test(`${slug} run ${run}`, async ({ page, baseURL }) => {
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

        // Navigate
        await page.goto(url, { waitUntil: 'load' });

        // Synthetic interaction for INP
        await page.evaluate(() => {
          const target = document.querySelector('button, a, [role="button"]');
          if (target) target.click();
        });

        // Wait for metrics to settle
        await page.waitForTimeout(2000);

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

        // Sanity check (LCP should be < 30s even on cold load)
        expect(metrics.lcp).not.toBeNull();
        expect(metrics.lcp).toBeLessThan(30000);
      });
    }
  }
});
```

- [ ] **Step 3.2: Verify file syntax**

Run: `cd apps/dashboard && node -c tests/perf/web-vitals.spec.js 2>&1 || echo "syntax error — recheck file"`
Expected: Empty output (or "syntax error" if file is malformed)

Note: `node -c` only checks syntax, not imports. Real verification happens in Task 7.

---

## Task 4: Production build (verify Phase 75 output still works)

**Files:** None (uses Phase 75 build)

- [ ] **Step 4.1: Verify or rebuild**

Run: `cd apps/dashboard && pnpm run build 2>&1 | tail -10`
Expected: `✓ built in <time>` (or reuse existing `dist/` from Phase 75)

---

## Task 5: Start vite preview server

**Files:** None

- [ ] **Step 5.1: Start preview server in background**

Run:
```bash
cd apps/dashboard
pnpm preview --port 4173 --strictPort &
PREVIEW_PID=$!
echo "PREVIEW_PID=$PREVIEW_PID"
sleep 5
```

Expected: Server starts on port 4173, no port conflict error

- [ ] **Step 5.2: Verify preview server responding**

Run: `curl -sf http://localhost:4173/ -o /dev/null && echo "preview OK" || echo "preview failed"`
Expected: `preview OK`

---

## Task 6: Run Playwright spec (12 tests, 12 JSON artifacts)

**Files:**
- Create: `docs/perf/playwright/{landing,creator,studio,production}-run{1,2,3}.json` (12 files)

- [ ] **Step 6.1: Create artifacts directory**

Run: `mkdir -p docs/perf/playwright`

- [ ] **Step 6.2: Run Playwright spec**

Run:
```bash
cd apps/dashboard
PW_BASE_URL=http://localhost:4173 pnpm exec playwright test \
  tests/perf/web-vitals.spec.js \
  --reporter=line \
  --workers=1 \
  --headed=false \
  2>&1 | tail -30
```

Expected: 12 tests PASS, 12 JSON files in `docs/perf/playwright/`

- [ ] **Step 6.3: Verify 12 JSON artifacts**

Run: `ls docs/perf/playwright/*.json | wc -l`
Expected: `12`

- [ ] **Step 6.4: Spot check 1 JSON file structure**

Run: `cat docs/perf/playwright/landing-run1.json`
Expected: JSON with `{ route, slug, run, timestamp, metrics: { lcp, cls, fcp, tbt, inp } }`

---

## Task 7: Kill preview server

**Files:** None

- [ ] **Step 7.1: Kill preview process**

Run: `kill $PREVIEW_PID 2>/dev/null && echo "preview killed" || echo "preview already gone"`
Expected: `preview killed`

- [ ] **Step 7.2: Verify port 4173 freed**

Run: `lsof -i :4173 2>&1 | head -3 || echo "port 4173 free"`
Expected: `port 4173 free`

---

## Task 8: Generate baseline doc from JSON artifacts

**Files:**
- Create: `docs/perf/playwright-web-vitals-baseline.md`

- [ ] **Step 8.1: Read all 12 JSON artifacts and compute medians**

Run: `cd docs/perf/playwright && for f in *.json; do echo "=== $f ==="; cat "$f"; done`
Expected: 12 JSON outputs (manual review to extract medians)

- [ ] **Step 8.2: Write baseline doc**

Use Write tool with content based on extracted medians. Structure per spec §4:

```markdown
# Playwright Web Vitals Baseline (Phase 76)

> **日期**: 2026-08-21
> **Commit**: e20f516a (master, post-Phase 75)
> **Build**: dist/ via `pnpm run build` (vite production)
> **Methodology**: Playwright 1.40+ × Chromium headless, 3 runs per route, **median**
> **Spec**: apps/dashboard/tests/perf/web-vitals.spec.js

---

## 1. Summary

[Fill based on actual data: X / 4 routes pass all 5 targets]

## 2. Per-route metrics (median of 3 runs)

| Route | LCP | INP | CLS | FCP | TBT | Score |
|-------|-----|-----|-----|-----|-----|-------|
| / (Landing) | _ms | _ms | _ | _ms | _ms | _/100 |
| /creator | _ms | _ms | _ | _ms | _ms | _/100 |
| /studio | _ms | _ms | _ | _ms | _ms | _/100 |
| /production | _ms | _ms | _ | _ms | _ms | _/100 |

## 3. Compliance vs Web Rules Targets

| Metric | Target | / | /creator | /studio | /production |
|--------|--------|---|---------|---------|-------------|
| LCP | < 2.5s | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |
| INP | < 200ms | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |
| CLS | < 0.1 | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |
| FCP | < 1.5s | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |
| TBT | < 200ms | ✓/✗ | ✓/✗ | ✓/✗ | ✓/✗ |

## 4. Bundle Size (from vite build output, Phase 71 reference)

| Chunk | Gzipped | Budget (App page) | Status |
|-------|---------|-------------------|--------|
| vendor | 407kB | < 500kB (soft) | ✓ |
| echarts | 306kB | < 350kB | ✓ |
| cytoscape | 151kB | < 200kB | ✓ |
| mermaid | 390kB | < 450kB | ✓ |
| katex | 78kB | < 100kB | ✓ |
| CreatorPage | 62kB | < 80kB | ✓ |
| index | 22kB | < 30kB | ✓ |

## 5. Top Issues (by priority)

[Fill based on data: rank by severity]

## 6. Phase 77+ Action Items

Based on baseline findings:

- **markRaw/shallowRef opportunities** (485 reactives, 1 file 已 markRaw):
  - 10 chart components 持有 `chartInstance = null` (local `let`, **已最优** — 不需改)
  - `useStudioStore.cacheTimestamps = ref({})` — shallowRef candidate
  - `useCreatorSettings` 18+ refs — 可整合
- **Bundle**:
  - `vendor` 407kB — 检查是否可拆 lodash / moment 等
  - `mermaid` 390kB — 评估是否需 lazy load
- **Code split**:
  - [Fill based on /production CLS findings]

---

## Methodology details

- Playwright 1.40+ with bundled Chromium
- `pnpm run build` + `pnpm preview --port 4173`
- 3 runs per route, median
- PerformanceObserver for LCP/CLS/FCP, longtasks API for TBT
- Synthetic click for INP (real interaction needs user)
- JSON artifacts: `docs/perf/playwright/*.json` (12 files)
- Bundle size from `pnpm run build` output (Phase 71 vite audit)
```

- [ ] **Step 8.3: Verify doc has required tables**

Run: `grep -E "Per-route metrics|Compliance vs Web Rules|Bundle Size|Top Issues|Phase 77" docs/perf/playwright-web-vitals-baseline.md`
Expected: 5 hits (all sections present)

---

## Task 9: Final verification

**Files:** None

- [ ] **Step 9.1: git diff stat**

Run: `git diff --stat`
Expected: Empty (no modifications) — only new files untracked

- [ ] **Step 9.2: Verify no code files in new files**

Run: `git status -s | grep -E '\.(vue|js|ts)$' | grep -v "tests/perf/web-vitals" || echo "OK: only test spec, no app code"`
Expected: `OK: only test spec, no app code`

- [ ] **Step 9.3: Verify 14 new files**

Run: `git status -s | wc -l`
Expected: `14` (1 spec + 1 doc + 12 JSON)

- [ ] **Step 9.4: Re-run unit tests (sanity)**

Run: `cd apps/dashboard && pnpm test 2>&1 | tail -5`
Expected: `Tests  1549 passed (1549)` (unchanged)

- [ ] **Step 9.5: Re-run vue-tsc**

Run: `cd apps/dashboard && pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -5`
Expected: 0 errors

- [ ] **Step 9.6: Re-run build**

Run: `cd apps/dashboard && pnpm run build 2>&1 | tail -3`
Expected: `✓ built in <time>`

---

## Task 10: 1 atomic commit

**Files:** None (commits existing working tree)

- [ ] **Step 10.1: Stage 14 new files**

Run:
```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/tests/perf/web-vitals.spec.js \
        docs/perf/playwright-web-vitals-baseline.md \
        docs/perf/playwright/
```

- [ ] **Step 10.2: Verify staged**

Run: `git status -s`
Expected:
```
A  apps/dashboard/tests/perf/web-vitals.spec.js
A  docs/perf/playwright-web-vitals-baseline.md
A  docs/perf/playwright/creator-run1.json
A  docs/perf/playwright/creator-run2.json
A  docs/perf/playwright/creator-run3.json
A  docs/perf/playwright/landing-run1.json
A  docs/perf/playwright/landing-run2.json
A  docs/perf/playwright/landing-run3.json
A  docs/perf/playwright/production-run1.json
A  docs/perf/playwright/production-run2.json
A  docs/perf/playwright/production-run3.json
A  docs/perf/playwright/studio-run1.json
A  docs/perf/playwright/studio-run2.json
A  docs/perf/playwright/studio-run3.json
```

- [ ] **Step 10.3: Commit**

Run:
```bash
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "test(perf): Playwright Web Vitals baseline for 4 representative routes (Phase 76)" \
    -m "Phase 76 Web Vitals baseline (pivot from Lighthouse due to env no Chrome):

- 1 Playwright spec: apps/dashboard/tests/perf/web-vitals.spec.js (uses bundled Chromium)
- 4 routes × 3 runs × 5 metrics (LCP/INP/CLS/FCP/TBT)
- 12 JSON artifacts: docs/perf/playwright/*.json
- 1 baseline doc: docs/perf/playwright-web-vitals-baseline.md
- Bundle size reference: Phase 71 vite audit
- Phase 77+ action items: markRaw/shallowRef + bundle split + lazy load

测试基线不变: 1549 PASS, 0 type errors, 0 build errors.

Pivot rationale: Sandbox env 缺 Chrome binary. Playwright 自带 Chromium, 无新依赖."
```

- [ ] **Step 10.4: Verify commit**

Run: `git show --stat HEAD | head -30`
Expected: 14 new files, all in `apps/dashboard/tests/perf/` + `docs/perf/playwright*`

- [ ] **Step 10.5: Final log check**

Run: `git log --oneline -5`
Expected:
```
<new-hash> test(perf): Playwright Web Vitals baseline for 4 representative routes (Phase 76)
6eac78c5 docs(spec): Phase 76 amend — pivot from Lighthouse to Playwright (env no Chrome)
9204d2be docs(spec): Phase 76 — Lighthouse baseline design
e20f516a docs: Phase 74 doc drift 修正 + 2 sites deep:true 决策记录 (Phase 75)
145e84ae docs(spec): Phase 75 — Phase 74 doc drift 修正 + 2 sites deep:true 决策记录
```

- [ ] **Step 10.6: Confirm no auto-push (per Phase 60-74 convention)**

Run: `git status -sb | head -3`
Expected: `## master...origin/master [ahead N]` (user pushes manually)

---

## Self-Review

**Spec coverage**:
- Spec §2 Goal 1 (1 baseline doc) → Task 8
- Spec §2 Goal 2 (1 Playwright spec) → Task 3
- Spec §2 Goal 3 (production mode) → Tasks 4, 5
- Spec §2 Goal 4 (4 routes × 5 metrics) → Task 3 (spec) + Task 6 (run)
- Spec §2 Goal 5 (3 runs/route + median) → Task 6 (3 runs) + Task 8 (median in doc)
- Spec §2 Goal 6 (bundle size reference) → Task 8 §4
- Spec §2 Goal 7 (compliance table) → Task 8 §3
- Spec §2 Goal 8 (Phase 77+ action items) → Task 8 §6
- Spec §2 Goal 9 (1 atomic commit) → Task 10

**Placeholder scan**:
- Task 3 spec code is complete (no `TBD` / `TODO`)
- Task 8 doc structure has `_ms` / `_/100` placeholders (intentional — runtime data fill from JSON in Task 8.1)
- All verification commands have expected output

**Type consistency**:
- Routes consistent across spec §3.3 + Task 3 code + Task 8 doc template
- Metric names consistent (LCP/INP/CLS/FCP/TBT) across spec + plan + doc

**Risks covered**:
- 9 verification steps in Task 9 catch any drift
- Pre-flight checks in Task 1 catch env issues before spec creation
- Preview server kill in Task 7 prevents port lock

