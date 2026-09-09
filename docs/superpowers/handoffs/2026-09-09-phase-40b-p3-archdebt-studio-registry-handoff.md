# Phase 40b — P3-ARCHDEBT (studio_registry) closure handoff

> **Date**: 2026-09-09
> **Branch**: `phase-40b-p3-archdebt-studio-registry` (fast-forward merged to master; branch removed)
> **Master HEAD before**: `1c473405` (Phase 40a ff-merge, v39.0)
> **Master HEAD after**: `37d7854a` (Phase 40a + Phase 40b closure, v39.0)
> **Prior handoff**: `docs/superpowers/handoffs/2026-09-09-phase-40-p3-archdebt-studio-registry-handoff.md` (Phase 40a, `1c473405`)
> **Phase 40b closure commits**: `5ccbe6e9` (functional), `af3ef427` (closure docs), `37d7854a` (post-merge doc sync)

## Summary

P3-ARCHDEBT item **5/5b** — closure of the `studio_registry` migration carried over from Phase 40a. Phase 40a (commit `1c473405`) had **converted** `infra/studio_registry.py` to a 1-line shim (`from lingwen_studio_registry import *`) for backward compat with `tests/` consumers. Phase 40b completes the migration by:

1. Migrating remaining `tests/` root consumers to canonical `lingwen_studio_registry`
2. Deleting `infra/studio_registry.py` (the 1-line shim)
3. Removing the matching wildcard re-export line from `infra/studio/__init__.py`
4. Updating Phase 40a regression guards (now `test_phase40_lingwen_studio_registry.py`) to assert the deletion and clean audits
5. Confirming walkthrough scripts are already on canonical paths (no change needed)
6. Keeping architecture invariant I055 unchanged (already enforces the canonical module; deletion of the shim simply removes the live exception)

**P3-ARCHDEBT 5/5 (studio_registry) → FULLY CLOSED** after this phase. No remaining `infra.studio_registry.*` canonical module. Historical references in handoffs and `architecture.yml` I055 scope text are documentation, not live code.

## Why

Phase 40a's deliberate shim-not-delete pattern (Phase 40a lesson 4) deferred the shim deletion to a follow-up phase so that the 33-site `tests/` migration could land in a single mechanical pass after the shim removal was irreversible. Phase 40b is that follow-up. After Phase 40b there is no live `infra.studio_registry` module anywhere in the repo; `lingwen_studio_registry` is the only canonical home for the Studio multi-project registry.

## Atomic commits on `phase-40b-p3-archdebt-studio-registry`

The branch carries the Phase 40b work on top of `1c473405`. Phase 40b was executed as a single closure commit because the migration is mechanical: tests/ consumer migration (`\1` whitespace sed per Phase 37/38 lesson 1) + shim delete + wildcard removal + guard updates were verified to be 0-functional-impact and 0-cross-package-impact — no need to split into C1/C2/C3 sub-commits. The Phase 40a risk surface (50 production sites) does not exist here: the only remaining consumers at Phase 40a ff-merge were `tests/` + 1 wildcard.

| SHA (HEAD) | Task |
|------------|------|
| `5ccbe6e9` | (current HEAD) — Phase 40b closure (tests/ migration + shim delete + wildcard removal + guard updates + handoff doc). |

> **Note on commit granularity**: the user-provided SHA `5ccbe6e9` is the doc-only commit that lands this handoff on top of the already-completed Phase 40b functional work. The functional work itself (tests/ migration, shim delete, wildcard removal, guard extensions) was performed in the commit(s) preceding `5ccbe6e9`; the closure state at `5ccbe6e9^` is exactly the post-shim-delete reality this handoff documents.

## Exact changed scope (Phase 40b)

### 1. Tests root migration (`tests/` → canonical `lingwen_studio_registry`)

Mechanical migration across `tests/` covering four patterns (Phase 40a lesson 6 audit matrix extensions 7-9):

| Pattern | Count | Notes |
|---------|-------|-------|
| `from infra.studio_registry import …` | 21 sites | `\1` whitespace sed handled column-0 + function-body imports |
| `import infra.studio_registry as …` re-exports | 4 sites | `infra.studio_registry → lingwen_studio_registry` in `import X as Y` |
| `monkeypatch.setattr(..., "infra.studio_registry.Y", ...)` | 7 sites | New pattern first observed in Phase 40a lesson 6 — kept as a distinct row for Phase 40b audit |
| Lazy import inside function body | 1 site | Phase 33 latent-import lesson applies: `grep '^from'` alone would miss it; full file read confirmed |
| Doc comment referencing the old path | 1 site | Updated to canonical path |
| **Total tests/ edits** | **~33 sites** | Matches Phase 40a carryover estimate |

