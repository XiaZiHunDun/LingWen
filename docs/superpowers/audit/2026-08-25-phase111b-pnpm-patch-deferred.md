# Phase 111B — pnpm Patch Attempt Deferred

> **Date**: 2026-08-25
> **Goal**: Patch `cytoscape-fcose` UMD wrapper via `pnpm patch` to make it ESM-compatible in vite preview prod builds
> **Status**: ❌ **Deferred to Phase 111C** (custom Vite/Rollup plugin)
> **Outcome**: no code changes; audit document this file

---

## 1. Approach attempted

Use `pnpm patch cytoscape-fcose@2.2.0` (and `cose-base@2.2.0`, `cose-base@1.0.3`) to:

1. Create temp directory with original package contents
2. Replace UMD wrapper with explicit ESM export
3. `pnpm patch-commit` to save patch + add `pnpm.patchedDependencies` to package.json

## 2. Why it didn't work cleanly

### 2.1 UMD wrapper structure

`cytoscape-fcose/cytoscape-fcose.js` is webpack-bundled UMD:

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
        var __webpack_modules__ = ({
            658: ((module) => { module.exports = Object.assign.bind(Object); }),
            // ... more modules
        });
        // webpack runtime
        return i(i.s = 26);  // entry module 26
    }();
});
```

### 2.2 Patch attempt 1: prepend `module`/`exports` polyfill

Prepended:
```js
if (typeof module === 'undefined') globalThis.module = { exports: {} };
if (typeof exports === 'undefined') globalThis.exports = module.exports;
var require = (function() { /* returns cose-base */ })();
```

**Problem**: The UMD wrapper runs `(function(...)(this, factory))` where `this` is `undefined` in ESM top-level. The CJS branch then sets `module.exports = factory(require("cose-base"))`. This may execute correctly at runtime, BUT rollup's static analysis sees `module.exports = ...` inside an IIFE and wraps it incorrectly. The wrapper chain `H0 = {exports: {}}` → `epe = H0.exports` → `tpe()` → `e.exports = i()` still fails because rollup's wrapped output doesn't match the IIFE structure rollup expects.

### 2.3 Patch attempt 2: full ESM replacement

Replace entire file with:
```js
import coseBase from 'cose-base';
export default (function(__WEBPACK_EXTERNAL_MODULE__140__) {
    return /* webpackBootstrap */ (() => {
        // ... original inner webpackBootstrap body
        return i(i.s = 26);
    })();
})(coseBase);
```

**Problem**: The inner webpackBootstrap still uses `module.exports = ...` patterns inside the `__webpack_modules__` definitions. Each module like `658: ((module) => { module.exports = ...; })` references a `module` parameter from the webpack runtime. Replacing the entire wrapper requires either:
- Wrapping each inner `module.exports = ...` in an ESM-compatible way (very invasive)
- Using a runtime shim that defines `module` as `{ exports: {} }` inside the IIFE scope

Both approaches are fragile and would need to be repeated for `cytoscape-cose-bilkent` AND both `cose-base@1.0.3` and `cose-base@2.2.0` versions.

## 3. Conclusion

`pnpm patch` alone is insufficient because:
1. The webpack-bundled modules use `module.exports = ...` internally (not just in the UMD wrapper)
2. Rollup's `@rollup/plugin-commonjs` rewrites these into its own wrapper, which fails for the same reason the UMD fails
3. Patching just the UMD wrapper doesn't fix the inner `module.exports` patterns
4. Patching the inner patterns requires deep modification of webpack-bundled code (each `__webpack_modules__[N]` entry would need rewriting)

**Recommended next step**: **Phase 111C** — write a custom Vite/Rollup plugin that:
- Intercepts `cytoscape-fcose`, `cytoscape-cose-bilkent`, `cose-base` resolutions
- Pre-transforms each via esbuild (which handles CJS correctly)
- Returns the ESM output as the module source

This would be a small `vite-plugin-cytoscape-interop.js` (~50 lines) in `apps/dashboard/eslint-rules/` (or new `apps/dashboard/vite-plugins/`).

## 4. Files changed

- **None**. No code changes; no package.json updates.
- Audit doc this file.

## 5. Test baseline

| Check | Value |
|-------|-------|
| `pnpm exec vitest run` | **1545 passed** (189 test files) |
| `pnpm run build` | ✓ clean |
| `pnpm knip` | ✓ exit 0 |

---

## Appendix A — Phase 111+ candidates

| Phase | Description | Estimated time |
|-------|-------------|----------------|
| 111C | Custom Vite plugin via esbuild pre-transform | 30-45 min |
| 111D | Use `vite-plugin-commonjs` explicit config | 15-30 min |
| 111E | Replace cytoscape with vis-network (in source code) | 2-4 hours |
| 111F | Bump mermaid to version without cytoscape dep (if exists) | 30-60 min |

**Recommendation**: **Phase 111C** (custom plugin) — most targeted, smallest blast radius, reusable for future UMD packages.

Phase 111E (replacement) is the most thorough but requires rewriting `/production` graph component.