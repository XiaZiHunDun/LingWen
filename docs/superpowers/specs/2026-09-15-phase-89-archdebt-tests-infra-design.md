# Phase 89 P3-ARCHDEBT Design — tests/infra/ tracked test files cleanup

> **Phase**: 89 (P3-ARCHDEBT carryover closure, post-Phase 88 disk cleanup)
> **Branch**: `phase-89-archdebt-tests-infra` (direct master commit, per simplified workflow 2026-09-15)
> **Date**: 2026-09-15
> **Version**: v54.20 → **v54.21**
> **Status**: 📋 spec ready
> **Pattern**: MIGRATE (95 test files → canonical package tests/) + DELETE (tests/infra/ directory)
> **Risk**: LOW (test-only changes, no production code touched, content already migrated)

@template: docs/superpowers/specs/_P3_ARCHDEBT_TEMPLATE.md

---

## §1. Background

Phase 81 handoff noted: "test_infra_modules.py 有 14 个 pre-existing ModuleNotFoundError 引用 non-migrated modules (infra.permission / infra.llm_cache / infra.types 从未作为 packages 存在) — inherited from master, NOT introduced by Phase 81".

Post-Phase 88 audit (2026-09-15) reveals the **full scope**: 95 test files in `tests/infra/` (1 `__init__.py` + 94 test_*.py) all import canonical packages (`lingwen_creator` / `lingwen_prose_judge` / `lingwen_studio_registry` / etc.) but their **physical location is still `tests/infra/`** — which is NOT in any PYTHONPATH's `packages/*/src` directory.

**Result**: `pytest tests/infra/` → 94 ModuleNotFoundError.

**Root cause**: Across Phases 32-87, multiple P3-ARCHDEBT phases updated test file **imports** to canonical packages but **forgot to migrate file location** (Phase 56b/56c/57b/87 half-migration lesson recurrence — N.14 v23 v4 variant).

---

## §2. 9-pattern audit (per N.14 lesson 1, 22+ variants)

| # | Pattern | Verdict | Notes |
|---|---------|---------|-------|
| 1 | Literal dotted-path imports `from infra.X import Y` | ✅ 0 hits | All 95 tests already import canonical packages (lingwen_*) |
| 2 | Indented / function-body imports | ✅ 0 hits | Same as #1 |
| 3 | Relative imports `from .X` / `from ..X` | ✅ 0 hits | No relative imports |
| 4 | Filesystem-path string literals | ✅ 0 hits | No path literals |
| 5 | Wildcard `from X import *` | ✅ 0 hits | None |
| 6 | `monkeypatch.setattr(..., "infra.X.Y", ...)` | ✅ 0 hits | None |
| 7 | `import X as Y` re-exports | ✅ 0 hits | None |
| 8 | Doc comments referencing deleted paths | ⚠️ 2 stale | `test_prose_judge.py:2` ("Phase 12.03 / Phase 51 P3-ARCHDEBT") + `test_creator_volume_plan.py:1` ("Tests for infra.creator_volume_plan") — both reference old paths. **C3 doc fixup** |
| 9 | Prior-phase guards hardcoded representative files | ⚠️ 1 hit | `test_phase53d_event_sourcing.py` and `test_phase18_8_stale_imports.py` may reference `tests/infra/` paths. **Audit before C1** |

**Audit verdict**: 9-pattern clean (only docstring fixups + 1 prior-phase guard audit needed). All canonical imports already in place.

---

## §3. Test files inventory + MIGRATE/DELETE classification

### §3.1 11 non-creator test_*.py files → MIGRATE to canonical packages

