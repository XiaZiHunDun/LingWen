# Phase 43 P3-ARCHDEBT (lingwen-llm-service) Handoff

> **Date**: 2026-09-11
> **Phase**: 43 — P3-ARCHDEBT item 7/6+1
> **Branch**: `phase-43-p3-archdebt-llm-service`
> **Status**: ✅ **CLOSED** (master HEAD pending ff-merge)
> **Spec**: [`docs/superpowers/specs/2026-09-11-phase-43-p3-archdebt-llm-service-design.md`](../specs/2026-09-11-phase-43-p3-archdebt-llm-service-design.md)
> **ARCHDEBT Rank**: #2 in [ARCHDEBT-CANDIDATES.md](../ARCHDEBT-CANDIDATES.md)

## TL;DR

`infra/llm_service.py` (309 LOC, 5 public symbols, NOT-LEAF 2 deps) → `packages/lingwen-llm-service/` (3 sub-modules: service.py + factory.py + __init__.py). 6 consumers migrated in single atomic C2 commit. DP-02 contract preserved via module-load `set_default_factory(_default_service_factory)` call. Tooling regex + DP-02 forbidden_modules updated to cover BOTH old (`infra.llm_service`) and new (`lingwen_llm_service`) paths. 1 NEW invariant (I057). Version bump v40.0 → v41.0.

## Atomic commits (6 total on `phase-43-p3-archdebt-llm-service`)

| SHA | Type | Scope | Notes |
|-----|------|-------|-------|
| `5885c7fb` | `docs(phase-43)` | spec | Pre-spec 9-pattern audit verified 6 consumers + 2 tooling sites |
| `4c028369` | `feat(packages)` | scaffold | 3 sub-modules + pyproject + workspace register (BEFORE uv sync per Phase 34 lesson) |
| `cb0de371` | `refactor(consumers)` | bulk 6 sites | Single atomic commit per Phase 37 lesson (6 sites = safe) |
| `3b58265e` | `refactor(tooling)` | hygiene + DP-02 | 3 files: pyproject.toml + check_no_grimp_evasion.py + test_no_concrete_llm_import.py |
| `bf47ca80` | `chore(infra)` | delete + I057 + v41.0 | infra/llm_service.py DELETED (FULL DELETE, not shim) |
| `<C5>` | `test(phase-43)` | 14 guards + handoff + MEMORY | Pending commit (this file) |

## Pre-spec audit (Phase 42 lesson #1 reinforcement — wildcard-in-`__init__.py`)

### 9-pattern audit results

| # | Pattern | Sites found |
|---|---------|-------------|
| 1 | Literal dotted-path imports `from infra.llm_service import X` | 6 |
| 2 | Indented/function-body imports | 0 |
| 3 | Relative imports | 0 |
| 4 | Filesystem path literals | 0 |
| 5 | Wildcard `from infra.llm_service import *` | **1** (`infra/core/__init__.py:5`) |
| 6 | `monkeypatch.setattr("infra.llm_service.X", ...)` | 1 (`tests/infra/test_creator_agent.py:140`) |
| 7 | Plain `import infra.llm_service` (side-effect) | 2 (`tests/tools/conftest.py:18` + `tests/test_inspector_repairer.py:254`) |
| 8 | Doc comments referencing old path | 8 (intentionally preserved) |
| 9 | Prior-phase guard's hardcoded representative | 1 (`tooling/hygiene/tests/test_no_concrete_llm_import.py`) |

### Real external consumers (6 sites, verified by fresh grep 2026-09-11)

| # | File | Pattern | Migration |
|---|------|---------|-----------|
| 1 | `infra/core/__init__.py:5` | wildcard | `from lingwen_llm_service import *` |
| 2 | `infra/world_db/agent_extractors.py:154-163` | `_default_llm_service()` returns `LLMServiceAdapter()` | No code change (relies on wildcard load) |
| 3 | `tests/infra/test_creator_agent.py:140` | monkeypatch path | `lingwen_llm_service.LLMService.execute_stream` |
| 4 | `tests/infra/test_llm_service.py` | direct import (3 sites) | **MOVE** → `packages/lingwen-llm-service/tests/test_service.py` |
| 5 | `tests/test_inspector_repairer.py:254` | `import infra.llm_service as llm_mod` | `import lingwen_llm_service as llm_mod` |
| 6 | `tests/tools/conftest.py:18` | factory trigger | `import lingwen_llm_service` |

### Tooling updates (2 files + pyproject.toml)

