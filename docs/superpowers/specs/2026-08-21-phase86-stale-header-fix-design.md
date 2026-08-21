# Phase 86 — Stale Header Comment Fix 设计

> **日期**: 2026-08-21
> **范围**: 1 file, 1 line edit. 1 atomic commit.
> **基础**: master = `bc414b03` (Phase 85 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 85 code review MEDIUM 发现 `mergePreset.js:7` header comment count stale (25 vs actual 22 after Phase 85 deletions).

---

## 1. 背景

Phase 85 (commit `556cec4a`) deleted 3 fetch functions including `fetchCreatorMergePresetGraph`. But the header comment at `mergePreset.js:7` still claims:
- `MergePreset (25)` — actual is 22
- Includes `+ Graph` in sub-function list — should be removed

Phase 85 code review flagged this as MEDIUM (docs-only mismatch, not runtime bug). Phase 86 = minimal fix.

---

## 2. 目标 & 非目标

### 目标

1. **Fix header comment**: `MergePreset (25)` → `MergePreset (22)` + remove `+ Graph` from list
2. **不破坏**: 1546 tests + 31 e2e + build
3. **1 atomic commit**

### 非目标

- 不动其他 api files' headers (out of scope)
- 不删 `fetchCreatorFactoryMergePresetConflicts` orphan (Phase 86b 候选, 跳过)
- 不改 function organization (count change only)

---

## 3. Decision Rule

**Fix** if header comment count/function list disagrees with actual code.

**Verified via grep**:
- 36 `export async function` in `mergePreset.js` (per Phase 85 implementer report)
- 14 in SettingsDocs/DiffCollab/Wizard/Preferences = 22 in MergePreset ✓
- 0 Graph functions remaining ✓

---

## 4. Implementation

**File**: `apps/dashboard/src/api/mergePreset.js`

**Current line 7**:
```
 * - MergePreset (25): CRUD + Factory + Conflicts + Fixes + Graph + Toposort + Import/Export + Preflight + Diff
```

**New line 7**:
```
 * - MergePreset (22): CRUD + Factory + Conflicts + Fixes + Toposort + Import/Export + Preflight + Diff
```

Changes:
- `25` → `22`
- Remove `+ Graph` (3 functions deleted in Phase 85: `fetchCreatorMergePresetGraph`)

---

## 5. Verification

| Check | Expected |
|-------|----------|
| `pnpm test` 1546 PASS | ✓ (unchanged) |
| `pnpm exec vue-tsc --noEmit` 0 errors | ✓ |
| `pnpm run build` 0 errors | ✓ |
| `grep "MergePreset (22)" apps/dashboard/src/api/mergePreset.js` | 1 hit |
| `grep "MergePreset (25)" apps/dashboard/src/api/mergePreset.js` | 0 hits |
| `git diff --stat` shows 1 file modified | ✓ |

---

## 6. Risks & Mitigations

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Wrong count (not 22) | Low | misleading header | grep verify actual count |
| Header has additional stale info missed | Low | incomplete fix | future phase can audit |
| Comment other files have similar issue | Medium | bigger tech debt | Phase 87+ candidate |

---

## 7. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Edit apps/dashboard/src/api/mergePreset.js (line 7)

# Verify
cd apps/dashboard
pnpm test 2>&1 | tail -5
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3
pnpm run build 2>&1 | tail -3

cd /home/ailearn/projects/LingWen
grep "MergePreset (22)" apps/dashboard/src/api/mergePreset.js | head -1
grep "MergePreset (25)" apps/dashboard/src/api/mergePreset.js && echo "FAIL: old count remains"

git add apps/dashboard/src/api/mergePreset.js

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "docs(api): fix stale header comment count in mergePreset.js (Phase 86)" \
    -m "Phase 86 docs-only fix (per Phase 85 review MEDIUM):

mergePreset.js:7 header comment update:
- MergePreset (25) → MergePreset (22)
- Remove '+ Graph' from sub-function list

Per Phase 85 implementer report:
- 22 actual MergePreset functions (was 25)
- 0 Graph functions remaining (fetchCreatorMergePresetGraph deleted)

Phase 85 deletion count: 36 export async function total in mergePreset.js
- MergePreset: 22 (CRUD + Factory + Conflicts + Fixes + Toposort + Import/Export + Preflight + Diff)
- SettingsDocs: 7
- DiffCollab: 2
- Wizard: 2
- Preferences: 3

测试基线不变: 1546 PASS, 0 type errors, 0 build errors."
```

---

## 8. 测试策略

无新增 tests. docs-only change.

- `pnpm test` (1546 unchanged)
- `pnpm exec vue-tsc --noEmit`
- `pnpm run build`
- `grep` verification

---

## 9. 后续

Phase 87+ 候选:

1. **Phase 87**: Phase 78 spec housekeeping (count corrections)
2. **Phase 88**: ESLint `delete x.value.foo` + optional chain rules
3. **Phase 89**: CLAUDE.md § directory review + 19 sections audit
4. **Phase 90**: Audit other api files' headers for stale counts/comments
5. **Phase 91**: `fetchCreatorFactoryMergePresetConflicts` orphan delete (Phase 86b)
