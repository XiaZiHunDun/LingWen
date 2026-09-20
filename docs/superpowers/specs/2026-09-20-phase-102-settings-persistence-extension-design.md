# Phase 102 — Settings Persistence Extension — Design

> **Date**: 2026-09-20
> **Phase**: v59.0 → v60.0
> **Cluster**: REQ-002 v2 #7 (seventh and final sub-project delivered)
> **Type**: Feature extension (full-stack inline pattern, Phase 90-101 inline mode延续)
> **Carryover**: Phase 95 deferred item (v2 API drives ProjectSettingsIllustration component) → closed by Phase 98 + 101 API plumbing; Phase 102 adds new fields on top
> **Workflow**: Solo repo, no PR, direct commits on master (per 2026-09-15 simplified workflow)

## 1. Goals

REQ-002 v2 #7 delivers 3 new fields to `ProjectSettings` extending illustration preferences beyond Phase 90-101 baseline:

1. **`fallback_models`** — per-provider model override used only when provider is invoked via the fallback chain path (Phase 101 atomic provider fallback integration)
2. **`chapter_overrides`** — per-chapter subset override for fine-grained control (e.g., opening chapter / climax chapter customization)
3. **`notify_threshold`** — consecutive failure count threshold that triggers a `severity: "warning"` notification (Phase 99 notification center integration)

All 3 fields persist via the existing `/api/projects/{slug}/settings` PUT/GET API (Phase 98/101 wiring). Frontend `ProjectSettingsIllustration.vue` is extended with 3 new sections (Phase 95 substitution closure: component is the single UI surface for project illustration preferences).

## 2. Non-goals

- **No new endpoints**: reuses existing PUT/GET /api/projects/{slug}/settings
- **No new dependencies**: 0 new third-party packages; 0 new workspace packages
- **No persistent failure counter**: counter is in-memory (Phase 99 trade-off consistent); restart loses counter (notification history via `audit_log` survives)
- **No per-chapter override UI for `fallback_chain`** (only `max_assets` + `confirm_before_generate` + `auto_generate` subset in v1; expand in later phase if requested)
- **No telemetry-driven chain reorder** (Phase 102+ future work from Phase 101 handoff)
- **No REQ-004 团队协作 work**: separate brainstorming deferred
- **No ProjectSettingsPage dedicated route**: Phase 95 substitution closure preserved (G13b regression guard enforces)

## 3. Architecture

### 3.1 Module-level changes

| Module | File | Change |
|--------|------|--------|
| `ProjectSettings` schema | `apps/studio_api/routes/project_settings.py` | +3 fields (`fallback_models: dict[str, str] = {}` / `chapter_overrides: dict[int, dict[str, Any]] = {}` / `notify_threshold: int = 3`) |
| Pipeline | `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py` | `resolve_model()` + `is_fallback: bool = False` param; new `merge_chapter_settings(settings, chapter_num)` helper |
| Notifications | `packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py` | in-memory `_consecutive_failures: dict[str, int]`; `record_failure(project_slug, error)` / `record_success(project_slug)`; threshold-driven warning emit; `NotificationEvent.severity: Literal["info", "warning"]` |
| Frontend store | `apps/dashboard/src/stores/useProjectSettings.js` | +3 fields mirror + default-fills |
| Frontend API wrapper | `apps/dashboard/src/api/illustrations.ts` | +3 fields type |
| Frontend UI | `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue` | +3 sections (fallback_models keyed table / chapter_overrides editable table / notify_threshold NSlider) |
| Frontend vitest | `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.js` + `useProjectSettings.spec.js` | +3 sections tests |

### 3.2 Invariants

**NEW I094** (Phase 102):
> `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py:merge_chapter_settings` is the ONLY entry point for chapter-overrides merging. `pipeline.generate_illustration()` / `pipeline.regenerate_illustration()` MUST call this helper before `resolve_provider()` / `resolve_model()`. `infra.illustrations.*` / `infra.image_provider.*` paths illegal.

