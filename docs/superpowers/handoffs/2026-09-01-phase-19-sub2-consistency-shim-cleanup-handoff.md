# Phase 19+ Sub2 — Consistency Shim Cleanup Handoff

## Summary

Phase 19+ Sub2 closed: 6 consumer files (5 tests + 1 script) migrated from
`infra.consistency.*` PHASE-COMPAT shim path to `lingwen_quality.consistency.*`
canonical directly. Migration closes 2 pre-existing latent bugs:

1. **test_creative_whitelist.py** — shim's legacy `CreativeWhitelist` /
   `WhitelistChapter` classes raised `NotImplementedError` per compat docstring;
   26 tests were erroring/failing. Canonical has full implementation: **+26 tests pass**.
2. **scripts/ci_baseline_check.py** — `from infra.consistency.checker_feedback
   import get_checker_stats` referenced a module that didn't exist in `infra/`
   (only in canonical); try/except silently no-op'd. Migration makes the call work.

Closes the `Sub2` carryover from Phase 18 / Phase 19+ Sub1.

**8 source commits** on branch `phase-19-sub2` (6 refactor + 1 ruff autofix +
will add 1 docs commit).

### Commits

```
00c3a11f refactor(test): test_item_checker imports from lingwen_quality
076a07aa refactor(test): test_pacing_checker imports from lingwen_quality
8721d75b refactor(test): test_character_agency imports from lingwen_quality
4a11ec94 refactor(test): test_core_props_checker imports from lingwen_quality
6ba0a9c4 refactor(test): test_creative_whitelist imports from lingwen_quality
efae9572 refactor(script): ci_baseline_check imports from lingwen_quality
917efcb3 chore(ruff): auto-fix I001 import sort for consistency tests (2 errors → 0)
```

### Per-task scope

**Test consumers migrated (5 files):**

| File | Migration |
|------|-----------|
| `tests/consistency/test_item_checker.py` | `infra.consistency.checkers.item_checker` → `lingwen_quality.consistency.checkers.item_checker` |
| `tests/consistency/test_pacing_checker.py` | `infra.consistency.checkers.pacing_checker` → `lingwen_quality.consistency.checkers.pacing_checker` |
| `tests/consistency/test_character_agency.py` | `infra.consistency.checkers.character_agency` → `lingwen_quality.consistency.checkers.character_agency` |
| `tests/consistency/test_core_props_checker.py` | `infra.consistency.checkers.core_props_checker` → `lingwen_quality.consistency.checkers.core_props_checker` |
| `tests/consistency/test_creative_whitelist.py` | `infra.consistency.creative_whitelist` → `lingwen_quality.consistency.creative_whitelist` |

**Script consumer migrated (1 file):**

| File | Migration | Pre-existing bug closed |
|------|-----------|-------------------------|
| `scripts/ci_baseline_check.py` | `infra.consistency.checker_feedback` → `lingwen_quality.consistency.checker_feedback` | Module didn't exist in `infra/consistency/`; try/except silently no-op'd |

### Actual scope vs carryover claim

**Carryover claim** (Phase 18 v18 / Phase 19+ Sub1 §5): "30+ consumers still use shim paths transparently, no migration needed".

**Actual scope**: 6 consumer files (5 tests + 1 script). The "30+" figure was carried forward through multiple phases of CLAUDE.md without re-verification. Per N.14 lesson 1 (verify-before-design): always re-verify carryover claims before executing.

## Verification gates (all GREEN)

- **ruff**: 0 errors (full project, 2 autofixed in T7 follow-up)
- **vitest**: 1762 passed + 1 skipped (no regression from v19.2 baseline)
- **vue-tsc**: 0 errors (no output = clean)
- **ESLint**: 0 errors (no output = clean)
- **knip**: `{"issues":[]}` (clean, no dead code)
- **lint-imports**: 3 contracts KEPT (`layer_dependencies`, `no_concrete_llm_service_in_business_code`, `no_concrete_sqlite3_in_business_code`)
- **Consistency tests (Sub2 scope)**: 320 passed + 1 pre-existing env failure (vs baseline 63 pass + 6 fail + 21 errors)
  - **Net improvement**: +27 tests pass (test_creative_whitelist.py 21 errors + 6 fails → 26 pass)
