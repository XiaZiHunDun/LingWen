# Phase 110 — Vite Preview JS Error Audit (Prod-mode Web Vitals Deferred)

> **Date**: 2026-08-25
> **Auditor**: 主控调度
> **Goal**: Fix `pnpm preview` JS error to enable prod-mode Web Vitals baseline (4 routes × 3 runs × 5 metrics against `dist/` build)
> **Status**: ❌ **Goal not achieved**. Dev baseline (Phase 106) remains the authoritative measurement.
> **Recommendation**: Defer to **Phase 111+** as separate research task. Vite config left unchanged.

---

## 1. Background

The Web Vitals baseline (Phase 76, commit `a7546b3d`) was originally spec'd against `pnpm preview` (production build via vite preview server). The Phase 76 spec noted:

> **⚠️ Methodology note**: Originally spec'd against `pnpm preview` (production build), but vite preview in this sandbox env triggers JS error "Cannot set properties of undefined (setting 'exports')" — Vue mount 失败, no LCP. Pivot to dev server (vite dev). Dev mode scores typically **lower than prod** (HMR overhead, no minification), so this is a conservative baseline. Prod preview re-measurement pending fix of vite preview issue.

Phase 106 re-confirmed the same error after Phase 100-105b dead-code cleanup (no change in behavior). Phase 110 was scoped to fix the error and produce a prod-mode baseline.

## 2. Error reproduction

Reproduced via Playwright 1.61.1 against `pnpm preview --port 4173 --strictPort`:

```text
TITLE: 灵文 · 网文写作伴侣
BODY LENGTH: 0

[pageerror] Cannot set properties of undefined (setting 'exports')
TypeError: Cannot set properties of undefined (setting 'exports')
    at http://localhost:4173/assets/vendor-lk4byDOd.js:113:63836   ← CJS wrapper `e.exports = i()`
    at http://localhost:4173/assets/vendor-lk4byDOd.js:113:63842
    at tpe (http://localhost:4173/assets/vendor-lk4byDOd.js:113:115237)   ← lazy module loader
    at http://localhost:4173/assets/vendor-lk4byDOd.js:113:115350
    at http://localhost:4173/assets/vendor-lk4byDOd.js:113:115358
    at Txe (http://localhost:4173/assets/vendor-lk4byDOd.js:113:134909)   ← cose-bilkent wrapper
    at http://localhost:4173/assets/cytoscape-DRslRMNe.js:331:34545   ← cytoscape main
    at http://localhost:4173/assets/cytoscape-DRslRMNe.js:331:34552
    at Gm (http://localhost:4173/assets/cytoscape-DRslRMNe.js:331:40722)
    at http://localhost:4173/assets/cytoscape-DRslRMNe.js:331:40746
```

Vue mount fails → `document.body.innerText.length === 0` → no LCP possible.

## 3. Root cause analysis

### 3.1 Dependency chain

```
mermaid 11.16.0 (prod dep)
├── cytoscape 3.34.0                (peerDep of cytoscape-* plugins)
├─┬ cytoscape-cose-bilkent 4.1.0    (CJS only: no `module`/`exports` field)
│ └── cose-base 1.0.3               (CJS only: webpack-bundled UMD)
└─┬ cytoscape-fcose 2.2.0           (CJS only: webpack-bundled UMD)
  └── cose-base 2.2.0               (different version → both bundled)
```

### 3.2 Why CJS in ESM context breaks

`cytoscape-fcose/cytoscape-fcose.js` is a webpack-bundled UMD module:

```js
(function webpackUniversalModuleDefinition(root, factory) {
    if(typeof exports === 'object' && typeof module === 'object')
        module.exports = factory(require("cose-base"));
    else if(typeof define === 'function' && define.amd)
        define(["cose-base"], factory);
    else if(typeof exports === 'object')
        exports["cytoscapeFcose"] = factory(require("cose-base"));
    else
        root["cytoscapeFcose"] = factory(root["coseBase"]);
})(this, function(__WEBPACK_EXTERNAL_MODULE__140__) {
    return /* webpackBootstrap */ function() {
        // ...
        module.exports = Object.assign != null ? Object.assign.bind(Object) : function(tgt) { /* ... */ };
        // ...
    }
});
```

When rollup wraps this for ESM, the inner `module.exports = ...` pattern gets converted to a CJS-style wrapper like:

```js
var epe = H0.exports;
function tpe() {
  return eD || (eD = 1, (function(e, t) {
    (function(n, i) {
      e.exports = i()  // ← here `e` is the outer IIFE param
    })(epe, function() {
      return /* webpack runtime + cose-bilkent modules */;
    });
  })([/* cose-bilkent module as array element */]));
}
```

The issue: when rollup calls the outer IIFE with the cose-bilkent module array, `e = [array]`. Then the inner IIFE tries to set `e.exports = i()`. But **the wrapper IIFE is called with only one argument** (`[array]`), so `e = [array]`. Setting `[array].exports = i()` should work, but the runtime error suggests `e` is undefined.

This points to a **rollup CJS-plugin bug or limitation** with webpack-bundled UMD modules that have nested IIFEs and `module.exports` references inside webpackBootstrap.

### 3.3 Why dev mode works

In dev mode, `pnpm dev` runs vite's dev server which uses **esbuild pre-bundling** (`optimizeDeps`). esbuild handles webpack-UMD modules correctly, converting `module.exports` patterns properly. In prod mode, rollup takes over with its built-in `@rollup/plugin-commonjs`, which has different heuristics and apparently fails on these specific packages.

## 4. Fix approaches attempted (all failed)

