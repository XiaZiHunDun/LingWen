# Phase 101 — Atomic Provider Fallback — Design Spec

> **Date**: 2026-09-18
> **Phase**: v58.0 → v59.0
> **Cluster**: REQ-002 v2 #6 (sixth sub-project delivered; 2/7 remaining after this phase)
> **Status**: Designed; awaiting user approval before implementation plan

## Summary

Phase 101 makes illustration generation resilient to provider outages. When the primary
provider's image API fails with a transient error (5xx, 429, timeout, network), the
pipeline automatically tries the next provider in a configurable fallback chain.
Succeeded metadata records the successful provider; the audit log captures every
attempt (provider, model, error, timestamp) in a single `generation` event.

## Motivation

Phase 96 introduced provider adapters for 3 image generation providers
(minimax / openai / stability). Phase 100 added multi-model selection per
provider. Today, if a provider's API is down or rate-limiting, generation fails
with HTTP 502 and the user must manually retry — usually by switching providers
in the UI. Phase 101 makes this transparent: configure a fallback chain once
in project settings, and the pipeline handles transient failures automatically.

## Scope

In scope:
- New module `lingwen_illustrations.fallback` (Attempt dataclass, ProviderExhaustedError, dispatch_with_fallback).
- ProjectSettings extension: `fallback_chain: list[str] = []` field (Phase 100 default-fill back-compat).
- GenerateRequest / RegenerateRequest extension: `fallback_chain: list[str] | None = None` optional override.
- Route layer: `_resolve_provider_for_request` returns `(provider, fallback_chain)`; `ProviderExhaustedError` → HTTP 502 with `detail.attempts`.
- Pipeline integration: `generate_illustration` and `regenerate_illustration` text-only path uses `dispatch_with_fallback`; i2i path unchanged (no fallback).
- ProjectSettingsIllustration UI: multi-select picker for fallback chain (from KNOWN_PROVIDERS).
- Frontend typed API wrappers + useProjectSettings store field.
- I093 NEW invariant.
- 10 regression guards G1-G10.

Out of scope (deferred to future phases):
- Stage 1 LLM fallback (lingwen-llm-service has its own retry).
- i2i path fallback (provider-specific i2i models are not interchangeable).
- Per-provider model mapping in fallback chain (each provider uses its own default).
- Adaptive learning from past failures (telemetry-driven chain reorder).
- Cross-project fallback chains (per-project only in v1).

## Design decisions

### 1. Trigger scope

Only Stage 3 `GenerateError(retryable=True)` triggers fallback. Other exception
classes propagate immediately without retrying the next provider:

| Exception | Fallback? | Reason |
|-----------|-----------|--------|
| `GenerateError(retryable=True)` | yes | Transient (5xx / 429 / timeout / network) |
| `GenerateError(retryable=False)` | no | 4xx user errors (401 / 403 / 422 / i2i unsupported) |
| `UnknownProviderError` | no | Configuration bug |
| `UnknownModelError` | no | Configuration bug |
| `LoadError` | no | Provider-independent |
| `ExtractError` | no | LLM retry handled by lingwen-llm-service |
| `ComposeError` | no | Code bug |
| `StoreError` | no | Disk / permission issue, not provider |

### 2. Fallback chain source

Priority order (highest first):
1. API request `body.fallback_chain` (one-off override for debugging)
2. Project settings `illustration_settings.yaml` `fallback_chain`
3. Empty (no fallback)

The chain is a list of provider names from `KNOWN_PROVIDERS`. The primary
provider (from `_resolve_provider_for_request`) is always first; the chain
appends to it. Empty chain = no fallback, behaves identically to Phase 100.

### 3. Audit / metadata semantics

- `meta.provider` records the **successful** provider (last attempt).
- `meta.model` records the **successful** model (resolved per-provider by
  Phase 100 logic).
- Audit `generation` / `regeneration` event has `extra.attempts: list[Attempt]`
  with one entry per provider tried. The successful attempt has `error: null`;
  failed attempts have `error: "<ExceptionClass>: <message>"`.
- Single event total (not one per attempt); the Phase 99 notification publish
  fires once with the same ULID.
