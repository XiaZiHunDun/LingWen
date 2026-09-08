# Phase 36 — P3-ARCHDEBT (errors pilot) — handoff

> **Date**: 2026-09-08
> **Branch**: `phase-36-p3-archdebt-errors` (deleted after ff-merge)
> **Master HEAD at start**: `61a35b56` (v34.0 — Phase 35 WORLD-MODEL-PACKAGE close)
> **Commits**: 7 atomic commits on phase-36-p3-archdebt-errors (1 spec + 1 plan + 5 implementation)
> **Status**: CLOSED ✅ — MERGED to master via ff-merge, master HEAD = `3c008873`

## Summary

Phase 36 opens **P3-ARCHDEBT** (new architectural debt category covering infrastructure utility files that have grown into first-class domain modules) with a **pilot** migration of `infra/errors.py` (380 lines, 23 `__all__` symbols) → `packages/lingwen-errors/`. 14 consumer sites migrated across 4 packages + 8 intra-infra files; full cutover (no PHASE-COMPAT shim); `infra/errors.py` deleted; **invariant #51 NEW** enforced. This is a **leaf package** with zero workspace deps — only stdlib (`json`, `traceback`, `dataclasses`, `datetime`, `typing`). 6 regression guards in `tests/test_phase36_lingwen_errors.py`.

**Net effect**: 380 lines of production code relocated to a proper workspace package with its own `pyproject.toml`. `infra/errors.py` deleted (full cutover). SnapshotError (with 2 active consumers in lingwen-world-model) re-exported through `lingwen_errors` package; PHASE-COMPAT docstring now stale but class preserved per Phase 36 design.

**Pilot pattern validated**: 1/5 P3-ARCHDEBT modules closed. Phase 37+ will tackle the remaining 4 (`paths`, `project_config`, `logging_config`, `studio_registry`) with the validated pattern.

## Commit chain (7 atomic)

```
8401ff70 docs(phase-36): spec for lingwen-errors package (P3-ARCHDEBT pilot)                                  [C0]
91735814 docs(phase-36): implementation plan for lingwen-errors (P3-ARCHDEBT pilot)                          [C0b plan]
23110bc1 chore(packages): scaffold lingwen-errors (Phase 36 P3-ARCHDEBT pilot)                                [C1]
6e3dd2cd refactor(consumers): migrate 14 errors consumers to lingwen_errors (Phase 36)                        [C2]
e4f60d30 chore(infra): delete infra/errors.py (Phase 36 P3-ARCHDEBT pilot)                                    [C3]
23e4c0c1 chore(infra): bump v35.0 + invariant #51 (lingwen-errors canonical) [Phase 36]                      [C4]
3c008873 test(phase-36): regression guards + doc sync (v35.0 P3-ARCHDEBT pilot)                                [C5]
```

> **Note**: P1 (Phase 35 handoff doc) is on master at `61a35b56`, NOT on the branch. Branch carries 7 commits: C0 + C0b + C1-C5.

## What was deleted (C3)

| File | Type | Lines | Status at deletion |
|------|------|-------|---------------------|
| `infra/errors.py` | Errors library (BaseError family + 14 subclasses + 7 factories) | 380 lines, 23 `__all__` symbols | 0 functional consumers; all 14 migrated to `lingwen_errors.*` |
| **Total** | | **380 lines** | |

`git mv infra/errors.py packages/lingwen-errors/src/lingwen_errors/__init__.py` was the C1+C3 path; the file is **literally the same bytes** (1:1 mapping preserved per spec §3 "No internal restructuring").

## What was created

| Path | Purpose |
|------|---------|
| `packages/lingwen-errors/pyproject.toml` | Hatchling build; `requires-python>=3.11`; zero workspace deps (leaf) |
| `packages/lingwen-errors/src/lingwen_errors/__init__.py` | 380 lines (1:1 from `infra/errors.py`); 23 `__all__` symbols |
| `tests/test_phase36_lingwen_errors.py` | 6 regression guards (new) |

