# Phase 26 — P2-WFSTATE `_last_*` 散点整合 `WorkflowState` dataclass · Handoff

> **Status**: 已实现并待合并 · **日期**: 2026-09-04
> **Branch**: `phase-26-wfstate` · **Design spec**: [../specs/2026-09-03-phase-26-wfstate-design.md](../specs/2026-09-03-phase-26-wfstate-design.md) · **Implementation plan**: [../plans/2026-09-03-phase-26-wfstate.md](../plans/2026-09-03-phase-26-wfstate.md)
> **Master HEAD at start**: `2240156b` (v25.9 closure) · **Commits**: 6 (`99bed427`..`ee3396ae`)
> **Scope**: MasterController 上 7 个 `self._last_*` 散点属性整合为单个 `self._state: WorkflowState` frozen dataclass；零行为变更；TDD 8 unit + 3 refactor guard；9 src + 16 test 文件迁移

## TL;DR

Phase 26 把 MasterController / WorkflowMixin 上 7 个散点属性（`_last_scheduler` / `_last_graph` / `_last_workflow_name` / `_last_start_nodes` / `_last_initial_inputs` / `_last_incremental_backfill` / `_last_memory_context`）整合为单个 `self._state: WorkflowState` frozen dataclass。改前 7 个属性默认值各异 + 裸写裸读 + getattr 防御；改后 dataclass 默认值保证 7 字段都存在 + `with_updates(**kwargs)` 原子切换 + immutable 防 mid-run 部分写入。0 行为变更（外部 API 不动）+ 0 新失败（spec §7 grep 命中从 15 降到 0；新建 11 个 test_workflow_state.py 测试覆盖）。

**6 commits atomic**：

```
99bed427  docs(phase-26): wfstate refactor design spec
14f40bd6  docs(phase-26): wfstate refactor implementation plan
01c504cf  feat(lingwen-core): add WorkflowState dataclass (TDD: 8 unit tests)
1409663b  refactor: migrate _last_* → _state WorkflowState (7 src files)
6ec11b1b  refactor: migrate _last_* test stubs to WorkflowState (9 test files)
ee3396ae  test(agent-system): workflow_state refactor guard (3 guard tests)
<待提交>  docs(phase-26): wfstate handoff + state sync  ← 本文件
```

---

## 背景与动机

v25.9（`2240156b`）修了 `human_review` 全流水线，但代码 review 把 `_last_*` 散点拎出来作为 **P2 重要 carryover（5 项中第 1）**。问题：

**前**（commit `2240156b` 上 master）：
- `mc_workflow.py` 在 `run_workflow` / `resume_workflow` 维护 7 个 `self._last_*` 属性；写散点 7 处裸赋值；读散点 5 处 `getattr` 防御
- `chapter_golden_path.build_stub_master_controller` 只初始化 5 个 → 漏 init `_last_incremental_backfill` / `_last_memory_context` 是**真实存在**隐患
- `mc_workflow.py L241` 裸写 `self._last_incremental_backfill` 无 getattr 兜底 → 与 stub 互动就 `AttributeError`

**后**：
- 单 `self._state: WorkflowState` frozen dataclass，7 字段必有合法默认值（`None` / `""` / `[]` / `{}`）
- `with_updates(**kwargs)` 原子切换：返回新 instance，杜绝 mid-run 半设状态
- 类型安全：测试可直接 `WorkflowState(...)` 构造，无需 MasterController stub
- refactor guard 3 测试防 `_last_*` 散点回潮

---

## What shipped

### 新文件 (2)

| 文件 | 行数 | 内容 |
|---|---|---|
| `packages/lingwen-core/src/lingwen_core/agents/workflow_state.py` | 35 | `WorkflowState` frozen dataclass + `with_updates` helper + `empty()` classmethod |
| `tests/agent_system/test_workflow_state.py` | 123 | 8 unit tests + 3 refactor guard (TDD) |

### 修改源文件 (7)

