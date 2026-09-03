# Phase 26 — P2-WFSTATE · `_last_*` 散点整合 `WorkflowState` dataclass · Design

> **Status**: 设计稿 · 待用户 review
> **日期**: 2026-09-03
> **目标版本**: v26.0
> **作用域**: `WorkflowMixin`（mc_workflow.py）+ 6 个读/写/重置 site + 新文件 `workflow_state.py`；零行为变更
> **范围选择**: **纯 refactor**（per brainstorming）— 不动架构债（infra.got 迁移 / chapter_golden_path 反向 import / HANDOFF 措辞 / WorkflowRunner service 拆分 / resume E2E 验证）

---

## 1. 背景与动机

v25.9（commit `2240156b`）修了 `human_review` 全流水线，但代码 review 把 `_last_*` 散点拎出来作为 **P2 重要 carryover**：

**问题**（基于当前 master `2240156b`）：
- `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` 在 `run_workflow` / `resume_workflow` 维护 **7 个 `self._last_*` 实例属性**（`workflow_name` / `start_nodes` / `initial_inputs` / `scheduler` / `graph` / `incremental_backfill` / `memory_context`），默认值各异（`None` / `None` / `""` / `[]` / `{}` / `None` / `None`）
- 写散点：mc_workflow.py L119-138、L241（7 处裸赋值）
- 读散点 + getattr 防御：production_summary.py L62-76 / got_bridge.py L302 / chapter_production_pilot.py L440 / apps/studio_api/protocols.py L231-307
- 初始化散点：chapter_golden_path.py L95-99 `build_stub_master_controller` 只初始化 5 个 → stub controller 漏 init `_last_incremental_backfill` / `_last_memory_context` 是真实存在隐患（未来字段访问会 AttributeError）
- **mc_workflow.py L241** 裸写 `self._last_incremental_backfill = incremental_backfill` 未做 getattr 兜底 → 一旦与配合 stub 互动就炸

**收益**：
- **类型安全**：dataclass 强制 7 字段都有合法默认值（不再是「忘了 init」的随机 AttributeError）
- **原子更新**：`with_updates(**kwargs)` 一次返回新 instance，杜绝 mid-run 半设状态
- **可测性**：测试可直接 `WorkflowState(...)` 构造，无需 MasterController stub；refactor guard 防回潮
- **0 行为变更**：外部 API 不动；现有 357 dashboard + 84 cascade fix 维持

---

## 2. 架构与端点形态

### 2.1 端点（无变化）

`POST /api/workflows/run` / `POST /api/workflows/resume` / `GET /api/workflows/active` / `GET /api/decisions/pending` 路由契约（`apps/studio_api/routes/workflows.py`、`decisions.py`、`packages/lingwen-shared/src/lingwen_shared/contracts/python/workflows.py`、`decisions.py`）**保持不变**。

### 2.2 修改文件清单 (full blast radius — 17 files + 3 docs)

**新文件 (1)**：
- `packages/lingwen-core/src/lingwen_core/agents/workflow_state.py` — WorkflowState frozen dataclass (~30 行)

**源文件 modified (7)**：
- `packages/lingwen-pipeline/src/lingwen_pipeline/master_controller.py` — `__init__` L110-116 7 行 init → `self._state = WorkflowState.empty()`
- `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` — 7 处 `self._last_* = Y` 写 → 2 次 `self._state.with_updates(...)`；5 处 `getattr` 读 → `self._state.X` 直读
- `packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py` — `build_stub_master_controller` 5 行 init → `controller._state = WorkflowState.empty()`；L138 直读
- `packages/lingwen-core/src/lingwen_core/agents/production_summary.py` — `build_production_summary_from_controller` 5 处 getattr → 直读
- `packages/lingwen-core/src/lingwen_core/agents/got_bridge.py` — `getattr(self._master, "_last_initial_inputs", None)` → `self._master._state.initial_inputs`（测试 fake class 同改）
- `packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py` — `master._last_initial_inputs.get(...)` → `master._state.initial_inputs.get(...)`
- `apps/studio_api/protocols.py` — 5 处 `getattr(self._controller, "_last_*", ...)` → 直读

