# Phase 36 — P3-ARCHDEBT (errors pilot) — design

> **Date**: 2026-09-08
> **Branch**: `phase-36-p3-archdebt-errors` (worktree at `.worktrees/phase-36-p3-archdebt-errors`)
> **Master HEAD at start**: `61a35b56` (v34.0 — Phase 35 WORLD-MODEL-PACKAGE handoff)
> **Scope**: Single-module pilot for **P3-ARCHDEBT** — migrate `infra/errors.py` (380 lines, 21 public symbols) to `packages/lingwen-errors/`
> **Carryover closes**: 1/5 of P3-ARCHDEBT (paths / project_config / logging_config / studio_registry remain for Phase 37+)

## 1. Summary

Phase 36 opens **P3-ARCHDEBT** (new architectural debt category covering infrastructure utility files that have grown into first-class domain modules). This phase is a **pilot** focused exclusively on `infra/errors.py` — the smallest, most contained leaf module with zero intra-P3 cross-references.

**Why errors first**:
- 380 lines + 23 public symbols — smallest P3 candidate
- 14 consumer files: 4 packages (6 files) + 8 intra-infra files — manageable fan-out
- Zero internal deps (no other P3 module imports errors) — clean leaf
- `SnapshotError` has 2 active consumers in `lingwen-world-model` (NOT stale despite PHASE-COMPAT docstring) — confirms package needs to expose it

**Why pilot pattern**: Phase 32/34/35 each started with a small, isolated pilot before scaling. Same risk reduction applies here. Phase 37+ will tackle the remaining 4 P3 modules with the validated pattern.

## 2. Goals

- Move `infra/errors.py` (380 lines) → `packages/lingwen-errors/src/lingwen_errors/__init__.py` with **1:1 file content mapping** (no internal restructuring)
- Migrate all 14 consumer files to `from lingwen_errors.X import Y`
- Delete `infra/errors.py` (full cutover — no PHASE-COMPAT shim)
- Add `packages/lingwen-errors` to `[tool.uv.workspace] members` + `[tool.uv.sources]`
- Add **invariant #51 NEW**: `packages/lingwen-errors/` is canonical; `infra.errors.*` forbidden
- Bump `.lingwen/architecture.yml` version 34.0 → 35.0
- Add regression guards in `tests/test_phase36_lingwen_errors.py` (6 guards, no functional tests)
- Update CLAUDE.md v35.0 entry + `tests/test_phase18_10_stale_imports.py` stale-list

## 3. Non-Goals (Out of Scope)

- **No internal restructuring** of errors.py — single-file package preserves 1:1 mapping
- **No new functional test suite** — guard-minimal only; coverage expansion deferred to Phase 37+
- **No migration of other P3 modules** — paths / project_config / logging_config / studio_registry deferred
- **No removal of SnapshotError** — it has 2 active consumers; PHASE-COMPAT docstring is now stale but class stays
- **No PHASE-COMPAT shim** — full cutover (delete `infra/errors.py`)
- **No renaming of any class/function** — names stay byte-for-byte identical

## 4. Architecture & Design

### 4.1 Package Layout

```
packages/lingwen-errors/                              # NEW workspace package
│   ├── pyproject.toml                              # Hatchling build; requires-python>=3.11; NO workspace deps (leaf)
│   └── src/lingwen_errors/
│       └── __init__.py                             # 380 lines (1:1 from infra/errors.py), 21 __all__ symbols
```

**Single-file package**: `lingwen_errors/__init__.py` contains all 380 lines + `__all__`. No submodule split. This matches the established pattern from `lingwen-got` (Phase 34) and `lingwen-world-model` (Phase 35) where a multi-file dir became a multi-file package; Phase 36 is single-file → single-file-package.

**`__all__` count: 23** (verified via `awk '/^__all__ = \[/, /^\]/' infra/errors.py | grep -c '"'`):
- 8 utility/factory: `BaseError, create, is_instance, wrap, unwrap, from_dict, from_json, capture_stack_trace`
- 15 subclasses: `RetryableError, FatalError, ValidationError, NotFoundError, ConflictError, AuthenticationError, AuthorizationError, RateLimitError, NetworkError, TimeoutError, ServiceUnavailableError, DatabaseError, ConfigurationError, NotImplementedError, SnapshotError`

### 4.2 Dependency Direction

