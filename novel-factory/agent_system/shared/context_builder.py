# novel-factory/agent_system/shared/context_builder.py
from typing import Dict, List, Optional, Any


class ContextBuilder:
    """上下文构建器 - 各Agent的数据共享标准"""

    def build_writing_context(
        self,
        chapter_outline: Dict,
        characters: List[Dict],
        memory_context: Dict,
        relationship_network: Dict,
        style_guide: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        构建写作上下文
        """
        character_states = self._get_current_states(characters)
        active_foreshadow = self._get_active_foreshadow(memory_context)
        recent_events = self._get_recent_events(memory_context)

        return {
            "chapter_outline": chapter_outline,
            "characters": characters,
            "character_states": character_states,
            "relationship_network": relationship_network,
            "active_foreshadow": active_foreshadow,
            "recent_events": recent_events,
            "style_guide": style_guide or self._get_default_style_guide()
        }

    def _get_current_states(self, characters: List[Dict]) -> Dict[str, Dict]:
        """获取角色当前状态"""
        states = {}
        for char in characters:
            states[char["name"]] = {
                "location": char.get("current_location"),
                "emotion": char.get("emotion_state"),
                "alive": char.get("alive", True)
            }
        return states

    def _get_active_foreshadow(self, memory_context: Dict) -> List[Dict]:
        """获取活跃伏笔"""
        return memory_context.get("pending_foreshadows", [])

    def _get_recent_events(self, memory_context: Dict) -> List[Dict]:
        """获取最近事件"""
        return memory_context.get("recent_events", [])[-5:]

    def _get_default_style_guide(self) -> Dict:
        """获取默认文风指南"""
        return {
            "tone": "简洁有力",
            "dialogue_ratio": "30%",
            "description_style": "白描为主"
        }