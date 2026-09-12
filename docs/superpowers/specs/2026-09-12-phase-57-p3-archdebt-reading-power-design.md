# Phase 57 — P3-ARCHDEBT `infra/reading_power/` → `packages/lingwen-reading-power/`

**Date**: 2026-09-12
**Phase**: 57
**Pattern**: NOT-LEAF P3-ARCHDEBT (Phase 40a + 56 hybrid)
**Author**: P3-ARCHDEBT session

## Context

P3-ARCHDEBT 5/5 (Phase 36-40) + 10/15 batch (Phase 42-50) + prose cluster (Phase 51) closed all top-level `infra/*.py` modules + first-layer sub-directories (`infra/{tools/legacy,core,studio,persistence,world_db}`). After Phase 56, `infra/` top-level is fully cleared but **21 sub-directories remain**, totaling 21,349 LOC across 213+ Python files (per `docs/superpowers/infra-subdir-audit.md`).

This phase targets **`infra/reading_power/`** — 1,006 LOC across 7 files (the **追读力系统** / Reading Power System), chosen because:

1. **Moderate size**: 1,006 LOC (smaller than Phase 54 `persistence` 1,578 LOC; same as Phase 56 `world_db` 1,006 LOC).
2. **Manageable consumer count**: 16 sites across 14 files (vs Phase 54's 66 sites).
3. **Clean prior-phase-guard state**: `grep -n "reading_power" tests/test_phase*.py` returns 0 hits — no guard needs reverse-unlocking (Phase 51 N.14 lesson 1 11th variant avoided).
4. **Real product feature** (not scaffolding): DB exists at `infra/.state/reading_power.db`, schema columns actively served by `studio_api/routes/overview.py`, UI rendered in 3 pages (ChapterTable.vue, CoolpointChart.vue, OverviewPage.vue). Migration preserves value; deletion would lose historical data.
5. **NOT-LEAF pattern template**: 2 workspace deps (`lingwen-shared` + `lingwen-storage`) — closest to Phase 40a `lingwen-studio-registry` (3 deps) but smaller scope.

## Audit findings (verified 2026-09-12)

### Module structure

| File | LOC | Symbols | Role |
|------|-----|---------|------|
| `__init__.py` | 17 | (barrel, 8 names) | Re-export layer |
| `db.py` | 427 | `ReadingPowerDB`, `DB_PATH` | **Data layer** — SQLite CRUD |
| `engine.py` | 127 | `ReadingPowerEngine` | Orchestrator |
| `rule_matcher.py` | 139 | `RuleMatcher`, `SuspectedSegment` (NamedTuple), `HOOKS_RULES_PATH`, `COOLPOINTS_RULES_PATH` | Rule scanning |
| `llm_analyzer.py` | 151 | `LLMAnalyzer`, `AnalysisResult` (dataclass), `SuspectedSegment` (dataclass — DUPLICATE), `ANALYZE_HOOKS_PROMPT` | LLM analysis |
| `hook_tracker.py` | 71 | `HookTracker` | DB wrapper |
| `coolpoint_tracker.py` | 74 | `CoolPointTracker` | DB wrapper |
| **Total** | **1006** | **8 classes + 1 NamedTuple + 1 dataclass + 3 constants** | |

### Consumer audit (N.14 9-pattern matrix)

| # | Pattern | Count | Notes |
|---|---------|-------|-------|
| 1 | Literal dotted-path imports | 14 sites across 13 files | Production + tests + function-body |
| 2 | Indented/function-body imports | 3 sites | `lingwen-cli/commands/reading_power.py:30`, `lingwen-persistence/bootstrap.py:18`, `tests/persistence/test_integration.py:103` |
| 3 | Relative imports inside `infra/reading_power/` | 14 (intra-package only) | All use `from infra.reading_power.X` form (will rewrite to canonical) |
| 4 | Filesystem-path string literals | 5 doc references | `pyproject.toml:327` comment + 4 doc files (no code path literals) |
| 5 | Wildcard `from infra.reading_power import *` | 0 | — |
| 6 | `monkeypatch.setattr(..., "infra.reading_power.X", ...)` | 0 | — |
| 7 | `import X as Y` re-exports | 1 | `apps/studio_api/__init__.py:5` re-exports `ReadingPowerDB` via `apps.studio_api` namespace |
| 8 | Doc comments referencing old path | 8 docs | Mostly historical design specs (acceptable, update post-migration) |
| 9 | Prior-phase guards | 0 | Clean slate — no reverse-unlocking needed |

### Workspace deps

```python
# db.py:18  — TYPE_CHECKING-style
from lingwen_shared.ports.storage import ConnectionPort

# db.py:57  — runtime deferred (inside _get_connection)
from lingwen_storage.sqlite_storage_adapter import SqliteStorageAdapter
```

→ **NOT-LEAF** with 2 deps. Migration must declare both in new `pyproject.toml`.

### Code-quality issues discovered

1. **Duplicate `SuspectedSegment`** — `rule_matcher.py:15` (NamedTuple) vs `llm_analyzer.py:11` (dataclass). `__all__` exposes only NamedTuple; dataclass is dead code.
2. **Dead-code bug** in `rule_matcher.py:_determine_position`: every chapter >20 chars returns "开头", rest of function unreachable.
3. **Unused import** in `engine.py:7` — imports `SuspectedSegment` but never uses it.
4. **`DB_PATH` will break on migration** — `db.py:24` uses `parents[2]` from `infra/reading_power/`. New location `packages/lingwen-reading-power/src/lingwen_reading_power/db.py` needs `parents[4]` (Phase 40a C1.5 lesson).

## Goal

Migrate `infra/reading_power/` (7 files, 1,006 LOC) + `tests/reading_power/` (8 files, ~26 KB) into `packages/lingwen-reading-power/` as a workspace member with canonical `lingwen_reading_power.*` import path. Apply 4 bug fixups during C1.5. Add I077 invariant. FULL DELETE `infra/reading_power/` + `tests/reading_power/`. Bump version to v53.0.

## Atomic commit plan

| # | Commit | Task | Lines | Risk |
|---|--------|------|-------|------|
| **C0** | `docs(phase-57)` | spec + plan | +400 / 0 | none |
| **C1** | `feat(packages)` | scaffold `packages/lingwen-reading-power/` (8 src files + tests dir + pyproject + workspace member declaration) | +1300 / 0 | medium (new package) |
| **C1.5** | `fix(reading-power)` | 4 bug fixups: `DB_PATH` parents[4], `SuspectedSegment` dedup, `_determine_position` unreachable-code, unused import | +5 / -15 | medium (behavior change) |
| **C2** | `refactor(consumers)` | migrate 16 sites (6 production + 8 tests + 1 apps re-export + 1 apps/__init__ re-export) | +24 / -24 | medium (touch many files) |
| **C3** | `chore(infra)` | FULL DELETE `infra/reading_power/` (7 files) + `tests/reading_power/` (8 files) + I077 invariant in CLAUDE.md | -1030 / +20 | medium (regression risk) |
| **C4** | `docs(arch)` | version bump v52.0 → v53.0 + update 8 doc references to old path | +50 / -50 | low |
| **C5** | `test(phase-57)` | regression guards + handoff + MEMORY.md | +300 / 0 | low |

**Total**: 7 atomic commits, ~1,679 line PR. NET = +650 lines (mostly new test coverage + guards).

## Invariant to add (I077)

```
I077 | `packages/lingwen-reading-power/` 是 Reading Power System（追读力：钩子 hooks + 爽点 coolpoints + chapter summary + analysis log + ReadingPowerDB/Engine/RuleMatcher/LLMAnalyzer/HookTracker/CoolPointTracker 8 个 public classes + SuspectedSegment NamedTuple + AnalysisResult dataclass + 3 module constants 共 13 个 public symbols）的唯一实包；`infra.reading_power.*` 和 `infra/reading_power/` 路径非法 (Phase 57 P3-ARCHDEBT infra/reading_power 全量迁移)
```

## What this phase does NOT do

- Does NOT remove `coolpoint_count` / `coolpoint_density` / `hook_count` schema columns (canonical in `lingwen-persistence`, not in scope).
- Does NOT remove `CoolpointChart.vue` / `ChapterTable.vue` coolpoint columns (UI plumbing outside `infra/`).
- Does NOT delete the SQLite DB at `infra/.state/reading_power.db` — but its path will need `parents[4]` fixup post-migration.
- Does NOT touch any consumer outside the 16 enumerated sites.
- Does NOT introduce a new CLI sub-command (existing `lingwen-cli reading-power` continues to work).

## Risks & mitigations

| Risk | Mitigation |
|------|-----------|
| New package breaks `uv sync` resolution | Run `uv sync --all-packages` after C1; verify `uv pip list \| grep lingwen-reading-power` |
| Function-body imports missed | Phase 38 lesson 3: grep `^[[:space:]]*from infra\.reading_power` (unanchored) |
| Wildcard import misses | grep `from infra\.reading_power import \*` (Pattern 5 audit confirms 0) |
| Relative imports inside module | 14 sites, all intra-package — rewrite to canonical `from lingwen_reading_power.X import Y` form |
| `monkeypatch.setattr` for old path | 0 sites confirmed (Pattern 6) |
| `DB_PATH` parents[N] regression | Apply `parents[4]` fixup in C1.5; add guard test that `DB_PATH.exists()` after scaffold |
| `ReadingPowerDB.__init__` `DeprecationWarning` still raised post-migration | Preserved (it's intentional, telling callers to use the registry singleton) |

## Validation gates

After all 7 commits, all of these must be GREEN:

1. `uv sync --all-packages` exits 0 with new member visible
2. `uv run pytest packages/lingwen-reading-power/tests/ -v` — all tests pass (mirrors `tests/reading_power/`)
3. `uv run pytest tests/persistence/test_integration.py -v` — function-body import still works
4. `grep -rn "infra\.reading_power" --include="*.py" --include="*.md" --include="*.toml"` returns 0 hits (excluding historical archive)
5. `grep -rn "infra/reading_power" --include="*.py"` returns 0 hits
6. `ruff check packages/lingwen-reading-power/` returns 0 issues
7. New `tests/test_phase57_lingwen_reading_power.py` passes all 8+ regression guards
8. Backend `uv run pytest tests/ -v` baseline preserved (336 passed + 11 skipped pre-phase, 336+8+ post-phase)
9. Phase 36-56 guards still GREEN (no regression on prior invariant enforcement)

## Pre-flight checklist

- [x] Audit complete (Phase 57-A)
- [x] Decision made: MIGRATE not DELETE (Phase 57-B)
- [ ] Branch created: `phase-57-p3-archdebt-reading-power`
- [ ] Worktree clean
- [ ] 7 atomic commits on phase branch
- [ ] User runs ff-merge to master after Phase 57-D

## References

- Phase 56 template: `packages/lingwen-world-db/` (1,006 LOC, LEAF, 23 sites)
- Phase 54 template: `packages/lingwen-persistence/` (1,578 LOC, LEAF, 66 sites)
- Phase 40a NOT-LEAF template: `packages/lingwen-studio-registry/` (3 deps)
- Phase 53 dead-code template: `infra/{tools/legacy,core,studio}/` deletions (full-delete pattern)
- Audit: `docs/superpowers/infra-subdir-audit.md` (Phase 52)
- N.14 lesson 1: 9-pattern audit matrix — see `MEMORY.md`
- DB_PATH fixup pattern: Phase 40a C1.5 (factory_root parents[4])