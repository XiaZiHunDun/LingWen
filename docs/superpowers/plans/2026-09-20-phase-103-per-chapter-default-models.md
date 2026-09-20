# Phase 103 — Per-Chapter default_models Overrides — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `ProjectSettings.chapter_overrides` whitelist with `default_models: dict[str, str]`, enabling per-chapter override of which model to use per provider.

**Architecture:** 5-module change (1 backend schema + 1 frontend type + 1 frontend component + 2 test files). Pipeline code unchanged — `merge_chapter_settings` shallow merge already replaces entire default_models dict correctly; `resolve_model` reads effective_settings which is already chapter-aware. Cross-reference validator reuses existing `fallback_models` pattern (Phase 100/102). I094 invariant preserved.

**Tech Stack:** Python 3.12+ (Pydantic v2) / FastAPI / Vue 3 / TypeScript strict / pytest / vitest / ruff

**Workflow:** Solo repo, direct commits on master (per 2026-09-15 simplified workflow). No PR. No worktree.

---

## File Structure

**Modify:**
- `apps/studio_api/routes/project_settings.py` — `_CHAPTER_OVERRIDABLE_FIELDS` add `default_models`; `_validate_chapter_overrides` adds per-chapter cross-reference validator
- `apps/dashboard/src/api/illustrations.ts` — `chapter_overrides` Pick whitelist add `'default_models'`
- `apps/dashboard/src/stores/useProjectSettings.js` — **0 code change**; mirror sync test confirms old-shape response leaves new field undefined (per Phase 102 lesson 7)
- `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` — new "Default Models" column with cascade picker (provider → model dropdown) + Add button

**Create:**
- `packages/lingwen-illustrations/tests/test_project_settings_phase103.py` — backend schema validator tests (~10 tests)
- `packages/lingwen-illustrations/tests/test_pipeline_chapter_default_models.py` — pipeline semantic tests (~4 tests)
- `packages/lingwen-illustrations/tests/test_phase103_per_chapter_default_models.py` — 8 regression guards G1-G8
- `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration-default-models.spec.ts` — frontend component tests (~6 tests)

**Modify (tests):**
- `packages/lingwen-illustrations/tests/test_pipeline_chapter_overrides.py` — extend with default_models tests (3 tests added)
- `apps/dashboard/src/stores/useProjectSettings.spec.js` — sync test for new field

---

## Task 1: Design spec (commit)

**Files:**
- Create: `docs/superpowers/specs/2026-09-20-phase-103-per-chapter-default-models-design.md`

- [ ] **Step 1: Verify spec exists**

Run: `test -f /home/ailearn/projects/LingWen/docs/superpowers/specs/2026-09-20-phase-103-per-chapter-default-models-design.md && echo OK`
Expected: `OK`

If not OK, re-run brainstorming spec writing. (Spec was already written in the brainstorming skill flow.)

- [ ] **Step 2: Commit spec**

```bash
cd /home/ailearn/projects/LingWen
git add docs/superpowers/specs/2026-09-20-phase-103-per-chapter-default-models-design.md
git commit -m "docs(phase-103): design spec for per-chapter default_models overrides"
```

---

## Task 2: Implementation plan (commit)

**Files:**
- Create: `docs/superpowers/plans/2026-09-20-phase-103-per-chapter-default-models.md`

- [ ] **Step 1: Verify this plan file is in place**

Run: `test -f /home/ailearn/projects/LingWen/docs/superpowers/plans/2026-09-20-phase-103-per-chapter-default-models.md && echo OK`
Expected: `OK`

- [ ] **Step 2: Commit plan**

```bash
cd /home/ailearn/projects/LingWen
git add docs/superpowers/plans/2026-09-20-phase-103-per-chapter-default-models.md
git commit -m "docs(phase-103): implementation plan — 11 tasks"
```

---

## Task 3: Backend schema validator — RED (commit)

**Files:**
- Create: `packages/lingwen-illustrations/tests/test_project_settings_phase103.py`

- [ ] **Step 1: Write failing tests**

Write the following to `packages/lingwen-illustrations/tests/test_project_settings_phase103.py`:

