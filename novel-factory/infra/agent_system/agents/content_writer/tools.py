# novel-factory/agent_system/agents/content_writer/tools.py
from typing import Dict, List, Optional


class ContentWriterTools:
    """正文写手工具集"""

    def build_writing_prompt(self, context: Dict) -> str:
        """
        构建写作Prompt
        """
        outline = context.get("chapter_outline", {})
        characters = context.get("characters", [])
        style = context.get("style_guide", {})

        prompt_parts = [
            f"请撰写{outline.get('title', '第X章')}，字数目标：{outline.get('word_count_target', 2500)}字",
            "",
            "## 章节大纲",
            f"核心事件：{', '.join(outline.get('events', []))}",
            "",
            "## 角色设定",
        ]

        for char in characters:
            prompt_parts.append(f"- {char.get('name')}: {', '.join(char.get('personality', []))}")

        prompt_parts.extend([
            "",
            "## 文风要求",
            f"基调：{style.get('tone', '简洁有力')}",
            f"对话比例：{style.get('dialogue_ratio', '30%')}",
            "",
            "请开始创作："
        ])

        return "\n".join(prompt_parts)

    def add_chapter_hook(self, content: str, hook_type: str = "cliffhanger") -> str:
        """添加章末钩子"""
        hooks = {
            "cliffhanger": "就在这时，他突然听到了一个声音...",
            "question": "这一切究竟是怎么回事？",
            "revelation": "原来，真相竟然是这样...",
            "tension": "危险，正在逼近..."
        }
        return content + "\n\n" + hooks.get(hook_type, hooks["cliffhanger"])

    def adjust_word_count(self, content: str, target: int) -> str:
        """调整字数"""
        current = len(content)
        if abs(current - target) < 200:
            return content
        return content