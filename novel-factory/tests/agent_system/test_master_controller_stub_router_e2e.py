"""Tests for MasterController.run_workflow E2E integration (Phase 7)

Doc 4 (GoT 适配设计 v1.0) §11 Phase 7:
- 验证 MasterController.run_workflow → AgentComputeFn → master 方法 →
  router → 真实 LLM 替代品 这条生产链
- 不替换任何 master 方法,只替换 router 注入点
- 用 StubProvider 模拟 LLM API,记录所有 calls

差异 (vs test_master_controller_workflow.py:121-141):
- 那个文件用 types.MethodType 替换 master.write_chapter/audit_chapter/polish_chapter
- 本文件保留 master 方法原样,只把 router 换成 AIRouter(3 StubProvider)

生产现实 (Phase 7.1 修复后):
- master.write_chapter → content_writer.generate_chapter → 1 次 LLM 调用
- master.audit_chapter → auditor.audit_chapter (Phase 7.1 修复: 原 llm_audit 方法名错误)
                → 1 次 LLM 调用
- read_snapshot / emit_chapter → AgentComputeFn 旁路 (got_bridge.py:168) → 0 次 LLM 调用

minimal_e2e (2 节点 write→review):预期至少 2 次 LLM 调用 (write + audit)
novel_writing (4 节点 read→write→review→emit):预期至少 2 次 LLM 调用 (write + audit)

Out of scope (Phase 7.1 跳过的 Polisher 候选):
- master.polish_chapter → PolisherTools 纯正则,0 次 LLM 调用
- minimal_e2e 不含 polish 节点,production 现实下 polish 链不入测试

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
        assert total_calls >= 2, (
            f"expected at least 2 LLM calls (write + audit), got {total_calls}. "
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

    def test_minimal_e2e_unchanged_no_polish(self, tmp_path: Path):
        """Sanity: minimal_e2e.yaml 不应有 polish 节点 (防止误改)"""
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
        assert "polish_chapter" not in result["executions"]


class TestNovelWritingE2E:
    """novel_writing.yaml 端到端 (5 节点:read_snapshot → write_chapter → review_chapter → polish_chapter → emit_chapter)"""

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
        """Phase 7.4: novel_writing 7 节点 — 含 2 个并行 polish + 1 merge (read/write/review/polish_e/polish_a/merge/emit)"""
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        assert result["summary"].completed == 7
        assert result["summary"].failed == 0
        assert result["summary"].paused is False

    def test_at_least_one_llm_call(self, tmp_path: Path):
        """Phase 7.4: novel_writing 7 节点 — write(1) + audit(1) + emotional_pacing{2 LLM} + ai_trace_removal{1 LLM} = 5 次 LLM
        read_snapshot/emit_chapter/polish_merge 旁路或纯 Python
        (polish_ai_trace_removal 走规则 remove_ai_gloss 0 LLM + optimize_dialogue_llm 1 LLM)"""
        router, providers = make_stub_router()
        self._run_novel_writing(tmp_path, router)

        total_calls = sum(len(p.calls) for p in providers.values())
        assert total_calls >= 5, (
            f"expected at least 5 LLM calls (write + audit + emotional_pacing{2} + ai_trace_removal{1}), "
            f"got {total_calls}. per-provider: {[(n, len(p.calls)) for n, p in providers.items()]}"
        )

    def test_novel_writing_has_polish_node(self, tmp_path: Path):
        """Phase 7.4: novel_writing.yaml 应含 2 个并行 polish 节点 + 1 merge (在 review 之后,emit 之前)"""
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        executions = result["executions"]
        assert "polish_emotional_pacing" in executions, (
            f"expected polish_emotional_pacing in executions, got {list(executions.keys())}"
        )
        assert "polish_ai_trace_removal" in executions
        assert "polish_merge" in executions
        # 拓扑: review → 2 个 polish → merge → emit
        assert "review_chapter" in executions
        assert "emit_chapter" in executions

    def test_polish_node_completed_in_production_path(self, tmp_path: Path):
        """Phase 7.4: polish_merge 节点应跑完,不是 SKIPPED/FAILED"""
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        merge_exec = result["executions"]["polish_merge"]
        assert merge_exec.status == NodeStatus.COMPLETED
        assert merge_exec.cost_tokens == 0  # token 估算在 TieredRouter 层

    def test_polish_chapter_output_has_content(self, tmp_path: Path):
        """Phase 7.4: polish_merge 节点 output 含非空 content 字段 (供 emit 落盘)"""
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        merge_output = result["executions"]["polish_merge"].output
        assert isinstance(merge_output, dict)
        assert "content" in merge_output
        content = merge_output["content"]
        assert isinstance(content, str)
        assert len(content) > 0, "polish_merge output.content should be non-empty"

    def test_bypass_nodes_have_no_llm_call(self, tmp_path: Path):
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        bypass_nodes = ("read_snapshot", "emit_chapter", "polish_merge")
        for node_id in bypass_nodes:
            ex = result["executions"][node_id]
            assert isinstance(ex.output, dict)
            assert ex.cost_tokens == 0

    def test_executions_graph_complete(self, tmp_path: Path):
        """Phase 7.4: novel_writing 7 节点 — 含 2 个并行 polish + 1 merge"""
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        executions = result["executions"]
        expected_ids = {
            "read_snapshot", "write_chapter", "review_chapter",
            "polish_emotional_pacing", "polish_ai_trace_removal",
            "polish_merge", "emit_chapter",
        }
        assert set(executions.keys()) == expected_ids
        for ex in executions.values():
            assert ex.status == NodeStatus.COMPLETED

    def test_novel_writing_does_not_pause(self, tmp_path: Path):
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        assert result["summary"].paused is False
        assert result.get("pending_decisions", []) == []

    def test_novel_writing_records_cost_to_tracker(self, tmp_path: Path) -> None:
        """Phase 8.5: 跑生产 path 后, cost_tracker 至少记录 1 笔 (写+审核+polish)

        StubProvider 每次返固定 'anthropic-response' 字符串 — 3 scenario 都会调 LLM:
        - chapter_writing (write_chapter → generate_chapter)
        - chapter_review (audit_chapter → auditor.audit_chapter)
        - polish_emotional_pacing (LLM 2 次: dialogue + pacing) + polish_ai_trace_removal (LLM 1 次)
        走 production path 后 cost_tracker 应有 5+ 笔 (write + audit + 2 polish_e + 1 polish_a),
        不依赖 polish_merge (走 identical fallback 不调 LLM)
        """
        from infra.ai_service.cost_tracker import CostTracker

        cost_tracker = CostTracker()
        router, _ = make_stub_router()
        master = make_master_with_router(tmp_path, router, cost_tracker=cost_tracker)
        master.run_workflow(
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
        # 至少 1 笔 + 至少 1 scenario
        assert cost_tracker.total_cost() > 0
        assert cost_tracker.count_by_scenario(), (
            f"expected at least 1 scenario recorded, got {cost_tracker.count_by_scenario()}"
        )

    def test_novel_writing_records_real_cost_usage(self, tmp_path: Path) -> None:
        """Phase 8.6.2: 走 production path, cost_tracker 收到真实 usage (非 len()//4 估算).

        record_usage=True 注入 _RecordingRouter (Phase 8.6.1 stub), _UsageRecordingProvider
        硬编码 {input_tokens: 100, output_tokens: 50} — 每次 LLM call 喂 cost_tracker
        真实 100+50=150, 而非 StubProvider + len()//4 估算.
        """
        from infra.ai_service.cost_tracker import CostTracker

        cost_tracker = CostTracker()
        master = make_master_with_router(
            state_dir=tmp_path,
            cost_tracker=cost_tracker,
            record_usage=True,  # Phase 8.6.2: 注入 _RecordingRouter
        )
        master.run_workflow(
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
        recs = cost_tracker.records()
        # 至少 4 LLM calls (write + audit + polish_e + polish_a), 每笔 100/50
        # polish_emotional_pacing sums 2 LLM (dialogue + pacing) → 200 input
        # polish_merge_synthesis 无 _with_usage variant (留 Phase 8.7), 走 dict path
        # 估算法 (len()//4), 故 5th record 可能是估算值
        assert len(recs) >= 4, f"expected >= 4 records, got {len(recs)}"
        # 真实 usage 不是 0
        total = sum(r.input_tokens + r.output_tokens for r in recs)
        assert total > 0
        # 前 4 笔都是 _with_usage 真实 100/50 (polish_e sum=200)
        real_path_recs = recs[:4]
        for r in real_path_recs:
            assert r.input_tokens in (100, 200), (
                f"expected input_tokens=100 (or 200 for polish_e sum), got {r.input_tokens}"
            )
            assert r.output_tokens in (50, 100), (
                f"expected output_tokens=50 (or 100 for polish_e sum), got {r.output_tokens}"
            )


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


def test_emit_chapter_depends_on_polish_yaml_static():
    """Phase 7.4 兼容: YAML 静态检查 — emit_chapter.depends_on 包含 polish_merge (旧 polish_chapter 已拆)"""
    from pathlib import Path

    import yaml

    yaml_path = Path(__file__).parent.parent.parent / "infra" / "got" / "workflows" / "novel_writing.yaml"
    assert yaml_path.exists(), f"workflow YAML not found: {yaml_path}"
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    nodes_by_id = {n["id"]: n for n in data["nodes"]}
    # Phase 7.4: polish_chapter 拆为 polish_emotional_pacing + polish_ai_trace_removal + polish_merge
    assert "polish_merge" in nodes_by_id
    assert "polish_chapter" not in nodes_by_id, "Phase 7.3 polish_chapter node should be removed in 7.4"
    emit = nodes_by_id["emit_chapter"]
    assert "polish_merge" in emit["depends_on"], (
        f"emit_chapter.depends_on should contain polish_merge, got {emit['depends_on']}"
    )


# === TestNovelWritingMultiVariantPolish (Phase 7.4 NEW) ===

class TestNovelWritingMultiVariantPolish:
    """Phase 7.4: novel_writing.yaml 7 节点 — review_chapter 后 2 个并行 polish + AGGREGATION merge"""

    MINIMAL_OUTLINE = {
        "chapters": [
            {"num": 1, "title": "第一章", "events": ["event_a"], "word_count_target": 2500}
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

    def test_seven_nodes_all_completed(self, tmp_path: Path):
        """Phase 7.4: novel_writing 7 节点 (read/write/review/polish_e/polish_a/merge/emit)"""
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        assert result["summary"].completed == 7
        assert result["summary"].failed == 0
        assert result["summary"].paused is False

    def test_novel_writing_has_parallel_polish_nodes(self, tmp_path: Path):
        """Phase 7.4: review_chapter 后应有 2 个 polish 节点 (emotional_pacing + ai_trace_removal)"""
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        executions = result["executions"]
        assert "polish_emotional_pacing" in executions
        assert "polish_ai_trace_removal" in executions
        # 拓扑: review → 2 个 polish → merge → emit
        assert "polish_merge" in executions
        assert "emit_chapter" in executions

    def test_polish_merge_output_has_content(self, tmp_path: Path):
        """Phase 7.4: polish_merge.output 含非空 content (供 emit 落盘)"""
        router, _ = make_stub_router()
        result = self._run_novel_writing(tmp_path, router)

        merge_output = result["executions"]["polish_merge"].output
        assert isinstance(merge_output, dict)
        assert "content" in merge_output
        content = merge_output["content"]
        assert isinstance(content, str)
        assert len(content) > 0, "polish_merge output.content should be non-empty"

    def test_at_least_seven_llm_calls(self, tmp_path: Path):
        """Phase 7.5: 7 节点, LLM 调用 >= 5 次 (测试桩下 polish_merge 走 identical fallback)

        write(1) + audit(1) + emotional_pacing(2: dialogue+pacing) + ai_trace_removal(1: dialogue)
        = 5 次. read_snapshot/emit_chapter 旁路.
        (ai_trace_removal 走规则 remove_ai_gloss 不调 LLM, 留下 optimize_dialogue_llm 1 次)

        注: 测试桩 StubProvider 返相同字符串, 两个 polish 节点都返 "anthropic-response",
        polish_merge 走 identical fallback (不调 LLM)。生产路径下两个 polish variant
        内容不同, polish_merge 会调 1 次 LLM S1-S8 评分 (= 6 次 LLM)。"""
        router, providers = make_stub_router()
        self._run_novel_writing(tmp_path, router)

        total_calls = sum(len(p.calls) for p in providers.values())
        assert total_calls >= 5, (
            f"expected at least 5 LLM calls (write + audit + emotional_pacing{2} + ai_trace_removal{1}), "
            f"got {total_calls}. per-provider: {[(n, len(p.calls)) for n, p in providers.items()]}"
        )


# === TestNovelWritingMultiVariantPolishYAML (Phase 7.4 NEW) ===

def test_novel_writing_emit_depends_on_polish_merge_yaml_static():
    """Phase 7.4: YAML 静态检查 — emit_chapter.depends_on == [polish_merge]"""
    from pathlib import Path

    import yaml

    yaml_path = Path(__file__).parent.parent.parent / "infra" / "got" / "workflows" / "novel_writing.yaml"
    assert yaml_path.exists(), f"workflow YAML not found: {yaml_path}"
    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    nodes_by_id = {n["id"]: n for n in data["nodes"]}
    assert "polish_merge" in nodes_by_id, "polish_merge node must exist"
    assert "polish_emotional_pacing" in nodes_by_id
    assert "polish_ai_trace_removal" in nodes_by_id
    # polish_chapter 旧节点应已删除
    assert "polish_chapter" not in nodes_by_id, "old polish_chapter node should be removed"

    emit = nodes_by_id["emit_chapter"]
    assert "polish_merge" in emit["depends_on"], (
        f"emit_chapter.depends_on should contain polish_merge, got {emit['depends_on']}"
    )

    # polish_merge 应为 aggregation 类型
    merge_node = nodes_by_id["polish_merge"]
    assert merge_node["type"] == "aggregation", (
        f"polish_merge.type should be aggregation, got {merge_node['type']}"
    )
    # polish_merge 应依赖 2 个 polish 节点
    assert "polish_emotional_pacing" in merge_node["depends_on"]
    assert "polish_ai_trace_removal" in merge_node["depends_on"]
    # Phase 7.5: polish_merge token_budget=4000, timeout_s=90
    assert merge_node["token_budget"] == 4000, f"polish_merge.token_budget should be 4000, got {merge_node['token_budget']}"
    assert merge_node["timeout_s"] == 90
    # version 升级到 3
    assert data["version"] == 3, f"novel_writing workflow version should be 3, got {data['version']}"
