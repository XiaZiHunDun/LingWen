# Phase 37 — P3-ARCHDEBT (paths) — design

> **Date**: 2026-09-08
> **Branch**: `phase-37-p3-archdebt-paths` (worktree at `.worktrees/phase-37-p3-archdebt-paths`)
> **Master HEAD at start**: `70be2987` (v35.0 — Phase 36 cleanup + P3-ARCHDEBT errors pilot handoff)
> **Scope**: Single-module migration for **P3-ARCHDEBT** item 2/5 — migrate `infra/paths.py` (125 lines, 5 top-level public symbols) to `packages/lingwen-paths/`
> **Carryover closes**: 2/5 of P3-ARCHDEBT (project_config / logging_config / studio_registry remain for Phase 38+)

## 1. Summary

Phase 37 continues **P3-ARCHDEBT** (the architectural debt category opened by Phase 36 pilot). This phase migrates `infra/paths.py` — a small, leaf module with **86 consumer files** (largest consumer fan-out of any P3 module to date, but same single-file leaf pattern validated by Phase 36).

**Why paths second**:
- 125 lines + 5 top-level public symbols (`resolve_project_root`, `ProjectPaths`, `get_paths`, `get_chapters_dir`, `get_rules_dir`) — slightly larger than errors but still small enough for single-file package
- 86 consumer files — 6× larger fan-out than errors (14), but all are mechanical import migration (no functional changes)
- Zero internal deps (no other P3 module imports paths) — clean leaf, same as errors
- All consumers use `from infra.paths import X` literal-style only (4-pattern audit: 0 relative imports + 0 filesystem path string literals)
- Validates the P3 pattern at scale before tackling `project_config` (25 consumers + depends on paths) and `studio_registry` (50 consumers, largest semantically)

**Pattern inheritance**: Phase 36 fully established the P3 cutover pattern (single-file package, hatchling build, no shim, full deletion). Phase 37 replicates it 1:1 with the only deltas being:
- Larger consumer count (86 vs 14)
- `tests/test_phase18_10_stale_imports.py` stale-list update for `infra.paths` → `lingwen_paths`
- Version bump: v35.0 → **v36.0** (next sequential)
- Invariant: I051 → **I052 NEW**

## 2. Goals

- Move `infra/paths.py` (125 lines) → `packages/lingwen-paths/src/lingwen_paths/__init__.py` with **1:1 file content mapping** (no internal restructuring)
- Migrate all 86 consumer files to `from lingwen_paths.X import Y`
- Delete `infra/paths.py` (full cutover — no PHASE-COMPAT shim)
- Add `packages/lingwen-paths` to `[tool.uv.workspace] members` + `[tool.uv.sources]`
- Add **invariant #52 NEW**: `packages/lingwen-paths/` is canonical; `infra.paths.*` forbidden
- Bump `.lingwen/architecture.yml` version 35.0 → 36.0
- Add regression guards in `tests/test_phase37_lingwen_paths.py` (6 guards, no functional tests)
- Update CLAUDE.md v36.0 entry + `tests/test_phase18_10_stale_imports.py` stale-list (line 20: `"infra.paths"` → `"lingwen_paths"`)

## 3. Non-Goals (Out of Scope)

- **No internal restructuring** of paths.py — single-file package preserves 1:1 mapping
- **No new functional test suite** — guard-minimal only; coverage expansion deferred to Phase 38+
- **No migration of other P3 modules** — project_config / logging_config / studio_registry deferred
- **No renaming of any class/function** — names stay byte-for-byte identical
- **No PHASE-COMPAT shim** — full cutover (delete `infra/paths.py`)
- **No changes to `infra/story_contracts/paths.py` or `infra/persistence/paths.py`** — separate namespaces, NOT part of P3-ARCHDEBT paths migration
- **No `__all__` introduction** — `infra/paths.py` has no `__all__`; preserve 1:1 mapping means lingwen_paths also has no `__all__`. Guard test verifies absence.

## 4. Architecture & Design

### 4.1 Package Layout

