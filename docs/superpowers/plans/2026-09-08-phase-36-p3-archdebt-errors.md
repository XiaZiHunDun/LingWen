# Phase 36 P3-ARCHDEBT (errors pilot) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate `infra/errors.py` (380 lines, 23 public symbols, 14 consumers) to `packages/lingwen-errors/` as Phase 36 pilot for P3-ARCHDEBT, with full cutover (delete infra/errors.py) + invariant #51 NEW + guard-minimal regression testing.

**Architecture:** Single-file workspace package `packages/lingwen-errors/` with `lingwen_errors/__init__.py` containing all 380 lines (1:1 mapping from `infra/errors.py`). Zero workspace deps (leaf package). 6 atomic commits (C0-C5) plus master prelude P1 (already done 61a35b56). Each consumer migration verified via 4-grep audit matrix (Phase 32+34+35 lessons applied).

**Tech Stack:** Python 3.12+ / uv workspace / Hatchling build / pytest / ruff

---

## File Structure

### New files
| Path | Purpose |
|---|---|
| `packages/lingwen-errors/pyproject.toml` | Hatchling build; requires-python>=3.11; zero workspace deps |
| `packages/lingwen-errors/src/lingwen_errors/__init__.py` | 380 lines (1:1 from `infra/errors.py`) |
| `tests/test_phase36_lingwen_errors.py` | 6 regression guards |

### Modified files
| Path | Purpose |
|---|---|
| `pyproject.toml` (root) | Add `packages/lingwen-errors` to `[tool.uv.workspace] members` + `lingwen-errors = { workspace = true }` to `[tool.uv.sources]` |
| `packages/lingwen-quality/src/lingwen_quality/consistency/checker_feedback.py` | sed update import |
| `packages/lingwen-quality/src/lingwen_quality/consistency/creative_whitelist.py` | sed update import |
| `packages/lingwen-world-model/src/lingwen_world_model/character_snapshot.py` | sed update import (SnapshotError) |
| `packages/lingwen-world-model/src/lingwen_world_model/foreshadow_snapshot.py` | sed update import (SnapshotError) |
| `packages/lingwen-pipeline/src/lingwen_pipeline/state_machine.py` | sed update import |
| `packages/lingwen-llm/src/lingwen_llm/providers/base.py` | sed update import |
| `infra/__init__.py` | sed update import |
| `infra/health.py` | sed update import |
| `infra/llm_cache.py` | sed update import |
| `infra/permission.py` | sed update import |
| `infra/schema.py` | sed update import |
| `infra/tool.py` | sed update import |
| `infra/types.py` | sed update import |
| `infra/util/retry.py` | sed update import |
| `tests/test_phase18_10_stale_imports.py` | Update stale-list line 19: `"infra.errors"` → `"lingwen_errors"` |
| `.lingwen/architecture.yml` | version 34.0 → 35.0; add I051 invariant |
| `CLAUDE.md` | Add v35.0 entry + I051 row in 架构不变量 table |
| `collaboration/CURRENT_STATUS.md` | Phase 36 status update |
| `collaboration/BACKLOG.md` | Phase 36 entry; P3-ARCHDEBT 1/5 → closed |

### Deleted files
| Path | Purpose |
|---|---|
| `infra/errors.py` | Original location; migrated to packages/lingwen-errors/src/lingwen_errors/__init__.py |

---

## Task 0: Baseline capture + worktree environment setup

**Files:** None modified

- [ ] **Step 1: Verify worktree exists at expected path**

```bash
cd /home/ailearn/projects/LingWen
git worktree list | grep phase-36-p3-archdebt-errors
```

Expected: shows `.worktrees/phase-36-p3-archdebt-errors  61a35b56 [phase-36-p3-archdebt-errors]`

- [ ] **Step 2: Bootstrap worktree venv (Phase 31+32 lesson)**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
uv sync --all-packages --offline
uv pip install --offline pytest pytest-asyncio pytest-timeout pytest-cov pytest-env pytest-metadata pytest-json-report psutil
```

Expected: `uv sync` succeeds; `uv pip install` adds 9 packages. If `--offline` flag fails, retry without it.

- [ ] **Step 3: Capture baseline test counts (Phase 34 lesson 4 — validate against drift)**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
./.venv/bin/python -m pytest packages/lingwen-world-model/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-core/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-got/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest apps/studio_api/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-quality/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-pipeline/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-llm/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest tests/test_phase18_10_stale_imports.py --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m ruff check . 2>&1 | tail -3
```

