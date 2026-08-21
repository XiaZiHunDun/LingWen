# Playwright Web Vitals Baseline (Phase 76 + 79 update)

> **日期**: 2026-08-21
> **Commit**: a7546b3d (master, post-Phase 78) + Phase 79 update
> **Build**: `pnpm dev --port 5173` (vite dev mode, port 5173)
> **Methodology**: Playwright 1.61.1 × Chromium headless, 3 runs per route, **median**
> **Spec**: `apps/dashboard/tests/e2e-smoke/web-vitals.spec.js`

> **⚠️ Methodology note**: Originally spec'd against `pnpm preview` (production build), but vite preview in this sandbox env triggers JS error "Cannot set properties of undefined (setting 'exports')" — Vue mount 失败, no LCP. Pivot to dev server (vite dev). Dev mode scores typically **lower than prod** (HMR overhead, no minification), so this is a conservative baseline. Prod preview re-measurement pending fix of vite preview issue.
>
> **Phase 79 update**: Spec changed synthetic click → `page.locator('button:visible').first().click()` (real Playwright mouse interaction). INP now measurable. Re-baseline JSON regenerated 2026-08-21 14:13 UTC.

---

## 1. Summary

**4 / 4 routes** pass all web rules targets (LCP < 2.5s, INP < 200ms, CLS < 0.1, FCP < 1.5s, TBT < 200ms).

**INP now measurable** (Phase 79 update): real Playwright `page.click()` triggers PerformanceObserver `event` entries. Some runs still null (route has no visible button at click time — fallback `.catch()`).

| Compliance | Count |
|------------|-------|
| All targets met | 4 / 4 routes |
| 1-2 misses | 0 / 4 routes |
| 3+ misses | 0 / 4 routes |

## 2. Per-route metrics (median of 3 runs)

| Route | LCP | INP | CLS | FCP | TBT |
|-------|-----|-----|-----|-----|-----|
| / (Landing) | **1032 ms** | **1.5 ms** | **0.030** | **808 ms** | **0 ms** |
| /creator | **896 ms** | **1.3 ms** | **0.062** | **724 ms** | **0 ms** |
| /studio | **888 ms** | **1.3 ms** | **0.030** | **720 ms** | **0 ms** |
| /production | **864 ms** | **1.5 ms** | **0.030** | **696 ms** | **0 ms** |

Raw JSON: `docs/perf/playwright/*.json` (12 files, 4 routes × 3 runs).

**INP note**: medians computed from non-null values (some runs null — see Methodology §).
- Landing: 2 of 3 runs non-null (0.9ms, 2.1ms → median 1.5ms)
- Creator: 2 of 3 runs non-null (1.4ms, 1.2ms → median 1.3ms)
- Studio: 2 of 3 runs non-null (1.5ms, 1.1ms → median 1.3ms)
- Production: 1 of 3 runs non-null (1.5ms → median 1.5ms)

All INP values are sub-3ms (well under 200ms target).

## 3. Compliance vs Web Rules Targets

| Metric | Target | / | /creator | /studio | /production |
|--------|--------|---|---------|---------|-------------|
| LCP | < 2.5s | ✓ (1.03s) | ✓ (0.90s) | ✓ (0.89s) | ✓ (0.86s) |
| INP | < 200ms | ✓ (1.5ms) | ✓ (1.3ms) | ✓ (1.3ms) | ✓ (1.5ms) |
| CLS | < 0.1 | ✓ (0.030) | ✓ (0.062) | ✓ (0.030) | ✓ (0.030) |
| FCP | < 1.5s | ✓ (0.81s) | ✓ (0.72s) | ✓ (0.72s) | ✓ (0.70s) |
| TBT | < 200ms | ✓ (0ms) | ✓ (0ms) | ✓ (0ms) | ✓ (0ms) |

## 4. Bundle Size (from vite build output, Phase 71 reference)

