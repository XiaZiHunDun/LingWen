#!/usr/bin/env python3
"""
关键章节润色器
使用MiniMax M2.7对关键章节进行深度润色
"""

import logging
import os
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from infra.ai_service.base import ProviderConfig
from infra.ai_service.minimax_provider import MiniMaxProvider
from infra.config.api_config_loader import get_api_config

logger = logging.getLogger(__name__)


class KeyChapterType(Enum):
    """章节关键类型"""
    REGULAR = "regular"           # 普通章节
    CLIMAX = "climax"             # 高潮章节
    EMOTIONAL = "emotional"       # 情感转折章节
    FORESHADOW = "foreshadow"     # 伏笔回收章节
    CREATION = "creation"         # 重要角色首次出场


@dataclass
class KeyChapterInfo:
    """关键章节信息"""
    chapter_num: int
    chapter_type: KeyChapterType
    confidence: float  # 0.0-1.0
    reason: str


class KeyChapterClassifier:
    """
    关键章节分类器

    根据章节号、标题、内容识别关键章节类型
    """

    # 高潮章节关键词
    CLIMAX_KEYWORDS = [
        "决战", "最终", "觉醒", "突破", "毁灭",
        "死亡", "永别", "终章", "天罚", "湮灭",
        "爆发", "升华", "蜕变", "真相大白"
    ]

    # 情感转折关键词
    EMOTIONAL_KEYWORDS = [
        "牺牲", "离别", "告白", "求婚", "婚礼",
        "死别", "重逢", "和解", "释怀", "心痛",
        "泪", "哭", "悲伤", "绝望", "希望"
    ]

    # 伏笔回收章节（来自伏笔追踪表）
    FORESHADOW_RECOVERY_CHAPTERS = [
        239, 240, 241,  # 决战前夕
        261, 262, 263,  # 苏琳苏醒
        270, 271, 272,  # 小九觉醒
        291, 292, 293,  # 暗皇登场
        340, 341, 342,  # 最终决战
    ]

    # 重要角色首次出场章节
    CHARACTER_CREATION_CHAPTERS = [
        1,    # 林夜首次出场
        6,    # 苏琳首次出场
        16,   # 小九首次出场
        22,   # 铁蛋首次出场
    ]

    def classify(
        self,
        chapter_num: int,
        chapter_title: str = "",
        content: str = ""
    ) -> KeyChapterInfo:
        """
        分类章节关键类型

        Args:
            chapter_num: 章节号
            chapter_title: 章节标题
            content: 章节内容（可选）

        Returns:
            KeyChapterInfo: 分类结果
        """
        # 检查高潮章节
        if self._is_climax(chapter_num, chapter_title, content):
            return KeyChapterInfo(
                chapter_num=chapter_num,
                chapter_type=KeyChapterType.CLIMAX,
                confidence=0.9,
                reason="章节标题或内容包含高潮关键词"
            )

        # 检查情感转折
        if self._is_emotional(chapter_num, chapter_title, content):
            return KeyChapterInfo(
                chapter_num=chapter_num,
                chapter_type=KeyChapterType.EMOTIONAL,
                confidence=0.85,
                reason="章节内容包含情感转折关键词"
            )

        # 检查伏笔回收
        if self._is_foreshadow_recovery(chapter_num):
            return KeyChapterInfo(
                chapter_num=chapter_num,
                chapter_type=KeyChapterType.FORESHADOW,
                confidence=0.95,
                reason="章节在伏笔追踪表的回收节点"
            )

        # 检查角色首次出场
        if self._is_character_creation(chapter_num):
            return KeyChapterInfo(
                chapter_num=chapter_num,
                chapter_type=KeyChapterType.CREATION,
                confidence=0.9,
                reason="重要角色首次出场章节"
            )

        # 默认普通章节
        return KeyChapterInfo(
            chapter_num=chapter_num,
            chapter_type=KeyChapterType.REGULAR,
            confidence=0.0,
            reason="普通章节"
        )

    def _is_climax(
        self,
        chapter_num: int,
        chapter_title: str,
        content: str
    ) -> bool:
        """检查是否为高潮章节"""
        combined = f"{chapter_title} {content[:500]}"
        for keyword in self.CLIMAX_KEYWORDS:
            if keyword in combined:
                return True
        return False

    def _is_emotional(
        self,
        chapter_num: int,
        chapter_title: str,
        content: str
    ) -> bool:
        """检查是否为情感转折章节"""
        combined = f"{chapter_title} {content[:500]}"
        for keyword in self.EMOTIONAL_KEYWORDS:
            if keyword in combined:
                return True
        return False

    def _is_foreshadow_recovery(self, chapter_num: int) -> bool:
        """检查是否为伏笔回收章节"""
        return chapter_num in self.FORESHADOW_RECOVERY_CHAPTERS

    def _is_character_creation(self, chapter_num: int) -> bool:
        """检查是否为首发出场章节"""
        return chapter_num in self.CHARACTER_CREATION_CHAPTERS

    def is_key_chapter(self, chapter_num: int) -> bool:
        """快速判断是否为关键章节"""
        info = self.classify(chapter_num)
        return info.confidence > 0.5


