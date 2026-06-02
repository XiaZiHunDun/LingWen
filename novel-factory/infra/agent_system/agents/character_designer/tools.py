# novel-factory/agent_system/agents/character_designer/tools.py
from typing import Dict, List, Optional
from ...core.character_schema import CharacterSchema


class CharacterDesignerTools:
    """人设师工具集"""

    def __init__(self, router=None):
        # router 当前未使用（纯规则实现）；保留参数以保持与其他 Agent 接口一致
        self.router = router
        self.schema = CharacterSchema()

    def generate_character_card(self, requirements: Dict) -> Dict:
        """
        生成角色卡片
        """
        character = {
            "name": requirements["name"],
            "role": requirements.get("role", "supporting"),
            "personality": requirements.get("personality", []),
            "first_appearance": requirements.get("first_appearance", 1),
            "background": requirements.get("background", ""),
            "abilities": requirements.get("abilities", []),
            "voice_pattern": requirements.get("voice_pattern", ""),
            "relationships": [],
            "character_arc": {}
        }
        self.schema.validate(character)
        return character

    def add_relationship(self, character: Dict, target: str, relationship_type: str, trust: float = 0.5, conflict: float = 0.1) -> Dict:
        """添加关系"""
        if "relationships" not in character:
            character["relationships"] = []
        character["relationships"].append({
            "target": target,
            "type": relationship_type,
            "trust": trust,
            "conflict": conflict
        })
        return character

    def save_character(self, character: Dict, file_path: str):
        """保存角色"""
        self.schema.to_yaml(character, file_path)

    def load_character(self, file_path: str) -> Dict:
        """加载角色"""
        return self.schema.from_yaml(file_path)