**NEW I095** (Phase 102):
> `packages/lingwen-illustrations/src/lingwen_illustrations/notifications.py:_consecutive_failures` state machine is maintained ONLY via `record_failure()` / `record_success()` helpers. Threshold crossing MUST emit exactly one `severity: "warning"` notification (no spam). `infra.notifications.*` paths illegal.

**EXTENDS** I090 + I091 + I093 (Phase 98/99/101): new fields stay inside the existing audit + notify + fallback architecture without bypassing established entry points.

## 4. Components

### 4.1 `ProjectSettings` schema (Phase 102 extension)

```python
class ProjectSettings(BaseModel):
    """Phase 102: extended with fallback_models + chapter_overrides + notify_threshold.

    Schema migration is back-compat: Pydantic v2 fills missing fields with defaults.
    Old yaml files from Phase 101 (without 3 new fields) still load successfully.
    """
    default_provider: Literal["minimax", "openai", "stability"] = "minimax"
    default_models: dict[str, str] = {}                  # Phase 100
    auto_generate: bool = False                          # Phase 98
    max_assets: int = 20                                # Phase 98
    confirm_before_generate: bool = False               # Phase 98
    fallback_chain: list[str] = []                      # Phase 101
    # NEW Phase 102 ↓
    fallback_models: dict[str, str] = {}                 # per-provider model for chain retry path
    chapter_overrides: dict[int, dict[str, Any]] = {}   # chapter_num -> subset of fields
    notify_threshold: int = 3                           # consecutive failures before warning

    @field_validator("fallback_models")
    @classmethod
    def _validate_fallback_models(cls, v: dict[str, str]) -> dict[str, str]:
        """Key must be in KNOWN_PROVIDERS; value must be in provider.KNOWN_MODELS."""
        # Imports lazily to avoid cycle with providers package.
        for provider, model in v.items():
            if provider not in KNOWN_PROVIDERS:
                raise ValueError(f"unknown provider: {provider}")
            # Cross-reference KNOWN_MODELS — accept only registered models
            if model not in _load_known_models(provider):
                raise ValueError(f"unknown model {model!r} for provider {provider!r}")
        return v

    @field_validator("chapter_overrides")
    @classmethod
    def _validate_chapter_overrides(cls, v: dict[int, dict]) -> dict[int, dict]:
        """Key >= 0 int; value keys subset of ProjectSettings field whitelist."""
        for chapter_num, subset in v.items():
            if not isinstance(chapter_num, int) or chapter_num < 0:
                raise ValueError(f"chapter_num must be >= 0 int, got {chapter_num!r}")
            unknown = set(subset.keys()) - _PROJECT_SETTINGS_FIELDS
            if unknown:
                raise ValueError(f"unknown fields in override: {unknown}")
        return v

    @field_validator("notify_threshold")
    @classmethod
    def _validate_notify_threshold(cls, v: int) -> int:
        if v < 1:
            raise ValueError(f"notify_threshold must be >= 1, got {v}")
        return v
```

- **Back-compat**: Pydantic v2 default fill — existing yaml files without new fields load successfully (Phase 98/100/101 pattern)
- **`_load_known_models(provider)`** — lazy lookup of provider's `KNOWN_MODELS` from `lingwen_illustrations.providers.<provider>` (avoid import cycle at module load)
- **`_PROJECT_SETTINGS_FIELDS`** — `frozenset({"max_assets", "confirm_before_generate", "auto_generate", "fallback_chain"})` (whitelisted subset for chapter_overrides; not all fields make per-chapter sense)

### 4.2 `pipeline.merge_chapter_settings()` (NEW helper)

```python
def merge_chapter_settings(
    settings: dict[str, Any],
    chapter_num: int | None,
) -> dict[str, Any]:
    """Return settings merged with chapter_overrides[chapter_num] subset.

    Override takes precedence. Returns settings unchanged (no copy) when:
    - chapter_num is None (cover asset, no chapter scope)
    - chapter_num not in settings['chapter_overrides']
    - settings['chapter_overrides'] is empty

    Immutable: never mutates input dict (KISS, avoids hidden aliasing bugs).
    """
    overrides = settings.get("chapter_overrides") or {}
    if chapter_num is None or chapter_num not in overrides:
        return settings
    subset = overrides[chapter_num] or {}
    return {**settings, **subset}
```