**测试文件 modified (8)** — 这些是 stub/类型 fake / 直接 controller 模拟：
- `tests/agent_system/test_chapter_emit.py` — `AgentComputeFn(type("_M", (), {"_last_initial_inputs": {...}})())` 改为 `{"_state": WorkflowState(initial_inputs={...})}`
- `tests/agent_system/test_production_summary.py` — 读侧 getattr 已变直接
- `tests/dashboard/test_app_workflow_production_summary_f66.py` — `master._last_* = X` 6 处 → `master._state = master._state.with_updates(...)`
- `tests/dashboard/test_app_workflow_status.py` — 同上 stub 模式
- `tests/dashboard/test_app_workflow_status_tier_budget.py` — L158-160 stub 改写
- `tests/dashboard/test_decision_api.py` — 6 处 stub 设置 (L693-695, L836-838, L960-962, L1013-1015, L1128+) 改写
- `tests/dashboard/test_protocols.py` — L175-177 stub 改写
- `tests/got/test_decision_pause_resume.py` — 10+ 处 stub 设置（L346-349, L394-397, L462-465, L496-498, L521-523, L575-577）+ reset 模式

**新测试 (1)**：
- `tests/agent_system/test_workflow_state.py` — WorkflowState 单元测试 6 + refactor guard 1 + sanity 1

**OUT OF SCOPE**（名字同前缀但语义不同）：
- `apps/studio_api/e2e_stub_controller.py::_last_workflow_status`（E2E stub 状态缓存，非 workflow cache）
- `apps/studio_api/routes/world.py::_last_access`（world rate limiter，非 workflow cache）
- `tests/dashboard/test_decision_api.py::_last_workflow_status`（controller decision status，与 workflow cache 不同）

`tests/test_workflow_state.py` **不动**（测的是顶层 `workflow_state.json` PHASE 状态文件，与 controller 内部 state 是两个概念，名字撞而已）。

### 2.3 架构不变量

- I001（infra 不 import apps）✅ 保持（`workflow_state.py` 在 `packages/lingwen-core/`，不引入新边缘）
- I005（创作流必须支持 checkpoint 恢复）✅ 保持（`resume_workflow` 仍读 `self._state.scheduler/graph/...`）
- **不新增不变量**

---

## 3. 组件与数据流

### 3.1 新文件 `workflow_state.py`

```python
"""MasterController 工作流状态快照 (Phase 26 P2-WFSTATE).

替代 v25.9 之前散落在 WorkflowMixin 上的 7 个 self._last_* 属性,
提供类型安全 + 原子更新 + 可直接构造以供测试。
"""

from __future__ import annotations
from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class WorkflowState:
    """MasterController 最近一次 run_workflow / resume_workflow 的状态快照.

    Frozen: 所有更新走 with_updates() 返回新实例, 防止 mid-run 部分写入.
    Defaults 强制 7 字段都存在 (不再有「漏 init 半初始化」风险).
    """
    scheduler: Any | None = None
    graph: Any | None = None
    workflow_name: str = ""
    start_nodes: list[str] = field(default_factory=list)
    initial_inputs: dict[str, Any] = field(default_factory=dict)
    incremental_backfill: Any | None = None
    memory_context: Any | None = None

    def with_updates(self, /, **kwargs: Any) -> "WorkflowState":
        """原子更新;返回带 override 的新实例. TypeError on 未知字段."""
        return replace(self, **kwargs)

    @classmethod
    def empty(cls) -> "WorkflowState":
        """构造空 state (测试 fixture / 桩用). 等价于 WorkflowState()."""
        return cls()
```

### 3.2 `WorkflowMixin.run_workflow`（mc_workflow.py 写入迁移）

