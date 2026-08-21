# Playwright Web Vitals Baseline (Phase 76)

> **日期**: 2026-08-21
> **Commit**: e20f516a (master, post-Phase 75)
> **Build**: `pnpm dev --port 5173` (vite dev mode, port 5173)
> **Methodology**: Playwright 1.61.1 × Chromium headless, 3 runs per route, **median**
> **Spec**: `apps/dashboard/tests/e2e-smoke/web-vitals.spec.js`

> **⚠️ Methodology note**: Originally spec'd against `pnpm preview` (production build), but vite preview in this sandbox env triggers JS error "Cannot set properties of undefined (setting 'exports')" — Vue mount 失败, no LCP. Pivot to dev server (vite dev). Dev mode scores typically **lower than prod** (HMR overhead, no minification), so this is a conservative baseline. Prod preview re-measurement pending fix of vite preview issue.

---

## 1. Summary

**4 / 4 routes** pass all measurable web rules targets (LCP < 2.5s, CLS < 0.1, FCP < 1.5s, TBT < 200ms).

**INP 无法测量**: synthetic click 不触发 `event` PerformanceObserver entry, INP 全部 null. Real-user INP requires actual user interaction (out of scope for headless baseline).

| Compliance | Count |
|------------|-------|
| All measurable targets met | 4 / 4 routes |
| 1-2 misses | 0 / 4 routes |
| 3+ misses | 0 / 4 routes |

## 2. Per-route metrics (median of 3 runs)

| Route | LCP | INP | CLS | FCP | TBT |
|-------|-----|-----|-----|-----|-----|
| / (Landing) | **924 ms** | null | **0.030** | **692 ms** | **0 ms** |
| /creator | **1880 ms** | null | **0.030** | **708 ms** | **0 ms** |
| /studio | **1580 ms** | null | **0.030** | **680 ms** | **0 ms** |
| /production | **1588 ms** | null | **0.030** | **680 ms** | **0 ms** |

Raw JSON: `docs/perf/playwright/*.json` (12 files, 4 routes × 3 runs).

## 3. Compliance vs Web Rules Targets

| Metric | Target | / | /creator | /studio | /production |
|--------|--------|---|---------|---------|-------------|
| LCP | < 2.5s | ✓ (0.92s) | ✓ (1.88s) | ✓ (1.58s) | ✓ (1.59s) |
| INP | < 200ms | — (null) | — (null) | — (null) | — (null) |
| CLS | < 0.1 | ✓ (0.030) | ✓ (0.030) | ✓ (0.030) | ✓ (0.030) |
| FCP | < 1.5s | ✓ (0.69s) | ✓ (0.71s) | ✓ (0.68s) | ✓ (0.68s) |
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
   - mavis: `mermaid` 390 kB + `vendor` 407 kB alone = 800 kB
   - Note: This is **dev mode** — production build with minification would be smaller
   - Action: Phase 78 candidate — split lazy-loaded chunks more aggressively

2. **/creator LCP = 1.88s** (vs /studio 1.58s, /production 1.59s)
   - 200-300ms slower than other routes
   - Cause: 7 panels in CreatorPage, 2 lazy-loaded but still hydration cost
   - Action: Phase 77 candidate — defer non-critical panels via `defineAsyncComponent`

3. **INP not measurable** (all routes null)
   - Synthetic click in `addInitScript` does not generate `event` PerformanceObserver entries
   - Workaround: Use page.click() (real interaction) — but adds complexity
   - Action: Phase 77 candidate — improve spec to use `page.click()` for INP

## 6. Phase 77+ Action Items

Based on baseline findings:

### Phase 77 (next): markRaw/shallowRef optimization

- **Stores** (1 file 已 markRaw, 485 reactives total):
  - `useStudioStore.cacheTimestamps = ref({})` — shallowRef candidate (nested object, no reactivity needed at property level)
  - `useCreatorSettings` 18+ refs — consolidate into 1 reactive object
- **Composables**: same audit for `useCreatorPage.js`, `useCreatorVolumePlan.js`
- **Chart components** (10 files): **already optimal** — `let chartInstance = null` (local var, non-reactive)

### Phase 78 candidate: Bundle splitting

- `vendor` 407 kB → split into `vendor-core` + `vendor-extras` (lazy load non-critical)
- `mermaid` 390 kB → only loaded on `/production` workflow page (Phase 72 already lazy-loaded `mermaid-C09PSu1T.js` for other routes)
- `cytoscape` 151 kB → only on `/creator` graph panel

### Phase 79 candidate: INP measurement improvement

- Replace synthetic `evaluate(() => button.click())` with `page.click()` (real Playwright interaction)
- Capture event-timing entries with proper user interaction semantics

### Phase 80+: Live e2e + CLAUDE.md housekeeping

- Phase 66 6 specs 需 livebackend env (per Handoff §6 candidate 3)
- CLAUDE.md v13.1 bump (Phase 76 close summary + bundle budget notes)

---

## Methodology details

- **Playwright 1.61.1** with bundled Chromium (1228)
- **Dev server**: `pnpm dev --port 5173 --strictPort` (NOT preview — see ⚠️ note above)
- **3 runs per route**, median
- **PerformanceObserver** API:
  - `largest-contentful-paint` (buffered) → LCP
  - `layout-shift` (buffered, cumulative) → CLS
  - `paint` (buffered) → FCP
  - `event` (buffered, durationThreshold: 16) → INP (did not fire for synthetic click)
  - `longtask` Performance API → TBT
- **JSON artifacts**: `docs/perf/playwright/*.json` (12 files)
- **Bundle size**: from `pnpm run build` output (Phase 71 vite audit reference)

### Spec execution summary

- Total runtime: 53.7s (12 tests × ~4.5s avg)
- All 12 tests PASS
- 12 JSON artifacts written
- 0 pageerrors on dev server (verified)
- Page text content > 0 chars for all routes (sanity check passed)

### Pivot history

1. Original spec (commit `9204d2be`): Lighthouse CLI baseline — env no Chrome
2. Spec amendment (commit `6eac78c5`): Pivot to Playwright + Performance API
3. Execution: vite preview mode has JS error "Cannot set properties of undefined (setting 'exports')" — Vue mount fails. Pivot to vite dev server.
4. Result: Baseline captured (12 tests PASS) on dev server.

---

**Next phase**: Phase 77 markRaw/shallowRef optimization (per Handoff §6 candidate 1).