Expected: All packages show `XXX passed` or `XXX passed, Y skipped` (no failures). Record exact counts in plan-tracker.md (or reply). Pre-existing ruff errors (3 in unrelated files per Phase 34 baseline) are acceptable.

- [ ] **Step 4: Verify C0 spec commit is HEAD of worktree**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
git log -1 --oneline
```

Expected: `8401ff70 docs(phase-36): spec for lingwen-errors package (P3-ARCHDEBT pilot)`

---

## Task 1: C1 — Scaffold lingwen-errors package

**Files:**
- Create: `packages/lingwen-errors/pyproject.toml`
- Create: `packages/lingwen-errors/src/lingwen_errors/__init__.py`
- Modify: `pyproject.toml` (root)

- [ ] **Step 1: Create packages/lingwen-errors/pyproject.toml**

```bash
mkdir -p packages/lingwen-errors/src/lingwen_errors
```

Then create `packages/lingwen-errors/pyproject.toml` with this exact content:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "lingwen-errors"
version = "0.1.0"
description = "LingWen canonical error base classes (Phase 36 P3-ARCHDEBT pilot)"
requires-python = ">=3.11"
dependencies = []

[tool.hatch.build.targets.wheel]
packages = ["src/lingwen_errors"]
```

- [ ] **Step 2: Copy infra/errors.py to packages/lingwen-errors/src/lingwen_errors/__init__.py (1:1)**

```bash
cp infra/errors.py packages/lingwen-errors/src/lingwen_errors/__init__.py
```

Verify byte-for-byte copy:

```bash
diff infra/errors.py packages/lingwen-errors/src/lingwen_errors/__init__.py
```

Expected: no output (files identical).

- [ ] **Step 3: Verify symbol count (Phase 34+35 lesson 3 — verify before writing regression tests)**

```bash
awk '/^__all__ = \[/, /^\]/' packages/lingwen-errors/src/lingwen_errors/__init__.py | grep -c '"'
```

Expected: `23` (matches `infra/errors.py` __all__)

- [ ] **Step 4: Add packages/lingwen-errors to root pyproject.toml workspace members**

Edit root `pyproject.toml`. Locate `[tool.uv.workspace]` block and add `"packages/lingwen-errors"` after `"packages/lingwen-world-model"`:

```toml
[tool.uv.workspace]
members = [
    "packages/lingwen-core",
    "packages/lingwen-storage",
    "packages/lingwen-llm",
    "packages/lingwen-memory",
    "packages/lingwen-prompt",
    "packages/lingwen-pipeline",
    "packages/lingwen-quality",
    "packages/lingwen-cli",
    "packages/lingwen-shared",
    "packages/lingwen-creator",
    "packages/lingwen-got",
    "packages/lingwen-world-model",
    "packages/lingwen-errors",   # ★ Phase 36 NEW
    "apps/studio_api",
]
```

Also add to `[tool.uv.sources]` block (after the existing `lingwen-world-model` entry):

```toml
[tool.uv.sources]
# ... existing entries ...
lingwen-world-model = { workspace = true }
lingwen-errors = { workspace = true }   # ★ Phase 36 NEW
```

