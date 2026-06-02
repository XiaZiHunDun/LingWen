# novel-factory/agent_system/agents/outline_master/tools.py
from typing import Dict, List, Optional, Any
from ...core.outline_schema import OutlineSchema


class OutlineMasterTools:
    """大纲师工具集"""

    def __init__(self):
        self.schema = OutlineSchema()

    def generate_outline(self, settings: Dict, requirements: Dict) -> Dict:
        """
        生成完整大纲
        """
        outline = {
            "title": settings.get("title", "未命名作品"),
            "genre": settings.get("genre", "玄幻"),
            "total_chapters": requirements.get("total_chapters", 360),
            "chapters": self._generate_chapters(
                settings,
                requirements.get("total_chapters", 360)
            )
        }
        self.schema.validate(outline)
        return outline

    def generate_chapter_outline(self, chapter_num: int, events: List[str], foreshadow: Optional[List[str]] = None) -> Dict:
        """生成章大纲"""
        return {
            "num": chapter_num,
            "title": f"第{chapter_num}章",
            "events": events,
            "foreshadow": foreshadow or [],
            "word_count_target": 2500
        }

    def _generate_chapters(self, settings: Dict, total: int) -> List[Dict]:
        """生成章节列表（结构）"""
        chapters = []
        for i in range(1, total + 1):
            chapters.append({
                "num": i,
                "title": f"第{i}章",
                "events": [],
                "word_count_target": 2500
            })
        return chapters

    def save_outline(self, outline: Dict, file_path: str):
        """保存大纲"""
        self.schema.to_yaml(outline, file_path)

    def load_outline(self, file_path: str) -> Dict:
        """加载大纲"""
        return self.schema.from_yaml(file_path)