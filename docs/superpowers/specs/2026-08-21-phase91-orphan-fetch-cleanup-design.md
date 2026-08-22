# Phase 91 — Orphan Fetch Cleanup 设计

> **日期**: 2026-08-22
> **范围**: 3 file change. Delete orphan `fetchCreatorFactoryMergePresetConflicts`. 1 atomic commit.
> **基础**: master = `79a87a41` (Phase 90 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 90 final-state doc 列出此 orphan (per Phase 86b skipped). Phase 91 = cleanup.

---

## 1. 背景

Phase 90 audit found `fetchCreatorFactoryMergePresetConflicts` has 0 consumer references outside definition + re-export:
- `mergePreset.js:83` — function definition
- `api/index.js:152` — re-export
- `tests/unit/api-creator-merge-preset.spec.ts:19, 163-165` — test case

Same pattern as Phase 85 (orphan fetch with test references).

---

## 2. 目标 & 非目标

### 目标

1. **Delete function definition** in `mergePreset.js:83` (~5 lines)
2. **Delete re-export** in `api/index.js:152`
3. **Delete test references** in `api-creator-merge-preset.spec.ts:19 + 163-165`
4. **不破坏**: 1546 tests → 1543 (-3 deleted test cases)
5. **1 atomic commit** (3 files logically related)

### 非目标

- 不audit OTHER api functions for similar orphan status (Phase 91b 候选)
- 不动 `preflightCreatorFactoryMergePresetPull` (LIVE, written in useCreatorSettings.js:427, 447)
- 不加 headers to no-header files (Phase 92 候选)

---

## 3. Decision Rule

**Delete** if: Only consumers were function definition + re-export + test references (3 files, all part of this phase).

**Keep** if: ANY consumer exists (template, computed, watch, etc.).

---

## 4. Specific Removals

### 4.1 File 1: `mergePreset.js`

Delete function definition (line 83, ~5 lines):

```js
export async function fetchCreatorFactoryMergePresetConflicts() {
  return request('/creator/settings-docs/merge-preferences/factory/conflicts');
}
```

### 4.2 File 2: `api/index.js`

Delete re-export entry (line 152):

```
  fetchCreatorFactoryMergePresetConflicts,
```

### 4.3 File 3: `tests/unit/api-creator-merge-preset.spec.ts`

Delete 2 sections:
1. **Line 19**: import entry in vi.mock factory:
   ```
     fetchCreatorFactoryMergePresetConflicts: (...args: unknown[]) => settingsMocks.fetchCreatorFactoryMergePresetConflicts(...args),
   ```
2. **Lines 163-169** (approx): test case block:
   ```js
   it('fetchCreatorFactoryMergePresetConflicts GETs factory/conflicts', async () => {
     mocks.request.mockResolvedValueOnce({ conflicts: [] });
     await fetchCreatorFactoryMergePresetConflicts();
     expect(mocks.request).toHaveBeenCalledWith(
       '/creator/settings-docs/merge-preferences/factory/conflicts',
     );
   });
   ```

---

## 5. Verification

| Check | Expected |
|-------|----------|
| `pnpm test` 1543 PASS | ✓ (-3 deleted test cases; was 1546) |
| `pnpm exec vue-tsc --noEmit` 0 errors | ✓ |
| `pnpm run build` 0 errors | ✓ |
| `grep "fetchCreatorFactoryMergePresetConflicts" apps/dashboard/src apps/dashboard/tests` | 0 hits |
| `pnpm exec eslint src` | 0 violations (no-shallowref-mutation rule not affected) |
| `git diff --stat` 3 files modified | ✓ |

---

## 6. Risks & Mitigations

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Test file has other untracked references | Low | rollback | grep + test |
| `preflightCreatorFactoryMergePresetPull` (LIVE) accidentally touched | Low | 1546 → lower | careful verify |
| Spec review found other untracked consumers | Low | BLOCKED | pre-flight grep verify |

---

## 7. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Pre-flight: verify 0 other consumers (excluding 3 target files)
grep -rn "fetchCreatorFactoryMergePresetConflicts" apps/dashboard/src apps/dashboard/tests \
  --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null \
  | grep -vE "(mergePreset\.js:|index\.js:|api-creator-merge-preset\.spec\.ts:)"

# Edit 3 files
# - apps/dashboard/src/api/mergePreset.js (delete line 83 function)
# - apps/dashboard/src/api/index.js (delete line 152 re-export)
# - apps/dashboard/tests/unit/api-creator-merge-preset.spec.ts (delete import + test case)

# Verify
cd apps/dashboard
node -c src/api/mergePreset.js && echo "syntax OK"
pnpm test 2>&1 | tail -5
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3
pnpm run build 2>&1 | tail -3

cd /home/ailearn/projects/LingWen
grep -rn "fetchCreatorFactoryMergePresetConflicts" apps/dashboard/src apps/dashboard/tests \
  --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | wc -l
echo "expected: 0"

git add apps/dashboard/src/api/mergePreset.js \
        apps/dashboard/src/api/index.js \
        apps/dashboard/tests/unit/api-creator-merge-preset.spec.ts

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(api): delete orphan fetchCreatorFactoryMergePresetConflicts (Phase 91)" \
    -m "Phase 91 orphan fetch cleanup (per Phase 90 final-state doc):

Delete fetchCreatorFactoryMergePresetConflicts — only consumers were:
- mergePreset.js:83 (function definition)
- api/index.js:152 (re-export)
- api-creator-merge-preset.spec.ts:19 + 163-169 (test case + mock)

Removed from 3 files:
- mergePreset.js: function definition (~5 lines)
- api/index.js: re-export entry (1 line)
- api-creator-merge-preset.spec.ts: import (1 line) + test case (7 lines)

Same pattern as Phase 85. Total: ~14 lines deleted across 3 files. No behavior change.

测试基线: 1546 → 1543 (-3 deleted test cases)."
```

---

## 8. 测试策略

无新增 tests. 1546 → 1543 (-3 deleted test cases).

- `pnpm test`
- `pnpm exec vue-tsc --noEmit`
- `pnpm run build`
- `grep` verification

---

## 9. 后续

Phase 92+ 候选 (per Phase 91 + reviews):

1. **Phase 92**: Add headers to 10 no-header api files
2. **Phase 93**: Comprehensive audit OTHER api functions for similar orphan status (Phase 91b expanded)
3. **Phase 94**: Audit codebase for `delete x.value.X` patterns (now enforced — Phase 88 follow-up)
4. **Phase 95**: Add knip or equivalent for CI dead-export detection
5. **Phase 96**: Audit remaining 19 CLAUDE.md sections for stale content