- [ ] **Step 5: Sync workspace + verify import (Phase 34 lesson — declaration BEFORE uv sync)**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
uv sync --all-packages --offline
./.venv/bin/python -c "import lingwen_errors; print(f'symbols={len(lingwen_errors.__all__)}')"
```

Expected output: `symbols=23`

- [ ] **Step 6: Verify workspace declarations visible**

```bash
grep "lingwen-errors" pyproject.toml
```

Expected: 2 hits (`packages/lingwen-errors` in members + `lingwen-errors = { workspace = true }` in sources)

- [ ] **Step 7: Commit C1**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
git status --short   # should show 3 files: pyproject.toml M, packages/lingwen-errors/pyproject.toml A, packages/lingwen-errors/src/lingwen_errors/__init__.py A
git add pyproject.toml packages/lingwen-errors/pyproject.toml packages/lingwen-errors/src/lingwen_errors/__init__.py
git status --short   # confirm all staged (no ^ M entries!)
git commit -m "$(cat <<'EOF'
chore(packages): scaffold lingwen-errors (Phase 36 P3-ARCHDEBT pilot)

Create packages/lingwen-errors workspace package:
- pyproject.toml: Hatchling build; requires-python>=3.11; zero deps (leaf)
- src/lingwen_errors/__init__.py: 380 lines, 23 __all__ symbols (1:1 copy from infra/errors.py)

Wire into uv workspace:
- pyproject.toml: add 'packages/lingwen-errors' to [tool.uv.workspace] members
- pyproject.toml: add 'lingwen-errors = { workspace = true }' to [tool.uv.sources]

Verified: import lingwen_errors succeeds; len(__all__) == 23.
Workspace declaration BEFORE uv sync (Phase 34 N.14 lesson 4).
EOF
)"
```

---

## Task 2: C2 — Migrate 14 consumers (2-pass sed + ruff --fix + audit)

**Files:** 14 consumer files modified (per spec §5.1)

- [ ] **Step 1: Pre-audit — verify all 14 consumers match expectation**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
grep -rln "from infra\.errors\|import infra\.errors" --include="*.py" . | grep -v "^./infra/errors.py$" | sort
```

Expected: 14 files matching spec §5.1 list. If mismatch, STOP and reconcile.

- [ ] **Step 2: Apply 4-grep audit matrix BEFORE migration (Phase 32+34+35 lessons)**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors

# Pattern 1: Literal dotted path
grep -rn "from infra\.errors\b" --include="*.py" . | wc -l
# Expected: ~14 (one per consumer file; some files may have multiple imports)

# Pattern 2: Relative same-package
grep -rn "from \.errors\b" infra/ packages/ --include="*.py" | wc -l
# Expected: 0 (errors is leaf)

# Pattern 3: Relative parent-package
grep -rn "from \.\.errors\b" infra/ packages/ --include="*.py" | wc -l
# Expected: 0 (errors is leaf)

# Pattern 4: Filesystem path string literals
grep -rn "infra/errors" --include="*.py" . | wc -l
# Expected: 0 (no Path(...) refs)

# Pattern 5: Function-body indented imports
grep -rn "^    from \|^        from " infra/ packages/ --include="*.py" | grep "infra\.errors" | wc -l
# Expected: 0 (errors rarely used as function-body import)
```

If any pattern returns unexpected non-zero, STOP and add to consumer migration list.

- [ ] **Step 3: Build the consumer file list for sed**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
CONSUMERS=$(grep -rln "from infra\.errors\|import infra\.errors" --include="*.py" . | grep -v "^./infra/errors.py$" | grep -v "tests/test_phase36")
echo "$CONSUMERS" | tee /tmp/phase36_consumers.txt
wc -l /tmp/phase36_consumers.txt
```

Expected: 14 files in `/tmp/phase36_consumers.txt`. The `tests/test_phase36` exclusion is for the future guard file (doesn't exist yet, but defensive).

- [ ] **Step 4: 2-pass sed (Phase 35 lesson 5 — space + dot separators)**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors

# Pass 1: space variant ("from infra.errors import X" → "from lingwen_errors import X")
while IFS= read -r file; do
  sed -i 's|from infra\.errors |from lingwen_errors |g' "$file"
done < /tmp/phase36_consumers.txt

# Pass 2: dot variant ("from infra.errors.X" → "from lingwen_errors.X")
while IFS= read -r file; do
  sed -i 's|from infra\.errors\.|from lingwen_errors.|g' "$file"
done < /tmp/phase36_consumers.txt
```

- [ ] **Step 5: Apply ruff --fix proactively (Phase 34 lesson 5 — I001 cleanup)**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
ruff check --fix packages/lingwen-quality/ packages/lingwen-world-model/ packages/lingwen-pipeline/ packages/lingwen-llm/ infra/ 2>&1 | tail -10
```

Expected: fixes I001 violations from import order changes; possibly 0 fixes if order was already correct.

- [ ] **Step 6: Verify NO remaining infra.errors imports (excluding self + future guard)**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
grep -rln "from infra\.errors\|import infra\.errors" --include="*.py" . | grep -v "^./infra/errors.py$" | grep -v "tests/test_phase36"
```

