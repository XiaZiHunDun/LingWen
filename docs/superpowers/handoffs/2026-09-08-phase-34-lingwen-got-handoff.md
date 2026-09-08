# Phase 34 — LINGWEN-GOT package migration — handoff

> **Date**: 2026-09-08
> **Branch**: `phase-34-lingwen-got`
> **Master HEAD at start**: `eecdd20c` (v32.0 — Phase 33 SAF-LABEL-FIXUP)
> **Commits**: 12 atomic commits (11 implementation + 1 final doc-sync)
> **Status**: CLOSED ✅

## Summary

Phase 34 closes the largest remaining P2-ARCHDEBT item: migrating the entire GoT engine from `infra/got/` (9 modules, 1788 lines) to a dedicated `packages/lingwen-got/` package with 32 public symbols. 30 consumer sites migrated across 4 lingwen-core + 3 apps/studio_api + 2 infra + 21 test files; 12 got-related test files moved to `packages/lingwen-got/tests/`; the workflow YAML data dir followed. `infra/got/` directory deleted. **Invariant #49 NEW**: `packages/lingwen-got/` is the canonical GoT engine location; `infra.got.*` paths are forbidden.

**Net effect**: ~1900 lines of production code relocated to a proper workspace package with its own `pyproject.toml` declaring `pydantic>=2.7`, `PyYAML>=6.0`, `lingwen-llm`, `lingwen-prompt` deps; `infra/got/` deleted; 7 regression guards in `tests/test_phase34_lingwen_got.py`.

## Commit chain (12 atomic)

```
f568a562 docs(phase-34): write spec for infra.got.* → packages/lingwen-got/ migration [C0]
649fab94 chore(packages): scaffold lingwen-got package skeleton                       [C1.1]
7cbdf3a3 fix(spec): correct 36 → 32 symbol count per T1 implementer verification     [C1.2]
46337378 fix(lingwen-got): copy workflows/ data dir + update stale docstrings        [C1.3]
e543914b fix(lingwen-got): declare PyYAML + lingwen-prompt deps + add llm_compute __all__ [C1.4]
182a5e0c refactor(test): move 12 got-related test files to packages/lingwen-got/tests/ [C2.1]
3880fdf5 fix(test): apply ruff --fix + update stale workflow path docstrings          [C2.2]
3f2311b3 refactor(infra): migrate 4 lingwen-core consumers to lingwen_got            [C3]
d53bb1cb refactor(apps): migrate 3 apps/studio_api consumers to lingwen_got           [C4]
83220eee refactor(infra): migrate 2 infra + 10 tests consumers to lingwen_got        [C5]
40ddccec fix(workflow-paths): update stale infra/got/workflows references            [pre-C6 fixup]
e2ad1529 chore(infra): delete infra/got/ directory                                    [C6]
<this>   test(phase-34): regression guard tests + doc sync                            [C7]
```

(11 implementation commits + 1 final doc-sync commit; per workflow, no separate handoff commit — handoff doc IS this file, committed via C7 doc sync.)

## What was deleted (C6)

| File / Dir | Type | Lines | Status at deletion |
|---|---|---|---|
| `infra/got/` (entire directory) | Pure GoT engine + workflows/ data dir | 9 modules + ~1788 lines | 0 functional consumers; all 30 migrated to `lingwen_got.*` |
| **Total** | | **~1788 lines + workflow YAMLs** | |

## What was created

| Path | Purpose |
|---|---|
| `packages/lingwen-got/pyproject.toml` | Hatchling build backend; deps: pydantic, PyYAML, lingwen-llm, lingwen-prompt |
| `packages/lingwen-got/src/lingwen_got/` | 9 modules: `__init__.py` + `aggregator.py` + `cache.py` + `data_structures.py` + `graph.py` + `llm_compute.py` + `scheduler.py` + `visualizer.py` + `workflow_loader.py` |
| `packages/lingwen-got/src/lingwen_got/workflows/` | YAML data dir (novel_writing.yaml + minimal_e2e.yaml) |
| `packages/lingwen-got/tests/` | 12 test files moved from `tests/`: test_aggregator, test_cache, test_data_structures, test_decision_pause_resume, test_graph, test_llm_compute, test_llm_compute_e2e, test_scheduler, test_visualizer, test_workflow_loader, test_got_bridge, test_got_bridge_budget |
| `tests/test_phase34_lingwen_got.py` | 7 regression guards (new) |

## Consumer migration (30 sites)

### Category 1: lingwen-core (4 files)
- `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py`
- `packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py`
- `packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py`
- `packages/lingwen-core/src/lingwen_core/agents/got_bridge.py`

