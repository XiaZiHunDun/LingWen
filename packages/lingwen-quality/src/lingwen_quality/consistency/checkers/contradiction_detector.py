#!/usr/bin/env python3
"""
矛盾检测引擎

整合三大检测模式：
1. RuleBasedDetector - 规则匹配检测
2. AttributeComparer - 属性比对检测
3. LLMCausalReasoner - LLM推理检测

使用方式：
    detector = ContradictionDetector()
    contradictions = detector.detect_for_chapter(chapter_num, content, context)
    contradictions = detector.detect_all(chapters)
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .attribute_comparer import AttributeComparer, AttributeValue, Contradiction

logger = logging.getLogger(__name__)


@dataclass
class ContradictionResult:
    """矛盾检测结果"""
    chapter: int
    contradictions: List[Contradiction]
    detection_time_ms: float
    detection_mode: str  # rule_based / attribute / llm / mixed
    total_scanned: int = 0  # 扫描的实体数量

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter": self.chapter,
            "contradictions": [c.to_dict() for c in self.contradictions],
            "contradiction_count": len(self.contradictions),
            "detection_time_ms": self.detection_time_ms,
            "detection_mode": self.detection_mode,
            "total_scanned": self.total_scanned,
        }


@dataclass
class DetectionConfig:
    """检测配置"""
    enable_rule_based: bool = True
    enable_attribute: bool = True
    enable_llm: bool = False  # 默认关闭，LLM成本高
    llm_threshold: str = "P1"  # 只有P1+问题才启用LLM复核
    max_llm_cases: int = 10  # 最多复核10个案例
    attribute_types: List[str] = field(default_factory=lambda: ["年龄", "眼睛颜色", "头发颜色", "身高"])


class RuleBasedDetector:
    """基于规则的矛盾检测器

    检测已知的、结构化的矛盾模式
    """

    # 矛盾模式规则
    CONTRADICTION_PATTERNS = [
        {
            "id": "death_action_contradiction",
            "name": "死亡后活动",
            "description": "角色已死亡但仍在活动/说话",
            "death_patterns": [
                r"死了", r"去世", r"死亡", r"断气", r"咽气",
                r"停止呼吸", r"心脏停止了", r"已经没有.*气息",
                r"的尸体", r"遗体", r"遗骸",
            ],
            "action_patterns": [
                r"他/她/它.*说", r"他/她/它.*做", r"他/她/它.*想",
                r"他/她/它.*走向", r"他/她/它.*拿起", r"他/她/它.*看着",
                r"走到", r"拿起", r"看着", r"说道", r"问道",
            ],
            "severity": "P0",
        },
        {
            "id": "left_no_return_contradiction",
            "name": "离开后无尸体矛盾",
            "description": "角色离开后没有回来，但后面提及其尸体",
            "departure_patterns": [
                r"出去了", r"离开了", r"走了", r"消失", r"不见踪影",
                r"再也没有回来", r"没有回来", r"不知去向", r"失踪",
            ],
            "body_patterns": [
                r"没有埋葬", r"那具尸体", r"在.*尸体.*旁", r"怕.*尸体",
                r"埋葬.*老人", r"老人的尸体",
            ],
            "severity": "P0",
        },
        {
            "id": "age_regression",
            "name": "年龄回退",
            "description": "角色年龄在后文描述中变小",
            "age_pattern": r"(\d+)岁",
            "check": "decreasing",
            "severity": "P0",
        },
    ]

    def __init__(self, rules: Optional[List[Dict]] = None):
        self.rules = rules or self.CONTRADICTION_PATTERNS

    def detect(
        self,
        chapter_num: int,
        content: str,
        previous_chapters: Optional[List[Tuple[int, str]]] = None,
    ) -> List[Contradiction]:
        """检测规则类矛盾"""
        contradictions = []

        for rule in self.rules:
            detected = self._check_rule(chapter_num, content, rule, previous_chapters)
            contradictions.extend(detected)

        return contradictions

    def _check_rule(
        self,
        chapter_num: int,
        content: str,
        rule: Dict[str, Any],
        previous_chapters: Optional[List[Tuple[int, str]]] = None,
    ) -> List[Contradiction]:
        """检查单条规则"""
        rule_id = rule["id"]

        if rule_id == "death_action_contradiction":
            return self._check_death_action(content, chapter_num, rule)
        elif rule_id == "left_no_return_contradiction":
            return self._check_left_no_return(content, chapter_num, rule, previous_chapters)
        elif rule_id == "age_regression":
            return self._check_age_regression(content, chapter_num, rule, previous_chapters)

        return []

    def _check_death_action(
        self, content: str, chapter_num: int, rule: Dict
    ) -> List[Contradiction]:
        """检测死亡后活动矛盾"""
        contradictions = []

        # 找所有死亡声明
        death_positions = []
        for pattern in rule.get("death_patterns", []):
            for match in re.finditer(pattern, content):
                death_positions.append((match.start(), match.group(0)))

        # 找所有活动描述
        action_positions = []
        action_pattern_str = "|".join(rule.get("action_patterns", []))
        if action_pattern_str:
            for match in re.finditer(action_pattern_str, content):
                action_positions.append((match.start(), match.group(0)))

        # 检查是否有矛盾（死亡声明后出现活动）
        for death_pos, death_text in death_positions:
            for action_pos, action_text in action_positions:
                if action_pos > death_pos:
                    # 提取上下文
                    context_start = max(0, death_pos - 50)
                    context_end = min(len(content), action_pos + 50)
                    content[context_start:context_end]

                    contradictions.append(Contradiction(
                        entity_name="UNKNOWN",
                        attribute_name="生死状态",
                        values=[],
                        severity=rule["severity"],
                        contradiction_type="death_action",
                        description=f"检测到角色死亡后仍有活动：'{death_text}' 后出现 '{action_text}'",
                        suggestion="如果角色已死亡，不应描述其后续活动。请检查是描述了其他角色还是存在错误。",
                    ))
                    break

        return contradictions

    def _check_left_no_return(
        self,
        content: str,
        chapter_num: int,
        rule: Dict,
        previous_chapters: Optional[List[Tuple[int, str]]] = None,
    ) -> List[Contradiction]:
        """检测离开后无尸体矛盾"""
        contradictions = []

        # 检查是否有"离开"声明
        has_departure = False
        for pattern in rule.get("departure_patterns", []):
            if re.search(pattern, content):
                has_departure = True
                break

        # 检查是否有"尸体"相关描述
        has_body = False
        for pattern in rule.get("body_patterns", []):
            if re.search(pattern, content):
                has_body = True
                break

        if has_departure and has_body:
            contradictions.append(Contradiction(
                entity_name="UNKNOWN",
                attribute_name="状态",
                values=[],
                severity=rule["severity"],
                contradiction_type="left_no_return",
                description="角色'离开后没有回来'，但后面提及'尸体'，矛盾点在于：没回来怎会有尸体？",
                suggestion="如果角色'离开后没回来'，不应该有尸体存在。请检查描述是否匹配。",
            ))

        return contradictions

    def _check_age_regression(
        self,
        content: str,
        chapter_num: int,
        rule: Dict,
        previous_chapters: Optional[List[Tuple[int, str]]] = None,
    ) -> List[Contradiction]:
        """检测年龄回退"""
        contradictions = []

        # 提取当前章节的年龄
        age_pattern = rule.get("age_pattern", r"(\d+)岁")
        current_ages = {}

        for match in re.finditer(age_pattern, content):
            age = int(match.group(1))
            pos = match.start()
            context_start = max(0, pos - 20)
            context_end = min(len(content), pos + 20)
            context = content[context_start:context_end]

            # 尝试提取角色名
            char_match = re.search(r"([^\s，,。！!？?]{2,4})(?:是|的|被|为)?\d+岁", context)
            if char_match:
                char_name = char_match.group(1)
                current_ages[char_name] = (age, chapter_num)

        # 与前文对比
        if previous_chapters:
            for char_name, (current_age, current_ch) in current_ages.items():
                for prev_ch, prev_content in reversed(previous_chapters):
                    prev_match = re.search(
                        rf"{re.escape(char_name)}(?:是|的|被|为)?(\d+)岁",
                        prev_content
                    )
                    if prev_match:
                        prev_age = int(prev_match.group(1))
                        if current_age < prev_age:
                            contradictions.append(Contradiction(
                                entity_name=char_name,
                                attribute_name="年龄",
                                values=[],
                                severity=rule["severity"],
                                contradiction_type="age_regression",
                                description=f"角色{char_name}的年龄从第{prev_ch}章的{prev_age}岁回退到第{current_ch}章的{current_age}岁",
                                suggestion="年龄通常只增不减。请检查是角色设定变化还是描述错误。",
                            ))
                        break

        return contradictions


class LLMCausalReasoner:
    """LLM因果推理检测器

    使用LLM检测复杂的、需推理的因果矛盾
    """

    def __init__(self, llm_service=None, config: Optional[Dict[str, Any]] = None):
        self.llm_service = llm_service
        self.config = config or {}

    async def detect(
        self,
        chapter_num: int,
        chapter_content: str,
        context: Dict[str, Any],
    ) -> List[Contradiction]:
        """使用LLM检测矛盾"""
        if not self.llm_service:
            logger.warning("LLM服务未配置，跳过LLM检测")
            return []

        # 准备prompt
        prompt = self._build_prompt(chapter_num, chapter_content, context)

        try:
            # 调用LLM
            response = await self.llm_service.generate(prompt)
            return self._parse_response(response, chapter_num)
        except Exception as e:
            logger.error(f"LLM检测失败: {e}")
            return []

    def _build_prompt(
        self,
        chapter_num: int,
        chapter_content: str,
        context: Dict[str, Any],
    ) -> str:
        """构建检测prompt"""
        # 获取相关段落
        related_chunks = context.get("related_chunks", [])
        chunks_text = "\n\n".join([
            f"章节{ch.get('chapter', 0)}: {ch.get('content', '')[:500]}"
            for ch in related_chunks[:5]
        ])

        prompt = f"""请检查以下小说片段是否存在矛盾。

