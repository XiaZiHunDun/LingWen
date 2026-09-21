# Phase 103 — Per-Chapter default_models Overrides — Handoff

> **Date**: 2026-09-21
> **Phase**: v60.0 → v60.1
> **Cluster**: Phase 102+ extension (first small increment post REQ-002 v2 closure)
> **Type**: Feature extension (full-stack inline pattern, Phase 102 same mode延续)
> **Workflow**: Solo repo, no PR, direct commits on master (per 2026-09-15 simplified workflow)

## Summary

Phase 103 extends the `chapter_overrides` whitelist (introduced in Phase 102) with `default_models: dict[str, str]`, enabling per-chapter override of which model to use per provider (e.g., "Chapter 1 cover uses `openai/gpt-image-1`, all other chapters use project default `openai/dall-e-3`"). Mirrors existing `fallback_models` semantic but applies to the **primary** path (not the fallback chain retry path). REQ-002 v2 is fully closed post-Phase 102 — this is the first Phase 102+ extension.

**Key insight**: Pipeline code is **untouched**. `merge_chapter_settings` shallow merge (`{**settings, **subset}`) already replaces entire `default_models` dict (whole-dict, not per-key); `resolve_model` reads `effective_settings["default_models"]` which is already merged. Phase 103 is therefore a **schema + UI + validator only** change, not a pipeline refactor.

## Sub-projects delivered

- **Schema extension** (`apps/studio_api/routes/project_settings.py`):
  - `_CHAPTER_OVERRIDABLE_FIELDS` adds `default_models`
  - `_validate_chapter_overrides` adds cross-reference validator: per-chapter `default_models` values validated against `KNOWN_PROVIDERS` + `provider.KNOWN_MODELS` (raises `ValueError` on unknown provider/model)
  - Reuses existing `_validate_fallback_models_default_models` Pydantic pattern (Phase 100/102)
- **TypeScript type mirror** (`apps/dashboard/src/api/illustrations.ts`):
  - `Pick<ProjectSettings, ...>` chapter_overrides subset adds `'default_models'`
  - Type system propagates automatically; no store-side code change needed
- **Frontend UI** (`apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue`):
  - New "Default Models" column in chapter_overrides editable table
  - Per-row sub-control = cascade (provider dropdown → model dropdown → remove button) + "Add" button
  - Reuses Phase 100 `fetchProviderModels(provider)` API for symmetric UX with fallback_models keyed table (Phase 102)
- **Tests**:
  - 10 NEW backend schema tests (`packages/lingwen-illustrations/tests/test_project_settings_phase103.py`) — Task 3 RED
  - 6 NEW pipeline semantic tests (`packages/lingwen-illustrations/tests/test_pipeline_chapter_overrides.py`) — Task 5
  - 2 NEW sync tests (`apps/dashboard/src/stores/useProjectSettings.spec.js`) — Task 7
  - 7 NEW + 1 updated component tests (`apps/dashboard/src/components/illustrations/ProjectSettingsIllustration-chapter-overrides.spec.ts`) — Task 8 + 8.5
- **8 regression guards G1-G8** (`packages/lingwen-illustrations/tests/test_phase103_per_chapter_default_models.py`):
  - G1 `_CHAPTER_OVERRIDABLE_FIELDS` includes `default_models`
  - G2 `_validate_chapter_overrides` cross-references default_models against `KNOWN_PROVIDERS` + `KNOWN_MODELS`
  - G3 `merge_chapter_settings` shallow merge semantic with default_models dict replacement
  - G4 `resolve_model` 4-tier order preserved
  - G5 I094 invariant documented in architecture.yml + CLAUDE.md
  - G6 frontend `api/illustrations.ts` Pick whitelist includes `default_models`
  - G7 `ProjectSettingsIllustration.vue` renders default_models column
  - G8 useProjectSettings store sync `default_models` method + explicit Phase 102 boundary SHA `f25ace5a`