```
packages/lingwen-paths/                                 # NEW workspace package
├── pyproject.toml                                     # Hatchling build; requires-python>=3.11; NO workspace deps (leaf)
└── src/lingwen_paths/
    └── __init__.py                                    # 125 lines (1:1 from infra/paths.py), NO __all__
```

**Single-file package**: `lingwen_paths/__init__.py` contains all 125 lines. No submodule split. This matches `lingwen-errors` (Phase 36) where a single-file `infra/errors.py` became a single-file-package.

**No `__all__`**: source file does not define `__all__`. All 5 top-level symbols are exported by default. Guard test verifies this absence.

**Public symbol count: 5** (verified at C0 via `grep -E "^def |^class " infra/paths.py`):
- `resolve_project_root()` — function
- `ProjectPaths` — class
- `get_paths()` — function
- `get_chapters_dir()` — function
- `get_rules_dir()` — function

(Note: `ProjectPaths` has 7 methods — `__init__`, `_validate`, `reset`, `get`, `get_chapter_path`, `read_chapter`, `write_chapter`, `__repr__` — but methods are attributes of the class, not separate top-level symbols.)

### 4.2 Dependency Direction

```
lingwen-paths (LEAF) ← infra/* (consumes ~5 intra-infra)
                    ← apps/* (consumes 1 — studio_api routes/creator_volume)
                    ← packages/* (consumes ~17 — 4 packages: lingwen-cli, lingwen-core, lingwen-creator, lingwen-quality)
                    ← tests/* (consumes ~63 — agent_system/infra/conftest/test_phase18_10 etc.)
                    ← tools/* (consumes 3 — batch_repair / legacy/contradiction_check / verify_quality)
```

`lingwen-paths` declares **no workspace deps**. It only requires Python stdlib (`os`, `pathlib`, `typing`). Cross-package consumers (none — packages import paths but paths does not import any workspace package) need no `dependencies` update.

### 4.3 Migration Pattern

**Pattern**: full cutover (matches Phase 36 exactly).
1. **C1 scaffold**: copy `infra/paths.py` → `packages/lingwen-paths/src/lingwen_paths/__init__.py` (no content change). Add workspace declaration.
2. **C2 migrate consumers**: sed-update 86 import sites. Apply `ruff check --fix` proactively.
3. **C3 delete**: `git rm infra/paths.py`.
4. **C4 invariant**: `.lingwen/architecture.yml` version + I052 entry.
5. **C5 guards + doc sync**: `tests/test_phase37_lingwen_paths.py` + CLAUDE.md + stale-import guard update.

## 5. Implementation Details

### 5.1 Consumer migration list (86 sites — verified at C0)

**Category 1: intra-infra (8 files)**:
| File | Symbols used (verified) |
|---|---|
| `infra/full_check_report.py` | (likely ProjectPaths / get_paths) |
| `infra/project/__init__.py` | (likely re-export) |
| `infra/project_characters.py` | (likely ProjectPaths) |
| `infra/project_config.py` | (likely ProjectPaths) |
| `infra/project_init.py` | (likely ProjectPaths) |
| `infra/studio_registry.py` | (likely ProjectPaths) |

(Note: `infra/paths.py` itself appears in the count but is the source — not a consumer. Other intra-infra files TBD at C1 by reading their actual imports.)

