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

    Phase 8.7: 同时 stub chat_with_usage() (走 polisher.chat() 估算 / 跟 Phase 8.6.1
    硬编码 {input_tokens: 100, output_tokens: 50} 一致) 供 *_with_usage 变体使用.
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

        def chat_with_usage(self, *, prompt: str, system: str, temperature: float, max_tokens: int):
            """Phase 8.7: 跟 chat() 行为一致, 但额外返硬编码 usage (跟 Phase 8.6.1 一致)."""
            self.calls.append({"prompt": prompt, "system": system, "temperature": temperature, "max_tokens": max_tokens, "via": "chat_with_usage"})
            if chat_raises:
                raise RuntimeError("simulated LLM failure")
            return _FakeLLMResponse(chat_response), {"input_tokens": 100, "output_tokens": 50}

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


# ==================== Phase 8.7: polish_merge_synthesis_with_usage ====================


class TestPolishMergeWithUsage:
    """Phase 8.7: MasterController.polish_merge_synthesis_with_usage 返 (dict, usage) tuple.

    模式: 跟其他 5 MC variants (write_chapter/audit_chapter/polish_chapter/
    polish_emotional_pacing/polish_ai_trace_removal) 一致 — 委托 _impl(record_usage=True),
    旧 method 走 record_usage=False 保 baseline.
    """

    def test_returns_tuple_with_real_usage_on_llm_success(self) -> None:
        """LLM success path: 返 (scored_dict, {input_tokens: 100, output_tokens: 50})."""
        # A 8 分, B 5 分 → winner=A
        scores_a = {f"S{i}": 8 for i in range(1, 9)}
        scores_b = {f"S{i}": 5 for i in range(1, 9)}
        chat_response = {
            "scores_emotional_pacing": scores_a,
            "scores_ai_trace_removal": scores_b,
            "reason": "A 整体质量更高",
        }
        master = _make_master(chat_response=chat_response)
        result, usage = master.polish_merge_synthesis_with_usage(
            content_a="A 章节内容" * 20,
            content_b="B 章节内容" * 20,
            labels=("emotional_pacing", "ai_trace_removal"),
        )
        # 1. result 是 dict (scored)
        assert isinstance(result, dict)
        assert "winner" in result
        assert "scores_a" in result
        assert "scores_b" in result
        assert result["winner"] == "emotional_pacing"
        # 2. usage 是 真实 dict (硬编码 _StubPolisher 走 chat_with_usage)
        assert usage == {"input_tokens": 100, "output_tokens": 50}
        # 3. 确认走的是 chat_with_usage (不是 chat)
        assert master.polisher.calls[-1].get("via") == "chat_with_usage"

    def test_returns_zero_usage_on_llm_failure(self) -> None:
        """LLM fail path: 返 (fallback_dict, zero_usage), 韧性契约不设 _error."""
        master = _make_master(chat_raises=True)
        result, usage = master.polish_merge_synthesis_with_usage(
            content_a="A 内容" * 20,
            content_b="B 内容" * 20,
        )
        assert isinstance(result, dict)
        # 韧性契约: 无 _error (跟 8.6.2 _impl_audit_chapter 同 fix)
        assert "_error" not in result
        assert result.get("fallback") == "llm_fail"
        # usage 是 0 (LLM fail 不录)
        assert usage == {"input_tokens": 0, "output_tokens": 0}

    def test_returns_zero_usage_on_empty_content(self) -> None:
        """Empty content path: 不调 LLM, 返 (empty_fallback, zero_usage)."""
        master = _make_master(chat_response="{}")
        result, usage = master.polish_merge_synthesis_with_usage(
            content_a="",  # empty
            content_b="B 内容" * 20,
        )
        assert isinstance(result, dict)
        assert result.get("fallback") == "empty_content"
        assert usage == {"input_tokens": 0, "output_tokens": 0}
        # 不调 LLM
        assert master.polisher.calls == []

    def test_returns_zero_usage_on_identical_content(self) -> None:
        """Identical content path: 不调 LLM, 返 (identical_fallback, zero_usage)."""
        master = _make_master(chat_response="{}")
        result, usage = master.polish_merge_synthesis_with_usage(
            content_a="相同内容" * 10,
            content_b="相同内容" * 10,
        )
        assert isinstance(result, dict)
        assert result.get("fallback") == "identical"
        assert usage == {"input_tokens": 0, "output_tokens": 0}
        # 不调 LLM
        assert master.polisher.calls == []


