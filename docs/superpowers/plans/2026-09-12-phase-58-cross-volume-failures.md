# Phase 58 — Cross-Volume 16 Failures Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the 16 pre-existing test failures in `packages/lingwen-cross-volume/tests/` that were deferred from Phase 56c, returning the cross_volume test suite to 220/220 GREEN and bumping version to v54.3.

**Architecture:** Two root causes identified via pytest `-xvs`:
- **RC2 (12 fails)**: `Command.__init__` eagerly validates `ProjectPaths.get()` → 12 tests fail at command construction. Fix: convert `paths`/`range_parser`/`formatter` to lazy `@property`.
- **RC1 (4 fails)**: Tests use legacy `dashboard.X` import paths; production uses canonical `apps.studio_api.X`. Fix: update 3 test files.

**Tech Stack:** Python 3.13 / pytest 9.1 / Phase 56c pattern (move tests into package + Phase 56b2 cwd-independence + atomic commits + regression guards).

---

## Task 1: Verify baseline (220 collect / 204 pass / 16 fail)

**Files:** none (verification only)

- [ ] **Step 1: Confirm worktree HEAD matches master**

Run:
```bash
git rev-parse HEAD && git log --oneline -1
```
Expected: `dcfed22e chore(phase-56c): gitignore fixup for runtime artifacts (C5)`

- [ ] **Step 2: Run cross_volume tests to confirm 220/16 baseline**

Run:
```bash
.venv/bin/python -m pytest packages/lingwen-cross-volume/tests/ --tb=no -q 2>&1 | tail -5
```
Expected: `16 failed, 204 passed in ~37s`

- [ ] **Step 3: Document the 16 failed test names for later verification**

Run:
```bash
.venv/bin/python -m pytest packages/lingwen-cross-volume/tests/ --tb=no -q 2>&1 | grep "^FAILED" > /tmp/phase58_before.txt
wc -l /tmp/phase58_before.txt
```
Expected: `16 /tmp/phase58_before.txt`

- [ ] **Step 4: No commit (verification only)**

---

## Task 2: Fix RC2 — Lazy-init Command base class (C1)

**Files:**
- Modify: `packages/lingwen-cli/src/lingwen_cli/commands/base.py:25-29`

This is a "make failing test pass" task (not red-green-refactor since the failing test
already exists). After this commit, all 12 RC2 failures should resolve to PASS.

- [ ] **Step 1: Read current base.py**

```bash
cat packages/lingwen-cli/src/lingwen_cli/commands/base.py
```

- [ ] **Step 2: Run one RC2 test to confirm current failure**

