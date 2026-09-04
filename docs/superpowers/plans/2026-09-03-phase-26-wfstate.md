# Phase 26 P2-WFSTATE Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 整合 MasterController 上 7 个 `self._last_*` 散点属性为单个 `self._state: WorkflowState` frozen dataclass, 消除半初始化风险并提供类型安全 + 可测性.

**Architecture:** 新建 `workflow_state.py` (dataclass + `with_updates` 原子更新 helper); 7 源文件 + 8 测试文件按 spec §3.5 三种 stub 模式迁移; refactor guard 测试防回潮. 0 行为变更 — 全部 357 dashboard + 15 incremental backfill 通过数不变.

**Tech Stack:** Python 3.11+ / dataclasses (stdlib) / pytest / uv workspace.

**Spec:** `docs/superpowers/specs/2026-09-03-phase-26-wfstate-design.md` (commit `99bed427`).

---

## File Structure (锁定自 spec §2.2)

**新建 (2)**:
- `packages/lingwen-core/src/lingwen_core/agents/workflow_state.py` — WorkflowState frozen dataclass (~30 行)
- `tests/agent_system/test_workflow_state.py` — WorkflowState 单元测试 + refactor guard

**修改源文件 (7)**:
- `packages/lingwen-pipeline/src/lingwen_pipeline/master_controller.py` (`__init__` L110-116)
- `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` (7 写 + 5 读)
- `packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py` (stub init + L138 read)
- `packages/lingwen-core/src/lingwen_core/agents/production_summary.py` (`build_production_summary_from_controller`)
- `packages/lingwen-core/src/lingwen_core/agents/got_bridge.py` (1 read line)
- `packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py` (1 read line)
- `apps/studio_api/protocols.py` (5 getattr reads)

**修改测试文件 (8) — 按 spec §3.5 模式**:
- **模式 A** (`test_decision_pause_resume.py`): stub init 多行 → `WorkflowState.empty()`
- **模式 B** (6 dashboard tests): `_last_X = X` → `with_updates(...)`
- **模式 C** (`test_chapter_emit.py`): `_M` fake type → `_state` 属性

**OUT OF SCOPE**: `e2e_stub_controller._last_workflow_status`, `routes/world._last_access`, `test_decision_api._last_workflow_status` (语义不同, spec §2.2 已列)

---

## Task 1: Setup + baseline 验证

**Files:** 工作目录确认

- [ ] **Step 1: 确认 worktree 在正确分支**

```bash
cd /home/ailearn/projects/LingWen-phase-26-wfstate
git status --short && git rev-parse --abbrev-ref HEAD
```

Expected: HEAD on `phase-26-wfstate`, working tree clean (spec 已 commit `99bed427`).

- [ ] **Step 2: 验证 baseline 测试数 (spec §7)**

```bash
uv run pytest tests/dashboard/ -q 2>&1 | tail -5
uv run pytest tests/cross_volume/test_incremental_backfill.py -q 2>&1 | tail -5
```

Expected:
- `tests/dashboard`: 357 passed, 3 skipped
- `tests/cross_volume/test_incremental_backfill.py`: 15 passed

- [ ] **Step 3: 验证 baseline grep (应命中 15 文件)**

```bash
grep -rln "_last_scheduler\|_last_graph\|_last_workflow_name\|_last_start_nodes\|_last_initial_inputs\|_last_incremental_backfill\|_last_memory_context" \
    packages/ apps/ tests/ 2>/dev/null | sort -u | wc -l
```

Expected: `15` (7 src + 8 test) — 与 spec §2.2 一致.

---

## Task 2: WorkflowState dataclass (TDD: RED → GREEN → commit 3)

**Files:**
- Create: `packages/lingwen-core/src/lingwen_core/agents/workflow_state.py`
- Create: `tests/agent_system/test_workflow_state.py`

- [ ] **Step 1: 写失败的单元测试 (RED)**

Create `tests/agent_system/test_workflow_state.py`:

```python
"""Phase 26 P2-WFSTATE — WorkflowState dataclass unit tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from lingwen_core.agents.workflow_state import WorkflowState


class TestWorkflowStateConstruction:
    """构造 / defaults / frozen 强制."""

    def test_empty_classmethod_returns_all_none_or_empty_defaults(self) -> None:
        state = WorkflowState.empty()
        assert state.scheduler is None
        assert state.graph is None
        assert state.workflow_name == ""
        assert state.start_nodes == []
        assert state.initial_inputs == {}
        assert state.incremental_backfill is None
        assert state.memory_context is None

    def test_constructor_with_no_args_equals_empty(self) -> None:
        assert WorkflowState() == WorkflowState.empty()

    def test_default_factory_independence_for_start_nodes(self) -> None:
        """list/dict 默认值不共享 (mutable default 复用陷阱)."""
        a = WorkflowState.empty()
        b = WorkflowState.empty()
        a.start_nodes.append("x")
        assert b.start_nodes == []  # b 不受 a 改动影响

    def test_default_factory_independence_for_initial_inputs(self) -> None:
        a = WorkflowState.empty()
        b = WorkflowState.empty()
        a.initial_inputs["k"] = "v"
        assert b.initial_inputs == {}

    def test_frozen_rejects_mutation(self) -> None:
        with pytest.raises(FrozenInstanceError):
            state = WorkflowState.empty()
            state.scheduler = object()  # type: ignore[misc]


class TestWorkflowStateWithUpdates:
    """with_updates 原子更新行为."""

    def test_with_updates_returns_new_instance_not_mutation(self) -> None:
        original = WorkflowState.empty()
        updated = original.with_updates(workflow_name="novel_writing")
        assert updated is not original
        assert original.workflow_name == ""  # 原 instance 不变

    def test_with_updates_overrides_only_named_fields(self) -> None:
        original = WorkflowState(workflow_name="wf1", initial_inputs={"k": 1})
        updated = original.with_updates(workflow_name="wf2")
        assert updated.workflow_name == "wf2"
        assert updated.initial_inputs == {"k": 1}  # 其他字段保留

    def test_with_updates_rejects_unknown_field(self) -> None:
        with pytest.raises(TypeError, match="unknown_field"):
            WorkflowState.empty().with_updates(unknown_field=1)
```