# ==================== Phase 8.1: Static LLM Robustness ====================


class TestScoreCoercion:
    """Phase 8.1: _coerce_score helper — 真实 LLM 输出类型安全 (int/float/str/None/NaN/越界)."""

    def test_int_value_unchanged(self):
        from infra.agent_system.master_controller import _coerce_score
        assert _coerce_score(7) == 7
        assert _coerce_score(0) == 0
        assert _coerce_score(10) == 10

    def test_float_value_rounds_not_truncates(self):
        from infra.agent_system.master_controller import _coerce_score
        # Python banker's rounding: round(7.5)=8, round(0.5)=0
        assert _coerce_score(7.5) == 8  # 不再 int 截断 7
        assert _coerce_score(7.4) == 7
        assert _coerce_score(0.5) == 0  # banker's rounding
        assert _coerce_score(1.5) == 2  # banker's rounding

    def test_str_value_coerces(self):
        from infra.agent_system.master_controller import _coerce_score
        assert _coerce_score("7") == 7
        assert _coerce_score("7.5") == 8
        assert _coerce_score("0") == 0
        assert _coerce_score("10") == 10

    def test_out_of_range_clamps(self):
        from infra.agent_system.master_controller import _coerce_score
        assert _coerce_score(15) == 10  # clamp high
        assert _coerce_score(-3) == 0  # clamp low
        assert _coerce_score(100) == 10
        assert _coerce_score("99") == 10
        assert _coerce_score("-5") == 0

    def test_invalid_value_defaults_to_5(self):
        from infra.agent_system.master_controller import _coerce_score
        assert _coerce_score(None) == 5
        assert _coerce_score("7/10") == 5  # str with slash
        assert _coerce_score("not a number") == 5
        assert _coerce_score(float("nan")) == 5  # NaN
        assert _coerce_score([]) == 5  # 列表


class TestMissingKeyDefault:
    """Phase 8.1: HAIKU 漏 S5 不让 7 维都丢 — .get(k, 5) 默认 5."""

    def test_missing_s5_uses_default_other_dims_preserved(self):
        """scores_A 漏 S5 → scores_a["S5"]=5, 其他维保留 LLM 给的"""
        chat_response = {
            "scores_A": {"S1": 8, "S2": 7, "S3": 8, "S4": 7, "S6": 7, "S7": 8, "S8": 7},  # 漏 S5
            "scores_B": {"S1": 5, "S2": 5, "S3": 5, "S4": 5, "S5": 5, "S6": 5, "S7": 5, "S8": 5},
            "reason": "A 漏 S5, 默认 5",
        }
        master = _make_master(chat_response=chat_response)
        result = master.polish_merge_synthesis(
            content_a="A content",
            content_b="B content",
            labels=("A", "B"),
        )

        # 走 LLM 路径 (没走 fallback)
        assert "fallback" not in result
        # S5 默认 5
        assert result["scores_a"]["S5"] == 5
        # 其他维保留
        assert result["scores_a"]["S1"] == 8
        assert result["scores_a"]["S8"] == 7
        # A 平均: (8+7+8+7+5+7+8+7)/8 = 57/8 = 7.125
        assert result["scores_total_a"] == pytest.approx(7.125)

    def test_missing_multiple_keys_all_default(self):
        """scores_A 漏 S5+S7 → 这两维都默认 5"""
        chat_response = {
            "scores_A": {"S1": 8, "S2": 7, "S3": 8, "S4": 7, "S6": 7, "S8": 7},  # 漏 S5+S7
            "scores_B": {"S1": 5, "S2": 5, "S3": 5, "S4": 5, "S5": 5, "S6": 5, "S7": 5, "S8": 5},
            "reason": "A 漏多维",
        }
        master = _make_master(chat_response=chat_response)
        result = master.polish_merge_synthesis(
            content_a="A content",
            content_b="B content",
            labels=("A", "B"),
        )

        assert "fallback" not in result  # 仍走 LLM
        assert result["scores_a"]["S5"] == 5
        assert result["scores_a"]["S7"] == 5

    def test_empty_scores_dict_all_default_to_5(self):
        """scores_A = {} → 8 维全默认 5, total=5.0, 仍走 LLM"""
        chat_response = {
            "scores_A": {},
            "scores_B": {"S1": 5, "S2": 5, "S3": 5, "S4": 5, "S5": 5, "S6": 5, "S7": 5, "S8": 5},
            "reason": "A 完全没分",
        }
        master = _make_master(chat_response=chat_response)
        result = master.polish_merge_synthesis(
            content_a="A content",
            content_b="B content",
            labels=("A", "B"),
        )

        assert "fallback" not in result  # 仍走 LLM
        assert all(v == 5 for v in result["scores_a"].values())
        assert result["scores_total_a"] == 5.0


