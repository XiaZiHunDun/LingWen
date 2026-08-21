# Phase 85 — Orphaned Fetch Cleanup 设计

> **日期**: 2026-08-21
> **范围**: 3 files code change. Delete 3 dead fetches. 1 atomic commit.
> **基础**: master = `6f45ec1b` (Phase 84 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 84 code review MEDIUM 发现 3 orphaned fetch imports (`fetchCreatorMergePresetGraph/Conflicts/ConflictFixes`) in `useMergePresets.ts`. Phase 85 扩展 sweep 到 api/index.js + api/mergePreset.js.

---

## 1. 背景

Phase 84 (commit `8fa5696a`) deleted 7 dead refs including:
- `mergePresetGraph`, `mergePresetConflicts`, `mergePresetConflictFixes` (3 main refs)
- These refs were the **only consumers** of 3 fetch functions:
  - `fetchCreatorMergePresetGraph`
  - `fetchCreatorMergePresetConflicts`
  - `fetchCreatorMergePresetConflictFixes`

Phase 84 code review flagged: "3 orphaned fetch imports in `useMergePresets.ts:19-21`". Phase 85 extends sweep to api layer.

---

## 2. 目标 & 非目标

### 目标

1. **Delete 3 imports** in `useMergePresets.ts` (line 19-21)
2. **Delete 3 re-exports** in `api/index.js` (line 146-148)
3. **Delete 3 function definitions** in `api/mergePreset.js` (lines 120, 124, 141)
4. **Delete 3 test cases** in `tests/unit/api-creator-merge-preset.spec.ts` (lines 235, 243, 269) — vacuous tests for now-dead functions
5. **Delete 9 dead mock references** in `tests/unit/use-creator-settings.spec.ts` (lines 24-26 settingsMocks + 55-57 vi.mock factory + 123-125 beforeEach mockResolvedValue)
6. **不破坏**: 1549 tests + 31 e2e + Web Vitals baseline + build
7. **1 atomic commit** (5 files logically related)

### 非目标

- 不查 backend Python endpoints (out of scope)
- 不动 submodule export (其他 LIVE exports still used)
- 不改 api/mergePreset.js structure (only 3 function definitions removed)

---

## 3. Decision Rule

**Delete** if: Only consumers were the 7 dead refs deleted in Phase 84 (verified via grep — 0 other consumers).

**Keep** if: ANY consumer exists (template, computed, watch, etc.).

---

## 4. Specific Removals

### 4.1 File 1: `useMergePresets.ts`

Lines 19-21 (in import block from `'../../api/index.js'`):
- `fetchCreatorMergePresetGraph,`
- `fetchCreatorMergePresetConflicts,`
- `fetchCreatorMergePresetConflictFixes,`

### 4.2 File 2: `api/index.js`

Lines 146-148 (re-exports from `'./mergePreset.js'`):
- `fetchCreatorMergePresetGraph,`
- `fetchCreatorMergePresetConflicts,`
- `fetchCreatorMergePresetConflictFixes,`

### 4.3 File 3: `api/mergePreset.js`

3 function definitions:
- Line 120: `export async function fetchCreatorMergePresetConflicts() { ... }`
- Line 124: `export async function fetchCreatorMergePresetConflictFixes() { ... }`
- Line 141: `export async function fetchCreatorMergePresetGraph() { ... }`

Each function is ~5-10 lines (function body + closing brace).

### 4.4 File 4: `tests/unit/api-creator-merge-preset.spec.ts`

3 test cases (vacuous — test now-dead functions):
- Line 235: `it('fetchCreatorMergePresetConflicts GETs preset-packages/conflicts', ...)`
- Line 243: `it('fetchCreatorMergePresetConflictFixes GETs preset-packages/conflicts/fixes', ...)`
- Line 269: `it('fetchCreatorMergePresetGraph GETs preset-packages/graph', ...)`

Each test block is ~7 lines (it() callback + assertions). Also delete the corresponding imports at lines 25, 26, 29 in the same file.

⚠️ Tests cover fetch functions directly. After deleting functions in api/mergePreset.js, these tests fail at module-resolution time. Must delete tests + imports together.

### 4.5 File 5: `tests/unit/use-creator-settings.spec.ts`

9 dead mock references (mocks for now-dead functions):
- Lines 24-26: 3 entries in `settingsMocks` object (`fetchCreatorMergePresetGraph: vi.fn()`, etc.)
- Lines 55-57: 3 entries in `vi.mock` factory (passthrough to settingsMocks)
- Lines 123-125: 3 `settingsMocks.<X>.mockResolvedValue()` calls in `beforeEach`

⚠️ `use-creator-settings.spec.ts:vi.mock` factory intercepts imports from `api/index.js`. After deleting the 3 re-exports, the mock factory would reference non-existent exports and fail at module-resolution time. Must delete mock entries together.

---

## 5. Verification

| Check | Expected |
|-------|----------|
| `pnpm test` 1549 PASS | ✓ (unchanged — 3 test cases removed, total count maintained) |
| `pnpm exec vue-tsc --noEmit` 0 errors | ✓ |
| `pnpm run build` 0 errors | ✓ |
| `grep -rn "fetchCreatorMergePresetGraph\|fetchCreatorMergePresetConflicts\|fetchCreatorMergePresetConflictFixes" apps/dashboard/src apps/dashboard/tests` | 0 hits (all 4 files clean) |
| `pnpm exec eslint src` | 0 violations |

---

## 6. Risks & Mitigations

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Future dev tries to use these functions | Low | confusion | git history preserves code; can revert + re-add if needed |
| Tree-shaking fails for `api/index.js` re-exports | Low | build error | vue-tsc + build verify |
| Related backend endpoint exists but frontend wrapper gone | Low | orphaned backend | out of scope (Phase 85+ candidate) |
| Other files may have additional dead imports this sweep misses | Low | leftover tech debt | explicit follow-up via Phase 86 (noUnusedLocals) or separate audit |

---

## 7. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Pre-flight: verify 0 other consumers
grep -rn "fetchCreatorMergePresetGraph\|fetchCreatorMergePresetConflicts\|fetchCreatorMergePresetConflictFixes" \
  apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null \
  | grep -vE "(useMergePresets\.ts:|api/index\.js:|api/mergePreset\.js:)"

# Edit 3 files
# - useMergePresets.ts (delete 3 imports)
# - api/index.js (delete 3 re-exports)
# - api/mergePreset.js (delete 3 function definitions)

# Verify
cd apps/dashboard
pnpm test 2>&1 | tail -5
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3
pnpm run build 2>&1 | tail -3

cd /home/ailearn/projects/LingWen
grep -rn "fetchCreatorMergePresetGraph\|fetchCreatorMergePresetConflicts\|fetchCreatorMergePresetConflictFixes" \
  apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | wc -l
echo "expected: 0"

git add apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts \
        apps/dashboard/src/api/index.js \
        apps/dashboard/src/api/mergePreset.js \
        apps/dashboard/tests/unit/api-creator-merge-preset.spec.ts \
        apps/dashboard/tests/unit/use-creator-settings.spec.ts

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(api): delete 3 orphaned mergePreset fetch functions (Phase 85)" \
    -m "Phase 85 dead code sweep (per Phase 84 review MEDIUM):

Delete 3 fetch functions (only consumers were Phase 84-deleted refs):
- fetchCreatorMergePresetGraph
- fetchCreatorMergePresetConflicts
- fetchCreatorMergePresetConflictFixes

Removed from:
- useMergePresets.ts (submodule imports, lines 19-21)
- api/index.js (re-exports, lines 146-148)
- api/mergePreset.js (function definitions, lines 120/124/141)

Total: ~15-20 lines deleted across 3 files. No behavior change.

测试基线不变: 1549 PASS, 0 type errors, 0 build errors."
```

---

## 8. 测试策略

无新增 tests. 现有 tests 验证 deleted functions 不被使用.

- `pnpm test` (1549 unchanged)
- `pnpm exec vue-tsc --noEmit`
- `pnpm run build`
- `grep` verification

---

## 9. 后续

Phase 86+ 候选 (per Phase 85 + reviews):

1. **Phase 86**: Enable `noUnusedLocals: true` in tsconfig.json (catches future dead imports)
2. **Phase 87**: Phase 78 spec housekeeping (count corrections)
3. **Phase 88**: ESLint `delete x.value.foo` + optional chain rules
4. **Phase 89**: CLAUDE.md § directory review + 19 sections audit
5. **Phase 90**: Backend Python endpoint audit (orphan mergePreset endpoints)
