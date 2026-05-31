# novel-factory/agent_system/shared/context_builder.py
from typing import Dict, List, Optional, Any
from pathlib import Path


class ContextBuilder:
    """上下文构建器 - 各Agent的数据共享标准"""

    def __init__(self, project_root: Optional[str | Path] = None) -> None:
        """Initialize ContextBuilder.

        Args:
            project_root: Root directory of the novel project.
                Defaults to current working directory.
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self._story_contract_injector: Optional[Any] = None

    def build_writing_context(
        self,
        chapter_outline: Dict,
        characters: List[Dict],
        memory_context: Dict,
        relationship_network: Dict,
        style_guide: Optional[Dict] = None,
        include_story_contract: bool = True,
    ) -> Dict[str, Any]:
        """构建写作上下文

        Args:
            chapter_outline: 章节大纲
            characters: 角色列表
            memory_context: 记忆上下文
            relationship_network: 关系网络
            style_guide: 文风指南
            include_story_contract: 是否注入故事合约 (默认: True)
        """
        character_states = self._get_current_states(characters)
        active_foreshadow = self._get_active_foreshadow(memory_context)
        recent_events = self._get_recent_events(memory_context)

        context = {
            "chapter_outline": chapter_outline,
            "characters": characters,
            "character_states": character_states,
            "relationship_network": relationship_network,
            "active_foreshadow": active_foreshadow,
            "recent_events": recent_events,
            "style_guide": style_guide or self._get_default_style_guide(),
        }

        # Inject story contract if available and requested
        if include_story_contract:
            story_contract = self._get_story_contract()
            if story_contract:
                context["story_contract"] = story_contract

        return context

    def _get_story_contract(self) -> Optional[Dict[str, Any]]:
        """Load story contract from .story-system/ if available.

        Returns:
            Story contract dict or None if not found.
        """
        try:
            from infra.story_contracts import StoryContractEngine

            engine = StoryContractEngine(project_root=self.project_root)
            payload = engine.load()

            if payload is None:
                return None

            return {
                "route": {
                    "primary_genre": payload.master_setting.get("route", {}).get("primary_genre", "unknown"),
                    "genre_aliases": payload.master_setting.get("route", {}).get("genre_aliases", []),
                },
                "master_constraints": {
                    "core_tone": payload.master_setting.get("master_constraints", {}).get("core_tone", ""),
                    "pacing_strategy": payload.master_setting.get("master_constraints", {}).get("pacing_strategy", ""),
                    "forbidden_patterns": payload.master_setting.get("master_constraints", {}).get("forbidden_patterns", []),
                },
                "anti_patterns": [
                    {"text": ap.get("text", ""), "source": ap.get("source_table", "unknown")}
                    for ap in payload.anti_patterns
                ],
            }
        except Exception:
            # Silently fail if story contract not available
            return None

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