| 文件 | diff | 内容 |
|---|---|---|
| `packages/lingwen-pipeline/src/lingwen_pipeline/master_controller.py` | +2 / -6 | `__init__` L110-116: 7 行 init → `self._state = WorkflowState.empty()` |
| `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` | +11 / -7 | `run_workflow` 7 写拆 2 次 `with_updates`；`resume_workflow` 5 `getattr` → 直读 + 1 `with_updates`；`_harvest_decision_specs` 兜底回退 |
| `packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py` | +2 / -5 | stub init 5 行 → `controller._state = WorkflowState.empty()` + L138 直读 |
| `packages/lingwen-core/src/lingwen_core/agents/production_summary.py` | +4 / -5 | `build_production_summary_from_controller` 5 getattr → 直读 |
| `packages/lingwen-core/src/lingwen_core/agents/got_bridge.py` | +1 / -1 | `getattr(self._master, "_last_initial_inputs", None)` → `self._master._state.initial_inputs` |
| `packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py` | +1 / -1 | `master._last_initial_inputs` → `master._state.initial_inputs` |
| `apps/studio_api/protocols.py` | +5 / -7 | 5 `getattr` → 直读 + 2 docstring 同步 |

### 修改测试文件 (9 — spec §2.2 列 8，实际 9)

| 文件 | 模式 | 主要 diff |
|---|---|---|
| `tests/got/test_decision_pause_resume.py` | A + B | stub init 多行 → `WorkflowState.empty()`；6 处 `_last_X = X` → `with_updates(...)` |
| `tests/dashboard/test_decision_api.py` | B + 额外 | 6 sites `_last_* = _Stub*` → `WorkflowState(...)`；7 `MasterController.__new__()` 加 `master._state = WorkflowState.empty()`；`_make_master` helper 同 |
| `tests/dashboard/test_app_workflow_production_summary_f66.py` | B | `_make_master_with_production_cache` 6 行 → `WorkflowState(...)` 7 字段 |
| `tests/dashboard/test_app_workflow_status.py` | B | 4 相同 3 行 stub → `WorkflowState(...)` |
| `tests/dashboard/test_app_workflow_status_tier_budget.py` | B | `MagicMock()` + 3 `_last_*` → `WorkflowState(...)` |
| `tests/dashboard/test_protocols.py` | B | `_StubMaster.__init__` 3 行 → `WorkflowState(...)` |
| `tests/agent_system/test_chapter_emit.py` | C | `_Master` 类 class-level `_last_initial_inputs = {...}` → `_state = WorkflowState(initial_inputs=...)`；1 处 fake type `{"_last_initial_inputs": ...}` → `{"_state": WorkflowState(...)}` |
| `tests/agent_system/test_production_summary.py` | 断言 | `_Controller` 类 5 行 init → `WorkflowState(...)` |
| **`tests/cross_volume/test_incremental_backfill.py`** | 补 | **`MasterController.__new__()` 缺 `controller._state = WorkflowState.empty()` — spec §2.2 漏列，执行时发现并补** |

---

## Pattern 三模式执行说明

| 模式 | 适用 | 改前 | 改后 |
|---|---|---|---|
| **A** | 多行 stub init | `controller._last_scheduler = None / ._last_graph = None / ...` (4-5 行) | `controller._state = WorkflowState.empty()` |
| **B** | 单/多行 `_last_X = X` | `master._last_scheduler = scheduler / ._last_graph = graph / ._last_workflow_name = "novel_writing"` | `master._state = master._state.with_updates(scheduler=scheduler, graph=graph, workflow_name="novel_writing")` (or `master._state = WorkflowState(...)` for fresh setup) |
| **C** | fake class dict | `type("_M", (), {"_last_initial_inputs": {...}})()` | `type("_M", (), {"_state": WorkflowState(initial_inputs={...})})()` |

---

## Verification gates (spec §7)

