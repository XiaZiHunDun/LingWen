# Phase 80 — Vendor Chunk Split 设计

> **日期**: 2026-08-21
> **范围**: 1 vite.config.js edit + build verification. 1 atomic commit.
> **基础**: master = `076120d6` (Phase 79 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 76 baseline §4 列出 bundle size: vendor 407kB gz (1462kB raw) 是最大 chunk. Phase 71+72+74 已 lazy load 大部分 libs (echarts/mermaid/cytoscape/katex). vendor chunk catch-all 可能含 Naive UI (~80% of vendor typical).

---

## 1. 背景

Phase 76 baseline §4 bundle size table:
| Chunk | Gzipped |
|-------|---------|
| vendor | 407 kB |
| mermaid | 390 kB |
| echarts | 306 kB |
| cytoscape | 151 kB |
| katex | 78 kB |

echarts/mermaid/cytoscape/katex 都已 lazy (cytoscape + katex 是 mermaid 11.x 的 transitive deps). 

`vendor` chunk 是 catch-all: `if (id.includes('node_modules/')) return 'vendor';`. Likely 包含 Naive UI (~80%), @vicons, dayjs, lodash (separate), vue (separate), 等.

Phase 80 = split Naive UI out of vendor chunk.

---

## 2. 目标 & 非目标

### 目标

1. **vendor split**: Naive UI out of vendor catch-all
2. **Verify**: vendor chunk size drops, Naive UI chunk emerges
3. **不破坏**: 1549 tests + 31 e2e specs
4. **1 atomic commit**

### 非目标

- 不动 echarts/mermaid/cytoscape/katex (already lazy)
- 不动 lodash tree-shake (Phase 81+)
- 不动 app-specific chunks (CreatorPage lazy already done Phase 72)
- 不替换 Naive UI (框架替换 out of scope)
- 不动 vite base config (server/dev settings)

---

## 3. Implementation

### 3.1 Vite config change

File: `apps/dashboard/vite.config.js`

Add `'naive-ui': 'naive-ui'` to NAMED map:

```js
manualChunks(id) {
  // Named chunks: package → chunk name
  const NAMED = {
    echarts: 'echarts',
    mermaid: 'mermaid',
    cytoscape: 'cytoscape',
    katex: 'katex',
    'naive-ui': 'naive-ui',  // ← NEW: extract from vendor
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

### 3.2 Expected outcome

Before:
- vendor-*.js: 407 kB gz (1462 kB raw)
- (no naive-ui chunk)

After:
- naive-ui-*.js: ~320 kB gz (Naive UI moved out)
- vendor-*.js: ~80 kB gz (other libs)
- Total reduction: ~7 kB gz (or similar — depends on what's in vendor)

The split itself doesn't reduce initial-load size much (Naive UI still in initial bundle), but:
- Easier analysis (know exactly what Naive UI costs)
- Foundation for future lazy loading (Phase 81+ candidates)

---

## 4. Verification

| Check | Expected |
|-------|----------|
| `pnpm run build` succeeds | ✓ |
| `dist/assets/naive-ui-*.js` chunk exists | ✓ |
| `vendor-*.js` size drops significantly | ≥50kB gz |
| Total chunks sum = previous total | sanity check |
| `pnpm test` 1549 PASS | ✓ (unchanged) |
| `pnpm exec vue-tsc --noEmit` 0 errors | ✓ |
| `pnpm run build` 0 errors | ✓ |

### 4.1 Build output comparison

Save before/after chunk sizes:

```
Before (Phase 79):
dist/assets/vendor-lk4byDOd.js      1,461.54 kB │ gzip: 406.86 kB
(no naive-ui chunk)

After (Phase 80):
dist/assets/naive-ui-XXX.js         ~1,XXX.XX kB │ gzip: ~320.XX kB
dist/assets/vendor-XXX.js             ~XXX.XX kB │ gzip: ~80.XX kB
```

---

## 5. Risks

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Naive UI 内部 cross-chunk imports | Low | build error | vite 会报错, 立即 rollback |
| Split 后 vendor 不减小 (Naive UI 在别处) | Medium | no gain | 查 actual chunk content |
| Vite warning about chunk size > limit | Low | warning only | adjust chunkSizeWarningLimit if needed |
| Functional regression (Naive UI broken at runtime) | Low | UI broken | 1549 tests + 31 e2e + dev server manual smoke |

---

## 6. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# 1. Edit vite.config.js (add 'naive-ui': 'naive-ui')

# 2. Build
cd apps/dashboard && pnpm run build 2>&1 | tail -20

# 3. Verify
ls -la dist/assets/naive-ui-*.js dist/assets/vendor-*.js 2>&1 | head -5

# 4. Tests
pnpm test 2>&1 | tail -5

# 5. Commit
git add apps/dashboard/vite.config.js
git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "build(vite): extract naive-ui from vendor chunk (Phase 80)" \
    -m "Phase 80 vendor chunk split:

vite.config.js: add 'naive-ui': 'naive-ui' to manualChunks NAMED map.

Before: vendor-*.js = 1462kB raw / 407kB gz (Naive UI ~80% + other libs)
After: naive-ui-*.js = ~XXXkB raw / ~XXXkB gz, vendor-*.js = ~XXXkB raw / ~XXXkB gz

Foundation for future lazy loading of Naive UI components (Phase 81+ candidate).

测试基线不变: 1549 PASS, 0 type errors, 0 build errors."
```

---

## 7. 测试策略

无新增 tests. vite config edit + build verification.

- `pnpm run build` — confirm chunk split works
- `pnpm test` — 1549 unit tests unchanged
- `pnpm exec vue-tsc --noEmit` — type check unchanged
- Dev server manual smoke — verify Naive UI components still render

---

## 8. 后续

Phase 81+ 候选 (per Phase 80 + Handoff §6 + Phase 77/78 reviews):

1. **Phase 81**: Lazy load specific Naive UI components (e.g., NMessageProvider, NDialogProvider) on heavy pages
2. **Phase 82**: lodash tree-shake (10kB gz → possibly 0)
3. **Phase 83**: CLAUDE.md v13.1 housekeeping
4. **Phase 84**: ESLint rule `no-shallowref-mutation`
5. **Phase 85**: 7 dead `mergePreset*` refs cleanup
6. **Phase 86**: Phase 78 spec housekeeping (count corrections)
