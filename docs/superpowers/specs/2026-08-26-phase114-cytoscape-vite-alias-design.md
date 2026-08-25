# Phase 114 — Cytoscape Vite Alias Stub (Prod Web Vitals Fix)

> **Date**: 2026-08-26
> **Goal**: Fix `pnpm preview` JS error to enable prod-mode Web Vitals baseline (4 routes × 3 runs × 5 metrics).
> **Approach**: Vite resolve.alias + ESM stub for cytoscape family (Option A from brainstorm).
> **Status**: Design (pre-implementation)

---

## 1. Background

Phase 110/111B/111C/112/112C documented the same `Cannot set properties of undefined (setting 'exports')` error in `pnpm preview` across 4 attempts. Root cause:

- mermaid 11.16.0 ships architecture diagrams as a separate chunk (`chunks/mermaid.core/architectureDiagram-ZJ3FMSHR.mjs`)
- That chunk statically `import cytoscape from "cytoscape"` and `import fcose from "cytoscape-fcose"`
- A third chunk (`cose-bilkent-JH36ORCC.mjs`) statically imports `cytoscape` and `cytoscape-cose-bilkent`
- These cytoscape packages are **webpack-bundled UMD** with `module.exports = ...` patterns inside `webpackBootstrap`
- Rollup's built-in `@rollup/plugin-commonjs` chokes on the nested IIFE wrapping pattern (`e.exports = i()` where `e` becomes undefined)

The current prod bundle emits `cytoscape-DRslRMNe.js` as a separate chunk. At runtime (preview server), the chunk loads and immediately throws on the `module.exports` assignment.

**LingWen's actual usage**: workflow diagrams only ever use `graph TD` (flowchart) syntax. mermaid's architectureDetector is a regex match (`/^\s*architecture/.test(txt)`) that never invokes `cytoscape()` in our render path. The architectureDiagram chunk is statically reachable through mermaid's dynamic `await import(...)` but never executed at runtime.

## 2. Approach

Replace the 5 cytoscape-family packages with a single ESM no-op stub via Vite `resolve.alias`. mermaid's architectureDetector (regex) registers normally; if anyone actually triggers the architecture chunk, the stub returns harmless Proxy values (no observable side effects because we never trigger it in our app).

### 2.1 Why this works

- **mermaid registration is static + lazy-load per diagram**: `registerLazyLoadedDiagrams(architectureDetector_default, ...)` registers the detector function, not the chunk. The chunk loads only when a `mermaid.render()` call hits the detector.
- **Detectors don't reference cytoscape**: `architectureDetector.ts` is a regex test that imports populateCommonDb/selectSvgElement/createText from mermaid internals only.
- **flowDiagram chunk has no cytoscape import**: `flowDiagram-23GEKE2U.mjs` imports 21 mermaid-internal chunks and 0 external cytoscape deps.
- **Vite alias intercepts at build time + dev time**: rollup and esbuild both honor `resolve.alias`, so the cytoscape-family packages never reach the bundler.
- **knip doesn't scan scripts/**: `knip.json#project` only globs `src/**` and `tests/**`. The stub file is invisible to knip's dead-code analysis.

### 2.2 Why this is safer than Phase 112C stub plugin

Phase 112C used a no-op Proxy that returned `undefined` for all property access. That triggered a TDZ error in vendor chunk because some mermaid internal eagerly accesses a property that was previously defined by cytoscape.use() / fcose.

This design uses a Proxy that returns **new Proxy function instances** for any access. This means:

- `cytoscape({...})` returns a Proxy (no-op call)
- `cytoscape.use(plugin)` returns undefined (no-op access), which is fine because no one calls it
- `import fcose from "cytoscape-fcose"` returns the Proxy (default export)
- `cytoscape.use(fcose)` would pass the Proxy as plugin — but we never trigger this path

The stub Proxy accepts any property/method/constructor/apply access without throwing. If mermaid's internal startup inadvertently accesses cytoscape synchronously, the Proxy gives it a Proxy (not undefined) — no TDZ violation.

## 3. Files to change

### 3.1 New file: `apps/dashboard/scripts/cytoscape-stub.mjs`

```js
// apps/dashboard/scripts/cytoscape-stub.mjs
//
// No-op ESM stub for cytoscape family (cytoscape, cytoscape-fcose,
// cytoscape-cose-bilkent, cose-base, layout-base).
//
// Background: LingWen renders only `graph TD` flowcharts (mermaid
// flowDiagram chunk). mermaid 11.16 ships architecture diagrams in a
// separate chunk that statically imports the cytoscape family — which
// are webpack-bundled UMD modules that rollup's commonjs plugin cannot
// wrap (`Cannot set properties of undefined (setting 'exports')`).
// Aliasing these to a Proxy stub keeps the prod bundle small and the
// build clean. Architecture chunk is unreachable from our render path
// because flowDetector_v2 never matches `architecture` syntax.

const handler = {
  get(_target, prop) {
    if (prop === 'default') return proxy;
    if (prop === Symbol.toPrimitive) return undefined;
    return new Proxy(function () {}, handler);
  },
  apply() {
    return new Proxy({}, handler);
  },
  construct() {
    return new Proxy({}, handler);
  },
};

function proxy() {}

Object.setPrototypeOf(proxy, new Proxy(function () {}, handler));
proxy.default = proxy;

export default proxy;
```

