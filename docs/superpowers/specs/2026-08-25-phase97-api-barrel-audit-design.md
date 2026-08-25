# Phase 97 — Audit & Resolve `apps/dashboard/src/api/index.js` Barrel Re-exports

> **Date**: 2026-08-25
> **Phase**: 97
> **Source**: Phase 99 knip CI integration follow-up + handoff §5 (`Audit api/index.js re-exports for stale entries`)
> **Status**: Design

---

## 1. Context

`apps/dashboard/src/api/index.js` is a barrel re-export module for the dashboard's API layer. It re-exports 158 functions from 8 sub-modules (connectivity, health, decisions, workflows, cvg, budgets, studio, creator).

Per Phase 103's spec, this barrel was added to `apps/dashboard/knip.json#ignore` as "public-API barrel". Phase 97 audits whether the barrel's re-exports are actually used, and removes stale entries.

**Phase 97 explore subagent** verified every re-exported function by grep. Result:

| Bucket | Count | Action |
 |--------|-------|--------|
| USED (via barrel by app code or tests) | 147 | keep |
| USED (direct-path only — barrel adds no value) | 7 | remove from barrel; keep submodule export |
| TRULY DEAD (zero importers anywhere) | 4 | delete from BOTH barrel + submodule |

---

## 2. Goal

Remove 4 truly-dead functions entirely (barrel entry + defining export) and remove 7 redundant barrel entries (function remains accessible via direct submodule path). End-state: `api/index.js` is leaner (drops 11 of 158 lines), and 4 functions that are genuinely unused are removed from the codebase.

---

## 3. Non-Goals

- **NOT** deleting the `api/index.js` barrel itself — it remains a public-API surface for the remaining 147 functions.
- **NOT** modifying any consumer (callers already use direct paths for the 7 dropped barrel entries).
- **NOT** removing `api/index.js` from `knip.json#ignore` — it remains a barrel.
- **NOT** modifying any submodule file other than removing the 4 dead exports.
- **NOT** renaming or restructuring the barrel.
- **NOT** addressing the 9 non-re-exported api/ files (`agent.js`, `core.js`, `memory.js`, `mergePreset.js`, `onboarding.js`, `publish.js`, `templateApproval.js`, `volumePlan.js`, `volumeTemplate.js`) — they're unrelated to the barrel audit.

---

## 4. Design

### 4.1 Decision Matrix (verified by Phase 97 explore subagent)

#### Bucket 4 — TRULY DEAD (delete from BOTH barrel + submodule)

| # | Function | Defining file | Action |
|---|----------|---------------|--------|
| 1 | `fetchHealth` | `apps/dashboard/src/api/health.js:39` | Drop `export` keyword (convert to local function); drop from barrel |
| 2 | `fetchActiveWorkflow` | `apps/dashboard/src/api/workflows.js:23` | Drop `export` keyword; drop from barrel |
| 3 | `fetchStudioActive` | `apps/dashboard/src/api/studio.js:12` | Drop `export` keyword; drop from barrel |
| 4 | `exportCreatorTemplateApprovalAudit` | `apps/dashboard/src/api/creator.js:24` | Drop `export` keyword; drop from barrel |

(These 4 functions have zero consumers anywhere in the codebase — verified by grep.)

#### Bucket 2 — Direct-path-only (remove from barrel, keep submodule export)