```python
"""Phase 103: ProjectSettings schema — chapter_overrides[].default_models cross-reference.

Per-chapter default_models must:
- Cross-reference provider in KNOWN_PROVIDERS
- Cross-reference model in provider.KNOWN_MODELS
- Empty dict accepted (chapter uses project default_models)
- Back-compat with old yaml without per-chapter default_models
"""
from __future__ import annotations

import pytest
import yaml
from pydantic import ValidationError

from apps.studio_api.routes.project_settings import ProjectSettings


def test_chapter_default_models_field_in_whitelist() -> None:
    """default_models added to _CHAPTER_OVERRIDABLE_FIELDS."""
    from apps.studio_api.routes.project_settings import _CHAPTER_OVERRIDABLE_FIELDS
    assert "default_models" in _CHAPTER_OVERRIDABLE_FIELDS


def test_chapter_default_models_accepts_valid_pair() -> None:
    """Valid chapter default_models subset passes validation."""
    from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider

    valid_provider = next(iter(KNOWN_PROVIDERS))
    valid_model = next(iter(get_provider(valid_provider).models))
    s = ProjectSettings(chapter_overrides={1: {"default_models": {valid_provider: valid_model}}})
    assert s.chapter_overrides[1]["default_models"] == {valid_provider: valid_model}


def test_chapter_default_models_accepts_empty_dict() -> None:
    """Empty default_models dict in subset is accepted (no override)."""
    s = ProjectSettings(chapter_overrides={1: {"default_models": {}}})
    assert s.chapter_overrides[1]["default_models"] == {}


def test_chapter_default_models_accepts_multiple_providers() -> None:
    """Multiple provider-model pairs in same chapter."""
    from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider

    if len(KNOWN_PROVIDERS) < 2:
        pytest.skip("Need >= 2 providers for this test")
    providers = list(KNOWN_PROVIDERS)[:2]
    pairs = {p: next(iter(get_provider(p).models)) for p in providers}
    s = ProjectSettings(chapter_overrides={5: {"default_models": pairs}})
    assert s.chapter_overrides[5]["default_models"] == pairs


def test_chapter_default_models_rejects_unknown_provider() -> None:
    """Unknown provider in chapter default_models raises ValidationError."""
    with pytest.raises(ValidationError, match="unknown provider"):
        ProjectSettings(chapter_overrides={1: {"default_models": {"unknown_provider_xyz": "model-x"}}})


def test_chapter_default_models_rejects_unknown_model() -> None:
    """Unknown model for valid provider raises ValidationError."""
    with pytest.raises(ValidationError, match="unknown model"):
        ProjectSettings(chapter_overrides={1: {"default_models": {"openai": "unknown-model-xyz"}}})


def test_chapter_default_models_does_not_break_other_columns() -> None:
    """Other chapter_overrides subset fields still work alongside default_models."""
    from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider

    valid_provider = next(iter(KNOWN_PROVIDERS))
    valid_model = next(iter(get_provider(valid_provider).models))
    s = ProjectSettings(chapter_overrides={
        3: {
            "max_assets": 8,
            "confirm_before_generate": True,
            "auto_generate": False,
            "fallback_chain": ["stability"],
            "default_models": {valid_provider: valid_model},
        }
    })
    assert s.chapter_overrides[3]["max_assets"] == 8
    assert s.chapter_overrides[3]["default_models"] == {valid_provider: valid_model}


def test_chapter_default_models_yaml_round_trip(tmp_path) -> None:
    """YAML dump + reload preserves per-chapter default_models."""
    from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider

    valid_provider = next(iter(KNOWN_PROVIDERS))
    valid_model = next(iter(get_provider(valid_provider).models))
    target = tmp_path / "settings.yaml"
    original = ProjectSettings(chapter_overrides={
        1: {"default_models": {valid_provider: valid_model}},
        5: {"default_models": {}},
    })
    target.write_text(yaml.safe_dump(original.model_dump(), allow_unicode=True), encoding="utf-8")
    data = yaml.safe_load(target.read_text(encoding="utf-8"))
    loaded = ProjectSettings(**data)
    assert loaded.chapter_overrides[1]["default_models"] == {valid_provider: valid_model}
    assert loaded.chapter_overrides[5]["default_models"] == {}


def test_chapter_default_models_back_compat_old_yaml() -> None:
    """Phase 102 yaml without per-chapter default_models still loads."""
    old_yaml = """\
default_provider: minimax
auto_generate: false
max_assets: 20
confirm_before_generate: false
fallback_chain: []
chapter_overrides:
  5:
    max_assets: 8
"""
    data = yaml.safe_load(old_yaml)
    s = ProjectSettings(**data)
    # Old yaml had no per-chapter default_models → key absent in subset
    assert "default_models" not in s.chapter_overrides[5]
    assert s.chapter_overrides[5]["max_assets"] == 8


def test_chapter_default_models_error_includes_chapter_num() -> None:
    """Error message identifies which chapter has bad default_models."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectSettings(chapter_overrides={42: {"default_models": {"unknown_provider": "x"}}})
    # Pydantic v2 ValidationError exposes error details
    error_str = str(exc_info.value)
    assert "42" in error_str or "chapter_overrides" in error_str
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /home/ailearn/projects/LingWen
uv run pytest packages/lingwen-illustrations/tests/test_project_settings_phase103.py -v 2>&1 | head -50
```
Expected: All 10 tests FAIL. The first failure should be `test_chapter_default_models_field_in_whitelist` failing because `_CHAPTER_OVERRIDABLE_FIELDS` does not yet contain `"default_models"`.

- [ ] **Step 3: Commit RED tests**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/tests/test_project_settings_phase103.py
git commit -m "test(phase-103): ProjectSettings — chapter_overrides[].default_models schema validator (RED)"
```

---

## Task 4: Backend schema validator — GREEN (commit)

**Files:**
- Modify: `apps/studio_api/routes/project_settings.py:34-89`

- [ ] **Step 1: Update `_CHAPTER_OVERRIDABLE_FIELDS`**

In `apps/studio_api/routes/project_settings.py`, modify line 34-36:

```python
# Whitelisted subset of ProjectSettings fields that can be overridden per chapter
# (Phase 102). Phase 103 adds default_models — chapter can override which model
# to use per provider. Other fields (e.g. default_provider, fallback_models,
# fallback_chain itself) make less sense per-chapter and would add complexity
# to the merge logic.
_CHAPTER_OVERRIDABLE_FIELDS: frozenset[str] = frozenset(
    {"max_assets", "confirm_before_generate", "auto_generate", "fallback_chain", "default_models"}
)
```

- [ ] **Step 2: Update `_validate_chapter_overrides` to cross-reference default_models**

In `apps/studio_api/routes/project_settings.py`, modify the `_validate_chapter_overrides` method (lines 74-89) to add per-chapter cross-reference. Replace the existing method body:

```python
    @field_validator("chapter_overrides")
    @classmethod
    def _validate_chapter_overrides(cls, v: dict[int, dict[str, Any]]) -> dict[int, dict[str, Any]]:
        """Key >= 0 int; value keys must be subset of _CHAPTER_OVERRIDABLE_FIELDS.

        Phase 103: cross-reference per-chapter default_models values against
        KNOWN_PROVIDERS + provider.KNOWN_MODELS (same pattern as top-level
        fallback_models validator).
        """
        from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider

        for chapter_num, subset in v.items():
            if not isinstance(chapter_num, int) or chapter_num < 0:
                raise ValueError(
                    f"chapter_num must be >= 0 int, got {chapter_num!r}"
                )
            unknown = set(subset.keys()) - _CHAPTER_OVERRIDABLE_FIELDS
            if unknown:
                raise ValueError(
                    f"unknown fields in chapter_overrides[{chapter_num}]: {unknown}; "
                    f"allowed: {sorted(_CHAPTER_OVERRIDABLE_FIELDS)}"
                )
            # Phase 103: cross-reference per-chapter default_models if present
            if "default_models" in subset:
                cls._validate_chapter_default_models(
                    chapter_num, subset["default_models"], KNOWN_PROVIDERS, get_provider
                )
        return v

    @classmethod
    def _validate_chapter_default_models(
        cls,
        chapter_num: int,
        default_models: dict[str, str],
        known_providers: frozenset[str],
        get_provider_fn: Callable,
    ) -> None:
        """Cross-reference per-chapter default_models against KNOWN_MODELS.

        Mirrors the top-level fallback_models validator pattern (Phase 100).
        """
        for provider, model in default_models.items():
            if provider not in known_providers:
                raise ValueError(
                    f"chapter_overrides[{chapter_num}].default_models: "
                    f"unknown provider: {provider!r}"
                )
            adapter = get_provider_fn(provider)
            if model not in adapter.models:
                raise ValueError(
                    f"chapter_overrides[{chapter_num}].default_models: "
                    f"unknown model {model!r} for provider {provider!r}; "
                    f"valid models: {adapter.models}"
                )
```

- [ ] **Step 3: Add Callable import**

Add at the top of `apps/studio_api/routes/project_settings.py` (after line 21 imports):

```python
from collections.abc import Callable
```

(Insert as the last import in the `from __future__ import annotations` + `from typing...` block.)

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /home/ailearn/projects/LingWen
uv run pytest packages/lingwen-illustrations/tests/test_project_settings_phase103.py -v 2>&1 | tail -20
```
Expected: All 10 tests PASS.

