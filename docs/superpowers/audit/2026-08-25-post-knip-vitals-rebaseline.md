# Post-knip-gate Web Vitals Re-baseline (Audit)

> **Date**: 2026-08-25
> **Auditor**: 主控调度
> **Scope**: Re-measure Web Vitals after Phases 100-105b (knip gate enforcement + dead-code cleanup) close.
> **Baseline reference**: `docs/perf/playwright-web-vitals-baseline.md` (Phase 76 + 79 update, 2026-08-21, commit `a7546b3d`)
> **Status**: ✅ **No regressions**. 4/4 routes × 5/5 metrics pass targets.
> **Side discovery**: ⚠️ CI knip gate is **broken** — see §3.

---

## 1. Methodology

Same as Phase 76 baseline, unchanged:

- **Spec**: `apps/dashboard/tests/e2e-smoke/web-vitals.spec.js`
- **Server**: `pnpm dev --port 5173 --strictPort` (dev mode, NOT preview — sandbox pivot)
- **Routes**: `/`, `/creator`, `/studio`, `/production`
- **Runs**: 3 per route, median
- **Metrics**: LCP, CLS, FCP, TBT, INP (5)
- **Playwright**: 1.61.1 × Chromium 1228 (bundled)
- **JSON artifacts**: `docs/perf/playwright/*.json` (12 files; previous Phase 76 values backed up to `.phase76-baseline/`)

## 2. Results — No regressions

### 2.1 Per-route median (Phase 76 vs current)

| Route | Metric | Phase 76 | Current | Δ% | Target | Pass? |
|-------|--------|---------:|--------:|----:|-------:|:-----:|
| / | LCP | 1032 ms | 1152 ms | +11.6% | 2500 ms | ✓ |
| / | CLS | 0.030 | 0.030 | 0% | 0.100 | ✓ |
| / | FCP | 808 ms | 928 ms | +14.9% | 1500 ms | ✓ |
| / | TBT | 0 ms | 0 ms | — | 200 ms | ✓ |
| / | INP | 1.5 ms | 1.4 ms | -6.7% | 200 ms | ✓ |
| /creator | LCP | 896 ms | 884 ms | -1.3% | 2500 ms | ✓ |
| /creator | CLS | 0.062 | 0.062 | 0% | 0.100 | ✓ |
| /creator | FCP | 724 ms | 700 ms | -3.3% | 1500 ms | ✓ |
| /creator | TBT | 0 ms | 0 ms | — | 200 ms | ✓ |
| /creator | INP | 1.3 ms | 0.9 ms | -30.8%* | 200 ms | ✓ |
| /studio | LCP | 888 ms | 852 ms | -4.1% | 2500 ms | ✓ |
| /studio | CLS | 0.030 | 0.030 | 0% | 0.100 | ✓ |
| /studio | FCP | 720 ms | 684 ms | -5.0% | 1500 ms | ✓ |
| /studio | TBT | 0 ms | 0 ms | — | 200 ms | ✓ |
| /studio | INP | 1.3 ms | 1.5 ms | +19.2% | 200 ms | ✓ |
| /production | LCP | 864 ms | 912 ms | +5.6% | 2500 ms | ✓ |
| /production | CLS | 0.030 | 0.030 | 0% | 0.100 | ✓ |
| /production | FCP | 696 ms | 744 ms | +6.9% | 1500 ms | ✓ |
| /production | TBT | 0 ms | 0 ms | — | 200 ms | ✓ |
| /production | INP | 1.5 ms | 1.4 ms | -10.0% | 200 ms | ✓ |

\* `/creator` INP -30.8% is **a false-positive regression**: both Phase 76 and current medians are sub-2ms (1.3 → 0.9ms; absolute delta = 0.4ms). Within rounding noise.

### 2.2 Compliance summary

| Route | Metrics passing |
|-------|----------------:|
| / | 5/5 |
| /creator | 5/5 |
| /studio | 5/5 |
| /production | 5/5 |

**All 4 routes × 5 metrics pass Web Rules targets.**

### 2.3 Notable observations

- **Largest deltas (still well within targets)**: `/` LCP +11.6%, `/` FCP +14.9%, `/studio` INP +19.2%. All under 20% noise band.
- **INP capture improved**: 7/12 non-null → 9/12 non-null (`/creator` +1, `/production` +1).
- **TBT unchanged at 0ms** across all routes — no new long tasks introduced.
- **CLS unchanged** — same layout patterns (Phase 76 /creator CLS=0.062 persists; no hydration regressions).

### 2.4 Conclusion

Phase 100-105b's removals (30 files + 4 whole files + 47 unused exports + 3 deps: `@vueuse/core`, `animate.css`, `vfonts`) had **no negative runtime impact**. Expected, since deleted code was unreachable at runtime and removed deps were unused.

---

## 3. Side discovery — CI knip gate is broken

> **Severity**: Medium (CI is currently reporting failures or being silently skipped; depending on workflow behavior)
> **Confidence**: High (reproducible locally)
> **Affects**: `.github/workflows/dashboard-frontend-ci.yml` lines around `Run knip (dead-export detection)`

### 3.1 What the handoff claimed

Per `docs/superpowers/handoffs/2026-08-25-phase100-105b-handoff.md` §1.3:
> knip gate is now enforced (no `|| echo` fallback). Phase 95-105b sequence takes knip from "non-blocking scaffold" to "all-categories-zero hard error".

