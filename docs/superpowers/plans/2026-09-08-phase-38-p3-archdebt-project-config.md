# Phase 38 — P3-ARCHDEBT (project_config) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate `infra/project_config.py` (171 lines, 2 public symbols, 27 consumer files) to `packages/lingwen-project-config/`, delete the source, and add invariant #53 — closing P3-ARCHDEBT 3/5.

**Architecture:** Single-file package (`packages/lingwen-project-config/src/lingwen_project_config/__init__.py`) preserves 1:1 source content. Non-leaf package with 2 workspace deps (`lingwen-paths` Phase 37 + `lingwen-shared` v16.1). 6 atomic commits matching Phase 37 pattern (C0 spec+plan / C1 scaffold / C2 migrate / C3 delete / C4 version+invariant / C5 guards+doc-sync).

**Tech Stack:** Python 3.12+, uv workspace, hatchling build, ruff, pytest. Phase 37 invariant #52 + new #53.

**Worktree:** `.claude/worktrees/phase-38-p3-archdebt-project-config/` on branch `phase-38-p3-archdebt-project-config` based on master `e65d7784`.

---

## File Structure

**Create (3 files):**
- `packages/lingwen-project-config/pyproject.toml` — Hatchling build, deps `lingwen-paths` + `lingwen-shared`
- `packages/lingwen-project-config/src/lingwen_project_config/__init__.py` — 171 lines 1:1 from source
- `tests/test_phase38_lingwen_project_config.py` — 6 regression guards (G1 scaffold + G2 source deleted + G3 no stale refs + G4 canonical symbols + G5 wildcard cleaned + G6 workspace declared)

**Modify (29 files):**
- `pyproject.toml` (root) — +1 workspace member, +1 source, version bump
- `.lingwen/architecture.yml` — +invariant #53, version bump
- `CLAUDE.md` — v37.0 entry + carryover update
- `infra/project/__init__.py` — remove wildcard line 4
- 27 consumer files — sed migrate `infra.project_config` → `lingwen_project_config`
- `tests/test_phase18_10_stale_imports.py` — update stale-list

**Delete (1 file):**
- `infra/project_config.py` (171 lines)

**Companion docs:**
- `docs/superpowers/specs/2026-09-08-phase-38-p3-archdebt-project-config-design.md` (spec, written in C0)
- `docs/superpowers/handoffs/2026-09-08-phase-38-p3-archdebt-project-config-handoff.md` (written in C5)

---

## Task 1 (C1): Scaffold `packages/lingwen-project-config/`

**Files:**
- Create: `packages/lingwen-project-config/pyproject.toml`
- Create: `packages/lingwen-project-config/src/lingwen_project_config/__init__.py`
- Modify: `pyproject.toml` (root) — add workspace member + source entry

- [ ] **Step 1.1: Verify worktree + branch**

```bash
pwd  # should show /home/ailearn/projects/LingWen/.claude/worktrees/phase-38-p3-archdebt-project-config
git rev-parse --abbrev-ref HEAD  # should be phase-38-p3-archdebt-project-config
git status  # clean
```

Expected: branch `phase-38-p3-archdebt-project-config`, clean tree.

- [ ] **Step 1.2: Create `packages/lingwen-project-config/pyproject.toml`**

Write:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "lingwen-project-config"
version = "0.1.0"
description = "LingWen canonical project_config module (Phase 38 P3-ARCHDEBT project_config)"
requires-python = ">=3.11"
dependencies = [
    "lingwen-paths",
    "lingwen-shared",
]

[tool.hatch.build.targets.wheel]
packages = ["src/lingwen_project_config"]
```

- [ ] **Step 1.3: Create `packages/lingwen-project-config/src/lingwen_project_config/__init__.py` (1:1 from source)**

```bash
mkdir -p packages/lingwen-project-config/src/lingwen_project_config
cp infra/project_config.py packages/lingwen-project-config/src/lingwen_project_config/__init__.py
```

Verify line count matches:

```bash
wc -l infra/project_config.py packages/lingwen-project-config/src/lingwen_project_config/__init__.py
```

Expected: 171 lines both files.

Verify NO `__all__`:

```bash
grep -n "^__all__" packages/lingwen-project-config/src/lingwen_project_config/__init__.py
```

Expected: 0 hits (matches source).

- [ ] **Step 1.4: Add workspace member + source to root `pyproject.toml`**

Edit `pyproject.toml`. In `[tool.uv.workspace] members` (after `packages/lingwen-paths`, before `apps/studio_api`):

```toml
    "packages/lingwen-paths",   # ★ Phase 37 NEW
    "packages/lingwen-project-config",   # ★ Phase 38 NEW
    "apps/studio_api",