| # | Function | Defining file | Only consumer(s) via direct path |
|---|----------|---------------|----------------------------------|
| 1 | `apiConnectivity` | `apps/dashboard/src/api/connectivity.js:8` | `SettingsPage.vue:219`, `useFilteredPageError.js:2`, 2 unit tests |
| 2 | `markApiOffline` | `apps/dashboard/src/api/connectivity.js:27` | `api/core.js:7` (internal) |
| 3 | `markApiOnline` | `apps/dashboard/src/api/connectivity.js:20` | `api/core.js:7`, `api/agent.js:11` (internal) |
| 4 | `deleteCreatorFactoryMergePresetPackage` | `apps/dashboard/src/api/creator.js` (re-exported from `mergePreset.js`) | `tests/unit/api-creator-merge-preset.spec.ts:15` |
| 5 | `fetchCreatorFactoryVolumeTemplates` | `apps/dashboard/src/api/creator.js` (re-exported from `volumeTemplate.js`) | `tests/unit/api-creator-volume-template.spec.ts:17` |
| 6 | `fetchCreatorGlobalMergePreferences` | `apps/dashboard/src/api/creator.js` (re-exported from `mergePreset.js`) | `tests/unit/api-creator-merge-preset.spec.ts:10` |
| 7 | `resolveCreatorFactoryMergePresetConflict` | `apps/dashboard/src/api/creator.js` (re-exported from `mergePreset.js`) | `tests/unit/api-creator-merge-preset.spec.ts:19` |

(These 7 functions are imported only via direct submodule path. Removing them from the barrel breaks nothing — consumers continue using the direct path. The submodule export stays so the consumer can continue to import.)

### 4.2 Change Set

**Edit 1**: `apps/dashboard/src/api/index.js` — drop 11 re-export entries (4 Bucket 4 + 7 Bucket 2).
**Edit 2-5**: 4 submodule files — drop `export` keyword on the 4 Bucket 4 functions.

No new files. No test files modified.

### 4.3 Risk Analysis

- **Build risk**: None. All consumer files already use either (a) the barrel for the kept 147 functions, or (b) direct submodule paths for the 7 Bucket 2 functions. No breakage.
- **Test risk**: None. Tests that import the 4 Bucket 4 functions don't exist (verified by grep). Tests that import the 7 Bucket 2 functions use direct submodule paths (not affected by barrel edits).
- **Behavioral risk**: None. The 4 Bucket 4 functions have no callers; deleting them has zero runtime effect.
- **Lint/type-check risk**: None. Function signatures unchanged; only `export` keyword and barrel entries removed.
- **knip risk**: None. The barrel remains in `knip.json#ignore`; other knip findings unaffected.

### 4.4 Verification Strategy

After change:
1. `grep -n "fetchHealth\b" apps/dashboard/src` → only definition in `health.js` (now unexported); no other references.
2. `grep -n "fetchActiveWorkflow\b" apps/dashboard/src` → only definition in `workflows.js` (now unexported); no other references.
3. `grep -n "fetchStudioActive\b" apps/dashboard/src` → only definition in `studio.js` (now unexported); no other references.
4. `grep -n "exportCreatorTemplateApprovalAudit\b" apps/dashboard/src` → only definition in `creator.js` (now unexported); no other references.
5. `grep -nE "^export \{[^|]*\bapiConnectivity\b|^export \{[^|]*\bmarkApiOffline\b|^export \{[^|]*\bmarkApiOnline\b" apps/dashboard/src/api/index.js` → 0 matches (Bucket 2 entries dropped).
6. `grep -nE "\bdeleteCreatorFactoryMergePresetPackage\b|\bfetchCreatorFactoryVolumeTemplates\b|\bfetchCreatorGlobalMergePreferences\b|\bresolveCreatorFactoryMergePresetConflict\b" apps/dashboard/src/api/index.js` → 0 matches (Bucket 2 entries dropped).
7. `pnpm exec vitest run` → 1545 tests pass.
8. `pnpm run build` → build succeeds.
9. `pnpm exec vue-tsc --noEmit` → 0 type errors.
10. `pnpm lint:all` → clean.
11. `pnpm exec knip` → `api/index.js` still in ignore; other categories unchanged.
12. `pnpm install` → no changes to lockfile needed (no dep changes).

### 4.5 Rollback Plan

If a deletion breaks runtime or test:
```bash
cd /home/ailearn/projects/LingWen && git revert HEAD --no-edit && git push origin master
```

Reverts 1 commit. No data loss.

---

## 5. Files Touched

