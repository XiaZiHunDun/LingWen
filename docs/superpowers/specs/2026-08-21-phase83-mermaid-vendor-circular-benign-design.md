# Phase 83 — Mermaid-Vendor Circular Chunk Warning 设计

> **日期**: 2026-08-21
> **范围**: 1 file (vite.config.js) comment update. 1 atomic commit.
> **基础**: master = `45f506d2` (Phase 82 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 80 build verification 报告 `Circular chunk: mermaid -> vendor -> mermaid` warning. Phase 83 investigation 决定 acceptance as benign + document.

---

## 1. 背景

Phase 80 (commit `a6d4afe2`) verification 报告:
```
Circular chunk: mermaid -> vendor -> mermaid. Please adjust the manual chunk logic for these chunks.
```

Phase 83 investigation:
- `mermaid` chunk imports ~100+ Vue 3 internal symbols (createVNode, h, etc.) from `vendor` — legitimate dependency
- `vendor` chunk imports 1 symbol `_ as ln` from `mermaid` — mermaid exports consumed by some markdown library (likely marked.js or markdown-it with mermaid extension)

**Decision**: True fix requires moving the mermaid-consuming library out of vendor, OR merging mermaid into vendor (loses lazy loading). Both have trade-offs.

**Outcome**: Warning is **benign** — build succeeds, runtime works. Accept trade-off + document explicitly.

---

## 2. 目标 & 非目标

### 目标

1. **Update vite.config.js**: replace Phase 80 comment with Phase 83 verbose investigation note
2. **Document trade-off**: explicitly explain why mermaid↔vendor circular is acceptable
3. **不破坏**: 1549 tests + 31 e2e + Web Vitals baseline
4. **1 atomic commit**

### 非目标

- 不强制 fix 循环依赖 (build works)
- 不改 manualChunks (current is correct for our use case)
- 不refactor mermaid-using libraries
- 不suppress warning with `onwarn` (cosmetic only, 不值得 commit)
- 不加 docs/perf/ 报告 (warning is informational only)

---

## 3. Implementation

### 3.1 Edit vite.config.js comment

Replace existing manualChunks comment with Phase 83 version:

```js
        manualChunks(id) {
          // Named chunks: package → chunk name
          //
          // === Phase 83 investigation (mermaid <-> vendor circular) ===
          //
          // Build emits: `Circular chunk: mermaid -> vendor -> mermaid`
          //
          // Analysis:
          // - mermaid chunk imports ~100+ Vue 3 internal symbols (createVNode, h, etc.)
          //   from vendor — LEGITIMATE dependency (mermaid needs Vue runtime)
          // - vendor chunk imports 1 symbol (_ as ln) from mermaid
          //   — likely a markdown lib (marked.js / markdown-it with mermaid extension)
          //   consuming a mermaid export
          //
          // Trade-off accepted:
          // - Build succeeds with warning only — runtime works
          // - True fix requires moving mermaid-consuming lib out of vendor
          //   OR merging mermaid into vendor (loses lazy-load isolation)
          // - Both options worse than current state
          //
          // Future work:
          // - Phase 84+ may delete dead mergePreset* refs (cleanup, unrelated)
          // - Phase 78+ reviews noted 7 dead refs in useMergePresets.ts
          //   — deletion may slightly alter chunk graph
          // - Vite upgrade could change warning behavior — revisit if upgraded
          //
          // === Phase 80 / Phase 71 chunk history ===
          //
          // - Phase 71: initial 8 chunks + vendor catch-all
          // - Phase 80: naive-ui already in NAMED (3.11kB chunk, but most code
          //   in vendor due to inter-deps with vue/pinia — see Phase 80 commit
          //   7516865d for verification details
          //
          const NAMED = {
            echarts: 'echarts',
            mermaid: 'mermaid',
            cytoscape: 'cytoscape',
            katex: 'katex',
            'naive-ui': 'naive-ui',
            'vue-router': 'vue-router',
            pinia: 'pinia',
            '@vicons': 'vicons',
            lodash: 'lodash',
            dayjs: 'dayjs',
          };
          for (const [pkg, chunk] of Object.entries(NAMED)) {
            if (id.includes(`node_modules/${pkg}`)) return chunk;
          }
          // 剩余 node_modules 合并到 vendor chunk
          if (id.includes('node_modules/')) return 'vendor';
        },
```

### 3.2 Build verification

After edit, verify build still succeeds with same warning:

```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm run build 2>&1 | tail -10
```

Expected: `✓ built in <time>` with `Circular chunk: mermaid -> vendor -> mermaid` warning (acceptable).

---

## 4. Verification

| Check | Expected |
|-------|----------|
| `pnpm run build` succeeds | ✓ |
| Circular chunk warning still emitted (now documented) | ✓ |
| `pnpm test` 1549 PASS | ✓ (unchanged) |
| `pnpm exec vue-tsc --noEmit` 0 errors | ✓ |
| `git diff --stat` shows 1 file modified | ✓ |

---

## 5. Risks & Mitigations

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Future dev tries to "fix" warning → breaks lazy load | Low | regression | explicit comment in vite.config.js explains trade-off |
| Vite upgrade → warning becomes error | Low | build broken | Vite version pinned; revisit on major upgrade |
| Document becomes stale over time | Medium | misleading | link to Phase 83 spec + final-state |

---

## 6. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Edit vite.config.js (replace existing comment with verbose Phase 83 note)

# Verify
cd apps/dashboard
pnpm run build 2>&1 | tail -5
pnpm test 2>&1 | tail -5
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3

cd /home/ailearn/projects/LingWen
git add apps/dashboard/vite.config.js

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(vite): document mermaid-vendor circular warning as benign (Phase 83)" \
    -m "Phase 83 mermaid-vendor circular chunk warning investigation:

vite.config.js: replace Phase 80 brief comment with verbose Phase 83 analysis.

Analysis:
- mermaid chunk imports ~100+ Vue 3 symbols from vendor (legitimate)
- vendor chunk imports 1 symbol (_ as ln) from mermaid (likely marked.js or similar)
- Build succeeds with warning only — runtime works
- True fix requires moving markdown lib out of vendor OR merging mermaid
  into vendor (loses lazy-load isolation). Both worse than current.

Accept trade-off + document explicitly.

测试基线不变: 1549 PASS, 0 type errors, build OK with circular warning."
```

---

## 7. 测试策略

无新增 tests. vite.config.js comment-only change.

- `pnpm run build` — circular warning still present (documented)
- `pnpm test` — 1549 PASS unchanged
- `pnpm exec vue-tsc --noEmit` — 0 errors

---

## 8. 后续

Phase 84+ 候选 (per Phase 83 + reviews):

1. **Phase 84**: 7 dead `mergePreset*` refs cleanup (Phase 78 review) — may simplify chunk graph
2. **Phase 85**: Phase 78 spec housekeeping (count corrections)
3. **Phase 86**: ESLint `delete x.value.foo` + optional chain rules (Phase 82 MEDIUM)
4. **Phase 87**: CLAUDE.md § directory review + other 19 sections
5. **Phase 88+**: Vite 6 upgrade (when stable) — may resolve circular differently
