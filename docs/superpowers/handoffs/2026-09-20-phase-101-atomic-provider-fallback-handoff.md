# Phase 101 — Atomic Provider Fallback — Handoff

> **Date**: 2026-09-20
> **Phase**: v58.0 → v59.0
> **Cluster**: REQ-002 v2 #6 (sixth sub-project delivered; 1/7 remaining)

## Summary

Phase 101 makes illustration generation resilient to provider outages. When the
primary provider's image API fails with a transient error (5xx, 429, timeout,
network), the pipeline automatically tries the next provider in a configurable
fallback chain. Succeeded metadata records the successful provider; the audit log
captures every attempt (provider, model, error, timestamp) in a single
`generation` event with `extra.attempts`.

Pipeline integration is a focused refactor: text-only paths go through the new
`dispatch_with_fallback` helper; i2i paths are unchanged (provider-specific i2i
models are not interchangeable). The fallback chain is configured per-project
in `illustration_settings.yaml` (or one-off via API request override).

## Validation gates

| Gate | Result |
|------|--------|
| Backend pytest (lingwen-illustrations) | 268/268 PASS (+4 new pipeline integration tests) |
| Backend pytest (studio_api settings) | 15/15 PASS (+4 new fallback_chain tests) |
| Backend pytest (studio_api illustrations) | 33/33 PASS (+5 new fallback_chain + STAGE_HTTP_CODES tests) |
| Backend pytest (fallback module unit) | 14/14 PASS (3 baseline + 11 chain retry/exhaustion/i2i) |
| Backend pytest (Phase 101 regression guards) | 13/13 PASS (G1-G10 + 3 I093 invariant checks) |
| Backend pytest (lingwen-illustrations Phase 100) | 250/250 preserved (no regression) |
| pnpm tsc | 0 new errors (48 pre-existing baseline unchanged) |
| ruff check | clean on introduced files (auto-fixed import sort) |
| Frontend vitest (useProjectSettings) | 12/12 PASS (2 default-equality assertions updated) |
| Frontend vitest (ProjectSettingsIllustration) | 3/3 PASS (no regression) |
| I093 invariant | recorded in `.lingwen/architecture.yml` + CLAUDE.md |

## Sub-projects delivered

- **New module `lingwen_illustrations.fallback`** (T2): `Attempt` frozen
  dataclass + `dispatch_with_fallback` async coroutine + `_dedupe_preserve_order`
  + `_filter_known_providers` helpers. Provider factory parameter
  (`provider_factory`) preserves test patchability.
- **`ProviderExhaustedError`** exception (T1): subclass of `GenerateError`,
  carries `.attempts: list[dict]` for HTTP 502 detail, `retryable=False`
  (terminal failure).
- **Pipeline integration** (T4, T5): `generate_illustration` and
  `regenerate_illustration` text-only paths use `dispatch_with_fallback`; i2i
  paths bypass fallback. Meta records successful provider/model; attempts list
  in audit + notification extras.
- **`ProjectSettings.fallback_chain`** (T6): new optional field on the Pydantic
  model. YAML back-compat via Pydantic v2 default fill (Phase 100/98 pattern).
- **Route layer** (T7, T8): `GenerateRequest.fallback_chain` optional override
  field. `_resolve_provider_for_request` returns `(provider, fallback_chain)`
  tuple. `RegenerateRequest` accepts comma-separated `fallback_chain` query
  param. `STAGE_HTTP_CODES[ProviderExhaustedError] = 502`; `_err_detail` includes
  `attempts` array.
- **Frontend api/illustrations.ts** (T9): `fallback_chain?: string[] | null`
  parameter on both wrappers.
- **`useProjectSettings` store** (T10): default state includes
  `fallback_chain: []`; save/fetch pass-through.
- **ProjectSettingsIllustration.vue** (T11): native multi-select picker +
  hint text. `on_fallback_chain_change` handler extracts and updates.
- **I093 NEW invariant** (T12): recorded in architecture.yml + CLAUDE.md.
  Enforcement: `dispatch_with_fallback` is the only entry point for cross-
  provider fallback iteration; i2i paths bypass it; `Attempt` is the only
  attempt-tracking shape; `ProviderExhaustedError` is the only terminal
  exhaustion exception.
- **13 regression guards** (T12+T13): G1-G10 + 3 invariant validations.

## Commits (14 atomic on master)

