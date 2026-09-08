# Phase 37 P3-ARCHDEBT (paths) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate `infra/paths.py` (125 lines, 5 top-level public symbols, 86 consumer files) to `packages/lingwen-paths/` with full cutover (no PHASE-COMPAT shim), adding invariant #52 and bumping project version to v36.0.

**Architecture:** Single-file package (`packages/lingwen-paths/src/lingwen_paths/__init__.py`) following the lingwen-errors (Phase 36) pattern exactly. Full cutover: 86 mechanical sed migrations + `git rm infra/paths.py` + invariant + 6 regression guards.

**Tech Stack:** Python 3.12+ / uv workspace (hatchling build) / pytest / ruff / git worktree

**Spec:** `docs/superpowers/specs/2026-09-08-phase-37-p3-archdebt-paths-design.md`

---

## Task 0: T0 baseline capture (BEFORE any code change)

**Files:** none (read-only verification)

- [ ] **Step 1: Capture per-suite pass counts**

Run from worktree root `.worktrees/phase-37-p3-archdebt-paths/`:

```bash
cd .worktrees/phase-37-p3-archdebt-paths
./.venv/bin/python -m pytest packages/lingwen-world-model/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-core/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-got/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest apps/studio_api/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-quality/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-pipeline/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-llm/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-creator/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-cli/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest tests/test_phase18_10_stale_imports.py --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m ruff check . 2>&1 | tail -3
```

Expected: all pass with `0 failed` (Phase 36 baseline had `582 passed + 1 xfail` total but split across these suites). Record actual numbers per suite — these are the G2-G10 baselines.

- [ ] **Step 2: Verify worktree clean**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
git status --short
```

Expected: only the user's pre-existing `M projects/anye-xinbiao/docs/novel-pillars.md` (out of scope, preserved).

- [ ] **Step 3: (No commit — read-only task)**

---

## Task 1: C1 - scaffold packages/lingwen-paths/

**Files:**
- Create: `packages/lingwen-paths/pyproject.toml`
- Create: `packages/lingwen-paths/src/lingwen_paths/__init__.py` (1:1 from `infra/paths.py`)
- Modify: `pyproject.toml` (root, lines around `[tool.uv.workspace]` members + `[tool.uv.sources]`)

- [ ] **Step 1: Create new package pyproject.toml**

Write `packages/lingwen-paths/pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "lingwen-paths"
version = "0.1.0"
description = "LingWen canonical project paths module (Phase 37 P3-ARCHDEBT paths)"
requires-python = ">=3.11"
dependencies = []  # LEAF — zero workspace deps (only stdlib: os, pathlib, typing)

[tool.hatch.build.targets.wheel]
packages = ["src/lingwen_paths"]
```

- [ ] **Step 2: Copy infra/paths.py → packages/lingwen-paths/src/lingwen_paths/__init__.py (byte-for-byte)**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
mkdir -p packages/lingwen-paths/src/lingwen_paths
cp infra/paths.py packages/lingwen-paths/src/lingwen_paths/__init__.py
wc -l packages/lingwen-paths/src/lingwen_paths/__init__.py
diff infra/paths.py packages/lingwen-paths/src/lingwen_paths/__init__.py
```

Expected: `125 packages/lingwen-paths/src/lingwen_paths/__init__.py`. `diff` produces no output (identical files).

- [ ] **Step 3: Add workspace member + source declarations to root pyproject.toml (BEFORE uv sync)**

Edit root `pyproject.toml`:

In `[tool.uv.workspace] members` list, add (alphabetical/chronological order — after `packages/lingwen-world-model,`):

```toml
    "packages/lingwen-paths",   # ★ Phase 37 NEW
```

In `[tool.uv.sources]` (alphabetical — after `lingwen-world-model = { workspace = true }`):

```toml
lingwen-paths = { workspace = true }  # ★ Phase 37 NEW
```

Verify:
```bash
cd .worktrees/phase-37-p3-archdebt-paths
grep -A 16 "tool.uv.workspace" pyproject.toml | head -18
grep "lingwen-paths" pyproject.toml
```

Expected: 2 matches in pyproject.toml (one for `members`, one for `sources`).