```
lingwen-errors (LEAF) ← lingwen-quality (consumes 2)
                     ← lingwen-world-model (consumes 2; SnapshotError)
                     ← lingwen-pipeline (consumes 1)
                     ← lingwen-llm (consumes 1)
                     ← infra/* (consumes 7 — intra-infra)
                     ← tests/* (consumes 1 — stale-import guard)
```

`lingwen-errors` declares **no workspace deps**. It only requires Python stdlib (`json`, `traceback`, `dataclasses`, `datetime`, `typing`). Cross-package consumers will need to declare `lingwen-errors` in their own `pyproject.toml [project.dependencies]`.

### 4.3 Migration Pattern

**Pattern**: full cutover (matches Phase 32 / 34 / 35).
1. **C1 scaffold**: copy `infra/errors.py` → `packages/lingwen-errors/src/lingwen_errors/__init__.py` (no content change). Add workspace declaration.
3. **C2 migrate consumers**: sed-update 14 import sites. Apply `ruff check --fix` proactively.
4. **C3 delete**: `git rm infra/errors.py`.
5. **C4 invariant**: `.lingwen/architecture.yml` version + I051 entry.
6. **C5 guards + doc sync**: `tests/test_phase36_lingwen_errors.py` + CLAUDE.md + stale-import guard update.

## 5. Implementation Details

### 5.1 Consumer migration list (14 sites — verified at C0)

**Category 1: cross-package (6 files, 4 packages)**:
| File | Symbols used (verified) |
|---|---|
| `packages/lingwen-quality/src/lingwen_quality/consistency/checker_feedback.py` | `BaseError` family |
| `packages/lingwen-quality/src/lingwen_quality/consistency/creative_whitelist.py` | `BaseError` family |
| `packages/lingwen-world-model/src/lingwen_world_model/character_snapshot.py` | `SnapshotError` |
| `packages/lingwen-world-model/src/lingwen_world_model/foreshadow_snapshot.py` | `SnapshotError` |
| `packages/lingwen-pipeline/src/lingwen_pipeline/state_machine.py` | `BaseError` family |
| `packages/lingwen-llm/src/lingwen_llm/providers/base.py` | `BaseError` family |

**Category 2: intra-infra (8 files)**:
| File | Notes |
|---|---|
| `infra/__init__.py` | re-export list |
| `infra/health.py` | |
| `infra/llm_cache.py` | |
| `infra/permission.py` | |
| `infra/schema.py` | |
| `infra/tool.py` | |
| `infra/types.py` | |
| `infra/util/retry.py` | |

**Category 3: stale-list reference (1 file — NOT a consumer)**:
| File | Notes |
|---|---|
| `tests/test_phase18_10_stale_imports.py` | Contains string `"infra.errors"` in stale-import list (line 19). Not an actual import; only needs C5 string replacement: `"infra.errors"` → `"lingwen_errors"` |

**Total: 14 import sites** (verified via `grep -rln "from infra\.errors\|import infra\.errors" --include="*.py" . | grep -v "^./infra/errors.py$" | wc -l` = 14).

### 5.2 Audit matrix (4 patterns per Phase 32+34+35 lessons)

C1 must execute all 4 grep audits to find ALL references (not just Python imports):

```bash
# 1. Literal dotted path
grep -rn "from infra\.errors\b" --include="*.py" .

# 2. Relative same-package (rare for errors since it's leaf, but check)
grep -rn "from \.errors\b" infra/ packages/

# 3. Relative parent-package (very rare for errors)
grep -rn "from \.\.errors\b" infra/ packages/

# 4. Filesystem path string literals
grep -rn "infra/errors" --include="*.py" .  # may find Path(...) or string-built paths

# Function-body indented
grep -rn "^    from \|^        from " infra/ packages/ --include="*.py" | grep "infra\.errors"
```

Expected: hits only in (1) — `from infra.errors import X` style. Zero hits in (2)/(3)/(4)/(5). If any hit, document in C1 + add to consumer migration set.

### 5.3 Workspace wiring (Phase 34 C1 lesson)

**CRITICAL**: workspace declaration BEFORE `uv sync`:

```toml
# pyproject.toml (root)
[tool.uv.workspace]
members = [
    "packages/lingwen-core",
    # ... (existing 12 entries) ...
    "packages/lingwen-errors",  # ★ Phase 36 NEW
]

[tool.uv.sources]
# ... (existing 12 entries) ...
lingwen-errors = { workspace = true }  # ★ Phase 36 NEW
```

Order: C1 edits `pyproject.toml` BEFORE running `uv sync --all-packages --offline`. Otherwise `import lingwen_errors` raises `ModuleNotFoundError`.