```

In `[tool.uv.sources]` (after `lingwen-paths`, before `apps/studio_api` if present):

```toml
lingwen-paths = { workspace = true }
lingwen-project-config = { workspace = true }
```

Verify:

```bash
grep "lingwen-project-config" pyproject.toml
```

Expected: 2 hits (workspace member + source).

- [ ] **Step 1.5: Run `uv sync` (workspace member must be declared FIRST — Phase 34 lesson)**

```bash
uv sync --all-packages --offline
```

Expected: success, no `ModuleNotFoundError`. If offline fails, drop `--offline` flag.

- [ ] **Step 1.6: Verify importable**

```bash
uv run python -c "from lingwen_project_config import ProjectConfig, update_project_creation_mode; print('OK', ProjectConfig.__name__)"
```

Expected: `OK ProjectConfig` printed.

- [ ] **Step 1.7: Verify infra/project_config.py still exists (parallel existence during C1)**

```bash
ls -la infra/project_config.py packages/lingwen-project-config/src/lingwen_project_config/__init__.py
```

Expected: BOTH files exist (parallel existence intentional — consumers not yet migrated). C3 deletes source.

- [ ] **Step 1.8: Commit C1**

```bash
git add packages/lingwen-project-config/pyproject.toml packages/lingwen-project-config/src/lingwen_project_config/__init__.py pyproject.toml
git commit -m "chore(packages): scaffold lingwen-project-config (Phase 38 P3-ARCHDEBT project_config)"
```

---

## Task 2 (C2): Migrate 27 consumers

**Files:**
- Modify: 27 consumer files (sed: `from infra.project_config` → `from lingwen_project_config`)

- [ ] **Step 2.1: Pre-C2 consumer audit (verify count = 27)**

```bash
grep -rln "infra\.project_config" --include="*.py" infra/ apps/ packages/ tests/ | wc -l
```

Expected: 27 files.

- [ ] **Step 2.2: Run C2 sed migration (single pass — handles module-level + function-body via `^[[:space:]]*from`)**

```bash
FILES=$(grep -rln --include="*.py" "from infra\.project_config" infra/ apps/ packages/ tests/)
echo "$FILES" | xargs -r sed -i 's|^from infra\.project_config import|from lingwen_project_config import|'
```

Also handle the `import infra.project_config` form (defensive — should be 0 hits, but verify):

```bash
grep -rln --include="*.py" "^import infra\.project_config\b" infra/ apps/ packages/ tests/
```

Expected: 0 hits (no module-level `import infra.project_config` form exists).

Also handle indented wildcard re-export `from infra.project_config import *  # noqa: F403` (in infra/project/__init__.py:4):

```bash
sed -i 's|^from infra\.project_config import \*  # noqa: F403$|from lingwen_project_config import *  # noqa: F403|' infra/project/__init__.py
```

Verify wildcard migrated:

```bash
grep -n "infra\.project_config\|lingwen_project_config" infra/project/__init__.py
```

Expected: 4 lines, all referencing `lingwen_project_config` (the sed replaced line 4 only; lines 1/3/5 reference lingwen_paths / infra.project_characters / infra.project_init which are NOT in scope).

- [ ] **Step 2.3: Post-C2 audit — verify 0 `infra.project_config` references in code**

```bash
grep -rln "infra\.project_config" --include="*.py" infra/ apps/ packages/ tests/
```

Expected: 0 files (C2 fully migrated).

If any hits remain:
- Inspect file
- For function-body imports not caught by sed: re-run with `grep -n` to verify line, then manual edit
- For TYPE_CHECKING blocks: manually edit

- [ ] **Step 2.4: Sanity-check imports resolve (run a small subset of consumers)**

