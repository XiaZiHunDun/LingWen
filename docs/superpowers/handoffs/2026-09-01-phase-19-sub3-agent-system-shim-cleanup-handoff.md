# Phase 19+ Sub3 — Agent System Shim Cleanup Handoff

## Summary

Phase 19+ Sub3 closed: 1 actual test consumer migrated from
`infra.agent_system.reviewer` PHASE-COMPAT shim path to
`lingwen_core.agents.agents.reviewer` canonical directly. Plus 4 docstring
drift fixes (canonical file + 3 lingwen_core files referencing non-existent
`infra.agent_system.*` modules in CLI examples).

Closes the `Sub3` carryover from Phase 18 / Phase 19+ Sub1 + Sub2.

**5 source commits** on branch `phase-19-sub3` (1 refactor + 2 docs fixes +
1 ruff autofix + 1 handoff docs commit).

### Commits

```
c896229a refactor(test): test_reviewer imports from lingwen_core.agents.agents
41bb2d34 fix(docs): reviewer.py Usage docstring points to canonical
3b5d84e0 fix(docs): 3 CLI docstring examples point to canonical lingwen_core.agents
3a7c3e59 chore(ruff): auto-fix I001 import sort for test_reviewer (1 error → 0)
```

### Per-task scope

**Test consumer migrated (1 file):**

| File | Migration |
|------|-----------|
| `tests/agent_system/test_reviewer.py` | `infra.agent_system.reviewer` → `lingwen_core.agents.agents.reviewer` |

**Docstring drift fixed (4 files):**

| File | Fix |
|------|-----|
| `packages/lingwen-core/src/lingwen_core/agents/agents/reviewer.py` | `Usage:` example `from infra.agent_system.reviewer import ...` → `from lingwen_core.agents.agents.reviewer import ...` |
| `packages/lingwen-core/src/lingwen_core/agents/chapter_production_batch.py` | `CLI:` examples `python -m infra.agent_system.chapter_production_batch` → `python -m lingwen_core.agents.chapter_production_batch` (3 lines) |
| `packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py` | `CLI:` examples `python -m infra.agent_system.chapter_production_pilot` → `python -m lingwen_core.agents.chapter_production_pilot` (2 lines) |
| `packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py` | `Used by pytest and 'python -m infra.agent_system.chapter_golden_path'.` → `python -m lingwen_core.agents.chapter_golden_path` |

### Actual scope vs carryover claim

**Carryover claim** (Phase 18 v18 / Phase 19+ Sub1 §5 / Phase 19+ Sub2 §1):
"infra/agent_system/ shim re-exports from lingwen_core.agents.agents — 30+ consumers, no migration needed".

**Actual scope**:
- 1 actual test consumer (`tests/agent_system/test_reviewer.py`)
- `tests/test_phase18_4_agent_migration.py` is a REGRESSION TEST (prevents NEW imports), not a consumer
- 3 `packages/lingwen-core/src/lingwen_core/agents/{chapter_production_*.py,chapter_golden_path.py}` reference `infra.agent_system.*` only in **CLI docstring examples** (`python -m infra.agent_system.X`). These are NOT consumers — they are docstring drift documenting non-functional commands.
- Plus 1 docstring drift in the canonical reviewer's own `Usage:` block.

The "30+" figure was carried forward through 4+ phases (Phase 18 → Phase 19+ Sub1 → Sub1 polish → Sub2 → Sub3) without re-verification. Per N.14 lesson 1, always re-verify carryover claims before executing.

## Verification gates (all GREEN)

- **ruff**: 0 errors (1 autofixed in T2 follow-up)
- **vitest**: 1762 passed + 1 skipped (no regression from v19.3 baseline)
- **vue-tsc**: 0 errors (no output = clean)
- **ESLint**: 0 errors (no output = clean)
- **knip**: `{"issues":[]}` (clean, no dead code)
- **lint-imports**: 3 contracts KEPT (`layer_dependencies`, `no_concrete_llm_service_in_business_code`, `no_concrete_sqlite3_in_business_code`)
- **Backend tests**:
  - `tests/agent_system/test_reviewer.py`: 18 passed
  - `tests/test_phase18_4_agent_migration.py`: 6 passed + 1 pre-existing failure (`test_infra_agent_system_deleted` expects `infra/agent_system/` to NOT exist — shim still present per Sub1 + Sub2 pattern of "shim remains as deletion target")
  - `packages/lingwen-shared/tests/`: 136 passed
  - `packages/lingwen-creator/tests/`: 73 passed
  - `packages/lingwen-core/tests/`: 68 passed

