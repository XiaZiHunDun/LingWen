# Phase 103 — Per-Chapter default_models Overrides — Design

> **Date**: 2026-09-20
> **Phase**: v60.0 → v60.1
> **Cluster**: Phase 102+ extension (single small increment, ~1 phase / ~2-3 days, ~12-15 commits)
> **Type**: Feature extension (full-stack inline pattern, Phase 102 same mode延续)
> **Workflow**: Solo repo, no PR, direct commits on master (per 2026-09-15 simplified workflow)

## 1. Goals

Extend `chapter_overrides` whitelist with `default_models: dict[str, str]`, enabling per-chapter override of which model to use per provider (e.g., "Chapter 1 cover uses openai/gpt-image-1, all other chapters use project default openai/dall-e-3"). Mirrors existing `fallback_models` semantic but applies to the **primary** path (not the fallback chain retry path).

REQ-002 v2 is fully closed post-Phase 102 — this is the first Phase 102+ extension. Single small increment.

### 1.1 Single-direction pivot recorded

**2026-09-20 user direction**: REQ-004 团队协作 (multi-user collaboration) removed from BACKLOG. Product is a single-user writing assistant — multi-user collaboration contradicts product vision. Future REQ-004-derived work, if any, must redefine as "single-user multi-device sync / import-export" or similar non-collaborative pattern.

**Future work after Phase 103**:
- notify_threshold per event_type (small)
- REQ-004 redefined (single-user sync) — separate brainstorm
- ARCHDEBT-REAL continuation if requested
- Telemetry-driven chain reorder — gated on Phase 102 failure tracker data accumulation

## 2. Non-goals

- **No `fallback_models` per-chapter override** — fallback path stays project-level (semantic clarity: fallback is "backup plan", chapter-specificity belongs in primary path)
- **No change to `merge_chapter_settings` signature** — dict replacement semantic already correct
- **No change to `resolve_model` signature** — effective_settings already carries merged default_models
- **No new endpoints** — reuses existing PUT/GET `/api/projects/{slug}/settings`
- **No new dependencies** — 0 new third-party packages; 0 new workspace packages
- **No per-chapter override of `default_provider`** — makes less sense per-chapter (provider switch typically project-wide)
- **No i2i-specific default_models** — Phase 100 lesson: i2i model parameter asymmetry is v1 limitation; Phase 103 follows same convention

## 3. Architecture

### 3.1 Module-level changes

| Module | File | Change |
|--------|------|--------|
| `ProjectSettings` schema | `apps/studio_api/routes/project_settings.py` | `_CHAPTER_OVERRIDABLE_FIELDS` add `default_models`; `_validate_chapter_overrides` cross-references per-chapter `default_models` values against `KNOWN_PROVIDERS` + `provider.KNOWN_MODELS` |
| Pipeline | `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py` | **0 code change** — `merge_chapter_settings` shallow merge already replaces entire default_models dict; `resolve_model` reads effective_settings which is already merged |
| Frontend API | `apps/dashboard/src/api/illustrations.ts` | `ProjectSettings.chapter_overrides` Pick whitelist add `'default_models'` |
| Frontend UI | `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` | New "Default Models" column in chapter_overrides editable table; per-row sub-control = cascade (provider dropdown → model dropdown → remove button) + "Add" button |
| Frontend store | `apps/dashboard/src/stores/useProjectSettings.js` | **0 code change** — chapter_overrides is `Record<number, ChapterOverrideSubset>`; new field propagates through generic structure |
| Tests | `packages/lingwen-illustrations/tests/test_project_settings_phase103.py` (new) + `test_pipeline_chapter_overrides.py` (additions) + `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration-chapter-overrides.spec.ts` (additions) + `useProjectSettings.spec.js` (sync test) |  |

### 3.2 Invariants

**I094 PRESERVED** (Phase 102 invariant): `pipeline.merge_chapter_settings` is the ONLY entry point for chapter-overrides merging. Phase 103 adds no new merge semantics; existing helper already handles dict replacement correctly.

**No new invariants introduced**. The `default_models` per-chapter validator follows the same pattern as the existing `fallback_models` validator (Phase 100) — extending an established pattern does not warrant a new invariant.

### 3.3 Resolution order (no code change, just confirm semantics)