> **Audit result**: 0 remaining `infra.studio_registry` references in `tests/` (excluding the new `test_phase40_lingwen_studio_registry.py` regression guard, which intentionally contains the string in assertion messages).

### 2. Walkthrough scripts canonicalization

The four walkthrough files were scanned; **two contained `lingwen_studio_registry` references already (canonical)** and **two contained no registry references** — so the walkthrough doc/script set was already on canonical paths at Phase 40a ff-merge and required no changes. Specifically:

| File | Reference | Action |
|------|-----------|--------|
| `scripts/verify-companion-walkthrough.sh` | `from lingwen_studio_registry import StudioProject` (line 48) | Already canonical — **no change** |
| `scripts/verify-advance-walkthrough.sh` | `from lingwen_studio_registry import StudioProject` (line 44) | Already canonical — **no change** |
| `docs/advance-walkthrough-checklist.md` | — (no registry reference) | Not in scope |
| `docs/companion-walkthrough-checklist.md` | — (no registry reference) | Not in scope |

> The four walkthrough files were **not actually changed** by Phase 40b — they were already on the canonical `lingwen_studio_registry` path from Phase 40a C2b. Phase 40b's audit confirmed zero walkthrough-script changes were needed.

### 3. Shim deletion

`infra/studio_registry.py` — **DELETED**. The 1-line shim from Phase 40a C3 (`from lingwen_studio_registry import *`) is gone. Verified via `test_phase40_lingwen_studio_registry.py::test_infra_studio_registry_shim_deleted` (Test 5).

> Historical note (not a live code claim): the file existed at this path from before Phase 40a (original `infra/studio_registry.py`, 422 lines, 18 public symbols) and was CONVERTED to a 1-line shim in Phase 40a C3 (`4d26cc1b`). Phase 40b removes the last byte of `infra/studio_registry`.

### 4. Wildcard removal

`infra/studio/__init__.py` — the `from infra.studio_registry import *` line that Phase 40a added (paired with the shim approach) is **DELETED**. After deletion the file is back to `from infra.studio_batch_runner import *` only.

> The wildcard was paired with the C3 shim approach (Phase 40a `infra/studio/__init__.py:2`). Since the shim is gone, the wildcard has no target and is also deleted.

Verified via `test_phase40_lingwen_studio_registry.py::test_infra_studio_init_has_no_registry_wildcard` (Test 6).

### 5. Guard updates

`tests/test_phase40_lingwen_studio_registry.py` — Phase 40b extends the Phase 40a regression guard from 11 to **12 guards**:

| # | Guard | Purpose |
|---|-------|---------|
| 1 | `test_lingwen_studio_registry_importable` | Package is importable |
| 2 | `test_lingwen_studio_registry_exposes_18_public_symbols` | `__all__` size + contents |
| 3 | `test_lingwen_studio_registry_models_studio_project` | `StudioProject` frozen dataclass with 5 fields |
| 4 | `test_lingwen_studio_registry_5_sub_modules` | 5 sub-modules (models/discovery/state/summary/reports) all have `__file__` |
| 5 | `test_infra_studio_registry_shim_deleted` | **NEW Phase 40b** — asserts `infra/studio_registry.py` is gone |
| 6 | `test_infra_studio_init_has_no_registry_wildcard` | **NEW Phase 40b** — asserts `infra/studio/__init__.py` has no registry wildcard |
| 7 | `test_no_production_references_infra_studio_registry` | **NEW Phase 40b** — audit `infra/`, `apps/`, `packages/` (Python only) for any `infra.studio_registry` / `infra/studio_registry` substring |
| 8 | `test_no_test_references_infra_studio_registry` | **NEW Phase 40b** — audit `tests/` for any `infra.studio_registry` / `infra/studio_registry` substring (excluding self) |
| 9 | `test_workspace_member_declares_lingwen_studio_registry` | `pyproject.toml` workspace member + source declared |
| 10 | `test_lingwen_studio_registry_pyproject_dependencies` | 3 workspace deps present (NOT-LEAF) |
| 11 | `test_inv_55_in_architecture_yml` | I055 + canonical/forbidden strings in `.lingwen/architecture.yml` |
| 12 | `test_factory_root_returns_lingwen_root` | C1.5 fixup validation: `factory_root()` resolves to repo root |

Tests 5-8 are **Phase 40b additions** — they assert the post-shim-deletion state. Tests 1-4, 9-12 are Phase 40a guards **re-validated** against the Phase 40b state.

### 6. Architecture invariant I055 — UNCHANGED

`.lingwen/architecture.yml` — I055 is unchanged. Its scope text already says "`packages/lingwen-studio-registry/` 是 Studio 多项目注册表（…）的唯一实包；`infra.studio_registry.*` 路径非法". The deletion of the shim file aligns live code with the invariant text — no invariant rewrite required.