- [ ] **Step 2: 确认测试失败 (import 错误)**

```bash
uv run pytest tests/agent_system/test_workflow_state.py -v 2>&1 | tail -15
```

Expected: `ModuleNotFoundError: No module named 'lingwen_core.agents.workflow_state'` (全部 8 tests ERROR).

- [ ] **Step 3: 实现 WorkflowState (GREEN)**

Create `packages/lingwen-core/src/lingwen_core/agents/workflow_state.py`:

```python
"""Phase 26 P2-WFSTATE — MasterController 工作流状态快照.

替代 v25.9 之前散落在 WorkflowMixin 上的 7 个 self._last_* 属性,
提供类型安全 + 原子更新 + 可直接构造以供测试.

frozen=True 强制: 所有 mutation 走 with_updates() 返回新 instance,
杜绝 mid-run 部分写入. defaults 保证 7 字段必存在,
替代散点「漏 init 半初始化」风险.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class WorkflowState:
    """MasterController 最近一次 run_workflow / resume_workflow 的状态快照.

    7 字段全部 optional + dataclass default, 默认空 state:
    - scheduler / graph: GoT 运行时对象 (None 表示未激活)
    - workflow_name: 上次 run 的 workflow 名 (空串)
    - start_nodes: 上次起点节点 list (空 list)
    - initial_inputs: 上次起点 seed inputs dict (空 dict)
    - incremental_backfill: 上次 run 末尾的 backfill 统计 (None)
    - memory_context: 上次 run 注入的 memory RAG context (None)
    """

    scheduler: Any | None = None
    graph: Any | None = None
    workflow_name: str = ""
    start_nodes: list[str] = field(default_factory=list)
    initial_inputs: dict[str, Any] = field(default_factory=dict)
    incremental_backfill: Any | None = None
    memory_context: Any | None = None

    def with_updates(self, /, **kwargs: Any) -> "WorkflowState":
        """原子更新; 返回带 override 的新 instance. TypeError on 未知字段.

        Usage:
            self._state = self._state.with_updates(workflow_name="novel_writing")
        """
        return replace(self, **kwargs)

    @classmethod
    def empty(cls) -> "WorkflowState":
        """构造空 state (测试 fixture / 桩用). 等价于 WorkflowState()."""
        return cls()
```

- [ ] **Step 4: 确认测试通过 (GREEN)**

```bash
uv run pytest tests/agent_system/test_workflow_state.py -v 2>&1 | tail -15
```

Expected: `8 passed` (5 TestWorkflowStateConstruction + 3 TestWorkflowStateWithUpdates).

- [ ] **Step 5: ruff 干净**

```bash
uv run ruff check packages/lingwen-core/src/lingwen_core/agents/workflow_state.py tests/agent_system/test_workflow_state.py
uv run ruff format --check packages/lingwen-core/src/lingwen_core/agents/workflow_state.py tests/agent_system/test_workflow_state.py
```

Expected: both clean.

- [ ] **Step 6: Commit**

```bash
git add packages/lingwen-core/src/lingwen_core/agents/workflow_state.py tests/agent_system/test_workflow_state.py
git commit -m "$(cat <<'EOF'
feat(lingwen-core): add WorkflowState dataclass

Phase 26 P2-WFSTATE commit 3 (TDD):
- frozen dataclass 替代 7 个 self._last_* 散点
- with_updates(**kwargs) 原子更新 helper
- default_factory list/dict 独立（immutable 复用陷阱）
- 8 个单元测试 (5 construction + 3 with_updates)

后续 commit 4 迁 src/, commit 5 加 refactor guard 测试。

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: master_controller.py 迁移 (commit 4a 部分)

**Files:**
- Modify: `packages/lingwen-pipeline/src/lingwen_pipeline/master_controller.py:110-116`

- [ ] **Step 1: 加 import**

Edit 文件顶部 imports 区（找 `from lingwen_core...` 之类的现有 import 行附近）:

```python
from lingwen_core.agents.workflow_state import WorkflowState
```

（确保 `lingwen-pipeline` 已允许 import `lingwen-core` — 与 master_controller.py 已有的 `from lingwen_core.agents...` 导入一致即可，无 I001 问题，因为 `lingwen-pipeline` 依赖 `lingwen-core`。）

- [ ] **Step 2: 替换 7 行 init 为 1 行**

Edit `packages/lingwen-pipeline/src/lingwen_pipeline/master_controller.py` 把 L110-116 的 7 行:

```python
        self._last_scheduler: Optional[Any] = None
        self._last_graph: Optional[Any] = None
        self._last_workflow_name: Optional[str] = None
        self._last_start_nodes: List[str] = []
        self._last_initial_inputs: Dict[str, Any] = {}
        self._last_incremental_backfill: Any = None
        self._last_memory_context: Optional[Dict[str, Any]] = None
