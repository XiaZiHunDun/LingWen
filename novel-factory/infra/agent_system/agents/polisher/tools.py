# novel-factory/agent_system/agents/polisher/tools.py
from typing import Any, Dict, List, Optional

from ..base import AgentBase
from .prompts import (
    build_dialogue_prompt,
    build_pacing_prompt,
    get_dialogue_system_prompt,
    get_pacing_system_prompt,
)

DEFAULT_MAX_TOKENS = 3000


class PolisherTools(AgentBase):
    """润色师工具集 — LLM 增强版 (Phase 7.2)

    继承 AgentBase 获得 LLM 集成能力。
    支持读者 A-T 变体配置, 通过 reader_id 参数切换。
    主入口 polish_chapter 串联 3 个路径 (2 LLM + 1 规则):
        optimize_dialogue_llm → adjust_pacing_llm → remove_ai_gloss
    """

    def __init__(self, router=None):
        super().__init__(router)
        self._current_reader_id: Optional[str] = None

    # ==================== Reader 切换 ====================

    def set_reader(self, reader_id: str) -> None:
        self._current_reader_id = reader_id.upper()

    def get_current_reader(self) -> Optional[str]:
        return self._current_reader_id

    # ==================== 主入口 (Phase 7.2 NEW) ====================

    def polish_chapter(
        self,
        chapter_num: int,
        content: str,
        style_guide: Optional[Dict] = None,
        reader_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """LLM 化润色主入口 (Phase 8.6.1: 委托 _impl(record_usage=False))

        串联 3 个路径, 每个 LLM 调用 try/except 兜底, 失败不致命。
        返回 dict: {content, reader, issues, chapter_num}
        """
        return self._impl_polish_chapter(
            chapter_num, content, style_guide, reader_id, record_usage=False
        )

    def polish_chapter_with_usage(
        self,
        chapter_num: int,
        content: str,
        style_guide: Optional[Dict] = None,
        reader_id: Optional[str] = None,
    ) -> tuple[Dict[str, Any], Dict[str, int]]:
        """Phase 8.6.1: 同 polish_chapter + 返回 2 LLM usage sum (dialogue + pacing).

        返回 (result, usage) tuple, usage dict 含 input_tokens/output_tokens (2x single).
        走 self.chat_with_usage() → router.generate_with_usage() 拿真实 token 计数.
        旧 polish_chapter() 签名 0 改, 保 2120 baseline.

        Args:
            (同 polish_chapter)

        Returns:
            (result_dict, usage_dict) tuple, usage = 2 LLM sum
        """
        return self._impl_polish_chapter(
            chapter_num, content, style_guide, reader_id, record_usage=True
        )

    def _impl_polish_chapter(
        self,
        chapter_num: int,
        content: str,
        style_guide: Optional[Dict],
        reader_id: Optional[str],
        record_usage: bool,
    ):
        effective_reader = reader_id or self._current_reader_id or "A"
        polished = content
        issues: List[Dict] = []
        usage_total: Dict[str, int] = {"input_tokens": 0, "output_tokens": 0}

        # 步骤 1: LLM 优化对话 (调 public 方法, 旧 tests 通过 monkeypatch 替换)
        try:
            if record_usage:
                polished, u1 = self.optimize_dialogue_llm_with_usage(polished, effective_reader)
                usage_total["input_tokens"] += u1["input_tokens"]
                usage_total["output_tokens"] += u1["output_tokens"]
            else:
                polished = self.optimize_dialogue_llm(polished, effective_reader)
        except Exception as e:
            issues.append({"type": "dialogue_llm_fail", "severity": "P3", "issue": str(e)})

        # 步骤 2: LLM 调整节奏 (调 public 方法, 旧 tests 通过 monkeypatch 替换)
        try:
            if record_usage:
                polished, u2 = self.adjust_pacing_llm_with_usage(polished, effective_reader)
                usage_total["input_tokens"] += u2["input_tokens"]
                usage_total["output_tokens"] += u2["output_tokens"]
            else:
                polished = self.adjust_pacing_llm(polished, effective_reader)
        except Exception as e:
            issues.append({"type": "pacing_llm_fail", "severity": "P3", "issue": str(e)})

        # 步骤 3: 规则去 AI 痕迹 (快速 + 兜底, 从不失败)
        polished = self.remove_ai_gloss(polished)

        result: Dict[str, Any] = {
            "content": polished,
            "reader": effective_reader,
            "issues": issues,
            "chapter_num": chapter_num,
        }
        if record_usage:
            return result, usage_total
        return result

    # ==================== LLM 子方法 (Phase 7.2 NEW, Phase 8.6.1: parallel _with_usage) ====================

    def optimize_dialogue_llm(
        self,
        content: str,
        reader_id: Optional[str] = None,
    ) -> str:
        return self._impl_optimize_dialogue(content, reader_id, record_usage=False)

    def optimize_dialogue_llm_with_usage(
        self,
        content: str,
        reader_id: Optional[str] = None,
    ) -> tuple[str, Dict[str, int]]:
        """Phase 8.6.1: 单独调 optimize_dialogue_llm + 返回 real usage.

        旧 optimize_dialogue_llm() 签名 0 改 (返回 str).
        """
        return self._impl_optimize_dialogue(content, reader_id, record_usage=True)

    def _impl_optimize_dialogue(
        self,
        content: str,
        reader_id: Optional[str],
        record_usage: bool,
    ):
        effective_reader = reader_id or self._current_reader_id or "A"
        prompt = build_dialogue_prompt(content, effective_reader)
        system = get_dialogue_system_prompt(effective_reader)
        if record_usage:
            return self.chat_with_usage(
                prompt=prompt, system=system,
                temperature=0.5, max_tokens=DEFAULT_MAX_TOKENS,
            )
        return self.chat(
            prompt=prompt, system=system,
            temperature=0.5, max_tokens=DEFAULT_MAX_TOKENS,
        )

    def adjust_pacing_llm(
        self,
        content: str,
        reader_id: Optional[str] = None,
    ) -> str:
        return self._impl_adjust_pacing(content, reader_id, record_usage=False)

    def adjust_pacing_llm_with_usage(
        self,
        content: str,
        reader_id: Optional[str] = None,
    ) -> tuple[str, Dict[str, int]]:
        """Phase 8.6.1: 单独调 adjust_pacing_llm + 返回 real usage.

        旧 adjust_pacing_llm() 签名 0 改 (返回 str).
        """
        return self._impl_adjust_pacing(content, reader_id, record_usage=True)

    def _impl_adjust_pacing(
        self,
        content: str,
        reader_id: Optional[str],
        record_usage: bool,
    ):
        effective_reader = reader_id or self._current_reader_id or "A"
        prompt = build_pacing_prompt(content, effective_reader)
        system = get_pacing_system_prompt(effective_reader)
        if record_usage:
            return self.chat_with_usage(
                prompt=prompt, system=system,
                temperature=0.4, max_tokens=DEFAULT_MAX_TOKENS,
            )
        return self.chat(
            prompt=prompt, system=system,
            temperature=0.4, max_tokens=DEFAULT_MAX_TOKENS,
        )

    # ==================== 规则方法 (保留, 不破坏 test_agent_tools.py) ====================

    def remove_ai_gloss(self, content: str) -> str:
        """去除 AI 痕迹 — 规则路径, 快速 + 兜底"""
        replacements = [
            ("首先", ""),
            ("其次", ""),
            ("然后", ""),
            ("最后", ""),
            ("总之", ""),
            ("可以看出", ""),
        ]
        result = content
        for old, new in replacements:
            result = result.replace(old, new)
        return result

    def apply_style_guide(self, content: str, style_guide: Dict) -> str:
        """应用文风指南 — 规则路径 (out of scope, 不 LLM 化)"""
        result = content
        if style_guide.get("remove_filler"):
            result = self._remove_filler(result)
        return result

    def _remove_filler(self, content: str) -> str:
        filler_phrases = ["值得注意的是", "需要指出的是", "实际上"]
        result = content
        for phrase in filler_phrases:
            result = result.replace(phrase, "")
        return result
