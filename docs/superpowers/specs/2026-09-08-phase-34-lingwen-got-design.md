# Phase 34 LINGWEN-GOT 设计稿

> **版本**: v33.0 · **日期**: 2026-09-08 · **状态**: 设计 (待 review)
> **范围**: P2-ARCHDEBT 最大块 — `infra.got.*` → `packages/lingwen-got/` 迁移
> **关联**: v32.0 SHIM-CLEANUP carryover 第 1 项; CLAUDE.md:147 P2-ARCHDEBT
> **分支**: `phase-34-lingwen-got` (worktree: `../LingWen-phase-34`)

---

## 1. Goal & Non-Goals

### Goal

完成 P2-ARCHDEBT 剩余 1/2 → 0/2:
- **唯一动作**: 把 `infra/got/` 8 模块 (1788 行) 迁到 `packages/lingwen-got/src/lingwen_got/` 新 uv workspace 包
- **连带**: 迁移 30 个跨 `apps/infra/packages/tests` 的 consumer; 把 12 个 got-specific 测试文件搬到 `packages/lingwen-got/tests/`
- **净结果**: `infra.got.*` 路径非法; I001 单向依赖深化 (workspace 内 clean dep); 新增 invariant #49

### Non-Goals (显式排除 → Phase 35+)

| 子任务 | 范围 | 状态 |
|-------|------|------|
| `infra/world_model/__init__.py` split (canonical + behavior services) | 1 phase / 8-12 commits / 5 consumer 迁移 | **Phase 35** (P2-ARCHDEBT remaining 1/1) |
| `infra.{paths, project_config, logging_config, errors, studio_registry}` → packages/ 迁移 | multi-week, 24+ 文件, 跨 3 个 lingwen-* 包 | **Phase 36+ P3-ARCHDEBT** (新增) |
| Phase 114 prod preview regression (cytoscape-fcose) | accepted debt | 永久保留 |
| vis-network fresh-clone install gap | 已知流程 | 永久保留 |

---

## 2. 架构上下文

### 当前状态 (`infra.got.*`)

```
infra/got/                                ← 8 Python 文件, 1788 行
├── __init__.py           (98)   # 32 symbols re-export
├── aggregator.py        (138)  # JudgmentAggregator
├── cache.py              (66)  # ThoughtCache
├── data_structures.py   (160)  # ThoughtNode / NodeExecution / NodeType / NodeStatus
├── graph.py             (352)  # ThoughtGraph + 5 exception classes
├── llm_compute.py       (133)  # LLMComputeFn + default_prompt_builder (外部依赖 lingwen_llm)
├── scheduler.py         (420)  # GoTScheduler + 5 result/error classes
├── visualizer.py        (211)  # 6 render_* 函数 + NODE_STATUS_CLASS
└── workflow_loader.py   (210)  # load_workflow + 4 error classes (YAML)
```

### 当前 Consumer 分布 (30 文件)

| 类别 | 文件数 | 文件清单 |
|------|--------|----------|
| `packages/lingwen-core/src/lingwen_core/agents/` | 4 | workflow_runner, chapter_production_pilot, chapter_golden_path, got_bridge |
| `apps/studio_api/` | 3 | protocols.py (lazy:259), routes/workflows.py (lazy:181-183), helpers/workflow.py |
| `infra/` | 2 | cross_volume/incremental_backfill.py, poc/run_volume_1.py |
| `tests/agent_system/` | 8 | test_chapter_emit, test_chapter_golden_path, test_decision_integration, test_got_bridge, test_got_bridge_budget, test_master_controller_stub_router_e2e, test_phase7_1_production_fixes, test_production_summary, test_workflow_runner |
| `tests/got/` | 10 | test_aggregator, test_decision_pause_resume, test_got_cache, test_got_data_structures, test_graph, test_llm_compute, test_llm_compute_e2e, test_scheduler, test_visualizer, test_workflow_loader |
| `tests/cross_volume/` | 1 | test_incremental_backfill |
| `tests/dashboard/` | 2 | test_app_workflow_production_summary_f66, test_decision_api |
| **合计** | **30** | |

### Consumer Import 形态

