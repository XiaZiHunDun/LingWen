# Phase 58 — Cross-Volume 16 Failures Fix Design

**Date**: 2026-09-12
**Branch**: `phase-57-p3-archdebt-reading-power` (continues from Phase 56c)
**Carryover from**: Phase 56c handoff §146 (16 pre-existing test failures)
**New version**: v54.2 → v54.3
**New invariants**: none (test-infra fix, no new domain invariants)

## Summary

Phase 56c relocated 32 test files + 5 guards but left **16 pre-existing test failures**
unaddressed. This phase closes that carryover debt. No production logic changes
(unless tests reveal a real bug during fix).

**Outcome target**: 220/220 tests pass in `packages/lingwen-cross-volume/tests/`
(currently 204/220 = 91% pass rate).

## Root Cause Analysis (verified via pytest -xvs)

Running each of the 16 failing tests with `-xvs` revealed **2 distinct root causes**,
not the 5 the handoff hypothesized:

### RC1 — Test path mismatch (4 failures)

Tests use legacy `dashboard.X` import paths; production code uses canonical
`apps.studio_api.X`. The patch never intercepts the call, so broadcast assertions
fail (or `_ripple_to_list_item` import raises `ModuleNotFoundError`).

| File | Lines | Bug |
|------|-------|-----|
| `tests/test_storage_ripple_action.py` | 118-120, 140-142, 156-158 | patches `sys.modules["dashboard.cvg_ws"]` (broadcast tests) |
| `tests/test_cascade_broadcast_log.py` | 75-77 | `monkeypatch.setattr("dashboard.cascade_notifier.notify_cascade_update", ...)` |
| `tests/test_chained_cascade.py` | 114 | `from dashboard.app import _ripple_to_list_item` |

Production code (verified):
- `lingwen_cross_volume/storage.py:1349` imports `from apps.studio_api.cvg_ws import broadcast`
- `lingwen_cross_volume/storage.py:358` imports `from apps.studio_api.cascade_notifier import notify_cascade_update`
- `_ripple_to_list_item` is exported at `apps/studio_api/app.py:95` and `apps/studio_api/helpers/cvg.py:80`

**Verification**:
- `apps/studio_api/cvg_ws.py` exists (storage.py target) ✓
- `apps/studio_api/cascade_notifier.py` exists (storage.py target) ✓
- `dashboard/` is **Vue frontend**, not a Python module — `dashboard.app` was never a valid Python import path

**Affects 4 tests**:
- `test_storage_ripple_action.py::TestUpdateRippleStatus::test_broadcast_hook_called_on_status_change`
- `test_storage_ripple_action.py::TestAppendNodesAtomicBroadcast::test_nonempty_nodes_broadcasts_ripple_created`
- `test_cascade_broadcast_log.py::TestCascadeBroadcastLogStorage::test_append_ripple_persists_broadcast_log`
- `test_chained_cascade.py::TestChainedCascadeAPIFields::test_list_item_includes_parent_and_child_count`

**Fix**: Replace `dashboard.X` → `apps.studio_api.X` in 3 test files. Pure string substitution, no production code change.

### RC2 — Command base class eagerly validates ProjectPaths (12 failures)

`packages/lingwen-cli/src/lingwen_cli/commands/base.py:25-29`:

```python
def __init__(self):
    self.paths = ProjectPaths.get()                              # ← raises here
    max_ch = project_max_chapter(self.paths)
    self.range_parser = RangeParser(all_chapters=max_ch)
    self.formatter = OutputFormatter()
```

`ProjectPaths.get()` validates that `03_内容仓库/04_正文` exists at
`LINGWEN_PROJECT_ROOT`. In test environments without a real project, the chapters
directory doesn't exist → `RuntimeError: 章节目录不存在: ...`.

**Affects 12 tests** (all construct `BackfillCommand()` / `RippleScanCommand()` directly):

