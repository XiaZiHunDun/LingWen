"""Tests for MasterController.run_workflow (Phase 3.2 — GoT integration)

Doc 4 (GoT 适配设计 v1.0) §十一 Phase 3:
MasterController.run_workflow 委托给 GoT bridge + GoTScheduler。

- run_workflow 返回 {"summary", "graph", "executions"} 三元组
- 默认 start_nodes = 无依赖的节点 (e.g. read_snapshot)
- initial_inputs 注入到起点节点
- 老 API (advance_step/dispatch_task) 不受影响,GoT 是新入口
"""
from __future__ import annotations

from typing import Any, Optional

import pytest

# === Stub MasterController (避免连真实 API) ===

class _StubMaster:
    """最小 MasterController stub — 只实现 run_workflow 依赖的方法"""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def write_chapter(self, chapter_num, outline, characters, memory_context, style_guide, use_llm):
        self.calls.append(("write_chapter", {"chapter_num": chapter_num}))
        return {
            "content": f"ch{chapter_num} text",
            "word_count": 100,
            "suggestions": [],
            "chapter_num": chapter_num,
        }

    def audit_chapter(self, chapter_num, content, characters, timeline, use_llm):
        self.calls.append(("audit_chapter", {"chapter_num": chapter_num, "content_len": len(content)}))
        return {"chapter": chapter_num, "issues": [], "scores": {"S1": 80}}

    def polish_chapter(self, content: str) -> str:
        return content + " [polished]"

    # Phase 7.5: stub polish_merge_synthesis — 走 max(len) 兜底
    def polish_merge_synthesis(self, content_a: str, content_b: str, *, labels=("A", "B")) -> dict:
        """Stub: 走 max(len) 兜底 (默认不调 LLM)"""
        if not content_a or not content_b:
            winner = labels[0] if content_a else labels[1]
            content = content_a or content_b
            return {"content": content, "winner": winner, "scores_a": {}, "scores_b": {}, "scores_total_a": 0.0, "scores_total_b": 0.0, "scores_delta": 0.0, "fallback": "empty_content"}
        if content_a == content_b:
            return {"content": content_a, "winner": labels[0], "scores_a": {}, "scores_b": {}, "scores_total_a": 0.0, "scores_total_b": 0.0, "scores_delta": 0.0, "fallback": "identical"}
        winner_label = labels[0] if len(content_a) >= len(content_b) else labels[1]
        content = content_a if winner_label == labels[0] else content_b
        return {"content": content, "winner": winner_label, "scores_a": {}, "scores_b": {}, "scores_total_a": 0.0, "scores_total_b": 0.0, "scores_delta": 0.0, "fallback": "llm_fail"}

    def generate_outline(self, settings, requirements):
        return {"chapters": [], "volume": 1}


# === 真实 MasterController + stub Agent methods (通过 monkeypatch) ===

