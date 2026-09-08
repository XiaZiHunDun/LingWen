# Phase 35 — WORLD-MODEL-PACKAGE migration — handoff

> **Date**: 2026-09-08
> **Branch**: `phase-35-world-model-package`
> **Master HEAD at start**: `220101a8` (v33.0 — Phase 34 LINGWEN-GOT close)
> **Commits**: 9 atomic commits on phase-35-world-model-package
> **Status**: CLOSED ✅ — MERGED to master via ff-merge, master HEAD = `66b39b1b`

## Summary

Phase 35 closes **P2-ARCHDEBT 收官**: migrating the entire World Model engine from `infra/world_model/` (10 modules, 2282 lines) + `infra/subplot/helpers.py` (52 lines) to a dedicated `packages/lingwen-world-model/` package with 37 public symbols. 16 consumer sites migrated across 1 POC + 3 cross-test + 12 in-package tests; 13 world_model test files moved to `packages/lingwen-world-model/tests/`; `infra/world_model/` directory deleted; `subplot_helpers` renamed for package-locality (LingWen-only namespace). **Invariant #50 NEW**: `packages/lingwen-world-model/` is the canonical World Model engine location; `infra.world_model.*` paths are forbidden.

**Net effect**: ~2334 lines of production code relocated to a proper workspace package with its own `pyproject.toml` declaring pydantic + lingwen-shared deps. `infra/world_model/` deleted. 17 regression guards in `tests/test_phase35_world_model.py`.

## Commit chain (9 atomic)

```
b8395749 docs(phase-35): spec + plan for lingwen-world-model package                                          [C0]
cf5bea41 chore(packages): scaffold lingwen-world-model + git mv src files + intra-package imports             [C1+C2]
80a93747 refactor(test): move 13 tests/world_model/*.py → packages/lingwen-world-model/tests/                 [C3]
e782ffe4 refactor(subplot): migrate test_subplot_integration.py subplot_helpers import                       [C4]
231ee27e refactor(poc): migrate run_volume_1.py + fix string literal                                          [C5]
6f226ff5 refactor(tests): migrate 2 consistency ripple checkers                                                [C6]
7fe56d9b fix(workflow-paths): audit + update stale infra.world_model string literals                          [preC7]
7053c2d9 chore(infra): bump to v34.0 + add invariant #50 (lingwen-world-model canonical)                      [C7]
66b39b1b test(phase-35): 17 regression guards + doc sync                                                       [C8]
```

> **Note**: C1+C2 合并是一个 git pipeline 失误（git commit --amend 抓走了 C3 staged renames），commit message 修正后保留了合并状态。Lessons captured in `phase35.md` MEMORY.

## What was deleted (C7)

| File / Dir | Type | Lines | Status at deletion |
|---|---|---|---|
| `infra/world_model/` (entire directory) | World Model engine | 10 modules + ~2282 lines | 0 functional consumers; all 16 migrated to `lingwen_world_model.*` |
| `infra/subplot/helpers.py` | subplot_helpers (3 funcs) | 52 lines | 1 test consumer migrated; renamed for package-locality |
| **Total** | | **~2334 lines** | |

## What was created

| Path | Purpose |
|---|---|
| `packages/lingwen-world-model/pyproject.toml` | Hatchling build backend; deps: pydantic, lingwen-shared |
| `packages/lingwen-world-model/src/lingwen_world_model/` | 10 modules: `__init__.py` + `character_snapshot.py` + `data_structures.py` + `engine.py` + `foreshadow_snapshot.py` + `key_point_graph.py` + `links.py` + `queries.py` + `registry.py` + `snapshot_store.py` + `subplot_helpers.py` (renamed from infra/subplot/helpers.py) |
| `packages/lingwen-world-model/tests/` | 13 test files moved from `tests/`: test_character_snapshot, test_data_structures, test_engine, test_foreshadow_snapshot, test_key_point_graph, test_links, test_queries, test_registry, test_snapshot_store, test_subplot_helpers, test_subplot, test_world_model, test_subplot_helpers_origin (and 2 more) |
| `tests/test_phase35_world_model.py` | 17 regression guards (new) |

## Consumer migration (16 sites)

### Category 1: POC (1 file)
- `infra/poc/run_volume_1.py` (1 site, includes string literal fix)

### Category 2: Cross-test (3 files)
- `infra/subplot/test_subplot_integration.py` (subplot_helpers import)
- `tests/consistency/checkers/` (2 ripple checker files)