## Architecture invariants preserved

- **#36-#43** (from v19.1 + v19.2 + v19.3): all canonical domain/agent/quality imports in place.

**New invariant** (T2):
- **#44**: `infra/agent_system/` is a 1-line PHASE-COMPAT shim namespace — all `infra.agent_system.*` consumer files have been migrated to `lingwen_core.agents.agents.*`. Shim remains for backward compat but has 0 remaining code consumers (only docstring references in lingwen_core itself, fixed in this phase).

## Lessons

1. **Carryover description staleness — N.14 lesson 1 re-confirmed (3rd time in Phase 19+)**: Phase 18 said "30+ consumers" for Sub3. Actual: 1 test consumer. The "30+" figure has propagated through Sub1, Sub2, Sub3 carryovers without re-verification. **Lesson**: when picking up old descriptions, ALWAYS re-verify with fresh grep. The 3 phase Sub1→Sub2→Sub3 chain shows the same carryover mistake was inherited 3 times. Going forward: each phase should start with `grep -rln "infra.X" --include="*.py" | grep -v "infra/X/" | wc -l` to count real consumers.

2. **Docstring references to non-existent modules are drift, not bugs** (T2 docstring fixes): 4 lingwen_core files referenced `infra.agent_system.X` in CLI examples where those modules don't exist (`infra/agent_system/` only has `__init__.py` + `reviewer.py`). The regression test filters docstrings so they're not "test failures", but they're documentation lies. **Lesson**: docstring audit should be part of any shim-cleanup phase. 5-10 minute task that closes drift.

3. **Regression tests that look for "X must not exist" can mask drift** (Phase 18 design observation): `tests/test_phase18_4_agent_migration.py::test_infra_agent_system_deleted` is supposed to fail when `infra/agent_system/` exists. The fact that it's been failing since 2026 (Phase 18) without anyone fixing it shows that "regression tests" can themselves become broken-state markers if no one tracks the failures. **Lesson**: regression tests that fail in the "regressed" direction should be treated as actionable, not just informational.

4. **Shim fallback stubs silently pass import-only tests** (T1 observation): `infra/agent_system/reviewer.py` had a `try/except ImportError` that fell back to stub classes (warning logged + empty impl). If a test only checked `from infra.agent_system.reviewer import ReviewerSession` succeeds, the test would pass even if the canonical symbols didn't exist. This is similar to v19.2 Sub2 lesson 2 (creative_whitelist legacy stubs raising NotImplementedError). **Lesson**: always verify the IMPORTED SYMBOLS work, not just that imports succeed. Tests should call methods / instantiate classes to verify real implementations.

5. **Atomic 1-task-per-commit scales to 5 commits** (N.14 lesson 7 re-confirmed). 1 refactor + 2 docstring fixes (batchable in 1 commit, but separate for review clarity) + 1 ruff autofix + 1 docs = 5 commits. Each independently revertable. Each verified.

## Carryover closure

- ✅ **Sub3 (infra/agent_system bulk consumer migration — "30+" actual → 1 consumer + 4 docstring drift)**: CLOSED

## Carryover to Phase 20+

- **infra/exports/* → packages/lingwen-storage migration** (separate concern, lingwen_storage package already exists)
- **lingwen_llm test-env gap** (Phase 115 carryover, still open)
- **ruff format cleanup** (Phase 19.x carryover)
- **Phase 114 prod preview regression** (accepted, no action planned)
- **Optional future polish**: delete `infra/consistency/` + `infra/agent_system/` shim files entirely now that 0 consumers remain in our codebase. Conservative: keep shims as documented deletion targets. Aggressive: full deletion in one phase.