Expected: empty output (0 hits).

- [ ] **Step 7: Verify SnapshotError migration to lingwen-world-model consumers**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
grep -n "SnapshotError" packages/lingwen-world-model/src/lingwen_world_model/character_snapshot.py packages/lingwen-world-model/src/lingwen_world_model/foreshadow_snapshot.py
```

Expected: each file imports `SnapshotError` from `lingwen_errors` (NOT from `infra.errors`).

- [ ] **Step 8: Run spot-check tests for migrated packages**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
./.venv/bin/python -m pytest packages/lingwen-world-model/tests/test_character_snapshot.py packages/lingwen-world-model/tests/test_foreshadow_snapshot.py --tb=short -q 2>&1 | tail -5
```

Expected: tests pass (SnapshotError import works through new package).

- [ ] **Step 9: Explicit git add per-file (Phase 35 lesson 1 — git mv + sed UNSTAGED prevention)**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
git status --short
# Should show all 14 files as modified. Use explicit add:
git add -- \
  packages/lingwen-quality/src/lingwen_quality/consistency/checker_feedback.py \
  packages/lingwen-quality/src/lingwen_quality/consistency/creative_whitelist.py \
  packages/lingwen-world-model/src/lingwen_world_model/character_snapshot.py \
  packages/lingwen-world-model/src/lingwen_world_model/foreshadow_snapshot.py \
  packages/lingwen-pipeline/src/lingwen_pipeline/state_machine.py \
  packages/lingwen-llm/src/lingwen_llm/providers/base.py \
  infra/__init__.py \
  infra/health.py \
  infra/llm_cache.py \
  infra/permission.py \
  infra/schema.py \
  infra/tool.py \
  infra/types.py \
  infra/util/retry.py

git status --short   # confirm all show as staged (M prefix, no ^ M)
```

- [ ] **Step 10: Verify scope before commit (Phase 35 lesson 2 — amend scope drift prevention)**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
git diff --cached --stat
```

Expected: 14 files changed, ~14 insertions(+) ~14 deletions(-) (each file has ~1 import line changed).

- [ ] **Step 11: Commit C2**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
git commit -m "$(cat <<'EOF'
refactor(consumers): migrate 14 errors consumers to lingwen_errors (Phase 36)

2-pass sed migration (space + dot variants per Phase 35 lesson 5):
- 'from infra.errors ' → 'from lingwen_errors '
- 'from infra.errors.X' → 'from lingwen_errors.X'

14 consumer files:
- 6 packages: lingwen-quality(2) + lingwen-world-model(2; SnapshotError) + lingwen-pipeline(1) + lingwen-llm(1)
- 8 infra: __init__.py + health + llm_cache + permission + schema + tool + types + util/retry

SnapshotError stays in errors package (2 active consumers in lingwen-world-model).
ruff --fix applied proactively for I001 violations.

Pre-audit (4-grep matrix per Phase 32+34+35 lessons):
- Literal dotted path: 14 hits → 0
- Relative same-package: 0 (leaf)
- Relative parent-package: 0 (leaf)
- Filesystem path strings: 0

Verified: grep infra.errors returns 0 hits after migration.
EOF
)"
```

---

## Task 3: C3 — Delete infra/errors.py

**Files:**
- Delete: `infra/errors.py`

- [ ] **Step 1: Verify infra/errors.py still exists (should)**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
test -f infra/errors.py && echo "EXISTS" || echo "MISSING"
```

Expected: `EXISTS`

- [ ] **Step 2: Verify infra/errors.py has zero remaining consumers**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
grep -rln "from infra\.errors\|import infra\.errors" --include="*.py" . | grep -v "^./infra/errors.py$"
```

Expected: empty output (0 hits — C2 already verified).

- [ ] **Step 3: Delete infra/errors.py**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
git rm infra/errors.py
```

