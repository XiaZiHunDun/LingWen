# Phase 7: MasterController.run_workflow E2E 集成 (StubProvider 模拟真实 LLM)

**日期**: 2026-06-04
**范围**: Phase 7, Doc 4 §11
**基线测试**: 2006 passed, 0 failed, 17 skipped
**目标测试**: ~2020 passed (+14 new)

---

## Context

Phase 2.12a 已经把 `LLMComputeFn` 写到 `infra/got/llm_compute.py`,有 269+479 行单元/E2E 测试。Phase 3 的 `AgentComputeFn`(`infra/agent_system/got_bridge.py`)是 `MasterController.run_workflow` 实际调用的生产路径,把 `prompt_scenario` 路由到 `master.write_chapter` / `master.audit_chapter` 等方法,这些方法内部走 `self._router` (AIRouter) → TieredRouter → LLM。

**真正的 gap**:MasterController.run_workflow → AgentComputeFn → master 方法 → Router → LLM 这条**生产链没有 E2E 集成测试**。现有 `test_master_controller_workflow.py:122` 显式把 `controller.write_chapter = types.MethodType(lambda ..., stub.write_chapter, ...)` 替换 master 方法,在注释里写明"避免触发真实 LLM"。

**目标**:补 E2E 集成测试,**不替换 master 方法**,只替换 Router 注入点为 `TieredRouter({tier: StubProvider})`。StubProvider 模拟 LLM API,记录所有调用,返回固定 response。CI 友好,不耗真实 token,但走完整生产链。

---

## 架构

```
MasterController (正常构造,不替换任何 master 方法)
  ↓ self._router
AIRouter
  ↓ 内部 tier 路由
TieredRouter ← 测试用,3 个 tier 全是 StubProvider
  ↓
StubProvider (返回固定 response,记录所有 calls + 估算 token cost)
```

**注入点**:monkeypatch `infra.agent_system.master_controller.build_router` (跟 `test_master_controller_workflow.py:325` 同模式)。

---

## 文件改动

| 文件 | 类型 | 说明 |
|---|---|---|
| `infra/got/workflows/minimal_e2e.yaml` | NEW | 3 节点 linear 工作流 (write → review → polish),不含 DECISION |
| `tests/agent_system/_e2e_helpers.py` | NEW | `_make_test_tiered_router()` + `_make_master_with_router()` fixture helpers |
| `tests/agent_system/test_master_controller_e2e_real_llm.py` | NEW | 3 个 test class,~17 tests |
| `MEMORY.md` | UPDATE | Phase 7 进度条目 |

**估计**: 2 新 src + 1 新 test = 3 新文件, ~17 新测试, 1 commit

---

## 组件设计

### 1. `infra/got/workflows/minimal_e2e.yaml`

```yaml
workflow: minimal_e2e
version: 1
nodes:
  - id: write
    type: generation
    name: Write Chapter
    description: chapter_writing
    prompt_scenario: chapter_writing
    depends_on: []
  - id: review
    type: generation
    name: Review
    description: chapter_review
    prompt_scenario: chapter_review
    depends_on: [write]
  - id: polish
    type: generation
    name: Polish
    description: ai_trace_removal
    prompt_scenario: ai_trace_removal
    depends_on: [review]
```

**为什么新建 YAML**:现有 `novel_writing.yaml` 含 DECISION + 多阶段,适合测 DECISION 路径但不适合"基础 happy path"快速 sanity check。新建 minimal 是为了 3 节点快速验证"路由链通 + LLM 调用被记录 + cost 累计",< 1s 跑完。

### 2. `tests/agent_system/_e2e_helpers.py`

```python
# API 草图
def _make_test_tiered_router(
    response_map: dict[ModelTier, str | Exception],
    cost_tracker: Optional[CostTracker] = None,
) -> tuple[TieredRouter, dict[ModelTier, _StubProvider]]: ...

def _make_master_with_router(
    state_dir: Path,
    tiered_router: TieredRouter,
    cost_tracker: Optional[CostTracker] = None,
) -> MasterController: ...
    # monkeypatch build_router → 注入测试 router
    # 不替换任何 master.* 方法
```

**为什么单独 helper 文件**:
- `test_llm_compute.py:30` 有 `_StubProvider` (复用,放共享 fixture 模块)
- `test_master_controller_workflow.py:121` 用了"替换 master 方法"模式,跟 Phase 7 的"不替换"模式不冲突但要明确分离
- 避免污染现有测试结构

### 3. `tests/agent_system/test_master_controller_e2e_real_llm.py`