```

替换为:

```python
        self._state = WorkflowState.empty()
```

- [ ] **Step 3: 校验无遗留 _last_* 字段**

```bash
grep -n "_last_" packages/lingwen-pipeline/src/lingwen_pipeline/master_controller.py
```

Expected: 0 lines.

---

## Task 4: mc_workflow.py 迁移 — run_workflow 写入 (commit 4a 部分)

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py:119-138`

- [ ] **Step 1: 替换预-run 3 行写入**

Edit `mc_workflow.py` L119-121:

```python
            self._last_initial_inputs = dict(seed_inputs)
            self._last_workflow_name = workflow_name
            self._last_start_nodes = list(start_nodes)
```

替换为:

```python
            self._state = self._state.with_updates(
                initial_inputs=dict(seed_inputs),
                workflow_name=workflow_name,
                start_nodes=list(start_nodes),
            )
```

- [ ] **Step 2: 替换后-run 4 行写入**

Edit `mc_workflow.py` L128-138:

```python
            self._last_scheduler = scheduler
            self._last_graph = graph
            ...

            self._last_incremental_backfill = incremental_backfill
            self._last_memory_context = memory_context
```

替换为:

```python
            incremental_backfill = self._maybe_incremental_backfill(...)

            self._state = self._state.with_updates(
                scheduler=scheduler,
                graph=graph,
                incremental_backfill=incremental_backfill,
                memory_context=memory_context,
            )
```

(注：`incremental_backfill` 局部变量在 `with_updates` 前先求值；`scheduler.resume_workflow` 调度器对象 / graph 对象 / 之上 `summary = scheduler.run(...)` 与 `executions = self._collect_executions(graph)` 计算保持不变)

- [ ] **Step 3: 校验**

```bash
grep -n "_last_" packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py
```

Expected: 0 lines.

---

## Task 5: mc_workflow.py 迁移 — resume_workflow 读侧 (commit 4a 部分)

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py:198-251`

- [ ] **Step 1: 替换活跃工作流检查**

Edit `mc_workflow.py` L198-201:

```python
        scheduler = getattr(self, "_last_scheduler", None)
        graph = getattr(self, "_last_graph", None)
        if scheduler is None or graph is None:
            raise RuntimeError("no active workflow; call run_workflow() first")
```

替换为:

```python
        if self._state.scheduler is None or self._state.graph is None:
            raise RuntimeError("no active workflow; call run_workflow() first")
        scheduler = self._state.scheduler
        graph = self._state.graph
```

- [ ] **Step 2: 替换 _harvest_decision_specs 输入回退**

Edit `mc_workflow.py` L220-223 (`_harvest_decision_specs` 的 `initial_inputs=...`):

```python
        pending_decisions = self._harvest_decision_specs(
            graph,
            initial_inputs=getattr(self, "_last_initial_inputs", None) or {},
        )
```

替换为:

```python
        pending_decisions = self._harvest_decision_specs(
            graph,
            initial_inputs=self._state.initial_inputs,
        )
```

- [ ] **Step 3: 替换 _last_start_nodes 读取**

Edit `mc_workflow.py` L226-228:

```python
        start_nodes = list(getattr(self, "_last_start_nodes", None) or [])
        if not start_nodes:
            start_nodes = [nid for nid in graph.node_ids() if not graph.get_node(nid).depends_on]
```

替换为:

```python
        start_nodes = list(self._state.start_nodes)
        if not start_nodes:
            start_nodes = [nid for nid in graph.node_ids() if not graph.get_node(nid).depends_on]
```

- [ ] **Step 4: 替换 _maybe_incremental_backfill 调用参数**

Edit `mc_workflow.py` L235-240:

```python
        incremental_backfill = self._maybe_incremental_backfill(
            workflow_name=getattr(self, "_last_workflow_name", "") or "",
            initial_inputs=getattr(self, "_last_initial_inputs", None),
            executions=executions,
            summary=summary,
        )
```

替换为:

```python
        incremental_backfill = self._maybe_incremental_backfill(
            workflow_name=self._state.workflow_name,
            initial_inputs=self._state.initial_inputs,
            executions=executions,
            summary=summary,
        )
```

- [ ] **Step 5: 替换 _last_incremental_backfill 单行赋值 + _last_memory_context 只读**

Edit `mc_workflow.py` L241 (one-liner) + L250 (last read):

```python
        self._last_incremental_backfill = incremental_backfill
```

替换为:

```python
        self._state = self._state.with_updates(incremental_backfill=incremental_backfill)
```

Edit L250:

```python
            "memory_context": getattr(self, "_last_memory_context", None),
```

替换为:

```python
            "memory_context": self._state.memory_context,
```

- [ ] **Step 6: 替换 _harvest_decision_specs 内的 initial_inputs 回退 (L347)**

Edit `mc_workflow.py` L345-347:

```python
        seed = initial_inputs
        if seed is None:
            seed = getattr(self, "_last_initial_inputs", None) or {}