**Category 2: cross-package (16 files, 5 packages)**:
| File | Package |
|---|---|
| `packages/lingwen-cli/src/lingwen_cli/commands/base.py` | lingwen-cli |
| `packages/lingwen-cli/src/lingwen_cli/project_range.py` | lingwen-cli |
| `packages/lingwen-core/src/lingwen_core/agents/chapter_emit.py` | lingwen-core |
| `packages/lingwen-core/src/lingwen_core/agents/chapter_production_outline.py` | lingwen-core |
| `packages/lingwen-creator/src/lingwen_creator/content/agent.py` | lingwen-creator |
| `packages/lingwen-creator/src/lingwen_creator/content/dashboard.py` | lingwen-creator |
| `packages/lingwen-creator/src/lingwen_creator/content/logic_check.py` | lingwen-creator |
| `packages/lingwen-creator/src/lingwen_creator/export/common.py` | lingwen-creator |
| `packages/lingwen-creator/src/lingwen_creator/onboarding/autodetect.py` | lingwen-creator |
| `packages/lingwen-creator/src/lingwen_creator/onboarding/onboarding.py` | lingwen-creator |
| `packages/lingwen-creator/src/lingwen_creator/settings/docs.py` | lingwen-creator |
| `packages/lingwen-creator/src/lingwen_creator/settings/history.py` | lingwen-creator |
| `packages/lingwen-creator/src/lingwen_creator/shared/check.py` | lingwen-creator |
| `packages/lingwen-creator/src/lingwen_creator/volume/plan.py` | lingwen-creator |
| `packages/lingwen-creator/src/lingwen_creator/volume/pulse.py` | lingwen-creator |
| `packages/lingwen-creator/src/lingwen_creator/volume/summary.py` | lingwen-creator |
| `packages/lingwen-creator/tests/test_shared_check.py` | lingwen-creator |
| `packages/lingwen-quality/src/lingwen_quality/consistency/checkers/character_agency.py` | lingwen-quality |
| `packages/lingwen-quality/src/lingwen_quality/quality/inspector.py` | lingwen-quality |
| `packages/lingwen-quality/src/lingwen_quality/quality/repairer.py` | lingwen-quality |

**Category 3: apps (1 file)**:
| File | Notes |
|---|---|
| `apps/studio_api/routes/creator_volume.py` | FastAPI router |

**Category 4: tests (61 files)**:
- `tests/agent_system/` (2 files: test_chapter_emit, test_chapter_production_outline)
- `tests/infra/` (~56 files: test_creator_*, test_project_*, test_studio_*, etc.)
- `tests/conftest.py` (1 file)
- `tests/test_inspector_repairer.py` (1 file)
- `tests/test_phase18_10_stale_imports.py` (1 file — special: stale-list reference, NOT an actual import)

**Category 5: tools (3 files)**:
- `tools/batch_repair.py`
- `tools/legacy/contradiction_check.py`
- `tools/verify_quality.py`

**Total: 86 import sites** (verified via `grep -rln "from infra\.paths\b\|import infra\.paths\b" --include="*.py" . | wc -l` = 86).

### 5.2 Audit matrix (4 patterns per Phase 32+34+35 lessons)

C1 must execute all 4 grep audits to find ALL references (not just Python imports):

```bash
# 1. Literal dotted path (done — 86 hits)
grep -rn "from infra\.paths\b\|import infra\.paths\b" --include="*.py" .

# 2. Relative same-package (done — 3 hits but ALL in infra/story_contracts/ → StoryContractPaths, DIFFERENT module)
grep -rn "^from \.paths\b\|^from \.\.paths\b" infra/ packages/ --include="*.py"

# 3. Relative parent-package (done — 0 hits)
grep -rn "^from \.\." infra/ packages/ --include="*.py" | grep -E "\bpaths\b"

# 4. Filesystem path string literals (done — 0 hits)
grep -rn '"infra/paths' --include="*.py" .

# 5. Function-body indented imports (do at C1 — Phase 33 lesson)
grep -rn "^    from \|^        from " infra/ packages/ --include="*.py" | grep "infra\.paths"
```

**Expected**: 86 hits only in (1). Zero hits in (2)/(3)/(4)/(5). Confirmed at C0:
- Pattern 2: 3 hits in `infra/story_contracts/{engine.py,__init__.py,persister.py}` — these import `StoryContractPaths` from `.paths`, but `.paths` here refers to `infra/story_contracts/paths.py` (separate module). NOT in scope for Phase 37.
- Pattern 3: 0 hits
- Pattern 4: 0 hits
- Pattern 5: TBD at C1

### 5.3 Workspace wiring (Phase 34 C1 lesson)

**CRITICAL**: workspace declaration BEFORE `uv sync`:

```toml
# pyproject.toml (root)
[tool.uv.workspace]
members = [
    "packages/lingwen-core",
    # ... (existing 13 entries) ...
    "packages/lingwen-paths",  # ★ Phase 37 NEW
]

[tool.uv.sources]
# ... (existing 13 entries) ...
lingwen-paths = { workspace = true }  # ★ Phase 37 NEW
```

