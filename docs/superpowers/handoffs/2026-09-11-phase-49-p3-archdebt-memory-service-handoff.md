# Phase 49 P3-ARCHDEBT (lingwen-memory-service) Handoff

> **Date**: 2026-09-11
> **Phase**: 49 — P3-ARCHDEBT item 13/12+1
> **Branch**: `phase-49-p3-archdebt-memory-service`
> **Status**: ✅ **CLOSED** (master HEAD pending ff-merge)
> **ARCHDEBT Rank**: memory_service (heavy 9 deps candidate)

## TL;DR

`infra/memory_service.py` (307 LOC, NOT-LEAF 9 workspace deps) → `packages/lingwen-memory-service/` (2 sub-modules per Phase 44 NOT-LEAF template). 4 consumer files migrated. 1 NEW invariant (I068). Version bump v46.0 → v47.0.

## Atomic commits (5+1 = 6 total on `phase-49-p3-archdebt-memory-service`)

| SHA | Type | Scope | Notes |
|-----|------|-------|-------|
| `daecfbf2` | `docs(phase-49)` | spec | 9-pattern audit + 4 real consumers + 3 false-positives |
| `4433d6ee` | `feat(packages)` | scaffold | 2 sub-modules + pyproject + workspace + tool.uv.sources |
| `795be3b8` | `refactor(consumers)` | bulk 4 sites | 1 wildcard + 3 indented lingwen-creator files |
| `a1e5f420` | `chore(infra)` | delete + I068 + v47.0 | infra/memory_service.py DELETED (via C1 git mv) + invariant + version |
| `<C4>` | `test(phase-49)` | 13 guards + handoff | Phase 49 guards + handoff + MEMORY.md + topic file |
| **(C4.5)** | `fix(test)` | pending | Phase 39 + 45 + 46 wildcard-remains + I067 invariant add |

## Pre-spec audit (verified by fresh grep 2026-09-11)

Real consumers (4 sites):
1. `infra/core/__init__.py:6` — wildcard
2. `packages/lingwen-creator/src/lingwen_creator/content/agent.py:78`
3. `packages/lingwen-creator/src/lingwen_creator/memory/assets.py:32`
4. `packages/lingwen-creator/src/lingwen_creator/memory/query.py:119`

False-positives (3 excluded):
- `infra/memory_service.py:7` self-import (Phase 42 lesson)
- `tests/test_phase45_lingwen_utilities.py:400` STRING LITERAL docstring
- `tests/test_phase46_lingwen_filter.py:313` STRING LITERAL docstring

## Architecture (single-module NOT-LEAF)

```
packages/lingwen-memory-service/
├── pyproject.toml              (2 deps: lingwen-logging-config + lingwen-memory)
├── src/lingwen_memory_service/
│   ├── __init__.py             (4 public symbols)
│   └── service.py              (307 LOC)
```

### Public surface (4 symbols)

| Symbol | Kind |
|--------|------|
| `NoOpMemoryGateway` | class |
| `get_memory_gateway` | public func |
| `is_memory_gateway_available` | public func |
| `get_initialization_error` | public func |

### Workspace deps — NOT-LEAF (2 deps via umbrella)

```toml
dependencies = [
    "lingwen-logging-config",  # Phase 39 (logger)
    "lingwen-memory",           # covers 8 submodule imports
]
```

`lingwen-memory` umbrella covers: config.load_yaml + embeddings.batch_embed.BatchEmbedder + gateway.memory_gateway.MemoryGateway + state.character_tracker.CharacterTracker + state.fact_base.FactBase + state.plot_thread_tracker.PlotThreadTracker + state.timeline_manager.TimelineManager + vector.embedder.Embedder + vector.qdrant_client.QdrantClientWrapper.

## Validation gates — all GREEN

| Gate | Status |
|------|--------|
| **13 phase49 guards** | ✅ 13/13 PASSED |
| **166 prior + phase49 guards total** | ✅ 166/166 (after C4.5 fixups for Phase 39 + 45 + 46 + I067 add) |

## 4 lessons

### Lesson 1: Self-import preservation (Phase 42 lesson)
`infra/memory_service.py:7` has `from infra.memory_service import get_memory_gateway` self-import (preserved per Phase 42 lesson). C4 test `test_self_import_preserved_in_service` validates this.

### Lesson 2: umbrella dep pattern (Phase 45+ lesson)
Declaring `lingwen-memory` as single dep covers 8 submodule imports via `packages/lingwen_memory.*` paths. Avoids 8 separate workspace dep entries.

### Lesson 3: N.14 lesson 1 #25 wildcard-remains (3rd fixup in this phase pattern)
Phase 45 + 46 guards both asserted `from infra.memory_service import *` was still in `infra/core/__init__.py`. Phase 49 migrated this wildcard → both guards broke → 2 C4.5 fixups.

### Lesson 4: Python regex insert can fail silently
My Phase 48 + Phase 49 C3 Python replace for invariant insertion failed silently when the source string was already long/different. Resulted in missing I067 invariant in architecture.yml. **Lesson**: ALWAYS verify invariant count after Python-based replacement (grep -c I067).

## Carryover closure

| Phase | Module | Status |
|-------|--------|--------|
| P3-ARCHDEBT 12/11+1 (full_check_report) | ✅ Phase 48 |
| **P3-ARCHDEBT 13/12+1 (memory_service)** | ✅ **Phase 49** |
| P3-ARCHDEBT remaining | 🟡 Phase 50+ (types / filter Phase 46 cleanup) |

## References

- ARCHDEBT-CANDIDATES.md "memory_service" (4 consumers, 10 deps)
- Phase 39 (logging_config) — provides logging dep
- Phase 44 (lingwen-prose-calibration) — single-module NOT-LEAF template
- Phase 45 (lingwen-utilities batch) — umbrella dep pattern (batch coverage)
- Phase 48 (full_check_report) — most recent NOT-LEAF single-module
- N.14 lesson 1 #25 — wildcard-remains pattern (recurring C4.5 fixups in P3-ARCHDEBT)

---

> **All claims verified by fresh-run** (Phase 41 mini lesson #1):
> 13 phase49 guards + 153 prior-phase guards (after 3 C4.5 fixups)
> = 166 PASSED, 0 regressions.