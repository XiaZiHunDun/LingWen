"""Phase 8.6.2: MasterController 5 *_with_usage variants + dual-path backward compat.

复用 Phase 8.6.1 _UsageRecordingProvider + _RecordingRouter stubs
(在 tests/agent_system/test_agent_with_usage.py 定义).

测试目标:
- 5 variants 返 (result, usage) tuple, usage 含 input_tokens/output_tokens
- 旧 method 签名 0 改, 返 dict / str (单 path)
- audit 异常 → 旧 try/except 兜底, usage 0
- chat_with_usage sanity 防回归
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from infra.agent_system.master_controller import MasterController
from tests.agent_system._e2e_helpers import make_master_with_router

# Reuse Phase 8.6.1 stubs (tests/agent_system/test_agent_with_usage.py)
from tests.agent_system.test_agent_with_usage import (
    _RecordingRouter,
    _UsageRecordingProvider,
)


class TestMasterControllerWithUsage:
    """Phase 8.6.2: 5 MC *_with_usage variants + backward compat 双路径."""

    def test_write_chapter_with_usage_returns_tuple(self, tmp_path: Path) -> None:
        """Variant 1: write_chapter_with_usage 返 (result, usage) tuple."""
        master = make_master_with_router(
            state_dir=tmp_path,
            router=None,
            record_usage=True,
        )
        # outline 用 num key (匹配 outline_schema.get_chapter_outline 的 ch.get("num"))
        result, usage = master.write_chapter_with_usage(
            chapter_num=1,
            outline={
                "title": "test chapter",
                "chapters": [
                    {"num": 1, "title": "c1", "summary": "s", "key_events": []},
                ],
            },
            characters=[],
            memory_context={},
            style_guide={},
            use_llm=True,
        )
        assert isinstance(result, dict)
        assert isinstance(usage, dict)
        assert "input_tokens" in usage
        assert "output_tokens" in usage
        assert "content" in result

    def test_audit_chapter_with_usage_returns_tuple(self, tmp_path: Path) -> None:
        """Variant 2: audit_chapter_with_usage 返 (result, usage) tuple."""
        master = make_master_with_router(
            state_dir=tmp_path,
            router=None,
            record_usage=True,
        )
        result, usage = master.audit_chapter_with_usage(
            chapter_num=1,
            content="test content",
            characters=[],
            timeline=[],
            use_llm=True,
        )
        assert isinstance(result, dict)
        assert isinstance(usage, dict)
        assert "input_tokens" in usage
        assert "output_tokens" in usage

    def test_polish_chapter_with_usage_sums_both_llms(self, tmp_path: Path) -> None:
        """Variant 3: polish_chapter_with_usage = 2 LLM (dialogue + pacing) sum."""
        master = make_master_with_router(
            state_dir=tmp_path,
            router=None,
            record_usage=True,
        )
        result, usage = master.polish_chapter_with_usage(
            chapter_num=1,
            content="text " * 50,
            style_guide=None,
        )
        # 2 LLM sum: each 100/50, total 200/100
        assert isinstance(result, str)
        assert usage["input_tokens"] == 200
        assert usage["output_tokens"] == 100

    def test_polish_emotional_pacing_with_usage_sums_sub_llms(self, tmp_path: Path) -> None:
        """Variant 4: polish_emotional_pacing_with_usage = 2 LLM (dialogue + pacing) sum."""
        master = make_master_with_router(
            state_dir=tmp_path,
            router=None,
            record_usage=True,
        )
        result, usage = master.polish_emotional_pacing_with_usage(
            chapter_num=1,
            content="text " * 50,
        )
        assert isinstance(result, str)
        assert usage["input_tokens"] == 200
        assert usage["output_tokens"] == 100

    def test_polish_ai_trace_removal_with_usage_includes_llm(self, tmp_path: Path) -> None:
        """Variant 5: polish_ai_trace_removal_with_usage = 1 LLM + 1 rule, usage only LLM."""
        master = make_master_with_router(
            state_dir=tmp_path,
            router=None,
            record_usage=True,
        )
        result, usage = master.polish_ai_trace_removal_with_usage(
            chapter_num=1,
            content="text " * 50,
        )
        assert isinstance(result, str)
        # 1 LLM call: 100/50 (rule remove_ai_gloss 0 token)
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50

    def test_old_methods_still_return_dict_only(self, tmp_path: Path) -> None:
        """Backward compat: 旧 5 method 走 _impl(record_usage=False) 返 dict / str (单 path)."""
        # Use stub router (Phase 7.1 e2e 模式) — record_usage=False 保旧 path
        from tests.agent_system._e2e_helpers import make_stub_router

        router, _providers = make_stub_router()
        master = make_master_with_router(
            state_dir=tmp_path,
            router=router,
            record_usage=False,
        )
        # write_chapter 返 dict (outline 必须有 title + num key 匹配 outline_schema)
        write_result = master.write_chapter(
            chapter_num=1,
            outline={
                "title": "test chapter",
                "chapters": [
                    {"num": 1, "title": "c1", "summary": "s", "key_events": []},
                ],
            },
            characters=[],
            memory_context={},
            style_guide={},
            use_llm=True,
        )
        assert isinstance(write_result, dict)
        # audit_chapter 返 dict
        audit_result = master.audit_chapter(
            chapter_num=1,
            content="text",
            characters=[],
            timeline=[],
            use_llm=True,
        )
        assert isinstance(audit_result, dict)
        # 3 polish methods 返 str
        assert isinstance(master.polish_chapter("text"), str)
        assert isinstance(master.polish_emotional_pacing("text"), str)
        assert isinstance(master.polish_ai_trace_removal("text"), str)

    def test_audit_with_usage_propagates_exception(self, tmp_path: Path, monkeypatch) -> None:
        """韧性契约: audit LLM 抛错 → try/except 兜底返正常 audit report, usage 0.

        跟 record_usage=False 路径语义一致 — audit 失败非致命, 规则检查结果保留,
        workflow 不中断 (跟 test_audit_chapter_failure_does_not_crash_workflow 一致).
        """
        master = make_master_with_router(
            state_dir=tmp_path,
            router=None,
            record_usage=True,
        )

        def raise_exc(**kwargs):
            raise RuntimeError("LLM 502")

        # Stub audit_chapter_with_usage 抛错 — 模拟 LLM 失败
        monkeypatch.setattr(master.auditor, "audit_chapter_with_usage", raise_exc)

        result, usage = master.audit_chapter_with_usage(
            chapter_num=1,
            content="text",
            characters=[],
            timeline=[],
        )
        # 韧性契约: 返正常 audit report (无 _error, 避免 AgentComputeFn fail=True)
        assert isinstance(result, dict)
        assert "_error" not in result  # 跟 record_usage=False 路径一致
        assert "chapter" in result  # generate_audit_report 用 "chapter" key
        # usage 是 0 (LLM 失败不录)
        assert usage == {"input_tokens": 0, "output_tokens": 0}

    def test_chat_with_usage_unaffected(self) -> None:
        """Phase 8.6 已就位 sanity — 防回归."""
        # MasterController.chat_with_usage 接受 scenario + prompt
        sig = inspect.signature(MasterController.chat_with_usage)
        assert "scenario" in sig.parameters
        assert "prompt" in sig.parameters
        # Returns (str, dict[str, int]) tuple
        assert sig.return_annotation == tuple[str, dict[str, int]]
