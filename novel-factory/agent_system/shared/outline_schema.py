# novel-factory/agent_system/shared/outline_schema.py
from typing import Dict, List, Any, Optional
import yaml


class OutlineSchema:
    """大纲Schema定义与验证"""

    REQUIRED_FIELDS = ["title", "chapters"]

    def validate(self, outline: Dict) -> bool:
        """验证大纲结构"""
        for field in self.REQUIRED_FIELDS:
            if field not in outline:
                raise ValueError(f"Missing required field: {field}")
        if not isinstance(outline["chapters"], list):
            raise ValueError("chapters must be a list")
        return True

    def to_yaml(self, outline: Dict, file_path: str):
        """导出为YAML"""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(outline, f, allow_unicode=True, default_flow_style=False)

    def from_yaml(self, file_path: str) -> Dict:
        """从YAML加载"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def get_chapter_outline(self, outline: Dict, chapter_num: int) -> Optional[Dict]:
        """获取指定章节的大纲"""
        for ch in outline.get("chapters", []):
            if ch.get("num") == chapter_num:
                return ch
        return None