| 形态 | 例子 | 占比 |
|------|------|------|
| Literal path: `from infra.got.X import Y` | 大多数 (含所有 tests/got/) | ~80% |
| Package: `from infra.got import (...)` | `infra/poc/run_volume_1.py:32` | ~3% |
| Lazy / function-body import | consumer: `got_bridge.py:447-449`, `protocols.py:259`, `routes/workflows.py:181-183`; infra/got internal: `scheduler.py:252` (`from infra.got.visualizer import render_mermaid_from_scheduler`) | consumer ~10% + infra/got 1 site (must convert in C1) |
| TYPE_CHECKING block import | grep confirmed: 0 | 0% |

### `infra/got` 内部 cross-import 图

```
__init__.py ─→ aggregator / cache / data_structures / graph / llm_compute / scheduler / visualizer / workflow_loader
llm_compute.py ─→ data_structures + scheduler
scheduler.py ─→ cache + data_structures + graph (lazy visualizer)
visualizer.py ─→ data_structures + graph
workflow_loader.py ─→ data_structures + graph
graph.py ─→ data_structures
```

**注**: `scheduler/visualizer/workflow_loader/graph` 内部仍用 literal-path (`from infra.got.X`), C1 必须同步改 relative.

### `infra/got` 外部依赖 (跨包)

| Dep | 文件 | 备注 |
|-----|------|------|
| `lingwen_llm.providers.cost_tracker.CostTracker` | `llm_compute.py:24` | lingwen-llm 是 workspace 包, 加 dep 即可 |
| `lingwen_llm.providers.tiered_router.TieredRouter` | `llm_compute.py:25` | 同上 |

**0 个 `infra.X` / `apps.X` 内部依赖** → 干净边界, 可直接迁。

---

## 3. 目标架构

### `packages/lingwen-got/` 包结构

```
packages/lingwen-got/
├── pyproject.toml                              # hatchling + [project] + lingwen-llm dep
├── README.md                                   # 1 段: 这是 GoT 引擎包
├── src/
│   └── lingwen_got/
│       ├── __init__.py                          # 32 symbol re-export (照搬 infra/got/__init__.py)
│       ├── aggregator.py                        # 138 行
│       ├── cache.py                             # 66 行
│       ├── data_structures.py                   # 160 行
│       ├── graph.py                             # 352 行
│       ├── llm_compute.py                       # 133 行
│       ├── scheduler.py                         # 420 行
│       ├── visualizer.py                        # 211 行
│       └── workflow_loader.py                   # 210 行
└── tests/
    ├── __init__.py                              # 标记 pytest 包
    ├── conftest.py                              # 共用 fixtures (mock LLM 等)
    ├── test_aggregator.py                       # from tests/got/test_aggregator.py
    ├── test_cache.py                            # from tests/got/test_got_cache.py (rename 去 got_ prefix)
    ├── test_data_structures.py                  # from tests/got/test_got_data_structures.py
    ├── test_decision_pause_resume.py            # from tests/got/test_decision_pause_resume.py
    ├── test_graph.py                            # from tests/got/test_graph.py
    ├── test_llm_compute.py                      # from tests/got/test_llm_compute.py
    ├── test_llm_compute_e2e.py                  # from tests/got/test_llm_compute_e2e.py
    ├── test_scheduler.py                        # from tests/got/test_got_scheduler.py (rename)
    ├── test_visualizer.py                       # from tests/got/test_visualizer.py
    ├── test_workflow_loader.py                  # from tests/got/test_workflow_loader.py
    ├── test_got_bridge.py                       # from tests/agent_system/test_got_bridge.py
    └── test_got_bridge_budget.py                # from tests/agent_system/test_got_bridge_budget.py
```

### 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| Layout | **Flat mirror** (8 文件 in `src/lingwen_got/`) | 与 (A) Batched mechanical sed 策略匹配, sed `infra.got.X` → `lingwen_got.X` 直接生效, 无 sub-package 重命名 |
| 依赖 | `lingwen-llm` (workspace) | `llm_compute.py` 需要 `CostTracker` + `TieredRouter`; lingwen-llm 已是 workspace 包, 加 dep 即可 |
| Python 基线 | `>=3.12` | 与 lingwen-core / lingwen-shared 一致 |
| 命名 | `lingwen_got` (下划线) | 符合 PEP 8 + 与 lingwen_core / lingwen_creator 一致 |
| Test 位置 | **All into `packages/lingwen-got/tests/`** (12 文件) | 用户选 (iii): 含 `tests/agent_system/*got*` 也搬; 移除 `got_` 前缀 (lingwen_got 已暗示) |
| 旧 `infra/got/` | **Hard delete** (C6) | 所有 consumer 已 bound; 无需保留 shim |