### 5.4 New pyproject.toml (lingwen-errors)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "lingwen-errors"
version = "0.1.0"
description = "LingWen canonical error base classes (Phase 36 P3-ARCHDEBT pilot)"
requires-python = ">=3.11"
dependencies = []  # LEAF — zero workspace deps

[tool.hatch.build.targets.wheel]
packages = ["src/lingwen_errors"]
```

### 5.5 Stale-import guard update

`tests/test_phase18_10_stale_imports.py:19` contains `"infra.errors"`. After Phase 36 C3 deletes `infra/errors.py`, this entry will fail (because no module exists at that path). C5 update:

```python
# Before (line 19):
"infra.errors",
# After:
"lingwen_errors",  # Phase 36: infra.errors → lingwen_errors
```

**Skip-file note** (N.14 lesson 6): the `test_phase36_lingwen_errors.py` guard itself and the updated `test_phase18_10_stale_imports.py` must be excluded from grep audit gates (their own content references the migration pattern).

## 6. Testing Strategy

### 6.1 Regression guards (6 tests in `tests/test_phase36_lingwen_errors.py`)

| Test | Asserts |
|---|---|
| `test_lingwen_errors_package_exists` | `packages/lingwen-errors/pyproject.toml` and `src/lingwen_errors/__init__.py` exist |
| `test_lingwen_errors_init_imports` | `import lingwen_errors` succeeds; `len(lingwen_errors.__all__) == 23` |
| `test_infra_errors_deleted` | `not Path("infra/errors.py").exists()` |
| `test_workspace_member_declared` | `pyproject.toml` contains both `packages/lingwen-errors` (members) and `lingwen-errors = { workspace = true }` (sources) |
| `test_no_infra_errors_references` | `grep -rln "from infra\.errors\|import infra\.errors" --include="*.py" .` returns 0 hits (excluding skip_files) |
| `test_snapshot_error_migrated` | `lingwen_errors.SnapshotError` is importable and `is BaseError` subclass; both `character_snapshot.py` and `foreshadow_snapshot.py` import it from `lingwen_errors` |

**Skip files** (N.14 lesson 6):
- `tests/test_phase36_lingwen_errors.py` (this guard)
- `tests/test_phase18_10_stale_imports.py` (contains "infra.errors" in stale-list — updated C5)

### 6.2 No new functional tests

Per user decision (Guard + Minimal). Full coverage (BaseError round-trip, factory function tests, subclass tag verification, cause-chain traversal) deferred to Phase 37+.

### 6.3 Validation gates (8 gates)

| Gate | Suite | Expected |
|---|---|---|
| G1 ruff | `ruff check .` | 0 NEW errors (pre-existing 3 in unrelated files OK) |
| G2 phase36 guards | `pytest tests/test_phase36_lingwen_errors.py` | 6/6 |
| G3 lingwen-world-model | `pytest packages/lingwen-world-model/tests/` | ≥201/201 (baseline) |
| G4 lingwen-core | `pytest packages/lingwen-core/tests/` | 68/68 |
| G5 lingwen-got | `pytest packages/lingwen-got/tests/` | 208/208 |
| G6 studio_api | `pytest apps/studio_api/tests/` | 82/82 |
| G7 lingwen-quality | `pytest packages/lingwen-quality/tests/` | baseline (T0 capture) |
| G8 lingwen-pipeline | `pytest packages/lingwen-pipeline/tests/` | baseline (T0 capture) |
| G9 lingwen-llm | `pytest packages/lingwen-llm/tests/` | baseline (T0 capture) |
| G10 stale-import guard | `pytest tests/test_phase18_10_stale_imports.py` | pass (after C5 stale-list update) |

Total: ≥ G2 + 6 baselines preserved. If any baseline drops, do NOT proceed to C4/C5 — investigate first.

## 7. Commit Chain (6 atomic commits)

```
P1 (master): docs(phase-35): handoff for v34.0 WORLD-MODEL-PACKAGE  [61a35b56] ✓ DONE