class ClaudePolisher:
    """
    MiniMax深度润色器

    使用MiniMax M2.7对关键章节进行深度润色
    """

    POLISH_SYSTEM_PROMPT = """你是一个专业的小说润色专家。你的任务是对小说关键章节进行深度润色。

润色要求：
1. 增强情感描写层次 - 让读者能更深刻地感受到情绪
2. 优化视角切换流畅度 - 确保视角转换自然
3. 增加感官描写细节 - 用视觉、听觉、触觉等丰富描写
4. 保持原有剧情和人物性格 - 不要改变故事走向
5. 句式要有多样性 - 避免重复使用相同的句式结构
6. 不要删除任何内容 - 只增强，不精简

输出要求：
- 直接输出润色后的正文
- 不要解释，不要标记
- 只返回修改后的内容
"""

    TYPE_HINTS = {
        KeyChapterType.CLIMAX: "这是高潮章节，需要增强紧张感和冲击力。战斗场面要更加激烈，情感要更加充沛。",
        KeyChapterType.EMOTIONAL: "这是情感转折章节，需要深化情感描写。人物内心要更加细腻，情感要更加真实动人。",
        KeyChapterType.FORESHADOW: "这是伏笔回收章节，需要强化因果关联。让读者感受到前面的伏笔都有意义。",
        KeyChapterType.CREATION: "这是重要角色首次出场，需要建立人物形象。让角色更加立体，给读者留下深刻印象。",
        KeyChapterType.REGULAR: "这是重要章节，需要全面润色。提升整体质量。",
    }

    def __init__(self, client: Optional[MiniMaxProvider] = None):
        """
        初始化润色器

        Args:
            client: MiniMaxProvider实例，默认从配置创建
        """
        if client is None:
            config_loader = get_api_config()
            api_key = config_loader.minimax_api_key
            if not api_key:
                raise ValueError(
                    "MiniMax API key not found. "
                    "Please set MINIMAX_API_KEY in config/api_config.yaml or environment."
                )
            provider_config = ProviderConfig(
                api_key=api_key,
                model="MiniMax-M2.7",
            )
            self._client = MiniMaxProvider(provider_config)
        else:
            self._client = client

    def polish(
        self,
        chapter_num: int,
        content: str,
        key_type: KeyChapterType
    ) -> str:
        """
        对关键章节进行深度润色

        Args:
            chapter_num: 章节号
            content: 章节内容
            key_type: 关键章节类型

        Returns:
            润色后的内容
        """
        prompt = self._build_prompt(chapter_num, content, key_type)

        try:
            polished = self._client.generate(
                prompt=prompt,
                system=self.POLISH_SYSTEM_PROMPT,
                max_tokens=8192,
                temperature=0.3
            )
            return polished.strip()
        except Exception as e:
            logger.error(f"Claude polish failed for ch{chapter_num:03d}: {e}")
            raise

    def _build_prompt(
        self,
        chapter_num: int,
        content: str,
        key_type: KeyChapterType
    ) -> str:
        """构建润色提示词"""
        hint = self.TYPE_HINTS.get(key_type, self.TYPE_HINTS[KeyChapterType.REGULAR])

        return f"""润色以下章节（第{chapter_num}章）：

章节类型：{key_type.value}
润色要求：{hint}

原文：
{content}

请直接输出润色后的正文，不要其他内容。"""