| SHA | Task | Description |
|-----|------|-------------|
| `3c92cd92` | T1 | ProviderExhaustedError + 2 tests |
| `8f3ba54c` | T2 | fallback module skeleton + Attempt dataclass + 3 tests |
| `b017aff8` | T2 fixup | Move resolve_model import inside dispatch_with_fallback to avoid cycle |
| `3c7ec954` | T3 | fallback dispatch — chain retry + exhaustion + i2i no-fallback + 11 tests |
| `679798fa` | T4 | pipeline.generate_illustration fallback chain + audit attempts |
| `08d26e0d` | T5 | pipeline.regenerate_illustration fallback chain + audit attempts |
| `c3d481d4` | T6 | ProjectSettings.fallback_chain field + back-compat |
| `363a0b13` | T7 | route layer — GenerateRequest.fallback_chain + resolve tuple |
| `6ad22f03` | T8 | STAGE_HTTP_CODES ProviderExhaustedError → 502 + detail.attempts |
| `435b1011` | T9 | api/illustrations.ts — fallback_chain param threading |
| `cbe7278f` | T10 | useProjectSettings store — fallback_chain field |
| `1d741c97` | T11 | ProjectSettingsIllustration — fallback_chain multi-select picker |
| `a5cb6613` | T12+T13 | 10 regression guards G1-G10 + I093 invariant (13 total) |

## Lessons learned

1. **provider_factory parameter preserves test patching**: When
   `dispatch_with_fallback` was created with a module-level `get_provider`
   binding, tests that patch `pipeline.get_provider` no longer propagated.
   Adding `provider_factory` parameter (caller passes `get_provider` from
   pipeline namespace) made dispatch_with_fallback test-friendly without
   breaking production behavior. Pattern: when a new module has its own
   import binding for a function that callers patch, parameterize the
   dependency explicitly.

2. **Single-provider failure now raises ProviderExhaustedError, not bare
   GenerateError**: Phase 101 changed the semantics of single-provider
   failure — even with no fallback_chain configured, a retryable failure
   now wraps the GenerateError in ProviderExhaustedError. Existing callers
   catch `except IllustrationError` continue to work (ProviderExhaustedError
   IS-A IllustrationError → GenerateError), but tests that asserted
   `with pytest.raises(GenerateError)` needed updates. Document this in
   any downstream code that distinguishes exception types.

3. **body_fallback_chain should override settings even when body_provider is
   None**: One-off override scenario (debugging, testing) should let users
   override the chain without overriding the provider. Initial implementation
   only honored body_fallback_chain when body_provider was set; fix
   generalized the override logic.

4. **i2i path bypass**: Confirmed via regression guard G9 that i2i branches
   never call `dispatch_with_fallback`. Provider-specific i2i models
   (stability SD3 i2i vs openai) are not interchangeable; silent fallback
   would lose the reference image context. Phase 97's i2i pre-flight check
   `if not adapter.supports_i2i: raise GenerateError(retryable=False)`
   remains the correct behavior.

5. **Audit extra schema**: attempts list is serialized via `a.__dict__` (provider
   + model + error + ts) — 4 fields per attempt. If Attempt grows more fields
   later (e.g. latency_ms), consumers will see new fields; back-compat preserved.

6. **Pydantic default-fill preserves yaml back-compat**: Adding
   `fallback_chain: list[str] = []` to ProjectSettings follows the Phase 98/100
   pattern. Old yaml files (without fallback_chain key) load with empty list
   (no fallback) — same observable behavior as Phase 100.

7. **No worktree, no PR**: Per 2026-09-15 simplified workflow, all 14 atomic
   commits went directly to master. 14 commits is the cluster pattern
   (matches Phase 90-100 phase sizes). No friction; ready to push.

## Future work

- **REQ-002 v2 #7 (next)**: v2 settings persistence extension — extend
  ProjectSettings with more illustration-related fields (e.g.
  `fallback_models: dict[provider, model]` for per-provider model mapping,
  per-chapter overrides). Also addresses deferred item from Phase 95.
- **REQ-004 团队协作**: Long-pending P4 brainstorm session. Team collaboration
  features (multi-user editing, conflict resolution, permission grading).
- **Phase 102+ (if any)**: Adaptive learning from past failures (telemetry-
  driven chain reorder) — currently fallback_chain is static.

## Cluster cumulative (Phase 90-101)

12 phases / 1 NEW package (lingwen-illustrations) + 5 carryover closures
(Phase 92-95) + 6 REQ-002 v2 sub-projects delivered (image provider adapters
+ reference image i2i + ProjectSettings extension + LRU archive + notification
center + **multi-model per provider** + **atomic provider fallback**).

**REQ-002 v2 remaining**: 1 of 7 (v2 settings persistence extension).

See `docs/superpowers/specs/2026-09-18-phase-101-atomic-provider-fallback-design.md`
for the design spec and `docs/superpowers/plans/2026-09-18-phase-101-atomic-provider-fallback.md`
for the implementation plan.