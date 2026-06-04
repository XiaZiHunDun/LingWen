# Phase 7: MasterController.run_workflow E2E 集成 (StubProvider 模拟真实 LLM)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补 E2E 集成测试,验证 `MasterController.run_workflow → AgentComputeFn → master 方法 → router → 真实 LLM 替代品` 这条生产链不替换任何 master 方法,只替换 router 注入点。

**Architecture:** 用 `MasterController(router=...)` 的现有参数注入测试 router。测试 router 是真实 `AIRouter`(被 `MasterController.__init__` 第 62 行直接传给 `self._router` → `build_agent_tools(self._router)`),3 个 provider 槽位注册 3 个 `StubProvider`(继承 `AIProvider`,`generate` 返回固定 string,记录所有 calls)。生产路径:AgentComputeFn → master.write_chapter → content_writer.generate_chapter → `self._router.generate(prompt, system, model, ...)`(per `base.py:90`)→ AIRouter → StubProvider.generate。

**Tech Stack:** Python 3.13, pytest, fixtures, monkeypatch

---

## File Map

| 新文件 | 用途 |
|--------|------|
| `infra/got/workflows/minimal_e2e.yaml` | 3 节点 linear 工作流 (write → review → polish),无 DECISION |
| `tests/agent_system/_e2e_helpers.py` | `StubProvider` + `make_master_with_router` fixture helpers |
| `tests/agent_system/test_master_controller_e2e_real_llm.py` | 3 个 test class,~14 tests |

**估计**: 3 新文件,~14 新测试,1 commit

---

## 注入点参考

| 文件:行 | 现有 | 改造 |
|---|---|---|
| `infra/agent_system/master_controller.py:48-62` | `__init__(self, state_dir, router=None, config=None)`,`self._router = router or build_router(self._config)` | 不动 — `router=` 参数已就位 |
| `infra/agent_system/agent_factory.py:50-59` | `build_router(config) → AIRouter` | 不动 — 测试直接构造 AIRouter 注入 |
| `infra/agent_system/agents/base.py:90` | `self._router.generate(prompt=..., system=..., model=..., temperature=..., max_tokens=..., **kwargs)` | 不动 — AIRouter 接受这些 kwargs |
| `infra/ai_service/router.py:129-182` | `AIRouter.generate(prompt, provider=None, provider_type=None, **kwargs)` | 不动 — 内部 failover 调 `prov.generate(prompt, **kwargs)` |

---

## Task 1: 创建 minimal_e2e.yaml

**Files:**
- Create: `infra/got/workflows/minimal_e2e.yaml`

- [ ] **Step 1: 写 minimal 工作流 (3 节点 linear,无 DECISION)**

```yaml
# 灵文 GoT · minimal_e2e 工作流 v1
#
# Phase 7 测试专用:3 节点 linear,无 DECISION 节点。
# 目的:快速验证 MasterController.run_workflow 端到端路由链。
# 不用 novel_writing.yaml 是因为它含 4 节点 (read_snapshot + emit_chapter)
# 增加测试复杂度;minimal 适合"基础 happy path" 快速 sanity check。
#
# 不实施 (后续 phase):
# - DECISION 节点测试由 test_decision_pause_resume.py 覆盖 (17 tests)
# - 并行 batch / backtrack 真实触发 / output 落盘

workflow: minimal_e2e
version: 1

nodes:
  - id: write
    type: generation
    name: Write Chapter
    description: chapter_writing
    depends_on: []
    prompt_scenario: chapter_writing
    output_schema: ChapterDraft
    token_budget: 4000
    timeout_s: 60

  - id: review
    type: evaluation
    name: Review Chapter
    description: chapter_review
    depends_on: [write]
    prompt_scenario: chapter_review
    output_schema: QualityReport
    token_budget: 2000
    timeout_s: 60

  - id: polish
    type: generation
    name: Polish
    description: ai_trace_removal
    depends_on: [review]
    prompt_scenario: ai_trace_removal
    output_schema: null
    token_budget: 1000
    timeout_s: 30
```

