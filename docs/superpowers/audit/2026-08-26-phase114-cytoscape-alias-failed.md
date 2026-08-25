# Phase 114 — Cytoscape Vite Alias Stub Attempt (Failed)

> **Date**: 2026-08-26
> **Goal**: Fix `pnpm preview` JS error to enable prod-mode Web Vitals baseline via Vite resolve.alias + ESM Proxy stub for cytoscape family.
> **Status**: ❌ **Attempt failed**. Same TDZ symptom as Phase 112C.
> **Recommendation**: Revert to Option B (accept dev baseline as authoritative). Do not retry cytoscape stub approaches without deeper investigation.

---

## 1. Background

Phase 110/111B/111C/112/112C documented the same `Cannot set properties of undefined (setting 'exports')` error in `pnpm preview` across 4 attempts. Phase 114 attempted Option A (Vite alias + ESM Proxy stub) to remove cytoscape from the prod bundle while keeping mermaid's flowchart path intact.

## 3. Phase 114 attempt

### 3.1 Approach

1. Created `apps/dashboard/scripts/cytoscape-stub.mjs` — ESM module exporting a Proxy function. Every access/call/construct returns a new Proxy (never undefined).
2. Modified `apps/dashboard/vite.config.js` — added `resolve.alias` mapping 5 packages (cytoscape, cytoscape-fcose, cytoscape-cose-bilkent, cose-base, layout-base) to the stub file.

### 3.2 Build result (PASS)

```
✓ built in 17.87s
dist/assets/ 81 files (no cytoscape-*.js, no cose-bilkent-*.js, no layout-base-*.js)
circular chunk: mermaid -> vendor -> mermaid  (known Phase 83 warning, harmless)
```

Build clean. No `FDLayoutConstants` traces in dist.

### 3.3 Test result (PASS)

```
vitest: 1545 passed (189 files)
vue-tsc: 0 errors
knip (root): exit 0
knip (CI): exit 0
```

### 3.4 Dev mode (PASS)

```
HTTP 200 /              (curl)
HTTP 200 /workflows
HTTP 200 /creator
```

### 3.5 Prod preview (FAIL)

```
[
  { "route": "/",              "bodyLength": 0, "errors": ["ReferenceError: Cannot access 'H' before initialization"] },
  { "route": "/workflows",     "bodyLength": 0, "errors": ["ReferenceError: Cannot access 'H' before initialization"] },
  { "route": "/creator",       "bodyLength": 0, "errors": ["ReferenceError: Cannot access 'H' before initialization"] },
  { "route": "/creator/write", "bodyLength": 0, "errors": ["ReferenceError: Cannot access 'H' before initialization"] }
]
```

Stack trace:
```
ReferenceError: Cannot access 'H' before initialization
    at new Theme (http://localhost:4173/assets/mermaid-DcPRGFNP.js:1:38279)
    at Object.getThemeVariables (http://localhost:4173/assets/mermaid-DcPRGFNP.js:1:55529)
    at http://localhost:4173/assets/mermaid-DcPRGFNP.js:1:182979
```

## 4. Root cause analysis

`H` is `It` in the minified vendor chunk (`It = new tJ`, where `tJ` is a jsdom-style DOMWrapper). `H` is exported from vendor (`c4 as H`).

