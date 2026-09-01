# Phase 126 v16.5 #N.16 — v15.7.1 Debt Closure Handoff

**Date**: 2026-09-01
**Branch**: `phase-126-v16-5-n16`
**Commits**: 4 source commits + 1 docs/handoff commit (`c3b9d214` + `a6faa527` + `a75a61ec` + `bd0dd4a9` + docs commit)
**Scope**: 4 source commits + 1 handoff commit

## Summary

Closed the 2 remaining v15.7.1 carryover items as a hardening mini-phase. Both items were largely documentation debt + inert bugs:

| Item | Reality | Action |
|------|---------|--------|
| `lingwen_quality` "missing" | Package EXISTS at `packages/lingwen-quality/` (100+ files). "15 failing tests" claim was stale from v15.7.1 baseline; Phase 126 sub-phases (N.7/8/9/10/11) progressively fixed it. | Added CI regression guard at `tooling/hygiene/check_lingwen_quality_importable.py` + 3 regression tests. |
| `plugin_manager.py` module path bug | Real bug at lines 58 + 81 (used `infra.ai_service.X` instead of canonical `lingwen_llm.providers.X`). Phase 123 fix bypassed it via `_PROVIDER_REGISTRY` decorator path. | 2-line module path correction + RED regression test now GREEN. 3-warning log spam on every `LLMService.get()` eliminated. |

## Investigation findings (carryover claims)

The "15 failing tests" count from v15.7.1 baseline was carried forward through multiple Phase 126 sub-phases. Static analysis (code-explorer subagent) revealed:
- Only 2 `tests/infra/` files import `lingwen_quality` symbols
- Both files SHOULD pass with the existing package
- The "13 other tests" no longer exist as failing (fixed in transit through N.7/8/9/10/11)

The plugin_manager bug was INERT (bypassed by Phase 123 fix) but emitted 3 warnings per LLMService init. Now both branches correctly use the canonical module path.

## Architecture invariants enforced (2 NEW, 35 total)

35. (NEW) ✅ `lingwen_quality` key symbols (`IssueSeverity`, `ConsistencyEngine`, `CheckerInspector`, `ForeshadowChecker`, `CreativeWhitelist`, etc.) are importable from canonical modules — verified by `tooling/hygiene/check_lingwen_quality_importable.py`. CI regression guard fails if symbols disappear.

36. (NEW) ✅ `plugin_manager.py` `_discover_internal_providers` (lines 58, 81) uses canonical `lingwen_llm.providers.X` module path. Regression test `tests/infra/test_plugin_manager.py` verifies all 3 providers load + no broken-import warnings.

## Verification (worktree HEAD)

- vitest: 1762 passed + 1 skipped (no regression)
- vue-tsc: 0 errors
- ESLint: 0 errors
- knip: `{"issues":[]}`
- shared pytest: 136 passed
- creator pkg pytest: 73 passed
- lingwen-llm pytest: 11 passed (3 NEW + pre-existing)
- infra pytest: 3 NEW passed (T3 RED → T4 GREEN)
- hygiene pytest: 3 NEW passed
- import-linter: 3 contracts KEPT

## Lessons

1. **Verify carryover claims before executing** — The "15 failing tests" claim was inherited from v15.7.1 baseline and propagated through 4+ phases of CLAUDE.md updates. Static analysis revealed it was already stale. Lesson: when picking up old carryover, verify the underlying claim first.

2. **CI regression guards beat CLAUDE.md text edits** — Adding `check_lingwen_quality_importable.py` means future package moves will surface as CI failures, not silent CLAUDE.md drift. The doc edit alone (without the guard) would let the "missing" claim re-emerge if someone moved the package.

3. **Phase 123 fix-by-bypass was the right intermediate step** — The `_PROVIDER_REGISTRY` decorator path bypassed the broken `_discover_internal_providers` without touching it. Now both layers are correct (decorator path is canonical, _discover_internal_providers also works). Two correct paths > one broken + one bypass.

4. **Conservative fix > aggressive cleanup for inert bugs** — Could have deleted `_discover_internal_providers` entirely (it duplicates what decorators do). Instead chose 2-line path fix: preserves code structure, lower risk, same end result.

## Out of carryover (post-closure)

After this mini-phase, remaining LingWen debt items:
- **Prod preview regression** (Phase 114 accepted, cytoscape-fcose incompatibility)

The v15.7.1 carryover chain closes here.

## Reference

- Design: `docs/superpowers/specs/2026-09-01-phase-126-v16-5-n16-v15-7-1-debt-closure-design.md`
- Plan: `docs/superpowers/plans/2026-09-01-phase-126-v16-5-n16-v15-7-1-debt-closure.md`
- Investigation: code-explorer subagent 2026-09-01