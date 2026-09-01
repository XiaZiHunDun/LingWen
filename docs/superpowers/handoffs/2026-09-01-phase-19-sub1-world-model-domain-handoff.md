# Phase 19+ Sub1 — World Model Domain Migration Handoff

## Summary

Phase 19+ Sub1 closed: WorldSnapshot + Plot + Ripple + RippleState + ResolutionMode + KeyPoint + NodeId + NodeType + Relation + PhysicalLine + MentalLine + PlotStatus fully migrated to `packages/lingwen-core/domain/`. `infra/world_model/data_structures.py` and `infra/subplot/data_structures.py` are now 1-line PHASE-COMPAT shims. `infra/world_model/__init__.py` is a canonical re-export module. 10+ test files migrated from `infra.world_model` / `infra.subplot` to `lingwen_core.domain`. 5 previously-blocked `tests/subplot/test_subplot_integration.py` tests now pass via canonical route.

**33 source commits** on branch `phase-19-sub1` (2 docs + 31 implementation commits).

### Commits

```
d3da0d27 docs(phase-19-sub1): design spec — world model domain migration
0a83a6fb docs(phase-19-sub1): implementation plan
c3fa3b78 feat(lingwen-core): WorldSnapshot.to_dict/from_dict
77691e2e fix(lingwen-core): WorldSnapshot serialization cleanup
34f5fc2e feat(lingwen-core): WorldSnapshot.physical/mental fields
79b86eb8 feat(lingwen-core): WorldSnapshot.active_subplots field
fad93170 feat(lingwen-core): subplot module + Plot entity
66dfc438 refactor(infra): subplot.data_structures shim + NodeId canonical alignment
cc502074 refactor(lingwen-core): tighten active_subplots to tuple[Plot, ...]
338c79e8 test(lingwen-core): WorldSnapshot serialization + field defaults
dac74be3 fix(lingwen-core): WorldSnapshot.from_dict loads active_subplots
ea0eb87c refactor(infra): split subplot helpers to infra.subplot.helpers
d23e544c refactor(tests): subplot_integration migrate to lingwen_core.domain
3f5dc750 style(infra): fix ruff I001 + update stale docstring
35ada25e refactor(tests): subplot_data_structures migrate to lingwen_core.domain
6ff65d6c refactor(tests): foreshadow_ripple_alignment migrate Ripple to domain
b78ecbf1 refactor(tests): pacing_ripple_integration migrate domain entities
1e253fed refactor(tests): test_world_snapshot migrate domain entities
79e0d2a1 style(tests): fix ruff I001 in test_world_snapshot
059ba823 refactor(tests): test_integration migrate domain entities
43baa63d refactor(tests): test_phase2_integration migrate domain entities
c0c77e44 refactor(tests): test_snapshot_diff migrate domain entities
311a8f9f refactor(tests): test_snapshot_store migrate domain entities
b48da8bd refactor(tests): test_key_point_graph migrate domain entities
acc9f6ab refactor(tests): test_ripple_queries migrate domain entities
9368aec4 refactor(tests): test_ripple_engine migrate domain entities
2bc4b565 refactor(tests): test_ripple_registry migrate domain entities
633235ca refactor(tests): test_ripple_lifecycle migrate domain entities
51da7278 refactor(tests): test_links migrate domain entities
41080393 fix(infra): canonicalize Ripple/RippleState/ResolutionMode
e21c9d88 refactor(infra): world_model.data_structures shim
e3ccc9be refactor(infra): world_model __init__ canonical re-exports
fe2fa219 fix(infra): canonicalize PlotStatus
```

## What Phase 19+ Sub1 Did

### T1 — WorldSnapshot.to_dict/from_dict (`c3fa3b78`)
Added `to_dict()` / `from_dict()` methods on `lingwen_core.domain.ripple.WorldSnapshot`. Closes Phase 18 Finding B (DDD purity concern about persistence methods on domain entity — pragmatic compromise: kept on domain for test bridgeability, with separate adapter possible later).

### T2 — WorldSnapshot serialization cleanup (`77691e2e`)
Refined T1 implementation: cleared stale docstring references, normalized JSON field ordering.

### T3 — physical/mental fields (`34f5fc2e`)
Added `physical: tuple[PhysicalLine, ...]` and `mental: tuple[MentalLine, ...]` fields to `WorldSnapshot` (also introduced `PhysicalLine` and `MentalLine` entity types in `lingwen_core.domain.chapter`). **Required `infra/persistence/chapter.py` prerequisite** — the persistence layer emits these tuples; domain needed matching fields.

### T4 — WorldSnapshot.active_subplots field (`79b86eb8`)
Added `active_subplots: tuple[Plot, ...]` field. Closes Phase 18 Finding B residual.

### T5 — subplot module + Plot entity (`fad93170`)
NEW `lingwen_core.domain.subplot` module with `Plot` entity + `PlotType` + `PlotPurpose` + `PlotStatus` + `MAX_ACTIVE_SUBPLOTS`. Plot is the bounded-context aggregate root for subplot tracking.

