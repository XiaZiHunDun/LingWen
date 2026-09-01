# Phase 18 — Business Boundary + Interface Cleanup Design

## Context

Phase 18 was originally planned on 2026-08-14 with 16 tasks focused on:
- Freezing Ports interfaces (Protocol classes)
- Domain entity extraction to `packages/lingwen-core/domain/`
- Use-cases events
- studio_api thin shell
- Cleanup of `infra/agent_system/`, `infra/consistency/`, `infra/memory_system/`, `infra/prompt_engineering/`, `infra/state/`, `infra/world_model/`

Between the plan's creation (Aug 14) and now (Sep 1), **Phase 126 v16.0-v16.5 #N.17** was completed, which substantially executed many Phase 18 deliverables:

| Task | Original plan | Current state (verified 2026-09-01) |
|------|----------------|-------------------------------------|
| 18.0 Freeze Ports | NEW `packages/lingwen-core/src/lingwen_core/ports/` | ✅ DONE — `checker.py` (29 lines) + `llm.py` (56 lines) + `storage.py` (85 lines) with `Protocol` classes + mock impls |
| 18.1 Domain entities | NEW `packages/lingwen-core/src/lingwen_core/domain/` | ✅ DONE — `chapter.py` (73) + `character.py` (43) + `common.py` (118) + `foreshadow.py` (60) + `ripple.py` (188) + `volume.py` (43). All entities + domain events defined. |
| 18.2 Use-cases | NEW `packages/lingwen-core/src/lingwen_core/use_cases/` | ✅ DONE — `merge_ripples.py` + `review_chapter.py` + `write_chapter.py` |
| 18.4 `infra/agent_system/` | DELETE | ⚠ PARTIAL — 4 files remain (`__init__.py` + `reviewer.py`) |
| 18.5 `infra/consistency/` | DELETE | ⚠ PARTIAL — 14 files remain (checkers + creative_whitelist) |
| 18.6 `infra/memory_system/` etc | DELETE | ✅ DONE — all 3 dirs gone |
| 18.7 `infra/world_model/` | Fix stale imports + DELETE | ⚠ PARTIAL — 13 files remain, 52 imports from external consumers |
| 18.8 `infra/__init__.py` | Clean up 178 lines | ✅ DONE — 23 lines (was 178) |
| 18.9 `dashboard/frontend/` shadow | DELETE | ✅ DONE — gone (was already cleaned up by Phase 17) |
| 18.10 Stale imports scan | Fix all `from infra.*` | ⚠ PARTIAL — many remain |
| 18.12-18.14 Gates | Pass + merge | ⏳ PENDING — Phase 18 was never formally closed |

## Phase 18 Remaining Work (4 sub-phases)

### Sub1: `infra/world_model/` migration

13 files in `infra/world_model/` are consumed by 10+ external files via 52 import statements. The canonical replacement is `packages/lingwen-core/domain/` (Ripple + RippleState + NodeId + NodeType already defined there).

**Files to migrate**:
- `infra/subplot/data_structures.py` (1 import)
- `infra/poc/run_volume_1.py` (multi-line import)
- `tests/consistency/checkers/test_pacing_ripple_integration.py` (2 imports)
- `tests/consistency/checkers/test_foreshadow_ripple_alignment.py` (3 imports)
- `tests/subplot/test_subplot_data_structures.py` (1 import)
- `tests/subplot/test_subplot_integration.py` (1 import)
- `tests/world_model/test_snapshot_store.py` (2 imports)
- `tests/world_model/test_ripple_engine.py` (2 imports)
- `tests/world_model/test_ripple_queries.py` (2 imports)

**Migration targets**:
- `infra.world_model.NodeId` → `lingwen_core.domain.common.NodeId`
- `infra.world_model.NodeType` → `lingwen_core.domain.common.NodeType`
- `infra.world_model.data_structures.Ripple` → `lingwen_core.domain.ripple.Ripple`
- `infra.world_model.data_structures.RippleState` → `lingwen_core.domain.ripple.RippleState`
- `infra.world_model.registry.RippleRegistry` → keep in `infra/world_model/` (concrete implementation, not domain entity) OR move to `packages/lingwen-core/use_cases/`
- `infra.world_model.engine.RippleEngine` → keep in `infra/world_model/` (concrete engine)
- `infra.world_model.snapshot_store.*` → keep in `infra/world_model/` (storage adapter, concrete)