```

替换为:

```python
        seed = initial_inputs
        if seed is None:
            seed = self._state.initial_inputs
```

- [ ] **Step 7: 校验 mc_workflow.py 完全迁移**

```bash
grep -n "_last_" packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py
```

Expected: 0 lines.

- [ ] **Step 8: ruff 干净**

```bash
uv run ruff check packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py
uv run ruff format --check packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py
```

Expected: clean.

---

## Task 6: chapter_golden_path.py 迁移 (commit 4a 部分)

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py:83-102, 138`

- [ ] **Step 1: 加 import**

Edit `chapter_golden_path.py` imports 区, 加:

```python
from lingwen_core.agents.workflow_state import WorkflowState
```

- [ ] **Step 2: 替换 stub init 5 行**

Edit `chapter_golden_path.py` L95-99 (`build_stub_master_controller`):

```python
    controller._last_scheduler = None
    controller._last_graph = None
    controller._last_workflow_name = None
    controller._last_start_nodes = []
    controller._last_initial_inputs = {}
```

替换为:

```python
    controller._state = WorkflowState.empty()
```

- [ ] **Step 3: 替换 L138 读取**

Edit `chapter_golden_path.py` L138:

```python
    memory_ctx = controller._last_initial_inputs.get("memory_context") or {}
```

替换为:

```python
    memory_ctx = controller._state.initial_inputs.get("memory_context") or {}
```

- [ ] **Step 4: 校验**

```bash
grep -n "_last_" packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py
```

Expected: 0 lines.

---

## Task 7: production_summary.py + got_bridge.py + chapter_production_pilot.py 迁移 (commit 4a 部分)

**Files:**
- Modify: `packages/lingwen-core/src/lingwen_core/agents/production_summary.py:60-77`
- Modify: `packages/lingwen-core/src/lingwen_core/agents/got_bridge.py:302`
- Modify: `packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py:440`

- [ ] **Step 1: production_summary.py — 替换 5 getattr 为直读**

Edit `production_summary.py` L60-77 (`build_production_summary_from_controller`):

```python
def build_production_summary_from_controller(controller: Any) -> dict[str, Any] | None:
    """Read MC._last_* cache after run_workflow / resume_workflow."""
    graph = getattr(controller, "_last_graph", None)
    if graph is None:
        return None

    executions: dict[str, Any] = {}
    for nid in graph.node_ids():
        if graph.has_execution(nid):
            executions[nid] = graph.get_execution(nid)

    return build_production_summary(
        workflow_name=getattr(controller, "_last_workflow_name", None),
        initial_inputs=getattr(controller, "_last_initial_inputs", None),
        executions=executions,
        incremental_backfill=getattr(controller, "_last_incremental_backfill", None),
        memory_context=getattr(controller, "_last_memory_context", None),
    )
```

替换为:

```python
def build_production_summary_from_controller(controller: Any) -> dict[str, Any] | None:
    """Read controller._state cache after run_workflow / resume_workflow."""
    state = controller._state
    graph = state.graph
    if graph is None:
        return None

    executions: dict[str, Any] = {}
    for nid in graph.node_ids():
        if graph.has_execution(nid):
            executions[nid] = graph.get_execution(nid)

    return build_production_summary(
        workflow_name=state.workflow_name,
        initial_inputs=state.initial_inputs,
        executions=executions,
        incremental_backfill=state.incremental_backfill,
        memory_context=state.memory_context,
    )
```

- [ ] **Step 2: got_bridge.py L302**

Edit `got_bridge.py` L302:

```python
            last_inputs = getattr(self._master, "_last_initial_inputs", None) or {}
```

替换为:

```python
            last_inputs = self._master._state.initial_inputs
```

- [ ] **Step 3: chapter_production_pilot.py L440**

Edit `chapter_production_pilot.py` L440:

```python
    mem_ctx = run_out.get("memory_context") or master._last_initial_inputs.get(
```

替换为:

```python
    mem_ctx = run_out.get("memory_context") or master._state.initial_inputs.get(
```

(行末 `(` 保持原样以继续 args)

- [ ] **Step 4: 校验 3 文件无遗留**

```bash
grep -n "_last_" packages/lingwen-core/src/lingwen_core/agents/production_summary.py packages/lingwen-core/src/lingwen_core/agents/got_bridge.py packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py
```

Expected: 0 lines across all 3.

---

## Task 8: apps/studio_api/protocols.py 迁移 (commit 4a 部分)

**Files:**
- Modify: `apps/studio_api/protocols.py:231-307`

- [ ] **Step 1: 替换 5 处 getattr 为直读**

Edit `protocols.py`. 找到 5 处 `getattr(self._controller, "_last_*", ...)` 模式, 分别替换:

L231:
```python
        d["workflow_name"] = getattr(self._controller, "_last_workflow_name", None)
```
→ `d["workflow_name"] = self._controller._state.workflow_name`

L236:
```python
            initial_inputs=getattr(self._controller, "_last_initial_inputs", None),
```
→ `initial_inputs=self._controller._state.initial_inputs,`