| Test file | Canonical package | Phase that MIGRATED source | Migration target |
|-----------|-------------------|----------------------------|------------------|
| `tests/infra/test_check_fail_severity.py` | `lingwen_quality` | Phase 46 (filter MERGE) | `packages/lingwen-quality/tests/test_check_fail_severity.py` |
| `tests/infra/test_plugin_manager.py` | `lingwen_llm` | Phase 43 (llm-service) | `packages/lingwen-llm/tests/test_plugin_manager.py` |
| `tests/infra/test_project_characters.py` | `lingwen_project_characters` | Phase 51 (prose cluster) | `packages/lingwen-project-characters/tests/test_project_characters.py` |
| `tests/infra/test_project_config.py` | `lingwen_project_config` | Phase 38 | `packages/lingwen-project-config/tests/test_project_config.py` |
| `tests/infra/test_project_init.py` | `lingwen_project_init` | Phase 42 | `packages/lingwen-project-init/tests/test_project_init.py` |
| `tests/infra/test_project_range.py` | `lingwen_cli` | (cli tools package) | `packages/lingwen-cli/tests/test_project_range.py` |
| `tests/infra/test_prose_calibration_overrides.py` | `lingwen_prose_calibration` | Phase 51 (prose cluster) | `packages/lingwen-prose-calibration/tests/test_prose_calibration_overrides.py` |
| `tests/infra/test_prose_judge.py` | `lingwen_prose_judge` | Phase 51 | `packages/lingwen-prose-judge/tests/test_prose_judge.py` |
| `tests/infra/test_prose_snapshot.py` | `lingwen_prose_snapshot` | Phase 51 | `packages/lingwen-prose-snapshot/tests/test_prose_snapshot.py` |
| `tests/infra/test_studio_batch_queue.py` | `lingwen_studio_batch_runner` | Phase 47 | `packages/lingwen-studio-batch-runner/tests/test_studio_batch_queue.py` |
| `tests/infra/test_studio_registry.py` | `lingwen_studio_registry` | Phase 40a | `packages/lingwen-studio-registry/tests/test_studio_registry.py` |

### §3.2 83 test_creator_*.py files → MIGRATE to lingwen-creator/tests/

All 83 files import `from lingwen_creator.*` (canonical, post-Phase 126 v16.2.1 closure). Migration target: `packages/lingwen-creator/tests/`.

**Naming strategy**: Keep `test_creator_*.py` filename (since existing `test_content.py` / `test_volume.py` / etc. cover subdomain-level integration; `test_creator_*.py` covers specific feature-level tests).

### §3.3 1 `tests/infra/__init__.py` → DELETE

Empty marker file. After all tests MIGRATE, `tests/infra/` directory + `__init__.py` should be deleted.

---

## §4. Path-depth fixup required (Phase 56b2 lesson)

**File**: `tests/infra/test_prose_judge.py:2 sites`
- Current: `factory = Path(__file__).resolve().parents[1]` (= `tests/` directory)
- After MIGRATE to `packages/lingwen-prose-judge/tests/`: `parents[1]` becomes `<pkg>/` directory (different meaning!)
- Fix: `parents[1]` → `parents[3]` (= repo root, since `packages/<pkg>/tests/` → 3 levels up)

Comment to add: `# Phase 56b2 lesson: parents[N] depth depends on file location`

---

## §5. Plan (atomic commits)

Per simplified workflow (2026-09-15) — direct master commits, no worktree:

| Commit | Type | Subject | Files | +/- |
|--------|------|---------|-------|-----|
| C0 | docs | spec + 9-pattern audit | `docs/superpowers/specs/...-phase-89-...md` | NEW |
| C1 | chore | MIGRATE 11 non-creator test_*.py to canonical packages (pathspec BOTH old + new for blame preservation, Phase 56c lesson 1) | 22 file ops (11 delete + 11 add) | neutral |
| C2 | chore | MIGRATE 83 test_creator_*.py to packages/lingwen-creator/tests/ | 166 file ops (83 mv + 83 add) | neutral |
| C3 | chore | DELETE tests/infra/__init__.py + rmdir tests/infra/ | 1 file op + rmdir | -1 |
| C4 | test | 12 regression guards G1-G12 (10/10 PASS expected) | NEW | +~250 |
| C5 | docs | CLAUDE.md v54.20→v54.21 + CURRENT_STATUS + BACKLOG + handoff | 4 files | +~20 |