```bash
uv run python -c "from lingwen_project_config import ProjectConfig; print('symbol OK')"
uv run python -c "from apps.studio_api.routes.creator_volume import router; print('creator_volume OK')"
uv run python -c "from apps.studio_api.routes.creator_core import router; print('creator_core OK')"
uv run python -c "from lingwen_cli.project_range import main; print('cli OK')"
uv run python -c "from lingwen_core.agents.chapter_production_outline import main; print('core OK')"
uv run python -c "from lingwen_creator.onboarding.autodetect import detect; print('creator OK')"
```

Expected: All print OK.

- [ ] **Step 2.5: Run regression test for existing project_config behavior**

```bash
uv run pytest tests/infra/test_project_config.py -v
```

Expected: 6/6 pass (existing tests still work after migration).

- [ ] **Step 2.6: Verify docstring drift (N.14 lesson 9)**

```bash
grep -rn "infra\.project_config" --include="*.py" apps/ packages/ infra/ 2>&1 | grep -v "^infra/project_config.py:"
```

Expected: 0 hits (any docstring `from infra.project_config` mentions would be in test infra references, which sed should have caught).

If hits exist in docstrings (e.g., comments saying "See infra/project_config.py for..."), they're benign but should be noted in commit message.

- [ ] **Step 2.7: Commit C2**

```bash
git add -u
git commit -m "refactor(consumers): migrate 27 project_config consumers to lingwen_project_config"
```

Include in commit message: "(27 sites across 2 apps + 16 packages + 4 infra intra + 5 tests; 3 function-body imports via ^[[:space:]]* sed pattern)."

---

## Task 3 (C3): Delete `infra/project_config.py` + clean wildcard

**Files:**
- Delete: `infra/project_config.py`
- Modify: `infra/project/__init__.py` (remove wildcard re-export — source no longer exists)

- [ ] **Step 3.1: Verify 0 references remain before deletion (defensive)**

```bash
grep -rln "infra\.project_config" --include="*.py" --include="*.toml" --include="*.md" infra/ apps/ packages/ tests/ docs/ 2>&1 | head -10
```

Expected: only matches in `docs/superpowers/specs/2026-09-08-phase-38-p3-archdebt-project-config-design.md` and `docs/superpowers/handoffs/2026-09-08-phase-38-...-handoff.md` (Phase 38 docs reference the old name historically). 0 hits in code.

- [ ] **Step 3.2: Remove wildcard re-export line from `infra/project/__init__.py`**

The C2 sed migrated the wildcard to `from lingwen_project_config import *  # noqa: F403`. But after C3 deletes `infra/project_config.py`... wait, no — `lingwen_project_config` is in `packages/`, NOT `infra/`. The wildcard re-export through `infra.project.*` namespace is still semantically weird (mixing infra + packages). Best to DELETE the wildcard line entirely.

Read current state:

```bash
cat infra/project/__init__.py
```

Expected: 5 lines, line 4 = `from lingwen_project_config import *  # noqa: F403`.

Edit `infra/project/__init__.py`: DELETE line 4 (the wildcard).

Result file should be 4 lines:

```python
from lingwen_paths import *  # noqa: F403

from infra.project_characters import *  # noqa: F403
from infra.project_init import *  # noqa: F403
```

- [ ] **Step 3.3: Delete `infra/project_config.py`**

```bash
git rm infra/project_config.py
```

- [ ] **Step 3.4: Verify deletion + post-C3 state**

```bash
ls -la infra/project_config.py 2>&1; echo "---"; ls -la packages/lingwen-project-config/src/lingwen_project_config/__init__.py
```

Expected: First `ls` shows "No such file" or similar (file deleted). Second shows the new package file.

- [ ] **Step 3.5: Sanity-import the canonical package**

```bash
uv run python -c "from lingwen_project_config import ProjectConfig, update_project_creation_mode; print('post-C3 OK')"
```

Expected: `post-C3 OK`.

- [ ] **Step 3.6: Run project_config regression tests post-deletion**

```bash
uv run pytest tests/infra/test_project_config.py -v
```

Expected: 6/6 pass.

- [ ] **Step 3.7: Commit C3**

```bash
git add -u
git commit -m "chore(infra): delete infra/project_config.py (Phase 38 P3-ARCHDEBT project_config cutover)"
```

---

## Task 4 (C4): Bump v37.0 + add invariant #53