### 4.1 `optimizeDeps.include: ['cytoscape', 'cytoscape-fcose', 'cytoscape-cose-bilkent', 'cose-base']`

Forces esbuild pre-bundling of these deps. **Effect**: build output unchanged (chunks identical hashes). `optimizeDeps` is dev-only — does NOT affect prod build.

### 4.2 `build.commonjsOptions.transformMixedEsModules: true`

Tells rollup to treat mixed ESM/CJS imports as CJS. **Effect**: same error, same chunk hashes.

### 4.3 `build.commonjsOptions.include: [/node_modules/, /cytoscape/, /cose-base/]`

Aggressive CJS plugin inclusion for these patterns. **Effect**: same error.

### 4.4 Add `'cytoscape-fcose': 'cytoscape'` + `'cytoscape-cose-bilkent': 'cytoscape'` to NAMED chunks

Bundle cytoscape plugins with cytoscape chunk. **Effect**: redundant (substring `'cytoscape'` already matches their paths via existing NAMED entry). No change.

### 4.5 Merge cytoscape into vendor chunk (avoid cross-chunk load order)

`'cytoscape': 'vendor'` in NAMED. **Effect**: NEW error appeared — `Cannot access 'H' before initialization` in mermaid chunk. Build still warns `Circular chunk: mermaid -> vendor -> mermaid`. The circular chunk graph was tolerable before but breaks once cytoscape is in vendor.

### 4.6 Just `'cose-base'` in `optimizeDeps.include`

Targeted pre-bundling. **Effect**: same error.

## 5. Why this is hard

The combination of:
- **Webpack-bundled UMD** (legacy module format with multiple `module.exports = ...` references inside `webpackBootstrap`)
- **CJS-only packages** (no `module`/`exports` field in package.json)
- **Cross-chunk dependencies** (cytoscape chunk imports from vendor where cose-base lives)
- **Rollup's built-in CJS plugin** (handles most cases but not this one)

…requires either:
1. **Custom rollup plugin** to transform these specific packages' UMD wrappers before rollup's CJS plugin sees them
2. **Patch the source packages** via pnpm `overrides` or `patches/` directory (modify UMD wrappers to be ESM-friendly)
3. **Replace `mermaid` architecture diagrams** with non-cytoscape alternatives (workflow page uses `cytoscape` for graph viz; would require significant rework)
4. **Live with dev-only baseline** (current state)

## 6. Recommendation: defer to Phase 111+

Given:
- The dev baseline (Phase 106) is sufficient for regression detection (conservative; lower numbers = safer)
- Fixing the prod error requires non-trivial work (custom plugin OR dep patches)
- Time invested vs value gained is unfavorable
- The Phase 76 team reached the same conclusion 4 months ago

**Recommendation**: Keep dev baseline as authoritative. Phase 111+ candidate list (ranked by value):

1. **Phase 111A** — Replace cytoscape graph in `/production` with a non-cytoscape alternative (e.g., `vis-network` or `d3-force`) and bump mermaid to a version that doesn't pull cytoscape (if available)
2. **Phase 111B** — Patch `cytoscape-fcose`/`cytoscape-cose-bilkent` UMD wrappers via `patches/` to use ESM-compatible export pattern
3. **Phase 111C** — Write custom rollup plugin to pre-transform these specific UMD wrappers
4. **Phase 111D** — Migrate from `vite` to `vite-plugin-commonjs` with explicit configuration (similar to existing Astro/Next.js setups)

**Recommended**: **Phase 111B** — minimal pnpm patch + rollup include is most targeted.

## 7. What was actually delivered

- **None of the goal**: no prod-mode Web Vitals baseline
- **Negative result**: audit document this file
- **Build state**: vite config reverted to HEAD, no residual changes
- **Test baseline**: 1545 PASS, 189 files — unchanged

## 8. Files changed by this audit

| File | Change |
|------|--------|
| `docs/superpowers/audit/2026-08-25-phase110-vite-preview-js-error-audit.md` | **Created** (this file) |
| `apps/dashboard/vite.config.js` | **Reverted** (no net change) |
| `apps/dashboard/dist/` | **Rebuilt** (regenerated from current source; same content as before this phase) |

No git changes in tracked source files. Only the audit doc is new.

## 9. Test baseline verification

| Check | Value |
|-------|-------|
| `pnpm exec vitest run` (from `apps/dashboard/`) | **1545 passed** (189 test files) |
| `pnpm run build` | ✓ built in ~19s (clean) |
| `pnpm lint:all` | unchanged, not re-run (no source changes) |

---

## Appendix A — Reproduction commands

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard

# Build
pnpm run build 2>&1 | tail -5

# Start preview
pnpm preview --port 4173 --strictPort &
sleep 4

# Reproduce via Playwright (script: /tmp/check-preview.mjs)
node /tmp/check-preview.mjs 2>&1 | head -20

# Cleanup
kill %1
```

Expected: `TypeError: Cannot set properties of undefined (setting 'exports')` with stack trace through cytoscape chunk → vendor chunk.

---

## Appendix B — Phase 76 reference

Per `docs/superpowers/specs/2026-08-21-phase76-lighthouse-baseline-design.md`:

> ⚠️ Methodology note: Originally spec'd against `pnpm preview` (production build), but vite preview in this sandbox env triggers JS error "Cannot set properties of undefined (setting 'exports')" — Vue mount 失败, no LCP. Pivot to dev server (vite dev).

Same error, 4 months later. The Phase 76 team decided to pivot to dev mode rather than fix the root cause. Phase 110 attempted the fix and confirmed it requires non-trivial work beyond a single-phase scope.