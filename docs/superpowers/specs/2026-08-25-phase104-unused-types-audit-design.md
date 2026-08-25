# Phase 104 — Audit & Resolve Unused Exported Types (10 files)

> **Date**: 2026-08-25
> **Phase**: 104
> **Source**: Phase 99 knip CI integration follow-up — `Unused exported types (10)` (~27 individual type names)
> **Status**: Design

---

## 1. Context

Phase 103 cleared `Unused exports (0)`. Phase 103.1 + 102.2 + 102.1 cleared `Unused files` + `Unused devDependencies` + `Unlisted binaries`. The remaining knip finding is `Unused exported types (10)` across 10 source files.

Phase 104 reduces this to 0 by:
- Dropping `export` keyword from 22 truly-dead type declarations across 9 files (the types stay in their files as internal interfaces)
- Adding `tests/helpers/strict-test-types.ts` to `knip.json#ignore` (the 4 test types there are public-API helpers — knip can't trace `as*` narrowing helpers)

---

## 2. Goal

Eliminate knip's `Unused exported types` category entirely (10 → 0).

---

## 3. Non-Goals

- **NOT** deleting the type declarations themselves — only dropping the `export` keyword. The types remain in their files as internal interfaces for in-file use.
- **NOT** consolidating the duplicate `Deviation` / `OverviewLike` / `QualityHint` types across files. Each file's instance is local-only after dropping `export`; cross-file consolidation is out of scope.
- **NOT** modifying `useCreatorWriteWorkbench/index.ts` barrel (it only re-exports hooks, not types; no change needed).
- **NOT** addressing the 1 unused `@vueuse/core` / `animate.css` / `vfonts` dependency (Phase 105a scope).
- **NOT** investigating why 3 different files each define their own `Deviation`/`OverviewLike`/`QualityHint` type — historical artifact, not blocking.

---

## 4. Design

### 4.1 Decision Matrix (verified by Phase 104 explore subagent)

| Bucket | Count | Action |
|--------|-------|--------|
| TRULY DEAD (drop `export`) | 22 types in 9 files | Edit `export interface` → `interface` |
| PUBLIC TEST API (knip false positive) | 4 types in 1 file | Add `tests/helpers/strict-test-types.ts` to `knip.json#ignore` |

### 4.2 Per-file edits (drop `export` keyword)

| File | Types (drop `export`) |
|------|-----------------------|
| `src/composables/useCreatorPage/useCreatorPageChrome.ts` | `ChromeContext` |
| `src/composables/useCreatorProductTools/useProductPreferences.ts` | `PreferencesShape` |
| `src/composables/useCreatorSettings/useSettingsHistory.ts` | `SettingsSnapshot` |
| `src/composables/useCreatorVolumePlanTemplates/useTemplateList.ts` | `TemplateRow` |
| `src/composables/useCreatorWrite/useWriteFlow.ts` | `ChapterRow`, `Deviation` |
| `src/composables/useCreatorWriteWorkbench/useWorkbenchCheckpoints.ts` | `CheckpointEntry`, `DiffViewLine`, `DiffView` |
| `src/composables/useCreatorWriteWorkbench/useWorkbenchLayout.ts` | `CreationMode`, `Deviation`, `LogicIssue`, `OverviewLike`, `MemoryAsset`, `ConsistencyItem`, `GoalCardLines` |
| `src/composables/useCreatorWriteWorkbench/useWorkbenchQuality.ts` | `QualityLevel`, `QualityHint`, `IntentEntry`, `LightValidationIssue`, `LogicCheckIssue`, `LogicCheckResult`, `Deviation`, `InlineConflictMarker`, `AgentLike`, `OverviewLike` |
| `src/composables/useCreatorWriteWorkbench/useWorkbenchSelection.ts` | `BodySelection`, `SelectionControls`, `QualityHint` |

**Edit pattern per type**: `export interface X { ... }` → `interface X { ... }` (or `export type X = ...` → `type X = ...`).

### 4.3 knip.json ignore addition

Add `tests/helpers/strict-test-types.ts` to the existing `ignore` array in `apps/dashboard/knip.json`. The 4 test types (`EditableVolume`, `MergePreview`, `SplitPreview`, `VolumePlanDiffPreview`) are intentionally exported as part of the public test-API surface (helpers like `asEditableVolumes()` narrow types in tests via `Ref<T>` casts; knip can't trace through the function-call return types).

---

## 5. Files Touched

| Category | File | Change |
|----------|------|--------|
| Edit | 9 source files (above) | Drop `export` from 22 type declarations |
| Edit | `apps/dashboard/knip.json` | Add 1 ignore entry |
| **Total** | **10 file operations** | |

**Files NOT touched**: any code logic, any tests, any package.json, any eslint config.

---

## 6. Test Strategy

**No new tests.** Rationale:
- All 22 type declarations stay in their files; only the `export` keyword is removed.
- Internal usage within the same file still works (verified by grep per spec §4.2).
- 1545 existing tests still cover all production behavior unchanged by this phase.
- 1545 tests passing after edit is the test.

---

## 7. Commit Strategy

**Two atomic commits** for clarity:

**Commit 1** — 9 source files (drop `export` keywords):
```
refactor(cleanup): drop export from 22 dead type declarations (Phase 104)

Phase 104 — reduce knip Unused exported types from 27 names to 4 (test helpers):

Drop \`export\` keyword from 22 type declarations across 9 source files.
The types remain in their files as internal interfaces for in-file use.

- useCreatorPageChrome.ts: ChromeContext
- useProductPreferences.ts: PreferencesShape
- useSettingsHistory.ts: SettingsSnapshot
- useTemplateList.ts: TemplateRow
- useWriteFlow.ts: ChapterRow, Deviation
- useWorkbenchCheckpoints.ts: CheckpointEntry, DiffViewLine, DiffView
- useWorkbenchLayout.ts: CreationMode, Deviation, LogicIssue, OverviewLike,
  MemoryAsset, ConsistencyItem, GoalCardLines
- useWorkbenchQuality.ts: QualityLevel, QualityHint, IntentEntry,
  LightValidationIssue, LogicCheckIssue, LogicCheckResult, Deviation,
  InlineConflictMarker, AgentLike, OverviewLike
- useWorkbenchSelection.ts: BodySelection, SelectionControls, QualityHint

Each type has 0 external consumers (verified via Phase 104 explore
subagent grep). Internal usage within the same file remains.

测试基线不变: 1545 PASS, 0 type errors, 0 build errors.
```

**Commit 2** — knip.json ignore entry:
```
build(ci): add tests/helpers/strict-test-types.ts to knip ignore (Phase 104)

Phase 104 — resolve knip false-positive Unused exported types (4 test types):

The file \`tests/helpers/strict-test-types.ts\` exports 4 types
(EditableVolume, MergePreview, SplitPreview, VolumePlanDiffPreview)
plus helper functions (\`asEditableVolumes()\`, \`asMergePreviewRef()\`,
etc.) that narrow types via \`Ref<T>\` casts in test files.

Knip cannot trace type usage through helper-function return types,
so it reports the file's exports as unused. The types are intentionally
public test-API surface — used by \`use-creator-volume-plan.spec.ts\`,
\`use-creator-volume-plan-diff.spec.ts\`, and
\`use-creator-volume-plan-merge-split.spec.ts\` via the helper
functions.

Add the whole file to apps/dashboard/knip.json#ignore to silence
the false positive.

测试基线不变: 1545 PASS, 0 type errors, 0 build errors.
```

Two-commit split because the knip.json edit is conceptually different (config vs source). Either commit alone achieves a partial improvement.

---

## 8. Open Questions

None. Scope confirmed (Option A: full audit 10 files).

---

## 9. Success Criteria

- [ ] 22 type declarations in 9 source files have `export` keyword removed
- [ ] `tests/helpers/strict-test-types.ts` added to `apps/dashboard/knip.json#ignore`
- [ ] `pnpm exec knip` reports `Unused exported types (0)`
- [ ] Other knip categories unchanged (Unused exports, Unused files, Unused deps, Unused devDeps, Unlisted binaries all remain at their Phase 102.2 / 103 / 103.1 / 105a-pending state)
- [ ] 1545 tests pass
- [ ] Build OK
- [ ] vue-tsc clean
- [ ] Lint clean
- [ ] Two atomic commits on master
- [ ] Pushed to origin/master

---

## 10. References

- Phase 99 spec: `docs/superpowers/specs/2026-08-24-phase99-knip-promote-to-error-design.md` (§4.4 follow-up queue)
- Phase 103 spec: `docs/superpowers/specs/2026-08-24-phase103-unused-exports-audit-design.md` (precedent: 47 export deletions + barrel ignore)
- Phase 103.1 spec: `docs/superpowers/specs/2026-08-24-phase103.1-delete-dead-useWriteValidation-design.md`
- Phase 102.2 spec: `docs/superpowers/specs/2026-08-24-phase102.2-clean-devDep-and-binary-config-design.md` (precedent: knip.json ignore additions)
- Phase 104 exploration: explore subagent output (decision matrix of 27 types across 10 files)
- Handoff: `docs/superpowers/handoffs/2026-08-23-phase60-95-handoff.md` §5