Run:
```bash
.venv/bin/python -m pytest packages/lingwen-cross-volume/tests/test_cli_llm_flags.py::TestCLINewFlags::test_apply_without_use_llm_errors -xvs 2>&1 | tail -10
```
Expected: `RuntimeError: 章节目录不存在: ...` (the failure we're fixing)

- [ ] **Step 3: Replace base.py __init__ with lazy @property pattern**

Edit `packages/lingwen-cli/src/lingwen_cli/commands/base.py` — replace the entire `Command.__init__` and add 3 `@property` methods.

**BEFORE (lines 25-29)**:
```python
    def __init__(self):
        self.paths = ProjectPaths.get()
        max_ch = project_max_chapter(self.paths)
        self.range_parser = RangeParser(all_chapters=max_ch)
        self.formatter = OutputFormatter()
```

**AFTER (replace lines 25-29 + add 3 properties)**:
```python
    def __init__(self):
        # Phase 58: lazy-init paths/range_parser/formatter. Constructing a Command
        # should not require a valid project layout (chapters dir + ProjectPaths.get
        # validation); only executing a command should. Production code accesses
        # these via self.paths.X etc. which triggers resolution on first access.
        # Tests that mock the inner work (BackfillCommand/RippleScanCommand with
        # fully-mocked LLMScanner/Backfiller/storage) can construct without a
        # real project.
        self._paths: ProjectPaths | None = None
        self._range_parser: RangeParser | None = None
        self._formatter: OutputFormatter | None = None

    @property
    def paths(self) -> ProjectPaths:
        """Lazy ProjectPaths singleton (resolved on first access)."""
        if self._paths is None:
            self._paths = ProjectPaths.get()
        return self._paths

    @property
    def range_parser(self) -> RangeParser:
        """Lazy RangeParser (depends on project max chapter)."""
        if self._range_parser is None:
            max_ch = project_max_chapter(self.paths)
            self._range_parser = RangeParser(all_chapters=max_ch)
        return self._range_parser

    @property
    def formatter(self) -> OutputFormatter:
        """Lazy OutputFormatter (no dependencies)."""
        if self._formatter is None:
            self._formatter = OutputFormatter()
        return self._formatter
```

- [ ] **Step 4: Re-run the same RC2 test to confirm it passes**

Run:
```bash
.venv/bin/python -m pytest packages/lingwen-cross-volume/tests/test_cli_llm_flags.py::TestCLINewFlags::test_apply_without_use_llm_errors -xvs 2>&1 | tail -5
```
Expected: `1 passed in <1s` (may need to investigate actual assertion failure if still in `Command.__init__`)

- [ ] **Step 5: Run all 12 RC2 tests**

Run:
```bash
.venv/bin/python -m pytest \
  packages/lingwen-cross-volume/tests/test_cli_llm_flags.py \
  packages/lingwen-cross-volume/tests/test_e2e_llm_backfill.py \
  packages/lingwen-cross-volume/tests/test_scanner_calibration.py \
  packages/lingwen-cross-volume/tests/test_scanner_calibration_feedback.py \
  packages/lingwen-cross-volume/tests/test_backfill_production_execute.py \
  --tb=no -q 2>&1 | tail -5
```
Expected: All 12 previously-failing tests now PASS (suite total = 12+8 = 20 in those files, all green)

- [ ] **Step 6: Verify no existing production code is broken**

Run:
```bash
grep -rn "self\.paths\s*=" packages/lingwen-cli/src/ --include="*.py" 2>/dev/null
grep -rn "self\.range_parser\s*=" packages/lingwen-cli/src/ --include="*.py" 2>/dev/null
grep -rn "self\.formatter\s*=" packages/lingwen-cli/src/ --include="*.py" 2>/dev/null
```
Expected: No matches (all production code is read-only `self.paths.X` access)

- [ ] **Step 7: Verify Phase 5x guards still pass**

Run:
```bash
.venv/bin/python -m pytest tests/ -k phase5 --tb=line -q 2>&1 | tail -3
```
Expected: `158 passed` (Phase 5x baseline preserved)

- [ ] **Step 8: Commit**

```bash
git add packages/lingwen-cli/src/lingwen_cli/commands/base.py
git commit -m "fix(cli): lazy-init Command paths/range_parser/formatter (Phase 58 RC2)
```

---

## Task 3: Fix RC1 — 3 test files path mismatch (C2)

**Files:**
- Modify: `packages/lingwen-cross-volume/tests/test_storage_ripple_action.py` (3 sys.modules patches)
- Modify: `packages/lingwen-cross-volume/tests/test_cascade_broadcast_log.py` (1 monkeypatch)
- Modify: `packages/lingwen-cross-volume/tests/test_chained_cascade.py` (1 import)

After this commit, all 4 RC1 failures should resolve to PASS.

- [ ] **Step 1: Fix test_storage_ripple_action.py — 3 patches**

In `packages/lingwen-cross-volume/tests/test_storage_ripple_action.py`, replace 3 instances of:
- Line 120: `sys.modules["dashboard.cvg_ws"] = mock_module`
- Line 142: same pattern
- Line 158: same pattern

With `apps.studio_api.cvg_ws`. Use `Edit` tool with `replace_all=True` on the literal string `dashboard.cvg_ws` (appears 3 times in this file, no other `dashboard.` refs).

```python
# BEFORE (lines 118-120, 140-142, 156-158):
        # Patch sys.modules because dashboard.cvg_ws is lazy-imported inside
        # _broadcast_ripple_event's try block; the import statement consults
        # sys.modules before falling back to filesystem lookup.
        mock_module = type(sys)("dashboard.cvg_ws")
        mock_module.broadcast = _MockManager().broadcast
        sys.modules["dashboard.cvg_ws"] = mock_module
```

```python
# AFTER (3 occurrences — same shape):
        # Phase 58: patch sys.modules for apps.studio_api.cvg_ws (canonical path
        # used by _broadcast_ripple_event's lazy import; replaces legacy
        # dashboard.cvg_ws which never existed as a Python module).
        mock_module = type(sys)("apps.studio_api.cvg_ws")
        mock_module.broadcast = _MockManager().broadcast
        sys.modules["apps.studio_api.cvg_ws"] = mock_module
```

Easiest path: use `Edit` tool with `old_string="dashboard.cvg_ws"` and `new_string="apps.studio_api.cvg_ws"` and `replace_all=True` on the file.

- [ ] **Step 2: Verify test_storage_ripple_action.py 2 failing tests now pass**

Run:
```bash
.venv/bin/python -m pytest packages/lingwen-cross-volume/tests/test_storage_ripple_action.py --tb=short -q 2>&1 | tail -5
```
Expected: All TestUpdateRippleStatus + TestAppendNodesAtomicBroadcast tests pass (8 total; 2 were failing)

- [ ] **Step 3: Fix test_cascade_broadcast_log.py — 1 monkeypatch**

In `packages/lingwen-cross-volume/tests/test_cascade_broadcast_log.py`, replace line 76:
```python
# BEFORE:
        monkeypatch.setattr(
            "dashboard.cascade_notifier.notify_cascade_update",
            MagicMock(),
        )
```

```python
# AFTER:
        # Phase 58: canonical path is apps.studio_api.cascade_notifier
        # (matches storage.py:358 lazy import).
        monkeypatch.setattr(
            "apps.studio_api.cascade_notifier.notify_cascade_update",
            MagicMock(),
        )
```

- [ ] **Step 4: Verify test_cascade_broadcast_log.py test passes**

Run:
```bash
.venv/bin/python -m pytest packages/lingwen-cross-volume/tests/test_cascade_broadcast_log.py::TestCascadeBroadcastLogStorage::test_append_ripple_persists_broadcast_log -xvs 2>&1 | tail -10
```
Expected: `1 passed`

- [ ] **Step 5: Fix test_chained_cascade.py — 1 import**

In `packages/lingwen-cross-volume/tests/test_chained_cascade.py`, replace line 114:
```python
# BEFORE:
        from dashboard.app import _ripple_to_list_item
```

```python
# AFTER:
        # Phase 58: canonical path is apps.studio_api.app (verified at
        # apps/studio_api/app.py:95 and apps/studio_api/helpers/cvg.py:80).
        from apps.studio_api.app import _ripple_to_list_item
```

- [ ] **Step 6: Verify test_chained_cascade.py test passes**

Run:
```bash
.venv/bin/python -m pytest packages/lingwen-cross-volume/tests/test_chained_cascade.py::TestChainedCascadeAPIFields::test_list_item_includes_parent_and_child_count -xvs 2>&1 | tail -10
```
Expected: `1 passed` (may reveal a real assertion failure if `_ripple_to_list_item` doesn't actually include child_count/parent_ripple_id fields — if so, that becomes a separate Phase 58+ followup, not blocker for this fix)

- [ ] **Step 7: Verify all 16 originally-failing tests now pass**

Run:
```bash
.venv/bin/python -m pytest packages/lingwen-cross-volume/tests/ --tb=no -q 2>&1 | tail -3
```
Expected: `220 passed` (or `220 passed, X skipped` — 0 failures)

- [ ] **Step 8: Cross-cwd verification (Phase 56b2 lesson)**

Run from 3 directories:
```bash
.venv/bin/python -m pytest packages/lingwen-cross-volume/tests/ --tb=no -q 2>&1 | tail -1
cd packages/lingwen-cross-volume && ../../.venv/bin/python -m pytest tests/ --tb=no -q 2>&1 | tail -1
cd tests && ../../.venv/bin/python -m pytest --tb=no -q 2>&1 | tail -1
cd /home/ailearn/projects/LingWen/.claude/worktrees/agent-bump
```
Expected: All 3 cwds show `220 passed` (or similar — 0 failures)

- [ ] **Step 9: Commit**

```bash
git add packages/lingwen-cross-volume/tests/test_storage_ripple_action.py \
        packages/lingwen-cross-volume/tests/test_cascade_broadcast_log.py \
        packages/lingwen-cross-volume/tests/test_chained_cascade.py
git commit -m "fix(cross-volume): align test paths to apps.studio_api.X (Phase 58 RC1)

3 test files patched dashboard.X import/monkeypatch paths to canonical
apps.studio_api.X matching production code in lingwen_cross_volume/storage.py:
- test_storage_ripple_action.py: 3 sys.modules patches for cvg_ws
- test_cascade_broadcast_log.py: 1 monkeypatch for cascade_notifier
- test_chained_cascade.py: 1 import for _ripple_to_list_item

Closes 4 of 16 carryover failures (combined with base.py lazy-init: all 16)."
```

---

## Task 4: Add 5 regression guards + version bump (C3)

**Files:**
- Create: `tests/test_phase58_cross_volume_failures.py`
- Modify: `CLAUDE.md` (version line)

The 5 guards prevent future regressions of the 2 root causes.

- [ ] **Step 1: Write the guards test file**

Create `tests/test_phase58_cross_volume_failures.py` with content:

```python
"""Phase 58: 5 regression guards for cross_volume 16 failures fix.

RC1 (4 fails): tests use legacy dashboard.X import paths; production uses
canonical apps.studio_api.X.
RC2 (12 fails): Command.__init__ eagerly validates ProjectPaths.get().

Run from any cwd:
    .venv/bin/python -m pytest tests/test_phase58_cross_volume_failures.py -v
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_PY = REPO_ROOT / "packages/lingwen-cli/src/lingwen_cli/commands/base.py"

CROSS_VOLUME_TESTS_DIR = REPO_ROOT / "packages/lingwen-cross-volume/tests"


class TestLazyCommandInit:
    """G1+G2: Command.__init__ must NOT eagerly resolve ProjectPaths."""

    def test_g1_no_eager_project_paths_get_in_init(self):
        """base.py Command.__init__ body must not call ProjectPaths.get() directly."""
        content = BASE_PY.read_text(encoding="utf-8")
        # Extract __init__ method body (between "def __init__" and next "def " at same indent)
        match = re.search(r"def __init__\(self\):\n((?:    .*\n)*)", content)
        assert match, "Command.__init__ not found"
        init_body = match.group(1)
        assert "ProjectPaths.get()" not in init_body, (
            "Phase 58 G1: Command.__init__ must lazily init paths "
            "(eager ProjectPaths.get() breaks 12 test constructions)"
        )

    def test_g2_no_eager_project_max_chapter_in_init(self):
        """base.py Command.__init__ body must not call project_max_chapter."""
        content = BASE_PY.read_text(encoding="utf-8")
        match = re.search(r"def __init__\(self\):\n((?:    .*\n)*)", content)
        assert match, "Command.__init__ not found"
        init_body = match.group(1)
        assert "project_max_chapter(" not in init_body, (
            "Phase 58 G2: Command.__init__ must not call project_max_chapter "
            "(depends on paths which is lazy)"
        )


class TestCanonicalPathsInCrossVolumeTests:
    """G3: No 'dashboard.X' import paths in cross_volume test files."""

    def test_g3_no_dashboard_imports_in_cross_volume_tests(self):
        """Cross-volume tests must NOT use legacy dashboard.X import paths.

        Legacy path never existed as a Python module (dashboard/ is Vue frontend).
        Canonical: apps.studio_api.X (matches lingwen_cross_volume/storage.py).
        """
        offenders: list[tuple[str, int, str]] = []
        # Search for dashboard.<python_module> patterns (exclude Vue frontend)
        pattern = re.compile(r'dashboard\.(cvg_ws|cascade_notifier|app)\b')
        for test_file in CROSS_VOLUME_TESTS_DIR.glob("test_*.py"):
            for i, line in enumerate(test_file.read_text(encoding="utf-8").splitlines(), 1):
                if pattern.search(line):
                    offenders.append((str(test_file.relative_to(REPO_ROOT)), i, line.strip()))
        assert not offenders, (
            "Phase 58 G3: cross_volume tests use legacy dashboard.X paths.\n"
            "Canonical is apps.studio_api.X (Phase 56c).\n"
            f"Offenders: {offenders}"
        )


class TestCrossVolumeSuiteGreen:
    """G4+G5: 220/220 cross_volume tests pass after fix."""

    def test_g4_all_cross_volume_tests_pass(self):
        """220/220 cross_volume tests pass (Phase 58 baseline)."""
        result = subprocess.run(
            [
                sys.executable, "-m", "pytest",
                str(CROSS_VOLUME_TESTS_DIR),
                "--tb=no", "-q", "--no-header",
            ],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        # Parse tail for "X failed, Y passed" or "Y passed"
        output = result.stdout + result.stderr
        if " failed" in output:
            match = re.search(r"(\d+) failed", output.splitlines()[-3:] if result.stdout else output)
            if match:
                fail_count = int(match.group(1))
                assert fail_count == 0, (
                    f"Phase 58 G4: {fail_count} cross_volume tests still failing.\n"
                    f"Last 10 lines: {output.splitlines()[-10:]}"
                )
        # Also check exit code
        assert result.returncode == 0, (
            f"Phase 58 G4: cross_volume pytest exit {result.returncode}\n"
            f"Output: {output.splitlines()[-10:]}"
        )

    def test_g5_lazy_command_construction_succeeds_without_chapters_dir(self):
        """BackfillCommand() can be instantiated without a valid chapters dir.

        After RC2 fix, Command.__init__ no longer calls ProjectPaths.get().
        Tests construct BackfillCommand/RippleScanCommand with full mocking;
        they should never hit ProjectPaths validation.
        """
        # Run from worktree root (chapters dir doesn't exist there)
        result = subprocess.run(
            [
                sys.executable, "-c",
                "from lingwen_cli.commands.backfill import BackfillCommand; "
                "from lingwen_cli.commands.ripple_scan import RippleScanCommand; "
                "b = BackfillCommand(); "
                "r = RippleScanCommand(); "
                "print('OK')",
            ],
            capture_output=True, text=True, cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, (
            f"Phase 58 G5: Command construction still requires chapters dir.\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "OK" in result.stdout
```

- [ ] **Step 2: Run guards to verify they pass**

Run:
```bash
.venv/bin/python -m pytest tests/test_phase58_cross_volume_failures.py -v 2>&1 | tail -15
```
Expected: `5 passed`

- [ ] **Step 3: Bump version v54.2 → v54.3 in CLAUDE.md**

Edit `CLAUDE.md` version line. Find the v54.2 reference and add v54.3 mention.

The CLAUDE.md version line begins with:
> `# 灵文 · 工业化小说生产系统`

The version history is in a long single line near the top. Find the substring `v54.2 + Phase 56c` and prepend `v54.3 (Phase 58 cross_volume 16 failures fix — RC2 lazy Command init + RC1 test path alignment)` before `v54.2`:

**BEFORE** (the substring):
```
v54.2 + Phase 56c
```

**AFTER** (prepend new version):
```
v54.3 (Phase 58 cross_volume 16 failures fix — RC2 lazy Command init + RC1 test path alignment) + v54.2 + Phase 56c
```

Use `Edit` tool with `old_string="v54.2 + Phase 56c"` and `new_string="v54.3 (Phase 58 cross_volume 16 failures fix — RC2 lazy Command init + RC1 test path alignment) + v54.2 + Phase 56c"`.

- [ ] **Step 4: Run all phase 5x + Phase 58 guards**

Run:
```bash
.venv/bin/python -m pytest tests/ -k "phase5 or phase58" --tb=line -q 2>&1 | tail -3
```
Expected: `163 passed` (158 phase5x + 5 phase58)

- [ ] **Step 5: Commit**

```bash
git add tests/test_phase58_cross_volume_failures.py CLAUDE.md
git commit -m "test(phase-58): 5 regression guards + v54.2 → v54.3

G1/G2: Command.__init__ no longer eagerly resolves ProjectPaths/get_max_chapter
G3: no legacy dashboard.X imports in cross_volume tests
G4: 220/220 cross_volume tests pass (was 204/220)
G5: BackfillCommand/RippleScanCommand construct without chapters dir

Phase 5x + Phase 58 cumulative: 158 → 163 GREEN."
```

---

## Task 5: Handoff + MEMORY + doc-sync (C4)

**Files:**
- Create: `docs/superpowers/handoffs/2026-09-12-phase-58-cross-volume-failures-handoff.md`
- Modify: `MEMORY.md` (add Phase 58 line + topic pointer)
- Modify: `CURRENT_STATUS.md` (if exists)
- Modify: `BACKLOG.md` (if exists)

- [ ] **Step 1: Write handoff doc**

Create `docs/superpowers/handoffs/2026-09-12-phase-58-cross-volume-failures-handoff.md` with content:

```markdown
# Phase 58 — Cross-Volume 16 Failures Fix Handoff

**Date**: 2026-09-12
**Branch**: `phase-57-p3-archdebt-reading-power`
**Commits**: 4 atomic (C1 base.py lazy / C2 3 test files / C3 guards+v54.3 / C4 handoff)
**New version**: v54.2 → v54.3
**New invariants**: none (test-infra fix)

## Summary

Phase 56c relocated 32 test files but left 16 pre-existing failures unaddressed
(carryover from `0f3239f4` commit pre-Phase 56). Phase 58 closes that debt:
**220/220 cross_volume tests GREEN** (was 204/220).

## Root cause collapse

Handoff hypothesized 5 root causes. Running each test with `pytest -xvs`
revealed **2 root causes**:
- **RC2 (12 fails)**: `Command.__init__` eagerly validated `ProjectPaths.get()`
- **RC1 (4 fails)**: Tests used legacy `dashboard.X` import paths; canonical is `apps.studio_api.X`

## Commits (4 atomic)

| C | Description | Files | Failures fixed |
|---|---|---|---|
| C1 | fix(cli): lazy-init Command paths/range_parser/formatter | base.py | 12 |
| C2 | fix(cross-volume): align test paths to apps.studio_api.X | 3 test files | 4 |
| C3 | test(phase-58): 5 regression guards + v54.2 → v54.3 | test_phase58_*.py + CLAUDE.md | (prevention) |
| C4 | docs(phase-58): handoff + MEMORY + status sync | handoff + MEMORY + status | (docs) |

## Validation gates

| Gate | Result |
|------|--------|
| 220/220 cross_volume tests pass (repo root) | ✓ |
| 220/220 cross_volume tests pass (packages/lingwen-cross-volume) | ✓ |
| 220/220 cross_volume tests pass (packages/lingwen-cross-volume/tests) | ✓ |
| 5/5 phase58 guards GREEN | ✓ |
| 158/158 phase5x guards preserved | ✓ |
| 0 production code breakage (no `self.paths = X` in commands/) | ✓ |

## Lessons (4)

1. **Handoff hypotheses may overcount root causes**: Phase 56c listed 5 RCs for 16 fails; actual is 2. Always re-verify with `pytest -xvs` before designing fixes — the symptom (FAILED test) hides the actual error.

2. **`assert 0 == 1` where `len([]) == 0` is the signature of monkeypatch path mismatch** (Phase 58 RC1): the patch doesn't intercept because the target module doesn't exist (or has different name). Common when migrating canonical paths without auditing all test patches.

3. **Eager construction with side effects is a test smell**: `Command.__init__` calling `ProjectPaths.get()` + `project_max_chapter(self.paths)` violates "construction should be side-effect-free". Lazy `@property` is the textbook fix and makes commands construction pure.

4. **`-xvs` is the canonical debugging tool**: pytest summary `FAILED test_name` doesn't show the actual error. `-xvs` shows the stack trace which is the only way to distinguish RC1 (test path) vs RC2 (Command construction) vs other.
```

- [ ] **Step 2: Update MEMORY.md**

Read current `MEMORY.md`, find the `## Topic Files` section, and add Phase 58 line. Also add a new topic file pointer.

Find:
```
| **Phase 56c P3-ARCHDEBT cross_volume tests relocation (32 files + 5 guards G1-G5 + 3 in-test fixes; v54.1 → v54.2; 220 collect / 204 pass / 16 fail carryover Phase 58+)** | → See `phase-56c-p3-archdebt-cross-volume-tests.md` + handoff `2026-09-12-phase-56c-p3-archdebt-cross-volume-tests-handoff.md` |
```

Add after it:
```
| **Phase 58 cross_volume 16 failures fix (RC1 dashboard→apps.studio_api test paths + RC2 Command lazy-init; v54.2 → v54.3; 220/220 GREEN)** | → See `phase-58-cross-volume-failures.md` + handoff `2026-09-12-phase-58-cross-volume-failures-handoff.md` |
```

Also find the **Version** line:
```
- **Version**: v54.2 (Phase 56c complete; P3-ARCHDEBT 15/15 closed).
```

Change to:
```
- **Version**: v54.3 (Phase 58 cross_volume 16 failures fix CLOSED; P3-ARCHDEBT 15/15 + Phase 58 carryover CLOSED).
```

- [ ] **Step 3: Create topic file pointer**

Create `~/.claude/projects/-home-ailearn-projects-LingWen/memory/phase-58-cross-volume-failures.md` (the global memory location; not in repo) with content:

```markdown
---
name: phase-58-cross-volume-failures
description: Phase 58 lessons — lazy Command init pattern, test path migration pitfalls
metadata:
  type: project
---

Phase 58 closed 16 carryover test failures in cross_volume package. 220/220 GREEN.

**RC1 pattern**: Tests patching `dashboard.X` (Vue frontend, never Python) when production imports `apps.studio_api.X`. Always grep test files for module paths when migrating canonical paths.

**RC2 pattern**: `Command.__init__` eagerly called `ProjectPaths.get()` + `project_max_chapter`. Side-effectful construction breaks test mocking. Fix: lazy `@property` for paths/range_parser/formatter.

**Lesson**: Handoff hypotheses overcount root causes. `pytest -xvs` shows actual stack traces — always run individually before designing fixes.

**Lesson**: `assert 0 == 1` where `len([]) == 0` is the signature of monkeypatch target mismatch — the patch didn't intercept because the target module doesn't exist or has different name.

**Why**: Phase 58 closes the "Phase 56c relocated tests but left 16 failures" debt. v54.3.
**How to apply**: When migrating canonical paths in P3-ARCHDEBT, audit ALL test patches + imports for stale module refs (N.14 lesson 1, variant 11 — path-mismatch in monkeypatch). When designing CLI base classes, prefer lazy @property over eager construction side effects. Related [[phase-56c-p3-archdebt-cross-volume-tests]] / [[phase56b2-cwd-independent-test-paths]] / [[N14-lesson-1-9-pattern-audit]].
```

- [ ] **Step 4: Add topic pointer to MEMORY.md Topic Files**

Find the Phase 56c entry and add this Phase 58 line to the Topic Files section (same as Step 2).

- [ ] **Step 5: Update CURRENT_STATUS.md / BACKLOG.md if they exist**

Check:
```bash
ls collaboration/CURRENT_STATUS.md collaboration/BACKLOG.md 2>&1
```

If they exist, add Phase 58 to "Completed" sections. If not, skip.

- [ ] **Step 6: Commit**

```bash
git add docs/superpowers/handoffs/2026-09-12-phase-58-cross-volume-failures-handoff.md
git commit -m "docs(phase-58): handoff + MEMORY + status sync (v54.2 → v54.3)

4 atomic commits total:
- C1 fix(cli): lazy-init Command paths/range_parser/formatter
- C2 fix(cross-volume): align test paths to apps.studio_api.X
- C3 test(phase-58): 5 regression guards + v54.2 → v54.3
- C4 docs(phase-58): handoff + MEMORY + status sync

220/220 cross_volume tests GREEN (was 204/220).
Phase 5x + Phase 58 cumulative: 158 → 163 GREEN."
```

---

## Self-Review (post-write)

- [ ] **Spec coverage**: Every RC in spec has a task:
  - RC2 → Task 2 (base.py lazy-init) ✓
  - RC1 → Task 3 (3 test files path fix) ✓
  - Regression guards → Task 4 (5 guards) ✓
  - Version bump → Task 4 Step 3 ✓
  - Handoff + MEMORY + status → Task 5 ✓
- [ ] **Placeholder scan**: No "TBD" / "TODO" / "implement later" / "fill in". ✓
- [ ] **Type consistency**: `_paths`, `_range_parser`, `_formatter` consistently used in base.py edits across all references. ✓
- [ ] **Cross-references**: `pytest -xvs` mentioned consistently; `apps.studio_api.X` consistently canonical; `ProjectPaths.get()` consistently the eager init to remove. ✓

---

## Execution Choice

After saving this plan, offer execution choice per writing-plans skill.
