#!/usr/bin/env python3
"""
场景模式重复检测器

检测连续章节中相同场景模式的重复问题
评分标准（S5节奏控制）：
- 优秀: 无连续3章相同场景
- 触发P0: 连续3+章相同场景标签
"""

import re
from typing import Any, Dict, List, Optional

from ..engine.data_structures import CheckerType, Issue, IssueLocation, IssueSeverity
from .base_checker import BaseChecker


class ScenePatternRepeatChecker(BaseChecker):
    """
    场景模式重复检测器

    检测连续章节中场景模式的重复，识别以下模式：
    - 星空对话：看星星、星空、星光、并肩
    - 废墟探索：废墟、残破
    - 战斗场景：战斗、交锋、对峙
    - 室内对话：房间、室内、厅堂
    """
    _checker_type = CheckerType.SCENE_PATTERN


    # 场景标签模式
    SCENE_TAGS = {
        "星空对话": ["看星星", "星空", "星光", "并肩", "星星", "夜空", "月色"],
        "废墟探索": ["废墟", "残破", "遗迹", "废墟中", "残垣"],
        "战斗场景": ["战斗", "交锋", "对峙", "激战", "厮杀"],
        "室内对话": ["房间", "室内", "厅堂", "屋内", "宅邸"],
        "森林场景": ["森林", "树木", "林间", "草木"],
        "水域场景": ["湖", "河", "海", "水边", "溪流"],
    }

    # 连续章节阈值
    CONSECUTIVE_THRESHOLD = 3

    def __init__(self):
        super().__init__(self._checker_type)

    def check(
        self,
        chapter_content: str,
        chapter_num: int,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Issue]:
        """
        检查场景模式重复

        Args:
            chapter_content: 章节内容
            chapter_num: 章节号
            context: 包含 recent_scene_labels 的上下文

        Returns:
            Issue列表
        """
        issues = []
        context = context or {}

        # 获取前三章场景标签
        recent_labels = context.get("recent_scene_labels", [])
        current_label = self._detect_scene_label(chapter_content)

        if current_label:
            # 检查连续重复
            consecutive_count = 1
            for label in reversed(recent_labels):
                if label == current_label:
                    consecutive_count += 1
                else:
                    break

            if consecutive_count >= self.CONSECUTIVE_THRESHOLD:
                issue = Issue(
                    id=f"scene_pattern_{chapter_num}_{current_label}",
                    severity=IssueSeverity.P0,
                    checker_type=CheckerType.SCENE_PATTERN,
                    issue_type="consecutive_scene_repeat",
                    title=f"连续场景重复：{current_label}",
                    description=f"检测到连续{consecutive_count}章使用相同的场景标签「{current_label}」，节奏单调。",
                    location=IssueLocation(chapter=chapter_num),
                    evidence=f"前{consecutive_count}章场景标签：{', '.join(recent_labels[-consecutive_count:])}",
                    suggestion=f"建议在第{chapter_num}章切换场景场景，如从「{current_label}」改为「废墟探索」或「室内对话」",
                )
                issues.append(issue)

        return issues

    def _detect_scene_label(self, content: str) -> Optional[str]:
        """
        检测章节的场景标签

        Args:
            content: 章节内容

        Returns:
            场景标签，如果未检测到返回None
        """
        content_lower = content

        # 统计每个场景标签的出现次数
        tag_counts = {}
        for scene_label, keywords in self.SCENE_TAGS.items():
            count = 0
            for keyword in keywords:
                count += len(re.findall(keyword, content_lower))
            if count > 0:
                tag_counts[scene_label] = count

        if not tag_counts:
            return None

        # 返回出现次数最多的场景标签
        return max(tag_counts, key=tag_counts.get)

    def get_scene_label(self, content: str) -> Optional[str]:
        """公开接口：获取章节场景标签"""
        return self._detect_scene_label(content)