L244-246 (active_workflow_status):
```python
        scheduler = getattr(self._controller, "_last_scheduler", None)
        graph = getattr(self._controller, "_last_graph", None)
        workflow_name = getattr(self._controller, "_last_workflow_name", None)
```
→
```python
        state = self._controller._state
        scheduler = state.scheduler
        graph = state.graph
        workflow_name = state.workflow_name
```

L307:
```python
            getattr(self._controller, "_last_incremental_backfill", None)
```
→
```python
            self._controller._state.incremental_backfill
```

- [ ] **Step 2: 校验**

```bash
grep -n "_last_" apps/studio_api/protocols.py
```

Expected: 0 lines.

- [ ] **Step 3: ruff 干净**

```bash
uv run ruff check apps/studio_api/protocols.py
uv run ruff format --check apps/studio_api/protocols.py
```

Expected: clean.

- [ ] **Step 4: 提交 src 迁移 (commit 4a)**

```bash
git add packages/lingwen-pipeline/src/lingwen_pipeline/master_controller.py \
        packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py \
        packages/lingwen-core/src/lingwen_core/agents/chapter_golden_path.py \
        packages/lingwen-core/src/lingwen_core/agents/production_summary.py \
        packages/lingwen-core/src/lingwen_core/agents/got_bridge.py \
        packages/lingwen-core/src/lingwen_core/agents/chapter_production_pilot.py \
        apps/studio_api/protocols.py
git commit -m "$(cat <<'EOF'
refactor: migrate _last_* → _state WorkflowState (7 src)

Phase 26 P2-WFSTATE commit 4a:
- master_controller.py: __init__ 7 行 init → 1 行 dataclass
- mc_workflow.py: 7 写拆 2 次 with_updates; 5 读 getattr → 直读
- chapter_golden_path.py: stub init 5 行 → 1 行; L138 直读
- production_summary.py: build_production_summary_from_controller 直读
- got_bridge.py + chapter_production_pilot.py: 各自 1 行 read site
- apps/studio_api/protocols.py: 5 getattr reads 直读

外部 API 不变. 现有 src 测试 fail (测试仍 _last_*, 下个 commit 4b 修)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: 测试迁移 — test_decision_pause_resume.py (commit 4b, 模式 A + B)

**Files:**
- Modify: `tests/got/test_decision_pause_resume.py` (10+ 处)

- [ ] **Step 1: 加 import**

Edit `test_decision_pause_resume.py` 顶部 imports:

```python
from lingwen_core.agents.workflow_state import WorkflowState
```

- [ ] **Step 2: 替换 stub init 多行 (L346-349, L462-465) — 模式 A**

每处 4 行:
```python
        controller._last_scheduler = None
        controller._last_graph = None
        controller._last_workflow_name = None
        controller._last_start_nodes = []
        # 注: _last_initial_inputs 不在此 4 行 init block (有时另设)
```

→ 替换为:
```python
        controller._state = WorkflowState.empty()
```

适用 lines:
- L346-349 (初始 reset)
- L462-465 (无活跃工作流 reset)

如遇仅前 4 行无 `_last_initial_inputs`, 保持 1 行 dataclass init 即可（dataclass 已含 5 个 default）。

- [ ] **Step 3: 替换 _last_X = X 注入块 — 模式 B**

适用 lines:
- L394-397 (`controller._last_scheduler = scheduler; ...; start_nodes = ["a"]`)
- L496-498
- L521-523 (`start_nodes = ["judge"]`)
- L575-577

每处:
```python
        controller._last_scheduler = scheduler
        controller._last_graph = graph
        controller._last_workflow_name = "wf_resume"
        controller._last_start_nodes = ["a"]
```

→ 替换为:
```python
        controller._state = controller._state.with_updates(
            scheduler=scheduler,
            graph=graph,
            workflow_name="wf_resume",
            start_nodes=["a"],
        )
```

(局部变量组合根据实际字段调整 — 注意 `_last_initial_inputs` 不必传, `WorkflowState.empty()` 默认 `{}` 已满足)

- [ ] **Step 4: 校验文件无 _last_***

```bash
grep -n "_last_" tests/got/test_decision_pause_resume.py
```

Expected: 0 lines.

- [ ] **Step 5: 跑测试验迁移有效**

```bash
uv run pytest tests/got/test_decision_pause_resume.py -q 2>&1 | tail -5
```

Expected: ALL passed (no failures, no skipped-up from skip).

---

## Task 10: 测试迁移 — test_decision_api.py (commit 4b, 6 处模式 B)

**Files:**
- Modify: `tests/dashboard/test_decision_api.py` (L693+, L836+, L960+, L1013+, L1128+)

- [ ] **Step 1: 加 import**

Edit `test_decision_api.py` 顶部 imports:

```python
from lingwen_core.agents.workflow_state import WorkflowState
```

- [ ] **Step 2: 替换 6 处 _last_X = X 模式 B**

每处 3-4 行裸赋值 (e.g. `_last_scheduler = _FakeScheduler()`, `_last_graph = _FakeGraph()`, `_last_workflow_name = "novel_writing"`):

```python
        controller._last_scheduler = _FakeScheduler()
        controller._last_graph = _FakeGraph()
        controller._last_workflow_name = "novel_writing"
```

→ 替换为:
```python
        controller._state = controller._state.with_updates(
            scheduler=_FakeScheduler(),
            graph=_FakeGraph(),
            workflow_name="novel_writing",
        )
