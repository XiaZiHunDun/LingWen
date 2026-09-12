# Phase 53b tools/ Legacy Cleanup — Handoff

> **Date**: 2026-09-12
> **Branch**: phase-57-p3-archdebt-reading-power (continuing from Phase 58)
> **Version**: v53.1 → v53.2
> **Triggered by**: Post-Phase-58 baseline check (`pytest tests/tools/`) — 9 failed + 1 pre-existing

## TL;DR

Phase 53b closes 9 pre-existing test failures + 1 broken shim + 1 silent
production bug. All were variants of "Phase 5 LLM_QUALITY split (1138L →
5+1 file subpackage) did not finish updating downstream consumers". 5
atomic commits; 9/9 fixable tests now pass; 11 regression guards added;
1 broken shim repaired; 1 production import migrated.

## Validation

| Gate | Before | After |
|------|--------|-------|
| `pytest tests/tools/` | 9 failed + 1 pre-existing (10 total) | **128 passed** + 1 pre-existing known |
| `from tools.llm_quality_deep_check import LLMQualityChecker, QualityReport, main` | ❌ ImportError (LLMService missing) | ✅ exit 0 |
| `from tools.llm_quality import LLMQualityChecker` | ✅ exit 0 | ✅ exit 0 (unchanged) |
| `from packages.lingwen_cli.commands.check import ...` | ❌ would fail at runtime | ✅ exit 0 |
| `grep -rln "tools\.llm_quality_deep_check" --include="*.py" packages/ apps/` | 1 site | **0 sites** |
| `pytest tests/test_phase53b_tools_legacy.py` | n/a | **11/11 passed** |

## Root causes

| # | Class | Files | Was | Now |
|---|-------|-------|-----|-----|
| 1 | Broken shim | `tools/llm_quality_deep_check.py:28` | `from tools.llm_quality import LLMService` — but LLMService doesn't exist (renamed to LLMServiceAdapter) | shim now imports only the 3 valid symbols |
| 2 | Stale test patch | `tests/tools/test_llm_quality_deep_check.py` (8 tests) | `patch("tools.llm_quality_deep_check.LLMService")` on a non-existent symbol | constructor injection: `LLMQualityChecker(llm_service=mock)` |
| 3 | Production stale import | `packages/lingwen-cli/.../check.py:167` | `from tools.llm_quality_deep_check import LLMQualityChecker` | `from tools.llm_quality import LLMQualityChecker` |
| 4 | Fixture bug | `tests/tools/test_llm_quality_deep_check.py::test_chapter_file_parsing` | set `project_root` but not `chapters_dir`; `get_chapter_files()` scanned wrong dir | set both `project_root` AND `chapters_dir` |

## Commits (5 atomic)

| # | SHA | Subject | Files | +/- |
|---|-----|---------|-------|-----|
| C0 | (spec/plan) | `docs(phase-53b): spec + plan` | 1 | +100 |
| C1 | `ebd76f16` | `fix(tools-shim): remove stale LLMService re-export` | 1 | +18/-11 |
| C2 | `cad400d8` | `fix(tests): migrate test_llm_quality_deep_check.py to canonical + chapter_file_parsing fix` | 1 | +76/-74 |
| C3 | `2e4f60fc` | `fix(lingwen-cli): use canonical tools.llm_quality.LLMQualityChecker` | 1 | +1/-1 |
| C5 | `ef24f74b` | `test(phase-53b): 11 regression guards + docstring cleanup` | 2 | +231/-2 |

## Lessons

1. **Phase 5 LLM_QUALITY split was incomplete.** The original
   1138-line `tools/llm_quality_deep_check.py` was split into a
   5+1 file subpackage (`tools/llm_quality/`) but the old file
   was kept as a 34-line shim. The shim's docstring claimed to
   re-export `LLMService`, but that symbol was renamed to
   `LLMServiceAdapter` in the new subpackage. Result: the shim
   itself failed to import, silently breaking 8 tests + 1
   production import.

2. **Shims that re-export must be re-verified after a refactor.**
   When the canonical source renames a symbol (e.g. LLMService →
   LLMServiceAdapter), every shim that re-exports the old name
   must be updated in the same commit. Otherwise the shim
   becomes a transitive failure that's hard to trace.

3. **Constructor injection > mock.patch for class-based DI.**
   The original test patched `tools.llm_quality_deep_check.LLMService`
   to inject a mock. The cleaner pattern is
   `LLMQualityChecker(llm_service=mock)` — the constructor was
   already designed for this, no patch gymnastics needed.
   This eliminates the entire `_service` patch fixture pattern.

4. **Setter ordering matters for fixture-based tests.** The
   `test_chapter_file_parsing` test set `checker.project_root`
   but not `checker.chapters_dir`. The checker's
   `get_chapter_files()` reads `chapters_dir` directly, ignoring
   `project_root` for that method. The fix (set both) is a
   classic example of "understand what the method actually reads
   before over-asserting on what the fixture sets".

5. **Test file docstrings should be prose, not literal code
   examples.** (Phase 58 lesson 4 reinforced.) The new test file
   originally had a docstring that included
   `` `patch("tools.llm_quality_deep_check.LLMService")` ``
   as an example. The static-source guard caught this as a
   false positive. Rewrote the docstring to use prose. Lesson:
   when documenting "what we used to do", describe it in words,
   not as an exact call that the guard will match.

## Out of scope (deliberate non-goals)

- `tools/legacy/` 19 old scripts (independent Phase 53c)
- Full removal of `tools/llm_quality_deep_check.py` shim
  (still used by `python tools/llm_quality_deep_check.py` script
  entry + 1 production site that may have shell-script deps)
- `test_get_state_uses_explicit_read_transaction` (pre-existing,
  memory known, deferred)

## FF-merge

```bash
cd /home/ailearn/projects/LingWen && \
  git checkout master && \
  git merge --ff-only phase-57-p3-archdebt-reading-power && \
  git push origin master
```