- `ProviderExhaustedError` is raised on chain exhaustion; no audit event is
  written (the failure path doesn't reach `record_event`). The exception
  carries `attempts` for the route layer to surface in HTTP `detail.attempts`.

### 4. Model resolution per provider

Each provider in the chain independently resolves its model via the existing
Phase 100 `resolve_model()` 3-tier order:
- For primary: `explicit` param is the API request's `model` (or None).
- For fallback providers: `explicit = None` → use project default → provider default.

Models are not portable across providers (e.g. `dall-e-3` exists only on openai),
so attempting to thread the primary's model into fallback would just produce
`UnknownModelError`. Each provider uses its own default model when called as
a fallback.

### 5. Path coverage

- `generate_illustration` text-only path: ✅ fallback enabled.
- `generate_illustration` i2i path (reference_image_bytes present): ❌ no fallback.
  i2i models are provider-specific; switching providers mid-pipeline would
  silently drop the reference. The current `GenerateError("not supported", retryable=False)`
  continues to surface as 422 with the same shape as Phase 97.
- `regenerate_illustration` text-only path: ✅ fallback enabled.
  Primary = `body.provider or existing_meta.provider`; chain appended.
- `regenerate_illustration` i2i path: ❌ no fallback (same reason).

## Architecture

### New module: `packages/lingwen-illustrations/src/lingwen_illustrations/fallback.py`

```python
@dataclass(frozen=True)
class Attempt:
    provider: str
    model: str
    error: str | None    # None = success
    ts: str              # ISO 8601 UTC


class ProviderExhaustedError(GenerateError):
    """All providers in chain failed. Carries attempts list."""

    def __init__(
        self,
        message: str,
        *,
        attempts: list[Attempt],
        provider: str,
    ) -> None:
        super().__init__(message, provider=provider, retryable=False)
        self.attempts = attempts


async def dispatch_with_fallback(
    *,
    chain: list[str],                          # ordered; first is primary
    explicit_model: str | None,                # primary override only
    project_settings: dict | None,
    api_credentials_for: Callable[[str], tuple[str, str]],
    prompt: str,
    i2i: bool = False,
    reference_image_bytes: bytes | None = None,
) -> tuple[bytes, str, str, list[Attempt]]:
    """Iterate chain. Returns (bytes, success_provider, success_model, attempts)."""
```

Internal flow:
1. Dedup chain preserving order; filter to KNOWN_PROVIDERS (warn + skip invalid).
2. For each provider in chain:
   - `adapter = get_provider(provider)`
   - `model = resolve_model(provider, explicit=(explicit_model if first else None), project_settings, adapter)`
   - If i2i: pre-check `adapter.supports_i2i`; if not supported, raise `GenerateError(retryable=False)` (no fallback for i2i)
   - Call `adapter.generate_with_reference(...)` (i2i) or `adapter.generate(...)` (text)
   - On success: append Attempt(error=None), return bytes + provider + model + attempts
   - On `GenerateError(retryable=False)`: re-raise immediately
   - On `GenerateError(retryable=True)`: append Attempt(error=str), continue
   - On `UnknownProviderError` / `UnknownModelError`: re-raise immediately
3. If chain exhausted: raise `ProviderExhaustedError` with full attempts list.

### Settings extension: `apps/studio_api/routes/project_settings.py`

```python
class ProjectSettings(BaseModel):
    default_provider: Literal["minimax", "openai", "stability"] = "minimax"
    default_models: dict[str, str] = {}                      # Phase 100
    auto_generate: bool = False                              # Phase 98
    max_assets: int = 20                                    # Phase 98
    confirm_before_generate: bool = False                   # Phase 98
    fallback_chain: list[str] = []                          # NEW (Phase 101)
```

Back-compat: Pydantic v2 default fill (Phase 100 same pattern). Old yaml files
without `fallback_chain` load successfully with empty list (no fallback).

### Route extension: `apps/studio_api/routes/illustrations.py`

```python
class GenerateRequest(BaseModel):
    # ... existing fields ...
    fallback_chain: Optional[list[str]] = None    # NEW (Phase 101)


def _resolve_provider_for_request(
    req_project_slug: str,
    body_provider: Optional[str],
    body_fallback_chain: Optional[list[str]],     # NEW
) -> tuple[str, list[str]]:
    """Returns (provider, fallback_chain). Priority:
    body_provider > settings.default_provider > 'minimax'
    body_fallback_chain > settings.fallback_chain > []
    """
```

`STAGE_HTTP_CODES` maps `ProviderExhaustedError → 502` (same as `GenerateError`,
since root cause is provider-side).

### Pipeline integration: `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py`

Both `generate_illustration` and `regenerate_illustration` replace the
Stage 4 text-only `adapter.generate(...)` call with:

```python
from lingwen_illustrations.fallback import dispatch_with_fallback

# Build chain: primary + body.fallback_chain (if provided)
chain = [provider]
if fallback_chain:
    chain.extend(fallback_chain)

if reference_image_bytes is not None:
    # i2i: no fallback. Preserve Phase 97 behavior.
    if not adapter.supports_i2i:
        raise GenerateError("...not supported...", retryable=False, provider=provider)
    image_bytes = await adapter.generate_with_reference(...)
    attempts = [Attempt(provider=provider, model=adapter.default_model, error=None, ts=...)]
else:
    image_bytes, success_provider, success_model, attempts = await dispatch_with_fallback(
        chain=chain,
        explicit_model=model,
        project_settings=settings,
        api_credentials_for=lambda p: _inline_credentials_for(p, settings),
        prompt=final_prompt,
    )

# meta.provider = success_provider, meta.model = success_model
# audit extra: {"attempts": [a.__dict__ for a in attempts]}
```

### UI extension: `apps/dashboard/src/components/illustrations/ProjectSettingsIllustration.vue`

Add `<n-select multiple>` after the default_provider dropdown:
- Options: KNOWN_PROVIDERS (fetched via existing GET /providers/{name}/models
  for available providers — actually just use static KNOWN_PROVIDERS list to
  avoid extra calls).
- v-model bound to `settings.fallback_chain`.
- Help text below: "如果主 provider 失败，将按顺序尝试这些 provider"

### Audit extra schema

```python
extra = {
    "auto_generate": _auto_generate,           # Phase 98
    "confirm_required": _confirm_required,      # Phase 98
    "attempts": [
        {
            "provider": "openai",
            "model": "dall-e-3",
            "error": "GenerateError: 502",
            "ts": "2026-09-18T10:30:00Z",
        },
        {
            "provider": "stability",
            "model": "sd3-large",
            "error": None,
            "ts": "2026-09-18T10:30:03Z",
        },
    ],
}
```

For HTTP 502 response on `ProviderExhaustedError`:
```python
detail = {
    "stage": "generate",
    "error": "all 3 providers failed: openai(GenerateError: 502), stability(GenerateError: timeout), minimax(...)",
    "retryable": False,
    "provider": "stability",   # last tried
    "attempts": [...],
}
```

## Data flow

### generate_illustration path

```
POST /api/illustrations/generate (body.provider, body.fallback_chain, body.model, ...)
  ↓
_resolve_provider_for_request(slug, body_provider, body_fallback_chain)
  → (provider, fallback_chain)
  ↓
_api_credentials_for(provider)  → (api_key, api_host)
  ↓
run_pipeline(provider, model, fallback_chain, ...)
  ↓
generate_illustration(...)
  ├── Stage 1a: _load_chapter_text, load_character_bible
  ├── Stage 2: extract_scene → scene_json
  ├── Stage 3: compose_prompt → final_prompt
  ├── Stage 4:
  │   ├── if reference_image_bytes: i2i path (no fallback)
  │   └── else: dispatch_with_fallback(chain=[provider, *fallback_chain], ...)
  │       → (bytes, success_provider, success_model, attempts)
  ├── Stage 5: storage.save_asset (meta.provider = success_provider, meta.model = success_model)
  └── Audit + Notification:
      record_event(event="generation", extra={"attempts": [...], ...})
      publish(NotificationEvent(...))   # same ULID
```

### dispatch_with_fallback chain iteration

```
chain = dedupe_preserve_order(filter_known([primary, *body.fallback_chain or settings.fallback_chain]))
attempts = []
for provider in chain:
    adapter = get_provider(provider)
    model = resolve_model(provider, explicit=(explicit_model if primary else None), settings, adapter)
    if i2i and not adapter.supports_i2i:
        raise GenerateError("...not supported...", retryable=False)  # not retried
    try:
        bytes = await (adapter.generate_with_reference if i2i else adapter.generate)(
            prompt=..., api_key=..., api_host=..., model=...)
        attempts.append(Attempt(provider, model, error=None, ts=...))
        return bytes, provider, model, attempts
    except GenerateError as e:
        if not e.retryable:
            raise   # 4xx, no fallback
        attempts.append(Attempt(provider, model, error=f"GenerateError: {e.message}", ts=...))
        continue
    except (UnknownProviderError, UnknownModelError):
        raise   # config bug

raise ProviderExhaustedError(message, attempts=attempts, provider=chain[-1])
```

### regenerate_illustration path

Symmetric to generate. Primary = `body.provider or existing_meta.provider`.
Chain = `[primary] + body.fallback_chain`. Same dispatch logic. Atomic swap
via `storage.replace_asset` preserved (Phase 94).

## Error handling

See "Trigger scope" table for the full classification.

### HTTP status mapping (route layer)

| Exception | HTTP | reason |
|-----------|------|--------|
| `LoadError` | 404 | Phase 90 unchanged |
| `ExtractError` | 502 | Phase 90 unchanged |
| `ComposeError` | 400 | Phase 90 unchanged |
| `GenerateError(retryable=True)` | 502 | Phase 96 unchanged |
| `GenerateError(retryable=False)` | 422 (i2i) / 400 (other 4xx) | Phase 96 + 97 unchanged |
| `StoreError` | 500 | Phase 90 unchanged |
| `UnknownModelError` | 422 | Phase 100 unchanged |
| **`ProviderExhaustedError`** | **502** | **NEW Phase 101** |
| `UnknownProviderError` | 500 (uncaught) | Phase 96 unchanged |

`ProviderExhaustedError.detail.attempts` exposes the full attempt list to
frontend for user-visible error reporting ("tried 3 providers, all failed:
openai 502, stability timeout, minimax rate-limited").

### Settings resilience

- `fallback_chain: []` default → no fallback (Phase 100 behavior preserved).
- Malformed YAML → silent fallback to defaults (Phase 100 same).
- Chain contains invalid provider names → `dispatch_with_fallback` skips with
  WARNING log; if all invalid, behaves as primary-only.
- Empty chain in settings + empty body.fallback_chain → single-provider call
  (no overhead, no behavior change from Phase 100).

### Concurrency

No shared state in fallback dispatch (each call loads its own settings).
JSONL append-only audit (best-effort, OSError swallowed per I090). No
locking required.

## Testing strategy

See "Test Plan" section below for full enumeration.

### Test layers

- **A. fallback.py unit tests** (`tests/test_fallback.py`): dispatch logic in
  isolation, mocked adapters, ~16 tests.
- **B. pipeline integration tests** (`tests/test_pipeline.py`): fallback
  integration with mocked adapters, attempts in audit, ~9 tests.
- **C. route integration tests** (`apps/studio_api/tests/test_illustrations_api.py`):
  request schemas, HTTP mapping, settings round-trip, ~9 tests.
- **D. frontend vitest** (`tests/unit/ProjectSettingsIllustration.spec.ts`):
  fallback_chain picker, ~4 tests.

### Regression guards

`tests/test_phase101_atomic_provider_fallback.py`:
- G1: settings.yaml new field default = []
- G2: GenerateRequest has fallback_chain optional field
- G3: pipeline.generate_illustration calls dispatch_with_fallback (regex signature)
- G4: pipeline.regenerate_illustration calls dispatch_with_fallback (regex signature)
- G5: ProviderExhaustedError class exists in fallback module
- G6: audit_log.record_event receives attempts in extra (grep pipeline audit callsite)
- G7: I093 NEW invariant in architecture.yml
- G8: Phase 100 G1-G9 all preserved (no regression)
- G9: i2i path does not call dispatch_with_fallback (regex grep)
- G10: route maps ProviderExhaustedError → 502 (STAGE_HTTP_CODES)

## Invariants

- **I093 NEW**: `packages/lingwen-illustrations/src/lingwen_illustrations/fallback.py:dispatch_with_fallback` is the
  only entry point for cross-provider fallback iteration. `pipeline.generate_illustration` and
  `pipeline.regenerate_illustration` text-only paths call this helper; i2i paths
  bypass it. `infra.fallback.*` and `infra.image_provider.*` paths are illegal.

## Migration / back-compat

- Phase 100 settings.yaml files (without `fallback_chain`) load successfully
  via Pydantic v2 default fill.
- API requests without `fallback_chain` field (old clients) work identically
  to Phase 100 (no fallback).
- Audit events from Phase 98-100 (`generation` / `regeneration` without
  `attempts` extra key) coexist with new events; frontend ignores unknown
  extra fields.

## Open questions

None — all design questions resolved during brainstorming.

## References

- Phase 96 handoff: `docs/superpowers/handoffs/2026-09-17-phase-96-image-provider-adapters-handoff.md`
- Phase 97 handoff: `docs/superpowers/handoffs/2026-09-18-phase-97-reference-image-i2i-handoff.md`
- Phase 100 handoff: `docs/superpowers/handoffs/2026-09-18-phase-100-multi-model-handoff.md`
- Phase 90 spec: `docs/superpowers/specs/2026-09-15-phase-90-illustrations-design.md`

## Test Plan

### A. `tests/test_fallback.py` (~16 tests)

```
test_attempt_dataclass_round_trip
test_dispatch_single_provider_success_no_fallback
test_dispatch_primary_success_ignores_chain
test_dispatch_primary_retryable_triggers_next
test_dispatch_fallback_retryable_triggers_next
test_dispatch_non_retryable_does_not_fallback
test_dispatch_unknown_provider_does_not_fallback
test_dispatch_unknown_model_does_not_fallback
test_dispatch_all_exhausted_raises_provider_exhausted
test_dispatch_chain_skips_unknown_provider
test_dispatch_chain_dedupes_preserving_order
test_dispatch_resolves_model_per_provider
test_dispatch_i2i_path_skips_fallback
test_dispatch_collects_attempts_with_timestamps
test_attempt_last_entry_is_success
test_provider_exhausted_carries_attempts_in_message
test_provider_exhausted_retryable_false
```

### B. `tests/test_pipeline.py` extensions (~9 tests)

```
test_generate_fallback_records_attempts_in_audit
test_generate_fallback_success_meta_provider_is_successful
test_generate_no_fallback_settings_chain_empty
test_generate_all_providers_exhausted_returns_502
test_generate_i2i_does_not_fallback
test_regenerate_fallback_chain_uses_existing_provider
test_regenerate_fallback_preserves_asset_id
test_fallback_first_attempt_is_primary
test_fallback_attempts_include_error_class
```

### C. `apps/studio_api/tests/test_illustrations_api.py` extensions (~9 tests)

```
test_generate_request_accepts_fallback_chain
test_generate_request_fallback_chain_overrides_settings
test_generate_response_includes_attempts_on_502
test_generate_response_no_fallback_field_on_success
test_regenerate_request_accepts_fallback_chain
test_settings_yaml_loads_fallback_chain_field
test_settings_yaml_missing_field_defaults_empty_list
test_settings_pydantic_validates_fallback_chain_strings
test_provider_models_endpoint_unaffected
```

### D. `tests/unit/ProjectSettingsIllustration.spec.ts` extensions (~4 tests)

```
test_fallback_chain_multi_select_renders
test_fallback_chain_persists_to_yaml
test_fallback_chain_loads_from_settings
test_fallback_chain_empty_hides_help_text
```

### E. `tests/test_phase101_atomic_provider_fallback.py` (G1-G10)

See "Regression guards" above.

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Latency: chain of 3 providers × 60s timeout = 3 min worst case | Document in route layer; settings UI warns when chain > 2 providers; future v2 may add global timeout |
| Cost: failed attempts may still incur billing on some providers | Phase 101 makes no attempt to track per-provider cost; documented as future work |
| Audit log bloat: attempts array in every event | Bounded by chain length × 1 (typically 1-3); no special handling needed |
| Settings change during generation | Per-call settings load; no caching; behavior consistent |
| Tests flake due to async timing | Use explicit `await` + small fixed mocks; no real network |

## Lessons applied from prior phases

- **Phase 91 (bible_loader)**: small focused module with public API + comprehensive
  tests. Phase 101 follows same pattern: single-purpose module, public symbols
  with clear contracts.
- **Phase 96 (image provider adapters)**: registry-based dispatch + dynamic
  importlib lookup. Phase 101 reuses `get_provider(name)` adapter pattern.
- **Phase 97 (reference image i2i)**: explicit `retryable=False` on i2i errors
  to prevent auto-fallback. Phase 101 honors this contract: any
  `retryable=False` propagates without trying fallback.
- **Phase 100 (multi-model)**: `resolve_model` 3-tier order per provider.
  Phase 101 calls `resolve_model` independently per provider in chain.
- **Phase 98 (LRU + audit)**: best-effort audit logging. Phase 101 preserves
  pattern — no audit on exception path.
- **Phase 99 (notification center)**: same ULID for audit + SSE. Phase 101
  preserves single-event semantics; ULID flow unchanged.
