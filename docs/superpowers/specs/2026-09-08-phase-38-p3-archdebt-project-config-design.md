# Phase 38 — P3-ARCHDEBT (project_config) — design

> **Date**: 2026-09-08
> **Branch**: `phase-38-p3-archdebt-project-config` (worktree at `.claude/worktrees/phase-38-p3-archdebt-project-config`)
> **Master HEAD at start**: `e65d7784` (v36.0 — Phase 37 P3-ARCHDEBT paths + 6 phase37 guards)
> **Scope**: Single-module migration for **P3-ARCHDEBT** item 3/5 — migrate `infra/project_config.py` (171 lines, 2 top-level public symbols) to `packages/lingwen-project-config/`
> **Carryover closes**: 3/5 of P3-ARCHDEBT (logging_config + studio_registry remain for Phase 39+)

## 1. Summary

Phase 38 continues **P3-ARCHDEBT** (the architectural debt category opened by Phase 36 pilot, extended by Phase 37). This phase migrates `infra/project_config.py` — a small, **non-leaf** module with **27 consumer files** (2 apps + 16 packages + 4 intra-infra + 5 tests) and 2 top-level public symbols.

**Why project_config third** (and not fourth/fifth):

- **Paths dependency NOW resolved** (Phase 37 closed `infra.paths.*` → `lingwen_paths`). `infra/project_config.py:11` already imports `from lingwen_paths import ProjectPaths` — Phase 37 was a hard prerequisite.
- **Smaller fan-out than studio_registry** (27 vs 50 consumers).
- **Has lingwen-shared dep too** (`infra/project_config.py:12-16` imports `normalize_creation_mode` + `normalize_quality_profile` + `CREATION_MODE_STUDIO` from `lingwen_shared.mode`) — `lingwen_shared` is also workspace-canonical (v16.1+), so Phase 38 exercises the **multi-dep package** pattern (lingwen-errors and lingwen-paths were both leaves; project_config is the first P3 with non-trivial workspace deps).
- **Audit matrix clean for 3 of 4 patterns** (0 relative imports + 0 filesystem path string literals + 0 indented TYPE_CHECKING blocks) — only 1 complication: **3 function-body imports** (Phase 37 lesson applies; uses `^\s*from` regex with `re.MULTILINE`).
- **1 wildcard re-export**: `infra/project/__init__.py:4` does `from infra.project_config import *` (transitive `infra.project.*` namespace). Cleanup required after deletion.

**Pattern inheritance**: Phases 36 + 37 fully established the P3 cutover pattern. Phase 38 replicates it 1:1 with the only deltas being:

- **Non-leaf package** (2 internal deps: `lingwen-paths` + `lingwen-shared`) — first multi-dep P3 package
- **27 consumers** (smaller than paths 86, larger than errors 14) — mid-scale
- **3 function-body imports** (N.14 lesson 1, 8th occurrence) — explicit handling
- **1 wildcard re-export** (`infra/project/__init__.py:4`) — wildcard deletion in same commit as source deletion
- **Version bump**: v36.0 → **v37.0** (next sequential)
- **Invariant**: I052 → **I053 NEW**

## 2. Goals

- Move `infra/project_config.py` (171 lines) → `packages/lingwen-project-config/src/lingwen_project_config/__init__.py` with **1:1 file content mapping** (no internal restructuring)
- Migrate all 27 consumer files to `from lingwen_project_config import X` (handling 3 function-body imports + 1 wildcard re-export)
- Delete `infra/project_config.py` (full cutover — no PHASE-COMPAT shim)
- Remove wildcard `from infra.project_config import *` from `infra/project/__init__.py:4`
- Add `packages/lingwen-project-config` to `[tool.uv.workspace] members` + `[tool.uv.sources]`
- Add **invariant #53 NEW**: `packages/lingwen-project-config/` is canonical; `infra.project_config.*` forbidden
- Bump `.lingwen/architecture.yml` version 36.0 → 37.0 + root `pyproject.toml` 9.11.0 → 9.12.0
- Add regression guards in `tests/test_phase38_lingwen_project_config.py` (6 guards, no functional tests)
- Update CLAUDE.md v37.0 entry + handoff doc

## 3. Non-Goals (Out of Scope)

- **No internal restructuring** of project_config.py — single-file package preserves 1:1 mapping
- **No new functional test suite** — guard-minimal only; coverage expansion deferred to Phase 39+
- **No migration of other P3 modules** — logging_config (8) + studio_registry (50) deferred
- **No renaming of any class/function** — names stay byte-for-byte identical (`ProjectConfig`, `update_project_creation_mode`, private helpers `_env_int`/`_env_bool`)
- **No PHASE-COMPAT shim** — full cutover (delete `infra/project_config.py`)
- **No changes to `infra/project_init.py` / `infra/project_characters.py`** — separate modules; they consume `project_config` but their own migration is a separate Phase
- **No `__all__` introduction** — `infra/project_config.py` has no `__all__`; preserve 1:1 mapping means `lingwen_project_config` also has no `__all__`. Guard test verifies absence.

