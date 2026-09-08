# Phase 39 — P3-ARCHDEBT (logging_config) design

> **Date**: 2026-09-08
> **Author**: Claude (主控调度)
> **Branch**: `phase-39-p3-archdebt-logging-config`
> **Master HEAD (start)**: `f36b0814` (Phase 38 ff-merge point)
> **Version**: v37.0 → **v38.0**
> **Invariant**: #54 NEW
> **Pattern**: Phase 38 P3-ARCHDEBT (project_config) adapted for LEAF package

## Why

P3-ARCHDEBT item **4/5** — `infra/logging_config.py` (59 行, 3 public symbols: `StructuredFormatter` 类 + `setup_logging` 函数 + `logger` 模块级实例) → `packages/lingwen-logging-config/`。

- **Phase 38 → Phase 39 差异**:
  - Phase 38 (project_config): 26 consumer sites, 1 module 170 行, 2 symbols, 7 function-body imports, 5 test consumers
  - **Phase 39 (logging_config)**: **8 consumer sites**, 1 module **59 行**, **3 symbols** (含 module-level `logger`), **0 function-body**, **0 test consumers**, **0 path literals**
- **Phase 39 是 5 个 P3 模块里最小的** (vs Phase 38 中等 / Phase 40 studio_registry 50 sites 最大)
- 唯一 wildcard consumer: `infra/core/__init__.py:6` — 必须从 C2 同步迁移, C3 一并删除

## Scope

### Source (delete)

| Path | Lines | Symbols | Action |
|------|-------|---------|--------|
| `infra/logging_config.py` | 59 | `StructuredFormatter` (class) + `setup_logging` (func) + `logger` (instance) | DELETE |

### Target (scaffold)

| Path | Action |
|------|--------|
| `packages/lingwen-logging-config/pyproject.toml` | NEW (LEAF template) |
| `packages/lingwen-logging-config/src/lingwen_logging_config/__init__.py` | NEW (verbatim copy of source) |
| `pyproject.toml [tool.uv.workspace] members` | ADD `packages/lingwen-logging-config` |
| `pyproject.toml [tool.uv.sources]` | ADD `lingwen-logging-config = { workspace = true }` |

### Consumers (migrate)

**Pattern 1 grep (verified)**: 8 sites total, **0 indented / function-body**.

| # | File | Line | Current | New |
|---|------|------|---------|-----|
| 1 | `packages/lingwen-pipeline/src/lingwen_pipeline/hooks/actions/run_checker.py` | 16 | `from infra.logging_config import logger` | `from lingwen_logging_config import logger` |
| 2 | `packages/lingwen-pipeline/src/lingwen_pipeline/hooks/actions/update_state.py` | 17 | `from infra.logging_config import logger` | `from lingwen_logging_config import logger` |
| 3 | `packages/lingwen-pipeline/src/lingwen_pipeline/hooks/actions/block_proceed.py` | 12 | `from infra.logging_config import logger` | `from lingwen_logging_config import logger` |
| 4 | `packages/lingwen-pipeline/src/lingwen_pipeline/hooks/actions/notify.py` | 11 | `from infra.logging_config import logger` | `from lingwen_logging_config import logger` |
| 5 | `packages/lingwen-pipeline/src/lingwen_pipeline/state/workflow_validator.py` | 5 | `from infra.logging_config import logger` | `from lingwen_logging_config import logger` |
| 6 | `packages/lingwen-core/src/lingwen_core/agents/orchestration/task_orchestrator.py` | 16 | `from infra.logging_config import logger` | `from lingwen_logging_config import logger` |
| 7 | `infra/memory_service.py` | 26 | `from infra.logging_config import logger` | `from lingwen_logging_config import logger` |
| 8 | `infra/core/__init__.py` | 6 | `from infra.logging_config import *  # noqa: F403` | **DELETE entire line** |

### Patterns Audited (5-pattern matrix from Phase 38 lesson 2)

| # | Pattern | Result |
|---|---------|--------|
| 1 | Literal dotted-path imports | **8 sites** (listed above) |
| 2 | Relative same-package | **0** (no `from .logging_config` references in infra/) |
| 3 | Relative parent-package | **0** (no `from ..logging_config` references) |
| 4 | Filesystem-path string literals | **0** (`grep -rn "infra/logging_config" --include="*.py"` returns empty) |
| 5 | Prior-phase regression guards | **0** (`grep -rn "infra\.logging_config" tests/` returns empty) |

### Files NOT to touch (out of scope)