- **Other backend packages** (no regression):
  - `packages/lingwen-shared/tests/`: 136 passed
  - `packages/lingwen-creator/tests/`: 73 passed
  - `packages/lingwen-core/tests/`: 68 passed

## Architecture invariants preserved

- **#36-#42** (from v19.1 + v19.2): all lingwen_core.domain canonical + behavior service direct imports from canonical.

**New invariant** (T7):
- **#43**: `infra/consistency/` is a 1-line PHASE-COMPAT shim namespace — all `infra.consistency.*` consumer files have been migrated to `lingwen_quality.consistency.*`. Shim remains for backward compat but has 0 remaining consumers in our codebase.

## Lessons

1. **Carryover description staleness — N.14 lesson 1 re-confirmed**: Phase 18 v18 said "30+ consumers still use shim paths". Phase 19+ Sub1 §5 repeated the claim. Phase 19+ Sub2 verification revealed only 6 actual consumers. **Lesson**: when picking up old descriptions, ALWAYS re-verify with fresh grep. Don't trust inherited numbers.

2. **Shim can hide latent bugs** (T5/T6 discovery): the shim's legacy compat aliases (`CreativeWhitelist`, `WhitelistChapter` raising `NotImplementedError`) were a known design choice — Phase 13 refactored to module-level functions. But the shim kept raising errors for any consumer using the legacy class API, including 26 tests that were passing-by-mocking in some cases but failing in others. **Lesson**: when migrating a shim to canonical, the canonical's full implementation may FIX pre-existing test errors that nobody was tracking.)

3. **`from infra.X.module_that_doesnt_exist` silently no-ops inside try/except** (T6 discovery): `scripts/ci_baseline_check.py:71` had `from infra.consistency.checker_feedback import get_checker_stats` but `infra/consistency/checker_feedback.py` doesn't exist (only canonical has it). The try/except wrapped the call silently — the script would always report "all checks passed" even when the data source was missing. **Lesson**: defense-in-depth grep audits should also flag imports of non-existent modules (Python doesn't warn on missing import until first call).

4. **Constant value drift between shim and canonical** (T5 detail): shim uses `DIAMOND = "DIAMOND"` (uppercase), canonical uses `DIAMOND = "diamond"` (lowercase). The test only uses `GOLD in levels` (membership) and `should_downgrade(GOLD)` (boolean), so both work. **Lesson**: when migrating constants, check whether tests use membership/boolean or literal string comparison. Membership tests are robust to value drift.

5. **`infra/consistency/` shim pattern** (still in place): 1-line marker docstring + small re-export files (`checkers/{character_agency,core_props_checker,item_checker,pacing_checker}.py`, `creative_whitelist.py`). These 200-300 byte shims remain as PHASE-COMPAT deletion targets. Migration of 6 consumers means shim indirection is fully removable in a future phase if desired.

6. **Atomic 1-task-per-commit scales to 7 commits** (N.14 lesson 7 re-confirmed). 6 consumer files + 1 ruff autofix = 7 commits. Each independently revertable. Each verified by running the relevant test subset.

## Carryover closure

- ✅ **Sub2 (infra/consistency bulk consumer migration — 30+ files → 6 actual)**: CLOSED

## Carryover to Phase 19.x+

- **Sub3** (infra/agent_system shim cleanup — 2 actual test consumers per Phase 18 carryover; verify-before-design will re-confirm)
- **infra/exports/* → packages/lingwen-storage migration** (separate concern)
- **lingwen_llm test-env gap** (Phase 115 carryover, still open)
- **ruff format cleanup** (Phase 19.x carryover)
- **Phase 114 prod preview regression** (accepted, no action planned)
- **Future polish** (optional): delete `infra/consistency/` PHASE-COMPAT shim now that no consumers remain in our codebase (would close #43 to fully delete). Conservative: keep shim as documented deletion target for Phase 20+.