## 4. Architecture & Design

### 4.1 Package Layout

```
packages/lingwen-project-config/                              # NEW workspace package (non-leaf)
├── pyproject.toml                                            # Hatchling build; requires-python>=3.11;
│                                                              # deps: lingwen-paths, lingwen-shared
└── src/lingwen_project_config/
    └── __init__.py                                           # 171 lines (1:1 from infra/project_config.py), NO __all__
```

**Single-file package**: `lingwen_project_config/__init__.py` contains all 171 lines. No submodule split. Matches `lingwen-paths` (Phase 37) and `lingwen-errors` (Phase 36) where single-file modules became single-file packages.

**No `__all__`**: source file does not define `__all__`. All 2 top-level public symbols (`ProjectConfig`, `update_project_creation_mode`) are exported by default. Private helpers (`_env_int`, `_env_bool`, `_DEFAULT_CONFIG_REL`, `_TRUTHY`) are also exported by Python default but never imported by name in any consumer (verified via grep).

### 4.2 Naming Choice: `lingwen-project-config` (NOT `lingwen-config`)

**Decision**: package = `lingwen-project-config`, import = `lingwen_project_config`.

**Rationale**:
- **Consistency with prior P3 phases**: `infra.world_model` → `lingwen-world-model` (hyphenated multi-word preserved). `infra.project_config` → `lingwen-project-config` follows the same pattern.
- **Avoids ambiguity**: `lingwen-config` is generic; the module is specifically **project-level production gates** (per `infra/project_config.py:1` docstring "Project-level production gates for LingWen Studio"). `project_config` name carries semantic meaning.
- **Handoff doc reference was a stale suggestion**: `docs/superpowers/handoffs/2026-09-08-phase-37-p3-archdebt-paths-handoff.md:164` listed `packages/lingwen-config/` as suggestion, but Phase 37 handoff is for paths not project_config — that suggestion was never ratified. Phase 38 picks the consistent naming.

### 4.3 Dependency Direction

`lingwen_project_config` depends on 2 workspace packages:

| Dep | Phase | Status |
|-----|-------|--------|
| `lingwen-paths` | Phase 37 (I052) | ✅ Canonical |
| `lingwen-shared` | v16.1 (T5) | ✅ Canonical |

`lingwen_project_config` is consumed by **4 infra modules** (intra-infra fan-out):
- `infra/full_check_report.py` (function-body import, line 170)
- `infra/project_characters.py` (function-body import, line 68)
- `infra/project/__init__.py` (wildcard import, line 4 — DELETE)
- `infra/studio_registry.py` (module-level import, line 15)

These 4 intra-infra consumers are NOT migrated in Phase 38 (Phase 39 logging_config + Phase 40 studio_registry will touch studio_registry; project_characters + full_check_report stay intra-infra). After Phase 38 C3 deletes `infra/project_config.py`, these 4 files MUST be migrated to `lingwen_project_config` in C2 — same atomic commit.

### 4.4 Audit Matrix Findings (N.14 Lesson 1, 8th time applied)

Full 4-pattern consumer audit (applied 2026-09-08 pre-C0):

| Pattern | Hits | Resolution |
|---------|------|------------|
| 1. Literal dotted path: `from infra\.project_config\b` | 26 sites in 26 files + 1 wildcard = 27 files | C2 sed migration (single-line replace, 2 patterns: `from infra.project_config import X` → `from lingwen_project_config import X` + wildcard → wildcard) |
| 2. Relative same-package: `from \.project_config\b` | 0 | n/a |
| 3. Relative parent-package: `from \.\.project_config\b` | 0 | n/a |
| 4. Filesystem path string literals: `infra/project_config` | 0 (only `infra/project_config.py` file path in commit message — not import) | n/a |

**3 function-body imports** (Phase 33/37 lesson — `^from` line-anchored regex misses indented imports):

| File | Line | Pattern |
|------|------|---------|
| `infra/full_check_report.py` | 170 | `    from infra.project_config import ProjectConfig` |
| `infra/project_characters.py` | 68 | `    from infra.project_config import ProjectConfig` |
| `packages/lingwen-creator/src/lingwen_creator/volume/summary.py` | 109 | `    from infra.project_config import ProjectConfig` |

**C2 sed strategy**: use `^\s*from infra\.project_config\b` (leading whitespace allowed) — `re.MULTILINE` in guards, but sed doesn't need MULTILINE since `.` matches newline only with `-z` flag. Use plain `sed -i 's/^[[:space:]]*from infra\.project_config import/from lingwen_project_config import/'` to catch both module-level + function-body in single pass.