**`__all__` count: 23** (verified via `awk '/^__all__ = \[/, /^\]/' infra/errors.py | grep -c '"'`):
- 8 utility/factory: `BaseError, create, is_instance, wrap, unwrap, from_dict, from_json, capture_stack_trace`
- 15 subclasses: `RetryableError, FatalError, ValidationError, NotFoundError, ConflictError, AuthenticationError, AuthorizationError, RateLimitError, NetworkError, TimeoutError, ServiceUnavailableError, DatabaseError, ConfigurationError, NotImplementedError, SnapshotError`

## Consumer migration (14 sites)

### Category 1: Cross-package (6 files, 4 packages)

| File | Symbols used |
|------|--------------|
| `packages/lingwen-quality/src/lingwen_quality/consistency/checker_feedback.py` | `BaseError` family |
| `packages/lingwen-quality/src/lingwen_quality/consistency/creative_whitelist.py` | `BaseError` family |
| `packages/lingwen-world-model/src/lingwen_world_model/character_snapshot.py` | `SnapshotError` |
| `packages/lingwen-world-model/src/lingwen_world_model/foreshadow_snapshot.py` | `SnapshotError` |
| `packages/lingwen-pipeline/src/lingwen_pipeline/state_machine.py` | `BaseError` family |
| `packages/lingwen-llm/src/lingwen_llm/providers/base.py` | `BaseError` family |

### Category 2: Intra-infra (8 files)

| File | Notes |
|------|-------|
| `infra/__init__.py` | re-export list (3 lines changed) |
| `infra/health.py` | |
| `infra/llm_cache.py` | |
| `infra/permission.py` | |
| `infra/schema.py` | 4-line change (multi-import) |
| `infra/tool.py` | |
| `infra/types.py` | |
| `infra/util/retry.py` | |

**4-grep audit matrix applied (Phase 32+34+35 lessons)**:
1. Literal dotted path imports: 14 hits pre-migration → 0 hits post-migration
2. Relative same-package imports: 0 (lingwen-errors is single-file package)
3. Relative parent-package imports: 0 (leaf)
4. Filesystem path string literals: 0 (no `infra/errors` string in any Path() call)

Verified: `grep infra.errors` returns 0 hits after migration.

## Validation gates (8/8 GREEN)

| Gate | Suite | Result |
|------|-------|--------|
| G1 | `tests/test_phase36_lingwen_errors.py` regression guards | 6/6 |
| G2 | `packages/lingwen-world-model/tests/` | 201/201 |
| G3 | `packages/lingwen-core/tests/` | 68/68 |
| G4 | `packages/lingwen-got/tests/` | 208/208 |
| G5 | `apps/studio_api/tests/` | 82/82 |
| G6 | `packages/lingwen-pipeline/tests/` | preserved |
| G7 | `packages/lingwen-llm/tests/` | preserved |
| G8 | `tests/test_phase18_10_stale_imports.py` | updated + passing |

**Total**: 575 PASS + 1 xfail baseline preserved; ruff clean on modified files.

## Architecture invariants enforced (1 NEW, 51 total)

- **#51 (NEW)** ✅ `packages/lingwen-errors/` is the canonical errors library package. `infra.errors.*` paths are forbidden (Phase 36+).
  - Enforced by: `tests/test_phase36_lingwen_errors.py::test_infra_errors_deleted` + `test_no_infra_errors_references` (grep audit).
  - Scope: all new error class code must `from lingwen_errors.X import Y`.

## Doc sync (C5 commit)

| File | Change |
|------|--------|
| `CLAUDE.md` | v35.0 entry + I051 invariant row + 架构债 段落更新 (P3-ARCHDEBT 1/5 → closed) |
| `.lingwen/architecture.yml` | version 34.0 → 35.0; I051 invariant added |
| `collaboration/CURRENT_STATUS.md` | Phase 36 status updated |
| `collaboration/BACKLOG.md` | Phase 36 entry; P3-ARCHDEBT 1/5 (errors) → closed |
| `tests/test_phase18_10_stale_imports.py` | line 19: `"infra.errors"` → `"lingwen_errors"` |
| `tests/test_phase36_lingwen_errors.py` | NEW — 6 regression guards |

## Carryover closure