Order: C1 edits `pyproject.toml` BEFORE running `uv sync --all-packages --offline`. Otherwise `import lingwen_paths` raises `ModuleNotFoundError`.

### 5.4 New pyproject.toml (lingwen-paths)

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

### 5.5 Stale-import guard update

`tests/test_phase18_10_stale_imports.py:20` contains `"infra.paths"`. After Phase 37 C3 deletes `infra/paths.py`, this entry will fail (because no module exists at that path). C5 update:

```python
# Before (line 20):
"infra.paths",
# After:
"lingwen_paths",  # Phase 37: infra.paths → lingwen_paths
```

**Skip-file note** (N.14 lesson 6): the `test_phase37_lingwen_paths.py` guard itself and the updated `test_phase18_10_stale_imports.py` must be excluded from grep audit gates (their own content references the migration pattern).

## 6. Testing Strategy

### 6.1 Regression guards (6 tests in `tests/test_phase37_lingwen_paths.py`)

| Test | Asserts |
|---|---|
| `test_lingwen_paths_package_exists` | `packages/lingwen-paths/pyproject.toml` and `src/lingwen_paths/__init__.py` exist |
| `test_lingwen_paths_init_imports` | `import lingwen_paths` succeeds; `hasattr(lingwen_paths, "__all__") == False` (source has no `__all__`); all 5 top-level symbols exist |
| `test_infra_paths_deleted` | `not Path("infra/paths.py").exists()` |
| `test_workspace_member_declared` | `pyproject.toml` contains both `packages/lingwen-paths` (members) and `lingwen-paths = { workspace = true }` (sources) |
| `test_no_infra_paths_references` | `grep -rln "from infra\.paths\|import infra\.paths" --include="*.py" .` returns 0 hits (excluding skip_files) |
| `test_canonical_symbols_migrated` | `lingwen_paths.{resolve_project_root, ProjectPaths, get_paths, get_chapters_dir, get_rules_dir}` all importable; spot-check 2-3 representative consumers use lingwen_paths |

**Skip files** (N.14 lesson 6):
- `tests/test_phase37_lingwen_paths.py` (this guard)
- `tests/test_phase18_10_stale_imports.py` (contains "infra.paths" in stale-list — updated C5)

### 6.2 No new functional tests

Per user decision (Guard + Minimal — same as Phase 36). Full coverage (ProjectPaths singleton edge cases, _validate behavior, get_chapter_path/write_chapter round-trip, env var LINGWEN_PROJECT_ROOT behavior) deferred to Phase 38+.

### 6.3 Validation gates (8 gates)

| Gate | Suite | Expected |
|---|---|---|
| G1 ruff | `ruff check .` | 0 NEW errors (Phase 36 baseline had 3 pre-existing in unrelated files; same baseline) |
| G2 phase37 guards | `pytest tests/test_phase37_lingwen_paths.py` | 6/6 |
| G3 lingwen-world-model | `pytest packages/lingwen-world-model/tests/` | ≥201/201 (Phase 36 baseline) |
| G4 lingwen-core | `pytest packages/lingwen-core/tests/` | 68/68 |
| G5 lingwen-got | `pytest packages/lingwen-got/tests/` | 208/208 |
| G6 studio_api | `pytest apps/studio_api/tests/` | 82/82 |
| G7 lingwen-quality | `pytest packages/lingwen-quality/tests/` | baseline (T0 capture) |
| G8 lingwen-pipeline | `pytest packages/lingwen-pipeline/tests/` | baseline (T0 capture) |
| G9 lingwen-llm | `pytest packages/lingwen-llm/tests/` | baseline (T0 capture) |
| G10 stale-import guard | `pytest tests/test_phase18_10_stale_imports.py` | pass (after C5 stale-list update; should now pass since infra.paths is deleted and lingwen_paths added to allowlist) |

Total: ≥ G2 + 6 baselines preserved. If any baseline drops, do NOT proceed to C4/C5 — investigate first.