The TDZ happens when `new Theme(...)` runs — Theme class body indirectly accesses `H` during construction. The Theme class lives in `chunks/mermaid.core/chunk-WYO6CB5R.mjs` (mermaid's themes bundle). Theme uses `khroma` functions (`adjust`, `darken`, `invert`, `isDark`, `lighten`) which may invoke `window.matchMedia`-like APIs through the DOMWrapper.

When cytoscape-family aliases resolve to Proxy stubs, **the order in which vendor chunk top-level statements execute changes** because rollup's chunk graph rearranges. The DOMWrapper instance (`H`) is no longer initialized before Theme class body needs it.

This is the **same root cause** as Phase 112C: "Stubbing cytoscape-related deps leaves a gap in mermaid's dependency graph. Mermaid (or one of its other deps) accesses something that was previously provided by cytoscape stubs."

## 5. Why Phase 114 differs from Phase 112C in approach but fails for the same reason

| Aspect | Phase 112C | Phase 114 |
|--------|------------|-----------|
| Stub file | `vite-plugins/cytoscape-stub.js` (Proxy, returns undefined) | `scripts/cytoscape-stub.mjs` (Proxy, returns Proxy) |
| Mechanism | Vite plugin (resolveId/load hooks) | Vite resolve.alias |
| Failure | TDZ in vendor chunk | TDZ in mermaid Theme class |
| Root | undefined propagation | module init order changed |

Both approaches break mermaid's chunk graph initialization. The Proxy that returns Proxy (Phase 114) is slightly safer (no undefined propagation) but the chunk graph ordering issue is unchanged.

## 6. Recommendation: revert to Option B

Per the Option B / Phase 110 recommendation already documented:

- **Dev baseline (Phase 106) remains the authoritative Web Vitals measurement**
- Document dev-mode baseline explicitly as conservative (dev numbers are typically lower than prod due to HMR overhead + no minification)
- Future fix attempts should consider: (a) custom rollup plugin with module-ID mapping to preserve init order, or (b) replace mermaid entirely with a flowchart-only library

Time invested in 5 phases (110, 111B, 111C, 112, 112C, 114) suggests cytoscape-family stubbing is not the right fix. **Stop attempting it.**

## 7. Files changed in Phase 114

| File | Commit | Action |
|------|--------|--------|
| `docs/superpowers/specs/2026-08-26-phase114-cytoscape-vite-alias-design.md` | `a7dd96ff` | **Kept** for reference |
| `docs/superpowers/plans/2026-08-26-phase114-cytoscape-vite-alias.md` | (uncommitted) | **Kept** for reference |
| `apps/dashboard/scripts/cytoscape-stub.mjs` | `91510f6a` | **Revert** |
| `apps/dashboard/vite.config.js` | `8da2ebfe` | **Revert** |
| `docs/superpowers/audit/2026-08-26-phase114-cytoscape-alias-failed.md` | (this file) | **Keep** |

## 8. Verification after revert

| Check | Expected |
|-------|----------|
| `pnpm exec vitest run` | 1545 PASS |
| `pnpm -C apps/dashboard exec knip` | exit 0 |
| `pnpm knip` | exit 0 |
| `pnpm preview` | same broken state as Phase 110 (current master baseline) |
| `pnpm dev` | works (4 routes render) |

## 9. Lessons learned (additive to Phase 112C)

1. **Same TDZ symptom means same root cause family**. Phase 112C and 114 both broke at "Cannot access X before initialization" — alias mechanism differs but graph reordering effect is the same.
2. **Stub variants don't help when graph reordering is the issue**. Returning Proxy instead of undefined is a marginal improvement; the underlying module-init order problem is unchanged.
3. **Build PASS ≠ runtime PASS**. Build emitted 0 cytoscape chunks (success), but mermaid startup still broke. Vite/rollup chunk separation doesn't preserve runtime initialization order.
4. **The right fix probably isn't stubbing**. Either custom rollup plugin with explicit module-ID mapping, or replacing mermaid. Stubbing has now failed twice (Phase 112C + 114).

## 10. Future options (not pursued)

| Option | Description | Estimated work |
|--------|-------------|----------------|
| Custom rollup plugin with module-ID map | Force cytoscape-family modules to keep their original webpack IDs in the combined shim chunk | 4-8 hours (high risk) |
| Replace mermaid with flowchart-only library | Use dagre or custom SVG renderer for `graph TD` syntax | 8-16 hours (feature work) |
| Migrate vite to webpack/rspack | Different CJS plugin handling, might wrap cytoscape correctly | 4-8 hours + dep change |
| Accept dev baseline as authoritative | No code change; document explicit policy | 0 (current state) |