### Category 3: In-package tests (12 files)
- 12 test files within `packages/lingwen-world-model/tests/` (rewritten imports)

## Pre-C7 fixup (N.14 lesson 1, 4th+5th occurrences)

C7 deletion was blocked by **filesystem-path string literals** containing `infra.world_model.X` inside 6 file bodies across `packages/lingwen-prompt/` + `tests/prompt_engineering/`. The preC7 fixup commit `7fe56d9b` migrated them to canonical `lingwen_world_model` paths.

**Pattern confirmed**: every shim-deletion phase must audit with 4 grep patterns (Phase 34 lesson + Phase 35 lesson):
1. Literal dotted path imports (`from infra.X.Y import ...`)
2. Relative same-package imports (`from .Y import ...`)
3. Relative parent-package imports (`from ..Y import ...`)
4. Filesystem path string literals: `grep -rn "infra/X/Y" --include="*.py"`

## Validation gates (8/8 GREEN)

| Gate | Suite | Result |
|------|-------|--------|
| G1 | `tests/test_phase35_world_model.py` regression guards | 17/17 |
| G2 | `packages/lingwen-world-model/tests/` | 201/201 |
| G3 | `packages/lingwen-core/tests/` | 68/68 |
| G4 | `packages/lingwen-got/tests/` | 208/208 |
| G5 | `apps/studio_api/tests/` | 82/82 |
| G6 | `tests/subplot/test_subplot_integration.py` | 11/11 |
| G7 | `tests/consistency/checkers/` (2 ripple files) | 22/22 |
| G8 | `tests/prompt_engineering/` | 244/1skip |

**Total**: 853 PASS + 1 skipped = 854 tests; ruff clean.

## Architecture invariants enforced (1 NEW, 50 total)

- **#50 (NEW)** ✅ `packages/lingwen-world-model/` is the canonical World Model engine package. `infra.world_model.*` paths are forbidden (Phase 35+).
  - Enforced by: `tests/test_phase35_world_model.py::test_infra_world_model_directory_deleted` + grep audit gate.
  - Scope: all new World Model engine code must `from lingwen_world_model.X import Y`.

## Doc sync (C8 commit)

| File | Change |
|------|--------|
| `CLAUDE.md` | v34.0 entry (mirror v33.0 format) + I050 invariant row + 架构债 段落更新 (P2-ARCHDEBT → P3-ARCHDEBT) |
| `.lingwen/architecture.yml` | version 33.0 → 34.0; I050 invariant added |
| `collaboration/CURRENT_STATUS.md` | Phase 35 status updated |
| `collaboration/BACKLOG.md` | Phase 35 entry added; P2-ARCHDEBT remaining 0/1 → closed |
| `tests/test_phase35_world_model.py` | NEW — 17 regression guards |

## Carryover closure

| Carryover | Status |
|-----------|--------|
| P2-ARCHDEBT `infra.world_model.*` → `packages/lingwen-world-model/` (v33.0 remaining 1/1) | **CLOSED** by v34.0 (16 consumers migrated, 13 test files moved, infra/world_model/ deleted, I050 enforced) |
| P2-ARCHDEBT `infra.got.*` → `packages/lingwen-got/` | ✅ CLOSED in v33.0 (Phase 34) |
| P2-ARCHDEBT 3 PHASE-COMPAT shims | ✅ CLOSED in v32.0 (Phase 32) |

## Carryover to Phase 36+

| ID | Scope | Estimate |
|----|-------|----------|
| **P3-ARCHDEBT (NEW)** | `infra.{paths, project_config, logging_config, errors, studio_registry}` → packages/ migration | multi-week, 5 modules |
| **HANDOFF.md `latest_decision_queue` wording** | pre-existing carryover | doc-only |
| **Phase 114 prod preview regression** (accepted) | do NOT attempt fix | n/a |
| **5 orphan files housekeeping** | `relationship_network.db` (gitignore) + phase-31 stale docs (归档) + anye-xinbiao + .trae/ (gitignore) + HANDOFF-claude-code.md | doc-only |

**Suggested entry for P3-ARCHDEBT**: `errors` module (380 lines, 14 consumers, leaf with zero internal deps). Phase 36+ will be the next phase.

## Lessons (Phase 35 specific)

### 1. N.14 lesson 1, 8th time — `git mv` + sed pipeline UNSTAGED (CRITICAL)

**Problem**: `git mv file.py new/file.py` stages the RENAME only, not content. After `sed -i 's|old|new|' <moved-files>`, sed changes are in working tree but **UNSTAGED**.

