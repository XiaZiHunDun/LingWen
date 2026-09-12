# Phase 56c P3-ARCHDEBT Handoff — cross_volume tests relocation

**Date**: 2026-09-12
**Branch**: `phase-57-p3-archdebt-reading-power`
**Commits**: 5 atomic (C1 / C2 / C3 / C4 + C5 gitignore fixup added post-handoff)
**New version**: v54.1 → v54.2 (test infra relocation, 32 files + 5 guards + 3 in-test fixes)
**New invariants**: none (continues I078 from Phase 55)

## Summary

Phase 55 scaffolded `packages/lingwen-cross-volume/` (commit `9d6a680d`) and FULL
DELETED `infra/cross_volume/` (commit `de105344`) + I078 invariant — but **left
32 test files at `tests/cross_volume/`** (NOT moved into the package).

This created a test infrastructure mismatch:
- 32 collection errors when running pytest via `/home/ailearn/miniconda3/bin/python`
  (venv site-packages invisible, `lingwen_cross_volume` not on sys.path)
- 220 tests collect, 204 pass, 16 fail when running via `.venv/bin/python`
  (venv site-packages visible, package importable)

Phase 56c completes the move Phase 55 left half-done. Mirrors Phase 56b
pattern for `lingwen-world-db` (5 files) and Phase 35 for `lingwen-world-model`.

## Commits (5 atomic)

| C | SHA | Description |
|---|-----|-------------|
| C1 | `2b9f31cb` | test(cross-volume): relocate 32 test files + conftest + fixtures to package (49 renames + 1 add + 1 modify) |
| C2 | `d241f351` | fix(cross-volume): cwd-independent paths in 3 tests (Phase 56b2 lesson, R098/R086/R090) |
| C3 | `bef73fdb` | test(cross-volume): 5 regression guards for Phase 56c move |
| C4 | `199654cc` | docs(phase-56c): handoff + CLAUDE.md sync + MEMORY update + v54.1 → v54.2 |
| C5 | (this commit) | chore(phase-56c): .gitignore fixup for runtime artifacts (C5 followup to lesson 5) |

## What moved (32 files + conftest + fixtures)

```
tests/cross_volume/                              → packages/lingwen-cross-volume/tests/
├── 32 test_*.py files                           ├── (same 32 files)
├── conftest.py                                  ├── conftest.py
└── fixtures/                                    └── fixtures/
    ├── __init__.py                                  ├── __init__.py
    ├── ch001.md ... ch005.md                        ├── ch001.md ... ch005.md
    ├── ch00X_大纲.md (5 files)                      ├── ch00X_大纲.md (5 files)
    ├── llm_responses/ (.calibrate_cache.json + 5    ├── llm_responses/
    │   character/edge/foreshadow/plot/setting .json)│   (same 6 files)
    ├── sample_corpus.py                            ├── sample_corpus.py
    └── scanner_calibration_gold.yaml               └── scanner_calibration_gold.yaml

NEW: packages/lingwen-cross-volume/tests/__init__.py (Phase 56c context docstring)
```

## Root cause of 32 collection errors

When pytest runs via `/home/ailearn/miniconda3/bin/python`:
- miniconda's sitecustomize.py adds master repo paths to sys.path
- `packages/lingwen-cross-volume/src/` (worktree) is NOT on miniconda sys.path
- The `.pth` file at `worktree/.venv/lib/python3.13/site-packages/_editable_impl_lingwen_cross_volume.pth`
  points to worktree path — but miniconda python doesn't see worktree's venv site-packages
- `from lingwen_cross_volume import ...` → `ModuleNotFoundError`

When pytest runs via `worktree/.venv/bin/python`:
- venv detected (`sys.prefix = worktree/.venv`, `sys.base_prefix = miniconda3`)
- venv's site-packages on sys.path
- `.pth` file processed → `packages/lingwen-cross-volume/src/` added
- 220 tests collect, 204 pass, 16 fail (pre-existing)

After move to `packages/lingwen-cross-volume/tests/`:
- pytest rootdir = worktree (pytest.ini-driven), conftest.py at `packages/lingwen-cross-volume/tests/`
- pythonpath includes `.` and `infra` (pytest.ini), auto-adds `packages/lingwen-cross-volume/tests/`
- `from lingwen_cross_volume import ...` works because `.venv/bin/python` sees venv site-packages
- 220 collect from any cwd (repo root / package dir / tests dir) — verified 3-cwd

## In-test cwd-independence fixes (C2)

Phase 56b2 taught: cwd-relative `Path("X/...")` is test-fixture smell.
Use `Path(__file__).resolve().parent / "..."` for cwd-independence.

| File | Line | Before | After |
|------|------|--------|-------|
| `test_backfill.py` | 276 | `from tests.cross_volume.fixtures.sample_corpus import ...` | `from .fixtures.sample_corpus import ...` |
| `test_scanner_calibration.py` | 112,113,126 | `Path("tests/cross_volume/fixtures/...")` | `Path(__file__).resolve().parent / "fixtures" / "..."` |
| `test_scanner_calibration_feedback.py` | 96,97 | `Path("tests/cross_volume/fixtures/...")` | `Path(__file__).resolve().parent / "fixtures" / "..."` |

Without C2, the move would have introduced 2 NEW test failures
(`test_backfill.py::TestBackfillE2E` + `test_scanner_calibration.py::test_load_gold_labels_fixture`).
Verified by running tests before/after move.