- **Call site**: `generate_illustration()` / `regenerate_illustration()` entry, **before** `resolve_provider()` / `resolve_model()`
- **Cover assets** (chapter_num=None) → no merge
- **chapter_num not in overrides** → no merge (common path; fast path)

### 4.3 `pipeline.resolve_model()` extension

```python
def resolve_model(
    provider: str,
    settings: dict,
    *,
    is_fallback: bool = False,  # NEW Phase 102
) -> str:
    """4-tier resolution: explicit > fallback override (fallback path only) > default > provider default.

    Phase 102: when is_fallback=True and fallback_models[provider] is set, prefer it
    over default_models[provider]. fallback_models is fallback-PATH-ONLY — primary
    path always uses default_models[provider] (or provider default).
    """
    # NEW Phase 102: prefer fallback_models when invoked via chain retry path
    if is_fallback:
        fallback_models = settings.get("fallback_models") or {}
        if provider in fallback_models:
            return fallback_models[provider]
    # Phase 100 3-tier resolution unchanged
    default_models = settings.get("default_models") or {}
    if provider in default_models:
        return default_models[provider]
    return _PROVIDER_DEFAULT[provider]
```

- **Call site update**: `pipeline.dispatch_with_fallback` passes `is_fallback=True` to `resolve_model()` (provider-specific i2i path bypass unchanged per Phase 101 I093)

### 4.4 `notifications` failure tracking

```python
# In-memory state (lost on restart — Phase 99 trade-off consistent; documented in module docstring)
_consecutive_failures: dict[str, int] = {}  # project_slug -> count

# NEW field on NotificationEvent
@dataclass(frozen=True)
class NotificationEvent:
    # ... existing Phase 99 fields ...
    severity: Literal["info", "warning"] = "info"  # NEW Phase 102

def record_failure(
    project_slug: str,
    error: BaseException,
    *,
    project_root: Path,        # caller passes (consistent with audit_log.record_event)
    threshold: int,            # caller passes settings.notify_threshold (notifications stays yaml-free)
) -> None:
    """Increment consecutive failure counter; emit warning notification when threshold reached.

    Idempotent on threshold crossing: after warning emit, does NOT reset counter.
    Counter stays elevated until record_success() is called. This surfaces a
    sustained-failure pattern to the user without spamming them.

    Caller passes project_root + threshold so notifications module stays free of
    yaml I/O (consistent with audit_log.record_event signature — pipeline knows
    project_root + has already loaded settings).
    """
    _consecutive_failures[project_slug] = _consecutive_failures.get(project_slug, 0) + 1
    count = _consecutive_failures[project_slug]
    if count >= threshold:
        _emit_failure_warning(project_slug, count, error, project_root)


def record_success(project_slug: str) -> None:
    """Reset counter to 0 on any successful illustration event.

    Called from pipeline on successful generation/regeneration.
    No project_root needed — counter state is in-memory only.
    """
    _consecutive_failures[project_slug] = 0


def _emit_failure_warning(
    project_slug: str,
    count: int,
    error: BaseException,
    project_root: Path,
) -> None:
    """Emit severity=warning notification; ULID shared with audit_log (I091 invariant)."""
    event_id = ulid.new().str
    audit_log.record_event(
        project_root,
        event="generation",
        extra={
            "severity": "warning",
            "consecutive_failures": count,
            "last_error": str(error),
            "id": event_id,
        },
    )
    publish(NotificationEvent(
        id=event_id,
        project_slug=project_slug,
        event_type="generation",
        severity="warning",  # NEW
        asset_id=None,
        asset_type=None,
        chapter_num=None,
        style_preset=None,
        provider=None,
        ts=datetime.now(timezone.utc).isoformat(),
        extra={"consecutive_failures": count, "last_error": str(error)},
    ))
```