**Note on Proxy semantics**: Vite alias treats this file as ESM. `import x from "./stub"` resolves to `proxy` (default export). `import { foo } from "./stub"` resolves to `undefined` (foo is undefined; if anyone destructures, they get undefined and a warning, not a crash). We expect zero destructuring in mermaid's startup path.

### 3.2 Modify: `apps/dashboard/vite.config.js`

Add `resolve.alias` block. Place alias after `import { fileURLToPath }` import, before `defineConfig`:

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath } from 'node:url'

// === Phase 114: cytoscape family stub ===
// mermaid 11.16 architectureDiagram chunk statically imports
// cytoscape/cytoscape-fcose/cytoscape-cose-bilkent/cose-base/layout-base.
// These are webpack-bundled UMD modules that rollup's commonjs plugin
// can't wrap. Alias to no-op ESM stub because LingWen never renders
// architecture diagrams (only `graph TD` flowcharts).
const cytoscapeStubPath = fileURLToPath(
  new URL('./scripts/cytoscape-stub.mjs', import.meta.url)
)
const CYTOSCAPE_STUB_ALIASES = [
  { find: /^cytoscape$/, replacement: cytoscapeStubPath },
  { find: /^cytoscape-fcose$/, replacement: cytoscapeStubPath },
  { find: /^cytoscape-cose-bilkent$/, replacement: cytoscapeStubPath },
  { find: /^cose-base$/, replacement: cytoscapeStubPath },
  { find: /^layout-base$/, replacement: cytoscapeStubPath },
]

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: CYTOSCAPE_STUB_ALIASES,
  },
  server: { /* unchanged */ },
  build: { /* unchanged */ },
  root: '.'
})
```

### 3.3 No other changes

- No package.json change
- No pnpm-lock.yaml change
- No mermaid source change
- No WorkflowGraph.vue change
- No knip.json change (stub file outside knip project globs)

## 4. Verification

| Check | Expected | Command |
|-------|----------|---------|
| Unit tests | 1545 PASS (unchanged) | `cd apps/dashboard && pnpm exec vitest run` |
| vue-tsc | 0 errors | `cd apps/dashboard && pnpm exec vue-tsc --noEmit` |
| Build | clean, no cytoscape chunk | `cd apps/dashboard && pnpm run build` |
| knip (CI) | exit 0 | `pnpm -C apps/dashboard exec knip` |
| knip (root) | exit 0 | `pnpm knip` |
| Dev mode | renders 4 routes | `pnpm dev` + curl + check body |
| Prod mode | renders 4 routes | `pnpm build && pnpm preview --port 4173 --strictPort` + Playwright check |
| Body length | > 0 for all 4 routes | `expect(bodyText).toBeGreaterThan(0)` |
| Web Vitals | recorded 4×3×5 = 60 measurements | Playwright run of `tests/e2e-smoke/web-vitals.spec.js` |

## 5. Rollback

If stub breaks mermaid's flowchart render:

1. Revert vite.config.js + delete stub file
2. `pnpm run build` to regenerate dist
3. Master returns to current (broken prod preview) state

Risk is contained: 2 file changes, no source code touched, no deps modified.

## 6. Out of scope

- Replacing cytoscape with vis-network (Option C from brainstorm)
- Accepting dev baseline (Option B from brainstorm)
- Patching cytoscape UMD via pnpm patches
- Writing custom rollup plugin

## 7. Acceptance criteria

- ✅ Tests 1545 PASS
- ✅ vue-tsc 0 errors
- ✅ Build clean, no `cytoscape-*.js` chunk in `dist/assets/`
- ✅ knip exit 0 (root + CI)
- ✅ pnpm preview: 4 routes render with body.length > 0
- ✅ Web Vitals prod baseline recorded (4 routes × 3 runs × 5 metrics)
- ✅ Prod baseline ≥ Phase 106 dev baseline (prod should be faster or equal — dev has HMR overhead)

## 8. Estimated work

- Write stub file: 5 min
- Modify vite.config.js: 5 min
- Build + manual preview test: 10 min
- Playwright check: 5 min
- Web Vitals baseline run: 15 min
- Verification (knip, tests, vue-tsc): 5 min
- **Total**: ~45 min