### Category 2: apps/studio_api (3 files)
- `apps/studio_api/protocols.py`
- `apps/studio_api/routes/workflows.py`
- `apps/studio_api/helpers/workflow.py`

### Category 3: infra (2 files)
- 2 files in `infra/` referencing GoT types/scheduler

### Category 4: tests (21 files)
- 12 test files MOVED to `packages/lingwen-got/tests/` (and rewritten `from infra.got.X` → `from lingwen_got.X`)
- 9 additional test files in `tests/` updated import paths

## Pre-C6 fixup (N.14 lesson 1, 3rd occurrence)

C6 deletion was almost blocked by **filesystem-path string literals** containing `infra/got/workflows/` inside 5 file bodies (not Python imports — actual `Path(...)` or string-built paths inside function bodies that resolved workflows via the package's `__file__` location). sed across Python imports missed them entirely. The fixup commit `40ddccec` migrated them to dynamic `lingwen_got.workflow_loader.__file__` resolution.

## Validation gates (all green)

| Gate | Command | Result |
|------|---------|--------|
| G1 ruff | `ruff check .` | 3 pre-existing errors unchanged (infra/subplot/__init__.py + infra/world_model/__init__.py + tests/agent_system/test_dashboard_budget_endpoints.py); zero new errors |
| G2 regression guards | `.venv/bin/python -m pytest tests/test_phase34_lingwen_got.py -v` | **7/7 GREEN** (pyproject-exists + init-exists + infra-deleted + 32-symbols + 12-test-files + 4-core-consumers + lingwen-llm-dep) |
| G3 lingwen-got suite | `.venv/bin/python -m pytest packages/lingwen-got/tests/` | **208/208 PASS** |
| G4 lingwen-core suite | `.venv/bin/python -m pytest packages/lingwen-core/tests/` | **68/68 PASS** (baseline preserved) |
| G5 studio_api suite | `.venv/bin/python -m pytest apps/studio_api/tests/` | **82/82 PASS** |
| G6 grep audit | `grep -rn "infra\.got\b" --include="*.py" .` | **0 hits** |
| G7 filesystem-path audit | `grep -rn "infra/got/workflows" --include="*.py" .` | **0 hits** (pre-C6 fixup) |
| G8 deleted-dir check | `test -d infra/got && echo EXISTS \|\| echo DELETED` | **DELETED** |
| G9 workspace members | `grep -c "lingwen-got" pyproject.toml` | 2 hits (members + dep) ✅ |
| G10 lingwen-got import | `python -c "import lingwen_got; print(len(lingwen_got.__all__))"` | **32** ✅ |
| G11 pre-existing fail baseline | Compare against master `eecdd20c` baseline (47 failed + 8 errors in tests/) | 0 NEW failures introduced |

## Architecture invariants enforced (1 NEW, 50 total)

- **#49 (NEW)** ✅ `packages/lingwen-got/` is the canonical GoT engine package. `infra.got.*` paths are forbidden (Phase 34+).
  - Enforced by: `tests/test_phase34_lingwen_got.py::test_infra_got_directory_deleted` + grep audit gate.
  - Scope: all new GoT engine code must `from lingwen_got.X import Y`.

## Doc sync (C7 commit)

| File | Change |
|------|--------|
| `CLAUDE.md` | v33.0 entry (mirror v32.0 format) + I049 invariant row + 架构债 段落更新 (Phase 33+ → Phase 35+) |
| `.lingwen/architecture.yml` | version 32.0 → 33.0; I049 invariant added |
| `docs/LINGWEN_ARCHITECTURE_SPEC.md` | §9.8 GOT 模块表 — `infra/got/X.py` → `packages/lingwen-got/src/lingwen_got/X.py` |
| `docs/superpowers/handoffs/2026-09-07-phase-32-shim-cleanup-handoff.md` | Carryover row: `infra.got.* → packages/lingwen-got/` migration → CLOSED; "Only 1 remaining P2-ARCHDEBT item" line appended closure note |
| `docs/superpowers/archive/PHASE_HISTORY.md` | v33.0 row added at top; v32.0/v31.0/v30.0/v29.0/v28.0/v27.0/v26.0/v25.9 rows also backfilled (these were missing from prior archive snapshot) |
| `tests/test_phase34_lingwen_got.py` | NEW — 7 regression guards |
| `MEMORY.md` (global, outside worktree) | Master HEAD `eecdd20c` → `<c7-sha>`; carryover closure update; Phase 34 lessons added |

## Carryover closure

| Carryover | Status |
|-----------|--------|
| P2-ARCHDEBT `infra.got.*` → `packages/lingwen-got/` migration (v32.0 剩余 1/2) | **CLOSED** by v33.0 (30 consumers migrated, 12 test files moved, infra/got/ deleted, I049 enforced) |

## Carryover to Phase 35+

| ID | Scope | Estimate |
|----|-------|----------|
| **`infra/world_model/__init__.py` split** (P2-ARCHDEBT remaining 1/1) | mixed file → canonical (lingwen_core.domain.*) + behavior (infra.world_model.{engine,queries,registry,...}) + 5 consumer migration | 1 phase / 8-12 commits |
| **P3-ARCHDEBT (NEW)** | `infra.{paths, project_config, logging_config, errors, studio_registry}` → packages/ migration | 1+ phases |
| **HANDOFF.md `latest_decision_queue` wording** | pre-existing carryover | doc-only |
| **Phase 114 prod preview regression** (accepted) | do NOT attempt fix | n/a |

## Lessons (Phase 34 specific)

### 1. N.14 lesson 1, 7th time — filesystem-path string literals missed by `sed` on Python imports

The pre-C6 fixup caught 5 missed sites where the *filesystem path string* `infra/got/workflows/` was used (not Python imports) inside function bodies — typically `Path(__file__).parent / "workflows"` style path resolutions that needed to point at the new `packages/lingwen-got/src/lingwen_got/workflows/` location. `sed -i 's/infra\.got/lingwen_got/g'` only touches Python import statements, not arbitrary string literals.

**Rule for all future shim-deletion phases**: audit must include 4 grep patterns:
1. Literal dotted path (`from infra.X.Y import ...`)
2. Relative same-package (`from .Y import ...`)
3. Relative parent-package (`from ..Y import ...`)
4. Filesystem path string literals: `grep -rn "infra/X/Y" --include="*.py"` — finds `Path(...)` or string-built paths inside function bodies.

### 2. N.14 lesson 4, 5th time — pre-existing failure baseline verification

Baseline capture in T0 was incomplete (claimed 0 failures; actual was 47 failed + 8 errors in tests/, all pre-existing environmental). The implementer caught the discrepancy by stashing phase-34 changes and running a representative subset of tests against master baseline. Always run multiple sample tests to validate baseline before relying on it.

### 3. Spec count error — 36 vs 32 (implementer caught the spec error)

The original spec listed 36 expected `__all__` symbols. During C1 scaffold the implementer counted actual symbols and reported **32** (not 36). Per "verify everything" principle, the implementer's verification was essential. If we'd shipped 36 guards, the symbol-count test would have failed in C7. Lesson: **specs can lie; always cross-check symbol counts against actual `__init__.py` `__all__`**.

### 4. C3 + C5 lesson (carried forward) — `git add dir/` is recursive

`git add packages/lingwen-got/` recursively added 12 test files plus the new __init__.py plus pyproject.toml. Per Phase 32 C3 lesson: prefer **explicit file paths** in `git add` when the commit scope is narrow (e.g. `git add packages/lingwen-got/tests/test_aggregator.py packages/lingwen-got/tests/test_cache.py ...`).

### 5. ruff I001 after sed — always run `ruff check --fix` proactively

Every sed migration that touches import order produces I001 violations. Pattern: run `ruff check --fix packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py` immediately after each consumer migration. Saves a follow-up commit.

### 6. Workspace member declaration before `uv sync` causes ImportError

`packages/lingwen-got` must be in root `pyproject.toml` `[tool.uv.workspace] members` BEFORE running `uv sync --all-packages`. Otherwise `import lingwen_got` raises `ModuleNotFoundError`. Lesson: workspace declaration is in C1, not C7.

## Solo workflow closure (T8)

After this C7 commit lands:
1. ff-merge phase-34-lingwen-got → master: `git checkout master && git merge --ff-only phase-34-lingwen-got`
2. Push master: `git push origin master`
3. Remove worktree: `git worktree remove /home/ailearn/projects/LingWen-phase-34`
4. Delete branch: `git branch -d phase-34-lingwen-got`
5. Update MEMORY.md Master HEAD to C7 SHA (already done in C7)

## See also

- Spec: `docs/superpowers/specs/2026-09-08-phase-34-lingwen-got-design.md`
- Plan: `docs/superpowers/plans/2026-09-08-phase-34-lingwen-got.md`
- Phase 32 handoff (predecessor): `docs/superpowers/handoffs/2026-09-07-phase-32-shim-cleanup-handoff.md`
- Phase 33 SAF-LABEL-FIXUP (predecessor): `eecdd20c` — no handoff doc, was a 1-line fixup