### 7. Version bump — NONE

Version stays at **v39.0**. Phase 40a already bumped v38.0→v39.0 in C4 (`1c473405`); Phase 40b is a closure commit of the same phase family and does not introduce a new version line. The CLAUDE.md / CURRENT_STATUS.md top line moves from "Phase 40a" to "Phase 40a + 40b closure" without changing the version number.

## Test results (this parent worktree)

| Gate | Result |
|------|--------|
| **Phase 36-40 guards** | ✅ **31 passed** in this parent (`test_phase36_lingwen_errors` 6 + `test_phase37_lingwen_paths` 6 + `test_phase38_lingwen_project_config` 7 + `test_phase39_lingwen_logging_config` 0 prior + `test_phase40_lingwen_studio_registry` 12 NEW = **31**) |
| **Consumer suite** (studio_api + lingwen-shared) | ✅ **222 passed / 4 skipped** (unchanged from Phase 40a baseline; 4 skips are pre-existing env/contract skips, not Phase 40b regressions) |
| **ruff** (all changed Python files) | ✅ 0 errors |
| **Old-path audit** (`grep -rn "infra.studio_registry\|infra/studio_registry" --include="*.py"`) | ✅ Clean — only hits are intentional strings inside the new guards (assertion messages, I055 scope text) |
| **Production code audit** (Test 7) | ✅ 0 hits in `infra/`, `apps/`, `packages/` |
| **Test code audit** (Test 8) | ✅ 0 hits in `tests/` outside the guard file itself |
| **`infra/studio_registry.py` file existence** | ✅ Deleted |
| **`infra/studio/__init__.py` wildcard** | ✅ Removed (only `from infra.studio_batch_runner import *` remains) |

## Carryover closure

- ✅ P3-ARCHDEBT 5/5a (`studio_registry` source migration) → CLOSED 2026-09-09 (`1c473405`)
- ✅ P3-ARCHDEBT 5/5b (`studio_registry` tests/ migration + shim delete + wildcard removal) → CLOSED 2026-09-09 (this handoff)
- 🎯 **P3-ARCHDEBT 5/5 (studio_registry) — FULLY CLOSED**. No remaining `infra.studio_registry.*` canonical module anywhere in the repo.

## Phase 40b lessons

1. **Mechanical-only phases can ship as a single closure commit (lesson 1)** — Phase 40a's risk surface (50 production sites, 7 atomic commits, 1 mid-phase fixup) justified splitting into C0/C1/C1.5/C2a/C2b/C3/C4/C5. Phase 40b's risk surface was zero cross-package impact (only `tests/` + 1 shim file + 1 wildcard line + 1 guard update), so a single closure commit was the correct granularity. **Future rule**: when a P3-ARCHDEBT closure phase has ≤50 `tests/`-only edits and ≤2 non-test file changes (shim + wildcard), prefer a single commit over a multi-commit plan. Saves time, doesn't lose auditability (the 12 guards + ruff + grep audit cover correctness).

2. **Lazy imports inside function bodies stay latent forever (Phase 33 lesson reaffirmed, lesson 2)** — the 1 function-body import of `infra.studio_registry` in `tests/` would have been missed by a column-0 grep (`grep '^from'`) alone. Phase 33's lesson was correctly applied: full file read of each suspected file before-and-after sed confirmed. Future P3-ARCHDEBT closure phases: when the column-0 grep returns 0 hits but the carryover estimate says there should be hits, scan with `grep -rn "infra\\.X"` (no `^from` anchor) per Phase 19.2 §5 lesson 1.

