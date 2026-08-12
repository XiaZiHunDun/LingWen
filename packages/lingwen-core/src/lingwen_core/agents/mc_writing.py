"""MasterController 创作相关 Mixin

Phase 15.0 P3-SPLIT: 从 master_controller.py 拆分的创作相关方法。
"""
from typing import Dict, List, Optional


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
            chapter_num, outline, characters, memory_context, style_guide, use_llm,
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
            chapter_num, outline, characters, memory_context, style_guide, use_llm,
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

        suggestions = self.writing_suggestion.generate_suggestions(
            self.relationship_tracker, chapter_num
        )

        if use_llm:
            if record_usage:
                result, usage = self.content_writer.generate_chapter_with_usage(
                    chapter_num, context,
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
            chapter_num, content, characters, timeline, use_llm, record_usage=False,
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
            chapter_num, content, characters, timeline, use_llm, record_usage=True,
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
        return {"issues": [], "suggestions": []}