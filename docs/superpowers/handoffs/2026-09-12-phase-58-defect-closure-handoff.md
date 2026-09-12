# Phase 58 P3-ARCHDEBT Defect Closure — Handoff

> **Date**: 2026-09-12
> **Branch**: phase-57-p3-archdebt-reading-power (continuing from Phase 57)
> **Version**: v53.0 → v53.1
> **Triggered by**: Post-Phase-57 baseline check (`pytest apps/studio_api/tests/`) — 24 failed

## TL;DR

Phase 58 closes 24 pre-existing pytest failures + 1 silent production bug
that were all variants of "Phase 56 P3-ARCHDEBT did not finish migrating
internal imports". 6 atomic commits; all 24 tests now pass; 22 regression
guards added; net +1 production bug found and fixed beyond the original
scope (caught by a repo-wide grep guard).

## Validation

| Gate | Result |
|------|--------|
| `pytest apps/studio_api/tests/` | 82 passed / 0 failed (was 24 failed / 58 passed) |
| `pytest tests/test_phase58_defect_closure.py` | 22/22 passed |
| `pytest tests/` (root, subset) | 22 new guards + 12 prior-phase guards GREEN |
| `from lingwen_world_db.queries.characters import create_character` | exit 0 |
| `from lingwen_world_db.agent_extractors import extract_proposals_from_chapters` | exit 0 |
| `import infra.llm_benchmarks.run` | exit 0 (was: silent broken import chain) |
| `grep -rln "from infra.world_db" --include="*.py"` | 0 hits repo-wide |

## Root causes

| # | Class | Files | Was | Now |
|---|-------|-------|-----|-----|
| 1 | Missing re-export | `lingwen_studio_batch_streamer/__init__.py` | `KNOWN_EVENT_TYPES` not in `__all__` | re-exported |
| 2 | Wrong patch path | `test_studio_batch_events_route.py:118` | `patch("lingwen_studio_batch_runner._completed_chapter_nums")` | `patch("lingwen_studio_batch_runner.service._completed_chapter_nums")` |
| 3 | Stale test imports | `test_world_route.py` (5 sites) | `from infra.world_db.*` | `from lingwen_world_db.*` |
| 4 | **Silent prod bug** | `packages/lingwen-world-db/` (8 files, 10 imports) | `from infra.world_db.*` | `from lingwen_world_db.*` |
| 5 | Bonus catch (via G5) | `infra/llm_benchmarks/run.py` (2 sites) | `from infra.world_db.agent_*` | `from lingwen_world_db.agent_*` |
| 6 | Orphan test dir | `tests/infra/world_db/` (5 files + `__pycache__`) | existed, all `infra.world_db` imports broken | deleted |

## Commits (6 atomic)

| # | SHA | Subject | Files | +/- |
|---|-----|---------|-------|-----|
| C1 | `3cedf498` | `fix(streamer): re-export KNOWN_EVENT_TYPES` | 1 | +2/-0 |
| C1.5 | `8bf9e259` | `fix(tests): correct patch path for _completed_chapter_nums` | 1 | +1/-1 |
| C2 | `82cd85a8` | `fix(tests): migrate test_world_route.py to lingwen_world_db` | 1 | +5/-5 |
| C3 | `db0e9b97` | `fix(world-db): migrate 8 production imports infra→lingwen` | 9 | +12/-12 |
| C4 | `0f3239f4` | `chore(tests): delete orphan tests/infra/world_db/` | 5 | +0/-491 |
| C5 | `ee1a82fa` | `test(phase-58): 22 regression guards + bonus fix` | 2 | +254/-2 |

**Net**: -250 LOC (491 deleted orphan tests - 241 added guards/spec).

## Lessons

1. **The "fix 24 test defects" framing was incomplete.** What looked like
   24 isolated test failures was actually 4 distinct bug classes + 1
   silent production bug. The most dangerous was the production-side
   internal imports — those don't fail at import time (the package's
   `__init__.py` only re-exports 2 symbols) but break every runtime
   call to `/api/world/characters`, `/api/world/import`, etc. A
   production API surface area had been silently broken for an unknown
   number of sessions.

2. **N.14 lesson 1 (10th variant): repo-wide grep guard caught
   `infra/llm_benchmarks/run.py` that the per-file guards missed.** The
   4 categories of "stale import" guards all used static source
   inspection of expected file lists, but a 5th file outside those
   lists (an unrelated infra/llm_benchmarks/ tool) had the same bug.
   The repo-wide grep guard (`grep -rln "from infra.world_db" --include="*.py"`)
   is the only one that catches *unknown* future files. Always add at
   least one repo-wide guard for cross-cutting migration.

3. **`__pycache__` lingers after `git rm -r`.** The orphan test
   directory guard's first run failed because `git rm -r` removes
   tracked files but not the build artifact `__pycache__/` subdir. A
   follow-up `rm -rf tests/infra/world_db/` was needed. Future phase
   cleanups should `rm -rf` the dir after `git rm -r` to ensure full
   removal.

4. **Grep regex must be import-form-aware, not just substring.** A
   naive `grep "infra.world_db"` would catch the docstring in
   `__init__.py` line 3 ("Phase 56 P3-ARCHDEBT: relocated verbatim from
   infra/world_db/") as a false positive. The guard regex
   `(^|\n)\s*(from|import)\s+infra\.world_db\b` is intentionally tight:
   only actual import statements count. Docstring historical references
   are fine.

5. **Test patch path lesson (N.14 Pattern 6 extension).** When
   `mock.patch("pkg._private_helper")` fails with AttributeError, the
   cause is that private helpers are not re-exported from `__init__.py`.
   Either fix the test to patch the actual source module
   (`pkg.service._private_helper`) or, if you intend the helper to be
   patchable, re-export it explicitly with a docstring explaining why.

## Out of scope (deliberate non-goals)

- `tests/infra/world_db/` → `packages/lingwen-world-db/tests/` migration
  (test coverage was lost in Phase 56; restoring is a separate phase)
- `I076` invariant upgrade (current text already declares
  `lingwen-world-db` canonical; no change needed)
- New production end-to-end tests (we restored existing test coverage,
  did not add new)

## FF-merge

```bash
cd /home/ailearn/projects/LingWen && \
  git checkout master && \
  git merge --ff-only phase-57-p3-archdebt-reading-power && \
  git push origin master
```