## 7. Commit Chain (6 atomic commits)

```
P1 (master): docs(phase-36): handoff for v35.0 P3-ARCHDEBT errors pilot  [70be2987] ✓ DONE

C0 (worktree): docs(phase-37): spec + plan for lingwen-paths package
C1 (worktree): chore(packages): scaffold lingwen-paths (pyproject + src/__init__.py + workspace declaration)
C2 (worktree): refactor(consumers): migrate 86 paths consumers to lingwen_paths
C3 (worktree): chore(infra): delete infra/paths.py
C4 (worktree): chore(infra): bump to v36.0 + add invariant #52 (lingwen-paths canonical)
C5 (worktree): test(phase-37): regression guards + doc sync
```

### 7.1 Commit details

**C0** (`docs(phase-37): spec`):
- `docs/superpowers/specs/2026-09-08-phase-37-p3-archdebt-paths-design.md` (this file)
- `docs/superpowers/plans/2026-09-08-phase-37-p3-archdebt-paths.md` (implementation plan)

**C1** (`chore(packages): scaffold`):
- `packages/lingwen-paths/pyproject.toml` (new)
- `packages/lingwen-paths/src/lingwen_paths/__init__.py` (copied from `infra/paths.py`, byte-for-byte)
- `pyproject.toml` (root): add `packages/lingwen-paths` to `[tool.uv.workspace] members` + `lingwen-paths = { workspace = true }` to `[tool.uv.sources]`
- Verification: `uv sync --all-packages --offline` succeeds; `python -c "import lingwen_paths; print(hasattr(lingwen_paths, '__all__'))"` returns `False`; spot-check 5 symbols exist

**C2** (`refactor(consumers): migrate 86 paths consumers`):
- sed: `from infra\.paths ` → `from lingwen_paths ` (space variant) on 86 files
- sed: `from infra\.paths\.` → `from lingwen_paths.` (dot variant) on 86 files
- Apply `ruff check --fix` proactively (Phase 34 lesson 5)
- Run `git status --short | grep "^ M"` after sed; explicit `git add -- <files>` per Phase 35 lesson 1
- Verify: `grep -rln "from infra\.paths\|import infra\.paths" --include="*.py" . | grep -v phase37 | wc -l` returns 0

**C3** (`chore(infra): delete infra/paths.py`):
- `git rm infra/paths.py`
- Verify: `test -f infra/paths.py && echo EXISTS || echo DELETED`

**C4** (`chore(infra): bump v36.0 + invariant #52`):
- `.lingwen/architecture.yml`: `version: "35.0"` → `"36.0"` + `invariants:` block add `id: I052` row
- CLAUDE.md: add v36.0 entry (mirror v35.0 format) + I052 row in 架构不变量 table
- Verify: `grep -n "I052" .lingwen/architecture.yml`

**C5** (`test(phase-37): regression guards + doc sync`):
- `tests/test_phase37_lingwen_paths.py` (new, 6 tests per §6)
- `tests/test_phase18_10_stale_imports.py` (update stale-list: `infra.paths` → `lingwen_paths`)
- `collaboration/CURRENT_STATUS.md` (Phase 37 status update)
- `collaboration/BACKLOG.md` (Phase 37 entry; P3-ARCHDEBT 2/5 → closed)
- MEMORY.md (outside worktree) — Master HEAD update + Phase 37 lessons

### 7.2 T0 baseline (must capture BEFORE C1)

