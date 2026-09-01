# Phase 126 v16.5 #N.16 — v15.7.1 Debt Closure Design

**Date**: 2026-09-01
**Status**: Approved
**Phase**: 126 v16.5 #N.16
**Estimated scope**: 5 commits, 3-4 hours

## Goal

Close the 2 remaining v15.7.1 carryover items as a small mini-phase, bringing LingWen to a true zero-carryover state. No new architecture changes, no behavior changes — pure hardening.

## Background

Two carryover items have been documented across multiple Phase 126 sub-phases as "v15.7.1 debt":

1. **`lingwen_quality` module missing** (alleged to affect 15 `tests/infra/` tests)
2. **`plugin_manager.py:_discover_internal_providers` wrong module path bug**

Investigation (via code-explorer subagent, 2026-09-01) revealed both items are largely **documentation debt**:

- The `lingwen_quality` package EXISTS at `packages/lingwen-quality/` (100+ files). The "missing" framing is stale from v15.7.1 baseline; Phase 126 sub-phases (N.7/8/9/10/11) progressively fixed the originally-failing tests through shim consolidation. The "15 failing tests" count is no longer accurate.
- The `plugin_manager.py` bug is REAL (`infra.ai_service.X` instead of `lingwen_llm.providers.X`) but INERT — Phase 123 fix bypassed it via `_PROVIDER_REGISTRY` decorator path. Every `LLMService.get()` logs 3 warnings but providers load via the canonical decorator path.

## Scope

### Task 1: `lingwen_quality` hardening (mostly docs sync)

The package exists and works. Real actions:
- Verify the 2 affected `tests/infra/` files actually pass in default env (no evidence of failure)
- Add CI regression guard so the "missing" claim can't recur
- Update CLAUDE.md / MEMORY.md to remove stale "missing" framing

### Task 2: `plugin_manager.py` bug fix (real but inert)

File: `packages/lingwen-llm/src/lingwen_llm/providers/plugin_manager.py`
- Lines 58 + 81: replace `f"infra.ai_service.{module_name}"` → `f"lingwen_llm.providers.{module_name}"` (both branches)
- Add regression test asserting `PluginManager().load_plugins()` populates `_plugins` with 3 providers

No public API change. `_PROVIDER_REGISTRY` decorator path remains canonical.

## Architecture / Components

### Task 1 — CI regression guard

- **NEW** `tooling/hygiene/check_lingwen_quality_importable.py`
  - Asserts key symbols are importable from `lingwen_quality.*`:
    - `IssueSeverity`, `Issue`, `IssueLocation`, `CheckerType`
    - `ConsistencyEngine`, `ConsistencyArbitrator`
    - `CheckerInspector`, `ForeshadowChecker`, `PacingChecker`
    - `SceneTransitionChecker`, `DialogueAuthenticityChecker`
    - `CreativeWhitelist`
  - Pattern: try/except for each symbol, fail loudly if missing
  - Module-level guard (no pytest dependency) — exits non-zero on failure

- **NEW** `tests/hygiene/test_check_lingwen_quality_importable.py`
  - 3 regression tests:
    1. `test_check_script_exists` — file exists at expected path
    2. `test_check_script_returns_zero_when_all_symbols_importable` — subprocess run returns 0
    3. `test_check_script_fails_when_symbol_missing` — mock via `sys.modules` injection, verify exit code 1

- **Placement rationale**: matches existing `check_no_concrete_*` pattern in `tooling/hygiene/` (DP-02/DP-03 hygiene tests)

### Task 2 — Plugin manager fix

- **MODIFY** `packages/lingwen-llm/src/lingwen_llm/providers/plugin_manager.py:58,81`
  - Line 58: `module_path = f"infra.ai_service.{module_name}"` → `module_path = f"lingwen_llm.providers.{module_name}"`
  - Line 81: `module_path = f"infra.ai_service.providers.{module_name}"` → `module_path = f"lingwen_llm.providers.{module_name}"` (same target — both branches target the canonical providers directory)
  - Verify both branches still iterate `os.listdir(ai_service_dir)` correctly

- **NEW** `tests/infra/test_plugin_manager.py`
  - Regression test: `PluginManager().load_plugins()` populates `_plugins` with 3 providers (minimax, anthropic, openai)
  - Verify no `warnings.warn` calls emitted (captured via `pytest.warns(None)` or `caplog`)
  - Verify each provider is the actual class (not just a string)

## Error Handling
- Both fixes are pure hardening — no runtime behavior changes
- Task 1 CI guard fails CI immediately if symbols disappear (preventive)
- Task 2 fix ELIMINATES the 3 warnings logged per LLMService init (silent improvement, side effect)

## Testing