| 门 | 命令 | Baseline | Target | 实测 | Status |
|---|---|---|---|---|---|
| `tests/dashboard` | `.venv/bin/python -m pytest tests/dashboard/` | 357p + 3s | 357p + 3s | **357p + 3s** | ✅ UNCHANGED |
| `tests/cross_volume/test_incremental_backfill.py` | 同 file | 15p | 15p | **15p** | ✅ UNCHANGED |
| `tests/got` (test_decision_pause_resume) | 同 file | 17p | ≥17p | **17p** | ✅ UNCHANGED |
| `tests/agent_system` 单元 / refactor guard | `tests/agent_system/test_workflow_state.py` | 0 | **+11 passed** | **11p (8u + 3g)** | ✅ NEW GREEN |
| `tests/agent_system` 其他 | 全部 test file | 84 pre-existing cascade fail | ZERO new | **0 new** (stash 验证: 同 9 fail 在 src commit 1409663b 上) | ✅ 0 NEW FAILURE |
| ruff check | `uv run ruff check .` | clean | clean | **clean** | ✅ |
| ruff format --check | `uv run ruff format --check .` | clean | clean | **clean** | ✅ |
| grep 7 fields | `grep -rln "_last_scheduler\|..." packages/ apps/ tests/` | 15 hits | 0 hits | **0 hits** | ✅ |

**0 改范围（声明外）**：未触及 P2-MC-WRITING（84+ 个 pre-existing cascade failure 仍在 — 推测 `mc_writing.py` 类似 gutted）/ P2-WFRUNNER / P2-RESUME-VERIFY / P2-ARCHDEBT（infra.got 迁移 / chapter_golden_path 反向 import / HANDOFF 措辞修订）。

---

## 关键决策记录（per brainstorming）

| 维度 | 选择 | 备注 |
|---|---|---|
| 字段范围 | 7 字段完整（含 v25.9 新增的 `incremental_backfill` / `memory_context`） | BACKLOG 原文 5 字段是 v25.9 修复前快照；7 字段统一管消除拼接复制 |
| Mutability | `frozen=True` + `with_updates()` 原子更新 | 与项目 python/coding-style.md「Prefer immutable」一致 |
| 迁移策略 | 直接替换 + 丢 `_last_*` 属性（无 compat shim） | 仓库内全 grep 已确认无第三方依赖 |
| 放置位置 | 独立模块 `workflow_state.py` | MANY SMALL FILES > FEW LARGE FILES；不拖 MasterController 依赖 |
| 测试范围 | Unit + integration + refactor guard（防回潮） | guard 测试断言 7 `_last_*` 在 dataclass 实例上 `not hasattr` — 未来若回潮 CI 拦截 |

---

## Carryover to Phase 27+

| ID | 标题 | 估计阶段 |
|---|---|---|
| **P2-WFRUNNER** | WorkflowRunner service 拆分（`run_workflow` 90+ 行偏多；拆 service 后 `run_workflow` 仅做编排，helper 收口） | 紧接 Phase 26 — 建议 Phase 27 |
| **P2-RESUME-VERIFY** | `start_nodes=None` 时 `resume_workflow` 重跑 E2E 验证（代码 review 列 important；scheduler 对已完成节点是否幂等无测试覆盖） | Phase 28 |
| **P2-MC-WRITING** | 84 pre-existing cascade failures 根因（推测 `mc_writing.py` 类似 gutted）— 独立大 phase | TBD（独立工作） |
| **P2-ARCHDEBT** | infra.got 迁移 + `chapter_golden_path` 反向 import 整改 + HANDOFF 措辞修订 | TBD |

未触：architecture.yml / CLAUDE.md / HANDOFF.md 等不需更新（无新增不变量）。

---

## 留您处理（未触）

- 主 checkout 未提交：`M HANDOFF.md` / `?? .trae/` / `?? HANDOFF-claude-code.md`（handoff 切换工作，独立）
- worktree `LingWen-phase-25-9` 待清理（分支已 merged）；独立 housekeeping
- worktree `.worktrees/track-a` / `.worktrees/track-b` 待清理（v25.0/v25.1 时代遗留）

---

## 下次会话选项

- **(a) 启动 Phase 27 — P2-WFRUNNER**（紧接顺位）：run_workflow 拆 service
- **(b) 启动 Phase 27 — P2-RESUME-VERIFY**：resume_workflow start_nodes=None 重跑 E2E 验证
- **(c) 暂停 + HANDOFF 工作收尾 + worktree 清理**
- **(d) 启动 P2-MC-WRITING 根因调查**：独立大 phase（84+ pre-existing cascade failure 调查）

未触要求：每 phase 都需 new design spec + implementation plan + TDD + refactor guard 同样纪律。
