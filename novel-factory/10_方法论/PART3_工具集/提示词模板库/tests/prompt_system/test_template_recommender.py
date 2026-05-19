#!/usr/bin/env python3
"""
模板推荐引擎测试

Tests for TemplateRecommender
"""

import pytest
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from prompt_assembler import PromptAssembler, TemplateCategory
from template_recommender import TemplateRecommender, TemplateScore, RecommendationCriteria


# ==================== Fixtures ====================

@pytest.fixture
def temp_config_dir(tmp_path):
    """创建临时配置目录"""
    config_dir = tmp_path / "config" / "prompts"
    config_dir.mkdir(parents=True)

    # 文件路径: config_dir.parent.parent = tmp_path
    # 文件位置: tmp_path/00_模板索引.yaml, tmp_path/01_大纲生成/, etc.

    # 创建模板索引 (在 tmp_path/00_模板索引.yaml)
    index_content = """
templates:
  - id: outline_full_novel_v1
    name: 全文大纲
    category: outline
    version: v1.0.0
    status: active
    file: 01_大纲生成/全文大纲_CARE.md
    description: 生成整本小说的完整大纲
    temperature:
      recommended: 0.6
      range: [0.5, 0.7]
    care_elements:
      result_metrics: [S1, S2, S6, S7]
    use_count: 5
    success_rate: 0.8
    avg_score: 8.5

  - id: continuation_standard_v1
    name: 标准续写
    category: continuation
    version: v1.0.0
    status: active
    file: 02_正文续写/标准续写_CARE.md
    description: 标准章节续写
    temperature:
      recommended: 0.7
      range: [0.6, 0.8]
    care_elements:
      result_metrics: [S1, S2, S3, S5, S6]
    use_count: 10
    success_rate: 0.9
    avg_score: 9.0

  - id: continuation_high_stakes_v1
    name: 高潮场景
    category: continuation
    version: v1.0.0
    status: active
    file: 02_正文续写/高潮场景_CARE.md
    description: 关键情节高潮场景
    temperature:
      recommended: 0.7
      range: [0.65, 0.75]
    care_elements:
      result_metrics: [S1, S3, S4, S5]

  - id: review_logic_v1
    name: 逻辑检查
    category: review
    version: v1.0.0
    status: active
    file: 04_审核辅助/逻辑检查_CARE.md
    description: 检查逻辑漏洞
    temperature:
      recommended: 0.4
      range: [0.3, 0.5]
    care_elements:
      result_metrics: [S1, S2]
"""
    (tmp_path / "00_模板索引.yaml").write_text(index_content, encoding='utf-8')

    # 创建温度映射
    temp_content = """
scene_types:
  outline_generation:
    description: "大纲生成"
    temperature:
      recommended: 0.6
      range: [0.5, 0.7]

  content_continuation:
    description: "正文续写"
    temperature:
      recommended: 0.7
      range: [0.6, 0.8]

  high_stakes_scene:
    description: "高潮场景"
    temperature:
      recommended: 0.7
      range: [0.65, 0.75]

  review_analysis:
    description: "审核分析"
    temperature:
      recommended: 0.4
      range: [0.3, 0.5]
"""
    (config_dir / "场景温度映射.yaml").write_text(temp_content, encoding='utf-8')

    # 创建模板目录和文件 - 文件路径相对于 tmp_path (config root)
    # file: 01_大纲生成/全文大纲_CARE.md -> tmp_path/01_大纲生成/全文大纲_CARE.md
    outline_dir = tmp_path / "01_大纲生成"
    outline_dir.mkdir(parents=True)
    (outline_dir / "全文大纲_CARE.md").write_text("# 全文大纲模板\n", encoding='utf-8')

    continuation_dir = tmp_path / "02_正文续写"
    continuation_dir.mkdir(parents=True)
    (continuation_dir / "标准续写_CARE.md").write_text("# 标准续写模板\n", encoding='utf-8')
    (continuation_dir / "高潮场景_CARE.md").write_text("# 高潮场景模板\n", encoding='utf-8')

    review_dir = tmp_path / "04_审核辅助"
    review_dir.mkdir(parents=True)
    (review_dir / "逻辑检查_CARE.md").write_text("# 逻辑检查模板\n", encoding='utf-8')

    return config_dir.parent


@pytest.fixture
def assembler(temp_config_dir):
    """创建PromptAssembler实例"""
    # temp_config_dir = tmp_path (config_dir.parent)
    # assembler needs config/prompts -> tmp_path / "config" / "prompts"
    return PromptAssembler(str(temp_config_dir / "config" / "prompts"))


@pytest.fixture
def recommender(assembler, temp_config_dir):
    """创建TemplateRecommender实例"""
    # temp_config_dir = tmp_path / "config" / "prompts"
    # index file is at tmp_path / "00_模板索引.yaml" = temp_config_dir.parent.parent / "00_模板索引.yaml"
    return TemplateRecommender(
        assembler,
        index_file=str(temp_config_dir.parent.parent / "00_模板索引.yaml")
    )


# ==================== 测试推荐引擎初始化 ====================

class TestRecommenderInit:
    def test_recommender_loads_assembler(self, recommender):
        """测试加载 assembler"""
        assert recommender is not None
        assert recommender.assembler is not None

    def test_loads_template_stats(self, recommender):
        """测试加载模板统计"""
        assert len(recommender.template_stats) > 0


# ==================== 测试场景推荐 ====================

