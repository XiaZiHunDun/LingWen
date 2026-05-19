#!/usr/bin/env python3
"""
get_popular_templates 方法测试

Tests for get_popular_templates method of TemplateRecommender
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from template_recommender import TemplateRecommender, TemplateMetadata, TemplateCategory
from prompt_assembler import TemperatureConfig


class TestGetPopularTemplates:
    """测试 get_popular_templates 方法"""

    @pytest.fixture
    def mock_assembler(self):
        """创建 Mock PromptAssembler"""
        assembler = Mock()
        return assembler

    @pytest.fixture
    def mock_index_file(self, tmp_path):
        """创建 Mock 索引文件"""
        index_file = tmp_path / "00_模板索引.yaml"
        return index_file

    @pytest.fixture
    def template_metadata(self):
        """创建模板元数据对象"""
        def _create_template(template_id: str, name: str, category: str = "continuation"):
            return TemplateMetadata(
                id=template_id,
                name=name,
                category=TemplateCategory(category),
                version="v1.0.0",
                status="active",
                file_path=f"02_正文续写/{name}_CARE.md",
                description=f"测试模板 {name}",
                temperature=TemperatureConfig(recommended=0.7, min_value=0.6, max_value=0.8),
                care_elements={"result_metrics": ["S1", "S2", "S3"]},
            )
        return _create_template

    # ==================== 测试1: 按综合评分排序 ====================

    def test_returns_templates_sorted_by_popularity_score(
        self, mock_assembler, mock_index_file, template_metadata
    ):
        """验证按综合评分排序: score = use_count * success_rate * (avg_score / 10)"""

        # 创建多个模板，其中 continuation_standard_v1 评分最高
        # continuation_standard_v1: use_count=10, success_rate=0.9, avg_score=9.0
        #   score = 10 * 0.9 * (9.0/10) = 8.1
        # outline_full_novel_v1: use_count=5, success_rate=0.8, avg_score=8.5
        #   score = 5 * 0.8 * (8.5/10) = 3.4
        # continuation_high_stakes_v1: use_count=3, success_rate=0.7, avg_score=8.0
        #   score = 3 * 0.7 * (8.0/10) = 1.68

        mock_assembler.get_template.side_effect = lambda name: {
            "outline_full_novel_v1": template_metadata("outline_full_novel_v1", "全文大纲", "outline"),
            "continuation_standard_v1": template_metadata("continuation_standard_v1", "标准续写", "continuation"),
            "continuation_high_stakes_v1": template_metadata("continuation_high_stakes_v1", "高潮场景", "continuation"),
        }.get(name)

        recommender = TemplateRecommender(
            assembler=mock_assembler,
            index_file=str(mock_index_file)
        )

        # 手动设置统计数据
        recommender.template_stats = {
            "outline_full_novel_v1": {
                "use_count": 5,
                "success_rate": 0.8,
                "avg_score": 8.5,
                "last_used": "2026-05-19",
            },
            "continuation_standard_v1": {
                "use_count": 10,
                "success_rate": 0.9,
                "avg_score": 9.0,
                "last_used": "2026-05-19",
            },
            "continuation_high_stakes_v1": {
                "use_count": 3,
                "success_rate": 0.7,
                "avg_score": 8.0,
                "last_used": "2026-05-19",
            },
        }

        results = recommender.get_popular_templates(limit=10)

        assert len(results) == 3
        # 验证排序正确: 标准续写(8.1) > 全文大纲(3.4) > 高潮场景(1.68)
        assert results[0].id == "continuation_standard_v1"
        assert results[1].id == "outline_full_novel_v1"
        assert results[2].id == "continuation_high_stakes_v1"

    # ==================== 测试2: 验证limit参数 ====================

    def test_respects_limit_parameter(
        self, mock_assembler, mock_index_file, template_metadata
    ):
        """验证limit参数"""

        mock_assembler.get_template.side_effect = lambda name: {
            "template_a": template_metadata("template_a", "模板A"),
            "template_b": template_metadata("template_b", "模板B"),
            "template_c": template_metadata("template_c", "模板C"),
        }.get(name)

        recommender = TemplateRecommender(
            assembler=mock_assembler,
            index_file=str(mock_index_file)
        )

        recommender.template_stats = {
            "template_a": {"use_count": 10, "success_rate": 0.9, "avg_score": 9.0},
            "template_b": {"use_count": 8, "success_rate": 0.8, "avg_score": 8.0},
            "template_c": {"use_count": 6, "success_rate": 0.7, "avg_score": 7.0},
        }

        # limit=2
        results = recommender.get_popular_templates(limit=2)

        assert len(results) == 2

    # ==================== 测试3: 过滤use_count=0的模板 ====================

    def test_excludes_unused_templates(
        self, mock_assembler, mock_index_file, template_metadata
    ):
        """过滤use_count=0的模板"""

        mock_assembler.get_template.side_effect = lambda name: {
            "active_template": template_metadata("active_template", "活跃模板"),
            "unused_template": template_metadata("unused_template", "未使用模板"),
        }.get(name)

        recommender = TemplateRecommender(
            assembler=mock_assembler,
            index_file=str(mock_index_file)
        )

        recommender.template_stats = {
            "active_template": {"use_count": 10, "success_rate": 0.9, "avg_score": 9.0},
            "unused_template": {"use_count": 0, "success_rate": 0.0, "avg_score": 0.0},
        }

        results = recommender.get_popular_templates(limit=10)

        assert len(results) == 1
        assert results[0].id == "active_template"

    # ==================== 测试4: 无统计信息时返回空列表 ====================

    def test_empty_list_when_no_stats(self, mock_assembler, mock_index_file):
        """无统计信息时返回空列表"""

        recommender = TemplateRecommender(
            assembler=mock_assembler,
            index_file=str(mock_index_file)
        )

        # 确保没有任何统计数据
        recommender.template_stats = {}

        results = recommender.get_popular_templates(limit=10)

        assert results == []
        assert len(results) == 0

    # ==================== 测试5: 回归测试现有recommend方法 ====================

    def test_recommend_returns_scored_templates(
        self, mock_assembler, mock_index_file, template_metadata
    ):
        """回归测试现有recommend方法"""

        mock_assembler.list_templates.return_value = ["全文大纲", "标准续写"]
        mock_assembler.get_template.side_effect = lambda name: {
            "全文大纲": template_metadata("outline_full_novel_v1", "全文大纲", "outline"),
            "标准续写": template_metadata("continuation_standard_v1", "标准续写", "continuation"),
        }.get(name)

        recommender = TemplateRecommender(
            assembler=mock_assembler,
            index_file=str(mock_index_file)
        )

        recommender.template_stats = {
            "outline_full_novel_v1": {"use_count": 5, "success_rate": 0.8, "avg_score": 8.5},
            "continuation_standard_v1": {"use_count": 10, "success_rate": 0.9, "avg_score": 9.0},
        }

        results = recommender.recommend(scene_type="outline_generation", top_k=3)

        assert len(results) > 0
        assert all(r.total_score >= 0 for r in results)


class TestGetPopularTemplatesEdgeCases:
    """边缘情况测试"""

    @pytest.fixture
    def mock_assembler(self):
        return Mock()

    @pytest.fixture
    def mock_index_file(self, tmp_path):
        return tmp_path / "00_模板索引.yaml"

    @pytest.fixture
    def template_metadata(self):
        """创建模板元数据对象"""
        def _create_template(template_id: str, name: str, category: str = "continuation"):
            return TemplateMetadata(
                id=template_id,
                name=name,
                category=TemplateCategory(category),
                version="v1.0.0",
                status="active",
                file_path=f"02_正文续写/{name}_CARE.md",
                description=f"测试模板 {name}",
                temperature=TemperatureConfig(recommended=0.7, min_value=0.6, max_value=0.8),
                care_elements={"result_metrics": ["S1", "S2", "S3"]},
            )
        return _create_template

    def test_with_missing_template_in_assembler(
        self, mock_assembler, mock_index_file, template_metadata
    ):
        """当assembler.get_template返回None时的处理"""

        mock_assembler.get_template.return_value = None

        recommender = TemplateRecommender(
            assembler=mock_assembler,
            index_file=str(mock_index_file)
        )

        recommender.template_stats = {
            "ghost_template": {"use_count": 5, "success_rate": 0.8, "avg_score": 8.5},
        }

        results = recommender.get_popular_templates(limit=10)

        # 应该忽略返回None的模板
        assert results == []

    def test_verify_popularity_score_formula(
        self, mock_assembler, mock_index_file, template_metadata
    ):
        """验证综合评分公式: score = use_count * success_rate * (avg_score / 10)"""

        mock_assembler.get_template.side_effect = lambda name: {
            "formula_template": template_metadata("formula_template", "公式验证模板"),
        }.get(name)

        recommender = TemplateRecommender(
            assembler=mock_assembler,
            index_file=str(mock_index_file)
        )

        # 设置特定值来验证公式
        # use_count=10, success_rate=0.8, avg_score=8.5
        # expected score = 10 * 0.8 * (8.5/10) = 6.8
        recommender.template_stats = {
            "formula_template": {
                "use_count": 10,
                "success_rate": 0.8,
                "avg_score": 8.5,
            },
        }

        results = recommender.get_popular_templates(limit=10)

        assert len(results) == 1
        assert results[0].id == "formula_template"

        # 通过计算验证公式正确性
        stats = recommender.template_stats["formula_template"]
        expected_score = stats["use_count"] * stats["success_rate"] * (stats["avg_score"] / 10)
        assert expected_score == 6.8


if __name__ == "__main__":
    pytest.main([__file__, "-v"])