class _StubAgents:
    """模拟 MasterController 的 5 个 Agent — 直接给 controller 注入"""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def write_chapter(self, chapter_num, outline, characters, memory_context, style_guide, use_llm):
        self.calls.append(("write_chapter", {"chapter_num": chapter_num}))
        return {
            "content": f"chapter {chapter_num} content",
            "chapter_num": chapter_num,
            "word_count": 50,
        }

    def audit_chapter(self, chapter_num, content, characters, timeline, use_llm):
        self.calls.append(("audit_chapter", {"chapter_num": chapter_num}))
        return {"chapter": chapter_num, "issues": [], "scores": {"S1": 90}}

    def polish_chapter(self, content: str) -> str:
        return content + " (polished)"

    # Phase 7.4: 新增 2 个 variant entry methods (用于 stub 测试)
    def polish_emotional_pacing(self, content: str) -> str:
        return content + " (emotional)"

    def polish_ai_trace_removal(self, content: str) -> str:
        return content + " (ai_removed)"

    # Phase 8.6.2: 5 *_with_usage methods (handler 调 variant 拿真实 usage)
    def write_chapter_with_usage(self, chapter_num, outline, characters, memory_context, style_guide, use_llm):
        self.calls.append(("write_chapter_with_usage", {"chapter_num": chapter_num}))
        return (
            {
                "content": f"chapter {chapter_num} content",
                "chapter_num": chapter_num,
                "word_count": 50,
            },
            {"input_tokens": 100, "output_tokens": 50},
        )

    def generate_chapter_with_usage(self, chapter_num, context, writer_id=None):
        """content_writer.generate_chapter_with_usage 签名: (chapter_num, context, writer_id=None)"""
        self.calls.append(("generate_chapter_with_usage", {"chapter_num": chapter_num}))
        return (
            {"content": f"chapter {chapter_num} content", "word_count": 50},
            {"input_tokens": 100, "output_tokens": 50},
        )

    def audit_chapter_with_usage(self, *args, **kwargs):
        """Accept both master signature (timeline=) and auditor signature (context=)"""
        chapter_num = kwargs.get("chapter_num", args[0] if args else 0)
        kwargs.get("content", args[1] if len(args) > 1 else "")
        self.calls.append(("audit_chapter_with_usage", {"chapter_num": chapter_num}))
        return (
            {"chapter": chapter_num, "issues": [], "scores": {"S1": 90}},
            {"input_tokens": 80, "output_tokens": 40},
        )

    def polish_chapter_with_usage(self, chapter_num, content, style_guide=None):
        return (content + " (polished)", {"input_tokens": 200, "output_tokens": 100})

    def polish_emotional_pacing_with_usage(self, chapter_num, content):
        return (content + " (emotional)", {"input_tokens": 200, "output_tokens": 100})

    def polish_ai_trace_removal_with_usage(self, chapter_num, content):
        return (content + " (ai_removed)", {"input_tokens": 100, "output_tokens": 50})

    # Phase 7.5: stub polish_merge_synthesis
    def polish_merge_synthesis(self, content_a, content_b, *, labels=("A", "B")) -> dict:
        if not content_a or not content_b:
            winner = labels[0] if content_a else labels[1]
            content = content_a or content_b
            return {"content": content, "winner": winner, "scores_a": {}, "scores_b": {}, "scores_total_a": 0.0, "scores_total_b": 0.0, "scores_delta": 0.0, "fallback": "empty_content"}
        if content_a == content_b:
            return {"content": content_a, "winner": labels[0], "scores_a": {}, "scores_b": {}, "scores_total_a": 0.0, "scores_total_b": 0.0, "scores_delta": 0.0, "fallback": "identical"}
        winner_label = labels[0] if len(content_a) >= len(content_b) else labels[1]
        content = content_a if winner_label == labels[0] else content_b
        return {"content": content, "winner": winner_label, "scores_a": {}, "scores_b": {}, "scores_total_a": 0.0, "scores_total_b": 0.0, "scores_delta": 0.0, "fallback": "llm_fail"}

    def generate_outline(self, settings, requirements):
        return {"chapters": [], "volume": 1}


