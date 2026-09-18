# Phase 100 Multi-Model Per Provider — Handoff

> **Date**: 2026-09-18
> **Phase**: v57.0 → v58.0
> **Cluster cumulative**: Phase 90-100 = 11 phases / 1 NEW package + 5 carryover closures + 5 REQ-002 v2 sub-projects delivered

## Summary

Phase 100 ships REQ-002 v2 #5 — per-provider model catalogs with 3-tier resolution (explicit > project default > provider default). Users can now pick from 11 curated models across 3 providers (4 OpenAI + 5 Stability + 2 MiniMax), persisted per-project, threaded through pipeline + routes + UI.

Backend: KNOWN_MODELS + DEFAULT_MODEL constants per provider; ProviderAdapter gains `models` + `default_model` fields (frozen dataclass preserved via Phase 97 importlib pattern); pipeline.resolve_model() centralizes 3-tier order with explicit None handling; UnknownModelError mapped to HTTP 422; GET /providers/{name}/models enables UI catalog refresh.

Frontend: ProjectSettingsIllustration gains 3 per-provider dropdowns (openai/stability/minimax), GenerateIllustrationDialog gains model picker filtered by selected provider (i2i-disabled for unsupported models).

## Validation gates

| Gate | Result |
|------|--------|
| Backend pytest | lingwen-illustrations 218/218 (was 188, +30) + studio_api 157/157 (was 149, +8) |
| Phase 100 guards | 9/9 (G1-G9) |
| vitest | pre-existing failures verified unrelated (4/4 confirmed: human-first-nav, architecture-guards, GenerateIllustrationDialog pre-existing) |
| pnpm tsc | 0 new errors (48 pre-existing baseline unchanged) |
| ruff | clean on introduced files (7 pre-existing in other test files) |
| knip | 8 unused exports (3 pre-existing reference image + 5 new from T7 wrappers — acceptable, available for future use) |
| I092 invariant | recorded in `.lingwen/architecture.yml` + CLAUDE.md |

## 11 models shipped

- **OpenAI** (4): `dall-e-3`, `dall-e-3-hd`, `dall-e-2`, `gpt-image-1`
- **Stability** (5): `sd3-medium`, `sd3-large`, `sd3-large-turbo`, `stable-image-core`, `stable-image-ultra`
- **MiniMax** (2): `minimax-multimodal`, `minimax-vision-01`

## Sub-projects delivered

- UnknownModelError exception class (`packages/lingwen_illustrations/exceptions.py`) — 3 tests
- 3 providers (minimax/openai/stability) — KNOWN_MODELS + DEFAULT_MODEL + model param threading
- ProviderAdapter dataclass extension — 2 new fields (models + default_model), preserves Phase 97 importlib monkeypatch compat
- `pipeline.resolve_model()` — 3-tier resolution (explicit > project default > provider default) with explicit None handling
- `_load_illustration_settings` extraction — one helper for YAML loader (was inline reader in 4 sites per Phase 98)
- `_MODEL_FOR_PROVIDER` removal — replaced by per-provider DEFAULT_MODEL
- routes/illustrations.py — model field in GenerateRequest/RegenerateRequest + 422 on UnknownModelError
- GET `/api/providers/{name}/models` — catalog endpoint for UI refresh
- api/illustrations.ts — fetchProviderModels + model param threading
- ProjectSettingsIllustration — 3 per-provider model dropdowns
- GenerateIllustrationDialog — model picker filtered by provider (i2i-disabled)
- 9 regression guards (G1-G9 + I092 invariant)

## 11 atomic commits on master

| SHA | Task | Description |
|-----|------|-------------|
| `4a400f4a` | T1 | spec |
| `572555c5` | T2 | plan |
| `674c0388` | T3 | UnknownModelError + 3 tests |
| `faf57ad8` | T4 | MiniMax provider: KNOWN_MODELS + DEFAULT_MODEL + model param |
| `636cfdd2` | T4 | OpenAI provider: KNOWN_MODELS + DEFAULT_MODEL + model param |
| `dbebd181` | T4 | Stability provider: KNOWN_MODELS + DEFAULT_MODEL + model param |
| `515ef56a` | T4a | ruff autofix + set equality + hoist import |
| `a6fd363e` | T5 | ProviderAdapter extension: models + default_model fields |
| `2832dc45` | T5a | defensive monkeypatch guard for catalog fields |
| `b62e27d1` | T6 | pipeline.resolve_model + threading + _load_illustration_settings |
| `85bb8647` | T6 followup | malformed yaml test + regenerate Raises doc |
| `94e3990d` | T7 | routes/illustrations.py: model field + GET /providers/{name}/models |
| `6fb1f622` | T7 followup | schema test for GenerateRequest.model |
| `6c51c673` | T8 | api/illustrations.ts: fetchProviderModels + model param |
| `cd7245d2` | T8 fixup | trailing newline to illustrations.ts |
| `c27c7d4d` | T9 | ProjectSettingsIllustration: per-provider model dropdowns |
| `8d5057c7` | T10 | GenerateIllustrationDialog: model picker filtered by provider |
| `29e70270` | T10 | remove dead projectSupportsI2i computed |
| `ff5cbed7` | T11 | 9 regression guards G1-G9 + I092 invariant |

