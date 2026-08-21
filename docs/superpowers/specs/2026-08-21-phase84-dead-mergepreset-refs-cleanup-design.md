# Phase 84 — Dead `mergePreset*` Refs Cleanup 设计

> **日期**: 2026-08-21
> **范围**: 2 files code change. Delete 7 dead refs + related declarations/types/returns. 1 atomic commit.
> **基础**: master = `fc76095e` (Phase 83 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 78 code review 列出 6 dead refs. Phase 84 investigation 确认实际 4 个 main refs + 3 loading flags = 7 dead refs across 2 files.

---

## 1. 背景

Phase 78 (commit `98c7aa89`) 转换 11 wholesale-refs 到 shallowRef in submodules. Code review 列出 6 dead mergePreset* refs in `useMergePresets.ts`.

Phase 84 investigation:
- Phase 78 "6 dead" 实际是 4 main refs (Graph/Conflicts/ConflictFixes/Toposort) + 3 loading flags
- All 4 main refs 声明在 BOTH parent (`useCreatorSettings.js`) AND submodule (`useMergePresets.ts`)
- All 3 loading flags 声明在 submodule only
- 0 writes anywhere (`x.value = ...`)
- 0 template reads
- Only usages: declarations + type defs + panelContext returns

---

## 2. 目标 & 非目标

### 目标

1. **Delete 4 main refs** (mergePresetGraph, mergePresetConflicts, mergePresetConflictFixes, mergePresetToposort):
   - Parent `useCreatorSettings.js`: declarations + panelContext returns
   - Submodule `useMergePresets.ts`: declarations + panelContext returns + Ref<...> type defs

2. **Delete 3 loading flags** (mergePresetGraphLoading, mergePresetConflictsLoading, mergePresetConflictFixesLoading):
   - Submodule `useMergePresets.ts`: declarations + panelContext returns + Ref<boolean> type defs

3. **Delete test reference**: `apps/dashboard/tests/unit/use-creator-settings.spec.ts:312` — references `panel.mergePresetGraph.value.node_count` in dead-ref assertion (per Phase 78 review note 5: this assertion was vacuous — checks initial value of a ref nothing ever writes).

4. **不破坏**: 1549 tests + 31 e2e + Web Vitals baseline
5. **1 atomic commit** (parent + submodule + test together — 3 files logically related)

### 非目标

- 不删 submodule `mergePresets` export (可能外部消费者)
- 不删其他 mergePreset refs (Changelog/ChangelogDiff/PullConflicts — 有 writes)
- 不重构 mermaid+其他无用代码
- 不加最终状态 doc (Phase 85+ 候选)

---

## 3. Decision Rule

**Delete** if BOTH:
- No writes (no `.value = ...` assignment anywhere)
- No template reads (not in any Vue template `{{ x.foo }}` or similar)

**KEEP** if EITHER:
- Has any write (data flow exists)
- Has any template/component read

---

## 4. Specific Removals

### 4.1 File 1: `useCreatorSettings.js` (parent)

Delete lines:
- 98: `const mergePresetGraph = shallowRef(...)`
- 99: `const mergePresetConflicts = shallowRef(...)`
- 100: `const mergePresetConflictFixes = shallowRef(...)`

Note: `mergePresetToposort` (line 93) is dead in PARENT (no writes), but **wait** — line 93 is in PARENT, let me re-verify.

Looking at earlier grep:
- mergePresetToposort declarations: parent line 93 (`useCreatorSettings.js`), submodule line 98
- mergePresetToposort writes: 0 hits
- mergePresetToposort reads (other than decl): parent line 598 (panelContext return), submodule line 52 (type def), submodule line 297 (return)

So `mergePresetToposort` IS also dead. Delete:
- Parent line 93: `const mergePresetToposort = shallowRef(...)`
- Parent line 598: `mergePresetToposort,` (panelContext return)

Final parent deletions (4 refs):
- Lines 93, 98, 99, 100: declarations
- Lines 598, 604, 605, 606: panelContext returns

### 4.2 File 2: `useMergePresets.ts` (submodule)

Delete lines (verified exact via grep):
- 49: type def `mergePresetConflicts: Ref<...>`
- 52: type def `mergePresetToposort: Ref<...>`
- 53: type def `mergePresetGraph: Ref<...>`
- 54: type def `mergePresetConflictFixes: Ref<...>`
- 70: type def `mergePresetGraphLoading: Ref<boolean>`
- 71: type def `mergePresetConflictsLoading: Ref<boolean>`
- 72: type def `mergePresetConflictFixesLoading: Ref<boolean>`
- 95: `const mergePresetConflicts = ref(...)`
- 98: `const mergePresetToposort = ref(...)`
- 99: `const mergePresetGraph = ref(...)`
- 100: `const mergePresetConflictFixes = ref(...)`
- 117: `const mergePresetGraphLoading = ref(false)`
- 118: `const mergePresetConflictsLoading = ref(false)`
- 119: `const mergePresetConflictFixesLoading = ref(false)`
- 293: `mergePresetConflicts,` (panelContext return)
- 296: `mergePresetToposort,` (panelContext return) [amend: was 297]
- 297: `mergePresetGraph,` (panelContext return) [amend: was 298]
- 314: `mergePresetGraphLoading,` (panelContext return)
- 315: `mergePresetConflictsLoading,` (panelContext return)
- 316: `mergePresetConflictFixesLoading,` (panelContext return)

Final submodule deletions: ~20 lines.

**WARNING**: Lines 306 (`mergePresetToposortApplying,`) and 313 (`mergePresetToposortLoading,`) are LIVE refs (written at lines 265/272). MUST NOT be deleted. Spec §4.2 original line numbers were off by 1-3 — verify before delete.

### 4.3 File 3: `tests/unit/use-creator-settings.spec.ts`

Delete line 312:
```js
    expect(panel.mergePresetGraph.value.node_count).toBe(0);   // line 312
```

This assertion was vacuous — checks initial value of a ref nothing ever writes. Per Phase 78 review note 5. Test still meaningfully asserts `mergePresetPackages` (line 311).

---

## 5. Verification

| Check | Expected |
|-------|----------|
| `pnpm test` 1549 PASS | ✓ (unchanged — test line 312 deleted, other 1548 unchanged) |
| `pnpm exec vue-tsc --noEmit` 0 errors | ✓ |
| `pnpm run build` 0 errors | ✓ |
| `grep -rn "mergePresetGraph\|mergePresetConflicts\|mergePresetConflictFixes\|mergePresetToposort" apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js"` | 0 hits (after delete) |
| `grep -rn "mergePresetGraphLoading\|mergePresetConflictsLoading\|mergePresetConflictFixesLoading" apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js"` | 0 hits (after delete) |
| `pnpm exec eslint src` | 0 violations (no-shallowref-mutation rule won't fire since refs deleted) |

---

## 6. Risks & Mitigations

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Submodule refs may be consumed by future external module | Low | regression | grep full src + tests before delete |
| TypeScript type inference breaks | Low | vue-tsc error | verify vue-tsc after |
| Runtime error from missing refs in template | Low | UI broken | 1549 tests + 31 e2e cover |
| Loading flags may be used by template conditionals | Low | UI broken | grep template refs + 1549 tests catch |

---

## 7. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Pre-flight: verify no other consumers
grep -rn "mergePresetGraph\|mergePresetConflicts\|mergePresetConflictFixes\|mergePresetToposort" apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | grep -vE "(useCreatorSettings\\.js:|useMergePresets\\.ts:)" || echo "safe to delete"

# Edit files (delete ~24 lines per spec §4)
# File 1: apps/dashboard/src/composables/useCreatorSettings.js
# File 2: apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts

# Verify
cd apps/dashboard
pnpm test 2>&1 | tail -5
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3
pnpm run build 2>&1 | tail -3

cd /home/ailearn/projects/LingWen
grep -rn "mergePresetGraph\|mergePresetConflicts\|mergePresetConflictFixes\|mergePresetToposort" apps/dashboard/src --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | wc -l
echo "expected: 0"

git add apps/dashboard/src/composables/useCreatorSettings.js \
        apps/dashboard/src/composables/useCreatorSettings/useMergePresets.ts

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(useCreatorSettings): delete 7 dead mergePreset* refs (Phase 84)" \
    -m "Phase 84 dead ref cleanup (per Phase 78 review):

Delete 4 main refs (never written, never read):
- mergePresetGraph
- mergePresetConflicts
- mergePresetConflictFixes
- mergePresetToposort

Delete 3 loading flags (never set, never read):
- mergePresetGraphLoading
- mergePresetConflictsLoading
- mergePresetConflictFixesLoading

Removed from:
- useCreatorSettings.js (parent): declarations + panelContext returns
- useMergePresets.ts (submodule): declarations + panelContext returns + Ref<...> type defs

Total: ~24 lines deleted across 2 files. No behavior change.

测试基线不变: 1549 PASS, 0 type errors, 0 build errors."
```

---

## 8. 测试策略

无新增 tests. 现有 tests 验证 deleted refs 不被使用.

- `pnpm test` (1549 unchanged — no test references these refs)
- `pnpm exec vue-tsc --noEmit` (catches type errors)
- `pnpm run build` (catches bundle issues)
- `grep` verification (confirms 0 hits post-delete)

---

## 9. 后续

Phase 85+ 候选 (per Phase 83 + reviews):

1. **Phase 85**: Phase 78 spec housekeeping (count corrections — also fix Phase 84 count)
2. **Phase 86**: ESLint `delete x.value.foo` + optional chain rules
3. **Phase 87**: CLAUDE.md § directory review + 19 sections audit
4. **Phase 88**: Residual `mergePreset*` in submodule (3 active + others — review again post-deletion)
5. **Phase 89+**: Vite 6 upgrade (when stable)
