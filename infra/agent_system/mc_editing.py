"""MasterController 润色相关 Mixin

Phase 15.0 P3-SPLIT: 从 master_controller.py 拆分的润色相关方法。
"""
import logging
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

_S1_S8_KEYS = ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8")


class EditingMixin:
    """润色相关方法"""

    def chat_with_usage(self, scenario: str, prompt: str, **kwargs):
        """Phase 8.6.1: 通用 chat + usage — 走 router (HAIKU tier)."""
        try:
            if hasattr(self._router, "generate_with_usage"):
                return self._router.generate_with_usage(scenario, prompt, **kwargs)
            text = self._router.generate(prompt=prompt, **kwargs)
            return text, {
                "input_tokens": len(prompt) // 4,
                "output_tokens": len(text) // 4,
            }
        except Exception as e:
            logger.error("chat_with_usage failed: %s", e)
            raise

    def polish_chapter(self, content: str) -> str:
        """润色章节"""
        result = self._impl_polish_chapter(
            chapter_num=0, content=content, style_guide=None, record_usage=False,
        )
        return result["content"]

    def polish_chapter_with_usage(
        self, chapter_num: int, content: str, style_guide: Optional[Dict] = None,
    ):
        """润色章节 variant — 真实 usage."""
        result, usage = self._impl_polish_chapter(
            chapter_num, content, style_guide, record_usage=True,
        )
        return result["content"], usage

    def _impl_polish_chapter(
        self, chapter_num: int, content: str, style_guide: Optional[Dict], record_usage: bool,
    ):
        if record_usage:
            return self.polisher.polish_chapter_with_usage(chapter_num, content, style_guide)
        return self.polisher.polish_chapter(chapter_num, content, style_guide)

    def polish_emotional_pacing(self, content: str) -> str:
        """情绪节奏 variant"""
        result = self._impl_polish_emotional_pacing(
            chapter_num=0, content=content, record_usage=False,
        )
        return result

    def polish_emotional_pacing_with_usage(
        self, chapter_num: int, content: str,
    ):
        """情绪节奏 variant — 真实 usage."""
        return self._impl_polish_emotional_pacing(
            chapter_num, content, record_usage=True,
        )

    def _impl_polish_emotional_pacing(
        self, chapter_num: int, content: str, record_usage: bool,
    ):
        polished = content
        usage_total = {"input_tokens": 0, "output_tokens": 0}
        try:
            if record_usage:
                r1, u1 = self.polisher.optimize_dialogue_llm_with_usage(polished)
                usage_total["input_tokens"] += u1["input_tokens"]
                usage_total["output_tokens"] += u1["output_tokens"]
            else:
                r1 = self.polisher.optimize_dialogue_llm(polished)
        except Exception as e:
            logger.warning("polish_emotional_pacing: dialogue_llm failed: %s", e)
            r1 = polished
        try:
            if record_usage:
                r2, u2 = self.polisher.adjust_pacing_llm_with_usage(r1)
                usage_total["input_tokens"] += u2["input_tokens"]
                usage_total["output_tokens"] += u2["output_tokens"]
            else:
                r2 = self.polisher.adjust_pacing_llm(r1)
        except Exception as e:
            logger.warning("polish_emotional_pacing: pacing_llm failed: %s", e)
            r2 = r1
        if record_usage:
            return r2, usage_total
        return r2

    def polish_ai_trace_removal(self, content: str) -> str:
        """AI 痕迹 variant"""
        result = self._impl_polish_ai_trace_removal(
            chapter_num=0, content=content, record_usage=False,
        )
        return result

    def polish_ai_trace_removal_with_usage(
        self, chapter_num: int, content: str,
    ):
        """AI 痕迹 variant — 真实 usage."""
        return self._impl_polish_ai_trace_removal(
            chapter_num, content, record_usage=True,
        )

    def _impl_polish_ai_trace_removal(
        self, chapter_num: int, content: str, record_usage: bool,
    ):
        cleaned = self.polisher.remove_ai_gloss(content)
        usage_total = {"input_tokens": 0, "output_tokens": 0}
        try:
            if record_usage:
                r, u = self.polisher.optimize_dialogue_llm_with_usage(cleaned)
                usage_total["input_tokens"] += u["input_tokens"]
                usage_total["output_tokens"] += u["output_tokens"]
            else:
                r = self.polisher.optimize_dialogue_llm(cleaned)
        except Exception as e:
            logger.warning("polish_ai_trace_removal: dialogue_llm failed: %s", e)
            r = cleaned
        if record_usage:
            return r, usage_total
        return r

    def polish_merge_synthesis(
        self,
        content_a: str,
        content_b: str,
        *,
        labels: Tuple[str, str] = ("A", "B"),
    ) -> Dict[str, Any]:
        """LLM S1-S8 8 维加权评分, 选高者."""
        result = self._impl_polish_merge_synthesis(
            content_a, content_b, labels=labels, record_usage=False,
        )
        return result

    def polish_merge_synthesis_with_usage(
        self,
        content_a: str,
        content_b: str,
        *,
        labels: Tuple[str, str] = ("A", "B"),
    ):
        """polish_merge_synthesis variant — 真实 usage."""
        return self._impl_polish_merge_synthesis(
            content_a, content_b, labels=labels, record_usage=True,
        )

    def _impl_polish_merge_synthesis(
        self,
        content_a: str,
        content_b: str,
        *,
        labels: Tuple[str, str],
        record_usage: bool,
    ):
        from mc_utils import _coerce_score, _safe_label

        try:
            system_prompt = (
                "你是资深小说编辑。请对以下两段文字进行8维度评分，"
                "每个维度1-10分。只返回JSON，不要其他内容。"
            )
            user_prompt = f"""
文本A ({labels[0]}):
{content_a}

文本B ({labels[1]}):
{content_b}

请对两段文字进行以下维度评分(1-10分):
S1: 情节连贯性
S2: 人物塑造
S3: 情感表达
S4: 语言风格
S5: 节奏把控
S6: 悬念设置
S7: 细节描写
S8: 整体感染力

返回格式:
{{
  "scores_a": {{S1-S8 scores}},
  "scores_b": {{S1-S8 scores}}
}}
"""
            if record_usage:
                response, usage = self.chat_with_usage("polish_merge", user_prompt)
            else:
                response = self._router.generate(prompt=user_prompt)
                usage = {"input_tokens": len(user_prompt) // 4, "output_tokens": len(response) // 4}

            try:
                import json
                data = json.loads(response)
                scores_a = data.get("scores_a", {})
                scores_b = data.get("scores_b", {})
            except (json.JSONDecodeError, ValueError):
                raise self._MergeParseError("Failed to parse LLM response")

            weights = {k: 1.0 for k in _S1_S8_KEYS}
            total_a = sum(
                weights.get(k, 1.0) * _coerce_score(scores_a.get(k))
                for k in _S1_S8_KEYS
            )
            total_b = sum(
                weights.get(k, 1.0) * _coerce_score(scores_b.get(k))
                for k in _S1_S8_KEYS
            )

            winner = labels[0] if total_a >= total_b else labels[1]
            content = content_a if winner == labels[0] else content_b

            result = {
                "content": content,
                "winner": winner,
                "scores_a": {_safe_label(k): _coerce_score(v) for k, v in scores_a.items()},
                "scores_b": {_safe_label(k): _coerce_score(v) for k, v in scores_b.items()},
                "scores_total_a": total_a,
                "scores_total_b": total_b,
                "scores_delta": total_a - total_b,
            }
            if record_usage:
                return result, usage
            return result

        except self._MergeParseError as e:
            logger.warning("polish_merge_synthesis: LLM parse failed: %s", e)
            reason = f"parse_failed: {e}"
            if record_usage:
                return {
                    "content": content_a,
                    "winner": labels[0],
                    "scores_a": {},
                    "scores_b": {},
                    "scores_total_a": 0.0,
                    "scores_total_b": 0.0,
                    "scores_delta": 0.0,
                    "fallback": reason,
                }, {"input_tokens": 0, "output_tokens": 0}
            return {
                "content": content_a,
                "winner": labels[0],
                "scores_a": {},
                "scores_b": {},
                "scores_total_a": 0.0,
                "scores_total_b": 0.0,
                "scores_delta": 0.0,
                "fallback": reason,
            }
        except Exception as e:
            logger.warning("polish_merge_synthesis: LLM failed: %s", e)
            reason = f"llm_failed: {e}"
            winner = labels[0] if len(content_a) >= len(content_b) else labels[1]
            content = content_a if winner == labels[0] else content_b
            if record_usage:
                return {
                    "content": content,
                    "winner": winner,
                    "scores_a": {},
                    "scores_b": {},
                    "scores_total_a": 0.0,
                    "scores_total_b": 0.0,
                    "scores_delta": 0.0,
                    "fallback": reason,
                }, {"input_tokens": 0, "output_tokens": 0}
            return {
                "content": content,
                "winner": winner,
                "scores_a": {},
                "scores_b": {},
                "scores_total_a": 0.0,
                "scores_total_b": 0.0,
                "scores_delta": 0.0,
                "fallback": reason,
            }