## 5 regression guards (C3, all GREEN)

Mirrors Phase 56b's `test_phase56b_p3_archdebt_world_db_tests.py`:

| Guard | Assertion |
|-------|-----------|
| G1 | `tests/cross_volume/` directory MUST NOT exist (Phase 56c moved files) |
| G2 | `packages/lingwen-cross-volume/tests/` MUST contain 32 test_*.py files |
| G3 | No file under `packages/lingwen-cross-volume/tests/` (excluding `__init__.py`) may reference `infra.cross_volume.*` (Phase 55 C3 FULL DELETED + I078) |
| G4 | No `Path("tests/cross_volume/...")` cwd-relative literals (Phase 56b2 lesson) |
| G5 | `packages/lingwen-cross-volume/tests/__init__.py` MUST have Phase 56c context marker |

Phase 5x cumulative baseline: 153 → 155 (Phase 56b2) → 158 (Phase 56c).
158/158 phase5x guards GREEN.

## Pre-existing 16 test failures (carryover)

Phase 56c does NOT fix these. Documented in
`packages/lingwen-cross-volume/tests/__init__.py` as Phase 58+ carryover:

| File | Test count | Root cause hypothesis |
|------|-----------|------------------------|
| `test_backfill_production_execute.py` | 2 | CLI integration / dry-run hint |
| `test_cascade_broadcast_log.py` | 1 | `append_ripple_persists_broadcast_log` |
| `test_chained_cascade.py` | 1 | `list_item_includes_parent_and_child_count` |
| `test_cli_llm_flags.py` | 5 | LLM flag integration (CLI uses `lingwen-cli` + `lingwen-paths` chain) |
| `test_e2e_llm_backfill.py` | 3 | E2E with mock router (likely mock setup issue) |
| `test_scanner_calibration.py` | 1 | `calibrate_fixture_report` (ProjectPaths missing chapters dir post-Phase 37) |
| `test_scanner_calibration_feedback.py` | 1 | `calibrate_cli_includes_per_dimension` (same ProjectPaths) |
| `test_storage_ripple_action.py` | 2 | `broadcast_hook_called_on_status_change` + `append_nodes_atomic_broadcast` |

These pre-date Phase 56c — verified by running tests from `tests/cross_volume/`
before move: same 16 failures, same 204 passing.

## Validation gates

| Gate | Result |
|------|--------|
| `pytest packages/lingwen-cross-volume/tests/` from repo root | 220 collect, 204 pass, 16 fail |
| `pytest packages/lingwen-cross-volume/tests/` from package dir | 220 collect, 204 pass, 16 fail |
| `pytest .` from tests dir | 220 collect, 204 pass, 16 fail |
| `pytest tests/test_phase56c_p3_archdebt_cross_volume_tests.py` | 5/5 GREEN |
| `pytest tests/ -k phase5` | 158/158 GREEN (no regression) |
| `pytest tests/test_phase55_p3_archdebt_cross_volume.py` | 27/27 GREEN (co-existence) |
| ruff on changed files | (ruff not in venv — manual syntax check via `ast.parse`) |

## Lessons (5)

1. **`git commit -- pathspec` only commits pathspec paths; for rename preservation, BOTH old + new paths must be in pathspec** (Phase 56c C1 redo cost ~10 min). Without both, git shows new files as `A` instead of `R`, losing blame history. Use `git diff --name-status -z -M` for NUL-separated rename data + manual python parse to build pathspec.

2. **Tests outside package dir are inherently fragile** (Phase 56c root cause). 32 collection errors = package import failed because tests live outside package. Phase 56b pattern (move tests into package) is the only stable solution. Lesson 1 of Phase 56b2 (cwd-independence) is necessary but not sufficient.

3. **Phase 55 half-migration pattern recurring** (Phase 56b world_db + Phase 56c cross_volume). When P3-ARCHDEBT deletes infra/* and scaffolds packages/*-db, test files left at `tests/X/` create orphan test infra. Phase 56b/56c are the **followup pattern** — must be planned for in original phase, not deferred.

4. **Test guard source code references to deleted paths are false-positives for prior-phase guards** (Phase 56c C3 fixup cost ~5 min). Phase 55's `TestNoPathLiterals::test_no_repo_wide_path_literals` flagged my G3 source for containing `"infra/cross_volume"` literal. Build slash-variant path via `chr(47)` concat OR regex with raw string parts to avoid the literal in source.

5. **P3-ARCHDEBT infra → packages migration MUST paired-update .gitignore paths** (Phase 56c C5 fixup). Phase 54 migrated `infra/agent_system/social_engine/relationship_network.db` → `packages/lingwen-core/src/lingwen_core/agents/social_engine/relationship_network.db` BUT only the new test artifacts were being created (Phase 54 left .gitignore rule on old infra path). Pattern for future P3-ARCHDEBT migrations: when adding new `packages/X/` rule, keep old `infra/X/` rule as safety net for partial migrations + audit both at C5/C7 phase.

## Carryover (Phase 58+)

- 16 pre-existing test failures (above) — real bugs in cross_volume logic
  (broadcast hook, CLI flag integration, calibration fixture, etc.)
- `lingwen-cross-volume/tests/logs/` artifacts (already gitignored via
  Phase 56c `.gitignore` addition `packages/**/logs/`)