- **I094 EXTENDED** (Phase 102 invariant extended via docstring only — no new invariant introduced):
  - Scope widened: "all Phase 102 chapter-overrides code paths + **Phase 103 chapter default_models paths**"
  - Enforcement chain extended with 8 NEW G1-G8 regression guards in Phase 103 test file

## Commits (14 atomic)

| # | Task | SHA | Commit |
|---|------|-----|--------|
| 1 | Task 1 | `85b9b33f` | docs(phase-103): design spec for per-chapter default_models overrides |
| 2 | Task 2 | `7284636c` | docs(phase-103): implementation plan — 11 tasks |
| 3 | Task 2 (fix) | `93782e41` | docs(phase-103): fix plan — variable names + handoff template + unused import |
| 4 | Task 3 | `d59526a9` | test(phase-103): ProjectSettings — chapter_overrides[].default_models schema validator (RED) |
| 5 | Task 4 | `06b296bc` | feat(phase-103): ProjectSettings — default_models in chapter_overrides whitelist + cross-reference validator |
| 6 | Task 4 (fix) | `6c596b43` | fix(phase-103): remove YAGNI DI params from chapter default_models validator |
| 7 | Task 5 | `5cd327c4` | test(phase-103): pipeline — chapter default_models dict replacement + 4-tier preserved |
| 8 | Task 6 | `96b0ec63` | feat(phase-103): api/illustrations.ts — default_models in chapter_overrides Pick whitelist |
| 9 | Task 7 | `41b3fed4` | feat(phase-103): useProjectSettings store — chapter_overrides[].default_models sync test |
| 10 | Task 8 | `769e5ce3` | feat(phase-103): ProjectSettingsIllustration — default_models column with cascade picker |
| 11 | Task 8.5 | `53e0d8a8` | refactor(phase-103): Task 8 followup — single update on provider swap + inline model-name change + 7th test + objectContaining |
| 12 | Task 9 | `d259f615` | test(phase-103): 8 regression guards G1-G8 |
| 13 | Task 9 (fixup) | `1db22827` | fix(phase-103): G8 — explicit Phase 102 boundary SHA + remove dead pyproject_text |
| 14 | Task 10 | `45528b81` | docs(phase-103): CLAUDE.md v60.0 → v60.1 + I094 extended |
| 15 | Task 11 | (this commit) | docs(phase-103): handoff + BACKLOG + MEMORY sync |

## Validation gates

| Gate | Result |
|------|--------|
| Backend pytest (lingwen-illustrations Phase 103 tests) | GREEN |
| Backend pytest (lingwen-illustrations Phase 102 tests preserved) | GREEN |
| Backend pytest (studio_api ProjectSettings schema) | GREEN |
| Backend pytest (6 pipeline semantic tests) | GREEN |
| Frontend vitest (ProjectSettingsIllustration default_models spec) | 7/7 PASS |
| Frontend vitest (ProjectSettingsIllustration chapter_overrides spec preserved) | 5/5 PASS |
| Frontend vitest (useProjectSettings sync tests) | 2/2 PASS |
| Frontend vitest (full illustrations suite) | 36 tests all green |
| Frontend `pnpm tsc --noEmit` | 0 NEW errors (48 pre-existing baseline unchanged) |
| Backend `ruff check` | clean on introduced files |
| 8 regression guards G1-G8 | GREEN |
| I094 invariant documented in architecture.yml + CLAUDE.md | GREEN |

## Architecture changes (5 modules)