C0 (worktree): docs(phase-36): spec + plan for lingwen-errors package
C1 (worktree): chore(packages): scaffold lingwen-errors (pyproject + src/__init__.py + workspace declaration)
C2 (worktree): refactor(consumers): migrate 14 errors consumers to lingwen_errors
C3 (worktree): chore(infra): delete infra/errors.py
C4 (worktree): chore(infra): bump to v35.0 + add invariant #51 (lingwen-errors canonical)
C5 (worktree): test(phase-36): regression guards + doc sync
```

### 7.1 Commit details

**C0** (`docs(phase-36): spec`):
- `docs/superpowers/specs/2026-09-08-phase-36-p3-archdebt-errors-design.md` (this file)
- Implementation plan will be generated by writing-plans skill after user approves this spec (per brainstorming → writing-plans flow)

**C1** (`chore(packages): scaffold`):
- `packages/lingwen-errors/pyproject.toml` (new)
- `packages/lingwen-errors/src/lingwen_errors/__init__.py` (copied from `infra/errors.py`, byte-for-byte)
- `pyproject.toml` (root): add `packages/lingwen-errors` to `[tool.uv.workspace] members` + `lingwen-errors = { workspace = true }` to `[tool.uv.sources]`
- Verification: `uv sync --all-packages --offline` succeeds; `python -c "import lingwen_errors; print(len(lingwen_errors.__all__))"` returns 23

**C2** (`refactor(consumers): migrate 14 errors consumers`):
- sed: `from infra\.errors ` → `from lingwen_errors ` (space variant) on 14 files
- sed: `from infra\.errors\.` → `from lingwen_errors.` (dot variant) on 14 files
- Apply `ruff check --fix` proactively (Phase 34 lesson 5)
- Run `git status --short | grep "^ M"` after sed; explicit `git add -- <files>` per Phase 35 lesson 1
- Verify: `grep -rln "from infra\.errors\|import infra\.errors" --include="*.py" . | grep -v phase36 | wc -l` returns 0

**C3** (`chore(infra): delete infra/errors.py`):
- `git rm infra/errors.py`
- Verify: `test -f infra/errors.py && echo EXISTS || echo DELETED`

**C4** (`chore(infra): bump v35.0 + invariant #51`):
- `.lingwen/architecture.yml`: `version: "34.0"` → `"35.0"` + `invariants:` block add `id: I051` row
- CLAUDE.md: add v35.0 entry (mirror v34.0 format) + I051 row in 架构不变量 table
- Verify: `grep -n "I051" .lingwen/architecture.yml`

**C5** (`test(phase-36): regression guards + doc sync`):
- `tests/test_phase36_lingwen_errors.py` (new, 6 tests per §6)
- `tests/test_phase18_10_stale_imports.py` (update stale-list: `infra.errors` → `lingwen_errors`)
- `collaboration/CURRENT_STATUS.md` (Phase 36 status update)
- `collaboration/BACKLOG.md` (Phase 36 entry; P3-ARCHDEBT 1/5 → closed)
- MEMORY.md (outside worktree) — Master HEAD update + Phase 36 lessons

### 7.2 T0 baseline (must capture BEFORE C1)

```bash
# Run each suite + record pass/fail counts:
cd .worktrees/phase-36-p3-archdebt-errors
uv sync --all-packages --offline
uv pip install --offline pytest pytest-asyncio pytest-timeout pytest-cov pytest-env pytest-metadata pytest-json-report psutil
.worktrees/phase-36-p3-archdebt-errors/.venv/bin/python -m pytest packages/lingwen-world-model/tests/ --tb=no -q
.worktrees/phase-36-p3-archdebt-errors/.venv/bin/python -m pytest packages/lingwen-core/tests/ --tb=no -q
.worktrees/phase-36-p3-archdebt-errors/.venv/bin/python -m pytest packages/lingwen-got/tests/ --tb=no -q
.worktrees/phase-36-p3-archdebt-errors/.venv/bin/python -m pytest apps/studio_api/tests/ --tb=no -q
.worktrees/phase-36-p3-archdebt-errors/.venv/bin/python -m pytest packages/lingwen-quality/tests/ --tb=no -q
.worktrees/phase-36-p3-archdebt-errors/.venv/bin/python -m pytest packages/lingwen-pipeline/tests/ --tb=no -q
.worktrees/phase-36-p3-archdebt-errors/.venv/bin/python -m pytest packages/lingwen-llm/tests/ --tb=no -q
.worktrees/phase-36-p3-archdebt-errors/.venv/bin/python -m pytest tests/test_phase18_10_stale_imports.py --tb=no -q
.worktrees/phase-36-p3-archdebt-errors/.venv/bin/python -m ruff check . | tail -5
```

Record per-suite pass/skip counts in plan.md as baseline. Compare after each commit.

## 8. Architecture Invariants