```python
def run_workflow(self, workflow_name: str, ...) -> Dict[str, Any]:
    ...
    try:
        # ... (build_got_scheduler + pending_decisions 计算, 不变) ...

        # 预-run: 仅写 first 3 字段 (chapter_num 等节点读得到)
        self._state = self._state.with_updates(
            initial_inputs=dict(seed_inputs),
            workflow_name=workflow_name,
            start_nodes=list(start_nodes),
        )

        summary = scheduler.run(start_nodes=start_nodes, initial_inputs=seed_inputs)
        executions = self._collect_executions(graph)
        incremental_backfill = self._maybe_incremental_backfill(
            workflow_name=workflow_name, initial_inputs=seed_inputs,
            executions=executions, summary=summary,
        )

        # 后-run: 写剩余 4 字段, 一次原子
        self._state = self._state.with_updates(
            scheduler=scheduler,
            graph=graph,
            incremental_backfill=incremental_backfill,
            memory_context=memory_context,
        )

        return { "summary": summary, "graph": graph, ... }
    finally:
        self._current_budget_usd = None
        self._current_run_id = None
```

### 3.3 `WorkflowMixin.resume_workflow`（mc_workflow.py 读侧迁移）

```python
def resume_workflow(self, decision_id: str, option: str, resolved_by: str = "human"):
    # 1. 检查活跃工作流 (linter-friendly 直读, 默认空 state 不会 AttributeError)
    if self._state.scheduler is None or self._state.graph is None:
        raise RuntimeError("no active workflow; call run_workflow() first")

    # 2-4. (不变)
    ...
    decision = queue.get(decision_id)
    resolved = self.resolve_decision(decision_id, option, resolved_by)
    scheduler.resume(decision_node_id=decision.node_id, option=option, resolved_by=resolved_by)

    # 5. 扫描新 DECISION (用 .initial_inputs 直读)
    pending_decisions = self._harvest_decision_specs(graph, initial_inputs=self._state.initial_inputs)

    # 6. resume 重跑
    start_nodes = list(self._state.start_nodes)
    if not start_nodes:
        start_nodes = [nid for nid in graph.node_ids() if not graph.get_node(nid).depends_on]
    summary = scheduler.run(start_nodes=start_nodes)

    # 7. 收集
    executions = self._collect_executions(graph)
    incremental_backfill = self._maybe_incremental_backfill(
        workflow_name=self._state.workflow_name,
        initial_inputs=self._state.initial_inputs,
        executions=executions,
        summary=summary,
    )
    self._state = self._state.with_updates(incremental_backfill=incremental_backfill)

    return { ... }
```

### 3.4 Stub master 初始化（chapter_golden_path.py L83-102）

```python
def build_stub_master_controller(state_dir: Path) -> Any:
    from lingwen_core.agents.decision_queue import HumanDecisionQueue
    from lingwen_core.agents.workflow_state import WorkflowState
    from lingwen_pipeline.master_controller import MasterController

    controller = MasterController.__new__(MasterController)
    controller._decision_queue = HumanDecisionQueue(state_dir=str(state_dir))
    controller._config = None
    controller._router = None
    controller._orchestrator = None
    controller._skill_registry = None
    controller._state_manager = None
    controller._state = WorkflowState.empty()  # NEW: 一次性 7 字段初始化
    controller._incremental_backfill_enabled = None
    controller._memory_rag_mode = "stub"
    return controller
```

L138 `controller._last_initial_inputs.get("memory_context")` → `controller._state.initial_inputs.get("memory_context")`

### 3.5 测试 stub 模式迁移（覆盖 8 个测试文件）

**模式 A（MasterController stub init）**：`tests/got/test_decision_pause_resume.py` 风格的多行 init：

```python
# 改前
controller._last_scheduler = None
controller._last_graph = None
controller._last_workflow_name = None
controller._last_start_nodes = []
controller._last_initial_inputs = {}

# 改后
from lingwen_core.agents.workflow_state import WorkflowState
controller._state = WorkflowState.empty()
```

