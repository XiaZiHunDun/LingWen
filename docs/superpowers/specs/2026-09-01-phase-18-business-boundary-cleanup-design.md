# Phase 18 — Business Boundary + Interface Cleanup Design (REVISED)

## Context

Phase 18 was originally planned on 2026-08-14 with 16 tasks focused on:
- Freezing Ports interfaces (Protocol classes)
- Domain entity extraction to `packages/lingwen-core/domain/`
- Use-cases events
- studio_api thin shell
- Cleanup of `infra/agent_system/`, `infra/consistency/`, `infra/memory_system/`, `infra/prompt_engineering/`, `infra/state/`, `infra/world_model/`

Between the plan's creation (Aug 14) and now (Sep 1), **Phase 126 v16.0-v16.5#N.17** was completed, which substantially executed many Phase 18 deliverables.

## Verify-before-design findings (2026-09-01)

| Task | Original plan | Current state |
|------|----------------|----------------|
| 18.0 Freeze Ports | NEW `packages/lingwen-core/src/lingwen_core/ports/` | ✅ DONE — `checker.py` (29 lines) + `llm.py` (56 lines) + `storage.py` (85 lines) with `Protocol` classes + mock impls |
| 18.1 Domain entities | NEW `packages/lingwen-core/src/lingwen_core/domain/` | ✅ DONE — `chapter.py` (73) + `character.py` (43) + `common.py` (118) + `foreshadow.py` (60) + `ripple.py` (188) + `volume.py` (43). All entities + domain events defined. |
| 18.2 Use-cases | NEW `packages/lingwen-core/src/lingwen_core/use_cases/` | ✅ DONE — `merge_ripples.py` + `review_chapter.py` + `write_chapter.py` |
| 18.4 `infra/agent_system/` | DELETE | ⚠ PARTIAL — 4 files remain (`__init__.py` + `reviewer.py`); BUT all are 1-line `PHASE-COMPAT` shims that re-export from `lingwen_core.agents.agents.reviewer`. |
| 18.5 `infra/consistency/` | DELETE | ⚠ PARTIAL — 14 files remain; BUT all are 1-line shims that re-export from `lingwen_quality.consistency.*`. |
| 18.6 `infra/memory_system/` etc | DELETE | ✅ DONE — all 3 dirs gone |
| 18.7 `infra/world_model/` | Fix stale imports + DELETE | ⚠ PARTIAL — 13 files remain, 52 imports from external consumers |
| 18.8 `infra/__init__.py` | Clean up 178 lines | ✅ DONE — 23 lines (was 178) |

## Critical Verification Findings

### Finding A: `infra/consistency/` and `infra/agent_system/` are PHASE-COMPAT shims (NOT duplication)

`infra/consistency/__init__.py` literally says:
```python
# PHASE-COMPAT: Phase 13.X — DELETE after v16.x
"""Compatibility namespace re-exporting consistency checkers from
``lingwen_quality.consistency``. Historically lived at ``infra.consistency.*``
before consolidation into the lingwen_quality package."""
```

Same pattern for `infra/agent_system/`. The shim directories contain 1-line re-exports, NOT duplicated implementations. 30+ consumers still use the shim paths (`packages/lingwen-core/src/lingwen_core/agents/*.py` + `scripts/`). Migrating all 30+ + deleting shims would expand Phase 18 to 30+ commits.

### Finding B: `infra/world_model.data_structures.WorldSnapshot` has API divergence with `lingwen_core.domain.ripple.WorldSnapshot`

The new `lingwen_core.domain.ripple.WorldSnapshot` is a **strict subset** of `infra.world_model.data_structures.WorldSnapshot`. Missing:
1. `to_dict()` / `from_dict()` methods (used by tests/consistency/checkers/, tests/subplot/, tests/world_model/)
2. `active_subplots: tuple["Plot", ...]` field (used by tests/subplot/test_subplot_integration.py:248)
3. `physical: PhysicalLine` and `mental: MentalLine` fields (used by subplot integration tests)

This blocks trivial migration. Adding these to `lingwen_core.domain` would expand Phase 18 scope beyond closure.

## Revised Phase 18 Closure Scope (3 sub-phases)