class TestSceneRecommendations:
    def test_recommend_outline_scene(self, recommender):
        """测试大纲场景推荐"""
        results = recommender.recommend(scene_type="outline_generation")

        assert len(results) > 0
        assert all(isinstance(r, TemplateScore) for r in results)
        # 大纲场景应该推荐outline类别
        assert results[0].template.category == TemplateCategory.OUTLINE

    def test_recommend_continuation_scene(self, recommender):
        """测试续写场景推荐"""
        results = recommender.recommend(scene_type="content_continuation")

        assert len(results) > 0
        assert results[0].template.category == TemplateCategory.CONTINUATION

    def test_recommend_high_stakes_scene(self, recommender):
        """测试高潮场景推荐"""
        results = recommender.recommend(scene_type="high_stakes_scene")

        assert len(results) > 0
        # 高潮场景应推荐continuation类别
        assert results[0].template.category == TemplateCategory.CONTINUATION

    def test_recommend_review_scene(self, recommender):
        """测试审核场景推荐"""
        results = recommender.recommend(scene_type="review_analysis")

        assert len(results) > 0
        assert results[0].template.category == TemplateCategory.REVIEW

    def test_recommend_with_required_metrics(self, recommender):
        """测试按必需质量维度推荐"""
        results = recommender.recommend(
            scene_type="high_stakes_scene",
            required_metrics=["S1", "S4", "S5"]
        )

        assert len(results) > 0
        # 检查第一个推荐是否包含必需维度
        top = results[0]
        for metric in ["S1", "S4", "S5"]:
            if metric in top.metric_scores:
                assert top.metric_scores[metric] > 0

    def test_recommend_with_category_preference(self, recommender):
        """测试按偏好类别推荐"""
        results = recommender.recommend(
            scene_type="content_continuation",
            preferred_category="continuation"
        )

        assert len(results) > 0
        assert results[0].template.category == TemplateCategory.CONTINUATION

    def test_recommend_top_k(self, recommender):
        """测试返回top_k个推荐"""
        results = recommender.recommend(scene_type="content_continuation", top_k=2)

        assert len(results) == 2
        # 检查是否按分数排序
        assert results[0].total_score >= results[1].total_score


# ==================== 测试单模板推荐 ====================

class TestSingleRecommendation:
    def test_recommend_single(self, recommender):
        """测试推荐单个模板"""
        result = recommender.recommend_single(scene_type="outline_generation")

        assert result is not None
        assert isinstance(result, TemplateScore)
        assert result.template.category == TemplateCategory.OUTLINE

    def test_recommend_single_no_match(self, recommender):
        """测试无匹配时返回None"""
        # 使用不存在的场景类型
        result = recommender.recommend_single(scene_type="nonexistent_scene")
        # 应该仍能返回结果（因为有后备方案）
        assert result is not None


# ==================== 测试评分计算 ====================

class TestScoring:
    def test_temperature_score_calculation(self, recommender, assembler):
        """测试温度评分计算"""
        template = assembler.get_template("全文大纲")
        criteria = RecommendationCriteria(
            scene_type="outline_generation",
            min_temperature=0.5,
            max_temperature=0.7
        )

        score = recommender._calculate_temperature_score(template, criteria)

        assert score >= 0
        assert score <= 3.0

    def test_history_bonus_calculation(self, recommender):
        """测试历史表现加分"""
        # 有使用记录的模板应该有加分
        bonus = recommender._calculate_history_bonus("outline_full_novel_v1")
        assert bonus >= 0

        # 新模板也应该有基础分
        new_bonus = recommender._calculate_history_bonus("nonexistent_template")
        assert new_bonus >= 0

    def test_category_bonus(self, recommender, assembler):
        """测试类别匹配加分"""
        template = assembler.get_template("标准续写")
        criteria = RecommendationCriteria(
            scene_type="content_continuation",
            preferred_category=TemplateCategory.CONTINUATION
        )

        score = recommender._score_template(template, criteria)

        assert score.category_bonus > 0
        assert "类别匹配" in score.reasons


# ==================== 测试统计更新 ====================

class TestStatsUpdate:
    def test_update_template_stats(self, recommender, temp_config_dir):
        """测试更新模板统计"""
        initial = recommender.template_stats.get("outline_full_novel_v1", {})
        initial_use_count = initial.get('use_count', 0)

        recommender.update_template_stats(
            template_id="outline_full_novel_v1",
            success=True,
            score=9.0
        )

        # 重新加载后验证
        recommender._load_extended_index()
        updated = recommender.template_stats.get("outline_full_novel_v1", {})
        updated_use_count = updated.get('use_count', 0)

        assert updated_use_count == initial_use_count + 1


# ==================== 测试推荐理由 ====================

class TestRecommendationExplanation:
    def test_explain_recommendation(self, recommender):
        """测试生成推荐理由"""
        result = recommender.recommend_single(scene_type="outline_generation")

        explanation = recommender.explain_recommendation(result)

        assert "全文大纲" in explanation
        assert "v1.0.0" in explanation
        assert "outline" in explanation
        assert "综合得分" in explanation


# ==================== 测试版本历史 ====================

class TestVersionHistory:
    def test_get_template_version_history(self, recommender):
        """测试获取模板版本历史"""
        # 由于是新系统，可能没有历史
        history = recommender.get_template_version_history("outline_full_novel_v1")

        assert isinstance(history, list)
