# Phase 25.9 — human_review 人审流水线修复 · Design

> **Status**: 设计稿 · 待用户 review
> **日期**: 2026-09-03
> **目标版本**: v25.9
> **作用域**: `WorkflowMixin.run_workflow` / `resume_workflow` 对齐新 `GoTScheduler` API；4 个诚实 skip 的 human_review 用例去 skip；零架构债修复
> **范围选择**: **最小可用**（per brainstorming）— 不动 `infra.got` 迁移 / `chapter_golden_path` 反向 import / HANDOFF 文档措辞

---

## 1. 背景与动机

v25.8（commit `f5934262`）已将 human_review 模块做迁移友好修复（`GotScheduler`→`GoTScheduler`、dashboard.* → apps.studio_api.* 导入），但**实测 `WorkflowMixin.run_workflow` 仍以 500 失败**：

- 当前 `mc_workflow.py:38-77` 直接 `GoTScheduler(workflow_name=..., start_nodes=..., initial_inputs=..., cost_budget_usd=..., base_dir=..., cost_tracker=..., budget_service=..., budget_service_by_tier=..., master_controller=...)`
- 真实 `infra/got/scheduler.py:135` `GoTScheduler.__init__(graph, compute_fn, cache, max_backtracks)` 拒绝上述 kwargs → `TypeError` → 500

**正确路径已存在**：`got_bridge.build_got_scheduler(master, workflow_name, base_dir, max_backtracks)` 工厂（`got_bridge.py:423`）能正确构造 `GoTScheduler` 并连线 `AgentComputeFn` / `cost_tracker` / `budget_service`。`WorkflowMixin.run_workflow` 应该调它，但没调。

**次生问题**：
- `WorkflowMixin.resume_workflow(self)` 无参数；`apps/studio_api/routes/workflows.py:90` 路由 / `apps/studio_api/protocols.py:218` adapter 传 `(decision_id, option, resolved_by)`（路由必然先于 mixin 失败）
- 4 个 `tests/dashboard/test_human_review_smoke.py` 用例诚实 skip
- 同因亦致 `tests/got` / `tests/agent_system` 多个关联用例未通过

**本阶段目标**（最小可用）：
1. **修 `WorkflowMixin.run_workflow`**：改调 `build_got_scheduler` + 正确传 `start_nodes`/`initial_inputs` 给 `scheduler.run`
2. **修 `WorkflowMixin.resume_workflow`**：签名加 `(decision_id, option, resolved_by)`，转给 `scheduler.resume`
3. **去 4 处 `@pytest.mark.skip`**：保留断言不变
4. **验证连带无新增失败**：`tests/got` / `tests/agent_system` / `tests/ci` 维持 ZERO 新增失败基线

**HANDOFF 文档误传澄清**（不修文档）：
- `cost_tracker` / `build_router` **已存在并已初始化**（`master_controller.py:78/76`）；测试 monkeypatch 是因为 `build_router` 触发真实 LLM provider 初始化
- `latest_decision_queue` 在代码中**根本不存在**（仅有 `_decision_queue`）—— HANDOFF 措辞误传
- `infra.got` 不在 `lingwen-core` `allowed_imports`（architecture.yml:126-129）—— **out of scope**

---

## 2. 架构与端点形态

### 2.1 端点（无变化）

`POST /api/workflows/run` / `POST /api/workflows/resume` / `GET /api/workflows/active` / `GET /api/decisions/pending` 路由契约（`apps/studio_api/routes/workflows.py`、`decisions.py`、`packages/lingwen-shared/src/lingwen_shared/contracts/python/workflows.py`、`decisions.py`）**保持不变**。

### 2.2 修改文件清单

| 文件 | 变更 |
|---|---|
| `packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py` | MODIFIED（`run_workflow` 改调 `build_got_scheduler` + `resume_workflow` 加 3 参数） |
| `tests/dashboard/test_human_review_smoke.py` | MODIFIED（移除 4 处 `@pytest.mark.skip`，断言不变） |

**不改**：`got_bridge.py`、`chapter_golden_path.py`、`apps/studio_api/*`、`infra/got/*`、`.lingwen/architecture.yml`、`HANDOFF*.md`