重点检查：
1. 时间矛盾：时间线是否前后一致？
2. 属性矛盾：角色外貌/性格/能力描述是否一致？
3. 因果矛盾：事件是否有合理的前因后果？
4. 关系矛盾：角色关系描述是否前后一致？

相关章节片段：
{chunks_text}

当前章节（第{chapter_num}章）：
{chapter_content[:2000]}

如果发现矛盾，请用以下JSON格式返回：
{{
    "contradictions": [
        {{
            "type": "time|attribute|causal|relationship",
            "severity": "P0|P1|P2",
            "description": "矛盾描述",
            "evidence": ["证据1", "证据2"],
            "suggestion": "修复建议"
        }}
    ]
}}

如果没有发现矛盾，返回空数组：{{"contradictions": []}}
"""
        return prompt

    def _parse_response(self, response: str, chapter_num: int) -> List[Contradiction]:
        """解析LLM响应"""
        contradictions = []

        try:
            import json
            # 尝试提取JSON
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                data = json.loads(json_match.group(0))
                for item in data.get("contradictions", []):
                    contradictions.append(Contradiction(
                        entity_name="LLM_DETECTED",
                        attribute_name=item.get("type", "unknown"),
                        values=[],
                        severity=item.get("severity", "P2"),
                        contradiction_type=item.get("type", "unknown"),
                        description=item.get("description", ""),
                        suggestion=item.get("suggestion", ""),
                    ))
        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}")

        return contradictions


class ContradictionDetector:
    """矛盾检测引擎

    整合三大检测模式，统一入口
    """

    def __init__(
        self,
        config: Optional[DetectionConfig] = None,
        llm_service=None,
    ):
        self.config = config or DetectionConfig()
        self.attribute_comparer = AttributeComparer()
        self.rule_detector = RuleBasedDetector()
        self.llm_reasoner = LLMCausalReasoner(llm_service)

        # 缓存
        self._chapter_cache: Dict[int, str] = {}
        self._all_attributes_cache: Optional[Dict[str, Dict[str, List[AttributeValue]]]] = None

    def detect_for_chapter(
        self,
        chapter_num: int,
        chapter_content: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ContradictionResult:
        """检测单章节矛盾"""
        import time
        start_time = time.perf_counter()

        context = context or {}
        contradictions = []

        # 更新缓存
        self._chapter_cache[chapter_num] = chapter_content

        # 1. 规则检测
        if self.config.enable_rule_based:
            previous_chapters = [
                (ch, content) for ch, content in self._chapter_cache.items()
                if ch < chapter_num
            ]
            rule_contradictions = self.rule_detector.detect(
                chapter_num, chapter_content, previous_chapters
            )
            contradictions.extend(rule_contradictions)

        # 2. 属性检测
        if self.config.enable_attribute:
            # 获取所有章节
            all_chapters = [
                (ch, content) for ch, content in sorted(self._chapter_cache.items())
            ]

            # 清除缓存的属性以重新计算
            self._all_attributes_cache = None

            # 提取并检测所有属性
            all_attributes = self.attribute_comparer.extract_all_attributes(
                all_chapters,
                self.config.attribute_types,
            )
            self._all_attributes_cache = all_attributes

            attribute_contradictions = self.attribute_comparer.detect_all_mismatches(
                all_attributes
            )
            contradictions.extend(attribute_contradictions)

        # 3. LLM检测（如果启用且有P1+问题）
        if self.config.enable_llm and contradictions:
            p1_contradictions = [c for c in contradictions if c.severity in ("P0", "P1")]
            if len(p1_contradictions) <= self.config.max_llm_cases:
                # 简化context用于LLM
                {
                    "related_chunks": context.get("related_chunks", []),
                }
                # 注意：LLM是异步的，这里简化处理
                # llm_contradictions = asyncio.run(self.llm_reasoner.detect(...))

        detection_time_ms = (time.perf_counter() - start_time) * 1000

        # 确定检测模式
        if self.config.enable_rule_based and self.config.enable_attribute:
            mode = "mixed"
        elif self.config.enable_attribute:
            mode = "attribute"
        else:
            mode = "rule_based"

        return ContradictionResult(
            chapter=chapter_num,
            contradictions=contradictions,
            detection_time_ms=detection_time_ms,
            detection_mode=mode,
            total_scanned=len(self._chapter_cache),
        )

    def detect_all(
        self,
        chapters: List[Tuple[int, str]],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ContradictionResult]:
        """全量检测所有章节"""
        results = []

        # 更新缓存
        for chapter_num, content in chapters:
            self._chapter_cache[chapter_num] = content

        # 批量属性检测（一次性提取所有属性）
        if self.config.enable_attribute:
            self._all_attributes_cache = self.attribute_comparer.extract_all_attributes(
                chapters,
                self.config.attribute_types,
            )

        # 逐章检测
        for chapter_num, content in sorted(chapters, key=lambda x: x[0]):
            result = self.detect_for_chapter(chapter_num, content, context)
            results.append(result)

        return results

    def get_contradiction_summary(
        self,
        results: List[ContradictionResult],
    ) -> Dict[str, Any]:
        """获取矛盾汇总统计"""
        all_contradictions = []
        for result in results:
            all_contradictions.extend(result.contradictions)

        # 按类型统计
        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {"P0": 0, "P1": 0, "P2": 0}
        by_entity: Dict[str, int] = {}

        for c in all_contradictions:
            by_type[c.contradiction_type] = by_type.get(c.contradiction_type, 0) + 1
            by_severity[c.severity] = by_severity.get(c.severity, 0) + 1
            if c.entity_name != "UNKNOWN" and c.entity_name != "LLM_DETECTED":
                by_entity[c.entity_name] = by_entity.get(c.entity_name, 0) + 1

        return {
            "total": len(all_contradictions),
            "by_type": by_type,
            "by_severity": by_severity,
            "by_entity": dict(sorted(by_entity.items(), key=lambda x: x[1], reverse=True)[:10]),
            "total_chapters": len(results),
            "chapters_with_issues": sum(1 for r in results if r.contradictions),
        }


# 导出
__all__ = [
    "ContradictionDetector",
    "ContradictionResult",
    "DetectionConfig",
    "RuleBasedDetector",
    "LLMCausalReasoner",
]
