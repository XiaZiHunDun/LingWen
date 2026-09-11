# Phase 47 P3-ARCHDEBT (studio_batch) — 3-module batch Design Spec

> **Phase**: 47 (P3-ARCHDEBT 11/10+1 — continues from Phase 46's `filter MERGE` closure)
> **Branch**: `phase-47-p3-archdebt-studio-batch`
> **Date**: 2026-09-11
> **Rank**: ARCHDEBT-CANDIDATES.md "studio_batch_*" (recommended as batch per "合并 1 phase")
> **Template**: Phase 45 (lingwen-utilities BATCH) — multi-module batch, 5-6 commit pattern
> **Special**: **Runner → Streamer workspace dep** (intra-batch coupling preserved across packages)

## Goal

Move 3 studio_batch modules (`infra/studio_batch_runner.py` + `infra/studio_batch_templates.py` + `infra/studio_batch_streamer.py` = 1041 LOC total) into 3 standalone canonical packages:

- `packages/lingwen-studio-batch-runner/` (676 LOC, NOT-LEAF)
- `packages/lingwen-studio-batch-templates/` (234 LOC, NOT-LEAF)
- `packages/lingwen-studio-batch-streamer/` (131 LOC, TRUE LEAF)

Delete the 3 source files and add **invariants I064-I066**. Continue P3-ARCHDEBT pattern.

## Background — Pre-Spec Audit (2026-09-11 fresh-run)

### 9-pattern audit

| # | Pattern | runner | templates | streamer | Total |
|---|---------|--------|-----------|----------|-------|
| 1 | Literal dotted-path imports `from infra.X import Y` | 8 | 1 | 2 | 11 |
| 2 | Indented/function-body imports | 0 | 0 | 0 | 0 |
| 3 | Relative imports | 0 | 0 | 0 | 0 |
| 4 | Filesystem path literals | 0 | 0 | 0 | 0 |
| 5 | **Wildcard** `from infra.X import *` | **1** | 0 | 0 | **1** |
| 6 | `monkeypatch.setattr` + `with patch("infra.X.Y", ...)` | 21 | 4 | 0 | 25 |
| 7 | Plain `import infra.X` | 0 | 0 | 0 | 0 |
| 8 | Doc comments referencing old path | 5 | 0 | 1 | 6 (preserved) |
| 9 | Prior-phase guard's hardcoded representative | 0 | 0 | 0 | 0 |

### Real external consumers (15 unique files, 1 wildcard + 11 anchored + 25 monkeypatch paths)

**studio_batch_runner (13 files)**:
1. `apps/studio_api/routes/creator_core.py` — 2 anchored imports (lines 161, 171)
2. `apps/studio_api/routes/studio.py` — 2 anchored imports (lines 295, 333) + 3 doc-only
3. `apps/studio_api/tests/test_studio_batch_events_route.py` — 1 anchored + 4 monkeypatches
4. `apps/studio_api/tests/test_studio_batch_history_route.py` — 4 monkeypatches
5. `apps/studio_api/tests/test_studio_cancel_route.py` — 1 anchored + 3 monkeypatches
6. `infra/studio/__init__.py:1` — WILDCARD
7. `infra/studio_batch_templates.py` — 3 doc-only (intra-batch reference)
8. `tests/dashboard/test_studio_batch_endpoints.py` — 4 monkeypatches
9. `tests/infra/test_studio_batch_queue.py` — 1 anchored + 4 monkeypatches
10. `tests/infra/test_studio_batch_runner.py` — 1 anchored + 4 monkeypatches
11. `tests/infra/test_studio_batch_runner_cancel.py` — 1 anchored + 1 monkeypatch
12. `tests/infra/test_studio_batch_runner_eta.py` — 1 anchored
13. `tests/infra/test_studio_batch_runner_restart.py` — 1 anchored + 4 monkeypatches

**studio_batch_templates (3 files)**:
1. `apps/studio_api/routes/studio.py` — 1 anchored (line 295 inside runner.py's multi-symbol import block)
2. `apps/studio_api/tests/test_studio_batch_templates_route.py` — 1 anchored + 4 monkeypatches
3. `tests/infra/test_studio_batch_templates.py` — 1 anchored

**studio_batch_streamer (2 files)**:
1. `apps/studio_api/routes/studio.py` — 1 doc-only (no actual import)
2. `infra/studio_batch_runner.py` — intra-batch (line 25 anchored)
3. `tests/infra/test_studio_batch_streamer.py` — 1 anchored

### False-positive filter (5+ sites excluded)

- `infra/studio_batch_templates.py:4,9,36` — docstring `:func:` references (preserve per spec)
- `tests/infra/test_studio_batch_templates.py:1` — docstring (preserve)
- `apps/studio_api/routes/studio.py:8,63,87` — docstring references (preserve)
- `tests/infra/test_studio_batch_streamer.py:1` — docstring (preserve)

### Spec drift (N.14 lesson 1 #25)

ARCHDEBT-CANDIDATES.md said "10/3/3 consumers" for runner/templates/streamer. Actual unanchored count is 13/3/2 (note templates.py doc-only reference counted). ARCHDEBT-CANDIDATES.md cited anchored count (~10/3/3).

## Architecture —

### Package layout (3 packages × 2-3 sub-modules)

```
packages/
├── lingwen-studio-batch-runner/                # 676 LOC, NOT-LEAF (2 deps)
│   ├── pyproject.toml                          # deps: lingwen-studio-registry + lingwen-studio-batch-streamer
│   ├── src/lingwen_studio_batch_runner/
│   │   ├── __init__.py                         # re-exports 12 public symbols
│   │   └── service.py                          # all logic
│   └── tests/test_studio_batch_runner.py + 4 sibling tests MOVED
│
├── lingwen-studio-batch-templates/             # 234 LOC, NOT-LEAF (1 dep)
│   ├── pyproject.toml                          # deps: lingwen-studio-registry
│   ├── src/lingwen_studio_batch_templates/
│   │   ├── __init__.py                         # re-exports 5 public symbols
│   │   └── service.py                          # all logic
│   └── tests/test_studio_batch_templates.py MOVED
│
└── lingwen-studio-batch-streamer/              # 131 LOC, TRUE LEAF (0 deps)
    ├── pyproject.toml                          # deps: [] (stdlib only)
    ├── src/lingwen_studio_batch_streamer/
    │   ├── __init__.py                         # re-exports 6 consts + 5 funcs
    │   └── service.py                          # all logic
    └── tests/test_studio_batch_streamer.py MOVED
```

### Public surface (27 total public symbols)

**runner** (12 public + 1 dataclass + 3 exceptions):
| Symbol | Kind |
|--------|------|
| `BatchJob` | dataclass |
| `BatchAlreadyRunningError`, `BatchPreflightError`, `BatchNotAllowedError` | exception classes |
| `dashboard_batch_allowed` | func |
| `find_running_job` | func |
| `start_batch_job`, `submit_batch_job` | funcs |
| `advance_batch_queue`, `list_batch_queue` | funcs |
| `list_batch_jobs_for_slug`, `get_batch_job` | funcs |
| `active_batch_job_for_project`, `cancel_batch_job` | funcs |
| `compute_pilot_eta`, `replay_events` | funcs |

**templates** (5 public + 1 dataclass):
| Symbol | Kind |
|--------|------|
| `BatchTemplate` | dataclass |
| `create_batch_template`, `list_batch_templates` | funcs |
| `get_batch_template`, `update_batch_template` | funcs |
| `delete_batch_template` | func |

**streamer** (6 consts + 5 funcs):
| Symbol | Kind |
|--------|------|
| `EVENT_JOB_STATE`, `EVENT_CHAPTER_STARTED`, `EVENT_CHAPTER_COMPLETED` | consts |
| `EVENT_JOB_COMPLETED`, `EVENT_JOB_FAILED`, `EVENT_JOB_CANCELLED` | consts |
| `format_event`, `is_terminal_event` | funcs |
| `subscribe`, `unsubscribe`, `publish` | funcs |

### Workspace deps — NOT-LEAF (runner + templates) + TRUE LEAF (streamer)

```toml
# packages/lingwen-studio-batch-runner/pyproject.toml
dependencies = [
    "lingwen-studio-registry",  # Phase 40a (NOT-LEAF for runner)
    "lingwen-studio-batch-streamer",  # intra-batch dep (Phase 47 batch)
]

# packages/lingwen-studio-batch-templates/pyproject.toml
dependencies = [
    "lingwen-studio-registry",  # uses factory_root
]

# packages/lingwen-studio-batch-streamer/pyproject.toml
dependencies = []  # TRUE LEAF — stdlib only
```

### Invariants I064-I066

```
I064 | `packages/lingwen-studio-batch-runner/` is BatchJob + dashboard_batch_allowed + start_batch_job +
       submit_batch_job + advance_batch_queue + list_batch_queue + list_batch_jobs_for_slug +
       get_batch_job + active_batch_job_for_project + cancel_batch_job + compute_pilot_eta +
       replay_events + 3 exception classes unique canonical package;
       `infra.studio_batch_runner.*` paths forbidden (P3-ARCHDEBT 11/10+1 Phase 47)

I065 | `packages/lingwen-studio-batch-templates/` is BatchTemplate + create_batch_template +
       list_batch_templates + get_batch_template + update_batch_template + delete_batch_template
       unique canonical package; `infra.studio_batch_templates.*` paths forbidden
       (P3-ARCHDEBT 11/10+1 Phase 47)

I066 | `packages/lingwen-studio-batch-streamer/` is 6 event constants + format_event +
       is_terminal_event + subscribe + unsubscribe + publish unique canonical package;
       `infra.studio_batch_streamer.*` paths forbidden (P3-ARCHDEBT 11/10+1 Phase 47)
```

## Atomic commits (5+1 = 6 total — batch pattern with potential C4.5 fixup)

| Commit | Type | Scope | Notes |
|--------|------|-------|-------|
| **C0** | `docs(phase-47)` | spec | This document (3-module batch) |
| **C1** | `feat(packages)` | scaffold 3 packages | 6 sub-modules + 3 pyproject + 3 workspace register + 6 test MOVEs |
| **C2** | `refactor(consumers)` | bulk migrate 15 files | Single commit per Phase 37 lesson (1 wildcard + 11 anchored + 25 monkeypatches) |
| **C3** | `chore(infra)` | delete 3 files + I064-I066 + v45.0 | 3 files DELETED + 3 invariants + version bump |
| **C4** | `test(phase-47)` | 20+ guards + handoff | Phase 47 guards + handoff doc + topic file |
| **(C4.5)** | `fix(test)` | optional fixup | If prior-phase guards break (N.14 lesson 1 #25 pattern) |

### C1 details (scaffold — 3 packages)

**Files created** (10 total):
- 3× `pyproject.toml` (one per package)
- 3× `__init__.py` (one per package)
- 3× `service.py` (one per package)
- 1× test MOVE per package (3 total)

**Files modified**:
- Root `pyproject.toml` — add 3 new workspace members BEFORE uv sync (per Phase 34 lesson)

### C2 details (bulk migrate 15 files — single commit)

**Migrations** (per module):
- runner: 1 wildcard + 8 anchored imports + 21 monkeypatch paths
- templates: 1 anchored import + 4 monkeypatch paths
- streamer: 1 anchored import (intra-batch dep in runner.py line 25)

**Single bulk commit** (per Phase 37 lesson — 15 files in one C2 is manageable; per-site edits via sed).

### C3 details (delete 3 files + 3 invariants)

**Files modified**:
- `infra/studio_batch_runner.py` — DELETED
- `infra/studio_batch_templates.py` — DELETED
- `infra/studio_batch_streamer.py` — DELETED
- `CLAUDE.md` — version v44.0 → v45.0 + 3 invariants added
- `.lingwen/architecture.yml` — version + invariants I064-I066 added

### C4 details (guards + handoff)

**Files created**:
- `tests/test_phase47_lingwen_studio_batch.py` (20+ regression guards)
- `docs/superpowers/handoffs/2026-09-11-phase-47-p3-archdebt-studio-batch-handoff.md`

**Files modified**:
- `CLAUDE.md` — version bump entry + handoff link
- `MEMORY.md` — Phase 47 entry + 4 lessons
- Memory topic file: `phase-47-p3-archdebt-studio-batch.md`

## Validation gates (Phase 47 acceptance)

1. ✅ ruff clean on changed Python files
2. ✅ 3 packages importable via `uv sync`
3. ✅ All 11 anchored imports + 1 wildcard + 25 monkeypatch paths migrated (audit grep clean)
4. ✅ `pytest apps/studio_api/tests/test_studio_batch_*.py` passes (5 test files updated)
5. ✅ `pytest tests/infra/test_studio_batch_*.py` passes (4 test files moved)
6. ✅ `pytest tests/dashboard/test_studio_batch_endpoints.py` passes
7. ✅ `pytest infra/studio/` passes (wildcard replacement works)
8. ✅ Phase 36-46 guards preserved (11 prior-phase guard files)
9. ✅ New Phase 47 guards (20+ tests)
10. ✅ Production audit: `grep -rn "infra\.studio_batch_\(runner\|templates\|streamer\)\b" infra/ apps/ packages/ tests/ tools/` → 0 hits
11. ✅ Test audit: same grep in tests/ → 0 hits

## Risks & mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| 25 monkeypatch paths missed in C2 | MEDIUM | Use sed with `\b` boundary + comprehensive anchored-grep audit |
| runner → streamer workspace dep creates circular potential | LOW | Only runner → streamer (one-way), no circular |
| 3 package test MOVEs miss 1 file | LOW | Pre-spec 9-pattern audit verified 6 test files (3 per package) |
| Spec drift 13/3/3 vs 10/3/3 | LOW | Pre-spec fresh-run grep captured actual counts (13/3/2) |
| Doc-only mentions accidentally migrated | LOW | Preserve in C2 commit message + commit-blame protection |

## Carryover closure

| Item | Status |
|------|--------|
| P3-ARCHDEBT 10/9+1 (filter MERGE) | ✅ Phase 46 |
| **P3-ARCHDEBT 11/10+1 (studio_batch_* 3-module batch)** | 🟡 Phase 47 (this phase) |
| P3-ARCHDEBT remaining (Phase 48+) | 🟡 full_check_report / memory_service / types / etc. |

**Next-actionable after Phase 47**: Phase 48 = `infra/full_check_report` (4 consumers, 3 deps cross-cutting `lingwen_quality` x2 — likely NOT-LEAF).

## References

- ARCHDEBT-CANDIDATES.md "studio_batch_*" (combined batch recommendation)
- Phase 34 (lingwen-got) — multi-module migration template
- Phase 45 (lingwen-utilities BATCH) — multi-module batch template (4 LEAF, similar)
- Phase 46 (filter MERGE) — different pattern (no new package)
- Phase 40a (studio_registry) — provides `lingwen_studio_registry` dep
- v16.5 #N.6 (async surface) — relevant for studio routes

---

> **Validation reminder (Phase 41 mini lesson #1)**: every claim in this spec
> (3 modules, 1041 LOC, 13/3/2 consumer files, 25 monkeypatch paths, 3 invariants)
> was verified by fresh-run grep on 2026-09-11 BEFORE writing this spec.
> No stale-count claims.