| Test class | Tests | 覆盖 |
|---|---|---|
| `TestMinimalWorkflowE2E` | 6 | happy path / LLM calls 数量 / 节点状态 / cost 记录 / execution.output 结构 / sanity check (master.write_chapter 没被替换) |
| `TestNovelWritingE2E` | 5 | 4 节点走完 / StubProvider.calls 长度 (=2 写+审) / read_snapshot/emit_chapter 旁路不调 LLM / cost 累计 / execution graph 完整 |
| `TestRouterFailure` | 3 | 单 provider 抛错 → 降级到下个 tier / 全部 tier 失败 → NodeStatus.FAILED / `run_workflow` 不抛异常 |

**总计 ~14 tests** (+2006 → ~2020)

**注**:`novel_writing.yaml` 实际不含 DECISION 节点(4 节点 read_snapshot/write_chapter/review_chapter/emit_chapter),DECISION+MasterController 集成已被 `tests/got/test_decision_pause_resume.py` 覆盖(17 tests),Phase 7 不重复 DECISION 测试,聚焦 LLM 路由链 E2E。

---

## 关键断言

### TestMinimalWorkflowE2E

```python
def test_happy_path_completes_all_nodes(self, tmp_path):
    router, providers = _make_test_tiered_router({tier: "ok" for tier in ModelTier})
    master = _make_master_with_router(tmp_path, router)
    result = master.run_workflow("minimal_e2e", initial_inputs={...})
    
    assert result["summary"].completed == 3
    assert result["summary"].failed == 0
    assert result["summary"].paused is False
    # Sanity: master 方法没被替换
    assert master.write_chapter.__qualname__ == "MasterController.write_chapter"
    # LLM 调了 3 次 (每节点 1 次)
    total_calls = sum(len(p.calls) for p in providers.values())
    assert total_calls == 3
```

### TestNovelWritingE2E

```python
def test_pauses_at_decision_node(self, tmp_path):
    # 跑 novel_writing → 应 pause 在 DECISION 节点
    router, providers = _make_test_tiered_router({tier: "ok" for tier in ModelTier})
    master = _make_master_with_router(tmp_path, router)
    
    # 注入 decision (production 通过 _harvest_decision_specs 注入)
    result = master.run_workflow("novel_writing", initial_inputs={...})
    assert result["summary"].paused is True
    assert "outline_judgment" in result["summary"].paused_nodes or \
           any("judge" in n for n in result["summary"].paused_nodes)
    # DECISION 节点不调 LLM
    # 非 DECISION 节点数 = providers 总调用次数
```

```python
def test_resume_after_decision_completes_workflow(self, tmp_path):
    # run → pause → resolve → resume → all COMPLETED
    ...
    result1 = master.run_workflow("novel_writing", initial_inputs={...})
    decision = result1["pending_decisions"][0]
    result2 = master.resume_workflow(decision["decision_id"], "approve")
    assert result2["summary"].paused is False
    # execution.output 含 option
    assert result2["executions"][decision["node_id"]].output["option"] == "approve"
```

### TestRouterFailure

```python
def test_provider_failure_triggers_downgrade(self, tmp_path):
    # OPUS tier 抛错 → 降级到 SONNET → 节点仍 COMPLETED
    router, providers = _make_test_tiered_router({
        ModelTier.OPUS: RuntimeError("opus down"),
        ModelTier.SONNET: "ok",
        ModelTier.HAIKU: "ok",
    })
    master = _make_master_with_router(tmp_path, router)
    result = master.run_workflow("minimal_e2e", initial_inputs={...})
    # OPUS 失败次数 >= 1,SONNET 接管
    assert providers[ModelTier.OPUS].calls  # 至少被试过
    assert providers[ModelTier.SONNET].calls  # 接管
    # 节点仍 COMPLETED (降级成功)
    assert result["summary"].completed >= 1
```

---

## 错误处理路径 (不变量)

| 失败点 | 传播 | 终点 |
|---|---|---|
| `StubProvider.generate()` 抛错 | TieredRouter 降级 (OPUS → SONNET → HAIKU) | 全部失败 → TieredRouterError |
| `TieredRouterError` | `LLMComputeFn` / `AgentComputeFn` catch | `ComputeResult(fail=True, error=...)` |
| `ComputeResult(fail=True)` | GoTScheduler 走 backtrack | `NodeStatus.FAILED` |
| `NodeStatus.FAILED` | workflow 继续跑其他节点 | `summary.failed` 累计 |
| DECISION 节点 | Phase 5: 不调 compute_fn | `NodeStatus.WAITING` + `summary.paused` |

