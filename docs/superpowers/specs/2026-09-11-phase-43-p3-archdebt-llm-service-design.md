# Phase 43 P3-ARCHDEBT (llm_service) — lingwen-llm-service Design Spec

> **Phase**: 43 (P3-ARCHDEBT 7/6+1 — continues from Phase 42's `project_init` closure)
> **Branch**: `phase-43-p3-archdebt-llm-service`
> **Date**: 2026-09-11
> **Rank**: ARCHDEBT-CANDIDATES.md #2 (shim cleanup, 9 consumers)
> **Template**: Phase 39 (logging_config) — half-migration LEAF-ish cleanup pattern

## Goal

Move `infra/llm_service.py` (309 LOC, 5 public symbols, NOT-LEAF 2 deps) into a standalone
canonical package `packages/lingwen-llm-service/`, deleting the `infra/` shim and adding
**invariant I057** to forbid reintroduction. Continues the P3-ARCHDEBT pattern established
across Phases 36-42.

## Background — Pre-Spec Audit (2026-09-11 fresh-run)

### 9-pattern audit (N.14 lesson 1, 18th occurrence — wildcard check explicit)

| # | Pattern | Finding | Action |
|---|---------|---------|--------|
| 1 | Literal dotted-path imports `from infra.llm_service import X` | 6 sites | Migrate all 6 |
| 2 | Indented/function-body imports `^[[:space:]]*from infra.llm_service` | 0 sites | n/a |
| 3 | Relative imports `from .llm_service` | 0 sites | n/a |
| 4 | Filesystem path literals `infra/llm_service.py` | 0 sites (spec is in code, not paths) | n/a |
| 5 | Wildcard `from infra.llm_service import *` | **1 site: `infra/core/__init__.py:5`** | Migrate wildcard |
| 6 | `monkeypatch.setattr("infra.llm_service.X", ...)` | 1 site: `tests/infra/test_creator_agent.py:140` | Migrate path |
| 7 | `import infra.llm_service` (plain, used for side effects) | 2 sites: `tests/tools/conftest.py:18`, `tests/test_inspector_repairer.py:254` | Migrate both |
| 8 | Doc comments referencing old path | 8 sites (lingwen-llm/port_adapter, lingwen-shared/ports/storage, tests/test_llm_dto, infra/world_db/agent_extractors, infra/llm_benchmarks/providers, tooling/*, packages/lingwen-storage/sqlite_storage_adapter) | Update DP-02 doc refs |
| 9 | Prior-phase guard's hardcoded representative files | `tooling/hygiene/tests/test_no_concrete_llm_import.py:75` greps `from infra.llm_service import.*LLMService` | Update grep pattern |

### Real external consumers (6 sites, verified by fresh grep 2026-09-11)

| # | File | Line | Pattern | Migration |
|---|------|------|---------|-----------|
| 1 | `infra/core/__init__.py` | 5 | wildcard `from infra.llm_service import *` | `from lingwen_llm_service import *` |
| 2 | `infra/world_db/agent_extractors.py` | 154-163 | `_default_llm_service()` returns `LLMServiceAdapter()` (relies on factory registration at process start) | No code change needed (function name unchanged) — but depends on `infra/core/__init__.py` wildcard load |
| 3 | `tests/infra/test_creator_agent.py` | 140 | `monkeypatch.setattr("infra.llm_service.LLMService.execute_stream", ...)` | `monkeypatch.setattr("lingwen_llm_service.LLMService.execute_stream", ...)` |
| 4 | `tests/infra/test_llm_service.py` | 26, 42, 55 | `from infra.llm_service import LLMService` (3 sites) | **MOVE FILE** → `packages/lingwen-llm-service/tests/test_service.py` |
| 5 | `tests/test_inspector_repairer.py` | 254 | `import infra.llm_service as llm_mod` | `import lingwen_llm_service as llm_mod` |
| 6 | `tests/tools/conftest.py` | 18 | `import infra.llm_service  # noqa: F401` | `import lingwen_llm_service  # noqa: F401` |

### Tooling updates (2 files, must update to recognize new path)

| # | File | Update |
|---|------|--------|
| 1 | `tooling/hygiene/check_no_grimp_evasion.py` | Regex `r"^\s*from\s+infra\.llm_service\s+import\s+"` → `r"^\s*from\s+(?:infra\.llm_service\|lingwen_llm_service)\s+import\s+"`. Plus string-concat + PEP 562 patterns + error messages. |
| 2 | `tooling/hygiene/tests/test_no_concrete_llm_import.py` | (a) `test_dp02_contract_targets_correct_modules`: `forbidden_modules` must include both `infra.llm_service` AND `lingwen_llm_service`. (b) `test_no_concrete_llm_in_business_code`: grep pattern must match `from lingwen_llm_service import.*LLMService`. (c) `test_no_infra_llm_service_imports_in_tools_with_whitelist`: pattern must include both forms. (d) Docstring references. |
| 3 | `pyproject.toml` | DP-02 contract `no_concrete_llm_service_in_business_code.forbidden_modules`: add `lingwen_llm_service` to existing list. |

### Doc-only mentions (8 files, comments only — no migration needed)

These reference `infra.llm_service` in docstrings/comments but never import. Optional cleanup:

- `infra/llm_benchmarks/providers.py` (doc-comment only, MockLLMService is local class)
- `packages/lingwen-llm/src/lingwen_llm/port_adapter.py` (architectural invariant docstring — must NOT import, references the forbidden module by name intentionally)
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py` (doc-comment only, already canonical)
- `packages/lingwen-shared/src/lingwen_shared/ports/storage.py` (comment-only)
- `packages/lingwen-shared/tests/test_llm_dto.py` (docstring only)
- `packages/lingwen-storage/src/lingwen_storage/sqlite_storage_adapter.py:220` (comment-only)
- `infra/world_db/agent_extractors.py:32-33, 159-161` (doc-comment references)

These are **left untouched** — they describe architectural contracts and historical context.
The tooling regression guards (Phase 36-42) ensure `infra.llm_service` doesn't reappear
in code, but doc-comments are exempt (commit-blame protection).

## Architecture

### Package layout (3 sub-modules per Phase 39 logging_config template)

```
packages/lingwen-llm-service/
├── pyproject.toml                                  # workspace member declaration
├── src/
│   └── lingwen_llm_service/
│       ├── __init__.py                             # public re-exports (5 symbols)
│       ├── service.py                              # LLMService class (~240 LOC)
│       └── factory.py                              # factory registration + helpers (~70 LOC)
└── tests/
    └── test_service.py                             # 3 tests moved from tests/infra/test_llm_service.py
```

### Public surface (5 symbols)

| Symbol | Source location | Module |
|--------|----------------|--------|
| `LLMService` (class) | service.py | lingwen_llm_service |
| `LLMTask` (re-export) | from lingwen_shared.contracts.python.llm | __init__.py |
| `TaskType` (re-export) | from lingwen_shared.contracts.python.llm | __init__.py |
| `get_llm_service()` | factory.py | lingwen_llm_service |
| `create_task()` | factory.py | lingwen_llm_service |

### Workspace deps (NOT-LEAF, 2 deps)

```toml
[project]
dependencies = [
    "lingwen-shared",
    "lingwen-llm",
]
```

Both packages already exist (Phase 34 lingwen-llm + Phase 30 lingwen-shared) and are stable.

### DP-02 contract preservation (CRITICAL)

The current module-load factory registration (lines 294-309 of `infra/llm_service.py`):

```python
# v16.5: Register LLMService.get as the default factory for LLMServiceAdapter.
# This eliminates the v16.4 grimp-evasion hack in port_adapter.py (which used
# string-concat to hide ``importlib.import_module("infra.llm_service")``).
#
# Side effect on import: importing ``infra.llm_service`` anywhere in the process
# wires up ``LLMServiceAdapter()`` default behavior.
from lingwen_llm.port_adapter import set_default_factory


def _default_service_factory() -> "LLMService":
    """Factory returning the LLMService singleton (lazy)."""
    return LLMService.get()


set_default_factory(_default_service_factory)
```

Must be preserved **verbatim** in `lingwen_llm_service.factory`. The factory call
(`set_default_factory(_default_service_factory)`) must execute at module load time
of `lingwen_llm_service/__init__.py` so that:

1. `infra/core/__init__.py:5` wildcard `from lingwen_llm_service import *` triggers factory registration
2. `tests/tools/conftest.py:18` `import lingwen_llm_service` triggers factory registration for test bootstrap
3. `infra/world_db/agent_extractors.py:_default_llm_service()` works in production (relies on `infra/core/__init__.py` being loaded by `create_app()` startup)

### Forbidden pattern (DP-02)

Business code (`lingwen_creator`, `apps/`) MUST NOT import the concrete LLMService class.
The only allowed touchpoint is `LLMServiceAdapter` from `lingwen_llm.port_adapter`. After
migration, the DP-02 contract must include BOTH old and new paths as forbidden.

```toml
[[tool.importlinter.contracts]]
name = "no_concrete_llm_service_in_business_code"
type = "forbidden"
source_modules = ["lingwen_creator", "apps"]
forbidden_modules = ["infra.llm_service", "lingwen_llm_service"]
```

### Invariant I057

```
I057 | `packages/lingwen-llm-service/` is LLM service (LLMService class + factory
       registration + get_llm_service/create_task helpers) unique canonical
       package; `infra.llm_service.*` paths forbidden (P3-ARCHDEBT 7/6+1 Phase 43)
```

## Atomic commits (6 total)

| Commit | Type | Scope | Notes |
|--------|------|-------|-------|
| **C0** | `docs(phase-43)` | spec | This document |
| **C1** | `feat(packages)` | scaffold `packages/lingwen-llm-service/` | 3 sub-modules + pyproject + workspace register |
| **C2** | `refactor(consumers)` | bulk migrate 6 sites | Single commit per Phase 37 lesson |
| **C3** | `refactor(tooling)` | hygiene regex + DP-02 contract test | Both tooling files + pyproject DP-02 update |
| **C4** | `chore(infra)` | delete `infra/llm_service.py` + I057 + version | v40.0 → v41.0 |
| **C5** | `test(phase-43)` | regression guards + handoff + CLAUDE.md + MEMORY | 10+ guards + topic file |

### C1 details (scaffold)

**Files created**:
- `packages/lingwen-llm-service/pyproject.toml` (workspace member + deps)
- `packages/lingwen-llm-service/src/lingwen_llm_service/__init__.py` (re-exports + factory registration call)
- `packages/lingwen-llm-service/src/lingwen_llm_service/service.py` (LLMService class)
- `packages/lingwen-llm-service/src/lingwen_llm_service/factory.py` (`get_llm_service` + `create_task` + `_default_service_factory` + `set_default_factory` call)

**Files modified**:
- Root `pyproject.toml` — add `packages/lingwen-llm-service` to `[tool.uv.workspace]` members (per Phase 34 lesson: workspace member declaration must precede `uv sync`)

**`__init__.py` content**:
```python
"""lingwen-llm-service — canonical LLM service package.

Phase 43 P3-ARCHDEBT: relocated from infra/llm_service.py (309 LOC).
NOT-LEAF (depends on lingwen_shared + lingwen_llm).
DP-02 contract: business code MUST NOT import LLMService directly — use
LLMServiceAdapter from lingwen_llm.port_adapter instead.
"""

from lingwen_llm_service.factory import (
    _default_service_factory,  # noqa: F401 — used in set_default_factory() below
    create_task,
    get_llm_service,
)
from lingwen_llm_service.service import LLMService
from lingwen_shared.contracts.python.llm import LLMTask, TaskType

# Module-load factory registration (preserves v16.5 DP-02 contract)
from lingwen_llm.port_adapter import set_default_factory

set_default_factory(_default_service_factory)

__all__ = [
    "LLMService",
    "LLMTask",
    "TaskType",
    "get_llm_service",
    "create_task",
]
```

### C2 details (bulk migrate 6 sites)

**Single bulk commit** (per Phase 37 lesson — 86 consumers in single C2 was safe):

```
refactor(consumers): migrate 6 sites from infra.llm_service to lingwen_llm_service

Phase 43 P3-ARCHDEBT (lingwen-llm-service):

  infra/core/__init__.py:5                  wildcard → from lingwen_llm_service import *
  tests/infra/test_creator_agent.py:140     monkeypatch path updated
  tests/infra/test_llm_service.py           MOVED → packages/lingwen-llm-service/tests/test_service.py
  tests/test_inspector_repairer.py:254      import infra.llm_service → import lingwen_llm_service
  tests/tools/conftest.py:18               import infra.llm_service → import lingwen_llm_service

infra/world_db/agent_extractors.py no code change needed — relies on
infra/core/__init__.py wildcard load to trigger factory registration.
```

### C3 details (tooling + DP-02 contract)

**Files modified**:
- `tooling/hygiene/check_no_grimp_evasion.py`:
  - `check_static_import`: regex `r"^\s*from\s+infra\.llm_service\s+import\s+"` → `r"^\s*from\s+(?:infra\.llm_service|lingwen_llm_service)\s+import\s+"`
  - `check_string_concat_evasion`: error message updated to mention both modules
  - `check_pep562_re_export`: regex `r"infra\s*\.\s*llm_service"` → `r"(?:infra\s*\.\s*llm_service|lingwen_llm_service)"` + error message update
  - Module docstring update

- `tooling/hygiene/tests/test_no_concrete_llm_import.py`:
  - Module docstring: add lingwen_llm_service to description
  - `test_dp02_contract_targets_correct_modules`: assert both `infra.llm_service` AND `lingwen_llm_service` in `forbidden_modules`
  - `test_no_concrete_llm_in_business_code`: grep pattern `from infra.llm_service import.*LLMService` → `from (?:infra.llm_service|lingwen_llm_service) import.*LLMService`
  - `test_no_infra_llm_service_imports_in_tools_with_whitelist`: regex `r"^\s*(?:from\s+infra\.llm_service|import\s+infra\.llm_service)\b"` → `r"^\s*(?:from\s+(?:infra\.llm_service|lingwen_llm_service)|import\s+(?:infra\.llm_service|lingwen_llm_service))\b"`. Rename test → `test_no_concrete_llm_imports_in_tools_with_whitelist`. Update error message.

- `pyproject.toml`:
  - DP-02 contract `forbidden_modules`: `[infra.llm_service]` → `[infra.llm_service, lingwen_llm_service]`

### C4 details (delete + invariant)

**Files modified**:
- `infra/llm_service.py` — DELETED
- `CLAUDE.md` — version v40.0 → v41.0 + invariant I057 added to architecture invariants table

**Commit message**:
```
chore(infra): delete infra/llm_service.py + I057 invariant (Phase 43 P3-ARCHDEBT)

  - infra/llm_service.py (309 LOC) DELETED
  - All 6 consumers migrated to lingwen_llm_service (C2)
  - All 2 tooling sites updated (C3)
  - DP-02 contract preserves both old + new paths in forbidden_modules

I057 | `packages/lingwen-llm-service/` is LLM service unique canonical
      package; `infra.llm_service.*` paths forbidden (P3-ARCHDEBT 7/6+1)

Version: v40.0 → v41.0
```

### C5 details (guards + handoff + doc-sync)

**Files created**:
- `tests/test_phase43_lingwen_llm_service.py` (10 regression guards, per Phase 40b pattern)
- `docs/superpowers/handoffs/2026-09-11-phase-43-p3-archdebt-llm-service-handoff.md`

**Files modified**:
- `CLAUDE.md` — version bump entry + handoff link
- `MEMORY.md` — Phase 43 entry + 4 lessons
- Memory topic file: `phase-43-p3-archdebt-llm-service.md`

**Phase 43 guard tests** (10+ tests):

| # | Test name | Asserts |
|---|-----------|---------|
| 1 | `test_infra_llm_service_module_deleted` | `infra/llm_service.py` does NOT exist |
| 2 | `test_lingwen_llm_service_module_importable` | `import lingwen_llm_service` works |
| 3 | `test_lingwen_llm_service_has_5_public_symbols` | `__all__ == ["LLMService", "LLMTask", "TaskType", "get_llm_service", "create_task"]` (per Phase 42 lesson #4) |
| 4 | `test_dp02_contract_forbids_both_paths` | pyproject.toml DP-02 `forbidden_modules` includes both old + new |
| 5 | `test_factory_registered_at_module_load` | After `import lingwen_llm_service`, `lingwen_llm.port_adapter.get_default_factory()` returns `_default_service_factory` |
| 6 | `test_production_audit_no_infra_llm_service_imports` | grep `infra.llm_service` in production code → 0 hits |
| 7 | `test_test_audit_no_infra_llm_service_imports` | grep `infra.llm_service` in test code → 0 hits |
| 8 | `test_hygiene_check_updated_for_new_path` | `tooling/hygiene/check_no_grimp_evasion.py` regex updated (no `infra.llm_service` literal in regex) |
| 9 | `test_dp02_contract_test_updated_for_new_path` | `tooling/hygiene/tests/test_no_concrete_llm_import.py` covers both paths |
| 10 | `test_invariant_057_in_arch_yml` | `.lingwen/architecture.yml` includes I057 (TODO Phase 43: add) |
| 11 | `test_6_prior_phase_guards_preserved` | All Phase 36-42 guards still pass |
| 12 | `test_workspace_deps_correct` | `packages/lingwen-llm-service/pyproject.toml` deps include `lingwen-shared` + `lingwen-llm` |

## Validation gates (Phase 43 acceptance)

1. ✅ ruff clean on changed Python files
2. ✅ `pytest packages/lingwen-llm-service/tests/` passes (3 tests moved from test_llm_service.py)
3. ✅ `pytest tests/infra/test_creator_agent.py tests/infra/test_llm_service.py tests/test_inspector_repairer.py tests/tools/` passes
4. ✅ `pytest infra/world_db/` passes (relies on factory registration via infra/core/__init__.py wildcard)
5. ✅ `pytest tests/infra/` passes (uses monkeypatch on lingwen_llm_service.LLMService)
6. ✅ `pytest tooling/hygiene/` passes (check_no_grimp_evasion + test_no_concrete_llm_import)
7. ✅ `lint-imports` (importlinter) passes — DP-02 contract honors both old + new paths as forbidden
8. ✅ Phase 36-42 guards preserved (7 prior-phase guard files)
9. ✅ New Phase 43 guards (10 tests)
10. ✅ Production audit: `grep -rn "infra.llm_service" infra/ apps/ packages/` → 0 hits
11. ✅ Test audit: `grep -rn "infra.llm_service" tests/` → 0 hits

## Risks & mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| DP-02 factory registration breaks (module load order changes) | MEDIUM | C5 test #5 verifies factory registered; explicit `set_default_factory(_default_service_factory)` in `__init__.py` |
| 6 consumer migrations miss a site in C2 (Phase 42 lesson #1) | MEDIUM | Pre-spec 9-pattern audit explicit; fresh-run grep verified 6 sites |
| Tooling regex update breaks existing check | LOW | C5 tests #8 + #9 verify regex updated; existing tests still pass |
| `__all__` count spec drift (Phase 42 lesson #4) | MEDIUM | Pre-spec audit verified 5 public symbols; C5 test #3 enforces `len(__all__) == 5` |
| Workspace member declaration order (Phase 34 lesson) | LOW | C1 modifies root `pyproject.toml [tool.uv.workspace]` BEFORE C2 (per Phase 34 lesson) |
| Stale doc-comment references to `infra.llm_service` left behind | LOW | 8 doc-only mentions audited; intentionally preserved (commit-blame protection); C5 test #6 excludes comments from grep |
| `infra/world_db/agent_extractors.py` factory registration via import side-effect | MEDIUM | Production test infra/world_db/ + C5 test #5 verifies factory chain |
| `infra/core/__init__.py` wildcard re-export of LLMService + LLMTask + TaskType + get_llm_service + create_task | LOW | `__all__` in lingwen_llm_service controls what's exported; wildcard imports all 5 |
| Pre-existing E741 ruff errors from Phase 35 baseline | n/a | C4 unchanged (no new ruff findings) |

## Carryover closure

| Item | Status |
|------|--------|
| P3-ARCHDEBT 5/5 (errors/paths/project_config/logging_config/studio_registry) | ✅ Phase 36-40b |
| P3-ARCHDEBT 6/5+1 (project_init) | ✅ Phase 42 |
| **P3-ARCHDEBT 7/6+1 (llm_service)** | 🟡 Phase 43 (this phase) |
| P3-ARCHDEBT remaining (Phase 44-46 candidates) | 🟡 known backlog (prose_calibration / cache / filter) |

**Next-actionable after Phase 43**: Phase 44 = `infra/prose_calibration` (TRUE LEAF, 6 consumers, 191 LOC, 0 deps).

## References

- ARCHDEBT-CANDIDATES.md #2
- Phase 36 (errors pilot) — first P3-ARCHDEBT
- Phase 39 (logging_config) — template for this phase (5-commit pattern, LEAF-ish cleanup)
- Phase 42 (project_init) — most recent P3-ARCHDEBT (wildcard-in-__init__.py lesson, C3 FULL DELETE decision tree)
- DP-02 architectural invariant (LLMServiceAdapter must NOT touch concrete service)
- v16.5 #1 / #N.6 / #N.12 (factory pattern, async surface, grimp-evasion removal)

---

> **Validation reminder (Phase 41 mini lesson #1)**: every claim in this spec
> (6 consumers, 5 public symbols, 309 LOC, 2 tooling sites) was verified by fresh-run
> grep on 2026-09-11 BEFORE writing this spec. No stale-count claims.