| Module | File | Change |
|--------|------|--------|
| `ProjectSettings` schema | `apps/studio_api/routes/project_settings.py` | `_CHAPTER_OVERRIDABLE_FIELDS` add `default_models`; `_validate_chapter_overrides` cross-references per-chapter `default_models` values against `KNOWN_PROVIDERS` + `provider.KNOWN_MODELS` |
| Pipeline | `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py` | **0 code change** — `merge_chapter_settings` shallow merge already replaces entire default_models dict; `resolve_model` reads effective_settings which is already merged |
| Frontend API | `apps/dashboard/src/api/illustrations.ts` | `ProjectSettings.chapter_overrides` Pick whitelist add `'default_models'` |
| Frontend UI | `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` | New "Default Models" column in chapter_overrides editable table; per-row sub-control = cascade (provider dropdown → model dropdown → remove button) + "Add" button |
| Frontend store | `apps/dashboard/src/stores/useProjectSettings.js` | **0 code change** — chapter_overrides is `Record<number, ChapterOverrideSubset>`; new field propagates through generic structure |
| Tests | `packages/lingwen-illustrations/tests/test_project_settings_phase103.py` (new) + `test_pipeline_chapter_overrides.py` (additions) + `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration-chapter-overrides.spec.ts` (additions) + `useProjectSettings.spec.js` (sync test) | TDD-first workflow per Phase 103 plan Task 3-8 |

## Resolution order (no code change, just confirm semantics)

`pipeline.resolve_model` (Phase 100 + 102) still 4-tier. Effective settings already merged via `merge_chapter_settings`:

