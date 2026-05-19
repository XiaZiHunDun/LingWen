#!/usr/bin/env python3
"""
模板推荐引擎 (Template Recommender)

根据场景类型、质量评分、模板历史使用情况推荐最佳模板

Usage:
    from template_recommender import TemplateRecommender

    recommender = TemplateRecommender(prompt_assembler)
    recommended = recommender.recommend(
        scene_type="high_stakes_scene",
        genre="玄幻",
        required_metrics=["S1", "S4", "S5"]
    )
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from prompt_assembler import PromptAssembler, TemplateCategory, TemplateMetadata


@dataclass
class TemplateScore:
    """模板评分结果"""
    template: TemplateMetadata
    total_score: float
    metric_scores: Dict[str, float]
    temperature_match: float
    category_bonus: float
    history_bonus: float
    reasons: List[str] = field(default_factory=list)


@dataclass
class RecommendationCriteria:
    """推荐标准"""
    scene_type: str
    genre: str = "玄幻"
    required_metrics: List[str] = field(default_factory=list)
    preferred_category: Optional[TemplateCategory] = None
    min_quality_threshold: float = 0.5
    max_temperature: float = 1.0
    min_temperature: float = 0.0


class TemplateRecommender:
    """模板推荐引擎"""

    # 场景类型到模板类别的映射
    SCENE_TO_CATEGORY = {
        "outline_generation": TemplateCategory.OUTLINE,
        "content_continuation": TemplateCategory.CONTINUATION,
        "high_stakes_scene": TemplateCategory.CONTINUATION,
        "dialogue_scene": TemplateCategory.CONTINUATION,
        "review_analysis": TemplateCategory.REVIEW,
        "polish": TemplateCategory.POLISH,
        "brainstorming": TemplateCategory.CONTINUATION,
        "long_content_generation": TemplateCategory.CONTINUATION,
    }

    # 质量维度权重配置
    QUALITY_WEIGHTS = {
        "S1": {"name": "剧情完整性", "weight": 0.20},
        "S2": {"name": "逻辑自洽", "weight": 0.20},
        "S3": {"name": "文笔风格", "weight": 0.15},
        "S4": {"name": "情感共鸣", "weight": 0.15},
        "S5": {"name": "节奏控制", "weight": 0.15},
        "S6": {"name": "可读性", "weight": 0.10},
        "S7": {"name": "主角魅力", "weight": 0.03},
        "S8": {"name": "人物弧光", "weight": 0.02},
    }

    def __init__(self, assembler: PromptAssembler, index_file: Optional[str] = None):
        self.assembler = assembler
        if index_file:
            self.index_file = Path(index_file)
        else:
            # 默认路径
            self.index_file = Path(__file__).parent / "00_模板索引.yaml"
        self._load_extended_index()

    def _load_extended_index(self):
        """加载扩展索引信息（使用统计等）"""
        self.template_stats: Dict[str, Dict] = {}

        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            for template in data.get('templates', []):
                self.template_stats[template['id']] = {
                    'use_count': template.get('use_count', 0),
                    'success_rate': template.get('success_rate', 0.0),
                    'avg_score': template.get('avg_score', 0.0),
                    'last_used': template.get('last_used'),
                }

    def recommend(
        self,
        scene_type: str,
        genre: str = "玄幻",
        required_metrics: Optional[List[str]] = None,
        preferred_category: Optional[str] = None,
        top_k: int = 3
    ) -> List[TemplateScore]:
        """
        推荐模板

        Args:
            scene_type: 场景类型 (如 "high_stakes_scene", "outline_generation")
            genre: 小说类型
            required_metrics: 必需的质量维度 (如 ["S1", "S4"])
            preferred_category: 偏好的模板类别
            top_k: 返回前k个推荐

        Returns:
            排序后的模板推荐列表
        """
        criteria = RecommendationCriteria(
            scene_type=scene_type,
            genre=genre,
            required_metrics=required_metrics or [],
            preferred_category=TemplateCategory(preferred_category) if preferred_category else None
        )

        candidates = self._get_candidate_templates(criteria)
        scored = [self._score_template(t, criteria) for t in candidates]
        ranked = sorted(scored, key=lambda x: x.total_score, reverse=True)

        return ranked[:top_k]

    def recommend_single(
        self,
        scene_type: str,
        genre: str = "玄幻",
        required_metrics: Optional[List[str]] = None
    ) -> Optional[TemplateScore]:
        """推荐单个最佳模板"""
        results = self.recommend(scene_type, genre, required_metrics, top_k=1)
        return results[0] if results else None

    def _get_candidate_templates(self, criteria: RecommendationCriteria) -> List[TemplateMetadata]:
        """获取候选模板列表"""
        templates = []

        # 确定目标类别
        target_category = criteria.preferred_category
        if target_category is None and criteria.scene_type in self.SCENE_TO_CATEGORY:
            target_category = self.SCENE_TO_CATEGORY[criteria.scene_type]

        # 按类别筛选
        if target_category:
            template_names = self.assembler.list_templates(target_category)
        else:
            template_names = self.assembler.list_templates()

        for name in template_names:
            template = self.assembler.get_template(name)
            if template and template.status == "active":
                templates.append(template)

        return templates

    def _score_template(
        self,
        template: TemplateMetadata,
        criteria: RecommendationCriteria
    ) -> TemplateScore:
        """计算模板评分"""
        metric_scores: Dict[str, float] = {}
        reasons: List[str] = []
        total = 0.0

        # 1. 质量维度匹配评分
        template_metrics = template.care_elements.get('result_metrics', [])
        for metric in criteria.required_metrics:
            if metric in template_metrics:
                weight = self.QUALITY_WEIGHTS.get(metric, {}).get('weight', 0.1)
                metric_scores[metric] = weight * 10  # 满分10分
                total += metric_scores[metric]
            else:
                metric_scores[metric] = 0.0

        # 2. 温度匹配评分
        temp_score = self._calculate_temperature_score(template, criteria)
        total += temp_score

        # 3. 类别匹配加分
        category_bonus = 0.0
        if criteria.preferred_category and template.category == criteria.preferred_category:
            category_bonus = 2.0
            reasons.append(f"类别匹配: {template.category.value}")
        total += category_bonus

        # 4. 历史表现加分
        history_bonus = self._calculate_history_bonus(template.id)
        total += history_bonus
        if history_bonus > 0:
            reasons.append(f"历史表现优秀: +{history_bonus:.1f}")

        # 5. 场景匹配加分
        if criteria.scene_type in self.SCENE_TO_CATEGORY:
            if template.category == self.SCENE_TO_CATEGORY[criteria.scene_type]:
                reasons.append("场景类型匹配")

        return TemplateScore(
            template=template,
            total_score=total,
            metric_scores=metric_scores,
            temperature_match=temp_score,
            category_bonus=category_bonus,
            history_bonus=history_bonus,
            reasons=reasons
        )

    def _calculate_temperature_score(
        self,
        template: TemplateMetadata,
        criteria: RecommendationCriteria
    ) -> float:
        """计算温度匹配分数"""
        template_temp = template.temperature.recommended
        min_temp = template.temperature.min_value
        max_temp = template.temperature.max_value

        # 检查是否在范围内
        if min_temp <= criteria.min_temperature <= max_temp:
            return 3.0  # 首选
        elif min_temp <= criteria.max_temperature <= max_temp:
            return 2.0  # 可接受
        elif criteria.min_temperature <= template_temp <= criteria.max_temperature:
            return 2.5  # 推荐温度在范围内
        else:
            # 计算距离
            optimal_temp = (min_temp + max_temp) / 2
            distance = abs(template_temp - optimal_temp)
            return max(0, 3.0 - distance)

    def _calculate_history_bonus(self, template_id: str) -> float:
        """计算历史表现加分"""
        stats = self.template_stats.get(template_id, {})
        use_count = stats.get('use_count', 0)
        success_rate = stats.get('success_rate', 0.0)
        avg_score = stats.get('avg_score', 0.0)

        if use_count == 0:
            return 0.5  # 新模板给点机会

        # 综合评分
        score = (success_rate * 3 + (avg_score / 10) * 5 + min(use_count / 10, 1) * 2)
        return min(score, 5.0)  # 最高5分

    def update_template_stats(
        self,
        template_id: str,
        success: bool,
        score: float
    ):
        """更新模板使用统计"""
        if not self.index_file.exists():
            return

        with open(self.index_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        for template in data.get('templates', []):
            if template['id'] == template_id:
                # 更新使用次数
                template['use_count'] = template.get('use_count', 0) + 1

                # 更新成功率和平均分
                old_rate = template.get('success_rate', 0.0)
                old_score = template.get('avg_score', 0.0)
                old_count = template.get('use_count', 1) - 1

                new_rate = (old_rate * old_count + (1 if success else 0)) / template['use_count']
                new_score = (old_score * old_count + score) / template['use_count']

                template['success_rate'] = round(new_rate, 3)
                template['avg_score'] = round(new_score, 2)
                template['last_used'] = datetime.now().strftime("%Y-%m-%d")

                break

        with open(self.index_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False, indent=2)

        # 重新加载
        self._load_extended_index()

    def get_template_version_history(self, template_id: str) -> List[Dict]:
        """获取模板版本历史"""
        if not self.index_file.exists():
            return []

        with open(self.index_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        version_history = data.get('version_history', [])

        # 找到该模板相关的版本记录
        relevant = []
        for entry in version_history:
            if any(template_id.startswith(v) for v in entry.get('templates_added', [])):
                relevant.append(entry)

        return relevant

    def explain_recommendation(self, template_score: TemplateScore) -> str:
        """生成推荐理由说明"""
        lines = [
            f"# 模板推荐: {template_score.template.name}",
            f"",
            f"## 基本信息",
            f"- ID: {template_score.template.id}",
            f"- 版本: {template_score.template.version}",
            f"- 类别: {template_score.template.category.value}",
            f"- 描述: {template_score.template.description}",
            f"",
            f"## 评分详情",
            f"- 综合得分: {template_score.total_score:.2f}",
            f"- 温度匹配: {template_score.temperature_match:.2f}",
            f"- 类别加成: {template_score.category_bonus:.2f}",
            f"- 历史加成: {template_score.history_bonus:.2f}",
            f"",
            f"## 推荐理由",
        ]

        for reason in template_score.reasons:
            lines.append(f"- {reason}")

        if template_score.metric_scores:
            lines.append(f"")
            lines.append(f"## 质量维度匹配")
            for metric, score in template_score.metric_scores.items():
                weight = self.QUALITY_WEIGHTS.get(metric, {})
                lines.append(f"- {metric} ({weight.get('name', '')}): {score:.1f}/10")

        lines.extend([
            f"",
            f"## 温度参数",
            f"- 推荐温度: {template_score.template.temperature.recommended}",
            f"- 温度范围: [{template_score.template.temperature.min_value}, {template_score.template.temperature.max_value}]",
        ])

        return "\n".join(lines)

    def get_popular_templates(self, limit: int = 10) -> List[TemplateMetadata]:
        """
        获取最受欢迎的模板（按综合评分排序）

        综合评分公式: score = use_count * success_rate * (avg_score / 10)

        Args:
            limit: 返回前N个，默认为10

        Returns:
            按热度综合评分降序排列的模板列表（不含use_count=0的模板）
        """
        if not self.template_stats:
            return []

        scored_templates = []
        for template_id, stats in self.template_stats.items():
            use_count = stats.get('use_count', 0)
            # 过滤掉未使用的模板
            if use_count == 0:
                continue

            success_rate = stats.get('success_rate', 0.0)
            avg_score = stats.get('avg_score', 0.0)

            # 计算综合评分
            score = use_count * success_rate * (avg_score / 10)
            scored_templates.append((template_id, score))

        # 按分数降序排列
        scored_templates.sort(key=lambda x: x[1], reverse=True)

        # 获取前limit个模板元数据
        results = []
        for template_id, score in scored_templates[:limit]:
            template = self.assembler.get_template(template_id)
            if template:
                results.append(template)

        return results


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="模板推荐引擎")
    parser.add_argument("--scene", "-s", required=True, help="场景类型")
    parser.add_argument("--genre", "-g", default="玄幻", help="小说类型")
    parser.add_argument("--metrics", "-m", nargs="*", help="必需的质量维度")
    parser.add_argument("--top-k", "-k", type=int, default=3, help="返回前k个推荐")
    parser.add_argument("--config", "-c", default="config/prompts", help="配置目录")
    parser.add_argument("--index", "-i", help="模板索引文件")

    args = parser.parse_args()

    assembler = PromptAssembler(args.config)
    recommender = TemplateRecommender(assembler, args.index)

    results = recommender.recommend(
        scene_type=args.scene,
        genre=args.genre,
        required_metrics=args.metrics,
        top_k=args.top_k
    )

    print(f"\n{'='*60}")
    print(f"场景: {args.scene} | 类型: {args.genre}")
    print(f"{'='*60}\n")

    for i, result in enumerate(results, 1):
        print(f"#{i} {result.template.name} (得分: {result.total_score:.2f})")
        print(f"    模板ID: {result.template.id}")
        print(f"    温度: {result.template.temperature.recommended}")
        if result.reasons:
            print(f"    理由: {', '.join(result.reasons)}")
        print()


if __name__ == "__main__":
    import sys
    sys.exit(main() or 0)