**模式 B（run 之后状态注入）**：`_last_X = X` 模拟 run_workflow 已发生：

```python
# 改前
controller._last_scheduler = scheduler
controller._last_graph = graph
controller._last_workflow_name = "wf_resume"
controller._last_start_nodes = ["a"]

# 改后
controller._state = controller._state.with_updates(
    scheduler=scheduler,
    graph=graph,
    workflow_name="wf_resume",
    start_nodes=["a"],
)
```

**模式 C（master 类型 fake 满足 AgentComputeFn 读）**：`test_chapter_emit.py` 风格：

```python
# 改前（fake type 暴露 _last_initial_inputs 给 AgentComputeFn 读）
compute = AgentComputeFn(type("_M", (), {"_last_initial_inputs": {"chapter_num": 1}})())

# 改后（fake 暴露 _state.initial_inputs）
compute = AgentComputeFn(type("_M", (), {"_state": WorkflowState(initial_inputs={"chapter_num": 1})})())
```

8 测试文件按实际模式 A/B/C 改写，断言不变。

### 3.6 数据流（读侧）

| Reader | 改前 | 改后 |
|---|---|---|
| `production_summary.build_production_summary_from_controller` L62-76 | `getattr(controller, "_last_graph", None)` × 5 | `controller._state.graph` 等直读 |
| `got_bridge.py L302` | `master._last_initial_inputs` | `master._state.initial_inputs` |
| `chapter_production_pilot.py L440` | `master._last_initial_inputs.get(...)` | `master._state.initial_inputs.get(...)` |
| `studio_api/protocols.py L231-307` | `getattr(self._controller, "_last_*", ...)` × 5 | `self._controller._state.*` 直读 |

### 3.7 `MasterController.__init__` 迁移（master_controller.py L110-116）

```python
def __init__(self, ...):
    ...
    # 改前 — 7 个散点 default 初始化
    self._last_scheduler: Optional[Any] = None
    self._last_graph: Optional[Any] = None
    self._last_workflow_name: Optional[str] = None
    self._last_start_nodes: List[str] = []
    self._last_initial_inputs: Dict[str, Any] = {}
    self._last_incremental_backfill: Any = None
    self._last_memory_context: Optional[Dict[str, Any]] = None

    # 改后 — 一次原子 dataclass 初始化
    self._state = WorkflowState.empty()
```

`import`: 文件顶部加 `from lingwen_core.agents.workflow_state import WorkflowState`（确保 `master_controller.py` 已在 `lingwen-pipeline`，import 不破 I001 边界）。

### 3.8 复用与新文件

| 类型 | 新增 | 复用 |
|---|---|---|
| WorkflowState | `workflow_state.py` ~30 行 dataclass | 现有语义（保留默认 7 字段 + 5 字段当前 dataclass 默认值形态） |
| `WorkflowMixin.run_workflow` | — | 现有 `build_got_scheduler` / `_harvest_decision_specs` / `_maybe_*` helpers |
| `MasterController.__init__` | — | 现有 `__init__` 其他 init body 保持不变 |
| 测试 | `tests/agent_system/test_workflow_state.py` | 现有 `chapter_golden_path` + `protocols` + 8 个 stub/fake 模式 |

---

## 4. 错误处理 + 边界

| 场景 | 行为 |
|---|---|
| `self._state.with_updates(unknown_field=1)` | `TypeError: __init__() got unexpected keyword 'unknown_field'` — 写入点 fail-fast |
| `self._state.scheduler = X` | `dataclasses.FrozenInstanceError` — 编译/运行立即挂 |
| Stub controller 漏 init `_state` 属性 | 任何 `self._state.X` 访问 → `AttributeError(_state)`（明显比「漏 init 某个具体字段」好定位） |
| `run_workflow` 中途异常 | `_state.with_updates` 已分两步原子切换；预-run 设了的字段保持 post-run 失败不变（**注意**：这是行为微调——之前异常时已设的 `_last_*` 也保留，新行为对齐） |
| `resume_workflow` 在未 run 时调用 | `RuntimeError("no active workflow")`（与原行为一致，仅读取路径换形式） |
| `_harvest_decision_specs` 传 `initial_inputs=None`（`mc_workflow.py L347` 兜底场景） | 改为不需兜底 — `self._state.initial_inputs` 必为 dict（默认 `{}`） |

