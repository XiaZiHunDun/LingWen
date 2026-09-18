# Phase 100 Multi-Model Per Provider (REQ-002 v2 #5) — Design Spec

> **Date**: 2026-09-18
> **Phase**: v57.0 → v58.0
> **Status**: design approved, awaiting implementation
> **Cluster**: Phase 90-100 = 11 phases / 1 NEW package + 5 carryover closures + 5 REQ-002 v2 sub-projects delivered (image provider adapters + reference image i2i + ProjectSettings+LRU + notification center + **multi-model per provider**)

---

## 1. Motivation

Phase 96 introduced multi-provider dispatch (minimax / openai / stability), each adapter hardcoding a single model in the API payload:

| Provider | Hardcoded model |
|----------|-----------------|
| minimax | `minimax-multimodal` |
| openai | `dall-e-3` |
| stability | `sd3-medium` |

This caps creative choice at the provider level only. Users can't pick `gpt-image-1` over `dall-e-3`, can't experiment with `sd3-large-turbo` for cheaper renders, can't pin `sd3-large` for a project that needs higher fidelity.

**Phase 100 goal**: every provider exposes its full model catalog, and users can select models at **two granularities** — per-call (UI override) and per-project (persistent default).

### In scope

- **11 models** across 3 providers (full catalog: 4 OpenAI + 5 Stability + 2 MiniMax)
- **Per-call override** in `GenerateIllustrationDialog` (provider switch → model picker refreshes)
- **Per-project default** persisted to `illustration_settings.yaml` as `default_models: { provider: model }`
- **Strict enum validation** — `UnknownModelError` (422) on invalid model
- **Resolution algorithm**: explicit > project default > provider default

### Out of scope (deferred)

