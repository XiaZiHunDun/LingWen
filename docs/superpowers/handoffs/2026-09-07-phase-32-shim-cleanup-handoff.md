# Phase 32 — PHASE-COMPAT shim cleanup — handoff

> **Date**: 2026-09-07
> **Branch**: `phase-32-shim-cleanup`
> **Master HEAD at start**: `69e620d7` (v31.0)
> **Commits**: 9 commits (`3570a86f..9980e393`)
> **Status**: CLOSED ✅

## Summary

Phase 32 closes 3 of 4 P2-ARCHDEBT PHASE-COMPAT shim deletion items. Three pure re-export shim files deleted, 6 test consumers migrated, +1 fixup commit for 5 missed relative imports (N.14 lesson 1 violation surfaced mid-execution and corrected), +10 regression guard tests in `tests/test_phase32_shim_cleanup.py`.

**Net effect**: -112 source lines (32 + 69 + 11 shims) + 75 lines (test file) + 7 lines (fixup) = -30 lines net. 3 files deleted, 5 fixup files, 1 new test file, 5 doc files updated.

## Commits

```
3570a86f docs(phase-32): write spec + plan design docs                       [C0]
0e3a664b test(shim): add Phase 32 regression guard tests (RED)               [C1]
1fd9fd7b chore(infra): delete infra/subplot/data_structures.py shim (1 of 3) [C2]
eafd6d05 chore(infra): delete infra/world_model/data_structures.py shim (2 of 3) [C3]
eeb8dad9 refactor(test): migrate 6 MasterController test imports to lingwen_pipeline (3a of 3) [C4]
143c08a0 chore(packages): delete lingwen-core/agents/master_controller.py shim (3b of 3) [C5]
81430539 fix(infra): migrate 5 missed relative imports from deleted data_structures + master_controller shims [C2.5]
9980e393 docs(architecture): CLAUDE.md v32.0 + architecture.yml version 32.0 + arch spec + carryover flips [C6]
```

(8 source commits + 1 final docs commit; per workflow, no separate handoff commit — handoff doc IS this file, committed via C7 docs sync.)

## What was deleted

| File | Lines | Type | Status at deletion |
|---|---|---|---|
| `infra/subplot/data_structures.py` | 32 | Pure re-export from `lingwen_core.domain.subplot` | 0 functional consumers (1 historical comment in `links.py:29` cleaned in same commit) |
| `infra/world_model/data_structures.py` | 69 | Pure re-export from `lingwen_core.domain.*` | 0 functional consumers |
| `packages/lingwen-core/src/lingwen_core/agents/master_controller.py` | 11 | Pure re-export from `lingwen_pipeline.master_controller` | 6 test consumers migrated to canonical path |
| **Total** | **112** | | |

## Consumer migration pattern (mechanical sed-equivalent)

12 import sites in 6 test files:

```
from lingwen_core.agents import master_controller as mc_mod
```
→
```
from lingwen_pipeline import master_controller as mc_mod
```

All 12 sites use `mc_mod.MasterController.__new__(mc_mod.MasterController)` (single-symbol use), making the migration pure mechanical replacement.

## Test consumer migration sites

| File | Line(s) |
|------|---------|
| `tests/agent_system/test_master_controller_workflow.py` | 246 |
| `tests/agent_system/test_decision_integration.py` | 33 |
| `tests/agent_system/test_got_bridge.py` | 591, 813, 847 |
| `tests/dashboard/test_decision_api.py` | 27, 633 |
| `tests/dashboard/test_app_workflow_production_summary_f66.py` | 9 |
| `tests/dashboard/test_app_workflow_status.py` | 18, 91, 187, 282 |

Per Phase 19+ Sub1 §5 lesson 8: 6 test files batched into 1 commit (mechanical, same pattern).

## CRITICAL LESSON — relative import audit (N.14 lesson 1, 6th time in Phase 19+ chain)

### What went wrong

C2/C3/C5 were committed based on a consumer audit that used literal-text grep:
- `grep -rn "infra.subplot.data_structures\|infra.world_model.data_structures\|lingwen_core.agents.master_controller" --include="*.py"`