class TestJsonParseFailure:
    """Phase 8.1: parse_response 失败显式检测, 新增 fallback='json_parse_failed'."""

    def _make_master_with_real_parse(self, chat_response: str):
        """构造 stub 用真 base.parse_response (base.py:178-181 兜底返 {raw})."""
        from infra.agent_system import master_controller as mc_mod
        from infra.agent_system.agents.base import AgentBase

        class _StubPolisher(AgentBase):
            def __init__(self) -> None:
                self.calls: list[dict] = []
                # 不调 super().__init__ (避免 router) — router=None 走 fallback 模式
                AgentBase.__init__(self)

            def chat(self, *, prompt: str, system: str, temperature: float, max_tokens: int):
                self.calls.append({"prompt": prompt})
                return chat_response  # 返 str (不 json.dumps)

            def parse_response(self, response, *, format_type: str = "json"):
                # 调真 AgentBase.parse_response (base.py:178-181)
                return AgentBase.parse_response(self, response, format_type=format_type)

        master = mc_mod.MasterController.__new__(mc_mod.MasterController)
        master.polisher = _StubPolisher()
        return master

    def test_non_json_response_returns_json_parse_failed_fallback(self):
        """chat 返 '我无法评分' (非 JSON) → base.parse_response 兜底 {raw} → fallback='json_parse_failed'"""
        master = self._make_master_with_real_parse(chat_response="我无法评分, 请重新提问")
        result = master.polish_merge_synthesis(
            content_a="A content",
            content_b="B content",
            labels=("A", "B"),
        )

        assert result["fallback"] == "json_parse_failed"
        assert result["scores_a"] == {}
        assert result["scores_b"] == {}
        # winner = max(len) 兜底
        assert result["winner"] == "A"  # len 相等, ties to first
        assert result["scores_total_a"] == 0.0

    def test_missing_scores_field_returns_json_parse_failed(self):
        """chat 返 valid JSON 但缺 scores_X 字段 → fallback='json_parse_failed'"""
        chat_response = '{"reason": "tie, no scores"}'  # valid JSON, 但无 scores_A/B
        master = self._make_master_with_real_parse(chat_response=chat_response)
        result = master.polish_merge_synthesis(
            content_a="A content",
            content_b="B content",
            labels=("A", "B"),
        )

        assert result["fallback"] == "json_parse_failed"
        assert result["scores_a"] == {}

    def test_scores_field_is_int_not_dict_returns_json_parse_failed(self):
        """chat 返 valid JSON, scores_A 是 int 而非 dict → fallback='json_parse_failed'"""
        chat_response = '{"scores_A": 7, "scores_B": 5, "reason": "wrong shape"}'
        master = self._make_master_with_real_parse(chat_response=chat_response)
        result = master.polish_merge_synthesis(
            content_a="A content",
            content_b="B content",
            labels=("A", "B"),
        )

        assert result["fallback"] == "json_parse_failed"
        assert result["scores_a"] == {}

    def test_valid_json_path_no_fallback_regression(self):
        """regression: valid JSON 仍走 LLM 路径 (no fallback) — 跟 TestPolishMergeSynthesis 5 测试一致"""
        chat_response = (
            '{"scores_A": {"S1": 8, "S2": 7, "S3": 8, "S4": 7, "S5": 8, "S6": 7, "S7": 8, "S8": 7},'
            '"scores_B": {"S1": 5, "S2": 5, "S3": 5, "S4": 5, "S5": 5, "S6": 5, "S7": 5, "S8": 5},'
            '"reason": "A better"}'
        )
        master = self._make_master_with_real_parse(chat_response=chat_response)
        result = master.polish_merge_synthesis(
            content_a="A content",
            content_b="B content",
            labels=("A", "B"),
        )

        assert "fallback" not in result  # 走 LLM 路径
        assert result["winner"] == "A"
        assert result["scores_a"]["S1"] == 8


