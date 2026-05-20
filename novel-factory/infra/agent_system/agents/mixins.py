#!/usr/bin/env python3
"""
Agent Mixins模块

提供可复用的LLM调用Mixin类，用于一致性检查、写作辅助等场景。

Usage:
    from agents.mixins import ConsistencyCheckingMixin, WritingMixin

    class AuditorTools(AgentBase, ConsistencyCheckingMixin):
        def __init__(self, router: 'AIRouter'):
            super().__init__(router)

        async def check_with_llm(self, content: str, check_type: str) -> dict:
            return await self.check_consistency(content, check_type)
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .base import AgentBase


class ConsistencyCheckingMixin:
    """一致性检查Mixin

    提供基于LLM的一致性检查能力。
    使用方式：在Agent工具类中继承此Mixin。

    Example:
        class AuditorTools(AgentBase, ConsistencyCheckingMixin):
            pass

        tools = AuditorTools(router)
        result = tools.check_consistency(content, "character")
    """

    def build_consistency_check_prompt(
        self,
        content: str,
        check_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建一致性检查Prompt

        Args:
            content: 待检查内容
            check_type: 检查类型 (character/timeline/event)
            context: 额外上下文

        Returns:
            格式化后的Prompt
        """
        check_descriptions = {
            "character": "角色行为和性格一致性",
            "timeline": "时间线和事件顺序一致性",
            "event": "事件逻辑和因果关系一致性",
            "world": "世界观设定一致性",
            "foreshadow": "伏笔埋设和回收一致性",
        }

        description = check_descriptions.get(check_type, check_type)

        prompt = f"""请检查以下小说内容的一致性问题：

## 检查类型
{description}

## 待检查内容
{content}
"""
        if context:
            prompt += f"\n## 额外上下文\n{context}"

        prompt += """
## 输出要求
请以JSON格式输出检查结果：
{
    "has_issues": true/false,
    "issues": [
        {
            "type": "问题类型",
            "severity": "P0/P1/P2/P3",
            "location": "位置描述",
            "description": "问题描述",
            "suggestion": "修改建议"
        }
    ],
    "summary": "总体评估"
}
"""
        return prompt

    def check_consistency(
        self,
        content: str,
        check_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行一致性检查

        Args:
            content: 待检查内容
            check_type: 检查类型
            context: 额外上下文

        Returns:
            检查结果字典
        """
        prompt = self.build_consistency_check_prompt(content, check_type, context)

        try:
            return self.chat_json(prompt)
        except Exception as e:
            return {
                "has_issues": False,
                "issues": [],
                "error": str(e),
                "summary": f"检查失败: {e}"
            }


class WritingMixin:
    """写作辅助Mixin

    提供基于LLM的写作辅助能力。
    """

    def build_writing_prompt(
        self,
        chapter_info: Dict[str, Any],
        characters: List[Dict[str, Any]],
        style_guide: Dict[str, Any]
    ) -> str:
        """构建写作Prompt

        Args:
            chapter_info: 章节信息（标题、大纲、事件等）
            characters: 角色列表
            style_guide: 风格指南

        Returns:
            格式化后的写作Prompt
        """
        prompt = f"""请撰写{chapter_info.get('title', '第X章')}，字数目标：{chapter_info.get('word_count_target', 2500)}字。

## 章节大纲
核心事件：{', '.join(chapter_info.get('events', []))}
"""
        if chapter_info.get('foreshadow'):
            prompt += f"\n本章需埋设伏笔：{', '.join(chapter_info['foreshadow'])}"

        prompt += "\n\n## 角色设定\n"
        for char in characters:
            prompt += f"- {char.get('name')}: {', '.join(char.get('personality', []))}"

        prompt += f"""

## 文风要求
基调：{style_guide.get('tone', '简洁有力')}
对话比例：{style_guide.get('dialogue_ratio', '30%')}
"""

        return prompt

    def generate_continuation(
        self,
        content: str,
        direction: str,
        target_length: int = 500
    ) -> str:
        """续写内容

        Args:
            content: 已有内容
            direction: 续写方向说明
            target_length: 目标字数

        Returns:
            续写内容
        """
        prompt = f"""请续写以下内容，遵循指定的风格和方向。

## 已有内容
{content}

## 续写方向
{direction}

## 要求
- 续写约{target_length}字
- 保持与前文一致的风格
- 不要重复前文内容

请直接输出续写内容：
"""
        return self.chat(prompt, temperature=0.8)


class PolishingMixin:
    """润色Mixin

    提供基于LLM的文本润色能力。
    """

    POLISH_PROMPTS = {
        "dialogue": "请优化以下对话，使其更加自然和符合角色性格：",
        "description": "请优化以下场景描写，增强画面感和沉浸感：",
        "pace": "请优化以下内容的节奏，加快或放缓以达到更好的阅读体验：",
        "ai_gloss": "请移除以下文本中的AI写作痕迹（如过度格式化、机械过渡等）：",
    }

    def polish(
        self,
        content: str,
        polish_type: str = "dialogue"
    ) -> str:
        """润色文本

        Args:
            content: 待润色内容
            polish_type: 润色类型 (dialogue/description/pace/ai_gloss)

        Returns:
            润色后的内容
        """
        instruction = self.POLISH_PROMPTS.get(polish_type, self.POLISH_PROMPTS["dialogue"])
        prompt = f"""{instruction}

## 待润色内容
{content}

请直接输出润色后的内容，不要添加任何说明：
"""
        return self.chat(prompt, temperature=0.6)


class AnalysisMixin:
    """分析Mixin

    提供基于LLM的内容分析能力。
    """

    def analyze_chapter(
        self,
        content: str,
        dimensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """分析章节质量

        Args:
            content: 章节内容
            dimensions: 分析维度列表 (S1-S8)

        Returns:
            分析结果
        """
        dimension_map = {
            "S1": "剧情完整性",
            "S2": "逻辑自洽",
            "S3": "文笔风格",
            "S4": "情感共鸣",
            "S5": "节奏控制",
            "S6": "可读性",
            "S7": "主角魅力",
            "S8": "人物弧光",
        }

        if dimensions is None:
            dimensions = list(dimension_map.keys())

        dims_desc = "\n".join([f"- {d}: {dimension_map.get(d, d)}" for d in dimensions])

        prompt = f"""请分析以下小说章节的质量：

## 分析维度
{dims_desc}

## 章节内容
{content[:8000]}  # 限制长度避免超出token限制

## 输出要求
请以JSON格式输出分析结果：
{{
    "scores": {{
        "S1": 85,
        "S2": 78,
        ...
    }},
    "strengths": ["优势1", "优势2"],
    "issues": [
        {{
            "dimension": "S1",
            "severity": "P1",
            "description": "问题描述",
            "suggestion": "修改建议"
        }}
    ],
    "overall_score": 82,
    "summary": "总体评价"
}}
"""
        return self.chat_json(prompt)