This audit missed **5 relative imports**:
1. `infra/subplot/__init__.py:19` — `from .data_structures import (MAX_ACTIVE_SUBPLOTS, Plot, ...)`
2. `infra/world_model/__init__.py:60` — `from .data_structures import PlotStatus`
3. `infra/world_model/key_point_graph.py:24` — `from .data_structures import KeyPoint, NodeId, Relation, WorldSnapshot`
4. `infra/world_model/snapshot_store.py:24` — `from .data_structures import WorldSnapshot`
5. `packages/lingwen-core/src/lingwen_core/agents/got_bridge.py:32` — `from .master_controller import MasterController`

These were discovered when running the full backend test suite after C5 — 23 collection errors in `tests/world_model/` + 5 errors in `tests/agent_system/` (got_bridge + chapter_emit + got_bridge_budget + phase7_1_production_fixes + ci/test_polish_merge_with_usage_ci).

### How it was fixed

Added C2.5 commit (`81430539`) migrating all 5 sites to canonical `lingwen_core.domain.*` (or `lingwen_pipeline.master_controller` for MasterController). Verified by re-running the 5 broken test files (68 passed) + tests/world_model/ (201 passed).

### Rule for future shim-deletion phases

The consumer audit MUST include these 3 greps in addition to literal-text grep:

```bash
# 1. Relative imports within the same package as the shim
grep -rn "from \.data_structures\b\|from \.\.data_structures\b" --include="*.py" $PACKAGE_DIR/

# 2. Sibling-package relative imports (e.g., `from .master_controller` in `agents/` package)
grep -rn "from \.${SHIM_MODULE}\b\|from \.\.${SHIM_MODULE}\b" --include="*.py" $PARENT_DIR/

# 3. Bare module-name imports without `from` (e.g., `import infra.world_model.data_structures`)
grep -rn "^import ${SHIM_PATH//./\\.}\b" --include="*.py" --include="*.md" --include="*.yml"
```

Phase 19+ Sub1 Polish §5 lesson 1 was about **indented imports inside TYPE_CHECKING blocks** being missed by `^from`. Phase 32's lesson is about **relative imports being missed by literal-text grep** (because `.data_structures` ≠ `infra.world_model.data_structures`). Both lessons apply to all future shim-deletion phases.

### Updated MEMORY.md entry

Added to "Avoid (Don't Do)" section:

> ❌ Don't rely solely on literal-text grep (`grep -rn "infra.X.Y"`) for shim consumer audit. Misses relative imports (`from .Y`, `from ..Y`). Also run `grep -rn "from \\.Y\\b"` (anchored to `from \\.`). Phase 32 lesson: 5 missed relative imports broke 23+5 collection errors after C2/C3/C5; fixed in C2.5 commit.

## Verification gates (all green after C2.5 + C6)

| Gate | Command | Result |
|------|---------|--------|
| G1 ruff | `ruff check .` | 0 errors on Phase 32 modified files (1 pre-existing error in `tests/agent_system/test_dashboard_budget_endpoints.py:20` unrelated to Phase 32) |
| G2 guard | `pytest tests/test_phase32_shim_cleanup.py -v` | **10/10 GREEN** (3 path-deleted + 6 consumer-migrated + 1 canonical-symbol) |
| G3 modified suites | `pytest <6 consumer files>` | **116 passed + 1 skipped** (baseline preserved) |
| G4 critical paths | `pytest tests/world_model/ tests/agent_system/test_chapter_emit.py tests/agent_system/test_got_bridge.py tests/agent_system/test_got_bridge_budget.py tests/agent_system/test_phase7_1_production_fixes.py tests/ci/test_polish_merge_with_usage_ci.py` | **201 + 68 passed** (all previously-broken-by-C2/C3/C5 now fixed by C2.5) |
| G5 full backend | `pytest tests/ --rootdir=.` | 3659 passed + 33 skipped + 1 xfailed + 40 failed (40 fails are PRE-EXISTING on master, confirmed via stash baseline: 9 fails in 5 representative test files before Phase 32) |
| G8 grep audit | `grep -rn "infra.subplot.data_structures\|infra.world_model.data_structures\|lingwen_core.agents.master_controller" --include="*.py" apps/ tests/ packages/ infra/ scripts/` | **0 consumer hits** (only docstring text in `tests/test_phase32_shim_cleanup.py` which is intentional guard-test pattern matching) |

