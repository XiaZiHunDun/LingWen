"""Phase 7.2 PolisherTools LLM-化 — 15 测试

- PolisherTools 继承 AgentBase
- 3 LLM 方法 (optimize_dialogue_llm / adjust_pacing_llm / polish_chapter)
- 韧性契约: LLM 失败降级到规则路径
- 默认 reader_id='A' + 可选切换
- 保留 remove_ai_gloss / apply_style_guide 规则方法 (向后兼容)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import pytest

from infra.agent_system.agents.base import AgentBase
from infra.agent_system.agents.polisher.tools import PolisherTools
from infra.agent_system.master_controller import MasterController


class _StubRouter:
    """极简 StubRouter — 模拟 AIRouter.generate"""

    def __init__(self, response: str = "LLM-stub-output"):
        self.response = response
        self.calls: List[Dict[str, Any]] = []

    def generate(self, prompt: str, **kwargs) -> str:
        self.calls.append({"prompt": prompt, **kwargs})
        return self.response


class TestPolisherLLMInit:
    """PolisherTools 继承 AgentBase + 初始化"""

    def test_inherits_agent_base(self):
        """PolisherTools 继承 AgentBase 获得 LLM 能力"""
        polisher = PolisherTools()
        assert isinstance(polisher, AgentBase)
        assert hasattr(polisher, "chat")
        assert hasattr(polisher, "_fallback_mode")

    def test_no_router_enters_fallback_mode(self):
        """PolisherTools() 无 router → fallback_mode=True"""
        polisher = PolisherTools()
        assert polisher._fallback_mode is True
        assert polisher.is_available is False

    def test_reader_id_default_and_set(self):
        """set_reader/get_current_reader 工作"""
        polisher = PolisherTools()
        assert polisher.get_current_reader() is None
        polisher.set_reader("B")
        assert polisher.get_current_reader() == "B"
        polisher.set_reader("T")
        assert polisher.get_current_reader() == "T"


class TestDialogueLLM:
    """optimize_dialogue_llm — LLM 路径"""

    def test_optimize_dialogue_llm_calls_chat(self, monkeypatch):
        polisher = PolisherTools(router=_StubRouter("dialogue-output"))
        called = {"count": 0, "prompt": None, "system": None, "kwargs": {}}

        def fake_chat(prompt, system, temperature, max_tokens, **kwargs):
            called["count"] += 1
            called["prompt"] = prompt
            called["system"] = system
            called["kwargs"] = {"temperature": temperature, "max_tokens": max_tokens}
            return "LLM 对话优化输出"

        monkeypatch.setattr(polisher, "chat", fake_chat)
        result = polisher.optimize_dialogue_llm("原文对话...", reader_id="A")
        assert called["count"] == 1
        assert "对话" in called["prompt"]
        assert "读者 A" in called["prompt"]
        assert result == "LLM 对话优化输出"

    def test_optimize_dialogue_uses_reader_variant_enhancement(self, monkeypatch):
        """reader_id='B' 触发 _load_variant_enhancement (reader_id 透传)"""
        polisher = PolisherTools(router=_StubRouter("output"))
        captured = {"prompt": None}

        def fake_chat(prompt, system, **kwargs):
            captured["prompt"] = prompt
            return "output"

        monkeypatch.setattr(polisher, "chat", fake_chat)
        polisher.optimize_dialogue_llm("test content", reader_id="B")
        # reader_id='B' 应当出现在 prompt 模板中
        assert "B" in captured["prompt"]

    def test_optimize_dialogue_fallback_returns_placeholder(self):
        """无 router 时返回 fallback string, 不抛错"""
        polisher = PolisherTools()  # 无 router (fallback)
        result = polisher.optimize_dialogue_llm("test content")
        assert isinstance(result, str)


class TestPacingLLM:
    """adjust_pacing_llm — LLM 路径"""

    def test_adjust_pacing_llm_calls_chat(self, monkeypatch):
        polisher = PolisherTools(router=_StubRouter("pacing-output"))
        called = {"count": 0, "kwargs": {}}

        def fake_chat(prompt, system, temperature, max_tokens, **kwargs):
            called["count"] += 1
            called["kwargs"] = {"temperature": temperature, "max_tokens": max_tokens}
            return "LLM 节奏调整输出"

        monkeypatch.setattr(polisher, "chat", fake_chat)
        result = polisher.adjust_pacing_llm("原文...", reader_id="A")
        assert called["count"] == 1
        assert result == "LLM 节奏调整输出"

    def test_adjust_pacing_temperature_is_lower(self, monkeypatch):
        """pacing 温度 0.4 (低于 dialogue 0.5)"""
        polisher = PolisherTools(router=_StubRouter("output"))
        captured = {"temp": None}

        def fake_chat(prompt, system, temperature, max_tokens, **kwargs):
            captured["temp"] = temperature
            return "output"

        monkeypatch.setattr(polisher, "chat", fake_chat)
        polisher.adjust_pacing_llm("test")
        assert captured["temp"] == 0.4


class TestPolishChapterMain:
    """polish_chapter 主入口 — 串联 3 路径, 返回 dict"""

    def test_polish_chapter_chains_three_paths(self):
        polisher = PolisherTools(router=_StubRouter("llm-out"))
        # 替换 LLM 子方法为 stub (避免实际调 chat)
        polisher.optimize_dialogue_llm = lambda content, reader_id=None: content + " [dial]"
        polisher.adjust_pacing_llm = lambda content, reader_id=None: content + " [pace]"

        result = polisher.polish_chapter(chapter_num=1, content="原文首先")

        # 关键断言: 3 路径串联
        assert " [dial]" in result["content"]
        assert " [pace]" in result["content"]
        assert "首先" not in result["content"]  # remove_ai_gloss 规则清理

    def test_polish_chapter_returns_dict_with_required_keys(self):
        polisher = PolisherTools(router=_StubRouter("out"))
        result = polisher.polish_chapter(chapter_num=1, content="test")
        for key in ["content", "reader", "issues", "chapter_num"]:
            assert key in result, f"missing key: {key}"
        assert isinstance(result["issues"], list)
        assert result["chapter_num"] == 1

    def test_polish_chapter_default_reader_is_A(self, monkeypatch):
        polisher = PolisherTools(router=_StubRouter("out"))
        captured = {"dialogue_reader": None, "pacing_reader": None}

        def fake_dialogue(content, reader_id=None):
            captured["dialogue_reader"] = reader_id
            return content

        def fake_pacing(content, reader_id=None):
            captured["pacing_reader"] = reader_id
            return content

        monkeypatch.setattr(polisher, "optimize_dialogue_llm", fake_dialogue)
        monkeypatch.setattr(polisher, "adjust_pacing_llm", fake_pacing)
        result = polisher.polish_chapter(chapter_num=1, content="test")
        assert captured["dialogue_reader"] == "A"
        assert captured["pacing_reader"] == "A"
        assert result["reader"] == "A"

    def test_polish_chapter_llm_failure_falls_back_to_rules(self):
        """韧性契约: 单 LLM 抛错时, content 仍产出, issues 记录"""
        polisher = PolisherTools(router=_StubRouter("out"))

        def boom(*a, **kw):
            raise RuntimeError("simulated LLM failure")

        polisher.optimize_dialogue_llm = boom
        polisher.adjust_pacing_llm = lambda content, reader_id=None: content  # OK

        result = polisher.polish_chapter(chapter_num=1, content="首先...其次...")

        # 关键断言: 不崩溃, content 仍产出
        assert "首先" not in result["content"]
        assert "其次" not in result["content"]
        assert len(result["issues"]) == 1
        assert result["issues"][0]["type"] == "dialogue_llm_fail"
        assert result["reader"] == "A"

    def test_polish_chapter_propagates_to_master_polish_chapter(self):
        """master.polish_chapter 调 polisher.polish_chapter, 返回 str"""
        # MasterController.__new__ 跳过 __init__ (Phase 7.1 同模式)
        master = MasterController.__new__(MasterController)
        master.polisher = PolisherTools(router=_StubRouter("llm-out"))
        master.polisher.optimize_dialogue_llm = lambda c, reader_id=None: c + " [d]"
        master.polisher.adjust_pacing_llm = lambda c, reader_id=None: c + " [p]"

        result = master.polish_chapter("原文首先")

        # 关键断言: master.polish_chapter 返回 str (向后兼容)
        assert isinstance(result, str)
        assert " [d]" in result
        assert " [p]" in result
        assert "首先" not in result

    def test_polish_chapter_with_all_llm_paths_failing_still_returns_content(self):
        """韧性契约扩展: 两 LLM 全抛错, content 仍产出 (全降级到规则)"""
        polisher = PolisherTools(router=_StubRouter("out"))

        def boom(*a, **kw):
            raise RuntimeError("boom")

        polisher.optimize_dialogue_llm = boom
        polisher.adjust_pacing_llm = boom

        result = polisher.polish_chapter(chapter_num=1, content="首先...其次...最后...")

        assert "首先" not in result["content"]
        assert "其次" not in result["content"]
        assert "最后" not in result["content"]
        assert len(result["issues"]) == 2
        assert {i["type"] for i in result["issues"]} == {"dialogue_llm_fail", "pacing_llm_fail"}


class TestRulePaths:
    """规则方法保留 — 不破坏 test_agent_tools.py 现有测试"""

    def test_remove_ai_gloss_still_works(self):
        """规则路径不破坏, fallback 模式可用"""
        polisher = PolisherTools()  # 无 router (fallback)
        content = "首先，我们需要冷静分析。其次，制定计划。最后，执行。"
        result = polisher.remove_ai_gloss(content)
        assert "首先" not in result
        assert "其次" not in result
        assert "最后" not in result