- `infra/logging_config.py` → DELETE only in C3 (not migrated)
- `infra/core/__init__.py` other lines → unchanged
- `infra/core/__init__.py:6` wildcard line → DELETE only in C3 (not migrated)
- `infra/memory_service.py` other imports → unchanged
- All 7 production consumer files → ONLY the `from infra.logging_config import logger` line changes

## Package design

### `packages/lingwen-logging-config/pyproject.toml`

LEAF pattern (matches `lingwen-paths`):

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "lingwen-logging-config"
version = "0.1.0"
description = "LingWen canonical logging_config module (Phase 39 P3-ARCHDEBT logging_config)"
requires-python = ">=3.11"
dependencies = []  # LEAF — zero workspace deps (only stdlib: json, logging, datetime, pathlib)

[tool.hatch.build.targets.wheel]
packages = ["src/lingwen_logging_config"]
```

### `packages/lingwen-logging-config/src/lingwen_logging_config/__init__.py`

Verbatim copy of `infra/logging_config.py` (no `__all__` per Phase 38 lesson).

Module docstring updated to reference new package:

```python
"""灵文系统结构化日志配置

LingWen canonical logging configuration (Phase 39 P3-ARCHDEBT logging_config).
Migrated from infra/logging_config.py — see invariant #54.
"""
```

## Atomic commits

| # | SHA (target) | Task | Validation gate |
|---|--------------|------|-----------------|
| **C0** | (this) | spec + plan | spec review by sub-agent |
| **C1** | (next) | scaffold package + workspace member | `uv sync --all-packages` succeeds; `import lingwen_logging_config` works |
| **C2** | (next) | migrate 7 line imports + ruff --fix | `ruff check --fix` clean; `grep -rn "from infra\.logging_config\b" infra/ apps/ packages/ tests/` returns 1 site (the wildcard) |
| **C3** | (next) | delete `infra/logging_config.py` + remove wildcard line from `infra/core/__init__.py` | `grep -rn "infra\.logging_config\b" infra/ apps/ packages/ tests/` returns 0 sites; ruff clean |
| **C4** | (next) | bump v37.0→v38.0 + I054 NEW | `grep -n "v38.0" .lingwen/architecture.yml`; `grep -n "I054" .lingwen/architecture.yml` |
| **C5** | (next) | regression guards + doc sync + handoff | `tests/test_phase39_lingwen_logging_config.py` 5-6 guards GREEN |

## Risk assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Wildcard `infra/core/__init__.py` consumers outside Phase 39's 8-site grep | LOW | Re-audit pattern 1 + pattern 2 (relative) + pattern 4 (filesystem) before C3 |
| `infra.core.__init__` re-exports `logger` symbol used somewhere | LOW | `grep -rn "from infra\.core\b" --include="*.py" \| grep -i "logger"` in C2 pre-check |
| Function-body lazy imports of `logger` | LOW | Re-audit pattern 1 with `grep -rn "^[[:space:]]*from infra\.logging_config\b"` before C2 |
| Workspace member declared after `uv sync` (Phase 34 lesson) | LOW | C1 declares BEFORE `uv sync` |
| `ruff --fix` out-of-scope edits (Phase 36/38 lesson) | LOW | C2 applies `ruff --fix` immediately after sed migration |

## Lessons applied from prior phases

| Phase | Lesson | How applied |
|-------|--------|------------|
| 34 | Workspace member declaration must precede `uv sync` | C1 declares in pyproject.toml BEFORE `uv sync --all-packages` |
| 36 | Worktree force-remove staging leak | Staging-leak check at BOTH ff-merge AND `git worktree remove --force` |
| 37 | Function-body imports via `\1` backreference sed | Pattern verified = 0 function-body sites in Phase 39 |
| 37 | Spec/plan combined single commit | C0 spec + plan in one commit (single package, no need for separate plan commit) |
| 37 | 86-consumer single-C2 commit | 7 imports in single C2 (smaller scope than Phase 37) |
| 38 | Whitespace-preserving sed `\1` backreference | Use `^([[:space:]]*)from infra\.logging_config` → `\1from lingwen_logging_config` pattern |
| 38 | 5-pattern audit matrix | All 5 patterns verified pre-spec (above table) |
| 38 | `ruff check --fix` belongs in C2 | C2 applies `ruff check --fix` after sed migration |
| 38 | Test artifact leakage | Pre-merge: `rm -f relationship_network.db` if regenerated by pytest |
| 38 | Spec count drift | All counts verified via `grep -c` before writing spec (8 sites, 3 symbols, 1 wildcard) |

## Carryover closure

- ✅ P3-ARCHDEBT 4/5 (`logging_config`, 8 consumers) → Phase 39
- ⏳ P3-ARCHDEBT 5/5 (`studio_registry`, 50 consumers) → Phase 40