def _make_controller_with_stubs(monkeypatch) -> tuple[Any, _StubAgents]:
    """构造 MasterController 但 stub 掉 init 中的重操作,只保留 run_workflow 链路"""
    from infra.agent_system import master_controller as mc_mod

    # 阻止 __init__ 中调 build_router (需要 API key)
    monkeypatch.setattr(mc_mod, "build_router", lambda config: None)
    monkeypatch.setattr(mc_mod, "build_orchestrator", lambda **kwargs: None)
    monkeypatch.setattr(mc_mod, "build_skill_registry", lambda: None)
    monkeypatch.setattr(mc_mod, "build_agent_tools", lambda router: None)
    monkeypatch.setattr(mc_mod, "build_social_engine", lambda state_dir: None)
    # StateManager 在 __init__ 内部用 `from ..state.state_manager import StateManager` 导入
    # 需要 patch 它在原模块中的位置
    import infra.state.state_manager as sm_mod
    monkeypatch.setattr(sm_mod, "StateManager", lambda *a, **kw: None)

    controller = mc_mod.MasterController.__new__(mc_mod.MasterController)
    stub = _StubAgents()
    # 注入 stubbed agents (MasterController.write_chapter 会用 outline_master.schema 等)
    # 用 lambda 包装: MasterController 调 self.write_chapter(...) → 走 lambda → stub.write_chapter
    # 但 AgentComputeFn 直接调 master.write_chapter,这里 master.write_chapter 走原方法
    # 实际我们 stub 的是 content_writer.generate_chapter (write_chapter 内部)
    controller.content_writer = type(
        "cw",
        (),
        {
            "generate_chapter": stub.write_chapter,
            # Phase 8.6.2: handler 调 write_chapter_with_usage → content_writer.generate_chapter_with_usage
            "generate_chapter_with_usage": stub.generate_chapter_with_usage,
        },
    )()
    controller.auditor = type(
        "au",
        (),
        {
            "check_character_consistency": staticmethod(lambda content, characters: []),
            "detect_ai_gloss": staticmethod(lambda content: []),
            "generate_audit_report": staticmethod(lambda chapter_num, issues, scores: {"chapter": chapter_num, "issues": issues, "scores": scores}),
            # Phase 8.6.2: handler 调 audit_chapter_with_usage (调 self.auditor.audit_chapter_with_usage)
            "audit_chapter_with_usage": stub.audit_chapter_with_usage,
        },
    )()
    controller.polisher = type(
        "po",
        (),
        {
            "remove_ai_gloss": stub.polish_chapter,
            "polish_chapter_with_usage": stub.polish_chapter_with_usage,
            "optimize_dialogue_llm_with_usage": lambda content: (content + " (dialogue)", {"input_tokens": 100, "output_tokens": 50}),
            "adjust_pacing_llm_with_usage": lambda content: (content + " (pacing)", {"input_tokens": 100, "output_tokens": 50}),
        },
    )()
    # outline_master 需要 .schema.get_chapter_outline (write_chapter 调它)
    controller.outline_master = type(
        "om",
        (),
        {"schema": type("s", (), {"get_chapter_outline": staticmethod(lambda *a, **kw: {})})()},
    )()
    controller.character_designer = type("cd", (), {})()
    # write_chapter 还会调 self.context_builder / self.relationship_tracker /
    # self.writing_suggestion
    controller.context_builder = type("cb", (), {"build_writing_context": staticmethod(lambda **kw: {})})()
    controller.writing_suggestion = type("ws", (), {"generate_suggestions": staticmethod(lambda *a, **kw: [])})()
    controller.relationship_tracker = type("rt", (), {"get_network": staticmethod(lambda: {})})()
    # audit_chapter 调 auditor.check_character_consistency + detect_ai_gloss + llm_audit
    # run_workflow 不直接调 audit, 走 AgentComputeFn bridge 调 audit_chapter
    controller.event_calculator = None
    controller.conflict_alert = None
    controller._router = None
    controller._state_manager = None
    controller._orchestrator = None
    controller._skill_registry = None
    controller._config = None
    # MasterController.write_chapter 走 controller.write_chapter,不是 stub
    # AgentComputeFn → master.write_chapter (real method, 内含 router + LLM)
    # 这里让 master.write_chapter 走 stub (避免触发真实 LLM)
    import types
    controller.write_chapter = types.MethodType(
        lambda self, chapter_num, outline, characters, memory_context, style_guide, use_llm: stub.write_chapter(
            chapter_num, outline, characters, memory_context, style_guide, use_llm,
        ),
        controller,
    )
    controller.audit_chapter = types.MethodType(
        lambda self, chapter_num, content, characters, timeline, use_llm: stub.audit_chapter(
            chapter_num, content, characters, timeline, use_llm,
        ),
        controller,
    )
    controller.polish_chapter = types.MethodType(
        lambda self, content: stub.polish_chapter(content), controller,
    )
    # Phase 7.4: stub 新增的 2 个 variant entry methods
    controller.polish_emotional_pacing = types.MethodType(
        lambda self, content: stub.polish_emotional_pacing(content), controller,
    )
    controller.polish_ai_trace_removal = types.MethodType(
        lambda self, content: stub.polish_ai_trace_removal(content), controller,
    )
    # Phase 8.6.2: 5 *_with_usage methods — handler 调 variant 拿真实 usage
    controller.write_chapter_with_usage = types.MethodType(
        lambda self, chapter_num, outline, characters, memory_context, style_guide, use_llm: stub.write_chapter_with_usage(
            chapter_num, outline, characters, memory_context, style_guide, use_llm,
        ),
        controller,
    )
    controller.audit_chapter_with_usage = types.MethodType(
        lambda self, chapter_num, content, characters, timeline, use_llm: stub.audit_chapter_with_usage(
            chapter_num, content, characters, timeline, use_llm,
        ),
        controller,
    )
    controller.polish_chapter_with_usage = types.MethodType(
        lambda self, chapter_num, content, style_guide=None: stub.polish_chapter_with_usage(
            chapter_num, content, style_guide=style_guide,
        ),
        controller,
    )
    controller.polish_emotional_pacing_with_usage = types.MethodType(
        lambda self, chapter_num, content: stub.polish_emotional_pacing_with_usage(chapter_num, content),
        controller,
    )
    controller.polish_ai_trace_removal_with_usage = types.MethodType(
        lambda self, chapter_num, content: stub.polish_ai_trace_removal_with_usage(chapter_num, content),
        controller,
    )
    # Phase 7.5: stub polish_merge_synthesis
    controller.polish_merge_synthesis = types.MethodType(
        lambda self, content_a, content_b, *, labels=("A", "B"): stub.polish_merge_synthesis(
            content_a, content_b, labels=labels,
        ),
        controller,
    )
    controller.generate_outline = types.MethodType(
        lambda self, settings, requirements: stub.generate_outline(settings, requirements), controller,
    )
    return controller, stub