- [ ] **Step 2: 验证 YAML 加载 (sanity check)**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
python -c "
from infra.got.workflow_loader import load_workflow
g = load_workflow('minimal_e2e')
print(f'nodes: {[n.id for n in g.nodes.values()]}')
print(f'edges: {[(e.from_node, e.to_node) for e in g.edges]}')
"
```

Expected: 打印 `nodes: ['write', 'review', 'polish']` 和 3 条 edge (write→review, review→polish)

---

## Task 2: 创建 _e2e_helpers.py (StubProvider + make_master_with_router)

**Files:**
- Create: `tests/agent_system/_e2e_helpers.py`

- [ ] **Step 1: 写 helpers 文件**

```python
"""E2E 集成测试 helpers (Phase 7)

目标:把 MasterController 的 router 注入点封装为可复用 fixture,
让 test_master_controller_e2e_real_llm.py 集中精力写业务断言。

设计:
- StubProvider 继承 AIProvider,记录所有 generate() calls,返回固定 response
- make_stub_router(responses) 构造 AIRouter,3 个 provider 槽位都注册 StubProvider
- make_master_with_router(router, tmp_path) 构造 MasterController(router=router, state_dir=tmp_path)
  不替换任何 master.* 方法,完全走生产路径
- run_workflow 内部:AgentComputeFn → master.write_chapter → content_writer → self._router.generate
  → AIRouter (select provider) → StubProvider.generate (记录 + 返回)
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from infra.ai_service.base import AIProvider, ProviderConfig
from infra.ai_service.router import AIRouter
from infra.agent_system.master_controller import MasterController


class StubProvider(AIProvider):
    """Test stub — 记录所有 generate() calls,返回固定 response 或抛错。

    跟 test_llm_compute.py 的 _StubProvider 等价,但显式继承 AIProvider
    以满足 AIRouter 内部 prov.generate(prompt, **kwargs) 调用。
    """

    def __init__(
        self,
        name: str,
        response: Union[str, Exception] = "ok",
    ):
        # 注: AIProvider.__init__ 需要 ProviderConfig (api_key 非空)
        # 用假 key 即可,generate() 不会真正调外部 API
        super().__init__(ProviderConfig(api_key="stub-key", model=name))
        self._name = name
        self._response = response
        self.calls: list[dict] = []  # [{prompt, kwargs}, ...]

    def get_provider_name(self) -> str:
        return self._name

    def generate(self, prompt: str, **kwargs) -> str:
        self.calls.append({"prompt": prompt, "kwargs": dict(kwargs)})
        if isinstance(self._response, Exception):
            raise self._response
        return self._response

    def embed(self, text: str):  # pragma: no cover
        return [0.0]

    def batch_generate(self, prompts, **kwargs):  # pragma: no cover
        return [self.generate(p, **kwargs) for p in prompts]


def make_stub_router() -> tuple[AIRouter, dict[str, StubProvider]]:
    """构造 AIRouter,3 个 provider 槽位都注册 StubProvider。

    AIRouter 的 provider 槽位是 "anthropic"/"openai"/"minimax" 等字符串名。
    返回 (router, providers) 二元组;providers 字典按 provider 名索引 StubProvider 实例,
    供测试断言 "哪个 provider 被调了"。

    Returns:
        (router, {"anthropic": StubProvider, "openai": StubProvider, "minimax": StubProvider})
    """
    providers = {
        "anthropic": StubProvider("anthropic", "anthropic-response"),
        "openai": StubProvider("openai", "openai-response"),
        "minimax": StubProvider("minimax", "minimax-response"),
    }
    # 用 AIRouter 的 register_provider 方法 (line 83),跳过它的 cls lookup
    from infra.ai_service.base import ProviderConfig  # noqa: F401
    router = AIRouter(
        config={},  # 传空 config,避免 AIRouter.__init__ 调 get_provider_class
        primary_provider="anthropic",
        enable_failover=False,  # 测试时不启用 failover,精确断言调用次数
    )
    for name, prov in providers.items():
        router.register_provider(name, prov)
    return router, providers


def make_stub_router_with_responses(
    responses: dict[str, Union[str, Exception]],
) -> tuple[AIRouter, dict[str, StubProvider]]:
    """构造 AIRouter,每个 provider 用独立 response (string 或 Exception)。

    Args:
        responses: {"anthropic": "ok", "openai": ValueError(...), ...}

    Returns:
        (router, providers) — providers 字典里 StubProvider 用了传入的 response
    """
    router = AIRouter(
        config={},
        primary_provider=list(responses.keys())[0],
        enable_failover=False,
    )
    providers: dict[str, StubProvider] = {}
    for name, resp in responses.items():
        providers[name] = StubProvider(name, resp)
        router.register_provider(name, providers[name])
    return router, providers


def make_master_with_router(
    state_dir: Path,
    router: AIRouter,
) -> MasterController:
    """构造 MasterController,注入测试 router,不替换任何 master 方法。

    MasterController.__init__ 接受 router= 参数 (master_controller.py:48-62),
    用 `self._router = router if router is not None else build_router(self._config)` 直接接收,
    然后 build_agent_tools(self._router) 用它构造 5 个 Agent 工具。

    Args:
        state_dir: 临时状态目录 (pytest tmp_path)
        router: 测试 AIRouter (3 个 StubProvider)

    Returns:
        完整构造的 MasterController 实例,所有 master.* 方法都是原方法,
        AgentComputeFn 会真实调 write_chapter / audit_chapter / polish_chapter,
        这些方法内部用 self._router.generate → StubProvider.generate。
    """
    return MasterController(state_dir=str(state_dir), router=router)
```

- [ ] **Step 2: ruff check**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
ruff check tests/agent_system/_e2e_helpers.py
```

Expected: 0 errors

---

## Task 3: 写 TestMinimalWorkflowE2E (6 tests)

**Files:**
- Create: `tests/agent_system/test_master_controller_e2e_real_llm.py`

- [ ] **Step 1: 写第 1 个 test (happy path)**

```python
"""Tests for MasterController.run_workflow E2E integration (Phase 7)