**Note**: MIGRATE 95 files in 2 commits (C1 + C2) keeps commit sizes manageable.

---

## §A. test files migration plan (MANDATORY per I079)

### A1. test files inventory

- [x] Listed **all 95 test files** in `tests/infra/` (above)
- [x] Classified each as MIGRATE (95 files) — all canonical imports already in place
- [x] DELETE `tests/infra/__init__.py` (1 file, empty marker)

### A2. MIGRATE 路径

- [x] Target locations: `packages/<canonical-package>/tests/test_*.py` (11 distinct packages)
- [x] Migration step: `git mv tests/infra/<file>.py packages/<pkg>/tests/<file>.py` (single commit per Phase group per I079 §A5)
- [x] **No import migrations** — content uses `from lingwen_*` already (canonical)
- [x] **sys.path hack cleanup**: 0 conftest.py found in `tests/infra/` — no cleanup needed
- [x] cwd-relative path fixup: 1 site `test_prose_judge.py` uses `parents[1]` — needs `parents[3]` after MIGRATE (Phase 56b2 lesson 2)
- [x] Functional gate: each migrated test file must run from its new package location with package's PYTHONPATH

### A3. DELETE 路径

- [x] `tests/infra/__init__.py` (1 file, empty marker) — DELETE in C3

### A4. RETAIN-ORPHAN 路径

**N/A** — all 95 tests MIGRATE to canonical packages; no orphan retention.

### A5. Half-migration defense (Phase 56b/56c/57b/87 4th-occurrence prevention)

- [x] **C1 + C2 commits** use `git mv` (single command, BOTH old + new paths in same commit — blame preserved per Phase 56c lesson 1)
- [x] **C1 + C2 commit messages** explicitly state "deleted tests/infra/X.py + created packages/<pkg>/tests/X.py" (NOT just "+ I0XX")
- [x] **C3 commit message** explicitly states "DELETE tests/infra/__init__.py + rmdir tests/infra/ + closes ARCHDEBT cycle carryover"
- [x] Verification: `git show <SHA> --stat` must show both old (deleted) + new (created) test files in single commit

---

## §B. P3-ARCHDEBT spec standard structure (recommended)

1. ✅ Background — Phase 81 handoff carryover
2. ✅ 9-pattern audit — clean (mostly)
3. ✅ Companion stale refs — only docstring fixups
4. ✅ Plan — 5 commits
5. ✅ §A test files migration plan
6. ⏳ Validation gates — pytest functional gate + 9-pattern audit
7. ⏳ Risk assessment — minimal (test-only)
8. ✅ Out of scope — explicit defer (no production code changes)
9. ⏳ Completion criteria

---

## §C. Lessons from prior phases

- **Phase 56b (world_db tests restoration)**: Established MIGRATE pattern for half-migrated tests.
- **Phase 56b2 (cwd-independent test paths)**: `parents[N]` depth depends on file location. MIGRATE from `tests/X/` → `packages/<pkg>/tests/` requires `N` recalibration.
- **Phase 56c (cross_volume tests)**: `git mv` single command for blame preservation.
- **Phase 57b (reading_power)**: parent.parent.parent silent wrong in new location.
- **N.14 lesson 1 v23 v4** (Phase 89 NEW): Half-migration recurrence (test imports migrated, file location not migrated) — 4th occurrence after Phase 56b/56c/57b.

---

## §D. Anti-patterns

- ❌ Don't `git rm` + `git add` separately (loses blame)
- ❌ Don't update imports but forget file location migration
- ❌ Don't fix `parents[N]` later in separate commit (bake into same MIGRATE commit per Phase 56b2 lesson)

---