### 2.3 架构不变量

- I001（infra 不 import apps）✅ 保持
- I005（创作流必须支持 checkpoint 恢复）✅ 保持（`resume_workflow` 仍走 `_last_scheduler`）
- **不新增不变量**（per 最小可用 — 架构债推后续 phase）

---

## 3. 组件与数据流

### 3.1 `WorkflowMixin.run_workflow`（mc_workflow.py:38-77 改写）

```python
def run_workflow(
    self,
    workflow_name: str,
    start_nodes: Optional[list[str]] = None,
    initial_inputs: Optional[Dict[str, Any]] = None,
    cost_budget_usd: Optional[float] = None,
    max_backtracks: int = 2,
    base_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """用 GoT 调度器运行工作流。"""
    from lingwen_core.agents.got_bridge import build_got_scheduler  # 本地 import 沿用原风格
    import dataclasses

    try:
        self._current_budget_usd = cost_budget_usd
        self._current_run_id = uuid.uuid4().hex

        scheduler, graph = build_got_scheduler(
            master=self,
            workflow_name=workflow_name,
            base_dir=base_dir,
            max_backtracks=max_backtracks,
        )

        summary = scheduler.run(
            start_nodes=start_nodes or [],
            initial_inputs=initial_inputs,
        )

        self._last_scheduler = scheduler
        self._last_graph = graph
        self._last_workflow_name = workflow_name
        self._last_start_nodes = start_nodes or []
        self._last_initial_inputs = initial_inputs or {}

        # ExecutionSummary → Dict; paused_nodes 是 list[NodeExecution] → 抽 id
        result = dataclasses.asdict(summary)
        if isinstance(result.get("paused_nodes"), list):
            result["paused_nodes"] = [
                getattr(n, "id", str(n)) for n in summary.paused_nodes
            ]
        return result
    finally:
        self._current_budget_usd = None
        self._current_run_id = None
```

### 3.2 `WorkflowMixin.resume_workflow`（mc_workflow.py:88-97 改写）

```python
def resume_workflow(
    self,
    decision_id: str,
    option: str,
    resolved_by: str = "human",
) -> Optional[Dict[str, Any]]:
    """恢复上次中断的工作流。"""
    import dataclasses
    if self._last_scheduler is None:
        return None
    try:
        node_execution = self._last_scheduler.resume(decision_id, option, resolved_by)
        return dataclasses.asdict(node_execution) if node_execution else None
    except Exception as e:
        logger.error("resume_workflow failed: %s", e)
        return None
```

### 3.3 数据流

```
POST /api/workflows/run (body=RunWorkflowRequest)
  → apps/studio_api/protocols.py MasterControllerAdapter.run_workflow
    → WorkflowMixin.run_workflow(workflow_name, start_nodes, initial_inputs, max_backtracks, base_dir, cost_budget_usd)
      → got_bridge.build_got_scheduler(master, workflow_name, base_dir, max_backtracks)
        → infra.got.workflow_loader.load_workflow → ThoughtGraph
        → GoTScheduler(graph, compute_fn=AgentComputeFn(master, cost_tracker, budget_service, budget_service_by_tier), max_backtracks)
      → GoTScheduler.run(start_nodes, initial_inputs) → ExecutionSummary
      ← dataclasses.asdict(summary) with paused_nodes 兜底
  ← adapter 包成 WorkflowStatusResponse
← {paused: <bool>, ...}
```

```
POST /api/workflows/resume (body=ResumeWorkflowRequest{decision_id, option, resolved_by})
  → MasterControllerAdapter.resume_workflow
    → WorkflowMixin.resume_workflow(decision_id, option, resolved_by)
      → self._last_scheduler.resume(decision_id, option, resolved_by) → NodeExecution
      ← dataclasses.asdict(node_execution)
```

### 3.4 复用与新文件

| 类型 | 新增 | 复用 |
|---|---|---|
| mc_workflow.py | — | `got_bridge.build_got_scheduler`（已存在并经回归） |
| tests/dashboard/test_human_review_smoke.py | — | 现有 4 个 test 方法体（仅去 skip 装饰器） |

---

## 4. 错误处理 + 边界