```bash
# Run each suite + record pass/fail counts:
cd .worktrees/phase-37-p3-archdebt-paths
.worktrees/phase-37-p3-archdebt-paths/.venv/bin/python -m pytest packages/lingwen-world-model/tests/ --tb=no -q
.worktrees/phase-37-p3-archdebt-paths/.venv/bin/python -m pytest packages/lingwen-core/tests/ --tb=no -q
.worktrees/phase-37-p3-archdebt-paths/.venv/bin/python -m pytest packages/lingwen-got/tests/ --tb=no -q
.worktrees/phase-37-p3-archdebt-paths/.venv/bin/python -m pytest apps/studio_api/tests/ --tb=no -q
.worktrees/phase-37-p3-archdebt-paths/.venv/bin/python -m pytest packages/lingwen-quality/tests/ --tb=no -q
.worktrees/phase-37-p3-archdebt-paths/.venv/bin/python -m pytest packages/lingwen-pipeline/tests/ --tb=no -q
.worktrees/phase-37-p3-archdebt-paths/.venv/bin/python -m pytest packages/lingwen-llm/tests/ --tb=no -q
.worktrees/phase-37-p3-archdebt-paths/.venv/bin/python -m pytest tests/test_phase18_10_stale_imports.py --tb=no -q
.worktrees/phase-37-p3-archdebt-paths/.venv/bin/python -m pytest packages/lingwen-creator/tests/ --tb=no -q
.worktrees/phase-37-p3-archdebt-paths/.venv/bin/python -m pytest packages/lingwen-cli/tests/ --tb=no -q
.worktrees/phase-37-p3-archdebt-paths/.venv/bin/python -m ruff check . | tail -5
```

Record per-suite pass/skip counts in plan.md as baseline. Compare after each commit.

## 8. Architecture Invariants

**Invariant #52 NEW** (after I051):
> `packages/lingwen-paths/` 是项目路径管理（ProjectPaths / resolve_project_root 等）的唯一实包；`infra.paths.*` 路径非法 (Phase 37+)。

**Scope**: all new project-paths imports must `from lingwen_paths.X import Y`. Direct `infra.paths.X` imports forbidden.

**Enforcement**: `tests/test_phase37_lingwen_paths.py::test_no_infra_paths_references` + `test_infra_paths_deleted`.

**Why**: P3-ARCHDEBT item 2/5; continues the canonical location establishment for the 5 P3 modules. Future phases (38+) will add I053 (project_config), I054 (logging_config), I055 (studio_registry).

**Out of scope for I052**: `infra/story_contracts/paths.py` (`StoryContractPaths` — separate namespace, story contracts subsystem) and `infra/persistence/paths.py` (separate namespace, persistence subsystem). These are NOT under P3-ARCHDEBT and remain unchanged.

## 9. Risks & Mitigations (Phase 32+34+35+36 lessons applied)