### T6 — infra/subplot.data_structures shim + NodeId canonical alignment (`66dfc438`)
Converted `infra/subplot/data_structures.py` into 1-line PHASE-COMPAT shim re-exporting from canonical. NodeId canonicalization: the entity was duplicated in both `infra.subplot` and `infra.world_model` paths; resolved to single canonical home.

### T7 — tighten active_subplots to tuple[Plot, ...] (`cc502074`)
Tightened type annotation from `list[Plot]` to `tuple[Plot, ...]` for immutability semantics consistent with other field types on WorldSnapshot.

### T8 — WorldSnapshot serialization + field defaults test (`338c79e8`)
7 NEW tests covering to_dict/from_dict round-trip, active_subplots default empty, physical/mental defaults, MAX_ACTIVE_SUBPLOTS invariant.

### T9 — WorldSnapshot.from_dict loads active_subplots (`dac74be3`)
Spec review caught missing `active_subplots` loading in `from_dict()`. 1-line fix.

### T10 — split subplot helpers to infra.subplot.helpers (`ea0eb87c`)
Internal refactor to split `subplot/data_structures.py` into pure shim + helpers module. No behavior change.

### T11 — test_subplot_integration migration (`d23e544c`)
Migrated `tests/subplot/test_subplot_integration.py` from `infra.subplot` to `lingwen_core.domain.subplot` imports. **5 previously-blocked tests now pass via canonical route** — the canonical bridge (`from_dict(to_dict())`) pattern works.

### T12 — ruff I001 fix (`3f5dc750`)
Style: fixed ruff import-sort + stale docstring update.

### T13 — test_subplot_data_structures migration (`35ada25e`)
Migrated `tests/subplot/test_subplot_data_structures.py`.

### T14 — test_foreshadow_ripple_alignment Ripple migration (`6ff65d6c`)
Migrated Ripple-related imports. Spec review caught field count divergence (Ripple had 11 fields on infra side, 12 on domain side with `resolution_mode` added); aligned.

### T15 — test_pacing_ripple_integration migration (`b78ecbf1`)

### T16 — test_world_snapshot migration (`1e253fed`) + ruff I001 (`79e0d2a1`)
Mechanical migration.

### T17 — test_integration migration (`059ba823`)
Migrated `tests/world_model/test_integration.py` with bridge adaptation (legacy `from_dict(to_dict())` calls now use canonical directly).

### T18 — test_phase2_integration migration (`43baa63d`)
Pre-existing fixture path had bridge pattern; removed.

### T19-T20 — test_snapshot_diff + test_snapshot_store migration (`c0c77e44` + `311a8f9f`)
2 snapshot tests migrated. test_snapshot_store needed 2 bridge adapters.

### T21 — test_key_point_graph migration (`b48da8bd`)

### T22-T25 — 4 ripple tests migration (`acc9f6ab` + `9368aec4` + `2bc4b565` + `633235ca`)
test_ripple_queries, test_ripple_engine, test_ripple_registry, test_ripple_lifecycle.

### T26 — test_links migration (`51da7278`)

### T27 — Ripple/RippleState/ResolutionMode canonicalization fix (`41080393`)
Code review caught class identity divergence: domain Ripple added a `resolution_mode` field that wasn't on infra Ripple, breaking `is` identity check used in shim consumers. Resolved by canonicalizing the infra Ripple to re-export from domain.

### T28 — infra/world_model.data_structures shim conversion (`e21c9d88`)
Converted the file to 1-line PHASE-COMPAT shim re-exporting from canonical.

### T29 — infra/world_model/__init__ canonical re-exports (`e3ccc9be`)
Re-export module: `infra/world_model/__init__.py` now re-exports from `lingwen_core.domain.*`. Behavior services that import from `infra.world_model.X` still work transparently.

### T30 — PlotStatus canonicalization (`fe2fa219`)
Code review caught PlotStatus had been left as local definition on infra side. Canonicalized to re-export from `lingwen_core.domain.subplot`.

## Architecture Invariants Established (NEW in this phase)

36. ✅ `lingwen_core.domain.*` is canonical source for WorldSnapshot + Ripple + ResolutionMode + RippleState + Ripple*Event + Plot + PlotType + PlotStatus + PlotPurpose + KeyPoint + NodeId + NodeType + Relation + PhysicalLine + MentalLine + MAX_OPEN_RIPPLOTS

37. ✅ `infra/world_model/data_structures` is a PHASE-COMPAT shim (all domain entities are re-exports from canonical; PlotStatus canonicalized in T30)

38. ✅ `infra/world_model/__init__.py` is a PHASE-COMPAT re-export module (Phase 19.x+ follow-up: behavior services should migrate to use `lingwen_core.domain.*` directly, removing the indirection through `infra.world_model.*`)

39. ✅ `infra/subplot/data_structures.py` is a PHASE-COMPAT shim (Plot + PlotType + PlotPurpose + PlotStatus + MAX_ACTIVE_SUBPLOTS re-exported)

40. ✅ `lingwen_core.domain.*` does NOT depend on `infra.*` (DDD purity preserved throughout all canonical re-exports)

## Verification Gates (Final State)

