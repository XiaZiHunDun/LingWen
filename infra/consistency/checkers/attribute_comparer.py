#!/usr/bin/env python3
"""
属性比对器模块

从小说章节中抽取角色/物品的属性值，并检测跨章节的属性矛盾。

支持的属性类型：
- 数值型：年龄、身高、人数等
- 描述型：眼睛颜色、头发颜色、体型等
- 状态型：存活/死亡、能力有无等

使用方式：
    comparer = AttributeComparer()
    values = comparer.extract_attribute_values("年龄", chapters)
    contradictions = comparer.detect_mismatch("年龄", values)
"""

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AttributeValue:
    """属性值记录"""
    entity_name: str       # 实体名称（角色/物品）
    attribute_name: str    # 属性名称
    value: str             # 属性值（原始字符串）
    parsed_value: Any      # 解析后的值（用于比对）
    chapter: int           # 章节号
    line_num: int          # 行号
    context: str           # 上下文（前后各50字）
    confidence: float      # 置信度 0.0-1.0


@dataclass
class Contradiction:
    """属性矛盾记录"""
    entity_name: str
    attribute_name: str
    values: List[AttributeValue]  # 不一致的值列表
    severity: str                 # P0/P1/P2
    contradiction_type: str        # age/eye_color/height/etc
    description: str               # 矛盾描述
    suggestion: str                # 修复建议

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity": self.entity_name,
            "attribute": self.attribute_name,
            "chapter_values": [(v.chapter, v.value) for v in self.values],
            "severity": self.severity,
            "type": self.contradiction_type,
            "description": self.description,
            "suggestion": self.suggestion,
        }


