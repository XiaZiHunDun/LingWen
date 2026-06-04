# novel-factory/agent_system/agents/polisher/tools.py
from typing import Any, Dict, List, Optional

from ..base import AgentBase

try:
    from .variant_loader import get_variant_loader
    VARIANT_LOADER_AVAILABLE = True
except ImportError:
    VARIANT_LOADER_AVAILABLE = False

from .prompts import (
    build_dialogue_prompt,
    build_pacing_prompt,
    build_polish_prompt,
    get_dialogue_system_prompt,
    get_pacing_system_prompt,
    get_polish_system_prompt,
)


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
        if VARIANT_LOADER_AVAILABLE:
            self._variant_loader = get_variant_loader()

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
        """LLM 化润色主入口

        串联 3 个路径, 每个 LLM 调用 try/except 兜底, 失败不致命。
        返回 dict: {content, reader, issues, chapter_num}
        """
        effective_reader = reader_id or self._current_reader_id or "A"
        polished = content
        issues: List[Dict] = []

        # 步骤 1: LLM 优化对话
        try:
            polished = self.optimize_dialogue_llm(polished, reader_id=effective_reader)
        except Exception as e:
            issues.append({"type": "dialogue_llm_fail", "severity": "P3", "issue": str(e)})

        # 步骤 2: LLM 调整节奏
        try:
            polished = self.adjust_pacing_llm(polished, reader_id=effective_reader)
        except Exception as e:
            issues.append({"type": "pacing_llm_fail", "severity": "P3", "issue": str(e)})

        # 步骤 3: 规则去 AI 痕迹 (快速 + 兜底, 从不失败)
        polished = self.remove_ai_gloss(polished)

        return {
            "content": polished,
            "reader": effective_reader,
            "issues": issues,
            "chapter_num": chapter_num,
        }

    # ==================== LLM 子方法 (Phase 7.2 NEW) ====================

    def optimize_dialogue_llm(
        self,
        content: str,
        reader_id: Optional[str] = None,
    ) -> str:
        effective_reader = reader_id or self._current_reader_id or "A"
        prompt = build_dialogue_prompt(content, effective_reader)
        system = get_dialogue_system_prompt(effective_reader)
        return self.chat(prompt=prompt, system=system, temperature=0.5, max_tokens=3000)

    def adjust_pacing_llm(
        self,
        content: str,
        reader_id: Optional[str] = None,
    ) -> str:
        effective_reader = reader_id or self._current_reader_id or "A"
        prompt = build_pacing_prompt(content, effective_reader)
        system = get_pacing_system_prompt(effective_reader)
        return self.chat(prompt=prompt, system=system, temperature=0.4, max_tokens=3000)

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