`pipeline.resolve_model` (Phase 100 + 102) still 4-tier. Effective settings already merged via `merge_chapter_settings`:

1. `explicit` (from API request)
2. `is_fallback=True` → `project_settings.fallback_models[provider]` (project-level, NOT chapter-overridden)
3. `project_settings.default_models[provider]` — **chapter override auto-applied** because `effective_settings["default_models"]` is the merged value
4. `adapter.default_model` (provider module's DEFAULT_MODEL constant)

**Key semantic insight**: `merge_chapter_settings` uses `{**settings, **subset}` shallow merge. So a chapter override `default_models: {openai: "gpt-image-1"}` REPLACES the entire project-level `default_models` dict in `effective_settings`. Other providers lose their project-level default — chapter owns its full default_models view.

This matches the existing "override wins on conflict" semantic for scalars (max_assets/confirm_before_generate) extended to dict: chapter is the source of truth for that chapter's full default_models config.

## 4. Components

### 4.1 `ProjectSettings` schema (Phase 103 extension)

```python
# apps/studio_api/routes/project_settings.py

_CHAPTER_OVERRIDABLE_FIELDS: frozenset[str] = frozenset(
    {"max_assets", "confirm_before_generate", "auto_generate", "fallback_chain", "default_models"}  # +default_models
)

class ProjectSettings(BaseModel):
    # ... existing 9 fields unchanged ...
    chapter_overrides: dict[int, dict[str, Any]] = {}

    @field_validator("chapter_overrides")
    @classmethod
    def _validate_chapter_overrides(cls, v: dict[int, dict[str, Any]]) -> dict[int, dict[str, Any]]:
        for chapter_num, subset in v.items():
            if not isinstance(chapter_num, int) or chapter_num < 0:
                raise ValueError(f"chapter_num must be >= 0 int, got {chapter_num!r}")
            unknown = set(subset.keys()) - _CHAPTER_OVERRIDABLE_FIELDS
            if unknown:
                raise ValueError(
                    f"unknown fields in chapter_overrides[{chapter_num}]: {unknown}; "
                    f"allowed: {sorted(_CHAPTER_OVERRIDABLE_FIELDS)}"
                )
            # NEW Phase 103: cross-reference per-chapter default_models if present
            if "default_models" in subset:
                cls._validate_chapter_default_models(chapter_num, subset["default_models"])
        return v

    @classmethod
    def _validate_chapter_default_models(cls, chapter_num: int, default_models: dict[str, str]) -> None:
        """Reuses the same pattern as top-level fallback_models validator."""
        from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider

        for provider, model in default_models.items():
            if provider not in KNOWN_PROVIDERS:
                raise ValueError(
                    f"chapter_overrides[{chapter_num}].default_models: unknown provider: {provider!r}"
                )
            adapter = get_provider(provider)
            if model not in adapter.models:
                raise ValueError(
                    f"chapter_overrides[{chapter_num}].default_models: unknown model {model!r} "
                    f"for provider {provider!r}; valid models: {adapter.models}"
                )
```

### 4.2 Pipeline semantics (no code change)

`merge_chapter_settings` (Phase 102 I094 invariant):

```python
def merge_chapter_settings(settings: dict, chapter_num: int | None) -> dict:
    overrides = settings.get("chapter_overrides") or {}
    if chapter_num is None or chapter_num not in overrides:
        return settings
    subset = overrides[chapter_num] or {}
    return {**settings, **subset}  # shallow merge — default_models dict is replaced wholesale
```

`resolve_model` (Phase 100 + 102): reads `project_settings.get("default_models").get(provider)` — automatically sees chapter-merged dict because `effective_settings` is passed in.

### 4.3 Frontend `ProjectSettings` interface

```typescript
// apps/dashboard/src/api/illustrations.ts

export interface ProjectSettings {
  // ... existing 9 fields unchanged ...

  chapter_overrides?: Record<
    number,
    Partial<
      Pick<
        ProjectSettings,
        'max_assets' | 'confirm_before_generate' | 'auto_generate' | 'fallback_chain' | 'default_models'  // +default_models
      >
    >
  >
}
```

### 4.4 Frontend UI

New "Default Models" column in chapter_overrides editable table. Each row sub-control mirrors the existing `fallback_models` keyed table pattern (Phase 102):

```
| Chapter | max_assets | confirm | auto_gen | fallback_chain | default_models                                            | × |
| 1       | 8          | ☐       | ☐        | []             | [openai: gpt-image-1] [minimax: minimax-02] [+Add]    | × |
| 5       |            |         |          | [stability]    | [—] [+Add]                                              | × |
```

Per-row default_models sub-control:
- Each existing pair: `provider dropdown` (3 options from KNOWN_PROVIDERS) → `model dropdown` (cascade fetchProviderModels(per provider)) → `[×]` remove button
- "+ Add" button adds new pair (defaults to first provider + first model)
- Empty list (no pairs) = chapter uses project-level default_models (no override)
- Same UX as fallback_models section for consistency

Cascade picker reuses Phase 100 `fetchProviderModels(providerName)` API (`apps/dashboard/src/api/illustrations.ts`) to populate model dropdown based on selected provider.

### 4.5 Data flow (per-chapter generation)

```
User triggers generation for chapter N
  ↓
generate_illustration(chapter_num=N, model=None, ...)
  ↓
settings = _load_illustration_settings(project_root)  # project-level
effective_settings = merge_chapter_settings(settings, N)  # I094
  ↓
If N has chapter_overrides[N].default_models:
    effective_settings["default_models"] = chapter_overrides[N].default_models
  ↓
resolve_model(provider, explicit=None, project_settings=effective_settings, adapter)
  ↓
Reads effective_settings["default_models"][provider] (chapter override if present)
  ↓
Returns chapter's model for the provider, OR project's model, OR provider default
```

## 5. Error handling

### 5.1 Validation errors (422 at PUT)

- `chapter_overrides[N].default_models[unknown_provider]` → 422 with field path `chapter_overrides.N.default_models` and message "unknown provider"
- `chapter_overrides[N].default_models[provider][unknown_model]` → 422 with field path and message "unknown model for provider X; valid models: [...]"
- Same shape as existing `fallback_models` validator errors (Phase 100 pattern)

### 5.2 Runtime errors (no new paths)

- `UnknownModelError` already raised by `resolve_model` for stale model names after project-level changes (Phase 100 invariant)
- No new exception classes introduced

### 5.3 UI errors

- Cascade picker model dropdown empty when KNOWN_MODELS not yet fetched → spinner (reuse Phase 100 fetchProviderModels loading state)
- Provider change resets model selection to first available model of new provider (Phase 100 UX)
- "+ Add" provider dropdown defaults to first provider not already in list (prevents duplicate keys)

## 6. Testing strategy

### 6.1 Backend tests

| Test | File |
|------|------|
| `ProjectSettings` accepts `chapter_overrides[N].default_models` valid subset | `test_project_settings_phase103.py` (NEW) |
| `ProjectSettings` rejects `chapter_overrides[N].default_models[unknown_provider]` | same |
| `ProjectSettings` rejects `chapter_overrides[N].default_models[provider][unknown_model]` | same |
| `ProjectSettings` rejects `chapter_overrides[N].default_models` empty dict | same (whitelist accepts, validator accepts empty) |
| `ProjectSettings` back-compat: old yaml without per-chapter default_models loads | same |
| YAML round-trip: write + reload preserves per-chapter default_models | same |
| `merge_chapter_settings` with chapter default_models replaces whole project dict | `test_pipeline_chapter_overrides.py` (extend) |
| `resolve_model` chapter default_models wins over project default_models | `test_pipeline_chapter_overrides.py` (extend) |
| `resolve_model` chapter default_models does NOT affect fallback path (project fallback_models still used) | `test_pipeline_chapter_overrides.py` (extend) |
| `resolve_model` no chapter override → uses project default_models (regression) | `test_pipeline_chapter_overrides.py` (extend) |
| I094 (merge_chapter_settings only entry) regression guard | `test_phase103_chapter_settings_invariant.py` (NEW) |

### 6.2 Frontend tests

| Test | File |
|------|------|
| `ProjectSettingsIllustration` new "Default Models" column renders | `ProjectSettingsIllustration-chapter-overrides.spec.ts` (extend) |
| Add default_models pair → row appears with provider + model selected | same |
| Remove default_models pair → row removed | same |
| Provider change resets model to first available of new provider | same |
| Empty default_models list → renders "— Add" button only | same |
| Existing 4 columns (max_assets / confirm / auto_gen / fallback_chain) unaffected | same (regression) |
| `useProjectSettings` store accepts chapter_overrides[N].default_models | `useProjectSettings.spec.js` (extend) |
| `useProjectSettings` store PUT round-trip with new field | same |

### 6.3 Regression guards (NEW)

7-10 regression guards in `packages/lingwen-illustrations/tests/test_phase103_per_chapter_default_models.py`:

| ID | Guard |
|----|-------|
| G1 | `default_models` added to `_CHAPTER_OVERRIDABLE_FIELDS` |
| G2 | `_validate_chapter_overrides` cross-references per-chapter `default_models` values |
| G3 | `merge_chapter_settings` shallow merge semantic (assertion via test_chapter_default_models_replaces_whole_dict) |
| G4 | `resolve_model` 4-tier order preserved (no signature change) |
| G5 | I094 invariant documented in CLAUDE.md / architecture.yml |
| G6 | Frontend Pick whitelist includes `default_models` |
| G7 | Frontend component renders new column |
| G8 | No new dependencies in pyproject.toml or apps/dashboard/package.json |

### 6.4 Validation gates

- `pytest lingwen-illustrations` all green (existing + new tests)
- `pytest studio_api` all green (existing 166 + new schema tests)
- `vitest ProjectSettingsIllustration + useProjectSettings` all green
- `pnpm tsc --noEmit` 0 new errors (48 pre-existing baseline unchanged)
- `ruff check` clean on introduced files
- 7-8 regression guards GREEN

## 7. Atomic commit plan (~13 commits)

Per 2026-09-15 simplified workflow (direct commits on master):

1. `docs(phase-103): design spec for per-chapter default_models overrides`
2. `docs(phase-103): implementation plan — 10 tasks TDD pattern`
3. `test(phase-103): ProjectSettings — chapter_overrides[].default_models schema validator (RED)`
4. `feat(phase-103): ProjectSettings — default_models in chapter_overrides whitelist + cross-reference validator`
5. `test(phase-103): pipeline.merge_chapter_settings — default_models dict replacement (RED)`
6. `feat(phase-103): pipeline.resolve_model — 4-tier preserved + chapter default_models docs`
7. `feat(phase-103): api/illustrations.ts — default_models in chapter_overrides Pick whitelist`
8. `feat(phase-103): useProjectSettings store — default_models default-fill (mirror sync test)`
9. `feat(phase-103): ProjectSettingsIllustration — default_models column in chapter_overrides table`
10. `test(phase-103): frontend — ProjectSettingsIllustration default_models column + cascade picker tests`
11. `test(phase-103): 8 regression guards G1-G8 + I094 invariant documented`
12. `docs(phase-103): CLAUDE.md v60.0 → v60.1 + handoff + BACKLOG + MEMORY sync`

## 8. Migration & back-compat

**YAML back-compat**: existing yaml files (without per-chapter default_models) load successfully. Pydantic v2 default-fill: missing `chapter_overrides[N].default_models` key in subset is absent, validator skips the per-chapter validation, dict replacement doesn't happen because subset doesn't contain `default_models` key.

**API back-compat**: PUT/GET `/api/projects/{slug}/settings` unchanged. New field is optional subset of `chapter_overrides`.

**UI back-compat**: existing 4 columns render unchanged for chapters without `default_models`. New column shows "— Add" button only for those chapters.

## 9. Out-of-scope notes for reviewers

- This is a 1-phase / ~2-3 day increment. No new package. No new architecture.
- Mirrors `fallback_models` pattern (Phase 100/102). Symmetric with existing sections.
- All code changes are localized; no cross-package ripple.
- Cluster cumulative Phase 90-103 = 14 phases / 1 NEW package + 5 carryover closures + 7 REQ-002 v2 sub-projects + **1 Phase 102+ extension**.

## 10. Carryover

**No carryover into Phase 104**. Phase 103 is complete + standalone.

Future work candidates (deferred until requested):
- `notify_threshold` per event_type
- REQ-004 redefined (single-user sync)
- Telemetry-driven chain reorder
- ARCHDEBT-REAL continuation