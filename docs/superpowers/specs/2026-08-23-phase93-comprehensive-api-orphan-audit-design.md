# Phase 93 — Comprehensive API Orphan Audit (Delete `onApiError`) 设计

> **日期**: 2026-08-23
> **范围**: 1 file change. Delete orphan `onApiError` function. 1 atomic commit.
> **基础**: master = `99cbd9f7` (Phase 92 pushed)
> **作者**: 主控调度 (brainstorming → spec)
> **状态**: spec 草稿待 user review

> **背景**: Phase 91 follow-up = comprehensive api orphan audit. Phase 93 = audit + delete 1 confirmed orphan (`onApiError`).

---

## 1. 背景

Phase 91b follow-up: audit all api functions for orphan status. Phase 93 = execute audit + delete orphan found.

**Audit result**: Only 1 true orphan found across 11 candidates:
- `onApiError` in `core.js` — 0 consumers (not re-exported, no internal call site)

10 other candidates have test consumers → NOT orphans.

---

## 2. 目标 & 非目标

### 目标

1. **Delete `onApiError` function** in `core.js` (~5-7 lines + internal usage)
2. **不破坏**: 1545 tests + 31 e2e + build
3. **1 atomic commit**

### 非目标

- 不删其他 10 candidates (test consumers exist, NOT orphans)
- 不audit api/index.js re-exports (out of scope)
- 不改 core.js body (only delete onApiError function)

---

## 3. Audit Results (11 candidates)

| Function | File | Consumer Count | Status |
|----------|------|----------------|--------|
| `markApiOnline` | connectivity.js | 6 (incl. internal core.js) | NOT orphan |
| `markApiOffline` | connectivity.js | 4 (incl. internal core.js) | NOT orphan |
| `onApiError` | **core.js** | **0** | **TRUE ORPHAN** |
| `exportCreatorTemplateApprovalAudit` | creator.js | 2 (tests) | NOT orphan |
| `fetchCreatorGlobalMergePreferences` | mergePreset.js | 4 (tests) | NOT orphan |
| `deleteCreatorFactoryMergePresetPackage` | mergePreset.js | 4 (tests) | NOT orphan |
| `resolveCreatorFactoryMergePresetConflict` | mergePreset.js | 4 (tests) | NOT orphan |
| `fetchCreatorFactoryVolumeTemplates` | volumeTemplate.js | 4 (tests) | NOT orphan |
| `fetchActiveWorkflow` | workflows.js | 2 (tests) | NOT orphan |
| `fetchHealth` | health.js | 12 (tests + app code) | NOT orphan |
| `fetchStudioActive` | studio.js | 1 (test mock) | NOT orphan |
| `applyCreatorVolumeTemplate` | creator.js | 14 (tests + app code) | NOT orphan |

(13 rows; first 3 from connectivity.js adjusted, 10 from main audit.)

---

## 4. Decision Rule

**Delete** if: 0 consumers outside self file (excluding re-export files).
**Verified** for `onApiError`: 0 src/ consumers, 0 tests/ consumers, not re-exported in `api/index.js`.

---

## 5. Specific Removal

**File**: `apps/dashboard/src/api/core.js`

Read current state of `onApiError`:

```bash
grep -n "onApiError" /home/ailearn/projects/LingWen/apps/dashboard/src/api/core.js
```

Delete:
1. The `onApiError` function definition (~5-7 lines)
2. Any reference inside `request` function (if present)

---

## 6. Verification

| Check | Expected |
|-------|----------|
| `pnpm test` 1545 PASS | ✓ (unchanged) |
| `pnpm exec vue-tsc --noEmit` 0 errors | ✓ |
| `pnpm run build` 0 errors | ✓ |
| `grep "onApiError" src tests` overall | 0 hits |
| `git diff --stat` 1 file modified | ✓ |

---

## 7. Risks & Mitigations

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| `onApiError` referenced dynamically (computed key) | Low | rollback | grep + visual check |
| Comment in core.js references onApiError | Low | orphaned comment | grep + visual |
| Other file references onApiError indirectly | Low | rollback | final grep verify |

---

## 8. Commit 模板

```bash
cd /home/ailearn/projects/LingWen

# Edit apps/dashboard/src/api/core.js (delete onApiError function + references)

# Verify
cd apps/dashboard
node -c src/api/core.js && echo "syntax OK"
grep "onApiError" src tests --include="*.vue" --include="*.ts" --include="*.js" 2>/dev/null | wc -l
echo "expected: 0"
pnpm test 2>&1 | tail -5
pnpm exec vue-tsc --noEmit --pretty false 2>&1 | tail -3
pnpm run build 2>&1 | tail -3

cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/api/core.js

git -c user.name="Claude" -c user.email="claude@anthropic.local" \
    commit -m "refactor(api): delete orphan onApiError (Phase 93)

Phase 93 comprehensive api orphan audit. Only 1 true orphan found:
- onApiError (core.js) — 0 consumers (not re-exported, no internal call site)

10 other candidates have test consumers (NOT orphans):
- markApiOnline/Offline (connectivity.js): internal core.js callers
- exportCreatorTemplateApprovalAudit (creator.js): tests
- fetchCreatorGlobalMergePreferences (mergePreset.js): tests
- deleteCreatorFactoryMergePresetPackage (mergePreset.js): tests
- resolveCreatorFactoryMergePresetConflict (mergePreset.js): tests
- fetchCreatorFactoryVolumeTemplates (volumeTemplate.js): tests
- fetchActiveWorkflow (workflows.js): tests
- fetchHealth (health.js): tests + app code
- fetchStudioActive (studio.js): tests
- applyCreatorVolumeTemplate (creator.js): tests + app code

Total: 1 file modified, ~5-7 lines deleted.

测试基线不变: 1545 PASS, 0 type errors, 0 build errors."
```

---

## 9. 测试策略

无新增 tests. 1545 tests unchanged (function had no consumers).

- `pnpm test`
- `pnpm exec vue-tsc --noEmit`
- `pnpm run build`
- `grep` count verification

---

## 10. 后续

Phase 94+ 候选 (per Phase 93 + reviews):

1. **Phase 94**: Audit codebase for `delete x.value.X` patterns (now enforced — Phase 88 follow-up)
2. **Phase 95**: Add knip or equivalent for CI dead-export detection
3. **Phase 96**: Audit remaining 19 CLAUDE.md sections for stale content
4. **Phase 97**: Audit `api/index.js` re-exports for stale entries