# === TestMasterControllerRunWorkflow ===

class TestMasterControllerRunWorkflow:
    """MasterController.run_workflow API 验证"""

    def test_run_workflow_returns_three_part_dict(self, monkeypatch):
        """run_workflow 返回 {summary, graph, executions}"""
        controller, _ = _make_controller_with_stubs(monkeypatch)
        result = controller.run_workflow(
            workflow_name="novel_writing",
            start_nodes=["read_snapshot"],
            initial_inputs={"chapter_num": 1, "characters": [], "style_guide": {}, "timeline": []},
        )
        assert "summary" in result
        assert "graph" in result
        assert "executions" in result

    def test_run_workflow_summary_has_completed_count(self, monkeypatch):
        controller, _ = _make_controller_with_stubs(monkeypatch)
        result = controller.run_workflow(
            workflow_name="novel_writing",
            start_nodes=["read_snapshot"],
            initial_inputs={"chapter_num": 1, "characters": [], "style_guide": {}, "timeline": []},
        )
        # Phase 7.4: 7 节点全 COMPLETED (含 2 个并行 polish + 1 merge)
        assert result["summary"].completed == 7
        assert result["summary"].failed == 0

    def test_run_workflow_executions_has_all_nodes(self, monkeypatch):
        controller, _ = _make_controller_with_stubs(monkeypatch)
        result = controller.run_workflow(
            workflow_name="novel_writing",
            start_nodes=["read_snapshot"],
            initial_inputs={"chapter_num": 1, "characters": [], "style_guide": {}, "timeline": []},
        )
        executions = result["executions"]
        assert "read_snapshot" in executions
        assert "write_chapter" in executions
        assert "review_chapter" in executions
        assert "emit_chapter" in executions

    def test_run_workflow_default_start_nodes(self, monkeypatch):
        """start_nodes=None → 自动选无依赖节点 (read_snapshot)"""
        controller, _ = _make_controller_with_stubs(monkeypatch)
        result = controller.run_workflow(
            workflow_name="novel_writing",
            initial_inputs={"chapter_num": 1, "characters": [], "style_guide": {}, "timeline": []},
        )
        # Phase 7.4: 默认起点 read_snapshot,跑完整 7 节点链
        assert result["summary"].completed == 7

    def test_run_workflow_dispatches_to_real_agent_methods(self, monkeypatch):
        """run_workflow 通过 AgentComputeFn 调 content_writer / auditor"""
        controller, stub = _make_controller_with_stubs(monkeypatch)
        controller.run_workflow(
            workflow_name="novel_writing",
            start_nodes=["read_snapshot"],
            initial_inputs={"chapter_num": 5, "characters": [], "style_guide": {}, "timeline": []},
        )
        called = [c[0] for c in stub.calls]
        # Phase 8.6.2: handler 调 *_with_usage variant 拿真实 usage
        assert "write_chapter_with_usage" in called
        assert "audit_chapter_with_usage" in called
        # write_chapter_with_usage 收到的 chapter_num=5
        write_call = next(c for c in stub.calls if c[0] == "write_chapter_with_usage")
        assert write_call[1]["chapter_num"] == 5

    def test_run_workflow_invalid_workflow_raises(self, monkeypatch):
        controller, _ = _make_controller_with_stubs(monkeypatch)
        with pytest.raises(Exception):  # WorkflowNotFoundError
            controller.run_workflow(workflow_name="nonexistent_workflow_xyz")


# === TestMasterControllerRunWorkflowBackwardCompat ===

class TestMasterControllerRunWorkflowBackwardCompat:
    """run_workflow 不破坏老 API (advance_step/dispatch_task)"""

    def test_old_methods_still_exist(self, monkeypatch):
        """MasterController 仍含 advance_step / dispatch_task / verify_task"""
        controller, _ = _make_controller_with_stubs(monkeypatch)
        assert hasattr(controller, "advance_step")
        assert hasattr(controller, "dispatch_task")
        assert hasattr(controller, "verify_task")
        assert hasattr(controller, "get_workflow_status")
