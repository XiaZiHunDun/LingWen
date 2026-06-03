#!/usr/bin/env python3
"""
反套路创意生成器
在章节大纲生成后、审核前，提供3-5个反套路创意选项供选择
"""

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.config.api_config_loader import get_api_config
from infra.llm_service import LLMService, LLMTask, TaskType

logger = logging.getLogger(__name__)


@dataclass
class CreativeOption:
    """创意选项"""
    id: str
    setting: str          # 世界观/设定
    conflict: str        # 核心冲突
    character: str       # 主角设定
    twist: str           # 转折设计
    anti_trope_tags: List[str]  # 反套路标签
    match_score: float   # 与高概念库的匹配度


class AntiTropeEnhancer:
    """
    反套路创意增强器

    在大纲生成后、审核前，调用LLM生成3-5个反套路创意选项
    供主编选择并注入到后续写作中
    """

    SYSTEM_PROMPT = """你是一个专业的小说创意设计师。你的任务是基于给定的大纲，生成3-5个反套路创意选项。

要求：
1. 每个选项包含"设定"、"冲突"、"转折"、"主角设定"
2. 选项之间要有明显差异，避免雷同
3. 避免常见的升级流/退婚打脸/系统流等套路
4. 可以借鉴高概念创意库中的元素（如"时间悖论循环"、"盟友即敌人"等）

输出格式：
直接输出JSON数组，每个元素包含：
- setting: 世界观/设定
- conflict: 核心冲突
- character: 主角设定
- twist: 转折设计
- anti_trope_tags: 反套路标签列表
"""

    EXAMPLE_OUTLINE = """
章节大纲示例：
林夜是一个废土世界的幸存者，他意外获得了一个古老的修真传承。
在寻找真相的过程中，他遇到了苏琳，两人产生了情愫。
但苏琳的真实身份却是暗皇的女儿，林夜必须在她和正义之间做出选择。
"""

    def __init__(self, llm_service=None):
        self._llm = llm_service or LLMService()
        self._config = get_api_config()

    def generate_options(
        self,
        chapter_outline: str,
        count: int = 3
    ) -> List[CreativeOption]:
        """
        生成反套路创意选项

        Args:
            chapter_outline: 章节大纲
            count: 生成数量，默认3个

        Returns:
            CreativeOption列表
        """
        prompt = self._build_prompt(chapter_outline, count)

        try:
            response = self._llm.execute(LLMTask(
                task_type=TaskType.QUALITY_ANALYSIS,
                prompt=prompt,
                system=self.SYSTEM_PROMPT,
                max_tokens=3000,
                temperature=0.7,
            ))
            return self._parse_response(response, count)
        except Exception as e:
            logger.error(f"AntiTropeEnhancer failed: {e}")
            return []

    def _build_prompt(self, outline: str, count: int) -> str:
        """构建提示词"""
        return f"""基于以下大纲，生成{count}个反套路创意选项：

大纲内容：
{outline}

要求：
1. 每个选项要有独特的"设定"、"冲突"、"转折"
2. 选项之间要有明显差异
3. 避免常见的升级流、退婚打脸、系统流套路
4. 可以融入"时间悖论"、"盟友即敌人"、"力量代价"、"沉默主角"等反套路元素

直接输出JSON数组，格式：
[
  {{
    "setting": "设定描述",
    "conflict": "核心冲突",
    "character": "主角设定",
    "twist": "转折设计",
    "anti_trope_tags": ["标签1", "标签2"]
  }}
]
"""

    def _parse_response(self, response: str, count: int) -> List[CreativeOption]:
        """解析LLM响应"""
        import json

        # 尝试提取JSON
        try:
            # 找JSON数组
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)

            options = []
            for i, item in enumerate(data[:count]):
                options.append(CreativeOption(
                    id=f"anti_trope_{i+1}",
                    setting=item.get("setting", ""),
                    conflict=item.get("conflict", ""),
                    character=item.get("character", ""),
                    twist=item.get("twist", ""),
                    anti_trope_tags=item.get("anti_trope_tags", []),
                    match_score=0.8,  # 默认分数
                ))
            return options
        except Exception as e:
            logger.error(f"Failed to parse response: {e}")
            return []

    def format_options(self, options: List[CreativeOption]) -> str:
        """格式化输出选项"""
        if not options:
            return "无可用选项"

        lines = ["=" * 60, "反套路创意选项", "=" * 60]

        for i, opt in enumerate(options, 1):
            lines.append(f"\n【选项 {i}】")
            lines.append(f"  设定: {opt.setting}")
            lines.append(f"  冲突: {opt.conflict}")
            lines.append(f"  主角: {opt.character}")
            lines.append(f"  转折: {opt.twist}")
            if opt.anti_trope_tags:
                lines.append(f"  标签: {', '.join(opt.anti_trope_tags)}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='反套路创意生成器')
    parser.add_argument("--outline", type=str, required=True, help="章节大纲")
    parser.add_argument("--count", type=int, default=3, help="生成数量")
    parser.add_argument("--format", action="store_true", help="格式化输出")

    args = parser.parse_args()

    enhancer = AntiTropeEnhancer()
    options = enhancer.generate_options(args.outline, args.count)

    if args.format:
        print(enhancer.format_options(options))
    else:
        import json
        print(json.dumps([{
            "setting": o.setting,
            "conflict": o.conflict,
            "character": o.character,
            "twist": o.twist,
            "anti_trope_tags": o.anti_trope_tags,
        } for o in options], ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