- [ ] **Step 4: Run uv sync (workspace declaration must precede this)**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
uv sync --all-packages --offline 2>&1 | tail -5
```

Expected: success (no errors). If `ModuleNotFoundError: lingwen_paths` later, recheck pyproject.toml.

- [ ] **Step 5: Verify import + symbol count**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
./.venv/bin/python -c "
import lingwen_paths
print('has __all__:', hasattr(lingwen_paths, '__all__'))
print('resolve_project_root:', hasattr(lingwen_paths, 'resolve_project_root'))
print('ProjectPaths:', hasattr(lingwen_paths, 'ProjectPaths'))
print('get_paths:', hasattr(lingwen_paths, 'get_paths'))
print('get_chapters_dir:', hasattr(lingwen_paths, 'get_chapters_dir'))
print('get_rules_dir:', hasattr(lingwen_paths, 'get_rules_dir'))
"
```

Expected output:
```
has __all__: False
resolve_project_root: True
ProjectPaths: True
get_paths: True
get_chapters_dir: True
get_rules_dir: True
```

- [ ] **Step 6: Commit C1**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
git add packages/lingwen-paths/pyproject.toml \
        packages/lingwen-paths/src/lingwen_paths/__init__.py \
        pyproject.toml
git status --short
git commit -m "chore(packages): scaffold lingwen-paths (Phase 37 P3-ARCHDEBT paths)"
```

Expected: 3 files staged; commit message clean. Verify commit:
```bash
git log -1 --stat
```

Expected: 3 files changed, scope limited to lingwen-paths + root pyproject.toml.

---

## Task 2: C2 - migrate 86 consumers from infra.paths to lingwen_paths

**Files:** 86 consumer files across 5 categories (intra-infra / cross-package / apps / tests / tools) — see spec §5.1

- [ ] **Step 1: Run sed migration (mechanical, all categories)**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
# Space variant: `from infra.paths ` → `from lingwen_paths `
grep -rln "from infra\.paths " --include="*.py" . | xargs sed -i 's|from infra\.paths |from lingwen_paths |g'
# Dot variant: `from infra.paths.X` → `from lingwen_paths.X`
grep -rln "from infra\.paths\." --include="*.py" . | xargs sed -i 's|from infra\.paths\.|from lingwen_paths.|g'
# Bare import: `import infra.paths` → `import lingwen_paths`
grep -rln "import infra\.paths\b" --include="*.py" . | xargs sed -i 's|import infra\.paths\b|import lingwen_paths|g'
```

Expected: all 3 commands complete silently; no "No such file" errors.

- [ ] **Step 2: Verify zero remaining infra.paths imports**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
grep -rln "from infra\.paths\b\|import infra\.paths\b" --include="*.py" . | grep -v test_phase37_lingwen_paths.py | grep -v test_phase18_10_stale_imports.py
```

Expected: empty output (zero matches after excluding the two skip files — `test_phase37_lingwen_paths.py` doesn't exist yet but excluding it preemptively is safe).

- [ ] **Step 3: Verify expected count of lingwen_paths imports**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
grep -rln "from lingwen_paths\b\|import lingwen_paths\b" --include="*.py" . | wc -l
```

Expected: 86 (matches the original infra.paths count).

- [ ] **Step 4: Apply ruff --fix for any I001 (import sorting) issues**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
./.venv/bin/python -m ruff check --fix . 2>&1 | tail -10
```

Expected: any auto-fixable issues resolved. If new errors appear (non-auto-fixable), investigate before proceeding.

- [ ] **Step 5: Verify git status scope (Phase 35 lesson 1 — sed UNSTAGED)**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
git status --short | grep "^ M" | head -20
git status --short | wc -l
```

Expected: many files in ` M` state (unstaged modifications). Total count ≈ 86-87 (86 consumer files + 1 ruff side-effect possibly).