| File | Tests |
|------|-------|
| `test_cli_llm_flags.py` | 5 (`test_apply_without_use_llm_errors`, `test_apply_with_use_llm_triggers_llm_path`, `test_dry_run_default_no_write_in_llm_path`, `test_cache_path_passed_to_llm_cache`, `test_backward_compat_no_new_flags_still_works`) |
| `test_e2e_llm_backfill.py` | 3 (`test_e2e_llm_backfill_full_flow_with_mock_router`, `test_e2e_llm_backfill_dry_run_no_write`, `test_e2e_llm_backfill_continues_on_chapter_error`) |
| `test_scanner_calibration.py` | 1 (`test_calibrate_fixture_report`) |
| `test_scanner_calibration_feedback.py` | 1 (`test_calibrate_cli_includes_per_dimension`) |
| `test_backfill_production_execute.py` | 2 (`test_cli_execute_integration_prints_executed_summary`, `test_cli_default_dry_run_hint_mentions_execute`) |

**Why this is a real bug, not a test-only issue**:

`Command.__init__` does eager work that should be lazy:
1. `self.paths = ProjectPaths.get()` — filesystem-dependent singleton resolution
2. `project_max_chapter(self.paths)` — requires reading chapters dir
3. `RangeParser(all_chapters=max_ch)` — depends on max_ch

These are all **side-effectful operations** that should be deferred to first use.
Constructing a Command should not require a valid project layout — only *executing*
it should.

**Production usage verified safe**:
- All 9 production uses are `self.paths.X` (read-only method/property access) — works with `@property`
- No production code does `self.paths = X` assignment (grep verified)
- `self.paths.X` access still triggers lazy `ProjectPaths.get()` if not already resolved

**Fix**: Convert `paths`, `range_parser`, `formatter` to lazy properties (cached
on first access). Construction succeeds without a valid project; `self.paths.X`
access from `execute()` triggers resolution with a clear error if project is invalid.

```python
def __init__(self):
    self._paths: ProjectPaths | None = None
    self._range_parser: RangeParser | None = None
    self._formatter: OutputFormatter | None = None

@property
def paths(self) -> ProjectPaths:
    if self._paths is None:
        self._paths = ProjectPaths.get()
    return self._paths

@property
def range_parser(self) -> RangeParser:
    if self._range_parser is None:
        max_ch = project_max_chapter(self.paths)
        self._range_parser = RangeParser(all_chapters=max_ch)
    return self._range_parser

@property
def formatter(self) -> OutputFormatter:
    if self._formatter is None:
        self._formatter = OutputFormatter()
    return self._formatter
```

Note: `BackfillCommand.execute()` doesn't access `self.paths` (corpus_root is
passed via options); `RippleScanCommand.execute()` also uses options-driven paths.
So tests that mock the inner work don't actually trigger paths resolution.

## Design Decision: 2-RC, not 5-cluster

The Phase 56c handoff hypothesized 5 root causes (CLI flag / E2E mock / broadcast
hook / scanner calibration ProjectPaths / cascade list item). After running each
test individually with `-xvs`:

- **CLI flag integration** → actually **RC2** (Command construction)
- **E2E with mock router** → actually **RC2** (Command construction)
- **broadcast hook** → actually **RC1** (test path) + RC2 doesn't apply
- **scanner calibration ProjectPaths** → actually **RC2** (Command construction)
- **cascade list item** → actually **RC1** (test path)
- **production execute** → actually **RC2** (Command construction)

So 12 are RC2 (same bug, different test files) and 4 are RC1 (3 test files).
Cleaner than 5 clusters — the 16 failures collapse to 2 root causes.

## Commits (4 atomic)

### C1: Fix Command base class (RC2 — 12 fixes)
- Edit `packages/lingwen-cli/src/lingwen_cli/commands/base.py`
- Lazy-init `paths`, `range_parser`, `formatter` as @property
- Verification: 12 tests pass that were failing on `RuntimeError`