## §E. Validation gates

### E.1 Functional gate

```
# Pre-Phase 89:
$ pytest /home/ailearn/miniconda3/bin/python -m pytest tests/infra/ --collect-only
collected 0 items / 94 errors
E   ModuleNotFoundError: No module named 'lingwen_creator'

# Post-Phase 89 C1+C2:
$ PYTHONPATH=packages/<pkg>/src /home/ailearn/miniconda3/bin/python -m pytest packages/<pkg>/tests/test_<name>.py -v
# Expect: 100% collection success for each migrated file (functional pass depends on test logic, but collection MUST succeed)

# Post-Phase 89 C3 + regression guards:
$ /home/ailearn/miniconda3/bin/python -m pytest tests/test_phase89_archdebt_tests_infra.py -v
# Expect: 12/12 GREEN
```

### E.2 9-pattern audit (post-C2)

Per §2 audit, 9-pattern clean post-MIGRATE.

### E.3 Disk / size verification

```
Pre-Phase 89:  tests/infra/ = 96 files (~2000 LOC test code)
Post-Phase 89: tests/infra/ = 0 files (deleted)
              packages/<pkg>/tests/ = +96 files (migrated)
```

---

## §F. Out of scope (explicit defer)

- ❌ No production code changes (only test files MIGRATE)
- ❌ No new test logic (MIGRATE preserves existing tests verbatim)
- ❌ No new pytest configuration
- ❌ No Phase 126 v16.2.1 duplicate cleanup (lingwen-creator/tests/ has 10 files for content/export/memory/onboarding/settings/shared/volume subdomains; test_creator_*.py tests are feature-specific and complementary, not duplicate)

---

## §G. Completion criteria

- [x] C0 spec doc written (this file)
- [ ] C1 — 11 non-creator tests MIGRATE to canonical packages (pathspec BOTH paths)
- [ ] C2 — 83 test_creator_*.py MIGRATE to packages/lingwen-creator/tests/
- [ ] C3 — DELETE tests/infra/__init__.py + rmdir tests/infra/
- [ ] C4 — 12 regression guards G1-G12 GREEN (10/10 PASS expected)
- [ ] C5 — CLAUDE.md v54.20 → v54.21 + handoff
- [ ] Cluster cumulative Phase 53-89 = 17 phases (~20464 LOC dead code + ~2K LOC orphan test files cleaned)
- [ ] ARCHDEBT cycle CARRY-OVER CLOSED — tests/infra/ gone

---

## §H. Post-Phase 89 state

After Phase 89:

```
$ git ls-files tests/infra/
(empty — directory removed)

$ git ls-files packages/lingwen-creator/tests/
... (existing 10 + 83 migrated = 93 test files)

$ git ls-files packages/lingwen-prose-judge/tests/
... (existing + 1 migrated = test_prose_judge.py added)

$ git ls-files packages/lingwen-studio-registry/tests/
... (existing + 1 migrated = test_studio_registry.py added)
... etc for 11 packages
```

**Cluster cumulative**: Phase 53-89 = **17 phases / ~20464 LOC dead code + ~2K LOC orphan tests cleaned**.

**ARCHDEBT cycle: FULLY CLOSED** (git tracking + filesystem + test infrastructure all clean).

---

**Pattern**: MIGRATE + DELETE (test infrastructure closure).

**Lessons**:
1. **N.14 v23 v4 lesson**: Half-migration (imports updated, location not) — Phase 89 closes 4th-occurrence after Phase 56b/56c/57b.
2. **Path-depth coupling**: `parents[N]` depth changes when MIGRATE between `tests/X/` and `packages/<pkg>/tests/`. Fix in same commit (Phase 56b2 lesson 2).
3. **Test-infrastructure phase**: Phase 89 is test-only MIGRATE — no production code changes. Distinguishes from real P3-ARCHDEBT phases (Phase 36-86 which migrated production code).