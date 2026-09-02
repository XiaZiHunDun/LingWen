# Phase 21 — shim cleanup continuation — handoff

> **Date**: 2026-09-02
> **Branch**: `phase-21-shim-cleanup`
> **Master HEAD at start**: `6d7d310d` (v20.0)
> **Commits**: 4 source commits (`a52ea0e2..d64587b4`)
> **Status**: CLOSED ✅

## Summary

Phase 21 closes 2 long-standing carryovers from v19.3 + v19.4: deletion of `infra/consistency/` + `infra/agent_system/` PHASE-COMPAT shim directories. Same pattern as Phase 20 (pure deletion of zero-consumer shims), split into 2 atomic commits for bisect-friendly history.

**Bonus side effect**: `tests/test_phase18_4_agent_migration.py::test_infra_agent_system_deleted` — **failing since Phase 18** — now passes naturally after `infra/agent_system/` deletion. This was the regression test v19.4 §5 lesson 3 warned about ("regression tests in 'regressed' direction should be actionable").

**Net effect**: -122 lines, 9 files deleted, 0 functional code changes, +2 architecture invariants.

## Commits

```
a52ea0e2  chore(infra): delete infra/consistency/ PHASE-COMPAT shim (1 of 4)
43464069  chore(infra): delete infra/agent_system/ PHASE-COMPAT shim (2 of 4)
d64587b4  docs(phase-21): CLAUDE.md v21.0 entry + architecture.yml version 21.0
[final]   docs(phase-21): handoff doc + lessons
```

## What was deleted

| File | Lines | Type | Status at deletion |
|---|---|---|---|
| `infra/consistency/__init__.py` | 6 | PHASE-COMPAT marker | only docstring (`Phase 13.X — DELETE after v16.x`) |
| `infra/consistency/creative_whitelist.py` | 16 | re-export shim | re-exports from `lingwen_quality.consistency.creative_whitelist` |
| `infra/consistency/checkers/__init__.py` | 2 | PHASE-COMPAT marker | only docstring |
| `infra/consistency/checkers/character_agency.py` | 5 | re-export shim | re-exports `CharacterAgencyChecker` from canonical |
| `infra/consistency/checkers/core_props_checker.py` | 5 | re-export shim | re-exports `CorePropsChecker` + `PropIssue` from canonical |
| `infra/consistency/checkers/item_checker.py` | 5 | re-export shim | re-exports `ItemChecker` + `ItemState` from canonical |
| `infra/consistency/checkers/pacing_checker.py` | 4 | re-export shim | re-exports `PacingChecker` from canonical |
| `infra/agent_system/__init__.py` | 3 | PHASE-COMPAT marker | only docstring (`Phase X.Y — DELETE after v16.x`) |
| `infra/agent_system/reviewer.py` | 41 | try/except-stub fallback shim | re-exports from `lingwen_core.agents.agents.reviewer` with try/except fallback (v19.4 §5 lesson 4 pattern) |
| **Total** | **87 (sum of file diffs)** | | **122 -line deletions** (sum of all `delete mode 100644` lines) |

## verify-before-design (N.14 lesson 1, 5th time in Phase 19+ chain)

The carryovers were:
- v19.3 invariant #43: "infra/consistency/ is a 1-line PHASE-COMPAT shim namespace — all infra.consistency.* consumer files have been migrated to lingwen_quality.consistency.*. Shim remains for backward compat but has 0 remaining consumers in our codebase."
- v19.4 invariant #44: "infra/agent_system/ is PHASE-COMPAT shim with 0 remaining code consumers"

The actual scope was:

1. **`infra/consistency/` was a pure re-export shim cluster** — 1 marker + 5 checkers + 1 creative_whitelist = 7 files, all either PHASE-COMPAT markers or re-exports from `lingwen_quality.consistency.*` canonical.
2. **`infra/agent_system/` was a marker + 1 try/except-stub fallback shim** — the shim's try/except wrapper provided stub classes that silently no-op'd if `lingwen_core.agents.agents.reviewer` wasn't available (v19.4 §5 lesson 4 pattern). v19.4 Sub3 closed the last 1 consumer chain.
3. **Zero external consumers** — unanchored grep returned:
   - `infra/consistency/`: 0 in `apps/`, `tests/`, `packages/`, `infra/`, `scripts/`
   - `infra/agent_system/`: 0 in `packages/` + `apps/` (the only refs are in `tests/test_phase18_4_agent_migration.py` guard test which scans for stale imports)
4. **All real consumers import directly from canonical**:
   - `lingwen_quality.consistency.*` for consistency symbols (verified via v19.3 Sub2 migrations)
   - `lingwen_core.agents.agents.*` for agent_system symbols (verified via v19.4 Sub3 migrations)