class AttributeComparer:
    """属性比对器

    核心功能：
    1. extract_attribute_values: 从章节中抽取指定属性的所有值
    2. detect_mismatch: 检测属性值的不一致
    """

    # 属性抽取规则
    ATTRIBUTE_RULES = {
        "年龄": {
            "patterns": [
                r"(\d+)岁",
                r"年纪(.*?)岁",
                r"年龄(\d+)",
            ],
            "entity_patterns": [
                r"([^\s，,。！!？?]{2,4})(?:是|的|被|为)?(\d+)岁",
                r"([^\s，,。！!？?]{2,4})今年(\d+)岁",
                r"([^\s，,。！!？?]{2,4})已经(\d+)岁了",
            ],
            "severity": "P0",
            "group_by": "entity",
        },
        "眼睛颜色": {
            "patterns": [
                r"(蓝色|蓝色|蓝色)的眼睛",
                r"蓝色双眸",
                r"眼睛是(蓝色|黑色|绿色|灰色|紫色|金色|棕色|褐色|碧色|墨色|赤色|橙黄色)",
                r"眸中(蓝色|黑色|绿色|灰色|紫色|金色|棕色|褐色|碧色|墨色|赤色|橙黄色)",
                r"(蓝色|黑色|绿色|灰色|紫色|金色|棕色|褐色|碧色|墨色|赤色|橙黄色)(?:的眼睛|双眸|眼眸)",
            ],
            "severity": "P1",
            "group_by": "entity",
        },
        "头发颜色": {
            "patterns": [
                r"(黑色|白色|金色|银色|红色|蓝色|绿色|紫色|棕色|褐色)的头发",
                r"头发(黑色|白色|金色|银色|红色|蓝色|绿色|紫色|棕色|褐色)",
                r"一头(黑色|白色|金色|银色|红色|蓝色|绿色|紫色|棕色|褐色)",
                r"(黑色|白色|金色|银色|红色|蓝色|绿色|紫色|棕色|褐色)长发",
            ],
            "severity": "P1",
            "group_by": "entity",
        },
        "身高": {
            "patterns": [
                r"身高(.*?)米",
                r"高(\d+\.?\d*)米",
                r"有(\d+\.?\d*)米高",
                r"身材高(.*?)米",
            ],
            "severity": "P1",
            "group_by": "entity",
        },
        "人数": {
            "patterns": [
                r"(\d+)个人",
                r"(\d+)名(.*?)人",
                r"一共(\d+)人",
                r"总计(\d+)人",
                r"(\d+)个人员",
            ],
            "severity": "P2",
            "group_by": "context",
        },
        "时间": {
            "patterns": [
                r"第(\d+)天",
                r"第(\d+)夜",
                r"第(\d+)年",
                r"(\d+)年后",
                r"(\d+)年前",
            ],
            "severity": "P1",
            "group_by": "context",
        },
    }

    def __init__(self, rules: Optional[Dict[str, Any]] = None):
        """初始化属性比对器

        Args:
            rules: 自定义规则（可选），覆盖默认规则
        """
        self.rules = rules or self.ATTRIBUTE_RULES

    def extract_attribute_values(
        self,
        attribute_name: str,
        chapters: List[Tuple[int, str]],
    ) -> Dict[str, List[AttributeValue]]:
        """从章节中抽取指定属性的所有值

        Args:
            attribute_name: 属性名称（如"年龄"、"眼睛颜色"）
            chapters: 章节列表 [(chapter_num, content), ...]

        Returns:
            {entity_name: [AttributeValue, ...]}  按实体分组的属性值
        """
        if attribute_name not in self.rules:
            return {}

        rule = self.rules[attribute_name]
        patterns = rule.get("patterns", [])
        entity_patterns = rule.get("entity_patterns", [])

        results: Dict[str, List[AttributeValue]] = defaultdict(list)

        for chapter_num, content in chapters:
            lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                # 使用实体模式抽取（优先）
                for entity_pattern in entity_patterns:
                    for match in re.finditer(entity_pattern, line):
                        groups = match.groups()
                        if len(groups) >= 2:
                            entity_name = groups[0].strip()
                            value_str = groups[1].strip()

                            if entity_name and value_str:
                                attr_value = AttributeValue(
                                    entity_name=entity_name,
                                    attribute_name=attribute_name,
                                    value=value_str,
                                    parsed_value=self._parse_value(attribute_name, value_str),
                                    chapter=chapter_num,
                                    line_num=line_num,
                                    context=self._extract_context(line, match.start(), 50),
                                    confidence=0.8,
                                )
                                results[entity_name].append(attr_value)

                # 使用通用模式抽取
                for pattern in patterns:
                    for match in re.finditer(pattern, line):
                        # 尝试提取实体名
                        entity_name = self._extract_entity_name(line, match.start())

                        attr_value = AttributeValue(
                            entity_name=entity_name or "UNKNOWN",
                            attribute_name=attribute_name,
                            value=match.group(0),
                            parsed_value=self._parse_value(attribute_name, match.group(0)),
                            chapter=chapter_num,
                            line_num=line_num,
                            context=self._extract_context(line, match.start(), 50),
                            confidence=0.6,
                        )

                        if entity_name:
                            results[entity_name].append(attr_value)
                        else:
                            results["UNKNOWN"].append(attr_value)

        return dict(results)

    def extract_all_attributes(
        self,
        chapters: List[Tuple[int, str]],
        attribute_names: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, List[AttributeValue]]]:
        """抽取所有（或指定）属性的值

        Args:
            chapters: 章节列表
            attribute_names: 要抽取的属性列表（None表示全部）

        Returns:
            {attribute_name: {entity_name: [AttributeValue, ...]}}
        """
        if attribute_names is None:
            attribute_names = list(self.rules.keys())

        results = {}
        for attr_name in attribute_names:
            if attr_name in self.rules:
                results[attr_name] = self.extract_attribute_values(attr_name, chapters)

        return results

    def detect_mismatch(
        self,
        attribute_name: str,
        values: Dict[str, List[AttributeValue]],
    ) -> List[Contradiction]:
        """检测属性值的不一致

        Args:
            attribute_name: 属性名称
            values: extract_attribute_values 的返回结果

        Returns:
            Contradiction列表
        """
        if attribute_name not in self.rules:
            return []

        rule = self.rules[attribute_name]
        severity = rule.get("severity", "P2")
        contradictions = []

        for entity_name, attr_values in values.items():
            if entity_name == "UNKNOWN" or len(attr_values) < 2:
                continue

            # 按章节排序
            sorted_values = sorted(attr_values, key=lambda x: x.chapter)

            # 检测不一致
            unique_values: List[AttributeValue] = [sorted_values[0]]
            for val in sorted_values[1:]:
                if not self._values_equal(attribute_name, val.parsed_value, unique_values[-1].parsed_value):
                    unique_values.append(val)

            # 如果有多个不同的值，说明存在矛盾
            if len(unique_values) > 1:
                # 检查是否真的是矛盾（相邻值差异太大）
                for i in range(len(unique_values) - 1):
                    curr = unique_values[i]
                    next_val = unique_values[i + 1]

                    # 对于数值型属性，检查差异是否合理
                    if isinstance(curr.parsed_value, (int, float)) and isinstance(next_val.parsed_value, (int, float)):
                        diff = abs(curr.parsed_value - next_val.parsed_value)
                        # 年龄差异超过10岁，可能是矛盾
                        if attribute_name == "年龄" and diff > 10:
                            contradictions.append(self._create_contradiction(
                                entity_name=entity_name,
                                attribute_name=attribute_name,
                                values=[curr, next_val],
                                severity=severity,
                                description=f"角色{entity_name}的年龄在第{curr.chapter}章描述为{curr.value}，"
                                           f"但在第{next_val.chapter}章描述为{next_val.value}，"
                                           f"差异{int(diff)}岁，可能存在矛盾。",
                            ))

        return contradictions

    def detect_all_mismatches(
        self,
        all_attributes: Dict[str, Dict[str, List[AttributeValue]]],
    ) -> List[Contradiction]:
        """检测所有属性的不一致

        Args:
            all_attributes: extract_all_attributes 的返回结果

        Returns:
            所有检测到的矛盾
        """
        all_contradictions = []

        for attribute_name, values in all_attributes.items():
            contradictions = self.detect_mismatch(attribute_name, values)
            all_contradictions.extend(contradictions)

        return all_contradictions

    def _parse_value(self, attribute_name: str, value_str: str) -> Any:
        """解析属性值为可比较的格式"""
        if attribute_name == "年龄":
            # 提取数字
            match = re.search(r"\d+", value_str)
            return int(match.group(0)) if match else 0
        elif attribute_name == "身高":
            # 提取数字（米）
            match = re.search(r"\d+\.?\d*", value_str)
            return float(match.group(0)) if match else 0.0
        elif attribute_name == "时间":
            # 提取数字
            match = re.search(r"\d+", value_str)
            return int(match.group(0)) if match else 0
        else:
            return value_str.strip()

    def _values_equal(self, attribute_name: str, val1: Any, val2: Any) -> bool:
        """判断两个值是否相等"""
        if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
            if attribute_name == "年龄":
                # 年龄差异在2岁以内认为是相同的（可能是描述误差）
                return abs(val1 - val2) <= 2
            elif attribute_name == "身高":
                # 身高差异在5cm以内认为是相同的
                return abs(val1 - val2) <= 0.05
            else:
                return val1 == val2
        else:
            return str(val1).strip() == str(val2).strip()

    def _extract_entity_name(self, line: str, match_pos: int) -> Optional[str]:
        """提取匹配位置前的实体名称"""
        start = max(0, match_pos - 30)
        text_before = line[start:match_pos]

        # 查找常见实体标记
        patterns = [
            r"([A-Za-z一-龥]{2,4})(?:是|的|被|为|这|那|有)",  # 中文名
            r"(他|她|它)(?:的|是|被|为|这|那)?([A-Za-z一-龥]{2,4})?",  # 他/她/它
        ]

        for pattern in patterns:
            match = re.search(pattern, text_before)
            if match:
                groups = match.groups()
                if groups[0] in ["他", "她", "它"]:
                    return groups[1] if groups[1] else None
                return groups[0]

        return None

    def _extract_context(self, line: str, match_pos: int, window: int) -> str:
        """提取匹配的上下文"""
        start = max(0, match_pos - window)
        end = min(len(line), match_pos + window)
        return line[start:end]

    def _create_contradiction(
        self,
        entity_name: str,
        attribute_name: str,
        values: List[AttributeValue],
        severity: str,
        description: str,
    ) -> Contradiction:
        """创建矛盾记录"""
        suggestion = self._generate_suggestion(attribute_name, values)

        return Contradiction(
            entity_name=entity_name,
            attribute_name=attribute_name,
            values=values,
            severity=severity,
            contradiction_type=f"{attribute_name}_mismatch",
            description=description,
            suggestion=suggestion,
        )

    def _generate_suggestion(self, attribute_name: str, values: List[AttributeValue]) -> str:
        """生成修复建议"""
        if attribute_name == "年龄":
            return (
                "建议统一角色年龄设定。\n"
                "方案1：修改较早出现的年龄描述，使其与后续一致\n"
                "方案2：在后续章节中补充角色成长/时间跳跃说明"
            )
        elif attribute_name == "眼睛颜色":
            return (
                "建议统一角色外貌设定。\n"
                "检查所有章节中该角色眼睛颜色的描述，统一为同一颜色"
            )
        elif attribute_name == "身高":
            return (
                "建议统一角色身材设定。\n"
                "检查所有章节中该角色身高的描述，如有出入需统一"
            )
        else:
            return f"建议检查并统一角色{attribute_name}的描述"


# 导出
__all__ = ["AttributeComparer", "AttributeValue", "Contradiction"]