---

## 5. 提交结构（4 commits + 1 docs prelude, atomic）

| # | Commit | 内容 |
|---|---|---|
| 1 | `docs(phase-26): wfstate refactor design` | spec（本文件） |
| 2 | `docs(phase-26): wfstate refactor plan` | plan |
| 3 | `feat(lingwen-core): add WorkflowState dataclass` | 新文件 workflow_state.py |
| 4 | `refactor: migrate _last_* → _state WorkflowState (7 source + 8 test)` | master_controller.py:110-116 + mc_workflow.py + chapter_golden_path.py + production_summary.py + got_bridge.py + chapter_production_pilot.py + apps/studio_api/protocols.py + 8 测试文件 (模式 A/B/C 按 §3.5) |
| 5 | `test(agent-system): workflow_state unit + refactor guard` | tests/agent_system/test_workflow_state.py |

（commit 4 预估净增 ~150 行（src ~75 + tests ~75），未超 800 行阈值，不需要 4a/4b 拆分；如实测超，按需拆分但 refactor guard 仍只在 commit 5 才挂上）

**baseline → target 测试数**：
- `tests/dashboard`: 357 passed + 3 skipped → **357 passed + 3 skipped**（**不变**——0 行为变更）
- `tests/cross_volume/test_incremental_backfill.py`: 15 passed → 15 passed（**不变**）
- `tests/agent_system` 关联用例：ZERO 新增失败（不变，因 mixin 行为对齐原状）
- `tests/agent_system/test_workflow_state.py`：**+8 新增**（unit 6 + refactor guard 1 + sanity 1）

---

## 6. 风险矩阵

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 漏迁移某个 `_last_*` 读写 site → runtime AttributeError | 中 | 高 | spec §2.2 列出完整 16 文件清单 + post-commit grep（见 §7）严格验证（仅 `e2e_stub_controller._last_workflow_status` + `routes/world._last_access` 留 — 与本 refactor 无关） |
| `MasterController.__init__` 漏改 → 所有 production MasterController 实例无 `_state` → 任何方法 NPE | 中 | 高 | spec §3.7 明确迁移代码；commit 4 grep 全检 `master_controller.py` 全部 __init__ 已不出现 7 个 `_last_X = ...` |
| `with_updates` 误传 None vs 未传导致行为微差 | 低 | 中 | frozen dataclass 行为明确：`with_updates(x=None)` 等于显式 None，与「未传」默认 None 等价（除非默认非 None 的字段如 `workflow_name`） |
| stub controller `WorkflowState.empty()` 替换 5 行 init 引发 fixture 漏字段 | 低 | 低 | refactor guard 测试兜底，CI 即知 |
| dataclass(frozen=True) + `default_factory` 测试断言深嵌套行为 | 低 | 低 | unit test 6 case 覆盖 |
| `chapter_production_pilot.py` / `got_bridge.py` 等 reader 漏改 → runtime AttributeError | 中 | 高 | spec §2.2 全列，post-commit grep 全检 reader site |
| 8 个测试文件 stub 模式 A/B/C 之一识别错（实际是 A 写成 B） | 中 | 中 | spec §3.5 给出 3 模式完整 find-replace 对照；test 改完跑该文件应 100% pass（vs 未改 baseline） |

---

## 7. 验证门（Phase 26 closure）

- ruff check + ruff format --check clean
- 后端 pytest:
  - `tests/dashboard`: 357 passed + 3 skipped（**不变**）
  - `tests/cross_volume/test_incremental_backfill.py`: 15 passed（**不变**）
  - `tests/got`: ZERO 新增失败（test_decision_pause_resume.py 等 8 文件改写后行为不变）
  - `tests/agent_system`: ZERO 新增失败；`test_workflow_state.py` **+8 通过**（unit 6 + refactor guard 1 + sanity 1）
  - 全量 `tests/`（含 studio_api、shared、llm）绿