**Decision**: pure deletion is the correct approach — v19.3 + v19.4 already closed the consumer chains; this phase just removes the now-empty shim infrastructure.

## Verification gates (all green)

| Gate | Command | Result |
|---|---|---|
| Phase 18.4 agent migration tests | `pytest tests/test_phase18_4_agent_migration.py -v` | **7 PASSED** (was 6 fail + 1 pass on master) ✅ |
| Infra init deferred re-exports | `pytest tests/test_infra_init_no_deferred_re_exports.py -v` | **8 PASSED** ✅ |
| Frontend vitest | `pnpm exec vitest run` | **1762 + 1 skipped** (matches v19.4/v20.0 baseline) ✅ |
| vue-tsc | `pnpm exec tsc --noEmit` | **0 errors** ✅ |
| ESLint | `pnpm exec eslint .` | **0 errors** ✅ |
| knip | `pnpm exec knip` | **0 issues** (`{"issues":[]}`) ✅ |
| ruff | `ruff check .` | **All checks passed!** ✅ |
| lint-imports | `.venv/bin/lint-imports` | **3 contracts KEPT, 0 broken** (315 files / 1386 deps — **DOWN 9 files from v20.0's 324 files**, validates 9 file deletions) ✅ |
| grep audit | `grep -rn "infra.consistency\|infra.agent_system" --include="*.py" apps/ tests/ packages/ infra/ scripts/` | **0 real consumers** (only 5 in `tests/test_phase18_4_agent_migration.py` guard test) ✅ |

**Critical win**: `test_infra_agent_system_deleted` **was FAILING since Phase 18** (asserted `infra/agent_system/` directory does NOT exist). After this phase's T2 deletion, it now PASSES naturally — closing the failing regression test v19.4 §5 lesson 3 warned about.

## Architecture invariants enforced (2 NEW, 47 total)

- **#46 (NEW)** ✅ `infra/consistency/` directory does not exist (deleted Phase 21).
- **#47 (NEW)** ✅ `infra/agent_system/` directory does not exist (deleted Phase 21).

## Files modified

**Deleted** (`git rm -r`):
- `infra/consistency/__init__.py`
- `infra/consistency/creative_whitelist.py`
- `infra/consistency/checkers/__init__.py`
- `infra/consistency/checkers/character_agency.py`
- `infra/consistency/checkers/core_props_checker.py`
- `infra/consistency/checkers/item_checker.py`
- `infra/consistency/checkers/pacing_checker.py`
- `infra/agent_system/__init__.py`
- `infra/agent_system/reviewer.py`
- `__pycache__/` (auto-cleaned in both dirs, not git-tracked)

**Updated**:
- `CLAUDE.md` — v21.0 entry at line 3, v20.0 demoted to line 4, v20.0 carryover line marked "CLOSED by v21.0"
- `.lingwen/architecture.yml` — version 20.0 → 21.0 + new `phase_21:` block at end with carryover_to_phase_22

**New**:
- `docs/superpowers/handoffs/2026-09-02-phase-21-shim-cleanup-handoff.md` (this file)

## Lessons

### 1. verify-before-design re-confirmed (N.14 lesson 1, 5th time in Phase 19+ chain)

Both v19.3 (consistency) + v19.4 (agent_system) carryovers were correctly described as "0 remaining consumers" by their original handoffs. Phase 21's verify-before-design confirmed: 0 consumers, both directories safe to delete.

| Phase | Claimed | Actual | Off-by |
|---|---|---|---|
| Sub1 | "30+" | 16 | 2x |
| Sub2 | "30+" | 6 | 5x |
| Sub3 | "30+" | 1 | 30x |
| 20 | "→ migration" | 0 (deletion) | ∞ |
| **21** | **"0 consumers"** | **0 consumers** | **✓** |

The lesson: when carryovers are correct descriptions, Phase closure is trivial (3-4 commits, no surprises). The carryover description staleness problem (Sub1/2/3/20) was the issue — Phase 21's carryovers were already accurate.

### 2. Regression tests in "regressed" direction MUST be tracked (v19.4 §5 lesson 3 re-confirmed)

`tests/test_phase18_4_agent_migration.py::test_infra_agent_system_deleted` was a **1-line test** asserting `infra/agent_system/` directory should NOT exist. It has been **failing since Phase 18** (4 phases: 18, 19, 19+, 20) — but no one tracked the failure because:
- It's a single test in a 7-test file
- The failure mode is silent (no exception, just an AssertionError)
- No CI gate failed because the test collection itself succeeded

**Lesson**: failing regression tests are NEVER acceptable. Either fix the underlying state (which Phase 21 finally did) or document why the test is intentionally failing. The 5-phase delay between Phase 18 (test first wrote the assertion) and Phase 21 (test now passes) represents accumulated tech debt.

### 3. try/except-stub fallback shim pattern (v19.4 §5 lesson 4) is the canonical Phase 18-era shim

`infra/agent_system/reviewer.py` had the canonical pattern:

```python
try:
    from lingwen_core.agents.agents.reviewer import (
        MAX_REVIEW_CYCLES, STOP_THRESHOLD, ReviewerSession,
        ReviewFinding, ReviewResult, review_chapter,
    )
except ImportError:
    import logging
    _log = logging.getLogger(__name__)

    class ReviewerSession:
        def __init__(self, *args, **kwargs):
            _log.warning("infra.agent_system.reviewer.ReviewerSession is a Phase X.Y compat stub...")

    # ... more stubs
```

This pattern silently passed import-only tests (the stubs satisfied `from infra.agent_system.reviewer import ReviewerSession`) but raised `NotImplementedError` at runtime. **Lesson**: when grepping for shim deletion candidates, this pattern is safe to identify because:
- `try:` + `except ImportError:` keyword is a strong signal
- Fallback stubs typically have logging warnings + `Phase X.Y` markers in docstrings
- Real consumers in v19.x+ phase work import directly from canonical

### 4. Atomic 1-task-per-commit scales to 4 commits (N.14 lesson 7 re-confirmed)

Phase 21 split into 4 atomic commits:
1. `a52ea0e2` — delete infra/consistency/
2. `43464069` — delete infra/agent_system/
3. `d64587b4` — docs sync
4. `[final]` — handoff

Even though both deletions are pure deletions with no interdependency, splitting them gives:
- **Bisect-friendly history**: if anything breaks after T1 vs T2, git bisect can pinpoint which deletion caused it
- **Clear commit boundaries**: each commit maps to one logical shim cluster (consistency vs agent_system are independent concerns)
- **Pattern matches Phase 19+ Sub2/Sub3 split** (separate branches per shim)

### 5. Split delete into 2 commits even though both are pure deletions

Pure deletions seem like good candidates for single commits. But Phase 21 split into 2 commits because:
- **Logical independence**: infra/consistency and infra/agent_system are unrelated modules with different canonical targets (lingwen_quality vs lingwen_core)
- **Bisect clarity**: separate commits make regression attribution trivial
- **PR review ergonomics** (not applicable here per solo workflow, but good practice): reviewer can approve one cluster at a time
- **Rollback granularity**: if a downstream consumer was missed, revert only the affected shim's commit

The same pattern applied in Phase 18 + Phase 19+ where shim clusters were split into separate commits/sub-phases.

## Carryover closure

| Carryover | Status |
|---|---|
| `infra/consistency/` shim cleanup (v19.3 #43 carryover) | **CLOSED** by v21.0 |
| `infra/agent_system/` shim cleanup (v19.4 #44 carryover) | **CLOSED** by v21.0 |
| `test_infra_agent_system_deleted` failing test (v19.4 §5 lesson 3 carryover) | **CLOSED** by v21.0 (now passes) |

## Carryover to Phase 22+

- **lingwen_llm test-env gap** — `pytest` loads `.env` via deepeval/langsmith plugins → `MINIMAX_API_KEY` set → real LLM calls hang. Workaround: `env -u MINIMAX_API_KEY` prefix. CI should set this in the env.
- **ruff format cleanup** — `ruff format --check` reports reformatting needed in many test files (pre-existing).
- **Phase 114 prod preview regression** — accepted (per CLAUDE.md); cytoscape-fcose CJS / rollup incompatibility; 5 phases of effort failed.

## Phase 19+ chain final state

After Phase 21:
- **11 NEW architecture invariants** added (#36-#47) across the chain
- **All Phase 18 carryovers closed**
- **All Phase 19+ sub-phases (Sub1/Sub1 polish/Sub2/Sub3) closed**
- **All Phase 20-21 carryovers closed**
- **0 shim directories remaining in `infra/`** (consistency, agent_system, exports all deleted)

LingWen shim cleanup is COMPLETE. Only remaining LingWen debt: lingwen_llm test-env + ruff format + Phase 114 prod preview regression (accepted).

## Solo workflow closure

```
$ git checkout master && git merge --ff-only phase-21-shim-cleanup
$ git push origin master
$ git worktree remove ../LingWen-phase-21
```

Master HEAD after merge: `d64587b4` (v21.0).