class TestLabelSanitization:
    """Phase 8.1: _safe_label helper + prompt 双轨 (header 原始 / JSON key sanitized)."""

    def test_safe_label_helper_basic(self):
        from infra.agent_system.master_controller import _safe_label
        assert _safe_label("polish_emotional_pacing") == "polish_emotional_pacing"  # 已安全
        assert _safe_label("polish.emotional") == "polish_emotional"  # . → _
        assert _safe_label("polish-ai-trace") == "polish_ai_trace"  # - → _
        assert _safe_label("a b c") == "a_b_c"  # 空格 → _
        assert _safe_label("中文标签") == "____"  # 4 个中文字符 → 4 个 _ (2-byte chars 都非 [a-zA-Z0-9_])
        assert _safe_label("mix.123-X_Y") == "mix_123_X_Y"  # 混合

    def test_prompt_uses_sanitized_in_json_key_original_in_header(self):
        """build_merge_synthesis_prompt: ## Variant 用原始, JSON key 用 sanitized"""
        from infra.agent_system.agents.polisher.prompts import build_merge_synthesis_prompt

        prompt = build_merge_synthesis_prompt(
            content_a="A content",
            content_b="B content",
            labels=("polish.emotional", "polish-ai-trace"),
        )

        # ## Variant header 用原始 (人类可读)
        assert "## Variant polish.emotional" in prompt
        assert "## Variant polish-ai-trace" in prompt
        # JSON key 用 sanitized
        assert '"scores_polish_emotional":' in prompt
        assert '"scores_polish_ai_trace":' in prompt
        # reason 也用原始 (curly braces 被 f-string 消费, 检查 raw label 在 reason 段)
        assert "选 polish.emotional" in prompt

    def test_polish_merge_synthesis_with_weird_labels_winner_uses_original(self):
        """labels 含特殊字符: winner 字段仍用原始 label (dashboard 显示), scores 从 sanitized key 读"""
        # LLM 看到 "polish.emotional" header, 输出 "scores_polish_emotional" sanitized key
        chat_response = {
            "scores_polish_emotional": {"S1": 8, "S2": 7, "S3": 8, "S4": 7, "S5": 8, "S6": 7, "S7": 8, "S8": 7},
            "scores_polish_ai_trace": {"S1": 5, "S2": 5, "S3": 5, "S4": 5, "S5": 5, "S6": 5, "S7": 5, "S8": 5},
            "reason": "emotional wins",
        }
        master = _make_master(chat_response=chat_response)
        result = master.polish_merge_synthesis(
            content_a="emotional variant",
            content_b="ai trace variant",
            labels=("polish.emotional", "polish-ai-trace"),
        )

        # winner 用原始
        assert result["winner"] == "polish.emotional"
        # scores 从 sanitized key 读
        assert result["scores_a"]["S1"] == 8  # scores_a 来自 sanitized "polish_emotional"
        assert result["scores_b"]["S8"] == 5  # scores_b 来自 sanitized "polish_ai_trace"
        # _labels 也用原始 (Phase 7.6 透传)
        assert result["_labels"] == ["polish.emotional", "polish-ai-trace"]


class TestTruncation:
    """Phase 8.1: build_merge_synthesis_prompt truncation 3000→6000 chars."""

    def test_8000_chars_truncated_to_6000(self):
        """8000 chars content → prompt 只含前 6000 chars"""
        from infra.agent_system.agents.polisher.prompts import build_merge_synthesis_prompt

        long_content = "X" * 8000
        prompt = build_merge_synthesis_prompt(
            content_a=long_content,
            content_b="B content",
            labels=("A", "B"),
        )

        # prompt 应含前 6000 X
        assert "X" * 6000 in prompt
        # 但不含 "X" * 6001 (第 6001 个被截)
        assert "X" * 6001 not in prompt

    def test_short_content_unchanged(self):
        """1000 chars content → no truncation, 完整包含"""
        from infra.agent_system.agents.polisher.prompts import build_merge_synthesis_prompt

        short_content = "Y" * 1000
        prompt = build_merge_synthesis_prompt(
            content_a=short_content,
            content_b="B content",
            labels=("A", "B"),
        )

        # 完整 1000 Y 应在
        assert "Y" * 1000 in prompt
        # 不应被任何 Y*1001 截
        assert "Y" * 1001 not in prompt  # 验证 short 路径
