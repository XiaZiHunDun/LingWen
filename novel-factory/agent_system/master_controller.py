# novel-factory/agent_system/master_controller.py
from typing import Dict, List, Optional, Any
from .agents.outline_master.tools import OutlineMasterTools
from .agents.character_designer.tools import CharacterDesignerTools
from .agents.content_writer.tools import ContentWriterTools
from .agents.auditor.tools import AuditorTools
from .agents.polisher.tools import PolisherTools
from .social_engine.relationship_tracker import RelationshipTracker
from .social_engine.event_effect_calculator import EventEffectCalculator
from .social_engine.conflict_alert import ConflictAlert
from .social_engine.writing_suggestion import WritingSuggestion
from .shared.context_builder import ContextBuilder


class MasterController:
    """主控调度器"""

    def __init__(self, state_dir: str = "novel-factory/agent_system"):
        self.outline_master = OutlineMasterTools()
        self.character_designer = CharacterDesignerTools()
        self.content_writer = ContentWriterTools()
        self.auditor = AuditorTools()
        self.polisher = PolisherTools()

        self.relationship_tracker = RelationshipTracker(f"{state_dir}/social_engine/relationship_network.json")
        self.event_calculator = EventEffectCalculator()
        self.conflict_alert = ConflictAlert()
        self.writing_suggestion = WritingSuggestion()
        self.context_builder = ContextBuilder()

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
        style_guide: Dict
    ) -> Dict:
        """写章节流程"""
        # 获取章节大纲
        chapter_outline = self.outline_master.schema.get_chapter_outline(outline, chapter_num)

        # 构建上下文
        context = self.context_builder.build_writing_context(
            chapter_outline=chapter_outline,
            characters=characters,
            memory_context=memory_context,
            relationship_network=self.relationship_tracker.get_network(),
            style_guide=style_guide
        )

        # 获取写作建议
        suggestions = self.writing_suggestion.generate_suggestions(
            self.relationship_tracker, chapter_num
        )

        # 构建Prompt
        prompt = self.content_writer.build_writing_prompt(context)

        return {
            "prompt": prompt,
            "suggestions": suggestions,
            "context": context
        }

    def audit_chapter(self, chapter_num: int, content: str, characters: List[Dict], timeline: List[Dict]) -> Dict:
        """审核章节"""
        # 角色一致性检查
        char_issues = self.auditor.check_character_consistency(content, characters)

        # AI痕迹检测
        ai_issues = self.auditor.detect_ai_gloss(content)

        # 生成报告
        all_issues = char_issues + ai_issues
        return self.auditor.generate_audit_report(chapter_num, all_issues, scores={})

    def polish_chapter(self, content: str) -> str:
        """润色章节"""
        result = self.polisher.remove_ai_gloss(content)
        result = self.polisher.optimize_dialogue(result)
        return result

    def apply_event(self, event_type: str, from_char: str, to_char: str, chapter: int):
        """应用事件并更新关系"""
        self.event_calculator.apply_event(event_type, from_char, to_char, self.relationship_tracker)
        self.relationship_tracker.record_event(from_char, to_char, event_type, chapter)

    def check_alerts(self, chapter: int) -> List[Dict]:
        """检查预警"""
        return self.conflict_alert.check_alerts(self.relationship_tracker, chapter)

    def get_writing_suggestions(self, chapter: int) -> List[str]:
        """获取写作建议"""
        return self.writing_suggestion.generate_suggestions(self.relationship_tracker, chapter)