- **Caller pattern** (in pipeline.dispatch_with_fallback):
  ```python
  settings = _load_settings(project_root)
  threshold = settings.get("notify_threshold", 3)
  try:
      attempt = ...
  except ProviderExhaustedError as e:
      notifications.record_failure(slug, e, project_root=project_root, threshold=threshold)
      raise
  except Exception as e:
      notifications.record_failure(slug, e, project_root=project_root, threshold=threshold)
      raise
  else:
      notifications.record_success(slug)
  ```
- **Counter is GIL-safe**: dict[int] += 1 is atomic in CPython (no lock needed for Phase 99 patterns)
- **Threshold cross + reset semantics**: documented above; intentional for sustained-failure visibility
- **notifications module stays yaml-free**: caller passes project_root + threshold (consistent with audit_log.record_event signature)

### 4.5 Frontend sections

```vue
<!-- ProjectSettingsIllustration.vue +3 sections -->

<!-- Section: Fallback Models -->
<n-card title="Fallback Models (chain retry path)">
  <p class="hint">Used only when a provider is invoked via the fallback chain.</p>
  <n-data-table :columns="fallbackModelsColumns" :data="fallbackModelsRows" />
  <n-button @click="addFallbackModelRow">+ Add provider</n-button>
</n-card>

<!-- Section: Chapter Overrides -->
<n-card title="Chapter Overrides">
  <n-data-table :columns="chapterOverridesColumns" :data="chapterOverridesRows" />
  <n-button @click="addChapterOverrideRow">+ Add chapter</n-button>
</n-card>

<!-- Section: Notify Threshold -->
<n-card title="Notify Threshold (consecutive failures)">
  <n-slider v-model:value="form.notify_threshold" :min="1" :max="10" :step="1" />
  <span>Current: {{ form.notify_threshold }} failures → warning notification</span>
</n-card>
```