**1 wildcard re-export**: `infra/project/__init__.py:4` `from infra.project_config import *  # noqa: F403`. Resolved by removing that single line in C3 (since source no longer exists).

### 4.5 Symbol Preservation

Source: `infra/project_config.py` has NO `__all__`. Top-level public symbols (verified by `import` greps):

| Symbol | Type | Source line | Consumers |
|--------|------|-------------|-----------|
| `ProjectConfig` | `@dataclass(frozen=True)` class with 12 fields + 4 methods | 22-134 | 26 files (all `import ProjectConfig` consumers) |
| `update_project_creation_mode` | function | 151-170 | 1 file (`apps/studio_api/routes/creator_core.py:79`) |

Private helpers (`_env_int`, `_env_bool`) and module constants (`_DEFAULT_CONFIG_REL`, `_TRUTHY`) stay as private (prefix `_`) — never imported by name in any consumer (verified via grep). They live in the package and work identically.

## 5. Migration Plan (6 Atomic Commits)

| # | Commit | Scope |
|---|--------|-------|
| **C0** | `docs(phase-38): spec + plan` | spec + plan in single commit (Phase 37 lesson 4) |
| **C1** | `chore(packages): scaffold lingwen-project-config` | new package + workspace member + sources |
| **C2** | `refactor(consumers): migrate 27 project_config consumers` | sed all 27 consumer files (incl. 3 function-body + 4 intra-infra) |
| **C3** | `chore(infra): delete infra/project_config.py` | source deletion + wildcard cleanup in infra/project/__init__.py |
| **C4** | `chore(infra): bump v37.0 + add invariant #53` | version bump + invariant #53 NEW + architecture.yml |
| **C5** | `test(phase-38): regression guards + doc sync` | 6 guards + CLAUDE.md sync + handoff doc |

**Atomic commit discipline** (per MEMORY N.14 lessons):
- C1 declares workspace member **BEFORE** `uv sync --all-packages` (Phase 34 lesson)
- C2 single commit handles all 27 consumers (Phase 37 lesson 5: 86 paths consumers migrated in single C2; project_config is smaller scale)
- C3 deletes source + cleans wildcard re-export (avoids ModuleNotFoundError between C2 and C3)
- C5 verifies BOTH staging-leak points (per Phase 36 critical lesson): post-ff-merge AND post-`git worktree remove --force`

## 6. Validation Gates

| Gate | Method | Target |
|------|--------|--------|
| G1 | `ruff check packages/lingwen-project-config/src/ apps/ packages/lingwen-* infra/` | clean (same as Phase 37 baseline: 4 pre-existing E741 in unrelated files) |
| G2 | `uv run pytest packages/lingwen-creator/tests/ --rootdir=packages/lingwen-creator` | 73/73 (preserved) |
| G3 | `uv run pytest packages/lingwen-shared/tests/ --rootdir=packages/lingwen-shared` | pass |
| G4 | `uv run pytest packages/lingwen-core/tests/ --rootdir=packages/lingwen-core` | 68/68 (preserved) |
| G5 | `uv run pytest packages/lingwen-got/tests/ --rootdir=packages/lingwen-got` | 208/208 (preserved) |
| G6 | `uv run pytest packages/lingwen-world-model/tests/ --rootdir=packages/lingwen-world-model` | 201/201 (preserved) |
| G7 | `uv run pytest packages/lingwen-paths/` | pass (NEW: lingwen-paths is a leaf with no test dir; smoke import test) |
| G8 | `uv run pytest packages/lingwen-pipeline/tests/ apps/studio_api/tests/ tests/infra/ tests/agent_system/` | pass |
| G9 | `grep -rn "infra\.project_config" --include="*.py" infra/ apps/ packages/` | 0 hits (Phase 37 invariant grep pattern) |
| G10 | `tests/test_phase38_lingwen_project_config.py` | 6/6 GREEN |

**Combined target**: ~660 tests pass (Phase 37 baseline 658 + ~2 new tests for package smoke).

## 7. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| `ProjectPaths` dependency on `lingwen-paths` breaks if Phase 37 reverted | Phase 37 already merged (HEAD e65d7784). Defensive: `grep -rn "from lingwen_paths" packages/lingwen-project-config/` to confirm import resolves. |
| Function-body imports missed by line-anchored grep | C2 uses `^\s*from` regex (leading whitespace allowed); verified by re-running consumer grep post-C2. |
| `infra.project_init.py` / `infra/project_characters.py` already wildcard `import *` from `infra/project_config` indirectly via `infra.project.__init__` | Wildcard re-export removed in C3 (line 4); these files import via the umbrella `infra.project.*`, NOT directly. Verified: `grep "infra.project_config" infra/project_init.py` = 0. |
| `infra/studio_registry.py` consumes `project_config` — Phase 40 candidate | This intra-infra consumer IS migrated in C2 (otherwise `infra.studio_registry` would still reference deleted `infra.project_config` after C3). |
| `tests/test_phase18_10_stale_imports.py` may still flag `infra.project_config` after migration | Check stale-list at Phase 37 confirmed `infra.paths` was updated. Apply same pattern: add `lingwen_project_config` to canonical list, remove `infra.project_config` from stale list. Done in C5. |