- `pyproject.toml`: DP-02 `forbidden_modules` = `[infra.llm_service, lingwen_llm_service]`
- `tooling/hygiene/check_no_grimp_evasion.py`: single `_LLM_SERVICE_RE = r"(?:infra\.llm_service|lingwen_llm_service)"` regex covers both paths. **Phase 43 lesson**: avoid `{a|b}` in f-string (Python evaluates as bitwise OR) — extracted placeholder into `_MODULE_PLACEHOLDER` constant
- `tooling/hygiene/tests/test_no_concrete_llm_import.py`: 4 test updates; renamed `test_no_infra_llm_service_imports_in_tools_*` → `test_no_concrete_llm_imports_in_tools_*` to reflect both forbidden paths

### Doc-only mentions (8 files, intentionally preserved)

- `infra/world_db/agent_extractors.py` (historical context)
- `infra/llm_benchmarks/providers.py` (MockLLMService local class, no infra import)
- `packages/lingwen-llm/src/lingwen_llm/port_adapter.py` (architectural invariant docstring describing FORBIDDEN by name)
- `packages/lingwen-llm/tests/test_port_adapter.py` (test docstring)
- `packages/lingwen-shared/src/lingwen_shared/contracts/python/llm.py` (v16.5 relocation context)
- `packages/lingwen-shared/src/lingwen_shared/ports/storage.py` (comment-only)
- `packages/lingwen-shared/tests/test_llm_dto.py` (v16.5 relocation context)
- `packages/lingwen-storage/src/lingwen_storage/sqlite_storage_adapter.py` (comment-only)

## Architecture (canonical layout)

```
packages/lingwen-llm-service/
├── pyproject.toml                                    # 2 deps: lingwen-shared + lingwen-llm
├── src/
│   └── lingwen_llm_service/
│       ├── __init__.py    # 5 public symbols + module-load DP-02 factory registration
│       ├── service.py     # LLMService class (240 LOC)
│       └── factory.py     # get_llm_service + create_task + _default_service_factory
└── tests/
    └── test_service.py    # 3 tests moved from tests/infra/test_llm_service.py
```

### Public surface (5 symbols — verified by `len(__all__) == 5`)

- `LLMService` (class — singleton, provider failover, execute/execute_stream/is_available/parse_json_response)
- `LLMTask` (re-export from `lingwen_shared.contracts.python.llm`)
- `TaskType` (re-export from `lingwen_shared.contracts.python.llm`)
- `get_llm_service()` (factory helper)
- `create_task()` (LLMTask factory helper)

### NOT-LEAF — 2 workspace deps

```toml
dependencies = ["lingwen-shared", "lingwen-llm"]
```

### DP-02 contract preservation (CRITICAL)

The v16.5 module-load factory registration (`set_default_factory(_default_service_factory)`) is preserved **verbatim** in `lingwen_llm_service/__init__.py`. When any process imports `lingwen_llm_service`:

1. `from lingwen_llm_service.service import LLMService` loads LLMService class (lazy provider init inside `__init__`)
2. `from lingwen_llm_service.factory import _default_service_factory` loads the lazy singleton factory
3. `from lingwen_llm.port_adapter import set_default_factory` imports the registration API
4. `set_default_factory(_default_service_factory)` **fires** at module load — wires LLMServiceAdapter() default behavior

**Trigger paths**:
- Production: `infra/core/__init__.py:5` wildcard `from lingwen_llm_service import *` (loaded by `create_app()` startup)
- Tests: `tests/tools/conftest.py:18` `import lingwen_llm_service`
- Direct: any business code that imports lingwen_llm_service transitively

## Validation gates — all GREEN