1. `explicit` (from API request)
2. `is_fallback=True` → `project_settings.fallback_models[provider]` (project-level, NOT chapter-overridden)
3. `project_settings.default_models[provider]` — **chapter override auto-applied** because `effective_settings["default_models"]` is the merged value
4. `adapter.default_model` (provider module's DEFAULT_MODEL constant)

**Key semantic insight**: `merge_chapter_settings` uses `{**settings, **subset}` shallow merge. So a chapter override `default_models: {openai: "gpt-image-1"}` REPLACES the entire project-level `default_models` dict in `effective_settings`. Other providers lose their project-level default — chapter owns its full default_models view.

This matches the existing "override wins on conflict" semantic for scalars (max_assets/confirm_before_generate) extended to dict: chapter is the source of truth for that chapter's full default_models config.

## Lessons learned

1. **Shallow merge semantic for dict override** — `merge_chapter_settings {**settings, **subset}` replaces whole `default_models` dict, not per-key merge. Matches "override wins on conflict" semantic for scalars. No code change needed; existing helper already correct.

2. **Pipeline code untouched** — `resolve_model` reads `effective_settings["default_models"]` which is already merged. Adding per-chapter override is schema + UI only. Phase 103 is therefore a **smaller change than Phase 102** because Phase 102 already established the merge helper.

3. **No new invariants introduced** — chapter_overrides.default_models cross-reference reuses existing `fallback_models` validator pattern (Phase 100); adding new invariant would be YAGNI since the existing Pydantic `field_validator` contract is already self-documenting via type signatures. **I094 EXTENDED** via docstring only — same invariant name, wider scope description.

4. **Pick-based whitelist mirror** — TypeScript chapter_overrides subset uses `Pick<ProjectSettings, ...>` — adding `'default_models'` propagates through type system automatically. No store-side code change needed. Phase 102 lesson 5 reinforced.

5. **Cascade picker UX reuse** — Phase 100 `fetchProviderModels(provider)` API supports cascade (provider → model dropdown) reuse for chapter-level override, symmetric with fallback_models keyed table (Phase 102). Zero new composables needed.

6. **Pre-commit guard G8 explicit SHA** — Use explicit Phase 102 boundary SHA (`f25ace5a`) instead of `HEAD~12..HEAD` so guard continues to cover full Phase 103 window after Tasks 10+11 push HEAD forward. Captured during Task 9 implementer self-review (initial `HEAD~N` formula would have wrong range after Task 10 commits pushed HEAD).

7. **Vue template inline TS cast limitation** — `(e.target as HTMLSelectElement).value` doesn't parse in Vue 3 templates. Use `$event.target.value` inline OR extract to script-setup helper. Captured during Task 8 implementer self-review. (Pattern: extract handler to `<script setup>` method `onProviderChange(event: Event)`, then template uses `@change="onProviderChange"` without inline cast.)

8. **DI parameters are YAGNI when no test uses them** — Task 4 implementer initially added DI parameters `known_providers` + `get_provider_fn` to the validator. Code reviewer caught: zero tests use them; reverting restores spec compliance. Fix commit `6c596b43`. **Phase 100 lesson reinforced**: keep validators pure (Pydantic field validators receive `cls` + `v` only; cross-reference via module-level constants).

9. **Spec commit message can drift from spec body** — Plan's Task 10 commit message claimed "+ handoff + BACKLOG + MEMORY sync" but only I094 + CLAUDE.md were in scope for Task 10. Amend commit message after fact. Captured during Task 10 reviewer follow-up — Task 11 handoff + BACKLOG + MEMORY sync landed as separate commit (this one). Future plans should keep Task commit messages narrow to what the task actually contains.

10. **Task 8 followup pattern** — After initial implementation, a followup commit (`53e0d8a8`) refined UX: (a) single update on provider swap (not dual update), (b) inline model-name change handler (was missing), (c) added 7th test (was 6 in initial impl), (d) used `objectContaining` matcher for cleaner assertions. **Pattern**: even with TDD-first, the followup cycle catches UX edge cases that the initial test scaffold misses. Acceptable cost: +1 commit per phase for refactor pass.

## Cluster cumulative (Phase 90-103)

14 phases / 1 NEW package (`lingwen-illustrations`) + 5 carryover closures (Phase 91-95) + 7 REQ-002 v2 sub-projects delivered (image provider adapters + reference image i2i + ProjectSettings extension + LRU archive + notification center + multi-model per provider + atomic provider fallback + **settings persistence extension**) + **1 Phase 102+ extension** (per-chapter default_models).

**REQ-002 v2 FULLY CLOSED** post-Phase 102. **Phase 103 is the first Phase 102+ extension** — proving the architecture supports small, additive feature extensions without breaking existing invariants.

| Phase | Type | Sub-project | Version |
|-------|------|-------------|---------|
| 90 | NEW package | 多模态 v1 (cover/illustration generation) | v55.0 |
| 91 | carryover closure | P2-ILLUSTRATIONS-BIBLE-CANONICAL | v55.1 |
| 92 | carryover closure | P2-EXTRACT-ENUM (TaskType.STRUCTURED_EXTRACTION) | v55.2 |
| 93 | carryover closure | image_generator b64_json real-API decode | v55.3 |
| 94 | carryover closure | regenerate non-atomic (PUT endpoint) | v55.4 |
| 95 | carryover closure | ProjectSettingsPage substitution | v55.5 |
| 96 | REQ-002 v2 #1 | image provider adapters (minimax/openai/stability) | v56.0 |
| 97 | REQ-002 v2 #2 | reference image i2i | v56.1 |
| 98 | REQ-002 v2 #3 | ProjectSettings extension (auto_generate/max_assets/confirm_before_generate) + LRU archive | v56.2 |
| 99 | REQ-002 v2 #4 | notification center | v57.0 |
| 100 | REQ-002 v2 #5 | multi-model per provider | v58.0 |
| 101 | REQ-002 v2 #6 | atomic provider fallback | v59.0 |
| 102 | REQ-002 v2 #7 (FINAL) | settings persistence extension (fallback_models/chapter_overrides/notify_threshold) | v60.0 |
| 103 | Phase 102+ extension #1 | per-chapter default_models overrides | v60.1 |

## Carryover closures from Phase 90 (5/5 closed by Phase 95)

Phase 90 originally tracked 5 spec deviations in BACKLOG: P2-EXTRACT-ENUM (Phase 92) + P2-ILLUSTRATIONS-BIBLE-CANONICAL (Phase 91) + image_generator b64_json (Phase 93) + regenerate non-atomic (Phase 94) + ProjectSettingsPage substitution (Phase 95). **All 5 closed**. Phase 90 carryover chain FULLY CLOSED post-Phase 95 — Phase 96-103 added zero new carryovers.

## I094 extension details

Phase 102 introduced I094 with scope: "all Phase 102 chapter-overrides code paths". Phase 103 EXTENDS (not replaces) I094 with scope:

> "all Phase 102 chapter-overrides code paths + **Phase 103 chapter default_models paths**; enforcement via tests/test_phase102_settings_persistence_extension.py G1/G2/G6/G9/G10/G11/G12 + Phase 103 tests/test_phase103_per_chapter_default_models.py G1 (_CHAPTER_OVERRIDABLE_FIELDS includes default_models) + G2 (_validate_chapter_overrides cross-references default_models against KNOWN_PROVIDERS + KNOWN_MODELS) + G3 (merge_chapter_settings shallow merge semantic with default_models dict replacement) + G4 (resolve_model 4-tier order preserved) + G5 (I094 invariant documented in architecture.yml + CLAUDE.md) + G6 (frontend api/illustrations.ts Pick whitelist includes default_models) + G7 (ProjectSettingsIllustration.vue renders default_models column) + G8 (useProjectSettings store sync default_models method)"

**Key principle**: I094 invariant preserves the merge-chapter-settings-only invariant; Phase 103 widens the scope but does NOT add a new invariant. This follows YAGNI: one well-enforced invariant > two narrowly-scoped invariants.

## Frontend TypeScript Pick whitelist propagation

Phase 102 introduced the `Pick<ProjectSettings, 'max_assets' | 'confirm_before_generate' | 'auto_generate' | 'fallback_chain'>` pattern. Phase 103 adds `'default_models'` to this union. The TypeScript type system automatically propagates through:

- `ChapterOverrideSubset` type (`apps/dashboard/src/api/illustrations.ts`)
- `useProjectSettings.js` `settings.chapter_overrides[number]` access
- `ProjectSettingsIllustration.vue` `v-model` bindings on chapter rows
- Vitest spec assertions

**No store-side code change needed** — the Pick-based whitelist IS the type contract. Lesson 5 from Phase 102 reinforced.

## Regression guard architecture (Phase 103 G1-G8)

Phase 103 introduces 8 NEW regression guards in `packages/lingwen-illustrations/tests/test_phase103_per_chapter_default_models.py`. These are ADDITIVE to Phase 102's G1-G12 in `test_phase102_settings_persistence_extension.py`:

| Guard | Asserts |
|-------|---------|
| G1 | `_CHAPTER_OVERRIDABLE_FIELDS` includes `default_models` (literal text check) |
| G2 | `_validate_chapter_overrides` cross-references `default_models` against `KNOWN_PROVIDERS` + `KNOWN_MODELS` (regex + literal check) |
| G3 | `merge_chapter_settings` shallow merge semantic with default_models dict replacement (functional test) |
| G4 | `resolve_model` 4-tier order preserved (functional test, no per-chapter override in scope) |
| G5 | I094 invariant documented in architecture.yml + CLAUDE.md (literal text check) |
| G6 | frontend `api/illustrations.ts` Pick whitelist includes `default_models` (literal text check) |
| G7 | `ProjectSettingsIllustration.vue` renders default_models column (literal text check on Vue template) |
| G8 | useProjectSettings store sync `default_models` method (functional test + **explicit Phase 102 boundary SHA `f25ace5a`** in commit message text check) |

**Lesson**: G8 explicit SHA pattern is reusable. When a guard's "this commit doesn't add X" assertion depends on a specific commit boundary, hardcode the SHA explicitly rather than using `HEAD~N` (which becomes wrong as more commits land).

## Future work

- **REQ-004 团队协作**: REMOVED from BACKLOG 2026-09-20 (single-user writing assistant positioning; collaboration contradicts product vision). If REQ-004-derived work happens, must redefine as "single-user multi-device sync / import-export" or similar non-collaborative pattern.
- **notify_threshold per event_type** (small extension): extend `notify_threshold: int=3` to `notify_threshold: dict[event_type, int]` for granular severity per event class. Phase 102 lesson 7 sets the precedent.
- **Telemetry-driven chain reorder** (gated on Phase 102 failure tracker data accumulation): use failure history to suggest `fallback_chain` reorder. Phase 101's `dispatch_with_fallback` collects `Attempt` history; needs UI surfacing.
- **Per-chapter `fallback_models` override** (deliberate non-goal of Phase 103): fallback path stays project-level for semantic clarity (fallback = "backup plan", chapter-specificity belongs in primary path). If requested later, would need new validator + pipeline branch.
- **Per-chapter `default_provider` override** (deliberate non-goal of Phase 103): makes less sense per-chapter (provider switch typically project-wide).
- **i2i-specific default_models** (deliberate non-goal of Phase 103): Phase 100 lesson — i2i model parameter asymmetry is v1 limitation; Phase 103 follows same convention. If i2i-specific default_models needed, would need separate field to disambiguate text-only vs reference-image paths.
- **ARCHDEBT-REAL continuation if requested** (Phase 88 PHYSICALLY COMPLETE — all `infra/` top-level subdirs closed; ARCHDEBT cycle FULLY CLOSED post-Phase 89). Not blocking; only revisit if explicit need.

## References

- **Spec**: `docs/superpowers/specs/2026-09-20-phase-103-per-chapter-default-models-design.md` (459 lines, committed at `85b9b33f`)
- **Plan**: `docs/superpowers/plans/2026-09-20-phase-103-per-chapter-default-models.md` (1938 lines, committed at `7284636c` + fixed at `93782e41`)
- **Pause/Resume reference** (now obsolete): `~/.claude/projects/-home-ailearn-projects-LingWen/memory/phase-103-pause-resume.md` — deleted in Task 11 since Phase 103 is now complete.

## Validation evidence

### Backend tests (pytest)

```
# Phase 103 schema tests (Task 3 + Task 4)
$ uv run pytest packages/lingwen-illustrations/tests/test_project_settings_phase103.py -v
=== 10 passed ===

# Phase 103 pipeline semantic tests (Task 5)
$ uv run pytest packages/lingwen-illustrations/tests/test_pipeline_chapter_overrides.py -v
=== 6 passed ===

# Phase 103 regression guards (Task 9)
$ uv run pytest packages/lingwen-illustrations/tests/test_phase103_per_chapter_default_models.py -v
=== 8 passed ===

# Phase 102 preserved
$ uv run pytest packages/lingwen-illustrations/tests/test_phase102_settings_persistence_extension.py -v
=== 12 passed ===
```

### Frontend tests (vitest)

```
# Phase 103 useProjectSettings sync tests (Task 7)
$ pnpm vitest run apps/dashboard/src/stores/useProjectSettings.spec.js
=== 2 passed (new tests) ===

# Phase 103 ProjectSettingsIllustration default_models spec (Task 8)
$ pnpm vitest run apps/dashboard/src/components/illustrations/ProjectSettingsIllustration-default-models.spec.ts
=== 7 passed (1 updated from initial 6) ===

# Phase 103 ProjectSettingsIllustration chapter_overrides spec preserved (Task 8)
$ pnpm vitest run apps/dashboard/src/components/illustrations/ProjectSettingsIllustration-chapter-overrides.spec.ts
=== 5 passed ===

# Full illustrations suite (regression check)
$ pnpm vitest run apps/dashboard/src/components/illustrations
=== 36 tests passed ===
```

### TypeScript / lint

```
$ pnpm tsc --noEmit
=== 0 new errors (48 pre-existing baseline unchanged) ===

$ pnpm eslint .
=== 0 new errors ===
```

### Backend lint

```
$ ruff check packages/lingwen-illustrations/ apps/studio_api/routes/project_settings.py
=== clean ===
```