- [ ] **Step 5: Run regression — Phase 102 schema tests still pass**

Run:
```bash
cd /home/ailearn/projects/LingWen
uv run pytest packages/lingwen-illustrations/tests/test_project_settings_phase102.py -v 2>&1 | tail -20
```
Expected: All Phase 102 tests still PASS (no regression).

- [ ] **Step 6: Commit GREEN**

```bash
cd /home/ailearn/projects/LingWen
git add apps/studio_api/routes/project_settings.py
git commit -m "feat(phase-103): ProjectSettings — default_models in chapter_overrides whitelist + cross-reference validator"
```

---

## Task 5: Pipeline semantic — merge + resolve_model tests (commit)

**Files:**
- Create: `packages/lingwen-illustrations/tests/test_pipeline_chapter_default_models.py`

- [ ] **Step 1: Write failing tests**

Write to `packages/lingwen-illustrations/tests/test_pipeline_chapter_default_models.py`:

```python
"""Phase 103: pipeline.merge_chapter_settings + resolve_model — chapter default_models.

Verifies that:
1. merge_chapter_settings replaces the WHOLE default_models dict (not per-key merge)
2. resolve_model reads chapter-merged default_models[provider] over project default_models[provider]
3. resolve_model fallback path is NOT affected by chapter default_models (project fallback_models wins)
4. resolve_model with no chapter override uses project default_models (regression)
"""
from __future__ import annotations

from lingwen_illustrations.pipeline import merge_chapter_settings, resolve_model
from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider


def _make_adapter(provider: str):
    return get_provider(provider)


def _valid_provider_and_model() -> tuple[str, str]:
    """Pick first provider with at least one model."""
    for p in KNOWN_PROVIDERS:
        models = _make_adapter(p).models
        if models:
            return p, next(iter(models))
    raise RuntimeError("No provider has any models")


def test_merge_chapter_default_models_replaces_whole_dict() -> None:
    """Chapter default_models dict REPLACES project default_models dict (shallow merge)."""
    settings = {
        "default_models": {"minimax": "minimax-01", "openai": "dall-e-3"},
        "chapter_overrides": {5: {"default_models": {"openai": "gpt-image-1"}}},
    }
    effective = merge_chapter_settings(settings, 5)
    # Whole dict replaced — minimax default_models lost (chapter owns its view)
    assert effective["default_models"] == {"openai": "gpt-image-1"}


def test_merge_chapter_no_default_models_keeps_project() -> None:
    """Chapter subset without default_models → project default_models preserved."""
    settings = {
        "default_models": {"openai": "dall-e-3"},
        "chapter_overrides": {5: {"max_assets": 8}},
    }
    effective = merge_chapter_settings(settings, 5)
    assert effective["default_models"] == {"openai": "dall-e-3"}
    assert effective["max_assets"] == 8


def test_resolve_model_chapter_default_models_wins_over_project() -> None:
    """Chapter default_models[provider] takes precedence over project default_models[provider]."""
    project_provider, project_model = _valid_provider_and_model()
    # Pick a different valid model for the same provider
    models = list(_make_adapter(project_provider).models)
    if len(models) < 2:
        # Skip — need two distinct models
        return
    chapter_model = models[1] if models[0] == project_model else models[0]
    settings = {
        "default_models": {project_provider: project_model},
        "chapter_overrides": {5: {"default_models": {project_provider: chapter_model}}},
    }
    effective = merge_chapter_settings(settings, 5)
    adapter = _make_adapter(project_provider)
    resolved = resolve_model(
        provider=project_provider,
        explicit=None,
        project_settings=effective,
        adapter=adapter,
    )
    assert resolved == chapter_model


def test_resolve_model_chapter_default_models_no_override() -> None:
    """Chapter without default_models override → uses project default_models."""
    project_provider, project_model = _valid_provider_and_model()
    settings = {
        "default_models": {project_provider: project_model},
        "chapter_overrides": {5: {"max_assets": 8}},  # no default_models key
    }
    effective = merge_chapter_settings(settings, 5)
    adapter = _make_adapter(project_provider)
    resolved = resolve_model(
        provider=project_provider,
        explicit=None,
        project_settings=effective,
        adapter=adapter,
    )
    assert resolved == project_model


def test_resolve_model_chapter_default_models_does_not_affect_fallback_path() -> None:
    """is_fallback=True path uses project fallback_models, NOT chapter default_models."""
    project_provider, _ = _valid_provider_and_model()
    fb_models = list(_make_adapter(project_provider).models)
    if len(fb_models) < 2:
        return
    fb_model = fb_models[1]
    project_default_model = fb_models[0]
    chapter_model = fb_models[-1] if len(fb_models) > 2 else fb_models[1]
    settings = {
        "default_models": {project_provider: project_default_model},
        "fallback_models": {project_provider: fb_model},
        "chapter_overrides": {5: {"default_models": {project_provider: chapter_model}}},
    }
    effective = merge_chapter_settings(settings, 5)
    adapter = _make_adapter(project_provider)
    # Fallback path: chapter default_models must be IGNORED, project fallback_models used
    resolved_fb = resolve_model(
        provider=project_provider,
        explicit=None,
        project_settings=effective,
        adapter=adapter,
        is_fallback=True,
    )
    assert resolved_fb == fb_model, (
        f"is_fallback path must use project fallback_models, "
        f"got {resolved_fb} (expected {fb_model})"
    )
    # Primary path: chapter default_models wins
    resolved_primary = resolve_model(
        provider=project_provider,
        explicit=None,
        project_settings=effective,
        adapter=adapter,
        is_fallback=False,
    )
    assert resolved_primary == chapter_model


def test_resolve_model_explicit_still_wins_over_chapter_default_models() -> None:
    """Explicit API request model wins over chapter default_models (4-tier preserved)."""
    project_provider, _ = _valid_provider_and_model()
    models = list(_make_adapter(project_provider).models)
    if len(models) < 2:
        return
    explicit_model = models[1] if models[0] != models[1] else models[0]
    chapter_model = models[0] if models[0] != explicit_model else models[-1]
    if chapter_model == explicit_model:
        return  # need 2 distinct models
    settings = {
        "default_models": {},
        "chapter_overrides": {5: {"default_models": {project_provider: chapter_model}}},
    }
    effective = merge_chapter_settings(settings, 5)
    adapter = _make_adapter(project_provider)
    resolved = resolve_model(
        provider=project_provider,
        explicit=explicit_model,
        project_settings=effective,
        adapter=adapter,
    )
    assert resolved == explicit_model
```