| Carryover | Status |
|-----------|--------|
| P3-ARCHDEBT `infra.errors.*` → `packages/lingwen-errors/` (v34.0 carryover 1/5) | **CLOSED** by v35.0 (14 consumers migrated, infra/errors.py deleted, I051 enforced) |
| P2-ARCHDEBT `infra.world_model.*` → `packages/lingwen-world-model/` | ✅ CLOSED in v34.0 (Phase 35) |
| P2-ARCHDEBT `infra.got.*` → `packages/lingwen-got/` | ✅ CLOSED in v33.0 (Phase 34) |

## Carryover to Phase 37+

| ID | Scope | Estimate | Notes |
|----|-------|----------|-------|
| **P3-ARCHDEBT 4/5** | `infra.{paths, project_config, logging_config, studio_registry}` → packages/ migration | multi-week | Pilot pattern validated; same shape (sed + workspace member + invariant + guards) |
| **HANDOFF.md `latest_decision_queue` wording** | pre-existing carryover | doc-only | (not Phase 36 introduced) |
| **Phase 114 prod preview regression** (accepted) | do NOT attempt fix | n/a | (not Phase 36 introduced) |
| **5 orphan files housekeeping** | `relationship_network.db` (gitignore) + phase-31 stale docs (归档) + anye-xinbiao + .trae/ (gitignore) + HANDOFF-claude-code.md | doc-only | (not Phase 36 introduced) |

**Suggested order for P3-ARCHDEBT Phase 37+**: `paths` (next smallest leaf) → `project_config` (single-config) → `logging_config` (cross-cuts many) → `studio_registry` (largest, last).

## Lessons (Phase 36 specific)

### 1. Specs can lie — extended scope drift (Phase 34+35+36, 3 verified occurrences)

**Problem**: Phase 36 spec drift in **3 different places**, each requiring in-flight correction:

| Task | Spec drift | Detection | Fix |
|------|------------|-----------|-----|
| T2 | `test_foreshadow_snapshot.py` referenced as a fixture that doesn't exist | Spec review | Drop the reference, use real fixture name |
| T4 | `head -1` pointed to wrong line in `tests/test_phase18_10_stale_imports.py` (line 19 vs actual line in stale-list array) | Spec review | Re-grep to find actual stale-list location |
| T4 | `test_infra_errors_module_deleted` vs canonical `test_infra_errors_deleted` (Phase 35-style naming) | Spec review | Align with `test_infra_X_<verb>` pattern from Phase 35 |
| T5 | `test_snapshot_error_migrated` used unanchored grep `lingwen_errors.SnapshotError` which matched Python code in test bodies too | Self-trigger | Tighten pattern to `^from lingwen_errors import` |
| T5 | `_is_skipped()` path comparison used `Path("tests/...")` absolute but grep returned relative paths | Self-trigger | Use `REPO_ROOT / rel_path` for comparison |

**Fix (MANDATORY before writing regression tests)**:
```bash
# Verify spec-asserted counts/locations BEFORE writing the regression test
grep -c '^    "' packages/lingwen-errors/src/lingwen_errors/__init__.py  # 23 expected
grep -n "infra.errors" tests/test_phase18_10_stale_imports.py           # verify exact line
ls packages/lingwen-world-model/tests/test_foreshadow_snapshot.py       # confirm exists
```

### 2. ruff --fix out-of-scope drift (Phase 36)

**Problem**: After `ruff check --fix` during C2 migration, **13 unrelated files** in `packages/lingwen-world-model/tests/` + `infra/subplot/__init__.py` picked up whitespace drift (single-line deletions/insertions of trailing whitespace).

**Why it happens**: ruff --fix can rewrite files that the migrator didn't intend to touch (e.g. pre-existing whitespace in test imports). These changes end up **unstaged** because the migrator used `git add -p` style selective staging.

**Fix (MANDATORY after any `ruff check --fix`)**:
```bash
git status --short | grep "^ M"  # list unstaged changes
# If any are out-of-scope, either:
#   (a) `git checkout -- <file>` to discard (preferred)
#   (b) add to a dedicated "lint cleanup" follow-up commit
# Then verify:
git status --short  # should be clean or only intended changes
```