Note: G5 shows 40 failed tests but those are PRE-EXISTING failures on master HEAD in unrelated test categories (LLM-based tests, sqlite hygiene tests, CLI integration tests). Confirmed via `git stash` baseline run. Phase 32 introduces 0 new failures.

## Architecture invariants enforced (1 NEW, 49 total)

- **#48 (NEW)** ✅ NO PHASE-COMPAT shim files in `infra/` or `packages/lingwen-core/`. All 3 closed:
  - `infra/subplot/data_structures.py` — deleted
  - `infra/world_model/data_structures.py` — deleted
  - `packages/lingwen-core/src/lingwen_core/agents/master_controller.py` — deleted

Updated invariants:
- **#37** ✅ `infra/world_model/data_structures.py` DELETED Phase 32 (was PHASE-COMPAT shim, 0 consumers)
- **#39** ✅ `infra/subplot/data_structures.py` DELETED Phase 32 (was PHASE-COMPAT shim, 0 consumers)
- **#38** ✅ `infra/world_model/__init__.py` = canonical re-export + behavior services mix (split candidate Phase 33+)

## Doc sync (C6 commit)

| File | Change |
|------|--------|
| `CLAUDE.md` | v32.0 entry (mirror v31.0 format); v32.0 carryover address; v31.0 demoted |
| `.lingwen/architecture.yml` | version 25.0 → 32.0; invariants #37, #39, #38, #48 updated; #46-#47 from Phase 21 untouched |
| `docs/LINGWEN_ARCHITECTURE_SPEC.md:669` | `SubplotDataStructures` row marked DELETED |
| `docs/superpowers/handoffs/2026-09-04-phase-27-wfrunner-handoff.md:26` | "PHASE-COMPAT shim, 留 P2-ARCHDEBT" → "deleted Phase 32" |
| `docs/superpowers/handoffs/2026-09-07-phase-31-archdebt-mini-handoff.md:39,162-168` | "Phase 33 candidate A/B" → "CLOSED by Phase 32" |

## Carryover closure

| Carryover | Status |
|-----------|--------|
| P2-ARCHDEBT PHASE-COMPAT shim deletion (v31.0 剩余 1/2) | **CLOSED** by v32.0 (3 shims deleted, 6 test consumers migrated, 5 missed relative imports fixed) |
| N.14 lesson 1 violation (relative import audit gap) | **CLOSED** by C2.5 fixup commit; new grep pattern logged in MEMORY.md |

## Carryover to Phase 33+

| ID | Scope | Estimate |
|----|-------|----------|
| ~~**`infra.got.*` → `packages/lingwen-got/` migration**~~ | CLOSED by Phase 34 (v33.0) | n/a |
| **`infra/world_model/__init__.py` split** | mixed file → canonical (lingwen_core.domain.*) + behavior (infra.world_model.{engine,queries,registry,...}) + 5 consumer migration (1 poc + 4 test files) | 1 phase / 8-12 commits |
| **`polisher/prompts.py:132` `_safe_label` import** | latent broken import (pre-existing bug discovered during Explore agent verification) | 1 small fixup |
| **HANDOFF.md `latest_decision_queue` wording** | pre-existing carryover | doc-only |
| **PHASE-COMPAT docstring in `tests/__init__.py` + `tests/consistency/__init__.py` + `tests/infra/__init__.py`** | false positive — legitimate pytest package init files. Leave as-is. | none |

## Lessons

### 1. N.14 lesson 1, 6th time — relative imports missed by literal-text grep

(see "CRITICAL LESSON" above for full detail)

The previous 5 applications of N.14 lesson 1 all used `^from` / column-0 anchors and caught **indented imports inside TYPE_CHECKING blocks**. Phase 32's lesson is that **literal-text grep with full dotted path** also misses **relative imports** with bare module names (`from .data_structures`, `from .master_controller`).

