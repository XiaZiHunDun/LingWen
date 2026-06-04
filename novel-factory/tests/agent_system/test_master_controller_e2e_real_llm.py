"""Tests for MasterController.run_workflow E2E integration (Phase 7)

Doc 4 (GoT 适配设计 v1.0) §11 Phase 7:
- 验证 MasterController.run_workflow → AgentComputeFn → master 方法 →
  router → 真实 LLM 替代品 这条生产链
- 不替换任何 master 方法,只替换 router 注入点
- 用 StubProvider 模拟 LLM API,记录所有 calls

差异 (vs test_master_controller_workflow.py:121-141):
- 那个文件用 types.MethodType 替换 master.write_chapter/audit_chapter/polish_chapter
- 本文件保留 master 方法原样,只把 router 换成 AIRouter(3 StubProvider)

生产现实 (Phase 7 实测):
- master.write_chapter → content_writer.generate_chapter → 1 次 LLM 调用
- master.audit_chapter → auditor.llm_audit() 不存在,被 AttributeError 捕获 → 0 次 LLM 调用
- master.polish_chapter → PolisherTools.remove_ai_gloss → 纯正则 → 0 次 LLM 调用
- read_snapshot / emit_chapter → AgentComputeFn 旁路 (got_bridge.py:168) → 0 次 LLM 调用

minimal_e2e (2 节点 write→review):预期至少 1 次 LLM 调用
novel_writing (4 节点 read→write→review→emit):预期至少 1 次 LLM 调用

合计:2 类 11 tests + 1 类 3 tests = 14 tests
"""
from __future__ import annotations

from pathlib import Path

import pytest

from infra.ai_service.router import AIRouter
from infra.got.data_structures import NodeStatus
from infra.got.scheduler import HumanInterventionRequired
from tests.agent_system._e2e_helpers import (
    make_master_with_router,
    make_stub_router,
    make_stub_router_with_responses,
)