**Invariant #51 NEW** (after I050):
> `packages/lingwen-errors/` 是错误基类系统的唯一实包；`infra.errors.*` 路径非法 (Phase 36+)。

**Scope**: all new error-class imports must `from lingwen_errors.X import Y`. Direct `infra.errors.X` imports forbidden.

**Enforcement**: `tests/test_phase36_lingwen_errors.py::test_no_infra_errors_references` + `test_infra_errors_deleted`.

**Why**: P3-ARCHDEBT pilot; establishes the canonical location for the 5 P3 modules. Future phases (37+) will add I052 (paths), I053 (project_config), I054 (logging_config), I055 (studio_registry).

## 9. Risks & Mitigations (Phase 32+34+35 lessons applied)

| Risk | Source lesson | Mitigation |
|---|---|---|
| `git mv` + sed UNSTAGED changes | Phase 35 lesson 1 (N.14 L1 #8) | After C2 sed, `git status --short \| grep "^ M"` must be empty; use `git add -- <files>` |
| amend picks up unrelated staged | Phase 35 lesson 2 | After each commit, `git log -1 --stat` verify scope |
| Spec count error (21 vs actual) | Phase 34+35 lesson 3 | C0 spec lists 23; C5 `__all__` guard uses `== 23`. Re-verify at C1 via `grep -c '^    "'` |
| Filesystem path string literals | Phase 34 lesson (N.14 L1 #7) | C1 audit includes `grep -rn "infra/errors" --include="*.py"` (Pattern 4) |
| Indented TYPE_CHECKING imports | Phase 19+Sub1 lesson | C1 audit uses unanchored grep (Pattern 5) |
| Relative imports (`.errors`) | Phase 32 lesson | C1 audit includes Patterns 2 + 3 (likely 0 hits for errors since leaf) |
| Test guard self-trigger | Phase 35 lesson 6 | skip_files in `test_no_infra_errors_references` |
| Empty dir with __pycache__ | Phase 35 lesson 7 | C3 uses `git rm infra/errors.py` (single file); no leftover shell |
| pre-existing failure baseline drift | Phase 34 lesson 4 | T0 captures baseline; G2-G10 verify no regression |
| ruff I001 after sed | Phase 34 lesson 5 | `ruff check --fix` after C2 sed |
| Workspace declaration after uv sync | Phase 34 lesson (N.14 L4) | C1 edits pyproject.toml BEFORE `uv sync` |
| SnapshotError has active consumers | Phase 35 audit pattern | C2 explicitly migrates `character_snapshot.py` + `foreshadow_snapshot.py` |
| `test_phase18_10_stale_imports.py` self-trigger | Phase 35 lesson 6 | C5 updates stale-list; skip_files for that test in C5 guard |

## 10. Open Questions

All resolved in brainstorm §7 (user-approved):
- ✅ Package layout: single-file `lingwen_errors/__init__.py`
- ✅ Scope: errors only (pilot)
- ✅ Migration: full cutover (delete infra/errors.py)
- ✅ Tests: guard minimal
- ✅ Phase 35 handoff: write first as prelude (P1 commit on master — DONE 61a35b56)
- ✅ `SnapshotError` keeps PHASE-COMPAT docstring + stays in errors (2 active consumers)
- ✅ `test_phase18_10_stale_imports.py` stale-list updated C5

## 11. Carryover Closure (post-Phase 36)

| Carryover | Status |
|-----------|--------|
| P3-ARCHDEBT 1/5 (errors → lingwen-errors) | **CLOSED** by Phase 36 |
| P3-ARCHDEBT 4/5 (paths / project_config / logging_config / studio_registry) | OPEN → Phase 37+ |
| Phase 114 prod preview regression (accepted) | unchanged |
| HANDOFF.md `latest_decision_queue` wording (doc-only) | unchanged |
| 5 orphan files housekeeping | unchanged |

## 12. See Also

- Phase 35 handoff: `docs/superpowers/handoffs/2026-09-08-phase-35-world-model-package-handoff.md`
- Phase 35 lessons: `~/.claude/projects/-home-ailearn-projects-LingWen/memory/phase35.md`
- Phase 35 spec: `docs/superpowers/specs/2026-09-08-phase-35-world-model-package-design.md`
- Phase 34 handoff: `docs/superpowers/handoffs/2026-09-08-phase-34-lingwen-got-handoff.md`
- .lingwen/architecture.yml: `id: I0*` invariants block
- Worktree: `.worktrees/phase-36-p3-archdebt-errors/`