**Files:**
- Modify: `pyproject.toml` (root) — version 9.11.0 → 9.12.0
- Modify: `.lingwen/architecture.yml` — version + invariant #53 NEW
- Modify: `CLAUDE.md` — v37.0 carryover line + invariant #53

- [ ] **Step 4.1: Bump root `pyproject.toml` version**

Edit `pyproject.toml`. Find `version = "9.11.0"` (line ~10) and change to:

```toml
version = "9.12.0"
```

Verify:

```bash
grep -n "^version" pyproject.toml | head -3
```

Expected: shows `version = "9.12.0"`.

- [ ] **Step 4.2: Bump `.lingwen/architecture.yml` version + add invariant #53**

Read current invariants section first:

```bash
grep -n "invariant\|version\|I052\|I051" .lingwen/architecture.yml | head -20
```

Find the I052 line (added in Phase 37) and the version field. Add invariant #53 immediately after #52:

```yaml
| I052 | `packages/lingwen-paths/` is canonical; `infra.paths.*` forbidden (Phase 37+) |
| I053 | `packages/lingwen-project-config/` is canonical; `infra.project_config.*` forbidden (Phase 38+) |
```

Bump architecture version (find existing 36.0 → change to 37.0):

```yaml
version: 37.0
```

(Adjust based on actual key name — search for `version: 36` to confirm format.)

- [ ] **Step 4.3: Update CLAUDE.md**

Find the "架构不变量" section table (Phase 37 added I052). Add I053 row after I052:

```markdown
| I052 | `packages/lingwen-paths/` is canonical; `infra.paths.*` forbidden (Phase 37+) |
| I053 | `packages/lingwen-project-config/` is canonical; `infra.project_config.*` forbidden (Phase 38+) |
```

Find the "已知遗留" section (Phase 37 added v36.0 entry at top). Prepend Phase 38 entry above v36.0:

```markdown
- ✅ **v37.0 P3-ARCHDEBT (project_config)**（2026-09-08 ff-merge `phase-38-p3-archdebt-project-config`）：P3-ARCHDEBT item 3/5 — `infra/project_config.py` (1 module, 171 lines, 2 top-level public symbols: ProjectConfig + update_project_creation_mode) → `packages/lingwen-project-config/`. 27 consumer 迁移 (2 apps + 16 packages + 4 infra intra + 5 tests); `infra/project_config.py` 删除; invariant #53 NEW. 6 atomic commits on phase-38-p3-archdebt-project-config (C0 spec+plan / C1 scaffold / C2 migrate / C3 delete / C4 invariant+version / C5 guards+doc-sync). Validation gates: ruff clean + 6 phase38 guards GREEN + baselines preserved. **Carryover closure**: P3-ARCHDEBT 3/5 (project_config) → CLOSED; P3-ARCHDEBT remaining 2/5 (logging_config + studio_registry) → Phase 39+. Details: `docs/superpowers/handoffs/2026-09-08-phase-38-p3-archdebt-project-config-handoff.md`.
```

Also bump the top header:

```
# 灵文 · 工业化小说生产系统

> **版本**: v37.0 (Phase 38 P3-ARCHDEBT project_config 闭环) · 更新: 2026-09-08
```

- [ ] **Step 4.4: Verify no version drift**

```bash
grep -n "v37\.0\|v36\.0\|9\.12\.0\|9\.11\.0" pyproject.toml .lingwen/architecture.yml CLAUDE.md | head -10
```

Expected: matches the v37.0 / 9.12.0 references introduced; pre-existing v36.0 / 9.11.0 should now be ONLY in historical carryover text (do not blanket replace).

- [ ] **Step 4.5: Commit C4**

```bash
git add pyproject.toml .lingwen/architecture.yml CLAUDE.md
git commit -m "chore(infra): bump v37.0 + add invariant #53 (lingwen-project-config canonical)"
```

---

## Task 5 (C5): Regression guards + doc sync + handoff

**Files:**
- Create: `tests/test_phase38_lingwen_project_config.py` — 6 guards
- Modify: `tests/test_phase18_10_stale_imports.py` — update stale-list
- Create: `docs/superpowers/handoffs/2026-09-08-phase-38-p3-archdebt-project-config-handoff.md` — phase handoff