- grep 验证（**精确 7 字段**，避免误伤 `_last_workflow_status` / `_last_access`）:
  ```bash
  grep -rn "_last_scheduler\|_last_graph\|_last_workflow_name\|_last_start_nodes\|_last_initial_inputs\|_last_incremental_backfill\|_last_memory_context" \
      packages/lingwen-core/ packages/lingwen-pipeline/ apps/studio_api/ tests/ 2>/dev/null
  # 应 = 0 hits
  ```
  - 例外允许（不在本 refactor 范围内，名字不同前缀易误伤，但本 grep 已用精确字段名，不会扫到）：
    - `apps/studio_api/e2e_stub_controller.py::_last_workflow_status`（不会匹配）
    - `apps/studio_api/routes/world.py::_last_access`（不会匹配）
- 前端：unaffected（untracked 改动 = 0）

---

## 8. 实施后结构变更

```
packages/lingwen-pipeline/src/lingwen_pipeline/
└── master_controller.py                                    ← MODIFIED (L110-116: 7 行 init → 1 行 dataclass init)
packages/lingwen-core/src/lingwen_core/agents/
├── mc_workflow.py                                          ← MODIFIED (~40 行 diff)
├── chapter_golden_path.py                                  ← MODIFIED (~10 行 diff: stub init + L138 read)
├── production_summary.py                                   ← MODIFIED (~10 行 diff: 5 getattr → 直读)
├── got_bridge.py                                           ← MODIFIED (1 行 diff: read site)
├── chapter_production_pilot.py                             ← MODIFIED (1 行 diff: read site)
└── workflow_state.py                                       ← NEW (~30 行)
apps/studio_api/protocols.py                                ← MODIFIED (~10 行 diff: 5 getattr → 直读)
tests/agent_system/
├── test_chapter_emit.py                                    ← MODIFIED (mock 类型 fake: 模式 C)
├── test_production_summary.py                              ← MODIFIED (assertion 调整)
└── test_workflow_state.py                                  ← NEW (~70 行: 6 unit + 1 guard + 1 sanity)
tests/dashboard/
├── test_app_workflow_production_summary_f66.py             ← MODIFIED (~10 行 stub setup: 模式 B)
├── test_app_workflow_status.py                             ← MODIFIED (stub setup)
├── test_app_workflow_status_tier_budget.py                 ← MODIFIED (L158-160 stub: 模式 B)
├── test_decision_api.py                                    ← MODIFIED (6 处 stub: L693+ 等: 模式 B)
└── test_protocols.py                                       ← MODIFIED (L175-177 stub: 模式 B)
tests/got/
└── test_decision_pause_resume.py                           ← MODIFIED (10+ 处 stub + reset: 模式 A + B)
docs/superpowers/specs/2026-09-03-phase-26-wfstate-design.md ← NEW（本文件）
docs/superpowers/plans/2026-09-03-phase-26-wfstate.md       ← NEW
docs/superpowers/handoffs/2026-09-03-phase-26-wfstate-handoff.md ← NEW
```

总计: **1 new source + 15 modified source (7 src + 8 test) + 1 new test = 17 files** + 3 docs.

---

## 9. Carryover to Phase 27+（**不在本阶段**）

- **P2-WFRUNNER**：WorkflowRunner service 拆分（建议紧接着 Phase 26 之后）
- **P2-RESUME-VERIFY**：`start_nodes=None` 时 `resume_workflow` 重跑行为 E2E 验证
- **P2-MC-WRITING**：84 pre-existing cascade failures 根因调查（mc_writing.py 类似 gutted？）
- **P2-ARCHDEBT**：infra.got 迁移 / chapter_golden_path 反向 import 整改 / HANDOFF 措辞修订