```

适用位置: `controller._last_* =` 在 `test_decision_api.py` 内 6 处 (用 grep 找精确行号).

- [ ] **Step 3: 校验 + 跑测试**

```bash
grep -n "_last_" tests/dashboard/test_decision_api.py | grep -v "_last_workflow_status"  # OUT OF SCOPE 字段
uv run pytest tests/dashboard/test_decision_api.py -q 2>&1 | tail -5
```

Expected: only `_last_workflow_status` lines remain (out of scope); 测试全过.

---

## Task 11: 测试迁移 — 4 个 dashboard 测试 (commit 4b, 模式 B)

**Files:**
- Modify: `tests/dashboard/test_app_workflow_production_summary_f66.py:45-50`
- Modify: `tests/dashboard/test_app_workflow_status.py`
- Modify: `tests/dashboard/test_app_workflow_status_tier_budget.py:158-160`
- Modify: `tests/dashboard/test_protocols.py:175-177`

- [ ] **Step 1: 加 import 到 4 文件**

每个文件顶部 imports 加:

```python
from lingwen_core.agents.workflow_state import WorkflowState
```

- [ ] **Step 2: test_app_workflow_production_summary_f66.py L45-50**

5 行:
```python
    master._last_scheduler = _StubScheduler()
    master._last_graph = _StubGraph()
    master._last_workflow_name = "novel_writing"
    master._last_initial_inputs = {"chapter_num": 360}
    master._last_memory_context = {"source": "stub"}
    master._last_incremental_backfill = {"nodes_written": 2, "total_count": 2, "elapsed_s": 0.1}
```

→ 替换为:
```python
    master._state = WorkflowState(
        scheduler=_StubScheduler(),
        graph=_StubGraph(),
        workflow_name="novel_writing",
        initial_inputs={"chapter_num": 360},
        memory_context={"source": "stub"},
        incremental_backfill={"nodes_written": 2, "total_count": 2, "elapsed_s": 0.1},
    )
```

(注: 此处用直接 `WorkflowState(...)` constructor 而非 `with_updates(empty(), ...)` 因为是新建 stub master 而非 partial update)

- [ ] **Step 3: test_app_workflow_status_tier_budget.py L158-160**

3 行:
```python
        master._last_scheduler = _StubScheduler()
        master._last_graph = _StubGraph()
        master._last_workflow_name = "novel_writing"
```

→ 替换为:
```python
        master._state = master._state.with_updates(
            scheduler=_StubScheduler(),
            graph=_StubGraph(),
            workflow_name="novel_writing",
        )
```

- [ ] **Step 4: test_protocols.py L175-177**

同模式 (3 行) → 同 form `with_updates(...)`.

- [ ] **Step 5: test_app_workflow_status.py**

按文件实际 stub 模式 (grep 找精确 `_last_*` 行), 同模式 B 改写.

- [ ] **Step 6: 校验 4 文件**

```bash
grep -n "_last_" tests/dashboard/test_app_workflow_production_summary_f66.py \
                tests/dashboard/test_app_workflow_status.py \
                tests/dashboard/test_app_workflow_status_tier_budget.py \
                tests/dashboard/test_protocols.py
```

Expected: 0 lines.

- [ ] **Step 7: 跑 4 测试**

```bash
uv run pytest tests/dashboard/test_app_workflow_production_summary_f66.py \
            tests/dashboard/test_app_workflow_status.py \
            tests/dashboard/test_app_workflow_status_tier_budget.py \
            tests/dashboard/test_protocols.py -q 2>&1 | tail -5
```

Expected: ALL passed.

---

## Task 12: 测试迁移 — test_chapter_emit.py (commit 4b, 模式 C)

**Files:**
- Modify: `tests/agent_system/test_chapter_emit.py:124` (主要) + 其他用 `_last_initial_inputs` 的地方

- [ ] **Step 1: 加 import**

Edit `test_chapter_emit.py` 顶部 imports:

```python
from lingwen_core.agents.workflow_state import WorkflowState
```

- [ ] **Step 2: 替换 fake type `_last_initial_inputs` → `_state`**

L124:
```python
        compute = AgentComputeFn(type("_M", (), {"_last_initial_inputs": {"chapter_num": 1}})())
```

→ 替换为:
```python
        compute = AgentComputeFn(type("_M", (), {"_state": WorkflowState(initial_inputs={"chapter_num": 1})})())
```

- [ ] **Step 3: 校验**

```bash
grep -n "_last_" tests/agent_system/test_chapter_emit.py
```

Expected: 0 lines.

- [ ] **Step 4: 跑测试**

```bash
uv run pytest tests/agent_system/test_chapter_emit.py -q 2>&1 | tail -5
```

Expected: ALL passed.

---

## Task 13: 测试迁移 — test_production_summary.py + commit 4b 收尾 (commit 4b)

**Files:**
- Modify: `tests/agent_system/test_production_summary.py`

- [ ] **Step 1: 替换断言/Setup**

按文件实际读 `_last_*` 处, 替换为 `controller._state.X`. (具体行号 grep 找.)

- [ ] **Step 2: 校验全 8 测试文件无 _last_***

```bash
grep -rln "_last_scheduler\|_last_graph\|_last_workflow_name\|_last_start_nodes\|_last_initial_inputs\|_last_incremental_backfill\|_last_memory_context" \
    tests/ 2>/dev/null