### C2: Fix test path mismatches (RC1 — 4 fixes)
- `test_storage_ripple_action.py`: 3 patches `dashboard.cvg_ws` → `apps.studio_api.cvg_ws`
- `test_cascade_broadcast_log.py`: 1 patch `dashboard.cascade_notifier` → `apps.studio_api.cascade_notifier`
- `test_chained_cascade.py`: 1 import `dashboard.app` → `apps.studio_api.app`
- Verification: 4 tests pass that were failing on import / wrong patch target

### C3: Regression guards + version bump
- New file `tests/test_phase58_cross_volume_failures.py`:
  - G1: lazy paths pattern in `base.py` (no eager `ProjectPaths.get()`)
  - G2: lazy range_parser pattern (no eager `project_max_chapter(self.paths)`)
  - G3: no `dashboard.X` (cvg_ws / cascade_notifier / app) imports in cross_volume tests
  - G4: `apps.studio_api.X` paths used in 3 fixed test files
  - G5: 220/220 cross_volume tests pass
- Bump v54.2 → v54.3 + update CLAUDE.md version line + invariants unchanged

### C4: Handoff + doc-sync
- New `docs/superpowers/handoffs/2026-09-12-phase-58-cross-volume-failures-handoff.md`
- Update `MEMORY.md` Phase 58 line + topic pointer

## Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Lazy property breaks existing `self.paths = X` assignment | Low | grep verified: 0 production assignments; property setter would raise AttributeError, surfacing bug early |
| Lazy resolution in `execute()` adds latency | Negligible | `ProjectPaths.get()` is cached singleton; subsequent calls O(1) |
| `Command.__init__` signature change breaks subclasses | None | Signature unchanged; only attribute access semantics change (property vs eager attr) |
| RC1 fix creates stale test assumption (test patches, code doesn't import) | Low | Use `apps.studio_api.X` which is the canonical path that storage.py imports |
| BackfillCommand / RippleScanCommand production behavior change | None | Both commands' `execute()` doesn't access `self.paths` (options-driven); production behavior identical |

## Verification Gates

1. **C1 verification**: 12 RC2 tests pass after base.py edit
2. **C2 verification**: 4 RC1 tests pass after test file edits
3. **C3 guards**: 5/5 GREEN
4. **C3 cross_volume**: 220/220 pass from any cwd (3-cwd verification per Phase 56b2 lesson)
5. **C3 baselines preserved**:
   - 158/158 phase 5x guards still GREEN
   - lingwen-core 68/68 + lingwen-got 208/208 + lingwen-world-model 201/201 + studio_api 82/82
   - lingwen-creator 50 test_creator_* (Phase 42 baseline)
   - lingwen-llm-service (Phase 43) + lingwen-prose-calibration (Phase 44) + others
6. **No production code change** beyond `base.py` (lazy pattern is the only prod edit)

## Lessons to Capture

1. **Handoff hypotheses may overcount root causes**: Phase 56c listed 5 root causes for the 16 fails; actual is 2 (with 12 being the same Command construction bug). Always re-verify with `-xvs` before designing fixes.

2. **`-xvs` is the canonical way to identify test failure root causes**: pytest's summary `FAILED test_name` doesn't show the actual error. `-xvs` shows the stack trace.

3. **Legacy `dashboard.X` import paths in cross_volume tests**: suggest these tests were written before the Phase 56 P3-ARCHDEBT migration when `infra.dashboard.*` paths existed. The migration to `apps.studio_api.*` happened but tests weren't updated. Pattern: when migrating canonical paths, audit ALL test patches + imports for stale module references.

4. **Eager construction with side effects is a test smell**: `Command.__init__` calling `ProjectPaths.get()` is the classic "constructing an object should not require world state" violation. The fix (lazy @property) makes commands construction pure — a textbook refactor.

5. **`assert 0 == 1` where `len([]) == 0` is the symptom of monkeypatch path mismatch** (Phase 58 RC1 signature): the patch doesn't intercept, the broadcast never happens, the assertion fails on count mismatch.