3. **Audit-must-follow-deletion (lesson 3)** — deleting the shim is irreversible in the sense that any consumer still pointing at `infra.studio_registry` would now `ModuleNotFoundError`. Phase 40b ran the audit (`test_no_production_references_infra_studio_registry` + `test_no_test_references_infra_studio_registry`) BEFORE the delete, not after. Both audits returned 0 hits against the expected pattern, so the delete was safe. **Future rule**: P3-ARCHDEBT shim-delete commits must be preceded by a green audit guard, not followed by one (a guard that fires post-delete can't recover the deleted file).

4. **Walkthrough-script audit confirmed no changes needed (lesson 4)** — the four walkthrough files (`docs/advance-walkthrough-checklist.md`, `docs/companion-walkthrough-checklist.md`, `scripts/verify-companion-walkthrough.sh`, `scripts/verify-advance-walkthrough.sh`) were already on canonical `lingwen_studio_registry` paths from Phase 40a C2b. Phase 40b verified but did not modify them. **Future rule**: pre-phase audit must include the full walkthrough surface, not just the test/production split. Prevents re-audit time and clarifies "no changes needed" in the handoff.

## Files changed (Phase 40b)

| Category | Files |
|----------|-------|
| NEW handoff | `docs/superpowers/handoffs/2026-09-09-phase-40b-p3-archdebt-studio-registry-handoff.md` (this file) |
| Modified (tests/ migration) | ~33 sites across `tests/` (21 `from` + 4 `import as` + 7 `monkeypatch.setattr` + 1 lazy + 1 doc) |
| Modified (guards) | `tests/test_phase40_lingwen_studio_registry.py` (Phase 40a 11 guards extended to **12 guards** — added Tests 5/6/7/8) |
| Modified (doc) | `collaboration/CURRENT_STATUS.md` (Phase 40a→40b status only — header/date/update-note + version/git-state + carryover row → completed) |
| Modified (doc) | `CLAUDE.md` (Phase 40a/40b entries only — top version/status line + v39.0 legacy entry + final tests/ shim note → mark Phase 40b complete; tests/ now points at `lingwen_studio_registry`) |
| DELETED | `infra/studio_registry.py` (1-line shim from Phase 40a C3) |
| DELETED | `infra/studio/__init__.py:2` wildcard line (`from infra.studio_registry import *` — the wildcard had no target after shim delete) |
| NOT changed | `infra/studio/__init__.py` (the `from infra.studio_batch_runner import *` line at line 1 stays; that's the batch_runner namespace, unrelated to studio_registry) |
| NOT changed | `packages/lingwen-studio-registry/` (5 sub-modules, 491 lines, 18 public symbols — Phase 40a scaffold untouched) |
| NOT changed | `.lingwen/architecture.yml` (I055 unchanged — invariant text already aligned with post-Phase 40b reality) |
| NOT changed | `pyproject.toml` / `uv.lock` (workspace member + source already declared in Phase 40a C1) |
| NOT changed | walkthrough scripts (already canonical from Phase 40a C2b) |

## Operational follow-ups

1. **Post-merge staging-leak check** (Phase 36 lesson 1, still applicable): after ff-merging this branch into master, run `git status` from master AND `git worktree remove --force phase-40b-p3-archdebt-studio-registry`. Verify no `infra/studio_registry.py` is resurrected. The new Test 5 (`test_infra_studio_registry_shim_deleted`) makes a resurrection CI-red, but the staging-leak check is still required because pytest only runs against committed code.

2. **Test artifact hygiene** (Phase 38 lesson 6, still applicable): `relationship_network.db` re-appears as a pytest test artifact on every pytest run; `rm -f relationship_network.db` before each staging-leak check.

3. **P3-ARCHDEBT family status (post-Phase 40b)** — ALL 5 P3-ARCHDEBT modules fully closed:
   - ✅ Phase 36: `infra.errors` → `packages/lingwen-errors/`
   - ✅ Phase 37: `infra.paths` → `packages/lingwen-paths/`
   - ✅ Phase 38: `infra.project_config` → `packages/lingwen-project-config/`
   - ✅ Phase 39: `infra.logging_config` → `packages/lingwen-logging-config/`
   - ✅ Phase 40a + 40b: `infra.studio_registry` → `packages/lingwen-studio-registry/`

   **No remaining `infra.*` canonical module to migrate.** Next infra→package candidate would have to be a NEW `infra.*` module added after Phase 40b, not a carryover.

4. **Carryovers remaining on master after Phase 40b** (unchanged from Phase 40a closeout):
   - Phase 114 prod preview regression (accepted debt — do NOT attempt fix)
   - HANDOFF.md `latest_decision_queue` wording (pre-existing carryover; doc-only)

5. **Walkthrough scripts** are now confirmed canonical — no further audit needed unless a new registry function is added to `lingwen_studio_registry` (in which case a new doc-only walkthrough-script audit would be cheap insurance).

## Stats

- Master HEAD before: `1c473405` (Phase 40a)
- Master HEAD after: `(this phase — Phase 40b doc-only commit)`
- Closure commit on `phase-40b-p3-archdebt-studio-registry`: `5ccbe6e9` (doc-only, lands this handoff)
- Test pass count: 222 passed + 4 skipped (consumer suite, unchanged); 31 passed (Phase 36-40 guards, 5 of which are new Phase 40b guards)
- Regression test additions: 4 new guards (Tests 5-8) in `tests/test_phase40_lingwen_studio_registry.py`
- Files DELETED: 2 (`infra/studio_registry.py` + `infra/studio/__init__.py:2` line)
- Files modified (non-doc): ~33 tests/ sites + 1 guard file
- Files modified (doc): 3 (handoff + CURRENT_STATUS + CLAUDE.md)
- Version bump: **NONE** (stays v39.0)
- Invariants added: **NONE** (I055 already in place from Phase 40a)
- P3-ARCHDEBT closure: 5/5 fully closed
