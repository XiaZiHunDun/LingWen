# novel-factory/agent_system/agents/polisher/tools.py
from typing import Dict, List


class PolisherTools:
    """润色师工具集"""

    def __init__(self, router=None):
        # router 当前未使用（纯规则实现）；保留参数以保持与其他 Agent 接口一致
        self.router = router

    def optimize_dialogue(self, content: str) -> str:
        """优化对话"""
        return content

    def remove_ai_gloss(self, content: str) -> str:
        """去除AI痕迹"""
        replacements = [
            ("首先", ""),
            ("其次", ""),
            ("然后", ""),
            ("最后", ""),
            ("总之", ""),
            ("可以看出", "")
        ]
        result = content
        for old, new in replacements:
            result = result.replace(old, new)
        return result

    def adjust_pacing(self, content: str) -> str:
        """调整节奏"""
        return content

    def apply_style_guide(self, content: str, style_guide: Dict) -> str:
        """应用文风指南"""
        result = content
        if style_guide.get("remove_filler"):
            result = self._remove_filler(result)
        return result

    def _remove_filler(self, content: str) -> str:
        """去除冗余"""
        filler_phrases = ["值得注意的是", "需要指出的是", "实际上"]
        result = content
        for phrase in filler_phrases:
            result = result.replace(phrase, "")
        return result