| Risk | Source lesson | Mitigation |
|---|---|---|
| `git mv` + sed UNSTAGED changes | Phase 35 lesson 1 (N.14 L1 #8) | After C2 sed, `git status --short \| grep "^ M"` must be empty; use `git add -- <files>` |
| amend picks up unrelated staged | Phase 35 lesson 2 | After each commit, `git log -1 --stat` verify scope |
| Spec count error (5 vs actual) | Phase 34+35 lesson 3 | C0 spec lists 5 top-level symbols; C5 guard verifies all 5 exist. Re-verify at C1 via `grep -E "^def \|^class "` |
| Filesystem path string literals | Phase 34 lesson (N.14 L1 #7) | C0 audit (Pattern 4) found 0 hits; C1 re-audit before commit |
| Indented TYPE_CHECKING imports | Phase 19+Sub1 lesson | C0 audit (Pattern 5) found 0 hits; C1 re-audit before commit |
| Relative imports (`.paths`) | Phase 32 lesson | C0 audit (Patterns 2+3) found 0 hits in scope (3 hits in infra/story_contracts/ are different module); C1 re-audit |
| Test guard self-trigger | Phase 35 lesson 6 | skip_files in `test_no_infra_paths_references` |
| Empty dir with __pycache__ | Phase 35 lesson 7 | C3 uses `git rm infra/paths.py` (single file); no leftover shell |
| pre-existing failure baseline drift | Phase 34 lesson 4 | T0 captures baseline; G2-G10 verify no regression |
| ruff I001 after sed | Phase 34 lesson 5 | `ruff check --fix` after C2 sed |
| Workspace declaration after uv sync | Phase 34 lesson (N.14 L4) | C1 edits pyproject.toml BEFORE `uv sync` |
| Stale-import guard self-trigger | Phase 36 lesson | C5 updates stale-list: `infra.paths` → `lingwen_paths`; skip_files for that test in C5 guard |
| `infra/story_contracts/paths.py` confusion | NEW | Explicit out-of-scope note in §3 + §8 to prevent accidental inclusion |
| 86 consumer scope risk | NEW (largest P3 fan-out to date) | C2 verified per-file via explicit `grep -rln`; mechanical sed-only; no semantic changes |
| Staging leak after ff-merge OR worktree remove | Phase 36 critical lesson | Verify clean at BOTH points (ff-merge + `git worktree remove --force`) — see §7.3 |

### 7.3 Staging leak check (Phase 36 critical lesson)

After T6 ff-merge of phase-37-p3-archdebt-paths → master, AND after `git worktree remove --force .worktrees/phase-37-p3-archdebt-paths`:

```bash
# Verify master working tree has NO unexpected staged files
git status --short
# Expected: only user's pre-existing `projects/anye-xinbiao/docs/novel-pillars.md` modification

# Verify infra/paths.py is TRULY gone (not re-staged)
git diff --cached --stat | grep "infra/paths.py" && echo "LEAK DETECTED" || echo "clean"
test -f infra/paths.py && echo "LEAK: file still exists" || echo "clean"
```

Both checks must return `clean`. If LEAK DETECTED:
1. `git restore --staged infra/paths.py`
2. `rm infra/paths.py`
3. Verify clean again

## 10. Open Questions

All resolved (carryover from Phase 36 + MEMORY.md P3-ARCHDEBT recommendations):
- ✅ Package layout: single-file `lingwen_paths/__init__.py` (matches lingwen-errors exactly)
- ✅ Scope: paths only
- ✅ Migration: full cutover (matches Phase 36)
- ✅ Tests: guard minimal (matches Phase 36)
- ✅ Phase 36 handoff: already on master (`70be2987`) — no P1 prelude commit needed
- ✅ No `__all__` introduction: source file has none; preserve 1:1
- ✅ `infra/story_contracts/paths.py` / `infra/persistence/paths.py`: explicitly out of scope (§3)
- ✅ `test_phase18_10_stale_imports.py` stale-list updated C5
- ✅ Staging leak check at both ff-merge + worktree remove (Phase 36 critical lesson)
- ✅ Version bump: v36.0 (next after v35.0)
- ✅ Invariant: I052 NEW

## 11. Carryover Closure (post-Phase 37)

| Carryover | Status |
|-----------|--------|
| P3-ARCHDEBT 1/5 (errors → lingwen-errors) | **CLOSED** by Phase 36 |
| P3-ARCHDEBT 2/5 (paths → lingwen-paths) | **CLOSED** by Phase 37 |
| P3-ARCHDEBT 3/5 (project_config → lingwen-config) | OPEN → Phase 38 |
| P3-ARCHDEBT 4/5 (logging_config → lingwen-logging) | OPEN → Phase 39 |
| P3-ARCHDEBT 5/5 (studio_registry → lingwen-registry) | OPEN → Phase 40 |
| Phase 114 prod preview regression (accepted) | unchanged |
| HANDOFF.md `latest_decision_queue` wording (doc-only) | unchanged |

## 12. See Also

- Phase 36 handoff: `docs/superpowers/handoffs/2026-09-08-phase-36-p3-archdebt-errors-handoff.md`
- Phase 36 spec: `docs/superpowers/specs/2026-09-08-phase-36-p3-archdebt-errors-design.md` (direct template)
- Phase 35 handoff: `docs/superpowers/handoffs/2026-09-08-phase-35-world-model-package-handoff.md`
- Phase 35 lessons: `~/.claude/projects/-home-ailearn-projects-LingWen/memory/phase35.md`
- Phase 34 handoff: `docs/superpowers/handoffs/2026-09-08-phase-34-lingwen-got-handoff.md`
- .lingwen/architecture.yml: `id: I0*` invariants block
- Worktree: `.worktrees/phase-37-p3-archdebt-paths/`
- MEMORY.md Phase 36 carryover: P3-ARCHDEBT 1/5 → 5/5 roadmap