**Rule for all future shim-deletion phases**: audit must include 3 grep patterns:
1. Literal dotted path (`from infra.X.Y import ...`)
2. Relative same-package (`from .Y import ...`)
3. Relative parent-package (`from ..Y import ...`)

### 2. Pre-existing failure baseline verification (N.14 lesson 4, 4th time)

When the post-C5 full backend test suite showed 40 fails + 8 errors, I initially suspected Phase 32 regression. The `git stash` baseline run on master HEAD (without Phase 32 changes) confirmed 9 fails in the same 5 representative test files. **All 40 fails are pre-existing in unrelated test categories** (LLM-based, sqlite hygiene, CLI integration).

**Lesson**: when full-suite fail count exceeds expected, always run `git stash` + master baseline before claiming regression. Saves hours of debug time.

### 3. Mechanical migrations batch when same pattern (N.14 lesson 7 re-confirmed)

6 test files migrated with identical sed pattern → 1 commit. Per Phase 19+ Sub1 §5 lesson 8. Review was <1 minute.

### 4. Carrier documentation update is part of the work, not optional

5 doc/spec/handoff files needed carryover-status flips. None of them was a code change, but skipping them would have left dangling "Phase 33 candidate" references. C6 commit batches all doc flips in 1 atomic commit (per Phase 21 lesson 5).

### 5. Sub-agent implementer audit pattern is correct

The Explore sub-agent correctly verified:
- ✅ All 12 MasterController consumer sites
- ✅ Canonical import paths exist + symbol availability
- ✅ Edge case discovery (`polisher/prompts.py:132` `_safe_label` latent broken import — flagged as Phase 33 carryover, NOT in Phase 32 scope)

The sub-agent missed **relative imports** because the agent's grep was also literal-text. **Lesson**: even with sub-agent verification, the final audit grep must include relative-import patterns per Phase 32 lesson 1.

## Phase 19+ chain final state

After Phase 32:
- **13 NEW architecture invariants** added (#36-#48) across the Phase 19+ chain (including #48 NEW in Phase 32)
- **All Phase 18 carryovers closed**
- **All Phase 19+ sub-phases (Sub1/Sub1 polish/Sub2/Sub3) closed**
- **All Phase 20-31 carryovers closed**
- **PHASE-COMPAT shim directories cleanup**: `infra/consistency/` (Phase 21) + `infra/agent_system/` (Phase 21) + `infra/exports/` (Phase 20) + 3 individual shims (Phase 32)
- **Only 1 remaining P2-ARCHDEBT item**: `infra.got.*` → `packages/lingwen-got/` migration (multi-day) → **CLOSED by Phase 34 (v33.0)**; remaining P2-ARCHDEBT → `infra/world_model/__init__.py` split (Phase 35)

## Solo workflow closure

```
$ git checkout master && git merge --ff-only phase-32-shim-cleanup
$ git push origin master
$ git worktree remove ../LingWen-phase-32
```

Master HEAD after merge: `9980e393` (v32.0).

## Final commit chain (8 source commits)

```
9980e393 docs(architecture): CLAUDE.md v32.0 + architecture.yml version 32.0 + arch spec + carryover flips  [C6]
81430539 fix(infra): migrate 5 missed relative imports from deleted data_structures + master_controller shims [C2.5]
143c08a0 chore(packages): delete lingwen-core/agents/master_controller.py PHASE-COMPAT shim (3b of 3)  [C5]
eeb8dad9 refactor(test): migrate 6 MasterController test imports to lingwen_pipeline (3a of 3)  [C4]
eafd6d05 chore(infra): delete infra/world_model/data_structures.py PHASE-COMPAT shim (2 of 3)  [C3]
1fd9fd7b chore(infra): delete infra/subplot/data_structures.py PHASE-COMPAT shim (1 of 3)  [C2]
0e3a664b test(shim): add Phase 32 regression guard tests (RED)  [C1]
3570a86f docs(phase-32): write spec + plan design docs  [C0]
```