**关键不变量**:
- LLM 失败**不抛异常**到 caller (per `got_bridge.py:181` + `llm_compute.py:103` 已确认)
- `controller.run_workflow(...)` 不 raise — 失败节点用 backtrack,terminal 状态汇总到 summary
- DECISION 节点不计入 LLM 调用次数 (DECISION 节点没有 `prompt_scenario`,走 AgentComputeFn line 169 的"旁路"路径)

---

## 验证

### 每阶段

```bash
# 1. 新文件 ruff 0
ruff check tests/agent_system/_e2e_helpers.py \
          tests/agent_system/test_master_controller_e2e_real_llm.py

# 2. 新测试通过
pytest tests/agent_system/test_master_controller_e2e_real_llm.py -v

# 3. 全套不回归
pytest -q --ignore=tests/e2e
# 期望: 2006 + 17 = ~2023 passed
```

### Commit 风格

```
feat(agent_system): phase 7 — MasterController.run_workflow E2E 集成 (StubProvider 模拟 LLM)
```

### 完成定义

- 3 个新文件创建并 ruff 0
- ~17 新测试全部通过
- 全套 2006 → ~2023 passed
- 1 commit 推送 origin/master
- MEMORY.md 更新 Phase 7 条目

---

## Out of scope (后续 phase)

- **真 API 调用 opt-in 测试** — 需要 API key,CI 跑不动,phase 7+ 单独做
- **`infra/poc/run_volume_1.py` 改 LLMComputeFn** — 用户没选
- **novel_writing.yaml 实际落盘** — 需要 chapter_storage 集成 (不在本阶段)
- **backtrack 真实场景触发** — StubProvider 固定 response,无法真实模拟输出质量问题
- **Mermaid 集成 MasterController.run_workflow** — Phase 6.3 已做 graph 可视化
- **dashboard 真 LLM 跑 workflow** — Phase 6 端到端已通,Phase 7 只补测试,不动 dashboard 逻辑

---

## 风险 + 缓解

| 风险 | 缓解 |
|---|---|
| MasterController 用 AIRouter (not TieredRouter) | monkeypatch `build_router` 替换整个 router,跟现有测试模式一致 |
| agent cache self._router at __init__ | 验证:content_writer/auditor 不 cache,polisher 虽 `self.router = router` 但 `tools.py:9` 注释确认"router 当前未使用(纯规则实现)",无影响 |
| minimal_e2e.yaml 加载路径 | 复用现有 workflow_loader (默认 `infra/got/workflows/`),新 YAML 放默认目录即可 |
| StubProvider 估算 token 误差 | 用 1 token ≈ 4 chars 估算(per `tiered_router.py:148` 已有),不追求精确 |
| DECISION 节点 prompt_scenario 为空 | AgentComputeFn:168 走旁路,返回 `ComputeResult(output=dict(inputs), cost_tokens=0)`,这是 expected 行为 |
| TieredRouter 降级顺序 | per `tiered_router.py:50` 是 (OPUS, SONNET, HAIKU),测试断言要匹配 |
| 跟 `test_master_controller_workflow.py` 的 stub 模式冲突 | helper 单独文件,fixture 命名不同 (`_e2e_master_with_router` vs 现有 `_build_master_controller_with_workflow`),不重叠 |

---

## TDD Sub-phases

| 阶段 | 动作 | 产物 | 累计测试 |
|---|---|---|---|
| 7.1 | RED: minimal_e2e.yaml + _e2e_helpers.py + 3 sanity tests (verify helpers + YAML load) | failing | 2006 |
| 7.2 | GREEN: 扩到 6 TestMinimalWorkflowE2E tests 全 pass | passing | 2012 |
| 7.3 | RED: 5 TestNovelWritingE2E tests | failing | 2012 |
| 7.4 | GREEN: 5 tests pass | passing | 2017 |
| 7.5 | RED: 3 TestRouterFailure tests | failing | 2017 |
| 7.6 | GREEN: 3 tests pass | passing | 2020 |
| 7.7 | ruff 0 + 全套 2006→2020 passed + 1 commit push | done | 2020 |

**预计 commits**: 1 (整个 Phase 7 一个 commit,因为改动集中且都是新文件)

---

## 实施顺序 (按 writing-plans skill 输出)

1. 创建 `infra/got/workflows/minimal_e2e.yaml` (纯数据)
2. 创建 `tests/agent_system/_e2e_helpers.py` (StubProvider + helpers)
3. 写 `TestMinimalWorkflowE2E` 6 tests
4. 跑测试 → pass
5. 写 `TestNovelWritingE2E` 8 tests
6. 跑测试 → pass
7. 写 `TestRouterFailure` 3 tests
8. 跑测试 → pass
9. ruff + 全套验证
10. 1 commit + push
11. 更新 MEMORY.md