- `pytest packages/lingwen-core/tests/ tests/subplot/ tests/world_model/ packages/lingwen-creator/tests/ --ignore=tests/world_model/test_phase2_integration.py` → 700+ passed
- `ruff check infra/ packages/ lingwen-shared/tests/ --exclude packages/lingwen-prompt` → 0
- `lint-imports` → 3 contracts KEPT (layer_dependencies + no_concrete_llm_service + no_concrete_sqlite3) + NO new lingwen-core → infra imports
- `cd apps/dashboard && pnpm exec knip` → 0 lines (unchanged)
- `cd apps/dashboard && pnpm vitest run` → 1762 passed + 1 skipped
- `cd apps/dashboard && pnpm tsc --noEmit` / `pnpm eslint .` → 0
- All 11 domain entity identities `True`: KeyPoint / NodeId / NodeType / Relation / PhysicalLine / MentalLine / WorldSnapshot / Ripple / RippleState / ResolutionMode / MAX_OPEN_RIPPLOTS (T27 fix)
- PlotStatus identity: True (T30 fix)

## Carryover to Phase 19.x+ / Sub-Phase 2+

1. **Sub1 behavior services**: behavior services in `infra/world_model/{engine,lifecycle,links,queries,registry,snapshot_diff,snapshot_store,key_point_graph,character_snapshot,foreshadow_snapshot}.py` still internally use `infra.world_model.data_structures` — these should be migrated to import directly from `lingwen_core.domain.*` when convenient, removing the shim indirection.

2. **Sub2**: `infra/consistency/*` PHASE-COMPAT shim cleanup (30+ files). Carryover from Phase 18 v18 handoff.

3. **Sub3**: `infra/agent_system/*` PHASE-COMPAT shim cleanup (similar).

4. **Pre-existing**: `lingwen_llm` module missing in test env (affects `tests/world_model/test_phase2_integration.py` collection). Should be installed once `packages/lingwen-llm` package's `__init__.py` is created.

5. **DDD purity follow-up**: Spec idealized "domain pure, persistence separate" in Phase 18.1 but `to_dict`/`from_dict` exists on domain entities. Future cleanup could extract a persistence adapter layer (lower priority).

6. **Ruff format** (T15 review observation): `ruff format --check` reports reformatting needed in many test files. Pre-existing condition. Defer to dedicated format cleanup commit.

7. **Pre-existing v15.7.1 debt** (`lingwen_quality`, `lingwen_llm`, `lingwen_prompt` missing modules): same as Phase 18 carryover — env-setup gap not introduced here.

8. **Phase 114 prod preview regression**: still accepted (per CLAUDE.md).

## Lessons (Phase 19+ Sub1)

1. **Verify-before-design (N.14 lesson 1 — confirmed in Phase 18)**: carried through Phase 19+. Each sub-phase pre-flight verified state before editing (e.g., T5 verified helper location, T11 verified pre-existing Task 5 prerequisite gap, T28 verified PlotStatus vs canonical divergence).

2. **PHASE-COMPAT shim detection**: tested in T28 review (Issue #2: missing `DELETE after Phase 19.x` text on marker). Convention is single grep-discoverable line.

3. **Class identity divergence pattern**: Ripple (T27), PlotStatus (T30) — the same Phase 18 v18 carryover pattern. Now closed for all 11 entities. Future canonical migrations should follow the re-export pattern (delete local definition, add canonical import).

4. **API divergence in domain migration**: most entities had identical field sets between infra and domain — easy re-export. WorldSnapshot had missing fields/methods (Phase 18 Finding B); Phase 19+ Sub1 filled the gap. Ripple had extra `resolution_mode` on domain side (silent value-equality break); Phase 19+ closed.

5. **Atomic 1-task-per-commit (N.14 lesson 7)**: maintained throughout Phase 19+. 33 commits on `phase-19-sub1` branch (28 source implementation commits + 2 docs + 3 fixup/cleanup commits).

6. **Phase 18 deferred ripple entities problem**: T30 PlotStatus was a hidden carryover — only reviewer caught it. **Lesson**: code review should specifically check for `local_definition vs canonical.re_export` patterns in PHASE-COMPAT shim files.

7. **Continuous review catches latent bugs**: T9 spec review caught missing `from_dict active_subplots` loading. T14 spec review caught Ripple field count divergence (11 vs 12). T28 code review caught PlotStatus shadowing. The 3-stage review process paid dividends.

8. **Mechanical migration scaling**: T11-T26 mechanical migrations (~10 test files across 2 suites) followed established pattern. Each file ~3 dispatches (implementer + spec + code review). 3-stage review was redundant for purely mechanical changes — could be optimized in future phases (single implementer + lightweight review).

## Document Trace

- Phase 18 handoff: `docs/superpowers/handoffs/2026-09-01-phase-18-business-boundary-cleanup-handoff.md`
- Spec: `docs/superpowers/specs/2026-09-01-phase-19-sub1-world-model-domain-design.md`
- Plan: `docs/superpowers/plans/2026-09-01-phase-19-sub1-world-model-domain.md`
- Architecture config: `.lingwen/architecture.yml` (version 19.1)
- CLAUDE.md: updated
- MEMORY.md: updated