- [ ] **Step 2: Run tests**

Run:
```bash
cd /home/ailearn/projects/LingWen
uv run pytest packages/lingwen-illustrations/tests/test_pipeline_chapter_default_models.py -v 2>&1 | tail -25
```
Expected: All 6 tests PASS (no code change needed in pipeline — these tests verify existing behavior already supports chapter default_models correctly).

If failures occur, the pipeline needs code adjustment (likely in `merge_chapter_settings` or `resolve_model`). Inspect failure and fix.

- [ ] **Step 3: Verify existing pipeline tests still pass (regression)**

Run:
```bash
cd /home/ailearn/projects/LingWen
uv run pytest packages/lingwen-illustrations/tests/test_pipeline_chapter_overrides.py packages/lingwen-illustrations/tests/test_pipeline_phase102_integration.py -v 2>&1 | tail -20
```
Expected: All existing pipeline tests PASS.

- [ ] **Step 4: Commit tests**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/tests/test_pipeline_chapter_default_models.py
git commit -m "test(phase-103): pipeline — chapter default_models dict replacement + 4-tier preserved"
```

---

## Task 6: Frontend TypeScript Pick whitelist (commit)

**Files:**
- Modify: `apps/dashboard/src/api/illustrations.ts:59-67`

- [ ] **Step 1: Update Pick whitelist**

In `apps/dashboard/src/api/illustrations.ts`, modify lines 59-67:

```typescript
  chapter_overrides?: Record<
    number,
    Partial<
      Pick<
        ProjectSettings,
        'max_assets' | 'confirm_before_generate' | 'auto_generate' | 'fallback_chain' | 'default_models'
      >
    >
  >
```

Note: Added `'default_models'` to the Pick union.

- [ ] **Step 2: Verify TypeScript compilation**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm tsc --noEmit 2>&1 | tail -10
```
Expected: 0 new errors. (Pre-existing 48 errors in unrelated files unchanged.)

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/api/illustrations.ts
git commit -m "feat(phase-103): api/illustrations.ts — default_models in chapter_overrides Pick whitelist"
```

---

## Task 7: Frontend store mirror sync test (commit)

**Files:**
- Modify: `apps/dashboard/src/stores/useProjectSettings.spec.js`

- [ ] **Step 1: Find existing spec file**

Run: `ls /home/ailearn/projects/LingWen/apps/dashboard/src/stores/useProjectSettings.spec.*`
Expected: `useProjectSettings.spec.js` exists.

If `.ts`, the rest of this task applies to TypeScript variant. If `.spec.ts`, the test file uses TS syntax — adjust syntax but logic is identical.

- [ ] **Step 2: Add sync test for chapter default_models**

Open `apps/dashboard/src/stores/useProjectSettings.spec.js` and add the following test inside the existing `describe` block (find appropriate location — after existing chapter_overrides tests):

```javascript
  describe('chapter_overrides default_models sync (Phase 103)', () => {
    it('store accepts chapter_overrides[N].default_models from new-shape response', async () => {
      const { setActivePinia, createPinia } = await import('pinia')
      setActivePinia(createPinia())
      const store = useProjectSettingsStore()

      // Simulate Phase 103 server response
      const settings = {
        default_provider: 'minimax',
        default_models: {},
        auto_generate: false,
        max_assets: 20,
        confirm_before_generate: false,
        fallback_chain: [],
        fallback_models: {},
        chapter_overrides: {
          1: { default_models: { openai: 'dall-e-3' } },
          5: { default_models: {} },
        },
        notify_threshold: 3,
      }
      store.applySettings(settings)

      expect(store.settings.chapter_overrides[1].default_models).toEqual({
        openai: 'dall-e-3',
      })
      expect(store.settings.chapter_overrides[5].default_models).toEqual({})
    })

    it('old-shape response (without per-chapter default_models) leaves field undefined', async () => {
      const { setActivePinia, createPinia } = await import('pinia')
      setActivePinia(createPinia())
      const store = useProjectSettingsStore()

      // Simulate Phase 102 server response (no per-chapter default_models)
      const settings = {
        default_provider: 'minimax',
        default_models: {},
        auto_generate: false,
        max_assets: 20,
        confirm_before_generate: false,
        fallback_chain: [],
        fallback_models: {},
        chapter_overrides: {
          5: { max_assets: 8 },  // no default_models key
        },
        notify_threshold: 3,
      }
      store.applySettings(settings)

      // Per Phase 102 lesson 7: consumer applies defaults via ??
      expect(store.settings.chapter_overrides[5].default_models).toBeUndefined()
      expect(store.settings.chapter_overrides[5].max_assets).toBe(8)
    })
  })
```

If the spec uses TypeScript (`.spec.ts`), convert the above to `.ts` syntax (replace `async () => { const ... = await import(...) }` with proper TS types).

- [ ] **Step 3: Run tests**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm vitest run src/stores/useProjectSettings.spec.js 2>&1 | tail -20
```
Expected: New 2 tests PASS, existing tests unaffected.

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/stores/useProjectSettings.spec.js
git commit -m "feat(phase-103): useProjectSettings store — chapter_overrides[].default_models sync test"
```

---

## Task 8: Frontend component — Default Models column (commit)

**Files:**
- Modify: `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` (add new column + sub-controls + add/remove handlers)
- Create: `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration-default-models.spec.ts`

- [ ] **Step 1: Read existing component structure**

Read `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` lines 130-225 (row helpers section) and lines 420-560 (chapter_overrides template section) to understand:
- How `addChapterOverride` and `removeChapterOverride` are implemented
- How the fallback_chain column is rendered (multi-select dropdown)
- How `update` propagates changes
- Existing CSS classes for column cells

- [ ] **Step 2: Add helper functions for default_models per chapter**

After the existing chapter row helpers (around line 219), add:

```typescript
// Phase 103: default_models row helpers (per-chapter provider-model pairs).
const addChapterDefaultModel = async (chapterKey: string, provider: string) => {
  const overrides = { ...(props.modelValue?.chapter_overrides || {}) }
  const existing = overrides[chapterKey] || {}
  const currentDefaultModels = existing.default_models || {}
  // Pull the provider's default model from the fetched modelCatalogs (same
  // pattern as Phase 100 default_models section above).
  const catalog = modelCatalogs.value[provider]
  const defaultModel = catalog?.default_model || ''
  overrides[chapterKey] = {
    ...existing,
    default_models: { ...currentDefaultModels, [provider]: defaultModel },
  }
  await update('chapter_overrides', overrides)
}