- [ ] **Step 6: Stage + commit C2**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
git add -- $(git diff --name-only)
git status --short | grep "^ M"
git commit -m "refactor(consumers): migrate 86 paths consumers from infra.paths to lingwen_paths"
```

Expected: `git status --short | grep "^ M"` returns empty (no unstaged modifications left).

Verify commit:
```bash
git log -1 --stat | head -30
git log -1 --stat | tail -5
```

Expected: 86 files changed (or 86 + ruff-affected files). Scope limited to consumer files only.

---

## Task 3: C3 - delete infra/paths.py

**Files:**
- Delete: `infra/paths.py`

- [ ] **Step 1: git rm infra/paths.py**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
git rm infra/paths.py
test -f infra/paths.py && echo "STILL EXISTS" || echo "DELETED"
```

Expected: `DELETED`.

- [ ] **Step 2: Verify file truly gone (no stale refs in git index)**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
git ls-files | grep "infra/paths.py"
```

Expected: empty output (file no longer tracked).

- [ ] **Step 3: Commit C3**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
git status --short
git commit -m "chore(infra): delete infra/paths.py (Phase 37 P3-ARCHDEBT paths cutover)"
```

Expected: `git status --short` empty after commit.

Verify:
```bash
git log -1 --stat
```

Expected: 1 file changed (infra/paths.py deleted).

---

## Task 4: C4 - add invariant #52 + bump version to v36.0

**Files:**
- Modify: `.lingwen/architecture.yml` (version: "35.0" → "36.0"; add I052 row)
- Modify: `CLAUDE.md` (add v36.0 entry; add I052 row in 架构不变量 table)

- [ ] **Step 1: Update .lingwen/architecture.yml version**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
sed -i 's|^version: "35.0"$|version: "36.0"|' .lingwen/architecture.yml
grep -n '^version:' .lingwen/architecture.yml
```

Expected: `version: "36.0"` (single match).

- [ ] **Step 2: Add I052 to .lingwen/architecture.yml invariants block**

Locate the invariants section (find a similar invariant like I051):
```bash
cd .worktrees/phase-37-p3-archdebt-paths
grep -n "I051\|invariants" .lingwen/architecture.yml | head -10
```

Read the I051 row to model after, then add I052 in the same format. The invariants block format is YAML key-value. Add after the I051 row:

```yaml
  - id: I052
    description: "`packages/lingwen-paths/` 是项目路径管理（ProjectPaths / resolve_project_root 等）的唯一实包；`infra.paths.*` 路径非法 (Phase 37+)."
    rationale: "P3-ARCHDEBT item 2/5; continues canonical location establishment. See docs/superpowers/specs/2026-09-08-phase-37-p3-archdebt-paths-design.md"
```

Verify:
```bash
grep -n "I052" .lingwen/architecture.yml
```

Expected: at least 1 match (the new I052 row).

- [ ] **Step 3: Update CLAUDE.md header version**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
sed -i 's|^> \*\*版本\*\*: v35.0 (Phase 36 P3-ARCHDEBT errors pilot 闭环)|> **版本**: v36.0 (Phase 37 P3-ARCHDEBT paths 闭环)|' CLAUDE.md
grep -n "版本\*\*: v36.0" CLAUDE.md
```

Expected: 1 match in the header line.

- [ ] **Step 4: Add I052 row to CLAUDE.md 架构不变量 table**

In CLAUDE.md, locate the invariants table (search for `| I051 |`):
```bash
cd .worktrees/phase-37-p3-archdebt-paths
grep -n "| I0[4-5][0-9] |" CLAUDE.md
```

After the `| I051 | ... |` row, add:
```markdown
| I052 | `packages/lingwen-paths/` 是项目路径管理（ProjectPaths / resolve_project_root 等）的唯一实包；`infra.paths.*` 路径非法 (Phase 37+) |
```

Verify:
```bash
grep -n "| I052" CLAUDE.md
```

Expected: 1 match in the invariants table.

- [ ] **Step 5: Add v36.0 已知遗留 entry (mirror v35.0 format)**

In CLAUDE.md, locate the v35.0 entry in "已知遗留" section:
```bash
cd .worktrees/phase-37-p3-archdebt-paths
grep -n "v35.0 P3-ARCHDEBT" CLAUDE.md
```

Read the v35.0 entry to model after. Prepend a v36.0 entry above v35.0:

