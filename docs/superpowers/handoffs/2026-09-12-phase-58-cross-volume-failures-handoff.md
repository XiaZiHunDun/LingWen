# Phase 58 — Cross-Volume 16 Failures Fix Handoff

**Date**: 2026-09-12
**Branch**: `phase-57-p3-archdebt-reading-power`
**Commits**: 4 atomic (C1 base.py lazy / C2 3 test files / C3 guards+v54.3 / C4 handoff)
**New version**: v54.2 → v54.3
**New invariants**: none (test-infra fix)

## Summary

Phase 56c relocated 32 test files but left **16 pre-existing failures** unaddressed
(carryover from `0f3239f4` commit pre-Phase 56, deferred to "Phase 58+"). Phase 58
closes that debt: **220/220 cross_volume tests GREEN** (was 204/220 = 91% pass rate).

## Root cause collapse

Phase 56c handoff §146 hypothesized **5 root causes** for the 16 failures:
1. CLI integration / dry-run hint
2. LLM flag integration (CLI uses `lingwen-cli` + `lingwen-paths` chain)
3. E2E with mock router (likely mock setup issue)
4. Scanner calibration ProjectPaths missing chapters dir post-Phase 37
5. Cascade list item API fields
6. Storage ripple broadcast hook

Running each test individually with `pytest -xvs` revealed **2 root causes** that
collapse all 16 failures:

- **RC2 (12 fails)**: `Command.__init__` eagerly validated `ProjectPaths.get()` +
  `project_max_chapter(self.paths)`, raising `RuntimeError("章节目录不存在")` when
  chapters dir missing.
- **RC1 (4 fails)**: Tests used legacy `dashboard.X` import paths; production uses
  canonical `apps.studio_api.X` (dashboard/ is Vue frontend, never a Python module).

| Hypothesized RC | Actual RC | Files affected |
|----------------|-----------|----------------|
| CLI integration / dry-run hint | RC2 | test_backfill_production_execute.py (2) |
| LLM flag integration (5 fails) | RC2 | test_cli_llm_flags.py (5) |
| E2E mock router (3 fails) | RC2 | test_e2e_llm_backfill.py (3) |
| Scanner calibration ProjectPaths (2 fails) | RC2 | test_scanner_calibration*.py (2) |
| Cascade list item API fields (1 fail) | RC1 | test_chained_cascade.py (1) |
| Storage ripple broadcast hook (2 fails) | RC1 | test_storage_ripple_action.py (2) |
| Cascade broadcast log (1 fail) | RC1 | test_cascade_broadcast_log.py (1) |

**12 + 4 = 16 = all accounted for.**

## Commits (4 atomic)

| C | SHA | Description | Files | Failures fixed |
|---|---|---|---|---|
| C1 | `5d4d0d30` | fix(cli): lazy-init Command paths/range_parser/formatter | `packages/lingwen-cli/src/lingwen_cli/commands/base.py` | 12 |
| C2 | `d87a5a08` | fix(cross-volume): align test paths to apps.studio_api.X | 3 test files | 4 |
| C3 | `d90e29d7` | test(phase-58): 5 regression guards + v54.2 → v54.3 | `tests/test_phase58_cross_volume_failures.py` + CLAUDE.md | (prevention) |
| C4 | (this) | docs(phase-58): handoff + MEMORY + status sync | handoff + MEMORY + status | (docs) |

## Detailed fixes

### C1 — `Command` lazy-init pattern (`base.py`)

**BEFORE** (4 lines, side-effectful construction):
```python
def __init__(self):
    self.paths = ProjectPaths.get()
    max_ch = project_max_chapter(self.paths)
    self.range_parser = RangeParser(all_chapters=max_ch)
    self.formatter = OutputFormatter()
```

**AFTER** (3 lazy @property):
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

Verified safe by `grep -rn "self\.paths\s*=" packages/lingwen-cli/src/`:
**0 production assignments** — all use `self.paths.X` read-only access.

### C2 — 3 test files path alignment

| File | Lines | BEFORE → AFTER |
|---|---|---|
| `test_storage_ripple_action.py` | 118-120, 140-142, 156-158 | `dashboard.cvg_ws` → `apps.studio_api.cvg_ws` (3 patches) |
| `test_cascade_broadcast_log.py` | 75-77 | `dashboard.cascade_notifier.notify_cascade_update` → `apps.studio_api.cascade_notifier.notify_cascade_update` |
| `test_chained_cascade.py` | 114 | `from dashboard.app import _ripple_to_list_item` → `from apps.studio_api.app import _ripple_to_list_item` |

Canonical paths verified:
- `apps/studio_api/cvg_ws.py` exists (storage.py:1349 lazy import target)
- `apps/studio_api/cascade_notifier.py` exists (storage.py:358 lazy import target)
- `_ripple_to_list_item` exported at `apps/studio_api/app.py:95` + `apps/studio_api/helpers/cvg.py:80`

## Validation gates

| Gate | Result |
|------|--------|
| 220/220 cross_volume tests pass (repo root) | ✓ (37.18s) |
| 220/220 cross_volume tests pass (packages/lingwen-cross-volume) | ✓ (37.83s) |
| 220/220 cross_volume tests pass (packages/lingwen-cross-volume/tests) | ✓ (36.89s) |
| 5/5 phase58 guards GREEN | ✓ |
| 158/158 phase5x guards preserved | ✓ |
| 163/163 phase5x + phase58 cumulative | ✓ (40.71s) |
| 0 production code breakage (no `self.paths = X` in commands/) | ✓ |

## Lessons (5)

1. **Handoff hypotheses may overcount root causes**: Phase 56c listed 5 RCs for 16 fails; actual is 2. Always re-verify with `pytest -xvs` before designing fixes — the symptom (`FAILED test_name`) hides the actual error.

2. **`assert 0 == 1` where `len([]) == 0` is the signature of monkeypatch path mismatch** (Phase 58 RC1): the patch doesn't intercept because the target module doesn't exist (or has different name). Common when migrating canonical paths without auditing all test patches.

3. **Eager construction with side effects is a test smell**: `Command.__init__` calling `ProjectPaths.get()` + `project_max_chapter(self.paths)` violates "construction should be side-effect-free". Lazy `@property` is the textbook fix and makes commands construction pure.

4. **`-xvs` is the canonical debugging tool**: pytest summary `FAILED test_name` doesn't show the actual error. `-xvs` shows the stack trace which is the only way to distinguish RC1 (test path) vs RC2 (Command construction) vs other.

5. **Cross-cwd verification (Phase 56b2 lesson 3, applied again)**: 3 cwds all show 220/220 — single invocation hides cwd-relative test fixture issues. Phase 58 inherits this discipline from Phase 56b2.

## Carryover closure

| Phase | Status |
|-------|--------|
| P2-ARCHDEBT (got/world_model) | ✅ Phase 33-35 |
| P3-ARCHDEBT 15/15 | ✅ Phase 36-57 |
| **Phase 58 cross_volume 16 failures** | ✅ **Phase 58 (this)** |
| Phase 53c infra/tools/ residual | 🟡 Candidate for next phase |
| Product features (Write Workspace / World / Reading Power) | 🟡 Candidate for next phase |

**v54.3 ready for ff-merge to master.**
