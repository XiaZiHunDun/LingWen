"""MasterController 创作相关 Mixin

Phase 15.0 P3-SPLIT: 从 master_controller.py 拆分的创作相关方法。
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class WritingMixin:
    """创作相关方法（委托给Agent工具）"""

    def generate_outline(self, settings: Dict, requirements: Dict) -> Dict:
        """生成大纲"""
        return self.outline_master.generate_outline(settings, requirements)

    def generate_characters(self, outline: Dict, character_requirements: List[Dict]) -> List[Dict]:
        """生成角色卡片"""
        characters = []
        for req in character_requirements:
            card = self.character_designer.generate_character_card(req)
            characters.append(card)
        return characters

    def write_chapter(
        self,
        chapter_num: int,
        outline: Dict,
        characters: List[Dict],
        memory_context: Dict,
        style_guide: Dict,
        use_llm: bool = True,
    ) -> Dict:
        """写章节流程（委托给content_writer）"""
        return self._impl_write_chapter(
            chapter_num,
            outline,
            characters,
            memory_context,
            style_guide,
            use_llm,
            record_usage=False,
        )

    def write_chapter_with_usage(
        self,
        chapter_num: int,
        outline: Dict,
        characters: List[Dict],
        memory_context: Dict,
        style_guide: Dict,
        use_llm: bool = True,
    ):
        """写章节 variant — 真实 usage."""
        return self._impl_write_chapter(
            chapter_num,
            outline,
            characters,
            memory_context,
            style_guide,
            use_llm,
            record_usage=True,
        )

    def _impl_write_chapter(
        self,
        chapter_num: int,
        outline: Dict,
        characters: List[Dict],
        memory_context: Dict,
        style_guide: Dict,
        use_llm: bool,
        record_usage: bool,
    ):
        chapter_outline = self.outline_master.schema.get_chapter_outline(outline, chapter_num)

        context = self.context_builder.build_writing_context(
            chapter_outline=chapter_outline,
            characters=characters,
            memory_context=memory_context,
            relationship_network=self.relationship_tracker.get_network(),
            style_guide=style_guide,
        )

        suggestions = self.writing_suggestion.generate_suggestions(self.relationship_tracker, chapter_num)

        if use_llm:
            if record_usage:
                result, usage = self.content_writer.generate_chapter_with_usage(
                    chapter_num,
                    context,
                )
                return {
                    "content": result["content"],
                    "word_count": result.get("word_count", len(result["content"])),
                    "suggestions": suggestions,
                    "context": context,
                }, usage
            result = self.content_writer.generate_chapter(chapter_num, context)
            return {
                "content": result["content"],
                "word_count": result.get("word_count", len(result["content"])),
                "suggestions": suggestions,
                "context": context,
            }
        else:
            prompt = self.content_writer.build_writing_prompt(context)
            if record_usage:
                return {
                    "prompt": prompt,
                    "suggestions": suggestions,
                    "context": context,
                }, {"input_tokens": 0, "output_tokens": 0}
            return {
                "prompt": prompt,
                "suggestions": suggestions,
                "context": context,
            }

    def audit_chapter(
        self,
        chapter_num: int,
        content: str,
        characters: List[Dict],
        timeline: List[Dict],
        use_llm: bool = True,
    ) -> Dict:
        """审核章节（委托给auditor）"""
        return self._impl_audit_chapter(
            chapter_num,
            content,
            characters,
            timeline,
            use_llm,
            record_usage=False,
        )

    def audit_chapter_with_usage(
        self,
        chapter_num: int,
        content: str,
        characters: List[Dict],
        timeline: List[Dict],
        use_llm: bool = True,
    ):
        """审核章节 variant — 真实 usage."""
        return self._impl_audit_chapter(
            chapter_num,
            content,
            characters,
            timeline,
            use_llm,
            record_usage=True,
        )

    def _impl_audit_chapter(
        self,
        chapter_num: int,
        content: str,
        characters: List[Dict],
        timeline: List[Dict],
        use_llm: bool,
        record_usage: bool,
    ):
        if use_llm:
            try:
                if record_usage:
                    result, usage = self.auditor.audit_chapter_with_usage(
                        chapter_num, content, characters, timeline
                    )
                    return {
                        "issues": result.get("issues", []),
                        "suggestions": result.get("suggestions", []),
                    }, usage
                result = self.auditor.audit_chapter(chapter_num, content, characters, timeline)
                return {
                    "issues": result.get("issues", []),
                    "suggestions": result.get("suggestions", []),
                }
            except Exception:
                # Phase 30 T3: 韧性契约 — audit LLM 抛错时兜底返正常 audit report,
                # workflow 不中断. record_usage=True 返 (empty issues, zero usage);
                # record_usage=False 返 empty issues. broad except 因 LLM 库
                # 异常多样 (502/timeout/rate limit/AttributeError from shape drift),
                # 且历史契约 (test_phase7_1_production_fixes.py:113-117) 确认需吞
                # AttributeError 而非仅 RequestException.
                logger.warning(
                    "audit_chapter failed at chapter_num=%s; returning empty audit report",
                    chapter_num,
                    exc_info=True,
                )
                if record_usage:
                    return (
                        {"issues": [], "suggestions": []},
                        {"input_tokens": 0, "output_tokens": 0},
                    )
                return {"issues": [], "suggestions": []}
        return {"issues": [], "suggestions": []}
