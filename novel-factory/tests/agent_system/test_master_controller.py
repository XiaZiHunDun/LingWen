"""MasterController unit tests — Phase 7.5 S1-S8 weighted scoring for polish_merge

测试 polish_merge_synthesis:
- LLM 评分: winner = 高总分者
- 平分: 选 first (>= ties)
- 空 content: 走 len fallback
- identical content: 走 fallback="identical"
- LLM 失败: 走 len fallback, reason="llm_fail"
"""
from __future__ import annotations

import json
from typing import Any, Optional

import pytest


class _FakeLLMResponse:
    """模拟 polisher.chat() 返的字符串 (json)"""
    def __init__(self, payload: dict) -> None:
        self._payload = payload
    def __str__(self) -> str:
        return json.dumps(self._payload, ensure_ascii=False)


def _make_master(chat_response: Optional[Any] = None, chat_raises: bool = False):
    """构造 MasterController.__new__ stub, 注入 polisher.chat() 行为.

    走 __new__ 绕过 __init__ (避免 build_router 等重操作),只塞 self.polisher
    即可 — polish_merge_synthesis 只读 self.polisher.chat + parse_response.
    """
    from infra.agent_system import master_controller as mc_mod

    class _StubPolisher:
        def __init__(self) -> None:
            self.calls: list[dict] = []

        def chat(self, *, prompt: str, system: str, temperature: float, max_tokens: int):
            self.calls.append({"prompt": prompt, "system": system, "temperature": temperature, "max_tokens": max_tokens})
            if chat_raises:
                raise RuntimeError("simulated LLM failure")
            return _FakeLLMResponse(chat_response)

        def parse_response(self, response: Any, *, format_type: str = "json"):
            if format_type != "json":
                raise ValueError(f"unsupported format_type: {format_type}")
            return json.loads(str(response))

    master = mc_mod.MasterController.__new__(mc_mod.MasterController)
    master.polisher = _StubPolisher()
    return master


class TestPolishMergeSynthesis:
    """Phase 7.5: MasterController.polish_merge_synthesis — S1-S8 8 维加权评分"""

    def test_returns_winner_with_higher_total_score(self):
        """A 平均 8 分, B 平均 5 分 → winner=A, scores_a/b 全填, total_a > total_b"""
        chat_response = {
            "scores_A": {"S1": 8, "S2": 8, "S3": 8, "S4": 8, "S5": 8, "S6": 8, "S7": 8, "S8": 8},
            "scores_B": {"S1": 5, "S2": 5, "S3": 5, "S4": 5, "S5": 5, "S6": 5, "S7": 5, "S8": 5},
            "reason": "A 整体质量更高",
        }
        master = _make_master(chat_response=chat_response)
        result = master.polish_merge_synthesis(
            content_a="A variant content here" * 5,
            content_b="B variant content here" * 3,
            labels=("A", "B"),
        )

        assert result["winner"] == "A"
        assert result["content"] == "A variant content here" * 5
        assert result["scores_total_a"] == 8.0
        assert result["scores_total_b"] == 5.0
        assert result["scores_delta"] == pytest.approx(3.0)
        assert result["scores_a"]["S1"] == 8
        assert result["scores_b"]["S8"] == 5
        assert "fallback" not in result  # 走 LLM 路径不带 fallback

    def test_equal_scores_winner_breaks_tie_to_first(self):
        """A=B=8.0 → winner=labels[0] (>= ties break to first)"""
        chat_response = {
            "scores_emotional_pacing": {"S1": 8, "S2": 8, "S3": 8, "S4": 8, "S5": 8, "S6": 8, "S7": 8, "S8": 8},
            "scores_ai_trace_removal": {"S1": 8, "S2": 8, "S3": 8, "S4": 8, "S5": 8, "S6": 8, "S7": 8, "S8": 8},
            "reason": "tie",
        }
        master = _make_master(chat_response=chat_response)
        result = master.polish_merge_synthesis(
            content_a="variant A",
            content_b="variant B",
            labels=("emotional_pacing", "ai_trace_removal"),
        )

        assert result["winner"] == "emotional_pacing"  # >= ties to first
        assert result["scores_total_a"] == result["scores_total_b"] == 8.0
        assert result["scores_delta"] == 0.0

    def test_empty_content_returns_len_fallback(self):
        """A="" → len_fallback, winner=labels[1] (B)"""
        master = _make_master(chat_response={})  # 不应被调
        result = master.polish_merge_synthesis(
            content_a="",
            content_b="non-empty B content",
            labels=("A", "B"),
        )

        assert result["fallback"] == "empty_content"
        assert result["winner"] == "B"
        assert result["content"] == "non-empty B content"
        assert result["scores_a"] == {}
        assert result["scores_b"] == {}
        # LLM 不应被调 (empty 直接 fallback)
        assert master.polisher.calls == []

    def test_identical_content_returns_first_with_fallback_identical(self):
        """A==B → fallback="identical", winner=labels[0], scores 0.0"""
        master = _make_master(chat_response={})  # 不应被调
        same = "identical content here"
        result = master.polish_merge_synthesis(
            content_a=same,
            content_b=same,
            labels=("alpha", "beta"),
        )

        assert result["fallback"] == "identical"
        assert result["winner"] == "alpha"
        assert result["content"] == same
        assert result["scores_total_a"] == 0.0
        assert result["scores_total_b"] == 0.0
        assert result["scores_delta"] == 0.0
        assert master.polisher.calls == []

    def test_llm_failure_returns_len_fallback_with_reason(self):
        """LLM 抛错 → fallback="llm_fail", winner=len 较长者"""
        master = _make_master(chat_raises=True)
        result = master.polish_merge_synthesis(
            content_a="short",
            content_b="this is a much longer content version",
            labels=("A", "B"),
        )

        assert result["fallback"] == "llm_fail"
        # max(len) → B (len 36 > 5)
        assert result["winner"] == "B"
        assert result["content"] == "this is a much longer content version"
        assert result["scores_a"] == {}
        assert result["scores_b"] == {}
        # LLM 调过 1 次 (然后失败)
        assert len(master.polisher.calls) == 1