- [ ] **Step 5.1: Write `tests/test_phase38_lingwen_project_config.py`**

Write the file (modeled on `tests/test_phase37_lingwen_paths.py`):

```python
"""Phase 38 P3-ARCHDEBT (project_config) regression guards.

Verifies lingwen-project-config package canonicalization (v37.0, invariant #53).
Pattern: Phase 37 test_phase37_lingwen_paths.py, adapted for project_config.

Skip files (N.14 lesson 6 — guard self-trigger):
- tests/test_phase38_lingwen_project_config.py (this file)
- tests/test_phase18_10_stale_imports.py (contains "infra.project_config" in stale-list)
- docs/superpowers/specs/2026-09-08-phase-38-p3-archdebt-project-config-design.md
- docs/superpowers/handoffs/2026-09-08-phase-38-p3-archdebt-project-config-handoff.md
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

SKIP_FILES = {
    REPO_ROOT / "tests" / "test_phase38_lingwen_project_config.py",
    REPO_ROOT / "tests" / "test_phase18_10_stale_imports.py",
    REPO_ROOT / "docs" / "superpowers" / "specs" / "2026-09-08-phase-38-p3-archdebt-project-config-design.md",
    REPO_ROOT / "docs" / "superpowers" / "handoffs" / "2026-09-08-phase-38-p3-archdebt-project-config-handoff.md",
}


def _is_skipped(path: Path) -> bool:
    return path in SKIP_FILES


# ---------------------------------------------------------------------------
# G1: lingwen-project-config package scaffolding exists
# ---------------------------------------------------------------------------


def test_lingwen_project_config_package_exists():
    """Verify packages/lingwen-project-config/ scaffold exists."""
    pkg_root = REPO_ROOT / "packages" / "lingwen-project-config"
    pyproject = pkg_root / "pyproject.toml"
    init_file = pkg_root / "src" / "lingwen_project_config" / "__init__.py"

    assert pkg_root.is_dir(), f"missing {pkg_root}"
    assert pyproject.is_file(), f"missing {pyproject}"
    assert init_file.is_file(), f"missing {init_file}"


def test_lingwen_project_config_init_imports():
    """Verify lingwen_project_config imports + 2 top-level public symbols (NO __all__)."""
    import lingwen_project_config

    # Source file has no __all__; preserve 1:1 means lingwen_project_config also has none
    assert not hasattr(lingwen_project_config, "__all__"), (
        "lingwen_project_config should NOT have __all__ (source file has none)"
    )

    # Both top-level symbols must exist
    for symbol in ["ProjectConfig", "update_project_creation_mode"]:
        assert hasattr(lingwen_project_config, symbol), (
            f"missing top-level symbol: {symbol}"
        )


# ---------------------------------------------------------------------------
# G2: infra/project_config.py deleted + invariant #53 enforced
# ---------------------------------------------------------------------------


def test_infra_project_config_deleted():
    """Verify infra/project_config.py removed (full cutover)."""
    infra_pc = REPO_ROOT / "infra" / "project_config.py"
    assert not infra_pc.exists(), f"{infra_pc} should not exist after Phase 38"


def test_workspace_member_declared():
    """Verify root pyproject.toml declares packages/lingwen-project-config in workspace."""
    root_pyproject = REPO_ROOT / "pyproject.toml"
    content = root_pyproject.read_text(encoding="utf-8")

    assert "packages/lingwen-project-config" in content, (
        "pyproject.toml missing 'packages/lingwen-project-config' in [tool.uv.workspace] members"
    )
    assert re.search(
        r"lingwen-project-config\s*=\s*\{\s*workspace\s*=\s*true\s*\}", content
    ), "pyproject.toml missing 'lingwen-project-config = { workspace = true }' in [tool.uv.sources]"


def test_no_infra_project_config_references():
    """Verify no Python file imports from infra.project_config (excluding skip files)."""
    result = subprocess.run(
        ["grep", "-rln", "--include=*.py", "."],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    files = [f for f in result.stdout.splitlines() if f]

    offenders = []
    pattern = re.compile(
        r"\b(infra\.project_config|from\s+infra\.project_config|import\s+infra\.project_config)\b"
    )

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
        "Found infra.project_config references (forbidden by invariant #53):\n"
        + "\n".join(f"  - {p}" for p in offenders)
    )


# ---------------------------------------------------------------------------
# G3: Canonical symbols migrated + representative consumers use lingwen_project_config
# ---------------------------------------------------------------------------


def test_canonical_symbols_migrated():
    """Verify both canonical symbols importable + representative consumer migrated."""
    import lingwen_project_config

    # Both symbols must be importable
    from dataclasses import is_dataclass

    assert is_dataclass(lingwen_project_config.ProjectConfig), (
        "ProjectConfig should be a dataclass"
    )
    assert callable(lingwen_project_config.update_project_creation_mode), (
        "update_project_creation_mode should be callable"
    )

    # Spot-check 3 representative consumers: 1 apps, 1 intra-infra, 1 tests
    representative_files = [
        REPO_ROOT / "apps" / "studio_api" / "routes" / "creator_volume.py",
        REPO_ROOT / "infra" / "studio_registry.py",
        REPO_ROOT / "tests" / "infra" / "test_project_config.py",
    ]
    for f in representative_files:
        content = f.read_text(encoding="utf-8")
        # Allow leading whitespace (Phase 33/37 lesson: function-body lazy imports)
        assert re.search(r"^\s*from lingwen_project_config\b", content, re.MULTILINE), (
            f"{f.name} should 'from lingwen_project_config' import (line-anchored, leading whitespace allowed)"
        )
        assert not re.search(r"^\s*from infra\.project_config\b", content, re.MULTILINE), (
            f"{f.name} should NOT 'from infra.project_config' import (forbidden by I053)"
        )


# ---------------------------------------------------------------------------
# G4: infra/project/__init__.py wildcard cleaned
# ---------------------------------------------------------------------------


def test_infra_project_init_no_project_config_wildcard():
    """Verify infra/project/__init__.py no longer references infra.project_config (or lingwen_project_config wildcard)."""
    init_file = REPO_ROOT / "infra" / "project" / "__init__.py"
    content = init_file.read_text(encoding="utf-8")

    assert "infra.project_config" not in content, (
        f"{init_file} should not reference 'infra.project_config' (deleted in C3)"
    )
    # Wildcard re-export through infra.project.* namespace is no longer needed;
    # consumers should import directly from lingwen_project_config
    assert not re.search(r"from\s+lingwen_project_config\s+import\s+\*", content), (
        f"{init_file} should not have wildcard re-export of lingwen_project_config"
    )
```