| 场景 | 行为 |
|---|---|
| `workflow_name` 不在 registry | `build_got_scheduler` 抛 ValueError → 500（与现行为一致） |
| `scheduler.run` 抛 `SchedulerError` / `MaxStepsExceeded` / `HumanInterventionRequired` | 透传（设计上抛给上层决定） |
| `resume_workflow` 时 `_last_scheduler is None` | 返回 `None`（保留现有宽松契约） |
| `resume_workflow` 决策失败（decision_id 未知等） | log + 返回 `None`（保留现有宽松契约） |
| `summary.paused_nodes` 非 dataclass 列表（旧 stub） | `getattr(n, "id", str(n))` 兜底，never raise |

---

## 5. 提交结构（3 commits, atomic）

| # | Commit | 内容 |
|---|---|---|
| 1 | `docs(phase-25-9): human_review pipeline refactor design` | spec（本文件） |
| 2 | `docs(phase-25-9): human_review pipeline refactor plan` | plan |
| 3 | `fix(lingwen-core): align WorkflowMixin with new GoTScheduler API; unskip human_review smoke` | mc_workflow.py 2 方法体改 + test_human_review_smoke.py 4 处去 skip |

**baseline → target 测试数**：
- `tests/dashboard`: 353 passed + 7 skipped → **357 passed + 3 skipped**（+4 新过，-4 skip）
- `tests/ci`: 205 passed + 1 skipped → 205 passed + 1 skipped（不变）
- `tests/got` + `tests/agent_system` 关联用例：ZERO 新增失败（不期望增量，因 monkeypatch 路径不受 mixin 改动影响）

**0 改范围**：`got_bridge.py` / `chapter_golden_path.py` / `apps/studio_api/*` / `infra/got/*` / `.lingwen/architecture.yml` / `HANDOFF*.md`

---

## 6. 风险矩阵

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| `build_got_scheduler` 行为差异导致 smoke 失败 | 中 | 中 | 它已通过 `tests/agent_system/test_got_bridge.py::TestBuildGoTScheduler` 验证；smoke 复跑即知 |
| `ExecutionSummary.asdict` 漏字段 | 低 | 低 | `dataclasses.asdict` 含所有 dataclass 字段；仅 `paused_nodes` 元素类型需兜底（已加） |
| `resume_workflow` 签名破坏其他 MC 继承者 | 低 | 低 | `MasterController` 是唯一 mixin 消费者（`master_controller.py:41`）；本地 `chapter_golden_path.run_golden_path` 已用 `(decision_id, option)` 调用形式，**新签名正好对齐** |
| `infra.got` import 在 lint / typecheck 触发额外告警 | 低 | 低 | 现状已 import（`got_bridge.py:28-29, 446-448` 持续；本阶段未增加新 import） |

---

## 7. 验证门（Phase 25.9 closure）

- ruff check + ruff format --check clean
- 后端 pytest:
  - `tests/dashboard` 357 passed + 3 skipped（**+4 vs baseline**）
  - `tests/ci` 205 passed + 1 skipped（**不变**）
  - `tests/got` / `tests/agent_system` 关联用例 **ZERO 新增失败**
  - 全量 `tests/`（含 studio_api、shared、llm）绿
- 前端：unaffected（untracked 改动 = 0）

---

## 8. 实施后结构变更

```
packages/lingwen-core/src/lingwen_core/agents/mc_workflow.py  ← MODIFIED (~30 行 diff: 2 方法体)
tests/dashboard/test_human_review_smoke.py                    ← MODIFIED (4 处去 skip)
docs/superpowers/specs/2026-09-03-phase-25-9-...-design.md   ← NEW（本文件）
docs/superpowers/plans/2026-09-03-phase-25-9-...md            ← NEW
```

---

## 9. Carryover to Phase 26+（**不在本阶段**）

- `infra.got.*` 迁移至 `packages/lingwen-got/`（补 `lingwen-core` `allowed_imports` 或新包）
- `chapter_golden_path.py` 反向 import `apps.studio_api.*` 整改（test 客户端构造迁至 `tests/dashboard`）
- `latest_decision_queue` HANDOFF 文档措辞修订
- `human_review` 真正端到端 E2E（Playwright + live backend）