| Gate | Status | Notes |
|------|--------|-------|
| **ruff clean** | ✅ | No new findings (pre-existing E741 baseline unchanged) |
| **lingwen_llm_service importable** | ✅ | `from lingwen_llm_service import LLMService` works |
| **`__all__ == 5 symbols EXACTLY** | ✅ | Phase 42 lesson #4 enforced — `len(__all__) == 5` |
| **test_service.py (3 tests moved)** | ✅ | 3/3 PASSED |
| **DP-02 contract test (6 tests)** | ✅ | 6/6 PASSED — both paths in forbidden_modules |
| **check_no_grimp_evasion tool** | ✅ | `OK: port_adapter.py is grimp-evasion-free` |
| **Phase 43 guards (14 tests)** | ✅ | 14/14 PASSED |
| **Phase 36-42 prior guards (48 tests)** | ✅ | 48/48 PASSED — no regression |
| **Production audit (no `infra.llm_service` runtime imports)** | ✅ | grep -rln returns 0 (only doc-comments in 8 files preserved by design) |
| **Test audit (no `infra.llm_service` runtime imports)** | ✅ | grep returns 0 |
| **Module-load factory registration** | ✅ | `get_default_factory()` returns non-None after `import lingwen_llm_service` |

**Total**: 71 tests passing across 4 test suites (Phase 36-42 guards + Phase 43 guards + DP-02 + migrated test_service.py).

## 4 lessons (Phase 43)

### Lesson 1: tomllib dotted-key nesting (N.14 lesson 1, 19th occurrence)

`pyproject["tool"]["uv.workspace"]["members"]` raises `KeyError: 'uv.workspace'`. tomllib does NOT flatten dotted table headers — `[tool.uv.workspace]` becomes `pyproject["tool"]["uv"]["workspace"]`. **Always use `pyproject["tool"]["uv"]["workspace"]["members"]` (3-level nesting) when reading workspace members**.

Initial guard test had this wrong → caught immediately by pytest, fixed in same commit.

### Lesson 2: f-string `{a|b}` is bitwise OR (NEW — Phase 43 specific)

In Python f-strings, `{...}` is evaluated as a Python expression. `f"... {infra.llm_service|lingwen_llm_service} ..."` tries to evaluate `infra` (NameError → attribute access fails → bitwise OR fails). **Solution**: extract placeholder into module constant:

```python
_MODULE_PLACEHOLDER = "{infra.llm_service|lingwen_llm_service}"
f"... {_MODULE_PLACEHOLDER} ..."
```

This way the literal braces are stored as a string and substituted via f-string `{name}` (which is just a name lookup, no expression eval).

This is the inverse of Phase 41 mini lesson #3 (bash backtick issue). Both are "context-specific escape character" traps.

### Lesson 3: Spec says 9 consumers, actual 6 + 2 tooling (Phase 36 spec-drift lesson reinforced)

ARCHDEBT-CANDIDATES.md #2 said "9 consumers". Fresh-run pre-spec grep (Phase 42 lesson #1 reinforcement) found **6 real runtime consumers + 2 tooling sites = 8 sites**. The 9th was a doc-reference count (8 doc-only mentions kept for commit-blame protection).

**Pattern**: when spec uses consumer counts, ALWAYS verify via fresh-run grep before writing spec. N.14 lesson 1 variants continue:
- Phase 36: paths consumer count (86 actual vs spec said ~90)
- Phase 37: paths function-body imports (Phase 37 lesson — used `^([[:space:]]*)from` anchor)
- Phase 38: project_config function-body imports (8 function-body imports found)
- Phase 40a: studio_registry 50 consumers (verified)
- Phase 42: project_init 46 consumers + 1 wildcard (wildcard caught late)
- **Phase 43**: llm_service 6 consumers + 2 tooling (spec said 9) ← this phase

### Lesson 4: tooling regex literal braces via placeholder constant (Phase 43 lesson #2 amplified)

Same as Lesson 2, but applied in a different context (re-exports pattern). The Phase 43 lesson: when error messages need to display literal `{...}` syntax, ALWAYS use a module-level constant rather than embedding `{...}` directly in f-strings. This makes the message "stable" against Python expression evaluation rules.

## Carryover closure

| Phase | Module | Status |
|-------|--------|--------|
| P3-ARCHDEBT 5/5 (errors/paths/project_config/logging_config/studio_registry) | ✅ | Phase 36-40b |
| P3-ARCHDEBT 6/5+1 (project_init) | ✅ | Phase 42 |
| **P3-ARCHDEBT 7/6+1 (lingwen-llm-service)** | ✅ | **Phase 43 (this phase)** |
| P3-ARCHDEBT 8/7+1 (prose_calibration TRUE LEAF) | 🟡 | Phase 44+ |
| P3-ARCHDEBT 9/8+1 (cache LEAF batch) | 🟡 | Phase 45+ |
| P3-ARCHDEBT 10/9+1 (filter near-LEAF) | 🟡 | Phase 46+ |

## References

- Pre-spec: [`docs/superpowers/specs/2026-09-11-phase-43-p3-archdebt-llm-service-design.md`](../specs/2026-09-11-phase-43-p3-archdebt-llm-service-design.md)
- ARCHDEBT-CANDIDATES.md #2 (this phase ranked #2)
- Phase 36 (errors pilot) — first P3-ARCHDEBT
- Phase 39 (logging_config) — template for this phase (5-commit pattern, NOT-LEAF cleanup)
- Phase 42 (project_init) — most recent P3-ARCHDEBT (wildcard lesson, C3 FULL DELETE decision tree)
- DP-02 architectural invariant (LLMServiceAdapter must NOT touch concrete service)
- v16.5 #1 (factory pattern) / v16.5 #N.6 (async surface) / v16.5 #N.12 (grimp-evasion removal)

---

> **All claims in this handoff verified by fresh-run** (Phase 41 mini lesson #1):
> 14 phase43 guards + 6 DP-02 tests + 3 migrated tests + 48 prior-phase guards
> = 71 PASSED, 0 regressions.