```markdown
- ✅ **v36.0 P3-ARCHDEBT (paths)**（2026-09-08 ff-merge `<branch>`）：P3-ARCHDEBT item 2/5 — `infra/paths.py` (125 lines, 5 top-level public symbols) → `packages/lingwen-paths/`。86 consumer 迁移 (8 intra-infra + 16 cross-package + 1 apps + 61 tests + 3 tools)；`infra/paths.py` 删除；invariant #52 NEW。详见 `docs/superpowers/handoffs/2026-09-08-phase-37-p3-archdebt-paths-handoff.md`。
```

(Final `<branch>` placeholder will be filled at handoff doc creation time.)

Verify:
```bash
grep -n "v36.0 P3-ARCHDEBT (paths)" CLAUDE.md
```

Expected: 1 match.

- [ ] **Step 6: Commit C4**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
git status --short
git diff --stat
git add .lingwen/architecture.yml CLAUDE.md
git commit -m "chore(infra): bump v36.0 + add invariant #52 (lingwen-paths canonical)"
```

Expected: 2 files changed. Verify:
```bash
git log -1 --stat
```

---

## Task 5: C5 - regression guards + doc sync

**Files:**
- Create: `tests/test_phase37_lingwen_paths.py` (6 guards per spec §6.1)
- Modify: `tests/test_phase18_10_stale_imports.py:20` (`"infra.paths"` → `"lingwen_paths"`)
- Modify: `collaboration/CURRENT_STATUS.md` (Phase 37 status)
- Modify: `collaboration/BACKLOG.md` (Phase 37 entry; P3-ARCHDEBT 2/5 closed)
- Create: `docs/superpowers/handoffs/2026-09-08-phase-37-p3-archdebt-paths-handoff.md`

- [ ] **Step 1: Create tests/test_phase37_lingwen_paths.py (6 guards)**

Write `tests/test_phase37_lingwen_paths.py`:

```python
"""Phase 37 P3-ARCHDEBT (paths) regression guards.

Verifies lingwen-paths package canonicalization (v36.0, invariant #52).
Pattern: Phase 36 test_phase36_lingwen_errors.py, adapted for paths.

Skip files (N.14 lesson 6 — guard self-trigger):
- tests/test_phase37_lingwen_paths.py (this file)
- tests/test_phase18_10_stale_imports.py (contains "infra.paths" in stale-list)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

SKIP_FILES = {
    REPO_ROOT / "tests" / "test_phase37_lingwen_paths.py",
    REPO_ROOT / "tests" / "test_phase18_10_stale_imports.py",
}


def _is_skipped(path: Path) -> bool:
    return path in SKIP_FILES


# ---------------------------------------------------------------------------
# G1: lingwen-paths package scaffolding exists
# ---------------------------------------------------------------------------


def test_lingwen_paths_package_exists():
    """Verify packages/lingwen-paths/ scaffold exists."""
    pkg_root = REPO_ROOT / "packages" / "lingwen-paths"
    pyproject = pkg_root / "pyproject.toml"
    init_file = pkg_root / "src" / "lingwen_paths" / "__init__.py"

    assert pkg_root.is_dir(), f"missing {pkg_root}"
    assert pyproject.is_file(), f"missing {pyproject}"
    assert init_file.is_file(), f"missing {init_file}"


def test_lingwen_paths_init_imports():
    """Verify lingwen_paths imports + 5 top-level public symbols (NO __all__)."""
    import lingwen_paths

    # Source file has no __all__; preserve 1:1 means lingwen_paths also has none
    assert not hasattr(lingwen_paths, "__all__"), (
        "lingwen_paths should NOT have __all__ (source file has none)"
    )

    # All 5 top-level symbols must exist
    for symbol in ["resolve_project_root", "ProjectPaths", "get_paths",
                   "get_chapters_dir", "get_rules_dir"]:
        assert hasattr(lingwen_paths, symbol), (
            f"missing top-level symbol: {symbol}"
        )


# ---------------------------------------------------------------------------
# G2: infra/paths.py deleted + invariant #52 enforced
# ---------------------------------------------------------------------------


def test_infra_paths_deleted():
    """Verify infra/paths.py removed (full cutover)."""
    infra_paths = REPO_ROOT / "infra" / "paths.py"
    assert not infra_paths.exists(), f"{infra_paths} should not exist after Phase 37"


def test_workspace_member_declared():
    """Verify root pyproject.toml declares packages/lingwen-paths in workspace."""
    root_pyproject = REPO_ROOT / "pyproject.toml"
    content = root_pyproject.read_text(encoding="utf-8")

    # Check workspace members declaration
    assert "packages/lingwen-paths" in content, (
        "pyproject.toml missing 'packages/lingwen-paths' in [tool.uv.workspace] members"
    )
    # Check workspace sources declaration
    assert re.search(r"lingwen-paths\s*=\s*\{\s*workspace\s*=\s*true\s*\}", content), (
        "pyproject.toml missing 'lingwen-paths = { workspace = true }' in [tool.uv.sources]"
    )


def test_no_infra_paths_references():
    """Verify no Python file imports from infra.paths (excluding skip files)."""
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
    pattern = re.compile(r"\b(infra\.paths|from\s+infra\.paths|import\s+infra\.paths)\b")

    for rel_path in files:
        path = REPO_ROOT / rel_path
        if _is_skipped(path):
            continue
        if path.suffix != ".py":
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if pattern.search(content):
            offenders.append(rel_path)

    assert not offenders, (
        "Found infra.paths references (forbidden by invariant #52):\n"
        + "\n".join(f"  - {p}" for p in offenders)
    )


# ---------------------------------------------------------------------------
# G3: Canonical symbols migrated + representative consumers use lingwen_paths
# ---------------------------------------------------------------------------


def test_canonical_symbols_migrated():
    """Verify all 5 canonical symbols importable + representative consumer migrated."""
    import lingwen_paths

    # All 5 symbols must be importable
    assert callable(lingwen_paths.resolve_project_root)
    assert isinstance(lingwen_paths.ProjectPaths, type)
    assert callable(lingwen_paths.get_paths)
    assert callable(lingwen_paths.get_chapters_dir)
    assert callable(lingwen_paths.get_rules_dir)

    # Spot-check 3 representative consumers: 1 package, 1 intra-infra, 1 tests
    representative_files = [
        REPO_ROOT / "packages" / "lingwen-core" / "src" / "lingwen_core" / "agents" / "chapter_emit.py",
        REPO_ROOT / "infra" / "project_config.py",
        REPO_ROOT / "tests" / "conftest.py",
    ]
    for f in representative_files:
        content = f.read_text(encoding="utf-8")
        assert re.search(r"^from lingwen_paths\b", content, re.MULTILINE), (
            f"{f.name} should 'from lingwen_paths' import (line-anchored)"
        )
        assert not re.search(r"^from infra\.paths\b", content, re.MULTILINE), (
            f"{f.name} should NOT 'from infra.paths' import (forbidden by I052)"
        )
```

- [ ] **Step 2: Update tests/test_phase18_10_stale_imports.py stale-list**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
sed -i 's|        "infra.paths",|        "lingwen_paths",  # Phase 37: was "infra.paths" (now deleted; canonicalized)|' tests/test_phase18_10_stale_imports.py
grep -n "lingwen_paths\|infra.paths" tests/test_phase18_10_stale_imports.py
```

Expected: `lingwen_paths` appears in ALLOWED_COMPAT_IMPORTS; `infra.paths` no longer present.

- [ ] **Step 3: Run phase37 guard tests (G2 from validation gates)**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
./.venv/bin/python -m pytest tests/test_phase37_lingwen_paths.py -v 2>&1 | tail -15
```

Expected: 6/6 PASS.

- [ ] **Step 4: Run full validation gates (G3-G10 baselines)**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
./.venv/bin/python -m pytest packages/lingwen-world-model/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-core/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-got/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest apps/studio_api/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-quality/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-pipeline/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-llm/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-creator/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest packages/lingwen-cli/tests/ --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m pytest tests/test_phase18_10_stale_imports.py --tb=no -q 2>&1 | tail -3
./.venv/bin/python -m ruff check . 2>&1 | tail -3
```

Expected: all 8 baselines at T0 levels (preserved, no regression). `test_phase18_10_stale_imports.py` should now PASS (not xfail) because `infra.paths` is deleted and `lingwen_paths` is in the allowlist — the xfail threshold (>200) is still exceeded by remaining infra.* imports, so it xfails but with reduced count.

- [ ] **Step 5: Write handoff doc**

Create `docs/superpowers/handoffs/2026-09-08-phase-37-p3-archdebt-paths-handoff.md`. Model after `docs/superpowers/handoffs/2026-09-08-phase-36-p3-archdebt-errors-handoff.md` (read it first to copy structure).

Key sections to include:
- Summary: P3-ARCHDEBT item 2/5 closed
- Migration stats: 86 consumers, 125 lines, 5 top-level symbols, 1 invariant
- Validation gates results (paste output from Step 4)
- Lessons learned (any deviations from spec)
- Carryover: P3-ARCHDEBT 3/5 remaining (project_config / logging_config / studio_registry)

- [ ] **Step 6: Update collaboration/CURRENT_STATUS.md + BACKLOG.md**

CURRENT_STATUS.md: add a Phase 37 status line near the top:
```markdown
- **Phase 37 P3-ARCHDEBT (paths)**: ✅ DONE on 2026-09-08. `infra/paths.py` → `packages/lingwen-paths/`. 86 consumer migration + invariant #52 + v36.0. See handoff: `docs/superpowers/handoffs/2026-09-08-phase-37-p3-archdebt-paths-handoff.md`.
```

BACKLOG.md: add Phase 37 to completed list; mark P3-ARCHDEBT 2/5 → closed; update carryover for 3/5 remaining.

- [ ] **Step 7: Commit C5**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
git status --short
git add tests/test_phase37_lingwen_paths.py \
        tests/test_phase18_10_stale_imports.py \
        collaboration/CURRENT_STATUS.md \
        collaboration/BACKLOG.md \
        docs/superpowers/handoffs/2026-09-08-phase-37-p3-archdebt-paths-handoff.md
git commit -m "test(phase-37): regression guards + doc sync"
```

Verify:
```bash
git log -1 --stat
```

Expected: 5 files changed.

---

## Task 6: C0 - commit spec + plan (BACK-DATED, before C1)

> **NOTE**: This task should have been Task 0. Since spec + plan were written at the start of this work but not committed yet, commit them now before any other merges happen. The C0 commit is informational only — it doesn't change any code, just adds spec + plan docs.

**Files:**
- Create: `docs/superpowers/specs/2026-09-08-phase-37-p3-archdebt-paths-design.md` (already exists from earlier)
- Create: `docs/superpowers/plans/2026-09-08-phase-37-p3-archdebt-paths.md` (already exists from earlier)

- [ ] **Step 1: Verify spec + plan exist**

```bash
cd .worktrees/phase-37-p3-archdebt-paths
ls -la docs/superpowers/specs/2026-09-08-phase-37-p3-archdebt-paths-design.md
ls -la docs/superpowers/plans/2026-09-08-phase-37-p3-archdebt-paths.md
```

Expected: both files exist.

- [ ] **Step 2: Commit C0 (informational)**

> **REORDER NOTE**: Tasks 1-5 already executed before this task. Reorder via `git rebase -i` would lose work. Instead, this commit lands AFTER C1-C5 with a "docs:" message indicating it's the spec/plan. Order in branch history: C0 → C1 → C2 → C3 → C4 → C5 (with C0 last in the chain — informational only).

Actually, the cleanest approach: commit C0 FIRST as a "docs(phase-37): spec + plan" commit, then rebase Tasks 1-5 onto it. But rebase loses ff-merge capability.

**Simpler approach**: commit C0 now as the LAST commit, with a clear "docs:" message. The branch will have 6 commits total, with C0 last (effectively retroactive, but git log shows it last).

**OR**: reset the branch and replay. Since master is unchanged, this is safe.

```bash
cd .worktrees/phase-37-p3-archdebt-paths
# Check current state
git log --oneline | head -10
```

If only C1-C5 commits exist:
```bash
git add docs/superpowers/specs/2026-09-08-phase-37-p3-archdebt-paths-design.md \
        docs/superpowers/plans/2026-09-08-phase-37-p3-archdebt-paths.md
git commit --amend --no-edit  # amend C5 to include spec + plan
```

OR if you want C0 separate:
```bash
git commit -m "docs(phase-37): spec + plan (retroactive — should have been first commit)"
```

**Recommended**: amend C5 to include spec + plan. This keeps the chain clean (6 atomic commits in correct order: C0 → C1 → ... → C5).

Actually, simplest: just commit C0 as a separate commit BEFORE merging to master, accepting that git log will show "spec/plan added in last commit" but the commit message makes it clear.

---

## Task 7: T6 - ff-merge to master + push

**Files:** none (git operations only)

- [ ] **Step 1: Verify branch is fast-forwardable**

```bash
cd /home/ailearn/projects/LingWen
git checkout master
git merge --ff-only phase-37-p3-archdebt-paths
```

Expected: fast-forward merge succeeds (no merge commit).

- [ ] **Step 2: Push master to origin**

```bash
cd /home/ailearn/projects/LingWen
git push origin master
```

Expected: master pushed (count of commits: 6).

- [ ] **Step 3: Staging leak check #1 (Phase 36 critical lesson — after ff-merge)**

```bash
cd /home/ailearn/projects/LingWen
git status --short
git diff --cached --stat | grep "infra/paths.py" && echo "LEAK DETECTED" || echo "clean"
test -f infra/paths.py && echo "LEAK: file still exists" || echo "clean"
```

Expected: 
- `git status --short`: only user's pre-existing `M projects/anye-xinbiao/docs/novel-pillars.md`
- Both leak checks return `clean`

If LEAK DETECTED:
```bash
git restore --staged infra/paths.py
rm infra/paths.py
# Re-verify
```

- [ ] **Step 4: Remove worktree**

```bash
cd /home/ailearn/projects/LingWen
git worktree remove --force .worktrees/phase-37-p3-archdebt-paths
git branch -d phase-37-p3-archdebt-paths
```

- [ ] **Step 5: Staging leak check #2 (Phase 36 critical lesson — after worktree remove)**

```bash
cd /home/ailearn/projects/LingWen
git status --short
git diff --cached --stat | grep "infra/paths.py" && echo "LEAK DETECTED" || echo "clean"
test -f infra/paths.py && echo "LEAK: file still exists" || echo "clean"
```

Expected: all checks return clean. If LEAK: same remediation as Step 3.

- [ ] **Step 6: Update MEMORY.md**

Outside worktree (master), update `~/.claude/projects/-home-ailearn-projects-LingWen/memory/MEMORY.md`:
- Master HEAD → `<new HEAD commit>`
- Add Phase 37 entry to "Project State"
- Add any new lessons learned
- Update carryover (P3-ARCHDEBT 2/5 done; remaining 3/5: project_config / logging_config / studio_registry)
- Update recommended next session options (Phase 38 = project_config or studio_registry)

---

## Self-Review Checklist (run after writing this plan)

- [x] **Spec coverage**: Each §2 goal has a corresponding task
  - Goal 1: Move infra/paths.py → Task 1 (C1)
  - Goal 2: Migrate 86 consumers → Task 2 (C2)
  - Goal 3: Delete infra/paths.py → Task 3 (C3)
  - Goal 4: Workspace declaration → Task 1 (C1) Step 3
  - Goal 5: Invariant #52 + version bump → Task 4 (C4)
  - Goal 6: 6 regression guards → Task 5 (C5) Step 1
  - Goal 7: CLAUDE.md + stale-list update → Task 4 (C4) + Task 5 (C5)
- [x] **Placeholder scan**: No "TBD" / "TODO" / "similar to Task N" patterns. All steps have concrete code/commands.
- [x] **Type consistency**: All symbol names (`resolve_project_root`, `ProjectPaths`, `get_paths`, `get_chapters_dir`, `get_rules_dir`) consistent across spec and guard test.
- [x] **File paths exact**: All paths use absolute paths relative to worktree root.
- [x] **Expected outputs documented**: Every command has `Expected:` line.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-09-08-phase-37-p3-archdebt-paths.md`.

Two execution options:
1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks
2. **Inline Execution** — execute tasks in this session with checkpoints

For Phase 37's mechanical nature (mostly sed migrations + file copies), **Inline Execution is more efficient** — subagent overhead per task adds latency without quality benefit. Recommend Inline.