- [ ] **Step 4: Verify deletion**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
test -f infra/errors.py && echo "STILL EXISTS" || echo "DELETED"
git status --short | grep "D.*infra/errors.py"
```

Expected: `DELETED`; git status shows `D  infra/errors.py`

- [ ] **Step 5: Commit C3**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
git commit -m "$(cat <<'EOF'
chore(infra): delete infra/errors.py (Phase 36 P3-ARCHDEBT pilot)

Full cutover — no PHASE-COMPAT shim (matches Phase 32/34/35 pattern).
All 14 consumers migrated to lingwen_errors (C2).

Canonical location: packages/lingwen-errors/src/lingwen_errors/__init__.py
(23 __all__ symbols: BaseError + 7 utils + 15 subclasses including SnapshotError)
EOF
)"
```

---

## Task 4: C4 — Bump v35.0 + invariant #51 NEW

**Files:**
- Modify: `.lingwen/architecture.yml`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Verify I051 slot is free (Phase 35 lesson 4)**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
grep -n "id: I0" .lingwen/architecture.yml
```

Expected: shows I001-I005 + I048 + I049 + I050 (no I051 yet). If I051 already exists, STOP and reconcile.

- [ ] **Step 2: Update .lingwen/architecture.yml — version + I051 invariant**

Edit `.lingwen/architecture.yml`. Update the `version:` line (first line of file) from `"34.0"` to `"35.0"` and prepend a new comment block describing Phase 36 (mirror the Phase 35 block format — see existing version comment for style).

Then locate the `invariants:` block and add I051 entry after I050:

```yaml
    - id: I050
      ...
    - id: I051   # ★ Phase 36 NEW
      constraint: "packages/lingwen-errors/ 是错误基类系统的唯一实包；infra.errors.* 路径非法 (Phase 36+)"
```

(Match the exact YAML structure of I048-I050 rows — same key order, same indentation, same style.)

- [ ] **Step 3: Update CLAUDE.md — v35.0 entry + I051 row**

Edit `CLAUDE.md`. Add a new "✅ v35.0 P3-ARCHDEBT (errors pilot)" entry after the v34.0 entry (mirror v34.0 format). Include:
- Phase date
- Branch
- Phase scope (errors only)
- Files migrated
- Validation gates passed
- Carryover closure (P3-ARCHDEBT 1/5 → closed)

Also add `I051` row in the 架构不变量 table:

```markdown
| I051 | `packages/lingwen-errors/` 是错误基类系统的唯一实包；`infra.errors.*` 路径非法 (Phase 36+) |
```

- [ ] **Step 4: Verify I051 appears in both files**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
grep -c "I051" .lingwen/architecture.yml CLAUDE.md
```

Expected: each file shows count ≥1.

- [ ] **Step 5: Verify version bump**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
head -1 .lingwen/architecture.yml | grep -o '"[0-9]\+\.[0-9]\+"'
```

Expected: `"35.0"`

- [ ] **Step 6: Stage + verify scope + commit C4**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
git add .lingwen/architecture.yml CLAUDE.md
git diff --cached --stat
# Expected: 2 files changed, ~10 insertions, ~few deletions
git commit -m "$(cat <<'EOF'
chore(infra): bump v35.0 + invariant #51 (lingwen-errors canonical) [Phase 36]

- .lingwen/architecture.yml: version 34.0 → 35.0; add I051 invariant row
- CLAUDE.md: v35.0 entry + I051 row in 架构不变量 table

Invariant #51: 'packages/lingwen-errors/ 是错误基类系统的唯一实包；
infra.errors.* 路径非法 (Phase 36+)'.

Enforced by tests/test_phase36_lingwen_errors.py (C5) + grep audit gate.
EOF
)"
```

---

## Task 5: C5 — Regression guards + doc sync + stale-list update

**Files:**
- Create: `tests/test_phase36_lingwen_errors.py` (6 tests)
- Modify: `tests/test_phase18_10_stale_imports.py` (line 19 stale-list update)
- Modify: `collaboration/CURRENT_STATUS.md` (Phase 36 status)
- Modify: `collaboration/BACKLOG.md` (Phase 36 entry)