| Sub | Description | Files |
|-----|-------------|-------|
| **Sub-A** | Remove 14 resolved TODO(Phase18) markers (workarounds for domain entity unavailability; domain now exists in `packages/lingwen-core/domain/`) | 8 source files |
| **Sub-B** | Update `.lingwen/architecture.yml` (version → "16.5.N17+18", DP-02/DP-03 enforcement_phase, add domain/ports/use_cases active_subsystems) | 1 file |
| **Sub-C** | Write Phase 18 handoff doc + update CLAUDE.md | 2 files |

**Estimated total**: 3 commits (atomic 1-task-per-commit).

## Goals

1. Remove 14 TODO(Phase18) markers — the workarounds are no longer needed because domain entities exist
2. Update `.lingwen/architecture.yml` to reflect that `domain`/`ports`/`use_cases` are shipped in `packages/lingwen-core/`
3. Produce Phase 18 handoff doc
4. All CI gates green: pytest / knip / vue-tsc / ESLint / ruff / import-linter 3 contracts

## Non-Goals

- **NOT** deleting `infra/world_model/` entirely — domain API divergence (Finding B)
- **NOT** deleting `infra/consistency/` or `infra/agent_system/` shims — 30+ consumers still depend on them (Finding A)
- **NOT** migrating the 30+ consumers using `infra.consistency.*` / `infra.agent_system.*` paths — out of scope
- **NOT** adding `to_dict()`/`from_dict()` methods to `lingwen_core.domain` — out of scope
- **NOT** touching `infra/exports/*` migration — separate concern (separate 2 TODO markers)
- **NOT** touching studio_api routes — separate refactor
- **NOT** adding new domain entities or ports — only marking shipped status

## Out of Scope (NOT in Phase 18 closure)

- **`infra/exports/*`** → `packages/lingwen-storage` migration (separate concern, 2 TODO markers, future work)
- **`infra/world_model.*` consumers migration** — blocked by API divergence (Finding B)
- **`infra/consistency.*` and `infra.agent_system.*` consumers migration** — 30+ files, out of Phase 18 scope
- **studio_api thin shell** — separate refactor

## Verification Before Closure

### Sub-A — Domain availability

```bash
grep -rn "class Ripple\b\|class RippleState\b\|class NodeId\b\|class NodeType\b\|class Chapter\b\|class Volume\b\|class Character\b\|class Foreshadow\b" \
  packages/lingwen-core/src/lingwen_core/domain/ --include="*.py"
```

Expected: all entities present.

### Sub-B — Domain/Ports/Use-cases in architecture.yml

```bash
test -d packages/lingwen-core/src/lingwen_core/domain
test -d packages/lingwen-core/src/lingwen_core/ports
test -d packages/lingwen-core/src/lingwen_core/use_cases
```

Expected: 3 directories exist.

### Sub-C — TODO(Phase18) marker count

```bash
grep -rn "TODO(Phase18)" packages/ --include="*.py" |  | wc -l
```

Expected: 14 results before Sub-A → 0 results after Sub-A (in `packages/lingwen-*` scope; `infra/exports/*` markers are separate concern).

## Implementation Plan (3 atomic commits)

| Commit | Sub | Description | Files |
|---|---|---|---|
| T1 | Sub-A | Remove 14 TODO(Phase18) markers (domain entities exist; workarounds obsolete) | 8 source files |
| T2 | Sub-B | Update `.lingwen/architecture.yml` | 1 file |
| T3 | Sub-C | Write handoff + update CLAUDE.md | 2 new/updated files |

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| T1 removes TODO that was actually load-bearing | Very Low | TODO comments are documentation only; logic unchanged |
| T2 breaks architecture.yml schema | Very Low | Manual edits; verified against existing module_boundaries pattern |
| T3 conflicts with MEMORY.md auto-load | Very Low | CLAUDE.md is project docs (committed); separate from MEMORY.md |

## Carryover to Phase 19+

After Phase 18 closure:
- **`infra/world_model.*` consumers migration** (Sub1 deferred) — blocked by WorldSnapshot API divergence. Future phase: add `to_dict()`/`from_dict()` + `active_subplots` field to `lingwen_core.domain.WorldSnapshot`.
- **`infra/consistency.*` + `infra.agent_system.*` consumers migration** (Sub2/3 deferred) — 30+ files. Future phase: bulk rename + delete shim directories.
- **`infra/exports/*`** → `packages/lingwen-storage` migration (separate, 2 TODO markers)
- **Phase 114 prod preview regression** (still accepted)
- **New feature work** (would require brainstorming)