| Layer | Test | Purpose |
|-------|------|---------|
| Task 1 | NEW `tests/hygiene/test_check_lingwen_quality_importable.py` (3 tests) | Verify CI guard runs and asserts symbols present |
| Task 1 | Existing `packages/lingwen-quality/tests/test_quality_import.py` | Already exists, verifies package import (no change needed) |
| Task 1 | Existing `tests/infra/test_check_fail_severity.py` + `tests/infra/test_full_check_report.py` | Verify they actually pass in default env |
| Task 2 | NEW `tests/infra/test_plugin_manager.py` | Regression: `PluginManager().load_plugins()` populates `_plugins` correctly |
| Task 2 | Existing `tests/infra/test_llm_service.py` (3 tests) | Phase 123 fix regression guard — must still pass |
| Task 2 | Existing `packages/lingwen-llm/tests/` | Full lingwen-llm test suite must pass |

## Out of Scope

- Touching `infra/consistency/*` shims (Phase 125 back-compat, still wired by callers)
- Deleting `_discover_internal_providers` or `discover_and_register` (conservative path fix preserves structure; aggressive cleanup is future)
- Any refactor of `plugin_manager.py` beyond 2-line path change
- Touching `lingwen_quality` package internals
- Refactoring `apps/dashboard` or any frontend code
- DTO schema audit (separate phase)

## Commit Plan (atomic 1-task-per-commit)

| # | Commit message | Type | Description |
|---|----------------|------|-------------|
| 1 | `test(hygiene): add check_lingwen_quality_importable CI guard` | T1 CI guard | Add `tooling/hygiene/check_lingwen_quality_importable.py` + 3 regression tests |
| 2 | `docs: update CLAUDE.md to mark lingwen_quality as verified + guarded` | T1 docs sync | Remove "lingwen_quality module missing" line, add "verified + guarded" note |
| 3 | `test(llm): add plugin_manager regression test (initially failing)` | T2 RED | Add `tests/infra/test_plugin_manager.py` — proves current bug |
| 4 | `fix(llm): correct plugin_manager module path (lines 58,81)` | T2 GREEN | Replace `infra.ai_service.X` → `lingwen_llm.providers.X` |
| 5 | `docs: update CLAUDE.md to mark v15.7.1 debt as closed + MEMORY.md` | T2 docs sync | Remove plugin_manager carryover; update MEMORY.md carryover list |

Total: 5 commits, ~3-4 hours.

## Verification Gates (must pass after each commit)

- `cd apps/dashboard && pnpm vitest run` — 1762 passed (no regression)
- `/home/ailearn/miniconda3/bin/python -m pytest packages/lingwen-shared/tests packages/lingwen-creator/tests packages/lingwen-llm/tests tests/infra/` — all pass
- `cd apps/dashboard && pnpm exec knip` — `{"issues":[]}`
- `cd apps/dashboard && pnpm tsc --noEmit` — 0 errors
- `cd apps/dashboard && pnpm eslint .` — 0 errors
- `lint-imports` — 3 contracts KEPT
- **NEW (Task 1)**: `python tooling/hygiene/check_lingwen_quality_importable.py` exits 0
- **NEW (Task 2)**: `tests/infra/test_plugin_manager.py` passes after GREEN commit

## Risks

**Low.** Both fixes are pure hardening.
- Task 1: pure addition (CI guard + docs sync). No code changes to existing paths.
- Task 2: 2-line module path replacement. The replacement path `lingwen_llm.providers` is the EXACT same path the decorators use (per `packages/lingwen-llm/src/lingwen_llm/providers/__init__.py:16-20`), so behavior converges to canonical.

**Known gotcha (per MEMORY.md)**: Worktree pytest verification may need `uv sync --all-packages` + use worktree's `.venv/bin/python` (NOT conda's `/home/ailearn/miniconda3/bin/python`). The conda python's stale PYTHONPATH can cause `ModuleNotFoundError` for worktree-specific workspace members.

## Carryover (post-closure)

After this mini-phase, the remaining LingWen debt items would be:
- **Prod preview regression** (Phase 114 accepted, cytoscape-fcose incompatibility with rollup commonjs) — 5+ phases invested, accepted as-is
- Any new findings from post-closure work

The v15.7.1 carryover chain closes here.

## Lessons to Capture (forward-looking)

If the mini-phase proceeds as designed:
1. **Docs debt persists even after code debt closes** — the "lingwen_quality missing" framing was stale but unquestioned for 4+ phases. Lesson: when picking up old carryover, verify the underlying claim first.
2. **CI regression guards prevent doc debt re-emergence** — adding `check_lingwen_quality_importable.py` means a future package move will fail CI, not just CLAUDE.md text drift.
3. **Phase 123 fix-by-bypass worked** — `_PROVIDER_REGISTRY` decorator path was added to bypass the broken `_discover_internal_providers` without touching the buggy code. The "real fix" is closing the bypass by also fixing the original code. Both layers preserved = robust.