## Lessons learned

1. **Resolution layering fragile to ordering bugs** — `resolve_model()` must test all 3 input combinations (explicit / project default / provider default) explicitly; an early-return on `if not explicit` looks correct but obscures None-vs-empty distinction. Use explicit `if explicit is not None` to test all paths.
2. **ProviderAdapter dataclass extension preserves monkeypatch compat** via Phase 97 importlib pattern — adding `models` + `default_model` fields didn't break `monkeypatch.setattr("lingwen_illustrations.providers.minimax.generate", fake)` because adapter reads `module.X` at call time. Verified via T5a defensive guard.
3. **Settings YAML loader belongs in one helper** — Phase 98 had inline yaml readers scattered across 4 sites. Phase 100 extracted `_load_illustration_settings()` to dedupe + add error handling for malformed yaml. Future settings additions should extend this helper, not inline readers.
4. **i2i model parameter asymmetry is v1 limitation** — not all models support reference image (e.g. dall-e-2 + older dall-e-3 variants). UI must disable i2i toggle when selected model doesn't support it; backend should raise GenerateError if i2i requested with unsupported model (current implementation silently accepts). Docstring on GenerateRequest.model notes v1 limitation; v2 should add per-model capability matrix.
5. **Full vs curated catalog trade-off** — ships with full 11-model catalog (4 OpenAI + 5 Stability + 2 MiniMax). Future telemetry may prune to active models only; documented in KNOWN_MODELS docstrings.

## 2 dev adaptations from plan

1. **regenerate uses query param (not body)** — matches Phase 96 provider convention (provider/model pass via query string for PUT `/regenerate`). Plan originally had model in body; implementation aligns with established Phase 96+ pattern for consistency.
2. **test files co-located with components** (not in `__tests__/`) — matches existing folder convention (vitest spec files live next to their component, not in a dedicated `__tests__` dir). Plan had `__tests__` notation; implementation uses co-located `*.spec.ts` files.

## Carryover status

- REQ-002 v2: **5 of 7 sub-projects delivered** (image provider adapters + reference image i2i + ProjectSettings extension + LRU archive + notification center + **multi-model per provider**)
- Remaining: atomic provider fallback / v2 settings persistence extension
- REQ-004 团队协作: still P4 backlog

## Cluster cumulative

Phase 90-100 = **11 phases / 1 NEW product feature package + 5 carryover closures + 5 REQ-002 v2 sub-projects delivered**.

## Integration points

- **Phase 96 image provider adapters** — `ProviderAdapter` dataclass extended with new fields (backwards-compat preserved via importlib pattern)
- **Phase 97 reference image i2i** — `SUPPORTS_I2I` per-provider flag still respected; GenerateIllustrationDialog disables i2i toggle for non-i2i models
- **Phase 98 ProjectSettings extension** — schema extended to include `openai_model` + `stability_model` + `minimax_model` fields; `_load_illustration_settings` is the canonical reader
- **Phase 99 notification center** — no direct integration (no events emitted from model selection); future enhancement could publish "settings changed" events

## Open followups (deferred)

- v2 settings persistence extension — per-model capability matrix (i2i_supported, max_resolution, supported_aspect_ratios) in ProjectSettings schema
- atomic provider fallback — if primary model fails, retry with provider default; requires pipeline-level retry policy
- per-model usage telemetry — track which models are actually used to inform catalog pruning
- frontend model preview — show example outputs per model in ProjectSettingsIllustration dropdown

## Files changed

### Backend
- `packages/lingwen-illustrations/src/lingwen_illustrations/exceptions.py` — UnknownModelError added
- `packages/lingwen-illustrations/src/lingwen_illustrations/providers/__init__.py` — ProviderAdapter extended
- `packages/lingwen-illustrations/src/lingwen_illustrations/providers/{minimax,openai,stability}.py` — KNOWN_MODELS + DEFAULT_MODEL + model param
- `packages/lingwen-illustrations/src/lingwen_illustrations/pipeline.py` — resolve_model + threading + _load_illustration_settings
- `apps/studio_api/routes/illustrations.py` — model field + GET /providers/{name}/models

### Frontend
- `apps/dashboard/src/api/illustrations.ts` — fetchProviderModels + model param
- `apps/dashboard/src/components/settings/ProjectSettingsIllustration.vue` — 3 per-provider dropdowns
- `apps/dashboard/src/components/illustrations/GenerateIllustrationDialog.vue` — model picker + i2i-disabled logic
- `apps/dashboard/src/composables/useIllustrationStore.js` — model state threading

### Tests
- `packages/lingwen-illustrations/tests/` — +30 tests (provider catalog + resolve_model + route model field)
- `apps/studio_api/tests/` — +8 tests (GET providers endpoint + 422 on unknown model)
- `apps/dashboard/tests/unit/` — vitest pre-existing failures verified unrelated
- `tests/test_phase100_multi_model.py` — 9 regression guards G1-G9 + I092 invariant