**Phase 35 case**: C2 commit only added `__init__.py` modifications; 6 other src/ files had unstaged sed changes. `git commit --amend` rescued it but caused secondary issue (see lesson 2).

**Fix**:
```bash
# After git mv + sed:
git status --short | grep "^ M"  # should be empty!
git add -- <explicit-path-1> <explicit-path-2> ...  # NOT git add dir/
git status --short | grep "^M"   # confirm staged
git commit
```

### 2. Amend picks up unrelated staged changes (CRITICAL)

**Problem**: `git commit --amend` integrates the WHOLE staging area, not just last-commit delta. If both C2 src/ AND C3 test renames are staged, `--amend` writes BOTH into C2.

**Phase 35 case**: After `git reset --soft HEAD~1` + re-add, the amend picked up unrelated C3 test renames. Result: combined commit `cf5bea41` with C1+C2 message but C1+C2+C3 content. Had to amend AGAIN with corrected message.

**Fix**:
1. After each commit, immediately `git log -1 --stat` to verify scope.
2. Don't `git reset --soft HEAD~1` mid-phase to fix mistakes — finish the commit + add fixup commit.
3. If amend is necessary, `git status --short` to confirm staging area matches intended scope BEFORE amend.

### 3. Specs can lie — verify symbol counts (Phase 34+35, 2 verified occurrences)

**Phase 34 case**: spec said 36 symbols; actual 32.
**Phase 35 case**: spec said 41 symbols; actual 37. Carryover doc said "5 consumer migration"; actual 16.

**Fix (MANDATORY before writing regression tests)**:
```bash
grep -c '^    "' package/__init__.py  # symbol counts
wc -l file.py                          # line counts
grep -rln "from infra.X\." --include="*.py" . | grep -v "infra/X/" | wc -l  # consumer counts
```

### 4. Invariant slot reservation can go stale

**Problem**: Version line narrative claims "I050 NEW invariant" but `invariants:` block never updated. Future phase adding invariant #50 finds slot empty.

**Phase 35 case**: Phase 25 SSE claimed I050 in version line (`.lingwen/architecture.yml:4`); invariants block only had I001-I005 + I048 + I049. I050 was free when Phase 35 claimed it.

**Fix**: `grep -n "id: I0" .lingwen/architecture.yml` to verify actual IDs in block (NOT the version line narrative).

### 5. sed 's|from infra.X.|' misses 'from infra.X import' (no trailing dot)

**Problem**: Trailing-dot anchor doesn't match space separator.

**Fix (2-pass sed)**:
```bash
sed -i 's|from infra\.X |from new_package |g' files   # space variant
sed -i 's|from infra\.X\.|from new_package.|g' files  # dot variant
```

### 6. Test guard files self-trigger audit patterns

**Problem**: `test_phaseNN_*.py` contains the patterns it audits (in docstrings/asserts), causing false-positive failures.

**Fix**: skip_files parameter + historical-references list exclusion. Phase 35 had 6 false-positive failures before excluding guard-file + phase32-shim-test.

### 7. Empty directory with __pycache__/ defeats 'not exists()' guard

**Problem**: `git mv` per-file leaves parent dir shell + `__pycache__/`. `assert not path.exists()` fails.

**Fix**: Use `git rm -r infra/X/` for whole-dir deletion (Phase 34 pattern) OR `rm -rf` after `git mv`.

## Validation gates matrix (Phase 35)

8 gates total, all GREEN: 853 passed + 1 skipped = 854. See `## Validation gates` above.

## Solo workflow closure (T8)

After C8 commit lands:
1. ✅ ff-merge phase-35-world-model-package → master: `git checkout master && git merge --ff-only phase-35-world-model-package`
2. ✅ Push master: `git push origin master`
3. ✅ Remove worktree: `git worktree remove` (Phase 35 worktree cleaned)
4. ✅ Delete branch: `git branch -d phase-35-world-model-package`
5. ✅ Update MEMORY.md Master HEAD to `66b39b1b` (already done in C8)

## See also

- Spec: `docs/superpowers/specs/2026-09-08-phase-35-world-model-package-design.md`
- Plan: `docs/superpowers/plans/2026-09-08-phase-35-world-model-package.md`
- Phase 34 handoff (predecessor): `docs/superpowers/handoffs/2026-09-08-phase-34-lingwen-got-handoff.md`
- Phase 35 lessons detail: `~/.claude/projects/-home-ailearn-projects-LingWen/memory/phase35.md`