**Post-migration**: `infra/world_model/` stays as the implementation home, just no longer exports domain types.

### Sub2: `infra/consistency/` migration

Tests still import from `infra/consistency.checkers.*` and `infra.consistency.creative_whitelist`. The canonical home is `packages/lingwen-quality.consistency.checkers.*` (per v15.7.1 Phase 125 work which verified `lingwen_quality` symbols are importable).

**Files to migrate**:
- `scripts/ci_baseline_check.py` (1 import: `infra.consistency.checker_feedback.get_checker_stats`)
- `tests/consistency/test_creative_whitelist.py` (1 import: `infra.consistency.creative_whitelist`)
- `tests/consistency/test_pacing_checker.py` (1 import: `infra.consistency.checkers.pacing_checker.PacingChecker`)
- `tests/consistency/test_character_agency.py` (1 import: `infra.consistency.checkers.character_agency`)
- `tests/consistency/test_core_props_checker.py` (1 import)
- `tests/consistency/test_item_checker.py` (1 import)

**Migration targets**: `packages/lingwen-quality.consistency.checkers.*` + `packages/lingwen-quality.consistency.creative_whitelist`

**Verify**: `tooling/hygiene/check_lingven_quality_importable.py` (v16.5 #N.16 CI guard) confirms canonical paths importable.

### Sub3: `infra/agent_system/` migration

`infra/agent_system/reviewer.py` is consumed by 1 external file + 1 test.

**Files to migrate**:
- `packages/lingwen-core/src/lingwen_core/agents/agents/reviewer.py` (uses `from infra.consistency.*` and `from infra.agent_system.*`)
- `tests/agent_system/test_reviewer.py` (1 test)

**Migration target**: `packages/lingwen-quality.consistency.*` for the consistency imports; `infra/agent_system/__init__.py` re-exports or shim.

**Post-migration**: delete `infra/agent_system/` if empty.

### Sub4: 17 TODO(Phase18) markers + doc updates

The 17 TODO(Phase18) comments reference `packages/lingwen-domain` which doesn't exist. The actual canonical location is `packages/lingwen-core/domain/` (already exists). The TODOs can be removed once migrations done — they were workarounds waiting for Phase 18 closure.

**TODO locations**:
- `packages/lingwen-quality/src/lingwen_quality/consistency/checkers/foreshadow_checker_types.py:18`
- `packages/lingwen-quality/src/lingwen_quality/consistency/checkers/pacing_checker.py:21,25`
- `packages/lingwen-cli/src/lingwen_cli/commands/{ripple_rollback,ripple_reset,cascade,ripple_audit,ripple_scan}.py` (7 TODOs)
- `packages/lingwen-core/src/lingwen_core/agents/{chapter_memory_hook,chapter_production_pilot,production_summary,context_helpers,context_builder}.py` (7 TODOs)
- `packages/lingwen-core/src/lingwen_core/agents/internal/incremental_backfill.py:1`
- `infra/exports/events.py:2` (separate concern — `lingwen-storage`)
- `infra/exports/__init__.py:2` (separate concern)

### Sub5: Doc sync (architecture.yml + handoff)

- `.lingwen/architecture.yml`:
  - `version` field: `"16.5.N7"` → `"16.5.N17+18"`
  - DP-02 + DP-03 `enforcement_phase` add v16.5 #N.0-#N.17 markers + Phase 18 closure
  - Add `domain` module_boundary (already present)
  - Add `ports` module_boundary (already present)
- `docs/superpowers/handoffs/2026-09-01-phase-18-business-boundary-cleanup-handoff.md` (NEW)

## Out of Scope (NOT in Phase 18 closure)

- **`infra/exports/*`** → `packages/lingwen-storage` migration (separate concern, 2 TODO markers, future work)
- **studio_api thin shell** (Phase 18.3) — separate refactor, not blocking closure of Sub1-Sub5
- **Use-cases events** (Phase 18.2) — already done

## Goals

1. Migrate 17 external files from `infra/world_model.*` + `infra/consistency.*` + `infra/agent_system.*` to canonical packages
2. Remove 17 TODO(Phase18) markers (Sub1-Sub3 will resolve most; remaining are doc-time references)
3. Update `.lingwen/architecture.yml` to reflect Phase 18 completion
4. Produce Phase 18 handoff doc
5. All CI gates green: pytest / knip / vue-tsc / ESLint / ruff / import-linter 3 contracts

## Non-Goals

- **NOT** deleting `infra/world_model/` entirely — it contains concrete engine + storage adapter implementations
- **NOT** deleting `infra/consistency/` entirely — it contains checkers that haven't been migrated yet (out of scope)
- **NOT** migrating `infra/exports/*` → `packages/lingwen-storage` (separate concern, different phase)
- **NOT** touching studio_api routes (Phase 18.3 is separate refactor)
- **NOT** adding new domain entities or ports — only migrating imports

## Verification Before Migration

### Sub1 — Domain entity availability

```bash
grep -rn "class Ripple\b\|class RippleState\b\|class NodeId\b\|class NodeType\b" \
  packages/lingwen-core/src/lingwen_core/domain/ --include="*.py"
```

Expected: all 4 entities present in `packages/lingwen-core/domain/{ripple,common}.py`.

### Sub2 — Quality consistency checker availability

```bash
python tooling/hygiene/check_lingwen_quality_importable.py
```

Expected: exits 0 with all key symbols importable from `packages/lingwen-quality.consistency.checkers.*` and `creative_whitelist`.

### Sub3 — Agent reviewer consumer analysis

```bash
grep -rn "infra.agent_system" --include="*.py" 2>/dev/null | grep -v __pycache__
```

Expected: only 2 consumers (`lingwen-core/.../agents/agents/reviewer.py` + `tests/agent_system/test_reviewer.py`).

## Implementation Plan (atomic commits)

| Commit | Sub | Description | Files |
|---|---|---|---|
| T1 | Sub1 | Migrate `infra/world_model.{NodeId,NodeType}` → `lingwen_core.domain.common` | 5 test files |
| T2 | Sub1 | Migrate `infra/world_model.data_structures.{Ripple,RippleState}` → `lingwen_core.domain.ripple` | 4 test files |
| T3 | Sub1 | Migrate `infra/subplot` + `infra/poc` consumers | 2 infra files |
| T4 | Sub2 | Migrate `infra/consistency.checkers.*` → `packages/lingwen-quality.consistency.checkers.*` | 5 test files |
| T5 | Sub2 | Migrate `infra/consistency.creative_whitelist` + `checker_feedback` | 2 test/script files |
| T6 | Sub3 | Migrate `infra/agent_system` consumer in `lingwen-core/agents/agents/reviewer.py` | 2 files |
| T7 | Sub4 | Remove 14 TODO(Phase18) markers (now resolved) | 8 files |
| T8 | Sub5 | Update `.lingwen/architecture.yml` version + DP enforcement_phase + add new module_boundaries | 1 file |
| T9 | Sub5 | Write Phase 18 handoff doc | 1 new file |
| T10 | Sub5 | Update CLAUDE.md + add v18 entry | 1 file |

**Estimated total**: 10 commits (atomic 1-task-per-commit).

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| `Ripple`/`RippleState` API differs between `infra/world_model` and `lingwen_core.domain` | Medium | Compare dataclass fields before/after migration; tests should catch |
| `RippleRegistry` API differs | Low | Keep `infra/world_model/registry.py` for now (concrete impl) |
| Missing re-export from `lingwen_core.domain` | Low | Already defined in `__init__.py` per audit |
| Tests break (consistency/quality tests) | Medium | `pytest packages/lingwen-quality/tests/` + `pytest tests/consistency/` must pass |
| `infra/agent_system/__init__.py` re-exports break | Low | Check who imports what before delete |

## Carryover to Phase 19+

After Phase 18 closure:
- `infra/world_model/` may still have concrete engine/storage (NOT deleted)
- `infra/consistency/` may still have some un-migrated checkers (out of scope)
- `infra/exports/*` → `packages/lingwen-storage` migration (separate phase)
- Phase 114 prod preview regression (still accepted)
- New feature work (would require brainstorming)