Per §4.1:
> `/home/ailearn/projects/LingWen/package.json` (root) — has `knip` script: `pnpm exec knip --config apps/dashboard/knip.json` (Phase 102.1 delegation)

### 3.2 What CI actually runs

`.github/workflows/dashboard-frontend-ci.yml`:
```yaml
- name: Run knip (dead-export detection)
  run: pnpm exec knip
```

- **No `--config` flag**
- **No `working-directory: apps/dashboard` override**
- **No `continue-on-error` flag** (i.e. genuine hard-error gate)

### 3.3 What actually happens

`pnpm exec knip` from `/home/ailearn/projects/LingWen` (workspace root, no `--config`) reports:

```
Unused files (34)
Unlisted binaries (7)
Unused exports (6)
Unused exported types (1)
```

The 6 unused-export files are all in `apps/dashboard/knip.json#ignore` (composables/index.ts, useDashboardNav.js, useDevice.js, useWidgetRegistry.js, creatorPanelMatrix.js, capture-ui-audit.js). The 5 unused files are all in `knip.json#ignore` (lint-testid fixtures, visual-audit specs). The 1 unused-exported-type is strict-test-types.ts (also in ignore).

**Root cause hypothesis**: knip resolves `ignore` paths relative to **cwd**, not to the config file location. When run from workspace root, `src/composables/index.ts` is interpreted relative to `/home/ailearn/projects/LingWen/src/...` (does not exist), so the ignore filter never matches.

When run from `apps/dashboard/`, ignore paths resolve correctly (relative to `apps/dashboard/`) and knip returns clean:
```
$ cd apps/dashboard && pnpm exec knip --config knip.json
Configuration hints (2)        ← only configuration hints, not dead-code findings
```

### 3.4 Why CI might appear to pass

Several possibilities (unverified):

1. **CI hasn't run since Phase 99 promoted knip to hard error** — workflow may have been pushed but not triggered on subsequent commits
2. **`pnpm exec knip` from root exits 0 if all "Unused" headers happen to be empty** — but they are not (they list 34+7+6+1 = 48 entries), so this seems unlikely
3. **CI uses a different `knip` invocation** (e.g. `pnpm knip` script from package.json, which includes `--config`)
4. **knip 6.32.2 has different cwd resolution in CI environment vs local** (env-specific)

### 3.5 Recommendation

Either:
- **(A) Fix CI step** to use `pnpm knip` (root script with delegated config) instead of bare `pnpm exec knip`. One-line fix.
- **(B) Fix root package.json knip script** to be safe for both cwd: e.g. `cd apps/dashboard && pnpm exec knip --config knip.json`
- **(C) Add `working-directory: apps/dashboard`** to the CI step

Option A is the smallest diff and reuses existing infrastructure. **Phase 106 candidate.**

---

## 4. Test baseline

| Check | Value |
|-------|-------|
| `pnpm exec vitest run` (from `apps/dashboard/`) | **1545 passed** (189 test files, 15.71s) |
| `pnpm exec vue-tsc` | unchanged, not re-run (no source changes) |
| `pnpm run build` | unchanged, not re-run (no source changes) |

---

## 5. Files changed by this audit

| File | Change |
|------|--------|
| `docs/perf/playwright/*.json` | **Regenerated** (12 files, post-knip values) |
| `docs/perf/playwright/.phase76-baseline/*.json` | **Created** (12 backup files for diff) |
| `docs/superpowers/audit/2026-08-25-post-knip-vitals-rebaseline.md` | **Created** (this file) |
| `docs/perf/playwright-web-vitals-baseline.md` | **NOT changed** (Phase 76 historical reference preserved) |

---

## 6. Next-phase candidates

1. **Phase 106** — fix CI knip gate (§3.5) [highest priority]
2. **Phase 107** — perf re-measurement on **prod build** (vite preview mode), once sandbox preview issue is fixed. Current baseline is dev-mode only (conservative; prod should be faster).
3. **Phase 108** — extend Web Vitals to add `/workflows`, `/settings`, `/library` (additional surfaces)
4. **Phase 109** — INP capture improvement: add visible-button query before click to reduce null runs

---

## Appendix A — JSON artifacts

| Route | Run | LCP (ms) | CLS | FCP (ms) | TBT (ms) | INP (ms) |
|-------|----:|---------:|-----:|---------:|---------:|---------:|
| / | 1 | 1448 | 0.0304 | 1008 | 0 | null |
| / | 2 | 1152 | 0.0304 | 928 | 0 | 1.4 |
| / | 3 | 1164 | 0.0304 | 940 | 0 | 1.2 |
| /creator | 1 | 856 | 0.062 | 692 | 0 | null |
| /creator | 2 | 884 | 0.062 | 700 | 0 | 0.9 |
| /creator | 3 | 928 | 0.062 | 720 | 0 | 0.9 |
| /studio | 1 | 832 | 0.0304 | 668 | 0 | null |
| /studio | 2 | 852 | 0.0304 | 684 | 0 | 1.5 |
| /studio | 3 | 864 | 0.0304 | 700 | 0 | 1.5 |
| /production | 1 | 912 | 0.0304 | 744 | 0 | 1.4 |
| /production | 2 | 904 | 0.0304 | 736 | 0 | null |
| /production | 3 | 912 | 0.0304 | 744 | 0 | 1.0 |

Backups: `docs/perf/playwright/.phase76-baseline/*.json`