### `pyproject.toml` workspace 改动 (C1)

```toml
[tool.uv.workspace]
members = [
    "packages/lingwen-core",
    # ... (现有 10 个)
    "packages/lingwen-creator",
    "packages/lingwen-got",   # ★ v33.0 新增
    "apps/studio_api",
]

[tool.uv.sources]
# ... (现有 10 个)
lingwen-got = { workspace = true }   # ★ v33.0 新增
```

### `packages/lingwen-got/pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "lingwen-got"
version = "0.1.0"
description = "LingWen · Graph of Thoughts engine (ThoughtGraph + GoTScheduler + aggregator + viz + workflow loader)"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.7",
    "lingwen-llm",   # for TieredRouter + CostTracker
]

[project.optional-dependencies]
test = ["pytest>=8.0"]

[tool.hatch.build.targets.wheel]
packages = ["src/lingwen_got"]
```

### 迁移后依赖图

```
 ┌──────────────────────────────────┐
 │      packages/lingwen-llm        │  (TieredRouter, CostTracker)
 └──────────────┬───────────────────┘
                │ workspace dep
 ┌──────────────▼───────────────────┐
 │      packages/lingwen-got        │  ← 新包 (8 modules, 1788 行)
 │      (8 modules, 32 public API)  │
 └──────┬─────────┬────────┬─────────┘
        │         │        │ consumer
 ┌──────▼──┐ ┌────▼────┐ ┌─▼───────────┐
 │ apps/   │ │ pkgs/   │ │ tests/*    │
 │studio_api│ │lingwen- │ │ (root 7 +  │
 │  (3)    │ │ core (4)│ │  package 12)│
 └─────────┘ └─────────┘ └────────────┘
```

---

## 4. 迁移 Consumer 分类

按 batched mechanical sed 策略, 把 30 个 consumer 文件分 4 个 commit batch:

### Batch 1 (C2): Test 文件搬迁 12 个

| 原路径 | 新路径 | rename |
|--------|--------|--------|
| `tests/got/__init__.py` | `packages/lingwen-got/tests/__init__.py` | n/a |
| `tests/got/test_aggregator.py` | `packages/lingwen-got/tests/test_aggregator.py` | n/a |
| `tests/got/test_got_cache.py` | `packages/lingwen-got/tests/test_cache.py` | 去掉 `got_` |
| `tests/got/test_got_data_structures.py` | `packages/lingwen-got/tests/test_data_structures.py` | 去掉 `got_` |
| `tests/got/test_got_scheduler.py` | `packages/lingwen-got/tests/test_scheduler.py` | 去掉 `got_` |
| `tests/got/test_graph.py` | `packages/lingwen-got/tests/test_graph.py` | n/a |
| `tests/got/test_llm_compute.py` | `packages/lingwen-got/tests/test_llm_compute.py` | n/a |
| `tests/got/test_llm_compute_e2e.py` | `packages/lingwen-got/tests/test_llm_compute_e2e.py` | n/a |
| `tests/got/test_visualizer.py` | `packages/lingwen-got/tests/test_visualizer.py` | n/a |
| `tests/got/test_workflow_loader.py` | `packages/lingwen-got/tests/test_workflow_loader.py` | n/a |
| `tests/got/test_decision_pause_resume.py` | `packages/lingwen-got/tests/test_decision_pause_resume.py` | n/a |
| `tests/agent_system/test_got_bridge.py` | `packages/lingwen-got/tests/test_got_bridge.py` | n/a |
| `tests/agent_system/test_got_bridge_budget.py` | `packages/lingwen-got/tests/test_got_bridge_budget.py` | n/a |

### Batch 2 (C3): lingwen-core 4 个

| 文件 | 改动 |
|------|------|
| `packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py` | `infra.got.X` → `lingwen_got.X` |
| `packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py` | 同上 |
| `packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py` | 同上 |
| `packages/lingwen-core/src/lingwen_core/agents/got_bridge.py` | 同上 (含 lazy imports L447-449) |

### Batch 3 (C4): apps/studio_api 3 个

| 文件 | 改动 |
|------|------|
| `apps/studio_api/protocols.py` | lazy import L259: `from infra.got.data_structures import ...` → `from lingwen_got.data_structures import ...` |
| `apps/studio_api/routes/workflows.py` | lazy imports L181-183: 3 个 `from infra.got.X` → `from lingwen_got.X` |
| `apps/studio_api/helpers/workflow.py` | (grep 确认后) `infra.got.X` → `lingwen_got.X` |

### Batch 4 (C5): 其他 12 个 (留原位 + 更新 import)

| 文件 | 改动 |
|------|------|
| `infra/cross_volume/incremental_backfill.py` | sed `infra.got.X` → `lingwen_got.X` |
| `infra/poc/run_volume_1.py` | sed `infra.got` → `lingwen_got` |
| `tests/agent_system/test_chapter_emit.py` | sed |
| `tests/agent_system/test_chapter_golden_path.py` | sed |
| `tests/agent_system/test_decision_integration.py` | sed |
| `tests/agent_system/test_master_controller_stub_router_e2e.py` | sed |
| `tests/agent_system/test_phase7_1_production_fixes.py` | sed |
| `tests/agent_system/test_production_summary.py` | sed |
| `tests/agent_system/test_workflow_runner.py` | sed |
| `tests/cross_volume/test_incremental_backfill.py` | sed |
| `tests/dashboard/test_app_workflow_production_summary_f66.py` | sed |
| `tests/dashboard/test_decision_api.py` | sed |

---

## 5. Commit Plan (8 atomic commits)

```
phase-34-lingwen-got
├── C0  docs(phase-34): spec + plan
├── C1  chore(packages): scaffold lingwen-got package skeleton
├── C2  refactor(test): move 12 got-related test files to packages/lingwen-got/tests/
├── C3  refactor(infra): migrate 4 lingwen-core consumers to lingwen_got
├── C4  refactor(apps): migrate 3 apps/studio_api consumers to lingwen_got
├── C5  refactor(infra): migrate 2 infra consumers + 10 tests/ consumers to lingwen_got
├── C6  chore(infra): delete infra/got/ directory
└── C7  test(phase-34): regression guard tests + doc sync
```

### C0 — `docs(phase-34): spec + plan`

| 变更 | 路径 |
|------|------|
| 新建 | `docs/superpowers/specs/2026-09-08-phase-34-lingwen-got-design.md` |
| 新建 | `docs/superpowers/plans/2026-09-08-phase-34-lingwen-got.md` |

Gate: 无 (doc-only)。

### C1 — `chore(packages): scaffold lingwen-got package skeleton`

| 变更 | 路径 |
|------|------|
| 新建 | `packages/lingwen-got/pyproject.toml` |
| 新建 | `packages/lingwen-got/README.md` |
| 新建 | `packages/lingwen-got/src/lingwen_got/{__init__.py,aggregator.py,cache.py,data_structures.py,graph.py,llm_compute.py,scheduler.py,visualizer.py,workflow_loader.py}` |
| 新建 | `packages/lingwen-got/tests/__init__.py` |
| 新建 | `packages/lingwen-got/tests/conftest.py` |
| 改 | `pyproject.toml` (root): `tool.uv.workspace.members` 加 `packages/lingwen-got`; `tool.uv.sources` 加 `lingwen-got = { workspace = true }` |
| 改 | `packages/lingwen-got/src/lingwen_got/__init__.py` + 4 子文件 (scheduler/visualizer/workflow_loader/graph): 内部 literal-path imports → relative |

**G1**: `uv sync --all-packages --offline` exit 0
**G2**: `python -c "import lingwen_got; print(len(lingwen_got.__all__))"` → 32

### C2 — `refactor(test): move 12 got-related test files`

| 变更 | 路径 |
|------|------|
| 移 (12) | 见 §4 Batch 1 |
| 改 (12) | sed `from infra.got.X` → `from lingwen_got.X` |
| 删 | `tests/got/` (空目录) |

**G3**: `cd packages/lingwen-got && pytest tests/ -v` 全 GREEN
**G4**: `pytest tests/agent_system/ -v --ignore=tests/agent_system/test_got_bridge.py --ignore=tests/agent_system/test_got_bridge_budget.py` 全 GREEN (剩余 7 文件)

### C3 — `refactor(infra): migrate 4 lingwen-core consumers`

| 变更 | 路径 |
|------|------|
| 改 (4) | workflow_runner / chapter_production_pilot / chapter_golden_path / got_bridge (含 lazy imports L447-449) |

**G5**: `cd packages/lingwen-core && pytest tests/ -v --rootdir=packages/lingwen-core` 全 GREEN

### C4 — `refactor(apps): migrate 3 apps/studio_api consumers`

| 变更 | 路径 |
|------|------|
| 改 (3) | protocols.py (lazy:259) / routes/workflows.py (lazy:181-183) / helpers/workflow.py |

**G6**: `python -c "from apps.studio_api.protocols import *; from apps.studio_api.routes.workflows import *"` exit 0 (lazy import 路径打通)
**G6b**: `pytest apps/studio_api/tests/ -v` 全 GREEN

### C5 — `refactor(infra): migrate 2 infra + 10 tests consumers`

| 变更 | 路径 |
|------|------|
| 改 (2 infra) | cross_volume/incremental_backfill.py, poc/run_volume_1.py |
| 改 (7 tests/agent_system) | test_chapter_emit, test_chapter_golden_path, test_decision_integration, test_master_controller_stub_router_e2e, test_phase7_1_production_fixes, test_production_summary, test_workflow_runner |
| 改 (1 tests/cross_volume) | test_incremental_backfill.py |
| 改 (2 tests/dashboard) | test_app_workflow_production_summary_f66, test_decision_api |

**G7**: `uv run pytest tests/ -v --ignore=tests/agent_system/test_got_bridge.py --ignore=tests/agent_system/test_got_bridge_budget.py` 全 GREEN
**G8**: `grep -rln "infra\.got\b" --include="*.py" .` (排除 `packages/lingwen-got/src/`) → 0 行

### C6 — `chore(infra): delete infra/got/ directory`

| 变更 | 路径 |
|------|------|
| 删 | `rm -rf infra/got/` (8 文件 + `__init__.py`) |
| (infra/ 目录本身保留 — paths/project_config/logging_config 还在) | n/a |

**G9**: `grep -rln "infra\.got\b" --include="*.py" .` (全 repo) → 0 行
**G10**: `ruff check .` All checks passed
**G11**: `uv run pytest tests/ -v` (root testpaths 全覆盖) 全 GREEN

### C7 — `test(phase-34): regression guard tests + doc sync`

| 变更 | 路径 |
|------|------|
| 新建 | `tests/test_phase34_lingwen_got.py` (7 个 guards) |
| 改 | `CLAUDE.md` v33.0 entry + Phase 34 carryover 段 + invariant #49 |
| 改 | `.lingwen/architecture.yml` version 32.0 → 33.0; invariants 加 #49; workspace members 加 lingwen-got |
| 改 | `docs/LINGWEN_ARCHITECTURE_SPEC.md` lingwen-got 段 + GoT 模块行 |
| 改 | `docs/superpowers/handoffs/2026-09-07-phase-32-shim-cleanup-handoff.md` "P2-ARCHDEBT remaining infra.got" → "CLOSED by Phase 34" |
| 改 | `docs/superpowers/archive/PHASE_HISTORY.md` v33.0 行 |
| 新建 | `docs/superpowers/handoffs/2026-09-08-phase-34-lingwen-got-handoff.md` |

**G12**: `pytest tests/test_phase34_lingwen_got.py -v` 7/7 GREEN
**G13**: `ruff check .` All checks passed

---

## 6. Regression Guard 设计 (C7)

`tests/test_phase34_lingwen_got.py` 7 个 guards:

```g
def test_lingwen_got_pyproject_exists():
    """packages/lingwen-got/pyproject.toml must exist."""
    assert Path("packages/lingwen-got/pyproject.toml").is_file()

def test_lingwen_got_init_exists():
    """packages/lingwen-got/src/lingwen_got/__init__.py must exist."""
    assert Path("packages/lingwen-got/src/lingwen_got/__init__.py").is_file()

def test_infra_got_directory_deleted():
    """infra/got/ directory must NOT exist (Phase 34 C6)."""
    assert not Path("infra/got").exists()

def test_lingwen_got_exports_32_symbols():
    """Public API surface must match pre-migration infra.got (32 symbols)."""
    import lingwen_got
    assert len(lingwen_got.__all__) == 32
    expected = {"ThoughtNode", "NodeExecution", "ThoughtGraph", "GoTScheduler",
                "JudgmentAggregator", "ThoughtCache", "load_workflow", "LLMComputeFn"}
    assert expected.issubset(set(lingwen_got.__all__))

def test_lingwen_got_tests_directory_complete():
    """12 test files must exist in packages/lingwen-got/tests/."""
    expected = ["test_aggregator.py", "test_cache.py", "test_data_structures.py",
                "test_decision_pause_resume.py", "test_graph.py", "test_llm_compute.py",
                "test_llm_compute_e2e.py", "test_scheduler.py", "test_visualizer.py",
                "test_workflow_loader.py", "test_got_bridge.py", "test_got_bridge_budget.py"]
    for f in expected:
        assert Path(f"packages/lingwen-got/tests/{f}").is_file(), f"Missing {f}"

def test_lingwen_core_consumers_use_lingwen_got():
    """4 lingwen-core consumers must import from lingwen_got (not infra.got)."""
    files = [
        "packages/lingwen-core/src/lingwen_core/agents/workflow_runner.py",
        "packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py",
        "packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py",
        "packages/lingwen-core/src/lingwen_core/agents/got_bridge.py",
    ]
    for f in files:
        content = Path(f).read_text()
        assert "infra.got" not in content, f"{f} still references infra.got"
        assert "lingwen_got" in content, f"{f} must import lingwen_got"

def test_lingwen_got_depends_on_lingwen_llm():
    """lingwen-got pyproject.toml must declare lingwen-llm dependency."""
    import tomllib
    with open("packages/lingwen-got/pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    deps = data["project"]["dependencies"]
    assert any("lingwen-llm" in d for d in deps), "lingwen-got must depend on lingwen-llm"
```

---

## 7. 验证 Gates 总表

| Gate | Trigger | 命令 | 期望 |
|------|---------|------|------|
| **G1** | C1 | `uv sync --all-packages --offline` | exit 0 |
| **G2** | C1 | `python -c "import lingwen_got; print(len(lingwen_got.__all__))"` | 32 |
| **G3** | C2 | `cd packages/lingwen-got && pytest tests/ -v` | 全 GREEN |
| **G4** | C2 | `pytest tests/agent_system/ -v --ignore=...got_bridge...got_bridge_budget` | 7 文件 GREEN |
| **G5** | C3 | `cd packages/lingwen-core && pytest tests/ -v` | 全 GREEN |
| **G6** | C4 | `python -c "from apps.studio_api.protocols import *; from apps.studio_api.routes.workflows import *"` | exit 0 |
| **G6b** | C4 | `pytest apps/studio_api/tests/ -v` | 全 GREEN |
| **G7** | C5 | `uv run pytest tests/ -v --ignore=tests/agent_system/test_got_bridge.py --ignore=tests/agent_system/test_got_bridge_budget.py` | 全 GREEN |
| **G8** | C5 | `grep -rln "infra\.got\b" --include="*.py" .` (排除 lingwen-got src) | 0 行 |
| **G9** | C6 | `grep -rln "infra\.got\b" --include="*.py" .` (全 repo) | 0 行 |
| **G10** | C6 | `ruff check .` | clean |
| **G11** | C6 | `uv run pytest tests/ -v` | 全 GREEN |
| **G12** | C7 | `pytest tests/test_phase34_lingwen_got.py -v` | 7/7 GREEN |
| **G13** | C7 | `ruff check .` | clean |

**Pre-C0 baseline** (per Phase 32 N.14 lesson 4): C0 前跑 `git stash` + `uv run pytest tests/` 拿 baseline failed 列表, Phase 34 完成时对照。任何 baseline 之外的 fail = Phase 34 引入 → 必须修。

---

## 8. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| **C1 内部 import 转换不完整** (scheduler/visualizer/workflow_loader/graph 内 literal-path) | 中 | 中 | C1 同步改; G2 `python -c "import lingwen_got"` 会触发 AttributeError; 完成后 `grep -n "infra\.got" src/lingwen_got/` 必须 0 |
| **C2 test fixture / conftest 错位** | 中 | 中 | C1 同步建 `tests/conftest.py`; G3 跑全 packages/lingwen-got/tests/ |
| **C5 12 文件批量 sed 漏 lazy / TYPE_CHECKING imports** | 中 | 高 | Phase 32 N.14 lesson: 3 个 grep pattern (literal path + 同包 relative + 父包 relative). C5 末 G8 兜底 |
| **apps/studio_api lazy import 路径未打通** | 中 | 高 | C4 G6 用 import smoke 而非仅 pytest (lazy import 不一定被 pytest 触发); `got_bridge.py:447-449` lazy 也必须验证 |
| **pyproject.toml workspace 加 lingwen-got 后 uv sync 失败** | 中 | 高 | G1 用 `--offline` flag (Phase 32 经验); fallback 用 conda env |
| **C6 删 infra/got/ 后某个 consumer 未发现** | 低 | 高 | C5 末 G8 + C6 G9 双层 grep 兜底; C7 regression guards 长期 |
| **P3-ARCHDEBT scope creep** (用户问"是不是顺手迁 infra.paths 等") | 中 | 中 | 设计 §1 Non-Goals 明确排除, handoff 显式记录 P3-ARCHDEBT 为下一 carryover |
| **C7 doc sync 漏改 12 处 carrier** | 中 | 低 | checklist 在 plan doc; G13 ruff 仍跑 |
| **conda env stale PYTHONPATH 误用** | 低 | 中 | per MEMORY.md phase-32 lesson: 用 worktree `.venv/bin/python`, 不用 `/home/ailearn/miniconda3/bin/python` |
| **199 test 估算与实际偏差** | 低 | 低 | §4 列出 12 文件清单, plan doc 用 12 file + ~199 case 估算 (与 Phase 32 handoff 对齐) |

---

## 9. Out of Scope (Phase 35+ 候选)

按 v32.0 carryover closure + Phase 34 新发现:

| 候选 | 真实规模 | 优先级 |
|------|---------|--------|
| `infra/world_model/__init__.py` split (canonical + behavior services) | 1 phase / 8-12 commits / 5 consumer 迁移 | **Phase 35** (P2-ARCHDEBT remaining 1/1) |
| `infra.{paths, project_config, logging_config, errors, studio_registry}` → packages/ 迁移 (P3-ARCHDEBT 新增) | multi-week / 24+ 文件 / 跨 3 个 lingwen-* 包 | **Phase 36+** |
| Phase 114 prod preview regression (cytoscape-fcose) | accepted debt | 永久保留 |
| vis-network fresh-clone install gap | 已知流程 | 永久保留 |

---

## 10. 成功标准

Phase 34 完成时:

- ✅ P2-ARCHDEBT 进度 1/2 → 0/2 (infra.got CLOSED, infra/world_model split 留 Phase 35)
- ✅ 8 个 atomic commits (C0-C7), 每个 commit 独立通过对应 gates
- ✅ 14 个 validation gate runs (G1-G13 + G6b 拆分) 全绿
- ✅ `infra/got/` 目录删除, `packages/lingwen-got/` 创建并可 `import lingwen_got`
- ✅ 30 个 consumer 全部迁移; 12 个 got-specific test 搬到 packages/lingwen-got/tests/
- ✅ `uv run pytest tests/` baseline + Phase 34 完成时一致 (无 Phase 34 引入的 regression)
- ✅ `ruff check .` clean
- ✅ invariant #49 NEW (lingwen-got canonical, infra.got illegal)
- ✅ CLAUDE.md v33.0 + `.lingwen/architecture.yml` v33.0 同步
- ✅ handoff `docs/superpowers/handoffs/2026-09-08-phase-34-lingwen-got-handoff.md` 完成
- ✅ ff-merge `phase-34-lingwen-got` 到 master 无冲突, push origin
- ✅ worktree `../LingWen-phase-34` 已 remove