**Phase 36 case**: 13 whitespace files appeared unstaged in the worktree after ff-merge. Confirmed drift was `1 line -/1 line +` whitespace only (no semantic change). Force-removed worktree without committing drift (per design — out-of-scope for Phase 36).

### 3. T4 follow-up fixes bundled into T5 (Phase 35 lesson 2 extension)

**Pattern**: When T4 (invariant) leaves spec-quality issues (e.g. invariant #51 references wrong test name in scope docstring), bundle the fix into T5 (guards + doc sync) rather than amending T4.

**Phase 36 application**: T5 commit `3c008873` included:
- `.lingwen/architecture.yml` I051 scope: `test_infra_errors_module_deleted` → `test_infra_errors_deleted` (per Phase 35 naming convention)
- `CLAUDE.md` v35.0 entry: "6 packages (wrong)" → "4 packages (lingwen-quality/world-model/pipeline/llm)" — the spec said 4 packages but doc listed 6, conflating intra-infra files with package consumers

**Why not amend**: Per Phase 35 lesson 2 ("amend picks up unrelated staged changes"), amending mid-phase is risky when other files are already staged. A follow-up commit in T5 is cleaner and self-explanatory.

### 4. _is_skipped() path comparison robustness

**Problem**: `SKIP_FILES = [Path("tests/test_phase36_lingwen_errors.py")]` is **absolute** (relative to CWD), but `grep -l` returns **relative-to-REPO_ROOT** paths. Direct `file in SKIP_FILES` comparison always fails.

**Fix**:
```python
def _is_skipped(rel_path: Path) -> bool:
    abs_path = REPO_ROOT / rel_path
    return abs_path in SKIP_FILES  # compare both as absolute
```

**Generalized rule**: When building skip-list exclusion in regression guards, **always normalize both sides** (relative-to-repo-root) before comparing. The test guard file self-triggers because the patterns it audits are present in its own docstrings/asserts.

### 5. Empty-directory guard pattern (Phase 35 lesson 7 confirmed)

**Phase 36 application**: `infra/errors.py` was a single file, not a directory. No `__pycache__/errors.cpython-313.pyc` shell leftover (verified via `git status` before C3 delete).

**Lesson re-confirmed**: When deleting a single file (not a directory), `git rm infra/errors.py` is clean. The Phase 35 "empty dir with `__pycache__/` defeats `not path.exists()` guard" lesson applies only to dir-level deletions.

## Validation gates matrix (Phase 36)

8 gates total, all GREEN: 575 PASS + 1 xfail baseline preserved, ruff clean on modified files. See `## Validation gates` above.

## Solo workflow closure (T6 — this task)

After C5 commit `3c008873` lands:
1. ✅ Verified all 7 commits on `phase-36-p3-archdebt-errors` (8401ff70..3c008873)
2. ✅ Pushed branch: `git push -u origin phase-36-p3-archdebt-errors` (remote push succeeded, not local-only)
3. ✅ ff-merge to master: `git checkout master && git merge --ff-only phase-36-p3-archdebt-errors` (no conflicts)
4. ✅ Pushed master: `git push origin master` (`66b39b1b..3c008873`)
5. ✅ Removed worktree (force — 13 ruff --fix whitespace drift files were unstaged per Phase 36 lesson 2): `git worktree remove --force .worktrees/phase-36-p3-archdebt-errors`
6. ✅ Deleted local + remote branch: `git branch -d phase-36-p3-archdebt-errors && git push origin --delete phase-36-p3-archdebt-errors`
7. ✅ Wrote this handoff doc (committed separately)

**Master HEAD after T6**: `3c008873` (C5 guards + doc sync)

## See also

- Spec: `docs/superpowers/specs/2026-09-08-phase-36-p3-archdebt-errors-design.md`
- Plan: `docs/superpowers/plans/2026-09-08-phase-36-p3-archdebt-errors.md`
- Phase 35 handoff (predecessor): `docs/superpowers/handoffs/2026-09-08-phase-35-world-model-package-handoff.md`
- Phase 34 handoff: `docs/superpowers/handoffs/2026-09-08-phase-34-lingwen-got-handoff.md`
- Phase 35 lessons: `~/.claude/projects/-home-ailearn-projects-LingWen/memory/phase35.md`