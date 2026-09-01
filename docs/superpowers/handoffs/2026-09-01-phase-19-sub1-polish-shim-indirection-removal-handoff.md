# Phase 19+ Sub1 Polish — Shim Indirection Removal Handoff

## Summary

Phase 19+ Sub1 polish closed: behavior services in `infra/world_model/` and
`infra/subplot/` now import domain entities directly from `lingwen_core.domain.*`
instead of via the PHASE-COMPAT shim (`infra.world_model.data_structures.X` and
`infra.subplot.data_structures.X`). 5 test consumer files also migrated.

Closes the `Sub1 polish` carryover from Phase 19+ Sub1 §5 — "infra/world_model
behavior services should import directly from lingwen_core.domain.* to remove
shim indirection."

**11 source commits** on branch `phase-19-sub1-polish` (10 source + 1 docs +
will add handoff/CLAUDE.md/architecture.yml).

### Commits

```
34ad92be refactor(infra): world_model.engine import from lingwen_core.domain
40addbfc refactor(infra): world_model.lifecycle import from lingwen_core.domain
be3f20d1 refactor(infra): world_model.queries import from lingwen_core.domain
e1475df4 refactor(infra): world_model.registry import from lingwen_core.domain
a1a17181 refactor(infra): world_model.snapshot_diff import from lingwen_core.domain
cb78d0ce refactor(infra): subplot.queries import from lingwen_core.domain
9b76e9a2 refactor(infra): subplot.registry import from lingwen_core.domain
4d2b7b43 refactor(infra): subplot.lifecycle import from lingwen_core.domain
40d207ae refactor(test): 5 subplot test consumers import from lingwen_core.domain
0ee0753d refactor(infra): world_model.links import from lingwen_core.domain
150447ea chore(ruff): auto-fix I001 import sort for test files (10 errors → 0)
```

### Per-task scope

**Behavior services migrated (9 files):**

| File | Entities (canonical) | Behavior→behavior imports preserved |
|------|----------------------|--------------------------------------|
| `infra/world_model/engine.py` | `common.NodeId`, `ripple.{ResolutionMode, Ripple, RippleState}` | `infra.world_model.lifecycle.{MAX_OPEN_RIPPLOTS, RESOLUTION_GRACE_CH, can_transition}` |
| `infra/world_model/lifecycle.py` | `ripple.{MAX_OPEN_RIPPLOTS, Ripple, RippleState}` | (no behavior imports) |
| `infra/world_model/queries.py` | `ripple.{Ripple, RippleState}` | `infra.world_model.lifecycle.{MAX_OPEN_RIPPLOTS, RESOLUTION_GRACE_CH}` |
| `infra/world_model/registry.py` | `ripple.{Ripple, RippleState}` | `infra.world_model.lifecycle.MAX_OPEN_RIPPLOTS` |
| `infra/world_model/snapshot_diff.py` | `ripple.WorldSnapshot` | (no behavior imports) |
| `infra/world_model/links.py` | `subset.Plot`, `subset.PlotStatus`, `ripple.Ripple` (TYPE_CHECKING + runtime lazy) | `infra.world_model.registry.RippleRegistry` |
| `infra/subplot/queries.py` | `subset.{MAX_ACTIVE_SUBPLOTS, PlotStatus, PlotType}` | `infra.subplot.registry.PlotRegistry` |
| `infra/subplot/registry.py` | `subset.{MAX_ACTIVE_SUBPLOTS, Plot, PlotPurpose, PlotStatus, PlotType}` | `infra.subplot.lifecycle.{CLOSING_MIN_CHAPTERS, can_transition}` |
| `infra/subplot/lifecycle.py` | `subset.{Plot, PlotStatus}` (removed unused TYPE_CHECKING block) | (no behavior imports) |

**Test consumers migrated (5 files):**

| File | Entities (canonical) |
|------|----------------------|
| `tests/subplot/test_lifecycle.py` | `subset.{Plot, PlotPurpose, PlotStatus, PlotType}` |
| `tests/subplot/test_queries.py` | `subset.{MAX_ACTIVE_SUBPLOTS, Plot, PlotPurpose, PlotStatus, PlotType}` |
| `tests/subplot/test_subplot_integration.py` | `subset.{MAX_ACTIVE_SUBPLOTS, Plot, PlotPurpose, PlotStatus, PlotType}` |
| `tests/subplot/test_subplot_registry.py` | `subset.{MAX_ACTIVE_SUBPLOTS, Plot, PlotPurpose, PlotStatus, PlotType}` |
| `tests/world_model/test_links.py` | `subset.{Plot, PlotStatus, PlotType}` |

### Why behavior→behavior imports preserved

`infra.world_model.lifecycle`, `infra.world_model.registry`, `infra.subplot.registry`, etc are NOT
shim indirection — they are behavior services within the same `infra.world_model` / `infra.subplot`
namespace. These imports stay. Only the entity imports (which routed through the shim to canonical
anyway) moved to canonical directly.

### `links.py` special handling

`infra/world_model/links.py` uses lazy import inside `apply_ripple_resolution` to dodge a historical
cycle risk:

```python
# Before Phase 19+ Sub1: infra.subplot.data_structures ↔ infra.world_model cycle
# After Phase 19+ Sub1: canonical lingwen_core.domain.* has NO cross-deps
# Defensive lazy pattern preserved (historical cycle risk gone but pattern retained)
```

TYPE_CHECKING block + runtime lazy import both migrated to canonical. Updated obsolete cycle-risk
comments to reflect new state.

### Why one missed file (T9b)

Original `grep -rln "from infra.world_model.data_structures" infra/world_model/` only matched
lines starting at column 0 — missed indented imports inside `if TYPE_CHECKING:` blocks. T9b was
discovered when running the final shim-indirection grep (which catches all lines, not just column 0).
Lesson documented in lessons section.