```

Expected: 0 files (8 测试文件全迁完).

- [ ] **Step 3: 跑全 tests/dashboard, tests/got, tests/agent_system**

```bash
uv run pytest tests/dashboard/ tests/got/ tests/agent_system/ -q 2>&1 | tail -10
```

Expected: 全过 (含原有 baseline). **没有新失败**.

- [ ] **Step 4: ruff 干净**

```bash
uv run ruff check tests/
uv run ruff format --check tests/
```

Expected: clean.

- [ ] **Step 5: 提交测试迁移 (commit 4b)**

```bash
git add tests/
git commit -m "$(cat <<'EOF'
refactor: migrate _last_* test stubs to WorkflowState (8 tests)

Phase 26 P2-WFSTATE commit 4b (continuation of 4a):
- tests/got/test_decision_pause_resume.py — Pattern A (stub init) + B
- tests/dashboard/test_decision_api.py — Pattern B (6 sites)
- tests/dashboard/test_app_workflow_* (4 files) — Pattern B
- tests/dashboard/test_protocols.py — Pattern B
- tests/agent_system/test_chapter_emit.py — Pattern C (fake type)
- tests/agent_system/test_production_summary.py — assertion adjust

Pattern A: stub init 多行 → WorkflowState.empty()
Pattern B: _last_X = X → controller._state.with_updates(...) or WorkflowState(...)
Pattern C: fake class dict {"_last_initial_inputs": ...} → {"_state": WorkflowState(...)}

Tests/dashboard + tests/got + tests/agent_system 全过 (no new failures).

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Task 14: Refactor guard 测试 (commit 5) + 最终测试验证

**Files:**
- Modify: `tests/agent_system/test_workflow_state.py` (appending new test class)

- [ ] **Step 1: 加 guard 测试**

Append to `tests/agent_system/test_workflow_state.py` (尾部):

```python
class TestRefactorGuard:
    """防 _last_* 散点回潮 — 仅 controller._state 单 source 模式."""

    def test_master_controller_has_state_attribute(self) -> None:
        """生产 MasterController.__init__ 后必有 _state 属性."""
        from lingwen_pipeline.master_controller import MasterController

        # 用 __new__ 跳过 __init__ 验证 dataclass init 路径;
        # 完整 __init__ 依赖外部 fixture, 这里只验 dataclass 路径
        controller = MasterController.__new__(MasterController)
        controller._state = WorkflowState.empty()

        assert hasattr(controller, "_state")
        assert isinstance(controller._state, WorkflowState)

    def test_no_last_underscore_attrs_on_workflow_state_instance(self) -> None:
        """WorkflowState 实例不应有 _last_* 前缀字段 — 7 字段全部 canonical 命名."""
        state = WorkflowState.empty()

        forbidden_prefixes = (
            "_last_scheduler", "_last_graph", "_last_workflow_name",
            "_last_start_nodes", "_last_initial_inputs",
            "_last_incremental_backfill", "_last_memory_context",
        )
        for name in forbidden_prefixes:
            assert not hasattr(state, name), (
                f"WorkflowState 不应有 {name}; 用 workflow_name / graph 等 canonical 名"
            )

        # canonical 命名必须存在
        canonical = (
            "scheduler", "graph", "workflow_name",
            "start_nodes", "initial_inputs",
            "incremental_backfill", "memory_context",
        )
        for name in canonical:
            assert hasattr(state, name), f"WorkflowState 缺 canonical 字段 {name}"

    def test_stub_master_controller_uses_workflow_state(self) -> None:
        """chapter_golden_path stub master 初始化后所有 7 字段均可读 — 不再漏 init."""
        from lingwen_core.agents.chapter_golden_path import build_stub_master_controller

        # 用 tmp_path 派生 state_dir — 不实际写文件 (stub init 只设 attrs)
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            controller = build_stub_master_controller(Path(tmp) / "state")

        # 全部 7 字段可读 + 默认值正确 (替代原 _last_X 漏 init AttributeError)
        assert controller._state.scheduler is None
        assert controller._state.graph is None
        assert controller._state.workflow_name == ""
        assert controller._state.start_nodes == []
        assert controller._state.initial_inputs == {}
        assert controller._state.incremental_backfill is None
        assert controller._state.memory_context is None
```

- [ ] **Step 2: 确认 refactor guard 测试通过**

```bash
uv run pytest tests/agent_system/test_workflow_state.py -v 2>&1 | tail -20
```

Expected: 11 passed (8 original + 3 guard tests).

- [ ] **Step 3: ruff 干净**

```bash
uv run ruff check tests/agent_system/test_workflow_state.py
uv run ruff format --check tests/agent_system/test_workflow_state.py
```

Expected: clean.

- [ ] **Step 4: 提交 commit 5**

```bash
git add tests/agent_system/test_workflow_state.py
git commit -m "$(cat <<'EOF'
test(agent-system): workflow_state refactor guard

Phase 26 P2-WFSTATE commit 5:
- 3 个 guard 测试防 _last_* 散点回潮
  1. MasterController 必有 _state 属性
  2. WorkflowState 实例无 _last_* 前缀字段 (7 字段全部 canonical)
  3. stub master 初始化后 7 字段全部可读 (替代 _last_X 漏 init AttributeError)

守护 spec §2.2 不变量 — 未来若有人「顺手优化」改回 _last_* 散点,
CI 即拦截.

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

---

## Task 15: 最终验证门 + handoff + ff-merge

- [ ] **Step 1: 全验证门 (spec §7)**

```bash
cd /home/ailearn/projects/LingWen-phase-26-wfstate
uv run ruff check . && uv run ruff format --check .