- **`fallback_models` table**: provider dropdown (KNOWN_PROVIDERS) + model dropdown (provider's KNOWN_MODELS)
- **`chapter_overrides` table**: chapter_num NInput + subset fields (max_assets NInputNumber / confirm_before_generate NSwitch / auto_generate NSwitch / fallback_chain NSelect multi)
- **`notify_threshold` slider**: 1-10 hardcoded range (extension would need design discussion)

## 5. Data flow

### 5.1 End-to-end happy path

1. User edits `chapter_overrides[5] = {max_assets: 8}` in `ProjectSettingsIllustration.vue`
2. `useProjectSettings.save()` PUTs full ProjectSettings (with chapter_overrides) to `/api/projects/{slug}/settings`
3. PUT validates chapter_overrides via Pydantic → 200 + persisted yaml
4. Pipeline receives request to generate illustration for chapter 5:
   - `pipeline.generate_illustration(slug, chapter=5, ...)`
   - `settings = _load_settings(slug)` → includes chapter_overrides
   - `effective = merge_chapter_settings(settings, 5)` → `{..., max_assets: 8, ...}`
   - `resolve_provider(effective)` → `"minimax"`
   - `resolve_model("minimax", effective, is_fallback=False)` → `default_models["minimax"]`
   - `dispatch_with_fallback(primary="minimax", chain=["openai"], settings=effective)`:
     - attempt 0 (minimax): success → `record_success("my-project")` + publish generation event (severity=info)

### 5.2 Fallback path with fallback_models

1. User sets `fallback_models = {"openai": "gpt-image-1"}` (overrides default_models["openai"] only in fallback path)
2. Generation retries through openai via chain → `resolve_model("openai", settings, is_fallback=True)` → `"gpt-image-1"` (NOT default_models["openai"])
3. `record_failure` / `record_success` per attempt outcome

### 5.3 Sustained failure → warning

1. `notify_threshold = 3`
2. attempt 0 fails → `record_failure` → count=1, no warning
3. attempt 1 fails → `record_failure` → count=2, no warning
4. attempt 2 fails → `record_failure` → count=3, **emit warning** notification (severity="warning", extra.consecutive_failures=3, extra.last_error=...)
5. attempt 3 fails → `record_failure` → count=4, **no additional warning** (idempotent until reset)
6. eventually succeeds → `record_success` → count=0
7. failure sequence resumes → counter starts at 0 again

## 6. Error handling

### 6.1 chapter_overrides validation
- **Pydantic validator**: subset must use whitelisted field keys
- **chapter_num key**: must be `>= 0` int (0 = opening chapter convention)
- **Failure**: 422 from PUT /settings (Naive UI message.error)

### 6.2 fallback_models validation
- **key**: must be in `KNOWN_PROVIDERS = ('minimax', 'openai', 'stability')`
- **value**: must be in `provider.KNOWN_MODELS[provider]`
- **Failure**: 422 from PUT /settings
- **Stale reference** (model removed in provider upgrade): `_load_settings()` falls back to defaults via Pydantic ValidationError (Phase 98 pattern)

### 6.3 notify_threshold validation
- Must be `>= 1` (Pydantic conint)
- Default 3
- Failure: `notify_threshold=0` → 422

### 6.4 merge_chapter_settings edge cases
- chapter_num=None → return settings unchanged (cover asset)
- chapter_num not in overrides → return settings unchanged (fast path)
- chapter_overrides empty → return settings unchanged
- All subset field types already validated at PUT time

### 6.5 record_failure counter edge cases
- Unknown project_slug → no-op (don't crash)
- Threshold reached: emit 1 warning, **don't reset** — counter stays elevated until success
- Project restart → counter lost (Phase 99 trade-off)
- Concurrent calls: GIL-safe (dict[int] += 1 atomic in CPython)
- record_success when count=0 → no-op (no negative counter)
- Caller (pipeline) passes `project_root` + `threshold` (notifications module stays yaml-free, consistent with `audit_log.record_event` signature)

### 6.6 resolve_model is_fallback edge cases
- is_fallback=True but fallback_models[provider] missing → fall through to default_models[provider]
- is_fallback=False but fallback_models[provider] exists → **ignored** (fallback_models is fallback-path-only)
- Both default_models and fallback_models missing → provider default model (Phase 100 behavior)

### 6.7 Frontend UX errors
- chapter_overrides table: duplicate chapter_num → "Add row" button disabled when invalid
- notify_threshold slider: 1-10 hardcoded range
- PUT failure (422) → Naive UI message.error with backend detail

## 7. Testing strategy

### 7.1 Backend pytest (new files)

| Test file | Coverage |
|-----------|----------|
| `packages/lingwen-illustrations/tests/test_project_settings_phase102.py` (NEW) | 3 fields back-compat (old yaml without new fields → defaults fill); Pydantic validation (invalid provider / invalid model / invalid chapter_num / notify_threshold < 1); round-trip yaml save/load preserves new fields |
| `packages/lingwen-illustrations/tests/test_pipeline_chapter_overrides.py` (NEW) | merge_chapter_settings: chapter in overrides → merged; chapter not in overrides → unchanged; chapter_num=None → unchanged; chapter_overrides empty → unchanged; override wins on conflict; immutable (no mutation) |
| `packages/lingwen-illustrations/tests/test_pipeline_fallback_models.py` (NEW) | resolve_model is_fallback=True: prefer fallback_models[provider]; fallback_models missing → fall through to default_models; provider default fallback; is_fallback=False → ignore fallback_models |
| `packages/lingwen-illustrations/tests/test_notifications_threshold.py` (NEW) | record_failure increments; record_success resets; threshold emit warning; below threshold no warning; per-project isolated counter; concurrent failures safe; notify_threshold=1 → first failure emits |
| `tests/test_phase102_*.py` (NEW regression guards) | G1-G12 regression guards covering new invariants + persistence |

### 7.2 Frontend vitest (extend existing)

| Test file | Coverage |
|-----------|----------|
| `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.spec.js` (extend) | fallback_models table renders + add/remove row; chapter_overrides table renders + add/remove row + invalid key blocks; notify_threshold slider updates v-model |
| `apps/dashboard/src/stores/useProjectSettings.spec.js` (extend) | store has 3 new fields; load() populates them; save() persists them; defaults applied when API returns old-shape data |

### 7.3 Validation gates

| Gate | Target |
|------|--------|
| `pytest packages/lingwen-illustrations/tests/` | existing 268 + ~25 new tests pass |
| `pytest apps/studio_api/tests/` | existing settings tests + ~6 new pass |
| `pnpm vitest run apps/dashboard/src/components/illustrations/` | existing 4 + ~6 new pass |
| `pnpm vitest run apps/dashboard/src/stores/useProjectSettings.spec.js` | store tests pass |
| `pnpm tsc --noEmit` | 0 new errors (48 pre-existing baseline) |
| `ruff check` | clean on introduced |
| regression guards G1-G12 | GREEN |
| I094 + I095 invariants | recorded in `.lingwen/architecture.yml` + CLAUDE.md |

### 7.4 Regression guards outline (G1-G12)

| Guard | Check |
|-------|-------|
| G1 | `ProjectSettings` schema file contains 3 new field names |
| G2 | `pipeline.merge_chapter_settings` function exists |
| G3 | `pipeline.resolve_model` accepts `is_fallback` kwarg |
| G4 | `notifications.record_failure` / `record_success` helpers exist |
| G5 | `notifications._consecutive_failures` state + warning emit logic |
| G6 | `chapter_overrides` Pydantic subset validator |
| G7 | `fallback_models` Pydantic provider/model validator |
| G8 | `notify_threshold >= 1` Pydantic validator |
| G9 | I094 + I095 invariants in `.lingwen/architecture.yml` |
| G10 | Frontend `ProjectSettingsIllustration.vue` mounts 3 new sections |
| G11 | `useProjectSettings` store has 3 new fields |
| G12 | Backward compat: Phase 101 yaml (without 3 new fields) loads with defaults |

## 8. Atomic commits (15 commits per Phase 90-101 pattern)

1. `docs(phase-102): design spec + implementation plan`
2. `feat(phase-102): ProjectSettings schema — 3 new fields + validators`
3. `test(phase-102): ProjectSettings schema back-compat + Pydantic validation`
4. `feat(phase-102): pipeline.merge_chapter_settings helper`
5. `test(phase-102): merge_chapter_settings — chapter in/out/None/empty/conflict/immutable`
6. `feat(phase-102): pipeline.resolve_model — is_fallback param + fallback_models priority`
7. `test(phase-102): resolve_model — fallback_models priority + default fallback`
8. `feat(phase-102): notifications.record_failure/record_success + threshold warning`
9. `test(phase-102): failure tracker — increment/reset/threshold/per-project/concurrent`
10. `feat(phase-102): NotificationEvent.severity field`
11. `test(phase-102): integration — pipeline emits warning on threshold crossing`
12. `feat(phase-102): api/illustrations.ts — 3 fields type threading`
13. `feat(phase-102): useProjectSettings store — 3 fields`
14. `feat(phase-102): ProjectSettingsIllustration — fallback_models section`
15. `feat(phase-102): ProjectSettingsIllustration — chapter_overrides section`
16. `feat(phase-102): ProjectSettingsIllustration — notify_threshold slider`
17. `test(phase-102): frontend — 3 sections + store sync`
18. `test(phase-102): 12 regression guards G1-G12 + I094 + I095 invariants`
19. `docs(phase-102): CLAUDE.md v59.0 → v60.0 + I094 + I095 + handoff + BACKLOG sync`

## 9. Future work

- **Phase 102+ (if any)**: Telemetry-driven chain reorder (use failure history to suggest fallback_chain reorder) — gated on Phase 102 failure tracker data accumulation
- **REQ-004 团队协作**: separate brainstorming — multi-user editing / conflict resolution / permission grading
- **Per-chapter `default_models` overrides** (if requested) — extend chapter_overrides whitelist
- **notify_threshold per event_type** (if requested) — extend to dict[event_type, int]

## 10. References

- Phase 90 — illustrations REQ-002 v1 baseline
- Phase 95 — ProjectSettingsPage substitution closure (component substitution documented)
- Phase 96 — image provider adapters (multi-provider)
- Phase 97 — reference image i2i
- Phase 98 — ProjectSettings extension + LRU archive
- Phase 99 — notification center (in-process SSE)
- Phase 100 — multi-model per provider
- Phase 101 — atomic provider fallback (I093)

## 11. Open questions

None. All design questions resolved in brainstorm session (2026-09-20).