- **i2i model-aware dispatch** — `model` param ignored on i2i path (uses provider's i2i-default model); v2 follow-up if user-facing need arises
- **Model quality/size attributes** as first-class fields — surfaced via existing API params only when needed
- **Per-call preview of model capabilities** (cost, latency) — defer to v2 analytics
- **Cross-provider model fallback** (atomic provider fallback is REQ-002 v2 #6, separate phase)

---

## 2. Architecture

### Component boundary

```
┌─────────────────────────────────────────────────────────┐
│  apps/dashboard (Vue 3 + Pinia)                         │
│   ├─ components/illustration/                           │
│   │   ├─ ProjectSettingsIllustration.vue                │
│   │   │     [+ per-provider model dropdowns]            │
│   │   └─ GenerateIllustrationDialog.vue                 │
│   │         [+ model picker (filters by provider)]      │
│   └─ api/illustrations.ts                               │
│         [+ fetchProviderModels(name)]                   │
└─────────────────────────────────────────────────────────┘
                    ↑ GET /providers/{name}/models
                    ↓ POST /illustrations/generate  (body+model)
┌─────────────────────────────────────────────────────────┐
│  apps/studio_api (FastAPI)                              │
│   └─ routes/illustrations.py                            │
│       ├─ GET /api/illustrations/providers/{name}/models │
│       ├─ POST /api/projects/{slug}/illustrations/generate│
│       │     [+ model: str | None]                       │
│       └─ PUT /api/projects/{slug}/illustrations/{id}/regenerate│
│             [+ model: str | None]                       │
└─────────────────────────────────────────────────────────┘
                    ↑ resolve_model(provider, settings, explicit)
                    ↓
┌─────────────────────────────────────────────────────────┐
│  packages/lingwen-illustrations/ (Python)               │
│   ├─ providers/                                         │
│   │   ├─ minimax.py   [+ KNOWN_MODELS + DEFAULT_MODEL   │
│   │   │                 + model param]                  │
│   │   ├─ openai.py    (4 models)                        │
│   │   ├─ stability.py (5 models)                        │
│   │   └─ __init__.py [+ ProviderAdapter.models +        │
│   │                    .default_model fields]           │
│   ├─ exceptions.py   [+ UnknownModelError]              │
│   └─ pipeline.py     [+ resolve_model() helper +        │
│                        model param threading]           │
└─────────────────────────────────────────────────────────┘
                    ↓ IllustrationMetadata.model (existing field)
                <project>/assets/.../...meta.json (records actual model)
```

### Invariant (I092 NEW)

`packages/lingwen-illustrations/src/lingwen_illustrations/providers/{minimax,openai,stability}.py:KNOWN_MODELS` is the sole model catalog per provider. `ProviderAdapter.models` and `.default_model` expose the catalog to consumers. `UnknownModelError` (added to `exceptions.py`) is the sole invalid-model error. Any path that hardcodes a model name outside the provider module, or bypasses the enum validation, is illegal. Pipeline threading must resolve through `resolve_model()` — never directly read `request.model` without going through the helper.

### Resolution algorithm

```python
def resolve_model(
    provider: str,
    explicit: str | None,            # from API request
    project_settings: dict | None,   # from illustration_settings.yaml
    adapter: ProviderAdapter,
) -> str:
    """Return the effective model for this generation.

    Order: explicit > project default > adapter default.
    Stale project defaults (not in adapter.models) → log warning + fallback.
    Explicit must be in adapter.models → else raise UnknownModelError.
    """
    if explicit is not None:
        if explicit not in adapter.models:
            raise UnknownModelError(provider, explicit, adapter.models)
        return explicit
    if project_settings and project_settings.get("default_models"):
        proj_default = project_settings["default_models"].get(provider)
        if proj_default is not None:
            if proj_default not in adapter.models:
                logger.warning(
                    "project default_model '%s' not in provider '%s' models %s; "
                    "falling back to %s",
                    proj_default, provider, adapter.models, adapter.default_model,
                )
                return adapter.default_model
            return proj_default
    return adapter.default_model
```

---

## 3. Data Model

### ProviderAdapter extension (Phase 97 → Phase 100)

```python
# packages/lingwen-illustrations/src/lingwen_illustrations/providers/__init__.py

@dataclass(frozen=True)
class ProviderAdapter:
    name: str
    generate: Callable[..., Awaitable[bytes]]
    generate_with_reference: Callable[..., Awaitable[bytes]]
    supports_i2i: bool
    # NEW (Phase 100)
    models: tuple[str, ...]       # canonical catalog for this provider
    default_model: str             # provider-level default if project has none
```

### Per-provider module catalog

```python
# providers/minimax.py
_PROVIDER_NAME = "minimax"
SUPPORTS_I2I = True
_DEFAULT_STRENGTH = 0.5
KNOWN_MODELS: tuple[str, ...] = (
    "minimax-multimodal",     # current default
    "minimax-vision-01",
)
DEFAULT_MODEL: str = "minimax-multimodal"

# providers/openai.py
KNOWN_MODELS: tuple[str, ...] = (
    "dall-e-3",                # current default
    "dall-e-3-hd",             # HD variant
    "dall-e-2",                # legacy / cheaper
    "gpt-image-1",             # newest
)
DEFAULT_MODEL: str = "dall-e-3"

# providers/stability.py
KNOWN_MODELS: tuple[str, ...] = (
    "sd3-medium",              # current default
    "sd3-large",
    "sd3-large-turbo",
    "stable-image-core",
    "stable-image-ultra",
)
DEFAULT_MODEL: str = "sd3-medium"
```

### Settings YAML schema (Phase 98 → Phase 100)

```yaml
# <project>/.lingwen/illustration_settings.yaml
default_provider: minimax
default_models:                      # NEW (Phase 100)
  minimax: minimax-multimodal
  openai: dall-e-3
  stability: sd3-medium
auto_generate: false                 # Phase 98
max_assets: 20                       # Phase 98
confirm_before_generate: false       # Phase 98
```

**Backwards compat**: missing `default_models` key → falls back to `adapter.default_model` for every generation. No migration needed for existing projects.

### Exception class

```python
# packages/lingwen-illustrations/src/lingwen_illustrations/exceptions.py

class UnknownModelError(ValueError):
    """Raised when explicit model is not in provider's KNOWN_MODELS catalog."""

    def __init__(self, provider: str, model: str, known: tuple[str, ...]) -> None:
        self.provider = provider
        self.model = model
        self.known = known
        super().__init__(
            f"unknown model '{model}' for provider '{provider}', "
            f"expected one of {known}"
        )
```

---

## 4. Backend module changes

### 4.1 Provider adapter signature change

Each `generate()` and `generate_with_reference()` gains a `model: str | None = None` keyword argument:

```python
# providers/minimax.py
async def generate(
    *,
    prompt: str,
    api_key: str,
    api_host: str,
    model: str | None = None,    # NEW (Phase 100). None → use DEFAULT_MODEL.
    timeout: float = 60.0,
) -> bytes:
    effective_model = model if model is not None else DEFAULT_MODEL
    if effective_model not in KNOWN_MODELS:
        raise UnknownModelError(_PROVIDER_NAME, effective_model, KNOWN_MODELS)
    payload = {
        "model": effective_model,
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "response_format": "b64_json",
    }
    # ... (rest unchanged)
```

**i2i path note**: `generate_with_reference()` also accepts `model` for API consistency, but Phase 100 ignores it (uses provider's i2i-default model). Documented in docstring as "i2i model selection deferred to v2".

### 4.2 Pipeline threading

```python
# packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py

async def generate_illustration(
    *,
    project_root: Path,
    project_slug: str,
    type: _TYPE,
    chapter_num: int | None,
    style_preset: str,
    custom_prompt: str | None,
    api_key: str,
    api_host: str,
    provider: str = "minimax",
    model: str | None = None,            # NEW (Phase 100). None → resolve.
    reference_image_bytes: bytes | None = None,
) -> IllustrationMetadata:
    # ... (stages 1-2 unchanged)

    adapter = get_provider(provider)
    settings = _load_illustration_settings(project_root)   # extracted helper
    effective_model = resolve_model(provider, model, settings, adapter)

    # Stage 3 dispatch (text vs i2i; i2i ignores effective_model for v1)
    if reference_image_bytes is not None:
        if not adapter.supports_i2i:
            raise GenerateError(...)
        image_bytes = await adapter.generate_with_reference(
            prompt=final_prompt,
            reference_image_bytes=reference_image_bytes,
            api_key=api_key,
            api_host=api_host,
            # NOTE: model NOT threaded to i2i path (Phase 100 v1).
        )
    else:
        image_bytes = await adapter.generate(
            prompt=final_prompt,
            api_key=api_key,
            api_host=api_host,
            model=effective_model,    # NEW
        )

    # Stage 4 metadata: model = effective_model (always, never raw input)
    meta = IllustrationMetadata(
        ...
        model=effective_model,
        ...
    )
```

**Refactor**: extract `_load_illustration_settings(project_root) -> dict` helper from existing inline code (Phase 98 block that reads `illustration_settings.yaml` for `max_assets` / `auto_generate` / `confirm_before_generate`). Now also reads `default_models`. Single helper, used in both `generate_illustration` and `regenerate_illustration`.

### 4.3 regenerate_illustration

Same threading: `model: str | None = None` param, `effective_model = resolve_model(...)`, passed to adapter.generate. Default `None` means "use the model's behavior the asset was originally generated with" — but resolution still kicks in (if user explicitly passes model OR project default has changed since original generation, the new model wins). Documented behavior.

### 4.4 `_MODEL_FOR_PROVIDER` removal

Currently `pipeline.py:57-61` has `_MODEL_FOR_PROVIDER` dict for metadata. **Phase 100 deletes this** since `adapter.default_model` and the resolved `effective_model` are the single source of truth. `_resolve_model()` function deleted. Cleaner pipeline.

---

## 5. API contract

### 5.1 Existing endpoints (extended)

#### `POST /api/projects/{slug}/illustrations/generate`

Request body (Phase 97 + Phase 100):
```json
{
  "type": "cover",
  "chapter_num": null,
  "style_preset": "ink",
  "custom_prompt": null,
  "provider": "openai",
  "model": "gpt-image-1",            // NEW (Phase 100). Optional.
  "use_project_reference": false,
  "reference_image": null
}
```

- `model: str | None` — explicit override; **422** if not in provider's KNOWN_MODELS
- Missing field → resolved from project settings or provider default

#### `PUT /api/projects/{slug}/illustrations/{id}/regenerate`

Request body (Phase 94 + Phase 100):
```json
{
  "provider": "openai",              // existing — None means use existing_meta.provider
  "model": "gpt-image-1",            // NEW (Phase 100). Optional.
  "use_project_reference": false,
  "reference_image": null
}
```

Same validation rules.

### 5.2 New endpoint

#### `GET /api/illustrations/providers/{name}/models`

Response (200):
```json
{
  "provider": "openai",
  "models": ["dall-e-3", "dall-e-3-hd", "dall-e-2", "gpt-image-1"],
  "default_model": "dall-e-3"
}
```

- **404** if provider name not in `KNOWN_PROVIDERS`
- No auth required (catalog is public knowledge)
- Frontend calls once on app boot, caches per provider

---

## 6. Frontend UX

### 6.1 ProjectSettingsIllustration.vue — new section

```
┌─ 插图设置 ─────────────────────────────────────┐
│ 默认 Provider: [minimax ▼]                    │
│                                                │
│ ── 默认模型 (Phase 100) ──────────────────────│
│   minimax:    [minimax-multimodal      ▼]    │
│   openai:     [dall-e-3                ▼]    │
│   stability:  [sd3-medium              ▼]    │
│                                                │
│ 自动生成: [ ] 启用                             │
│ 最大资产数: [20]                                │
│ 生成前确认: [ ] 启用                            │
└────────────────────────────────────────────────┘
```

- 3 dropdowns, one per provider (hardcoded list matches `KNOWN_PROVIDERS`)
- Options fetched via `fetchProviderModels(name)` on component mount
- "Provider default" sentinel option per dropdown (resets to `default_model`)
- Persists `default_models: { provider: model }` dict via existing `PATCH /projects/{slug}/settings`

### 6.2 GenerateIllustrationDialog.vue — model picker

```
┌─ 生成插图 ────────────────────────────┐
│ 类型:    [封面 ▼]                     │
│ Provider: [openai ▼]                  │
│ 模型:     [gpt-image-1         ▼]    │ ← NEW (Phase 100)
│   ↳ "默认: dall-e-3" hint below      │
│ 风格:    [水墨写意 ▼]                 │
│ 自定义提示: [________________]         │
│ 使用参考图: [ ]                        │
│ [取消]                  [生成]        │
└───────────────────────────────────────┘
```

- Provider dropdown unchanged (Phase 96)
- **NEW** model dropdown: appears below provider, options = `fetchProviderModels(provider).models`
- Default selection = `fetchProviderModels(provider).default_model` OR project default if set
- Disabled when `use_project_reference = true` (i2i path ignores model in v1)
- "默认: dall-e-3" hint below when project default differs from current selection

### 6.3 api/illustrations.ts typed wrappers

```typescript
// Existing wrappers gain optional model parameter:
export function generateIllustration(
  slug: string,
  body: {
    type: 'cover' | 'chapter'
    chapter_num: number | null
    style_preset: string
    custom_prompt: string | null
    provider: string
    model?: string | null            // NEW
    use_project_reference?: boolean
    reference_image?: File | null
  }
): Promise<IllustrationMetadata>

export function regenerateIllustration(
  slug: string,
  assetId: string,
  body: {
    provider?: string | null
    model?: string | null            // NEW
    use_project_reference?: boolean
    reference_image?: File | null
  }
): Promise<IllustrationMetadata>

// NEW wrapper for the catalog endpoint:
export interface ProviderModelCatalog {
  provider: string
  models: string[]
  default_model: string
}

export function fetchProviderModels(name: string): Promise<ProviderModelCatalog>
```

---

## 7. Test strategy

| Level | Count | Focus |
|-------|-------|-------|
| Per-provider module (`minimax/openai/stability`) | 18 (6 each) | `KNOWN_MODELS` count, `DEFAULT_MODEL` in catalog, `generate(explicit model)` payload assertion, `generate(None)` uses default, `generate(invalid model)` → `UnknownModelError`, i2i path unchanged |
| `providers/__init__.py` (ProviderAdapter) | 3 | New `models` + `default_model` fields populated, `get_provider` returns correct catalog |
| `pipeline.py` (resolve_model + threading) | 5 | Resolution order (explicit > project > provider), `metadata.model` records resolved value (not raw input), `regenerate_illustration` threads model, `_MODEL_FOR_PROVIDER` dict removed |
| `illustration_settings.yaml` loader | 2 | Accepts `default_models` dict, missing key → empty dict (no error) |
| Route layer (`routes/illustrations.py`) | 4 | POST generate accepts `model`, POST generate 422 on invalid, PUT regenerate accepts `model`, GET providers/models returns catalog + 404 unknown |
| Frontend (vitest) | 6 | `useProjectSettings.default_models` setter/getter, `ProjectSettingsIllustration` 3 dropdowns render, `GenerateIllustrationDialog` model picker filter, i2i disables picker, `api/illustrations.ts` `fetchProviderModels` typed wrapper, `generateIllustration(model)` typed |
| **Regression guards** | **9** | G1 11 models declared + G2 ProviderAdapter new fields + G3 UnknownModelError class + G4 pipeline.resolve_model signature + G5 settings schema accepts default_models + G6 route accepts model + G7 GET /models endpoint registered + G8 IllustrationMetadata.model records resolved value + G9 I092 in architecture.yml |

---

## 8. Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Provider API silently ignores unknown `model` field | MED | Trust 400 response — `UnknownModelError` already raised before HTTP call; provider-side validation is defense in depth |
| Stale project default model after provider catalog shrinks | LOW | Log warning + fallback to provider default; user can update settings on next visit |
| i2i path silently uses different model than user selected | LOW | UI disables model picker when `use_project_reference=true`; docstring documents Phase 100 v1 limitation |
| Frontend cache of model catalog stale on new provider added | LOW | `fetchProviderModels` called on app boot; new providers require app reload (acceptable) |
| `dall-e-3-hd` quality param conflict | LOW | Phase 100 treats `dall-e-3-hd` as separate model name (catalog); no `quality` param in payload; v2 follow-up if API requires both |
| MiniMax model names speculative | MED | "minimax-vision-01" is a placeholder for the catalog entry; real API may use different name — Phase 100 v1 ships with placeholder, Phase 101 (or v2 follow-up) corrects if needed |

---

## 9. Integration points

- `packages/lingwen-illustrations/src/lingwen_illustrations/providers/{minimax,openai,stability}.py` — module-level constants + signature changes
- `packages/lingwen-illustrations/src/lingwen_illustrations/providers/__init__.py` — `ProviderAdapter` extension + `get_provider` updated
- `packages/lingwen-illustrations/src/lingwen_illustrations/exceptions.py` — `UnknownModelError` class
- `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py` — `model` param threading + `resolve_model` helper + `_load_illustration_settings` extraction + `_MODEL_FOR_PROVIDER` removal
- `apps/studio_api/routes/illustrations.py` — POST/PUT routes accept `model`; new GET `/providers/{name}/models`
- `apps/studio_api/routes/__init__.py` facade — registration (Phase 96/97/98/99 convention)
- `apps/dashboard/src/api/illustrations.ts` — typed wrappers extended + new `fetchProviderModels`
- `apps/dashboard/src/components/.../ProjectSettingsIllustration.vue` — new "默认模型" section with 3 dropdowns
- `apps/dashboard/src/components/.../GenerateIllustrationDialog.vue` — model picker dropdown
- `packages/lingwen-illustrations/pyproject.toml` — no new deps (uses stdlib only)
- `.lingwen/architecture.yml` — I092 NEW invariant entry
- `CLAUDE.md` — v57.0 → v58.0 with Phase 100 entry + I092 row

---

## 10. Task breakdown (~12 atomic commits, ~700 LOC + 38 tests)

| # | Task | LOC est. | Tests |
|---|------|----------|-------|
| T1 | spec + plan (this doc + `2026-09-18-phase-100-multi-model.md`) | — | — |
| T2 | `exceptions.py` `UnknownModelError` class + 3 unit tests | ~25 | 3 |
| T3 | `providers/minimax.py` + `providers/openai.py` + `providers/stability.py` (KNOWN_MODELS + DEFAULT_MODEL + model param + signature updates) + 18 unit tests | ~60 | 18 |
| T4 | `providers/__init__.py` `ProviderAdapter` extension + `get_provider` updates + 3 adapter tests | ~30 | 3 |
| T5 | `pipeline.py` `resolve_model` helper + threading + `_load_illustration_settings` extraction + `_MODEL_FOR_PROVIDER` removal + 5 pipeline tests + 2 settings loader tests | ~80 | 7 |
| T6 | `routes/illustrations.py` POST/PUT `model` field + new GET `/providers/{name}/models` + 4 route tests | ~60 | 4 |
| T7 | `api/illustrations.ts` typed wrappers extended + `fetchProviderModels` wrapper + 1 typed wrapper test | ~40 | 1 |
| T8 | `ProjectSettingsIllustration.vue` 3 model dropdowns + `useProjectSettings.default_models` setter/getter + 2 vitest tests | ~80 | 2 |
| T9 | `GenerateIllustrationDialog.vue` model picker (filter by provider, i2i disable, hint) + 3 vitest tests | ~80 | 3 |
| T10 | 9 regression guards (G1-G9) + I092 invariant | ~150 | 9 |
| T11 | ruff clean + pnpm tsc 0 new errors + final pytest + vitest gates | — | — |
| T12 | docs (CLAUDE.md v57.0 → v58.0 + I092 + handoff + BACKLOG row + CURRENT_STATUS row) | — | — |

---

## 11. Validation gates

| Gate | Target |
|------|--------|
| Backend pytest | lingwen-illustrations 218 → ~245 + studio_api 149 → ~153 + phase90/96/97/98/99 guards all GREEN + 9 NEW phase100 guards |
| Frontend vitest | 17 notification-center tests + 6 NEW multi-model tests GREEN + full app suite no regressions |
| `pnpm tsc --noEmit` | 0 new errors |
| `ruff check` | clean on introduced |
| `pnpm exec knip` | 0 new issues |
| Manual smoke | (1) Set project default openai=gpt-image-1; generate without UI override → metadata.model="gpt-image-1"; (2) Generate with UI override model=dall-e-3-hd → 422; (3) Generate with valid dall-e-3-hd → metadata.model="dall-e-3-hd"; (4) i2i generation with use_project_reference=true → model picker disabled in UI |
| I092 invariant | recorded in `.lingwen/architecture.yml` + preserved by G1-G9 |

---

## 12. Cluster cumulative (post-Phase 100)

| Phase | Sub-project |
|-------|-------------|
| 96 | image provider adapters (minimax/openai/stability) |
| 97 | reference image i2i |
| 98 | ProjectSettings extension + LRU archive |
| 99 | notification center |
| **100** | **multi-model per provider** |
| 101+ (candidates) | atomic provider fallback / v2 settings persistence extension (2 of 7 remaining) |

**REQ-002 v2 进度**: 5 / 7 sub-projects delivered. 2 remaining.

---

## 13. Lessons anticipated

1. **Resolution layering is fragile to ordering bugs**: explicit > project > provider must be tested with all 3 input combinations; per-Phase 99 lesson 2 (double-write dual invariant), tests must verify the EXACT path that wins, not just "some model was used".
2. **Adapter dataclass extension preserves monkeypatch compat**: Phase 97's `importlib.import_module` lookup pattern means `monkeypatch.setattr("lingwen_illustrations.providers.openai.DEFAULT_MODEL", "x")` still works for new fields — no special-casing needed.
3. **Settings YAML loader belongs in one helper**: Phase 98 inlined settings reading inside `pipeline.generate_illustration`. Phase 100 extracts to `_load_illustration_settings(project_root)` — single read path, easier to test, prevents drift between `generate` and `regenerate`.
4. **i2i model parameter asymmetry is a v1 limitation, not a bug**: explicitly documented in adapter docstrings + UI disable. v2 follow-up tracks in BACKLOG.
5. **Full catalog vs curated catalog trade-off**: Full (11 models) gives users choice but increases catalog surface. Curated (3-5) is opinionated. Phase 100 ships full — future telemetry may reveal which models are actually used; Phase 101 can prune.

---

## 14. Acceptance criteria

Phase 100 is complete when:

1. ✅ Backend: 3 providers expose `KNOWN_MODELS` + `DEFAULT_MODEL` + accept `model` param + validate via `UnknownModelError`
2. ✅ `ProviderAdapter` extended with `models` + `default_model` fields
3. ✅ Pipeline `resolve_model()` helper implemented with explicit > project > provider order
4. ✅ `illustration_settings.yaml` schema accepts `default_models` dict (backwards compatible)
5. ✅ Frontend: `ProjectSettingsIllustration` has 3 per-provider model dropdowns
6. ✅ Frontend: `GenerateIllustrationDialog` has model picker that filters by provider + disables on i2i
7. ✅ API: `GET /api/illustrations/providers/{name}/models` returns catalog
8. ✅ All 9 regression guards GREEN
9. ✅ pytest + vitest + tsc + ruff clean
10. ✅ Manual smoke test: explicit override / project default / provider default all produce correct `metadata.model`
11. ✅ CLAUDE.md v57.0 → v58.0 + I092 + handoff doc committed
12. ✅ `_MODEL_FOR_PROVIDER` legacy dict removed from pipeline (Phase 100 cleanup)