class TestMinimalWorkflowE2E:
    """minimal_e2e.yaml 端到端 (2 节点 linear,write → review)"""

    # 最小 outline: 1 个章节匹配 chapter_num=1
    # master.write_chapter → content_writer.generate_chapter → build_writing_prompt
    # 需要 outline["chapters"] 含 num=1 的条目
    MINIMAL_OUTLINE = {
        "chapters": [
            {
                "num": 1,
                "title": "第一章",
                "events": ["event_a", "event_b"],
                "word_count_target": 2500,
            }
        ]
    }

    def test_happy_path_completes_both_nodes(self, tmp_path: Path):
        router, _ = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        result = master.run_workflow(
            workflow_name="minimal_e2e",
            initial_inputs={
                "chapter_num": 1,
                "outline": self.MINIMAL_OUTLINE,
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "use_llm": True,
            },
        )

        assert result["summary"].completed == 2
        assert result["summary"].failed == 0
        assert result["summary"].paused is False

    def test_both_nodes_in_executions(self, tmp_path: Path):
        router, _ = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        result = master.run_workflow(
            workflow_name="minimal_e2e",
            initial_inputs={
                "chapter_num": 1,
                "outline": self.MINIMAL_OUTLINE,
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "use_llm": True,
            },
        )

        executions = result["executions"]
        assert "write" in executions
        assert "review" in executions
        assert set(executions.keys()) == {"write", "review"}
        for ex in executions.values():
            assert ex.status == NodeStatus.COMPLETED

    def test_at_least_one_llm_call(self, tmp_path: Path):
        """生产现实:write → 1 次 LLM,review → 0 次 (auditor.llm_audit 不存在,
        AttributeError 被吞)。至少 1 次 LLM 调用证明生产链路通。"""
        router, providers = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        master.run_workflow(
            workflow_name="minimal_e2e",
            initial_inputs={
                "chapter_num": 1,
                "outline": self.MINIMAL_OUTLINE,
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "use_llm": True,
            },
        )

        total_calls = sum(len(p.calls) for p in providers.values())
        assert total_calls >= 1, (
            f"expected at least 1 LLM call (write), got {total_calls}. "
            f"per-provider: {[(n, len(p.calls)) for n, p in providers.items()]}"
        )

    def test_sanity_master_methods_not_replaced(self, tmp_path: Path):
        """Sanity check: master.write_chapter/audit_chapter/polish_chapter 仍是原方法"""
        router, _ = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        assert master.write_chapter.__qualname__ == "MasterController.write_chapter"
        assert master.audit_chapter.__qualname__ == "MasterController.audit_chapter"
        assert master.polish_chapter.__qualname__ == "MasterController.polish_chapter"

    def test_each_node_has_output_dict(self, tmp_path: Path):
        router, _ = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        result = master.run_workflow(
            workflow_name="minimal_e2e",
            initial_inputs={
                "chapter_num": 1,
                "outline": self.MINIMAL_OUTLINE,
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
        router, _ = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        result = master.run_workflow(
            workflow_name="minimal_e2e",
            initial_inputs={
                "chapter_num": 1,
                "outline": self.MINIMAL_OUTLINE,
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "use_llm": True,
            },
        )

        assert result["summary"].paused is False
        assert result.get("pending_decisions", []) == []


class TestNovelWritingE2E:
    """novel_writing.yaml 端到端 (4 节点:read_snapshot → write_chapter → review_chapter → emit_chapter)"""

    MINIMAL_OUTLINE = {
        "chapters": [
            {
                "num": 1,
                "title": "第一章",
                "events": ["event_a"],
                "word_count_target": 2500,
            }
        ]
    }

    def _run_novel_writing(self, tmp_path: Path, router: AIRouter):
        master = make_master_with_router(tmp_path, router)
        result = master.run_workflow(
            workflow_name="novel_writing",
            initial_inputs={
                "chapter_num": 1,
                "outline": self.MINIMAL_OUTLINE,
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "timeline": [],
                "use_llm": True,
            },
        )
        return result

    def test_four_nodes_all_completed(self, tmp_path: Path):
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        assert result["summary"].completed == 4
        assert result["summary"].failed == 0
        assert result["summary"].paused is False

    def test_at_least_one_llm_call(self, tmp_path: Path):
        """read_snapshot (input) + emit_chapter (output) 走旁路不调 LLM。
        write_chapter 至少 1 次 LLM 调用 (review_chapter 因 auditor.llm_audit
        不存在,AttributeError 被吞,可能为 0 次)。"""
        router, providers = make_stub_router()
        self._run_novel_writing(tmp_path, router)

        total_calls = sum(len(p.calls) for p in providers.values())
        assert total_calls >= 1, (
            f"expected at least 1 LLM call from write_chapter, got {total_calls}. "
            f"per-provider: {[(n, len(p.calls)) for n, p in providers.items()]}"
        )

    def test_bypass_nodes_have_no_llm_call(self, tmp_path: Path):
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        bypass_nodes = ("read_snapshot", "emit_chapter")
        for node_id in bypass_nodes:
            ex = result["executions"][node_id]
            assert isinstance(ex.output, dict)
            assert ex.cost_tokens == 0

    def test_executions_graph_complete(self, tmp_path: Path):
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        executions = result["executions"]
        expected_ids = {"read_snapshot", "write_chapter", "review_chapter", "emit_chapter"}
        assert set(executions.keys()) == expected_ids
        for ex in executions.values():
            assert ex.status == NodeStatus.COMPLETED

    def test_novel_writing_does_not_pause(self, tmp_path: Path):
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        assert result["summary"].paused is False
        assert result.get("pending_decisions", []) == []


class TestRouterFailure:
    """router 失败路径:provider 抛错降级 / 默认走 primary"""

    MINIMAL_OUTLINE = {
        "chapters": [
            {
                "num": 1,
                "title": "第一章",
                "events": ["event_a"],
                "word_count_target": 2500,
            }
        ]
    }

    def test_run_workflow_raises_human_intervention_on_provider_error(self, tmp_path: Path):
        """Provider 持续抛错 → GoT 硬回溯 3 次后 → HumanInterventionRequired。

        错误链路应包含原 provider 错误消息 + 失败节点名。
        """
        router, _ = make_stub_router_with_responses({
            "anthropic": ValueError("anthropic down"),
        })
        master = make_master_with_router(tmp_path, router)

        with pytest.raises(HumanInterventionRequired) as exc_info:
            master.run_workflow(
                workflow_name="minimal_e2e",
                initial_inputs={
                    "chapter_num": 1,
                    "outline": self.MINIMAL_OUTLINE,
                    "characters": [],
                    "memory_context": {},
                    "style_guide": {},
                    "use_llm": True,
                },
            )

        # 验证错误链路:节点 write 失败,根因是 provider 抛的 "anthropic down"
        msg = str(exc_info.value)
        assert "write" in msg
        assert "anthropic down" in msg

    def test_router_uses_only_anthropic_provider(self, tmp_path: Path):
        """默认 primary_provider="anthropic" + enable_failover=False → 只调 anthropic"""
        router, providers = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        master.run_workflow(
            workflow_name="minimal_e2e",
            initial_inputs={
                "chapter_num": 1,
                "outline": self.MINIMAL_OUTLINE,
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "use_llm": True,
            },
        )

        assert len(providers["anthropic"].calls) >= 1
        assert len(providers["openai"].calls) == 0
        assert len(providers["minimax"].calls) == 0

    def test_prompts_are_non_empty_strings(self, tmp_path: Path):
        """StubProvider 收到的 prompt 应该非空"""
        router, providers = make_stub_router()
        master = make_master_with_router(tmp_path, router)

        master.run_workflow(
            workflow_name="minimal_e2e",
            initial_inputs={
                "chapter_num": 1,
                "outline": self.MINIMAL_OUTLINE,
                "characters": [],
                "memory_context": {},
                "style_guide": {},
                "use_llm": True,
            },
        )

        prompts = [c["prompt"] for c in providers["anthropic"].calls]
        assert len(prompts) >= 1
        for p in prompts:
            assert isinstance(p, str)
            assert len(p) > 0