const removeChapterDefaultModel = async (chapterKey: string, provider: string) => {
  const overrides = { ...(props.modelValue?.chapter_overrides || {}) }
  const existing = overrides[chapterKey] || {}
  const currentDefaultModels = { ...(existing.default_models || {}) }
  delete currentDefaultModels[provider]
  overrides[chapterKey] = {
    ...existing,
    default_models: currentDefaultModels,
  }
  await update('chapter_overrides', overrides)
}

const updateChapterDefaultModel = async (
  chapterKey: string,
  provider: string,
  model: string,
) => {
  const overrides = { ...(props.modelValue?.chapter_overrides || {}) }
  const existing = overrides[chapterKey] || {}
  const currentDefaultModels = { ...(existing.default_models || {}) }
  currentDefaultModels[provider] = model
  overrides[chapterKey] = {
    ...existing,
    default_models: currentDefaultModels,
  }
  await update('chapter_overrides', overrides)
}
```

Adjust to match existing script setup style (composable / ref / computed / etc.).

- [ ] **Step 3: Add new column header in chapter_overrides table**

In the `<thead>` section (around line 444), add a new `<th>` after the fallback_chain column:

```html
              <th>Default Models</th>
```

- [ ] **Step 4: Add new column cell in chapter_overrides table**

In the `<tbody>` row section (around line 519, after the fallback_chain cell), add:

```html
                <td
                  class="project-settings-illustration-chapter-override-default-models"
                  :data-testid="`chapter-override-default-models-${chapter}`"
                >
                  <div
                    v-for="(model, provider) in props.modelValue?.chapter_overrides?.[chapter]?.default_models || {}"
                    :key="`${chapter}-${provider}`"
                    class="project-settings-illustration-chapter-default-model-pair"
                    :data-testid="`chapter-override-default-model-pair-${chapter}-${provider}`"
                  >
                    <select
                      :value="provider"
                      class="project-settings-illustration-chapter-default-model-provider"
                      :data-testid="`chapter-override-default-model-provider-${chapter}-${provider}`"
                      @change="(e) => {
                        const newProvider = (e.target as HTMLSelectElement).value
                        if (newProvider !== provider) {
                          removeChapterDefaultModel(chapter, provider).then(() =>
                            addChapterDefaultModel(chapter, newProvider)
                          )
                        }
                      }"
                    >
                      <option v-for="p in providers" :key="p.id" :value="p.id">{{ p.label }}</option>
                    </select>
                    <select
                      :value="model"
                      class="project-settings-illustration-chapter-default-model-name"
                      :data-testid="`chapter-override-default-model-name-${chapter}-${provider}`"
                      @change="(e) => updateChapterDefaultModel(chapter, provider, (e.target as HTMLSelectElement).value)"
                    >
                      <option
                        v-for="m in (modelCatalogs[provider] && modelCatalogs[provider].models) || []"
                        :key="m"
                        :value="m"
                      >{{ m }}</option>
                    </select>
                    <button
                      type="button"
                      class="project-settings-illustration-chapter-default-model-remove"
                      :data-testid="`chapter-override-default-model-remove-${chapter}-${provider}`"
                      @click="removeChapterDefaultModel(chapter, provider)"
                    >×</button>
                  </div>
                  <button
                    type="button"
                    class="project-settings-illustration-chapter-default-model-add"
                    :data-testid="`chapter-override-default-model-add-${chapter}`"
                    @click="addChapterDefaultModel(chapter, providers[0].id)"
                  >+ Add</button>
                </td>
```

Adjust syntax to match existing template patterns (e.g., script setup variable names — `providers` array is already declared at the top of the script setup; no new import needed).

- [ ] **Step 5: Add CSS for new column**

In the `<style scoped>` section, add:

```css
.project-settings-illustration-chapter-override-default-models {
  min-width: 220px;
}

.project-settings-illustration-chapter-default-model-pair {
  display: flex;
  gap: 4px;
  align-items: center;
  margin-bottom: 4px;
}

.project-settings-illustration-chapter-default-model-provider,
.project-settings-illustration-chapter-default-model-name {
  flex: 1;
  padding: 2px 4px;
}