class KeyChapterPolisher:
    """
    关键章节润色器

    整合分类器和润色器，提供完整的润色流程
    """

    def __init__(
        self,
        client: Optional[MiniMaxProvider] = None,
        classifier: Optional[KeyChapterClassifier] = None,
        polisher: Optional[ClaudePolisher] = None
    ):
        self._classifier = classifier or KeyChapterClassifier()
        self._polisher = polisher or ClaudePolisher(client)

    def polish_chapter(
        self,
        chapter_num: int,
        content: str,
        chapter_title: str = "",
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        润色章节

        Args:
            chapter_num: 章节号
            content: 章节内容
            chapter_title: 章节标题
            dry_run: 干跑模式，不实际润色

        Returns:
            包含润色结果的字典
        """
        # 分类
        info = self._classifier.classify(chapter_num, chapter_title, content)

        if info.confidence == 0:
            return {
                "chapter_num": chapter_num,
                "polished": False,
                "reason": "普通章节，不需要润色",
                "type": info.chapter_type.value
            }

        if dry_run:
            return {
                "chapter_num": chapter_num,
                "polished": True,
                "reason": info.reason,
                "type": info.chapter_type.value,
                "dry_run": True,
                "message": "干跑模式，实际未润色"
            }

        # 执行润色
        try:
            polished_content = self._polisher.polish(
                chapter_num, content, info.chapter_type
            )
            return {
                "chapter_num": chapter_num,
                "polished": True,
                "reason": info.reason,
                "type": info.chapter_type.value,
                "original_length": len(content),
                "polished_length": len(polished_content)
            }
        except Exception as e:
            return {
                "chapter_num": chapter_num,
                "polished": False,
                "reason": info.reason,
                "type": info.chapter_type.value,
                "error": str(e)
            }

    def polish_with_backup(
        self,
        chapter_num: int,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        带备份的润色

        读取章节文件，润色后保存备份
        """
        chapters_dir = PROJECT_ROOT / "03_内容仓库" / "04_正文"
        ch_file = chapters_dir / f"ch{chapter_num:03d}.md"

        if not ch_file.exists():
            return {
                "chapter_num": chapter_num,
                "polished": False,
                "error": f"章节文件不存在: {ch_file}"
            }

        # 读取内容
        content = ch_file.read_text(encoding="utf-8")

        # 提取标题和内容
        lines = content.split("\n")
        title = ""
        body = content
        if lines and lines[0].startswith("#"):
            title = lines[0].lstrip("#").strip()
            body = "\n".join(lines[1:]).strip()

        # 执行润色
        result = self.polish_chapter(chapter_num, body, title, dry_run)

        if result.get("polished") and not dry_run:
            # 备份原文件
            backup_file = chapters_dir / f"ch{chapter_num:03d}.md.bak"
            ch_file.rename(backup_file)

            # 写入润色后内容
            polished_content = self._polisher.polish(
                chapter_num, body,
                KeyChapterType(result["type"])
            )
            ch_file.write_text(f"# {title}\n\n{polished_content}", encoding="utf-8")

            result["backup_file"] = str(backup_file)

        return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="关键章节润色工具")
    parser.add_argument("--chapter", type=int, required=True, help="章节号")
    parser.add_argument("--dry-run", action="store_true", help="干跑模式")
    parser.add_argument("--auto-detect", action="store_true", help="自动检测关键章节")

    args = parser.parse_args()

    polisher = KeyChapterPolisher()

    if args.dry_run:
        print(f"干跑模式：检查章节 {args.chapter}")
        result = polisher.polish_chapter(args.chapter, "测试内容", dry_run=True)
    else:
        result = polisher.polish_with_backup(args.chapter, args.dry_run)

    print(f"\n结果: {result}")


if __name__ == "__main__":
    main()