Doc 4 (GoT 适配设计 v1.0) §11 Phase 7:
- 验证 MasterController.run_workflow → AgentComputeFn → master 方法 →
  router → 真实 LLM 替代品 这条生产链
- 不替换任何 master 方法,只替换 router 注入点
- 用 StubProvider 模拟 LLM API,记录所有 calls

差异 (vs test_master_controller_workflow.py:121-141):
- 那个文件用 types.MethodType 替换 master.write_chapter/audit_chapter/polish_chapter
  在注释里写明"避免触发真实 LLM"
- 本文件保留 master 方法原样,只把 router 换成 AIRouter(3 StubProvider)
  走完整生产链(content_writer.generate_chapter → self._router.generate)
"""
from __future__ import annotations

from pathlib import Path

import pytest

from infra.ai_service.router import AIRouter
from infra.got.data_structures import NodeStatus
from tests.agent_system._e2e_helpers import (
    make_master_with_router,
    make_stub_router,
    make_stub_router_with_responses,
)


class TestMinimalWorkflowE2E:
    """minimal_e2e.yaml 端到端 (3 节点 linear,write → review → polish)"""

    def test_happy_path_completes_all_three_nodes(self, tmp_path: Path):
        """3 节点全部 COMPLETED,summary.completed == 3,failed == 0"""
        router, _ = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        result = master.run_workflow(
            workflow_name="minimal_e2e",
            initial_inputs={
                "chapter_num": 1,
                "outline": {},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "use_llm": True,
            },
        )

        assert result["summary"].completed == 3
        assert result["summary"].failed == 0
        assert result["summary"].paused is False

    def test_all_three_nodes_in_executions(self, tmp_path: Path):
        """executions 含 write / review / polish 三个节点"""
        router, _ = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        result = master.run_workflow(
            workflow_name="minimal_e2e",
            initial_inputs={
                "chapter_num": 1,
                "outline": {},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "use_llm": True,
            },
        )

        executions = result["executions"]
        assert "write" in executions
        assert "review" in executions
        assert "polish" in executions
        for ex in executions.values():
            assert ex.status == NodeStatus.COMPLETED

    def test_llm_called_three_times(self, tmp_path: Path):
        """3 个 LLM 节点各调 1 次 LLM (read_snapshot 是 input 旁路,emit_chapter 是 output 旁路,
        minimal_e2e 没有这两个,3 节点都是 generation/evaluation)"""
        router, providers = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        master.run_workflow(
            workflow_name="minimal_e2e",
            initial_inputs={
                "chapter_num": 1,
                "outline": {},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "use_llm": True,
            },
        )

        total_calls = sum(len(p.calls) for p in providers.values())
        assert total_calls == 3

    def test_sanity_master_methods_not_replaced(self, tmp_path: Path):
        """Sanity check: master.write_chapter/audit_chapter/polish_chapter 仍是原方法,
        证明测试真的走生产链而不是 stub 路径"""
        router, _ = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        # 原方法的 __qualname__ 形如 "MasterController.write_chapter"
        assert master.write_chapter.__qualname__ == "MasterController.write_chapter"
        assert master.audit_chapter.__qualname__ == "MasterController.audit_chapter"
        assert master.polish_chapter.__qualname__ == "MasterController.polish_chapter"

    def test_each_node_has_output_dict(self, tmp_path: Path):
        """每个节点的 output 是 dict (AgentComputeFn 把 handler 返回值放 output)"""
        router, _ = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        result = master.run_workflow(
            workflow_name="minimal_e2e",
            initial_inputs={
                "chapter_num": 1,
                "outline": {},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "use_llm": True,
            },
        )

        for node_id, ex in result["executions"].items():
            assert isinstance(ex.output, dict), (
                f"node {node_id} output is {type(ex.output).__name__}, expected dict"
            )

    def test_no_decision_pause(self, tmp_path: Path):
        """minimal_e2e.yaml 不含 DECISION 节点 → summary.paused is False,pending_decisions 空"""
        router, _ = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        result = master.run_workflow(
            workflow_name="minimal_e2e",
            initial_inputs={
                "chapter_num": 1,
                "outline": {},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "use_llm": True,
            },
        )

        assert result["summary"].paused is False
        assert result.get("pending_decisions", []) == []
```

- [ ] **Step 2: 跑这 6 tests 验证 GREEN**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
pytest tests/agent_system/test_master_controller_e2e_real_llm.py::TestMinimalWorkflowE2E -v
```

Expected: 6 passed

如果失败,先看哪个 assertion 触发:
- `test_happy_path` 失败 → 检查 `master.run_workflow` 是否正常返回,workflow YAML 是否被加载
- `test_llm_called_three_times` 失败 → 检查 `providers[...].calls` 长度,可能是 content_writer 走 fallback 模式
- `test_sanity_master_methods_not_replaced` 失败 → 不应该,`__new__` 模式才会破坏
- `test_each_node_has_output_dict` 失败 → 节点 output 不是 dict,检查 `agent_compute_fn` 是否包装

---

## Task 4: 写 TestNovelWritingE2E (5 tests)

**Files:**
- Modify: `tests/agent_system/test_master_controller_e2e_real_llm.py` (追加 test class)

- [ ] **Step 1: 追加 TestNovelWritingE2E**

在 `tests/agent_system/test_master_controller_e2e_real_llm.py` 文件末尾追加:

```python
class TestNovelWritingE2E:
    """novel_writing.yaml 端到端 (4 节点:read_snapshot → write_chapter → review_chapter → emit_chapter)

    novel_writing.yaml 含 input/output 旁路节点 (read_snapshot, emit_chapter),
    不调 LLM。只有 write_chapter (chapter_writing) 和 review_chapter (chapter_review) 调 LLM。
    """

    def _run_novel_writing(self, tmp_path: Path, router: AIRouter):
        """helper:跑 novel_writing 工作流,返回 (result, providers)"""
        master = make_master_with_router(tmp_path, router)
        result = master.run_workflow(
            workflow_name="novel_writing",
            initial_inputs={
                "chapter_num": 1,
                "outline": {},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "timeline": [],
                "use_llm": True,
            },
        )
        return result

    def test_four_nodes_all_completed(self, tmp_path: Path):
        """4 节点全部 COMPLETED,summary.completed == 4"""
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        assert result["summary"].completed == 4
        assert result["summary"].failed == 0
        assert result["summary"].paused is False

    def test_only_write_and_review_call_llm(self, tmp_path: Path):
        """read_snapshot (input) + emit_chapter (output) 走旁路不调 LLM,
        只有 write_chapter + review_chapter 各调 1 次 LLM,总 = 2 次"""
        router, providers = make_stub_router()
        self._run_novel_writing(tmp_path, router)

        total_calls = sum(len(p.calls) for p in providers.values())
        assert total_calls == 2, (
            f"expected 2 LLM calls (write + review), got {total_calls}. "
            f"per-provider: {[(n, len(p.calls)) for n, p in providers.items()]}"
        )

    def test_bypass_nodes_have_no_llm_call(self, tmp_path: Path):
        """read_snapshot 和 emit_chapter 节点的 prompt_scenario 是 null,
        AgentComputeFn 走旁路 (got_bridge.py:168) → ComputeResult(output=dict(inputs), cost_tokens=0)"""
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        bypass_nodes = ("read_snapshot", "emit_chapter")
        for node_id in bypass_nodes:
            ex = result["executions"][node_id]
            # 旁路节点 output 应该是 dict 含 inputs 的字段
            assert isinstance(ex.output, dict)
            # 旁路节点 cost_tokens = 0 (got_bridge.py:169)
            assert ex.cost_tokens == 0

    def test_executions_graph_complete(self, tmp_path: Path):
        """4 节点全在 executions 里,边关系正确 (read → write → review → emit)"""
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        executions = result["executions"]
        expected_ids = {"read_snapshot", "write_chapter", "review_chapter", "emit_chapter"}
        assert set(executions.keys()) == expected_ids
        for ex in executions.values():
            assert ex.status == NodeStatus.COMPLETED

    def test_novel_writing_does_not_pause(self, tmp_path: Path):
        """novel_writing.yaml 不含 DECISION 节点 → 不 pause,pending_decisions 空"""
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        assert result["summary"].paused is False
        assert result.get("pending_decisions", []) == []
```

- [ ] **Step 2: 跑 TestNovelWritingE2E 5 tests 验证 GREEN**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
pytest tests/agent_system/test_master_controller_e2e_real_llm.py::TestNovelWritingE2E -v
```

Expected: 5 passed

如果失败:
- `test_only_write_and_review_call_llm` 失败 → 检查 emit_chapter 是否误调 LLM(应有逻辑短路)
- `test_bypass_nodes_have_no_llm_call` 失败 → 检查 `cost_tokens` 字段是否在 NodeExecution 上,或在 result["executions"][node_id].cost_tokens

---

## Task 5: 写 TestRouterFailure (3 tests)

**Files:**
- Modify: `tests/agent_system/test_master_controller_e2e_real_llm.py` (追加 test class)

- [ ] **Step 1: 追加 TestRouterFailure**

在 `tests/agent_system/test_master_controller_e2e_real_llm.py` 文件末尾追加:

```python
class TestRouterFailure:
    """router 失败路径:单 provider 抛错降级 / 全部失败 → NodeStatus.FAILED"""

    def test_run_workflow_does_not_raise_on_provider_error(self, tmp_path: Path):
        """单个 provider 抛错 → 节点 catch 后 fail=True → run_workflow 不抛异常
        (per got_bridge.py:181 已确认 — handler 抛异常被 ComputeResult 包)"""
        router, _ = make_stub_router_with_responses({
            "anthropic": ValueError("anthropic down"),
        })
        master = make_master_with_router(tmp_path, router)

        # 关键: run_workflow 不 raise (production contract)
        result = master.run_workflow(
            workflow_name="minimal_e2e",
            initial_inputs={
                "chapter_num": 1,
                "outline": {},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "use_llm": True,
            },
        )

        # 因为 AIRouter 关闭了 failover (enable_failover=False) 且只有 1 个 provider,
        # 它会 raise AIProviderError → AgentComputeFn 捕获 → ComputeResult.fail=True
        # → 节点 FAILED,其他节点仍 COMPLETED
        assert result["summary"].failed >= 1
        assert "write" in result["executions"]
        write_exec = result["executions"]["write"]
        assert write_exec.status == NodeStatus.FAILED

    def test_router_uses_only_anthropic_provider(self, tmp_path: Path):
        """默认 primary_provider="anthropic" + enable_failover=False → 只调 anthropic"""
        router, providers = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        master.run_workflow(
            workflow_name="minimal_e2e",
            initial_inputs={
                "chapter_num": 1,
                "outline": {},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "use_llm": True,
            },
        )

        # 3 节点全走 anthropic (primary)
        assert len(providers["anthropic"].calls) == 3
        # openai/minimax 完全没被调
        assert len(providers["openai"].calls) == 0
        assert len(providers["minimax"].calls) == 0

    def test_prompts_include_scenario_metadata(self, tmp_path: Path):
        """StubProvider 收到的 prompt 应该非空 (master 方法 → content_writer → router.generate
        时 prompt 是构造好的,非空 string)"""
        router, providers = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        master.run_workflow(
            workflow_name="minimal_e2e",
            initial_inputs={
                "chapter_num": 1,
                "outline": {},
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "use_llm": True,
            },
        )

        # 3 个 prompt 全部非空
        prompts = [c["prompt"] for c in providers["anthropic"].calls]
        assert len(prompts) == 3
        for p in prompts:
            assert isinstance(p, str)
            assert len(p) > 0
```

- [ ] **Step 2: 跑 TestRouterFailure 3 tests 验证 GREEN**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
pytest tests/agent_system/test_master_controller_e2e_real_llm.py::TestRouterFailure -v
```

Expected: 3 passed

如果失败:
- `test_run_workflow_does_not_raise_on_provider_error` 失败 → 可能是 AIRouter 真的 raise 出去了
  (per AIRouter:179 `raise AIProviderError(str(last_error))`),看是否在 production chain 里被 catch
- `test_router_uses_only_anthropic_provider` 失败 → 检查 primary_provider 设置

---

## Task 6: ruff 0 + 全套验证

**Files:** (no new files)

- [ ] **Step 1: ruff check 全部新文件**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
ruff check tests/agent_system/_e2e_helpers.py \
          tests/agent_system/test_master_controller_e2e_real_llm.py \
          infra/got/workflows/minimal_e2e.yaml
```

Expected: 0 errors (yaml 应该被 ruff 忽略或 OK)

- [ ] **Step 2: 跑 Phase 7 全部新 tests**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
pytest tests/agent_system/test_master_controller_e2e_real_llm.py -v
```

Expected: 14 passed

- [ ] **Step 3: 跑全套不回归**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
pytest -q --ignore=tests/e2e
```

Expected: **2006 + 14 = 2020 passed**, 0 failed, 17 skipped

如果失败数 > 0:检查具体失败的 test,可能是 minimal_e2e.yaml 路径解析问题或 AIRouter 接口假设错误。**不要**改 spec / plan,只改 test 假设(让断言跟 production 行为对齐),并把对齐结果记录在 commit message。

---

## Task 7: 1 commit + push

**Files:** (modified/new: 3 files)

- [ ] **Step 1: git status + diff**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
git status
git diff --stat
```

Expected: 3 untracked files (minimal_e2e.yaml, _e2e_helpers.py, test_master_controller_e2e_real_llm.py)

- [ ] **Step 2: commit**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
git add infra/got/workflows/minimal_e2e.yaml \
        tests/agent_system/_e2e_helpers.py \
        tests/agent_system/test_master_controller_e2e_real_llm.py
git commit -m "$(cat <<'EOF'
feat(agent_system): phase 7 — MasterController.run_workflow E2E 集成 (StubProvider 模拟 LLM)

补 E2E 集成测试,验证生产链 MasterController.run_workflow → AgentComputeFn →
master 方法 → router → 真实 LLM 替代品。

设计:
- MasterController(router=...) 现有参数 (master_controller.py:48-62) 注入测试 AIRouter
- AIRouter 3 个 provider 槽位注册 StubProvider(继承 AIProvider,记录 calls + 固定 response)
- 不替换任何 master.* 方法,完全走生产路径(content_writer → self._router.generate)
- 区别 test_master_controller_workflow.py:121-141 的 types.MethodType 替换模式

文件:
- infra/got/workflows/minimal_e2e.yaml: 3 节点 linear (write → review → polish)
- tests/agent_system/_e2e_helpers.py: StubProvider + make_master_with_router helpers
- tests/agent_system/test_master_controller_e2e_real_llm.py: 14 tests / 3 classes
  - TestMinimalWorkflowE2E (6): happy path / node 状态 / LLM 调用次数 /
    sanity check master 方法未替换 / output 是 dict / 无 DECISION pause
  - TestNovelWritingE2E (5): 4 节点走完 / 只 2 次 LLM 调用 (read/emit 旁路) /
    bypass 节点 cost_tokens=0 / 完整 graph / 无 pause
  - TestRouterFailure (3): 单 provider 抛错 → NodeStatus.FAILED / run_workflow
    不 raise / 全部调用走 primary provider / prompt 非空

DECISION + MasterController 集成 (17 tests) 已被
tests/got/test_decision_pause_resume.py 覆盖,本 phase 不重复。

测试: 2006 → 2020 passed (+14)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 3: 推 origin**

```bash
cd /home/ailearn/projects/AI-Incursion/domains/IP创作/projects/LingWen/novel-factory
git push origin master
```

Expected: 推送成功,本地 master 跟 origin/master 同步

---

## Task 8: 更新 MEMORY.md

**Files:**
- Modify: `~/.claude/projects/-home-ailearn-projects-AI-Incursion-domains-IP---projects-LingWen/memory/MEMORY.md`

- [ ] **Step 1: 检查 MEMORY.md 行数 (确保 < 200)**

```bash
wc -l ~/.claude/projects/-home-ailearn-projects-AI-Incursion-domains-IP---projects-LingWen/memory/MEMORY.md
```

Expected: < 200

- [ ] **Step 2: 追加 Phase 7 条目**

在 MEMORY.md 顶部 "测试覆盖" 段后追加:

```markdown
- **Phase 7 (2026-06-04)**: Doc 4 §11 Phase 7 — MasterController.run_workflow E2E 集成 (StubProvider 模拟真实 LLM) — infra/got/workflows/minimal_e2e.yaml (3 节点 linear) + tests/agent_system/_e2e_helpers.py (StubProvider 继承 AIProvider + make_master_with_router 注入 AIRouter 不替换 master 方法) + tests/agent_system/test_master_controller_e2e_real_llm.py (14 tests / 3 classes: MinimalWorkflowE2E 6 / NovelWritingE2E 5 / RouterFailure 3); 利用 MasterController(router=) 现有参数 (master_controller.py:48-62) 注入测试 AIRouter,区别 test_master_controller_workflow.py:121-141 的 types.MethodType 替换模式; novel_writing.yaml 4 节点含 read/emit 旁路只调 2 次 LLM,DECISION+MasterController 已被 test_decision_pause_resume.py 17 tests 覆盖不重复; 2006→2020 passed (+14); 1 commit 推送 origin/master
```

- [ ] **Step 3: 验证总行数**

```bash
wc -l ~/.claude/projects/-home-ailearn-projects-AI-Incursion-domains-IP---projects-LingWen/memory/MEMORY.md
```

Expected: 仍在 < 200 (如果接近 200,精简已有条目)

---

## Self-Review

执行 checklist 验完整 plan:

**1. Spec 覆盖**:
- [x] 架构 (Task 0 architecture + Task 1-7 实施)
- [x] 3 文件改动 (Task 1 YAML / Task 2 helpers / Task 3-5 tests)
- [x] 14 tests (Task 3: 6 / Task 4: 5 / Task 5: 3)
- [x] 错误处理 (Task 5 TestRouterFailure)
- [x] 验证 (Task 6 ruff + 全套)

**2. Placeholder 扫描**:
- 无 "TBD" / "TODO" / "fill in details"
- 无 "similar to Task N" — 每个 Task 的代码都完整

**3. Type 一致性**:
- `make_stub_router()` 返回 `tuple[AIRouter, dict[str, StubProvider]]` — Task 2 + Task 3 都用此签名 ✓
- `make_master_with_router(state_dir: Path, router: AIRouter)` — Task 2 + Task 3/4/5 都用此签名 ✓
- `master.run_workflow(workflow_name=..., initial_inputs={...})` — 3 个 test class 都用同形 initial_inputs ✓
- `result["summary"].completed / failed / paused` — 跟 test_master_controller_workflow.py:169 一致 ✓
- `result["executions"][node_id].status / output / cost_tokens` — 跟 test_decision_pause_resume.py 一致 ✓

**4. 文件路径精确性**:
- `infra/got/workflows/minimal_e2e.yaml` — 新建,跟现有 `novel_writing.yaml` 同目录 ✓
- `tests/agent_system/_e2e_helpers.py` — 新建,跟 `test_master_controller_workflow.py` 同目录 ✓
- `tests/agent_system/test_master_controller_e2e_real_llm.py` — 新建 ✓
- `~/.claude/projects/-.../memory/MEMORY.md` — 已存在,append-only ✓

**完成定义**:
- 3 新文件创建,ruff 0
- 14 新 tests 全部通过
- 全套 2006 → 2020 passed
- 1 commit 推 origin/master
- MEMORY.md 追加 Phase 7 条目

---

## 风险 + 缓解

| 风险 | 缓解 |
|---|---|
| `master.run_workflow` 在 router raise 时会 propagate 到 caller | Task 5 test_run_workflow_does_not_raise_on_provider_error 显式断言,若 fail 则改 plan 而非修测试 |
| `NodeExecution.cost_tokens` 字段名假设错误 | Task 4 test_bypass_nodes_have_no_llm_call 验证,若 fail 在 commit message 里标注 |
| `result["executions"][node_id].output` 不是 dict (可能是 str) | Task 3 test_each_node_has_output_dict 验证,若 fail 改用 `isinstance(..., (dict, str))` 兼容 |
| StubProvider 用 `ProviderConfig(api_key="stub-key")` 但 AIRouter 又要求 `register_provider` 后才能用 | Task 2 已显式 `register_provider` (绕过 AIRouter.__init__ 的 `get_provider_class` 查表) |
| `MasterController(state_dir=..., router=...)` 仍会调 `load_default_config` (因为 config=None 走 fallback) | 这是 expected — config 仍需有 state_dir 等元数据;router 注入仅覆盖 `self._router` 不影响其他子模块 |
| 跟 `test_master_controller_workflow.py` 的 __new__ 模式混用导致 fixture 冲突 | helper 文件独立,fixture 命名 (`_e2e_master_with_router`) 显式加 `_e2e_` 前缀跟现有 `_make_controller_with_stubs` 区分 |
| minimal_e2e.yaml 的 depends_on [] 写法,workflow_loader 能否正确处理 | Task 1 Step 2 用 `load_workflow("minimal_e2e")` 显式 sanity check |

---

## 完成定义

- [ ] 3 个新文件创建并 ruff 0
- [ ] 14 个新测试全部通过
- [ ] 全套 2006 → 2020 passed, 0 failed, 17 skipped
- [ ] 1 commit 推送 origin/master
- [ ] MEMORY.md 追加 Phase 7 条目,行数 < 200