.project-settings-illustration-chapter-default-model-remove {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--color-text-secondary, #888);
}
.project-settings-illustration-chapter-default-model-remove:hover {
  color: var(--color-error, #c00);
}

.project-settings-illustration-chapter-default-model-add {
  background: transparent;
  border: 1px dashed var(--color-border, #ccc);
  padding: 2px 8px;
  cursor: pointer;
  font-size: 0.85em;
}
```

- [ ] **Step 6: Verify Vue + TypeScript compiles**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm tsc --noEmit 2>&1 | tail -10
```
Expected: 0 new errors from this component.

If errors arise, fix inline (typical issues: `$attrs['x'] as unknown` cast for vue-tsc strict, missing reactive destructuring, etc.).

- [ ] **Step 7: Write frontend component tests**

Create `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration-default-models.spec.ts`:

```typescript
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ProjectSettingsIllustration from './ProjectSettingsIllustration.vue'

// Phase 103: Default Models column in chapter_overrides editable table.

describe('ProjectSettingsIllustration — chapter_overrides default_models column (Phase 103)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders default_models column header', () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: { modelValue: { chapter_overrides: {} } },
    })
    const headers = wrapper.findAll('th')
    const defaultModelsHeader = headers.find(h => h.text() === 'Default Models')
    expect(defaultModelsHeader).toBeTruthy()
  })

  it('renders existing provider-model pairs for a chapter', () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          chapter_overrides: {
            1: { default_models: { openai: 'dall-e-3' } },
          },
        },
      },
    })
    const pair = wrapper.find('[data-testid="chapter-override-default-model-pair-1-openai"]')
    expect(pair.exists()).toBe(true)
    const provider = wrapper.find('[data-testid="chapter-override-default-model-provider-1-openai"]')
    expect((provider.element as HTMLSelectElement).value).toBe('openai')
    const model = wrapper.find('[data-testid="chapter-override-default-model-name-1-openai"]')
    expect((model.element as HTMLSelectElement).value).toBe('dall-e-3')
  })

  it('shows Add button when no default_models exist for chapter', () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: { chapter_overrides: { 5: { max_assets: 8 } } },
      },
    })
    const addBtn = wrapper.find('[data-testid="chapter-override-default-model-add-5"]')
    expect(addBtn.exists()).toBe(true)
    expect(addBtn.text()).toContain('+ Add')
  })

  it('emits update when remove button clicked', async () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          chapter_overrides: {
            1: { default_models: { openai: 'dall-e-3' } },
          },
        },
      },
    })
    const removeBtn = wrapper.find('[data-testid="chapter-override-default-model-remove-1-openai"]')
    await removeBtn.trigger('click')
    // Verify chapter_overrides[1].default_models is empty in emitted update
    const updates = wrapper.emitted('update:modelValue')
    expect(updates).toBeTruthy()
    const lastUpdate = updates![updates!.length - 1][0] as Record<string, unknown>
    const chapterOverrides = lastUpdate.chapter_overrides as Record<string, Record<string, unknown>>
    expect(chapterOverrides[1].default_models).toEqual({})
  })

  it('emits update when Add button clicked', async () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: { chapter_overrides: { 5: {} } },
      },
    })
    const addBtn = wrapper.find('[data-testid="chapter-override-default-model-add-5"]')
    await addBtn.trigger('click')
    const updates = wrapper.emitted('update:modelValue')
    expect(updates).toBeTruthy()
    const lastUpdate = updates![updates!.length - 1][0] as Record<string, unknown>
    const chapterOverrides = lastUpdate.chapter_overrides as Record<string, Record<string, unknown>>
    expect(chapterOverrides[5].default_models).toBeDefined()
    expect(Object.keys(chapterOverrides[5].default_models).length).toBeGreaterThan(0)
  })

  it('preserves existing chapter_overrides columns (max_assets / confirm / auto_gen / fallback_chain) when adding default_models', () => {
    const wrapper = mount(ProjectSettingsIllustration, {
      props: {
        modelValue: {
          chapter_overrides: {
            3: {
              max_assets: 8,
              confirm_before_generate: true,
              auto_generate: false,
              fallback_chain: ['stability'],
            },
          },
        },
      },
    })
    // Existing columns still render
    expect(wrapper.find('[data-testid="chapter-override-max-assets-3"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="chapter-override-confirm-3"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="chapter-override-auto-generate-3"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="chapter-override-fallback-chain-3"]').exists()).toBe(true)
    // New column also renders
    expect(wrapper.find('[data-testid="chapter-override-default-models-3"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="chapter-override-default-model-add-3"]').exists()).toBe(true)
  })
})
```

- [ ] **Step 8: Run component tests**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm vitest run src/components/illustrations/ProjectSettingsIllustration-default-models.spec.ts 2>&1 | tail -25
```
Expected: All 6 tests PASS.

- [ ] **Step 9: Run existing chapter_overrides tests (regression)**

Run:
```bash
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm vitest run src/components/illustrations/ProjectSettingsIllustration-chapter-overrides.spec.ts 2>&1 | tail -20
```
Expected: Existing chapter_overrides tests still PASS (regression preserved).

- [ ] **Step 10: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue apps/dashboard/src/components/illustrations/ProjectSettingsIllustration-default-models.spec.ts
git commit -m "feat(phase-103): ProjectSettingsIllustration — default_models column with cascade picker"
```

---

## Task 9: Regression guards G1-G8 (commit)

**Files:**
- Create: `packages/lingwen-illustrations/tests/test_phase103_per_chapter_default_models.py`

- [ ] **Step 1: Write regression guards**

Create `packages/lingwen-illustrations/tests/test_phase103_per_chapter_default_models.py`:

```python
"""Phase 103 regression guards — per-chapter default_models overrides.

G1: default_models added to _CHAPTER_OVERRIDABLE_FIELDS
G2: _validate_chapter_overrides cross-references per-chapter default_models
G3: merge_chapter_settings shallow merge semantic (dict replacement)
G4: resolve_model 4-tier order preserved (no signature change)
G5: I094 invariant documented in CLAUDE.md / architecture.yml
G6: Frontend Pick whitelist includes default_models
G7: Frontend component renders new column
G8: No new dependencies in pyproject.toml or apps/dashboard/package.json
"""
from __future__ import annotations

from pathlib import Path
import re


REPO_ROOT = Path(__file__).resolve().parents[3]


# G1
def test_g1_default_models_in_chapter_overridable_fields() -> None:
    from apps.studio_api.routes.project_settings import _CHAPTER_OVERRIDABLE_FIELDS
    assert "default_models" in _CHAPTER_OVERRIDABLE_FIELDS


# G2
def test_g2_validate_chapter_overrides_cross_references_default_models() -> None:
    """Validator raises when per-chapter default_models has unknown provider."""
    from pydantic import ValidationError
    from apps.studio_api.routes.project_settings import ProjectSettings
    with __import__("pytest").raises(ValidationError, match="unknown provider"):
        ProjectSettings(chapter_overrides={1: {"default_models": {"unknown_xyz": "m"}}})


# G3
def test_g3_merge_chapter_settings_dict_replacement_semantic() -> None:
    from lingwen_illustrations.pipeline import merge_chapter_settings
    settings = {
        "default_models": {"minimax": "minimax-01", "openai": "dall-e-3"},
        "chapter_overrides": {5: {"default_models": {"openai": "gpt-image-1"}}},
    }
    effective = merge_chapter_settings(settings, 5)
    # Whole dict replaced (shallow merge); minimax default_models lost
    assert "minimax" not in effective["default_models"]
    assert effective["default_models"] == {"openai": "gpt-image-1"}


# G4
def test_g4_resolve_model_4_tier_order_preserved() -> None:
    """Explicit > fallback (when is_fallback) > default_models > provider default."""
    from lingwen_illustrations.pipeline import resolve_model
    from lingwen_illustrations.providers import KNOWN_PROVIDERS, get_provider
    # Pick any valid provider
    provider = next(iter(KNOWN_PROVIDERS))
    adapter = get_provider(provider)
    models = list(adapter.models)
    if len(models) < 2:
        __import__("pytest").skip("Need >= 2 models")
    # explicit wins
    resolved = resolve_model(
        provider=provider, explicit=models[1], project_settings={}, adapter=adapter,
    )
    assert resolved == models[1]
    # default tier
    resolved = resolve_model(
        provider=provider, explicit=None,
        project_settings={"default_models": {provider: models[1]}},
        adapter=adapter,
    )
    assert resolved == models[1]
    # provider default tier (no settings)
    resolved = resolve_model(
        provider=provider, explicit=None, project_settings=None, adapter=adapter,
    )
    assert resolved == adapter.default_model


# G5
def test_g5_i094_invariant_documented() -> None:
    """I094 invariant exists in architecture.yml OR CLAUDE.md."""
    arch_yml = REPO_ROOT / ".lingwen" / "architecture.yml"
    claude_md = REPO_ROOT / "CLAUDE.md"
    arch_text = arch_yml.read_text(encoding="utf-8") if arch_yml.exists() else ""
    claude_text = claude_md.read_text(encoding="utf-8") if claude_md.exists() else ""
    # Either source mentions I094 by number AND merge_chapter_settings
    assert ("I094" in arch_text and "merge_chapter_settings" in arch_text) or (
        "I094" in claude_text and "merge_chapter_settings" in claude_text
    ), "I094 invariant must be documented in architecture.yml or CLAUDE.md"


# G6
def test_g6_frontend_pick_whitelist_includes_default_models() -> None:
    """TypeScript Pick<ProjectSettings, ...> includes 'default_models' for chapter_overrides."""
    api_ts = REPO_ROOT / "apps" / "dashboard" / "src" / "api" / "illustrations.ts"
    text = api_ts.read_text(encoding="utf-8")
    # Match the Pick whitelist union containing chapter_overrides
    pattern = re.compile(
        r"chapter_overrides\?:.*?Pick<[^>]*?'default_models'",
        re.DOTALL,
    )
    assert pattern.search(text), (
        f"chapter_overrides Pick whitelist must include 'default_models' in {api_ts}"
    )


# G7
def test_g7_component_renders_default_models_column() -> None:
    """ProjectSettingsIllustration.vue has default_models column header."""
    component = REPO_ROOT / "apps" / "dashboard" / "src" / "components" / "illustrations" / "ProjectSettingsIllustration.vue"
    text = component.read_text(encoding="utf-8")
    # Column header text and at least one testid reference
    assert "Default Models" in text, "Column header missing"
    assert "chapter-override-default-models" in text, "testid missing"


# G8
def test_g8_no_new_dependencies() -> None:
    """Phase 103 introduces 0 new third-party or workspace dependencies."""
    # No new pyproject.toml package additions
    pyproject = REPO_ROOT / "pyproject.toml"
    pyproject_text = pyproject.read_text(encoding="utf-8") if pyproject.exists() else ""
    # No new packages added in Phase 103 (sanity check — Phase 103 commits touch
    # settings.py, illustrations.ts, ProjectSettingsIllustration.vue + tests only)
    # Verified by checking no package workspace member was added in last 12 commits.
    import subprocess
    result = subprocess.run(
        ["git", "diff", "HEAD~12..HEAD", "--name-only", "--", "pyproject.toml", "packages/*/pyproject.toml", "apps/*/package.json"],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True,
    )
    assert result.returncode == 0, "git diff failed"
    assert result.stdout.strip() == "", (
        f"Phase 103 should not add new deps; touched: {result.stdout}"
    )
```

- [ ] **Step 2: Run regression guards**

Run:
```bash
cd /home/ailearn/projects/LingWen
uv run pytest packages/lingwen-illustrations/tests/test_phase103_per_chapter_default_models.py -v 2>&1 | tail -25
```
Expected: All 8 guards PASS.

- [ ] **Step 3: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add packages/lingwen-illustrations/tests/test_phase103_per_chapter_default_models.py
git commit -m "test(phase-103): 8 regression guards G1-G8"
```

---

## Task 10: Update I094 invariant in architecture.yml + CLAUDE.md (commit)

**Files:**
- Modify: `.lingwen/architecture.yml` (extend I094 to mention chapter default_models supported)
- Modify: `CLAUDE.md` (add v60.1 entry to version block)

- [ ] **Step 1: Find I094 in architecture.yml**

Run:
```bash
cd /home/ailearn/projects/LingWen
grep -n "I094\|merge_chapter_settings" .lingwen/architecture.yml | head -5
```

- [ ] **Step 2: Extend I094 description**

Locate the I094 entry and extend its description to mention Phase 103 support:

```yaml
        # Phase 103:
        # I094 (extended) — merge_chapter_settings supports per-chapter default_models
        # (dict[str, str]) via shallow merge (chapter owns its full default_models view).
        # No code change to merge_chapter_settings; dict replacement semantic is correct.
```

Adjust YAML structure to match existing convention (use inline comment or extended scope field per existing pattern).

- [ ] **Step 3: Update CLAUDE.md**

In `CLAUDE.md`, the version line at the top:

Change from:
```
> **版本**: v60.0 (Phase 102 REQ-002 v2: Settings Persistence Extension...
```

To:
```
> **版本**: v60.1 (Phase 103 Per-Chapter default_models Overrides — first Phase 102+ extension; chapter_overrides whitelist +default_models: dict[str,str] + Pydantic cross-reference validator (KNOWN_PROVIDERS + KNOWN_MODELS) + api/illustrations.ts Pick whitelist + ProjectSettingsIllustration.vue Default Models column with cascade picker + 8 regression guards G1-G8 + I094 extended; cluster cumulative Phase 90-103 = 14 phases / 1 NEW package + 5 carryover closures + 7 REQ-002 v2 sub-projects + 1 Phase 102+ extension. v60.0 → v60.1)
> **Previous**: v60.0 (Phase 102 REQ-002 v2: Settings Persistence Extension...
```

Add the v60.0 → v60.1 entry to the "已完成" / "Known legacy" / version history sections as appropriate per project convention. Reference existing v59.0 → v60.0 entries for format.

- [ ] **Step 4: Verify syntax**

Run:
```bash
cd /home/ailearn/projects/LingWen
uv run python -c "import yaml; yaml.safe_load(open('.lingwen/architecture.yml'))" && echo OK
```
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add .lingwen/architecture.yml CLAUDE.md
git commit -m "docs(phase-103): CLAUDE.md v60.0 → v60.1 + I094 extended + handoff + BACKLOG + MEMORY sync"
```

---

## Task 11: Handoff + BACKLOG + MEMORY sync (commit)

**Files:**
- Create: `docs/superpowers/handoffs/2026-09-20-phase-103-per-chapter-default-models-handoff.md`
- Modify: `collaboration/BACKLOG.md`
- Modify: `/home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md`

- [ ] **Step 1: Write handoff doc**

Create `docs/superpowers/handoffs/2026-09-20-phase-103-per-chapter-default-models-handoff.md` with the following structure (model after Phase 102 handoff):

```markdown
# Phase 103 — Per-Chapter default_models Overrides — Handoff

> **Date**: 2026-09-20
> **Phase**: v60.0 → v60.1
> **Type**: Phase 102+ extension (first small increment post REQ-002 v2 closure)
> **Workflow**: Solo repo, no PR, direct commits on master

## Summary

[Follow Phase 102 handoff structure: spec link + plan link + commit list + validation gates + lessons + cluster cumulative + future work]

## Commits (10 atomic)

1. `docs(phase-103): design spec for per-chapter default_models overrides` (Task 1)
2. `docs(phase-103): implementation plan — 11 tasks` (Task 2)
3. `test(phase-103): ProjectSettings — chapter_overrides[].default_models schema validator (RED)` (Task 3)
4. `feat(phase-103): ProjectSettings — default_models in chapter_overrides whitelist + cross-reference validator` (Task 4)
5. `test(phase-103): pipeline — chapter default_models dict replacement + 4-tier preserved` (Task 5)
6. `feat(phase-103): api/illustrations.ts — default_models in chapter_overrides Pick whitelist` (Task 6)
7. `feat(phase-103): useProjectSettings store — chapter_overrides[].default_models sync test` (Task 7)
8. `feat(phase-103): ProjectSettingsIllustration — default_models column with cascade picker` (Task 8)
9. `test(phase-103): 8 regression guards G1-G8` (Task 9)
10. `docs(phase-103): CLAUDE.md v60.0 → v60.1 + I094 extended + handoff + BACKLOG + MEMORY sync` (Task 10+11)

## Validation gates

- pytest lingwen-illustrations (Phase 103 tests + Phase 102 preserved): all green
- pytest studio_api (ProjectSettings schema): all green
- vitest ProjectSettingsIllustration (default_models spec + chapter_overrides spec preserved): all green
- vitest useProjectSettings (sync tests): all green
- pnpm tsc --noEmit: 0 new errors (48 pre-existing baseline unchanged)
- ruff check: clean on introduced files
- 8 regression guards G1-G8 GREEN

## Lessons

1. **Shallow merge semantic for dict override** — `merge_chapter_settings {**settings, **subset}` replaces whole `default_models` dict, not per-key merge. Matches "override wins on conflict" semantic for scalars. No code change needed; existing helper already correct.
2. **Pipeline code untouched** — `resolve_model` reads `effective_settings["default_models"]` which is already merged. Adding per-chapter override is schema + UI only.
3. **No new invariants introduced** — chapter_overrides.default_models cross-reference reuses existing fallback_models validator pattern; adding new invariant would be YAGNI since the existing Pydantic field_validator contract is already self-documenting via type signatures.
4. **Pick-based whitelist mirror** — TypeScript chapter_overrides subset uses `Pick<ProjectSettings, ...>` — adding `'default_models'` propagates through type system automatically. No store-side code change needed.
5. **Cascade picker UX reuse** — Phase 100 `fetchProviderModels(provider)` API supports cascade (provider → model dropdown) reuse for chapter-level override, symmetric with fallback_models keyed table (Phase 102).
6. **Pre-commit guard G8** — verifying "no new deps" via `git diff HEAD~12..HEAD -- pyproject.toml package.json` catches accidental dep additions across the whole phase atomic commit range.

## Cluster cumulative (Phase 90-103)

14 phases / 1 NEW package (lingwen-illustrations) + 5 carryover closures + 7 REQ-002 v2 sub-projects + **1 Phase 102+ extension**.

REQ-002 v2 FULLY CLOSED post-Phase 102. Phase 103 is first Phase 102+ extension (per-chapter default_models override).

## Future work

- REQ-004 团队协作: removed from BACKLOG 2026-09-20 (single-user writing assistant positioning; collaboration contradicts product vision)
- notify_threshold per event_type (small extension)
- Telemetry-driven chain reorder (gated on Phase 102 failure tracker data accumulation)
- ARCHDEBT-REAL continuation if requested (Phase 88 PHYSICALLY COMPLETE — all infra/ top-level subdirs closed)
```

(Fill in commit SHAs after commits are made. Track via `git log --oneline` post-execution.)

- [ ] **Step 2: Update BACKLOG.md**

In `collaboration/BACKLOG.md`, add a new entry in the "已完成 (近期)" or appropriate section:

```markdown
| **v60.1 Phase 103 (Per-Chapter default_models Overrides — first Phase 102+ extension)** | [handoff + spec + plan summary] | [validation] |
```

Add Phase 103 to "最近变更" with date 2026-09-20.

- [ ] **Step 3: Update MEMORY.md**

In `/home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md`, add to "Project State":

```
- **Version**: v60.1 (Phase 103 Per-Chapter default_models Overrides — first Phase 102+ extension; chapter_overrides whitelist + default_models dict[str,str] + Pydantic cross-reference validator + api/illustrations.ts Pick whitelist + ProjectSettingsIllustration.vue Default Models column + 8 regression guards G1-G8 + I094 extended. v60.0 → v60.1). 32 lingwen-* packages.
```

Update "REQ-002 v2 FULLY CLOSED" reference to mention Phase 103 as first extension.

Add new entry in "Topic Files":
```
| **Phase 103 Per-Chapter default_models (v60.1; first Phase 102+ extension)** | → See handoff `2026-09-20-phase-103-per-chapter-default-models-handoff.md` (chapter_overrides.whitelist +default_models + cross-reference validator + cascade picker + 6 lessons: shallow merge semantic / pipeline untouched / Pick-based whitelist mirror / cascade picker UX reuse / pre-commit guard G8)
```

- [ ] **Step 4: Commit**

```bash
cd /home/ailearn/projects/LingWen
git add docs/superpowers/handoffs/2026-09-20-phase-103-per-chapter-default-models-handoff.md collaboration/BACKLOG.md /home/ailearn/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md
git commit -m "docs(phase-103): handoff + BACKLOG + MEMORY sync"
```

---

## Final Validation (after Task 11 commit)

```bash
cd /home/ailearn/projects/LingWen

# Backend tests
uv run pytest packages/lingwen-illustrations/tests/test_project_settings_phase102.py packages/lingwen-illustrations/tests/test_project_settings_phase103.py packages/lingwen-illustrations/tests/test_pipeline_chapter_overrides.py packages/lingwen-illustrations/tests/test_pipeline_chapter_default_models.py packages/lingwen-illustrations/tests/test_pipeline_phase102_integration.py packages/lingwen-illustrations/tests/test_phase103_per_chapter_default_models.py -v 2>&1 | tail -10

# Studio API tests
cd /home/ailearn/projects/LingWen
uv run pytest apps/studio_api/tests/ -v 2>&1 | tail -5

# Frontend tests
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm vitest run src/components/illustrations/ src/stores/useProjectSettings.spec.js 2>&1 | tail -10

# TypeScript check
cd /home/ailearn/projects/LingWen/apps/dashboard
pnpm tsc --noEmit 2>&1 | tail -5

# Lint
cd /home/ailearn/projects/LingWen
ruff check apps/studio_api/routes/project_settings.py packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py 2>&1 | tail -5
```

Expected:
- All pytest: green
- All vitest: green (new tests + preserved tests)
- pnpm tsc: 0 new errors
- ruff: clean

If any gate fails, fix inline before declaring Phase 103 complete.

---

## Out-of-Scope Notes

- This plan does NOT cover REQ-004 (removed from BACKLOG 2026-09-20)
- This plan does NOT modify pipeline code (Phase 103 is schema + UI only)
- This plan does NOT introduce new dependencies
- This plan does NOT add new endpoints (reuses existing PUT/GET settings)
- This plan does NOT introduce new invariants (I094 extended via docstring only)