## Verification gates (all GREEN)

- **ruff**: 0 errors (full project check, 10 autofixed in T9b follow-up)
- **vitest**: 1762 passed + 1 skipped (no regression from v19.1 baseline)
- **vue-tsc**: 0 errors (no output = clean)
- **ESLint**: 0 errors (no output = clean)
- **knip**: `{"issues":[]}` (clean, no dead code)
- **lint-imports**: 3 contracts KEPT (`layer_dependencies`, `no_concrete_llm_service_in_business_code`, `no_concrete_sqlite3_in_business_code`)
- **Identity check**: 16/16 canonical entities `is`-identity with shim-path entities
  (KeyPoint, NodeId, NodeType, Relation, MentalLine, PhysicalLine, Ripple, RippleState,
  ResolutionMode, WorldSnapshot, Plot, PlotType, PlotPurpose, PlotStatus [cross-package],
  MAX_OPEN_RIPPLOTS, MAX_ACTIVE_SUBPLOTS)
- **Shim indirection in production code**: 0 (only 1 historical comment reference in `links.py:28`
  which explicitly notes the historical cycle risk)
- **Backend tests**:
  - `tests/subplot/`: 68 passed (incl. test_subplot_data_structures.py still passing)
  - `tests/world_model/`: 246 passed
  - `tests/consistency/checkers/`: 9 passed (test_foreshadow_ripple_alignment, test_pacing_ripple_integration)
  - `packages/lingwen-core/tests/`: 56 passed
  - `packages/lingwen-shared/tests/`: 136 passed (no regression)
  - `packages/lingwen-creator/tests/`: 73 passed (no regression)
  - `packages/lingwen-llm/tests/`: pass (no regression)

## Architecture invariants enforced (preserved from v19.1)

- **#36**: `lingwen_core.domain.*` is canonical source for all world_model + subplot entities.
- **#37**: `infra/world_model/data_structures` is a PHASE-COMPAT shim (all entities are re-exports from canonical).
- **#38**: `infra/world_model/__init__.py` is a PHASE-COMPAT re-export module.
- **#39**: `infra/subplot/data_structures.py` is a PHASE-COMPAT shim.
- **#40**: `lingwen_core.domain.*` does NOT depend on `infra.*` (DDD purity).

**New invariant (T10)**:
- **#41**: `infra/world_model/*.py` behavior services (engine, lifecycle, queries, registry,
  snapshot_diff, links) import domain entities directly from `lingwen_core.domain.*` — no
  `infra.world_model.data_structures.X` indirection in production code.
- **#42**: `infra/subplot/*.py` behavior services (queries, registry, lifecycle) import domain
  entities directly from `lingwen_core.domain.*` — no `infra.subplot.data_structures.X` indirection
  in production code.

## Lessons

1. **grep `^from` misses indented imports inside `if TYPE_CHECKING:` blocks** (T9b discovery). Use
   `grep -rn "infra.subplot.data_structures\|infra.world_model.data_structures"` (no `^` anchor) for
   full-coverage shim-indirection audit. The 9 behavior-service migrations (T1-T8) caught the
   column-0 imports; T9b caught the indented ones. Future shim-removal phases should start with the
   unanchored grep.

2. **Mechanical migrations batch when same pattern** (T9 batch of 5 test files in one commit — per
   Phase 19+ Sub1 §5 lesson 8). Same `infra.subplot.data_structures.X → lingwen_core.domain.subplot.X`
   pattern across 5 files = 1 commit. Review was 1 minute (diff confirmed) instead of 5 minutes.

3. **`from __future__ import annotations` enables forward-ref strings without TYPE_CHECKING blocks**
   (T8 cleanup). After migrating `Plot` to runtime import, the TYPE_CHECKING forward-ref block became
   unused. Removed cleanly. No mypy/pyright regressions.

4. **Behavior→behavior imports are NOT shim indirection** (T1-T8 design decision). `infra.world_model.lifecycle.MAX_OPEN_RIPPLOTS`
   stays as-is because it's a behavior service, not a re-export. The shim indirection question is
   specifically about ENTITY imports (KeyPoint, Ripple, PlotStatus, etc).

5. **`ruff --fix` for `noqa: F811` (duplicate import) flags `from X import Y` in TYPE_CHECKING when
   `Y` already imported at runtime** (T8 cleanup). Solution: remove the TYPE_CHECKING block
   (forward-ref strings work via `from __future__ import annotations`).

6. **Worktree python env-sync gotcha** (N.14 lesson 4 re-confirmed): `uv sync --all-packages` is
   not enough — `uv pip install pytest pytest-asyncio psutil` is also required for tests to run.
   `uv run pytest` uses system Python 3.10 by default (no fastapi/sqlite3 access) — must use
   `.venv/bin/python -m pytest ...` explicitly.

7. **Atomic 1-task-per-commit scales to 11 commits** (N.14 lesson 7 re-confirmed). 9 behavior
   services × ~1 commit + 5 test files batch + 1 missed behavior service (T9b) + 1 ruff autofix
   = 11 commits. Each independently revertable. Each verified by running the relevant test subset.

## Carryover closure

- ✅ **Sub1 polish (infra/world_model behavior services → direct lingwen_core.domain imports)**: CLOSED

## Carryover to Phase 19.x+

- **Sub2** (infra/consistency shim cleanup, 30+ files)
- **Sub3** (infra/agent_system shim cleanup)
- **infra/exports/* → packages/lingwen-storage migration** (separate concern)
- **lingwen_llm test-env gap** (Phase 115 carryover, still open)
- **ruff format cleanup** (Phase 19.x carryover)
- **Phase 114 prod preview regression** (accepted, no action planned)