- [ ] **Step 1: Create tests/test_phase36_lingwen_errors.py with 6 guards**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
```

Create file `tests/test_phase36_lingwen_errors.py` with this exact content:

```python
"""Phase 36 P3-ARCHDEBT (errors pilot) regression guards.

Verifies lingwen-errors package canonicalization (v35.0, invariant #51).
Pattern: Phase 34+35 guard tests, simplified for single-file pilot.

Skip files (N.14 lesson 6 — guard self-trigger):
- tests/test_phase36_lingwen_errors.py (this file)
- tests/test_phase18_10_stale_imports.py (contains "infra.errors" in stale-list)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent

SKIP_FILES = {
    REPO_ROOT / "tests" / "test_phase36_lingwen_errors.py",
    REPO_ROOT / "tests" / "test_phase18_10_stale_imports.py",
}


def _is_skipped(path: Path) -> bool:
    return path in SKIP_FILES


# ---------------------------------------------------------------------------
# G1: lingwen-errors package scaffolding exists
# ---------------------------------------------------------------------------


def test_lingwen_errors_package_exists():
    """Verify packages/lingwen-errors/ scaffold exists."""
    pkg_root = REPO_ROOT / "packages" / "lingwen-errors"
    pyproject = pkg_root / "pyproject.toml"
    init_file = pkg_root / "src" / "lingwen_errors" / "__init__.py"

    assert pkg_root.is_dir(), f"missing {pkg_root}"
    assert pyproject.is_file(), f"missing {pyproject}"
    assert init_file.is_file(), f"missing {init_file}"


def test_lingwen_errors_init_imports():
    """Verify lingwen_errors imports + 23 __all__ symbols."""
    import lingwen_errors

    assert hasattr(lingwen_errors, "__all__"), "missing __all__"
    assert len(lingwen_errors.__all__) == 23, (
        f"expected 23 symbols, got {len(lingwen_errors.__all__)}: {lingwen_errors.__all__}"
    )

    # Spot-check key symbols
    assert hasattr(lingwen_errors, "BaseError")
    assert hasattr(lingwen_errors, "create")
    assert hasattr(lingwen_errors, "SnapshotError")
    assert hasattr(lingwen_errors, "ValidationError")
    assert hasattr(lingwen_errors, "NotFoundError")


# ---------------------------------------------------------------------------
# G2: infra/errors.py deleted + invariant #51 enforced
# ---------------------------------------------------------------------------


def test_infra_errors_deleted():
    """Verify infra/errors.py removed (full cutover)."""
    infra_errors = REPO_ROOT / "infra" / "errors.py"
    assert not infra_errors.exists(), f"{infra_errors} should not exist after Phase 36"


def test_workspace_member_declared():
    """Verify root pyproject.toml declares packages/lingwen-errors in workspace."""
    root_pyproject = REPO_ROOT / "pyproject.toml"
    content = root_pyproject.read_text(encoding="utf-8")

    # Check workspace members declaration
    assert "packages/lingwen-errors" in content, (
        "pyproject.toml missing 'packages/lingwen-errors' in [tool.uv.workspace] members"
    )
    # Check workspace sources declaration
    assert re.search(r"lingwen-errors\s*=\s*\{\s*workspace\s*=\s*true\s*\}", content), (
        "pyproject.toml missing 'lingwen-errors = { workspace = true }' in [tool.uv.sources]"
    )


def test_no_infra_errors_references():
    """Verify no Python file imports from infra.errors (excluding skip files)."""
    result = subprocess.run(
        [
            "grep",
            "-rln",
            "--include=*.py",
            ".",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    # grep returns 1 when no matches; capture all output regardless
    files = [f for f in result.stdout.splitlines() if f]

    offenders = []
    pattern = re.compile(r"\b(infra\.errors|from\s+infra\.errors|import\s+infra\.errors)\b")

    for rel_path in files:
        path = Path(rel_path)
        if _is_skipped(path):
            continue
        # Only check actual Python files (grep --include already filters)
        if path.suffix != ".py":
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if pattern.search(content):
            offenders.append(rel_path)

    assert not offenders, (
        f"Found infra.errors references (forbidden by invariant #51):\n"
        + "\n".join(f"  - {p}" for p in offenders)
    )


# ---------------------------------------------------------------------------
# G3: SnapshotError migration to lingwen-world-model
# ---------------------------------------------------------------------------


def test_snapshot_error_migrated():
    """Verify SnapshotError migrated + world-model consumers use lingwen_errors."""
    import lingwen_errors

    # SnapshotError must be in lingwen_errors
    assert "SnapshotError" in lingwen_errors.__all__
    assert issubclass(lingwen_errors.SnapshotError, lingwen_errors.BaseError)

    # Both world-model consumers must import from lingwen_errors (NOT infra.errors)
    wm_root = REPO_ROOT / "packages" / "lingwen-world-model" / "src" / "lingwen_world_model"
    char_snap = wm_root / "character_snapshot.py"
    fore_snap = wm_root / "foreshadow_snapshot.py"

    for f in [char_snap, fore_snap]:
        content = f.read_text(encoding="utf-8")
        assert "from lingwen_errors" in content, (
            f"{f.name} should import from lingwen_errors"
        )
        assert "from infra.errors" not in content, (
            f"{f.name} should NOT import from infra.errors (forbidden by I051)"
        )
```

- [ ] **Step 2: Run guards — verify all 6 PASS**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
./.venv/bin/python -m pytest tests/test_phase36_lingwen_errors.py -v
```

Expected: `6 passed`

- [ ] **Step 3: Update tests/test_phase18_10_stale_imports.py stale-list**

Edit `tests/test_phase18_10_stale_imports.py` line 19: replace `"infra.errors",` with `"lingwen_errors",` (and add a comment if needed):

```python
        "infra.errors",       # → Phase 36 update below
```
becomes
```python
        "lingwen_errors",     # Phase 36: was "infra.errors" (now deleted; canonicalized)
```

(Read the file first to confirm exact line 19 content, then apply Edit. Verify line 19 after edit.)

- [ ] **Step 4: Verify updated stale-import guard still passes**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
./.venv/bin/python -m pytest tests/test_phase18_10_stale_imports.py -v
```

Expected: passes (was passing pre-Phase 36 with `infra.errors` in list; should still pass with `lingwen_errors`).

- [ ] **Step 5: Update collaboration/CURRENT_STATUS.md + collaboration/BACKLOG.md**

Read both files first. Add Phase 36 status entry to CURRENT_STATUS.md (Phase 36 completed section). Add Phase 36 entry to BACKLOG.md (move P3-ARCHDEBT 1/5 from "open" to "closed"). Match existing Phase 34/35 entries' style.

- [ ] **Step 6: Run full validation gate matrix**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors

# G1 ruff
./.venv/bin/python -m ruff check . 2>&1 | tail -5

# G2 phase36 guards
./.venv/bin/python -m pytest tests/test_phase36_lingwen_errors.py --tb=no -q 2>&1 | tail -3

# G3-G8 baselines (compare to Task 0 Step 3 baseline counts)
./.venv/bin/python -m pytest packages/lingwen-world-model/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-core/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-got/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest apps/studio_api/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-quality/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-pipeline/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-llm/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest tests/test_phase18_10_stale_imports.py --tb=no -q 2>&1 | tail -3
```

Expected:
- G1 ruff: same as baseline (3 pre-existing errors acceptable, no NEW errors)
- G2 phase36: 6 passed
- G3-G8: matches baseline counts from Task 0 Step 3 (no regressions)
- G9 stale-import: passes

If any baseline drops by 1+, STOP and investigate before committing.

- [ ] **Step 7: Stage + verify scope + commit C5**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
git status --short
git add tests/test_phase36_lingwen_errors.py tests/test_phase18_10_stale_imports.py collaboration/CURRENT_STATUS.md collaboration/BACKLOG.md
git diff --cached --stat
git commit -m "$(cat <<'EOF'
test(phase-36): regression guards + doc sync (v35.0 P3-ARCHDEBT pilot)

Regression guards (tests/test_phase36_lingwen_errors.py — 6 tests):
1. test_lingwen_errors_package_exists — packages/lingwen-errors/ scaffold
2. test_lingwen_errors_init_imports — import works; __all__ == 23
3. test_infra_errors_deleted — infra/errors.py removed
4. test_workspace_member_declared — workspace members + sources updated
5. test_no_infra_errors_references — grep audit (excluding skip files)
6. test_snapshot_error_migrated — SnapshotError in lingwen_errors + world-model consumers

Stale-import guard update:
- tests/test_phase18_10_stale_imports.py line 19: "infra.errors" → "lingwen_errors"

Skip files (N.14 lesson 6 — guard self-trigger):
- tests/test_phase36_lingwen_errors.py (this file)
- tests/test_phase18_10_stale_imports.py (stale-list reference)

Doc sync:
- collaboration/CURRENT_STATUS.md: Phase 36 status
- collaboration/BACKLOG.md: Phase 36 entry; P3-ARCHDEBT 1/5 → closed

Validation: 8 gates GREEN (ruff clean, 6 phase36 guards, 7 baselines preserved).
EOF
)"
```

---

## Task 6: ff-merge to master + worktree cleanup

**Files:** None (git operations only)

- [ ] **Step 1: Verify all Phase 36 commits on worktree branch**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
git log --oneline master..HEAD
```

Expected: 6 commits (C0 spec + C1 scaffold + C2 migrate + C3 delete + C4 invariant + C5 guards)

- [ ] **Step 2: Push worktree branch to origin (Phase 35 pattern)**

```bash
cd /home/ailearn/projects/LingWen/.worktrees/phase-36-p3-archdebt-errors
git push -u origin phase-36-p3-archdebt-errors
```

Expected: 6 commits pushed to remote.

- [ ] **Step 3: ff-merge to master**

```bash
cd /home/ailearn/projects/LingWen
git checkout master
git merge --ff-only phase-36-p3-archdebt-errors
git log -1 --oneline
```

Expected: master HEAD now points to Phase 36 C5 (test(phase-36): regression guards...)

- [ ] **Step 4: Push master to origin**

```bash
cd /home/ailearn/projects/LingWen
git push origin master
```

- [ ] **Step 5: Remove worktree + delete branch**

```bash
cd /home/ailearn/projects/LingWen
git worktree remove .worktrees/phase-36-p3-archdebt-errors
git branch -d phase-36-p3-archdebt-errors
git worktree list
git branch -a | grep phase-36
```

Expected: worktree removed; branch deleted; no phase-36 references in either output.

- [ ] **Step 6: Update MEMORY.md (outside worktree)**

Edit `~/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md`:
- Master HEAD: `61a35b56` → Phase 36 C5 SHA
- Carryover closure: P3-ARCHDEBT 1/5 → CLOSED
- Add Phase 36 lessons (if any new)

- [ ] **Step 7: Write Phase 36 handoff doc**

Write `docs/superpowers/handoffs/2026-09-08-phase-36-p3-archdebt-errors-handoff.md` (mirror Phase 34/35 format). Commit on master.

---

## Self-Review Checklist

After completing the plan, verify:

- [x] **Spec coverage**: Each spec section maps to a task:
  - §1 Summary → Task 1+2+3
  - §2 Goals → Tasks 1, 2, 3, 4, 5
  - §3 Non-Goals → respected throughout (no internal restructuring, no new functional tests, no other P3 modules)
  - §4.1 Package layout → Task 1
  - §4.2 Dependency direction → Task 1 (zero deps)
  - §4.3 Migration pattern → Tasks 2, 3
  - §5.1 Consumer list → Task 2 (14 sites verified)
  - §5.2 Audit matrix → Task 2 Step 2
  - §5.3 Workspace wiring → Task 1 Step 4
  - §5.4 New pyproject.toml → Task 1 Step 1
  - §5.5 Stale-import guard → Task 5 Step 3
  - §6.1 Regression guards → Task 5 Step 1
  - §6.3 Validation gates → Task 5 Step 6
  - §7 Commit chain → Tasks 1, 2, 3, 4, 5
  - §8 Invariant #51 → Task 4
  - §9 Risks → mitigated across all tasks
- [x] **Placeholder scan**: No TBD/TODO/FIXME in code steps. Audit commands show expected counts.
- [x] **Type consistency**: `__all__` symbols match spec §4.1 (BaseError + 7 utils + 15 subclasses = 23).
- [x] **Code completeness**: Every code step shows full content (no "similar to Task N").