## 8. N.14 Lessons Applied (cumulative from Phase 19+)

| # | Lesson | Phase Origin | Application |
|---|--------|--------------|-------------|
| 1 | Line-anchored `^from` regex misses indented TYPE_CHECKING imports | Phase 19 | Use `^\s*from` + `re.MULTILINE` for grep; `^[[:space:]]*from` for sed |
| 2 | Lazy imports inside function bodies stay latent | Phase 33 | Audit 3 function-body sites listed in §4.4 |
| 3 | Filesystem-path string literals get missed | Phase 34 (7th) | Verified 0 hits in §4.4 row 4 |
| 4 | Specs can lie — verify symbol counts | Phase 34 + 35 | Spec asserts 2 public symbols; verified against `import` greps. Guard test will re-verify. |
| 5 | Workspace member declaration BEFORE uv sync | Phase 34 | C1 declares member + sources BEFORE `uv sync --all-packages` |
| 6 | Staging-leak check BOTH points | Phase 36 CRITICAL | C5 verifies post-ff-merge AND post-worktree-remove |
| 7 | C0 spec+plan combined is valid | Phase 37 | Single C0 commit |
| 8 | `xargs sed` without `-r` fails on empty input | Phase 36 + 37 | Use `xargs -r sed` or verify post-state via grep counts |
| 9 | Docstring example drift during sed | Phase 37 | Audit docstring `from infra.project_config` mentions post-C2; usually benign but noted in commit |
| 10 | Function-body imports break `^from` regex | Phase 33 + 37 | `^\s*from` regex used in C2 sed |
| 11 | 86-consumer migration feasible in single C2 | Phase 37 | Phase 38 = 27 consumers, same pattern |

## 9. Carryover Closure

- ✅ P3-ARCHDEBT 3/5 (`errors` Phase 36 + `paths` Phase 37 + `project_config` Phase 38) → CLOSED
- ⏳ P3-ARCHDEBT 4/5 (`logging_config`, 8 consumers) → Phase 39
- ⏳ P3-ARCHDEBT 5/5 (`studio_registry`, 50 consumers) → Phase 40

After Phase 40 closes `infra.studio_registry.*`, P3-ARCHDEBT 5/5 → fully CLOSED.

---

## 10. File-by-File Inventory

**Create (3 new files)**:

| File | Lines (est.) | Purpose |
|------|-------------|---------|
| `packages/lingwen-project-config/pyproject.toml` | ~25 | Hatchling build, deps: lingwen-paths + lingwen-shared |
| `packages/lingwen-project-config/src/lingwen_project_config/__init__.py` | 171 (1:1 from source) | All 2 public symbols + private helpers |
| `tests/test_phase38_lingwen_project_config.py` | ~120 | 6 regression guards (G1-G6) |
| `docs/superpowers/handoffs/2026-09-08-phase-38-p3-archdebt-project-config-handoff.md` | ~120 | Phase handoff doc |

**Modify (29 existing files)**:

| File | Change |
|------|--------|
| `pyproject.toml` (root) | +1 workspace member + 1 source + version 9.11.0→9.12.0 |
| `.lingwen/architecture.yml` | +1 invariant (#53 NEW) + version 36.0→37.0 |
| `.lingwen/constraints.yml` | (no change expected — no constraint affects project_config) |
| `CLAUDE.md` | +1 carryover line for v37.0 + invariant #53 + status update |
| `infra/project/__init__.py` | -1 line: remove `from infra.project_config import *  # noqa: F403` |
| 27 consumer files | sed: `from infra.project_config` → `from lingwen_project_config` (single-line replace, handles module-level + function-body + wildcard via pattern-aware sed) |
| `tests/test_phase18_10_stale_imports.py` | stale-list: remove `infra.project_config`, add `lingwen_project_config` |

**Delete (1 file)**:

| File | Lines | Reason |
|------|-------|--------|
| `infra/project_config.py` | 171 | full cutover to `packages/lingwen-project-config` |

**Total scope**: 3 create + 29 modify + 1 delete = 33 file ops across 6 atomic commits.

---

> Companion plan: `docs/superpowers/plans/2026-09-08-phase-38-p3-archdebt-project-config.md`