| File | Change |
|------|--------|
| `apps/dashboard/src/api/index.js` | Drop 11 re-export entries |
| `apps/dashboard/src/api/health.js` | Drop `export` on `fetchHealth` |
| `apps/dashboard/src/api/workflows.js` | Drop `export` on `fetchActiveWorkflow` |
| `apps/dashboard/src/api/studio.js` | Drop `export` on `fetchStudioActive` |
| `apps/dashboard/src/api/creator.js` | Drop `export` on `exportCreatorTemplateApprovalAudit` |
| **Total** | **5 file operations** |

**Files NOT touched**: `apps/dashboard/src/api/connectivity.js` (submodule exports unchanged; only barrel entries dropped), `apps/dashboard/src/api/decisions.js`, `apps/dashboard/src/api/cvg.js`, `apps/dashboard/src/api/budgets.js`, `apps/dashboard/src/api/studio.js` (other exports unchanged), `apps/dashboard/src/api/creator.js` (other exports unchanged), all consumer files, all test files, `knip.json`, `package.json`.

---

## 6. Test Strategy

**No new tests.** Rationale:
- All consumers of the 4 Bucket 4 functions don't exist (verified zero importers).
- All consumers of the 7 Bucket 2 functions already use direct submodule paths (unaffected by barrel edits).
- 1545 existing tests still cover all production behavior unchanged.
- 1545 tests passing after deletion is the test.

---

## 7. Commit Strategy

**Single atomic commit** (related barrel + submodule changes for the same audit):
```
refactor(cleanup): remove 4 dead functions + 7 redundant barrel entries from api/ (Phase 97)

Phase 97 — api/index.js barrel re-export audit (158 exports):

Delete 4 truly-dead functions (zero consumers anywhere):
- fetchHealth (api/health.js)
- fetchActiveWorkflow (api/workflows.js)
- fetchStudioActive (api/studio.js)
- exportCreatorTemplateApprovalAudit (api/creator.js)

Remove 7 functions from barrel only (still consumed via direct submodule path):
- apiConnectivity (4 direct consumers: SettingsPage.vue,
  useFilteredPageError.js, 2 tests)
- markApiOffline (api/core.js internal consumer)
- markApiOnline (api/core.js + api/agent.js internal consumers)
- deleteCreatorFactoryMergePresetPackage (1 test direct consumer)
- fetchCreatorFactoryVolumeTemplates (1 test direct consumer)
- fetchCreatorGlobalMergePreferences (1 test direct consumer)
- resolveCreatorFactoryMergePresetConflict (1 test direct consumer)

Net: barrel drops 11 of 158 lines; 4 dead functions removed entirely.

All consumers verified by grep before edit. No callers of the 4 dead functions
exist. The 7 barrel-only-removals have no barrel consumers (verified).

测试基线不变: 1545 PASS, 0 type errors, 0 build errors.
```

---

## 8. Open Questions

None. Scope confirmed (Option A: full audit).

---

## 9. Success Criteria

- [ ] `apps/dashboard/src/api/index.js` drops 11 re-export entries (4 Bucket 4 + 7 Bucket 2)
- [ ] 4 submodule files drop `export` keyword on the 4 Bucket 4 functions
- [ ] All grep checks per §4.4 return expected counts
- [ ] 1545 tests pass
- [ ] Build OK
- [ ] vue-tsc clean
- [ ] Lint clean
- [ ] knip `api/index.js` still in ignore; other categories unchanged
- [ ] Single atomic commit on master
- [ ] Pushed to origin/master

---

## 10. References

- Phase 99 spec: `docs/superpowers/specs/2026-08-24-phase99-knip-promote-to-error-design.md` (§4.4 follow-up queue)
- Phase 103 spec: `docs/superpowers/specs/2026-08-24-phase103-unused-exports-audit-design.md` (added `api/index.js` to `knip.json#ignore` as public-API barrel)
- Phase 97 exploration: explore subagent output (158 exports audited)
- Handoff: `docs/superpowers/handoffs/2026-08-23-phase60-95-handoff.md` §5