- [ ] **Step 5.2: Update `tests/test_phase18_10_stale_imports.py` whitelist (defensive)**

Phase 37 pattern: add `lingwen_project_config` to `ALLOWED_COMPAT_IMPORTS` to prevent future false-positive stale-imports from docstring/comment mentions.

Edit `tests/test_phase18_10_stale_imports.py` line 15-24 (the frozenset). Add entry:

```python
ALLOWED_COMPAT_IMPORTS = frozenset(
    {
        "infra.config",
        "infra.util",
        "infra.tools",
        "lingwen_paths",  # Phase 37: was "infra.paths" (now deleted; canonicalized)
        "lingwen_errors",     # Phase 36: was "infra.errors" (now deleted; canonicalized)
        "lingwen_project_config",  # Phase 38: was "infra.project_config" (now deleted; canonicalized)
        "infra.hooks",
    }
)
```

Verify:

```bash
grep -n "lingwen_project_config\|infra\.project_config" tests/test_phase18_10_stale_imports.py
```

Expected: 1 hit (the new whitelist line). 0 hits for `infra.project_config` (the old name should not appear in this test file's whitelist).

The whitelist prevents false positives where future code comments mention "used to be from infra.project_config" — those lines would otherwise match `from infra.` pattern and falsely flag.

NOTE: `infra.project_config` is NOT in the whitelist (only `lingwen_project_config` is) — this is intentional, because any future re-introduction of `from infra.project_config import ...` should be flagged as stale.

- [ ] **Step 5.3: Write `docs/superpowers/handoffs/2026-09-08-phase-38-p3-archdebt-project-config-handoff.md`**

Modeled on `docs/superpowers/handoffs/2026-09-08-phase-37-p3-archdebt-paths-handoff.md`. Cover:
- Phase 38 status: CLOSED
- Commit chain: 6 atomic (C0 spec+plan / C1 scaffold / C2 migrate / C3 delete / C4 version+invariant / C5 guards+doc-sync)
- Validation gates: G1-G10 (11 entries) GREEN
- Carryover closure: P3-ARCHDEBT 3/5 → CLOSED
- Lessons learned: any new N.14 lessons specific to Phase 38

- [ ] **Step 5.4: Run phase38 guards**

```bash
uv run pytest tests/test_phase38_lingwen_project_config.py -v
```

Expected: 6/6 GREEN.

- [ ] **Step 5.5: Run full backend regression suite**

```bash
uv run pytest packages/lingwen-creator/tests/ packages/lingwen-shared/tests/ packages/lingwen-core/tests/ packages/lingwen-got/tests/ packages/lingwen-world-model/tests/ packages/lingwen-pipeline/tests/ apps/studio_api/tests/ tests/infra/ tests/agent_system/ tests/test_phase18_10_stale_imports.py tests/test_phase38_lingwen_project_config.py -v
```

Expected: 0 failures (allow same pre-existing 1 stale-import xfail as Phase 37).

- [ ] **Step 5.6: ruff lint**

```bash
ruff check packages/lingwen-project-config/ apps/ packages/ infra/
```

Expected: same 4 pre-existing E741 errors in unrelated files (Phase 37 baseline). 0 new errors.

- [ ] **Step 5.7: Staging-leak check (Phase 36 CRITICAL lesson — verify BOTH points)**

**Point 1**: post-ff-merge (after merging branch to master):

```bash
git checkout master
git merge --ff-only phase-38-p3-archdebt-project-config
git status  # must show clean
```

**Point 2**: post-worktree-remove:

```bash
git worktree remove --force .claude/worktrees/phase-38-p3-archdebt-project-config
git status  # must show clean
git worktree list  # must NOT show phase-38 worktree
```

Expected: BOTH `git status` calls return clean (no uncommitted files, no orphan staging).

- [ ] **Step 5.8: Commit C5**

```bash
git checkout phase-38-p3-archdebt-project-config  # return to branch
git add tests/test_phase38_lingwen_project_config.py tests/test_phase18_10_stale_imports.py docs/superpowers/handoffs/2026-09-08-phase-38-p3-archdebt-project-config-handoff.md
git commit -m "test(phase-38): regression guards + doc sync"
```

---

## Validation Gates Summary

| # | Gate | Expected |
|---|------|----------|
| G1 | `ruff check packages/lingwen-project-config/ apps/ packages/ infra/` | 4 pre-existing E741, 0 new |
| G2 | `pytest packages/lingwen-creator/tests/` | 73/73 |
| G3 | `pytest packages/lingwen-shared/tests/` | pass |
| G4 | `pytest packages/lingwen-core/tests/` | 68/68 |
| G5 | `pytest packages/lingwen-got/tests/` | 208/208 |
| G6 | `pytest packages/lingwen-world-model/tests/` | 201/201 |
| G7 | `pytest packages/lingwen-pipeline/tests/ apps/studio_api/tests/ tests/infra/ tests/agent_system/` | pass |
| G8 | `grep -rn "infra\.project_config" --include="*.py" infra/ apps/ packages/` | 0 hits |
| G9 | `pytest tests/test_phase18_10_stale_imports.py` | pass (stale-list updated) |
| G10 | `pytest tests/test_phase38_lingwen_project_config.py` | 6/6 GREEN |

**Combined target**: ~660 tests pass (Phase 37 baseline 658 + ~2 new).

---

## Execution Handoff

After completing all 5 tasks:

1. ✅ Spec + plan written (this file + spec)
2. ✅ 6 atomic commits on `phase-38-p3-archdebt-project-config`
3. ✅ Validation gates G1-G10 GREEN
4. ✅ BOTH staging-leak checks clean (per Phase 36 critical lesson)
5. ✅ Handoff doc written
6. ✅ Carryover closure: P3-ARCHDEBT 3/5 → CLOSED
7. ⏳ Next session: P3-ARCHDEBT Phase 39 — `infra.logging_config.*` (8 consumers) OR `infra.studio_registry.*` (50 consumers)

---

> Companion spec: `docs/superpowers/specs/2026-09-08-phase-38-p3-archdebt-project-config-design.md`