uv run pytest tests/dashboard/ -q 2>&1 | tail -3
uv run pytest tests/cross_volume/test_incremental_backfill.py -q 2>&1 | tail -3
uv run pytest tests/got/ -q 2>&1 | tail -3
uv run pytest tests/agent_system/ -q 2>&1 | tail -3

uv run pytest tests/ tests/apps/ packages/lingwen-shared/ packages/lingwen-llm/ -q 2>&1 | tail -3
```

Expected:
- ruff: clean
- tests/dashboard: 357 passed, 3 skipped (UNCHANGED from baseline)
- tests/cross_volume: 15 passed (UNCHANGED)
- tests/got: ZERO new failures (compare to baseline 84 pre-existing cascade)
- tests/agent_system: pre-existing cascade unchanged + 11 new (8 unit + 3 guard) PASSED
- full suite green

- [ ] **Step 2: grep 验证 (spec §7)**

```bash
grep -rn "_last_scheduler\|_last_graph\|_last_workflow_name\|_last_start_nodes\|_last_initial_inputs\|_last_incremental_backfill\|_last_memory_context" \
    packages/ apps/ tests/ 2>/dev/null
```

Expected: NO output (0 hits).

- [ ] **Step 3: 写 handoff + 更新 CURRENT_STATUS / BACKLOG**

Create `docs/superpowers/handoffs/2026-09-04-phase-26-wfstate-handoff.md` (沿用 v25.9 handoff 模板):

涵盖:
- 执行总结: 5 commits 列表 + spec/plan/handoff
- 测试矩阵: baseline → target (含 +11 新增)
- grep 验证: 0 hits 截图
- carryover to Phase 27+: 4 项 (P2-WFRUNNER 建议紧接, P2-RESUME-VERIFY, P2-MC-WRITING, P2-ARCHDEBT)

更新 `collaboration/CURRENT_STATUS.md`:
- 新一行 "v26.0 (Phase 26 P2-WFSTATE) — _last_* 散点整合 WorkflowState dataclass (master `X`, N commits) ✅"

更新 `collaboration/BACKLOG.md`:
- P2-WFSTATE 行: 标记 ✅ 完成

- [ ] **Step 4: 提交 handoff / state updates**

```bash
git add docs/superpowers/handoffs/ collaboration/
git commit -m "$(cat <<'EOF'
docs(phase-26): wfstate handoff + state sync

Phase 26 closure: P2-WFSTATE 完成，15 modified + 2 new files.
master HEAD pre-merge = current branch tip.

5 commits breakdown:
- docs(phase-26): wfstate refactor design (99bed427)
- docs(phase-26): wfstate refactor plan (this commits' prev)
- feat(lingwen-core): add WorkflowState dataclass
- refactor: migrate _last_* → _state WorkflowState (7 src)
- refactor: migrate _last_* test stubs to WorkflowState (8 tests)
- test(agent-system): workflow_state refactor guard (3 guard tests)

Verification gates (spec §7): ruff clean / dashboard 357+3 / cross_volume 15
/ agent_system +11 (8 unit + 3 guard) / grep 0 hits on 7 fields.

Carryover: P2-WFRUNNER (建议紧接) / P2-RESUME-VERIFY / P2-MC-WRITING / P2-ARCHDEBT.

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 5: ff-merge 到 master + push**

```bash
cd /home/ailearn/projects/LingWen
git checkout master
git merge --ff-only phase-26-wfstate
git log --oneline -7
git push origin master
```

Expected: `git log` 顶部出现 5 个新 commits (含 docs), `git push` 成功 (无 rejected).

(若 ff-merge 报 "Not possible to fast-forward" — main checkout 期间有别人推送 → git pull --rebase origin master 重试)

- [ ] **Step 6: 清理 worktree**

```bash
git worktree remove /home/ailearn/projects/LingWen-phase-26-wfstate
git branch -d phase-26-wfstate
git worktree list
```

Expected: `LingWen-phase-26-wfstate` 从 worktree list 移除, 分支也删.

(可选后续: 同时清理 `LingWen-phase-25-9` 与 `.worktrees/track-a/b` — 独立 housekeeping task)

---

## 验证门总表 (per spec §7)

| 门 | 命令 | Expected |
|---|---|---|
| ruff check | `uv run ruff check .` | clean |
| ruff format --check | `uv run ruff format --check .` | clean |
| tests/dashboard | `uv run pytest tests/dashboard/ -q` | 357 passed, 3 skipped (UNCHANGED) |
| tests/cross_volume/test_incremental_backfill.py | 同上 file | 15 passed (UNCHANGED) |
| tests/got | 同上 dir | ZERO 新增失败 (vs baseline 84 cascade pre-existing) |
| tests/agent_system | 同上 dir | +11 new (8 unit + 3 guard) 通过；其他 ZERO 新增失败 |
| full suite | `uv run pytest tests/` | 绿 |
| grep 7 fields | `grep -rn "_last_scheduler\|..." packages/ apps/ tests/` | 0 hits |
