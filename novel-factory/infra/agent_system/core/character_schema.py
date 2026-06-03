# novel-factory/agent_system/core/character_schema.py
from typing import Any, Dict, List

import yaml


class CharacterSchema:
    """角色Schema定义与验证"""

    REQUIRED_FIELDS = ["name", "personality", "first_appearance"]

    def validate(self, character: Dict) -> bool:
        """验证角色结构"""
        for field in self.REQUIRED_FIELDS:
            if field not in character:
                raise ValueError(f"Missing required field: {field}")
        return True

    def to_yaml(self, character: Dict, file_path: str):
        """导出为YAML"""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(character, f, allow_unicode=True, default_flow_style=False)

    def from_yaml(self, file_path: str) -> Dict:
        """从YAML加载"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def to_character_card(self, character: Dict) -> str:
        """生成角色卡片文本"""
        lines = [
            f"# {character['name']}",
            f"**角色**: {character.get('role', 'N/A')}",
            f"**首次出场**: 第{character['first_appearance']}章",
            "",
            "## 性格",
            ", ".join(character.get('personality', [])),
            "",
            "## 背景",
            character.get('background', 'N/A'),
            "",
            "## 能力",
            ", ".join(character.get('abilities', [])) or 'N/A',
            "",
            "## 关系",
        ]
        for rel in character.get('relationships', []):
            lines.append(f"- **{rel['target']}**: {rel['type']} (信任:{rel.get('trust', 0)}, 冲突:{rel.get('conflict', 0)})")
        return "\n".join(lines)