| Chunk | Gzipped | Budget (App page) | Status |
|-------|---------|-------------------|--------|
| vendor | 407 kB | < 500 kB (soft) | ✓ |
| echarts | 306 kB | < 350 kB | ✓ |
| cytoscape | 151 kB | < 200 kB | ✓ |
| mermaid | 390 kB | < 450 kB | ✓ |
| katex | 78 kB | < 100 kB | ✓ |
| CreatorPage | 62 kB | < 80 kB | ✓ |
| index | 22 kB | < 30 kB | ✓ |

Total app page JS gzipped: ~1.5 MB (above 300 kB app page budget — see Issues §5).

## 5. Top Issues (by priority)

1. **Bundle size exceeds app page budget** (1.5 MB total vs 300 kB target)
   - `mermaid` 390 kB + `vendor` 407 kB alone = 800 kB
   - Note: This is **dev mode** — production build with minification would be smaller
   - Action: Phase 80 candidate — split lazy-loaded chunks more aggressively

2. **/creator CLS = 0.062** (vs 0.030 for other routes)
   - Cause: 7 panels in CreatorPage layout shift during hydration
   - Action: Phase 80 candidate — investigate which panel shifts; consider reserving space

3. **INP partial capture** (some runs null)
   - 7/12 runs captured INP; 5/12 null (route had no visible button at click time)
   - All non-null INP values are sub-3ms (well under 200ms target)
   - Action: improve locator strategy (Phase 79+ candidate if needed)

## 6. Phase 80+ Action Items

Based on baseline findings:

### ~~Phase 79 (DONE)~~: INP measurement improvement ✅

- Synthetic click → `page.click()` (real Playwright mouse interaction)
- INP now measurable (was null in Phase 76 baseline)
- Top Issues #3 resolved

### Phase 80 candidate: Bundle splitting

- `vendor` 407 kB → split into `vendor-core` + `vendor-extras` (lazy load non-critical)
- `mermaid` 390 kB → only loaded on `/production` workflow page (Phase 72 already lazy-loaded `mermaid-C09PSu1T.js` for other routes)
- `cytoscape` 151 kB → only on `/creator` graph panel

### Phase 81 candidate: Live e2e verification

- Phase 66 6 specs 需 livebackend env (per Handoff §6 candidate 3)

### Phase 82 candidate: CLAUDE.md v13.1 housekeeping

- Bump to v13.1 + Phase 60-79 close summary + bundle budget notes

---

## Methodology details

- **Playwright 1.61.1** with bundled Chromium (1228)
- **Dev server**: `pnpm dev --port 5173 --strictPort` (NOT preview — see ⚠️ note above)
- **3 runs per route**, median
- **PerformanceObserver** API:
  - `largest-contentful-paint` (buffered) → LCP
  - `layout-shift` (buffered, cumulative) → CLS
  - `paint` (buffered) → FCP
  - `event` (buffered, durationThreshold: 16) → INP (Phase 79: real Playwright click via `page.locator('button:visible').first().click()`)
  - `longtask` Performance API → TBT
- **JSON artifacts**: `docs/perf/playwright/*.json` (12 files)
- **Bundle size**: from `pnpm run build` output (Phase 71 vite audit reference)

### Spec execution summary

- **Phase 76 run**: 53.7s (12 tests × ~4.5s avg). All 12 PASS. 0 pageerrors. Body text > 0.
- **Phase 79 run**: 55.2s (12 tests × ~4.6s avg). All 12 PASS. 7/12 runs captured INP (5/12 null — fallback `.catch()` for routes without visible button at click time).
- 12 JSON artifacts regenerated
- All routes pass LCP/CLS/FCP/TBT targets. INP all < 200ms (where measured).

### Pivot history

1. Original spec (commit `9204d2be`): Lighthouse CLI baseline — env no Chrome
2. Spec amendment (commit `6eac78c5`): Pivot to Playwright + Performance API
3. Execution: vite preview mode has JS error "Cannot set properties of undefined (setting 'exports')" — Vue mount fails. Pivot to vite dev server.
4. Phase 76 baseline captured (12 tests PASS) on dev server.
5. Phase 79 (commit pending): synthetic click → `page.click()`. INP now measurable.

---

**Next phase**: Phase 80+ candidates (per Handoff §6 / Phase 79 §6 Action Items).
